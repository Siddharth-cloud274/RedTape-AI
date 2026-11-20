import json
import os
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

SYSTEM_INSTRUCTION = """You are RedTape AI, an agentic AI assistant helping Indian citizens navigate government bureaucracy.
Your task is CONVERSATIONAL INTENT UNDERSTANDING and CONTEXT RETENTION.

CRITICAL RULES & GROUNDING:
1. Grounding & Anti-Hallucination: You do NOT have a live government research engine connected yet. NEVER invent or fabricate eligibility criteria, required documents, application fees, turnaround times, or government URLs. If the user asks for verified legal checklists, clarify that verified official requirements will be connected in subsequent milestones.
2. Initial Bureaucratic Taxonomy:
   - "wb_income_certificate": Income certificate in West Bengal (e.g. for college admissions, scholarships, subsidies).
   - "wb_domicile_certificate": Domicile / residential certificate in West Bengal.
   - "fssai_registration": Food business registration or license under FSSAI (Food Safety and Standards Authority of India).
   - "trade_licence": Municipal or panchayat trade licence to run a commercial establishment.
     *NON-NEGOTIABLE*: Trade licence is a municipal permit and is STRICTLY SEPARATE from FSSAI food registration. NEVER classify trade licence as FSSAI.
   - "food_business_setup": Opening or setting up a food business (e.g., bakery, restaurant, cafe, sweet shop). Acknowledge that food establishments typically involve both a local municipal Trade Licence and an FSSAI Food Safety registration, but do not assert unverified legal rules.
   - "unsupported": Services outside the initial scope (e.g., passport, driving licence, property registration, voter card). Transparently acknowledge the limitation.
   - "unclear": Ambiguous or underspecified requests (e.g., "I need some certificate", "help me with paperwork"). Ask a concise clarifying question.
3. Context Memory:
   - Always analyze the full conversation history.
   - Follow-up messages (e.g., "I live in Kolkata", "It's for college") must be interpreted in the context of the active administrative request, not as unrelated standalone goals.
4. Output:
   - Provide a concise, helpful conversational reply for the citizen in the 'reply' field.
   - Extract only explicitly established facts into 'known_information'.
"""


class GeminiServiceError(Exception):
    """Exception raised for Gemini SDK or integration errors."""

    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class GeminiService:
    """Modular service handling Google Gemini API integration and intent detection."""

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

    def _format_conversation_history(
        self, current_message: str, history: List[Dict]
    ) -> str:
        """Assembles chronological conversation history for prompt grounding."""
        recent_history = history[-10:] if len(history) > 10 else history

        lines = ["Prior Conversation Context:"]
        if not recent_history:
            lines.append("No prior turns. This is the first message.")
        else:
            for turn in recent_history:
                role = turn.get("role", "user").capitalize()
                content = turn.get("content", "")
                lines.append(f"{role}: {content}")

        lines.append(f"\nCurrent User Message: {current_message}")
        lines.append(
            "Based on the conversation context and current user message, "
            "perform intent classification and generate your conversational response."
        )
        return "\n".join(lines)

    def validate_consistency(
        self, result: StructuredIntentResult
    ) -> StructuredIntentResult:
        """Enforces logical consistency across intent, status, support, and action."""
        intent = result.intent

        if intent == IntentCategory.UNCLEAR:
            result.intent_status = IntentStatus.NEEDS_CLARIFICATION
            result.service_support = ServiceSupport.UNDETERMINED
            result.next_action = NextAction.ASK_CLARIFICATION

        elif intent == IntentCategory.UNSUPPORTED:
            result.intent_status = IntentStatus.UNSUPPORTED
            result.service_support = ServiceSupport.UNSUPPORTED
            result.next_action = NextAction.EXPLAIN_LIMITATION

        elif intent == IntentCategory.TRADE_LICENCE:
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
            if result.next_action not in {
                NextAction.ACKNOWLEDGE_INTENT,
                NextAction.ASK_CLARIFICATION,
            }:
                result.next_action = NextAction.ACKNOWLEDGE_INTENT

        elif intent == IntentCategory.FOOD_BUSINESS_SETUP:
            result.intent_status = IntentStatus.IDENTIFIED
            result.service_support = ServiceSupport.RECOGNIZED_NOT_IMPLEMENTED
            result.next_action = NextAction.ACKNOWLEDGE_INTENT

        return result

    def analyze_intent_and_reply(
        self, current_message: str, history: Optional[List[Dict]] = None
    ) -> StructuredIntentResult:
        """
        Sends conversation context to Gemini with structured output,
        validates the response, and returns StructuredIntentResult.
        """
        client = self._get_client()
        prompt = self._format_conversation_history(
            current_message, history or []
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

                # Enforce logical consistency rules
                return self.validate_consistency(structured)

            except APIError as api_err:
                code = getattr(api_err, "code", None)
                if code == 429:
                    raise GeminiServiceError(
                        "Gemini API rate limit or quota exceeded. Please wait a moment and retry.",
                        status_code=429,
                    ) from api_err
                if code == 503:
                    # Model spike in demand: record and try next candidate
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

        # If all candidates experienced 503 high demand
        if last_error:
            raise GeminiServiceError(
                "Gemini service is currently experiencing temporary high demand across models. Please retry in a few moments.",
                status_code=503,
            ) from last_error

        raise GeminiServiceError("No model response was generated.", status_code=500)


gemini_service = GeminiService()
