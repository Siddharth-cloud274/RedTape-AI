import json
import os
import time
from typing import Dict, List, Optional
from google import genai
from google.genai import types
from google.genai.errors import APIError

from app.config import settings
from app.schemas.chat import (
    IntentCategory,
    IntentStatus,
    NextAction,
    ServiceSupport,
    StructuredIntentResult,
)
from app.services.context_tracker import context_tracker
from app.services.research_service import research_service

SYSTEM_INSTRUCTION = """You are RedTape AI, an open-to-all civic AI chatbot assisting Indian citizens with ANY government service, certificate, licence, or bureaucratic procedure across India.
Your task is CONVERSATIONAL CIVIC GUIDANCE, INTENT UNDERSTANDING, FACT EXTRACTION, ADAPTIVE INTERVIEWING, and CITING VERIFIED OR PROBABLE OFFICIAL GOVERNMENT RESOURCES.

CRITICAL RULES & GROUNDING:
1. Open-to-All Civic Chatbot:
   - You can converse, explain, and guide citizens on ANY Indian civic procedure (e.g. Domicile, Income, Trade Licence, FSSAI, Passport, Driving Licence, PAN Card, Voter ID, Aadhaar, Caste Certificates, Birth/Death Certificates, Welfare Schemes, etc.).
   - If a service is verified (WB Domicile, WB Income, Trade Licence, FSSAI), use the verified official portals and checklists provided.
   - If a service is outside the verified set, STILL ACT AS A HELPFUL CIVIC CHATBOT: provide helpful procedural steps, document checklists, and the probable official government portal (e.g. passportindia.gov.in, parivahan.gov.in, incometax.gov.in, voters.eci.gov.in, myaadhaar.uidai.gov.in, services.india.gov.in). Clearly note that these are probable official guidelines.
   - NEVER invent non-existent government websites or fake URLs. Always use real official portals.
2. Conversational Conciseness:
   - Provide direct, warm, and concise answers.
   - If asking an interview question, ask ONLY ONE natural question at a time.
   - Only elaborate with full portal lists or heavy checklists when specifically asked by the citizen or when relevant.
3. Bureaucratic Taxonomy:
   - "wb_income_certificate": Income certificate in West Bengal.
   - "wb_domicile_certificate": Domicile / residential certificate in West Bengal.
   - "fssai_registration": Food business registration or license under FSSAI.
   - "trade_licence": Municipal or panchayat trade licence (Certificate of Enlistment).
   - "food_business_setup": Opening a commercial food business (Trade Licence + FSSAI).
   - "passport_services": Indian Passport applications, renewals, and Tatkaal.
   - "driving_licence": Driving licences, learner permits, and vehicle registration (Sarathi/Vahan).
   - "pan_card": Permanent Account Number (PAN Card) issuance and corrections.
   - "voter_id": Election Photo Identity Card (EPIC) and voter roll registration.
   - "aadhaar_services": UIDAI Aadhaar card enrollment, update, and PVC card.
   - "caste_certificate": SC/ST/OBC caste certificate issuance.
   - "birth_death_certificate": Civil registration of births and deaths.
   - "general_service": Any other Indian municipal, state, or central government service.
   - "unclear": Ambiguous or underspecified requests (e.g., "I need some certificate", "help me with paperwork"). Ask a concise clarifying question.
   - "unsupported": Non-civic or illegal requests outside public administration.
4. Fact Extraction & Corrections:
   - Extract facts explicitly stated by the user into 'extracted_facts' (with field_name, field_value, exact evidence snippet).
   - Use standardized field names: 'applicant_name', 'father_name', 'date_of_birth', 'present_address', 'stay_duration', 'business_type', 'business_location', 'application_type' (new/renewal), 'application_purpose', 'approximate_annual_turnover', 'residence_location'.
   - If the user explicitly corrects a prior fact (e.g. 'Actually, I live in Howrah'), set is_correction=true.
   - Separate personal residence location from business shop location if both are mentioned.
   - Never extract guesses or assumptions as confirmed facts.
   - Do NOT collect or store sensitive personal identifiers (Aadhaar number, PAN, passwords, bank details).
5. Adaptive Conversational Interviewing & Guidance:
   - Sound like a warm, knowledgeable, helpful assistant. Do not use robotic numbered form menus.
   - NEVER ask for information that is already in the 'Confirmed Facts' list.
   - If a target field is specified, ask ONLY ONE conversational question for that field.
   - Understand short answers, multiple facts in one message, and Hindi or mixed Hinglish naturally.
"""


