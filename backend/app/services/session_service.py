import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional
from app.schemas.chat import ChatRequest, ChatResponse

STUB_REPLY_TEXT = (
    "Demo mode: your message was received by the RedTape AI backend. "
    "AI assistance is not enabled yet."
)


class SessionNotFoundError(Exception):
    """Raised when an existing conversation_id is requested but does not exist in memory."""
    pass


class SessionManager:
    """In-memory conversation session manager for RedTape AI."""

    def __init__(self):
        # Maps conversation_id -> dict with session metadata, messages, and client_id cache
        self._sessions: Dict[str, Dict] = {}

    def get_session(self, conversation_id: str) -> Optional[Dict]:
        return self._sessions.get(conversation_id)

    def process_message(self, request: ChatRequest) -> ChatResponse:
        conversation_id = request.conversation_id

        # 1. New conversation
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
            self._sessions[conversation_id] = {
                "id": conversation_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "messages": [],
                "client_message_cache": {},
            }
        else:
            # 2. Existing conversation check
            if conversation_id not in self._sessions:
                raise SessionNotFoundError(f"Conversation '{conversation_id}' not found or expired.")

        session = self._sessions[conversation_id]

        # 3. Idempotency / Retry Check
        if request.client_message_id in session["client_message_cache"]:
            # Return previously generated response without duplicating history
            return session["client_message_cache"][request.client_message_id]

        # 4. Record User Message
        user_message_record = {
            "id": request.client_message_id,
            "role": "user",
            "content": request.message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        session["messages"].append(user_message_record)

        # 5. Generate Assistant Stub Turn
        assistant_message_id = str(uuid.uuid4())
        response = ChatResponse(
            conversation_id=conversation_id,
            message_id=assistant_message_id,
            reply=STUB_REPLY_TEXT,
            mode="backend_stub",
        )

        assistant_message_record = {
            "id": assistant_message_id,
            "role": "assistant",
            "content": response.reply,
            "mode": response.mode,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        session["messages"].append(assistant_message_record)

        # 6. Cache for client_message_id deduplication
        session["client_message_cache"][request.client_message_id] = response

        return response

    def clear_all(self):
        """Helper for testing to reset session memory."""
        self._sessions.clear()


session_manager = SessionManager()
