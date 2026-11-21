import hashlib
import json
import os
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

from app.db.database import get_db, init_db
from app.schemas.chat import IntentCategory
from app.schemas.review import (
    ApprovalRecord,
    ApprovalRequest,
    ApprovalResponse,
    AuditEventResponse,
    HandoffGuidanceResponse,
    HandoffType,
    ReviewChangesRequest,
    ReviewStatus,
    ReviewSummaryResponse,
)
from app.services.memory_service import memory_service
from app.services.pdf.generator import (
    get_draft_file_path,
    get_latest_document_for_conversation,
)
from app.services.pdf.validator import validate_document_readiness
from app.services.research_service import research_service

# Whitelisted official government domains to prevent open redirects
APPROVED_PORTAL_DOMAINS = {
    "kolkatacollectorate.wb.gov.in",
    "edistrict.wb.gov.in",
    "kmcgov.in",
    "www.kmcgov.in",
    "foscos.fssai.gov.in",
    "fssai.gov.in",
    "silpasathi.wb.gov.in",
    "passportindia.gov.in",
    "www.passportindia.gov.in",
    "parivahan.gov.in",
    "sarathi.parivahan.gov.in",
    "incometax.gov.in",
    "www.incometax.gov.in",
    "onlineservices.nsdl.com",
    "voters.eci.gov.in",
    "myaadhaar.uidai.gov.in",
    "castcertificatewb.gov.in",
    "crsorgi.gov.in",
    "janma-mrityutathya.wb.gov.in",
    "services.india.gov.in",
    "digitalindia.gov.in",
    "svmcm.wbhed.gov.in",
}


