"""
Rate limiting middleware for API key validation.
"""

import logging
import time
from typing import Dict, Optional
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from app.config import settings

logger = logging.getLogger(__name__)

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to rate limit requests based on API key."""
    
    def __init__(self, app, requests: int = 100, period_seconds: int = 60):
        super().__init__(app)
        self.enabled = settings.RATE_LIMIT_ENABLED
        self.default_limit = requests
        self.window_size = period_seconds
        # Simple in-memory store for rate limiting when Redis is disabled
        self._request_counts = {}
        logger.info(f"RateLimitMiddleware initialized: enabled={self.enabled}, "
                   f"limit={self.default_limit}, window={self.window_size}s")
    
    async def dispatch(self, request: Request, call_next):
        """Process request and check rate limits."""
        
        # Skip rate limiting if disabled
        if not self.enabled:
            return await call_next(request)
        
        # Skip rate limiting for public paths
        public_paths = ["/docs", "/redoc", "/openapi.json", "/ui", "/favicon.ico", "/static", "/health"]
        if any(request.url.path.startswith(path) for path in public_paths):
            return await call_next(request)
        
        # Get API key from header
        auth_header = request.headers.get("authorization", "")
        api_key = auth_header.replace("Bearer ", "").strip() if auth_header else "anonymous"
        
        # Check rate limit
        is_allowed, rate_limit_info = self._check_rate_limit(api_key)
        
        if not is_allowed:
            logger.warning(f"Rate limit exceeded for {api_key[:8]}... on {request.url.path}")
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Rate limit exceeded",
                    "limit": rate_limit_info.get("limit"),
                    "remaining": 0,
                    "reset": rate_limit_info.get("reset")
                }
            )
        
        # Add rate limit headers to response
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(rate_limit_info.get("limit", self.default_limit))
        response.headers["X-RateLimit-Remaining"] = str(rate_limit_info.get("remaining", 0))
        response.headers["X-RateLimit-Reset"] = str(rate_limit_info.get("reset", 0))
        
        return response
    
    def _check_rate_limit(self, api_key: str):
        """
        Check if request is within rate limit
        Returns (is_allowed, rate_limit_info)
        """
        try:
            current_time = int(time.time())
            window_start = current_time - self.window_size
            
            # Clean up old entries
            self._request_counts = {
                k: v for k, v in self._request_counts.items() 
                if v["timestamp"] > window_start
            }
            
            # Get or create rate limit info for this key
            if api_key not in self._request_counts:
                self._request_counts[api_key] = {
                    "count": 0,
                    "timestamp": current_time
                }
            
            # Reset count if window has passed
            if self._request_counts[api_key]["timestamp"] < window_start:
                self._request_counts[api_key] = {
                    "count": 0,
                    "timestamp": current_time
                }
            
            # Check if over limit
            current_count = self._request_counts[api_key]["count"]
            
            if current_count >= self.default_limit:
                reset_time = self._request_counts[api_key]["timestamp"] + self.window_size
                return False, {
                    "limited": True,
                    "limit": self.default_limit,
                    "remaining": 0,
                    "reset": reset_time
                }
            
            # Increment count
            self._request_counts[api_key]["count"] += 1
            
            return True, {
                "limited": False,
                "limit": self.default_limit,
                "remaining": self.default_limit - (current_count + 1),
                "reset": self._request_counts[api_key]["timestamp"] + self.window_size
            }
            
        except Exception as e:
            logger.error(f"Error checking rate limit: {e}")
            # Fail open if rate limiting fails
            return True, {
                "limited": False,
                "limit": self.default_limit,
                "remaining": "unknown",
                "reset": 0
            }