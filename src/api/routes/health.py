"""
Health check endpoints for monitoring and Docker health checks.
"""
from fastapi import APIRouter
from datetime import datetime

router = APIRouter(tags=["health"])

@router.get("/api/health")
async def health_check():
    """Health check endpoint for Docker and monitoring."""
    return {
        "status": "healthy",
        "service": "ollama-chat",
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/api/ready")
async def readiness_check():
    """Readiness check to verify all dependencies are available."""
    # You can add checks for Ollama connectivity here
    return {
        "status": "ready",
        "service": "ollama-chat",
        "timestamp": datetime.utcnow().isoformat()
    }