"""Session management endpoints."""
from fastapi import APIRouter, HTTPException, status

from core.models import MessageCreate, SessionCreateResponse
from core.storage import storage
from llm.client import LLMClient
from llm.prompts import get_chat_response_prompt

router = APIRouter()


@router.post("/sessions", response_model=SessionCreateResponse)
async def create_session():
    """Create a new session."""
    session_id = storage.create_session()
    return SessionCreateResponse(session_id=session_id)


@router.post("/sessions/{session_id}/messages")
async def create_message(session_id: str, message: MessageCreate):
    """Add a message to a session and get agent response if it's a user message."""
    session_dir = storage.get_session_dir(session_id)
    if not session_dir.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )
    
    storage.add_message(session_id, message.role, message.content)
    
    # If it's a user message, generate an agent response
    if message.role == "user":
        try:
            messages = storage.get_messages(session_id)
            prompt_messages = get_chat_response_prompt(message.content, messages[:-1])  # Exclude current message
            
            llm = LLMClient()
            response = llm.chat(prompt_messages, temperature=0.7, max_tokens=500)
            
            # Store assistant response
            storage.add_message(session_id, "assistant", response)
            
            return {
                "status": "ok",
                "assistant_response": response
            }
        except Exception as e:
            # If LLM fails, still return ok (message was stored)
            return {
                "status": "ok",
                "error": str(e)
            }
    
    return {"status": "ok"}
