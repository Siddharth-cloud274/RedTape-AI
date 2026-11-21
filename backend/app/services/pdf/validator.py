import re
from typing import Dict, List, Optional, Tuple
import sqlite3

from app.db.database import get_db
from app.schemas.document import DocumentReadinessCheck, DocumentReadinessStatus
from app.services.pdf.mappings.kolkata_domicile import KOLKATA_DOMICILE_FIELD_MAP, REQUIRED_FIELDS


def get_conversation_facts(conversation_id: str, db: sqlite3.Connection = None) -> Dict[str, str]:
    """Retrieves all confirmed facts for a conversation from the database."""
    def _fetch(conn: sqlite3.Connection) -> Dict[str, str]:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT field_name, field_value FROM applicant_facts WHERE conversation_id = ?",
            (conversation_id,),
        )
        return {row[0]: row[1] for row in cursor.fetchall()}

    if db is not None:
        return _fetch(db)
    with get_db() as conn:
        return _fetch(conn)


def resolve_field_value(field_name: str, facts: Dict[str, str], custom_overrides: Optional[Dict[str, str]] = None) -> Optional[str]:
    """Resolves a field's value from custom overrides, canonical facts, or known aliases."""
    if custom_overrides and field_name in custom_overrides and custom_overrides[field_name]:
        return str(custom_overrides[field_name]).strip()

    # Direct match in facts
    if field_name in facts and facts[field_name]:
        return str(facts[field_name]).strip()

    # Check aliases defined in mapping
    config = KOLKATA_DOMICILE_FIELD_MAP.get(field_name, {})
    aliases = config.get("aliases", [])
    for alias in aliases:
        if custom_overrides and alias in custom_overrides and custom_overrides[alias]:
            return str(custom_overrides[alias]).strip()
        if alias in facts and facts[alias]:
            return str(facts[alias]).strip()

    # Check default if any
    return config.get("default")


def check_kolkata_jurisdiction(facts: Dict[str, str], custom_overrides: Optional[Dict[str, str]] = None) -> Tuple[bool, Optional[str]]:
    """
    Checks if the applicant's location or address falls under Kolkata Collectorate.
    Returns (is_valid, warning_or_reason).
    """
    merged = {**facts, **(custom_overrides or {})}
    location = (merged.get("business_location") or merged.get("location") or merged.get("district") or merged.get("present_address") or "").lower()

    if not location:
        # Not yet specified - unverified
        return True, "Jurisdiction not yet explicitly confirmed, defaulting to Kolkata Collectorate."

    kolkata_keywords = ["kolkata", "calcutta", "alipore", "bowbazar", "bhowanipore", "tollygunge", "park street", "salt lake", "700"]
    non_kolkata_districts = ["barrackpore", "howrah", "hooghly", "darjeeling", "siliguri", "nadia", "murshidabad", "malda", "jalpaiguri", "bardhaman", "burdwan", "asansol", "durgapur", "purulia", "bankura", "medinipur", "birbhum", "cooch behar"]

    for kw in kolkata_keywords:
        if kw in location:
            return True, None

    for dist in non_kolkata_districts:
        if dist in location:
            return False, f"Applicant location '{location}' falls outside Kolkata Collectorate jurisdiction ({dist.title()})."

    # Default to true with note if indeterminate
    return True, None


def validate_document_readiness(
    conversation_id: str,
    template_id: str = "kolkata_domicile_higher_studies",
    custom_overrides: Optional[Dict[str, str]] = None,
    db: sqlite3.Connection = None,
) -> DocumentReadinessCheck:
    """Evaluates whether sufficient applicant facts exist to generate a verified PDF draft."""
    facts = get_conversation_facts(conversation_id, db=db)
    is_jurisdiction_valid, _ = check_kolkata_jurisdiction(facts, custom_overrides)

    present_fields: Dict[str, str] = {}
    missing_required: List[str] = []

    for field in REQUIRED_FIELDS:
        val = resolve_field_value(field, facts, custom_overrides)
        if val:
            present_fields[field] = val
        else:
            missing_required.append(field)

    # Collect all available fields in mapping
    for field in KOLKATA_DOMICILE_FIELD_MAP.keys():
        if field not in present_fields:
            val = resolve_field_value(field, facts, custom_overrides)
            if val:
                present_fields[field] = val

    if not is_jurisdiction_valid:
        status = DocumentReadinessStatus.JURISDICTION_UNVERIFIED
        can_generate = False
    elif missing_required:
        status = DocumentReadinessStatus.COLLECTING_DOCUMENT_DETAILS
        can_generate = False
    else:
        status = DocumentReadinessStatus.READY_FOR_DRAFT
        can_generate = True

    return DocumentReadinessCheck(
        can_generate=can_generate,
        readiness_status=status,
        template_id=template_id,
        jurisdiction_verified=is_jurisdiction_valid,
        missing_required_fields=missing_required,
        present_fields=present_fields,
    )
