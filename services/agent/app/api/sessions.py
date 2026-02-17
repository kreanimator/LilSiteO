"""Session management endpoints."""
from fastapi import APIRouter, HTTPException, status

from core.models import MessageCreate, SessionCreateResponse
from core.storage import storage

router = APIRouter()


@router.post("/sessions", response_model=SessionCreateResponse)
async def create_session():
    """Create a new session."""
    session_id = storage.create_session()
    return SessionCreateResponse(session_id=session_id)


@router.post("/sessions/{session_id}/messages")
async def create_message(session_id: str, message: MessageCreate):
    """Add a message to a session."""
    session_dir = storage.get_session_dir(session_id)
    if not session_dir.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )
    
    storage.add_message(session_id, message.role, message.content)
    return {"status": "ok"}
