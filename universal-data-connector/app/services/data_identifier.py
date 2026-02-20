
import logging
from typing import List, Dict, Any
from app.models.common import DataTypeEnum

logger = logging.getLogger(__name__)


class DataIdentifier:
    """Service for identifying data types and characteristics."""

    @staticmethod
    def identify_data_type(data: List[Dict[str, Any]]) -> DataTypeEnum:
        """
        Identify the type of data in the list.
        
        Args:
            data: List of data dictionaries
            
        Returns:
            DataTypeEnum value
        """
        if not data:
            logger.info("Identified data type: EMPTY")
            return DataTypeEnum.EMPTY
        
        first_item = data[0]
        
        # Check for time-series data (has date/timestamp field)
        if "date" in first_item or "timestamp" in first_item or "datetime" in first_item:
            logger.info("Identified data type: TIME_SERIES")
            return DataTypeEnum.TIME_SERIES
        
        # Check for hierarchical data (has nested objects)
        for value in first_item.values():
            if isinstance(value, (dict, list)):
                logger.info("Identified data type: HIERARCHICAL")
                return DataTypeEnum.HIERARCHICAL
        
        # Check for support ticket data
        if "ticket_id" in first_item:
            logger.info("Identified data type: TABULAR (support)")
            return DataTypeEnum.TABULAR
        
        # Check for customer CRM data
        if "customer_id" in first_item:
            logger.info("Identified data type: TABULAR (CRM)")
            return DataTypeEnum.TABULAR
        
        # Default to tabular for other structured data
        logger.info("Identified data type: TABULAR (default)")
        return DataTypeEnum.TABULAR

    @staticmethod
    def get_field_names(data: List[Dict[str, Any]]) -> List[str]:
        """
        Get all field names from data.
        
        Args:
            data: List of data dictionaries
            
        Returns:
            List of field names
        """
        if not data:
            return []
        
        fields = list(data[0].keys())
        logger.info(f"Identified fields: {fields}")
        return fields

    @staticmethod
    def get_data_characteristics(data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get detailed characteristics of the data.
        
        Args:
            data: List of data dictionaries
            
        Returns:
            Dictionary with data characteristics
        """
        characteristics = {
            "record_count": len(data),
            "data_type": str(DataIdentifier.identify_data_type(data)),
            "fields": DataIdentifier.get_field_names(data),
            "has_dates": False,
            "has_priorities": False,
            "has_status": False,
        }
        
        if data:
            first_item = data[0]
            characteristics["has_dates"] = any(k in first_item for k in ["date", "created_at", "timestamp"])
            characteristics["has_priorities"] = "priority" in first_item
            characteristics["has_status"] = "status" in first_item
        
        logger.info(f"Data characteristics: {characteristics}")
        return characteristics

    @staticmethod
    def get_data_summary(data: List[Dict[str, Any]]) -> str:
        """
        Get a human-readable summary of the data.
        
        Args:
            data: List of data dictionaries
            
        Returns:
            Summary string
        """
        if not data:
            return "No data available"
        
        data_type = DataIdentifier.identify_data_type(data)
        record_count = len(data)
        fields = DataIdentifier.get_field_names(data)
        
        return f"{record_count} {data_type.value} records with fields: {', '.join(fields)}"


# Create singleton instance
data_identifier = DataIdentifier()
