"""
Enigma Profile Repository Contracts and Database Implementations

Repository layer for persistent Enigma Profile state.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enigma_profile import (
    EnigmaProfile as EnigmaProfileModel,
    KnowledgeProgress as KnowledgeProgressModel,
    TrainingItem as TrainingItemModel,
    PlatformReadiness as PlatformReadinessModel,
    DevelopmentPriority as DevelopmentPriorityModel,
    Issue as IssueModel,
)
from app.enigma_profile.contracts import (
    EnigmaProfile,
    KnowledgeProgress,
    TrainingItem,
    PlatformReadiness,
    DevelopmentPriority,
    Issue,
    SkillLevel,
    IssueSeverity,
    IssueType,
    IssueStatus,
)
from app.marketplace.contracts import MarketplacePlatform


# ============================================================================
# Repository Contracts
# ============================================================================

class EnigmaProfileRepository(ABC):
    """Contract for Enigma Profile repository."""

    @abstractmethod
    async def get_profile(self, profile_id: str = "enigma_profile") -> Optional[EnigmaProfile]:
        """Get Enigma profile by ID."""
        pass

    @abstractmethod
    async def save_profile(self, profile: EnigmaProfile) -> EnigmaProfile:
        """Save or update Enigma profile."""
        pass

    @abstractmethod
    async def delete_profile(self, profile_id: str) -> bool:
        """Delete Enigma profile."""
        pass


class KnowledgeProgressRepository(ABC):
    """Contract for Knowledge Progress repository."""

    @abstractmethod
    async def get_progress(self, profile_id: str, domain: str) -> Optional[KnowledgeProgress]:
        """Get knowledge progress for a domain."""
        pass

    @abstractmethod
    async def save_progress(self, profile_id: str, progress: KnowledgeProgress) -> KnowledgeProgress:
        """Save or update knowledge progress."""
        pass

    @abstractmethod
    async def get_all_progress(self, profile_id: str) -> Dict[str, KnowledgeProgress]:
        """Get all knowledge progress for a profile."""
        pass

    @abstractmethod
    async def delete_progress(self, profile_id: str, domain: str) -> bool:
        """Delete knowledge progress for a domain."""
        pass


class TrainingItemRepository(ABC):
    """Contract for Training Item repository."""

    @abstractmethod
    async def get_training(self, profile_id: str, skill: str) -> Optional[TrainingItem]:
        """Get training item for a skill."""
        pass

    @abstractmethod
    async def save_training(self, profile_id: str, item: TrainingItem) -> TrainingItem:
        """Save or update training item."""
        pass

    @abstractmethod
    async def get_all_training(self, profile_id: str) -> List[TrainingItem]:
        """Get all training items for a profile."""
        pass

    @abstractmethod
    async def delete_training(self, profile_id: str, skill: str) -> bool:
        """Delete training item for a skill."""
        pass


class PlatformReadinessRepository(ABC):
    """Contract for Platform Readiness repository."""

    @abstractmethod
    async def get_readiness(self, profile_id: str, platform: MarketplacePlatform) -> Optional[PlatformReadiness]:
        """Get platform readiness."""
        pass

    @abstractmethod
    async def save_readiness(self, profile_id: str, readiness: PlatformReadiness) -> PlatformReadiness:
        """Save or update platform readiness."""
        pass

    @abstractmethod
    async def get_all_readiness(self, profile_id: str) -> Dict[MarketplacePlatform, PlatformReadiness]:
        """Get all platform readiness for a profile."""
        pass

    @abstractmethod
    async def delete_readiness(self, profile_id: str, platform: MarketplacePlatform) -> bool:
        """Delete platform readiness."""
        pass


class DevelopmentPriorityRepository(ABC):
    """Contract for Development Priority repository."""

    @abstractmethod
    async def get_priority(self, profile_id: str, priority_id: int) -> Optional[DevelopmentPriority]:
        """Get development priority by ID."""
        pass

    @abstractmethod
    async def save_priority(self, profile_id: str, priority: DevelopmentPriority) -> DevelopmentPriority:
        """Save or update development priority."""
        pass

    @abstractmethod
    async def get_all_priorities(self, profile_id: str) -> List[DevelopmentPriority]:
        """Get all development priorities for a profile."""
        pass

    @abstractmethod
    async def delete_priority(self, profile_id: str, priority_id: int) -> bool:
        """Delete development priority."""
        pass

    @abstractmethod
    async def delete_all_priorities(self, profile_id: str) -> bool:
        """Delete all development priorities for a profile."""
        pass


class IssueRepository(ABC):
    """Contract for Issue repository."""

    @abstractmethod
    async def get_issue(self, profile_id: str, issue_id: str) -> Optional[Issue]:
        """Get issue by ID."""
        pass

    @abstractmethod
    async def save_issue(self, profile_id: str, issue: Issue) -> Issue:
        """Save or update issue."""
        pass

    @abstractmethod
    async def get_all_issues(self, profile_id: str) -> List[Issue]:
        """Get all issues for a profile."""
        pass

    @abstractmethod
    async def get_open_issues(self, profile_id: str, severity: Optional[IssueSeverity] = None) -> List[Issue]:
        """Get open issues, optionally filtered by severity."""
        pass

    @abstractmethod
    async def delete_issue(self, profile_id: str, issue_id: str) -> bool:
        """Delete issue."""
        pass

    @abstractmethod
    async def delete_all_issues(self, profile_id: str) -> bool:
        """Delete all issues for a profile."""
        pass


# ============================================================================
# Database Implementations
# ============================================================================

class DatabaseEnigmaProfileRepository(EnigmaProfileRepository):
    """Database implementation of Enigma Profile repository."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_profile(self, profile_id: str = "enigma_profile") -> Optional[EnigmaProfile]:
        """Get Enigma profile by ID."""
        result = await self.db.execute(
            select(EnigmaProfileModel).where(EnigmaProfileModel.profile_id == profile_id)
        )
        model = result.scalar_one_or_none()
        
        if not model:
            return None
        
        return self._model_to_contract(model)

    async def save_profile(self, profile: EnigmaProfile) -> EnigmaProfile:
        """Save or update Enigma profile."""
        result = await self.db.execute(
            select(EnigmaProfileModel).where(EnigmaProfileModel.profile_id == profile.profile_id)
        )
        model = result.scalar_one_or_none()
        
        if model:
            # Update existing
            model.owner = profile.owner
            model.active_goals = profile.active_goals
            model.target_professions = profile.target_professions
            model.target_platforms = [p.value for p in profile.target_platforms]
            model.target_markets = profile.target_markets
            model.target_languages = profile.target_languages
            model.metadata = profile.metadata
            model.updated_at = datetime.utcnow()
        else:
            # Create new
            model = EnigmaProfileModel(
                profile_id=profile.profile_id,
                owner=profile.owner,
                active_goals=profile.active_goals,
                target_professions=profile.target_professions,
                target_platforms=[p.value for p in profile.target_platforms],
                target_markets=profile.target_markets,
                target_languages=profile.target_languages,
                metadata=profile.metadata,
            )
            self.db.add(model)
        
        await self.db.commit()
        await self.db.refresh(model)
        
        return self._model_to_contract(model)

    async def delete_profile(self, profile_id: str) -> bool:
        """Delete Enigma profile."""
        result = await self.db.execute(
            select(EnigmaProfileModel).where(EnigmaProfileModel.profile_id == profile_id)
        )
        model = result.scalar_one_or_none()
        
        if not model:
            return False
        
        await self.db.delete(model)
        await self.db.commit()
        return True

    def _model_to_contract(self, model: EnigmaProfileModel) -> EnigmaProfile:
        """Convert database model to contract."""
        return EnigmaProfile(
            profile_id=model.profile_id,
            owner=model.owner,
            created_at=model.created_at.isoformat() if model.created_at else None,
            updated_at=model.updated_at.isoformat() if model.updated_at else None,
            active_goals=model.active_goals or [],
            target_professions=model.target_professions or [],
            target_platforms=[MarketplacePlatform(p) for p in (model.target_platforms or [])],
            target_markets=model.target_markets or [],
            target_languages=model.target_languages or [],
            metadata=model.metadata or {},
        )


