# TASK-066D — Remaining Manual Intake Safety Patch

## Result

**READY FOR INDEPENDENT VALIDATION**

This patch closes only the remaining lifecycle and dedupe blockers reported by TASK-066C against `f51c55cac34503f35fd14ddad4abbece7a68e494`. It adds no Freelancer feature, Chat workflow, marketplace integration, TASK-067 code, or frontend change.

No stage, commit, push, merge, rebase, cherry-pick, or PR was performed. No real database, marketplace, production service, or credential was contacted.

## Lifecycle bypass root cause

`POST /api/freelancing/jobs/{job_id}/assess` loaded every `MarketplaceJob` under `enigma_profile`, including manual opportunities, and directly assigned a generic lifecycle (`ready`, `training_required`, `knowledge_missing`, or `verification_pending`). It did not identify manual ingestion or use the manual transition service. The `commit` transaction-control argument had also become a public FastAPI query parameter.

## Lifecycle fix

- Extracted the implementation into the internal `_assess_existing_job(..., commit=...)` helper.
- The public route no longer exposes `commit`.
- Generic assessment still creates/updates the durable `MarketplaceJobAssessment` and commits normally.
- Generic lifecycle mapping is skipped when `job.ingestion_source == "manual"`.
- Manual Save-and-Analyze and dedicated Analyze call the internal helper with `commit=False`, then perform the authorized `ready_for_analysis -> analyzed` transition through the existing TASK-066B `ManualOpportunityService.transition()`.
- No second state machine was introduced.

Regression tests execute the public assessment function against a terminal `won` manual opportunity, verify scoring persists/commits, and assert lifecycle remains `won`. A signature regression confirms the public route exposes no `commit` control.

## Dedupe mismatch root cause

Migration 011 stored raw `identity_fingerprint` as `manual_dedupe_key`, while runtime creation stored a SHA-256 hash of platform plus URL/external ID/fingerprint. Therefore pre-011 and post-011 representations could not collide in the unique index. Runtime lookup and key selection also disagreed for distinct external IDs, and update-side `IntegrityError` leaked instead of using the create duplicate contract.

## Canonical dedupe representation

One representation is now used by runtime and migration 012:

```text
MD5(lower(trim(platform)) + "|" + preferred_identity)
```

`preferred_identity` is selected in this exact order:

1. normalized stored HTTP(S) source URL;
2. external platform ID normalized with trim and lowercase;
3. existing stable `identity_fingerprint` fallback.

MD5 here is a deterministic identity digest, not a security primitive. The platform prefix prevents cross-platform collision. The 32-character result fits the existing 64-character column.

Runtime and SQL both use lowercase/trim for platform and external ID. Existing manual source URLs were already normalized by TASK-066 creation/update before persistence, so migration can reuse the stored URL exactly.

## Create/update/race handling

- New creates persist normalized external IDs and the canonical key.
- Duplicate reads compare legacy external IDs with SQL `lower(trim(platform_job_id))`.
- Updates recompute the same key whenever URL, external ID, title, client identity, or platform context changes.
- Update `IntegrityError` now rolls back, retrieves the canonical winner, and raises `DuplicateOpportunityError(existing_job_id)`, matching create behavior.
- The existing unique `(profile_id, manual_dedupe_key)` index remains the concurrency authority.
- URL takes precedence, so equal URL/different external ID requests collide.
- Equal normalized external ID variants collide within the same platform.

## Migration strategy

Migration 011 was not edited. New migration:

`011_manual_intake_safety -> 012_canonical_manual_dedupe`

Upgrade:

1. Drops the existing unique index.
2. Recomputes every manual row with the runtime-equivalent PostgreSQL `md5(...)` expression.
3. Ranks collisions by `(profile_id, manual_dedupe_key, id)`.
4. Retains the lowest-ID historical row as canonical and sets later historical duplicates to `NULL`.
5. Recreates the unique index.

This is deterministic and prevents migration failure on historical duplicates. A replay after upgrade collides with the retained canonical row. Null duplicate history remains readable but cannot become the canonical winner.

Downgrade restores the migration-011 identity-fingerprint representation, resolves historical collisions using the same lowest-ID rule, and recreates the index. Downgrade necessarily removes the canonical representation but does not delete opportunities.

## Files changed

- `enigma-backend/app/freelancing/manual_intake.py`
- `enigma-backend/app/routers/enigma_profile.py`
- `enigma-backend/app/routers/freelancing.py`
- `enigma-backend/alembic/versions/012_canonical_manual_dedupe.py`
- `enigma-backend/tests/test_066_manual_opportunity_intake.py`
- `docs/TASK-066D-REMAINING-SAFETY-PATCH.md`

Frontend V2 was not changed.

## Tests added

- external ID trim/case normalization;
- cross-platform key separation;
- equal URL/different external IDs produce one key;
- create uniqueness race returns canonical duplicate;
- update uniqueness race returns the same duplicate contract;
- migration 012 contains the same identity ordering and deterministic collision ranking;
- general assessment preserves a terminal manual lifecycle;
- public assessment route does not expose transaction-control input.

## Validation results

All backend tests used `PYTHONDONTWRITEBYTECODE=1`, `DEBUG=false`, an unreachable loopback PostgreSQL URL, and disabled pytest cache.

- Focused TASK-066/manual safety: **48 passed**, 0 failed.
- Combined TASK-066, TASK-065, Freelancer adapter/runtime/integration/negative/domain/isolation, durable opportunity, application package 050/051, security, and capability-intelligence regression: **224 passed**, 0 failed.
- Alembic head: single head `012_canonical_manual_dedupe`.
- Offline upgrade `011 -> 012`: passed.
- Offline downgrade `012 -> 011`: passed.
- Offline repeated upgrade `011 -> 012`: passed.
- `git diff --check`: passed with line-ending conversion warnings only.
- Frontend build/TypeScript: not rerun because no frontend file changed in TASK-066D; TASK-066C had already validated the unchanged committed frontend build and TypeScript.

One existing Pydantic V2 class-based Config deprecation warning remains unrelated.

## Remaining known issues

- No disposable PostgreSQL instance was configured, so migration and two-session concurrency were validated through offline SQL, database constraint inspection, deterministic `IntegrityError` simulations, and focused runtime tests rather than a live local PostgreSQL race.
- Historical duplicate rows intentionally receive a null canonical key while the lowest-ID row becomes the database-enforced winner. A future audited data-cleanup task may archive or merge those historical duplicates, but they no longer prevent migration or permit a new canonical duplicate.
- The fallback `identity_fingerprint` remains a separate descriptive ingestion field for existing discovery behavior; it is no longer an alternate manual uniqueness representation. Manual uniqueness authority is only `manual_dedupe_key`.

## Readiness

The TASK-066C blockers are closed in code and the result is ready for a clean detached independent validation, with a disposable PostgreSQL concurrency replay recommended when infrastructure is available.
