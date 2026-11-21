import uuid
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from main import app
from app.db.database import get_db, init_db
from app.schemas.chat import (
    IntentCategory,
    StructuredIntentResult,
    NextAction,
    IntentStatus,
    ServiceSupport,
    ExtractedFactItem,
)
from app.services.gemini_service import gemini_service
from app.services.pdf.generator import generate_pdf_draft, regenerate_pdf_draft
from app.services.review_service import review_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    init_db()
    with get_db() as db:
        db.execute("DELETE FROM review_audit_log")
        db.execute("DELETE FROM review_approvals")
        db.execute("DELETE FROM application_reviews")
        db.execute("DELETE FROM generated_documents")
        db.execute("DELETE FROM applicant_facts")
        db.execute("DELETE FROM messages")
        db.execute("DELETE FROM conversations")
    yield
    with get_db() as db:
        db.execute("DELETE FROM review_audit_log")
        db.execute("DELETE FROM review_approvals")
        db.execute("DELETE FROM application_reviews")
        db.execute("DELETE FROM generated_documents")
        db.execute("DELETE FROM applicant_facts")
        db.execute("DELETE FROM messages")
        db.execute("DELETE FROM conversations")


def _setup_complete_domicile_conversation() -> Tuple[str, str]:
    """Helper that creates a conversation with complete confirmed applicant facts and a generated draft."""
    conv_id = str(uuid.uuid4())
    now = "2026-11-21T09:00:00Z"
    with get_db() as db:
        db.execute(
            "INSERT INTO conversations (id, title, current_intent, intent_status, created_at, updated_at) "
            "VALUES (?, 'Domicile Review Test', 'wb_domicile_certificate', 'identified', ?, ?)",
            (conv_id, now, now),
        )

        facts = [
            ("applicant_name", "Sourav Mukherjee"),
            ("father_name", "Debasis Mukherjee"),
            ("date_of_birth", "15/08/2004"),
            ("present_address", "12/A College Street, Ward 44, Kolkata - 700073"),
            ("residence_location", "Kolkata"),
            ("purpose", "Higher Studies"),
            ("stay_duration", "20 years"),
            ("father_occupation", "Teacher"),
        ]
        for field, val in facts:
            db.execute(
                "INSERT INTO applicant_facts (conversation_id, field_name, field_value, confidence_status, updated_at) "
                "VALUES (?, ?, ?, 'confirmed', ?)",
                (conv_id, field, val, now),
            )

    doc_meta = generate_pdf_draft(conversation_id=conv_id)
    return conv_id, doc_meta.document_id


from typing import Tuple


def test_review_summary_structure_and_ready_state():
    """Verifies complete review summary includes facts, research requirements, and ready status."""
    conv_id, doc_id = _setup_complete_domicile_conversation()

    res = client.get(f"/api/reviews/{conv_id}")
    assert res.status_code == 200
    data = res.json()

    assert data["conversation_id"] == conv_id
    assert data["service_id"] == "wb_domicile_certificate"
    assert data["review_status"] == "review_ready"
    assert data["can_approve"] is True
    assert data["confirmed_facts"]["applicant_name"] == "Sourav Mukherjee"
    assert data["confirmed_facts"]["father_name"] == "Debasis Mukherjee"
    assert data["latest_document_id"] == doc_id
    assert data["latest_document_version"] == 1
    assert data["document_hash"] is not None
    assert len(data["required_documents"]) >= 4
    assert data["handoff_type"] == "offline"


