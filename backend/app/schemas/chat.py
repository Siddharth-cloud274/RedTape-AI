from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class IntentCategory(str, Enum):
    WB_INCOME_CERTIFICATE = "wb_income_certificate"
    WB_DOMICILE_CERTIFICATE = "wb_domicile_certificate"
    FSSAI_REGISTRATION = "fssai_registration"
    TRADE_LICENCE = "trade_licence"
    FOOD_BUSINESS_SETUP = "food_business_setup"
    UNSUPPORTED = "unsupported"
    UNCLEAR = "unclear"


class IntentStatus(str, Enum):
    IDENTIFIED = "identified"
    NEEDS_CLARIFICATION = "needs_clarification"
    UNSUPPORTED = "unsupported"


class ServiceSupport(str, Enum):
    SUPPORTED_MVP = "supported_mvp"
    RECOGNIZED_NOT_IMPLEMENTED = "recognized_not_implemented"
    UNSUPPORTED = "unsupported"
    UNDETERMINED = "undetermined"


class NextAction(str, Enum):
    ASK_CLARIFICATION = "ask_clarification"
    ACKNOWLEDGE_INTENT = "acknowledge_intent"
    EXPLAIN_LIMITATION = "explain_limitation"


class KnownInformation(BaseModel):
    location: Optional[str] = Field(
        default=None,
        description="Citizen's state, district, or city (e.g. Kolkata, West Bengal)"
    )
    purpose: Optional[str] = Field(
        default=None,
        description="Purpose of certificate or registration (e.g. college admission, scholarship)"
    )
    business_type: Optional[str] = Field(
        default=None,
        description="Type of business (e.g. bakery, grocery, restaurant)"
    )
    annual_turnover: Optional[str] = Field(
        default=None,
        description="Annual turnover if mentioned"
    )
    notes: Optional[str] = Field(
        default=None,
        description="Any other key factual detail explicitly provided"
    )


class StructuredIntentResult(BaseModel):
    intent: IntentCategory = Field(
        ...,
        description="Categorized bureaucratic intent."
    )
    intent_status: IntentStatus = Field(
        ...,
        description="Status of the intent classification."
    )
    service_support: ServiceSupport = Field(
        ...,
        description="Whether this service is supported in current MVP, recognized but not implemented, or unsupported."
    )
    known_information: KnownInformation = Field(
        default_factory=KnownInformation,
        description="Explicit information established in this conversation."
    )
    missing_information: List[str] = Field(
        default_factory=list,
        description="Relevant missing context fields that could clarify intent."
    )
    next_action: NextAction = Field(
        ...,
        description="Appropriate next conversational action."
    )
    reply: str = Field(
        ...,
        description="Concise, natural-language conversational response for the citizen."
    )


class ChatRequest(BaseModel):
    conversation_id: Optional[str] = Field(
        default=None,
        description="Existing conversation session ID, or null to start a new conversation."
    )
    client_message_id: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="Unique client-generated identifier for this turn/message."
    )
    message: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="User's natural language input."
    )

    @field_validator("message")
    @classmethod
    def validate_message_not_whitespace(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Message cannot be empty or contain only whitespace.")
        return trimmed


class ChatResponse(BaseModel):
    conversation_id: str
    message_id: str
    reply: str
    mode: str = "gemini"
    intent: Optional[StructuredIntentResult] = None
