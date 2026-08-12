import asyncio
from typing import List

from sqlalchemy import text

from app.database import engine

EXPECTED_REVISION = "003_capability_intelligence"
EXPECTED_COLUMNS = [
    "capability_status",
    "evidence_count",
    "successful_execution_count",
    "failed_execution_count",
    "last_success_at",
    "freelance_readiness_threshold",
]


def format_yes_no(value: bool) -> str:
    return "YES" if value else "NO"


async def verify_migration() -> int:
    status_ok = True

    async with engine.connect() as conn:
        try:
            result = await conn.execute(text("SELECT version_num FROM alembic_version"))
            revision_rows = result.scalars().all()
            revisions = [str(r) for r in revision_rows if r is not None]
        except Exception as exc:
            print(f"MIGRATION_VERIFY revision_error=FAILED")
            print(f"MIGRATION_VERIFY status=FAIL")
            print(f"MIGRATION_VERIFY error=alembic_version_query_failed")
            print(f"MIGRATION_VERIFY error_detail={str(exc)}")
            return 1

        revision_value = revisions[0] if revisions else "NONE"
        revision_matches_expected = EXPECTED_REVISION in revisions

        print(f"MIGRATION_VERIFY revision={revision_value}")
        print(f"MIGRATION_VERIFY revision_matches_expected={format_yes_no(revision_matches_expected)}")

        try:
            result = await conn.execute(
                text(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_name = 'knowledge_progress' AND table_schema = 'public' "
                    "ORDER BY ordinal_position"
                )
            )
            column_rows = result.scalars().all()
            column_names = {str(column) for column in column_rows if column is not None}
        except Exception as exc:
            print(f"MIGRATION_VERIFY column_check_error=FAILED")
            print(f"MIGRATION_VERIFY status=FAIL")
            print(f"MIGRATION_VERIFY error=knowledge_progress_column_query_failed")
            print(f"MIGRATION_VERIFY error_detail={str(exc)}")
            return 1

        missing_columns = [col for col in EXPECTED_COLUMNS if col not in column_names]
        for column in EXPECTED_COLUMNS:
            print(f"MIGRATION_VERIFY {column}={format_yes_no(column in column_names)}")

        if missing_columns:
            print(f"MIGRATION_VERIFY missing_columns={','.join(sorted(missing_columns))}")
            status_ok = False
        else:
            print("MIGRATION_VERIFY knowledge_progress_columns=OK")

        migration_003_status = "APPLIED" if not missing_columns else "NOT_APPLIED"
        print(f"MIGRATION_VERIFY migration_003={migration_003_status}")

        if not revision_matches_expected and not status_ok:
            print("MIGRATION_VERIFY status=FAIL")
            return 1

        if status_ok:
            print("MIGRATION_VERIFY status=PASS")
            return 0

        print("MIGRATION_VERIFY status=FAIL")
        return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(verify_migration()))
