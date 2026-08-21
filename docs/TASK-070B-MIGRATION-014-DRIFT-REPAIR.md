# TASK-070B — Migration 014 Production Schema Drift Repair

## Decision

**READY_FOR_COMMIT**

Migration 014 now reconciles compatible Freelancer Chat objects that already exist while Alembic is at revision 013. It preserves existing rows, creates only missing safe schema pieces, and fails deterministically on incompatible drift. No production database or external service was contacted.

## Root cause

`app.database.init_db()` imports `app.models` and calls `Base.metadata.create_all()` during application startup. The model import registers the three Freelancer Chat models on `Base.metadata`. If the application starts without first completing `alembic upgrade head`, SQLAlchemy can create the current ORM tables while `alembic_version` remains at 013. The original 014 then blindly calls `op.create_table("freelancer_conversations", ...)`, producing the observed `DuplicateTable`.

The Railway container command runs `alembic upgrade head` before Uvicorn, which is the correct ordering. Keeping `create_all()` is therefore not required to repair this incident and was not changed in this narrowly scoped patch. It remains a long-term drift risk whenever the application is launched through any command that bypasses Alembic; removing it should be a separate, explicitly validated startup-policy change.

## Complete migration-014 schema audit

Migration 014 changes no existing pre-014 table. It creates the following three tables.

### `freelancer_conversations`

| Column | Type | Nullability/default/constraint |
|---|---|---|
| `id` | String(64) | NOT NULL, primary key |
| `profile_id` | String(64) | NOT NULL |
| `user_id` | String(64) | NOT NULL |
| `title` | String(300) | NOT NULL |
| `active_project_id` | String(64) | nullable |
| `metadata` | JSON | NOT NULL |
| `created_at` | DateTime | NOT NULL, `CURRENT_TIMESTAMP` server default |
| `updated_at` | DateTime | NOT NULL, `CURRENT_TIMESTAMP` server default |

Indexes:

- `ix_freelancer_conversations_user_updated(user_id, updated_at)`, non-unique.
- `ix_freelancer_conversations_profile(profile_id)`, non-unique.

### `freelancer_chat_messages`

| Column | Type | Nullability/default/constraint |
|---|---|---|
| `id` | String(64) | NOT NULL, primary key |
| `conversation_id` | String(64) | NOT NULL, FK to `freelancer_conversations.id`, ON DELETE CASCADE |
| `profile_id` | String(64) | NOT NULL |
| `user_id` | String(64) | NOT NULL |
| `project_id` | String(64) | nullable |
| `role` | String(20) | NOT NULL |
| `sequence` | Integer | NOT NULL |
| `intent` | String(50) | nullable |
| `content` | Text | NOT NULL |
| `structured_data` | JSON | NOT NULL |
| `created_at` | DateTime | NOT NULL, `CURRENT_TIMESTAMP` server default |

Indexes:

- `ix_freelancer_messages_conversation_created(conversation_id, created_at)`, non-unique.
- `uq_freelancer_messages_conversation_sequence(conversation_id, sequence)`, unique.
- `ix_freelancer_messages_user_project(user_id, project_id)`, non-unique.

### `freelancer_project_artifacts`

| Column | Type | Nullability/default/constraint |
|---|---|---|
| `id` | String(64) | NOT NULL, primary key |
| `profile_id` | String(64) | NOT NULL |
| `user_id` | String(64) | NOT NULL |
| `project_id` | String(64) | nullable |
| `artifact_type` | String(50) | NOT NULL |
| `visibility` | String(30) | NOT NULL |
| `version` | Integer | NOT NULL |
| `content` | Text | NOT NULL |
| `data` | JSON | NOT NULL |
| `source_message_id` | String(64) | nullable, FK to `freelancer_chat_messages.id`, ON DELETE SET NULL |
| `created_at` | DateTime | NOT NULL, `CURRENT_TIMESTAMP` server default |

Indexes:

- `ix_freelancer_artifacts_user_project_type(user_id, project_id, artifact_type)`, non-unique.
- `ix_freelancer_artifacts_visibility_type(user_id, visibility, artifact_type)`, non-unique.
- `uq_freelancer_artifact_version(user_id, project_id, artifact_type, version)`, unique.

There are no additional named unique constraints or server defaults in 014. Uniqueness is implemented by the two named unique indexes plus each table's primary key.

## Reconciliation behavior

For each of the three tables migration 014 now:

- creates the complete intended table when absent;
- reflects and validates every existing column's name, type family, string capacity, nullability, timestamp default, and `id` primary key;
- adds a missing nullable column;
- adds a missing required column only when the table is empty or the column has a safe server default;
- makes a required column NOT NULL only after proving no NULL rows exist;
- restores missing timestamp server defaults without rewriting row values;
- validates both foreign-key target and ON DELETE action;
- adds a missing PostgreSQL foreign key only after proving there are no orphan rows;
- validates exact index name, ordered columns, and uniqueness;
- checks existing data for collisions before creating either missing unique index.

The migration raises an actionable `RuntimeError` beginning with `Migration 014 schema drift is incompatible` for incompatible types, insufficient string capacity, missing/wrong primary keys, unsafe required-column gaps, NULL violations, wrong same-name indexes, duplicate unique keys, wrong foreign keys, or orphan rows. It does not swallow database errors or drop/recreate existing objects during upgrade.

SQLite cannot add a missing FK without rebuilding a table, so that isolated-database-only case fails closed. PostgreSQL—the production dialect—uses `ALTER TABLE ... ADD FOREIGN KEY` after the orphan check. Clean creation and the observed `create_all()` schema already contain both FKs.

Downgrade retains the established 014 contract and drops the three 014 tables. It was exercised only on an isolated test database, never production.

## Tests

Focused TASK-070B coverage validates:

1. clean 013 → 014;
2. pre-existing compatible `freelancer_conversations` only;
3. all three compatible create-all-style tables pre-existing;
4. persisted conversation, message, and artifact data preservation;
5. safe repair of a missing nullable column and all missing indexes;
6. incompatible column rejection without deleting the existing row;
7. fail-closed unique-index repair when duplicate data exists;
8. idempotent re-run plus isolated downgrade/re-upgrade;
9. full 009 → 010 → 011 → 012 → 013 → 014 sequence.

Results:

| Suite/check | Result |
|---|---:|
| TASK-070B focused migration suite | 7 passed |
| TASK-070A migration suite | 8 passed |
| TASK-066 manual-intake suite | 53 passed |
| TASK-068 Freelancer Chat suite | 39 passed |
| TASK-069A CORS suite | 17 passed |
| Combined pytest execution | **124 passed, 0 failed** |
| Python source compilation | 316 files passed |
| FastAPI/Chat model/router imports | passed |
| Freelancer Chat registered routes | 5 |
| Alembic history 009 through 014 | linear |
| Alembic head | `014_project_aware_freelancer_chat` |

The only test warning is the pre-existing Pydantic V2 class-based Settings deprecation warning.

## Files changed

- `enigma-backend/alembic/versions/014_project_aware_freelancer_chat.py`
- `enigma-backend/tests/test_070b_migration_014_drift_repair.py`
- `docs/TASK-070B-MIGRATION-014-DRIFT-REPAIR.md`

No frontend, model, router, environment, Railway, Vercel, or Alembic history/stamp file was changed. No commit, push, deployment, production database connection, destructive production operation, or external service call was performed.
