"""
Tests for Execution Registry module.

Tests component registration, domain configuration, and default initialization.
"""

import pytest

from app.execution.contracts import (
    ExecutionPlan,
    ExecutionStep,
    StepState,
    StepType,
)
from app.execution.registry import ExecutionRegistry, execution_registry
from app.execution.planner import BaseExecutionPlanner, TemplateBasedPlanner
from app.execution.scheduler import BaseExecutionScheduler
from app.execution.validation import BaseValidator
from app.execution.outputs import BaseOutputBuilder
from app.execution.reflection import BaseReflectionGenerator


class TestExecutionRegistry:
    """Test ExecutionRegistry."""

    def test_registry_initialization(self):
        """Test registry initialization."""
        registry = ExecutionRegistry()
        
        assert registry._planners == {}
        assert registry._schedulers == {}
        assert registry._validators == {}
        assert registry._output_builders == {}
        assert registry._reflection_generators == {}

    def test_register_planner(self):
        """Test registering a planner."""
        registry = ExecutionRegistry()
        
        planner = BaseExecutionPlanner()
        registry.register_planner("test_planner", planner)
        
        assert "test_planner" in registry._planners
        assert registry.get_planner("test_planner") is planner

    def test_register_planner_as_default(self):
        """Test registering planner as default."""
        registry = ExecutionRegistry()
        
        planner = BaseExecutionPlanner()
        registry.register_planner("test_planner", planner, set_as_default=True)
        
        assert registry.get_default_planner() is planner

    def test_register_scheduler(self):
        """Test registering a scheduler."""
        registry = ExecutionRegistry()
        
        scheduler = BaseExecutionScheduler()
        registry.register_scheduler("test_scheduler", scheduler)
        
        assert "test_scheduler" in registry._schedulers
        assert registry.get_scheduler("test_scheduler") is scheduler

    def test_register_validator(self):
        """Test registering a validator."""
        registry = ExecutionRegistry()
        
        validator = BaseValidator()
        registry.register_validator("test_validator", validator)
        
        assert "test_validator" in registry._validators
        assert registry.get_validator("test_validator") is validator

    def test_register_output_builder(self):
        """Test registering an output builder."""
        registry = ExecutionRegistry()
        
        builder = BaseOutputBuilder()
        registry.register_output_builder("test_builder", builder)
        
        assert "test_builder" in registry._output_builders
        assert registry.get_output_builder("test_builder") is builder

    def test_register_reflection_generator(self):
        """Test registering a reflection generator."""
        registry = ExecutionRegistry()
        
        generator = BaseReflectionGenerator()
        registry.register_reflection_generator("test_generator", generator)
        
        assert "test_generator" in registry._reflection_generators
        assert registry.get_reflection_generator("test_generator") is generator

    def test_register_template(self):
        """Test registering a template."""
        registry = ExecutionRegistry()
        
        template = {
            "steps": [
                {
                    "step_id": "step_001",
                    "step_type": "task",
                    "name": "Task 1",
                    "description": "First task",
                }
            ],
            "step_order": ["step_001"],
        }
        
        registry.register_template("test_template", template)
        
        assert "test_template" in registry._templates
        assert registry.get_template("test_template") is template

    def test_register_quality_gate(self):
        """Test registering a quality gate."""
        registry = ExecutionRegistry()
        
        gate = {
            "gate_id": "gate_001",
            "step_id": "step_001",
            "gate_name": "Quality Check",
            "description": "Quality gate",
            "criteria": ["criterion_1"],
        }
        
        registry.register_quality_gate("gate_001", gate)
        
        assert "gate_001" in registry._quality_gates
        assert registry.get_quality_gate("gate_001") is gate

    def test_register_domain_config(self):
        """Test registering domain configuration."""
        registry = ExecutionRegistry()
        
        config = {
            "planner_id": "test_planner",
            "scheduler_id": "test_scheduler",
        }
        
        registry.register_domain_config("seo", config)
        
        assert "seo" in registry._domain_configs
        assert registry.get_domain_config("seo") is config

    def test_configure_domain(self):
        """Test configuring a domain."""
        registry = ExecutionRegistry()
        
        planner = BaseExecutionPlanner()
        scheduler = BaseExecutionScheduler()
        
        registry.register_planner("test_planner", planner)
        registry.register_scheduler("test_scheduler", scheduler)
        
        registry.configure_domain(
            "seo",
            planner_id="test_planner",
            scheduler_id="test_scheduler",
        )
        
        assert registry.get_domain_planner("seo") is planner
        assert registry.get_domain_scheduler("seo") is scheduler

    def test_get_domain_planner_fallback(self):
        """Test getting domain planner falls back to default."""
        registry = ExecutionRegistry()
        
        default_planner = BaseExecutionPlanner()
        registry.register_planner("default", default_planner, set_as_default=True)
        
        # Configure domain without setting planner_id
        registry.register_domain_config("seo", {})
        
        # Should fall back to default when no planner_id is configured
        assert registry.get_domain_planner("seo") is default_planner

    def test_get_domain_scheduler_fallback(self):
        """Test getting domain scheduler falls back to default."""
        registry = ExecutionRegistry()
        
        default_scheduler = BaseExecutionScheduler()
        registry.register_scheduler("default", default_scheduler, set_as_default=True)
        
        # Configure domain without setting scheduler_id
        registry.register_domain_config("seo", {})
        
        # Should fall back to default when no scheduler_id is configured
        assert registry.get_domain_scheduler("seo") is default_scheduler

    def test_list_planners(self):
        """Test listing all planners."""
        registry = ExecutionRegistry()
        
        registry.register_planner("planner1", BaseExecutionPlanner())
        registry.register_planner("planner2", BaseExecutionPlanner())
        
        planners = registry.list_planners()
        
        assert len(planners) == 2
        assert "planner1" in planners
        assert "planner2" in planners

    def test_list_schedulers(self):
        """Test listing all schedulers."""
        registry = ExecutionRegistry()
        
        registry.register_scheduler("scheduler1", BaseExecutionScheduler())
        registry.register_scheduler("scheduler2", BaseExecutionScheduler())
        
        schedulers = registry.list_schedulers()
        
        assert len(schedulers) == 2

    def test_list_validators(self):
        """Test listing all validators."""
        registry = ExecutionRegistry()
        
        registry.register_validator("validator1", BaseValidator())
        registry.register_validator("validator2", BaseValidator())
        
        validators = registry.list_validators()
        
        assert len(validators) == 2

    def test_list_output_builders(self):
        """Test listing all output builders."""
        registry = ExecutionRegistry()
        
        registry.register_output_builder("builder1", BaseOutputBuilder())
        registry.register_output_builder("builder2", BaseOutputBuilder())
        
        builders = registry.list_output_builders()
        
        assert len(builders) == 2

    def test_list_reflection_generators(self):
        """Test listing all reflection generators."""
        registry = ExecutionRegistry()
        
        registry.register_reflection_generator("generator1", BaseReflectionGenerator())
        registry.register_reflection_generator("generator2", BaseReflectionGenerator())
        
        generators = registry.list_reflection_generators()
        
        assert len(generators) == 2

    def test_list_templates(self):
        """Test listing all templates."""
        registry = ExecutionRegistry()
        
        registry.register_template("template1", {})
        registry.register_template("template2", {})
        
        templates = registry.list_templates()
        
        assert len(templates) == 2

    def test_list_quality_gates(self):
        """Test listing all quality gates."""
        registry = ExecutionRegistry()
        
        registry.register_quality_gate("gate1", {})
        registry.register_quality_gate("gate2", {})
        
        gates = registry.list_quality_gates()
        
        assert len(gates) == 2

    def test_list_domains(self):
        """Test listing all domains."""
        registry = ExecutionRegistry()
        
        registry.register_domain_config("seo", {})
        registry.register_domain_config("ads", {})
        
        domains = registry.list_domains()
        
        assert len(domains) == 2

    def test_initialize_with_defaults(self):
        """Test initializing registry with defaults."""
        registry = ExecutionRegistry()
        registry.initialize_with_defaults()
        
        # Should have default components
        assert registry.get_default_planner() is not None
        assert registry.get_default_scheduler() is not None
        assert registry.get_default_validator() is not None
        assert registry.get_default_output_builder() is not None
        assert registry.get_default_reflection_generator() is not None

    def test_clear_registry(self):
        """Test clearing registry."""
        registry = ExecutionRegistry()
        
        registry.register_planner("test_planner", BaseExecutionPlanner())
        registry.register_scheduler("test_scheduler", BaseExecutionScheduler())
        registry.register_template("test_template", {})
        
        registry.clear()
        
        assert len(registry._planners) == 0
        assert len(registry._schedulers) == 0
        assert len(registry._templates) == 0
        assert registry.get_default_planner() is None