class GeminiServiceError(Exception):
    """Exception raised for Gemini SDK or integration errors."""

    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class GeminiService:
    """Modular service handling Google Gemini API integration, intent detection, and fact extraction."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self._api_key = api_key
        self._model = model

    @property
    def api_key(self) -> str:
        raw_key = (
            self._api_key
            or settings.GEMINI_API_KEY
            or os.environ.get("GEMINI_API_KEY", "")
        )
        return raw_key.strip("'\" \t\r\n")

    @property
    def model(self) -> str:
        return (
            self._model
            or settings.GEMINI_MODEL
            or os.environ.get("GEMINI_MODEL", "gemini-3.1-flash-lite")
        )

    def _get_client(self) -> genai.Client:
        key = self.api_key
        if not key:
            raise GeminiServiceError(
                "Gemini API key is not configured on the backend.",
                status_code=503,
            )
        try:
            return genai.Client(api_key=key)
        except Exception as e:
            raise GeminiServiceError(
                f"Failed to initialize Gemini client: {str(e)}",
                status_code=500,
            ) from e

    def _format_conversation_context(
        self,
        current_message: str,
        history: List[Dict],
        confirmed_facts: Dict[str, str],
        missing_fields: List[str],
        target_field: Optional[str] = None,
        interview_status: Optional[str] = None,
        current_intent: Optional[str] = None,
    ) -> str:
        """Assembles prompt grounding with history, confirmed facts, missing fields, and verified official research."""
        recent_history = history[-10:] if len(history) > 10 else history

        lines = ["=== Prior Conversation Turns ==="]
        if not recent_history:
            lines.append("No prior turns in this session.")
        else:
            for turn in recent_history:
                role = turn.get("role", "user").capitalize()
                content = turn.get("content", "")
                lines.append(f"{role}: {content}")

        lines.append("\n=== Established Confirmed Facts ===")
        if not confirmed_facts:
            lines.append("No confirmed facts recorded yet.")
        else:
            for k, v in confirmed_facts.items():
                lines.append(f"- {k}: {v}")

        if missing_fields:
            lines.append(f"\nMissing Context Fields Needed: {', '.join(missing_fields)}")

        if target_field:
            lines.append(
                f"\nNext Interview Focus: If asking a question, ask naturally ONLY for the target field: '{target_field}'. Do not re-ask known facts."
            )
        if interview_status == "ready_for_research":
            lines.append(
                "\nInterview Status: All preliminary scoping context is fulfilled. Acknowledge the details provided and share the official portal links and required document checklist clearly."
            )

        # Inject verified or probable official research based on service intent or query keywords
        service_for_research = current_intent
        if not service_for_research and current_message:
            research_obj = research_service.get_service_research(None, query=current_message)
            if research_obj:
                service_for_research = research_obj.service_id

        if service_for_research:
            research_text = research_service.format_research_context_for_prompt(service_for_research, query=current_message)
            if research_text:
                lines.append(f"\n{research_text}")

        lines.append(f"\nCurrent User Message: {current_message}")
        lines.append(
            "Instructions: Analyze the message, extract any newly supplied facts or corrections, "
            "perform intent classification, and provide your concise, natural reply."
        )
        return "\n".join(lines)

    def validate_consistency(
        self,
        result: StructuredIntentResult,
        known_facts: Optional[Dict[str, str]] = None,
    ) -> StructuredIntentResult:
        """Enforces logical consistency across intent, status, support, and action."""
        if known_facts is None:
            known_facts = {}
        intent = result.intent

        if intent == IntentCategory.UNCLEAR:
            result.intent_status = IntentStatus.NEEDS_CLARIFICATION
            result.service_support = ServiceSupport.UNDETERMINED
            result.next_action = NextAction.ASK_CLARIFICATION

        elif intent == IntentCategory.UNSUPPORTED:
            result.intent_status = IntentStatus.UNSUPPORTED
            result.service_support = ServiceSupport.UNSUPPORTED
            result.next_action = NextAction.EXPLAIN_LIMITATION

        elif intent in {
            IntentCategory.TRADE_LICENCE,
            IntentCategory.FOOD_BUSINESS_SETUP,
            IntentCategory.PASSPORT_SERVICES,
            IntentCategory.DRIVING_LICENCE,
            IntentCategory.PAN_CARD,
            IntentCategory.VOTER_ID,
            IntentCategory.AADHAAR_SERVICES,
            IntentCategory.CASTE_CERTIFICATE,
            IntentCategory.BIRTH_DEATH_CERTIFICATE,
            IntentCategory.GENERAL_SERVICE,
        }:
            result.intent_status = IntentStatus.IDENTIFIED
            result.service_support = ServiceSupport.RECOGNIZED_NOT_IMPLEMENTED
            result.next_action = NextAction.ACKNOWLEDGE_INTENT

        elif intent in {
            IntentCategory.WB_INCOME_CERTIFICATE,
            IntentCategory.WB_DOMICILE_CERTIFICATE,
            IntentCategory.FSSAI_REGISTRATION,
        }:
            result.intent_status = IntentStatus.IDENTIFIED
            result.service_support = ServiceSupport.SUPPORTED_MVP

        elif intent == IntentCategory.FOOD_BUSINESS_SETUP:
            result.intent_status = IntentStatus.IDENTIFIED
            result.service_support = ServiceSupport.RECOGNIZED_NOT_IMPLEMENTED
            result.next_action = NextAction.ACKNOWLEDGE_INTENT

        # Combine previously known facts with newly extracted facts for missing context calculation
        combined_facts = dict(known_facts)
        for ef in result.extracted_facts:
            if ef.field_name and ef.field_value:
                combined_facts[ef.field_name.strip().lower()] = ef.field_value.strip()

        # Deterministically compute missing fields
        deterministic_missing = context_tracker.calculate_missing_fields(
            result.intent, combined_facts
        )
        result.missing_information = deterministic_missing

        if deterministic_missing and result.intent_status == IntentStatus.IDENTIFIED:
            result.next_action = NextAction.ASK_CLARIFICATION
        elif not deterministic_missing and result.intent_status == IntentStatus.IDENTIFIED:
            result.next_action = NextAction.ACKNOWLEDGE_INTENT

        return result

    def analyze_intent_and_reply(
        self,
        current_message: str,
        history: Optional[List[Dict]] = None,
        confirmed_facts: Optional[Dict[str, str]] = None,
        missing_fields: Optional[List[str]] = None,
        target_field: Optional[str] = None,
        interview_status: Optional[str] = None,
        current_intent: Optional[str] = None,
    ) -> StructuredIntentResult:
        """
        Sends conversation context to Gemini with structured output,
        extracts facts and intent, and returns validated StructuredIntentResult.
        """
        client = self._get_client()
        facts_dict = confirmed_facts or {}
        missing_list = missing_fields or []

        prompt = self._format_conversation_context(
            current_message=current_message,
            history=history or [],
            confirmed_facts=facts_dict,
            missing_fields=missing_list,
            target_field=target_field,
            interview_status=interview_status,
            current_intent=current_intent,
        )

        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            response_mime_type="application/json",
            response_schema=StructuredIntentResult,
            temperature=0.2,
        )

        # Primary and fallback model candidates to handle temporary 503 high demand spikes
        candidate_models = [self.model]
        for fb in ["gemini-3.1-flash-lite", "gemini-3.5-flash", "gemini-3.8-flash"]:
            if fb not in candidate_models:
                candidate_models.append(fb)

        last_error = None
        for model_candidate in candidate_models:
            try:
                response = client.models.generate_content(
                    model=model_candidate,
                    contents=prompt,
                    config=config,
                )

                if not response.text:
                    raise GeminiServiceError(
                        "Gemini returned an empty response.", status_code=502
                    )

                # Parse and validate with Pydantic
                try:
                    data = json.loads(response.text)
                    structured = StructuredIntentResult.model_validate(data)
                except Exception as parse_err:
                    raise GeminiServiceError(
                        f"Failed to parse structured model response: {str(parse_err)}",
                        status_code=502,
                    ) from parse_err

                # Enforce logical consistency and update missing fields deterministically
                return self.validate_consistency(structured, facts_dict)

            except APIError as api_err:
                code = getattr(api_err, "code", None)
                if code == 429:
                    # Bounded single retry before failing to absorb short per-minute burst rate limits
                    time.sleep(1.5)
                    try:
                        retry_resp = client.models.generate_content(
                            model=model_candidate,
                            contents=prompt,
                            config=config,
                        )
                        if retry_resp.text:
                            data = json.loads(retry_resp.text)
                            structured = StructuredIntentResult.model_validate(data)
                            return self.validate_consistency(structured, facts_dict)
                    except Exception:
                        pass
                    raise GeminiServiceError(
                        "Gemini API rate limit or quota exceeded. Please wait a moment and retry.",
                        status_code=429,
                    ) from api_err
                if code == 503:
                    last_error = api_err
                    continue
                raise GeminiServiceError(
                    f"Gemini API error ({code}): {api_err.message}",
                    status_code=502,
                ) from api_err
            except GeminiServiceError:
                raise
            except TimeoutError as to_err:
                raise GeminiServiceError(
                    "Request to Gemini API timed out.", status_code=504
                ) from to_err
            except Exception as generic_err:
                raise GeminiServiceError(
                    f"Unexpected AI service error: {str(generic_err)}",
                    status_code=500,
                ) from generic_err

        if last_error:
            raise GeminiServiceError(
                "Gemini service is currently experiencing temporary high demand across models. Please retry in a few moments.",
                status_code=503,
            ) from last_error

        raise GeminiServiceError("No model response was generated.", status_code=500)


gemini_service = GeminiService()
