import os
import uuid
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from main import app
from app.db.database import get_db, init_db
from app.services.session_service import SessionManager, session_manager
from app.services.memory_service import memory_service
from app.services.context_tracker import context_tracker
from app.services.interview_engine import question_planner, interview_orchestrator
from app.services.gemini_service import gemini_service
from app.schemas.chat import (
    IntentCategory,
    IntentStatus,
    ServiceSupport,
    NextAction,
    KnownInformation,
    StructuredIntentResult,
)
from app.schemas.interview import (
    InterviewStatus,
    InterviewAction,
    InterviewDecision,
)
from app.schemas.facts import ExtractedFactItem

client = TestClient(app)


@pytest.fixture(autouse=True)
def ensure_fresh_db():
    init_db()


def mock_ai_intent_result(
    intent=IntentCategory.TRADE_LICENCE,
    intent_status=IntentStatus.IDENTIFIED,
    reply="Understood.",
    extracted_facts=None,
):
    return StructuredIntentResult(
        intent=intent,
        intent_status=intent_status,
        service_support=ServiceSupport.RECOGNIZED_NOT_IMPLEMENTED if intent == IntentCategory.TRADE_LICENCE else ServiceSupport.SUPPORTED_MVP,
        known_information=KnownInformation(),
        missing_information=[],
        next_action=NextAction.ACKNOWLEDGE_INTENT,
        reply=reply,
        extracted_facts=extracted_facts or [],
    )


# 1. Trade Licence Preliminary Interview
@patch.object(gemini_service, "analyze_intent_and_reply")
def test_trade_licence_preliminary_interview(mock_gemini):
    mock_gemini.return_value = mock_ai_intent_result(
        intent=IntentCategory.TRADE_LICENCE,
        reply="I can help guide you with a trade licence. Which area is the shop located in?",
        extracted_facts=[
            ExtractedFactItem(field_name="business_type", field_value="grocery shop", evidence="grocery shop")
        ],
    )

    res = client.post(
        "/api/chat",
        json={
            "conversation_id": None,
            "client_message_id": str(uuid.uuid4()),
            "message": "I need a trade licence for my grocery shop.",
        },
    )
    assert res.status_code == 200
    data = res.json()
    interview = data["interview"]
    assert interview["interview_status"] == "collecting_context"
    assert interview["current_intent"] == "trade_licence"
    assert "business_type" in interview["known_fields"]
    assert interview["target_field"] in ["business_location", "application_type"]


# 2. Domicile Certificate Preliminary Interview
@patch.object(gemini_service, "analyze_intent_and_reply")
def test_domicile_certificate_preliminary_interview(mock_gemini):
    mock_gemini.return_value = mock_ai_intent_result(
        intent=IntentCategory.WB_DOMICILE_CERTIFICATE,
        reply="Where in West Bengal do you reside?",
        extracted_facts=[],
    )
    res = client.post(
        "/api/chat",
        json={
            "conversation_id": None,
            "client_message_id": str(uuid.uuid4()),
            "message": "I need a domicile certificate in West Bengal.",
        },
    )
    assert res.status_code == 200
    interview = res.json()["interview"]
    assert interview["interview_status"] == "collecting_context"
    assert interview["current_intent"] == "wb_domicile_certificate"
    assert interview["target_field"] == "location"


# 3. Income Certificate Preliminary Interview
@patch.object(gemini_service, "analyze_intent_and_reply")
def test_income_certificate_preliminary_interview(mock_gemini):
    mock_gemini.return_value = mock_ai_intent_result(
        intent=IntentCategory.WB_INCOME_CERTIFICATE,
        reply="I can help with income certificate. Which district are you in?",
        extracted_facts=[],
    )
    res = client.post(
        "/api/chat",
        json={
            "conversation_id": None,
            "client_message_id": str(uuid.uuid4()),
            "message": "I need an income certificate.",
        },
    )
    assert res.status_code == 200
    interview = res.json()["interview"]
    assert interview["interview_status"] == "collecting_context"
    assert interview["target_field"] == "location"


