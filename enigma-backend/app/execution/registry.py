from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from app.execution.contracts import (
    ExecutionPlanner,
    ExecutionScheduler,
    ExecutionValidator,
    OutputBuilder,
    ReflectionGenerator,
)
from app.execution.planner import BaseExecutionPlanner, TemplateBasedPlanner
from app.execution.scheduler import BaseExecutionScheduler, PriorityExecutionScheduler
from app.execution.validation import BaseValidator, RuleBasedValidator
from app.execution.outputs import BaseOutputBuilder
from app.execution.reflection import BaseReflectionGenerator


class ExecutionRegistry:
    """
    Registry for execution framework components.
    
    This registry manages:
    - Execution planners
    - Execution schedulers
    - Execution validators
    - Output builders
    - Reflection generators
    - Custom templates
    - Quality gates
    """

    def __init__(self) -> None:
        # Planners
        self._planners: Dict[str, ExecutionPlanner] = {}
        self._default_planner: Optional[ExecutionPlanner] = None
        
        # Schedulers
        self._schedulers: Dict[str, ExecutionScheduler] = {}
        self._default_scheduler: Optional[ExecutionScheduler] = None
        
        # Validators
        self._validators: Dict[str, ExecutionValidator] = {}
        self._default_validator: Optional[ExecutionValidator] = None
        
        # Output builders
        self._output_builders: Dict[str, OutputBuilder] = {}
        self._default_output_builder: Optional[OutputBuilder] = None
        
        # Reflection generators
        self._reflection_generators: Dict[str, ReflectionGenerator] = {}
        self._default_reflection_generator: Optional[ReflectionGenerator] = None
        
        # Templates
        self._templates: Dict[str, Dict[str, Any]] = {}
        
        # Quality gates
        self._quality_gates: Dict[str, Dict[str, Any]] = {}
        
        # Domain-specific configurations
        self._domain_configs: Dict[str, Dict[str, Any]] = {}

    # Planner Management
    def register_planner(
        self,
        planner_id: str,
        planner: ExecutionPlanner,
        set_as_default: bool = False,
    ) -> None:
        """Register an execution planner."""
        self._planners[planner_id] = planner
        if set_as_default or self._default_planner is None:
            self._default_planner = planner

    def get_planner(self, planner_id: str) -> Optional[ExecutionPlanner]:
        """Get a registered planner."""
        return self._planners.get(planner_id)

    def get_default_planner(self) -> Optional[ExecutionPlanner]:
        """Get the default planner."""
        return self._default_planner

    def list_planners(self) -> List[str]:
        """List all registered planner IDs."""
        return list(self._planners.keys())

    # Scheduler Management
    def register_scheduler(
        self,
        scheduler_id: str,
        scheduler: ExecutionScheduler,
        set_as_default: bool = False,
    ) -> None:
        """Register an execution scheduler."""
        self._schedulers[scheduler_id] = scheduler
        if set_as_default or self._default_scheduler is None:
            self._default_scheduler = scheduler

    def get_scheduler(self, scheduler_id: str) -> Optional[ExecutionScheduler]:
        """Get a registered scheduler."""
        return self._schedulers.get(scheduler_id)

    def get_default_scheduler(self) -> Optional[ExecutionScheduler]:
        """Get the default scheduler."""
        return self._default_scheduler

    def list_schedulers(self) -> List[str]:
        """List all registered scheduler IDs."""
        return list(self._schedulers.keys())

    # Validator Management
    def register_validator(
        self,
        validator_id: str,
        validator: ExecutionValidator,
        set_as_default: bool = False,
    ) -> None:
        """Register an execution validator."""
        self._validators[validator_id] = validator
        if set_as_default or self._default_validator is None:
            self._default_validator = validator

    def get_validator(self, validator_id: str) -> Optional[ExecutionValidator]:
        """Get a registered validator."""
        return self._validators.get(validator_id)

    def get_default_validator(self) -> Optional[ExecutionValidator]:
        """Get the default validator."""
        return self._default_validator

    def list_validators(self) -> List[str]:
        """List all registered validator IDs."""
        return list(self._validators.keys())

    # Output Builder Management
    def register_output_builder(
        self,
        builder_id: str,
        builder: OutputBuilder,
        set_as_default: bool = False,
    ) -> None:
        """Register an output builder."""
        self._output_builders[builder_id] = builder
        if set_as_default or self._default_output_builder is None:
            self._default_output_builder = builder

    def get_output_builder(self, builder_id: str) -> Optional[OutputBuilder]:
        """Get a registered output builder."""
        return self._output_builders.get(builder_id)

    def get_default_output_builder(self) -> Optional[OutputBuilder]:
        """Get the default output builder."""
        return self._default_output_builder

    def list_output_builders(self) -> List[str]:
        """List all registered output builder IDs."""
        return list(self._output_builders.keys())

    # Reflection Generator Management
    def register_reflection_generator(
        self,
        generator_id: str,
        generator: ReflectionGenerator,
        set_as_default: bool = False,
    ) -> None:
        """Register a reflection generator."""
        self._reflection_generators[generator_id] = generator
        if set_as_default or self._default_reflection_generator is None:
            self._default_reflection_generator = generator

    def get_reflection_generator(self, generator_id: str) -> Optional[ReflectionGenerator]:
        """Get a registered reflection generator."""
        return self._reflection_generators.get(generator_id)

    def get_default_reflection_generator(self) -> Optional[ReflectionGenerator]:
        """Get the default reflection generator."""
        return self._default_reflection_generator

    def list_reflection_generators(self) -> List[str]:
        """List all registered reflection generator IDs."""
        return list(self._reflection_generators.keys())

    # Template Management
    def register_template(
        self,
        template_id: str,
        template: Dict[str, Any],
    ) -> None:
        """Register an execution template."""
        self._templates[template_id] = template

    def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Get a registered template."""
        return self._templates.get(template_id)

    def list_templates(self) -> List[str]:
        """List all registered template IDs."""
        return list(self._templates.keys())

    # Quality Gate Management
    def register_quality_gate(
        self,
        gate_id: str,
        gate: Dict[str, Any],
    ) -> None:
        """Register a quality gate."""
        self._quality_gates[gate_id] = gate

    def get_quality_gate(self, gate_id: str) -> Optional[Dict[str, Any]]:
        """Get a registered quality gate."""
        return self._quality_gates.get(gate_id)

    def list_quality_gates(self) -> List[str]:
        """List all registered quality gate IDs."""
        return list(self._quality_gates.keys())

    # Domain Configuration Management
    def register_domain_config(
        self,
        domain_id: str,
        config: Dict[str, Any],
    ) -> None:
        """Register domain-specific configuration."""
        self._domain_configs[domain_id] = config

    def get_domain_config(self, domain_id: str) -> Optional[Dict[str, Any]]:
        """Get domain-specific configuration."""
        return self._domain_configs.get(domain_id)

    def list_domains(self) -> List[str]:
        """List all registered domain IDs."""
        return list(self._domain_configs.keys())

    # Domain-specific component registration
    def configure_domain(
        self,
        domain_id: str,
        planner_id: Optional[str] = None,
        scheduler_id: Optional[str] = None,
        validator_id: Optional[str] = None,
        output_builder_id: Optional[str] = None,
        reflection_generator_id: Optional[str] = None,
    ) -> None:
        """
        Configure a domain with specific components.
        
        Args:
            domain_id: ID of the domain
            planner_id: ID of the planner to use
            scheduler_id: ID of the scheduler to use
            validator_id: ID of the validator to use
            output_builder_id: ID of the output builder to use
            reflection_generator_id: ID of the reflection generator to use
        """
        config = {}
        if planner_id:
            config["planner_id"] = planner_id
        if scheduler_id:
            config["scheduler_id"] = scheduler_id
        if validator_id:
            config["validator_id"] = validator_id
        if output_builder_id:
            config["output_builder_id"] = output_builder_id
        if reflection_generator_id:
            config["reflection_generator_id"] = reflection_generator_id
        
        self._domain_configs[domain_id] = config

    def get_domain_planner(self, domain_id: str) -> Optional[ExecutionPlanner]:
        """Get the planner configured for a domain."""
        config = self._domain_configs.get(domain_id)
        if config and "planner_id" in config:
            return self.get_planner(config["planner_id"])
        return self._default_planner

    def get_domain_scheduler(self, domain_id: str) -> Optional[ExecutionScheduler]:
        """Get the scheduler configured for a domain."""
        config = self._domain_configs.get(domain_id)
        if config and "scheduler_id" in config:
            return self.get_scheduler(config["scheduler_id"])
        return self._default_scheduler

    def get_domain_validator(self, domain_id: str) -> Optional[ExecutionValidator]:
        """Get the validator configured for a domain."""
        config = self._domain_configs.get(domain_id)
        if config and "validator_id" in config:
            return self.get_validator(config["validator_id"])
        return self._default_validator

    def get_domain_output_builder(self, domain_id: str) -> Optional[OutputBuilder]:
        """Get the output builder configured for a domain."""
        config = self._domain_configs.get(domain_id)
        if config and "output_builder_id" in config:
            return self.get_output_builder(config["output_builder_id"])
        return self._default_output_builder

    def get_domain_reflection_generator(self, domain_id: str) -> Optional[ReflectionGenerator]:
        """Get the reflection generator configured for a domain."""
        config = self._domain_configs.get(domain_id)
        if config and "reflection_generator_id" in config:
            return self.get_reflection_generator(config["reflection_generator_id"])
        return self._default_reflection_generator

    # Registry initialization
    def initialize_with_defaults(self) -> None:
        """Initialize registry with default components."""
        # Register default planners
        base_planner = BaseExecutionPlanner()
        template_planner = TemplateBasedPlanner()
        self.register_planner("base", base_planner, set_as_default=True)
        self.register_planner("template", template_planner)
        
        # Register default schedulers
        base_scheduler = BaseExecutionScheduler()
        priority_scheduler = PriorityExecutionScheduler()
        self.register_scheduler("base", base_scheduler, set_as_default=True)
        self.register_scheduler("priority", priority_scheduler)
        
        # Register default validators
        base_validator = BaseValidator()
        rule_validator = RuleBasedValidator()
        self.register_validator("base", base_validator, set_as_default=True)
        self.register_validator("rule", rule_validator)
        
        # Register default output builders
        base_output_builder = BaseOutputBuilder()
        self.register_output_builder("base", base_output_builder, set_as_default=True)
        
        # Register default reflection generators
        base_reflection_generator = BaseReflectionGenerator()
        self.register_reflection_generator("base", base_reflection_generator, set_as_default=True)

    def clear(self) -> None:
        """Clear all registered components."""
        self._planners.clear()
        self._schedulers.clear()
        self._validators.clear()
        self._output_builders.clear()
        self._reflection_generators.clear()
        self._templates.clear()
        self._quality_gates.clear()
        self._domain_configs.clear()
        self._default_planner = None
        self._default_scheduler = None
        self._default_validator = None
        self._default_output_builder = None
        self._default_reflection_generator = None


# Global execution registry instance
execution_registry = ExecutionRegistry()
execution_registry.initialize_with_defaults()
