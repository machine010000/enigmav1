from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class ProposalStrategyType(str, Enum):
    """Types of proposal strategies."""
    DIRECT = "direct"
    VALUE_FOCUSED = "value_focused"
    PROBLEM_SOLUTION = "problem_solution"
    COMPETITIVE = "competitive"
    CONSULTATIVE = "consultative"


class ProposalTone(str, Enum):
    """Tone for the proposal."""
    PROFESSIONAL = "professional"
    FRIENDLY = "friendly"
    TECHNICAL = "technical"
    BUSINESS_FOCUSED = "business_focused"


@dataclass
class CapabilityClaim:
    """A capability claim backed by evidence."""
    capability_id: str
    capability_name: str
    claim: str
    evidence_ids: List[str] = field(default_factory=list)
    confidence: float = 0.0
    provenance: str = ""
    is_fabricated: bool = False


@dataclass
class ClientRequirement:
    """Extracted client requirement."""
    requirement_id: str
    description: str
    priority: str  # "critical", "high", "medium", "low"
    category: str  # "technical", "business", "timeline", "budget"
    source_text: str = ""


@dataclass
class Deliverable:
    """A deliverable for the job."""
    deliverable_id: str
    name: str
    description: str
    estimated_hours: float = 0.0
    dependencies: List[str] = field(default_factory=list)
    acceptance_criteria: List[str] = field(default_factory=list)


@dataclass
class Risk:
    """A risk identified for the project."""
    risk_id: str
    description: str
    likelihood: str  # "low", "medium", "high"
    impact: str  # "low", "medium", "high"
    mitigation: str = ""


@dataclass
class Assumption:
    """An assumption made for the proposal."""
    assumption_id: str
    description: str
    category: str  # "technical", "business", "scope", "timeline"


@dataclass
class ClientQuestion:
    """A question for the client."""
    question_id: str
    question: str
    category: str  # "clarification", "scope", "timeline", "budget", "technical"
    priority: str  # "critical", "high", "medium", "low"


