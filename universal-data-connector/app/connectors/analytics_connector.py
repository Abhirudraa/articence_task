"""
Analytics connector for fetching metrics data.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from .base import BaseConnector
from app.config import settings

logger = logging.getLogger(__name__)


class AnalyticsConnector(BaseConnector):
    """Connector for analytics and metrics data."""

    def __init__(self):
        """Initialize analytics connector."""
        super().__init__()
        # Construct absolute path relative to project root
        current_dir = Path(__file__).parent.parent.parent
        self.data_path = current_dir / settings.DATA_DIR / "analytics.json"
        logger.info(f"Initialized AnalyticsConnector with data path: {self.data_path}")

    def fetch_sync(self, metric: Optional[str] = None, limit: Optional[int] = 10, **kwargs) -> List[Dict[str, Any]]:
        """
        Synchronous version of fetch for backward compatibility.
        
        Args:
            metric: Optional metric filter (e.g., 'daily_active_users')
            limit: Maximum number of results to return
            **kwargs: Additional arguments (ignored)
            
        Returns:
            List of analytics records
        """
        try:
            if not self.data_path.exists():
                logger.error(f"Analytics data file not found: {self.data_path}")
                return []
            
            with open(self.data_path, 'r') as f:
                data = json.load(f)
            
            logger.debug(f"Loaded {len(data)} analytics records")
            
            # Apply metric filter if provided (case-insensitive)
            if metric:
                metric_lower = metric.lower().strip()
                data = [item for item in data if str(item.get("metric", "")).lower() == metric_lower]
                logger.info(f"Filtered to {len(data)} records for metric={metric}")
            
            # Sort by date (most recent first)
            data = sorted(data, key=lambda x: x.get("date", ""), reverse=True)
            
            # Apply limit
            if limit:
                data = data[:min(limit, settings.MAX_RESULTS)]
            
            return data
        except FileNotFoundError:
            logger.error(f"Analytics data file not found: {self.data_path}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding analytics JSON: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching analytics: {e}")
            return []
    
    async def fetch(self, metric: Optional[str] = None, limit: Optional[int] = 10, **kwargs) -> List[Dict[str, Any]]:
        """
        Asynchronous version of fetch (used by the API).
        
        Args:
            metric: Optional metric filter (e.g., 'daily_active_users')
            limit: Maximum number of results to return
            **kwargs: Additional arguments (ignored)
            
        Returns:
            List of analytics records
        """
        # Call the synchronous version
        return self.fetch_sync(metric=metric, limit=limit, **kwargs)
    
    async def fetch_daily_active_users(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get daily active users metrics.
        
        Args:
            limit: Maximum number of results
            
        Returns:
            List of daily active user records
        """
        return await self.fetch(metric="daily_active_users", limit=limit)
    
    async def fetch_latest_metrics(self, limit: int = 1) -> List[Dict[str, Any]]:
        """
        Get the latest analytics metrics.
        
        Args:
            limit: Maximum number of results
            
        Returns:
            List of latest metric records
        """
        return await self.fetch(limit=limit)
    
    async def summarize_metrics(self, limit: int = 10) -> Dict[str, Any]:
        """
        Get summarized metrics data for voice optimization.
        
        Args:
            limit: Maximum number of recent records to consider for summary
            
        Returns:
            Dictionary with summarized metric information
        """
        try:
            if not self.data_path.exists():
                logger.error(f"Analytics data file not found: {self.data_path}")
                return {"error": "Analytics data file not found"}
            
            with open(self.data_path, 'r') as f:
                data = json.load(f)
            
            if not data:
                return {"error": "No analytics data available"}
            
            # Sort by date and get latest
            data = sorted(data, key=lambda x: x.get("date", ""), reverse=True)[:limit]
            
            # Group by metric and calculate summary stats
            metrics_summary = {}
            for item in data:
                metric_name = item.get("metric", "unknown")
                value = item.get("value", 0)
                
                if metric_name not in metrics_summary:
                    metrics_summary[metric_name] = {
                        "latest_value": value,
                        "latest_date": item.get("date", ""),
                        "samples": [value]
                    }
                else:
                    metrics_summary[metric_name]["samples"].append(value)
            
            # Calculate averages and trends
            summary = {}
            for metric_name, stats in metrics_summary.items():
                samples = stats["samples"]
                avg_value = sum(samples) / len(samples) if samples else 0
                summary[metric_name] = {
                    "latest": stats["latest_value"],
                    "average": round(avg_value, 2),
                    "as_of": stats["latest_date"],
                    "data_points": len(samples)
                }
            
            return summary
        except Exception as e:
            logger.error(f"Error summarizing metrics: {e}")
            return {"error": str(e)}
    
    def get_metadata(self) -> Dict[str, str]:
        """
        Get metadata about the analytics connector.
        
        Returns:
            Dictionary with connector information
        """
        return {
            "name": "Analytics Connector",
            "description": "Provides access to key metrics and analytics data",
            "data_type": "time_series",
            "supported_filters": ["metric"],
            "fields": ["metric", "date", "value"]
        }