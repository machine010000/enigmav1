# Enigma Profile

Enigma's internal operator intelligence profile for tracking knowledge, training, performance, and development.

## Purpose

Enigma Profile is NOT a user profile. It is Enigma's private admin intelligence profile for:
- Tracking knowledge domain progress (SEO, Technical SEO, etc.)
- Monitoring training and learning progress
- Assessing platform readiness (Upwork, Freelancer, Fiverr, etc.)
- Generating development priorities
- Tracking errors, issues, and failures
- Providing actionable development recommendations

## Architecture

### Core Components

- **contracts.py**: Core data structures and enums
- **knowledge_progress.py**: Knowledge domain progress tracking
- **training_tracker.py**: Training and learning progress tracking
- **platform_intelligence.py**: Marketplace platform readiness assessment
- **development_engine.py**: Development priority generation
- **issue_intelligence.py**: Error and issue tracking
- **profile.py**: Main Enigma Profile manager

### Design Principles

1. **No Fake Knowledge**: Missing knowledge ≠ expert
2. **No Fake Evidence**: Missing evidence ≠ portfolio
3. **No Silent Failures**: All issues are explicitly tracked
4. **Actionable Priorities**: Generates "what to improve next"
5. **Severity Classification**: Issues classified by severity

## Usage Examples

### Initialize Profile

```python
from app.enigma_profile.profile import EnigmaProfileManager

manager = EnigmaProfileManager()
profile = manager.initialize_default_profile()

print(manager.get_profile_summary())
```

### Track Knowledge Progress

```python
from app.enigma_profile.contracts import KnowledgeProgress
from app.enigma_profile.knowledge_progress import KnowledgeProgressTracker

tracker = KnowledgeProgressTracker()

progress = KnowledgeProgress(
    domain="SEO",
    knowledge_score=0.72,
    execution_score=0.48,
    evidence_score=0.35,
    confidence=0.61,
    readiness=0.52,
    last_verified="2026-08-10T00:00:00",
    freshness="fresh",
)

tracker.register_domain(progress)
readiness = tracker.calculate_readiness("SEO")
```

### Track Training

```python
from app.enigma_profile.contracts import TrainingItem, SkillLevel
from app.enigma_profile.training_tracker import TrainingTracker

tracker = TrainingTracker()

item = TrainingItem(
    skill="Technical SEO",
    level=SkillLevel.GROWING,
    started_at="2026-08-01T00:00:00",
    progress=0.45,
)

tracker.register_training(item)
tracker.update_progress("Technical SEO", 0.60)
```

### Platform Readiness

```python
from app.enigma_profile.platform_intelligence import PlatformIntelligence
from app.enigma_profile.contracts import PlatformReadiness
from app.marketplace.contracts import MarketplacePlatform

intelligence = PlatformIntelligence()

readiness = PlatformReadiness(
    platform=MarketplacePlatform.UPWORK,
    overall_readiness=0.43,
    knowledge_score=0.80,
    evidence_score=0.30,
    portfolio_score=0.10,
    execution_score=0.50,
    win_probability=0.40,
    economics_score=0.50,
    blockers=["No reviews", "Weak portfolio"],
    recommendations=["Build 3 proof-of-work assets"],
)

intelligence.register_platform_readiness(readiness)
summary = intelligence.generate_platform_summary(MarketplacePlatform.UPWORK)
```

### Issue Tracking

```python
from app.enigma_profile.issue_intelligence import IssueIntelligence
from app.enigma_profile.contracts import IssueType, IssueSeverity

intelligence = IssueIntelligence()

issue = intelligence.report_issue(
    source="system",
    type=IssueType.API,
    severity=IssueSeverity.HIGH,
    detected_reason="API timeout",
    impact="Cannot fetch account data",
    required_action="Retry or investigate API",
    platform=MarketplacePlatform.UPWORK,
)

critical_issues = intelligence.get_critical_issues()
```

### Development Priorities

```python
from app.enigma_profile.development_engine import DevelopmentEngine

engine = DevelopmentEngine(
    knowledge_tracker=knowledge_tracker,
    training_tracker=training_tracker,
    platform_intelligence=platform_intelligence,
)

priorities = engine.generate_priorities()
top_priorities = engine.get_top_priorities(limit=5)

for priority in top_priorities:
    print(f"{priority.priority}. {priority.title}")
    print(f"   {priority.description}")
```

## Knowledge Domains

Common tracked domains:
- SEO
- Keyword Research
- On-Page SEO
- Technical SEO
- Content Writing
- Proposal Writing
- Client Communication

## Platform Readiness

Tracked platforms:
- Upwork
- Freelancer
- Fiverr
- Mostaql
- Khamsat

Each platform includes:
- Overall readiness score
- Knowledge, evidence, portfolio, execution scores
- Win probability
- Economics score
- Current blockers
- Development recommendations

## Issue Classification

### Types
- SYSTEM: System errors
- API: API failures
- MARKETPLACE: Platform issues
- KNOWLEDGE: Knowledge gaps
- EXECUTION: Task failures
- BUSINESS: Business constraints
- CLIENT: Client issues

### Severity
- CRITICAL: Blocks all operations
- HIGH: Significant impact
- MEDIUM: Moderate impact
- LOW: Minor impact

## Integration with Pipeline

Enigma Profile integrates with the pipeline after Execution and Reflection:
- Marketplace → Work Spec → Economics → Account Economics → Knowledge/Evidence → Creativity → Decision → Execution → Reflection → Enigma Profile

## Testing

Tests cover:
- Knowledge progress tracking
- Training progress tracking
- Platform readiness assessment
- Development priority generation
- Issue tracking and classification
- Severity classification
- Stale knowledge detection
- Platform-specific blockers

## Negative Tests

- Missing knowledge ≠ expert
- Missing evidence ≠ portfolio
- Failed task ≠ success
- API failure ≠ healthy account
- Unknown platform economics ≠ free
