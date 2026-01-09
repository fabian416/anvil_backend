"""
Local conftest for unit/infrastructure tests.

These are pure mock/unit tests that don't need a real database.
We override the auto-use fixtures from the parent conftest to avoid
connecting to PostgreSQL.
"""

import pytest
import pytest_asyncio


# Override session-scoped fixtures to avoid DB connection
@pytest.fixture(scope="session", autouse=True)
def test_db_engine():
    """Stub: Unit tests don't need a real DB engine."""
    return None


@pytest_asyncio.fixture(scope="function", autouse=True)
async def cleanup_database(test_db_engine):
    """Stub: No database cleanup needed for unit tests."""
    yield

