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
from app.services.gemini_service import GeminiServiceError, gemini_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_sessions():
    """Ensure in-memory sessions are reset between tests."""
    session_manager.clear_all()
    yield
    session_manager.clear_all()


def make_mock_result(
    intent: IntentCategory,
    status: IntentStatus = IntentStatus.IDENTIFIED,
    support: ServiceSupport = ServiceSupport.SUPPORTED_MVP,
    action: NextAction = NextAction.ACKNOWLEDGE_INTENT,
    reply: str = "Test response from RedTape AI",
    known_info: dict = None,
    missing_info: list = None,
) -> StructuredIntentResult:
    info_obj = KnownInformation(**(known_info or {}))
    return StructuredIntentResult(
        intent=intent,
        intent_status=status,
        service_support=support,
        known_information=info_obj,
        missing_information=missing_info or [],
        next_action=action,
        reply=reply,
    )


# Test 1: Income certificate intent
@patch.object(gemini_service, "analyze_intent_and_reply")
def test_income_certificate_intent(mock_gemini):
    mock_gemini.return_value = make_mock_result(
        intent=IntentCategory.WB_INCOME_CERTIFICATE,
        reply="I can help you with the West Bengal income certificate application guidance.",
    )

    res = client.post("/api/chat", json={
        "conversation_id": None,
        "client_message_id": str(uuid.uuid4()),
        "message": "I need an income certificate for college admission.",
    })

    assert res.status_code == 200
    data = res.json()
    assert data["mode"] == "gemini"
    assert data["intent"]["intent"] == "wb_income_certificate"
    assert data["intent"]["service_support"] == "supported_mvp"
    assert "income certificate" in data["reply"].lower()


# Test 2: Domicile certificate intent
@patch.object(gemini_service, "analyze_intent_and_reply")
def test_domicile_certificate_intent(mock_gemini):
    mock_gemini.return_value = make_mock_result(
        intent=IntentCategory.WB_DOMICILE_CERTIFICATE,
        reply="I can help you understand the requirements for a West Bengal domicile certificate.",
    )

    res = client.post("/api/chat", json={
        "conversation_id": None,
        "client_message_id": str(uuid.uuid4()),
        "message": "I need a domicile certificate in West Bengal.",
    })

    assert res.status_code == 200
    data = res.json()
    assert data["mode"] == "gemini"
    assert data["intent"]["intent"] == "wb_domicile_certificate"
    assert data["intent"]["service_support"] == "supported_mvp"


# Test 3: FSSAI registration intent
@patch.object(gemini_service, "analyze_intent_and_reply")
def test_fssai_registration_intent(mock_gemini):
    mock_gemini.return_value = make_mock_result(
        intent=IntentCategory.FSSAI_REGISTRATION,
        reply="I can guide you on FSSAI food business registration under FoSCoS.",
    )

    res = client.post("/api/chat", json={
        "conversation_id": None,
        "client_message_id": str(uuid.uuid4()),
        "message": "I want an FSSAI food safety license for my packaged snacks.",
    })

    assert res.status_code == 200
    data = res.json()
    assert data["mode"] == "gemini"
    assert data["intent"]["intent"] == "fssai_registration"
    assert data["intent"]["service_support"] == "supported_mvp"


# Test 4: Trade licence intent recognized separately from FSSAI
@patch.object(gemini_service, "analyze_intent_and_reply")
def test_trade_licence_distinct_from_fssai(mock_gemini):
    mock_gemini.return_value = make_mock_result(
        intent=IntentCategory.TRADE_LICENCE,
        status=IntentStatus.IDENTIFIED,
        support=ServiceSupport.RECOGNIZED_NOT_IMPLEMENTED,
        action=NextAction.ACKNOWLEDGE_INTENT,
        reply="A trade licence is issued by your local municipality or gram panchayat to operate a commercial establishment.",
    )

    res = client.post("/api/chat", json={
        "conversation_id": None,
        "client_message_id": str(uuid.uuid4()),
        "message": "I need a trade licence for my hardware shop in Howrah.",
    })

    assert res.status_code == 200
    data = res.json()
    assert data["intent"]["intent"] == "trade_licence"
    assert data["intent"]["intent"] != "fssai_registration"
    assert data["intent"]["service_support"] == "recognized_not_implemented"


