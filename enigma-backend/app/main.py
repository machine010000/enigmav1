from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.database import init_db
from app.routers import auth, products, master_brain, engine, dashboard, events, freelancing, execution
from app.engine.registry import register_all as register_workers
from app.engine.events import event_bus

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("ENIGMA is initializing...")
    await init_db()
    print("Database connected and tables created")
    # Register all Workers with the Execution Engine (TASK-001)
    worker_names = register_workers()
    print(f"Registered {len(worker_names)} workers: {worker_names}")
    print(f"EventBus ready — {event_bus.connected_clients} live WebSocket clients")
    yield
    print("ENIGMA shutting down...")

app = FastAPI(title="ENIGMA - AI Business Brain", description="Your intelligent partner for business growth", version="1.0.0", lifespan=lifespan)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

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
    return {"name": "ENIGMA - AI Business Brain", "version": "1.0.0", "status": "running", "ai_provider": "NVIDIA NIM (Free Tier)", "database": "Neon PostgreSQL", "workers": engine.registered_names}

@app.get("/health")
async def health_check():
    from app.engine.engine import engine
    from app.engine.events import event_bus
    return {"status": "healthy", "workers": len(engine.registered_names), "ws_clients": event_bus.connected_clients}
