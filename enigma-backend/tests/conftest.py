import sys
import os
import pytest
from unittest.mock import AsyncMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


@pytest.fixture
async def db_session():
    """Create a mock database session for E2E tests."""
    session = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.refresh = AsyncMock()
    session.execute = AsyncMock()
    session.execute.return_value.scalar_one_or_none = MagicMock(return_value=None)
    session.execute.return_value.scalars.return_value.all = MagicMock(return_value=[])
    yield session
