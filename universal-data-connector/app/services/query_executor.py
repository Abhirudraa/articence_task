"""Query executor for handling built-in and LLM-based responses."""

import logging
from typing import Dict, Any, Optional
from app.services.query_analyzer import QueryAnalyzer, QueryType, QueryComplexity
from app.services.llm_service import get_openai_service
from app.connectors.crm_connector import CRMConnector
from app.connectors.support_connector import SupportConnector
from app.connectors.analytics_connector import AnalyticsConnector
from app.services.voice_optimizer import voice_optimizer
from app.config import settings

logger = logging.getLogger(__name__)


class QueryExecutor:
    """Executes queries using built-in functions or LLM fallback."""

    def __init__(self):
        """Initialize executor with connectors."""
        self.crm = CRMConnector()
        self.support = SupportConnector()
        self.analytics = AnalyticsConnector()
        self.llm = None
        
        # Initialize LLM if enabled
        if settings.ENABLE_LLM:
            try:
                self.llm = get_openai_service()
                logger.info("LLM service initialized")
            except ValueError as e:
                logger.warning(f"LLM service not available: {e}")
                self.llm = None

    async def execute(self, query: str) -> Dict[str, Any]:  # Make this async
        """
        Execute a query intelligently.
        
        Args:
            query: Natural language query
            
        Returns:
            Response dictionary with result and metadata
        """
        logger.debug(f"Executing query: {query}")
        
        # Analyze query
        analysis = QueryAnalyzer.analyze(query)
        
        # Route based on complexity
        if analysis["requires_llm"] and analysis["complexity"] == QueryComplexity.COMPLEX:
            # Only use LLM for truly complex/conversational queries
            return await self._execute_complex_query(query, analysis)  # Add await
        elif analysis["complexity"] in [QueryComplexity.SIMPLE, QueryComplexity.MODERATE]:
            # Try data functions for simple and moderate queries (includes relationship queries)
            return await self._execute_simple_query(analysis)  # Add await
        else:
            # Fallback: try data first, then LLM
            result = await self._execute_simple_query(analysis)  # Add await
            if result["count"] == 0 and self.llm:
                logger.debug(f"No data found, routing to LLM")
                return await self._execute_complex_query(query, analysis)  # Add await
            return result

    async def _execute_simple_query(self, analysis: Dict[str, Any]) -> Dict[str, Any]:  # Make this async
        """Execute simple queries using built-in functions."""
        query_type = analysis["type"]
        params = analysis["parameters"]
        limit = analysis["limit"]
        
        logger.debug(f"Executing simple query: type={query_type}")
        
        try:
            # Customer queries
            if query_type == QueryType.LIST_CUSTOMERS:
                # Handle relationship queries where user asks about customers filtered by ticket attributes
                # e.g., "customers whose ticket priority is medium and status open"
                if params.get("priority") and params.get("status") in ["open", "closed"]:
                    # Fetch tickets matching the ticket filters (no limit)
                    tickets = await self.support.fetch(status=params.get("status"), priority=params.get("priority"), limit=None)  # Add await
                    customer_ids = {t.get("customer_id") for t in tickets if t.get("customer_id") is not None}

                    if not customer_ids:
                        return self._build_response(
                            [],
                            "Found 0 customers matching the ticket filters",
                            "simple",
                            analysis
                        )

                    # Fetch all customers and filter by customer_id set
                    all_customers = await self.crm.fetch(limit=None)  # Add await
                    matched_customers = [c for c in all_customers if c.get("customer_id") in customer_ids]

                    # Apply requested limit
                    if limit:
                        matched_customers = matched_customers[:limit]

                    return self._build_response(
                        matched_customers,
                        f"Found {len(matched_customers)} customer(s) matching ticket filters",
                        "simple",
                        analysis
                    )

                # Default customer listing (no cross-source filters)
                data = await self.crm.fetch(status=params.get("status"), limit=limit)  # Add await
                return self._build_response(
                    data,
                    f"Found {len(data)} customer(s)",
                    "simple",
                    analysis
                )
            
            elif query_type == QueryType.CUSTOMER_COUNT:
                data = await self.crm.fetch()  # Add await
                status = params.get("status")
                if status:
                    filtered = self.crm.filter_by_status(data, status)
                    count = len(filtered)
                    return self._build_response(
                        [{"count": count, "status": status}],
                        f"Total {status} customers: {count}",
                        "simple",
                        analysis
                    )
                return self._build_response(
                    [{"count": len(data)}],
                    f"Total customers: {len(data)}",
                    "simple",
                    analysis
                )
            
            elif query_type == QueryType.CUSTOMER_SUMMARY:
                data = await self.crm.fetch()  # Add await
                active = len(self.crm.filter_by_status(data, "active"))
                inactive = len(self.crm.filter_by_status(data, "inactive"))
                return self._build_response(
                    [{
                        "total": len(data),
                        "active": active,
                        "inactive": inactive,
                        "active_percentage": round((active / len(data) * 100), 1) if data else 0
                    }],
                    f"Customer Summary: {active} active, {inactive} inactive",
                    "simple",
                    analysis
                )
            
            # Ticket queries
            elif query_type == QueryType.LIST_TICKETS:
                data = await self.support.fetch(  # Add await
                    status=params.get("status"),
                    priority=params.get("priority"),
                    limit=limit
                )
                return self._build_response(
                    data,
                    f"Found {len(data)} ticket(s)",
                    "simple",
                    analysis
                )
            
            elif query_type == QueryType.TICKET_COUNT:
                data = await self.support.fetch()  # Add await
                status = params.get("status")
                if status:
                    filtered = self.support.filter_by_status(data, status)
                    count = len(filtered)
                    return self._build_response(
                        [{"count": count, "status": status}],
                        f"Total {status} tickets: {count}",
                        "simple",
                        analysis
                    )
                return self._build_response(
                    [{"count": len(data)}],
                    f"Total tickets: {len(data)}",
                    "simple",
                    analysis
                )
            
            elif query_type == QueryType.TICKET_SUMMARY:
                data = await self.support.fetch()  # Add await
                
                # Priority breakdown
                priority_breakdown = voice_optimizer._summarize_priority(data)
                
                # Status breakdown
                open_tickets = len([x for x in data if x.get("status") == "open"])
                closed_tickets = len([x for x in data if x.get("status") == "closed"])
                
                return self._build_response(
                    [{
                        "total": len(data),
                        "open": open_tickets,
                        "closed": closed_tickets,
                        "priority_breakdown": priority_breakdown
                    }],
                    f"Ticket Summary: {open_tickets} open, {closed_tickets} closed",
                    "simple",
                    analysis
                )
            
            # Analytics queries
            elif query_type == QueryType.LIST_ANALYTICS:
                data = await self.analytics.fetch(  # Add await
                    metric=params.get("metric"),
                    limit=limit
                )
                return self._build_response(
                    data,
                    f"Found {len(data)} metric(s)",
                    "simple",
                    analysis
                )
            
            elif query_type == QueryType.ANALYTICS_TREND:
                data = await self.analytics.fetch(  # Add await
                    metric=params.get("metric", "daily_active_users"),
                    limit=7
                )
                if len(data) >= 2:
                    trend = voice_optimizer._calculate_trend(data)
                    recent = data[0].get("value", 0)
                    return self._build_response(
                        [{
                            "metric": data[0].get("metric"),
                            "latest_value": recent,
                            "latest_date": data[0].get("date"),
                            "trend": trend,
                            "data_points": len(data)
                        }],
                        f"Metric: {data[0].get('metric')} - Latest: {recent} - Trend: {trend}",
                        "simple",
                        analysis
                    )
                return self._build_response(
                    data,
                    "Not enough data for trend analysis",
                    "simple",
                    analysis
                )
            
            else:
                return self._build_error_response(
                    "Could not understand query type",
                    analysis
                )
        
        except Exception as e:
            logger.error(f"Error executing simple query: {e}")
            return self._build_error_response(str(e), analysis)

    async def _execute_complex_query(self, query: str, analysis: Dict[str, Any]) -> Dict[str, Any]:  # Make this async
        """Execute complex queries using LLM with improved prompt engineering."""
        logger.debug(f"Routing to LLM for complex query: {query}")

        # Check if LLM is available
        if not self.llm:
            logger.warning("LLM not available, returning fallback response")
            return self._build_llm_unavailable_response(query, analysis)

        try:
            # Build rich context for the LLM: include data summary and extracted parameters
            data_context = await self._build_data_context()  # Add await
            prompt = self._build_llm_prompt(query, analysis, data_context)

            # Call LLM with controlled token limits
            max_tokens = analysis.get("max_tokens") or settings.GEMINI_MAX_TOKENS
            llm_result = self.llm.query(prompt, max_output_tokens=max_tokens) if hasattr(self.llm, 'query') else self.llm.query(prompt)

            # Check if call was successful
            if llm_result.get("status") == "success":
                logger.info(f"LLM analysis successful. Tokens: {llm_result.get('tokens', {}).get('total')}")

                response_text = llm_result.get("response", "")

                # Try to parse structured JSON response from LLM if present
                parsed = None
                try:
                    import json
                    parsed = json.loads(response_text)
                except Exception:
                    parsed = None

                if isinstance(parsed, dict):
                    answer = parsed.get("answer") or parsed.get("message") or response_text
                    explanation = parsed.get("explanation")
                    used_data = parsed.get("used_data")
                else:
                    answer = response_text
                    explanation = None
                    used_data = None

                return {
                    "status": "success",
                    "query": query,
                    "query_type": str(analysis["type"].value),
                    "complexity": str(analysis["complexity"].value),
                    "message": answer,
                    "response_type": "llm_analysis",
                    "used_llm": True,
                    "data": [{"analysis": answer, "explanation": explanation, "used_data": used_data}],
                    "count": 1,
                    "confidence": analysis["confidence"],
                    "metadata": {
                        "llm_model": llm_result.get("model"),
                        "tokens_used": llm_result.get("tokens", {}).get("total"),
                        "cost": llm_result.get("costs", {}).get("total_cost")
                    }
                }
            else:
                logger.error(f"LLM call failed: {llm_result.get('message')}")
                return {
                    "status": "error",
                    "query": query,
                    "query_type": str(analysis["type"].value),
                    "complexity": str(analysis["complexity"].value),
                    "message": f"LLM error: {llm_result.get('message')}",
                    "response_type": "error",
                    "used_llm": True,
                    "data": [],
                    "count": 0,
                    "confidence": analysis["confidence"],
                    "fallback": {
                        "action": "TRY_AGAIN_LATER",
                        "reason": llm_result.get("message", "Unknown error")
                    }
                }

        except Exception as e:
            logger.error(f"Error in LLM query execution: {e}")
            return {
                "status": "error",
                "query": query,
                "query_type": str(analysis["type"].value),
                "complexity": str(analysis["complexity"].value),
                "message": f"Unexpected error: {str(e)}",
                "response_type": "error",
                "used_llm": True,
                "data": [],
                "count": 0,
                "confidence": analysis["confidence"]
            }

    async def _build_data_context(self) -> str:  # Make this async
        """Build a summary of available data for LLM context."""
        try:
            # Fetch data with await
            customers = await self.crm.fetch()  # Add await
            tickets = await self.support.fetch()  # Add await
            analytics = await self.analytics.fetch()  # Add await
            
            # Count statuses without fetching again
            active_count = len([c for c in customers if c.get('status') == 'active'])  # Use list comprehension instead
            inactive_count = len([c for c in customers if c.get('status') == 'inactive'])
            
            open_count = len([t for t in tickets if t.get('status') == 'open'])
            closed_count = len([t for t in tickets if t.get('status') == 'closed'])
            
            high_priority = len([t for t in tickets if t.get('priority') == 'high'])
            medium_priority = len([t for t in tickets if t.get('priority') == 'medium'])
            low_priority = len([t for t in tickets if t.get('priority') == 'low'])
            
            context = f"""
** CUSTOMERS **
Total: {len(customers)}
- Active: {active_count}
- Inactive: {inactive_count}
Sample: {[f"{c['customer_id']} ({c['status']})" for c in customers[:3]]}

** SUPPORT TICKETS **
Total: {len(tickets)}
- Open: {open_count}
- Closed: {closed_count}
Priority: High={high_priority}, Medium={medium_priority}, Low={low_priority}

** ANALYTICS **
Latest: {analytics[0] if analytics else 'No data'}
Trend: {voice_optimizer._calculate_trend(analytics) if analytics else 'N/A'}
"""
            return context
        except Exception as e:
            logger.warning(f"Could not build data context: {e}")
            return "Data unavailable"

    def _build_llm_unavailable_response(self, query: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Build response when LLM is not available."""
        return {
            "status": "fallback_to_manual",
            "query": query,
            "query_type": str(analysis["type"].value),
            "complexity": str(analysis["complexity"].value),
            "message": "Complex query detected but LLM is not configured. Please set GEMINI_API_KEY in .env",
            "response_type": "error",
            "used_llm": False,
            "data": [],
            "confidence": analysis["confidence"],
            "instructions": {
                "action": "CONFIGURE_LLM",
                "steps": [
                    "1. Get Gemini API key from https://aistudio.google.com/app/apikey",
                    "2. Add to .env: GEMINI_API_KEY=your-key-here",
                    "3. Restart the application",
                    "4. Try the query again"
                ]
            }
        }

    def _build_llm_prompt(self, query: str, analysis: Dict[str, Any], data_context: str = "") -> str:
        """Build an improved structured prompt for LLM with explicit instructions.

        The LLM should return a short, voice-optimized `answer` and an optional
        `explanation`. Prefer JSON output when possible to allow structured parsing.
        """
        instructions = (
            "You are a data assistant that helps answer questions based on the system's data. "
            "Produce a concise answer suitable for voice (1-2 sentences). If the question requires reasoning, include a short explanation in the 'explanation' field. "
            "Return output as JSON with keys: 'answer' (string), 'explanation' (optional string), 'used_data' (optional summary)."
        )

        examples = (
            "Example JSON output: {\"answer\": \"There are 12 active customers.\", \"explanation\": \"Counted active customers from CRM.\" }"
        )

        prompt = f"""
{instructions}

User Query: {query}

Extracted Parameters: {analysis.get('parameters')}
Query Type: {analysis.get('type')}
Confidence: {analysis.get('confidence')}

Data Context (summary):
{data_context}

If you cannot answer from available data, say so and suggest which endpoints or filters to use.

{examples}

Provide only JSON in your final response when possible.
"""
        return prompt

    def _build_response(
        self,
        data: list,
        message: str,
        response_type: str,
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build a standard response."""
        return {
            "status": "success",
            "query": analysis["query"],
            "query_type": str(analysis["type"].value),
            "complexity": str(analysis["complexity"].value),
            "message": message,
            "response_type": response_type,
            "used_llm": False,
            "data": data,
            "count": len(data),
            "confidence": analysis["confidence"],
            "metadata": {
                "extracted_params": analysis["parameters"],
                "query_limit": analysis["limit"]
            }
        }

    def _build_error_response(self, error: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Build an error response."""
        return {
            "status": "error",
            "query": analysis["query"],
            "query_type": str(analysis["type"].value),
            "complexity": str(analysis["complexity"].value),
            "message": error,
            "response_type": "error",
            "used_llm": False,
            "data": [],
            "count": 0,
            "confidence": analysis["confidence"],
            "fallback": {
                "action": "ROUTE_TO_LLM",
                "reason": "Could not execute with built-in functions"
            }
        }


# Create singleton instance
query_executor = QueryExecutor()