# Test 5: Ambiguous request triggers clarification
@patch.object(gemini_service, "analyze_intent_and_reply")
def test_ambiguous_request_clarification(mock_gemini):
    mock_gemini.return_value = make_mock_result(
        intent=IntentCategory.UNCLEAR,
        status=IntentStatus.NEEDS_CLARIFICATION,
        support=ServiceSupport.UNDETERMINED,
        action=NextAction.ASK_CLARIFICATION,
        reply="Which specific certificate or official procedure do you need assistance with?",
        missing_info=["certificate_type", "purpose"],
    )

    res = client.post("/api/chat", json={
        "conversation_id": None,
        "client_message_id": str(uuid.uuid4()),
        "message": "I need some government papers.",
    })

    assert res.status_code == 200
    data = res.json()
    assert data["intent"]["intent"] == "unclear"
    assert data["intent"]["intent_status"] == "needs_clarification"
    assert data["intent"]["next_action"] == "ask_clarification"


# Test 6: Unsupported service handling
@patch.object(gemini_service, "analyze_intent_and_reply")
def test_unsupported_service(mock_gemini):
    mock_gemini.return_value = make_mock_result(
        intent=IntentCategory.UNSUPPORTED,
        status=IntentStatus.UNSUPPORTED,
        support=ServiceSupport.UNSUPPORTED,
        action=NextAction.EXPLAIN_LIMITATION,
        reply="Currently, RedTape AI focuses on West Bengal certificates and FSSAI registrations. Passport services are not yet supported.",
    )

    res = client.post("/api/chat", json={
        "conversation_id": None,
        "client_message_id": str(uuid.uuid4()),
        "message": "I want to apply for an Indian passport renewal.",
    })

    assert res.status_code == 200
    data = res.json()
    assert data["intent"]["intent"] == "unsupported"
    assert data["intent"]["service_support"] == "unsupported"
    assert data["intent"]["next_action"] == "explain_limitation"


# Test 7: Follow-up message using prior context
@patch.object(gemini_service, "analyze_intent_and_reply")
def test_multi_turn_context_retention(mock_gemini):
    # Turn 1
    mock_gemini.return_value = make_mock_result(
        intent=IntentCategory.WB_INCOME_CERTIFICATE,
        reply="What is your location or municipality in West Bengal?",
    )
    res_1 = client.post("/api/chat", json={
        "conversation_id": None,
        "client_message_id": str(uuid.uuid4()),
        "message": "I need an income certificate.",
    })
    conv_id = res_1.json()["conversation_id"]

    # Turn 2: User provides location in context
    mock_gemini.return_value = make_mock_result(
        intent=IntentCategory.WB_INCOME_CERTIFICATE,
        known_info={"location": "Kolkata"},
        reply="Got it, you are applying from Kolkata for your income certificate.",
    )
    res_2 = client.post("/api/chat", json={
        "conversation_id": conv_id,
        "client_message_id": str(uuid.uuid4()),
        "message": "I live in Kolkata.",
    })

    assert res_2.status_code == 200
    assert res_2.json()["conversation_id"] == conv_id
    assert res_2.json()["intent"]["intent"] == "wb_income_certificate"
    # Ensure history was sent to gemini_service
    call_args = mock_gemini.call_args
    assert len(call_args.kwargs["history"]) == 2


# Test 8: Independent conversations isolation
@patch.object(gemini_service, "analyze_intent_and_reply")
def test_independent_conversations_isolation(mock_gemini):
    mock_gemini.return_value = make_mock_result(intent=IntentCategory.WB_INCOME_CERTIFICATE)
    res_a = client.post("/api/chat", json={
        "conversation_id": None,
        "client_message_id": str(uuid.uuid4()),
        "message": "Session A request",
    })
    conv_a = res_a.json()["conversation_id"]

    mock_gemini.return_value = make_mock_result(intent=IntentCategory.TRADE_LICENCE)
    res_b = client.post("/api/chat", json={
        "conversation_id": None,
        "client_message_id": str(uuid.uuid4()),
        "message": "Session B request",
    })
    conv_b = res_b.json()["conversation_id"]

    assert conv_a != conv_b
    assert session_manager.get_session(conv_a)["messages"][0]["content"] == "Session A request"
    assert session_manager.get_session(conv_b)["messages"][0]["content"] == "Session B request"


# Test 9: Invalid structured model response handled safely
@patch.object(gemini_service, "analyze_intent_and_reply")
def test_invalid_structured_model_response(mock_gemini):
    mock_gemini.side_effect = GeminiServiceError("Failed to parse structured model response", status_code=502)

    res = client.post("/api/chat", json={
        "conversation_id": None,
        "client_message_id": str(uuid.uuid4()),
        "message": "Test malformed output",
    })

    assert res.status_code == 502
    assert "parse structured model response" in res.json()["detail"]


