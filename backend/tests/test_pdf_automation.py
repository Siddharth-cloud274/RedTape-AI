import os
import tempfile
import pytest
import pymupdf
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

from main import app
from app.db.database import get_db, init_db
from app.templates.registry import get_template, list_templates, TEMPLATE_REGISTRY
from app.services.pdf.mappings.kolkata_domicile import KOLKATA_DOMICILE_FIELD_MAP, REQUIRED_FIELDS
from app.services.pdf.validator import (
    validate_document_readiness,
    check_kolkata_jurisdiction,
    resolve_field_value,
)
from app.services.pdf.generator import (
    generate_pdf_draft,
    get_draft_metadata,
    get_draft_file_path,
    regenerate_pdf_draft,
    compute_file_sha256,
)
from app.schemas.document import DocumentReadinessStatus
from app.schemas.chat import (
    StructuredIntentResult,
    IntentCategory,
    IntentStatus,
    ServiceSupport,
    NextAction,
    KnownInformation,
)
from app.schemas.facts import ExtractedFactItem

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    init_db()
    with get_db() as conn:
        conn.execute("DELETE FROM generated_documents")
        conn.execute("DELETE FROM applicant_facts")
        conn.execute("DELETE FROM messages")
        conn.execute("DELETE FROM conversations")
    yield
    with get_db() as conn:
        conn.execute("DELETE FROM generated_documents")
        conn.execute("DELETE FROM applicant_facts")
        conn.execute("DELETE FROM messages")
        conn.execute("DELETE FROM conversations")


# --------------------------------------------------------------------------
# Template Provenance & Structure Tests
# --------------------------------------------------------------------------

def test_template_registry_lookup():
    template = get_template("kolkata_domicile_higher_studies")
    assert template is not None
    assert template.template_id == "kolkata_domicile_higher_studies"
    assert "Kolkata Collectorate" in template.issuing_authority
    assert template.purpose == "Higher Studies"
    assert template.page_count == 3
    assert template.template_type == "static"
    assert os.path.exists(template.file_path)


def test_template_sha256_integrity():
    template = get_template("kolkata_domicile_higher_studies")
    computed_hash = compute_file_sha256(template.file_path)
    assert computed_hash == template.sha256_hash


def test_template_is_static_pdf_without_acroform():
    template = get_template("kolkata_domicile_higher_studies")
    doc = pymupdf.open(template.file_path)
    assert doc.page_count == 3
    for page in doc:
        # Static PDF has no interactive form widgets
        widgets = list(page.widgets())
        assert len(widgets) == 0
    doc.close()


def test_coordinate_mapping_structure():
    assert len(KOLKATA_DOMICILE_FIELD_MAP) >= 12
    for field_name, config in KOLKATA_DOMICILE_FIELD_MAP.items():
        assert "page" in config
        assert config["page"] in [0, 1]  # Page 1 or Page 2
        assert "rect" in config
        rect = config["rect"]
        assert len(rect) == 4
        assert rect[0] < rect[2]  # x0 < x1
        assert rect[1] < rect[3]  # y0 < y1


# --------------------------------------------------------------------------
# Validator & Readiness Tests
# --------------------------------------------------------------------------

def test_jurisdiction_check_kolkata_valid():
    facts = {"location": "Kolkata, Salt Lake", "present_address": "Kolkata 700001"}
    is_valid, reason = check_kolkata_jurisdiction(facts)
    assert is_valid is True
    assert reason is None


def test_jurisdiction_check_non_kolkata_mismatch():
    facts = {"location": "Barrackpore, North 24 Parganas"}
    is_valid, reason = check_kolkata_jurisdiction(facts)
    assert is_valid is False
    assert "Barrackpore" in reason


def test_validate_readiness_empty_conversation():
    conv_id = "test-conv-empty"
    with get_db() as conn:
        conn.execute(
            "INSERT INTO conversations (id, created_at, updated_at) VALUES (?, datetime('now'), datetime('now'))",
            (conv_id,),
        )
    readiness = validate_document_readiness(conv_id)
    assert readiness.can_generate is False
    assert readiness.readiness_status == DocumentReadinessStatus.COLLECTING_DOCUMENT_DETAILS
    assert len(readiness.missing_required_fields) == len(REQUIRED_FIELDS)