class TestGlobalRegistry:
    """Test global registry instance."""

    def test_global_registry_exists(self):
        """Test global registry instance exists."""
        from app.execution import execution_registry
        
        assert execution_registry is not None
        assert isinstance(execution_registry, ExecutionRegistry)

    def test_global_registry_initialized(self):
        """Test global registry is initialized with defaults."""
        from app.execution import execution_registry
        
        # Should have default components
        assert execution_registry.get_default_planner() is not None
        assert execution_registry.get_default_scheduler() is not None
        assert execution_registry.get_default_validator() is not None

    def test_global_registry_has_base_planner(self):
        """Test global registry has base planner."""
        from app.execution import execution_registry
        
        assert execution_registry.get_planner("base") is not None

    def test_global_registry_has_template_planner(self):
        """Test global registry has template planner."""
        from app.execution import execution_registry
        
        assert execution_registry.get_planner("template") is not None

    def test_global_registry_has_base_scheduler(self):
        """Test global registry has base scheduler."""
        from app.execution import execution_registry
        
        assert execution_registry.get_scheduler("base") is not None

    def test_global_registry_has_priority_scheduler(self):
        """Test global registry has priority scheduler."""
        from app.execution import execution_registry
        
        assert execution_registry.get_scheduler("priority") is not None

    def test_global_registry_has_base_validator(self):
        """Test global registry has base validator."""
        from app.execution import execution_registry
        
        assert execution_registry.get_validator("base") is not None

    def test_global_registry_has_rule_validator(self):
        """Test global registry has rule validator."""
        from app.execution import execution_registry
        
        assert execution_registry.get_validator("rule") is not None
