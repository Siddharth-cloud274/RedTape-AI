from typing import Dict, List, Optional
from app.schemas.chat import IntentCategory
from app.schemas.interview import InterviewStatus, InterviewAction, InterviewDecision
from app.services.context_tracker import context_tracker, FIELD_SYNONYMS

# Natural question templates per target context field
FIELD_QUESTION_TEMPLATES: Dict[str, str] = {
    "location": "Which district or local body in West Bengal do you reside in?",
    "business_location": "Which municipality, district, or area is your shop or business located in?",
    "business_type": "What type of business or commercial establishment are you running or planning to open?",
    "application_type": "Is this a fresh new application or a renewal of an existing licence?",
    "application_purpose": "What is the primary purpose for this application (e.g. college admission, scholarship, employment)?",
    "approximate_annual_turnover": "What is the approximate annual turnover of your food business?",
    "operation_status": "Is your business already operating, or are you currently setting it up?",
    "service_needed": "Could you clarify which specific government certificate, licence, or service you need assistance with?",
    "applicant_name": "Could you please share your full name as it should appear on the official application?",
    "father_name": "What is your father's or guardian's full name?",
    "date_of_birth": "What is your date of birth (in DD/MM/YYYY format)?",
    "present_address": "What is your complete present residential address in Kolkata?",
    "stay_duration": "How many years have you been residing in West Bengal?",
}


class QuestionPlanner:
    """
    Deterministic question planner.
    Evaluates known facts and intent against preliminary context requirements.
    Decides the interview status, next action, and target field.
    """

    @staticmethod
    def get_default_question(field_name: str) -> str:
        return FIELD_QUESTION_TEMPLATES.get(
            field_name,
            f"Could you please share details regarding your {field_name.replace('_', ' ')}?"
        )

    def plan_decision(
        self,
        intent: IntentCategory,
        known_facts: Dict[str, str],
        skipped_fields: Optional[List[str]] = None,
        is_pause_requested: bool = False,
        is_conflict: bool = False,
    ) -> InterviewDecision:
        skipped = skipped_fields or []
        known_field_names = list(known_facts.keys())

        # 1. Unsupported Service Intent
        if intent == IntentCategory.UNSUPPORTED:
            return InterviewDecision(
                interview_status=InterviewStatus.UNSUPPORTED,
                current_intent=intent,
                known_fields=known_field_names,
                missing_context=[],
                skipped_fields=skipped,
                next_action=InterviewAction.EXPLAIN_LIMITATION,
                target_field=None,
                question=None,
                notes="Service is outside current RedTape AI scope.",
            )

        # 2. Citizen requested to pause or stop
        if is_pause_requested:
            missing = context_tracker.calculate_missing_fields(intent, known_facts, skipped)
            return InterviewDecision(
                interview_status=InterviewStatus.PAUSED,
                current_intent=intent,
                known_fields=known_field_names,
                missing_context=missing,
                skipped_fields=skipped,
                next_action=InterviewAction.PAUSE_INTERVIEW,
                target_field=None,
                question=None,
                notes="Interview paused at user request. State is preserved.",
            )

        # 3. Ambiguous / Unclear User Goal
        if intent == IntentCategory.UNCLEAR:
            return InterviewDecision(
                interview_status=InterviewStatus.CLARIFICATION_NEEDED,
                current_intent=intent,
                known_fields=known_field_names,
                missing_context=["service_needed"],
                skipped_fields=skipped,
                next_action=InterviewAction.ASK_QUESTION,
                target_field="service_needed",
                question=self.get_default_question("service_needed"),
                notes="Citizen goal is ambiguous; requesting clarification.",
            )

        # 4. Preliminary Context Evaluation
        missing_fields = context_tracker.calculate_missing_fields(
            intent=intent,
            known_facts=known_facts,
            skipped_fields=skipped,
        )

        # 5. Stopping Condition: Sufficient Context Gathered
        if not missing_fields:
            return InterviewDecision(
                interview_status=InterviewStatus.READY_FOR_RESEARCH,
                current_intent=intent,
                known_fields=known_field_names,
                missing_context=[],
                skipped_fields=skipped,
                next_action=InterviewAction.HANDOFF_TO_FUTURE_RESEARCH,
                target_field=None,
                question=None,
                notes="Sufficient preliminary context collected. Ready for future official-source research.",
            )

        # 6. Active Question Planning
        target_field = missing_fields[0]
        action = InterviewAction.CLARIFY_CONFLICT if is_conflict else InterviewAction.ASK_QUESTION

        return InterviewDecision(
            interview_status=InterviewStatus.COLLECTING_CONTEXT,
            current_intent=intent,
            known_fields=known_field_names,
            missing_context=missing_fields,
            skipped_fields=skipped,
            next_action=action,
            target_field=target_field,
            question=self.get_default_question(target_field),
            notes=f"Targeting context field: '{target_field}'.",
        )

    def validate_decision(
        self,
        decision: InterviewDecision,
        known_facts: Dict[str, str],
    ) -> InterviewDecision:
        """
        Enforces backend authority rules:
        - Prevents re-asking any field already present in known_facts.
        - Ensures target field belongs to missing context.
        """
        if decision.target_field:
            synonyms = FIELD_SYNONYMS.get(decision.target_field, {decision.target_field})
            # If target field is already known, advance or conclude
            is_already_known = any(
                s in known_facts and bool(known_facts[s].strip())
                for s in synonyms
            )
            if is_already_known:
                # Recalculate decision without the already known field
                return self.plan_decision(
                    intent=decision.current_intent,
                    known_facts=known_facts,
                    skipped_fields=decision.skipped_fields,
                )

        return decision


question_planner = QuestionPlanner()
