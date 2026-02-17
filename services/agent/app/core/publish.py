"""Publish generated sites to preview directory."""
import shutil
from pathlib import Path
from typing import Optional

from core.config import Config


def publish_site(session_id: str, source_dir: Optional[Path] = None) -> Path:
    """
    Publish a site from the session's run directory to the published directory.
    
    Args:
        session_id: Session identifier
        source_dir: Optional source directory (defaults to session's run dir)
    
    Returns:
        Path to the published directory
    """
    if source_dir is None:
        source_dir = Config.RUNS_DIR / session_id
    
    published_dir = Config.PUBLISHED_DIR / session_id
    published_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy all files from source to published
    if source_dir.exists():
        for item in source_dir.iterdir():
            if item.name == "metadata.json":
                continue  # Skip metadata
            dest = published_dir / item.name
            if item.is_file():
                shutil.copy2(item, dest)
            elif item.is_dir():
                shutil.copytree(item, dest, dirs_exist_ok=True)
    
    return published_dir


def get_preview_url(session_id: str, filename: str = "index.html") -> str:
    """Get the preview URL for a published file."""
    return f"/preview/{session_id}/{filename}"
