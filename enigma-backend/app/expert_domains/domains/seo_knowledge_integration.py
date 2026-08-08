from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid

from app.execution.contracts import ExecutionOutput, OutputType
from app.knowledge_governance.models import CandidateKnowledge, Evidence
from app.knowledge_governance.contracts import KnowledgeGovernanceService


@dataclass
class KnowledgeUpdateResult:
    """Result of knowledge update operation."""
    success: bool
    candidates_submitted: int
    candidates_accepted: int
    candidates_rejected: int
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class SEOKnowledgeIntegration:
    """
    Integration for updating SEO knowledge from execution outputs.
    
    Takes execution outputs and converts them to candidate knowledge
    for submission through the knowledge governance service.
    """

    def __init__(self, governance_service: Optional[KnowledgeGovernanceService] = None) -> None:
        self._governance_service = governance_service

    def set_governance_service(self, service: KnowledgeGovernanceService) -> None:
        """Set the knowledge governance service."""
        self._governance_service = service

    def update_knowledge_from_outputs(
        self,
        outputs: List[ExecutionOutput],
        session_id: str,
        domain_id: str = "seo",
    ) -> KnowledgeUpdateResult:
        """
        Update knowledge from execution outputs.
        
        Args:
            outputs: List of execution outputs
            session_id: Execution session ID
            domain_id: Domain ID for the knowledge
            
        Returns:
            KnowledgeUpdateResult with submission statistics
        """
        result = KnowledgeUpdateResult(
            success=True,
            candidates_submitted=0,
            candidates_accepted=0,
            candidates_rejected=0,
        )

        if not self._governance_service:
            result.success = False
            result.errors.append("Knowledge governance service not configured")
            return result

        # Extract candidate knowledge from outputs
        candidates = self._extract_candidate_knowledge(outputs, session_id, domain_id)

        for candidate in candidates:
            try:
                governed = self._governance_service.submit_candidate(candidate, actor="seo_execution")
                result.candidates_submitted += 1
                if governed.status == "accepted":
                    result.candidates_accepted += 1
                else:
                    result.candidates_rejected += 1
            except Exception as e:
                result.errors.append(f"Failed to submit candidate: {str(e)}")

        result.metadata = {
            "session_id": session_id,
            "domain_id": domain_id,
            "timestamp": datetime.utcnow().isoformat(),
        }

        return result

    def _extract_candidate_knowledge(
        self,
        outputs: List[ExecutionOutput],
        session_id: str,
        domain_id: str,
    ) -> List[CandidateKnowledge]:
        """Extract candidate knowledge from execution outputs."""
        candidates = []

        for output in outputs:
            # Process candidate knowledge outputs
            if output.output_type == OutputType.ARTIFACT and "candidate_knowledge" in str(output.name).lower():
                candidates.extend(self._parse_candidate_knowledge_output(output, session_id, domain_id))

            # Process evidence outputs as knowledge sources
            if output.output_type == OutputType.EVIDENCE:
                candidates.extend(self._convert_evidence_to_knowledge(output, session_id, domain_id))

            # Process report outputs for patterns
            if output.output_type == OutputType.REPORT:
                candidates.extend(self._extract_patterns_from_report(output, session_id, domain_id))

        return candidates

    def _parse_candidate_knowledge_output(
        self,
        output: ExecutionOutput,
        session_id: str,
        domain_id: str,
    ) -> List[CandidateKnowledge]:
        """Parse candidate knowledge from output."""
        candidates = []

        if not isinstance(output.content, dict):
            return candidates

        knowledge_items = output.content.get("candidate_knowledge", [])

        for item in knowledge_items:
            candidate = CandidateKnowledge(
                candidate_id=f"candidate_{uuid.uuid4().hex[:8]}",
                concept_id=item.get("concept_id", f"concept_{uuid.uuid4().hex[:8]}"),
                domain_id=domain_id,
                definition=item.get("definition", ""),
                evidence_sources=[item.get("evidence_source", "seo_execution")],
                confidence=item.get("confidence", 0.7),
                source=f"seo_execution_{session_id}",
                metadata={
                    "session_id": session_id,
                    "step_id": output.step_id,
                    "category": item.get("category", ""),
                    **item.get("metadata", {}),
                },
            )
            candidates.append(candidate)

        return candidates

    def _convert_evidence_to_knowledge(
        self,
        output: ExecutionOutput,
        session_id: str,
        domain_id: str,
    ) -> List[CandidateKnowledge]:
        """Convert evidence output to candidate knowledge."""
        candidates = []

        if not isinstance(output.content, dict):
            return candidates

        # Extract patterns from evidence
        evidence_data = output.content

        # Create candidate knowledge from evidence patterns
        if "crawl_data" in evidence_data:
            candidate = CandidateKnowledge(
                candidate_id=f"candidate_{uuid.uuid4().hex[:8]}",
                concept_id="technical_crawl_pattern",
                domain_id=domain_id,
                definition="Pattern for technical SEO crawling and data collection",
                evidence_sources=["seo_execution"],
                confidence=0.75,
                source=f"seo_execution_{session_id}",
                metadata={
                    "session_id": session_id,
                    "evidence_type": "crawl_data",
                    "pages_crawled": evidence_data.get("crawl_data", {}).get("pages_crawled", 0),
                },
            )
            candidates.append(candidate)

        if "performance_data" in evidence_data:
            candidate = CandidateKnowledge(
                candidate_id=f"candidate_{uuid.uuid4().hex[:8]}",
                concept_id="performance_optimization_pattern",
                domain_id=domain_id,
                definition="Pattern for performance optimization based on SEO metrics",
                evidence_sources=["seo_execution"],
                confidence=0.8,
                source=f"seo_execution_{session_id}",
                metadata={
                    "session_id": session_id,
                    "evidence_type": "performance_data",
                    "page_speed": evidence_data.get("performance_data", {}).get("page_speed", 0),
                },
            )
            candidates.append(candidate)

        return candidates

    def _extract_patterns_from_report(
        self,
        output: ExecutionOutput,
        session_id: str,
        domain_id: str,
    ) -> List[CandidateKnowledge]:
        """Extract patterns from report output."""
        candidates = []

        if not isinstance(output.content, dict):
            return candidates

        report_content = output.content

        # Extract patterns from findings
        findings = report_content.get("findings", {})
        if findings:
            candidate = CandidateKnowledge(
                candidate_id=f"candidate_{uuid.uuid4().hex[:8]}",
                concept_id="technical_seo_analysis_pattern",
                domain_id=domain_id,
                definition=f"Technical SEO analysis pattern based on {findings.get('url', 'unknown')}",
                evidence_sources=["seo_execution"],
                confidence=0.7,
                source=f"seo_execution_{session_id}",
                metadata={
                    "session_id": session_id,
                    "report_type": "technical_analysis",
                    "ssl_status": findings.get("ssl_status"),
                    "mobile_friendly": findings.get("mobile_friendly"),
                },
            )
            candidates.append(candidate)

        # Extract patterns from recommendations
        recommendations = report_content.get("recommendations", [])
        for rec in recommendations:
            if rec.get("priority") == "high":
                candidate = CandidateKnowledge(
                    candidate_id=f"candidate_{uuid.uuid4().hex[:8]}",
                    concept_id=f"seo_solution_{rec.get('recommendation_id', '')}",
                    domain_id=domain_id,
                    definition=f"SEO solution pattern: {rec.get('title', '')}",
                    evidence_sources=["seo_execution"],
                    confidence=0.75,
                    source=f"seo_execution_{session_id}",
                    metadata={
                        "session_id": session_id,
                        "category": rec.get("category", ""),
                        "estimated_impact": rec.get("estimated_impact", ""),
                    },
                )
                candidates.append(candidate)

        return candidates


