import pytest

from app.expert_domains.learning import LearningManager


class TestLearningManager:
    """Tests for LearningManager."""

    def test_learning_manager_initialization(self):
        """Test learning manager initialization."""
        manager = LearningManager("test_domain")
        assert manager.domain_id == "test_domain"

    def test_record_new_knowledge(self):
        """Test recording new knowledge."""
        manager = LearningManager("test_domain")
        manager.record_new_knowledge("concept1", "test knowledge", "test_source")
        history = manager.get_learning_history()
        assert len(history) == 1
        assert history[0]["type"] == "new_knowledge"
        assert history[0]["concept_id"] == "concept1"

    def test_record_evidence_update(self):
        """Test recording evidence update."""
        manager = LearningManager("test_domain")
        manager.record_evidence_update("evidence1", "add")
        history = manager.get_learning_history()
        assert len(history) == 1
        assert history[0]["type"] == "evidence_update"
        assert history[0]["evidence_id"] == "evidence1"

    def test_record_concept_update(self):
        """Test recording concept update."""
        manager = LearningManager("test_domain")
        manager.record_concept_update("concept1", "refine")
        history = manager.get_learning_history()
        assert len(history) == 1
        assert history[0]["type"] == "concept_update"
        assert history[0]["concept_id"] == "concept1"

    def test_record_rule_update(self):
        """Test recording rule update."""
        manager = LearningManager("test_domain")
        manager.record_rule_update("rule1", "update")
        history = manager.get_learning_history()
        assert len(history) == 1
        assert history[0]["type"] == "rule_update"
        assert history[0]["rule_id"] == "rule1"

    def test_record_reflection(self):
        """Test recording reflection."""
        manager = LearningManager("test_domain")
        manager.record_reflection("test reflection", "success")
        history = manager.get_learning_history()
        assert len(history) == 1
        assert history[0]["type"] == "reflection"
        assert history[0]["reflection"] == "test reflection"

    def test_record_maturity_update(self):
        """Test recording maturity update."""
        manager = LearningManager("test_domain")
        manager.record_maturity_update("concept1", 2, 3)
        history = manager.get_learning_history()
        assert len(history) == 1
        assert history[0]["type"] == "maturity_update"
        assert history[0]["old_maturity"] == 2
        assert history[0]["new_maturity"] == 3

    def test_get_learning_history(self):
        """Test getting learning history."""
        manager = LearningManager("test_domain")
        manager.record_new_knowledge("concept1", "test", "source")
        manager.record_evidence_update("evidence1", "add")
        history = manager.get_learning_history()
        assert len(history) == 2

    def test_get_recent_learning(self):
        """Test getting recent learning."""
        manager = LearningManager("test_domain")
        manager.record_new_knowledge("concept1", "test", "source")
        recent = manager.get_recent_learning(24)
        assert len(recent) == 1

    def test_get_learning_summary(self):
        """Test getting learning summary."""
        manager = LearningManager("test_domain")
        manager.record_new_knowledge("concept1", "test", "source")
        manager.record_evidence_update("evidence1", "add")
        summary = manager.get_learning_summary()
        assert summary["domain_id"] == "test_domain"
        assert summary["total_learning_events"] == 2
        assert "learning_by_type" in summary

    def test_should_trigger_reflection(self):
        """Test reflection trigger condition."""
        manager = LearningManager("test_domain")
        assert manager.should_trigger_reflection() is False
        for i in range(5):
            manager.record_new_knowledge(f"concept{i}", "test", "source")
        assert manager.should_trigger_reflection() is True

    def test_get_learning_recommendations(self):
        """Test getting learning recommendations."""
        manager = LearningManager("test_domain")
        recommendations = manager.get_learning_recommendations()
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        manager.record_new_knowledge("concept1", "test", "source")
        recommendations = manager.get_learning_recommendations()
        assert isinstance(recommendations, list)
