import pytest
from datetime import datetime

from app.engagement.pricing import (
    PricingModel,
    PricingModelType,
    PricingStatus,
    Currency,
    PricingProposal,
    PricingComponent,
    PricingAdjustment,
    PricingFramework,
)


class TestPricingModel:
    """Tests for PricingModel."""

    def test_pricing_model_creation(self):
        """Test creating a pricing model."""
        model = PricingModel(
            model_id="model1",
            model_type=PricingModelType.HOURLY,
            name="Hourly Model",
            description="Hourly pricing",
            currency=Currency.USD,
            base_rate=50.0,
            estimated_hours=10.0,
        )
        assert model.model_id == "model1"
        assert model.model_type == PricingModelType.HOURLY
        assert model.currency == Currency.USD


class TestPricingProposal:
    """Tests for PricingProposal."""

    def test_pricing_proposal_creation(self):
        """Test creating a pricing proposal."""
        from app.engagement.pricing import PricingModel
        model = PricingModel(
            model_id="model1",
            model_type=PricingModelType.FIXED,
            name="Fixed Model",
            description="Fixed pricing",
            currency=Currency.USD,
            total_amount=1000.0,
        )
        proposal = PricingProposal(
            proposal_id="proposal1",
            work_specification_id="work1",
            pricing_model=model,
            status=PricingStatus.DRAFT,
        )
        assert proposal.proposal_id == "proposal1"
        assert proposal.status == PricingStatus.DRAFT


class TestPricingFramework:
    """Tests for PricingFramework."""

    def test_framework_initialization(self):
        """Test framework initialization."""
        framework = PricingFramework()
        assert framework is not None

    def test_create_hourly_model(self):
        """Test creating an hourly pricing model."""
        framework = PricingFramework()
        model = framework.create_hourly_model(
            model_id="model1",
            name="Hourly Model",
            description="Hourly pricing",
            hourly_rate=50.0,
            estimated_hours=10.0,
        )
        assert model.model_type == PricingModelType.HOURLY
        assert model.base_rate == 50.0
        assert model.estimated_hours == 10.0

    def test_create_fixed_model(self):
        """Test creating a fixed pricing model."""
        framework = PricingFramework()
        model = framework.create_fixed_model(
            model_id="model1",
            name="Fixed Model",
            description="Fixed pricing",
            total_amount=1000.0,
        )
        assert model.model_type == PricingModelType.FIXED
        assert model.total_amount == 1000.0

    def test_register_model(self):
        """Test registering a pricing model."""
        framework = PricingFramework()
        model = framework.create_fixed_model(
            model_id="model1",
            name="Fixed Model",
            description="Fixed pricing",
            total_amount=1000.0,
        )
        result = framework.register_model(model)
        assert result is True

    def test_get_model(self):
        """Test getting a pricing model."""
        framework = PricingFramework()
        model = framework.create_fixed_model(
            model_id="model1",
            name="Fixed Model",
            description="Fixed pricing",
            total_amount=1000.0,
        )
        framework.register_model(model)
        retrieved = framework.get_model("model1")
        assert retrieved is not None
        assert retrieved.model_id == "model1"

    def test_calculate_total(self):
        """Test calculating total amount."""
        framework = PricingFramework()
        model = framework.create_hourly_model(
            model_id="model1",
            name="Hourly Model",
            description="Hourly pricing",
            hourly_rate=50.0,
            estimated_hours=10.0,
        )
        total = framework.calculate_total(model)
        assert total == 500.0