# 4. FSSAI Intent Preliminary Interview
@patch.object(gemini_service, "analyze_intent_and_reply")
def test_fssai_intent_preliminary_interview(mock_gemini):
    mock_gemini.return_value = mock_ai_intent_result(
        intent=IntentCategory.FSSAI_REGISTRATION,
        reply="What kind of food business are you starting?",
        extracted_facts=[],
    )
    res = client.post(
        "/api/chat",
        json={
            "conversation_id": None,
            "client_message_id": str(uuid.uuid4()),
            "message": "I need an FSSAI registration.",
        },
    )
    assert res.status_code == 200
    interview = res.json()["interview"]
    assert interview["interview_status"] == "collecting_context"
    assert interview["target_field"] == "business_type"


# 5. Ambiguous User Goal
@patch.object(gemini_service, "analyze_intent_and_reply")
def test_ambiguous_user_goal(mock_gemini):
    mock_gemini.return_value = mock_ai_intent_result(
        intent=IntentCategory.UNCLEAR,
        intent_status=IntentStatus.NEEDS_CLARIFICATION,
        reply="Could you clarify what certificate you need?",
    )
    res = client.post(
        "/api/chat",
        json={
            "conversation_id": None,
            "client_message_id": str(uuid.uuid4()),
            "message": "I need some government paper.",
        },
    )
    assert res.status_code == 200
    interview = res.json()["interview"]
    assert interview["interview_status"] == "clarification_needed"
    assert interview["next_action"] == "ask_question"


# 6. Unsupported Administrative Request
@patch.object(gemini_service, "analyze_intent_and_reply")
def test_unsupported_administrative_request(mock_gemini):
    mock_gemini.return_value = mock_ai_intent_result(
        intent=IntentCategory.UNSUPPORTED,
        intent_status=IntentStatus.UNSUPPORTED,
        reply="Passport services are not supported currently.",
    )
    res = client.post(
        "/api/chat",
        json={
            "conversation_id": None,
            "client_message_id": str(uuid.uuid4()),
            "message": "I want to apply for a fresh passport.",
        },
    )
    assert res.status_code == 200
    interview = res.json()["interview"]
    assert interview["interview_status"] == "unsupported"
    assert interview["next_action"] == "explain_limitation"


# 7. Multiple Facts in One Message Reaches Ready For Research
@patch.object(gemini_service, "analyze_intent_and_reply")
def test_multiple_facts_in_one_message_stopping_condition(mock_gemini):
    mock_gemini.return_value = mock_ai_intent_result(
        intent=IntentCategory.TRADE_LICENCE,
        reply="Got all your trade licence details.",
        extracted_facts=[
            ExtractedFactItem(field_name="business_type", field_value="grocery shop", evidence="grocery shop"),
            ExtractedFactItem(field_name="business_location", field_value="Barrackpore", evidence="in Barrackpore"),
            ExtractedFactItem(field_name="application_type", field_value="new application", evidence="new application"),
        ],
    )
    res = client.post(
        "/api/chat",
        json={
            "conversation_id": None,
            "client_message_id": str(uuid.uuid4()),
            "message": "I need a new trade licence for my grocery shop in Barrackpore.",
        },
    )
    assert res.status_code == 200
    interview = res.json()["interview"]
    assert interview["interview_status"] == "ready_for_research"
    assert interview["next_action"] == "handoff_to_future_research"
    assert interview["missing_context"] == []
    # Assert anti-hallucination disclaimer is present
    assert "official verification" in res.json()["reply"].lower() or "milestone" in res.json()["reply"].lower()


