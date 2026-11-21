from typing import Optional
from fastapi import APIRouter, HTTPException, status

from app.schemas.review import (
    ApprovalRequest,
    ApprovalResponse,
    HandoffActionRequest,
    HandoffGuidanceResponse,
    ReviewChangesRequest,
    ReviewSummaryResponse,
)
from app.services.review_service import review_service, ReviewServiceError

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.get("/{conversation_id}", response_model=ReviewSummaryResponse)
async def get_review(conversation_id: str):
    """Retrieves current application review summary, draft versions, requirements, and approval status."""
    try:
        return review_service.get_review_summary(conversation_id)
    except ReviewServiceError as rse:
        raise HTTPException(status_code=rse.status_code, detail=rse.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch review: {str(e)}")


@router.post("/{conversation_id}/approve", response_model=ApprovalResponse)
async def approve_review(conversation_id: str, request: ApprovalRequest):
    """
    Records explicit user consent and approves a specific document draft version for personal use.
    Requires explicit opt-in checkboxes; rejects stale draft versions.
    """
    try:
        return review_service.record_approval(conversation_id, request)
    except ReviewServiceError as rse:
        raise HTTPException(status_code=rse.status_code, detail=rse.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Approval failed: {str(e)}")


@router.post("/{conversation_id}/request-changes")
async def request_changes(conversation_id: str, request: ReviewChangesRequest):
    """Reopens the application review for corrections and invalidates prior approvals."""
    try:
        return review_service.request_changes(conversation_id, request)
    except ReviewServiceError as rse:
        raise HTTPException(status_code=rse.status_code, detail=rse.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to request changes: {str(e)}")


@router.get("/{conversation_id}/handoff", response_model=HandoffGuidanceResponse)
async def get_handoff(conversation_id: str):
    """Retrieves verified online portal or offline submission instructions for the approved application."""
    try:
        return review_service.get_handoff_guidance(conversation_id)
    except ReviewServiceError as rse:
        raise HTTPException(status_code=rse.status_code, detail=rse.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch handoff: {str(e)}")


@router.post("/{conversation_id}/handoff/action")
async def record_handoff_action(conversation_id: str, request: HandoffActionRequest):
    """Records user action (opening external portal or downloading final pack) into audit trail."""
    try:
        return review_service.record_handoff_action(
            conversation_id, action=request.action, target_url=request.url_target
        )
    except ReviewServiceError as rse:
        raise HTTPException(status_code=rse.status_code, detail=rse.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record action: {str(e)}")
