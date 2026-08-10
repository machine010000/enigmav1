"""
Constraint Detection and Management

Identifies and manages creative constraints based on opportunity context.
"""

from typing import List, Set, Optional, Dict, Any
from dataclasses import dataclass

from app.creativity.contracts import (
    CreativeConstraint,
    ConstraintType,
    ConstraintSeverity,
    CreativeOpportunityContext,
)


class ConstraintDetector:
    """
    Detects constraints from opportunity context.
    
    Analyzes readiness, economics, and other factors to identify
    constraints that may limit opportunity success.
    """
    
    def detect_constraints(
        self,
        context: CreativeOpportunityContext,
    ) -> List[CreativeConstraint]:
        """
        Detect all constraints from the given context.
        
        Args:
            context: Opportunity context to analyze
            
        Returns:
            List of detected constraints
        """
        constraints = []
        
        # Portfolio constraints
        if context.portfolio_strength < 0.3:
            constraints.append(CreativeConstraint(
                constraint_type=ConstraintType.NO_PORTFOLIO,
                severity=ConstraintSeverity.HIGH,
                impact="Reduces client trust and competitive advantage",
                source="portfolio_analysis",
                confidence=0.9,
                blocking=False,
                description="Weak or missing portfolio limits ability to demonstrate capability",
            ))
        
        # Review constraints
        if context.review_strength < 0.3:
            constraints.append(CreativeConstraint(
                constraint_type=ConstraintType.NO_REVIEWS,
                severity=ConstraintSeverity.HIGH,
                impact="Reduces social proof and client confidence",
                source="review_analysis",
                confidence=0.9,
                blocking=False,
                description="No or few reviews reduces trust in service quality",
            ))
        
        # Evidence constraints
        if context.evidence_readiness < 0.4:
            constraints.append(CreativeConstraint(
                constraint_type=ConstraintType.LOW_EVIDENCE,
                severity=ConstraintSeverity.MEDIUM,
                impact="Difficulty demonstrating past success",
                source="evidence_analysis",
                confidence=0.8,
                blocking=False,
                description="Insufficient evidence to support claims of capability",
            ))
        
        # Readiness constraints
        if context.knowledge_readiness < 0.5 or context.execution_readiness < 0.5:
            constraints.append(CreativeConstraint(
                constraint_type=ConstraintType.LOW_READINESS,
                severity=ConstraintSeverity.MEDIUM,
                impact="Increased risk of execution failure",
                source="readiness_analysis",
                confidence=0.8,
                blocking=False,
                description="Knowledge or execution readiness below optimal threshold",
            ))
        
        # Competition constraints
        if context.competition_level > 0.7:
            constraints.append(CreativeConstraint(
                constraint_type=ConstraintType.HIGH_COMPETITION,
                severity=ConstraintSeverity.MEDIUM,
                impact="Lower probability of winning opportunity",
                source="competition_analysis",
                confidence=0.7,
                blocking=False,
                description="High competition reduces success probability",
            ))
        
        # Budget constraints
        if context.budget and context.application_cost:
            if context.budget < context.application_cost * 2:
                constraints.append(CreativeConstraint(
                    constraint_type=ConstraintType.LOW_BUDGET,
                    severity=ConstraintSeverity.HIGH,
                    impact="Poor economic viability",
                    source="economic_analysis",
                    confidence=0.9,
                    blocking=True,
                    description=f"Budget ${context.budget} is low relative to application cost ${context.application_cost}",
                ))
        
        # Application cost constraints
        if context.application_cost and context.expected_value:
            if context.application_cost > context.expected_value * 0.3:
                constraints.append(CreativeConstraint(
                    constraint_type=ConstraintType.HIGH_APPLICATION_COST,
                    severity=ConstraintSeverity.HIGH,
                    impact="Reduces economic viability",
                    source="economic_analysis",
                    confidence=0.9,
                    blocking=True,
                    description=f"Application cost ${context.application_cost} is high relative to expected value ${context.expected_value}",
                ))
        
        # Knowledge freshness constraints
        if context.knowledge_freshness < 0.5:
            constraints.append(CreativeConstraint(
                constraint_type=ConstraintType.STALE_KNOWLEDGE,
                severity=ConstraintSeverity.MEDIUM,
                impact="Risk of using outdated information",
                source="knowledge_analysis",
                confidence=0.8,
                blocking=False,
                description="Knowledge may be outdated, reducing accuracy and effectiveness",
            ))
        
        # Confidence constraints
        if context.confidence_score < 0.4:
            constraints.append(CreativeConstraint(
                constraint_type=ConstraintType.LOW_CONFIDENCE,
                severity=ConstraintSeverity.MEDIUM,
                impact="Higher uncertainty in execution",
                source="confidence_analysis",
                confidence=0.8,
                blocking=False,
                description="Low confidence increases risk of poor outcomes",
            ))
        
        # Experience constraints
        if context.experience_strength < 0.3:
            constraints.append(CreativeConstraint(
                constraint_type=ConstraintType.EXPERIENCE_GAP,
                severity=ConstraintSeverity.MEDIUM,
                impact="Difficulty demonstrating relevant experience",
                source="experience_analysis",
                confidence=0.8,
                blocking=False,
                description="Limited experience in relevant domain reduces competitiveness",
            ))
        
        # Risk constraints
        if context.risk_score > 0.7:
            constraints.append(CreativeConstraint(
                constraint_type=ConstraintType.EXECUTION_GAP,
                severity=ConstraintSeverity.HIGH,
                impact="High risk of execution failure",
                source="risk_analysis",
                confidence=0.8,
                blocking=True,
                description="High risk score indicates significant execution challenges",
            ))
        
        return constraints
    
    def get_blocking_constraints(
        self,
        constraints: List[CreativeConstraint],
    ) -> List[CreativeConstraint]:
        """
        Filter to only blocking constraints.
        
        Args:
            constraints: List of all constraints
            
        Returns:
            List of blocking constraints
        """
        return [c for c in constraints if c.blocking]
    
    def get_constraints_by_type(
        self,
        constraints: List[CreativeConstraint],
        constraint_type: ConstraintType,
    ) -> List[CreativeConstraint]:
        """
        Filter constraints by type.
        
        Args:
            constraints: List of all constraints
            constraint_type: Type to filter by
            
        Returns:
            List of constraints of the specified type
        """
        return [c for c in constraints if c.constraint_type == constraint_type]
    
    def get_constraints_by_severity(
        self,
        constraints: List[CreativeConstraint],
        severity: ConstraintSeverity,
    ) -> List[CreativeConstraint]:
        """
        Filter constraints by severity.
        
        Args:
            constraints: List of all constraints
            severity: Severity to filter by
            
        Returns:
            List of constraints with the specified severity
        """
        return [c for c in constraints if c.severity == severity]
