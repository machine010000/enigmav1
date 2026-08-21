# TASK-070A — Production Migration Drift Repair

## Decision

**READY_FOR_COMMIT**

The patch is designed for the observed production state—Alembic at `009_durable_opportunity_pipeline` with one or more revision-010 objects already present—without stamping history, deleting data, dropping production objects, or connecting to production.

## Root cause

`app.database.init_db()` imports every model and executes:

```python
await conn.run_sync(Base.metadata.create_all)
```

`app.main` calls `init_db()` during application startup. `create_all()` creates missing tables from the latest ORM metadata but does not run Alembic and does not advance `alembic_version`. At an earlier startup it could therefore create `manual_opportunity_submissions` from the current `ManualOpportunitySubmission` model while Alembic remained at revision 009.

The original migration 010 then unconditionally called `op.create_table("manual_opportunity_submissions", ...)`, causing the observed PostgreSQL error:

```text
psycopg2.errors.DuplicateTable:
relation "manual_opportunity_submissions" already exists
```

The failure was reproduced semantically on an isolated SQLite database: creating the compatible table first and executing the old blind `create_table` operation raises `OperationalError: table manual_opportunity_submissions already exists`.

The current ORM table also contains revision-011 columns (`application_id` and `submission_intent_id`). Consequently, only skipping the 010 table creation would be insufficient: migration 011 could immediately fail on duplicate columns. TASK-070A therefore adds narrowly scoped compatibility checks to 011 for its own objects.

## Migration 010 schema audit

### `marketplace_jobs` mutations

Migration 010 adds these nullable columns:

| Column | Intended type |
|---|---|
| `original_text` | Text |
| `normalized_requirements` | JSON |
| `source_language` | String(10) |
| `customer_preferred_language` | String(10) |
| `proposal_language` | String(10) |
| `translation_metadata` | JSON |
| `created_by_user_id` | String(64) |

It adds non-unique index `ix_marketplace_jobs_created_by_user_id(created_by_user_id)`.

### `manual_opportunity_submissions`

| Column | Intended contract |
|---|---|
| `id` | Integer primary key, autoincrement |
| `profile_id` | String, NOT NULL |
| `job_id` | String, NOT NULL |
| `created_by_user_id` | String(64), NOT NULL |
| `marketplace_proposal_id` | String(200), nullable |
| `submitted_at` | DateTime, NOT NULL |
| `proposal_text_snapshot` | Text, NOT NULL |
| `submitted_price` | Numeric(10,2), nullable |
| `currency` | String(3), NOT NULL |
| `delivery_estimate` | String(200), nullable |
| `outcome_status` | String(40), NOT NULL, default `manually_submitted` |
| `admin_notes` | Text, nullable |
| `created_at` | DateTime, NOT NULL, current timestamp default |
| `updated_at` | DateTime, NOT NULL, current timestamp default |

Indexes:

- `ix_manual_opportunity_submissions_profile_id(profile_id)`, non-unique.
- `ix_manual_opportunity_submissions_job_id(job_id)`, unique.
- `ix_manual_opportunity_submissions_created_by_user_id(created_by_user_id)`, non-unique.
- `ix_manual_submission_profile_job(profile_id, job_id)`, unique.

Migration 010 declares no foreign keys and no separate named unique constraints; its uniqueness contract is expressed by the two unique indexes and the primary key.

`CURRENT_TIMESTAMP` replaces the dialect-specific spelling `now()` for timestamp defaults. It has the same intended PostgreSQL meaning and makes the fresh migration contract portable to isolated SQLite validation.

## Dependent migrations

- **011** requires `manual_opportunity_submissions` to add approval/intent links. It also adds `manual_dedupe_key` and `proposal_application_id` to `marketplace_jobs` and creates the canonical dedupe index.
- **012** requires the 011 dedupe column/index and normalizes keys.
- **013** requires the 012 dedupe schema plus the manual metadata/URL identity fields and applies the runtime URL canonicalizer.
- **014** adds Chat persistence tables. Its schema does not directly reference the submission table, but Alembic cannot reach it unless 010–013 complete.

## Compatibility and reconciliation behavior

Migration 010 now uses the active Alembic connection and SQLAlchemy inspection.

