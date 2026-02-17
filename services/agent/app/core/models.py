"""Pydantic models for API requests/responses."""
from typing import List, Optional

from pydantic import BaseModel, Field


class SessionCreateResponse(BaseModel):
    """Response for session creation."""
    session_id: str


class MessageCreate(BaseModel):
    """Request to create a message."""
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")


class GenerateResponse(BaseModel):
    """Response for generation request."""
    session_id: str
    status: str = "started"
    message: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "ok"
    llm_connected: bool = False
