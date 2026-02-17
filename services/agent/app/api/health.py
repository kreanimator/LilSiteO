"""Health check endpoint."""
import httpx
from fastapi import APIRouter

from core.config import Config
from core.models import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Check API and LLM server health."""
    llm_connected = False
    
    # Try to connect to LLM server
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(f"{Config.LLM_BASE_URL}/health")
            llm_connected = response.status_code == 200
    except Exception:
        pass
    
    return HealthResponse(
        status="ok",
        llm_connected=llm_connected
    )
