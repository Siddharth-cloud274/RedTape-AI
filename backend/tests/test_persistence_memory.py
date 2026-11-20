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
from app.services.gemini_service import gemini_service
from app.schemas.chat import (
    IntentCategory,
    IntentStatus,
    ServiceSupport,
    NextAction,
    KnownInformation,
    StructuredIntentResult,
)
from app.schemas.facts import ExtractedFactItem

client = TestClient(app)


@pytest.fixture(autouse=True)
def ensure_fresh_db():
    """Ensure DB schema is initialized before each test."""
    init_db()


def make_mock_result(
    intent=IntentCategory.WB_INCOME_CERTIFICATE,
    intent_status=IntentStatus.IDENTIFIED,
    reply="Understood.",
    extracted_facts=None,
):
    return StructuredIntentResult(
        intent=intent,
        intent_status=intent_status,
        service_support=ServiceSupport.SUPPORTED_MVP,
        known_information=KnownInformation(location="Kolkata"),
        missing_information=[],
        next_action=NextAction.ASK_CLARIFICATION,
        reply=reply,
        extracted_facts=extracted_facts or [],
    )


# 1. SQLite Persistence
@patch.object(gemini_service, "analyze_intent_and_reply")
def test_conversation_creation_and_sqlite_persistence(mock_gemini):
    client_msg_id = str(uuid.uuid4())
    mock_gemini.return_value = make_mock_result(
        reply="I can help you apply for a West Bengal income certificate.",
        extracted_facts=[
            ExtractedFactItem(
                field_name="location",
                field_value="Kolkata",
                evidence="I live in Kolkata",
                is_correction=False,
            )
        ],
    )

    response = client.post(
        "/api/chat",
        json={
            "conversation_id": None,
            "client_message_id": client_msg_id,
            "message": "I need an income certificate. I live in Kolkata.",
        },
    )
    assert response.status_code == 200
    data = response.json()
    conv_id = data["conversation_id"]

    # Verify directly in SQLite
    with get_db() as db:
        conv_row = db.execute("SELECT * FROM conversations WHERE id = ?", (conv_id,)).fetchone()
        assert conv_row is not None
        assert conv_row["current_intent"] == "wb_income_certificate"

        msg_rows = db.execute(
            "SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at ASC, rowid ASC",
            (conv_id,),
        ).fetchall()
        assert len(msg_rows) == 2
        assert msg_rows[0]["role"] == "user"
        assert msg_rows[0]["client_message_id"] == client_msg_id
        assert msg_rows[1]["role"] == "assistant"

        fact_rows = db.execute("SELECT * FROM applicant_facts WHERE conversation_id = ?", (conv_id,)).fetchall()
        assert len(fact_rows) == 1
        assert fact_rows[0]["field_name"] == "location"
        assert fact_rows[0]["field_value"] == "Kolkata"


# 2. Server Restart Restoration
@patch.object(gemini_service, "analyze_intent_and_reply")
def test_server_restart_restoration(mock_gemini):
    mock_gemini.return_value = make_mock_result(reply="Saved.")
    res = client.post(
        "/api/chat",
        json={
            "conversation_id": None,
            "client_message_id": str(uuid.uuid4()),
            "message": "Hello, this is a test session.",
        },
    )
    conv_id = res.json()["conversation_id"]

    # Simulate fresh server startup by instantiating a completely new SessionManager
    fresh_session_manager = SessionManager()
    detail = fresh_session_manager.get_conversation_detail(conv_id)
    assert detail.conversation_id == conv_id
    assert len(detail.messages) == 2
    assert detail.messages[0].content == "Hello, this is a test session."

    # Test via GET /api/conversations/{conversation_id} endpoint
    get_res = client.get(f"/api/conversations/{conv_id}")
    assert get_res.status_code == 200
    api_data = get_res.json()
    assert api_data["conversation_id"] == conv_id
    assert len(api_data["messages"]) == 2


# 3. Fact Extraction with Evidence
@patch.object(gemini_service, "analyze_intent_and_reply")
def test_fact_extraction_with_evidence(mock_gemini):
    conv_id = None
    mock_gemini.return_value = make_mock_result(
        reply="Annual turnover recorded.",
        extracted_facts=[
            ExtractedFactItem(
                field_name="annual_turnover",
                field_value="Rs. 8 lakhs",
                evidence="my turnover is 8 lakhs",
                is_correction=False,
            )
        ],
    )

    res = client.post(
        "/api/chat",
        json={
            "conversation_id": conv_id,
            "client_message_id": str(uuid.uuid4()),
            "message": "I run a grocery store and my turnover is 8 lakhs.",
        },
    )
    conv_id = res.json()["conversation_id"]

    facts = res.json().get("facts", [])
    assert len(facts) >= 1
    turnover_fact = next(f for f in facts if f["field_name"] == "annual_turnover")
    assert turnover_fact["field_value"] == "Rs. 8 lakhs"
    assert turnover_fact["evidence"] == "my turnover is 8 lakhs"
    assert turnover_fact["confidence_status"] == "confirmed"


