"""
Marketplace Repository Contracts and Database Implementations

Repository layer for persistent marketplace state.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict
from datetime import datetime
from decimal import Decimal

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.marketplace import (
    MarketplaceAccountState as MarketplaceAccountStateModel,
    MarketplaceJob as MarketplaceJobModel,
    MarketplaceJobAssessment as MarketplaceJobAssessmentModel,
    MarketplaceApplication as MarketplaceApplicationModel,
    MarketplaceActiveWork as MarketplaceActiveWorkModel,
)
from app.marketplace.contracts import MarketplacePlatform, NormalizedJob, NormalizedApplication, ApplicationStatus
from app.marketplace.account_state import (
    MarketplaceAccountState as AccountStateContract,
    CreditBalance,
    WalletBalance,
    SubscriptionPlan,
    AccountStatus,
    DataSource,
    FreshnessStatus,
)


# ============================================================================
# Repository Contracts
# ============================================================================

class MarketplaceAccountStateRepository(ABC):
    """Contract for Marketplace Account State repository."""

    @abstractmethod
    async def get_account_state(
        self,
        profile_id: str,
        platform: MarketplacePlatform,
    ) -> Optional[AccountStateContract]:
        """Get account state for a profile and platform."""
        pass

    @abstractmethod
    async def save_account_state(
        self,
        profile_id: str,
        state: AccountStateContract,
    ) -> AccountStateContract:
        """Save or update account state."""
        pass

    @abstractmethod
    async def delete_account_state(
        self,
        profile_id: str,
        platform: MarketplacePlatform,
    ) -> bool:
        """Delete account state."""
        pass

    @abstractmethod
    async def get_all_account_states(
        self,
        profile_id: str,
    ) -> Dict[MarketplacePlatform, AccountStateContract]:
        """Get all account states for a profile."""
        pass


class MarketplaceJobRepository(ABC):
    """Contract for Marketplace Job repository."""

    @abstractmethod
    async def get_job(
        self,
        profile_id: str,
        job_id: str,
    ) -> Optional[NormalizedJob]:
        """Get job by ID."""
        pass

    @abstractmethod
    async def save_job(
        self,
        profile_id: str,
        job: NormalizedJob,
    ) -> NormalizedJob:
        """Save or update job."""
        pass

    @abstractmethod
    async def delete_job(
        self,
        profile_id: str,
        job_id: str,
    ) -> bool:
        """Delete job."""
        pass

    @abstractmethod
    async def get_all_jobs(
        self,
        profile_id: str,
        platform: Optional[MarketplacePlatform] = None,
        limit: int = 100,
    ) -> List[NormalizedJob]:
        """Get all jobs for a profile, optionally filtered by platform."""
        pass

    @abstractmethod
    async def get_job_by_platform_id(
        self,
        profile_id: str,
        platform: MarketplacePlatform,
        platform_job_id: str,
    ) -> Optional[NormalizedJob]:
        """Get job by platform-specific job ID."""
        pass


class MarketplaceJobAssessmentRepository(ABC):
    """Contract for Marketplace Job Assessment repository."""

    @abstractmethod
    async def get_assessment(
        self,
        profile_id: str,
        job_id: str,
    ) -> Optional[Dict]:
        """Get job assessment."""
        pass

    @abstractmethod
    async def save_assessment(
        self,
        profile_id: str,
        job_id: str,
        assessment: Dict,
    ) -> Dict:
        """Save or update job assessment."""
        pass

    @abstractmethod
    async def delete_assessment(
        self,
        profile_id: str,
        job_id: str,
    ) -> bool:
        """Delete job assessment."""
        pass

    @abstractmethod
    async def get_all_assessments(
        self,
        profile_id: str,
    ) -> List[Dict]:
        """Get all assessments for a profile."""
        pass


class MarketplaceApplicationRepository(ABC):
    """Contract for Marketplace Application repository."""

    @abstractmethod
    async def get_application(
        self,
        profile_id: str,
        application_id: str,
    ) -> Optional[NormalizedApplication]:
        """Get application by ID."""
        pass

    @abstractmethod
    async def save_application(
        self,
        profile_id: str,
        application: NormalizedApplication,
    ) -> NormalizedApplication:
        """Save or update application."""
        pass

    @abstractmethod
    async def delete_application(
        self,
        profile_id: str,
        application_id: str,
    ) -> bool:
        """Delete application."""
        pass

    @abstractmethod
    async def get_all_applications(
        self,
        profile_id: str,
        job_id: Optional[str] = None,
        status: Optional[ApplicationStatus] = None,
    ) -> List[NormalizedApplication]:
        """Get all applications for a profile, optionally filtered."""
        pass

    @abstractmethod
    async def get_application_by_platform_id(
        self,
        profile_id: str,
        platform: MarketplacePlatform,
        platform_application_id: str,
    ) -> Optional[NormalizedApplication]:
        """Get application by platform-specific application ID."""
        pass


class MarketplaceActiveWorkRepository(ABC):
    """Contract for Marketplace Active Work repository."""

    @abstractmethod
    async def get_active_work(
        self,
        profile_id: str,
        work_id: str,
    ) -> Optional[Dict]:
        """Get active work by ID."""
        pass

    @abstractmethod
    async def save_active_work(
        self,
        profile_id: str,
        work: Dict,
    ) -> Dict:
        """Save or update active work."""
        pass

    @abstractmethod
    async def delete_active_work(
        self,
        profile_id: str,
        work_id: str,
    ) -> bool:
        """Delete active work."""
        pass

    @abstractmethod
    async def get_all_active_work(
        self,
        profile_id: str,
        application_id: Optional[str] = None,
    ) -> List[Dict]:
        """Get all active work for a profile, optionally filtered."""
        pass


# ============================================================================
# Database Implementations
# ============================================================================

class DatabaseMarketplaceAccountStateRepository(MarketplaceAccountStateRepository):
    """Database implementation of Marketplace Account State repository."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_account_state(
        self,
        profile_id: str,
        platform: MarketplacePlatform,
    ) -> Optional[AccountStateContract]:
        """Get account state for a profile and platform."""
        result = await self.db.execute(
            select(MarketplaceAccountStateModel).where(
                and_(
                    MarketplaceAccountStateModel.profile_id == profile_id,
                    MarketplaceAccountStateModel.platform == platform.value
                )
            )
        )
        model = result.scalar_one_or_none()
        
        if not model:
            return None
        
        return self._model_to_contract(model)

    async def save_account_state(
        self,
        profile_id: str,
        state: AccountStateContract,
    ) -> AccountStateContract:
        """Save or update account state."""
        result = await self.db.execute(
            select(MarketplaceAccountStateModel).where(
                and_(
                    MarketplaceAccountStateModel.profile_id == profile_id,
                    MarketplaceAccountStateModel.platform == state.platform.value
                )
            )
        )
        model = result.scalar_one_or_none()
        
        if model:
            # Update existing
            model.account_id = state.account_id
            model.account_status = AccountStatus(state.account_status.value)
            model.credits_available = state.credits.available
            model.credits_pending = state.credits.pending
            model.credits_used = state.credits.used
            model.credits_limit = state.credits.limit
            model.credits_currency = state.credits.currency
            model.wallet_available = float(state.wallet.available) if state.wallet.available else None
            model.wallet_currency = state.wallet.currency
            model.subscription_plan_name = state.subscription.plan_name if state.subscription else None
            model.subscription_plan_type = state.subscription.plan_type if state.subscription else None
            model.subscription_expires_at = datetime.fromisoformat(state.subscription.expires_at) if state.subscription and state.subscription.expires_at else None
            model.subscription_features = state.subscription.features if state.subscription else {}
            model.last_verified_at = datetime.fromisoformat(state.last_verified_at) if state.last_verified_at else None
            model.source = DataSource(state.source.value)
            model.confidence = state.confidence
            model.freshness = FreshnessStatus(state.freshness.value)
            model.metadata = state.metadata
            model.updated_at = datetime.utcnow()
        else:
            # Create new
            model = MarketplaceAccountStateModel(
                profile_id=profile_id,
                platform=state.platform.value,
                account_id=state.account_id,
                account_status=AccountStatus(state.account_status.value),
                credits_available=state.credits.available,
                credits_pending=state.credits.pending,
                credits_used=state.credits.used,
                credits_limit=state.credits.limit,
                credits_currency=state.credits.currency,
                wallet_available=float(state.wallet.available) if state.wallet.available else None,
                wallet_currency=state.wallet.currency,
                subscription_plan_name=state.subscription.plan_name if state.subscription else None,
                subscription_plan_type=state.subscription.plan_type if state.subscription else None,
                subscription_expires_at=datetime.fromisoformat(state.subscription.expires_at) if state.subscription and state.subscription.expires_at else None,
                subscription_features=state.subscription.features if state.subscription else {},
                last_verified_at=datetime.fromisoformat(state.last_verified_at) if state.last_verified_at else None,
                source=DataSource(state.source.value),
                confidence=state.confidence,
                freshness=FreshnessStatus(state.freshness.value),
                metadata=state.metadata,
            )
            self.db.add(model)
        
        await self.db.commit()
        await self.db.refresh(model)
        
        return self._model_to_contract(model)

    async def delete_account_state(
        self,
        profile_id: str,
        platform: MarketplacePlatform,
    ) -> bool:
        """Delete account state."""
        result = await self.db.execute(
            select(MarketplaceAccountStateModel).where(
                and_(
                    MarketplaceAccountStateModel.profile_id == profile_id,
                    MarketplaceAccountStateModel.platform == platform.value
                )
            )
        )
        model = result.scalar_one_or_none()
        
        if not model:
            return False
        
        await self.db.delete(model)
        await self.db.commit()
        return True

    async def get_all_account_states(
        self,
        profile_id: str,
    ) -> Dict[MarketplacePlatform, AccountStateContract]:
        """Get all account states for a profile."""
        result = await self.db.execute(
            select(MarketplaceAccountStateModel).where(
                MarketplaceAccountStateModel.profile_id == profile_id
            )
        )
        models = result.scalars().all()
        
        return {
            MarketplacePlatform(model.platform): self._model_to_contract(model)
            for model in models
        }

    def _model_to_contract(self, model: MarketplaceAccountStateModel) -> AccountStateContract:
        """Convert database model to contract."""
        subscription = None
        if model.subscription_plan_name:
            subscription = SubscriptionPlan(
                plan_name=model.subscription_plan_name,
                plan_type=model.subscription_plan_type,
                expires_at=model.subscription_expires_at.isoformat() if model.subscription_expires_at else None,
                features=model.subscription_features or {},
            )
        
        return AccountStateContract(
            platform=MarketplacePlatform(model.platform),
            account_id=model.account_id,
            account_status=AccountStatus(model.account_status.value),
            credits=CreditBalance(
                available=model.credits_available,
                pending=model.credits_pending,
                used=model.credits_used,
                limit=model.credits_limit,
                currency=model.credits_currency,
            ),
            wallet=WalletBalance(
                available=float(model.wallet_available) if model.wallet_available else None,
                currency=model.wallet_currency,
            ),
            subscription=subscription,
            last_verified_at=model.last_verified_at.isoformat() if model.last_verified_at else None,
            source=DataSource(model.source.value),
            confidence=model.confidence,
            freshness=FreshnessStatus(model.freshness.value),
            metadata=model.metadata or {},
        )


