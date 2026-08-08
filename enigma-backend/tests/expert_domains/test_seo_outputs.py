"""
Tests for SEO Output Builders module.

Tests SEO-specific output builders that produce real SEO outputs.
"""

import pytest

from app.execution.contracts import ExecutionStep, StepType, ExecutionOutput, OutputType
from app.expert_domains.domains.seo_outputs import (
    SEOAuditReportBuilder,
    SEOEvidenceBuilder,
    SEOKnowledgeBuilder,
    SEOCompositeOutputBuilder,
)


class TestSEOAuditReportBuilder:
    """Test SEOAuditReportBuilder."""

    def test_build_audit_report_outputs(self):
        """Test building SEO audit report outputs."""
        builder = SEOAuditReportBuilder()
        
        step = ExecutionStep(
            step_id="step_001",
            step_type=StepType.DELIVERABLE,
            name="Generate SEO Audit Report",
            description="Generate comprehensive SEO audit report",
        )
        
        execution_result = {
            "findings": {"url": "https://example.com", "ssl_status": "valid"},
            "issues": [
                {"issue_id": "issue_001", "severity": "high", "title": "Slow Page Speed"},
            ],
            "recommendations": [
                {"recommendation_id": "rec_001", "priority": "high", "title": "Optimize Page Speed"},
            ],
            "metrics": {"overall_health": 75},
        }
        
        context = {"session_id": "session_001", "url": "https://example.com"}
        
        outputs = builder.build_outputs(step, execution_result, context)
        
        assert len(outputs) >= 1
        
        # Check for main report
        report_output = next(
            (o for o in outputs if "audit_report" in o.output_id),
            None,
        )
        assert report_output is not None
        assert report_output.output_type == OutputType.REPORT

    def test_report_content_structure(self):
        """Test that report content has correct structure."""
        builder = SEOAuditReportBuilder()
        
        step = ExecutionStep(
            step_id="step_001",
            step_type=StepType.DELIVERABLE,
            name="Generate Report",
            description="Generate report",
        )
        
        execution_result = {
            "findings": {},
            "issues": [],
            "recommendations": [],
            "metrics": {},
        }
        
        context = {"session_id": "session_001"}
        
        outputs = builder.build_outputs(step, execution_result, context)
        
        report_output = next(
            (o for o in outputs if "audit_report" in o.output_id),
            None,
        )
        
        assert report_output.content is not None
        assert "report_id" in report_output.content
        assert "summary" in report_output.content
        assert "sections" in report_output.content

    def test_report_includes_findings_section(self):
        """Test that report includes findings section."""
        builder = SEOAuditReportBuilder()
        
        step = ExecutionStep(
            step_id="step_001",
            step_type=StepType.DELIVERABLE,
            name="Generate Report",
            description="Generate report",
        )
        
        execution_result = {
            "findings": {"ssl_status": "valid", "mobile_friendly": True},
            "issues": [],
            "recommendations": [],
            "metrics": {},
        }
        
        context = {"session_id": "session_001"}
        
        outputs = builder.build_outputs(step, execution_result, context)
        
        report_output = next(
            (o for o in outputs if "audit_report" in o.output_id),
            None,
        )
        
        sections = report_output.content.get("sections", [])
        findings_section = next(
            (s for s in sections if s.get("section_id") == "technical_analysis"),
            None,
        )
        assert findings_section is not None

    def test_report_includes_issues_section(self):
        """Test that report includes issues section."""
        builder = SEOAuditReportBuilder()
        
        step = ExecutionStep(
            step_id="step_001",
            step_type=StepType.DELIVERABLE,
            name="Generate Report",
            description="Generate report",
        )
        
        execution_result = {
            "findings": {},
            "issues": [{"issue_id": "issue_001", "severity": "high"}],
            "recommendations": [],
            "metrics": {},
        }
        
        context = {"session_id": "session_001"}
        
        outputs = builder.build_outputs(step, execution_result, context)
        
        report_output = next(
            (o for o in outputs if "audit_report" in o.output_id),
            None,
        )
        
        sections = report_output.content.get("sections", [])
        issues_section = next(
            (s for s in sections if s.get("section_id") == "issues_identified"),
            None,
        )
        assert issues_section is not None

    def test_report_includes_recommendations_section(self):
        """Test that report includes recommendations section."""
        builder = SEOAuditReportBuilder()
        
        step = ExecutionStep(
            step_id="step_001",
            step_type=StepType.DELIVERABLE,
            name="Generate Report",
            description="Generate report",
        )
        
        execution_result = {
            "findings": {},
            "issues": [],
            "recommendations": [{"recommendation_id": "rec_001", "priority": "high"}],
            "metrics": {},
        }
        
        context = {"session_id": "session_001"}
        
        outputs = builder.build_outputs(step, execution_result, context)
        
        report_output = next(
            (o for o in outputs if "audit_report" in o.output_id),
            None,
        )
        
        sections = report_output.content.get("sections", [])
        recommendations_section = next(
            (s for s in sections if s.get("section_id") == "recommendations"),
            None,
        )
        assert recommendations_section is not None


