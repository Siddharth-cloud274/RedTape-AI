from typing import List, Optional
from pydantic import BaseModel, Field


class ExtractedFactItem(BaseModel):
    """A discrete fact extracted by Gemini from user messages."""
    field_name: str = Field(
        ...,
        description="Name of the recognized field, e.g. location, purpose, business_type, annual_turnover"
    )
    field_value: str = Field(
        ...,
        description="Normalized value, e.g. Howrah, college admission, bakery"
    )
    evidence: str = Field(
        ...,
        description="Exact snippet or reference from user message supporting this fact"
    )
    is_correction: bool = Field(
        default=False,
        description="True if the user is explicitly correcting an earlier statement (e.g. 'Actually I live in Howrah')"
    )


class ApplicantFactResponse(BaseModel):
    """Stored confirmed or reconciled applicant fact."""
    field_name: str
    field_value: str
    evidence: Optional[str] = None
    confidence_status: str = "confirmed"
    updated_at: str


class ConversationMessageResponse(BaseModel):
    """A single stored message in a conversation."""
    id: str
    role: str
    content: str
    mode: Optional[str] = None
    created_at: str


class ConversationDetailResponse(BaseModel):
    """Complete restored conversation with history and structured facts."""
    conversation_id: str
    title: Optional[str] = None
    current_intent: Optional[str] = None
    intent_status: Optional[str] = None
    created_at: str
    updated_at: str
    messages: List[ConversationMessageResponse] = []
    facts: List[ApplicantFactResponse] = []
    interview: Optional[object] = None
    document_draft: Optional[object] = None
    official_resources: Optional[object] = None