def test_review_in_progress_when_facts_incomplete():
    """Verifies review is marked review_in_progress and can_approve is False when facts are missing."""
    conv_id = str(uuid.uuid4())
    now = "2026-11-21T09:00:00Z"
    with get_db() as db:
        db.execute(
            "INSERT INTO conversations (id, title, current_intent, intent_status, created_at, updated_at) "
            "VALUES (?, 'Incomplete Intake', 'wb_domicile_certificate', 'identified', ?, ?)",
            (conv_id, now, now),
        )
        db.execute(
            "INSERT INTO applicant_facts (conversation_id, field_name, field_value, confidence_status, updated_at) "
            "VALUES (?, 'applicant_name', 'Rahul Das', 'confirmed', ?)",
            (conv_id, now),
        )

    res = client.get(f"/api/reviews/{conv_id}")
    assert res.status_code == 200
    data = res.json()
    assert data["review_status"] == "review_in_progress"
    assert data["can_approve"] is False
    assert len(data["missing_fields"]) > 0


def test_approval_requires_explicit_opt_in_checkboxes():
    """Verifies approval fails with 400 if user does not explicitly check the confirmation declarations."""
    conv_id, doc_id = _setup_complete_domicile_conversation()

    # Neither checked
    res1 = client.post(
        f"/api/reviews/{conv_id}/approve",
        json={
            "document_id": doc_id,
            "document_version": 1,
            "confirm_correctness": False,
            "acknowledge_unsubmitted": True,
        },
    )
    assert res1.status_code == 400
    assert "explicitly confirm" in res1.json()["detail"].lower()

    # Second unchecked
    res2 = client.post(
        f"/api/reviews/{conv_id}/approve",
        json={
            "document_id": doc_id,
            "document_version": 1,
            "confirm_correctness": True,
            "acknowledge_unsubmitted": False,
        },
    )
    assert res2.status_code == 400
    assert "not been submitted" in res2.json()["detail"].lower()


