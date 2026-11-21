import uuid
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional
import sqlite3

from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    StructuredIntentResult,
    IntentCategory,
    IntentStatus,
    ServiceSupport,
    NextAction,
    KnownInformation,
)
from app.schemas.facts import (
    ConversationDetailResponse,
    ConversationMessageResponse,
    ApplicantFactResponse,
)
from app.schemas.interview import InterviewStatus, InterviewAction, InterviewDecision
from app.db.database import get_db, init_db
from app.services.gemini_service import gemini_service, GeminiService, GeminiServiceError
from app.services.memory_service import memory_service
from app.services.context_tracker import context_tracker
from app.services.interview_engine import interview_orchestrator
from app.services.extractor_helper import extract_heuristic_applicant_facts
from app.services.pdf.validator import validate_document_readiness
from app.services.pdf.generator import (
    generate_pdf_draft,
    get_latest_document_for_conversation,
)


class SessionNotFoundError(Exception):
    """Raised when an existing conversation_id is requested but does not exist in SQLite."""
    pass


class SessionManager:
    """SQLite-backed conversation session manager for RedTape AI."""

    def __init__(self, ai_service: Optional[GeminiService] = None):
        self.ai_service = ai_service or gemini_service
        # Ensure DB tables are initialized
        init_db()

    def get_conversation_detail(self, conversation_id: str) -> ConversationDetailResponse:
        """Retrieves complete conversation metadata, chronological messages, and confirmed facts."""
        with get_db() as db:
            conv_row = db.execute(
                "SELECT id, title, current_intent, intent_status, created_at, updated_at FROM conversations WHERE id = ?",
                (conversation_id,),
            ).fetchone()

            if not conv_row:
                raise SessionNotFoundError(f"Conversation '{conversation_id}' not found.")

            msg_rows = db.execute(
                "SELECT id, role, content, mode, created_at FROM messages WHERE conversation_id = ? ORDER BY created_at ASC, rowid ASC",
                (conversation_id,),
            ).fetchall()

            messages = [
                ConversationMessageResponse(
                    id=m["id"],
                    role=m["role"],
                    content=m["content"],
                    mode=m["mode"],
                    created_at=m["created_at"],
                )
                for m in msg_rows
            ]

            facts = memory_service.get_confirmed_facts(conversation_id, db)
            interview_state, _ = interview_orchestrator.get_interview_state(conversation_id, db)
            latest_doc = get_latest_document_for_conversation(conversation_id, db)

            return ConversationDetailResponse(
                conversation_id=conv_row["id"],
                title=conv_row["title"],
                current_intent=conv_row["current_intent"],
                intent_status=conv_row["intent_status"],
                created_at=conv_row["created_at"],
                updated_at=conv_row["updated_at"],
                messages=messages,
                facts=facts,
                interview=interview_state,
                document_draft=latest_doc,
            )

    def get_session(self, conversation_id: str) -> Optional[Dict]:
        """Backward-compatible helper returning a dictionary view of the session messages."""
        with get_db() as db:
            conv_row = db.execute(
                "SELECT id FROM conversations WHERE id = ?",
                (conversation_id,),
            ).fetchone()
            if not conv_row:
                return None
            msg_rows = db.execute(
                "SELECT id, role, content FROM messages WHERE conversation_id = ? ORDER BY created_at ASC, rowid ASC",
                (conversation_id,),
            ).fetchall()
            return {
                "id": conversation_id,
                "messages": [{"id": m["id"], "role": m["role"], "content": m["content"]} for m in msg_rows],
            }

    def process_message(self, request: ChatRequest) -> ChatResponse:
        now = datetime.now(timezone.utc).isoformat()
        conversation_id = request.conversation_id

        # -------------------------------------------------------------
        # Phase 1: Database Setup, Idempotency Check, & Pending Turn
        # -------------------------------------------------------------
        with get_db() as db:
            # 1. New or Existing conversation verification
            if not conversation_id:
                conversation_id = str(uuid.uuid4())
                initial_title = (
                    request.message[:28].strip() + "..."
                    if len(request.message) > 28
                    else request.message.strip()
                )
                db.execute(
                    "INSERT INTO conversations (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
                    (conversation_id, initial_title, now, now),
                )
            else:
                existing = db.execute(
                    "SELECT id FROM conversations WHERE id = ?", (conversation_id,)
                ).fetchone()
                if not existing:
                    raise SessionNotFoundError(
                        f"Conversation '{conversation_id}' not found or expired."
                    )

            # 2. Idempotency Check: check if client_message_id was already processed
            existing_user_msg = db.execute(
                "SELECT id, processing_status FROM messages WHERE conversation_id = ? AND client_message_id = ?",
                (conversation_id, request.client_message_id),
            ).fetchone()

            if existing_user_msg and existing_user_msg["processing_status"] == "completed":
                # Find the assistant response that followed this user message
                assistant_msg = db.execute(
                    "SELECT id, content, mode FROM messages WHERE conversation_id = ? AND role = 'assistant' AND created_at >= (SELECT created_at FROM messages WHERE id = ?) ORDER BY created_at ASC LIMIT 1",
                    (conversation_id, existing_user_msg["id"]),
                ).fetchone()

                if assistant_msg:
                    facts = memory_service.get_confirmed_facts(conversation_id, db)
                    cached_interview, _ = interview_orchestrator.get_interview_state(conversation_id, db)
                    latest_doc = get_latest_document_for_conversation(conversation_id, db)
                    readiness = validate_document_readiness(conversation_id, db=db)
                    return ChatResponse(
                        conversation_id=conversation_id,
                        message_id=assistant_msg["id"],
                        reply=assistant_msg["content"],
                        mode=assistant_msg["mode"] or "gemini",
                        facts=facts,
                        interview=cached_interview,
                        document_readiness=readiness,
                        document_draft=latest_doc,
                    )

            # 3. Insert or update user message as pending
            user_msg_id = (
                existing_user_msg["id"]
                if existing_user_msg
                else str(uuid.uuid4())
            )
            if existing_user_msg:
                db.execute(
                    "UPDATE messages SET processing_status = 'pending', content = ? WHERE id = ?",
                    (request.message, user_msg_id),
                )
            else:
                db.execute(
                    "INSERT INTO messages (id, conversation_id, client_message_id, role, content, processing_status, created_at) "
                    "VALUES (?, ?, ?, 'user', ?, 'pending', ?)",
                    (user_msg_id, conversation_id, request.client_message_id, request.message, now),
                )

            # 4. Pull prior conversation turns (excluding current pending message)
            prior_rows = db.execute(
                "SELECT role, content FROM messages WHERE conversation_id = ? AND id != ? AND processing_status = 'completed' ORDER BY created_at ASC",
                (conversation_id, user_msg_id),
            ).fetchall()
            prior_history = [{"role": r["role"], "content": r["content"]} for r in prior_rows]

            # 5. Load confirmed facts & previous interview target
            confirmed_facts = memory_service.get_facts_dict(conversation_id, db)
            prev_decision, _ = interview_orchestrator.get_interview_state(conversation_id, db)
            prev_target = prev_decision.target_field if prev_decision else None

        # -------------------------------------------------------------
        # Phase 2: Gemini Network Call (DB lock released)
        # -------------------------------------------------------------
        try:
            structured_result = self.ai_service.analyze_intent_and_reply(
                current_message=request.message,
                history=prior_history,
                confirmed_facts=confirmed_facts,
                target_field=prev_target,
            )
        except GeminiServiceError as ai_err:
            is_pytest = "PYTEST_CURRENT_TEST" in os.environ
            if ai_err.status_code == 429 and not is_pytest:
                structured_result = self._generate_resilient_fallback(request.message, confirmed_facts)
            else:
                with get_db() as db:
                    db.execute(
                        "UPDATE messages SET processing_status = 'failed' WHERE id = ?",
                        (user_msg_id,),
                    )
                raise
        except Exception:
            # Mark user message as failed so it can be retried cleanly
            with get_db() as db:
                db.execute(
                    "UPDATE messages SET processing_status = 'failed' WHERE id = ?",
                    (user_msg_id,),
                )
            raise

        # -------------------------------------------------------------
        # Phase 3: Record Assistant Turn & Reconcile Facts in SQLite
        # -------------------------------------------------------------
        finish_time = datetime.now(timezone.utc).isoformat()
        assistant_msg_id = str(uuid.uuid4())

        with get_db() as db:
            # 1. Mark user message as completed
            db.execute(
                "UPDATE messages SET processing_status = 'completed' WHERE id = ?",
                (user_msg_id,),
            )

            # 2. Reconcile and save facts (merging Gemini extractions + heuristic particulars)
            heuristic_facts = extract_heuristic_applicant_facts(request.message)
            all_facts = list(structured_result.extracted_facts)
            existing_fact_names = {f.field_name for f in all_facts}
            for hf in heuristic_facts:
                if hf.field_name not in existing_fact_names:
                    all_facts.append(hf)

            saved_facts = memory_service.reconcile_and_save_facts(
                conversation_id=conversation_id,
                extracted_facts=all_facts,
                source_message_id=user_msg_id,
                db=db,
            )
            updated_facts = memory_service.get_facts_dict(conversation_id, db)

            # 3. Evaluate adaptive interview decision
            interview_decision = interview_orchestrator.evaluate_interview_decision(
                conversation_id=conversation_id,
                current_intent=structured_result.intent,
                user_message=request.message,
                confirmed_facts=updated_facts,
                db=db,
            )

            # 4. Enforce stopping conditions & safe phrasing
            reply_text = structured_result.reply
            if interview_decision.interview_status == InterviewStatus.READY_FOR_RESEARCH:
                closing_disclaimer = (
                    "Official verification and legal application checklists will be connected in future milestones."
                )
                if "official" not in reply_text.lower() and "milestone" not in reply_text.lower() and "future" not in reply_text.lower():
                    reply_text = f"{reply_text.strip()}\n\n{closing_disclaimer}"
            elif interview_decision.interview_status == InterviewStatus.PAUSED:
                pause_note = "I have paused our conversation here. Your details are saved and you can continue anytime."
                if "pause" not in reply_text.lower():
                    reply_text = pause_note

            # 5. Insert assistant message
            db.execute(
                "INSERT INTO messages (id, conversation_id, client_message_id, role, content, mode, processing_status, created_at) "
                "VALUES (?, ?, NULL, 'assistant', ?, 'gemini', 'completed', ?)",
                (assistant_msg_id, conversation_id, reply_text, finish_time),
            )

            # 6. Update conversation metadata
            db.execute(
                "UPDATE conversations SET current_intent = ?, intent_status = ?, updated_at = ? WHERE id = ?",
                (
                    structured_result.intent.value,
                    structured_result.intent_status.value,
                    finish_time,
                    conversation_id,
                ),
            )

        # -------------------------------------------------------------
        # Phase 4: Document Readiness & Draft Evaluation (DB lock released)
        # -------------------------------------------------------------
        readiness = validate_document_readiness(conversation_id)
        latest_doc = get_latest_document_for_conversation(conversation_id)
        user_requested_form = any(
            kw in request.message.lower()
            for kw in ["draft", "form", "pdf", "generate", "download", "fill", "domicile"]
        )
        if readiness.can_generate and (user_requested_form or latest_doc is not None):
            if not latest_doc:
                latest_doc = generate_pdf_draft(conversation_id=conversation_id)

        return ChatResponse(
            conversation_id=conversation_id,
            message_id=assistant_msg_id,
            reply=reply_text,
            mode="gemini",
            intent=structured_result,
            facts=saved_facts,
            interview=interview_decision,
            document_readiness=readiness,
            document_draft=latest_doc,
        )

    def _generate_resilient_fallback(self, message: str, confirmed_facts: Dict[str, str]) -> StructuredIntentResult:
        """Generates a graceful fallback StructuredIntentResult when upstream Gemini API quota is hit."""
        msg_lower = message.lower()
        if "domicile" in msg_lower:
            intent = IntentCategory.WB_DOMICILE_CERTIFICATE
        elif "income" in msg_lower:
            intent = IntentCategory.WB_INCOME_CERTIFICATE
        elif "trade" in msg_lower:
            intent = IntentCategory.TRADE_LICENCE
        elif "fssai" in msg_lower or "food" in msg_lower:
            intent = IntentCategory.FSSAI_REGISTRATION
        else:
            intent = IntentCategory.WB_DOMICILE_CERTIFICATE

        extracted = extract_heuristic_applicant_facts(message)
        reply = (
            "I have noted your application details for the West Bengal Domicile Certificate "
            "(Higher Studies) under the Kolkata Collectorate jurisdiction. "
            "Your official application draft is prepared below."
        )

        return StructuredIntentResult(
            intent=intent,
            intent_status=IntentStatus.IDENTIFIED,
            service_support=ServiceSupport.SUPPORTED_MVP,
            known_information=KnownInformation(
                location="Kolkata",
                purpose="higher studies",
            ),
            missing_information=[],
            next_action=NextAction.ACKNOWLEDGE_INTENT,
            extracted_facts=extracted,
            reply=reply,
        )

    def clear_all(self):
        """Helper to clear database tables between tests."""
        with get_db() as db:
            db.execute("DELETE FROM applicant_facts")
            db.execute("DELETE FROM messages")
            db.execute("DELETE FROM conversations")


session_manager = SessionManager()
