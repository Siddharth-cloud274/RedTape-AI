from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class DocumentReadinessStatus(str, Enum):
    JURISDICTION_UNVERIFIED = "jurisdiction_unverified"
    COLLECTING_DOCUMENT_DETAILS = "collecting_document_details"
    READY_FOR_DRAFT = "ready_for_draft"
    DRAFT_GENERATED = "draft_generated"
    DRAFT_NEEDS_REVIEW = "draft_needs_review"


class DocumentDraftRequest(BaseModel):
    conversation_id: str
    template_id: str = "kolkata_domicile_higher_studies"
    custom_field_values: Optional[Dict[str, str]] = None


class DocumentRegenerateRequest(BaseModel):
    updated_fields: Optional[Dict[str, str]] = None


class DocumentMetadataResponse(BaseModel):
    document_id: str
    conversation_id: str
    template_id: str
    title: str
    issuing_authority: str
    jurisdiction: str
    version: int
    status: str
    readiness_status: DocumentReadinessStatus
    missing_fields: List[str] = Field(default_factory=list)
    filled_fields: Dict[str, str] = Field(default_factory=dict)
    preview_url: str
    download_url: str
    source_portal_url: str
    created_at: str
    updated_at: str


class DocumentDraftResponse(BaseModel):
    success: bool
    document: Optional[DocumentMetadataResponse] = None
    message: str
    missing_fields: List[str] = Field(default_factory=list)


class DocumentReadinessCheck(BaseModel):
    can_generate: bool
    readiness_status: DocumentReadinessStatus
    template_id: str
    jurisdiction_verified: bool
    missing_required_fields: List[str] = Field(default_factory=list)
    present_fields: Dict[str, str] = Field(default_factory=dict)
