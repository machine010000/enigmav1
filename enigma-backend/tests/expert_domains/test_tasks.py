import pytest

from app.expert_domains.tasks import (
    TaskContract,
    TaskCategory,
    TaskStatus,
    TaskRequirement,
    TaskExecution,
    TaskRegistry,
)


class TestTaskContract:
    """Tests for TaskContract."""

    def test_task_contract_creation(self):
        """Test creating a task contract."""
        task = TaskContract(
            task_id="seo_audit",
            name="SEO Audit",
            description="Perform SEO audit",
            goal="Identify SEO issues",
            category=TaskCategory.ANALYSIS,
        )
        assert task.task_id == "seo_audit"
        assert task.name == "SEO Audit"
        assert task.category == TaskCategory.ANALYSIS

    def test_task_contract_with_requirements(self):
        """Test task with requirements."""
        task = TaskContract(
            task_id="seo_audit",
            name="SEO Audit",
            description="Perform SEO audit",
            goal="Identify SEO issues",
            category=TaskCategory.ANALYSIS,
            required_capabilities=["keyword_research", "technical_seo"],
            inputs=["website_url"],
            outputs=["audit_report"],
        )
        assert len(task.required_capabilities) == 2
        assert len(task.inputs) == 1
        assert len(task.outputs) == 1


class TestTaskRequirement:
    """Tests for TaskRequirement."""

    def test_task_requirement_creation(self):
        """Test creating a task requirement."""
        requirement = TaskRequirement(
            requirement_id="req1",
            task_id="seo_audit",
            requirement_type="capability",
            requirement_value="keyword_research",
        )
        assert requirement.requirement_id == "req1"
        assert requirement.task_id == "seo_audit"
        assert requirement.requirement_type == "capability"


class TestTaskExecution:
    """Tests for TaskExecution."""

    def test_task_execution_creation(self):
        """Test creating a task execution."""
        execution = TaskExecution(
            execution_id="exec1",
            task_id="seo_audit",
            status=TaskStatus.IN_PROGRESS,
            started_at="2024-01-01T00:00:00",
        )
        assert execution.execution_id == "exec1"
        assert execution.task_id == "seo_audit"
        assert execution.status == TaskStatus.IN_PROGRESS


class TestTaskRegistry:
    """Tests for TaskRegistry."""

    def test_registry_initialization(self):
        """Test registry initialization."""
        registry = TaskRegistry()
        assert registry.list_all() == []

    def test_register_task(self):
        """Test registering a task."""
        registry = TaskRegistry()
        task = TaskContract(
            task_id="seo_audit",
            name="SEO Audit",
            description="Perform SEO audit",
            goal="Identify SEO issues",
            category=TaskCategory.ANALYSIS,
        )
        result = registry.register(task)
        assert result is True
        assert "seo_audit" in [t.task_id for t in registry.list_all()]

    def test_register_duplicate_task(self):
        """Test that registering a duplicate task fails."""
        registry = TaskRegistry()
        task = TaskContract(
            task_id="seo_audit",
            name="SEO Audit",
            description="Perform SEO audit",
            goal="Identify SEO issues",
            category=TaskCategory.ANALYSIS,
        )
        registry.register(task)
        result = registry.register(task)
        assert result is False

    def test_get_task(self):
        """Test retrieving a task."""
        registry = TaskRegistry()
        task = TaskContract(
            task_id="seo_audit",
            name="SEO Audit",
            description="Perform SEO audit",
            goal="Identify SEO issues",
            category=TaskCategory.ANALYSIS,
        )
        registry.register(task)
        retrieved = registry.get("seo_audit")
        assert retrieved is not None
        assert retrieved.task_id == "seo_audit"

    def test_list_by_category(self):
        """Test listing tasks by category."""
        registry = TaskRegistry()
        task1 = TaskContract(
            task_id="seo_audit",
            name="SEO Audit",
            description="Perform SEO audit",
            goal="Identify SEO issues",
            category=TaskCategory.ANALYSIS,
        )
        task2 = TaskContract(
            task_id="content_creation",
            name="Content Creation",
            description="Create content",
            goal="Produce content",
            category=TaskCategory.EXECUTION,
        )
        registry.register(task1)
        registry.register(task2)
        analysis_tasks = registry.list_by_category(TaskCategory.ANALYSIS)
        assert len(analysis_tasks) == 1
        assert analysis_tasks[0].task_id == "seo_audit"

    def test_list_by_capability(self):
        """Test listing tasks by capability."""
        registry = TaskRegistry()
        task1 = TaskContract(
            task_id="seo_audit",
            name="SEO Audit",
            description="Perform SEO audit",
            goal="Identify SEO issues",
            category=TaskCategory.ANALYSIS,
            required_capabilities=["keyword_research"],
        )
        task2 = TaskContract(
            task_id="content_creation",
            name="Content Creation",
            description="Create content",
            goal="Produce content",
            category=TaskCategory.EXECUTION,
            required_capabilities=["content_writing"],
        )
        registry.register(task1)
        registry.register(task2)
        keyword_tasks = registry.list_by_capability("keyword_research")
        assert len(keyword_tasks) == 1
        assert keyword_tasks[0].task_id == "seo_audit"

    def test_validate_capability_requirements_success(self):
        """Test capability requirement validation with all capabilities available."""
        registry = TaskRegistry()
        task = TaskContract(
            task_id="seo_audit",
            name="SEO Audit",
            description="Perform SEO audit",
            goal="Identify SEO issues",
            category=TaskCategory.ANALYSIS,
            required_capabilities=["keyword_research", "technical_seo"],
        )
        registry.register(task)
        validation = registry.validate_capability_requirements(
            "seo_audit",
            ["keyword_research", "technical_seo"],
        )
        assert validation["valid"] is True
        assert validation["capabilities_met"] is True

    def test_validate_capability_requirements_failure(self):
        """Test capability requirement validation with missing capabilities."""
        registry = TaskRegistry()
        task = TaskContract(
            task_id="seo_audit",
            name="SEO Audit",
            description="Perform SEO audit",
            goal="Identify SEO issues",
            category=TaskCategory.ANALYSIS,
            required_capabilities=["keyword_research", "technical_seo"],
        )
        registry.register(task)
        validation = registry.validate_capability_requirements(
            "seo_audit",
            ["keyword_research"],
        )
        assert validation["valid"] is False
        assert validation["capabilities_met"] is False
        assert "technical_seo" in validation["missing_capabilities"]
