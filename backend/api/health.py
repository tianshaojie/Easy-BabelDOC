from fastapi import APIRouter
from pathlib import Path

router = APIRouter(prefix="/api", tags=["health"])

@router.get("/health")
async def health_check():
    """Health check endpoint for the packaged application."""
    from config.settings import FRONTEND_STATIC_DIR, DATA_DIR
    
    return {
        "status": "ok",
        "version": "1.0.0",
        "frontend_ready": FRONTEND_STATIC_DIR.exists(),
        "data_dir": str(DATA_DIR),
    }

@router.get("")
async def api_root():
    return {"message": "BabelDOC API Server", "version": "1.0.0"}
