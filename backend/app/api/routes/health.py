from fastapi import APIRouter
from app.schemas.health import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Return backend health and service information."""
    return HealthResponse(
        service="RedTape AI Backend",
        status="healthy",
        version="0.1.0"
    )