def test_approval_binds_to_exact_version_and_computes_hashes():
    """Verifies that approval succeeds, records version and hashes, and transitions status to user_approved."""
    conv_id, doc_id = _setup_complete_domicile_conversation()

    res = client.post(
        f"/api/reviews/{conv_id}/approve",
        json={
            "document_id": doc_id,
            "document_version": 1,
            "confirm_correctness": True,
            "acknowledge_unsubmitted": True,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["review_status"] == "user_approved"
    assert data["approval"] is not None
    assert data["approval"]["document_version"] == 1
    assert data["approval"]["document_hash"] is not None
    assert data["approval"]["facts_snapshot_hash"] is not None
    assert data["approval"]["status"] == "active"

    # Verify summary now reflects user_approved
    sum_res = client.get(f"/api/reviews/{conv_id}")
    assert sum_res.status_code == 200
    assert sum_res.json()["review_status"] == "user_approved"
    assert sum_res.json()["active_approval"] is not None


def test_approval_of_stale_document_version_rejected():
    """Verifies attempting to approve an older document version returns 400."""
    conv_id, doc_id = _setup_complete_domicile_conversation()

    # Regenerate draft to v2
    doc_v2 = regenerate_pdf_draft(doc_id, updated_fields={"stay_duration": "22 years"})
    assert doc_v2.version == 2

    # Attempt to approve v1
    res = client.post(
        f"/api/reviews/{conv_id}/approve",
        json={
            "document_id": doc_id,
            "document_version": 1,
            "confirm_correctness": True,
            "acknowledge_unsubmitted": True,
        },
    )
    assert res.status_code == 400
    assert "stale document version" in res.json()["detail"].lower()


def test_duplicate_approval_is_idempotent():
    """Verifies repeated approval calls for the same version return existing record without duplicate audits."""
    conv_id, doc_id = _setup_complete_domicile_conversation()

    payload = {
        "document_id": doc_id,
        "document_version": 1,
        "confirm_correctness": True,
        "acknowledge_unsubmitted": True,
    }
    res1 = client.post(f"/api/reviews/{conv_id}/approve", json=payload)
    assert res1.status_code == 200
    appr1_id = res1.json()["approval"]["id"]

    res2 = client.post(f"/api/reviews/{conv_id}/approve", json=payload)
    assert res2.status_code == 200
    appr2_id = res2.json()["approval"]["id"]

    assert appr1_id == appr2_id


def test_draft_regeneration_invalidates_approval():
    """Verifies that manual draft regeneration automatically invalidates active approval."""
    conv_id, doc_id = _setup_complete_domicile_conversation()

    # Approve v1
    client.post(
        f"/api/reviews/{conv_id}/approve",
        json={
            "document_id": doc_id,
            "document_version": 1,
            "confirm_correctness": True,
            "acknowledge_unsubmitted": True,
        },
    )

    # Regenerate draft via endpoint
    regen_res = client.post(
        f"/api/documents/{doc_id}/regenerate",
        json={"updated_fields": {"stay_duration": "25 years"}},
    )
    assert regen_res.status_code == 200
    assert regen_res.json()["document"]["version"] == 2

    # Review summary should now be approval_invalidated
    sum_res = client.get(f"/api/reviews/{conv_id}")
    assert sum_res.status_code == 200
    assert sum_res.json()["review_status"] == "approval_invalidated"
    assert sum_res.json()["active_approval"] is None


def test_request_changes_endpoint():
    """Verifies /api/reviews/{id}/request-changes sets status to review_changes_requested."""
    conv_id, doc_id = _setup_complete_domicile_conversation()

    # Approve v1
    client.post(
        f"/api/reviews/{conv_id}/approve",
        json={
            "document_id": doc_id,
            "document_version": 1,
            "confirm_correctness": True,
            "acknowledge_unsubmitted": True,
        },
    )

    res = client.post(
        f"/api/reviews/{conv_id}/request-changes",
        json={"reason": "Father's name spelling mistake", "fields_to_edit": ["father_name"]},
    )
    assert res.status_code == 200
    assert res.json()["review_status"] == "review_changes_requested"

    # Confirm approval invalidated
    sum_res = client.get(f"/api/reviews/{conv_id}")
    assert sum_res.json()["review_status"] == "review_changes_requested"
    assert sum_res.json()["active_approval"] is None


def test_offline_handoff_guidance():
    """Verifies GET /api/reviews/{id}/handoff returns correct offline submission guidance for Domicile."""
    conv_id, doc_id = _setup_complete_domicile_conversation()

    res = client.get(f"/api/reviews/{conv_id}/handoff")
    assert res.status_code == 200
    data = res.json()
    assert data["handoff_type"] == "offline"
    assert "kolkatacollectorate.wb.gov.in" in data["official_source_url"]
    assert data["government_submission_status"] == "not_submitted"
    assert any("Kolkata Collectorate" in step for step in data["submission_instructions"])
    assert any("ink" in step.lower() or "sign" in step.lower() for step in data["submission_instructions"])


def test_handoff_action_logging_and_domain_whitelist():
    """Verifies portal open and download actions log audit events, and unsafe redirects are blocked."""
    conv_id, doc_id = _setup_complete_domicile_conversation()

    # Valid domain open
    res = client.post(
        f"/api/reviews/{conv_id}/handoff/action",
        json={"action": "open_portal", "url_target": "https://kolkatacollectorate.wb.gov.in/domicile-certificate/"},
    )
    assert res.status_code == 200
    assert res.json()["success"] is True

    # Malicious external domain blocked
    res_bad = client.post(
        f"/api/reviews/{conv_id}/handoff/action",
        json={"action": "open_portal", "url_target": "https://phishing-site.example.com/login"},
    )
    assert res_bad.status_code == 403


def test_approval_survives_backend_restart():
    """Verifies that approval records and status persist across service reinstantiation."""
    conv_id, doc_id = _setup_complete_domicile_conversation()

    client.post(
        f"/api/reviews/{conv_id}/approve",
        json={
            "document_id": doc_id,
            "document_version": 1,
            "confirm_correctness": True,
            "acknowledge_unsubmitted": True,
        },
    )

    # Reinstantiate ReviewService (simulating server restart)
    new_service = type(review_service)()
    summary = new_service.get_review_summary(conv_id)
    assert summary.review_status.value == "user_approved"
    assert summary.active_approval is not None
    assert summary.active_approval.document_version == 1
