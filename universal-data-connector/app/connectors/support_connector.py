"""
Support connector for fetching ticket data.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from .base import BaseConnector
from app.config import settings

logger = logging.getLogger(__name__)


class SupportConnector(BaseConnector):
    """Connector for support ticket data."""

    def __init__(self):
        """Initialize support connector."""
        super().__init__()
        # Construct absolute path relative to project root
        current_dir = Path(__file__).parent.parent.parent
        self.data_path = current_dir / settings.DATA_DIR / "support_tickets.json"
        logger.info(f"Initialized SupportConnector with data path: {self.data_path}")

    def fetch_sync(self, status: Optional[str] = None, priority: Optional[str] = None, 
                   limit: Optional[int] = 10, **kwargs) -> List[Dict[str, Any]]:
        """
        Synchronous version of fetch for backward compatibility.
        
        Args:
            status: Optional status filter ('open' or 'closed')
            priority: Optional priority filter ('low', 'medium', 'high')
            limit: Maximum number of results to return
            **kwargs: Additional arguments (ignored)
            
        Returns:
            List of support ticket records
        """
        try:
            if not self.data_path.exists():
                logger.error(f"Support ticket data file not found: {self.data_path}")
                return []
            
            with open(self.data_path, 'r') as f:
                data = json.load(f)
            
            logger.debug(f"Loaded {len(data)} support tickets")
            
            # Apply status filter if provided
            if status:
                data = [d for d in data if d.get("status") == status]
                logger.info(f"Filtered to {len(data)} tickets with status={status}")
            
            # Apply priority filter if provided
            if priority:
                data = [d for d in data if d.get("priority") == priority]
                logger.info(f"Filtered to {len(data)} tickets with priority={priority}")
            
            # Sort by creation date (most recent first), then by priority
            priority_order = {"high": 0, "medium": 1, "low": 2}
            data = sorted(data, key=lambda x: (
                x.get("created_at", ""),
                priority_order.get(x.get("priority", "low"), 3)
            ), reverse=True)
            
            # Apply limit
            if limit:
                data = data[:min(limit, settings.MAX_RESULTS)]
            
            return data
        except FileNotFoundError:
            logger.error(f"Support ticket data file not found: {self.data_path}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding support ticket JSON: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching support tickets: {e}")
            return []
    
    async def fetch(self, status: Optional[str] = None, priority: Optional[str] = None, 
                    limit: Optional[int] = 10, **kwargs) -> List[Dict[str, Any]]:
        """
        Asynchronous version of fetch (used by the API).
        
        Args:
            status: Optional status filter ('open' or 'closed')
            priority: Optional priority filter ('low', 'medium', 'high')
            limit: Maximum number of results to return
            **kwargs: Additional arguments (ignored)
            
        Returns:
            List of support ticket records
        """
        # Call the synchronous version
        return self.fetch_sync(status=status, priority=priority, limit=limit, **kwargs)
    
    async def fetch_open_tickets(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get open support tickets only.
        
        Args:
            limit: Maximum number of results
            
        Returns:
            List of open ticket records
        """
        return await self.fetch(status="open", limit=limit)
    
    async def fetch_closed_tickets(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get closed support tickets only.
        
        Args:
            limit: Maximum number of results
            
        Returns:
            List of closed ticket records
        """
        return await self.fetch(status="closed", limit=limit)
    
    async def fetch_high_priority_tickets(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get high priority support tickets.
        
        Args:
            limit: Maximum number of results
            
        Returns:
            List of high priority ticket records
        """
        return await self.fetch(priority="high", limit=limit)
    
    async def fetch_medium_priority_tickets(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get medium priority support tickets.
        
        Args:
            limit: Maximum number of results
            
        Returns:
            List of medium priority ticket records
        """
        return await self.fetch(priority="medium", limit=limit)
    
    async def fetch_low_priority_tickets(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get low priority support tickets.
        
        Args:
            limit: Maximum number of results
            
        Returns:
            List of low priority ticket records
        """
        return await self.fetch(priority="low", limit=limit)
    
    async def get_ticket_by_id(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific ticket by ID.
        
        Args:
            ticket_id: Ticket ID to fetch
            
        Returns:
            Ticket record or None if not found
        """
        tickets = await self.fetch(limit=settings.MAX_RESULTS)
        for ticket in tickets:
            if ticket.get("ticket_id") == ticket_id:
                return ticket
        return None
    
    def get_metadata(self) -> Dict[str, str]:
        """
        Get metadata about the support connector.
        
        Returns:
            Dictionary with connector information
        """
        return {
            "name": "Support Connector",
            "description": "Provides access to support tickets and issue tracking",
            "data_type": "tabular_support",
            "supported_filters": ["status", "priority"],
            "fields": ["ticket_id", "customer_id", "subject", "description", "priority", "created_at", "updated_at", "status"]
        }