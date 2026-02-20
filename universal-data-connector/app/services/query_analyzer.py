"""Query analyzer for natural language understanding."""

import logging
import re
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class QueryType(str, Enum):
    """Types of queries."""
    LIST_CUSTOMERS = "list_customers"
    LIST_TICKETS = "list_tickets"
    LIST_ANALYTICS = "list_analytics"
    CUSTOMER_COUNT = "customer_count"
    TICKET_COUNT = "ticket_count"
    TICKET_SUMMARY = "ticket_summary"
    CUSTOMER_SUMMARY = "customer_summary"
    ANALYTICS_TREND = "analytics_trend"
    COMPLEX_ANALYSIS = "complex_analysis"
    UNKNOWN = "unknown"


class QueryComplexity(str, Enum):
    """Query complexity levels."""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"


class QueryAnalyzer:
    """Analyzes natural language queries to extract intent and parameters."""

    # Keywords for different intents
    CUSTOMER_KEYWORDS = ["customer", "client", "account", "user", "users"]
    TICKET_KEYWORDS = ["ticket", "issue", "problem", "support", "help"]
    ANALYTICS_KEYWORDS = ["metric", "analytics", "data", "active", "performance", "trend"]
    
    STATUS_KEYWORDS = {
        "active": "active",
        "inactive": "inactive",
        "open": "open",
        "closed": "closed"
    }
    
    PRIORITY_KEYWORDS = {
        "high": "high",
        "critical": "high",
        "urgent": "high",
        "medium": "medium",
        "low": "low",
        "minor": "low"
    }

    @staticmethod
    def analyze(query: str) -> Dict[str, Any]:
        """
        Analyze a natural language query.
        
        Args:
            query: Natural language query
            
        Returns:
            Dictionary with query analysis
        """
        logger.debug(f"Analyzing query: {query}")
        
        # Normalize query
        query_lower = query.lower().strip()
        
        # Detect query type
        query_type = QueryAnalyzer._detect_query_type(query_lower)
        
        # Extract parameters
        params = QueryAnalyzer._extract_parameters(query_lower)
        
        # Determine complexity
        complexity = QueryAnalyzer._determine_complexity(query_type, query_lower)
        
        # Extract limit/count
        limit = QueryAnalyzer._extract_limit(query_lower)
        
        analysis = {
            "query": query,
            "query_lower": query_lower,
            "type": query_type,
            "complexity": complexity,
            "parameters": params,
            "limit": limit,
            "requires_llm": complexity == QueryComplexity.COMPLEX,
            "confidence": QueryAnalyzer._calculate_confidence(query_type),
            # Hint for response style: concise, professional; include humble apology if uncertain
            "response_style": {
                "tone": "professional",
                "concise_for_voice": True,
                "apologize_if_incorrect": True
            }
        }
        
        logger.debug(f"Query analysis: type={query_type}, complexity={complexity}, requires_llm={complexity == QueryComplexity.COMPLEX}")
        # Post-process: detect relationship/relationship-language queries that require cross-entity reasoning
        relationship_markers = ["whose", "that have", "having", "with", "which have", "who have", "which have"]

        # If parameters indicate ticket-level filters (priority) along with ticket status
        if params.get("priority") and params.get("status") in ["open", "closed"]:
            analysis["complexity"] = QueryComplexity.COMPLEX
            analysis["requires_llm"] = True

        # If query contains relationship markers and mentions more than one domain, escalate to COMPLEX
        domain_hits = 0
        for kw_list in [QueryAnalyzer.CUSTOMER_KEYWORDS, QueryAnalyzer.TICKET_KEYWORDS, QueryAnalyzer.ANALYTICS_KEYWORDS]:
            if any(kw in query_lower for kw in kw_list):
                domain_hits += 1

        if domain_hits >= 2 and any(marker in query_lower for marker in relationship_markers):
            analysis["complexity"] = QueryComplexity.COMPLEX
            analysis["requires_llm"] = True

        logger.debug(f"Post-processed analysis: complexity={analysis['complexity']}, requires_llm={analysis['requires_llm']}")
        return analysis

    @staticmethod
    def _detect_query_type(query_lower: str) -> QueryType:
        """Detect the type of query."""
        # Normalize some common count phrases
        count_phrases = ["count", "how many", "no. of", "no of", "number of"]

        # Check if it's about customers
        if any(kw in query_lower for kw in QueryAnalyzer.CUSTOMER_KEYWORDS):
            if any(phrase in query_lower for phrase in count_phrases):
                return QueryType.CUSTOMER_COUNT
            if "summary" in query_lower or "overview" in query_lower:
                return QueryType.CUSTOMER_SUMMARY
            return QueryType.LIST_CUSTOMERS
        
        # Check if it's about tickets
        if any(kw in query_lower for kw in QueryAnalyzer.TICKET_KEYWORDS):
            if any(phrase in query_lower for phrase in count_phrases):
                return QueryType.TICKET_COUNT
            if "summary" in query_lower or "overview" in query_lower or "breakdown" in query_lower:
                return QueryType.TICKET_SUMMARY
            return QueryType.LIST_TICKETS
        
        # Check if it's about analytics
        if any(kw in query_lower for kw in QueryAnalyzer.ANALYTICS_KEYWORDS):
            if "trend" in query_lower or "change" in query_lower or "growth" in query_lower:
                return QueryType.ANALYTICS_TREND
            return QueryType.LIST_ANALYTICS
        
        return QueryType.UNKNOWN

    @staticmethod
    def _extract_parameters(query_lower: str) -> Dict[str, str]:
        """Extract parameters from query."""
        params = {}
        
        # Extract status
        for keyword, status_value in QueryAnalyzer.STATUS_KEYWORDS.items():
            if keyword in query_lower:
                params["status"] = status_value
                break
        
        # Extract priority
        for keyword, priority_value in QueryAnalyzer.PRIORITY_KEYWORDS.items():
            if keyword in query_lower:
                params["priority"] = priority_value
                break
        
        # Extract metric name
        if "daily" in query_lower and "user" in query_lower:
            params["metric"] = "daily_active_users"
        
        return params

    @staticmethod
    def _extract_limit(query_lower: str) -> int:
        """Extract limit/count from query."""
        
        # Look for "top N" or "first N"
        match = re.search(r'(?:top|first|show me|give me|list)\s+(\d+)', query_lower)
        if match:
            return int(match.group(1))
        
        # Look for number words
        number_words = {
            "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
            "ten": 10, "few": 5, "several": 5
        }
        
        for word, num in number_words.items():
            if word in query_lower:
                return num
        
        # Default limit
        return 10

    @staticmethod
    def _determine_complexity(query_type: QueryType, query_lower: str) -> QueryComplexity:
        """Determine query complexity based on whether data can answer it."""
        
        # SIMPLE: Direct data queries that built-in functions can handle
        if query_type in [
            QueryType.LIST_CUSTOMERS,
            QueryType.LIST_TICKETS,
            QueryType.LIST_ANALYTICS,
            QueryType.CUSTOMER_COUNT,
            QueryType.TICKET_COUNT
        ]:
            return QueryComplexity.SIMPLE
        
        # MODERATE: Summaries and trends
        if query_type in [QueryType.CUSTOMER_SUMMARY, QueryType.TICKET_SUMMARY]:
            return QueryComplexity.MODERATE
        
        if query_type == QueryType.ANALYTICS_TREND:
            return QueryComplexity.MODERATE
        
        # Data-answerable complex queries (don't need LLM)
        data_answerable_keywords = [
            "compare", "which", "most", "least", "count",
            "total", "average", "breakdown", "distribution",
            "customer.*ticket", "ticket.*customer",  # Relationship queries
            "priority.*metric", "status.*analysis"
        ]
        
        if any(kw in query_lower for kw in data_answerable_keywords):
            # Check if it's specifically about our data
            if any(kw in query_lower for kw in QueryAnalyzer.CUSTOMER_KEYWORDS + QueryAnalyzer.TICKET_KEYWORDS + QueryAnalyzer.ANALYTICS_KEYWORDS):
                return QueryComplexity.MODERATE  # Use built-in processing

        # If the query mentions more than one domain (customers, tickets, analytics)
        # and contains relationship/analysis wording, treat as COMPLEX so LLM can reason.
        domain_hits = 0
        for kw_list in [QueryAnalyzer.CUSTOMER_KEYWORDS, QueryAnalyzer.TICKET_KEYWORDS, QueryAnalyzer.ANALYTICS_KEYWORDS]:
            if any(kw in query_lower for kw in kw_list):
                domain_hits += 1

        relationship_terms = ["correlat", "relationship", "correlation", "which", "between", "among", "related to", "impact", "influence"]
        if domain_hits >= 2 and any(term in query_lower for term in relationship_terms):
            return QueryComplexity.COMPLEX
        
        # COMPLEX: Only for true conversational/analytical questions outside data scope
        # (greetings, general advice, etc.)
        if query_type == QueryType.UNKNOWN:
            # Check if it's actually asking about conversational topics
            conversational_keywords = [
                "how are you", "hello", "hi ", "bye", "thanks", "help with",
                "what is", "who is", "explain", "tell me about", "general",
                "best practice", "advice", "opinion", "recommend"
            ]
            if any(kw in query_lower for kw in conversational_keywords):
                return QueryComplexity.COMPLEX
            
            # Otherwise, try data functions first
            return QueryComplexity.MODERATE
        
        return QueryComplexity.SIMPLE

    @staticmethod
    def _calculate_confidence(query_type: QueryType) -> float:
        """Calculate confidence in query understanding."""
        if query_type == QueryType.UNKNOWN:
            return 0.3
        if query_type in [QueryType.LIST_CUSTOMERS, QueryType.LIST_TICKETS, QueryType.LIST_ANALYTICS]:
            return 0.9
        return 0.7