For existing objects it verifies:

- all required column names;
- compatible SQLAlchemy type families, string capacity, and numeric precision/scale where reflected;
- the `id` primary key;
- required NOT NULL state;
- critical server defaults;
- exact index name, ordered columns, and uniqueness;
- absence of duplicate values before adding a missing unique index.

Safe reconciliation:

- missing nullable columns are added;
- missing required columns are added only when the table is empty or a safe server default exists;
- a nullable required column is changed to NOT NULL only after proving it contains no NULL rows;
- missing/mismatched safe server defaults are set without rewriting row values;
- missing indexes are created only after checking their uniqueness preconditions;
- compatible existing tables, rows, columns, and indexes are preserved.

Fail-closed behavior:

- missing revision-009 `marketplace_jobs`;
- missing primary key;
- incompatible column type/capacity;
- unreconcilable NOT NULL data;
- incompatible same-name index;
- existing duplicates that prevent a required unique index;
- required missing values on a non-empty table without a safe backfill.

These conditions raise an actionable `RuntimeError` beginning with `Migration 010 schema drift is incompatible`. No exception is blindly swallowed, and no existing object is dropped or replaced during upgrade.

Migration 011 now applies the same narrow reuse rule to its four nullable String(64) columns and its unique dedupe index. This covers the exact extra objects that current ORM `create_all()` may have placed in the pre-existing 010 table.

No `alembic stamp`, direct `alembic_version` edit, table recreation, data deletion, truncation, or production connection is used.

## Files changed for TASK-070A

- `enigma-backend/alembic/versions/010_manual_opportunity_intake.py`
- `enigma-backend/alembic/versions/011_manual_intake_safety.py`
- `enigma-backend/tests/test_070a_migration_drift_repair.py`
- `docs/TASK-070A-PRODUCTION-MIGRATION-DRIFT-REPAIR.md`

The existing uncommitted TASK-070 frontend/configuration files were preserved and are unrelated. TASK-070A modifies no frontend, model, router, Railway, Vercel, or environment file.

## Isolated migration scenarios

1. Clean revision 009 schema → 010: passed.
2. Revision 009 plus compatible populated `manual_opportunity_submissions` → 010: passed; snapshot row preserved.
3. Revision 009 plus all compatible 010 objects pre-existing → 010: passed.
4. Incompatible existing snapshot column → deterministic RuntimeError; table and row remain present.
5. Current-ORM/create-all style 011 columns already present → 010 then 011: passed; row preserved.
6. 009 → 010 → 011 → 012 → 013 → 014: passed on isolated SQLite, including runtime-equivalent MD5 support.
7. Head 014 downgrade then re-upgrade: passed.
8. Old blind-create duplicate-table failure: reproduced in isolation.

The migration sequence was executed through Alembic `MigrationContext`/`Operations`, the same revision functions used by `alembic upgrade head`, against an isolated database. A production PostgreSQL command was deliberately not run. The Railway command remains:

```text
alembic upgrade head && python -m app.core.migration_verify && exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

## Validation results

| Validation | Result |
|---|---:|
| TASK-070A migration drift suite | 8 passed |
| TASK-066 manual-intake suite | 53 passed |
| TASK-068 Chat suite | 39 passed |
| TASK-069A CORS suite | 17 passed |
| Combined required pytest run | **117 passed, 0 failed** |
| Application and revision compilation | 316 files passed |
| FastAPI import | passed |
| Required manual/Chat route registration | passed |
| Academy/Creativity/Product Verification imports | passed |
| Alembic history 009 → 014 | linear |
| Alembic head | `014_project_aware_freelancer_chat` |
| External/production connections | none |

The only warning is the existing Pydantic V2 deprecation warning for class-based Settings configuration.

## Commit/push safety conclusion

The patch is safe to commit for independent review and then push after approval. On production it will either:

1. validate and preserve compatible drifted objects, add only demonstrably safe missing pieces, and advance normally through 014; or
2. stop with an explicit structural incompatibility message before any destructive repair.

Because the production schema was not queried in this task, the first deployment remains the authoritative compatibility check. If it fails with a TASK-070A RuntimeError, stop and audit the named object; do not stamp or modify history manually.
