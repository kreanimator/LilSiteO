"""WebSocket streaming endpoint for generation."""
import json
from pathlib import Path

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, status

from core.config import Config
from core.events import (
    artifact_published_event,
    assistant_message_event,
    assistant_token_event,
    error_event,
    log_event,
)
from core.publish import get_preview_url, publish_site
from core.storage import storage
from llm.client import LLMClient, LLMError
from llm.prompts import get_site_generation_prompt
from tools.site_writer import write_site_file
from tools.validator import validate_site

router = APIRouter()


async def generate_site_stream(websocket: WebSocket, session_id: str):
    """Generate a site and stream progress via WebSocket."""
    session_dir = storage.get_session_dir(session_id)
    if not session_dir.exists():
        await websocket.send_json(error_event(f"Session {session_id} not found"))
        return
    
    try:
        # Get conversation history
        messages = storage.get_messages(session_id)
        
        # Get the last user message or use a default prompt
        user_prompt = "Generate a simple landing page"
        if messages:
            for msg in reversed(messages):
                if msg.get("role") == "user":
                    user_prompt = msg.get("content", user_prompt)
                    break
        
        await websocket.send_json(log_event(f"Starting generation for: {user_prompt}"))
        
        # Initialize LLM client
        llm = LLMClient()
        
        # Build prompt
        prompt_messages = get_site_generation_prompt(user_prompt, messages)
        
        await websocket.send_json(log_event("Calling LLM..."))
        
        # Stream LLM response
        full_response = ""
        for delta in llm.stream_chat(prompt_messages, temperature=0.7, max_tokens=4000):
            await websocket.send_json(assistant_token_event(delta))
            full_response += delta
        
        if not full_response.strip():
            await websocket.send_json(error_event("LLM returned empty response"))
            return
        
        await websocket.send_json(log_event("Writing site files..."))
        
        # Write HTML file
        html_file = write_site_file(session_dir, full_response)
        await websocket.send_json(log_event(f"Wrote {html_file.name}"))
        
        # Validate
        is_valid, errors = validate_site(session_dir)
        if not is_valid:
            await websocket.send_json(log_event(f"Validation warnings: {', '.join(errors)}"))
        else:
            await websocket.send_json(log_event("Site validated successfully"))
        
        # Publish
        published_dir = publish_site(session_id, session_dir)
        await websocket.send_json(log_event(f"Published to {published_dir}"))
        
        # Get preview URL (use localhost for preview since UI runs separately)
        preview_url = get_preview_url(session_id, "index.html")
        # Use localhost:9000 as default (matches README)
        api_base = f"http://localhost:{Config.API_PORT}"
        full_preview_url = f"{api_base}{preview_url}"
        
        # Send completion event
        await websocket.send_json(artifact_published_event(full_preview_url))
        await websocket.send_json(log_event("Generation complete!"))
        
    except LLMError as e:
        await websocket.send_json(error_event(f"LLM error: {str(e)}"))
    except Exception as e:
        await websocket.send_json(error_event(f"Generation failed: {str(e)}"))




@router.websocket("/sessions/{session_id}/stream")
async def websocket_stream(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for streaming generation progress."""
    await websocket.accept()
    
    try:
        # Check if session exists
        session_dir = storage.get_session_dir(session_id)
        if not session_dir.exists():
            await websocket.send_json(error_event(f"Session {session_id} not found"))
            await websocket.close()
            return
        
        # Auto-start generation when WebSocket connects (if messages exist)
        messages = storage.get_messages(session_id)
        if messages:
            # Auto-start generation if there are messages
            await generate_site_stream(websocket, session_id)
        else:
            # Wait for generate command via WebSocket message
            await websocket.send_json(log_event("Connected. Send 'generate' to start, or add a message first."))
            try:
                while True:
                    data = await websocket.receive_text()
                    # Trigger generation on "generate" command
                    if data.strip().lower() == "generate":
                        await generate_site_stream(websocket, session_id)
                        break
            except WebSocketDisconnect:
                pass
        
    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json(error_event(f"Unexpected error: {str(e)}"))
        except Exception:
            pass
