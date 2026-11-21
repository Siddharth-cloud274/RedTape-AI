import os
import sqlite3
from contextlib import contextmanager
from typing import Generator

DEFAULT_DB_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "redtape.db")
)


def get_db_path() -> str:
    """Returns database path from environment or default."""
    return os.environ.get("REDTAPE_DB_PATH", DEFAULT_DB_PATH)


def get_connection(db_path: str = None) -> sqlite3.Connection:
    """Creates a configured sqlite3 connection with WAL mode and foreign keys enabled."""
    path = db_path or get_db_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    conn = sqlite3.connect(path, timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


@contextmanager
def get_db(db_path: str = None) -> Generator[sqlite3.Connection, None, None]:
    """Context manager for database connections ensuring proper commit and cleanup."""
    conn = get_connection(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db_path: str = None) -> None:
    """Initializes SQLite schema, tables, and indexes."""
    schema_sql = """
    CREATE TABLE IF NOT EXISTS conversations (
        id TEXT PRIMARY KEY,
        title TEXT,
        current_intent TEXT,
        intent_status TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS messages (
        id TEXT PRIMARY KEY,
        conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
        client_message_id TEXT,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        mode TEXT,
        processing_status TEXT NOT NULL,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS applicant_facts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
        field_name TEXT NOT NULL,
        field_value TEXT NOT NULL,
        evidence TEXT,
        source_message_id TEXT,
        confidence_status TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        UNIQUE(conversation_id, field_name)
    );

    CREATE TABLE IF NOT EXISTS interview_state (
        conversation_id TEXT PRIMARY KEY REFERENCES conversations(id) ON DELETE CASCADE,
        interview_status TEXT NOT NULL,
        current_intent TEXT,
        target_field TEXT,
        skipped_fields TEXT,
        last_decision TEXT,
        updated_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS generated_documents (
        id TEXT PRIMARY KEY,
        conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
        template_id TEXT NOT NULL,
        version INTEGER NOT NULL DEFAULT 1,
        status TEXT NOT NULL,
        file_path TEXT NOT NULL,
        missing_fields TEXT,
        metadata_json TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS application_reviews (
        id TEXT PRIMARY KEY,
        conversation_id TEXT NOT NULL UNIQUE REFERENCES conversations(id) ON DELETE CASCADE,
        service_id TEXT NOT NULL,
        review_status TEXT NOT NULL,
        latest_document_id TEXT REFERENCES generated_documents(id),
        latest_document_version INTEGER,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS review_approvals (
        id TEXT PRIMARY KEY,
        review_id TEXT NOT NULL REFERENCES application_reviews(id) ON DELETE CASCADE,
        conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
        document_id TEXT,
        document_version INTEGER,
        document_hash TEXT,
        facts_snapshot_hash TEXT,
        status TEXT NOT NULL, -- 'active' | 'invalidated'
        invalidation_reason TEXT,
        approved_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS review_audit_log (
        id TEXT PRIMARY KEY,
        conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
        review_id TEXT NOT NULL,
        document_version INTEGER,
        event_type TEXT NOT NULL,
        state_from TEXT,
        state_to TEXT,
        payload_json TEXT,
        created_at TEXT NOT NULL
    );

    CREATE INDEX IF NOT EXISTS idx_messages_conv ON messages(conversation_id, created_at ASC);
    CREATE INDEX IF NOT EXISTS idx_messages_client_id ON messages(conversation_id, client_message_id);
    CREATE INDEX IF NOT EXISTS idx_facts_conv ON applicant_facts(conversation_id);
    CREATE INDEX IF NOT EXISTS idx_docs_conv ON generated_documents(conversation_id);
    CREATE INDEX IF NOT EXISTS idx_reviews_conv ON application_reviews(conversation_id);
    CREATE INDEX IF NOT EXISTS idx_approvals_rev ON review_approvals(review_id);
    CREATE INDEX IF NOT EXISTS idx_audit_conv ON review_audit_log(conversation_id);
    """
    with get_db(db_path) as conn:
        conn.executescript(schema_sql)
