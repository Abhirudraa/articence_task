"""
API routes for bonus features: Authentication, Webhooks, Export, Redis Caching, etc.
"""

import logging
import json
from fastapi import APIRouter, HTTPException, Header, BackgroundTasks
from fastapi.responses import StreamingResponse, JSONResponse
from typing import Optional, Dict, Any, List
from datetime import datetime
from app.services.auth_service import auth_service
from app.services.webhook_service import webhook_service
from app.services.export_service import export_service
from app.services.cache_service import cache_service
from app.services.rate_limiter import rate_limiter
from app.models.common import APIKeyResponse, WebhookPayload, WebhookResponse
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["bonus-features"])


# ==================== AUTHENTICATION ENDPOINTS ====================

@router.post("/auth/generate-key", response_model=APIKeyResponse)
async def generate_api_key(name: str):
    """Generate a new API key with rate limiting capabilities"""
    if not settings.AUTH_ENABLED:
        raise HTTPException(status_code=403, detail="Authentication is disabled")

    try:
        api_key = auth_service.generate_api_key(name)
        key_info = auth_service.get_key_info(api_key)
        
        # Store in cache for quick access
        await cache_service.set(
            f"api_key:{api_key}", 
            key_info,
            ttl=3600  # Cache for 1 hour
        )
        
        # Convert rate_limit to string if it's an integer
        rate_limit = key_info.get("rate_limit", "unlimited")
        if isinstance(rate_limit, int):
            rate_limit = str(rate_limit)
        
        return APIKeyResponse(
            api_key=api_key,
            name=name,
            created_at=key_info["created_at"],
            rate_limit=rate_limit
        )
    except Exception as e:
        logger.error(f"Error generating API key: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate API key")


