import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.gemini_service import gemini_service
from app.schemas.chat import IntentCategory, IntentStatus, ServiceSupport


def test_query(prompt: str, expected_intent: IntentCategory):
    print(f"\nUser query: '{prompt}'")
    result = gemini_service.analyze_intent_and_reply(current_message=prompt, history=[])
    print(f"  -> Detected Intent: {result.intent.value}")
    print(f"  -> Intent Status:   {result.intent_status.value}")
    print(f"  -> Service Support: {result.service_support.value}")
    print(f"  -> Next Action:     {result.next_action.value}")
    print(f"  -> Reply preview:   {result.reply[:100]}...")
    assert result.intent == expected_intent, f"Expected {expected_intent}, got {result.intent}"


def main():
    print(f"Running Gemini Live Multi-Intent Smoke Test using model: {gemini_service.model}")
    print(f"API Key present: {bool(gemini_service.api_key)}")

    try:
        # Test 1: WB Income Certificate
        test_query(
            "I need an income certificate for college admission in West Bengal.",
            IntentCategory.WB_INCOME_CERTIFICATE,
        )

        # Test 2: Trade Licence (must NOT be FSSAI)
        test_query(
            "I want a municipal trade licence for my clothing boutique in Kolkata.",
            IntentCategory.TRADE_LICENCE,
        )

        # Test 3: FSSAI Food Business Registration
        test_query(
            "I need an FSSAI food safety registration for selling homemade pickles.",
            IntentCategory.FSSAI_REGISTRATION,
        )

        # Test 4: Ambiguous
        test_query(
            "I need some government certificate please.",
            IntentCategory.UNCLEAR,
        )

        print("\nALL LIVE INTENT SMOKE TESTS PASSED!")

    except Exception as e:
        print(f"\nSMOKE TEST FAILED: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
