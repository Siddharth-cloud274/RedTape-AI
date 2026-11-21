from typing import Dict, List, Optional, Set
from app.schemas.chat import IntentCategory

# Required preliminary context fields per intent category (needed to clarify citizen's administrative goal)
INTENT_REQUIRED_CONTEXT: Dict[IntentCategory, List[str]] = {
    IntentCategory.WB_INCOME_CERTIFICATE: [
        "location",
        "application_purpose",
    ],
    IntentCategory.WB_DOMICILE_CERTIFICATE: [
        "location",
        "application_purpose",
        "applicant_name",
        "father_name",
        "date_of_birth",
        "present_address",
    ],
    IntentCategory.FSSAI_REGISTRATION: [
        "business_type",
        "business_location",
        "approximate_annual_turnover",
        "application_type",
    ],
    IntentCategory.TRADE_LICENCE: [
        "business_type",
        "business_location",
        "application_type",
    ],
    IntentCategory.FOOD_BUSINESS_SETUP: [
        "business_type",
        "business_location",
        "operation_status",
    ],
    IntentCategory.UNCLEAR: [
        "service_needed",
    ],
    IntentCategory.UNSUPPORTED: [],
}

# Synonymous field groups: satisfying any one of these satisfies the requirement
FIELD_SYNONYMS: Dict[str, Set[str]] = {
    "location": {
        "location",
        "state",
        "district",
        "city_or_municipality",
        "jurisdiction_type",
        "residence_location",
        "home_location",
    },
    "business_location": {
        "business_location",
        "location",
        "shop_location",
        "store_location",
        "workplace_location",
        "city_or_municipality",
        "district",
    },
    "application_purpose": {"application_purpose", "purpose", "reason"},
    "business_type": {
        "business_type",
        "shop_type",
        "store_type",
        "trade_type",
        "food_business_type",
        "proposed_business_type",
    },
    "approximate_annual_turnover": {
        "approximate_annual_turnover",
        "annual_turnover",
        "turnover",
    },
    "application_type": {
        "application_type",
        "new_or_renewal",
        "is_renewal",
        "application_status",
    },
    "operation_status": {
        "operation_status",
        "is_operating",
        "already_operating",
        "business_stage",
    },
    "service_needed": {"service_needed", "certificate_type"},
    "applicant_name": {"applicant_name", "name", "full_name", "citizen_name"},
    "father_name": {"father_name", "parent_name", "guardian_name", "father"},
    "date_of_birth": {"date_of_birth", "dob", "birth_date", "birthdate"},
    "present_address": {
        "present_address",
        "address",
        "current_address",
        "residential_address",
        "residence_location",
        "residence",
        "domicile_address",
    },
    "stay_duration": {"stay_duration", "duration_of_stay", "stay_years", "years_in_state"},
}


class ContextTracker:
    """Computes deterministic missing context fields based on intent, confirmed facts, and skipped fields."""

    @staticmethod
    def calculate_missing_fields(
        intent: IntentCategory,
        known_facts: Dict[str, str],
        skipped_fields: Optional[List[str]] = None,
    ) -> List[str]:
        required = INTENT_REQUIRED_CONTEXT.get(intent, [])
        known_keys = set(k.strip().lower() for k in known_facts.keys())
        skipped_set = set(s.strip().lower() for s in (skipped_fields or []))

        missing: List[str] = []
        for req_field in required:
            synonyms = FIELD_SYNONYMS.get(req_field, {req_field})
            # If the user explicitly skipped or could not answer this field
            if any(syn in skipped_set for syn in synonyms) or req_field in skipped_set:
                continue

            # Check if any synonym is already known and has a non-empty value
            has_fact = any(
                syn in known_keys and bool(known_facts.get(syn, "").strip())
                for syn in synonyms
            )
            if not has_fact:
                missing.append(req_field)

        return missing


context_tracker = ContextTracker()