def test_validate_readiness_complete_facts():
    conv_id = "test-conv-complete"
    with get_db() as conn:
        conn.execute(
            "INSERT INTO conversations (id, created_at, updated_at) VALUES (?, datetime('now'), datetime('now'))",
            (conv_id,),
        )
        for field, val in [
            ("applicant_name", "Sourav Mukherjee"),
            ("father_name", "Debabrata Mukherjee"),
            ("date_of_birth", "2003-05-14"),
            ("present_address", "12 Park Street, Kolkata 700016"),
            ("stay_duration", "15 years"),
        ]:
            conn.execute(
                "INSERT INTO applicant_facts (conversation_id, field_name, field_value, confidence_status, updated_at) VALUES (?, ?, ?, 'confirmed', datetime('now'))",
                (conv_id, field, val),
            )

    readiness = validate_document_readiness(conv_id)
    assert readiness.can_generate is True
    assert readiness.readiness_status == DocumentReadinessStatus.READY_FOR_DRAFT
    assert len(readiness.missing_required_fields) == 0
    assert readiness.jurisdiction_verified is True


# --------------------------------------------------------------------------
# Generator Tests
# --------------------------------------------------------------------------

def test_generate_pdf_draft_and_verify_structure():
    conv_id = "test-conv-gen"
    with get_db() as conn:
        conn.execute(
            "INSERT INTO conversations (id, created_at, updated_at) VALUES (?, datetime('now'), datetime('now'))",
            (conv_id,),
        )
        for field, val in [
            ("applicant_name", "Ananya Sen"),
            ("father_name", "Pradip Sen"),
            ("date_of_birth", "2002-11-20"),
            ("present_address", "45 Gariahat Road, Kolkata 700019"),
            ("stay_duration", "20 years"),
        ]:
            conn.execute(
                "INSERT INTO applicant_facts (conversation_id, field_name, field_value, confidence_status, updated_at) VALUES (?, ?, ?, 'confirmed', datetime('now'))",
                (conv_id, field, val),
            )

    meta = generate_pdf_draft(conv_id)
    assert meta.document_id is not None
    assert meta.version == 1
    assert meta.status == "draft_generated"
    assert meta.filled_fields["applicant_name"] == "Ananya Sen"
    assert meta.filled_fields["father_name"] == "Pradip Sen"

    # Verify physical PDF
    filepath = get_draft_file_path(meta.document_id)
    assert filepath is not None
    assert os.path.exists(filepath)

    doc = pymupdf.open(filepath)
    assert doc.page_count == 3

    # Check watermark banner in text
    page1_text = doc[0].get_text()
    assert "UNSUBMITTED DRAFT" in page1_text
    assert "REDTAPE AI" in page1_text
    assert "Ananya Sen" in page1_text
    assert "Pradip Sen" in page1_text

    page2_text = doc[1].get_text()
    assert "UNSUBMITTED DRAFT" in page2_text

    doc.close()


def test_signature_area_remains_strictly_unpopulated():
    conv_id = "test-conv-sig"
    with get_db() as conn:
        conn.execute(
            "INSERT INTO conversations (id, created_at, updated_at) VALUES (?, datetime('now'), datetime('now'))",
            (conv_id,),
        )
        conn.execute(
            "INSERT INTO applicant_facts (conversation_id, field_name, field_value, confidence_status, updated_at) VALUES (?, 'applicant_name', 'Rohan Bose', 'confirmed', datetime('now'))",
            (conv_id,),
        )
        conn.execute(
            "INSERT INTO applicant_facts (conversation_id, field_name, field_value, confidence_status, updated_at) VALUES (?, 'father_name', 'Alok Bose', 'confirmed', datetime('now'))",
            (conv_id,),
        )
        conn.execute(
            "INSERT INTO applicant_facts (conversation_id, field_name, field_value, confidence_status, updated_at) VALUES (?, 'date_of_birth', '2001-08-10', 'confirmed', datetime('now'))",
            (conv_id,),
        )
        conn.execute(
            "INSERT INTO applicant_facts (conversation_id, field_name, field_value, confidence_status, updated_at) VALUES (?, 'present_address', 'Kolkata', 'confirmed', datetime('now'))",
            (conv_id,),
        )

    meta = generate_pdf_draft(conv_id)
    filepath = get_draft_file_path(meta.document_id)
    doc = pymupdf.open(filepath)
    page2 = doc[1]
    # Check text around signature area (approx y: 720 to 780, x: 350 to 550)
    sig_rect = pymupdf.Rect(350, 720, 550, 780)
    sig_text = page2.get_text("text", clip=sig_rect).strip()
    # Should only contain official static words like "(Signature of the Applicant)" or nothing, never applicant name
    assert "Rohan Bose" not in sig_text
    doc.close()


