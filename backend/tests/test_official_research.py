import uuid
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from main import app
from app.db.database import get_db, init_db
from app.schemas.chat import IntentCategory, StructuredIntentResult, NextAction, IntentStatus, ServiceSupport
from app.services.research_service import research_service, OFFICIAL_RESEARCH_DATABASE
from app.services.gemini_service import gemini_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    init_db()
    with get_db() as db:
        db.execute("DELETE FROM applicant_facts")
        db.execute("DELETE FROM messages")
        db.execute("DELETE FROM conversations")
    yield
    with get_db() as db:
        db.execute("DELETE FROM applicant_facts")
        db.execute("DELETE FROM messages")
        db.execute("DELETE FROM conversations")


def test_official_research_database_completeness():
    """Verifies that all targeted services have verified links, authorities, and checklists."""
    targeted_services = [
        IntentCategory.WB_DOMICILE_CERTIFICATE.value,
        IntentCategory.WB_INCOME_CERTIFICATE.value,
        IntentCategory.TRADE_LICENCE.value,
        IntentCategory.FSSAI_REGISTRATION.value,
        IntentCategory.FOOD_BUSINESS_SETUP.value,
    ]

    for s_id in targeted_services:
        res = research_service.get_service_research(s_id)
        assert res is not None, f"Service '{s_id}' missing in OFFICIAL_RESEARCH_DATABASE"
        assert res.title
        assert res.issuing_authority
        assert res.jurisdiction
        assert res.official_portal_url.startswith("https://")
        assert len(res.required_documents) >= 3, f"Insufficient document checklist for '{s_id}'"
        assert len(res.official_links) >= 1, f"Missing official links for '{s_id}'"
        for link in res.official_links:
            assert link.title
            assert link.url.startswith("https://")


def test_research_context_prompt_formatting():
    """Verifies prompt context generation includes official portal URLs and documents."""
    text = research_service.format_research_context_for_prompt(IntentCategory.WB_DOMICILE_CERTIFICATE)
    assert "https://kolkatacollectorate.wb.gov.in/domicile-certificate/" in text
    assert "Kolkata Collectorate" in text
    assert "Proof of continuous residence" in text
    assert "Verified Required Documents Checklist" in text


def mock_ai_intent_result(intent=IntentCategory.WB_DOMICILE_CERTIFICATE, reply="Official guidance"):
    return StructuredIntentResult(
        intent=intent,
        intent_status=IntentStatus.IDENTIFIED,
        service_support=ServiceSupport.SUPPORTED_MVP,
        missing_information=[],
        next_action=NextAction.ACKNOWLEDGE_INTENT,
        extracted_facts=[],
        reply=reply,
    )


@patch.object(gemini_service, "analyze_intent_and_reply")
def test_chat_response_contains_official_resources(mock_gemini):
    """Verifies /api/chat returns structured official_resources matching intent."""
    mock_gemini.return_value = mock_ai_intent_result(
        intent=IntentCategory.WB_DOMICILE_CERTIFICATE,
        reply="Here are the official links and documents for West Bengal domicile.",
    )
    res = client.post(
        "/api/chat",
        json={
            "conversation_id": None,
            "client_message_id": str(uuid.uuid4()),
            "message": "Where can I apply for a West Bengal domicile certificate online and what documents do I need?",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["official_resources"] is not None
    res_obj = data["official_resources"]
    assert res_obj["service_id"] == "wb_domicile_certificate"
    assert "kolkatacollectorate.wb.gov.in" in res_obj["official_portal_url"]
    assert len(res_obj["required_documents"]) >= 4
    assert len(res_obj["official_links"]) >= 2


@patch.object(gemini_service, "analyze_intent_and_reply")
def test_conversation_detail_includes_official_resources(mock_gemini):
    """Verifies GET /api/conversations/{id} returns official_resources for persisted intent."""
    mock_gemini.return_value = mock_ai_intent_result(
        intent=IntentCategory.WB_INCOME_CERTIFICATE,
        reply="I can guide you on the WB income certificate requirements.",
    )
    first_res = client.post(
        "/api/chat",
        json={
            "conversation_id": None,
            "client_message_id": str(uuid.uuid4()),
            "message": "I need an income certificate for college admission in West Bengal.",
        },
    )
    assert first_res.status_code == 200
    conv_id = first_res.json()["conversation_id"]

    detail_res = client.get(f"/api/conversations/{conv_id}")
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["official_resources"] is not None
    assert detail["official_resources"]["service_id"] == "wb_income_certificate"
    assert "edistrict.wb.gov.in" in detail["official_resources"]["official_portal_url"]


@patch.object(gemini_service, "analyze_intent_and_reply")
def test_official_resources_omitted_during_routine_interview_turns(mock_gemini):
    """Verifies official_resources card is NOT attached during routine interview Q&A turns to avoid clutter."""
    mock_gemini.return_value = StructuredIntentResult(
        intent=IntentCategory.WB_DOMICILE_CERTIFICATE,
        intent_status=IntentStatus.IDENTIFIED,
        service_support=ServiceSupport.SUPPORTED_MVP,
        missing_information=["father_name", "date_of_birth"],
        next_action=NextAction.ASK_CLARIFICATION,
        extracted_facts=[],
        reply="What is your father's name?",
    )
    res = client.post(
        "/api/chat",
        json={
            "conversation_id": None,
            "client_message_id": str(uuid.uuid4()),
            "message": "My name is Subham Ghosh.",
        },
    )
    assert res.status_code == 200
    data = res.json()
    # During normal conversational fact collection, card is omitted
    assert data["official_resources"] is None


def test_probable_research_for_general_services():
    """Verifies open-to-all civic services return probable guidance with is_verified=False."""
    services = ["passport_services", "driving_licence", "pan_card", "voter_id", "aadhaar_services"]
    for s in services:
        res = research_service.get_service_research(s)
        assert res is not None, f"Service '{s}' missing"
        assert res.is_verified is False
        assert res.verification_badge == "Probable Official Guidance"
        assert res.disclaimer is not None
        assert res.official_portal_url.startswith("https://")
        assert len(res.required_documents) >= 2


@patch.object(gemini_service, "analyze_intent_and_reply")
def test_open_civic_chatbot_passport_guidance(mock_gemini):
    """Verifies that citizen queries for passport return probable guidance rather than being blocked."""
    mock_gemini.return_value = mock_ai_intent_result(
        intent=IntentCategory.PASSPORT_SERVICES,
        reply="You can apply for an Indian passport on the official Passport Seva portal.",
    )
    res = client.post(
        "/api/chat",
        json={
            "conversation_id": None,
            "client_message_id": str(uuid.uuid4()),
            "message": "What is the official website and documents needed for Indian passport renewal?",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["official_resources"] is not None
    res_obj = data["official_resources"]
    assert res_obj["service_id"] == "passport_services"
    assert res_obj["is_verified"] is False
    assert res_obj["verification_badge"] == "Probable Official Guidance"
    assert "passportindia.gov.in" in res_obj["official_portal_url"]

