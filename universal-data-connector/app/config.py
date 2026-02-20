"""
Configuration settings for the Universal Data Connector.
"""

import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application Configuration
    APP_NAME: str = Field(default="Universal Data Connector", env="APP_NAME")
    APP_VERSION: str = Field(default="1.0.0", env="APP_VERSION")
    DEBUG: bool = Field(default=False, env="DEBUG")
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    
    # API Configuration
    MAX_RESULTS: int = Field(default=10, env="MAX_RESULTS")
    DEFAULT_LIMIT: int = Field(default=10, env="DEFAULT_LIMIT")
    
    # Data Configuration
    DATA_DIR: str = Field(default="data", env="DATA_DIR")
    DATA_FRESHNESS_HOURS: int = Field(default=2, env="DATA_FRESHNESS_HOURS")
    
    # Voice Optimization Settings
    ENABLE_VOICE_OPTIMIZATION: bool = Field(default=True, env="ENABLE_VOICE_OPTIMIZATION")
    VOICE_SUMMARY_THRESHOLD: int = Field(default=10, env="VOICE_SUMMARY_THRESHOLD")
    
    # Google Gemini Configuration
    GEMINI_API_KEY: Optional[str] = Field(default=None, env="GEMINI_API_KEY")
    GEMINI_MODEL: str = Field(default="gemini-pro", env="GEMINI_MODEL")
    GEMINI_MAX_TOKENS: int = Field(default=1000, env="GEMINI_MAX_TOKENS")
    GEMINI_TEMPERATURE: float = Field(default=0.7, env="GEMINI_TEMPERATURE")
    ENABLE_LLM: bool = Field(default=True, env="ENABLE_LLM")
    TRACK_TOKEN_USAGE: bool = Field(default=True, env="TRACK_TOKEN_USAGE")
    
    # Authentication Settings
    AUTH_ENABLED: bool = Field(default=True, env="AUTH_ENABLED")
    API_KEY_SECRET: str = Field(default="your-secret-key-change-in-production", env="API_KEY_SECRET")
    API_KEY_EXPIRY_DAYS: int = Field(default=365, env="API_KEY_EXPIRY_DAYS")
    API_KEYS_FILE: str = Field(default="api_keys.json", env="API_KEYS_FILE")
    
    # Rate Limiting Settings (unified naming)
    RATE_LIMIT_ENABLED: bool = Field(default=False, env="RATE_LIMIT_ENABLED")
    RATE_LIMITING_ENABLED: bool = Field(default=False, env="RATE_LIMITING_ENABLED")  # Alias
    RATE_LIMIT_REQUESTS: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    DEFAULT_RATE_LIMIT: int = Field(default=100, env="DEFAULT_RATE_LIMIT")  # Alias
    RATE_LIMIT_PERIOD_SECONDS: int = Field(default=60, env="RATE_LIMIT_PERIOD_SECONDS")
    RATE_LIMIT_WINDOW: int = Field(default=60, env="RATE_LIMIT_WINDOW")  # Alias
    
    # Cache/Redis Settings
    CACHE_ENABLED: bool = Field(default=False, env="CACHE_ENABLED")
    REDIS_ENABLED: bool = Field(default=False, env="REDIS_ENABLED")  # Alias
    REDIS_URL: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    REDIS_TTL: int = Field(default=3600, env="REDIS_TTL")
    CACHE_TTL_SECONDS: int = Field(default=3600, env="CACHE_TTL_SECONDS")  # Alias
    
    # Webhook Settings
    WEBHOOK_ENABLED: bool = Field(default=False, env="WEBHOOK_ENABLED")
    WEBHOOKS_ENABLED: bool = Field(default=False, env="WEBHOOKS_ENABLED")  # Alias
    WEBHOOK_TIMEOUT: int = Field(default=10, env="WEBHOOK_TIMEOUT")
    WEBHOOK_TIMEOUT_SECONDS: int = Field(default=10, env="WEBHOOK_TIMEOUT_SECONDS")  # Alias
    WEBHOOK_MAX_RETRIES: int = Field(default=3, env="WEBHOOK_MAX_RETRIES")
    WEBHOOKS_FILE: str = Field(default="webhooks.json", env="WEBHOOKS_FILE")
    
    # Export Settings
    EXPORT_ENABLED: bool = Field(default=True, env="EXPORT_ENABLED")
    EXPORT_MAX_RECORDS: int = Field(default=10000, env="EXPORT_MAX_RECORDS")
    
    # Connector Settings
    CRM_CONNECTOR_ENABLED: bool = Field(default=True, env="CRM_CONNECTOR_ENABLED")
    SUPPORT_CONNECTOR_ENABLED: bool = Field(default=True, env="SUPPORT_CONNECTOR_ENABLED")
    ANALYTICS_CONNECTOR_ENABLED: bool = Field(default=True, env="ANALYTICS_CONNECTOR_ENABLED")
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure aliases are set
        self.RATE_LIMITING_ENABLED = self.RATE_LIMIT_ENABLED
        self.DEFAULT_RATE_LIMIT = self.RATE_LIMIT_REQUESTS
        self.RATE_LIMIT_WINDOW = self.RATE_LIMIT_PERIOD_SECONDS
        self.REDIS_ENABLED = self.CACHE_ENABLED
        self.CACHE_TTL_SECONDS = self.REDIS_TTL
        self.WEBHOOKS_ENABLED = self.WEBHOOK_ENABLED
        self.WEBHOOK_TIMEOUT_SECONDS = self.WEBHOOK_TIMEOUT

# Create global settings instance
settings = Settings()

# Export settings for use in other modules
__all__ = ["settings"]