class DatabaseKnowledgeProgressRepository(KnowledgeProgressRepository):
    """Database implementation of Knowledge Progress repository."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_progress(self, profile_id: str, domain: str) -> Optional[KnowledgeProgress]:
        """Get knowledge progress for a domain."""
        result = await self.db.execute(
            select(KnowledgeProgressModel).where(
                KnowledgeProgressModel.profile_id == profile_id,
                KnowledgeProgressModel.domain == domain
            )
        )
        model = result.scalar_one_or_none()
        
        if not model:
            return None
        
        return self._model_to_contract(model)

    async def save_progress(self, profile_id: str, progress: KnowledgeProgress) -> KnowledgeProgress:
        """Save or update knowledge progress."""
        result = await self.db.execute(
            select(KnowledgeProgressModel).where(
                KnowledgeProgressModel.profile_id == profile_id,
                KnowledgeProgressModel.domain == progress.domain
            )
        )
        model = result.scalar_one_or_none()
        
        if model:
            # Update existing
            model.knowledge_score = progress.knowledge_score
            model.execution_score = progress.execution_score
            model.evidence_score = progress.evidence_score
            model.confidence = progress.confidence
            model.readiness = progress.readiness
            model.last_verified = datetime.fromisoformat(progress.last_verified) if progress.last_verified else None
            model.freshness = progress.freshness
            model.concepts = progress.concepts
            model.updated_at = datetime.utcnow()
        else:
            # Create new
            model = KnowledgeProgressModel(
                profile_id=profile_id,
                domain=progress.domain,
                knowledge_score=progress.knowledge_score,
                execution_score=progress.execution_score,
                evidence_score=progress.evidence_score,
                confidence=progress.confidence,
                readiness=progress.readiness,
                last_verified=datetime.fromisoformat(progress.last_verified) if progress.last_verified else None,
                freshness=progress.freshness,
                concepts=progress.concepts,
            )
            self.db.add(model)
        
        await self.db.commit()
        await self.db.refresh(model)
        
        return self._model_to_contract(model)

    async def get_all_progress(self, profile_id: str) -> Dict[str, KnowledgeProgress]:
        """Get all knowledge progress for a profile."""
        result = await self.db.execute(
            select(KnowledgeProgressModel).where(KnowledgeProgressModel.profile_id == profile_id)
        )
        models = result.scalars().all()
        
        return {model.domain: self._model_to_contract(model) for model in models}

    async def delete_progress(self, profile_id: str, domain: str) -> bool:
        """Delete knowledge progress for a domain."""
        result = await self.db.execute(
            select(KnowledgeProgressModel).where(
                KnowledgeProgressModel.profile_id == profile_id,
                KnowledgeProgressModel.domain == domain
            )
        )
        model = result.scalar_one_or_none()
        
        if not model:
            return False
        
        await self.db.delete(model)
        await self.db.commit()
        return True

    def _model_to_contract(self, model: KnowledgeProgressModel) -> KnowledgeProgress:
        """Convert database model to contract."""
        return KnowledgeProgress(
            domain=model.domain,
            knowledge_score=model.knowledge_score,
            execution_score=model.execution_score,
            evidence_score=model.evidence_score,
            confidence=model.confidence,
            readiness=model.readiness,
            last_verified=model.last_verified.isoformat() if model.last_verified else None,
            freshness=model.freshness,
            concepts=model.concepts or {},
        )


class DatabaseTrainingItemRepository(TrainingItemRepository):
    """Database implementation of Training Item repository."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_training(self, profile_id: str, skill: str) -> Optional[TrainingItem]:
        """Get training item for a skill."""
        result = await self.db.execute(
            select(TrainingItemModel).where(
                TrainingItemModel.profile_id == profile_id,
                TrainingItemModel.skill == skill
            )
        )
        model = result.scalar_one_or_none()
        
        if not model:
            return None
        
        return self._model_to_contract(model)

    async def save_training(self, profile_id: str, item: TrainingItem) -> TrainingItem:
        """Save or update training item."""
        result = await self.db.execute(
            select(TrainingItemModel).where(
                TrainingItemModel.profile_id == profile_id,
                TrainingItemModel.skill == item.skill
            )
        )
        model = result.scalar_one_or_none()
        
        if model:
            # Update existing
            model.level = item.level
            model.started_at = datetime.fromisoformat(item.started_at) if item.started_at else None
            model.completed_at = datetime.fromisoformat(item.completed_at) if item.completed_at else None
            model.progress = item.progress
            model.resources = item.resources
            model.notes = item.notes
            model.updated_at = datetime.utcnow()
        else:
            # Create new
            model = TrainingItemModel(
                profile_id=profile_id,
                skill=item.skill,
                level=item.level,
                started_at=datetime.fromisoformat(item.started_at) if item.started_at else None,
                completed_at=datetime.fromisoformat(item.completed_at) if item.completed_at else None,
                progress=item.progress,
                resources=item.resources,
                notes=item.notes,
            )
            self.db.add(model)
        
        await self.db.commit()
        await self.db.refresh(model)
        
        return self._model_to_contract(model)

    async def get_all_training(self, profile_id: str) -> List[TrainingItem]:
        """Get all training items for a profile."""
        result = await self.db.execute(
            select(TrainingItemModel).where(TrainingItemModel.profile_id == profile_id)
        )
        models = result.scalars().all()
        
        return [self._model_to_contract(model) for model in models]

    async def delete_training(self, profile_id: str, skill: str) -> bool:
        """Delete training item for a skill."""
        result = await self.db.execute(
            select(TrainingItemModel).where(
                TrainingItemModel.profile_id == profile_id,
                TrainingItemModel.skill == skill
            )
        )
        model = result.scalar_one_or_none()
        
        if not model:
            return False
        
        await self.db.delete(model)
        await self.db.commit()
        return True

    def _model_to_contract(self, model: TrainingItemModel) -> TrainingItem:
        """Convert database model to contract."""
        return TrainingItem(
            skill=model.skill,
            level=model.level,
            started_at=model.started_at.isoformat() if model.started_at else None,
            completed_at=model.completed_at.isoformat() if model.completed_at else None,
            progress=model.progress,
            resources=model.resources or [],
            notes=model.notes or "",
        )


