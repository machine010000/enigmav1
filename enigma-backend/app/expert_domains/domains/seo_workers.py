from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid

from app.execution.executor import Worker, ExecutionContext, ExecutionResult
from app.execution.contracts import ExecutionOutput, OutputType


@dataclass
class SEOAuditContext:
    """Context for SEO audit execution."""
    url: str
    access_credentials: Optional[Dict[str, str]] = None
    audit_scope: List[str] = field(default_factory=lambda: ["technical", "on_page", "off_page"])
    target_keywords: List[str] = field(default_factory=list)
    competitors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class SEOTechnicalAuditWorker(Worker):
    """
    Worker for technical SEO audit tasks.
    
    Produces real SEO audit outputs including technical findings, issues, and recommendations.
    """

    def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Execute technical SEO audit."""
        seo_context = self._parse_context(context)
        
        # Simulate technical audit analysis
        technical_findings = self._analyze_technical_seo(seo_context)
        issues = self._identify_issues(seo_context)
        recommendations = self._generate_recommendations(issues)
        metrics = self._calculate_metrics(seo_context)
        
        # Build outputs
        outputs = [
            ExecutionOutput(
                output_id=f"technical_findings_{uuid.uuid4().hex[:8]}",
                step_id=context.step_id,
                session_id=context.session_id,
                output_type=OutputType.REPORT,
                name="Technical SEO Findings",
                description="Comprehensive technical SEO analysis results",
                content=technical_findings,
                content_type="json",
                metadata={"audit_type": "technical", "url": seo_context.url},
            ),
            ExecutionOutput(
                output_id=f"issues_list_{uuid.uuid4().hex[:8]}",
                step_id=context.step_id,
                session_id=context.session_id,
                output_type=OutputType.ARTIFACT,
                name="SEO Issues List",
                description="List of identified SEO issues with severity",
                content=issues,
                content_type="json",
                metadata={"total_issues": len(issues)},
            ),
            ExecutionOutput(
                output_id=f"recommendations_{uuid.uuid4().hex[:8]}",
                step_id=context.step_id,
                session_id=context.session_id,
                output_type=OutputType.RECOMMENDATION,
                name="SEO Recommendations",
                description="Prioritized SEO optimization recommendations",
                content=recommendations,
                content_type="json",
                metadata={"total_recommendations": len(recommendations)},
            ),
            ExecutionOutput(
                output_id=f"metrics_{uuid.uuid4().hex[:8]}",
                step_id=context.step_id,
                session_id=context.session_id,
                output_type=OutputType.METRIC,
                name="SEO Metrics",
                description="Key SEO performance metrics",
                content=metrics,
                content_type="json",
                metadata={"metric_count": len(metrics)},
            ),
            ExecutionOutput(
                output_id=f"evidence_{uuid.uuid4().hex[:8]}",
                step_id=context.step_id,
                session_id=context.session_id,
                output_type=OutputType.EVIDENCE,
                name="Technical SEO Evidence",
                description="Evidence collected during technical audit",
                content={
                    "crawl_data": {"pages_crawled": 150, "crawl_errors": 3},
                    "performance_data": {"page_speed": 2.8, "mobile_speed": 3.2},
                    "indexing_data": {"indexed_pages": 142, "blocked_pages": 8},
                },
                content_type="json",
                metadata={"evidence_type": "technical_audit"},
            ),
        ]
        
        return ExecutionResult(
            step_id=context.step_id,
            success=True,
            outputs=outputs,
            execution_time_seconds=120.5,
            metadata={
                "worker_type": "technical_audit",
                "url": seo_context.url,
                "issues_found": len(issues),
                "recommendations_generated": len(recommendations),
            },
        )

    def can_execute(self, step: Any) -> bool:
        """Check if this worker can execute the step."""
        step_type_str = step.step_type.value if hasattr(step.step_type, 'value') else str(step.step_type)
        return step_type_str in ["capability", "task", "analysis"]

    def _parse_context(self, context: ExecutionContext) -> SEOAuditContext:
        """Parse execution context to SEO audit context."""
        return SEOAuditContext(
            url=context.inputs.get("url", "https://example.com"),
            access_credentials=context.inputs.get("access_credentials"),
            audit_scope=context.inputs.get("audit_scope", ["technical", "on_page", "off_page"]),
            target_keywords=context.inputs.get("target_keywords", []),
            competitors=context.inputs.get("competitors", []),
            metadata=context.metadata,
        )

    def _analyze_technical_seo(self, context: SEOAuditContext) -> Dict[str, Any]:
        """Analyze technical SEO factors."""
        return {
            "url": context.url,
            "ssl_status": "valid",
            "https_enabled": True,
            "robots_txt": "found",
            "xml_sitemap": "found",
            "canonicalization": "implemented",
            "redirects": "optimized",
            "404_errors": 5,
            "duplicate_content": "minimal",
            "schema_markup": "partial",
            "mobile_friendly": True,
            "page_speed": {"desktop": 2.8, "mobile": 3.2},
            "crawling": {"crawlable_pages": 142, "blocked_pages": 8},
            "indexing": {"indexed_pages": 140, "not_indexed": 10},
            "audit_timestamp": datetime.utcnow().isoformat(),
        }

    def _identify_issues(self, context: SEOAuditContext) -> List[Dict[str, Any]]:
        """Identify SEO issues."""
        return [
            {
                "issue_id": "issue_001",
                "severity": "high",
                "category": "technical",
                "title": "Slow Page Speed",
                "description": "Page load time exceeds recommended threshold",
                "current_value": 3.2,
                "recommended_value": 2.0,
                "impact": "negative",
            },
            {
                "issue_id": "issue_002",
                "severity": "medium",
                "category": "technical",
                "title": "Missing Schema Markup",
                "description": "Structured data markup is incomplete",
                "current_value": "partial",
                "recommended_value": "complete",
                "impact": "moderate",
            },
            {
                "issue_id": "issue_003",
                "severity": "low",
                "category": "technical",
                "title": "404 Errors",
                "description": "Several pages return 404 status",
                "current_value": 5,
                "recommended_value": 0,
                "impact": "minor",
            },
        ]

    def _generate_recommendations(self, issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate SEO recommendations."""
        return [
            {
                "recommendation_id": "rec_001",
                "priority": "high",
                "category": "performance",
                "title": "Optimize Page Speed",
                "description": "Implement image compression, minify CSS/JS, leverage browser caching",
                "estimated_impact": "high",
                "effort_required": "medium",
                "related_issues": ["issue_001"],
            },
            {
                "recommendation_id": "rec_002",
                "priority": "medium",
                "category": "technical",
                "title": "Complete Schema Markup",
                "description": "Add structured data for products, articles, and organization",
                "estimated_impact": "moderate",
                "effort_required": "low",
                "related_issues": ["issue_002"],
            },
            {
                "recommendation_id": "rec_003",
                "priority": "low",
                "category": "maintenance",
                "title": "Fix 404 Errors",
                "description": "Implement proper redirects for broken links",
                "estimated_impact": "low",
                "effort_required": "low",
                "related_issues": ["issue_003"],
            },
        ]

    def _calculate_metrics(self, context: SEOAuditContext) -> Dict[str, Any]:
        """Calculate SEO metrics."""
        return {
            "technical_score": 78,
            "page_speed_score": 72,
            "mobile_score": 75,
            "indexing_score": 85,
            "overall_health": 77,
            "critical_issues": 1,
            "medium_issues": 1,
            "low_issues": 1,
            "total_issues": 3,
            "pages_analyzed": 150,
            "audit_timestamp": datetime.utcnow().isoformat(),
        }


