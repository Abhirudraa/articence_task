"""
Authentication middleware for API key validation.
"""

import logging
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from app.services.auth_service import auth_service
from app.config import settings
from app.services.rate_limiter import rate_limiter  # Add rate limiter import

logger = logging.getLogger(__name__)

class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware to validate API keys for protected endpoints."""
    
    # Routes that don't require authentication
    UNPROTECTED_ROUTES = {
        # API documentation
        "/docs",
        "/redoc",
        "/openapi.json",
        
        # Health checks (both with and without /api prefix)
        "/health",
        "/api/health",
        
        # Metrics
        "/metrics",
        
        # Authentication endpoints that should be public
        "/api/auth/generate-key",  # Allow generating keys without auth
        "/api/auth",                # Auth base path
        
        # UI and static files
        "/ui",                      # UI static files
        "/ui/",                     # UI directory
        "/favicon.ico",             # Favicon
        "/static",                   # Static files
        
        # Root path
        "/",
    }
    
    async def dispatch(self, request: Request, call_next):
        """Process request and validate API key if needed."""
        
        # Log the request path for debugging
        logger.debug(f"Processing request: {request.method} {request.url.path}")
        
        # Check if authentication is disabled
        if not settings.AUTH_ENABLED:
            logger.debug("Authentication is disabled, allowing all requests")
            return await call_next(request)
        
        # Skip auth for unprotected routes
        path = request.url.path
        if any(self._path_matches(path, route) for route in self.UNPROTECTED_ROUTES):
            logger.info(f"Skipping authentication for public path: {path}")
            return await call_next(request)
        
        # Check authorization header
        auth_header = request.headers.get("authorization", "")
        
        if not auth_header:
            logger.warning(f"Missing authorization header for {path}")
            raise HTTPException(
                status_code=401,
                detail="Missing authorization header. Use 'Bearer <api_key>'"
            )
        
        try:
            # Extract and validate API key
            api_key = auth_header.replace("Bearer ", "").strip()
            if not api_key:
                logger.warning(f"Empty API key in authorization header for {path}")
                raise HTTPException(
                    status_code=401, 
                    detail="Invalid authorization header format"
                )
            
            # Validate the API key
            if not auth_service.validate_api_key(api_key):
                logger.warning(f"Invalid API key attempt for {path}")
                raise HTTPException(
                    status_code=401, 
                    detail="Invalid or inactive API key"
                )
            
            # Check rate limit
            try:
                rate_limit_info = await rate_limiter.check_rate_limit(api_key)
                if rate_limit_info.get("limited", False):
                    logger.warning(f"Rate limit exceeded for {api_key[:8]}... on {path}")
                    raise HTTPException(
                        status_code=429,
                        detail=f"Rate limit exceeded. Try again in {rate_limit_info.get('reset', 0)} seconds."
                    )
            except Exception as e:
                logger.error(f"Rate limit check error: {e}")
                # Continue even if rate limiting fails (fail open)
            
            # Get key info for logging
            key_info = auth_service.get_key_info(api_key)
            logger.debug(f"Valid API key used for {path} by {key_info.get('name', 'unknown')}")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Authentication error for {path}: {str(e)}")
            raise HTTPException(
                status_code=401, 
                detail="Authentication failed"
            )
        
        # Proceed with the request
        return await call_next(request)
    
    def _path_matches(self, path: str, route: str) -> bool:
        """Check if a path matches a route pattern."""
        # Exact match
        if path == route:
            return True
        
        # Path starts with route (for directory-like routes)
        if path.startswith(route + '/'):
            return True
        
        # Handle routes without trailing slash
        if route.endswith('/'):
            return path.startswith(route)
        
        return False