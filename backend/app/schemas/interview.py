from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.chat import IntentCategory


class InterviewStatus(str, Enum):
    UNDERSTANDING_GOAL = "understanding_goal"
    COLLECTING_CONTEXT = "collecting_context"
    CLARIFICATION_NEEDED = "clarification_needed"
    PAUSED = "paused"
    READY_FOR_RESEARCH = "ready_for_research"
    UNSUPPORTED = "unsupported"


class InterviewAction(str, Enum):
    ASK_QUESTION = "ask_question"
    CLARIFY_CONFLICT = "clarify_conflict"
    ACKNOWLEDGE_INFORMATION = "acknowledge_information"
    PAUSE_INTERVIEW = "pause_interview"
    EXPLAIN_LIMITATION = "explain_limitation"
    HANDOFF_TO_FUTURE_RESEARCH = "handoff_to_future_research"


class InterviewDecision(BaseModel):
    """
    Validated interview decision produced by the Adaptive Interview Engine.
    The backend remains authoritative over state, next action, and target field.
    """
    interview_status: InterviewStatus = Field(
        ...,
        description="Current state of the conversational interview."
    )
    current_intent: IntentCategory = Field(
        ...,
        description="Recognized citizen bureaucratic intent."
    )
    known_fields: List[str] = Field(
        default_factory=list,
        description="Context fields established from user facts."
    )
    missing_context: List[str] = Field(
        default_factory=list,
        description="Remaining unfulfilled preliminary context fields."
    )
    skipped_fields: List[str] = Field(
        default_factory=list,
        description="Fields user skipped, declined, or could not answer."
    )
    next_action: InterviewAction = Field(
        ...,
        description="Next conversational action to be executed."
    )
    target_field: Optional[str] = Field(
        default=None,
        description="The specific context field currently being queried."
    )
    question: Optional[str] = Field(
        default=None,
        description="Natural-language question phrasing for the citizen."
    )
    notes: Optional[str] = Field(
        default=None,
        description="Internal context or reasoning notes."
    )