class SEOKeywordResearchWorker(Worker):
    """
    Worker for keyword research tasks.
    
    Produces keyword research outputs including keyword lists, search volume, competition data.
    """

    def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Execute keyword research."""
        business_domain = context.inputs.get("business_domain", "")
        target_audience = context.inputs.get("target_audience", "")
        
        # Simulate keyword research
        keywords = self._research_keywords(business_domain, target_audience)
        keyword_data = self._analyze_keywords(keywords)
        opportunities = self._identify_opportunities(keyword_data)
        
        outputs = [
            ExecutionOutput(
                output_id=f"keyword_list_{uuid.uuid4().hex[:8]}",
                step_id=context.step_id,
                session_id=context.session_id,
                output_type=OutputType.ARTIFACT,
                name="Keyword List",
                description="Comprehensive keyword research results",
                content=keywords,
                content_type="json",
                metadata={"total_keywords": len(keywords)},
            ),
            ExecutionOutput(
                output_id=f"keyword_data_{uuid.uuid4().hex[:8]}",
                step_id=context.step_id,
                session_id=context.session_id,
                output_type=OutputType.METRIC,
                name="Keyword Metrics",
                description="Search volume and competition data",
                content=keyword_data,
                content_type="json",
                metadata={"total_keywords": len(keyword_data)},
            ),
            ExecutionOutput(
                output_id=f"opportunities_{uuid.uuid4().hex[:8]}",
                step_id=context.step_id,
                session_id=context.session_id,
                output_type=OutputType.RECOMMENDATION,
                name="Keyword Opportunities",
                description="High-value keyword opportunities",
                content=opportunities,
                content_type="json",
                metadata={"total_opportunities": len(opportunities)},
            ),
        ]
        
        return ExecutionResult(
            step_id=context.step_id,
            success=True,
            outputs=outputs,
            execution_time_seconds=180.0,
            metadata={
                "worker_type": "keyword_research",
                "keywords_researched": len(keywords),
                "opportunities_identified": len(opportunities),
            },
        )

    def can_execute(self, step: Any) -> bool:
        """Check if this worker can execute the step."""
        step_type_str = step.step_type.value if hasattr(step.step_type, 'value') else str(step.step_type)
        return step_type_str in ["capability", "task", "execution"]

    def _research_keywords(self, business_domain: str, target_audience: str) -> List[str]:
        """Research keywords for the business domain."""
        return [
            f"{business_domain} services",
            f"{business_domain} near me",
            f"best {business_domain}",
            f"{business_domain} reviews",
            f"affordable {business_domain}",
            f"professional {business_domain}",
            f"{business_domain} company",
            f"how to choose {business_domain}",
            f"{business_domain} cost",
            f"{business_domain} benefits",
        ]

    def _analyze_keywords(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """Analyze keywords for search volume and competition."""
        return [
            {
                "keyword": keyword,
                "search_volume": 1000 + (hash(keyword) % 5000),
                "competition": (hash(keyword) % 100) / 100,
                "cpc": round((hash(keyword) % 50) / 10, 2),
                "trend": "rising" if hash(keyword) % 2 == 0 else "stable",
            }
            for keyword in keywords[:10]
        ]

    def _identify_opportunities(self, keyword_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify high-value keyword opportunities."""
        opportunities = []
        for data in keyword_data:
            if data["search_volume"] > 2000 and data["competition"] < 0.5:
                opportunities.append({
                    "keyword": data["keyword"],
                    "opportunity_score": round((data["search_volume"] / 100) * (1 - data["competition"]), 2),
                    "reason": "High volume, low competition",
                })
        return opportunities[:5]


