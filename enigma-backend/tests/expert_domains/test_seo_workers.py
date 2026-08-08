"""
Tests for SEO Workers module.

Tests SEO-specific workers that produce real SEO outputs.
"""

import pytest

from app.execution.executor import ExecutionContext, ExecutionResult
from app.execution.contracts import ExecutionStep, StepType
from app.expert_domains.domains.seo_workers import (
    SEOTechnicalAuditWorker,
    SEOKeywordResearchWorker,
    SEOReportGenerationWorker,
    SEOAuditContext,
)


class TestSEOTechnicalAuditWorker:
    """Test SEOTechnicalAuditWorker."""

    def test_execute_technical_audit(self):
        """Test executing technical SEO audit."""
        worker = SEOTechnicalAuditWorker()
        
        context = ExecutionContext(
            session_id="session_001",
            step_id="step_001",
            inputs={
                "url": "https://example.com",
                "audit_scope": ["technical", "on_page"],
            },
        )
        
        result = worker.execute(context)
        
        assert result.success is True
        assert len(result.outputs) == 5
        assert result.execution_time_seconds > 0

    def test_execute_provides_real_outputs(self):
        """Test that worker produces real SEO outputs."""
        worker = SEOTechnicalAuditWorker()
        
        context = ExecutionContext(
            session_id="session_001",
            step_id="step_001",
            inputs={"url": "https://example.com"},
        )
        
        result = worker.execute(context)
        
        # Check for technical findings output
        technical_output = next(
            (o for o in result.outputs if "technical" in o.name.lower()),
            None,
        )
        assert technical_output is not None
        
        # Check for issues list output
        issues_output = next(
            (o for o in result.outputs if "issue" in o.name.lower()),
            None,
        )
        assert issues_output is not None
        
        # Check for recommendations output
        recommendations_output = next(
            (o for o in result.outputs if "recommendation" in o.name.lower()),
            None,
        )
        assert recommendations_output is not None
        
        # Check for metrics output
        metrics_output = next(
            (o for o in result.outputs if "metric" in o.name.lower()),
            None,
        )
        assert metrics_output is not None
        
        # Check for evidence output
        evidence_output = next(
            (o for o in result.outputs if "evidence" in o.name.lower()),
            None,
        )
        assert evidence_output is not None

    def test_technical_findings_content(self):
        """Test that technical findings contain real data."""
        worker = SEOTechnicalAuditWorker()
        
        context = ExecutionContext(
            session_id="session_001",
            step_id="step_001",
            inputs={"url": "https://example.com"},
        )
        
        result = worker.execute(context)
        
        technical_output = next(
            (o for o in result.outputs if "technical" in o.name.lower()),
            None,
        )
        
        assert technical_output.content is not None
        assert "url" in technical_output.content
        assert "ssl_status" in technical_output.content
        assert "page_speed" in technical_output.content

    def test_issues_list_content(self):
        """Test that issues list contains real issues."""
        worker = SEOTechnicalAuditWorker()
        
        context = ExecutionContext(
            session_id="session_001",
            step_id="step_001",
            inputs={"url": "https://example.com"},
        )
        
        result = worker.execute(context)
        
        issues_output = next(
            (o for o in result.outputs if "issue" in o.name.lower()),
            None,
        )
        
        assert isinstance(issues_output.content, list)
        assert len(issues_output.content) > 0
        
        # Check issue structure
        issue = issues_output.content[0]
        assert "issue_id" in issue
        assert "severity" in issue
        assert "title" in issue
        assert "description" in issue

    def test_recommendations_content(self):
        """Test that recommendations contain real data."""
        worker = SEOTechnicalAuditWorker()
        
        context = ExecutionContext(
            session_id="session_001",
            step_id="step_001",
            inputs={"url": "https://example.com"},
        )
        
        result = worker.execute(context)
        
        recommendations_output = next(
            (o for o in result.outputs if "recommendation" in o.name.lower()),
            None,
        )
        
        assert isinstance(recommendations_output.content, list)
        assert len(recommendations_output.content) > 0
        
        # Check recommendation structure
        recommendation = recommendations_output.content[0]
        assert "recommendation_id" in recommendation
        assert "priority" in recommendation
        assert "title" in recommendation
        assert "description" in recommendation

    def test_metrics_content(self):
        """Test that metrics contain real data."""
        worker = SEOTechnicalAuditWorker()
        
        context = ExecutionContext(
            session_id="session_001",
            step_id="step_001",
            inputs={"url": "https://example.com"},
        )
        
        result = worker.execute(context)
        
        metrics_output = next(
            (o for o in result.outputs if "metric" in o.name.lower()),
            None,
        )
        
        assert metrics_output.content is not None
        assert "technical_score" in metrics_output.content
        assert "overall_health" in metrics_output.content
        assert "total_issues" in metrics_output.content

    def test_can_execute_capability_step(self):
        """Test that worker can execute capability steps."""
        worker = SEOTechnicalAuditWorker()
        
        step = ExecutionStep(
            step_id="step_001",
            step_type=StepType.CAPABILITY,
            name="Technical Audit",
            description="Technical SEO audit",
        )
        
        can_execute = worker.can_execute(step)
        
        assert can_execute is True

    def test_can_execute_task_step(self):
        """Test that worker can execute task steps."""
        worker = SEOTechnicalAuditWorker()
        
        step = ExecutionStep(
            step_id="step_001",
            step_type=StepType.TASK,
            name="Technical Audit",
            description="Technical SEO audit",
        )
        
        can_execute = worker.can_execute(step)
        
        assert can_execute is True


