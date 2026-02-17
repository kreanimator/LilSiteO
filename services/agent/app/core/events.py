"""Event types for WebSocket streaming."""
from typing import Any, Dict, Literal

EventType = Literal[
    "log",
    "assistant_message",
    "assistant_token",
    "artifact_published",
    "error",
    "status"
]


def create_event(
    event_type: EventType,
    **kwargs: Any
) -> Dict[str, Any]:
    """Create a WebSocket event dictionary."""
    return {
        "type": event_type,
        **kwargs
    }


def log_event(message: str) -> Dict[str, Any]:
    """Create a log event."""
    return create_event("log", message=message)


def assistant_message_event(content: str) -> Dict[str, Any]:
    """Create an assistant message event."""
    return create_event("assistant_message", content=content)


def assistant_token_event(delta: str) -> Dict[str, Any]:
    """Create an assistant token event."""
    return create_event("assistant_token", delta=delta)


def artifact_published_event(preview_url: str) -> Dict[str, Any]:
    """Create an artifact published event."""
    return create_event("artifact_published", preview_url=preview_url)


def error_event(message: str) -> Dict[str, Any]:
    """Create an error event."""
    return create_event("error", message=message)


def status_event(status: str) -> Dict[str, Any]:
    """Create a status event."""
    return create_event("status", status=status)
