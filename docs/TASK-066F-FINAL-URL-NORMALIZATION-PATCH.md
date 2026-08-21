# TASK-066F — Final URL Normalization Consistency Patch

## Outcome

The remaining TASK-066E blocker is fixed and the patch is **ready for independent validation**.

Work was performed in the detached TASK-066 worktree based on:

- baseline: `90d244f7d6d6e59356490386eff6275de976a75b`
- parent baseline: `f51c55cac34503f35fd14ddad4abbece7a68e494`
- no stage, commit, push, merge, rebase, cherry-pick, or PR was performed
- no external marketplace, production service, or real database was contacted

## Root cause

Runtime dedupe called `normalize_source_url()` before calculating `canonical_dedupe_key()`. Migration 012 instead calculated MD5 from the URL stored in the row without applying runtime URL normalization. A historical URL containing runtime-equivalent differences—such as whitespace, scheme/host casing, a default port, trailing slash, fragment, tracking query keys, or query ordering—could therefore receive a different backfilled key from a new create.

The unique database index could not prevent an old-vs-new duplicate when the migration and runtime produced different keys.

## Authoritative runtime normalization path

The one authoritative implementation now lives in:

`app.freelancing.manual_dedupe.normalize_source_url()`

Both runtime manual intake and migration 013 import that exact function. Existing public imports from `app.freelancing.manual_intake` continue to work because the functions are imported into that module under their original names.

The behavior was preserved, not broadened:

- trim surrounding whitespace
- require an absolute HTTP or HTTPS URL
- lowercase scheme and hostname
- omit default ports 80/443 while preserving non-default ports
- remove trailing path slashes, retaining `/` for the root
- remove fragments
- parse query pairs while preserving blank values
- remove only query keys whose names begin with `utm_`, case-insensitively
- sort remaining query pairs and encode them with Python `urlencode`

`canonical_dedupe_key()`, external-ID normalization, and fallback fingerprinting were moved with the normalizer into the same pure module so runtime and migration share a single canonical identity contract. No independent AI, provider, lifecycle, or storage architecture was introduced.

## Migration strategy

Added revision:

`013_runtime_url_canonical_dedupe`

Revision chain:

`012_canonical_manual_dedupe -> 013_runtime_url_canonical_dedupe (head)`

Upgrade behavior:

1. Drop `uq_marketplace_jobs_manual_dedupe` inside the migration transaction.
2. Read manual opportunities in ascending database `id` order.
3. Normalize each stored URL with the exact runtime function.
4. Recompute each key with the exact runtime `canonical_dedupe_key()` function and identity priority.
5. Update the stored URL to its canonical runtime representation.
6. Recreate the unique `(profile_id, manual_dedupe_key)` index.

Invalid historical URLs cause the transactional migration to fail rather than silently inventing an identity that runtime would reject.

Downgrade restores the pre-013 URL recorded in metadata and recomputes the migration-012 representation. Upgrade/downgrade/upgrade was exercised against an isolated in-memory database.

## Collision behavior and auditability

If canonicalization collapses multiple historical rows to the same `(profile_id, canonical_key)`:

- no row or business data is deleted
- the row with the lowest database `id` deterministically retains the canonical key
- later colliding rows receive `manual_dedupe_key = NULL`, compatible with the unique index
- the previous noncanonical URL is retained in `metadata.task_066f_pre_013_source_url`
- each collision row records the winner in `metadata.task_066f_collision_canonical_job_id`
- processed rows record `metadata.task_066f_canonicalized_by = 013_runtime_url_canonical_dedupe`
- existing metadata is preserved

Runtime duplicate lookup now checks the canonical dedupe key first. This returns the deterministic canonical winner before legacy URL/external-ID/fingerprint compatibility checks.

## Files changed

1. `enigma-backend/app/freelancing/manual_dedupe.py`
   - Added the pure shared authoritative normalization and canonical identity helpers.
2. `enigma-backend/app/freelancing/manual_intake.py`
   - Reuses the shared helpers while preserving existing imports/interfaces.
   - Checks `manual_dedupe_key` first during duplicate lookup.
3. `enigma-backend/alembic/versions/013_runtime_url_canonical_dedupe.py`
   - Adds transactional historical normalization, deterministic collision planning, audit metadata, and reversible URL restoration.
4. `enigma-backend/tests/test_066_manual_opportunity_intake.py`
   - Adds migration/runtime parity, historical collision, downgrade, isolated migration-cycle, and update duplicate-contract tests.
5. `docs/TASK-066F-FINAL-URL-NORMALIZATION-PATCH.md`
   - This report.

No frontend, lifecycle, Freelancer Chat, TASK-067, or marketplace-integration file was changed.

## Tests added

- Historical noncanonical URL produces the exact runtime key.
- Differently formatted runtime-equivalent URLs normalize to one URL/key.
- Canonical collisions retain all rows and identify the deterministic winner.
- Downgrade restores the audited pre-013 URL and migration-012 key behavior.
- Migration 013 executes upgrade/downgrade/upgrade against an isolated database.
- Updating a record to a runtime-equivalent existing URL raises the existing `DuplicateOpportunityError` contract before flush.
- Existing create/create and database-race tests continue to verify that raw `IntegrityError` is not exposed for recognized duplicates.

## Validation results

### Focused TASK-066 and URL/dedupe suite

Command:

```powershell
python -m pytest -p no:cacheprovider tests\test_066_manual_opportunity_intake.py -q
```

Result: **53 passed, 0 failed, 0 skipped**. One pre-existing Pydantic deprecation warning was emitted.

### Freelancer, durable, security, and package regression

The combined safe suite included:

- TASK-066 manual intake
- TASK-065 Freelancer discovery
- durable opportunity contract
- freelancing backend isolation/domain/negative/no-placeholder/runtime suites
- TASK-016 security
- TASK-017 capability intelligence
- application package and application package persistence

Result: **211 passed, 0 failed, 0 skipped**. The count includes the 53 focused tests.

### Migration validation

- `alembic heads`: `013_runtime_url_canonical_dedupe (head)`
- Alembic history confirms the linear `010 -> 011 -> 012 -> 013` chain.
- Migration 013 upgrade/downgrade/upgrade executed successfully in the focused test against an isolated in-memory database, including a real unique index and colliding historical rows.
- No production or external database was used.
- Migration 013 is data-dependent and deliberately invokes the Python runtime normalizer row-by-row; it therefore requires online migration execution and cannot be faithfully rendered as static offline SQL. The repository's full offline chain was already not renderable because migration 001 performs schema inspection.

### Repository validation

- `git diff --check`: passed; only line-ending conversion warnings were reported by Git.
- No frontend validation was rerun because no frontend file or frontend/backend response contract changed.
- No external connection or real ingestion occurred.

## Known limitations

- A PostgreSQL-backed disposable integration test remains desirable before deployment because the isolated migration-cycle test uses SQLite. The migration itself uses portable SQLAlchemy row selection/update and index operations, and no PostgreSQL-only data expression.
- Migration runtime is row-by-row to guarantee exact reuse of Python URL semantics. This favors correctness over bulk speed; migration duration should be observed if the manual-opportunity table becomes large.
- Invalid historical HTTP(S) data blocks migration transactionally and must be reviewed rather than silently reinterpreted.

## Readiness

The TASK-066E URL-normalization mismatch has been removed: migration 013 and runtime invoke the same canonical function, stored historical URLs are normalized, canonical winners remain protected by the database unique index, and create/update callers retain the deterministic duplicate contract.

**READY FOR INDEPENDENT VALIDATION.**
