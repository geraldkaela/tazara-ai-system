from fastapi import APIRouter
from datetime import datetime

router = APIRouter()

@router.get("/")
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "phase": "Phase 3 – Deployment Ready"
    }