class DatabasePlatformReadinessRepository(PlatformReadinessRepository):
    """Database implementation of Platform Readiness repository."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_readiness(self, profile_id: str, platform: MarketplacePlatform) -> Optional[PlatformReadiness]:
        """Get platform readiness."""
        result = await self.db.execute(
            select(PlatformReadinessModel).where(
                PlatformReadinessModel.profile_id == profile_id,
                PlatformReadinessModel.platform == platform.value
            )
        )
        model = result.scalar_one_or_none()
        
        if not model:
            return None
        
        return self._model_to_contract(model)

    async def save_readiness(self, profile_id: str, readiness: PlatformReadiness) -> PlatformReadiness:
        """Save or update platform readiness."""
        result = await self.db.execute(
            select(PlatformReadinessModel).where(
                PlatformReadinessModel.profile_id == profile_id,
                PlatformReadinessModel.platform == readiness.platform.value
            )
        )
        model = result.scalar_one_or_none()
        
        if model:
            # Update existing
            model.overall_readiness = readiness.overall_readiness
            model.knowledge_score = readiness.knowledge_score
            model.evidence_score = readiness.evidence_score
            model.portfolio_score = readiness.portfolio_score
            model.execution_score = readiness.execution_score
            model.win_probability = readiness.win_probability
            model.economics_score = readiness.economics_score
            model.blockers = readiness.blockers
            model.recommendations = readiness.recommendations
            model.last_updated = datetime.fromisoformat(readiness.last_updated) if readiness.last_updated else None
            model.updated_at = datetime.utcnow()
        else:
            # Create new
            model = PlatformReadinessModel(
                profile_id=profile_id,
                platform=readiness.platform.value,
                overall_readiness=readiness.overall_readiness,
                knowledge_score=readiness.knowledge_score,
                evidence_score=readiness.evidence_score,
                portfolio_score=readiness.portfolio_score,
                execution_score=readiness.execution_score,
                win_probability=readiness.win_probability,
                economics_score=readiness.economics_score,
                blockers=readiness.blockers,
                recommendations=readiness.recommendations,
                last_updated=datetime.fromisoformat(readiness.last_updated) if readiness.last_updated else None,
            )
            self.db.add(model)
        
        await self.db.commit()
        await self.db.refresh(model)
        
        return self._model_to_contract(model)

    async def get_all_readiness(self, profile_id: str) -> Dict[MarketplacePlatform, PlatformReadiness]:
        """Get all platform readiness for a profile."""
        result = await self.db.execute(
            select(PlatformReadinessModel).where(PlatformReadinessModel.profile_id == profile_id)
        )
        models = result.scalars().all()
        
        return {
            MarketplacePlatform(model.platform): self._model_to_contract(model)
            for model in models
        }

    async def delete_readiness(self, profile_id: str, platform: MarketplacePlatform) -> bool:
        """Delete platform readiness."""
        result = await self.db.execute(
            select(PlatformReadinessModel).where(
                PlatformReadinessModel.profile_id == profile_id,
                PlatformReadinessModel.platform == platform.value
            )
        )
        model = result.scalar_one_or_none()
        
        if not model:
            return False
        
        await self.db.delete(model)
        await self.db.commit()
        return True

    def _model_to_contract(self, model: PlatformReadinessModel) -> PlatformReadiness:
        """Convert database model to contract."""
        return PlatformReadiness(
            platform=MarketplacePlatform(model.platform),
            overall_readiness=model.overall_readiness,
            knowledge_score=model.knowledge_score,
            evidence_score=model.evidence_score,
            portfolio_score=model.portfolio_score,
            execution_score=model.execution_score,
            win_probability=model.win_probability,
            economics_score=model.economics_score,
            blockers=model.blockers or [],
            recommendations=model.recommendations or [],
            last_updated=model.last_updated.isoformat() if model.last_updated else None,
        )


class DatabaseDevelopmentPriorityRepository(DevelopmentPriorityRepository):
    """Database implementation of Development Priority repository."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_priority(self, profile_id: str, priority_id: int) -> Optional[DevelopmentPriority]:
        """Get development priority by ID."""
        result = await self.db.execute(
            select(DevelopmentPriorityModel).where(
                DevelopmentPriorityModel.profile_id == profile_id,
                DevelopmentPriorityModel.id == priority_id
            )
        )
        model = result.scalar_one_or_none()
        
        if not model:
            return None
        
        return self._model_to_contract(model)

    async def save_priority(self, profile_id: str, priority: DevelopmentPriority) -> DevelopmentPriority:
        """Save or update development priority."""
        # Development priorities are regenerated, so we always create new
        model = DevelopmentPriorityModel(
            profile_id=profile_id,
            priority=priority.priority,
            title=priority.title,
            description=priority.description,
            category=priority.category,
            impact=priority.impact,
            effort=priority.effort,
            status=priority.status,
            created_at=datetime.fromisoformat(priority.created_at) if priority.created_at else datetime.utcnow(),
        )
        self.db.add(model)
        
        await self.db.commit()
        await self.db.refresh(model)
        
        return self._model_to_contract(model)

    async def get_all_priorities(self, profile_id: str) -> List[DevelopmentPriority]:
        """Get all development priorities for a profile."""
        result = await self.db.execute(
            select(DevelopmentPriorityModel)
            .where(DevelopmentPriorityModel.profile_id == profile_id)
            .order_by(DevelopmentPriorityModel.priority)
        )
        models = result.scalars().all()
        
        return [self._model_to_contract(model) for model in models]

    async def delete_priority(self, profile_id: str, priority_id: int) -> bool:
        """Delete development priority."""
        result = await self.db.execute(
            select(DevelopmentPriorityModel).where(
                DevelopmentPriorityModel.profile_id == profile_id,
                DevelopmentPriorityModel.id == priority_id
            )
        )
        model = result.scalar_one_or_none()
        
        if not model:
            return False
        
        await self.db.delete(model)
        await self.db.commit()
        return True

    async def delete_all_priorities(self, profile_id: str) -> bool:
        """Delete all development priorities for a profile."""
        result = await self.db.execute(
            select(DevelopmentPriorityModel).where(DevelopmentPriorityModel.profile_id == profile_id)
        )
        models = result.scalars().all()
        
        for model in models:
            await self.db.delete(model)
        
        await self.db.commit()
        return True

    def _model_to_contract(self, model: DevelopmentPriorityModel) -> DevelopmentPriority:
        """Convert database model to contract."""
        return DevelopmentPriority(
            priority=model.priority,
            title=model.title,
            description=model.description,
            category=model.category,
            impact=model.impact,
            effort=model.effort,
            created_at=model.created_at.isoformat() if model.created_at else None,
            status=model.status,
        )


