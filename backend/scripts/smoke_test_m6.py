import sys
import os
import uuid

# Add backend directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.session_service import session_manager
from app.schemas.chat import ChatRequest
from app.db.database import get_db, init_db
from app.schemas.interview import InterviewStatus


def main():
    print("=== Milestone M6 Live Adaptive Interview Smoke Test ===")
    init_db()

    # Turn 1: Initial goal
    client_id_1 = str(uuid.uuid4())
    req_1 = ChatRequest(
        conversation_id=None,
        client_message_id=client_id_1,
        message="I need a trade licence for my father's shop.",
    )
    print("\n[Turn 1] User:", req_1.message)
    resp_1 = session_manager.process_message(req_1)
    conv_id = resp_1.conversation_id
    print(f"  -> Assistant Reply: {resp_1.reply[:120]}...")
    print(f"  -> Interview Status: {resp_1.interview.interview_status}")
    print(f"  -> Target Field: {resp_1.interview.target_field}")
    print(f"  -> Missing Context: {resp_1.interview.missing_context}")

    # Turn 2: Provide business type & location
    client_id_2 = str(uuid.uuid4())
    req_2 = ChatRequest(
        conversation_id=conv_id,
        client_message_id=client_id_2,
        message="It's a grocery shop in Barrackpore.",
    )
    print("\n[Turn 2] User:", req_2.message)
    resp_2 = session_manager.process_message(req_2)
    print(f"  -> Assistant Reply: {resp_2.reply[:120]}...")
    print(f"  -> Interview Status: {resp_2.interview.interview_status}")
    print(f"  -> Known Fields: {resp_2.interview.known_fields}")
    print(f"  -> Target Field: {resp_2.interview.target_field}")
    print(f"  -> Missing Context: {resp_2.interview.missing_context}")

    # Turn 3: Provide application type & rented details
    client_id_3 = str(uuid.uuid4())
    req_3 = ChatRequest(
        conversation_id=conv_id,
        client_message_id=client_id_3,
        message="It's a new application and the shop is rented.",
    )
    print("\n[Turn 3] User:", req_3.message)
    resp_3 = session_manager.process_message(req_3)
    print(f"  -> Assistant Reply: {resp_3.reply[:140]}...")
    print(f"  -> Final Interview Status: {resp_3.interview.interview_status}")
    print(f"  -> Next Action: {resp_3.interview.next_action}")
    print(f"  -> Missing Context: {resp_3.interview.missing_context}")

    # Verify stopping condition
    assert resp_3.interview.interview_status == InterviewStatus.READY_FOR_RESEARCH, (
        f"Expected READY_FOR_RESEARCH, got {resp_3.interview.interview_status}"
    )
    print("\nSUCCESS: Adaptive Interview Engine successfully collected scoping context and reached ready_for_research stopping condition!")


if __name__ == "__main__":
    main()