class DatabaseMarketplaceJobRepository(MarketplaceJobRepository):
    """Database implementation of Marketplace Job repository."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_job(
        self,
        profile_id: str,
        job_id: str,
    ) -> Optional[NormalizedJob]:
        """Get job by ID."""
        result = await self.db.execute(
            select(MarketplaceJobModel).where(
                and_(
                    MarketplaceJobModel.profile_id == profile_id,
                    MarketplaceJobModel.job_id == job_id
                )
            )
        )
        model = result.scalar_one_or_none()
        
        if not model:
            return None
        
        return self._model_to_contract(model)

    async def save_job(
        self,
        profile_id: str,
        job: NormalizedJob,
    ) -> NormalizedJob:
        """Save or update job."""
        result = await self.db.execute(
            select(MarketplaceJobModel).where(
                and_(
                    MarketplaceJobModel.profile_id == profile_id,
                    MarketplaceJobModel.platform == job.platform.value,
                    MarketplaceJobModel.platform_job_id == job.platform_job_id
                )
            )
        )
        model = result.scalar_one_or_none()
        
        if model:
            # Update existing
            model.title = job.title
            model.description = job.description
            model.budget_min = float(job.budget_min) if job.budget_min else None
            model.budget_max = float(job.budget_max) if job.budget_max else None
            model.budget_type = job.budget_type
            model.currency = job.currency
            model.client_info = job.client_info
            model.skills_required = job.skills_required
            model.job_type = job.job_type
            model.duration = job.duration
            model.posted_date = job.posted_date
            model.deadline = job.deadline
            model.url = job.url
            model.platform_cost = job.platform_cost.__dict__ if job.platform_cost else None
            model.metadata = job.metadata
            model.synced_at = datetime.utcnow()
            model.updated_at = datetime.utcnow()
        else:
            # Create new
            model = MarketplaceJobModel(
                profile_id=profile_id,
                job_id=job.job_id,
                platform=job.platform.value,
                platform_job_id=job.platform_job_id,
                title=job.title,
                description=job.description,
                budget_min=float(job.budget_min) if job.budget_min else None,
                budget_max=float(job.budget_max) if job.budget_max else None,
                budget_type=job.budget_type,
                currency=job.currency,
                client_info=job.client_info,
                skills_required=job.skills_required,
                job_type=job.job_type,
                duration=job.duration,
                posted_date=job.posted_date,
                deadline=job.deadline,
                url=job.url,
                platform_cost=job.platform_cost.__dict__ if job.platform_cost else None,
                metadata=job.metadata,
                synced_at=datetime.utcnow(),
            )
            self.db.add(model)
        
        await self.db.commit()
        await self.db.refresh(model)
        
        return self._model_to_contract(model)

    async def delete_job(
        self,
        profile_id: str,
        job_id: str,
    ) -> bool:
        """Delete job."""
        result = await self.db.execute(
            select(MarketplaceJobModel).where(
                and_(
                    MarketplaceJobModel.profile_id == profile_id,
                    MarketplaceJobModel.job_id == job_id
                )
            )
        )
        model = result.scalar_one_or_none()
        
        if not model:
            return False
        
        await self.db.delete(model)
        await self.db.commit()
        return True

    async def get_all_jobs(
        self,
        profile_id: str,
        platform: Optional[MarketplacePlatform] = None,
        limit: int = 100,
    ) -> List[NormalizedJob]:
        """Get all jobs for a profile, optionally filtered by platform."""
        query = select(MarketplaceJobModel).where(
            MarketplaceJobModel.profile_id == profile_id
        )
        
        if platform:
            query = query.where(MarketplaceJobModel.platform == platform.value)
        
        query = query.limit(limit)
        
        result = await self.db.execute(query)
        models = result.scalars().all()
        
        return [self._model_to_contract(model) for model in models]

    async def get_job_by_platform_id(
        self,
        profile_id: str,
        platform: MarketplacePlatform,
        platform_job_id: str,
    ) -> Optional[NormalizedJob]:
        """Get job by platform-specific job ID."""
        result = await self.db.execute(
            select(MarketplaceJobModel).where(
                and_(
                    MarketplaceJobModel.profile_id == profile_id,
                    MarketplaceJobModel.platform == platform.value,
                    MarketplaceJobModel.platform_job_id == platform_job_id
                )
            )
        )
        model = result.scalar_one_or_none()
        
        if not model:
            return None
        
        return self._model_to_contract(model)

    def _model_to_contract(self, model: MarketplaceJobModel) -> NormalizedJob:
        """Convert database model to contract."""
        from app.marketplace.contracts import PlatformCost, CreditType
        
        platform_cost = None
        if model.platform_cost:
            platform_cost = PlatformCost(
                credit_type=CreditType(model.platform_cost.get("credit_type", CreditType.CONNECTS)),
                amount=model.platform_cost.get("amount", 0.0),
                currency=model.platform_cost.get("currency", "USD"),
                is_free=model.platform_cost.get("is_free", False),
                description=model.platform_cost.get("description", ""),
            )
        
        return NormalizedJob(
            job_id=model.job_id,
            platform=MarketplacePlatform(model.platform),
            platform_job_id=model.platform_job_id,
            title=model.title,
            description=model.description,
            budget_min=float(model.budget_min) if model.budget_min else None,
            budget_max=float(model.budget_max) if model.budget_max else None,
            budget_type=model.budget_type,
            currency=model.currency,
            client_info=model.client_info or {},
            skills_required=model.skills_required or [],
            job_type=model.job_type,
            duration=model.duration,
            posted_date=model.posted_date,
            deadline=model.deadline,
            url=model.url,
            platform_cost=platform_cost,
            metadata=model.metadata or {},
        )


class DatabaseMarketplaceJobAssessmentRepository(MarketplaceJobAssessmentRepository):
    """Database implementation of Marketplace Job Assessment repository."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_assessment(
        self,
        profile_id: str,
        job_id: str,
    ) -> Optional[Dict]:
        """Get job assessment."""
        result = await self.db.execute(
            select(MarketplaceJobAssessmentModel).where(
                and_(
                    MarketplaceJobAssessmentModel.profile_id == profile_id,
                    MarketplaceJobAssessmentModel.job_id == job_id
                )
            )
        )
        model = result.scalar_one_or_none()
        
        if not model:
            return None
        
        return self._model_to_dict(model)

    async def save_assessment(
        self,
        profile_id: str,
        job_id: str,
        assessment: Dict,
    ) -> Dict:
        """Save or update job assessment."""
        result = await self.db.execute(
            select(MarketplaceJobAssessmentModel).where(
                and_(
                    MarketplaceJobAssessmentModel.profile_id == profile_id,
                    MarketplaceJobAssessmentModel.job_id == job_id
                )
            )
        )
        model = result.scalar_one_or_none()
        
        if model:
            # Update existing
            model.knowledge_match_score = assessment.get("knowledge_match_score", 0.0)
            model.evidence_match_score = assessment.get("evidence_match_score", 0.0)
            model.execution_match_score = assessment.get("execution_match_score", 0.0)
            model.overall_readiness_score = assessment.get("overall_readiness_score", 0.0)
            model.win_probability = assessment.get("win_probability", 0.0)
            model.recommended_action = assessment.get("recommended_action")
            model.blockers = assessment.get("blockers", [])
            model.strengths = assessment.get("strengths", [])
            model.recommendations = assessment.get("recommendations", [])
            model.assessed_at = datetime.utcnow()
            model.assessment_version = assessment.get("assessment_version", "1.0")
            model.metadata = assessment.get("metadata", {})
            model.updated_at = datetime.utcnow()
        else:
            # Create new
            model = MarketplaceJobAssessmentModel(
                profile_id=profile_id,
                job_id=job_id,
                knowledge_match_score=assessment.get("knowledge_match_score", 0.0),
                evidence_match_score=assessment.get("evidence_match_score", 0.0),
                execution_match_score=assessment.get("execution_match_score", 0.0),
                overall_readiness_score=assessment.get("overall_readiness_score", 0.0),
                win_probability=assessment.get("win_probability", 0.0),
                recommended_action=assessment.get("recommended_action"),
                blockers=assessment.get("blockers", []),
                strengths=assessment.get("strengths", []),
                recommendations=assessment.get("recommendations", []),
                assessed_at=datetime.utcnow(),
                assessment_version=assessment.get("assessment_version", "1.0"),
                metadata=assessment.get("metadata", {}),
            )
            self.db.add(model)
        
        await self.db.commit()
        await self.db.refresh(model)
        
        return self._model_to_dict(model)

    async def delete_assessment(
        self,
        profile_id: str,
        job_id: str,
    ) -> bool:
        """Delete job assessment."""
        result = await self.db.execute(
            select(MarketplaceJobAssessmentModel).where(
                and_(
                    MarketplaceJobAssessmentModel.profile_id == profile_id,
                    MarketplaceJobAssessmentModel.job_id == job_id
                )
            )
        )
        model = result.scalar_one_or_none()
        
        if not model:
            return False
        
        await self.db.delete(model)
        await self.db.commit()
        return True

    async def get_all_assessments(
        self,
        profile_id: str,
    ) -> List[Dict]:
        """Get all assessments for a profile."""
        result = await self.db.execute(
            select(MarketplaceJobAssessmentModel).where(
                MarketplaceJobAssessmentModel.profile_id == profile_id
            )
        )
        models = result.scalars().all()
        
        return [self._model_to_dict(model) for model in models]

    def _model_to_dict(self, model: MarketplaceJobAssessmentModel) -> Dict:
        """Convert database model to dictionary."""
        return {
            "knowledge_match_score": model.knowledge_match_score,
            "evidence_match_score": model.evidence_match_score,
            "execution_match_score": model.execution_match_score,
            "overall_readiness_score": model.overall_readiness_score,
            "win_probability": model.win_probability,
            "recommended_action": model.recommended_action,
            "blockers": model.blockers or [],
            "strengths": model.strengths or [],
            "recommendations": model.recommendations or [],
            "assessed_at": model.assessed_at.isoformat() if model.assessed_at else None,
            "assessment_version": model.assessment_version,
            "metadata": model.metadata or {},
        }


