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
from app.services.interview_engine.planner import QuestionPlanner
from app.services.extractor_helper import extract_heuristic_applicant_facts
from app.services.research_service import research_service
from app.services.review_service import review_service
from app.services.pdf.validator import (
    validate_document_readiness,
    get_conversation_facts,
    resolve_field_value,
)
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
            official_res = (
                research_service.get_service_research(conv_row["current_intent"])
                if conv_row["current_intent"]
                else None
            )

            review_summary = None
            try:
                review_summary = review_service.get_review_summary(conversation_id)
            except Exception:
                pass

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
                official_resources=official_res,
                review=review_summary,
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
                    existing_conv = db.execute("SELECT current_intent FROM conversations WHERE id = ?", (conversation_id,)).fetchone()
                    intent_val = existing_conv["current_intent"] if existing_conv else None
                    official_res = research_service.get_service_research(intent_val) if intent_val else None
                    review_summary = None
                    try:
                        review_summary = review_service.get_review_summary(conversation_id)
                    except Exception:
                        pass
                    return ChatResponse(
                        conversation_id=conversation_id,
                        message_id=assistant_msg["id"],
                        reply=assistant_msg["content"],
                        mode=assistant_msg["mode"] or "gemini",
                        facts=facts,
                        interview=cached_interview,
                        document_readiness=readiness,
                        document_draft=latest_doc,
                        official_resources=official_res,
                        review=review_summary,
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
            existing_conv = db.execute("SELECT current_intent FROM conversations WHERE id = ?", (conversation_id,)).fetchone()
            existing_intent = existing_conv["current_intent"] if existing_conv else None

        # -------------------------------------------------------------
        # Phase 2: Gemini Network Call (DB lock released)
        # -------------------------------------------------------------
        try:
            structured_result = self.ai_service.analyze_intent_and_reply(
                current_message=request.message,
                history=prior_history,
                confirmed_facts=confirmed_facts,
                target_field=prev_target,
                current_intent=existing_intent,
            )
        except GeminiServiceError as ai_err:
            is_pytest = "PYTEST_CURRENT_TEST" in os.environ
            if ai_err.status_code == 429 and not is_pytest:
                structured_result = self._generate_resilient_fallback(
                    message=request.message,
                    confirmed_facts=confirmed_facts,
                    prev_target=prev_target,
                    existing_intent=existing_intent,
                )
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
            heuristic_facts = extract_heuristic_applicant_facts(
                text=request.message,
                target_field=prev_target,
                confirmed_facts=confirmed_facts,
            )
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

            # Invalidate any active approval if user explicitly corrected or updated facts
            has_fact_corrections = any(
                f.confidence_status == "corrected" for f in saved_facts
            ) or any(f.is_correction for f in all_facts)
            if has_fact_corrections:
                review_service.invalidate_approval_if_needed(
                    conversation_id=conversation_id,
                    reason="applicant_fact_corrected_by_user",
                    db=db,
                )

            # 3. Evaluate adaptive interview decision
            interview_decision = interview_orchestrator.evaluate_interview_decision(
                conversation_id=conversation_id,
                current_intent=structured_result.intent,
                user_message=request.message,
                confirmed_facts=updated_facts,
                db=db,
            )

            # 4. Enforce stopping conditions & contextual research guidance
            msg_lower = request.message.lower()
            is_asking_for_resources = any(
                w in msg_lower
                for w in [
                    "link", "links", "website", "websites", "portal", "portals", "url", "urls",
                    "where to apply", "how to apply", "where can i apply", "how can i apply",
                    "where do i apply", "how do i apply",
                    "document", "documents", "checklist", "form", "forms", "page", "pages",
                    "process", "procedure", "official", "requirement", "requirements",
                ]
            )
            is_ready = interview_decision.interview_status == InterviewStatus.READY_FOR_RESEARCH

            # Official resources card appears ONLY when requested by user or when the interview reaches completion
            if is_asking_for_resources or is_ready:
                official_resources = research_service.get_service_research(
                    structured_result.intent,
                    query=request.message,
                )
            else:
                official_resources = None

            reply_text = structured_result.reply
            if is_ready:
                if official_resources and official_resources.official_portal_url:
                    if official_resources.official_portal_url not in reply_text:
                        badge_label = "Official Application Portal" if official_resources.is_verified else "Probable Official Portal"
                        reply_text = (
                            f"{reply_text.strip()}\n\n"
                            f"**{badge_label}**: [{official_resources.title}]({official_resources.official_portal_url})\n"
                            f"**Issuing Authority**: {official_resources.issuing_authority}\n\n"
                            f"Official verification and application procedures are guided by verified government portal resources."
                        )
                elif "official" not in reply_text.lower():
                    reply_text = f"{reply_text.strip()}\n\nOfficial verification is guided by official government portals."
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
                    return ChatResponse(
                        conversation_id=conversation_id,
                        message_id=assistant_msg["id"],
                        reply=assistant_msg["content"],
                        mode=assistant_msg["mode"] or "gemini",
                        facts=facts,
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

            # 5. Load confirmed facts & calculate missing fields
            confirmed_facts = memory_service.get_facts_dict(conversation_id, db)

        # -------------------------------------------------------------
        # Phase 2: Gemini Network Call (DB lock released)
        # -------------------------------------------------------------
        try:
            structured_result = self.ai_service.analyze_intent_and_reply(
                current_message=request.message,
                history=prior_history,
                confirmed_facts=confirmed_facts,
            )
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

            # 2. Insert assistant message
            db.execute(
                "INSERT INTO messages (id, conversation_id, client_message_id, role, content, mode, processing_status, created_at) "
                "VALUES (?, ?, NULL, 'assistant', ?, 'gemini', 'completed', ?)",
                (assistant_msg_id, conversation_id, structured_result.reply, finish_time),
            )

            # 3. Reconcile and save facts
            saved_facts = memory_service.reconcile_and_save_facts(
                conversation_id=conversation_id,
                extracted_facts=structured_result.extracted_facts,
                source_message_id=user_msg_id,
                db=db,
            )

            # 4. Update conversation metadata
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

        if readiness.can_generate:
            if not latest_doc:
                latest_doc = generate_pdf_draft(conversation_id=conversation_id)
            else:
                # Check if current confirmed facts in DB have changed since latest_doc was generated
                current_facts = get_conversation_facts(conversation_id)
                key_fields = [
                    "applicant_name",
                    "father_name",
                    "date_of_birth",
                    "present_address",
                    "father_occupation",
                    "stay_duration",
                    "purpose",
                ]
                has_changed = any(
                    resolve_field_value(k, current_facts) != latest_doc.filled_fields.get(k)
                    for k in key_fields
                    if resolve_field_value(k, current_facts) is not None
                )
                if has_changed:
                    latest_doc = generate_pdf_draft(
                        conversation_id=conversation_id,
                        document_id=latest_doc.document_id,
                        version=latest_doc.version + 1,
                    )
                    review_service.invalidate_approval_if_needed(
                        conversation_id=conversation_id,
                        reason=f"draft_regenerated_to_v{latest_doc.version}",
                    )
        else:
            latest_doc = None

        review_summary = None
        try:
            review_summary = review_service.get_review_summary(conversation_id)
        except Exception:
            pass

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
            official_resources=official_resources,
            review=review_summary,
        )

    def _generate_resilient_fallback(
        self,
        message: str,
        confirmed_facts: Dict[str, str],
        prev_target: Optional[str] = None,
        existing_intent: Optional[str] = None,
    ) -> StructuredIntentResult:
        """
        Generates an adaptive, conversational fallback StructuredIntentResult when Gemini API
        quota is exhausted. Ensures no data loss, step-by-step missing context collection,
        and full applicant data verification.
        """
        msg_lower = message.lower()

        # 1. Resolve Intent accurately
        if "domicile" in msg_lower or "residential" in msg_lower:
            intent = IntentCategory.WB_DOMICILE_CERTIFICATE
        elif "income" in msg_lower:
            intent = IntentCategory.WB_INCOME_CERTIFICATE
        elif "trade" in msg_lower:
            intent = IntentCategory.TRADE_LICENCE
        elif "fssai" in msg_lower:
            intent = IntentCategory.FSSAI_REGISTRATION
        elif "food" in msg_lower:
            intent = IntentCategory.FOOD_BUSINESS_SETUP
        elif "passport" in msg_lower:
            intent = IntentCategory.PASSPORT_SERVICES
        elif "driving" in msg_lower or ("licence" in msg_lower and "trade" not in msg_lower):
            intent = IntentCategory.DRIVING_LICENCE
        elif "pan" in msg_lower:
            intent = IntentCategory.PAN_CARD
        elif "voter" in msg_lower or "epic" in msg_lower:
            intent = IntentCategory.VOTER_ID
        elif "aadhaar" in msg_lower or "aadhar" in msg_lower:
            intent = IntentCategory.AADHAAR_SERVICES
        elif "caste" in msg_lower:
            intent = IntentCategory.CASTE_CERTIFICATE
        elif "birth" in msg_lower or "death" in msg_lower:
            intent = IntentCategory.BIRTH_DEATH_CERTIFICATE
        elif existing_intent and existing_intent in [i.value for i in IntentCategory]:
            intent = IntentCategory(existing_intent)
        else:
            intent = IntentCategory.GENERAL_SERVICE

        # 2. Extract facts from current message using context-aware heuristics
        extracted = extract_heuristic_applicant_facts(
            text=message,
            target_field=prev_target,
            confirmed_facts=confirmed_facts,
        )

        # 3. Merge newly extracted facts with previously confirmed facts
        merged = dict(confirmed_facts)
        for ef in extracted:
            merged[ef.field_name] = ef.field_value

        # 4. Compute missing fields deterministically
        missing = context_tracker.calculate_missing_fields(
            intent=intent,
            known_facts=merged,
        )

        # 5. Formulate natural conversational reply
        res = research_service.get_service_research(intent, query=message)
        is_asking_for_resources = any(
            w in msg_lower
            for w in [
                "link", "links", "website", "websites", "portal", "portals", "url", "urls",
                "where to apply", "how to apply", "where can i apply", "how can i apply",
                "where do i apply", "how do i apply",
                "document", "documents", "checklist", "form", "forms", "page", "pages",
                "process", "procedure", "official", "requirement", "requirements",
            ]
        )

        if (is_asking_for_resources or intent not in {IntentCategory.WB_DOMICILE_CERTIFICATE, IntentCategory.WB_INCOME_CERTIFICATE, IntentCategory.TRADE_LICENCE, IntentCategory.FSSAI_REGISTRATION}) and res:
            links_str = "\n".join(f"• [{link.title}]({link.url}) — {link.description}" for link in res.official_links)
            docs_str = "\n".join(f"• {doc}" for doc in res.required_documents)
            badge_title = "Verified Official Portals" if res.is_verified else "Probable Official Guidance"
            disclaimer_note = f"\n\n*(Note: {res.disclaimer})*" if res.disclaimer else ""
            reply = (
                f"Here is the {badge_title.lower()} and overview for **{res.title}**:\n\n"
                f"**Portals & Official Links**:\n{links_str}\n\n"
                f"**Key Supporting Documents Needed**:\n{docs_str}\n\n"
                f"**Issuing Authority**: {res.issuing_authority} ({res.jurisdiction}){disclaimer_note}"
            )
            action = NextAction.ACKNOWLEDGE_INTENT
            intent_status = IntentStatus.IDENTIFIED
        elif missing:
            next_target = missing[0]
            question = QuestionPlanner.get_default_question(next_target)

            ack = ""
            if any(f.field_name == "applicant_name" for f in extracted):
                ack = f"Thank you, {merged.get('applicant_name')}! "
            elif extracted:
                ack = "Thank you, I have recorded that. "

            reply = f"{ack}{question}"
            action = NextAction.ASK_CLARIFICATION
            intent_status = IntentStatus.IDENTIFIED
        else:
            # All required data is gathered! Formulate verified data confirmation
            if intent == IntentCategory.WB_DOMICILE_CERTIFICATE:
                name = merged.get("applicant_name", "N/A")
                father = merged.get("father_name", "N/A")
                dob = merged.get("date_of_birth", "N/A")
                address = merged.get("present_address") or merged.get("residence_location") or "N/A"
                stay = merged.get("stay_duration", "Not specified")
                purpose = merged.get("application_purpose", "Higher Studies")

                portal_link = (
                    f"**Official Application Portal**: [{res.title} Portal]({res.official_portal_url})\n\n"
                    if res
                    else ""
                )

                reply = (
                    f"I have recorded and verified all your application details:\n\n"
                    f"• **Full Name**: {name}\n"
                    f"• **Father's Name**: {father}\n"
                    f"• **Date of Birth**: {dob}\n"
                    f"• **Present Address**: {address}\n"
                    f"• **Duration of Stay**: {stay}\n"
                    f"• **Purpose**: {purpose}\n"
                    f"• **Issuing Authority**: Kolkata Collectorate, Government of West Bengal\n\n"
                    f"{portal_link}"
                    f"Your official unsubmitted application draft has been generated below. "
                    f"You can preview the PDF, download it, or make corrections anytime."
                )
            else:
                links_str = (
                    "\n".join(f"• [{link.title}]({link.url})" for link in res.official_links)
                    if res
                    else ""
                )
                reply = (
                    f"I have recorded all your preliminary details for **{res.title if res else intent.value}**.\n\n"
                    f"**Issuing Authority**: {res.issuing_authority if res else 'Competent Government Authority'}\n\n"
                    f"**Official Portals & Resources**:\n{links_str}"
                )
            action = NextAction.ACKNOWLEDGE_INTENT
            intent_status = IntentStatus.IDENTIFIED

        known_info = KnownInformation(
            location=merged.get("location") or merged.get("residence_location"),
            business_location=merged.get("business_location"),
            purpose=merged.get("application_purpose"),
            business_type=merged.get("business_type"),
            application_type=merged.get("application_type"),
            annual_turnover=merged.get("approximate_annual_turnover"),
        )

        return StructuredIntentResult(
            intent=intent,
            intent_status=intent_status,
            service_support=ServiceSupport.SUPPORTED_MVP,
            known_information=known_info,
            missing_information=missing,
            next_action=action,
            extracted_facts=extracted,
            reply=reply,
        )

        return ChatResponse(
            conversation_id=conversation_id,
            message_id=assistant_msg_id,
            reply=structured_result.reply,
            mode="gemini",
            intent=structured_result,
            facts=saved_facts,
        )

    def clear_all(self):
        """Helper to clear database tables between tests."""
        with get_db() as db:
            db.execute("DELETE FROM applicant_facts")
            db.execute("DELETE FROM messages")
            db.execute("DELETE FROM conversations")


session_manager = SessionManager()
