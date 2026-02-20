
import logging
from fastapi import APIRouter
from datetime import datetime
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
@router.get("/")
def health_check():
    """
    Health check endpoint.
    
    Returns:
        Health status information
    """
    logger.info("Health check requested")
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


@router.get("/readiness")
def readiness_check():
    """
    Readiness check endpoint.
    Indicates if the service is ready to handle requests.
    
    Returns:
        Readiness status
    """
    logger.info("Readiness check requested")
    return {
        "ready": True,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/liveness")
def liveness_check():
    """
    Liveness check endpoint.
    Indicates if the service is running.
    
    Returns:
        Liveness status
    """
    logger.info("Liveness check requested")
    return {
        "alive": True,
        "timestamp": datetime.utcnow().isoformat()
    }