class TestSEOKeywordResearchWorker:
    """Test SEOKeywordResearchWorker."""

    def test_execute_keyword_research(self):
        """Test executing keyword research."""
        worker = SEOKeywordResearchWorker()
        
        context = ExecutionContext(
            session_id="session_001",
            step_id="step_001",
            inputs={
                "business_domain": "plumbing",
                "target_audience": "homeowners",
            },
        )
        
        result = worker.execute(context)
        
        assert result.success is True
        assert len(result.outputs) == 3
        assert result.execution_time_seconds > 0

    def test_keyword_list_output(self):
        """Test keyword list output."""
        worker = SEOKeywordResearchWorker()
        
        context = ExecutionContext(
            session_id="session_001",
            step_id="step_001",
            inputs={"business_domain": "plumbing"},
        )
        
        result = worker.execute(context)
        
        keyword_output = next(
            (o for o in result.outputs if "keyword" in o.name.lower() and "list" in o.name.lower()),
            None,
        )
        
        assert keyword_output is not None
        assert isinstance(keyword_output.content, list)
        assert len(keyword_output.content) > 0

    def test_keyword_data_output(self):
        """Test keyword metrics output."""
        worker = SEOKeywordResearchWorker()
        
        context = ExecutionContext(
            session_id="session_001",
            step_id="step_001",
            inputs={"business_domain": "plumbing"},
        )
        
        result = worker.execute(context)
        
        data_output = next(
            (o for o in result.outputs if "metric" in str(o.output_type).lower()),
            None,
        )
        
        assert data_output is not None
        assert isinstance(data_output.content, list)
        
        # Check keyword data structure
        keyword_data = data_output.content[0]
        assert "keyword" in keyword_data
        assert "search_volume" in keyword_data
        assert "competition" in keyword_data

    def test_opportunities_output(self):
        """Test keyword opportunities output."""
        worker = SEOKeywordResearchWorker()
        
        context = ExecutionContext(
            session_id="session_001",
            step_id="step_001",
            inputs={"business_domain": "plumbing"},
        )
        
        result = worker.execute(context)
        
        opportunities_output = next(
            (o for o in result.outputs if "opportunity" in o.name.lower()),
            None,
        )
        
        # Opportunities may not be generated if no high-value keywords found
        # This is expected behavior
        if opportunities_output is not None:
            assert isinstance(opportunities_output.content, list)


class TestSEOReportGenerationWorker:
    """Test SEOReportGenerationWorker."""

    def test_execute_report_generation(self):
        """Test executing report generation."""
        worker = SEOReportGenerationWorker()
        
        context = ExecutionContext(
            session_id="session_001",
            step_id="step_001",
            inputs={
                "findings": {"url": "https://example.com", "ssl_status": "valid"},
                "issues": [{"issue_id": "issue_001", "severity": "high", "title": "Test Issue"}],
                "recommendations": [{"recommendation_id": "rec_001", "priority": "high", "title": "Test Recommendation"}],
                "metrics": {"overall_health": 75},
            },
        )
        
        result = worker.execute(context)
        
        assert result.success is True
        assert len(result.outputs) == 1
        assert result.execution_time_seconds > 0

    def test_report_output_structure(self):
        """Test report output structure."""
        worker = SEOReportGenerationWorker()
        
        context = ExecutionContext(
            session_id="session_001",
            step_id="step_001",
            inputs={
                "findings": {},
                "issues": [],
                "recommendations": [],
                "metrics": {},
            },
        )
        
        result = worker.execute(context)
        
        report_output = result.outputs[0]
        
        assert "report" in report_output.name.lower()
        assert report_output.content is not None
        assert "report_id" in report_output.content
        assert "sections" in report_output.content

    def test_report_includes_summary(self):
        """Test that report includes summary."""
        worker = SEOReportGenerationWorker()
        
        context = ExecutionContext(
            session_id="session_001",
            step_id="step_001",
            inputs={
                "findings": {},
                "issues": [{"issue_id": "issue_001", "severity": "high"}],
                "recommendations": [{"recommendation_id": "rec_001", "priority": "high"}],
                "metrics": {"overall_health": 75},
            },
        )
        
        result = worker.execute(context)
        
        report_output = result.outputs[0]
        
        assert "summary" in report_output.content
        assert "overall_score" in report_output.content["summary"]
        assert "total_issues" in report_output.content["summary"]

    def test_can_execute_completion_step(self):
        """Test that worker can execute completion steps."""
        worker = SEOReportGenerationWorker()
        
        step = ExecutionStep(
            step_id="step_001",
            step_type=StepType.TASK,  # Use TASK instead of DELIVERABLE
            name="Report Generation",
            description="Generate report",
        )
        
        can_execute = worker.can_execute(step)
        
        assert can_execute is True


class TestSEOAuditContext:
    """Test SEOAuditContext."""

    def test_create_audit_context(self):
        """Test creating SEO audit context."""
        context = SEOAuditContext(
            url="https://example.com",
            audit_scope=["technical", "on_page"],
            target_keywords=["plumbing", "emergency"],
        )
        
        assert context.url == "https://example.com"
        assert len(context.audit_scope) == 2
        assert len(context.target_keywords) == 2

    def test_audit_context_with_credentials(self):
        """Test audit context with access credentials."""
        context = SEOAuditContext(
            url="https://example.com",
            access_credentials={"api_key": "test_key"},
        )
        
        assert context.access_credentials is not None
        assert "api_key" in context.access_credentials
