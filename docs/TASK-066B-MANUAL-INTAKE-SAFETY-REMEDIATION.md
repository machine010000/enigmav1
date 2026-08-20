# TASK-066B — Manual Intake Safety Remediation

## Result

**READY FOR INDEPENDENT VALIDATION**

The TASK-066 manual opportunity intake blockers identified by TASK-066A were remediated on `feature/manual-opportunity-intake` at starting SHA `b267beac9bccf734a97f4471e084e03af44efffd`. No TASK-067 code, Freelancer Chat, marketplace integration, automatic submission, or legacy frontend code was incorporated.

No stage, commit, push, merge, rebase, cherry-pick, or PR was performed. No real marketplace, production service, credential, or real database was contacted.

## Files changed

- `enigma-backend/alembic/versions/011_manual_intake_safety.py`
- `enigma-backend/app/freelancing/manual_intake.py`
- `enigma-backend/app/models/marketplace.py`
- `enigma-backend/app/routers/enigma_profile.py`
- `enigma-backend/app/routers/freelancing.py`
- `enigma-backend/tests/test_066_manual_opportunity_intake.py`
- `enigma-frontend-v2/app/components/freelancing-control-center.tsx`
- `docs/TASK-066B-MANUAL-INTAKE-SAFETY-REMEDIATION.md`

## Blockers and fixes

### 1. Original marketplace text immutability

Root cause: `ManualOpportunityService.update()` copied edited `original_description` into both `description` and `original_text`.

Fix:

- `original_text` is assigned only at creation.
- Later operator correction updates `description`, not `original_text`.
- Normalized requirements and translation metadata remain separate.
- Existing records remain readable through the existing `original_text or description` serialization fallback.
- Frontend editing uses the editable `description`, while the immutable original remains displayed separately.

Regression: an edit replacing the derived description asserts the initially pasted original remains byte-for-byte unchanged.

### 2. Lifecycle state machine

Root cause: PATCH accepted a caller-provided lifecycle and assigned it directly; outcomes were checked against a flat set without validating the source state.

Fix:

- Removed `lifecycle_status` from the general update request.
- Added a single server-side transition map and `ManualOpportunityService.transition()`.
- Valid path: `draft → ready_for_analysis → analyzed → proposal_prepared → manually_submitted`, then optional `client_replied`, then a terminal outcome.
- `won`, `lost`, `withdrawn`, and `expired` are terminal.
- Service calls and API commands both use the state machine.

Regression: parameterized direct-service invalid transitions and a complete valid path with terminal-state rejection.

### 3. Human approval and Submission Intent

Root cause: manual submission allowed `proposal_prepared`, did not persist the generated package ID, and did not verify package ownership/state or an active Submission Intent.

Fix:

- Proposal preparation persists `proposal_application_id` on the opportunity.
- Recording submission requires:
  - lifecycle `proposal_prepared`;
  - the linked package belongs to `current_user.id`;
  - package opportunity matches the manual job;
  - package state is `APPROVED`;
  - an owned `PENDING_EXTERNAL_SUBMISSION` intent exists for that package.
- The immutable manual snapshot stores both `application_id` and `submission_intent_id`.
- No external submission is attempted; the operation records only what the human submitted manually.
- Frontend does not show submission controls until a package is linked and explains the approval/intent prerequisite. Backend remains authoritative.

Regression: missing, unapproved, and intent-less paths fail; the successful path proves both IDs are snapshotted.

### 4. Transaction safety

Root cause: service methods committed internally, and Save-and-Analyze could commit creation before analysis failed.

Fix:

- Manual service write methods use `flush()` and do not commit.
- Endpoint/use-case boundaries own commit/rollback.
- Save-and-Analyze calls assessment with `commit=False`, flushes the assessment, transitions lifecycle, and commits once.
- `assess_existing_job()` preserves its public default (`commit=True`); only the manual atomic flow opts out.
- Update, submission, and outcome endpoints commit after all validation/writes and roll back handled failures.
- The uniqueness-race recovery performs rollback before querying the canonical winner.

Regression:

- Service test proves flush without intermediate commit.
- Endpoint test proves a partial create/analyze failure calls rollback and never commit.
- Existing package repositories already use flush, so proposal package creation participates in the caller transaction.

### 5. Concurrent duplicate detection

Root cause: SELECT-before-INSERT checks could race; fingerprint and normalized URL were not protected by a unique database key.

Fix:

