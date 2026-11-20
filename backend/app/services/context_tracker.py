from typing import Dict, List, Set
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
    ],
    IntentCategory.FSSAI_REGISTRATION: [
        "business_type",
        "business_location",
        "approximate_annual_turnover",
    ],
    IntentCategory.TRADE_LICENCE: [
        "business_type",
        "business_location",
    ],
    IntentCategory.FOOD_BUSINESS_SETUP: [
        "business_type",
        "business_location",
    ],
    IntentCategory.UNCLEAR: [
        "service_needed",
    ],
    IntentCategory.UNSUPPORTED: [],
}

# Synonymous field groups: satisfying any one of these satisfies the requirement
FIELD_SYNONYMS: Dict[str, Set[str]] = {
    "location": {"location", "state", "district", "city_or_municipality", "jurisdiction_type"},
    "business_location": {"business_location", "location", "city_or_municipality", "district"},
    "application_purpose": {"application_purpose", "purpose"},
    "business_type": {"business_type"},
    "approximate_annual_turnover": {"approximate_annual_turnover", "annual_turnover", "turnover"},
    "service_needed": {"service_needed", "certificate_type"},
}


class ContextTracker:
    """Computes deterministic missing context fields based on intent and confirmed facts."""

    @staticmethod
    def calculate_missing_fields(
        intent: IntentCategory,
        known_facts: Dict[str, str]
    ) -> List[str]:
        required = INTENT_REQUIRED_CONTEXT.get(intent, [])
        known_keys = set(known_facts.keys())

        missing: List[str] = []
        for req_field in required:
            synonyms = FIELD_SYNONYMS.get(req_field, {req_field})
            # Check if any synonym is already known and has a non-empty value
            has_fact = any(
                syn in known_keys and bool(known_facts[syn].strip())
                for syn in synonyms
            )
            if not has_fact:
                missing.append(req_field)

        return missing


context_tracker = ContextTracker()
