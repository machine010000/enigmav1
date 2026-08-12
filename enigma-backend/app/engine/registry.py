"""
Worker Registry — auto-discovers and registers all Workers with the Engine.

Workers live in ``app/workers/`` and expose a module-level singleton instance.
This module imports every worker module and calls ``engine.register()``.
"""
from __future__ import annotations

from typing import List

from app.engine.engine import engine
from app.engine.contracts import Worker
from app.engine.capabilities import capability_registry

from app.workers.product_verification import product_verification_worker
from app.workers.market_analysis import market_analysis_worker


def register_all() -> List[str]:
    """Register all known workers and return the list of names."""
    workers: List[Worker] = [
        product_verification_worker,
        market_analysis_worker,
    ]
    
    # Register workers with the Engine
    engine.register_many(workers)
    
    # Auto-register worker capabilities with the CapabilityRegistry
    for worker in workers:
        if hasattr(worker, 'capabilities') and worker.capabilities:
            capability_registry.register_worker_from_contract(
                worker_name=worker.name,
                capabilities=worker.capabilities,
                description=worker.description,
            )
    
    return [w.name for w in workers]


def get_registered() -> List[str]:
    return engine.registered_names