class ReviewServiceError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class ReviewService:
    """Manages application review, explicit version-bound human approval, audit trail, and handoff."""

    def __init__(self):
        init_db()

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _compute_file_sha256(file_path: str) -> Optional[str]:
        if not file_path or not os.path.exists(file_path):
            return None
        sha = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                sha.update(chunk)
        return sha.hexdigest()

    @staticmethod
    def _compute_facts_hash(facts: Dict[str, str]) -> str:
        sorted_pairs = sorted(facts.items())
        serialized = json.dumps(sorted_pairs, separators=(",", ":"))
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def log_audit_event(
        self,
        conversation_id: str,
        review_id: str,
        event_type: str,
        document_version: Optional[int] = None,
        state_from: Optional[str] = None,
        state_to: Optional[str] = None,
        payload: Optional[Dict] = None,
        db=None,
    ) -> str:
        """Appends an internal audit event. Does NOT store raw sensitive PII in log text."""
        event_id = str(uuid.uuid4())
        now = self._now()
        payload_str = json.dumps(payload or {})

        sql = """
        INSERT INTO review_audit_log (id, conversation_id, review_id, document_version, event_type, state_from, state_to, payload_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        def _insert(conn):
            conn.execute(
                sql,
                (
                    event_id,
                    conversation_id,
                    review_id,
                    document_version,
                    event_type,
                    state_from,
                    state_to,
                    payload_str,
                    now,
                ),
            )

        if db:
            _insert(db)
        else:
            with get_db() as conn:
                _insert(conn)

        return event_id

    def get_or_create_review(
        self, conversation_id: str, service_id: str, db=None
    ) -> Dict:
        """Retrieves existing review record or initializes a fresh one."""
        now = self._now()

        def _fetch(conn):
            row = conn.execute(
                "SELECT * FROM application_reviews WHERE conversation_id = ?",
                (conversation_id,),
            ).fetchone()
            if row:
                return dict(row)

            review_id = str(uuid.uuid4())
            conn.execute(
                """
                INSERT INTO application_reviews (id, conversation_id, service_id, review_status, latest_document_id, latest_document_version, created_at, updated_at)
                VALUES (?, ?, ?, 'review_pending', NULL, NULL, ?, ?)
                """,
                (review_id, conversation_id, service_id, now, now),
            )
            self.log_audit_event(
                conversation_id=conversation_id,
                review_id=review_id,
                event_type="review_created",
                state_to=ReviewStatus.REVIEW_PENDING.value,
                db=conn,
            )
            return {
                "id": review_id,
                "conversation_id": conversation_id,
                "service_id": service_id,
                "review_status": ReviewStatus.REVIEW_PENDING.value,
                "latest_document_id": None,
                "latest_document_version": None,
                "created_at": now,
                "updated_at": now,
            }

        if db:
            return _fetch(db)
        with get_db() as conn:
            return _fetch(conn)

    def determine_handoff_type(self, service_id: str) -> HandoffType:
        """Resolves whether a service requires online or offline handoff based on verified rules."""
        s = (service_id or "").lower()
        if "domicile" in s or "kolkata_income" in s:
            return HandoffType.OFFLINE
        elif s in {
            "trade_licence",
            "fssai_registration",
            "food_business_setup",
            "passport_services",
            "driving_licence",
            "pan_card",
            "voter_id",
            "aadhaar_services",
        }:
            return HandoffType.ONLINE
        return HandoffType.UNVERIFIED

    def get_review_summary(self, conversation_id: str) -> ReviewSummaryResponse:
        """Assembles structured review information from confirmed facts, research, and drafts."""
        with get_db() as db:
            conv = db.execute(
                "SELECT current_intent, title FROM conversations WHERE id = ?",
                (conversation_id,),
            ).fetchone()
            if not conv:
                raise ReviewServiceError(
                    f"Conversation '{conversation_id}' not found.", status_code=404
                )

            current_service = conv["current_intent"] or "wb_domicile_certificate"
            review_dict = self.get_or_create_review(conversation_id, current_service, db=db)
            confirmed_facts = memory_service.get_facts_dict(conversation_id, db)
            latest_doc = get_latest_document_for_conversation(conversation_id, db)
            readiness = validate_document_readiness(conversation_id, db=db)

            # Check active approval
            approval_row = db.execute(
                "SELECT * FROM review_approvals WHERE review_id = ? AND status = 'active' ORDER BY approved_at DESC LIMIT 1",
                (review_dict["id"],),
            ).fetchone()

        active_approval = None
        if approval_row:
            active_approval = ApprovalRecord(
                id=approval_row["id"],
                review_id=approval_row["review_id"],
                conversation_id=approval_row["conversation_id"],
                document_id=approval_row["document_id"],
                document_version=approval_row["document_version"],
                document_hash=approval_row["document_hash"],
                facts_snapshot_hash=approval_row["facts_snapshot_hash"],
                status=approval_row["status"],
                invalidation_reason=approval_row["invalidation_reason"],
                approved_at=approval_row["approved_at"],
            )

        research = research_service.get_service_research(current_service)
        service_title = research.title if research else "Government Bureaucracy Assistance"
        authority = research.issuing_authority if research else "Competent Authority"
        jurisdiction = research.jurisdiction if research else "Government of West Bengal / India"
        required_docs = research.required_documents if research else []
        official_sources = [
            {"title": link.title, "url": link.url, "type": link.link_type}
            for link in (research.official_links if research else [])
        ]
        handoff_type = self.determine_handoff_type(current_service)

        # Compute Review Status
        current_status_val = review_dict.get("review_status", ReviewStatus.REVIEW_PENDING.value)
        can_approve = False
        status_message = "Review pending. Please complete application intake."

        if active_approval:
            # Check if document draft was regenerated past approved version
            if latest_doc and active_approval.document_version != latest_doc.version:
                review_status = ReviewStatus.APPROVAL_INVALIDATED
                status_message = f"Draft was updated to version {latest_doc.version}. Please review and approve the latest draft."
                can_approve = readiness.can_generate
            else:
                review_status = ReviewStatus.USER_APPROVED
                status_message = f"Approved draft v{active_approval.document_version} for your personal use. Unsubmitted to government."
        elif current_status_val == ReviewStatus.REVIEW_CHANGES_REQUESTED.value:
            review_status = ReviewStatus.REVIEW_CHANGES_REQUESTED
            status_message = "Edits requested. Please update particulars to proceed."
            can_approve = readiness.can_generate
        elif current_status_val == ReviewStatus.APPROVAL_INVALIDATED.value:
            review_status = ReviewStatus.APPROVAL_INVALIDATED
            status_message = "Previous approval was invalidated due to edits. Please review and re-approve."
            can_approve = readiness.can_generate
        elif not readiness.jurisdiction_verified:
            review_status = ReviewStatus.REVIEW_BLOCKED
            status_message = "Jurisdiction check failed. Application cannot be processed for this location."
        elif readiness.missing_required_fields:
            review_status = ReviewStatus.REVIEW_IN_PROGRESS
            status_message = f"Missing required information: {', '.join(readiness.missing_required_fields)}"
        elif readiness.can_generate or latest_doc:
            review_status = ReviewStatus.REVIEW_READY
            can_approve = True
            doc_ver = latest_doc.version if latest_doc else 1
            status_message = f"All required details confirmed. Official unsubmitted draft v{doc_ver} is ready for human review."
        else:
            review_status = ReviewStatus.REVIEW_PENDING

        doc_hash = None
        if latest_doc:
            doc_path = get_draft_file_path(latest_doc.document_id)
            doc_hash = self._compute_file_sha256(doc_path)

        return ReviewSummaryResponse(
            review_id=review_dict["id"],
            conversation_id=conversation_id,
            service_id=current_service,
            service_title=service_title,
            issuing_authority=authority,
            jurisdiction=jurisdiction,
            administrative_goal=confirmed_facts.get("purpose") or confirmed_facts.get("application_purpose"),
            review_status=review_status,
            confirmed_facts=confirmed_facts,
            missing_fields=readiness.missing_required_fields,
            conflicting_fields=[],
            unverified_information=[
                "Official processing fees and live portal queue times are not confirmed without live government login."
            ],
            required_documents=required_docs,
            official_sources=official_sources,
            handoff_type=handoff_type,
            latest_document_id=latest_doc.document_id if latest_doc else None,
            latest_document_version=latest_doc.version if latest_doc else None,
            document_hash=doc_hash,
            active_approval=active_approval,
            can_approve=can_approve,
            status_message=status_message,
        )

    def record_approval(
        self, conversation_id: str, request: ApprovalRequest
    ) -> ApprovalResponse:
        """
        Records explicit, opt-in human approval bound to a specific document draft version.
        Rejects stale version approval attempts and unconfirmed consent.
        """
        if not request.confirm_correctness:
            raise ReviewServiceError(
                "You must explicitly confirm that the entered application details are correct."
            )
        if not request.acknowledge_unsubmitted:
            raise ReviewServiceError(
                "You must acknowledge that this is a personal draft and has NOT been submitted to the government."
            )

        summary = self.get_review_summary(conversation_id)
        if not summary.can_approve and summary.review_status != ReviewStatus.USER_APPROVED:
            raise ReviewServiceError(
                f"Cannot approve application in state '{summary.review_status.value}': {summary.status_message}"
            )

        latest_doc = get_latest_document_for_conversation(conversation_id)
        if latest_doc:
            if request.document_version and request.document_version != latest_doc.version:
                raise ReviewServiceError(
                    f"Stale document version: approval requested for v{request.document_version}, but latest draft is v{latest_doc.version}."
                )
            if request.document_id and request.document_id != latest_doc.document_id:
                raise ReviewServiceError("Stale document ID provided for approval.")

        # Compute document & facts hashes
        doc_path = get_draft_file_path(latest_doc.document_id) if latest_doc else None
        doc_hash = self._compute_file_sha256(doc_path)
        facts_hash = self._compute_facts_hash(summary.confirmed_facts)

        now = self._now()
        doc_ver = latest_doc.version if latest_doc else (request.document_version or 1)
        doc_id = latest_doc.document_id if latest_doc else request.document_id

        with get_db() as db:
            # Check idempotency: if already approved for this version with active status
            existing_active = db.execute(
                "SELECT * FROM review_approvals WHERE review_id = ? AND document_version = ? AND status = 'active'",
                (summary.review_id, doc_ver),
            ).fetchone()

            if existing_active:
                approval_rec = ApprovalRecord(
                    id=existing_active["id"],
                    review_id=existing_active["review_id"],
                    conversation_id=existing_active["conversation_id"],
                    document_id=existing_active["document_id"],
                    document_version=existing_active["document_version"],
                    document_hash=existing_active["document_hash"],
                    facts_snapshot_hash=existing_active["facts_snapshot_hash"],
                    status=existing_active["status"],
                    invalidation_reason=existing_active["invalidation_reason"],
                    approved_at=existing_active["approved_at"],
                )
                return ApprovalResponse(
                    success=True,
                    review_status=ReviewStatus.USER_APPROVED,
                    approval=approval_rec,
                    message=f"Draft v{doc_ver} is already approved for your personal use.",
                    handoff_type=summary.handoff_type,
                )

            # Invalidate any prior active approvals
            db.execute(
                "UPDATE review_approvals SET status = 'invalidated', invalidation_reason = 'superceded_by_newer_approval' WHERE review_id = ? AND status = 'active'",
                (summary.review_id,),
            )

            # Insert new approval record
            approval_id = str(uuid.uuid4())
            db.execute(
                """
                INSERT INTO review_approvals (id, review_id, conversation_id, document_id, document_version, document_hash, facts_snapshot_hash, status, invalidation_reason, approved_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'active', NULL, ?)
                """,
                (
                    approval_id,
                    summary.review_id,
                    conversation_id,
                    doc_id,
                    doc_ver,
                    doc_hash,
                    facts_hash,
                    now,
                ),
            )

            # Update application_reviews status
            db.execute(
                "UPDATE application_reviews SET review_status = 'user_approved', latest_document_id = ?, latest_document_version = ?, updated_at = ? WHERE id = ?",
                (doc_id, doc_ver, now, summary.review_id),
            )

            # Audit event
            self.log_audit_event(
                conversation_id=conversation_id,
                review_id=summary.review_id,
                document_version=doc_ver,
                event_type="approval_granted",
                state_from=summary.review_status.value,
                state_to=ReviewStatus.USER_APPROVED.value,
                payload={"document_version": doc_ver, "document_hash": doc_hash},
                db=db,
            )

        approval_rec = ApprovalRecord(
            id=approval_id,
            review_id=summary.review_id,
            conversation_id=conversation_id,
            document_id=doc_id,
            document_version=doc_ver,
            document_hash=doc_hash,
            facts_snapshot_hash=facts_hash,
            status="active",
            approved_at=now,
        )

        return ApprovalResponse(
            success=True,
            review_status=ReviewStatus.USER_APPROVED,
            approval=approval_rec,
            message=f"Official draft version {doc_ver} approved for your use. Unsubmitted to government.",
            handoff_type=summary.handoff_type,
        )

    def request_changes(
        self, conversation_id: str, request: ReviewChangesRequest
    ) -> Dict:
        """Reopens review, invalidating existing approvals and logging user corrections."""
        summary = self.get_review_summary(conversation_id)
        now = self._now()

        with get_db() as db:
            # Invalidate any active approval
            db.execute(
                "UPDATE review_approvals SET status = 'invalidated', invalidation_reason = ? WHERE review_id = ? AND status = 'active'",
                (f"changes_requested: {request.reason}", summary.review_id),
            )

            # Set review status
            db.execute(
                "UPDATE application_reviews SET review_status = 'review_changes_requested', updated_at = ? WHERE id = ?",
                (now, summary.review_id),
            )

            self.log_audit_event(
                conversation_id=conversation_id,
                review_id=summary.review_id,
                event_type="changes_requested",
                state_from=summary.review_status.value,
                state_to=ReviewStatus.REVIEW_CHANGES_REQUESTED.value,
                payload={"reason": request.reason, "fields": request.fields_to_edit},
                db=db,
            )

        return {
            "success": True,
            "review_status": ReviewStatus.REVIEW_CHANGES_REQUESTED,
            "message": "Review reopened for corrections. Previous approval has been invalidated.",
        }

    def invalidate_approval_if_needed(
        self, conversation_id: str, reason: str, db=None
    ) -> bool:
        """
        Called when facts or documents change to automatically invalidate existing approvals.
        Returns True if an active approval was invalidated.
        """
        now = self._now()

        def _invalidate(conn):
            active_row = conn.execute(
                "SELECT id, review_id, document_version FROM review_approvals WHERE conversation_id = ? AND status = 'active'",
                (conversation_id,),
            ).fetchone()

            if not active_row:
                return False

            conn.execute(
                "UPDATE review_approvals SET status = 'invalidated', invalidation_reason = ? WHERE id = ?",
                (reason, active_row["id"]),
            )

            conn.execute(
                "UPDATE application_reviews SET review_status = 'approval_invalidated', updated_at = ? WHERE id = ?",
                (now, active_row["review_id"]),
            )

            self.log_audit_event(
                conversation_id=conversation_id,
                review_id=active_row["review_id"],
                document_version=active_row["document_version"],
                event_type="approval_invalidated",
                state_from=ReviewStatus.USER_APPROVED.value,
                state_to=ReviewStatus.APPROVAL_INVALIDATED.value,
                payload={"reason": reason},
                db=conn,
            )
            return True

        if db:
            return _invalidate(db)
        with get_db() as conn:
            return _invalidate(conn)

    def get_handoff_guidance(self, conversation_id: str) -> HandoffGuidanceResponse:
        """Retrieves verified submission handoff instructions based on service and approval state."""
        summary = self.get_review_summary(conversation_id)
        service = summary.service_id
        research = research_service.get_service_research(service)
        now = self._now()

        handoff_type = self.determine_handoff_type(service)
        instructions = []
        warnings = [
            "RedTape AI does NOT automatically submit applications to government portals.",
            "You are responsible for completing physical submission or online portal authentication.",
        ]

        if handoff_type == HandoffType.OFFLINE:
            instructions = [
                "1. Download your approved application draft PDF using the Download button.",
                "2. Print out 1 physical copy on standard A4 paper.",
                "3. Affix two recent passport-sized color photographs in the designated top-right corner.",
                "4. Attach self-attested photocopies of all 6 supporting documents (residence proof, DOB, address proof, education verification).",
                "5. Sign in physical ink inside the applicant signature block on Page 2 (which RedTape AI leaves blank for you).",
                "6. Submit in person at: Kolkata Collectorate, Certificate Section, New Treasury Building, Kolkata.",
            ]
        elif handoff_type == HandoffType.ONLINE:
            portal_url = research.official_portal_url if research else "https://services.india.gov.in/"
            instructions = [
                f"1. Click 'Open Official Portal' to navigate directly to: {portal_url}",
                "2. Log in using your registered mobile number / Aadhaar / user ID.",
                "3. Select the appropriate application form and copy over your verified details.",
                "4. Upload required scanned supporting documents.",
                "5. Complete citizen authentication (Aadhaar OTP / e-Sign) and fee payment.",
                "6. Save the official Government Acknowledgement Receipt generated by the portal.",
            ]

        return HandoffGuidanceResponse(
            handoff_type=handoff_type,
            service_id=service,
            service_title=summary.service_title,
            issuing_authority=summary.issuing_authority,
            jurisdiction=summary.jurisdiction,
            official_portal_url=research.official_portal_url if research else None,
            official_source_url=research.official_portal_url if research else "https://services.india.gov.in/",
            submission_instructions=instructions,
            document_sets_required=1,
            signature_required=True,
            government_submission_status="not_submitted",
            approved_document_version=(
                summary.active_approval.document_version
                if summary.active_approval
                else summary.latest_document_version
            ),
            warnings=warnings,
            last_verified_at=now,
        )

    def record_handoff_action(
        self, conversation_id: str, action: str, target_url: Optional[str] = None
    ) -> Dict:
        """Records an explicit user click on portal open or download action. Validates destination domain."""
        if target_url:
            parsed = urlparse(target_url)
            domain = parsed.netloc.lower()
            if domain and domain not in APPROVED_PORTAL_DOMAINS:
                raise ReviewServiceError(
                    f"Refusing redirect to unverified external domain: '{domain}'.",
                    status_code=403,
                )

        summary = self.get_review_summary(conversation_id)
        now = self._now()

        with get_db() as db:
            if action == "open_portal":
                db.execute(
                    "UPDATE application_reviews SET review_status = 'handoff_opened', updated_at = ? WHERE id = ?",
                    (now, summary.review_id),
                )
                self.log_audit_event(
                    conversation_id=conversation_id,
                    review_id=summary.review_id,
                    event_type="external_portal_opened",
                    state_from=summary.review_status.value,
                    state_to=ReviewStatus.HANDOFF_OPENED.value,
                    payload={"target_url": target_url},
                    db=db,
                )
            elif action == "download_final":
                self.log_audit_event(
                    conversation_id=conversation_id,
                    review_id=summary.review_id,
                    event_type="offline_pack_downloaded",
                    payload={"version": summary.latest_document_version},
                    db=db,
                )

        return {
            "success": True,
            "action": action,
            "recorded_at": now,
            "message": "User handoff action recorded in audit log. Status remains NOT SUBMITTED to government.",
        }


review_service = ReviewService()
