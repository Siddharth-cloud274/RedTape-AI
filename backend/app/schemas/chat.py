from typing import Optional
from pydantic import BaseModel, Field, field_validator


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
    mode: str = "backend_stub"