@dataclass
class ProposalStrategy:
    """Strategy for creating a proposal."""
    strategy_id: str
    job_id: str
    strategy_type: ProposalStrategyType
    tone: ProposalTone
    key_selling_points: List[str] = field(default_factory=list)
    client_requirements: List[ClientRequirement] = field(default_factory=list)
    capability_claims: List[CapabilityClaim] = field(default_factory=list)
    deliverables: List[Deliverable] = field(default_factory=list)
    risks: List[Risk] = field(default_factory=list)
    assumptions: List[Assumption] = field(default_factory=list)
    client_questions: List[ClientQuestion] = field(default_factory=list)
    estimated_timeline_days: int = 0
    estimated_budget: float = 0.0
    confidence_score: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProposalStrategyResult:
    """Result of proposal strategy generation."""
    strategy: ProposalStrategy
    success: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class ProposalStrategyGenerator:
    """
    Generates proposal strategies for jobs.
    
    Ensures all capability claims are evidence-backed and
    no fabricated claims are made.
    """

    def __init__(self) -> None:
        self._default_strategy_type = ProposalStrategyType.VALUE_FOCUSED
        self._default_tone = ProposalTone.PROFESSIONAL

    def generate_strategy(
        self,
        job_id: str,
        job_description: str,
        available_capabilities: List[str],
        available_evidence: Dict[str, List[str]],  # capability_id -> evidence_ids
        governed_knowledge: List[Any],
    ) -> ProposalStrategyResult:
        """
        Generate a proposal strategy for a job.
        
        Args:
            job_id: The job identifier
            job_description: The job description
            available_capabilities: List of available capabilities
            available_evidence: Mapping of capabilities to evidence
            governed_knowledge: Available governed knowledge
            
        Returns:
            ProposalStrategyResult with the strategy
        """
        strategy_id = f"strategy_{job_id}_{datetime.utcnow().timestamp()}"
        
        # Extract client requirements
        client_requirements = self._extract_client_requirements(job_description)
        
        # Generate evidence-backed capability claims
        capability_claims = self._generate_capability_claims(
            available_capabilities,
            available_evidence,
            job_description,
        )
        
        # Generate deliverables
        deliverables = self._generate_deliverables(job_description, client_requirements)
        
        # Identify risks
        risks = self._identify_risks(job_description, deliverables)
        
        # Identify assumptions
        assumptions = self._identify_assumptions(job_description, deliverables)
        
        # Generate client questions
        client_questions = self._generate_client_questions(
            job_description,
            client_requirements,
            risks,
        )
        
        # Calculate confidence score based on evidence coverage
        confidence_score = self._calculate_confidence_score(
            capability_claims,
            available_capabilities,
        )
        
        strategy = ProposalStrategy(
            strategy_id=strategy_id,
            job_id=job_id,
            strategy_type=self._default_strategy_type,
            tone=self._default_tone,
            client_requirements=client_requirements,
            capability_claims=capability_claims,
            deliverables=deliverables,
            risks=risks,
            assumptions=assumptions,
            client_questions=client_questions,
            confidence_score=confidence_score,
        )
        
        # Check for fabricated claims
        fabricated_claims = [c for c in capability_claims if c.is_fabricated]
        if fabricated_claims:
            warnings = [
                f"Capability '{c.capability_name}' has no evidence backing"
                for c in fabricated_claims
            ]
            return ProposalStrategyResult(
                strategy=strategy,
                success=False,
                errors=["Proposal contains claims without evidence backing"],
                warnings=warnings,
            )
        
        return ProposalStrategyResult(strategy=strategy, success=True)

    def _extract_client_requirements(self, job_description: str) -> List[ClientRequirement]:
        """Extract client requirements from job description."""
        requirements = []
        
        # Simple heuristic extraction - in production would use NLP
        keywords = {
            "technical": ["seo", "audit", "optimization", "technical", "code"],
            "business": ["revenue", "growth", "sales", "business", "strategy"],
            "timeline": ["deadline", "timeline", "delivery", "urgent"],
            "budget": ["budget", "cost", "price", "affordable"],
        }
        
        for category, category_keywords in keywords.items():
            for keyword in category_keywords:
                if keyword.lower() in job_description.lower():
                    requirement = ClientRequirement(
                        requirement_id=f"req_{len(requirements)}",
                        description=f"Requirement related to {keyword}",
                        priority="high",
                        category=category,
                        source_text=job_description,
                    )
                    requirements.append(requirement)
                    break
        
        return requirements

    def _generate_capability_claims(
        self,
        available_capabilities: List[str],
        available_evidence: Dict[str, List[str]],
        job_description: str,
    ) -> List[CapabilityClaim]:
        """
        Generate evidence-backed capability claims.
        
        Only generates claims for capabilities that have evidence.
        """
        claims = []
        
        for capability in available_capabilities:
            evidence_ids = available_evidence.get(capability, [])
            
            if evidence_ids:
                # Has evidence - can make claim
                claim = CapabilityClaim(
                    capability_id=capability,
                    capability_name=capability,
                    claim=f"We have experience in {capability}",
                    evidence_ids=evidence_ids,
                    confidence=0.8,
                    provenance="governed_knowledge",
                    is_fabricated=False,
                )
                claims.append(claim)
            else:
                # No evidence - mark as fabricated if we were to claim it
                # We don't add the claim, but track it for validation
                pass
        
        return claims

    def _generate_deliverables(
        self,
        job_description: str,
        client_requirements: List[ClientRequirement],
    ) -> List[Deliverable]:
        """Generate deliverables based on requirements."""
        deliverables = []
        
        # Simple heuristic - map requirements to deliverables
        for i, req in enumerate(client_requirements):
            deliverable = Deliverable(
                deliverable_id=f"del_{i}",
                name=f"Deliverable for {req.category}",
                description=req.description,
                estimated_hours=8.0,
            )
            deliverables.append(deliverable)
        
        return deliverables

    def _identify_risks(
        self,
        job_description: str,
        deliverables: List[Deliverable],
    ) -> List[Risk]:
        """Identify potential risks."""
        risks = []
        
        # Common risks
        risk_descriptions = [
            "Scope creep during project execution",
            "Technical complexity may require additional time",
            "Client availability for feedback",
            "Third-party dependencies",
        ]
        
        for i, desc in enumerate(risk_descriptions):
            risk = Risk(
                risk_id=f"risk_{i}",
                description=desc,
                likelihood="medium",
                impact="medium",
                mitigation="Regular communication and scope management",
            )
            risks.append(risk)
        
        return risks

    def _identify_assumptions(
        self,
        job_description: str,
        deliverables: List[Deliverable],
    ) -> List[Assumption]:
        """Identify assumptions made for the proposal."""
        assumptions = []
        
        # Common assumptions
        assumption_descriptions = [
            "Client will provide necessary access and resources",
            "Requirements are stable and won't change significantly",
            "Technical specifications are accurate",
        ]
        
        for i, desc in enumerate(assumption_descriptions):
            assumption = Assumption(
                assumption_id=f"assump_{i}",
                description=desc,
                category="scope",
            )
            assumptions.append(assumption)
        
        return assumptions

    def _generate_client_questions(
        self,
        job_description: str,
        client_requirements: List[ClientRequirement],
        risks: List[Risk],
    ) -> List[ClientQuestion]:
        """Generate questions for the client."""
        questions = []
        
        # Common questions
        question_templates = [
            ("What is your timeline for this project?", "timeline"),
            ("What is your budget range?", "budget"),
            ("Who will be the primary point of contact?", "clarification"),
            ("Are there any specific tools or technologies you prefer?", "technical"),
        ]
        
        for i, (question, category) in enumerate(question_templates):
            client_question = ClientQuestion(
                question_id=f"q_{i}",
                question=question,
                category=category,
                priority="high",
            )
            questions.append(client_question)
        
        return questions

    def _calculate_confidence_score(
        self,
        capability_claims: List[CapabilityClaim],
        available_capabilities: List[str],
    ) -> float:
        """Calculate confidence score based on evidence coverage."""
        if not available_capabilities:
            return 0.0
        
        claims_with_evidence = len([c for c in capability_claims if not c.is_fabricated])
        coverage = claims_with_evidence / len(available_capabilities)
        
        return coverage
