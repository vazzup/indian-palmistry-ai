"""
FastAPI main application factory and startup configuration.

This module creates and configures the FastAPI application with all necessary
middleware, routers, and startup hooks. It serves as the entry point for the
Indian palmistry AI backend application.

Features:
- CORS middleware configuration
- Database initialization
- Structured logging setup
- Health check endpoints
- API versioning with /api/v1 prefix
- Graceful startup and shutdown

Usage:
    uvicorn app.main:app --host 0.0.0.0 --port 8000
"""

import asyncio
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import init_sqlite_pragmas, check_database_connection
from app.core.logging import setup_logging, get_logger, set_correlation_id, log_request, log_response
from app.core.cache import cache_service


# Setup logging before creating the app
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager for startup and shutdown tasks.
    
    Args:
        app: FastAPI application instance
    """
    # Startup tasks
    logger.info("Starting Indian Palmistry AI Backend", extra={"version": "0.1.0"})
    
    # Initialize cache service
    try:
        await cache_service.connect()
        logger.info("Redis cache service connected")
    except Exception as e:
        logger.warning(f"Failed to connect to Redis cache: {e}")
        # Continue without cache - the service will handle fallbacks
    
    # Initialize database
    try:
        if settings.is_sqlite:
            await init_sqlite_pragmas()
            logger.info("SQLite pragmas initialized")
        
        # Check database connection
        if await check_database_connection():
            logger.info("Database connection established", extra={"database_type": "sqlite" if settings.is_sqlite else "postgresql"})
        else:
            logger.error("Failed to connect to database")
            raise RuntimeError("Database connection failed")
    
    except Exception as e:
        logger.error("Database initialization failed", error=str(e))
        raise
    
    logger.info("Application startup completed")
    
    yield
    
    # Shutdown tasks
    logger.info("Application shutdown initiated")
    
    # Close cache connections
    try:
        await cache_service.close()
        logger.info("Cache service connections closed")
    except Exception as e:
        logger.warning(f"Error closing cache connections: {e}")
    
    logger.info("Application shutdown completed")


# Create FastAPI application
app = FastAPI(
    title="Indian Palmistry AI Backend",
    description="AI-powered palmistry reading application with OpenAI integration",
    version="0.1.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan,
)

# Add rate limiting and security middleware (disabled for development)
# from app.middleware.rate_limiting import RateLimitMiddleware
# app.add_middleware(RateLimitMiddleware, enable_security_monitoring=True)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Log HTTP requests and responses with correlation ID tracking."""
    # Set correlation ID
    correlation_id = set_correlation_id()
    
    # Log request
    start_time = time.time()
    log_request(logger, request.method, str(request.url.path), correlation_id=correlation_id)
    
    try:
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000
        
        # Log response
        log_response(
            logger, 
            request.method, 
            str(request.url.path), 
            response.status_code,
            duration_ms,
            correlation_id=correlation_id
        )
        
        # Add correlation ID to response headers
        response.headers["X-Correlation-ID"] = correlation_id
        
        return response
    
    except Exception as e:
        # Log error
        duration_ms = (time.time() - start_time) * 1000
        logger.error(
            "Request processing failed",
            method=request.method,
            path=str(request.url.path),
            duration_ms=duration_ms,
            error=str(e),
            correlation_id=correlation_id,
            exc_info=True
        )
        
        # Return error response
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "correlation_id": correlation_id}
        )


@app.get("/healthz")
async def health_check():
    """
    Health check endpoint for container orchestration.
    
    Returns:
        dict: Health status and application information
    """
    # Check database connection
    db_healthy = await check_database_connection()
    
    # Check cache connection
    cache_healthy = True
    try:
        cache_health = await cache_service.health_check()
        cache_healthy = cache_health.get("status") == "healthy"
    except Exception as e:
        logger.warning(f"Cache health check failed: {e}")
        cache_healthy = False
    
    # Overall health
    overall_healthy = db_healthy and cache_healthy
    
    health_status = {
        "status": "healthy" if overall_healthy else "unhealthy",
        "version": "0.1.0",
        "timestamp": int(time.time()),
        "database": "connected" if db_healthy else "disconnected",
        "cache": "connected" if cache_healthy else "disconnected",
        "environment": settings.environment,
    }
    
    status_code = 200 if overall_healthy else 503
    return JSONResponse(content=health_status, status_code=status_code)


@app.get("/")
async def root():
    """
    Root endpoint with basic application information.
    
    Returns:
        dict: Application welcome message and info
    """
    return {
        "message": "Welcome to Indian Palmistry AI Backend",
        "version": "0.1.0",
        "docs_url": "/docs" if settings.debug else None,
        "health_check": "/healthz",
    }


# API v1 routers
from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.readings import router as readings_router
from app.api.v1.analyses import router as analyses_router
from app.api.v1.conversations import router as conversations_router
from app.api.v1.enhanced_endpoints import router as enhanced_router

api_v1_router = APIRouter(prefix="/api/v1", tags=["v1"])

@api_v1_router.get("/health")
async def api_health():
    """API v1 health check endpoint."""
    return {
        "status": "healthy", 
        "api_version": "v1",
        "timestamp": int(time.time())
    }

# Include sub-routers
api_v1_router.include_router(auth_router)
api_v1_router.include_router(readings_router)
api_v1_router.include_router(analyses_router)  # Keep for backward compatibility
api_v1_router.include_router(conversations_router)
api_v1_router.include_router(enhanced_router)

app.include_router(api_v1_router)


# Exception handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Handle 404 errors with structured response."""
    return JSONResponse(
        status_code=404,
        content={
            "detail": "Not found",
            "path": str(request.url.path),
            "method": request.method,
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    """Handle 500 errors with structured response."""
    correlation_id = set_correlation_id()
    logger.error(
        "Internal server error", 
        path=str(request.url.path),
        method=request.method,
        error=str(exc),
        correlation_id=correlation_id,
        exc_info=True
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "correlation_id": correlation_id,
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_config=None,  # Use our custom logging
    )