# Test 10: Missing API key handling
@patch.object(gemini_service, "analyze_intent_and_reply")
def test_missing_api_key_handling(mock_gemini):
    mock_gemini.side_effect = GeminiServiceError("Gemini API key is not configured on the backend.", status_code=503)

    res = client.post("/api/chat", json={
        "conversation_id": None,
        "client_message_id": str(uuid.uuid4()),
        "message": "Check missing key",
    })

    assert res.status_code == 503
    assert "Gemini API key is not configured" in res.json()["detail"]


# Test 11: Model timeout handling
@patch.object(gemini_service, "analyze_intent_and_reply")
def test_model_timeout_handling(mock_gemini):
    mock_gemini.side_effect = GeminiServiceError("Request to Gemini API timed out.", status_code=504)

    res = client.post("/api/chat", json={
        "conversation_id": None,
        "client_message_id": str(uuid.uuid4()),
        "message": "Test timeout",
    })

    assert res.status_code == 504
    assert "timed out" in res.json()["detail"]


# Test 12: API rate limit (429) handling
@patch.object(gemini_service, "analyze_intent_and_reply")
def test_api_rate_limit_handling(mock_gemini):
    mock_gemini.side_effect = GeminiServiceError("Gemini API rate limit or quota exceeded. Please wait a moment and retry.", status_code=429)

    res = client.post("/api/chat", json={
        "conversation_id": None,
        "client_message_id": str(uuid.uuid4()),
        "message": "Test rate limit",
    })

    assert res.status_code == 429
    assert "rate limit or quota" in res.json()["detail"]


# Test 13: Failed request and retry
@patch.object(gemini_service, "analyze_intent_and_reply")
def test_failed_request_and_retry(mock_gemini):
    client_msg_id = str(uuid.uuid4())

    # First attempt fails with 502
    mock_gemini.side_effect = GeminiServiceError("Transient upstream error", status_code=502)
    res_1 = client.post("/api/chat", json={
        "conversation_id": None,
        "client_message_id": client_msg_id,
        "message": "Retry me",
    })
    assert res_1.status_code == 502

    # Second attempt succeeds
    mock_gemini.side_effect = None
    mock_gemini.return_value = make_mock_result(
        intent=IntentCategory.WB_INCOME_CERTIFICATE,
        reply="Success after retry",
    )
    res_2 = client.post("/api/chat", json={
        "conversation_id": None,
        "client_message_id": client_msg_id,
        "message": "Retry me",
    })
    assert res_2.status_code == 200
    assert res_2.json()["reply"] == "Success after retry"


# Test 14: Duplicate client message ID (Idempotency)
@patch.object(gemini_service, "analyze_intent_and_reply")
def test_duplicate_client_message_id_idempotency(mock_gemini):
    mock_gemini.return_value = make_mock_result(
        intent=IntentCategory.WB_DOMICILE_CERTIFICATE,
        reply="Idempotent response",
    )
    client_msg_id = str(uuid.uuid4())
    payload = {
        "conversation_id": None,
        "client_message_id": client_msg_id,
        "message": "Testing idempotency",
    }

    # First call
    res_1 = client.post("/api/chat", json=payload)
    assert res_1.status_code == 200
    conv_id = res_1.json()["conversation_id"]
    msg_id = res_1.json()["message_id"]

    # Duplicate call with same client_message_id
    payload_retry = {
        "conversation_id": conv_id,
        "client_message_id": client_msg_id,
        "message": "Testing idempotency",
    }
    res_2 = client.post("/api/chat", json=payload_retry)
    assert res_2.status_code == 200
    assert res_2.json()["message_id"] == msg_id

    # Gemini service should have only been invoked ONCE
    assert mock_gemini.call_count == 1


# Test 15: Logical consistency validation unit test
def test_logical_consistency_enforcement():
    raw_unclear = StructuredIntentResult(
        intent=IntentCategory.UNCLEAR,
        intent_status=IntentStatus.IDENTIFIED,
        service_support=ServiceSupport.SUPPORTED_MVP,
        known_information=KnownInformation(),
        missing_information=[],
        next_action=NextAction.ACKNOWLEDGE_INTENT,
        reply="Clarification needed",
    )
    corrected = gemini_service.validate_consistency(raw_unclear)
    assert corrected.intent_status == IntentStatus.NEEDS_CLARIFICATION
    assert corrected.service_support == ServiceSupport.UNDETERMINED
    assert corrected.next_action == NextAction.ASK_CLARIFICATION
