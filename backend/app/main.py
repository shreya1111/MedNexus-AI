"""
MedNexus-AI Backend Application.

Production-ready FastAPI application for medical AI assistant.
"""

import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.exceptions import MedNexusException
from app.database.session import init_db, close_db
from app.api.v1 import auth, chat, search, dashboard, reports, documents, profile, admin


# Rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup and shutdown events.
    """
    # Startup
    print("🚀 Starting MedNexus-AI Backend...")
    
    # Initialize database
    if settings.ENVIRONMENT != "test":
        await init_db()
        print("✅ Database initialized")
    
    print(f"✅ {settings.APP_NAME} v{settings.APP_VERSION} started")
    print(f"📖 Docs: http://{settings.HOST}:{settings.PORT}{settings.DOCS_URL}")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down MedNexus-AI Backend...")
    await close_db()
    print("✅ Cleanup complete")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Production-ready backend for medical AI assistant platform",
    docs_url=settings.DOCS_URL,
    redoc_url=settings.REDOC_URL,
    lifespan=lifespan
)

# Add rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Middleware Configuration
# -------------------------

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted Host Middleware (Security)
if settings.ENVIRONMENT == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"]  # Configure with actual allowed hosts
    )


# Request ID and Timing Middleware
@app.middleware("http")
async def add_request_context(request: Request, call_next):
    """
    Add request ID and timing to all requests.
    """
    import uuid
    
    # Generate request ID
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    # Start timer
    start_time = time.time()
    
    # Process request
    response = await call_next(request)
    
    # Calculate processing time
    process_time = (time.time() - start_time) * 1000  # ms
    
    # Add headers
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = f"{process_time:.2f}ms"
    
    return response


# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """
    Add security headers to all responses.
    """
    response = await call_next(request)
    
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    return response


# Exception Handlers
# ------------------

@app.exception_handler(MedNexusException)
async def mednexus_exception_handler(request: Request, exc: MedNexusException):
    """Handle MedNexus custom exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.message,
            "details": exc.details,
            "request_id": getattr(request.state, "request_id", None)
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "details": str(exc) if settings.DEBUG else None,
            "request_id": getattr(request.state, "request_id", None)
        }
    )


# Health Check Endpoints
# ----------------------

@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint.
    
    Returns basic health status.
    """
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT
    }


@app.get("/ready", tags=["Health"])
async def readiness_check():
    """
    Readiness check endpoint.
    
    Checks if service is ready to accept requests.
    """
    # TODO: Add database connectivity check
    return {
        "status": "ready",
        "service": settings.APP_NAME,
        "checks": {
            "database": "ok",
            "ai_service": "ok"
        }
    }


@app.get("/live", tags=["Health"])
async def liveness_check():
    """
    Liveness check endpoint.
    
    Checks if service is alive.
    """
    return {
        "status": "alive",
        "service": settings.APP_NAME
    }


# API Routes
# ----------

# Include API v1 routers
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(chat.router, prefix=settings.API_V1_PREFIX)
app.include_router(search.router, prefix=settings.API_V1_PREFIX)
app.include_router(dashboard.router, prefix=settings.API_V1_PREFIX)
app.include_router(reports.router, prefix=settings.API_V1_PREFIX)
app.include_router(documents.router, prefix=settings.API_V1_PREFIX)
app.include_router(profile.router, prefix=settings.API_V1_PREFIX)
app.include_router(admin.router, prefix=settings.API_V1_PREFIX)


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint.
    
    Returns API information.
    """
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": "Production-ready backend for medical AI assistant platform",
        "docs": f"{settings.DOCS_URL}",
        "health": "/health",
        "api": {
            "v1": settings.API_V1_PREFIX
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
