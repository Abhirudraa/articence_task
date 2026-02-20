"""
Data export service for CSV and Excel formats.
"""

import json
import logging
from io import BytesIO, StringIO
from typing import Any, List, Dict
from datetime import datetime
import pandas as pd
from app.config import settings

logger = logging.getLogger(__name__)

class ExportService:
    """Data export service supporting CSV and Excel formats."""
    
    def __init__(self):
        """Initialize the export service."""
        self.enabled = settings.EXPORT_ENABLED
        self.max_records = settings.EXPORT_MAX_RECORDS
    
    def _normalize_data(self, data: Any) -> List[Dict]:
        """Normalize data to list of dictionaries."""
        if isinstance(data, dict):
            if "data" in data:
                return self._normalize_data(data["data"])
            return [data]
        elif isinstance(data, list):
            return [item if isinstance(item, dict) else {"value": item} for item in data]
        else:
            return [{"value": data}]
    
    def _flatten_dict(self, d: Dict, parent_key: str = '', sep: str = '_') -> Dict:
        """Flatten nested dictionaries."""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                items.append((new_key, json.dumps(v)))
            else:
                items.append((new_key, v))
        return dict(items)
    
    async def export_to_csv(self, data: Any) -> BytesIO:
        """Export data to CSV format."""
        if not self.enabled:
            raise ValueError("Export service is disabled")
        
        try:
            normalized = self._normalize_data(data)
            if len(normalized) > self.max_records:
                logger.warning(f"Truncating data from {len(normalized)} to {self.max_records} records")
                normalized = normalized[:self.max_records]
            
            # Flatten nested structures
            flattened_data = []
            for item in normalized:
                if isinstance(item, dict):
                    flattened_data.append(self._flatten_dict(item))
                else:
                    flattened_data.append({"value": item})
            
            df = pd.DataFrame(flattened_data)
            
            # Use BytesIO directly
            csv_buffer = BytesIO()
            df.to_csv(csv_buffer, index=False)
            csv_buffer.seek(0)
            
            logger.info(f"Exported {len(normalized)} records to CSV")
            return csv_buffer
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
            raise

    async def export_to_excel(self, data: Any) -> BytesIO:
        """Export data to Excel format."""
        if not self.enabled:
            raise ValueError("Export service is disabled")
        
        try:
            normalized = self._normalize_data(data)
            if len(normalized) > self.max_records:
                logger.warning(f"Truncating data from {len(normalized)} to {self.max_records} records")
                normalized = normalized[:self.max_records]
            
            # Flatten nested structures
            flattened_data = []
            for item in normalized:
                if isinstance(item, dict):
                    flattened_data.append(self._flatten_dict(item))
                else:
                    flattened_data.append({"value": item})
            
            df = pd.DataFrame(flattened_data)
            
            # Use BytesIO directly
            excel_buffer = BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Data')
            excel_buffer.seek(0)
            
            logger.info(f"Exported {len(normalized)} records to Excel")
            return excel_buffer
        except Exception as e:
            logger.error(f"Error exporting to Excel: {e}")
            raise

    async def export_to_json(self, data: Any) -> Dict:
        """Export data to JSON format."""
        if not self.enabled:
            raise ValueError("Export service is disabled")
        
        try:
            normalized = self._normalize_data(data)
            if len(normalized) > self.max_records:
                logger.warning(f"Truncating data from {len(normalized)} to {self.max_records} records")
                normalized = normalized[:self.max_records]
            
            logger.info(f"Exported {len(normalized)} records to JSON")
            return {
                "exported_at": datetime.utcnow().isoformat(),
                "record_count": len(normalized),
                "data": normalized
            }
        except Exception as e:
            logger.error(f"Error exporting to JSON: {e}")
            raise

# Global export service instance
export_service = ExportService()