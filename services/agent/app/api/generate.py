"""Site generation endpoint."""
import json
from fastapi import APIRouter, HTTPException, status
from fastapi import WebSocket

from core.config import Config
from core.models import GenerateResponse
from core.storage import storage

router = APIRouter()

# Import active connections (defined in ws/stream.py)
try:
    from ws.stream import _active_connections
except ImportError:
    _active_connections: dict[str, WebSocket] = {}


@router.post("/sessions/{session_id}/generate", response_model=GenerateResponse)
async def generate_site(session_id: str):
    """Start site generation for a session."""
    session_dir = storage.get_session_dir(session_id)
    if not session_dir.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )
    
    # If WebSocket is connected, send generate command
    try:
        from ws.stream import _active_connections
        websocket = _active_connections.get(session_id)
        if websocket:
            try:
                await websocket.send_json({"action": "generate"})
            except Exception:
                pass  # WebSocket might be closed
    except Exception:
        pass
    
    return GenerateResponse(
        session_id=session_id,
        status="started",
        message="Generation started. Check WebSocket for progress."
    )