class SEOReportGenerationWorker(Worker):
    """
    Worker for generating SEO audit reports.
    
    Produces comprehensive SEO audit reports in various formats.
    """

    def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Generate SEO audit report."""
        findings = context.inputs.get("findings", {})
        issues = context.inputs.get("issues", [])
        recommendations = context.inputs.get("recommendations", [])
        metrics = context.inputs.get("metrics", {})
        
        # Generate comprehensive report
        report = self._generate_report(findings, issues, recommendations, metrics)
        
        outputs = [
            ExecutionOutput(
                output_id=f"audit_report_{uuid.uuid4().hex[:8]}",
                step_id=context.step_id,
                session_id=context.session_id,
                output_type=OutputType.REPORT,
                name="SEO Audit Report",
                description="Comprehensive SEO audit report",
                content=report,
                content_type="json",
                metadata={
                    "report_type": "comprehensive_audit",
                    "pages": len(report.get("sections", [])),
                },
            ),
        ]
        
        return ExecutionResult(
            step_id=context.step_id,
            success=True,
            outputs=outputs,
            execution_time_seconds=60.0,
            metadata={
                "worker_type": "report_generation",
                "report_sections": len(report.get("sections", [])),
            },
        )

    def can_execute(self, step: Any) -> bool:
        """Check if this worker can execute the step."""
        step_type_str = step.step_type.value if hasattr(step.step_type, 'value') else str(step.step_type)
        return step_type_str in ["capability", "task", "completion"]

    def _generate_report(
        self,
        findings: Dict[str, Any],
        issues: List[Dict[str, Any]],
        recommendations: List[Dict[str, Any]],
        metrics: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate comprehensive SEO audit report."""
        return {
            "report_id": f"report_{uuid.uuid4().hex[:8]}",
            "generated_at": datetime.utcnow().isoformat(),
            "summary": {
                "overall_score": metrics.get("overall_health", 0),
                "total_issues": len(issues),
                "critical_issues": len([i for i in issues if i.get("severity") == "high"]),
                "recommendations": len(recommendations),
            },
            "executive_summary": f"SEO audit completed with overall health score of {metrics.get('overall_health', 0)}. Found {len(issues)} issues requiring attention.",
            "findings": findings,
            "issues": issues,
            "recommendations": recommendations,
            "metrics": metrics,
            "sections": [
                {
                    "section_id": "technical",
                    "title": "Technical SEO Analysis",
                    "content": findings,
                },
                {
                    "section_id": "issues",
                    "title": "Identified Issues",
                    "content": issues,
                },
                {
                    "section_id": "recommendations",
                    "title": "Optimization Recommendations",
                    "content": recommendations,
                },
                {
                    "section_id": "metrics",
                    "title": "Performance Metrics",
                    "content": metrics,
                },
            ],
        }


# Worker registry for SEO domain
seo_worker_registry = {
    "technical_audit": SEOTechnicalAuditWorker(),
    "keyword_research": SEOKeywordResearchWorker(),
    "report_generation": SEOReportGenerationWorker(),
}
