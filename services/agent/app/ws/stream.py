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
from tools.site_writer import write_multiple_pages
from tools.validator import validate_site

router = APIRouter()


async def generate_site_stream(websocket: WebSocket, session_id: str):
    """Generate a site and stream progress via WebSocket."""
    session_dir = storage.get_session_dir(session_id)
    if not session_dir.exists():
        await websocket.send_json(error_event(f"Session {session_id} not found"))
        return
    
    try:
        # Get ALL conversation history for full context
        messages = storage.get_messages(session_id)
        
        # Build context summary
        user_messages = [msg for msg in messages if msg.get("role") == "user"]
        if user_messages:
            user_prompt = user_messages[-1].get("content", "Generate a simple landing page")
            context_info = f"Based on {len(user_messages)} user message(s)"
        else:
            user_prompt = "Generate a simple landing page"
            context_info = "No previous messages"
        
        # Send initial assistant message with context
        await websocket.send_json(assistant_message_event(
            f"🚀 Starting generation...\n"
            f"📋 Context: {context_info}\n"
            f"💬 Latest request: {user_prompt[:100]}{'...' if len(user_prompt) > 100 else ''}"
        ))
        await websocket.send_json(log_event(f"Starting generation with full context ({len(messages)} messages)"))
        
        # Initialize LLM client
        await websocket.send_json(assistant_message_event("📡 Connecting to LLM..."))
        await websocket.send_json(log_event("Connecting to LLM..."))
        llm = LLMClient()
        
        # Build prompt
        prompt_messages = get_site_generation_prompt(user_prompt, messages)
        
        await websocket.send_json(assistant_message_event("🤖 Generating website code..."))
        await websocket.send_json(log_event("Calling LLM..."))
        
        # Stream LLM response
        full_response = ""
        token_count = 0
        for delta in llm.stream_chat(prompt_messages, temperature=0.7, max_tokens=4000):
            await websocket.send_json(assistant_token_event(delta))
            full_response += delta
            token_count += 1
            # Send progress update every 50 tokens
            if token_count % 50 == 0:
                await websocket.send_json(log_event(f"Generated {token_count} tokens..."))
        
        if not full_response.strip():
            await websocket.send_json(assistant_message_event("❌ LLM returned empty response"))
            await websocket.send_json(error_event("LLM returned empty response"))
            return
        
        await websocket.send_json(assistant_message_event(f"✅ Generated {token_count} tokens. Writing files..."))
        await websocket.send_json(log_event("Writing site files..."))
        
        # Write HTML files (may be multiple pages)
        written_files = write_multiple_pages(session_dir, full_response)
        
        if len(written_files) > 1:
            await websocket.send_json(assistant_message_event(f"📝 Wrote {len(written_files)} pages: {', '.join(f.name for f in written_files)}"))
            await websocket.send_json(log_event(f"Wrote {len(written_files)} pages: {', '.join(f.name for f in written_files)}"))
        else:
            await websocket.send_json(assistant_message_event(f"📝 Wrote {written_files[0].name}"))
            await websocket.send_json(log_event(f"Wrote {written_files[0].name}"))
        
        # Validate
        await websocket.send_json(assistant_message_event("🔍 Validating site..."))
        await websocket.send_json(log_event("Validating site..."))
        is_valid, errors = validate_site(session_dir)
        if not is_valid:
            await websocket.send_json(assistant_message_event(f"⚠️ Validation warnings: {', '.join(errors)}"))
            await websocket.send_json(log_event(f"Validation warnings: {', '.join(errors)}"))
        else:
            await websocket.send_json(assistant_message_event("✅ Site validated successfully"))
            await websocket.send_json(log_event("Site validated successfully"))
        
        # Publish
        await websocket.send_json(assistant_message_event("📦 Publishing site..."))
        await websocket.send_json(log_event("Publishing site..."))
        published_dir = publish_site(session_id, session_dir)
        await websocket.send_json(assistant_message_event(f"✅ Published to preview"))
        await websocket.send_json(log_event(f"Published to {published_dir}"))
        
        # Get preview URL (use localhost for preview since UI runs separately)
        preview_url = get_preview_url(session_id, "index.html")
        # Use localhost:9000 as default (matches README)
        api_base = f"http://localhost:{Config.API_PORT}"
        full_preview_url = f"{api_base}{preview_url}"
        
        # Send completion event
        await websocket.send_json(assistant_message_event("🎉 Generation complete! Preview is ready."))
        await websocket.send_json(artifact_published_event(full_preview_url))
        await websocket.send_json(log_event("Generation complete!"))
        
    except LLMError as e:
        await websocket.send_json(error_event(f"LLM error: {str(e)}"))
    except Exception as e:
        await websocket.send_json(error_event(f"Generation failed: {str(e)}"))




# Store active WebSocket connections per session
_active_connections: dict[str, WebSocket] = {}


@router.websocket("/sessions/{session_id}/stream")
async def websocket_stream(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for streaming generation progress."""
    await websocket.accept()
    _active_connections[session_id] = websocket
    
    try:
        # Check if session exists
        session_dir = storage.get_session_dir(session_id)
        if not session_dir.exists():
            await websocket.send_json(error_event(f"Session {session_id} not found"))
            await websocket.close()
            return
        
        await websocket.send_json(log_event("WebSocket connected. Ready for generation."))
        
        # Wait for generate command or auto-start if messages exist
        messages = storage.get_messages(session_id)
        if messages:
            # Auto-start generation if there are messages
            await websocket.send_json(assistant_message_event("💬 I see your message! Starting generation..."))
            await websocket.send_json(log_event("Messages found. Starting generation..."))
            await generate_site_stream(websocket, session_id)
        else:
            # Send welcome message telling user to press Generate
            await websocket.send_json(assistant_message_event(
                "👋 Hello! I'm ready to generate a website for you.\n\n"
                "📝 **How to use:**\n"
                "1. Type your website description in the chat\n"
                "2. Click **Send** to save your message\n"
                "3. Click **Generate** to start building your site\n\n"
                "I'll create a complete static website with HTML, CSS, and any needed pages!"
            ))
            await websocket.send_json(log_event("Waiting for user to send message and click Generate..."))
            # Wait for generate command via WebSocket message
            try:
                while True:
                    data = await websocket.receive_text()
                    try:
                        msg = json.loads(data)
                        if msg.get("action") == "generate":
                            await generate_site_stream(websocket, session_id)
                            break
                    except json.JSONDecodeError:
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
    finally:
        _active_connections.pop(session_id, None)