class TestSEOEvidenceBuilder:
    """Test SEOEvidenceBuilder."""

    def test_build_evidence_outputs(self):
        """Test building evidence outputs."""
        builder = SEOEvidenceBuilder()
        
        step = ExecutionStep(
            step_id="step_001",
            step_type=StepType.TASK,
            name="Collect Evidence",
            description="Collect SEO evidence",
        )
        
        execution_result = {
            "evidence": {
                "crawl_data": {"pages_crawled": 150},
                "performance_data": {"page_speed": 2.8},
            }
        }
        
        context = {"session_id": "session_001", "url": "https://example.com"}
        
        outputs = builder.build_outputs(step, execution_result, context)
        
        assert len(outputs) == 1
        assert outputs[0].output_type == OutputType.EVIDENCE

    def test_evidence_output_structure(self):
        """Test evidence output structure."""
        builder = SEOEvidenceBuilder()
        
        step = ExecutionStep(
            step_id="step_001",
            step_type=StepType.TASK,
            name="Collect Evidence",
            description="Collect SEO evidence",
        )
        
        execution_result = {
            "evidence": {"crawl_data": {"pages_crawled": 150}},
        }
        
        context = {"session_id": "session_001"}
        
        outputs = builder.build_outputs(step, execution_result, context)
        
        evidence_output = outputs[0]
        
        assert evidence_output.content is not None
        assert "evidence" in evidence_output.name.lower()
        assert "collection_timestamp" in evidence_output.metadata

    def test_no_evidence_without_data(self):
        """Test that no evidence is built without data."""
        builder = SEOEvidenceBuilder()
        
        step = ExecutionStep(
            step_id="step_001",
            step_type=StepType.TASK,
            name="Collect Evidence",
            description="Collect SEO evidence",
        )
        
        execution_result = {}
        context = {"session_id": "session_001"}
        
        outputs = builder.build_outputs(step, execution_result, context)
        
        assert len(outputs) == 0


