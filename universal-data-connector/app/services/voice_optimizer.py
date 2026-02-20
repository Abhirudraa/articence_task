
import logging
from typing import List, Dict, Any, Optional
from app.config import settings

logger = logging.getLogger(__name__)


class VoiceOptimizer:
    """Service for optimizing data responses for voice conversations."""

    @staticmethod
    def summarize_if_large(data: List[Dict[str, Any]], threshold: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Summarize data if it exceeds the threshold for voice optimization.
        
        Args:
            data: List of data items
            threshold: Size threshold (defaults to settings.VOICE_SUMMARY_THRESHOLD)
            
        Returns:
            Original data if under threshold, summarized version if over
        """
        if threshold is None:
            threshold = settings.VOICE_SUMMARY_THRESHOLD
        
        if len(data) <= threshold or not settings.ENABLE_VOICE_OPTIMIZATION:
            return data
        
        logger.info(f"Data size {len(data)} exceeds threshold {threshold}, summarizing...")
        return [{"summary": f"{len(data)} records found. Showing first {threshold}."}]

    @staticmethod
    def optimize_response(data: List[Dict[str, Any]], data_type: str) -> Dict[str, Any]:
        """
        Fully optimize a response for voice conversations.
        
        Args:
            data: Raw data list
            data_type: Type of data (tabular, time_series, etc.)
            
        Returns:
            Optimized response dictionary
        """
        optimized = {
            "items": data,
            "count": len(data),
            "type": data_type,
            "verbose": False
        }
        
        # Add type-specific optimizations
        if data_type == "time_series":
            optimized["trend"] = VoiceOptimizer._calculate_trend(data)
        elif data_type == "tabular_support":
            optimized["priority_summary"] = VoiceOptimizer._summarize_priority(data)
        elif data_type == "tabular_crm":
            optimized["status_summary"] = VoiceOptimizer._summarize_status(data)
        
        logger.info(f"Optimized response for voice: {len(data)} items")
        return optimized

    @staticmethod
    def make_concise(data: List[Dict[str, Any]], max_chars: int = 200) -> List[Dict[str, Any]]:
        """
        Make data concise for voice by limiting text length.
        
        Args:
            data: List of data items
            max_chars: Maximum characters per field
            
        Returns:
            Concise data
        """
        concise = []
        for item in data:
            concise_item = {}
            for key, value in item.items():
                if isinstance(value, str) and len(value) > max_chars:
                    concise_item[key] = value[:max_chars] + "..."
                else:
                    concise_item[key] = value
            concise.append(concise_item)
        
        logger.info(f"Made {len(concise)} items concise (max {max_chars} chars)")
        return concise

    @staticmethod
    def add_context_metadata(data: List[Dict[str, Any]], total_available: int) -> Dict[str, Any]:
        """
        Add helpful metadata for voice context.
        
        Args:
            data: Returned data items
            total_available: Total items available
            
        Returns:
            Data with added context
        """
        returned = len(data)
        
        context = {
            "items": data,
            "returned": returned,
            "total": total_available,
            "has_more": returned < total_available,
            "context_message": VoiceOptimizer._build_context_message(returned, total_available)
        }
        
        return context

    @staticmethod
    def _build_context_message(returned: int, total: int) -> str:
        """Build a human-readable context message."""
        if returned == 0:
            return "No results found"
        if returned == total:
            return f"Showing all {returned} results"
        return f"Showing {returned} of {total} results"

    @staticmethod
    def _calculate_trend(data: List[Dict[str, Any]]) -> Optional[str]:
        """
        Calculate trend from time series data.
        
        Args:
            data: Time series data
            
        Returns:
            Trend description or None
        """
        try:
            if len(data) < 2:
                return None
            
            # Get numeric values
            values = []
            for item in data:
                if "value" in item:
                    try:
                        values.append(float(item["value"]))
                    except (ValueError, TypeError):
                        pass
            
            if len(values) < 2:
                return None
            
            # Compare recent vs older
            recent = values[0]
            older = values[-1]
            
            if recent > older:
                percent_change = ((recent - older) / older * 100) if older != 0 else 0
                return f"Up {percent_change:.1f}%"
            elif recent < older:
                percent_change = ((older - recent) / older * 100) if older != 0 else 0
                return f"Down {percent_change:.1f}%"
            else:
                return "Stable"
        except Exception as e:
            logger.warning(f"Could not calculate trend: {e}")
            return None

    @staticmethod
    def _summarize_priority(data: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Summarize support tickets by priority.
        
        Args:
            data: Support ticket data
            
        Returns:
            Priority breakdown
        """
        summary = {"high": 0, "medium": 0, "low": 0}
        for item in data:
            priority = item.get("priority", "low")
            if priority in summary:
                summary[priority] += 1
        return summary

    @staticmethod
    def _summarize_status(data: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Summarize customers by status.
        
        Args:
            data: Customer data
            
        Returns:
            Status breakdown
        """
        summary = {"active": 0, "inactive": 0}
        for item in data:
            status = item.get("status", "inactive")
            if status in summary:
                summary[status] += 1
        return summary


# Create singleton instance
voice_optimizer = VoiceOptimizer()
