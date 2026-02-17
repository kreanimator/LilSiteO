"""Site generation endpoint."""
from fastapi import APIRouter, BackgroundTasks, HTTPException, status

from core.config import Config
from core.models import GenerateResponse
from core.storage import storage

router = APIRouter()


@router.post("/sessions/{session_id}/generate", response_model=GenerateResponse)
async def generate_site(session_id: str, background_tasks: BackgroundTasks):
    """Start site generation for a session."""
    session_dir = storage.get_session_dir(session_id)
    if not session_dir.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )
    
    # Generation will happen via WebSocket stream
    # This endpoint just acknowledges the request
    return GenerateResponse(
        session_id=session_id,
        status="started",
        message="Generation started. Connect to WebSocket for progress."
    )