class TestSEOKnowledgeBuilder:
    """Test SEOKnowledgeBuilder."""

    def test_build_knowledge_outputs(self):
        """Test building knowledge outputs."""
        builder = SEOKnowledgeBuilder()
        
        step = ExecutionStep(
            step_id="step_001",
            step_type=StepType.TASK,
            name="Generate Knowledge",
            description="Generate candidate knowledge",
        )
        
        execution_result = {
            "issues": [
                {"issue_id": "issue_001", "severity": "high", "title": "Critical Issue"},
            ],
            "recommendations": [
                {"recommendation_id": "rec_001", "priority": "high", "title": "Important Recommendation"},
            ],
        }
        
        context = {"session_id": "session_001"}
        
        outputs = builder.build_outputs(step, execution_result, context)
        
        assert len(outputs) >= 1
        assert outputs[0].output_type == OutputType.ARTIFACT

    def test_knowledge_output_structure(self):
        """Test knowledge output structure."""
        builder = SEOKnowledgeBuilder()
        
        step = ExecutionStep(
            step_id="step_001",
            step_type=StepType.TASK,
            name="Generate Knowledge",
            description="Generate candidate knowledge",
        )
        
        execution_result = {
            "issues": [{"issue_id": "issue_001", "severity": "high", "title": "Test Issue"}],
        }
        
        context = {"session_id": "session_001"}
        
        outputs = builder.build_outputs(step, execution_result, context)
        
        knowledge_output = outputs[0]
        
        assert knowledge_output.content is not None
        assert "candidate_knowledge" in knowledge_output.content

    def test_no_knowledge_without_issues(self):
        """Test that no knowledge is built without issues or recommendations."""
        builder = SEOKnowledgeBuilder()
        
        step = ExecutionStep(
            step_id="step_001",
            step_type=StepType.TASK,
            name="Generate Knowledge",
            description="Generate candidate knowledge",
        )
        
        execution_result = {}
        context = {"session_id": "session_001"}
        
        outputs = builder.build_outputs(step, execution_result, context)
        
        assert len(outputs) == 0


class TestSEOCompositeOutputBuilder:
    """Test SEOCompositeOutputBuilder."""

    def test_build_composite_outputs(self):
        """Test building composite outputs."""
        builder = SEOCompositeOutputBuilder()
        
        step = ExecutionStep(
            step_id="step_001",
            step_type=StepType.DELIVERABLE,
            name="Generate SEO Audit Report",
            description="Generate comprehensive SEO audit report",
        )
        
        execution_result = {
            "findings": {},
            "issues": [],
            "recommendations": [],
            "metrics": {},
            "evidence": {"crawl_data": {"pages_crawled": 150}},
        }
        
        context = {"session_id": "session_001", "url": "https://example.com"}
        
        outputs = builder.build_outputs(step, execution_result, context)
        
        # Should have report, evidence, and knowledge outputs
        assert len(outputs) >= 2

    def test_composite_includes_report_for_audit_steps(self):
        """Test that composite builder includes report for audit steps."""
        builder = SEOCompositeOutputBuilder()
        
        step = ExecutionStep(
            step_id="step_001",
            step_type=StepType.DELIVERABLE,
            name="SEO Audit Report",
            description="Generate SEO audit report",
        )
        
        execution_result = {
            "findings": {},
            "issues": [],
            "recommendations": [],
            "metrics": {},
        }
        
        context = {"session_id": "session_001"}
        
        outputs = builder.build_outputs(step, execution_result, context)
        
        report_output = next(
            (o for o in outputs if "report" in o.name.lower()),
            None,
        )
        assert report_output is not None

    def test_composite_includes_evidence(self):
        """Test that composite builder always includes evidence."""
        builder = SEOCompositeOutputBuilder()
        
        step = ExecutionStep(
            step_id="step_001",
            step_type=StepType.TASK,
            name="Test Step",
            description="Test step",
        )
        
        execution_result = {
            "evidence": {"test_data": "value"},
        }
        
        context = {"session_id": "session_001"}
        
        outputs = builder.build_outputs(step, execution_result, context)
        
        evidence_output = next(
            (o for o in outputs if o.output_type == OutputType.EVIDENCE),
            None,
        )
        assert evidence_output is not None

    def test_composite_includes_knowledge(self):
        """Test that composite builder includes knowledge."""
        builder = SEOCompositeOutputBuilder()
        
        step = ExecutionStep(
            step_id="step_001",
            step_type=StepType.TASK,
            name="Test Step",
            description="Test step",
        )
        
        execution_result = {
            "issues": [{"issue_id": "issue_001", "severity": "high"}],
        }
        
        context = {"session_id": "session_001"}
        
        outputs = builder.build_outputs(step, execution_result, context)
        
        knowledge_output = next(
            (o for o in outputs if "candidate" in o.name.lower()),
            None,
        )
        assert knowledge_output is not None
