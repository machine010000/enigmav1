# TASK-050 Persistence Audit

## In-Memory State (Self._* variables)

### Academy
- **academy_manager.py**: `_cache: Dict[str, AcademyModule]` - Module cache
  - **Status**: SAFE TO KEEP (runtime cache, can be rebuilt from registry)
  - **Deployment**: No action needed

- **academy_registry.py**: `_modules: Dict[str, AcademyModule]` - Module registry
  - **Status**: REQUIRED FOR DEPLOY (core data structure)
  - **Deployment**: Keep as in-memory registry (acceptable for academy modules)

### AI Gateway
- **ai/gateway.py**: `_provider: LLMProvider` - LLM provider instance
  - **Status**: REQUIRED FOR DEPLOY (singleton provider)
  - **Deployment**: Keep as singleton (acceptable)

- **ai/master_brain/state.py**: `_event_state_order` - Event order configuration
  - **Status**: SAFE TO KEEP (static configuration)
  - **Deployment**: No action needed

### Marketplace Mock
- **marketplace/mock_adapter.py**: Multiple `_` variables for mock state
  - `_authenticated: bool`
  - `_account: Optional[MarketplaceAccount]`
  - `_jobs: Dict[str, NormalizedJob]`
  - `_applications: Dict[str, NormalizedApplication]`
  - `_job_counter: int`
  - `_application_counter: int`
  - **Status**: MUST BE REPLACED BEFORE LIVE API (test-only mock)
  - **Deployment**: Do not use in production

### Time Intelligence
- **time_intelligence/timezone_service.py**: `_timezone_cache: Dict[str, ZoneInfo]`
  - **Status**: SAFE TO KEEP (performance cache)
  - **Deployment**: Keep as cache (acceptable)

### Enigma Profile
- **enigma_profile/knowledge_progress.py**: `_progress: Dict[str, KnowledgeProgress]`
  - **Status**: MUST BE REPLACED BEFORE LIVE API (needs persistence)
  - **Deployment**: Requires database persistence

- **enigma_profile/training_tracker.py**: `_training_items: List[TrainingItem]`
  - **Status**: MUST BE REPLACED BEFORE LIVE API (needs persistence)
  - **Deployment**: Requires database persistence

- **enigma_profile/platform_intelligence.py**: `_platform_readiness: Dict[MarketplacePlatform, PlatformReadiness]`
  - **Status**: MUST BE REPLACED BEFORE LIVE API (needs persistence)
  - **Deployment**: Requires database persistence

- **enigma_profile/development_engine.py**: `_priorities: List[DevelopmentPriority]`
  - **Status**: MUST BE REPLACED BEFORE LIVE API (needs persistence)
  - **Deployment**: Requires database persistence

- **enigma_profile/issue_intelligence.py**: `_issues: Dict[str, Issue]`
  - **Status**: MUST BE REPLACED BEFORE LIVE API (needs persistence)
  - **Deployment**: Requires database persistence

- **enigma_profile/customer_time.py**: `_customer_timezones: Dict[str, TimezoneInfo]`
  - **Status**: MUST BE REPLACED BEFORE LIVE API (needs persistence)
  - **Deployment**: Requires database persistence

### Pipeline
- **pipeline/orchestrator.py**: Multiple engine instances
  - `self.creativity_engine`
  - `self.account_economics_engine`
  - `self.customer_time_analyzer`
  - `self.deadline_analyzer`
  - `self.working_hours_analyzer`
  - `self.enigma_profile_manager`
  - **Status**: SAFE TO KEEP (stateless services)
  - **Deployment**: Keep as instances (acceptable)

## Localhost Dependencies

### config.py
- **Line 37**: `REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")`
  - **Status**: MUST BE REPLACED (production hardcoded localhost)
  - **Deployment**: Use environment variable

- **Line 42**: `UPWORK_REDIRECT_URI: str = os.getenv("UPWORK_REDIRECT_URI", "http://localhost:8000/callback")`
  - **Status**: MUST BE REPLACED (production hardcoded localhost)
  - **Deployment**: Use environment variable

- **Line 45**: `CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")`
  - **Status**: MUST BE REPLACED (production hardcoded localhost)
  - **Deployment**: Use environment variable

## Summary

### Required for Deploy (Keep)
- Academy registry and cache
- AI gateway provider
- Timezone service cache
- Pipeline orchestrator engines

### Must Be Replaced Before Live API
- Mock marketplace adapter (test-only)
- Enigma Profile persistence (all modules)
- Localhost defaults in config

### Safe to Keep (No Action)
- Static configurations
- Performance caches
- Stateless services