# 4. Deterministic Missing Information Tracking
def test_missing_information_deterministic_tracking():
    # Test WB Income Certificate missing fields
    missing_income_0 = context_tracker.calculate_missing_fields(
        IntentCategory.WB_INCOME_CERTIFICATE, {}
    )
    assert "location" in missing_income_0
    assert "application_purpose" in missing_income_0

    # Supply location
    missing_income_1 = context_tracker.calculate_missing_fields(
        IntentCategory.WB_INCOME_CERTIFICATE, {"location": "Kolkata"}
    )
    assert "location" not in missing_income_1
    assert "application_purpose" in missing_income_1

    # Supply all required
    missing_income_full = context_tracker.calculate_missing_fields(
        IntentCategory.WB_INCOME_CERTIFICATE,
        {"location": "Kolkata", "application_purpose": "College admission scholarship"},
    )
    assert len(missing_income_full) == 0


# 5. Fact Correction Reconciliation
@patch.object(gemini_service, "analyze_intent_and_reply")
def test_fact_correction_reconciliation(mock_gemini):
    # Turn 1: Citizen says Kolkata
    mock_gemini.return_value = make_mock_result(
        reply="Noted Kolkata.",
        extracted_facts=[
            ExtractedFactItem(
                field_name="location",
                field_value="Kolkata",
                evidence="I am in Kolkata",
                is_correction=False,
            )
        ],
    )
    res_1 = client.post(
        "/api/chat",
        json={
            "conversation_id": None,
            "client_message_id": str(uuid.uuid4()),
            "message": "I am in Kolkata and need an income certificate.",
        },
    )
    conv_id = res_1.json()["conversation_id"]

    # Turn 2: Citizen corrects to Howrah
    mock_gemini.return_value = make_mock_result(
        reply="Updated your location to Howrah.",
        extracted_facts=[
            ExtractedFactItem(
                field_name="location",
                field_value="Howrah",
                evidence="Actually, I live in Howrah",
                is_correction=True,
            )
        ],
    )
    res_2 = client.post(
        "/api/chat",
        json={
            "conversation_id": conv_id,
            "client_message_id": str(uuid.uuid4()),
            "message": "Actually, I live in Howrah.",
        },
    )
    facts_2 = res_2.json()["facts"]
    loc_fact = next(f for f in facts_2 if f["field_name"] == "location")
    assert loc_fact["field_value"] == "Howrah"

    # Verify no duplicate location facts in DB for this conversation
    with get_db() as db:
        loc_rows = db.execute(
            "SELECT * FROM applicant_facts WHERE conversation_id = ? AND field_name = 'location'",
            (conv_id,),
        ).fetchall()
        assert len(loc_rows) == 1
        assert loc_rows[0]["field_value"] == "Howrah"


# 6. Multi-Conversation Fact Isolation
@patch.object(gemini_service, "analyze_intent_and_reply")
def test_multi_conversation_fact_isolation(mock_gemini):
    # Conv A: Siliguri
    mock_gemini.return_value = make_mock_result(
        reply="Recorded Siliguri.",
        extracted_facts=[
            ExtractedFactItem(
                field_name="location",
                field_value="Siliguri",
                evidence="Siliguri resident",
                is_correction=False,
            )
        ],
    )
    res_a = client.post(
        "/api/chat",
        json={
            "conversation_id": None,
            "client_message_id": str(uuid.uuid4()),
            "message": "Siliguri resident needing domicile.",
        },
    )
    conv_a = res_a.json()["conversation_id"]

    # Conv B: Asansol
    mock_gemini.return_value = make_mock_result(
        reply="Recorded Asansol.",
        extracted_facts=[
            ExtractedFactItem(
                field_name="location",
                field_value="Asansol",
                evidence="Asansol resident",
                is_correction=False,
            )
        ],
    )
    res_b = client.post(
        "/api/chat",
        json={
            "conversation_id": None,
            "client_message_id": str(uuid.uuid4()),
            "message": "Asansol resident needing income certificate.",
        },
    )
    conv_b = res_b.json()["conversation_id"]

    assert conv_a != conv_b

    # Verify facts are cleanly isolated
    facts_a = memory_service.get_facts_dict(conv_a)
    facts_b = memory_service.get_facts_dict(conv_b)
    assert facts_a.get("location") == "Siliguri"
    assert facts_b.get("location") == "Asansol"


# 7. Idempotency Retry with Persisted State
@patch.object(gemini_service, "analyze_intent_and_reply")
def test_idempotency_retry_with_persisted_state(mock_gemini):
    mock_gemini.return_value = make_mock_result(reply="Idempotent test reply.")
    client_msg_id = str(uuid.uuid4())

    payload = {
        "conversation_id": None,
        "client_message_id": client_msg_id,
        "message": "First transmission attempt.",
    }
    res_1 = client.post("/api/chat", json=payload)
    assert res_1.status_code == 200
    conv_id = res_1.json()["conversation_id"]
    msg_id = res_1.json()["message_id"]

    # Retry identical client_message_id
    retry_payload = {
        "conversation_id": conv_id,
        "client_message_id": client_msg_id,
        "message": "First transmission attempt.",
    }
    res_2 = client.post("/api/chat", json=retry_payload)
    assert res_2.status_code == 200
    assert res_2.json()["conversation_id"] == conv_id
    assert res_2.json()["message_id"] == msg_id

    # Verify only 1 user message and 1 assistant message in SQLite
    with get_db() as db:
        rows = db.execute(
            "SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at ASC",
            (conv_id,),
        ).fetchall()
        assert len(rows) == 2


# 8. GET /api/conversations/{id} 404 for Unknown ID
def test_get_conversation_endpoint_404_on_unknown():
    unknown_id = str(uuid.uuid4())
    res = client.get(f"/api/conversations/{unknown_id}")
    assert res.status_code == 404
    assert f"Conversation '{unknown_id}' not found." in res.json()["detail"]
