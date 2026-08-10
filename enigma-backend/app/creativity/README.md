# Creativity & Opportunity Strategy Engine

Domain-agnostic creativity engine for identifying alternative strategies when Enigma encounters constraints during opportunity evaluation.

## Purpose

The Creativity Engine generates strategy candidates to improve opportunity success probability when facing constraints such as:

- Weak portfolio
- No reviews
- Low evidence
- Low readiness
- High competition
- Low budget
- High application cost
- Knowledge gaps
- Stale knowledge
- Execution limitations
- Weak positioning
- Low confidence

## Architecture Position

The Creativity Engine sits after economics and before decision:

```
Marketplace / Client Work
        ↓
Work Specification
        ↓
Expert Domain
        ↓
Knowledge / Evidence
        ↓
Readiness
        ↓
Economics
        ↓
Risk / Scope
        ↓
Creativity Engine
        ↓
Creative Strategies
        ↓
Decision Engine
        ↓
ACCEPT / REJECT / CONDITIONS
        ↓
Execution
```

## Core Principle

Creativity means:

1. **Constraint** → Understand why it is a constraint
2. **Generate** → Alternative strategies
3. **Evaluate** → Strategy feasibility
4. **Assess** → Economic impact
5. **Measure** → Risk
6. **Check** → Evidence requirements
7. **Return** → Ranked strategy candidates

The engine never directly approves or rejects work. It produces strategy candidates for the Decision Engine.

## Components

### Contracts (`contracts.py`)

Core contracts for the creativity system:

- `CreativeConstraint` - Represents a limiting factor
- `CreativeStrategy` - A potential solution strategy
- `StrategyEvaluation` - Evaluation of a strategy
- `CreativeOpportunityContext` - Normalized context for reasoning
- `CreativityResult` - Final result with ranked strategies

### Constraints (`constraints.py`)

Detects and manages constraints from opportunity context:

- `ConstraintDetector` - Identifies constraints from context
- Constraint types: NO_PORTFOLIO, NO_REVIEWS, LOW_EVIDENCE, HIGH_COMPETITION, etc.
- Severity levels: BLOCKING, HIGH, MEDIUM, LOW

### Strategies (`strategies.py`)

Predefined domain-agnostic strategies:

- `StrategyLibrary` - Collection of available strategies
- Strategy categories: PRICE_ADJUSTMENT, SCOPE_REDUCTION, PROOF_OF_WORK, etc.
- Each strategy includes: target constraints, requirements, effects, complexity

### Evaluation (`evaluation.py`)

Deterministic strategy evaluation:

- `StrategyEvaluator` - Scores strategies against context
- Evaluation dimensions: benefit, feasibility, economic viability, risk, confidence
- Provides explainable scoring with reasons

### Ranking (`ranking.py`)

Deterministic strategy ranking:

- `StrategyRanker` - Sorts strategies by overall score
- Supports filtering by threshold and category
- Returns top N strategies

### Engine (`engine.py`)

Main creativity engine:

- `CreativityEngine` - Orchestrates constraint detection, strategy generation, evaluation, ranking
- Respects economics, knowledge freshness, and evidence governance
- Never fabricates evidence or bypasses governance

### Registry (`registry.py`)

Strategy management:

- `CreativityRegistry` - Manages strategy registration and retrieval
- Indexes strategies by constraint, category, and domain
- Supports custom strategy providers

## Governance Compliance

The Creativity Engine:

- **Never** fabricates portfolio items, reviews, or evidence
- **Never** bypasses Knowledge Governance
- **Never** bypasses Evidence Governance
- **Never** bypasses Decision Layer authority
- **Always** respects economic viability
- **Always** respects knowledge freshness
- **Always** provides explainable reasoning

## Economics Integration

The engine consumes `MarketplaceEconomicsContract` and considers:

- Expected value vs application cost
- Economic viability of strategies
- Platform-specific economics
- Budget constraints

Strategies that destroy economic viability are penalized or rejected.

## Knowledge Freshness Integration

The engine identifies when research is the creative solution:

- Stale knowledge triggers RESEARCH_FIRST strategy
- Low confidence may trigger learning requirements
- Knowledge gaps trigger LEARNING_FIRST strategy

## Usage Example

```python
from app.creativity.engine import CreativityEngine
from app.creativity.contracts import CreativeOpportunityContext

# Create context
context = CreativeOpportunityContext(
    portfolio_strength=0.2,
    review_strength=0.1,
    competition_level=0.8,
    budget=50.0,
    application_cost=8.0,
    expected_value=40.0,
)

# Generate strategies
engine = CreativityEngine()
result = engine.generate_strategies(context)

# Access results
for evaluation in result.ranked_strategies:
    print(f"{evaluation.strategy.name}: {evaluation.overall_score:.2f}")
    print(f"  Reason: {evaluation.recommendation_reason}")
```

## Future Extensions

The architecture supports:

- AI-based creativity providers behind the same contract
- Domain-specific strategy packs
- Custom strategy providers
- LLM integration for strategy generation

## Testing

Run creativity tests:

```bash
pytest tests/creativity -q
```

Run marketplace regression:

```bash
pytest tests/marketplace -q
```

Run full regression:

```bash
pytest tests/ -q
```