# 8. Out of Order Answers Handled Gracefully
@patch.object(gemini_service, "analyze_intent_and_reply")
def test_out_of_order_answers(mock_gemini):
    # User provides application type (new) before location
    mock_gemini.return_value = mock_ai_intent_result(
        intent=IntentCategory.TRADE_LICENCE,
        reply="Understood, new application. Where is it located?",
        extracted_facts=[
            ExtractedFactItem(field_name="business_type", field_value="clothing shop", evidence="clothing shop"),
            ExtractedFactItem(field_name="application_type", field_value="new", evidence="first time applying"),
        ],
    )
    res = client.post(
        "/api/chat",
        json={
            "conversation_id": None,
            "client_message_id": str(uuid.uuid4()),
            "message": "It's my first time applying for a clothing shop trade licence.",
        },
    )
    assert res.status_code == 200
    interview = res.json()["interview"]
    assert interview["interview_status"] == "collecting_context"
    # Target field should adapt to missing business_location
    assert interview["target_field"] == "business_location"


# 9. Already Answered Questions Are Not Repeated
def test_already_answered_questions_not_repeated():
    known = {"business_type": "bakery", "business_location": "Salt Lake"}
    decision = question_planner.plan_decision(
        intent=IntentCategory.TRADE_LICENCE,
        known_facts=known,
    )
    assert decision.target_field == "application_type"
    assert decision.target_field != "business_location"
    assert decision.target_field != "business_type"


# 10. Distinct Facts: Residence Location vs Business Location
@patch.object(gemini_service, "analyze_intent_and_reply")
def test_distinct_residence_and_business_locations(mock_gemini):
    mock_gemini.return_value = mock_ai_intent_result(
        intent=IntentCategory.TRADE_LICENCE,
        reply="Noted your residence in Kolkata and shop in Barrackpore.",
        extracted_facts=[
            ExtractedFactItem(field_name="residence_location", field_value="Kolkata", evidence="I live in Kolkata"),
            ExtractedFactItem(field_name="business_location", field_value="Barrackpore", evidence="shop is in Barrackpore"),
        ],
    )
    res = client.post(
        "/api/chat",
        json={
            "conversation_id": None,
            "client_message_id": str(uuid.uuid4()),
            "message": "I live in Kolkata, but my father's shop is in Barrackpore.",
        },
    )
    assert res.status_code == 200
    conv_id = res.json()["conversation_id"]

    facts = memory_service.get_facts_dict(conv_id)
    assert facts.get("residence_location") == "Kolkata"
    assert facts.get("business_location") == "Barrackpore"


# 11. Explicit Corrections Reconciled
@patch.object(gemini_service, "analyze_intent_and_reply")
def test_explicit_corrections_in_interview(mock_gemini):
    # Turn 1
    mock_gemini.return_value = mock_ai_intent_result(
        intent=IntentCategory.TRADE_LICENCE,
        reply="Noted Kolkata.",
        extracted_facts=[
            ExtractedFactItem(field_name="business_location", field_value="Kolkata", evidence="Kolkata"),
        ],
    )
    res1 = client.post(
        "/api/chat",
        json={"conversation_id": None, "client_message_id": str(uuid.uuid4()), "message": "My shop is in Kolkata."},
    )
    conv_id = res1.json()["conversation_id"]

    # Turn 2: Correction
    mock_gemini.return_value = mock_ai_intent_result(
        intent=IntentCategory.TRADE_LICENCE,
        reply="Updated location to Howrah.",
        extracted_facts=[
            ExtractedFactItem(field_name="business_location", field_value="Howrah", evidence="Actually, it's in Howrah", is_correction=True),
        ],
    )
    res2 = client.post(
        "/api/chat",
        json={"conversation_id": conv_id, "client_message_id": str(uuid.uuid4()), "message": "Actually, it's in Howrah."},
    )
    facts2 = memory_service.get_facts_dict(conv_id)
    assert facts2.get("business_location") == "Howrah"