class DatabaseIssueRepository(IssueRepository):
    """Database implementation of Issue repository."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_issue(self, profile_id: str, issue_id: str) -> Optional[Issue]:
        """Get issue by ID."""
        result = await self.db.execute(
            select(IssueModel).where(
                IssueModel.profile_id == profile_id,
                IssueModel.issue_id == issue_id
            )
        )
        model = result.scalar_one_or_none()
        
        if not model:
            return None
        
        return self._model_to_contract(model)

    async def save_issue(self, profile_id: str, issue: Issue) -> Issue:
        """Save or update issue."""
        result = await self.db.execute(
            select(IssueModel).where(
                IssueModel.profile_id == profile_id,
                IssueModel.issue_id == issue.issue_id
            )
        )
        model = result.scalar_one_or_none()
        
        if model:
            # Update existing
            model.source = issue.source
            model.type = issue.type
            model.severity = issue.severity
            model.status = issue.status
            model.platform = issue.platform.value if issue.platform else None
            model.task = issue.task
            model.detected_reason = issue.detected_reason
            model.impact = issue.impact
            model.required_action = issue.required_action
            model.resolved_at = datetime.fromisoformat(issue.resolved_at) if issue.resolved_at else None
            model.metadata = issue.metadata
            model.updated_at = datetime.utcnow()
        else:
            # Create new
            model = IssueModel(
                profile_id=profile_id,
                issue_id=issue.issue_id,
                source=issue.source,
                type=issue.type,
                severity=issue.severity,
                status=issue.status,
                platform=issue.platform.value if issue.platform else None,
                task=issue.task,
                detected_reason=issue.detected_reason,
                impact=issue.impact,
                required_action=issue.required_action,
                timestamp=datetime.fromisoformat(issue.timestamp) if issue.timestamp else datetime.utcnow(),
                resolved_at=datetime.fromisoformat(issue.resolved_at) if issue.resolved_at else None,
                metadata=issue.metadata,
            )
            self.db.add(model)
        
        await self.db.commit()
        await self.db.refresh(model)
        
        return self._model_to_contract(model)

    async def get_all_issues(self, profile_id: str) -> List[Issue]:
        """Get all issues for a profile."""
        result = await self.db.execute(
            select(IssueModel).where(IssueModel.profile_id == profile_id)
        )
        models = result.scalars().all()
        
        return [self._model_to_contract(model) for model in models]

    async def get_open_issues(self, profile_id: str, severity: Optional[IssueSeverity] = None) -> List[Issue]:
        """Get open issues, optionally filtered by severity."""
        query = select(IssueModel).where(
            IssueModel.profile_id == profile_id,
            IssueModel.status == IssueStatus.OPEN
        )
        
        if severity:
            query = query.where(IssueModel.severity == severity)
        
        result = await self.db.execute(query)
        models = result.scalars().all()
        
        return [self._model_to_contract(model) for model in models]

    async def delete_issue(self, profile_id: str, issue_id: str) -> bool:
        """Delete issue."""
        result = await self.db.execute(
            select(IssueModel).where(
                IssueModel.profile_id == profile_id,
                IssueModel.issue_id == issue_id
            )
        )
        model = result.scalar_one_or_none()
        
        if not model:
            return False
        
        await self.db.delete(model)
        await self.db.commit()
        return True

    async def delete_all_issues(self, profile_id: str) -> bool:
        """Delete all issues for a profile."""
        result = await self.db.execute(
            select(IssueModel).where(IssueModel.profile_id == profile_id)
        )
        models = result.scalars().all()
        
        for model in models:
            await self.db.delete(model)
        
        await self.db.commit()
        return True

    def _model_to_contract(self, model: IssueModel) -> Issue:
        """Convert database model to contract."""
        return Issue(
            issue_id=model.issue_id,
            source=model.source,
            type=model.type,
            severity=model.severity,
            timestamp=model.timestamp.isoformat() if model.timestamp else None,
            platform=MarketplacePlatform(model.platform) if model.platform else None,
            task=model.task,
            detected_reason=model.detected_reason,
            impact=model.impact,
            required_action=model.required_action,
            status=model.status,
            resolved_at=model.resolved_at.isoformat() if model.resolved_at else None,
            metadata=model.metadata or {},
        )
