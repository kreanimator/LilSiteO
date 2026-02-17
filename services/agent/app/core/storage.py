"""Session storage and management."""
import json
import uuid
from pathlib import Path
from typing import Dict, List, Optional

from core.config import Config


class SessionStorage:
    """Simple file-based session storage."""
    
    def __init__(self):
        self.sessions_dir = Config.RUNS_DIR
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
    
    def create_session(self) -> str:
        """Create a new session and return its ID."""
        session_id = str(uuid.uuid4())[:8]
        session_dir = self.sessions_dir / session_id
        session_dir.mkdir(exist_ok=True)
        
        # Initialize session metadata
        metadata = {
            "session_id": session_id,
            "created_at": None,
            "messages": [],
            "status": "active"
        }
        self._save_metadata(session_id, metadata)
        return session_id
    
    def get_session_dir(self, session_id: str) -> Path:
        """Get the working directory for a session."""
        return self.sessions_dir / session_id
    
    def add_message(self, session_id: str, role: str, content: str):
        """Add a message to the session."""
        metadata = self._load_metadata(session_id)
        if metadata is None:
            return
        
        metadata["messages"].append({
            "role": role,
            "content": content
        })
        self._save_metadata(session_id, metadata)
    
    def get_messages(self, session_id: str) -> List[Dict[str, str]]:
        """Get all messages for a session."""
        metadata = self._load_metadata(session_id)
        if metadata is None:
            return []
        return metadata.get("messages", [])
    
    def _metadata_path(self, session_id: str) -> Path:
        """Get path to session metadata file."""
        return self.sessions_dir / session_id / "metadata.json"
    
    def _load_metadata(self, session_id: str) -> Optional[Dict]:
        """Load session metadata."""
        path = self._metadata_path(session_id)
        if not path.exists():
            return None
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception:
            return None
    
    def _save_metadata(self, session_id: str, metadata: Dict):
        """Save session metadata."""
        path = self._metadata_path(session_id)
        with open(path, "w") as f:
            json.dump(metadata, f, indent=2)


# Global storage instance
storage = SessionStorage()
