from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.work_market.contracts import EvidenceProvider


class EvidenceAdapter(EvidenceProvider):
    """
    Adapter that bridges Freelancing layer with Evidence systems.
    
    This adapter implements the EvidenceProvider contract using
    the existing Evidence/Memory framework without modifying it.
    """

    def __init__(self, evidence_registry: Optional[Any] = None) -> None:
        self._evidence_registry = evidence_registry

    def get_evidence_for_capability(self, capability_id: str) -> Dict[str, Any]:
        """Get evidence information for a capability."""
        if not self._evidence_registry:
            return {}
        
        try:
            # Try to get evidence from registry
            evidence = self._evidence_registry.get_evidence_for_capability(capability_id)
            if evidence:
                return {
                    "capability_id": capability_id,
                    "evidence_count": len(evidence),
                    "evidence": evidence,
                }
        except Exception:
            pass
        
        return {}

    def get_evidence_coverage(self, capability_id: str) -> float:
        """Get evidence coverage score (0.0 to 1.0)."""
        evidence_info = self.get_evidence_for_capability(capability_id)
        if not evidence_info:
            return 0.0
        
        # Calculate coverage based on evidence count and quality
        evidence_count = evidence_info.get("evidence_count", 0)
        
        # Simple heuristic: more evidence = better coverage
        # Max out at 10 evidence items for full coverage
        coverage = min(evidence_count / 10.0, 1.0)
        
        return coverage

    def get_evidence_quality(self, capability_id: str) -> float:
        """Get evidence quality score (0.0 to 1.0)."""
        evidence_info = self.get_evidence_for_capability(capability_id)
        if not evidence_info:
            return 0.0
        
        # Calculate quality based on evidence attributes
        evidence = evidence_info.get("evidence", [])
        if not evidence:
            return 0.0
        
        # Average quality across all evidence items
        quality_scores = []
        for item in evidence:
            # Try to get quality from evidence item
            if isinstance(item, dict):
                quality = item.get("quality", 0.5)
                quality_scores.append(quality)
        
        if not quality_scores:
            return 0.5
        
        return sum(quality_scores) / len(quality_scores)

    def get_evidence_freshness(self, capability_id: str) -> float:
        """Get evidence freshness score (0.0 to 1.0)."""
        evidence_info = self.get_evidence_for_capability(capability_id)
        if not evidence_info:
            return 0.0
        
        # Calculate freshness based on evidence timestamps
        evidence = evidence_info.get("evidence", [])
        if not evidence:
            return 0.0
        
        from datetime import datetime, timedelta
        
        freshness_scores = []
        now = datetime.utcnow()
        
        for item in evidence:
            if isinstance(item, dict):
                timestamp = item.get("timestamp")
                if timestamp:
                    try:
                        if isinstance(timestamp, str):
                            timestamp = datetime.fromisoformat(timestamp)
                        
                        # Calculate age in days
                        age = (now - timestamp).days
                        
                        # Convert age to freshness score
                        # 0 days = 1.0, 30 days = 0.5, 60+ days = 0.0
                        if age <= 0:
                            freshness = 1.0
                        elif age <= 30:
                            freshness = 1.0 - (age / 60.0)
                        elif age <= 60:
                            freshness = 0.5 - ((age - 30) / 60.0)
                        else:
                            freshness = 0.0
                        
                        freshness_scores.append(max(0.0, freshness))
                    except Exception:
                        freshness_scores.append(0.5)
        
        if not freshness_scores:
            return 0.5
        
        return sum(freshness_scores) / len(freshness_scores)


class MockEvidenceProvider(EvidenceProvider):
    """
    Mock implementation of EvidenceProvider for testing.
    
    This provides static evidence scores for development when the real
    Evidence framework is not fully configured.
    """

    def get_evidence_for_capability(self, capability_id: str) -> Dict[str, Any]:
        """Return mock evidence information."""
        # Return different evidence counts based on capability
        capability_evidence = {
            "seo_audit": 7,
            "keyword_research": 5,
            "content_strategy": 3,
            "technical_seo": 4,
            "competitor_analysis": 2,
            "content_writing": 6,
            "social_media_management": 3,
            "digital_marketing": 4,
        }
        
        count = capability_evidence.get(capability_id.lower(), 2)
        
        return {
            "capability_id": capability_id,
            "evidence_count": count,
            "evidence": [
                {
                    "source": "internal",
                    "quality": 0.8,
                    "timestamp": "2026-08-01T00:00:00",
                }
                for _ in range(count)
            ],
        }

    def get_evidence_coverage(self, capability_id: str) -> float:
        """Get mock evidence coverage score."""
        capability_scores = {
            "seo_audit": 0.70,
            "keyword_research": 0.50,
            "content_strategy": 0.30,
            "technical_seo": 0.40,
            "competitor_analysis": 0.20,
            "content_writing": 0.60,
            "social_media_management": 0.30,
            "digital_marketing": 0.40,
        }
        return capability_scores.get(capability_id.lower(), 0.2)

    def get_evidence_quality(self, capability_id: str) -> float:
        """Get mock evidence quality score."""
        capability_scores = {
            "seo_audit": 0.82,
            "keyword_research": 0.88,
            "content_strategy": 0.70,
            "technical_seo": 0.75,
            "competitor_analysis": 0.65,
            "content_writing": 0.80,
            "social_media_management": 0.72,
            "digital_marketing": 0.78,
        }
        return capability_scores.get(capability_id.lower(), 0.5)

    def get_evidence_freshness(self, capability_id: str) -> float:
        """Get mock evidence freshness score."""
        capability_scores = {
            "seo_audit": 0.75,
            "keyword_research": 0.80,
            "content_strategy": 0.60,
            "technical_seo": 0.70,
            "competitor_analysis": 0.65,
            "content_writing": 0.78,
            "social_media_management": 0.68,
            "digital_marketing": 0.72,
        }
        return capability_scores.get(capability_id.lower(), 0.5)
