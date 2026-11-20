from fastapi import APIRouter, HTTPException, status
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.session_service import session_manager, SessionNotFoundError
from app.services.gemini_service import GeminiServiceError

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
    Uses Gemini to perform structured intent detection and conversational response,
    maintains conversation session state, and deduplicates retried client_message_id.
    """
    try:
        return session_manager.process_message(request)
    except SessionNotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation session not found or expired."
        ) from err
    except GeminiServiceError as ai_err:
        raise HTTPException(
            status_code=ai_err.status_code,
            detail=ai_err.message
        ) from ai_err
    except Exception as generic_err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing your request."
        ) from generic_err
