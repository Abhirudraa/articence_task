"""
Authentication and API key management service.
"""

import json
import logging
import secrets
from typing import Optional, Dict
from datetime import datetime, timedelta
from pathlib import Path
from app.config import settings

logger = logging.getLogger(__name__)

class AuthService:
    """API key and authentication management."""
    
    def __init__(self):
        """Initialize the auth service."""
        self.enabled = settings.AUTH_ENABLED
        # Get the project root directory (3 levels up: services -> app -> project_root)
        self.project_root = Path(__file__).parent.parent.parent
        self.keys_file = self.project_root / settings.API_KEYS_FILE
        self.api_keys: Dict[str, Dict] = {}
        logger.info(f"Auth service initialized with keys file: {self.keys_file}")
        self._load_keys()
    
    def _load_keys(self):
        """Load API keys from file."""
        try:
            if self.keys_file.exists():
                with open(self.keys_file, 'r') as f:
                    self.api_keys = json.load(f)
                logger.info(f"Loaded {len(self.api_keys)} API keys from {self.keys_file}")
            else:
                logger.info(f"No API keys file found at {self.keys_file}, creating empty keys file")
                self._save_keys()
        except Exception as e:
            logger.error(f"Error loading API keys: {e}")
            self.api_keys = {}
    
    def _save_keys(self):
        """Save API keys to file."""
        try:
            self.keys_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.keys_file, 'w') as f:
                json.dump(self.api_keys, f, indent=2, default=str)
            logger.info(f"API keys saved to {self.keys_file}")
        except Exception as e:
            logger.error(f"Error saving API keys: {e}")
    
    def generate_api_key(self, name: str) -> str:
        """Generate a new API key."""
        key = f"uk_{secrets.token_urlsafe(32)}"
        self.api_keys[key] = {
            "name": name,
            "created_at": datetime.utcnow().isoformat(),
            "last_used": None,
            "active": True,
            "rate_limit": 1000,  # Requests per hour
        }
        self._save_keys()
        logger.info(f"Generated new API key for: {name}")
        return key
    
    def validate_api_key(self, api_key: str) -> bool:
        """Validate an API key."""
        if not self.enabled:
            return True
        
        if api_key not in self.api_keys:
            logger.warning(f"Invalid API key attempt: {api_key[:10]}...")
            return False
        
        key_data = self.api_keys[api_key]
        if not key_data.get("active", False):
            logger.warning(f"Inactive API key used: {key_data['name']}")
            return False
        
        # Update last used
        key_data["last_used"] = datetime.utcnow().isoformat()
        self._save_keys()
        return True
    
    def get_key_info(self, api_key: str) -> Optional[Dict]:
        """Get information about an API key."""
        if api_key not in self.api_keys:
            return None
        return self.api_keys[api_key]
    
    def revoke_api_key(self, api_key: str) -> bool:
        """Revoke an API key."""
        if api_key not in self.api_keys:
            return False
        
        self.api_keys[api_key]["active"] = False
        self._save_keys()
        logger.info(f"Revoked API key: {self.api_keys[api_key]['name']}")
        return True
    
    def list_api_keys(self) -> list:
        """List all active API keys."""
        return [
            {
                "key_preview": k[:10] + "...",  # Show only preview for security
                "name": v.get("name", "unknown"),
                "created_at": v.get("created_at"),
                "last_used": v.get("last_used"),
                "active": v.get("active", False),
                "rate_limit": v.get("rate_limit", 1000)
            }
            for k, v in self.api_keys.items()
            if v.get("active", False)
        ]

# Global auth service instance
auth_service = AuthService()