class SEOEvidenceIntegration:
    """
    Integration for updating SEO evidence from execution outputs.
    
    Takes execution outputs and converts them to evidence
    for submission through the evidence registry.
    """

    def __init__(self) -> None:
        self._evidence_registry: Dict[str, Evidence] = {}

    def register_evidence(
        self,
        outputs: List[ExecutionOutput],
        session_id: str,
        domain_id: str = "seo",
    ) -> Dict[str, Any]:
        """
        Register evidence from execution outputs.
        
        Args:
            outputs: List of execution outputs
            session_id: Execution session ID
            domain_id: Domain ID for the evidence
            
        Returns:
            Registration result with statistics
        """
        result = {
            "success": True,
            "evidence_registered": 0,
            "evidence_ids": [],
            "errors": [],
        }

        for output in outputs:
            if output.output_type == OutputType.EVIDENCE:
                try:
                    evidence = self._convert_output_to_evidence(output, session_id, domain_id)
                    evidence_id = evidence.evidence_id
                    self._evidence_registry[evidence_id] = evidence
                    result["evidence_registered"] += 1
                    result["evidence_ids"].append(evidence_id)
                except Exception as e:
                    result["errors"].append(f"Failed to register evidence: {str(e)}")

        return result

    def _convert_output_to_evidence(
        self,
        output: ExecutionOutput,
        session_id: str,
        domain_id: str,
    ) -> Evidence:
        """Convert execution output to evidence."""
        evidence_id = f"evidence_{uuid.uuid4().hex[:8]}"

        return Evidence(
            evidence_id=evidence_id,
            concept_id=output.metadata.get("concept_id", f"concept_{uuid.uuid4().hex[:8]}"),
            domain_id=domain_id,
            source_type="seo_execution",
            source_url=output.metadata.get("url", ""),
            content=output.content,
            collected_at=datetime.utcnow(),
            metadata={
                "session_id": session_id,
                "step_id": output.step_id,
                "output_id": output.output_id,
                "evidence_type": output.metadata.get("evidence_type", "general"),
                **output.metadata,
            },
        )

    def get_evidence(self, evidence_id: str) -> Optional[Evidence]:
        """Get evidence by ID."""
        return self._evidence_registry.get(evidence_id)

    def list_evidence(self, session_id: Optional[str] = None) -> List[Evidence]:
        """List evidence, optionally filtered by session."""
        if session_id:
            return [
                e for e in self._evidence_registry.values()
                if e.metadata.get("session_id") == session_id
            ]
        return list(self._evidence_registry.values())


