import pytest

from app.learning.competitor_curriculum import CompetitorResearchTrainingRunner
from app.learning.curriculum import KeywordResearchTrainingRunner, TrainingMode
from app.learning.product_verification_curriculum import ProductVerificationTrainingRunner
from app.learning.runner_registry import (
    RunnerNotRegisteredError,
    capability_runner_registry,
)


def test_keyword_runner_resolves_from_registry():
    runner = capability_runner_registry.resolve("keyword_research")
    assert isinstance(runner, KeywordResearchTrainingRunner)
    assert runner.capability == "keyword_research"


def test_competitor_runner_resolves_from_registry():
    runner = capability_runner_registry.resolve("competitor_research")
    assert isinstance(runner, CompetitorResearchTrainingRunner)
    assert runner.capability == "competitor_research"


def test_product_verification_runner_resolves_from_registry():
    runner = capability_runner_registry.resolve(
        "product_verification", target_id="owned-product", plan_id="dev-plan"
    )
    assert isinstance(runner, ProductVerificationTrainingRunner)
    assert runner.capability == "product_verification"


def test_unsupported_capability_fails_cleanly():
    with pytest.raises(RunnerNotRegisteredError):
        capability_runner_registry.resolve("not_registered")


@pytest.mark.parametrize("mode", list(TrainingMode))
@pytest.mark.parametrize("capability", ["keyword_research", "competitor_research"])
def test_all_training_modes_resolve_without_duplicate_runners(capability, mode):
    runner = capability_runner_registry.resolve(capability, mode=mode)
    assert runner.mode == mode
    assert runner.capability == capability


def test_registry_contains_exactly_the_verified_learning_capabilities():
    assert set(capability_runner_registry.registered_capabilities()) == {
        "keyword_research", "competitor_research", "product_verification",
    }
