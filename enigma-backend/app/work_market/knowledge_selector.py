from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class KnowledgeSelection:
    """A selected knowledge item with relevance score."""
    knowledge_id: str
    knowledge_name: str
    relevance_score: float
    reason: str
    usage_context: str


@dataclass
class KnowledgeSelectionResult:
    """Result of knowledge selection."""
    selections: List[KnowledgeSelection]
    total_selected: int
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class RelevantKnowledgeSelector:
    """
    Selects relevant knowledge for a job proposal.
    
    Filters governed knowledge to find items most relevant
    to the job requirements and proposal strategy.
    """

    def __init__(self) -> None:
        self._relevance_threshold = 0.5

    def select_knowledge(
        self,
        job_id: str,
        job_description: str,
        required_capabilities: List[str],
        governed_knowledge: List[Any],
    ) -> KnowledgeSelectionResult:
        """
        Select relevant knowledge for the job.
        
        Args:
            job_id: The job identifier
            job_description: The job description
            required_capabilities: Required capabilities for the job
            governed_knowledge: Available governed knowledge
            
        Returns:
            KnowledgeSelectionResult with selected knowledge
        """
        selections = []
        
        for knowledge in governed_knowledge:
            # Get knowledge name
            knowledge_name = self._get_knowledge_name(knowledge)
            knowledge_id = self._get_knowledge_id(knowledge)
            
            # Calculate relevance
            relevance = self._calculate_relevance(
                knowledge_name,
                job_description,
                required_capabilities,
            )
            
            if relevance >= self._relevance_threshold:
                reason = self._generate_selection_reason(
                    knowledge_name,
                    relevance,
                    required_capabilities,
                )
                
                selection = KnowledgeSelection(
                    knowledge_id=knowledge_id,
                    knowledge_name=knowledge_name,
                    relevance_score=relevance,
                    reason=reason,
                    usage_context="proposal_support",
                )
                selections.append(selection)
        
        # Sort by relevance
        selections.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # Calculate overall confidence
        confidence = self._calculate_confidence(selections)
        
        return KnowledgeSelectionResult(
            selections=selections,
            total_selected=len(selections),
            confidence=confidence,
            metadata={
                "job_id": job_id,
                "total_knowledge_available": len(governed_knowledge),
                "relevance_threshold": self._relevance_threshold,
            },
        )

    def _get_knowledge_name(self, knowledge: Any) -> str:
        """Extract knowledge name from governed knowledge."""
        if hasattr(knowledge, 'concept'):
            return knowledge.concept.name
        elif hasattr(knowledge, 'name'):
            return knowledge.name
        else:
            return str(knowledge)

    def _get_knowledge_id(self, knowledge: Any) -> str:
        """Extract knowledge ID from governed knowledge."""
        if hasattr(knowledge, 'concept'):
            return knowledge.concept.id
        elif hasattr(knowledge, 'id'):
            return knowledge.id
        else:
            return f"unknown_{hash(knowledge)}"

    def _calculate_relevance(
        self,
        knowledge_name: str,
        job_description: str,
        required_capabilities: List[str],
    ) -> float:
        """
        Calculate relevance score for knowledge.
        
        Simple heuristic - in production would use semantic similarity.
        """
        score = 0.0
        knowledge_lower = knowledge_name.lower()
        job_desc_lower = job_description.lower()
        
        # Check if knowledge name appears in job description
        if knowledge_lower in job_desc_lower:
            score += 0.5
        
        # Check if knowledge matches required capabilities
        for capability in required_capabilities:
            if capability.lower() in knowledge_lower or knowledge_lower in capability.lower():
                score += 0.3
        
        # Check for keyword overlap
        knowledge_words = set(knowledge_lower.split('_'))
        job_words = set(job_desc_lower.split())
        overlap = len(knowledge_words & job_words)
        if overlap > 0:
            score += min(overlap * 0.1, 0.2)
        
        return min(score, 1.0)

    def _generate_selection_reason(
        self,
        knowledge_name: str,
        relevance: float,
        required_capabilities: List[str],
    ) -> str:
        """Generate reason for knowledge selection."""
        if relevance >= 0.8:
            return f"Highly relevant to job requirements"
        elif relevance >= 0.6:
            return f"Moderately relevant to required capabilities"
        else:
            return f"Potentially useful for context"

    def _calculate_confidence(self, selections: List[KnowledgeSelection]) -> float:
        """Calculate overall confidence in selections."""
        if not selections:
            return 0.0
        
        # Average relevance score
        avg_relevance = sum(s.relevance_score for s in selections) / len(selections)
        
        return avg_relevance
