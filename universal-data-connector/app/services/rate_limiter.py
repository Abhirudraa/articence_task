"""
Rate limiting service for API key based rate limiting (programmatic access).
"""

import logging
import time
from typing import Dict, Any
from collections import defaultdict
from app.config import settings

logger = logging.getLogger(__name__)

class RateLimiter:
    """Rate limiter service for programmatic rate limit checks."""
    
    def __init__(self):
        """Initialize the rate limiter."""
        self.enabled = settings.RATE_LIMIT_ENABLED
        self.default_limit = settings.RATE_LIMIT_REQUESTS
        self.window_seconds = settings.RATE_LIMIT_PERIOD_SECONDS
        
        # In-memory store for rate limiting
        self._request_counts = defaultdict(list)
        
        logger.info(f"Rate limiter service initialized: enabled={self.enabled}, "
                   f"limit={self.default_limit}, window={self.window_seconds}s")
    
    async def check_rate_limit(self, api_key: str) -> Dict[str, Any]:
        """
        Check if request is within rate limit.
        
        Returns:
            Dict with rate limit info
        """
        if not self.enabled:
            return {
                "limited": False,
                "limit": self.default_limit,
                "remaining": self.default_limit,
                "reset": 0
            }
        
        current_time = int(time.time())
        window_start = current_time - self.window_seconds
        
        # Clean up old requests
        self._request_counts[api_key] = [
            ts for ts in self._request_counts[api_key]
            if ts > window_start
        ]
        
        current_count = len(self._request_counts[api_key])
        
        # Calculate reset time
        if self._request_counts[api_key]:
            oldest_request = min(self._request_counts[api_key])
            reset_time = oldest_request + self.window_seconds
        else:
            reset_time = current_time + self.window_seconds
        
        if current_count >= self.default_limit:
            return {
                "limited": True,
                "limit": self.default_limit,
                "remaining": 0,
                "reset": reset_time
            }
        
        # Add current request
        self._request_counts[api_key].append(current_time)
        
        return {
            "limited": False,
            "limit": self.default_limit,
            "remaining": self.default_limit - (current_count + 1),
            "reset": reset_time
        }
    
    def get_remaining(self, api_key: str) -> int:
        """Get remaining requests for an API key."""
        if not self.enabled:
            return self.default_limit
        
        current_time = int(time.time())
        window_start = current_time - self.window_seconds
        
        # Clean up old requests
        self._request_counts[api_key] = [
            ts for ts in self._request_counts[api_key]
            if ts > window_start
        ]
        
        current_count = len(self._request_counts[api_key])
        return max(0, self.default_limit - current_count)
    
    def reset_counter(self, api_key: str):
        """Reset rate limit counter for an API key."""
        if api_key in self._request_counts:
            self._request_counts[api_key] = []
            logger.info(f"Reset rate limit counter for {api_key[:8]}...")


# Create global rate limiter instance
rate_limiter = RateLimiter()