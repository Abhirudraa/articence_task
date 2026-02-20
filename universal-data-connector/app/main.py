
# import logging
# from fastapi import FastAPI
# from fastapi.staticfiles import StaticFiles
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.openapi.utils import get_openapi
# from pathlib import Path
# from app.config import settings
# from app.routers import health, data
# from app.routers import bonus
# from app.middleware.rate_limit import RateLimitMiddleware
# from app.middleware.auth import AuthenticationMiddleware
# from app.utils.logging import configure_logging

# # Configure logging
# configure_logging()
# logger = logging.getLogger(__name__)

# # Create FastAPI application
# app = FastAPI(
#     title=settings.APP_NAME,
#     version=settings.APP_VERSION,
#     description="Universal Data Connector - LLM Function Calling Interface",
#     docs_url="/docs",
#     redoc_url="/redoc",
#     openapi_url="/openapi.json"
# )

# # Add CORS middleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Add rate limiting middleware
# app.add_middleware(
#     RateLimitMiddleware,
#     requests=settings.RATE_LIMIT_REQUESTS,
#     period_seconds=settings.RATE_LIMIT_PERIOD_SECONDS
# )

# # Add authentication middleware (after rate limiting)
# app.add_middleware(AuthenticationMiddleware)

# # Include routers
# app.include_router(health.router)
# app.include_router(data.router)
# app.include_router(bonus.router)

# # Mount static files (web UI)
# static_dir = Path(__file__).parent.parent / "static"
# if static_dir.exists():
#     app.mount("/ui", StaticFiles(directory=str(static_dir)), name="ui")
#     logger.info(f"Static files mounted from {static_dir}")

# # Custom OpenAPI schema for function calling
# def custom_openapi():
#     """
#     Generate custom OpenAPI schema optimized for LLM function calling.
#     """
#     if app.openapi_schema:
#         return app.openapi_schema
    
#     openapi_schema = get_openapi(
#         title=settings.APP_NAME,
#         version=settings.APP_VERSION,
#         description="""
#         A production-quality Universal Data Connector that provides a unified interface
#         for LLMs to access different data sources through function calling.
        
#         Optimized for voice conversations with intelligent filtering, business rules,
#         and voice-specific optimizations.
        
#         **Bonus Features:**
#         - Redis caching for frequently accessed data
#         - Rate limiting per data source
#         - Streaming responses for large datasets
#         - Authentication & API key management
#         - Webhook support for real-time updates
#         - Data export (CSV, Excel, JSON)
#         """,
#         routes=app.routes,
#     )
    
#     # Add function calling examples
#     openapi_schema["info"]["x-examples"] = {
#         "get_active_customers": {
#             "arguments": {"status": "active", "limit": 10},
#             "description": "Get list of active customers"
#         },
#         "get_open_tickets": {
#             "arguments": {"status": "open", "limit": 10},
#             "description": "Get open support tickets"
#         },
#         "get_analytics": {
#             "arguments": {"metric": "daily_active_users", "limit": 10},
#             "description": "Get analytics metrics"
#         }
#     }
    
#     app.openapi_schema = openapi_schema
#     return app.openapi_schema


# app.openapi = custom_openapi


# # Root endpoint
# @app.get("/", tags=["root"])
# def root():
#     """
#     Root endpoint providing API information.
#     """
#     logger.info("Root endpoint accessed")
#     return {
#         "app_name": settings.APP_NAME,
#         "version": settings.APP_VERSION,
#         "description": "Universal Data Connector for LLM Function Calling",
#         "documentation": "/docs",
#         "redoc": "/redoc",
#         "openapi": "/openapi.json",
#         "features": {
#             "caching": settings.CACHE_ENABLED,
#             "rate_limiting": settings.RATE_LIMIT_ENABLED,
#             "authentication": settings.AUTH_ENABLED,
#             "webhooks": settings.WEBHOOK_ENABLED,
#             "export": settings.EXPORT_ENABLED
#         }
#     }


# # Startup event
# @app.on_event("startup")
# async def startup_event():
#     """Run on application startup."""
#     logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
#     logger.info(f"Debug mode: {settings.DEBUG}")
#     logger.info(f"Max results per query: {settings.MAX_RESULTS}")
    
#     # Initialize bonus features
#     if settings.CACHE_ENABLED:
#         from app.services.cache_service import cache_service
#         logger.info(f"Cache service initialized: {cache_service.is_healthy()}")
    
#     if settings.AUTH_ENABLED:
#         from app.services.auth_service import auth_service
#         logger.info(f"Authentication enabled with {len(auth_service.api_keys)} API keys")
    
#     if settings.WEBHOOK_ENABLED:
#         from app.services.webhook_service import webhook_service
#         logger.info(f"Webhook service initialized with {len(webhook_service.list_webhooks())} webhooks")
    
#     if settings.EXPORT_ENABLED:
#         logger.info("Data export service initialized")
    
#     logger.info("Rate limiting: ENABLED" if settings.RATE_LIMIT_ENABLED else "Rate limiting: DISABLED")


