"""
CRM connector for fetching customer data.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from .base import BaseConnector
from app.config import settings

logger = logging.getLogger(__name__)


class CRMConnector(BaseConnector):
    """Connector for CRM customer data."""

    def __init__(self):
        """Initialize CRM connector."""
        super().__init__()
        # Construct absolute path relative to project root
        current_dir = Path(__file__).parent.parent.parent
        self.data_path = current_dir / settings.DATA_DIR / "customers.json"
        logger.info(f"Initialized CRMConnector with data path: {self.data_path}")

    def fetch_sync(self, status: Optional[str] = None, limit: Optional[int] = 10, **kwargs) -> List[Dict[str, Any]]:
        """
        Synchronous version of fetch for backward compatibility.
        
        Args:
            status: Optional status filter ('active' or 'inactive')
            limit: Maximum number of results to return
            **kwargs: Additional arguments (ignored)
            
        Returns:
            List of customer records
        """
        try:
            if not self.data_path.exists():
                logger.error(f"Customer data file not found: {self.data_path}")
                return []
            
            with open(self.data_path, 'r') as f:
                data = json.load(f)
            
            logger.debug(f"Loaded {len(data)} customer records from CRM")
            
            # Apply status filter if provided
            if status:
                data = [d for d in data if d.get("status") == status]
                logger.info(f"Filtered to {len(data)} records with status={status}")
            
            # Sort by creation date (most recent first)
            data = sorted(data, key=lambda x: x.get("created_at", ""), reverse=True)
            
            # Apply limit
            if limit:
                data = data[:min(limit, settings.MAX_RESULTS)]
            
            return data
        except FileNotFoundError:
            logger.error(f"Customer data file not found: {self.data_path}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding customer JSON: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching customer data: {e}")
            return []
    
    async def fetch(self, status: Optional[str] = None, limit: Optional[int] = 10, **kwargs) -> List[Dict[str, Any]]:
        """
        Asynchronous version of fetch (used by the API).
        
        Args:
            status: Optional status filter ('active' or 'inactive')
            limit: Maximum number of results to return
            **kwargs: Additional arguments (ignored)
            
        Returns:
            List of customer records
        """
        # Call the synchronous version
        return self.fetch_sync(status=status, limit=limit, **kwargs)
    
    async def fetch_active_customers(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get active customers only."""
        return await self.fetch(status="active", limit=limit)
    
    async def fetch_inactive_customers(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get inactive customers only."""
        return await self.fetch(status="inactive", limit=limit)
    
    async def get_customer_by_id(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific customer by ID."""
        customers = await self.fetch(limit=settings.MAX_RESULTS)
        for customer in customers:
            if customer.get("id") == customer_id:
                return customer
        return None
    
    def get_metadata(self) -> Dict[str, str]:
        """
        Get metadata about the CRM connector.
        
        Returns:
            Dictionary with connector information
        """
        return {
            "name": "CRM Connector",
            "description": "Provides access to customer data from CRM system",
            "data_type": "tabular_crm",
            "supported_filters": ["status"],
            "fields": ["id", "name", "email", "created_at", "status", "tier", "total_spent"]
        }