"""LLM service for Google Gemini integration."""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import google.generativeai as genai
from app.config import settings

logger = logging.getLogger(__name__)


class GeminiService:
    """Service for Google Gemini API interactions."""

    def __init__(self):
        """Initialize Gemini service."""
        if not settings.GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY not set. Please add it to .env file.\n"
                "Get your key from: https://aistudio.google.com/app/apikey"
            )
        
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = settings.GEMINI_MODEL
        self.call_history: List[Dict[str, Any]] = []
        
        logger.info(f"Initialized Gemini service with model: {self.model}")

    def query(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Query Gemini API.
        
        Args:
            prompt: Input prompt for Gemini
            **kwargs: Additional parameters
            
        Returns:
            Dictionary with response and token usage
        """
        try:
            logger.info(f"Calling Gemini for query (prompt: {len(prompt)} chars)")
            
            # Create Gemini model
            model = genai.GenerativeModel(self.model)
            
            # Generate response
            generation_config = genai.types.GenerationConfig(
                max_output_tokens=settings.GEMINI_MAX_TOKENS,
                temperature=settings.GEMINI_TEMPERATURE
            )
            
            response = model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            # Extract response text
            response_text = response.text if response.text else "No response"
            
            # Get token usage (Gemini provides usage info)
            input_tokens = len(prompt.split()) * 1.5  # Rough estimate
            output_tokens = len(response_text.split()) * 1.5
            
            result = {
                "status": "success",
                "response": response_text,
                "model": self.model,
                "tokens": {
                    "input": int(input_tokens),
                    "output": int(output_tokens),
                    "total": int(input_tokens + output_tokens)
                },
                "costs": {
                    "input_cost": 0.0,  # Gemini is free
                    "output_cost": 0.0,
                    "total_cost": 0.0
                }
            }
            
            self.call_history.append(result)
            logger.info(f"Gemini response successful")
            return result
            
        except Exception as e:
            logger.error(f"Gemini error: {e}")
            return self._build_error_response("Query failed", e)

    def _build_error_response(self, message: str, error: Exception) -> Dict[str, Any]:
        """Build error response."""
        return {
            "status": "error",
            "message": f"{message}: {str(error)}",
            "error_type": type(error).__name__,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics."""
        total_tokens = sum(c["tokens"]["total"] for c in self.call_history)
        return {
            "total_calls": len(self.call_history),
            "model": self.model,
            "total_tokens": total_tokens,
            "total_cost": 0.0,  # Gemini free tier
            "currency": "USD",
            "average_tokens_per_call": round(total_tokens / len(self.call_history), 1) if self.call_history else 0,
            "calls": self.call_history
        }


class MockLLMService:
    """Mock LLM service for testing without API costs."""
    
    def __init__(self):
        """Initialize mock LLM service."""
        self.model = "mock-gemini-pro"
        self.call_history: List[Dict[str, Any]] = []
        logger.info("Initialized Mock LLM service (no API costs)")
        
        self.mock_responses = {
            "greeting": "I'm a helpful voice assistant. How can I help you today?",
            "how are you": "I'm doing well, thank you for asking! How can I assist you?",
            "ready": "Yes, I'm ready to help! What would you like to know?",
            "default": "That's an interesting question. Based on our data, I can help you with customer, ticket, and analytics information."
        }
    
    def query(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Query mock LLM service (instant response, no cost)."""
        # Simple keyword matching for mock responses
        prompt_lower = prompt.lower()
        
        response = self.mock_responses["default"]
        for key, value in self.mock_responses.items():
            if key in prompt_lower:
                response = value
                break
        
        # Estimate tokens (mock)
        mock_input_tokens = len(prompt.split()) * 1.3
        mock_output_tokens = len(response.split()) * 1.3
        
        result = {
            "status": "success",
            "response": response,
            "model": self.model,
            "tokens": {
                "input": int(mock_input_tokens),
                "output": int(mock_output_tokens),
                "total": int(mock_input_tokens + mock_output_tokens)
            },
            "costs": {
                "input_cost": 0.0,
                "output_cost": 0.0,
                "total_cost": 0.0
            }
        }
        
        self.call_history.append(result)
        logger.debug(f"Mock LLM query: Returning canned response")
        return result
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics."""
        return {
            "total_calls": len(self.call_history),
            "model": self.model,
            "total_cost": 0.0,
            "currency": "USD",
            "calls": self.call_history
        }


# Create singleton instance
def get_openai_service():
    """Get LLM service instance (Gemini or mock based on settings)."""
    try:
        if settings.GEMINI_API_KEY:
            logger.info("Using Gemini LLM service")
            return GeminiService()
        else:
            logger.warning("No GEMINI_API_KEY set, using Mock LLM service")
            return MockLLMService()
    except Exception as e:
        logger.error(f"Failed to initialize LLM service: {e}")
        logger.warning("Falling back to Mock LLM service")
        return MockLLMService()