- Added `manual_dedupe_key` with unique `(profile_id, manual_dedupe_key)` index.
- Canonical key is derived from platform plus normalized URL when available, otherwise external project ID, otherwise stable title/client fingerprint.
- A losing insert catches `IntegrityError`, rolls back the failed transaction, retrieves the canonical existing row, and returns the existing duplicate contract.
- Migration backfill assigns keys only to the earliest existing record in each duplicate fingerprint group, preserving readability and avoiding a migration failure on historical duplicates.

Regression: simulated competing insert verifies the uniqueness failure becomes `DuplicateOpportunityError(existing_job_id)` and rollback occurs.

### 6. Frontend status correctness

Root cause: list endpoint serialized jobs without loading their submission rows, so every list row appeared `Not submitted`.

Fix: list endpoint loads authoritative `ManualOpportunitySubmission` rows, maps by job ID, and passes them to the existing serializer. No parallel frontend status model was added.

### 7. Frontend edit data loss

Root cause: edit form initialized URL/external ID/client as empty and sent a full create-like PATCH that reset source, normalized, translation, and client data.

Fix:

- Edit form populates URL, platform job ID, client metadata, and editable description from authoritative detail.
- Edit sends a dedicated allowlisted payload.
- It omits source URL, external ID, client metadata, normalized requirements, translation metadata, and lifecycle unless a dedicated safe editing workflow is later added.
- Original source text is never sent as an overwrite target.

## Migration impact

Migration chain: `010_manual_opportunity_intake → 011_manual_intake_safety`.

Added to `marketplace_jobs`:

- nullable `manual_dedupe_key` plus unique profile/key index;
- nullable `proposal_application_id`.

Added to `manual_opportunity_submissions`:

- nullable `application_id`;
- nullable `submission_intent_id`.

The two snapshot-link columns remain nullable at database/model level only so pre-011 rows remain readable. All new application writes require both through service validation.

Offline SQL validation succeeded for upgrade, downgrade, and second upgrade. No disposable PostgreSQL server was configured, so an online migration was intentionally not run.

## Tests added or repaired

- Original-text immutability across edits.
- Flush-without-commit transaction ownership.
- Endpoint rollback on partial workflow failure.
- Database uniqueness race recovery.
- Valid lifecycle path.
- Invalid jumps and terminal reversals.
- Approved owned package requirement.
- Active owned Submission Intent requirement.
- Immutable snapshot linkage to package and intent.
- Existing admin, URL, language, validation, safe-rendering, and no-external-submit tests retained.

## Validation results

All backend tests used `DEBUG=false`, `PYTHONDONTWRITEBYTECODE=1`, an unreachable loopback PostgreSQL URL, and disabled pytest cache.

- Final focused TASK-066 suite: **43 passed**, 0 failed.
- Freelancer durable, runtime, adapter, application-package, and security regression suite before the final added rollback test: **192 passed**, 0 failed. The added test subsequently passed in the 43-test focused replay.
- Frontend V2 TypeScript from project root: **passed** (`npx tsc --noEmit --incremental false`).
- Frontend V2 production build from project root: **passed**, 11 static routes (`npx next build --webpack`).
- Alembic offline `010 → 011 → 010 → 011`: **passed**.
- Python imports/collection exercised by pytest: **passed**.
- `git diff --check`: **passed** (line-ending conversion warnings only; no whitespace errors).

The default Turbopack build initially failed because the worktree's `node_modules` is a symlink outside Turbopack's filesystem root. The established Webpack build from the actual Frontend V2 root passed. An earlier build was mistakenly launched from the nested `app/` directory and failed prerendering because that directory is not the project root; generated artifacts from that attempt were removed.

One existing Pydantic V2 class-based Config deprecation warning remains unrelated.

## Remaining known issues

- A real concurrent PostgreSQL integration test was not possible without a disposable local server. Database uniqueness, generated SQL, and deterministic `IntegrityError` recovery are covered, but independent validation should replay two concurrent transactions against disposable PostgreSQL.
- Pre-011 manual submission rows have null package/intent linkage by design for compatibility. They are readable historical snapshots but cannot satisfy the new-write invariant retroactively without an audited data reconciliation.
- The manual workspace does not duplicate the existing package approval and Submission Intent creation UIs. Users must complete those existing controlled actions; the manual submission endpoint then validates them authoritatively.
- Existing TASK-063 competitor-research failures and the obsolete `app.auth.dependencies` test import remain outside this remediation.

## Independent validation recommendation

The implementation is ready for independent validation. The most valuable additional check is online migration plus a two-session duplicate race on a disposable PostgreSQL database, followed by package approval/intent/manual-recording HTTP integration with two distinct users to reconfirm non-disclosure ownership behavior.
