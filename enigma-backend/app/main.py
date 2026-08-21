from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.database import init_db
from app.core.config import CORS_ALLOW_HEADERS, CORS_ALLOW_METHODS, settings
from app.core.health import perform_startup_health_check, get_health_status

@asynccontextmanager
async def lifespan(app: FastAPI):
    import os
    import sys
    print("ENIGMA is initializing...")
    print(f"Python version: {sys.version}")
    print(f"PORT environment variable: {os.getenv('PORT', 'NOT SET')}")
    print(f"API_PORT from settings: {settings.API_PORT}")
    print(f"API_HOST from settings: {settings.API_HOST}")
    print(f"ENVIRONMENT: {settings.ENVIRONMENT}")

    # Perform startup health check
    print("Running startup health checks...")
    health_result = await perform_startup_health_check()

    print(f"Health check status: {health_result['status']}")
    if health_result["status"] == "unhealthy":
        print("❌ Startup health check failed:")
        for error in health_result["errors"]:
            print(f"  - {error}")
        raise RuntimeError("Startup health check failed. See logs for details.")

    print("✅ Startup health check passed")
    if health_result["warnings"]:
        print("⚠️  Warnings:")
        for warning in health_result["warnings"]:
            print(f"  - {warning}")

    await init_db()
    print("Database connected and tables created")

    # Import and register routers after database is initialized
    try:
        from app.routers import auth, products, master_brain, engine, dashboard, events, freelancing, freelancer_chat, execution, enigma_profile as enigma_profile_router
        from app.engine.registry import register_all as register_workers
        from app.engine.events import event_bus

        app.include_router(auth.router)
        app.include_router(products.router)
        app.include_router(master_brain.router)
        app.include_router(engine.router)
        app.include_router(dashboard.router)
        app.include_router(events.router)
        app.include_router(freelancing.router)
        app.include_router(freelancer_chat.router)
        app.include_router(execution.router)
        app.include_router(enigma_profile_router.router)  # TASK-017

        # Register all Workers with the Execution Engine (TASK-001)
        worker_names = register_workers()
        print(f"Registered {len(worker_names)} workers: {worker_names}")
        print(f"EventBus ready — {event_bus.connected_clients} live WebSocket clients")
    except Exception as e:
        print(f"⚠️  Warning: Failed to initialize some components: {e}")
        import traceback
        traceback.print_exc()
        print("Application continuing with limited functionality")

    print(f"Environment: {settings.ENVIRONMENT}")
    print("✅ Application startup complete - ready to serve requests")
    print(f"FastAPI app routes: {[route.path for route in app.routes]}")
    print(f"Listening on: 0.0.0.0:{os.getenv('PORT', '8000')}")
    yield
    print("ENIGMA shutting down...")

app = FastAPI(
    title="ENIGMA - AI Business Brain",
    description="Your intelligent partner for business growth",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration from environment
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=CORS_ALLOW_METHODS,
    allow_headers=CORS_ALLOW_HEADERS,
)

# Request logging middleware for diagnostics
@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(f"REQUEST {request.method} {request.url.path}")
    response = await call_next(request)
    print(f"RESPONSE {response.status_code} {request.method} {request.url.path}")
    return response

@app.get("/")
async def root():
    return {
        "name": "ENIGMA - AI Business Brain",
        "version": "1.0.0",
        "status": "running",
        "environment": settings.ENVIRONMENT
    }

@app.get("/health")
async def health_check():
    """Basic health check endpoint with zero dependencies."""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT
    }

@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with configuration validation."""
    return await perform_startup_health_check()