# 12. User Skips Question / Says "I don't know"
@patch.object(gemini_service, "analyze_intent_and_reply")
def test_user_skips_question(mock_gemini):
    # Turn 1: Establish intent and ask for location
    mock_gemini.return_value = mock_ai_intent_result(
        intent=IntentCategory.TRADE_LICENCE,
        reply="Which municipality is the shop in?",
        extracted_facts=[
            ExtractedFactItem(field_name="business_type", field_value="stationery", evidence="stationery"),
        ],
    )
    res1 = client.post(
        "/api/chat",
        json={"conversation_id": None, "client_message_id": str(uuid.uuid4()), "message": "Trade licence for stationery shop."},
    )
    conv_id = res1.json()["conversation_id"]
    assert res1.json()["interview"]["target_field"] == "business_location"

    # Turn 2: User says "I don't know"
    mock_gemini.return_value = mock_ai_intent_result(
        intent=IntentCategory.TRADE_LICENCE,
        reply="No problem, we can determine the municipality later. Is this a new application?",
        extracted_facts=[],
    )
    res2 = client.post(
        "/api/chat",
        json={"conversation_id": conv_id, "client_message_id": str(uuid.uuid4()), "message": "I don't know the municipality."},
    )
    interview2 = res2.json()["interview"]
    # The previously targeted field "business_location" should now be in skipped_fields
    assert "business_location" in interview2["skipped_fields"]
    # And the engine advances to next field (application_type)
    assert interview2["target_field"] == "application_type"


# 13. User Requests Pause
@patch.object(gemini_service, "analyze_intent_and_reply")
def test_user_requests_pause(mock_gemini):
    mock_gemini.return_value = mock_ai_intent_result(
        intent=IntentCategory.TRADE_LICENCE,
        reply="Understood, pausing.",
    )
    res = client.post(
        "/api/chat",
        json={
            "conversation_id": None,
            "client_message_id": str(uuid.uuid4()),
            "message": "Let's pause for now.",
        },
    )
    assert res.status_code == 200
    interview = res.json()["interview"]
    assert interview["interview_status"] == "paused"
    assert interview["next_action"] == "pause_interview"


# 14. User Changes Topic Naturally
@patch.object(gemini_service, "analyze_intent_and_reply")
def test_user_changes_topic(mock_gemini):
    # Turn 1: Trade licence
    mock_gemini.return_value = mock_ai_intent_result(
        intent=IntentCategory.TRADE_LICENCE,
        reply="Trade licence acknowledged.",
        extracted_facts=[ExtractedFactItem(field_name="business_type", field_value="bakery", evidence="bakery")],
    )
    res1 = client.post(
        "/api/chat",
        json={"conversation_id": None, "client_message_id": str(uuid.uuid4()), "message": "I need a trade licence."},
    )
    conv_id = res1.json()["conversation_id"]
    assert res1.json()["interview"]["current_intent"] == "trade_licence"

    # Turn 2: Pivot to FSSAI
    mock_gemini.return_value = mock_ai_intent_result(
        intent=IntentCategory.FSSAI_REGISTRATION,
        reply="Switching to FSSAI registration.",
        extracted_facts=[],
    )
    res2 = client.post(
        "/api/chat",
        json={"conversation_id": conv_id, "client_message_id": str(uuid.uuid4()), "message": "Actually tell me about FSSAI registration."},
    )
    assert res2.json()["interview"]["current_intent"] == "fssai_registration"


# 15. Persistence of Interview State Across Session Reload
@patch.object(gemini_service, "analyze_intent_and_reply")
def test_interview_state_persistence(mock_gemini):
    mock_gemini.return_value = mock_ai_intent_result(
        intent=IntentCategory.TRADE_LICENCE,
        reply="Noted.",
        extracted_facts=[ExtractedFactItem(field_name="business_type", field_value="electronics", evidence="electronics")],
    )
    res = client.post(
        "/api/chat",
        json={"conversation_id": None, "client_message_id": str(uuid.uuid4()), "message": "I have an electronics shop."},
    )
    conv_id = res.json()["conversation_id"]

    # Restore via GET /api/conversations/{id}
    detail_res = client.get(f"/api/conversations/{conv_id}")
    assert detail_res.status_code == 200
    interview_data = detail_res.json()["interview"]
    assert interview_data["current_intent"] == "trade_licence"
    assert "business_type" in interview_data["known_fields"]
