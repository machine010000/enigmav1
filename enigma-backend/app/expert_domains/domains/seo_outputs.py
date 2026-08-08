from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid

from app.execution.contracts import ExecutionStep, ExecutionOutput, OutputType
from app.execution.outputs import BaseOutputBuilder


class SEOAuditReportBuilder:
    """
    Builder for SEO audit report outputs.
    
    Produces comprehensive SEO audit reports with findings, issues, and recommendations.
    """

    def build_outputs(
        self,
        step: ExecutionStep,
        execution_result: Any,
        context: Dict[str, Any],
    ) -> List[ExecutionOutput]:
        """Build SEO audit report outputs."""
        if isinstance(execution_result, dict):
            findings = execution_result.get("findings", {})
            issues = execution_result.get("issues", [])
            recommendations = execution_result.get("recommendations", [])
            metrics = execution_result.get("metrics", {})
        else:
            # Extract from execution result if it's an object
            findings = getattr(execution_result, "findings", {})
            issues = getattr(execution_result, "issues", [])
            recommendations = getattr(execution_result, "recommendations", [])
            metrics = getattr(execution_result, "metrics", {})

        outputs = []

        # Build comprehensive audit report
        report = self._build_audit_report(step, findings, issues, recommendations, metrics, context)
        outputs.append(report)

        # Build technical findings output
        if findings:
            technical_output = ExecutionOutput(
                output_id=f"technical_findings_{uuid.uuid4().hex[:8]}",
                step_id=step.step_id,
                session_id=context.get("session_id", ""),
                output_type=OutputType.REPORT,
                name="Technical SEO Findings",
                description="Detailed technical SEO analysis findings",
                content=findings,
                content_type="json",
                metadata={
                    "category": "technical",
                    "url": context.get("url", ""),
                },
            )
            outputs.append(technical_output)

        # Build issues list output
        if issues:
            issues_output = ExecutionOutput(
                output_id=f"issues_list_{uuid.uuid4().hex[:8]}",
                step_id=step.step_id,
                session_id=context.get("session_id", ""),
                output_type=OutputType.ARTIFACT,
                name="SEO Issues List",
                description="List of identified SEO issues with severity and priority",
                content=issues,
                content_type="json",
                metadata={
                    "total_issues": len(issues),
                    "critical_issues": len([i for i in issues if i.get("severity") == "high"]),
                },
            )
            outputs.append(issues_output)

        # Build recommendations output
        if recommendations:
            recommendations_output = ExecutionOutput(
                output_id=f"recommendations_{uuid.uuid4().hex[:8]}",
                step_id=step.step_id,
                session_id=context.get("session_id", ""),
                output_type=OutputType.RECOMMENDATION,
                name="SEO Recommendations",
                description="Prioritized SEO optimization recommendations",
                content=recommendations,
                content_type="json",
                metadata={
                    "total_recommendations": len(recommendations),
                    "high_priority": len([r for r in recommendations if r.get("priority") == "high"]),
                },
            )
            outputs.append(recommendations_output)

        # Build metrics output
        if metrics:
            metrics_output = ExecutionOutput(
                output_id=f"seo_metrics_{uuid.uuid4().hex[:8]}",
                step_id=step.step_id,
                session_id=context.get("session_id", ""),
                output_type=OutputType.METRIC,
                name="SEO Performance Metrics",
                description="Key SEO performance metrics and scores",
                content=metrics,
                content_type="json",
                metadata={
                    "overall_score": metrics.get("overall_health", 0),
                    "metric_count": len(metrics),
                },
            )
            outputs.append(metrics_output)

        return outputs

    def _build_audit_report(
        self,
        step: ExecutionStep,
        findings: Dict[str, Any],
        issues: List[Dict[str, Any]],
        recommendations: List[Dict[str, Any]],
        metrics: Dict[str, Any],
        context: Dict[str, Any],
    ) -> ExecutionOutput:
        """Build comprehensive SEO audit report."""
        report_content = {
            "report_id": f"seo_audit_report_{uuid.uuid4().hex[:8]}",
            "report_type": "comprehensive_seo_audit",
            "generated_at": datetime.utcnow().isoformat(),
            "url": context.get("url", "unknown"),
            "summary": {
                "overall_health_score": metrics.get("overall_health", 0),
                "total_issues": len(issues),
                "critical_issues": len([i for i in issues if i.get("severity") == "high"]),
                "medium_issues": len([i for i in issues if i.get("severity") == "medium"]),
                "low_issues": len([i for i in issues if i.get("severity") == "low"]),
                "total_recommendations": len(recommendations),
            },
            "executive_summary": self._generate_executive_summary(findings, issues, recommendations, metrics),
            "sections": [
                {
                    "section_id": "technical_analysis",
                    "title": "Technical SEO Analysis",
                    "content": findings,
                    "key_findings": self._extract_key_findings(findings),
                },
                {
                    "section_id": "issues_identified",
                    "title": "Identified Issues",
                    "content": issues,
                    "severity_breakdown": self._get_severity_breakdown(issues),
                },
                {
                    "section_id": "recommendations",
                    "title": "Optimization Recommendations",
                    "content": recommendations,
                    "priority_breakdown": self._get_priority_breakdown(recommendations),
                },
                {
                    "section_id": "performance_metrics",
                    "title": "Performance Metrics",
                    "content": metrics,
                },
            ],
        }

        return ExecutionOutput(
            output_id=f"audit_report_{uuid.uuid4().hex[:8]}",
            step_id=step.step_id,
            session_id=context.get("session_id", ""),
            output_type=OutputType.REPORT,
            name="Comprehensive SEO Audit Report",
            description="Complete SEO audit report with findings, issues, and recommendations",
            content=report_content,
            content_type="json",
            metadata={
                "report_type": "comprehensive",
                "sections": len(report_content["sections"]),
                "total_issues": len(issues),
                "total_recommendations": len(recommendations),
            },
        )

    def _generate_executive_summary(
        self,
        findings: Dict[str, Any],
        issues: List[Dict[str, Any]],
        recommendations: List[Dict[str, Any]],
        metrics: Dict[str, Any],
    ) -> str:
        """Generate executive summary for the report."""
        score = metrics.get("overall_health", 0)
        critical_count = len([i for i in issues if i.get("severity") == "high"])
        
        if score >= 80:
            health_status = "Good"
        elif score >= 60:
            health_status = "Fair"
        else:
            health_status = "Poor"
        
        summary = f"SEO audit completed with overall health score of {score}/100 ({health_status}). "
        summary += f"Found {len(issues)} total issues, including {critical_count} critical issues. "
        summary += f"Generated {len(recommendations)} prioritized recommendations for optimization."
        
        return summary

    def _extract_key_findings(self, findings: Dict[str, Any]) -> List[str]:
        """Extract key findings from technical analysis."""
        key_findings = []
        
        if findings.get("ssl_status") == "valid":
            key_findings.append("SSL certificate is properly configured")
        if findings.get("mobile_friendly"):
            key_findings.append("Website is mobile-friendly")
        if findings.get("page_speed", {}).get("desktop", 0) > 3:
            key_findings.append("Desktop page speed needs improvement")
        if findings.get("schema_markup") == "partial":
            key_findings.append("Schema markup is partially implemented")
        
        return key_findings

    def _get_severity_breakdown(self, issues: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get breakdown of issues by severity."""
        breakdown = {"high": 0, "medium": 0, "low": 0}
        for issue in issues:
            severity = issue.get("severity", "low")
            breakdown[severity] = breakdown.get(severity, 0) + 1
        return breakdown

    def _get_priority_breakdown(self, recommendations: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get breakdown of recommendations by priority."""
        breakdown = {"high": 0, "medium": 0, "low": 0}
        for rec in recommendations:
            priority = rec.get("priority", "low")
            breakdown[priority] = breakdown.get(priority, 0) + 1
        return breakdown


class SEOEvidenceBuilder:
    """
    Builder for SEO evidence outputs.
    
    Produces evidence collected during SEO execution for knowledge governance.
    """

    def build_outputs(
        self,
        step: ExecutionStep,
        execution_result: Any,
        context: Dict[str, Any],
    ) -> List[ExecutionOutput]:
        """Build SEO evidence outputs."""
        outputs = []

        # Extract evidence from execution result
        if isinstance(execution_result, dict):
            evidence_data = execution_result.get("evidence", {})
        else:
            evidence_data = getattr(execution_result, "evidence", {})

        if evidence_data:
            evidence_output = ExecutionOutput(
                output_id=f"seo_evidence_{uuid.uuid4().hex[:8]}",
                step_id=step.step_id,
                session_id=context.get("session_id", ""),
                output_type=OutputType.EVIDENCE,
                name="SEO Execution Evidence",
                description="Evidence collected during SEO execution",
                content=evidence_data,
                content_type="json",
                metadata={
                    "evidence_type": "seo_execution",
                    "collection_timestamp": datetime.utcnow().isoformat(),
                    "url": context.get("url", ""),
                },
            )
            outputs.append(evidence_output)

        return outputs


class SEOKnowledgeBuilder:
    """
    Builder for SEO knowledge outputs.
    
    Produces candidate knowledge from SEO execution for knowledge governance.
    """

    def build_outputs(
        self,
        step: ExecutionStep,
        execution_result: Any,
        context: Dict[str, Any],
    ) -> List[ExecutionOutput]:
        """Build SEO knowledge outputs."""
        outputs = []

        # Generate candidate knowledge from execution results
        candidate_knowledge = self._generate_candidate_knowledge(step, execution_result, context)

        if candidate_knowledge:
            knowledge_output = ExecutionOutput(
                output_id=f"candidate_knowledge_{uuid.uuid4().hex[:8]}",
                step_id=step.step_id,
                session_id=context.get("session_id", ""),
                output_type=OutputType.ARTIFACT,
                name="Candidate Knowledge",
                description="Candidate knowledge generated from SEO execution",
                content=candidate_knowledge,
                content_type="json",
                metadata={
                    "knowledge_type": "candidate",
                    "source": "seo_execution",
                    "step_id": step.step_id,
                },
            )
            outputs.append(knowledge_output)

        return outputs

    def _generate_candidate_knowledge(
        self,
        step: ExecutionStep,
        execution_result: Any,
        context: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """Generate candidate knowledge from execution results."""
        if isinstance(execution_result, dict):
            issues = execution_result.get("issues", [])
            recommendations = execution_result.get("recommendations", [])
        else:
            issues = getattr(execution_result, "issues", [])
            recommendations = getattr(execution_result, "recommendations", [])

        if not issues and not recommendations:
            return None

        # Generate knowledge from successful patterns
        knowledge_items = []

        for issue in issues:
            if issue.get("severity") == "high":
                knowledge_items.append({
                    "concept_id": f"seo_issue_{issue.get('issue_id', '')}",
                    "name": issue.get("title", ""),
                    "definition": f"SEO issue: {issue.get('description', '')}",
                    "evidence_source": "seo_audit",
                    "confidence": 0.8,
                    "metadata": {
                        "category": issue.get("category", ""),
                        "severity": issue.get("severity", ""),
                    },
                })

        for recommendation in recommendations:
            if recommendation.get("priority") == "high":
                knowledge_items.append({
                    "concept_id": f"seo_solution_{recommendation.get('recommendation_id', '')}",
                    "name": recommendation.get("title", ""),
                    "definition": f"SEO solution: {recommendation.get('description', '')}",
                    "evidence_source": "seo_audit",
                    "confidence": 0.75,
                    "metadata": {
                        "category": recommendation.get("category", ""),
                        "estimated_impact": recommendation.get("estimated_impact", ""),
                    },
                })

        return {
            "candidate_knowledge": knowledge_items,
            "source_execution": context.get("session_id", ""),
            "generated_at": datetime.utcnow().isoformat(),
        }


class SEOCompositeOutputBuilder:
    """
    Composite output builder for SEO domain.
    
    Combines multiple SEO-specific output builders.
    """

    def __init__(self) -> None:
        self._audit_report_builder = SEOAuditReportBuilder()
        self._evidence_builder = SEOEvidenceBuilder()
        self._knowledge_builder = SEOKnowledgeBuilder()

    def build_outputs(
        self,
        step: ExecutionStep,
        execution_result: Any,
        context: Dict[str, Any],
    ) -> List[ExecutionOutput]:
        """Build SEO outputs using all registered builders."""
        all_outputs = []

        # Use audit report builder for report-type steps
        if "report" in step.name.lower() or "audit" in step.name.lower():
            all_outputs.extend(self._audit_report_builder.build_outputs(step, execution_result, context))

        # Always try to build evidence
        all_outputs.extend(self._evidence_builder.build_outputs(step, execution_result, context))

        # Build knowledge for learning
        all_outputs.extend(self._knowledge_builder.build_outputs(step, execution_result, context))

        return all_outputs


# Default SEO output builder instance
seo_output_builder = SEOCompositeOutputBuilder()
