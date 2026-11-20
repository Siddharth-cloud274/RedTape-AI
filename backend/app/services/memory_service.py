from datetime import datetime, timezone
from typing import Dict, List, Optional
import sqlite3

from app.schemas.facts import ApplicantFactResponse, ExtractedFactItem
from app.db.database import get_db


class MemoryService:
    """Manages applicant facts, reconciliation, corrections, and persistence."""

    @staticmethod
    def get_confirmed_facts(conversation_id: str, db: sqlite3.Connection = None) -> List[ApplicantFactResponse]:
        """Loads all stored facts for a conversation."""
        query = """
        SELECT field_name, field_value, evidence, confidence_status, updated_at
        FROM applicant_facts
        WHERE conversation_id = ?
        ORDER BY updated_at ASC
        """
        if db:
            rows = db.execute(query, (conversation_id,)).fetchall()
        else:
            with get_db() as conn:
                rows = conn.execute(query, (conversation_id,)).fetchall()

        return [
            ApplicantFactResponse(
                field_name=row["field_name"],
                field_value=row["field_value"],
                evidence=row["evidence"],
                confidence_status=row["confidence_status"],
                updated_at=row["updated_at"],
            )
            for row in rows
        ]

    @staticmethod
    def get_facts_dict(conversation_id: str, db: sqlite3.Connection = None) -> Dict[str, str]:
        """Returns a simple dictionary of field_name -> field_value."""
        facts = MemoryService.get_confirmed_facts(conversation_id, db)
        return {f.field_name: f.field_value for f in facts}

    @staticmethod
    def reconcile_and_save_facts(
        conversation_id: str,
        extracted_facts: List[ExtractedFactItem],
        source_message_id: str,
        db: sqlite3.Connection,
    ) -> List[ApplicantFactResponse]:
        """
        Reconciles incoming facts against stored facts.
        Handles corrections, deduplication, and updates SQLite.
        """
        now = datetime.now(timezone.utc).isoformat()
        current_facts = MemoryService.get_facts_dict(conversation_id, db)

        for fact in extracted_facts:
            norm_name = fact.field_name.strip().lower()
            norm_value = fact.field_value.strip()

            if not norm_name or not norm_value:
                continue

            # Check if value is already identical
            if norm_name in current_facts and current_facts[norm_name].lower() == norm_value.lower():
                # Value is already confirmed and unchanged
                continue

            # Check if this is an explicit correction or update
            confidence = "confirmed"

            # Upsert into applicant_facts
            upsert_query = """
            INSERT INTO applicant_facts (
                conversation_id, field_name, field_value, evidence, source_message_id, confidence_status, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(conversation_id, field_name) DO UPDATE SET
                field_value = excluded.field_value,
                evidence = excluded.evidence,
                source_message_id = excluded.source_message_id,
                confidence_status = excluded.confidence_status,
                updated_at = excluded.updated_at
            """
            db.execute(
                upsert_query,
                (
                    conversation_id,
                    norm_name,
                    norm_value,
                    fact.evidence,
                    source_message_id,
                    confidence,
                    now,
                ),
            )

        return MemoryService.get_confirmed_facts(conversation_id, db)


memory_service = MemoryService()
