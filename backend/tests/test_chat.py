import uuid
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient

from main import app
from app.schemas.chat import (
    IntentCategory,
    IntentStatus,
    NextAction,
    ServiceSupport,
    StructuredIntentResult,
    KnownInformation,
)
from app.services.session_service import session_manager
from app.services.gemini_service import gemini_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_sessions():
    """Ensure in-memory sessions are reset between tests."""
    session_manager.clear_all()
    yield
    session_manager.clear_all()


def mock_ai_reply(text: str = "Test response from Gemini AI"):
    return StructuredIntentResult(
        intent=IntentCategory.WB_INCOME_CERTIFICATE,
        intent_status=IntentStatus.IDENTIFIED,
        service_support=ServiceSupport.SUPPORTED_MVP,
        known_information=KnownInformation(),
        missing_information=[],
        next_action=NextAction.ACKNOWLEDGE_INTENT,
        reply=text,
    )


@patch.object(gemini_service, "analyze_intent_and_reply")
def test_new_session_creation(mock_gemini):
    mock_gemini.return_value = mock_ai_reply("I can help with your income certificate.")
    client_msg_id = str(uuid.uuid4())
    payload = {
        "conversation_id": None,
        "client_message_id": client_msg_id,
        "message": "I need an income certificate for college admission.",
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert "conversation_id" in data
    assert uuid.UUID(data["conversation_id"])  # must be valid UUID
    assert "message_id" in data
    assert uuid.UUID(data["message_id"])
    assert data["mode"] == "gemini"
    assert "income certificate" in data["reply"].lower()
    assert "intent" in data


@patch.object(gemini_service, "analyze_intent_and_reply")
def test_follow_up_message_reuses_conversation_id(mock_gemini):
    mock_gemini.return_value = mock_ai_reply("Trade licence acknowledged.")
    # 1. First message
    client_msg_id_1 = str(uuid.uuid4())
    payload_1 = {
        "conversation_id": None,
        "client_message_id": client_msg_id_1,
        "message": "I want a trade licence for my grocery shop.",
    }
    res_1 = client.post("/api/chat", json=payload_1)
    assert res_1.status_code == 200
    conv_id = res_1.json()["conversation_id"]

    # 2. Follow-up message
    mock_gemini.return_value = mock_ai_reply("Location Kolkata recorded.")
    client_msg_id_2 = str(uuid.uuid4())
    payload_2 = {
        "conversation_id": conv_id,
        "client_message_id": client_msg_id_2,
        "message": "My shop is located in Kolkata municipal area.",
    }
    res_2 = client.post("/api/chat", json=payload_2)
    assert res_2.status_code == 200
    assert res_2.json()["conversation_id"] == conv_id

    # 3. Verify chronological order in session
    session = session_manager.get_session(conv_id)
    assert session is not None
    assert len(session["messages"]) == 4  # 2 user messages + 2 assistant replies
    assert session["messages"][0]["role"] == "user"
    assert session["messages"][0]["content"] == payload_1["message"]
    assert session["messages"][1]["role"] == "assistant"
    assert session["messages"][2]["role"] == "user"
    assert session["messages"][2]["content"] == payload_2["message"]
    assert session["messages"][3]["role"] == "assistant"


@patch.object(gemini_service, "analyze_intent_and_reply")
def test_independent_sessions_isolation(mock_gemini):
    mock_gemini.return_value = mock_ai_reply("Session response")
    # Session A
    res_a = client.post("/api/chat", json={
        "conversation_id": None,
        "client_message_id": str(uuid.uuid4()),
        "message": "Message for Session A"
    })
    conv_a = res_a.json()["conversation_id"]

    # Session B
    res_b = client.post("/api/chat", json={
        "conversation_id": None,
        "client_message_id": str(uuid.uuid4()),
        "message": "Message for Session B"
    })
    conv_b = res_b.json()["conversation_id"]

    assert conv_a != conv_b

    session_a = session_manager.get_session(conv_a)
    session_b = session_manager.get_session(conv_b)

    assert len(session_a["messages"]) == 2
    assert len(session_b["messages"]) == 2
    assert session_a["messages"][0]["content"] == "Message for Session A"
    assert session_b["messages"][0]["content"] == "Message for Session B"


def test_invalid_input_handling():
    # Empty message
    res_empty = client.post("/api/chat", json={
        "conversation_id": None,
        "client_message_id": str(uuid.uuid4()),
        "message": ""
    })
    assert res_empty.status_code == 422

    # Whitespace-only message
    res_whitespace = client.post("/api/chat", json={
        "conversation_id": None,
        "client_message_id": str(uuid.uuid4()),
        "message": "   \n\t  "
    })
    assert res_whitespace.status_code == 422

    # Missing client_message_id
    res_missing_id = client.post("/api/chat", json={
        "conversation_id": None,
        "message": "Valid text"
    })
    assert res_missing_id.status_code == 422

    # Message exceeding 4000 characters
    res_too_long = client.post("/api/chat", json={
        "conversation_id": None,
        "client_message_id": str(uuid.uuid4()),
        "message": "x" * 4001
    })
    assert res_too_long.status_code == 422


def test_unknown_session_returns_404():
    unknown_id = str(uuid.uuid4())
    res = client.post("/api/chat", json={
        "conversation_id": unknown_id,
        "client_message_id": str(uuid.uuid4()),
        "message": "Hello to unknown session"
    })
    assert res.status_code == 404
    data = res.json()
    assert "detail" in data
    assert "not found or expired" in data["detail"].lower()


@patch.object(gemini_service, "analyze_intent_and_reply")
def test_duplicate_request_idempotency(mock_gemini):
    mock_gemini.return_value = mock_ai_reply("First answer")
    client_msg_id = str(uuid.uuid4())
    payload = {
        "conversation_id": None,
        "client_message_id": client_msg_id,
        "message": "Duplicate check message.",
    }

    # First request
    res_1 = client.post("/api/chat", json=payload)
    assert res_1.status_code == 200
    data_1 = res_1.json()
    conv_id = data_1["conversation_id"]
    msg_id_1 = data_1["message_id"]

    # Retry same request with same client_message_id and conv_id
    retry_payload = {
        "conversation_id": conv_id,
        "client_message_id": client_msg_id,
        "message": "Duplicate check message.",
    }
    res_2 = client.post("/api/chat", json=retry_payload)
    assert res_2.status_code == 200
    data_2 = res_2.json()

    # Must return exact same message_id
    assert data_2["conversation_id"] == conv_id
    assert data_2["message_id"] == msg_id_1

    # Must not duplicate messages in session history
    session = session_manager.get_session(conv_id)
    assert len(session["messages"]) == 2  # exactly 1 user + 1 assistant
