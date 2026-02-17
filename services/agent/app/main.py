"""FastAPI main application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pathlib import Path

from api import generate, health, sessions
from core.config import Config
from ws import stream

app = FastAPI(
    title="LilSite-o Agent",
    description="A tiny AI agent that builds static websites from prompts",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(sessions.router)
app.include_router(generate.router)
app.include_router(stream.router)


@app.get("/preview/{session_id}/{filename:path}")
async def serve_preview(session_id: str, filename: str):
    """Serve published preview files."""
    from fastapi import HTTPException, status
    
    file_path = Config.PUBLISHED_DIR / session_id / filename
    
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # Security: ensure file is within published directory
    try:
        file_path.resolve().relative_to(Config.PUBLISHED_DIR.resolve())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid path"
        )
    
    return FileResponse(file_path)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "LilSite-o Agent",
        "version": "0.1.0",
        "status": "running"
    }
