"""
Webhook service for managing and triggering webhooks.
"""

import json
import logging
import httpx
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
from app.config import settings

logger = logging.getLogger(__name__)

class WebhookService:
    """Service for managing webhooks."""
    
    def __init__(self):
        """Initialize the webhook service."""
        self.enabled = settings.WEBHOOK_ENABLED or settings.WEBHOOKS_ENABLED
        # Get timeout from settings (try both naming conventions)
        self.timeout = getattr(settings, 'WEBHOOK_TIMEOUT_SECONDS', 
                               getattr(settings, 'WEBHOOK_TIMEOUT', 10))
        self.max_retries = settings.WEBHOOK_MAX_RETRIES
        # Get the project root directory
        self.project_root = Path(__file__).parent.parent.parent
        self.webhooks_file = self.project_root / settings.WEBHOOKS_FILE
        self.webhooks: Dict[str, Dict] = {}
        self._load_webhooks()
        logger.info(f"Webhook service initialized with timeout={self.timeout}s, max_retries={self.max_retries}")
        logger.info(f"Webhooks file: {self.webhooks_file}")
    
    def _load_webhooks(self):
        """Load webhooks from file."""
        try:
            if self.webhooks_file.exists():
                with open(self.webhooks_file, 'r') as f:
                    self.webhooks = json.load(f)
                logger.info(f"Loaded {len(self.webhooks)} webhooks from {self.webhooks_file}")
            else:
                logger.info(f"No webhooks file found at {self.webhooks_file}, starting with empty webhooks")
                self.webhooks = {}
                self._save_webhooks()
        except Exception as e:
            logger.error(f"Error loading webhooks: {e}")
            self.webhooks = {}
    
    def _save_webhooks(self):
        """Save webhooks to file."""
        try:
            self.webhooks_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.webhooks_file, 'w') as f:
                json.dump(self.webhooks, f, indent=2, default=str)
            logger.info(f"Saved {len(self.webhooks)} webhooks to {self.webhooks_file}")
        except Exception as e:
            logger.error(f"Error saving webhooks: {e}")
    
    async def register_webhook(self, url: str, events: List[str], api_key: str) -> str:
        """Register a new webhook."""
        import uuid
        webhook_id = str(uuid.uuid4())
        
        self.webhooks[webhook_id] = {
            "id": webhook_id,
            "url": url,
            "events": events,
            "api_key": api_key,
            "created_at": datetime.utcnow().isoformat(),
            "last_triggered": None,
            "success_count": 0,
            "failure_count": 0,
            "active": True
        }
        
        self._save_webhooks()
        logger.info(f"Registered webhook {webhook_id} for events: {events}")
        return webhook_id
    
    async def unregister_webhook(self, webhook_id: str) -> bool:
        """Unregister a webhook."""
        if webhook_id in self.webhooks:
            del self.webhooks[webhook_id]
            self._save_webhooks()
            logger.info(f"Unregistered webhook {webhook_id}")
            return True
        return False
    
    async def trigger_webhook(self, webhook_id: str, event_type: str, data: Dict[str, Any]):
        """Trigger a webhook with retry logic."""
        if webhook_id not in self.webhooks:
            logger.error(f"Webhook {webhook_id} not found")
            return
        
        webhook = self.webhooks[webhook_id]
        if not webhook.get("active", True):
            logger.warning(f"Webhook {webhook_id} is inactive")
            return
        
        if event_type not in webhook.get("events", []):
            logger.debug(f"Webhook {webhook_id} not subscribed to event {event_type}")
            return
        
        url = webhook["url"]
        payload = {
            "event": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }
        
        # Trigger with retries
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(url, json=payload)
                    
                    if response.status_code < 300:
                        webhook["last_triggered"] = datetime.utcnow().isoformat()
                        webhook["success_count"] = webhook.get("success_count", 0) + 1
                        self._save_webhooks()
                        logger.info(f"Webhook {webhook_id} triggered successfully for {event_type}")
                        return
                    else:
                        logger.warning(f"Webhook {webhook_id} returned status {response.status_code} (attempt {attempt + 1})")
            
            except Exception as e:
                logger.error(f"Error triggering webhook {webhook_id} (attempt {attempt + 1}): {e}")
            
            # Wait before retry (exponential backoff)
            if attempt < self.max_retries - 1:
                await asyncio.sleep(2 ** attempt)
        
        # All retries failed
        webhook["failure_count"] = webhook.get("failure_count", 0) + 1
        self._save_webhooks()
        logger.error(f"Webhook {webhook_id} failed after {self.max_retries} attempts")
    
    def list_webhooks(self, api_key: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all webhooks, optionally filtered by API key."""
        webhooks = []
        for webhook_id, webhook in self.webhooks.items():
            if api_key and webhook.get("api_key") != api_key:
                continue
            
            # Return a copy without sensitive data
            webhook_copy = webhook.copy()
            if "api_key" in webhook_copy:
                del webhook_copy["api_key"]
            webhooks.append(webhook_copy)
        
        return webhooks
    
    def get_webhook(self, webhook_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific webhook by ID."""
        webhook = self.webhooks.get(webhook_id)
        if webhook:
            # Return a copy without sensitive data
            webhook_copy = webhook.copy()
            if "api_key" in webhook_copy:
                del webhook_copy["api_key"]
            return webhook_copy
        return None

# Global webhook service instance
webhook_service = WebhookService()