
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class BaseConnector(ABC):
    """Base class for all data connectors."""

    def __init__(self):
        """Initialize the connector."""
        self.logger = logger

    @abstractmethod
    def fetch(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Fetch data from the source.
        
        Args:
            **kwargs: Additional arguments for filtering/pagination
            
        Returns:
            List of dictionaries containing the data
            
        Raises:
            Exception: If data cannot be fetched
        """
        pass

    @abstractmethod
    def get_metadata(self) -> Dict[str, str]:
        """
        Get metadata about the connector.
        
        Returns:
            Dictionary with connector information
        """
        pass

    def filter_by_limit(self, data: List[Dict[str, Any]], limit: Optional[int] = 10) -> List[Dict[str, Any]]:
        """
        Filter data by limit.
        
        Args:
            data: Raw data
            limit: Maximum number of results
            
        Returns:
            Limited data
        """
        if limit is None:
            return data
        return data[:limit]

    def filter_by_status(self, data: List[Dict[str, Any]], status: str) -> List[Dict[str, Any]]:
        """
        Filter data by status field (case-insensitive).
        
        Args:
            data: Raw data
            status: Status to filter by
            
        Returns:
            Filtered data
        """
        if not status:
            return data
        status_lower = status.lower().strip()
        return [item for item in data if str(item.get("status", "")).lower() == status_lower]

    def filter_by_priority(self, data: List[Dict[str, Any]], priority: str) -> List[Dict[str, Any]]:
        """
        Filter data by priority field (case-insensitive).
        
        Args:
            data: Raw data
            priority: Priority to filter by
            
        Returns:
            Filtered data
        """
        if not priority:
            return data
        priority_lower = priority.lower().strip()
        return [item for item in data if str(item.get("priority", "")).lower() == priority_lower]
