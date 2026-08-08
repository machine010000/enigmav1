import pytest

from app.expert_domains.models import DomainLifecycle, DomainLifecycleStage
from app.expert_domains.lifecycle import LifecycleManager


class TestDomainLifecycle:
    """Tests for DomainLifecycle model."""

    def test_lifecycle_initialization(self):
        """Test lifecycle initialization with default stage."""
        lifecycle = DomainLifecycle()
        assert lifecycle.get_current_stage() == DomainLifecycleStage.UNKNOWN

    def test_lifecycle_initialization_with_stage(self):
        """Test lifecycle initialization with specific stage."""
        lifecycle = DomainLifecycle(DomainLifecycleStage.LEARNING)
        assert lifecycle.get_current_stage() == DomainLifecycleStage.LEARNING

    def test_can_advance_to_valid_stage(self):
        """Test advancing to a valid stage."""
        lifecycle = DomainLifecycle(DomainLifecycleStage.LEARNING)
        assert lifecycle.can_advance_to(DomainLifecycleStage.GROWING) is True

    def test_can_advance_to_invalid_stage(self):
        """Test advancing to an invalid stage."""
        lifecycle = DomainLifecycle(DomainLifecycleStage.LEARNING)
        assert lifecycle.can_advance_to(DomainLifecycleStage.UNKNOWN) is False

    def test_advance_to_valid_stage(self):
        """Test advancing to a valid stage."""
        lifecycle = DomainLifecycle(DomainLifecycleStage.LEARNING)
        result = lifecycle.advance_to(DomainLifecycleStage.GROWING)
        assert result is True
        assert lifecycle.get_current_stage() == DomainLifecycleStage.GROWING

    def test_advance_to_invalid_stage(self):
        """Test advancing to an invalid stage."""
        lifecycle = DomainLifecycle(DomainLifecycleStage.LEARNING)
        result = lifecycle.advance_to(DomainLifecycleStage.UNKNOWN)
        assert result is False
        assert lifecycle.get_current_stage() == DomainLifecycleStage.LEARNING

    def test_stage_history_tracking(self):
        """Test that stage history is tracked."""
        lifecycle = DomainLifecycle(DomainLifecycleStage.LEARNING)
        lifecycle.advance_to(DomainLifecycleStage.GROWING)
        history = lifecycle.get_stage_history()
        assert len(history) == 2
        assert history[0][0] == DomainLifecycleStage.LEARNING
        assert history[1][0] == DomainLifecycleStage.GROWING


class TestLifecycleManager:
    """Tests for LifecycleManager."""

    def test_lifecycle_manager_initialization(self):
        """Test lifecycle manager initialization."""
        manager = LifecycleManager("test_domain")
        assert manager.domain_id == "test_domain"
        assert manager.get_current_stage() == DomainLifecycleStage.UNKNOWN

    def test_get_current_stage(self):
        """Test getting current stage."""
        manager = LifecycleManager("test_domain")
        stage = manager.get_current_stage()
        assert stage == DomainLifecycleStage.UNKNOWN

    def test_can_advance_to(self):
        """Test checking if can advance to stage."""
        manager = LifecycleManager("test_domain")
        assert manager.can_advance_to(DomainLifecycleStage.LEARNING) is True
        assert manager.can_advance_to(DomainLifecycleStage.UNKNOWN) is False

    def test_advance_to(self):
        """Test advancing to stage."""
        manager = LifecycleManager("test_domain")
        result = manager.advance_to(DomainLifecycleStage.LEARNING)
        assert result is True
        assert manager.get_current_stage() == DomainLifecycleStage.LEARNING

    def test_get_stage_history(self):
        """Test getting stage history."""
        manager = LifecycleManager("test_domain")
        manager.advance_to(DomainLifecycleStage.LEARNING)
        history = manager.get_stage_history()
        assert len(history) == 2

    def test_get_transition_requirements(self):
        """Test getting transition requirements."""
        manager = LifecycleManager("test_domain")
        requirements = manager.get_transition_requirements(DomainLifecycleStage.LEARNING)
        assert isinstance(requirements, list)
        assert len(requirements) > 0

    def test_get_stage_description(self):
        """Test getting stage description."""
        manager = LifecycleManager("test_domain")
        description = manager.get_stage_description(DomainLifecycleStage.LEARNING)
        assert isinstance(description, str)
        assert len(description) > 0
