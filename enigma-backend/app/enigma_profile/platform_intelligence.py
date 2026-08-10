"""
Platform Intelligence

Platform readiness and intelligence for marketplace platforms.
"""

from typing import Optional, Dict, List
from datetime import datetime

from app.enigma_profile.contracts import (
    PlatformReadiness,
)
from app.enigma_profile.repositories import PlatformReadinessRepository
from app.marketplace.contracts import MarketplacePlatform
from app.marketplace.account_state import MarketplaceAccountState


class PlatformIntelligence:
    """
    Intelligence for marketplace platform readiness.
    
    Tracks platform-specific readiness, blockers, and recommendations.
    """
    
    def __init__(self, platform_repo: Optional[PlatformReadinessRepository] = None):
        """Initialize platform intelligence.
        
        Args:
            platform_repo: Platform readiness repository
        """
        self._platform_readiness: Dict[MarketplacePlatform, PlatformReadiness] = {}
        self._platform_repo = platform_repo
    
    async def register_platform_readiness(self, readiness: PlatformReadiness) -> None:
        """
        Register platform readiness.
        
        Args:
            readiness: Platform readiness data
        """
        self._platform_readiness[readiness.platform] = readiness
        if self._platform_repo:
            await self._platform_repo.save_readiness("enigma_profile", readiness)
    
    def get_platform_readiness(self, platform: MarketplacePlatform) -> Optional[PlatformReadiness]:
        """
        Get platform readiness.
        
        Args:
            platform: Marketplace platform
            
        Returns:
            PlatformReadiness or None
        """
        return self._platform_readiness.get(platform)
    
    async def update_readiness(
        self,
        platform: MarketplacePlatform,
        knowledge_score: Optional[float] = None,
        evidence_score: Optional[float] = None,
        portfolio_score: Optional[float] = None,
        execution_score: Optional[float] = None,
        win_probability: Optional[float] = None,
        economics_score: Optional[float] = None,
    ) -> None:
        """
        Update platform readiness scores.
        
        Args:
            platform: Marketplace platform
            knowledge_score: Knowledge score (0.0 to 1.0)
            evidence_score: Evidence score (0.0 to 1.0)
            portfolio_score: Portfolio score (0.0 to 1.0)
            execution_score: Execution score (0.0 to 1.0)
            win_probability: Win probability (0.0 to 1.0)
            economics_score: Economics score (0.0 to 1.0)
        """
        if platform not in self._platform_readiness:
            return
        
        readiness = self._platform_readiness[platform]
        
        if knowledge_score is not None:
            readiness.knowledge_score = knowledge_score
        if evidence_score is not None:
            readiness.evidence_score = evidence_score
        if portfolio_score is not None:
            readiness.portfolio_score = portfolio_score
        if execution_score is not None:
            readiness.execution_score = execution_score
        if win_probability is not None:
            readiness.win_probability = win_probability
        if economics_score is not None:
            readiness.economics_score = economics_score
        
        # Recalculate overall readiness
        readiness.overall_readiness = self._calculate_overall_readiness(readiness)
        readiness.last_updated = datetime.utcnow().isoformat()
        
        if self._platform_repo:
            await self._platform_repo.save_readiness("enigma_profile", readiness)
    
    def _calculate_overall_readiness(self, readiness: PlatformReadiness) -> float:
        """
        Calculate overall platform readiness.
        
        Args:
            readiness: Platform readiness data
            
        Returns:
            Overall readiness score (0.0 to 1.0)
        """
        weights = {
            "knowledge": 0.25,
            "evidence": 0.25,
            "portfolio": 0.15,
            "execution": 0.15,
            "economics": 0.10,
            "win_probability": 0.10,
        }
        
        overall = (
            readiness.knowledge_score * weights["knowledge"] +
            readiness.evidence_score * weights["evidence"] +
            readiness.portfolio_score * weights["portfolio"] +
            readiness.execution_score * weights["execution"] +
            readiness.economics_score * weights["economics"] +
            readiness.win_probability * weights["win_probability"]
        )
        
        return min(1.0, max(0.0, overall))
    
    def add_blocker(self, platform: MarketplacePlatform, blocker: str) -> None:
        """
        Add a blocker for a platform.
        
        Args:
            platform: Marketplace platform
            blocker: Blocker description
        """
        if platform in self._platform_readiness:
            readiness = self._platform_readiness[platform]
            if blocker not in readiness.blockers:
                readiness.blockers.append(blocker)
    
    def remove_blocker(self, platform: MarketplacePlatform, blocker: str) -> None:
        """
        Remove a blocker for a platform.
        
        Args:
            platform: Marketplace platform
            blocker: Blocker description
        """
        if platform in self._platform_readiness:
            readiness = self._platform_readiness[platform]
            if blocker in readiness.blockers:
                readiness.blockers.remove(blocker)
    
    def add_recommendation(self, platform: MarketplacePlatform, recommendation: str) -> None:
        """
        Add a recommendation for a platform.
        
        Args:
            platform: Marketplace platform
            recommendation: Recommendation description
        """
        if platform in self._platform_readiness:
            readiness = self._platform_readiness[platform]
            if recommendation not in readiness.recommendations:
                readiness.recommendations.append(recommendation)
    
    async def analyze_from_account_state(
        self,
        platform: MarketplacePlatform,
        account_state: MarketplaceAccountState,
    ) -> PlatformReadiness:
        """
        Analyze platform readiness from account state.
        
        Args:
            platform: Marketplace platform
            account_state: Account state
            
        Returns:
            PlatformReadiness
        """
        # Collect blockers first
        blockers = []
        economics_score = 0.5  # Default
        
        if account_state.account_status.value in ["suspended", "restricted"]:
            blockers.append("Account suspended or restricted")
            economics_score = 0.0
        elif not account_state.is_account_active():
            blockers.append(f"Account status: {account_state.account_status.value}")
            economics_score = 0.2
        
        # Check credits/balance
        if account_state.has_known_credits():
            if account_state.credits.available and account_state.credits.available < 5:
                blockers.append("Low credits available")
                economics_score = min(economics_score, 0.3)
        
        if account_state.has_known_wallet():
            if account_state.wallet.available and account_state.wallet.available < 10:
                blockers.append("Low wallet balance")
                economics_score = min(economics_score, 0.3)
        
        # Check freshness
        if not account_state.is_data_fresh():
            blockers.append("Account data is stale")
            economics_score = min(economics_score, 0.4)
        
        # Update or create readiness
        if platform in self._platform_readiness:
            # Add new blockers to existing
            for blocker in blockers:
                self.add_blocker(platform, blocker)
            await self.update_readiness(platform, economics_score=economics_score)
        else:
            readiness = PlatformReadiness(
                platform=platform,
                overall_readiness=economics_score,
                knowledge_score=0.0,
                evidence_score=0.0,
                portfolio_score=0.0,
                execution_score=0.0,
                win_probability=0.0,
                economics_score=economics_score,
                blockers=blockers,
                last_updated=datetime.utcnow().isoformat(),
            )
            await self.register_platform_readiness(readiness)
        
        return self.get_platform_readiness(platform)
    
    async def get_all_readiness(self) -> Dict[MarketplacePlatform, PlatformReadiness]:
        """Get all platform readiness."""
        if self._platform_repo:
            return await self._platform_repo.get_all_readiness("enigma_profile")
        return self._platform_readiness
    
    def get_all_platforms(self) -> List[MarketplacePlatform]:
        """Get all tracked platforms."""
        return list(self._platform_readiness.keys())
    
    def get_platforms_by_readiness(self, min_readiness: float = 0.5) -> List[MarketplacePlatform]:
        """
        Get platforms with readiness above threshold.
        
        Args:
            min_readiness: Minimum readiness threshold
            
        Returns:
            List of platform names
        """
        return [
            platform
            for platform, readiness in self._platform_readiness.items()
            if readiness.overall_readiness >= min_readiness
        ]
    
    def generate_platform_summary(self, platform: MarketplacePlatform) -> Optional[str]:
        """
        Generate platform readiness summary.
        
        Args:
            platform: Marketplace platform
            
        Returns:
            Summary string or None
        """
        readiness = self.get_platform_readiness(platform)
        if not readiness:
            return None
        
        lines = [
            f"{platform.value.upper()}",
            f"Readiness: {readiness.overall_readiness:.0%}",
            f"Knowledge: {'█' * int(readiness.knowledge_score * 10)}{'░' * (10 - int(readiness.knowledge_score * 10))} {readiness.knowledge_score:.0%}",
            f"Evidence: {'█' * int(readiness.evidence_score * 10)}{'░' * (10 - int(readiness.evidence_score * 10))} {readiness.evidence_score:.0%}",
            f"Portfolio: {'█' * int(readiness.portfolio_score * 10)}{'░' * (10 - int(readiness.portfolio_score * 10))} {readiness.portfolio_score:.0%}",
            f"Execution: {'█' * int(readiness.execution_score * 10)}{'░' * (10 - int(readiness.execution_score * 10))} {readiness.execution_score:.0%}",
        ]
        
        if readiness.blockers:
            lines.append("\nCurrent Problems:")
            for blocker in readiness.blockers:
                lines.append(f"- {blocker}")
        
        if readiness.recommendations:
            lines.append("\nRecommended Development:")
            for i, rec in enumerate(readiness.recommendations, 1):
                lines.append(f"{i}. {rec}")
        
        return "\n".join(lines)