@router.get("/auth/validate")
async def validate_api_key(authorization: Optional[str] = Header(None)):
    """Validate an API key and return its details"""
    if not settings.AUTH_ENABLED:
        return {"valid": True, "message": "Authentication is disabled"}

    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    try:
        api_key = authorization.replace("Bearer ", "").strip()
        
        # Try to get from cache first
        cached_info = await cache_service.get(f"api_key:{api_key}")
        if cached_info:
            key_info = cached_info
        else:
            if not auth_service.validate_api_key(api_key):
                raise HTTPException(status_code=401, detail="Invalid or inactive API key")
            
            key_info = auth_service.get_key_info(api_key)
            # Cache for future requests
            await cache_service.set(f"api_key:{api_key}", key_info, ttl=3600)
        
        # Check rate limit
        rate_limit_info = await rate_limiter.check_rate_limit(api_key)
        
        # Convert rate_limit to string if needed
        rate_limit = key_info.get("rate_limit", "unlimited")
        if isinstance(rate_limit, int):
            rate_limit = str(rate_limit)
        
        return {
            "valid": True,
            "key_name": key_info["name"],
            "rate_limit": rate_limit,
            "rate_limit_remaining": rate_limit_info.get("remaining", 0),
            "rate_limit_reset": rate_limit_info.get("reset", 0)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating API key: {e}")
        raise HTTPException(status_code=500, detail="Validation error")


@router.get("/auth/keys")
async def list_api_keys(authorization: Optional[str] = Header(None)):
    """List all active API keys (requires valid API key)"""
    if not settings.AUTH_ENABLED:
        raise HTTPException(status_code=403, detail="Authentication is disabled")
    
    # Validate the requesting user has a valid API key
    api_key = await _validate_and_get_api_key(authorization)
    
    try:
        keys = auth_service.list_api_keys()
        return {
            "keys": keys,
            "total": len(keys)
        }
    except Exception as e:
        logger.error(f"Error listing API keys: {e}")
        raise HTTPException(status_code=500, detail="Failed to list API keys")


@router.post("/auth/revoke/{api_key}")
async def revoke_api_key(api_key: str, authorization: Optional[str] = Header(None)):
    """Revoke an API key"""
    if not settings.AUTH_ENABLED:
        raise HTTPException(status_code=403, detail="Authentication is disabled")
    
    # Validate the requesting user has a valid API key
    await _validate_and_get_api_key(authorization)
    
    try:
        auth_service.revoke_api_key(api_key)
        # Remove from cache
        await cache_service.delete(f"api_key:{api_key}")
        return {"message": f"API key {api_key[:10]}... revoked successfully"}
    except Exception as e:
        logger.error(f"Error revoking API key: {e}")
        raise HTTPException(status_code=500, detail="Failed to revoke API key")


# ==================== WEBHOOK ENDPOINTS ====================

@router.post("/webhooks/register")
async def register_webhook(
    url: str,
    events: List[str],
    authorization: Optional[str] = Header(None)
):
    """Register a new webhook for real-time updates"""
    if not settings.WEBHOOKS_ENABLED:
        raise HTTPException(status_code=403, detail="Webhooks are disabled")
    
    # Validate API key
    api_key = await _validate_and_get_api_key(authorization)
    
    try:
        webhook_id = await webhook_service.register_webhook(
            url=url,
            events=events,
            api_key=api_key
        )
        
        return {
            "webhook_id": webhook_id,
            "url": url,
            "events": events,
            "status": "active",
            "created_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error registering webhook: {e}")
        raise HTTPException(status_code=500, detail="Failed to register webhook")


@router.delete("/webhooks/{webhook_id}")
async def unregister_webhook(
    webhook_id: str,
    authorization: Optional[str] = Header(None)
):
    """Unregister a webhook"""
    if not settings.WEBHOOKS_ENABLED:
        raise HTTPException(status_code=403, detail="Webhooks are disabled")
    
    await _validate_and_get_api_key(authorization)
    
    try:
        await webhook_service.unregister_webhook(webhook_id)
        return {"message": f"Webhook {webhook_id} unregistered successfully"}
    except Exception as e:
        logger.error(f"Error unregistering webhook: {e}")
        raise HTTPException(status_code=500, detail="Failed to unregister webhook")


@router.get("/webhooks")
async def list_webhooks(authorization: Optional[str] = Header(None)):
    """List all webhooks for the authenticated user"""
    if not settings.WEBHOOKS_ENABLED:
        raise HTTPException(status_code=403, detail="Webhooks are disabled")
    
    api_key = await _validate_and_get_api_key(authorization)
    
    try:
        webhooks = webhook_service.list_webhooks(api_key)
        return {"webhooks": webhooks, "total": len(webhooks)}
    except Exception as e:
        logger.error(f"Error listing webhooks: {e}")
        raise HTTPException(status_code=500, detail="Failed to list webhooks")


@router.post("/webhooks/{webhook_id}/trigger")
async def trigger_webhook(
    webhook_id: str,
    payload: WebhookPayload,
    background_tasks: BackgroundTasks,
    authorization: Optional[str] = Header(None)
):
    """Manually trigger a webhook (for testing)"""
    if not settings.WEBHOOKS_ENABLED:
        raise HTTPException(status_code=403, detail="Webhooks are disabled")
    
    await _validate_and_get_api_key(authorization)
    
    try:
        background_tasks.add_task(
            webhook_service.trigger_webhook,
            webhook_id=webhook_id,
            event_type=payload.event_type,
            data=payload.data
        )
        
        return {
            "message": "Webhook triggered",
            "webhook_id": webhook_id,
            "event_type": payload.event_type
        }
    except Exception as e:
        logger.error(f"Error triggering webhook: {e}")
        raise HTTPException(status_code=500, detail="Failed to trigger webhook")


# ==================== CACHE MANAGEMENT ENDPOINTS ====================

@router.get("/cache/status")
async def get_cache_status(authorization: Optional[str] = Header(None)):
    """Get cache status (simpler version of stats)"""
    if not settings.CACHE_ENABLED:
        raise HTTPException(status_code=403, detail="Caching is disabled")
    
    await _validate_and_get_api_key(authorization)
    
    try:
        # Simple status response
        return {
            "enabled": settings.CACHE_ENABLED,
            "redis_connected": cache_service.redis is not None,
            "fallback_cache_size": len(cache_service.fallback_cache) if hasattr(cache_service, 'fallback_cache') else 0,
            "ttl": cache_service.ttl,
            "healthy": cache_service.is_healthy() if hasattr(cache_service, 'is_healthy') else True
        }
    except Exception as e:
        logger.error(f"Error getting cache status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get cache status")


@router.get("/cache/stats")
async def get_cache_stats(authorization: Optional[str] = Header(None)):
    """Get Redis cache statistics"""
    if not settings.CACHE_ENABLED:
        raise HTTPException(status_code=403, detail="Caching is disabled")
    
    await _validate_and_get_api_key(authorization)
    
    try:
        stats = await cache_service.get_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get cache stats")


@router.delete("/cache/clear")
async def clear_cache(authorization: Optional[str] = Header(None)):
    """Clear all cached data"""
    if not settings.CACHE_ENABLED:
        raise HTTPException(status_code=403, detail="Caching is disabled")
    
    await _validate_and_get_api_key(authorization)
    
    try:
        await cache_service.clear()
        return {"message": "Cache cleared successfully", "timestamp": datetime.now().isoformat()}
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear cache")


# ==================== EXPORT ENDPOINTS ====================

def validate_export_format(format: str):
    """Validate export format"""
    allowed = {"csv", "excel", "json"}
    if format.lower() not in allowed:
        raise HTTPException(
            status_code=400,
            detail="Invalid format. Use csv, excel, or json"
        )


@router.post("/export/customers")
async def export_customers(
    format: str = "csv",
    background_tasks: BackgroundTasks = None,
    authorization: Optional[str] = Header(None)
):
    """Export customers data"""
    if not settings.EXPORT_ENABLED:
        raise HTTPException(status_code=403, detail="Export is disabled")

    api_key = await _validate_and_get_api_key(authorization)
    validate_export_format(format)

    try:
        from app.connectors.crm_connector import CRMConnector
        from app.services.business_rules import business_rules

        # Check cache first
        cache_key = f"export:customers:{format}"
        cached_content = await cache_service.get(cache_key)
        
        if cached_content and format != "json":  # Don't cache streaming responses
            # cached_content might be bytes or BytesIO
            if hasattr(cached_content, 'getvalue'):
                content_bytes = cached_content.getvalue()
            else:
                content_bytes = cached_content
                
            return StreamingResponse(
                iter([content_bytes]),
                media_type=_get_media_type(format),
                headers={"Content-Disposition": f"attachment; filename=customers.{format}"}
            )

        connector = CRMConnector()
        customers = await connector.fetch(
            status=None,
            limit=settings.EXPORT_MAX_RECORDS
        )

        customers = business_rules.apply_voice_limits(
            customers,
            limit=settings.EXPORT_MAX_RECORDS
        )

        # Log export in background
        if background_tasks:
            background_tasks.add_task(
                _log_export_activity,
                api_key=api_key,
                export_type="customers",
                format=format,
                record_count=len(customers)
            )

        if format.lower() == "csv":
            content = await export_service.export_to_csv(customers)
            # Get bytes from BytesIO
            content_bytes = content.getvalue()
            await cache_service.set(cache_key, content_bytes, ttl=300)  # Cache for 5 minutes
            return StreamingResponse(
                iter([content_bytes]),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=customers.csv"}
            )

        elif format.lower() == "excel":
            content = await export_service.export_to_excel(customers)
            # Get bytes from BytesIO
            content_bytes = content.getvalue()
            await cache_service.set(cache_key, content_bytes, ttl=300)
            return StreamingResponse(
                iter([content_bytes]),
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": "attachment; filename=customers.xlsx"}
            )

        else:  # json
            return JSONResponse(content=customers)

    except Exception as e:
        logger.error(f"Error exporting customers: {e}")
        raise HTTPException(status_code=500, detail="Export failed")


@router.post("/export/tickets")
async def export_tickets(
    format: str = "csv",
    background_tasks: BackgroundTasks = None,
    authorization: Optional[str] = Header(None)
):
    """Export tickets data"""
    if not settings.EXPORT_ENABLED:
        raise HTTPException(status_code=403, detail="Export is disabled")

    api_key = await _validate_and_get_api_key(authorization)
    validate_export_format(format)

    try:
        from app.connectors.support_connector import SupportConnector
        from app.services.business_rules import business_rules

        connector = SupportConnector()
        tickets = await connector.fetch(
            status=None,
            priority=None,
            limit=settings.EXPORT_MAX_RECORDS
        )

        tickets = business_rules.apply_voice_limits(
            tickets,
            limit=settings.EXPORT_MAX_RECORDS
        )

        # Log export in background
        if background_tasks:
            background_tasks.add_task(
                _log_export_activity,
                api_key=api_key,
                export_type="tickets",
                format=format,
                record_count=len(tickets)
            )

        if format.lower() == "csv":
            content = await export_service.export_to_csv(tickets)
            # Get bytes from BytesIO
            content_bytes = content.getvalue()
            return StreamingResponse(
                iter([content_bytes]),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=tickets.csv"}
            )

        elif format.lower() == "excel":
            content = await export_service.export_to_excel(tickets)
            # Get bytes from BytesIO
            content_bytes = content.getvalue()
            return StreamingResponse(
                iter([content_bytes]),
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": "attachment; filename=tickets.xlsx"}
            )

        else:
            return JSONResponse(content=tickets)

    except Exception as e:
        logger.error(f"Error exporting tickets: {e}")
        raise HTTPException(status_code=500, detail="Export failed")


@router.post("/export/analytics")
async def export_analytics(
    format: str = "csv",
    background_tasks: BackgroundTasks = None,
    authorization: Optional[str] = Header(None)
):
    """Export analytics data"""
    if not settings.EXPORT_ENABLED:
        raise HTTPException(status_code=403, detail="Export is disabled")

    api_key = await _validate_and_get_api_key(authorization)
    validate_export_format(format)

    try:
        from app.connectors.analytics_connector import AnalyticsConnector
        from app.services.business_rules import business_rules

        connector = AnalyticsConnector()
        analytics = await connector.fetch(
            metric=None,
            limit=settings.EXPORT_MAX_RECORDS
        )

        analytics = business_rules.apply_voice_limits(
            analytics,
            limit=settings.EXPORT_MAX_RECORDS
        )

        # Log export in background
        if background_tasks:
            background_tasks.add_task(
                _log_export_activity,
                api_key=api_key,
                export_type="analytics",
                format=format,
                record_count=len(analytics)
            )

        if format.lower() == "csv":
            content = await export_service.export_to_csv(analytics)
            # Get bytes from BytesIO
            content_bytes = content.getvalue()
            return StreamingResponse(
                iter([content_bytes]),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=analytics.csv"}
            )

        elif format.lower() == "excel":
            content = await export_service.export_to_excel(analytics)
            # Get bytes from BytesIO
            content_bytes = content.getvalue()
            return StreamingResponse(
                iter([content_bytes]),
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": "attachment; filename=analytics.xlsx"}
            )

        else:
            return JSONResponse(content=analytics)

    except Exception as e:
        logger.error(f"Error exporting analytics: {e}")
        raise HTTPException(status_code=500, detail="Export failed")


# ==================== HELPER FUNCTIONS ====================

async def _validate_and_get_api_key(authorization: Optional[str]) -> str:
    """Helper function to validate API key and return it"""
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Missing authorization header. Use 'Bearer <api_key>'"
        )
    
    try:
        api_key = authorization.replace("Bearer ", "").strip()
        if not api_key:
            raise HTTPException(
                status_code=401,
                detail="Invalid authorization header format"
            )
        
        if not auth_service.validate_api_key(api_key):
            raise HTTPException(
                status_code=401,
                detail="Invalid or inactive API key"
            )
        
        # Check rate limit
        rate_limit_info = await rate_limiter.check_rate_limit(api_key)
        if rate_limit_info.get("limited", False):
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please try again later."
            )
        
        return api_key
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")


async def _log_export_activity(api_key: str, export_type: str, format: str, record_count: int):
    """Log export activity for analytics"""
    try:
        # Get key info for logging
        key_info = auth_service.get_key_info(api_key)
        
        # Log to database or file
        logger.info(
            f"Export completed - User: {key_info.get('name')}, "
            f"Type: {export_type}, Format: {format}, Records: {record_count}"
        )
    except Exception as e:
        logger.error(f"Error logging export activity: {e}")


def _get_media_type(format: str) -> str:
    """Get media type for export format"""
    media_types = {
        "csv": "text/csv",
        "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "json": "application/json"
    }
    return media_types.get(format.lower(), "application/octet-stream")