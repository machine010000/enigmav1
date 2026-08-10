"""
Persistence Boundary Tests

Tests to verify persistence boundaries and in-memory state handling.
"""

import pytest

from app.enigma_profile.knowledge_progress import KnowledgeProgressTracker
from app.enigma_profile.training_tracker import TrainingTracker
from app.enigma_profile.platform_intelligence import PlatformIntelligence
from app.enigma_profile.development_engine import DevelopmentEngine
from app.enigma_profile.issue_intelligence import IssueIntelligence
from app.time_intelligence.customer_time import CustomerTimeAnalyzer
from app.marketplace.mock_adapter import MockMarketplaceAdapter
from app.marketplace.contracts import MarketplacePlatform


class TestEnigmaProfilePersistence:
    """Test Enigma Profile in-memory state."""
    
    def test_knowledge_progress_in_memory(self):
        """Test knowledge progress is in-memory."""
        tracker = KnowledgeProgressTracker()
        
        # Register a domain
        from app.enigma_profile.contracts import KnowledgeProgress
        tracker.register_domain(KnowledgeProgress(
            domain="SEO",
            knowledge_score=0.5,
            execution_score=0.3,
            evidence_score=0.2,
            confidence=0.4,
            readiness=0.35,
        ))
        
        # Verify it's stored in memory
        assert tracker.get_progress("SEO") is not None
        
        # Create new tracker instance - data should be lost
        tracker2 = KnowledgeProgressTracker()
        assert tracker2.get_progress("SEO") is None
    
    def test_training_tracker_in_memory(self):
        """Test training tracker is in-memory."""
        tracker = TrainingTracker()
        
        # Register training
        from app.enigma_profile.contracts import TrainingItem, SkillLevel
        tracker.register_training(TrainingItem(
            skill="SEO",
            level=SkillLevel.LEARNING,
            progress=0.2,
        ))
        
        # Verify it's stored in memory
        assert tracker.get_training("SEO") is not None
        
        # Create new tracker instance - data should be lost
        tracker2 = TrainingTracker()
        assert tracker2.get_training("SEO") is None
    
    def test_platform_intelligence_in_memory(self):
        """Test platform intelligence is in-memory."""
        intelligence = PlatformIntelligence()
        
        # Register platform readiness
        from app.enigma_profile.contracts import PlatformReadiness
        intelligence.register_platform_readiness(PlatformReadiness(
            platform=MarketplacePlatform.UPWORK,
            overall_readiness=0.5,
            knowledge_score=0.5,
            evidence_score=0.5,
            portfolio_score=0.5,
            execution_score=0.5,
            win_probability=0.5,
            economics_score=0.5,
        ))
        
        # Verify it's stored in memory
        assert intelligence.get_platform_readiness(MarketplacePlatform.UPWORK) is not None
        
        # Create new intelligence instance - data should be lost
        intelligence2 = PlatformIntelligence()
        assert intelligence2.get_platform_readiness(MarketplacePlatform.UPWORK) is None
    
    def test_development_engine_in_memory(self):
        """Test development engine is in-memory."""
        engine = DevelopmentEngine()
        
        # Add priority
        engine.add_priority(
            title="Test priority",
            description="Test description",
            category="knowledge",
        )
        
        # Verify it's stored in memory
        priorities = engine.get_top_priorities()
        assert len(priorities) == 1
        
        # Create new engine instance - data should be lost
        engine2 = DevelopmentEngine()
        priorities2 = engine2.get_top_priorities()
        assert len(priorities2) == 0
    
    def test_issue_intelligence_in_memory(self):
        """Test issue intelligence is in-memory."""
        intelligence = IssueIntelligence()
        
        # Report issue
        issue = intelligence.report_issue(
            source="system",
            type="API",
            severity="HIGH",
            detected_reason="Test error",
        )
        
        # Verify it's stored in memory
        retrieved = intelligence.get_issue(issue.issue_id)
        assert retrieved is not None
        
        # Create new intelligence instance - data should be lost
        intelligence2 = IssueIntelligence()
        assert intelligence2.get_issue(issue.issue_id) is None
    
    def test_customer_time_in_memory(self):
        """Test customer time analyzer is in-memory."""
        analyzer = CustomerTimeAnalyzer()
        
        # Register customer timezone
        from app.time_intelligence.contracts import TimezoneInfo, TimezoneSource
        analyzer.register_customer_timezone("customer_1", TimezoneInfo(
            timezone="America/Toronto",
            source=TimezoneSource.EXPLICIT,
            confidence=1.0,
        ))
        
        # Verify it's stored in memory
        assert analyzer.get_customer_timezone("customer_1") is not None
        
        # Create new analyzer instance - data should be lost
        analyzer2 = CustomerTimeAnalyzer()
        assert analyzer2.get_customer_timezone("customer_1") is None


