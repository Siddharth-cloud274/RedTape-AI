import os
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import FileResponse

from app.schemas.document import (
    DocumentDraftRequest,
    DocumentDraftResponse,
    DocumentMetadataResponse,
    DocumentRegenerateRequest,
    DocumentReadinessCheck,
)
from app.services.pdf.generator import (
    generate_pdf_draft,
    get_draft_metadata,
    get_draft_file_path,
    regenerate_pdf_draft,
)
from app.services.pdf.validator import validate_document_readiness

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("/check/{conversation_id}", response_model=DocumentReadinessCheck)
async def check_readiness(
    conversation_id: str,
    template_id: str = "kolkata_domicile_higher_studies",
):
    """Checks whether the conversation has collected enough verified applicant facts for a draft."""
    try:
        return validate_document_readiness(conversation_id, template_id=template_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/draft", response_model=DocumentDraftResponse)
async def create_document_draft(request: DocumentDraftRequest):
    """Generates an official unsubmitted draft PDF populated with applicant facts."""
    try:
        readiness = validate_document_readiness(
            request.conversation_id,
            template_id=request.template_id,
            custom_overrides=request.custom_field_values,
        )

        if not readiness.can_generate:
            return DocumentDraftResponse(
                success=False,
                document=None,
                message=(
                    f"Applicant facts incomplete for official draft. Missing required fields: "
                    f"{', '.join(readiness.missing_required_fields)}"
                ),
                missing_fields=readiness.missing_required_fields,
            )

        metadata = generate_pdf_draft(
            conversation_id=request.conversation_id,
            template_id=request.template_id,
            custom_field_values=request.custom_field_values,
        )

        return DocumentDraftResponse(
            success=True,
            document=metadata,
            message="Official draft generated successfully.",
            missing_fields=metadata.missing_fields,
        )
    except FileNotFoundError as fnf:
        raise HTTPException(status_code=404, detail=str(fnf))
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Draft generation failed: {str(e)}")


@router.get("/{document_id}/metadata", response_model=DocumentMetadataResponse)
async def get_metadata(document_id: str):
    """Retrieves metadata and field status for a generated document draft."""
    metadata = get_draft_metadata(document_id)
    if not metadata:
        raise HTTPException(status_code=404, detail=f"Document draft not found: {document_id}")
    return metadata


@router.get("/{document_id}/preview")
async def preview_document(document_id: str):
    """Returns the generated PDF draft stream for inline browser preview."""
    file_path = get_draft_file_path(document_id)
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Document file not found for: {document_id}")

    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"inline; filename=draft_{document_id}.pdf",
            "Cache-Control": "no-cache",
        },
    )


@router.get("/{document_id}/download")
async def download_document(document_id: str):
    """Serves the generated PDF draft as an attachment download with safe headers."""
    file_path = get_draft_file_path(document_id)
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Document file not found for: {document_id}")

    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=f"WB_Domicile_Draft_{document_id[:8]}.pdf",
        headers={
            "Content-Disposition": f"attachment; filename=WB_Domicile_Draft_{document_id[:8]}.pdf",
            "Cache-Control": "no-cache",
        },
    )


@router.post("/{document_id}/regenerate", response_model=DocumentDraftResponse)
async def regenerate_document(document_id: str, request: DocumentRegenerateRequest):
    """Regenerates the draft PDF with user-edited or newly provided fields."""
    try:
        new_metadata = regenerate_pdf_draft(
            document_id=document_id, updated_fields=request.updated_fields
        )
        return DocumentDraftResponse(
            success=True,
            document=new_metadata,
            message=f"Official draft regenerated as version {new_metadata.version}.",
            missing_fields=new_metadata.missing_fields,
        )
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Draft regeneration failed: {str(e)}")