class SEOReadinessIntegration:
    """
    Integration for updating SEO readiness from execution results.
    
    Updates knowledge readiness, evidence readiness, execution readiness,
    and overall readiness based on execution outcomes.
    """

    def __init__(self) -> None:
        self._readiness_scores: Dict[str, Dict[str, float]] = {}

    def update_readiness(
        self,
        session_id: str,
        domain_id: str = "seo",
        execution_success: bool = True,
        quality_score: float = 0.8,
        evidence_collected: int = 0,
        knowledge_generated: int = 0,
    ) -> Dict[str, Any]:
        """
        Update readiness scores based on execution results.
        
        Args:
            session_id: Execution session ID
            domain_id: Domain ID
            execution_success: Whether execution was successful
            quality_score: Quality score of execution (0-1)
            evidence_collected: Number of evidence items collected
            knowledge_generated: Number of knowledge items generated
            
        Returns:
            Updated readiness scores
        """
        # Calculate readiness components
        execution_readiness = self._calculate_execution_readiness(execution_success, quality_score)
        evidence_readiness = self._calculate_evidence_readiness(evidence_collected)
        knowledge_readiness = self._calculate_knowledge_readiness(knowledge_generated)
        overall_readiness = (execution_readiness + evidence_readiness + knowledge_readiness) / 3

        readiness = {
            "execution_readiness": execution_readiness,
            "evidence_readiness": evidence_readiness,
            "knowledge_readiness": knowledge_readiness,
            "overall_readiness": overall_readiness,
            "session_id": session_id,
            "domain_id": domain_id,
            "updated_at": datetime.utcnow().isoformat(),
        }

        # Store readiness scores
        key = f"{domain_id}_{session_id}"
        self._readiness_scores[key] = readiness

        return readiness

    def _calculate_execution_readiness(self, success: bool, quality_score: float) -> float:
        """Calculate execution readiness."""
        if not success:
            return max(0.0, quality_score - 0.2)
        return min(1.0, quality_score + 0.1)

    def _calculate_evidence_readiness(self, evidence_count: int) -> float:
        """Calculate evidence readiness."""
        # More evidence = higher readiness (capped at 1.0)
        return min(1.0, 0.5 + (evidence_count * 0.1))

    def _calculate_knowledge_readiness(self, knowledge_count: int) -> float:
        """Calculate knowledge readiness."""
        # More knowledge = higher readiness (capped at 1.0)
        return min(1.0, 0.5 + (knowledge_count * 0.15))

    def get_readiness(self, domain_id: str, session_id: str) -> Optional[Dict[str, Any]]:
        """Get readiness scores for a session."""
        key = f"{domain_id}_{session_id}"
        return self._readiness_scores.get(key)

    def get_latest_readiness(self, domain_id: str) -> Optional[Dict[str, Any]]:
        """Get latest readiness scores for a domain."""
        domain_scores = {
            k: v for k, v in self._readiness_scores.items()
            if k.startswith(f"{domain_id}_")
        }
        if not domain_scores:
            return None
        # Return the most recent (last in dict)
        return list(domain_scores.values())[-1]


# Default integration instances
seo_knowledge_integration = SEOKnowledgeIntegration()
seo_evidence_integration = SEOEvidenceIntegration()
seo_readiness_integration = SEOReadinessIntegration()
