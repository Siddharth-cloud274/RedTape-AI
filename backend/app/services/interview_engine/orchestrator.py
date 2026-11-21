import json
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set, Tuple
import sqlite3

from app.schemas.chat import IntentCategory
from app.schemas.interview import (
    InterviewStatus,
    InterviewAction,
    InterviewDecision,
)
from app.db.database import get_db
from app.services.interview_engine.planner import question_planner

PAUSE_PHRASES: Set[str] = {
    "pause",
    "stop",
    "stop for now",
    "wait",
    "hold on",
    "let's pause",
    "pause for now",
    "can we stop",
    "let us pause",
    "pause interview",
    "stop interview",
    "ruk jao",
    "ruko",
}

SKIP_OR_UNKNOWN_PATTERNS = [
    r"\bi\s*(?:don'?t|do\s*not)\s*know\b",
    r"\bnot\s*sure\b",
    r"\bno\s*idea\b",
    r"\bskip\b",
    r"\bskip\s*(?:this|it|that)\b",
    r"\bcan\s*we\s*skip\b",
    r"\bpata\s*nahi\b",
    r"\bmalum\s*nahi\b",
    r"\bunavailable\b",
]


class InterviewOrchestrator:
    """
    Manages the conversational interview lifecycle, tracks skipped/unresolved fields,
    evaluates stopping conditions, and coordinates deterministic backend authority.
    """

    @staticmethod
    def get_interview_state(
        conversation_id: str,
        db: Optional[sqlite3.Connection] = None,
    ) -> Tuple[Optional[InterviewDecision], List[str]]:
        """Retrieves stored interview decision and skipped fields for a conversation."""
        query = "SELECT interview_status, current_intent, target_field, skipped_fields, last_decision FROM interview_state WHERE conversation_id = ?"
        row = None
        if db:
            row = db.execute(query, (conversation_id,)).fetchone()
        else:
            with get_db() as conn:
                row = conn.execute(query, (conversation_id,)).fetchone()

        if not row:
            return None, []

        skipped: List[str] = []
        if row["skipped_fields"]:
            try:
                skipped = json.loads(row["skipped_fields"])
            except Exception:
                skipped = []

        decision: Optional[InterviewDecision] = None
        if row["last_decision"]:
            try:
                data = json.loads(row["last_decision"])
                decision = InterviewDecision.model_validate(data)
            except Exception:
                decision = None

        return decision, skipped

    @staticmethod
    def save_interview_state(
        conversation_id: str,
        decision: InterviewDecision,
        skipped_fields: List[str],
        db: sqlite3.Connection,
    ) -> None:
        """Persists the latest interview decision and skipped fields into SQLite."""
        now = datetime.now(timezone.utc).isoformat()
        skipped_json = json.dumps(skipped_fields)
        decision_json = json.dumps(decision.model_dump())

        query = """
        INSERT INTO interview_state (
            conversation_id, interview_status, current_intent, target_field, skipped_fields, last_decision, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(conversation_id) DO UPDATE SET
            interview_status = excluded.interview_status,
            current_intent = excluded.current_intent,
            target_field = excluded.target_field,
            skipped_fields = excluded.skipped_fields,
            last_decision = excluded.last_decision,
            updated_at = excluded.updated_at
        """
        db.execute(
            query,
            (
                conversation_id,
                decision.interview_status.value,
                decision.current_intent.value,
                decision.target_field,
                skipped_json,
                decision_json,
                now,
            ),
        )

    def detect_user_signals(
        self,
        user_message: str,
        previous_target_field: Optional[str] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Detects if user asks to pause, or skips/declines to answer the active target field.
        Returns: (is_pause_requested, skipped_field)
        """
        msg_clean = user_message.strip().lower()

        # Check pause
        if msg_clean in PAUSE_PHRASES or any(msg_clean.startswith(p) for p in PAUSE_PHRASES):
            return True, None

        # Check skip / unknown
        for pattern in SKIP_OR_UNKNOWN_PATTERNS:
            if re.search(pattern, msg_clean):
                return False, previous_target_field

        return False, None

    def evaluate_interview_decision(
        self,
        conversation_id: str,
        current_intent: IntentCategory,
        user_message: str,
        confirmed_facts: Dict[str, str],
        db: sqlite3.Connection,
    ) -> InterviewDecision:
        """
        Coordinates interview progression:
        1. Loads previous interview state & skipped fields.
        2. Detects user pause or skip signals.
        3. Invokes deterministic question planner.
        4. Validates backend authority rules.
        5. Saves decision to SQLite.
        """
        prev_decision, skipped_fields = self.get_interview_state(conversation_id, db)
        prev_target = prev_decision.target_field if prev_decision else None

        # Check user conversational signals (pause or skip)
        is_pause, skipped_field = self.detect_user_signals(user_message, prev_target)
        if skipped_field and skipped_field not in skipped_fields:
            skipped_fields = list(skipped_fields) + [skipped_field]

        # Plan next decision
        decision = question_planner.plan_decision(
            intent=current_intent,
            known_facts=confirmed_facts,
            skipped_fields=skipped_fields,
            is_pause_requested=is_pause,
        )

        # Enforce backend authority
        validated_decision = question_planner.validate_decision(decision, confirmed_facts)

        # Persist updated interview state
        self.save_interview_state(
            conversation_id=conversation_id,
            decision=validated_decision,
            skipped_fields=skipped_fields,
            db=db,
        )

        return validated_decision


interview_orchestrator = InterviewOrchestrator()