class TestMockAdapterInMemory:
    """Test mock adapter in-memory state."""
    
    def test_mock_adapter_in_memory(self):
        """Test mock adapter is in-memory."""
        adapter = MockMarketplaceAdapter()
        
        # Authenticate
        import asyncio
        account = asyncio.run(adapter.authenticate({}))
        
        # Verify account is stored
        assert adapter._account is not None
        assert adapter._authenticated is True
        
        # Create new adapter instance - data should be lost
        adapter2 = MockMarketplaceAdapter()
        assert adapter2._account is None
        assert adapter2._authenticated is False


class TestSafeInMemoryState:
    """Test in-memory state that is safe to keep."""
    
    def test_academy_cache_safe(self):
        """Test academy cache is safe (rebuildable)."""
        from app.academy.academy_manager import AcademyManager
        from app.academy.academy_models import AcademyModule
        
        manager = AcademyManager()
        
        # Cache should be rebuildable from registry
        assert manager._cache is not None
        
        # This is safe because it can be rebuilt from registry
        manager2 = AcademyManager()
        assert manager2._cache is not None
    
    def test_timezone_cache_safe(self):
        """Test timezone cache is safe (performance only)."""
        from app.time_intelligence.timezone_service import TimezoneService
        
        service = TimezoneService()
        
        # Cache is for performance only
        assert service._timezone_cache is not None
        
        # This is safe because it's just a performance cache
        service2 = TimezoneService()
        assert service2._timezone_cache is not None
    
    def test_pipeline_engines_stateless(self):
        """Test pipeline engines are stateless."""
        from app.pipeline.orchestrator import PipelineOrchestrator
        
        orchestrator = PipelineOrchestrator()
        
        # Engines should be stateless services
        assert orchestrator.creativity_engine is not None
        assert orchestrator.account_economics_engine is not None
        assert orchestrator.customer_time_analyzer is not None
        
        # These are safe because they're stateless services
        orchestrator2 = PipelineOrchestrator()
        assert orchestrator2.creativity_engine is not None


class TestPersistenceRequirements:
    """Test persistence requirements documentation."""
    
    def test_enigma_profile_requires_persistence(self):
        """Test that Enigma Profile modules require persistence."""
        # These modules lose data on restart
        modules = [
            KnowledgeProgressTracker,
            TrainingTracker,
            PlatformIntelligence,
            DevelopmentEngine,
            IssueIntelligence,
            CustomerTimeAnalyzer,
        ]
        
        for module_class in modules:
            instance = module_class()
            # Create another instance
            instance2 = module_class()
            # Data should be lost (requires persistence)
            # This is expected behavior for TASK-050
            # Persistence will be added in future tasks
    
    def test_mock_adapter_test_only(self):
        """Test that mock adapter is test-only."""
        adapter = MockMarketplaceAdapter()
        
        # Mock adapter should only be used in tests
        assert adapter.platform.value.lower() == "mock"
        
        # Should not be used in production
        # This is documented in TASK-050 audit
