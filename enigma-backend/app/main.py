from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.database import init_db
from app.routers import auth, products, master_brain, engine, dashboard, events, freelancing, execution
from app.engine.registry import register_all as register_workers
from app.engine.events import event_bus
from app.core.config import settings
from app.core.health import perform_startup_health_check, get_health_status

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("ENIGMA is initializing...")
    
    # Perform startup health check
    print("Running startup health checks...")
    health_result = await perform_startup_health_check()
    
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
    
    # Register all Workers with the Execution Engine (TASK-001)
    worker_names = register_workers()
    print(f"Registered {len(worker_names)} workers: {worker_names}")
    print(f"EventBus ready — {event_bus.connected_clients} live WebSocket clients")
    print(f"Environment: {settings.ENVIRONMENT}")
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
    allow_origins=settings.cors_origins_list if settings.cors_origins_list else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(products.router)
app.include_router(master_brain.router)
app.include_router(engine.router)
app.include_router(dashboard.router)
app.include_router(events.router)
app.include_router(freelancing.router)
app.include_router(execution.router)

@app.get("/")
async def root():
    from app.engine.engine import engine
    return {
        "name": "ENIGMA - AI Business Brain",
        "version": "1.0.0",
        "status": "running",
        "environment": settings.ENVIRONMENT,
        "ai_provider": "NVIDIA NIM (Free Tier)",
        "database": "Neon PostgreSQL",
        "workers": engine.registered_names
    }

@app.get("/health")
async def health_check():
    """Basic health check endpoint."""
    from app.engine.engine import engine
    from app.engine.events import event_bus
    
    return {
        "status": "healthy",
        "workers": len(engine.registered_names),
        "ws_clients": event_bus.connected_clients,
        "environment": settings.ENVIRONMENT
    }

@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with configuration validation."""
    return await perform_startup_health_check()
