from fastapi import APIRouter, HTTPException, status
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.session_service import session_manager, SessionNotFoundError

router = APIRouter()


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Process a conversational chat message"
)
def chat_endpoint(request: ChatRequest) -> ChatResponse:
    """
    Accepts natural language input from the citizen.
    Maintains conversation session state, deduplicates retried client_message_id,
    and returns a deterministic backend stub response.
    """
    try:
        return session_manager.process_message(request)
    except SessionNotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation session not found or expired."
        ) from err
