
import logging
from typing import List, Dict, Any, Optional
from app.config import settings

logger = logging.getLogger(__name__)


class BusinessRulesEngine:
    """Engine for applying business rules to data."""

    @staticmethod
    def apply_voice_limits(data: List[Dict[str, Any]], limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Apply voice-optimized limits to data.
        Limits results to prevent overwhelming voice responses.
        
        Args:
            data: Raw data list
            limit: Maximum number of results (defaults to settings.MAX_RESULTS)
            
        Returns:
            Limited data list
        """
        if limit is None:
            limit = settings.MAX_RESULTS
        
        limited = data[:limit]
        logger.info(f"Applied voice limit: returned {len(limited)} of {len(data)} records")
        return limited

    @staticmethod
    def prioritize_by_date(data: List[Dict[str, Any]], date_field: str = "created_at") -> List[Dict[str, Any]]:
        """
        Prioritize data by most recent date first.
        
        Args:
            data: Raw data list
            date_field: Field name containing the date
            
        Returns:
            Sorted data (most recent first)
        """
        try:
            sorted_data = sorted(data, key=lambda x: x.get(date_field, ""), reverse=True)
            logger.info(f"Prioritized {len(sorted_data)} records by {date_field}")
            return sorted_data
        except Exception as e:
            logger.warning(f"Could not sort by {date_field}: {e}")
            return data

    @staticmethod
    def prioritize_by_priority(data: List[Dict[str, Any]], priority_field: str = "priority") -> List[Dict[str, Any]]:
        """
        Prioritize data by priority level (high > medium > low).
        
        Args:
            data: Raw data list
            priority_field: Field name containing the priority
            
        Returns:
            Sorted data (high priority first)
        """
        try:
            priority_order = {"high": 0, "medium": 1, "low": 2}
            sorted_data = sorted(
                data,
                key=lambda x: priority_order.get(x.get(priority_field, "low"), 3)
            )
            logger.info(f"Prioritized {len(sorted_data)} records by {priority_field}")
            return sorted_data
        except Exception as e:
            logger.warning(f"Could not prioritize by {priority_field}: {e}")
            return data

    @staticmethod
    def filter_by_status(data: List[Dict[str, Any]], status: str, status_field: str = "status") -> List[Dict[str, Any]]:
        """
        Filter data by status.
        
        Args:
            data: Raw data list
            status: Status value to filter by
            status_field: Field name containing the status
            
        Returns:
            Filtered data
        """
        filtered = [item for item in data if item.get(status_field) == status]
        logger.info(f"Filtered {len(filtered)} records with {status_field}={status}")
        return filtered

    @staticmethod
    def apply_pagination(data: List[Dict[str, Any]], limit: int = 10, offset: int = 0) -> tuple:
        """
        Apply pagination to data.
        
        Args:
            data: Raw data list
            limit: Number of results per page
            offset: Number of results to skip
            
        Returns:
            Tuple of (paginated_data, total_count, returned_count)
        """
        total = len(data)
        paginated = data[offset:offset + limit]
        logger.info(f"Applied pagination: offset={offset}, limit={limit}, returned={len(paginated)} of {total}")
        return paginated, total, len(paginated)

    @staticmethod
    def build_context_message(total: int, returned: int, data_type: str) -> str:
        """
        Build a human-readable context message for voice optimization.
        
        Args:
            total: Total number of results available
            returned: Number of results returned
            data_type: Type of data
            
        Returns:
            Human-readable context string
        """
        if returned == 0:
            return f"No {data_type} data available"
        
        if returned == total:
            return f"Showing all {returned} {data_type} records"
        
        has_more = total - returned
        return f"Showing {returned} of {total} {data_type} records ({has_more} more available)"

    @staticmethod
    def should_summarize(data: List[Dict[str, Any]], threshold: Optional[int] = None) -> bool:
        """
        Determine if data should be summarized based on size.
        
        Args:
            data: Data list
            threshold: Size threshold (defaults to settings.VOICE_SUMMARY_THRESHOLD)
            
        Returns:
            True if data should be summarized
        """
        if threshold is None:
            threshold = settings.VOICE_SUMMARY_THRESHOLD
        
        return len(data) > threshold


# Create singleton instance
business_rules = BusinessRulesEngine()
