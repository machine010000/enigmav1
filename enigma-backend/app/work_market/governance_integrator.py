from __future__ import annotations

from typing import Optional

from app.work_market.models import FreelanceJob


class KnowledgeGovernanceIntegrator:
    """Integrates job knowledge with the Knowledge Governance Layer."""

    def convert_job_to_candidate_knowledge(self, job: FreelanceJob) -> Optional[object]:
        """Convert job knowledge to CandidateKnowledge for governance."""
        try:
            from app.knowledge_governance import CandidateKnowledge, Evidence, SourceType
            from datetime import datetime
        except ImportError:
            return None

        # Convert job skills to evidence
        evidence_list = []
        for skill in job.skills:
            evidence = Evidence(
                id=f"job-{job.job_id}-skill-{skill}",
                source=job.source.value,
                source_type=SourceType.EXTERNAL_SOURCE,
                claim=f"Job requires {skill} skill",
                retrieved_at=datetime.utcnow(),
                quality_score=0.7,  # Job postings have moderate quality
                confidence=0.7,
            )
            evidence_list.append(evidence)

        # Create CandidateKnowledge from job
        return CandidateKnowledge(
            id=f"job-{job.job_id}",
            name=job.title,
            definition=f"Freelance job: {job.description}",
            evidence=evidence_list,
            source="job_market",
            submitted_at=datetime.utcnow(),
        )

    def submit_job_knowledge_to_governance(self, candidate: object) -> Optional[object]:
        """Submit job knowledge through governance."""
        try:
            from app.knowledge_governance import knowledge_governance_service
        except ImportError:
            return None

        governed = knowledge_governance_service.submit_candidate(candidate, actor="work_market")
        return governed