# # Shutdown event
# @app.on_event("shutdown")
# async def shutdown_event():
#     """Run on application shutdown."""
#     logger.info(f"Shutting down {settings.APP_NAME}")


# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(
#         "app.main:app",
#         host=settings.HOST,
#         port=settings.PORT,
#         reload=settings.DEBUG,
#         log_level="info"
#     )

"""
Main application entry point for Universal Data Connector.
"""
"""
Main application entry point for Universal Data Connector.
"""

import logging
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from pathlib import Path

# Import settings directly - this should now work
from app.config import settings

# Import routers
from app.routers import health, data, bonus

# Import middleware
from app.middleware.auth import AuthenticationMiddleware
from app.middleware.rate_limit import RateLimitMiddleware

# Import logging config
from app.utils.logging import configure_logging

# Configure logging
configure_logging()
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Universal Data Connector - LLM Function Calling Interface",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiting middleware
app.add_middleware(
    RateLimitMiddleware,
    requests=settings.RATE_LIMIT_REQUESTS,
    period_seconds=settings.RATE_LIMIT_PERIOD_SECONDS
)

# Add authentication middleware (after rate limiting)
app.add_middleware(AuthenticationMiddleware)

# Include routers - note: bonus router already has /api prefix in its definition
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(data.router, prefix="/api", tags=["data"])
app.include_router(bonus.router, tags=["bonus"])  # No prefix here since it's in bonus.py

# Mount static files (web UI)
# Try multiple possible locations for static files
possible_static_dirs = [
    Path(__file__).parent.parent / "static",  # ../static
    Path(__file__).parent.parent / "ui",       # ../ui
    Path(__file__).parent / "static",          # ./static
]

static_mounted = False
for static_dir in possible_static_dirs:
    if static_dir.exists():
        try:
            app.mount("/ui", StaticFiles(directory=str(static_dir), html=True), name="ui")
            logger.info(f"UI static files mounted from {static_dir}")
            static_mounted = True
            break
        except Exception as e:
            logger.warning(f"Failed to mount {static_dir}: {e}")

if not static_mounted:
    logger.warning("No UI static files directory found")

# Custom OpenAPI schema for function calling
def custom_openapi():
    """
    Generate custom OpenAPI schema optimized for LLM function calling.
    """
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="""
        A production-quality Universal Data Connector that provides a unified interface
        for LLMs to access different data sources through function calling.
        
        Optimized for voice conversations with intelligent filtering, business rules,
        and voice-specific optimizations.
        
        **Bonus Features:**
        - Redis caching for frequently accessed data
        - Rate limiting per data source
        - Streaming responses for large datasets
        - Authentication & API key management
        - Webhook support for real-time updates
        - Data export (CSV, Excel, JSON)
        """,
        routes=app.routes,
    )
    
    # Add function calling examples
    openapi_schema["info"]["x-examples"] = {
        "get_active_customers": {
            "arguments": {"status": "active", "limit": 10},
            "description": "Get list of active customers"
        },
        "get_open_tickets": {
            "arguments": {"status": "open", "limit": 10},
            "description": "Get open support tickets"
        },
        "get_analytics": {
            "arguments": {"metric": "daily_active_users", "limit": 10},
            "description": "Get analytics metrics"
        }
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """
    Root endpoint providing API information.
    """
    logger.info("Root endpoint accessed")
    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": "Universal Data Connector for LLM Function Calling",
        "documentation": "/docs",
        "redoc": "/redoc",
        "openapi": "/openapi.json",
        "ui": "/ui/index.html" if static_mounted else None,
        "features": {
            "caching": settings.CACHE_ENABLED,
            "rate_limiting": settings.RATE_LIMIT_ENABLED,
            "authentication": settings.AUTH_ENABLED,
            "webhooks": settings.WEBHOOK_ENABLED,
            "export": settings.EXPORT_ENABLED
        }
    }

# Health check endpoint (without /api prefix - public)
@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION
    }

# Also add health check with /api prefix for consistency (optional)
@app.get("/api/health", tags=["health"])
async def api_health_check():
    """Health check endpoint with API prefix."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info(f"Max results per query: {settings.MAX_RESULTS}")
    
    # Initialize bonus features
    if settings.CACHE_ENABLED:
        try:
            from app.services.cache_service import cache_service
            logger.info(f"Cache service initialized")
        except ImportError as e:
            logger.warning(f"Cache service not available: {e}")
    
    if settings.AUTH_ENABLED:
        try:
            from app.services.auth_service import auth_service
            logger.info("Authentication enabled")
        except ImportError as e:
            logger.warning(f"Auth service not available: {e}")
    
    if settings.WEBHOOK_ENABLED:
        try:
            from app.services.webhook_service import webhook_service
            logger.info("Webhook service initialized")
        except ImportError as e:
            logger.warning(f"Webhook service not available: {e}")
    
    if settings.EXPORT_ENABLED:
        logger.info("Data export service enabled")
    
    logger.info(f"Rate limiting: {'ENABLED' if settings.RATE_LIMIT_ENABLED else 'DISABLED'}")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    logger.info(f"Shutting down {settings.APP_NAME}")

# For running directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )