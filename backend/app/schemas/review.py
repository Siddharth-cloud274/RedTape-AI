from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class ReviewStatus(str, Enum):
    REVIEW_NOT_STARTED = "review_not_started"
    REVIEW_PENDING = "review_pending"
    REVIEW_IN_PROGRESS = "review_in_progress"
    REVIEW_CHANGES_REQUESTED = "review_changes_requested"
    REVIEW_BLOCKED = "review_blocked"
    REVIEW_READY = "review_ready"
    USER_APPROVED = "user_approved"
    APPROVAL_INVALIDATED = "approval_invalidated"
    HANDOFF_READY = "handoff_ready"
    HANDOFF_OPENED = "handoff_opened"


class HandoffType(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    UNVERIFIED = "unverified"


class ApprovalRecord(BaseModel):
    id: str
    review_id: str
    conversation_id: str
    document_id: Optional[str] = None
    document_version: Optional[int] = None
    document_hash: Optional[str] = None
    facts_snapshot_hash: Optional[str] = None
    status: str = "active"  # 'active' | 'invalidated'
    invalidation_reason: Optional[str] = None
    approved_at: str


class ApprovalRequest(BaseModel):
    document_id: Optional[str] = None
    document_version: Optional[int] = None
    confirm_correctness: bool = Field(
        ..., description="Citizen explicitly confirms all entered details are accurate."
    )
    acknowledge_unsubmitted: bool = Field(
        ...,
        description="Citizen explicitly acknowledges this is a draft and NOT yet submitted to government.",
    )


class ApprovalResponse(BaseModel):
    success: bool
    review_status: ReviewStatus
    approval: Optional[ApprovalRecord] = None
    message: str
    handoff_type: Optional[HandoffType] = None


class ReviewChangesRequest(BaseModel):
    reason: str = Field(..., description="Reason for requesting changes / corrections.")
    fields_to_edit: Optional[List[str]] = Field(
        default_factory=list, description="Specific field names that require correction."
    )


class HandoffGuidanceResponse(BaseModel):
    handoff_type: HandoffType
    service_id: str
    service_title: str
    issuing_authority: str
    jurisdiction: str
    official_portal_url: Optional[str] = None
    official_source_url: str
    submission_instructions: List[str]
    document_sets_required: int = 1
    signature_required: bool = True
    government_submission_status: str = "not_submitted"
    approved_document_version: Optional[int] = None
    warnings: List[str] = Field(default_factory=list)
    last_verified_at: str


class ReviewSummaryResponse(BaseModel):
    review_id: str
    conversation_id: str
    service_id: str
    service_title: str
    issuing_authority: str
    jurisdiction: str
    administrative_goal: Optional[str] = None
    review_status: ReviewStatus
    confirmed_facts: Dict[str, str] = Field(default_factory=dict)
    missing_fields: List[str] = Field(default_factory=list)
    conflicting_fields: List[str] = Field(default_factory=list)
    unverified_information: List[str] = Field(default_factory=list)
    required_documents: List[str] = Field(default_factory=list)
    official_sources: List[Dict[str, str]] = Field(default_factory=list)
    handoff_type: HandoffType
    latest_document_id: Optional[str] = None
    latest_document_version: Optional[int] = None
    document_hash: Optional[str] = None
    active_approval: Optional[ApprovalRecord] = None
    can_approve: bool = False
    status_message: str


class HandoffActionRequest(BaseModel):
    action: str = Field(
        ..., description="'open_portal' | 'view_instructions' | 'download_final'"
    )
    url_target: Optional[str] = None


class AuditEventResponse(BaseModel):
    id: str
    conversation_id: str
    review_id: str
    document_version: Optional[int] = None
    event_type: str
    state_from: Optional[str] = None
    state_to: Optional[str] = None
    created_at: str
