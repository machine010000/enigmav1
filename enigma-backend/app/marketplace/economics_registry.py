"""
Economics Engine Registry.

Manages economics engines for different marketplaces.
"""
from typing import Dict, Optional

from .contracts import MarketplacePlatform
from .economics import EconomicsEngine
from .fiverr_economics import FiverrEconomicsEngine
from .freelancer_economics import FreelancerEconomicsEngine
from .khamsat_economics import KhamsatEconomicsEngine
from .mostaql_economics import MostaqlEconomicsEngine
from .upwork_economics import UpworkEconomicsEngine


class EconomicsRegistry:
    """
    Registry for marketplace economics engines.

    Manages the available economics engines and provides lookup by platform.
    """

    def __init__(self) -> None:
        self._engines: Dict[MarketplacePlatform, EconomicsEngine] = {}
        self._register_default_engines()

    def _register_default_engines(self) -> None:
        """Register default economics engines for all platforms."""
        self.register(UpworkEconomicsEngine())
        self.register(FreelancerEconomicsEngine())
        self.register(MostaqlEconomicsEngine())
        self.register(FiverrEconomicsEngine())
        self.register(KhamsatEconomicsEngine())

    def register(self, engine: EconomicsEngine) -> None:
        """Register an economics engine."""
        self._engines[engine.platform] = engine

    def get(self, platform: MarketplacePlatform) -> Optional[EconomicsEngine]:
        """Get an economics engine by platform."""
        return self._engines.get(platform)

    def list_platforms(self) -> list[MarketplacePlatform]:
        """List all registered platforms."""
        return list(self._engines.keys())


# Global economics registry
economics_registry = EconomicsRegistry()