class DatabaseMarketplaceApplicationRepository(MarketplaceApplicationRepository):
    """Database implementation of Marketplace Application repository."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_application(
        self,
        profile_id: str,
        application_id: str,
    ) -> Optional[NormalizedApplication]:
        """Get application by ID."""
        result = await self.db.execute(
            select(MarketplaceApplicationModel).where(
                and_(
                    MarketplaceApplicationModel.profile_id == profile_id,
                    MarketplaceApplicationModel.application_id == application_id
                )
            )
        )
        model = result.scalar_one_or_none()
        
        if not model:
            return None
        
        return self._model_to_contract(model)

    async def save_application(
        self,
        profile_id: str,
        application: NormalizedApplication,
    ) -> NormalizedApplication:
        """Save or update application."""
        result = await self.db.execute(
            select(MarketplaceApplicationModel).where(
                MarketplaceApplicationModel.application_id == application.application_id
            )
        )
        model = result.scalar_one_or_none()
        
        if model:
            # Update existing
            model.job_id = application.job_id
            model.platform = application.platform.value
            model.platform_job_id = application.platform_job_id
            model.platform_application_id = application.platform_application_id
            model.status = ApplicationStatus(application.status.value)
            model.status_history = application.metadata.get("status_history", []) if hasattr(application, 'metadata') else []
            model.proposal_text = application.proposal_text
            model.cover_letter = application.cover_letter
            model.attachments = application.attachments
            model.bid_amount = float(application.bid_amount) if application.bid_amount else None
            model.currency = application.currency
            model.submitted_at = application.submitted_at
            model.metadata = application.metadata
            model.updated_at = datetime.utcnow()
        else:
            # Create new
            model = MarketplaceApplicationModel(
                profile_id=profile_id,
                application_id=application.application_id,
                job_id=application.job_id,
                platform=application.platform.value,
                platform_job_id=application.platform_job_id,
                platform_application_id=application.platform_application_id,
                status=ApplicationStatus(application.status.value),
                status_history=application.metadata.get("status_history", []) if hasattr(application, 'metadata') else [],
                proposal_text=application.proposal_text,
                cover_letter=application.cover_letter,
                attachments=application.attachments,
                bid_amount=float(application.bid_amount) if application.bid_amount else None,
                currency=application.currency,
                submitted_at=application.submitted_at,
                metadata=application.metadata,
            )
            self.db.add(model)
        
        await self.db.commit()
        await self.db.refresh(model)
        
        return self._model_to_contract(model)

    async def delete_application(
        self,
        profile_id: str,
        application_id: str,
    ) -> bool:
        """Delete application."""
        result = await self.db.execute(
            select(MarketplaceApplicationModel).where(
                and_(
                    MarketplaceApplicationModel.profile_id == profile_id,
                    MarketplaceApplicationModel.application_id == application_id
                )
            )
        )
        model = result.scalar_one_or_none()
        
        if not model:
            return False
        
        await self.db.delete(model)
        await self.db.commit()
        return True

    async def get_all_applications(
        self,
        profile_id: str,
        job_id: Optional[str] = None,
        status: Optional[ApplicationStatus] = None,
    ) -> List[NormalizedApplication]:
        """Get all applications for a profile, optionally filtered."""
        query = select(MarketplaceApplicationModel).where(
            MarketplaceApplicationModel.profile_id == profile_id
        )
        
        if job_id:
            query = query.where(MarketplaceApplicationModel.job_id == job_id)
        
        if status:
            query = query.where(MarketplaceApplicationModel.status == ApplicationStatus(status.value))
        
        result = await self.db.execute(query)
        models = result.scalars().all()
        
        return [self._model_to_contract(model) for model in models]

    async def get_application_by_platform_id(
        self,
        profile_id: str,
        platform: MarketplacePlatform,
        platform_application_id: str,
    ) -> Optional[NormalizedApplication]:
        """Get application by platform-specific application ID."""
        result = await self.db.execute(
            select(MarketplaceApplicationModel).where(
                and_(
                    MarketplaceApplicationModel.profile_id == profile_id,
                    MarketplaceApplicationModel.platform == platform.value,
                    MarketplaceApplicationModel.platform_application_id == platform_application_id
                )
            )
        )
        model = result.scalar_one_or_none()
        
        if not model:
            return None
        
        return self._model_to_contract(model)

    def _model_to_contract(self, model: MarketplaceApplicationModel) -> NormalizedApplication:
        """Convert database model to contract."""
        metadata = model.metadata or {}
        if model.status_history:
            metadata["status_history"] = model.status_history
        
        return NormalizedApplication(
            application_id=model.application_id,
            platform=MarketplacePlatform(model.platform),
            job_id=model.job_id,
            platform_job_id=model.platform_job_id,
            platform_application_id=model.platform_application_id,
            status=ApplicationStatus(model.status.value),
            submitted_at=model.submitted_at,
            proposal_text=model.proposal_text,
            cover_letter=model.cover_letter,
            attachments=model.attachments or [],
            bid_amount=float(model.bid_amount) if model.bid_amount else None,
            currency=model.currency,
            metadata=metadata,
        )


class DatabaseMarketplaceActiveWorkRepository(MarketplaceActiveWorkRepository):
    """Database implementation of Marketplace Active Work repository."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_active_work(
        self,
        profile_id: str,
        work_id: str,
    ) -> Optional[Dict]:
        """Get active work by ID."""
        result = await self.db.execute(
            select(MarketplaceActiveWorkModel).where(
                and_(
                    MarketplaceActiveWorkModel.profile_id == profile_id,
                    MarketplaceActiveWorkModel.work_id == work_id
                )
            )
        )
        model = result.scalar_one_or_none()
        
        if not model:
            return None
        
        return self._model_to_dict(model)

    async def save_active_work(
        self,
        profile_id: str,
        work: Dict,
    ) -> Dict:
        """Save or update active work."""
        result = await self.db.execute(
            select(MarketplaceActiveWorkModel).where(
                MarketplaceActiveWorkModel.work_id == work["work_id"]
            )
        )
        model = result.scalar_one_or_none()
        
        if model:
            # Update existing
            model.application_id = work.get("application_id")
            model.platform = work.get("platform")
            model.platform_work_id = work.get("platform_work_id")
            model.status = work.get("status", "active")
            model.title = work.get("title")
            model.description = work.get("description")
            model.total_amount = float(work["total_amount"]) if work.get("total_amount") else None
            model.currency = work.get("currency", "USD")
            model.hourly_rate = float(work["hourly_rate"]) if work.get("hourly_rate") else None
            model.started_at = datetime.fromisoformat(work["started_at"]) if work.get("started_at") else None
            model.completed_at = datetime.fromisoformat(work["completed_at"]) if work.get("completed_at") else None
            model.deadline = datetime.fromisoformat(work["deadline"]) if work.get("deadline") else None
            model.progress_percentage = work.get("progress_percentage", 0.0)
            model.milestones_completed = work.get("milestones_completed", 0)
            model.milestones_total = work.get("milestones_total")
            model.metadata = work.get("metadata", {})
            model.updated_at = datetime.utcnow()
        else:
            # Create new
            model = MarketplaceActiveWorkModel(
                application_id=work.get("application_id"),
                profile_id=profile_id,
                work_id=work["work_id"],
                platform=work.get("platform"),
                platform_work_id=work.get("platform_work_id"),
                status=work.get("status", "active"),
                title=work.get("title"),
                description=work.get("description"),
                total_amount=float(work["total_amount"]) if work.get("total_amount") else None,
                currency=work.get("currency", "USD"),
                hourly_rate=float(work["hourly_rate"]) if work.get("hourly_rate") else None,
                started_at=datetime.fromisoformat(work["started_at"]) if work.get("started_at") else None,
                completed_at=datetime.fromisoformat(work["completed_at"]) if work.get("completed_at") else None,
                deadline=datetime.fromisoformat(work["deadline"]) if work.get("deadline") else None,
                progress_percentage=work.get("progress_percentage", 0.0),
                milestones_completed=work.get("milestones_completed", 0),
                milestones_total=work.get("milestones_total"),
                metadata=work.get("metadata", {}),
            )
            self.db.add(model)
        
        await self.db.commit()
        await self.db.refresh(model)
        
        return self._model_to_dict(model)

    async def delete_active_work(
        self,
        profile_id: str,
        work_id: str,
    ) -> bool:
        """Delete active work."""
        result = await self.db.execute(
            select(MarketplaceActiveWorkModel).where(
                and_(
                    MarketplaceActiveWorkModel.profile_id == profile_id,
                    MarketplaceActiveWorkModel.work_id == work_id
                )
            )
        )
        model = result.scalar_one_or_none()
        
        if not model:
            return False
        
        await self.db.delete(model)
        await self.db.commit()
        return True

    async def get_all_active_work(
        self,
        profile_id: str,
        application_id: Optional[str] = None,
    ) -> List[Dict]:
        """Get all active work for a profile, optionally filtered."""
        query = select(MarketplaceActiveWorkModel).where(
            MarketplaceActiveWorkModel.profile_id == profile_id
        )
        
        if application_id:
            query = query.where(MarketplaceActiveWorkModel.application_id == application_id)
        
        result = await self.db.execute(query)
        models = result.scalars().all()
        
        return [self._model_to_dict(model) for model in models]

    def _model_to_dict(self, model: MarketplaceActiveWorkModel) -> Dict:
        """Convert database model to dictionary."""
        return {
            "work_id": model.work_id,
            "application_id": model.application_id,
            "platform": model.platform,
            "platform_work_id": model.platform_work_id,
            "status": model.status,
            "title": model.title,
            "description": model.description,
            "total_amount": float(model.total_amount) if model.total_amount else None,
            "currency": model.currency,
            "hourly_rate": float(model.hourly_rate) if model.hourly_rate else None,
            "started_at": model.started_at.isoformat() if model.started_at else None,
            "completed_at": model.completed_at.isoformat() if model.completed_at else None,
            "deadline": model.deadline.isoformat() if model.deadline else None,
            "progress_percentage": model.progress_percentage,
            "milestones_completed": model.milestones_completed,
            "milestones_total": model.milestones_total,
            "metadata": model.metadata or {},
        }
