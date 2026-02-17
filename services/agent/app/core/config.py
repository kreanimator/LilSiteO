"""Configuration for LilSite-o agent."""
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Load .env from project root
env_path = Path(__file__).parent.parent.parent.parent.parent / ".env"
load_dotenv(env_path)


class Config:
    """Application configuration."""
    
    # LLM settings
    LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "http://localhost:8000").rstrip("/")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "deepseek-ai/DeepSeek-Coder-6.7B-Instruct")
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "EMPTY")
    LLM_TIMEOUT_S: float = float(os.getenv("LLM_TIMEOUT_S", "300"))  # 5 minutes for generation
    
    # Server settings
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "9000"))
    
    # Runtime paths
    PROJECT_ROOT: Path = Path(__file__).parent.parent.parent.parent.parent
    RUNTIME_DIR: Path = PROJECT_ROOT / "runtime"
    RUNS_DIR: Path = RUNTIME_DIR / "runs"
    PUBLISHED_DIR: Path = RUNTIME_DIR / "published"
    LOGS_DIR: Path = RUNTIME_DIR / "logs"
    
    @classmethod
    def ensure_dirs(cls):
        """Create runtime directories if they don't exist."""
        cls.RUNTIME_DIR.mkdir(exist_ok=True)
        cls.RUNS_DIR.mkdir(exist_ok=True)
        cls.PUBLISHED_DIR.mkdir(exist_ok=True)
        cls.LOGS_DIR.mkdir(exist_ok=True)


# Initialize directories on import
Config.ensure_dirs()
