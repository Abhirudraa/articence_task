import logging
from fastapi import APIRouter, Query, Path, HTTPException
from typing import Optional
from datetime import datetime
from app.connectors.crm_connector import CRMConnector
from app.connectors.support_connector import SupportConnector
from app.connectors.analytics_connector import AnalyticsConnector
from app.services.business_rules import business_rules
from app.services.voice_optimizer import voice_optimizer
from app.services.data_identifier import data_identifier
from app.services.query_executor import query_executor
from app.models.common import DataResponse, Metadata, DataTypeEnum, QueryRequest, QueryResponse
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/data", tags=["data"])

# Initialize connectors
crm_connector = CRMConnector()
support_connector = SupportConnector()
analytics_connector = AnalyticsConnector()


@router.get("/customers", response_model=DataResponse)
async def get_customers(  # Make this async
    status: Optional[str] = Query(None, description="Filter by status (active/inactive)"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results"),
):
    """
    Get customer data from CRM.
    
    Supports filtering by status and pagination.
    Optimized for voice conversations.
    
    Args:
        status: Optional status filter
        limit: Maximum number of results
        
    Returns:
        DataResponse with customer data and metadata
    """
    try:
        # Normalize parameters
        status = status.strip().lower() if status else None
        
        logger.debug(f"Fetching customers: status={status}, limit={limit}")
        
        # Fetch data - ADD AWAIT HERE
        raw_data = await crm_connector.fetch(status=status, limit=limit)  # Added await
        total_available = len(raw_data)
        
        # Identify data type (handles empty data gracefully)
        data_type = data_identifier.identify_data_type(raw_data)

        # Apply voice optimization, but honor explicit user limits larger than threshold
        if settings.ENABLE_VOICE_OPTIMIZATION:
            if limit and limit > settings.VOICE_SUMMARY_THRESHOLD:
                logger.debug(f"User requested limit={limit} > VOICE_SUMMARY_THRESHOLD; skipping summarization")
                optimized_data = raw_data
            else:
                optimized_data = voice_optimizer.summarize_if_large(raw_data)
        else:
            optimized_data = raw_data
        
        # Build metadata
        context = business_rules.build_context_message(
            total_available,
            len(optimized_data),
            "customer"
        )
        
        metadata = Metadata(
            total_results=total_available,
            returned_results=len(optimized_data),
            data_type=data_type,
            data_freshness=f"Data as of {datetime.utcnow().isoformat()}",
            context=context,
            has_more=len(optimized_data) < total_available
        )
        
        logger.debug(f"Returning {len(optimized_data)} of {total_available} customer records")
        return DataResponse(data=optimized_data, metadata=metadata)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching customers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/support-tickets", response_model=DataResponse)
async def get_support_tickets(  # Make this async
    status: Optional[str] = Query(None, description="Filter by status (open/closed)"),
    priority: Optional[str] = Query(None, description="Filter by priority (low/medium/high)"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results"),
):
    """
    Get support ticket data.
    
    Supports filtering by status and priority.
    Optimized for voice conversations.
    
    Args:
        status: Optional status filter
        priority: Optional priority filter
        limit: Maximum number of results
        
    Returns:
        DataResponse with support ticket data and metadata
    """
    try:
        # Normalize parameters
        status = status.strip().lower() if status else None
        priority = priority.strip().lower() if priority else None
        
        logger.debug(f"Fetching support tickets: status={status}, priority={priority}, limit={limit}")
        
        # Fetch data - ADD AWAIT HERE
        raw_data = await support_connector.fetch(status=status, priority=priority, limit=limit)  # Added await
        total_available = len(raw_data)
        
        # Identify data type (handles empty data gracefully)
        data_type = data_identifier.identify_data_type(raw_data)

        # Apply voice optimization, but honor explicit user limits larger than threshold
        if settings.ENABLE_VOICE_OPTIMIZATION:
            if limit and limit > settings.VOICE_SUMMARY_THRESHOLD:
                logger.debug(f"User requested limit={limit} > VOICE_SUMMARY_THRESHOLD; skipping summarization")
                optimized_data = raw_data
            else:
                optimized_data = voice_optimizer.summarize_if_large(raw_data)
        else:
            optimized_data = raw_data
        
        # Add priority summary
        priority_summary = voice_optimizer._summarize_priority(optimized_data)
        
        # Build metadata
        context = business_rules.build_context_message(
            total_available,
            len(optimized_data),
            "support ticket"
        )
        
        metadata = Metadata(
            total_results=total_available,
            returned_results=len(optimized_data),
            data_type=data_type,
            data_freshness=f"Data as of {datetime.utcnow().isoformat()}",
            context=f"{context} - Priority breakdown: {priority_summary}",
            has_more=len(optimized_data) < total_available
        )
        
        logger.debug(f"Returning {len(optimized_data)} of {total_available} support tickets")
        return DataResponse(data=optimized_data, metadata=metadata)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching support tickets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics", response_model=DataResponse)
async def get_analytics(  # Make this async
    metric: Optional[str] = Query(None, description="Filter by metric name"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results"),
):
    """
    Get analytics and metrics data.
    
    Returns time-series metrics.
    Optimized for voice conversations.
    
    Args:
        metric: Optional metric name filter
        limit: Maximum number of results
        
    Returns:
        DataResponse with analytics data and metadata
    """
    try:
        # Normalize metric parameter - convert hyphens to underscores
        metric = metric.strip().replace("-", "_") if metric else None
        
        logger.debug(f"Fetching analytics: metric={metric}, limit={limit}")
        
        # Fetch data - ADD AWAIT HERE
        raw_data = await analytics_connector.fetch(metric=metric, limit=limit)  # Added await
        total_available = len(raw_data)
        
        # Identify data type (handles empty data gracefully)
        data_type = data_identifier.identify_data_type(raw_data)

        # Apply voice optimization, but honor explicit user limits larger than threshold
        if settings.ENABLE_VOICE_OPTIMIZATION:
            if limit and limit > settings.VOICE_SUMMARY_THRESHOLD:
                logger.debug(f"User requested limit={limit} > VOICE_SUMMARY_THRESHOLD; skipping summarization")
                optimized_data = raw_data
            else:
                optimized_data = voice_optimizer.summarize_if_large(raw_data)
        else:
            optimized_data = raw_data
        
        # Calculate trend
        trend = voice_optimizer._calculate_trend(optimized_data)
        
        # Build metadata
        context = business_rules.build_context_message(
            total_available,
            len(optimized_data),
            "metric"
        )
        if trend:
            context += f" - Trend: {trend}"
        
        metadata = Metadata(
            total_results=total_available,
            returned_results=len(optimized_data),
            data_type=data_type,
            data_freshness=f"Data as of {datetime.utcnow().isoformat()}",
            context=context,
            has_more=len(optimized_data) < total_available
        )
        
        logger.debug(f"Returning {len(optimized_data)} of {total_available} analytics records")
        return DataResponse(data=optimized_data, metadata=metadata)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{source}", response_model=DataResponse)
async def get_data(  # Make this async
    source: str = Path(..., description="Data source: customers, support-tickets, or analytics"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results"),
):
    """
    Generic data endpoint supporting multiple sources.
    
    Args:
        source: Data source name
        limit: Maximum number of results
        
    Returns:
        DataResponse with data and metadata
    """
    source_lower = source.lower()
    
    if source_lower in ["customers", "crm"]:
        return await get_customers(limit=limit)  # Added await
    elif source_lower in ["support-tickets", "support", "tickets"]:
        return await get_support_tickets(limit=limit)  # Added await
    elif source_lower in ["analytics", "metrics"]:
        return await get_analytics(limit=limit)  # Added await
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown data source: {source}. Supported: customers, support-tickets, analytics"
        )


@router.get("/connectors/info", tags=["metadata"])
async def get_connectors_info():  # Make this async (though it doesn't need to be, but for consistency)
    """
    Get information about all available connectors.
    
    Returns:
        Dictionary with metadata for each connector
    """
    logger.debug("Fetching connector information")
    return {
        "customers": crm_connector.get_metadata(),
        "support_tickets": support_connector.get_metadata(),
        "analytics": analytics_connector.get_metadata()
    }


@router.get("/summary/all", tags=["summary"])
async def get_all_summary(limit: int = Query(5, ge=1, le=20, description="Results per data source")):
    """
    Get a summary of all data sources.
    Voice-optimized view of what's available.
    
    Args:
        limit: Number of items to return per source
        
    Returns:
        Summary of all data sources
    """
    try:
        logger.debug(f"Fetching all data summaries with limit={limit}")
        
        # Fetch data with await
        customers = await crm_connector.fetch(limit=limit)
        tickets = await support_connector.fetch(limit=limit)
        analytics_data = await analytics_connector.fetch(limit=limit)
        
        return {
            "customers": {
                "count": len(customers),
                "sample": customers[:3]
            },
            "support_tickets": {
                "count": len(tickets),
                "sample": tickets[:3]
            },
            "analytics": {
                "count": len(analytics_data),
                "summary": analytics_connector.summarize_metrics(limit=limit)
            }
        }
    except Exception as e:
        logger.error(f"Error fetching summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Note: The /ask endpoint uses query_executor which is already handling async correctly
@router.post("/ask", response_model=QueryResponse, tags=["intelligent-query"])
async def ask_question(request: QueryRequest):
    """
    Ask an intelligent question in natural language.
    
    This endpoint:
    1. Parses your natural language query
    2. Extracts intent and parameters
    3. Routes to built-in functions for simple queries (fast, no tokens)
    4. Falls back to LLM for complex analysis (when needed)
    
    Examples:
    - "Show me active customers"
    - "How many open high-priority tickets?"
    - "List the last 10 analytics records"
    - "Give me a ticket summary"
    - "What's the trend in daily active users?" (shows trend info)
    - "Which inactive customers have open tickets?" (complex - routes to LLM)
    
    Args:
        request: QueryRequest with natural language query
        
    Returns:
        QueryResponse with answer and metadata
    """
    try:
        logger.info(f"Processing intelligent query: {request.query}")
        
        # Execute query
        result = await query_executor.execute(request.query)  # Note: This needs to be async too
        
        logger.info(f"Query result: status={result['status']}, used_llm={result['used_llm']}")
        return result
        
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ask/examples", tags=["intelligent-query"])
async def get_query_examples():  # Make this async for consistency
    """
    Get examples of queries you can ask.
    
    Returns examples for different query types and complexities.
    """
    return {
        "simple_customer_queries": [
            "Show me active customers",
            "List inactive customers",
            "How many customers do we have?",
            "Give me customer summary"
        ],
        "simple_ticket_queries": [
            "Show open tickets",
            "List high-priority tickets",
            "How many open tickets?",
            "Ticket summary",
            "Show me closed issues",
            "List critical support issues"
        ],
        "simple_analytics_queries": [
            "Show daily active users",
            "List recent metrics",
            "Get last 5 analytics records",
            "What's the trend in daily active users?"
        ],
        "complex_queries_llm_required": [
            "Which inactive customers have the most open tickets?",
            "Show me a correlation between ticket priority and customer status",
            "Analyze which support issues are most common among active customers",
            "What's the relationship between user activity and support tickets?",
            "Predict which customers might churn based on their support activity"
        ],
        "note": "Simple queries use built-in functions (instant, no token cost). Complex queries route to LLM."
    }