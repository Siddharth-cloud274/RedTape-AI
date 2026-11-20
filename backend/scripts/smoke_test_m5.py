import sys
import os
import uuid

# Add backend directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.session_service import session_manager
from app.schemas.chat import ChatRequest
from app.db.database import get_db, init_db


def main():
    print("=== Milestone M5 Live Memory & Fact Smoke Test ===")
    init_db()

    # Turn 1
    client_id_1 = str(uuid.uuid4())
    req_1 = ChatRequest(
        conversation_id=None,
        client_message_id=client_id_1,
        message="I need an income certificate for college admission. I live in Kolkata.",
    )
    print("\n[Turn 1] Sending message:", req_1.message)
    resp_1 = session_manager.process_message(req_1)
    conv_id = resp_1.conversation_id
    print(f"  -> Conversation ID: {conv_id}")
    print(f"  -> Assistant reply: {resp_1.reply[:120]}...")
    print(f"  -> Extracted facts count: {len(resp_1.facts or [])}")
    for f in resp_1.facts or []:
        print(f"     * {f.field_name}: {f.field_value} (evidence: {f.evidence})")

    # Turn 2: Correction
    client_id_2 = str(uuid.uuid4())
    req_2 = ChatRequest(
        conversation_id=conv_id,
        client_message_id=client_id_2,
        message="Actually, I live in Howrah.",
    )
    print("\n[Turn 2] Sending correction:", req_2.message)
    resp_2 = session_manager.process_message(req_2)
    print(f"  -> Assistant reply: {resp_2.reply[:120]}...")
    print(f"  -> Reconciled facts count: {len(resp_2.facts or [])}")
    for f in resp_2.facts or []:
        print(f"     * {f.field_name}: {f.field_value} (evidence: {f.evidence})")

    # Verify directly in SQLite
    with get_db() as db:
        conv = db.execute("SELECT * FROM conversations WHERE id = ?", (conv_id,)).fetchone()
        assert conv is not None
        print(f"\n[SQLite Verification] Conversation current_intent: {conv['current_intent']}")

        msgs = db.execute(
            "SELECT role, content FROM messages WHERE conversation_id = ? ORDER BY created_at ASC, rowid ASC",
            (conv_id,),
        ).fetchall()
        print(f"[SQLite Verification] Total stored messages: {len(msgs)}")
        for m in msgs:
            print(f"  - [{m['role']}]: {m['content'][:60]}...")

        facts = db.execute(
            "SELECT field_name, field_value FROM applicant_facts WHERE conversation_id = ?",
            (conv_id,),
        ).fetchall()
        print(f"[SQLite Verification] Stored unique facts: {len(facts)}")
        for f in facts:
            print(f"  - {f['field_name']}: {f['field_value']}")

        # Ensure location is reconciled to Howrah
        loc = next((f["field_value"] for f in facts if f["field_name"] == "location"), None)
        assert loc == "Howrah", f"Expected location 'Howrah', got '{loc}'"
        print("\nSUCCESS: Fact correction reconciled perfectly to Howrah in SQLite!")


if __name__ == "__main__":
    main()