def test_regenerate_draft_increments_version():
    conv_id = "test-conv-regen"
    with get_db() as conn:
        conn.execute(
            "INSERT INTO conversations (id, created_at, updated_at) VALUES (?, datetime('now'), datetime('now'))",
            (conv_id,),
        )
        for field, val in [
            ("applicant_name", "Tanmay Roy"),
            ("father_name", "Subhas Roy"),
            ("date_of_birth", "2000-01-01"),
            ("present_address", "Bowbazar, Kolkata"),
        ]:
            conn.execute(
                "INSERT INTO applicant_facts (conversation_id, field_name, field_value, confidence_status, updated_at) VALUES (?, ?, ?, 'confirmed', datetime('now'))",
                (conv_id, field, val),
            )

    meta1 = generate_pdf_draft(conv_id)
    assert meta1.version == 1

    meta2 = regenerate_pdf_draft(
        meta1.document_id,
        updated_fields={"father_occupation": "Professor", "stay_duration": "24 years"},
    )
    assert meta2.version == 2
    assert meta2.filled_fields["father_occupation"] == "Professor"
    assert meta2.filled_fields["stay_duration"] == "24 years"
    assert meta2.filled_fields["applicant_name"] == "Tanmay Roy"


# --------------------------------------------------------------------------
# API Endpoints Tests
# --------------------------------------------------------------------------

def test_api_check_readiness():
    conv_id = "test-api-check"
    with get_db() as conn:
        conn.execute(
            "INSERT INTO conversations (id, created_at, updated_at) VALUES (?, datetime('now'), datetime('now'))",
            (conv_id,),
        )
    resp = client.get(f"/api/documents/check/{conv_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["can_generate"] is False
    assert len(data["missing_required_fields"]) > 0


def test_api_draft_flow_create_preview_download_regenerate():
    conv_id = "test-api-flow"
    with get_db() as conn:
        conn.execute(
            "INSERT INTO conversations (id, created_at, updated_at) VALUES (?, datetime('now'), datetime('now'))",
            (conv_id,),
        )
        for field, val in [
            ("applicant_name", "Suman Das"),
            ("father_name", "Bimal Das"),
            ("date_of_birth", "2004-03-12"),
            ("present_address", "Salt Lake Sector 1, Kolkata 700064"),
        ]:
            conn.execute(
                "INSERT INTO applicant_facts (conversation_id, field_name, field_value, confidence_status, updated_at) VALUES (?, ?, ?, 'confirmed', datetime('now'))",
                (conv_id, field, val),
            )

    # 1. POST /api/documents/draft
    post_resp = client.post(
        "/api/documents/draft",
        json={"conversation_id": conv_id, "template_id": "kolkata_domicile_higher_studies"},
    )
    assert post_resp.status_code == 200
    post_data = post_resp.json()
    assert post_data["success"] is True
    doc = post_data["document"]
    doc_id = doc["document_id"]
    assert doc["version"] == 1

    # 2. GET /api/documents/{id}/metadata
    meta_resp = client.get(f"/api/documents/{doc_id}/metadata")
    assert meta_resp.status_code == 200
    assert meta_resp.json()["document_id"] == doc_id

    # 3. GET /api/documents/{id}/preview
    preview_resp = client.get(f"/api/documents/{doc_id}/preview")
    assert preview_resp.status_code == 200
    assert preview_resp.headers["content-type"] == "application/pdf"
    assert "inline" in preview_resp.headers["content-disposition"]
    assert len(preview_resp.content) > 10000

    # 4. GET /api/documents/{id}/download
    dl_resp = client.get(f"/api/documents/{doc_id}/download")
    assert dl_resp.status_code == 200
    assert dl_resp.headers["content-type"] == "application/pdf"
    assert "attachment" in dl_resp.headers["content-disposition"]
    assert len(dl_resp.content) > 10000

    # 5. POST /api/documents/{id}/regenerate
    regen_resp = client.post(
        f"/api/documents/{doc_id}/regenerate",
        json={"updated_fields": {"father_occupation": "Architect"}},
    )
    assert regen_resp.status_code == 200
    regen_data = regen_resp.json()
    assert regen_data["success"] is True
    assert regen_data["document"]["version"] == 2
    assert regen_data["document"]["filled_fields"]["father_occupation"] == "Architect"


def test_api_preview_nonexistent_returns_404():
    resp = client.get("/api/documents/non-existent-id/preview")
    assert resp.status_code == 404


def test_api_download_nonexistent_returns_404():
    resp = client.get("/api/documents/non-existent-id/download")
    assert resp.status_code == 404


def test_api_regenerate_nonexistent_returns_404():
    resp = client.post("/api/documents/non-existent-id/regenerate", json={"updated_fields": {}})
    assert resp.status_code == 404
