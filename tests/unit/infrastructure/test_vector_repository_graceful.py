"""
Unit tests: VectorRepositorySqla degrades gracefully when embedding tables are missing.

These tests simulate ProgrammingError with 'UndefinedTable' / 'does not exist' messages
to verify that the repository returns safe defaults (None / [] / 0) instead of propagating 500s.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from sqlalchemy.exc import ProgrammingError


# We mock the session entirely, so no real DB needed.


class FakeProgrammingError(ProgrammingError):
    """Simulated ProgrammingError with UndefinedTable message."""

    def __init__(self, message: str = "UndefinedTable"):
        self.orig = Exception(message)


@pytest.fixture
def mock_session():
    """Create a mock AsyncSession."""
    session = AsyncMock()
    return session


@pytest.fixture
def repo(mock_session):
    """Create VectorRepositorySqla with mocked session."""
    from app.infrastructure.persistence_sqla.repositories.vector_repository_sqla import (
        VectorRepositorySqla,
    )

    return VectorRepositorySqla(session=mock_session)


# ---------------------------------------------------------------------------
# get_embedding
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_embedding_returns_none_when_table_missing(repo, mock_session):
    """get_embedding should return None when embedding tables don't exist."""
    # Simulate table missing
    mock_session.execute.side_effect = FakeProgrammingError("UndefinedTable")

    result = await repo.get_embedding(uuid4())
    assert result is None


@pytest.mark.asyncio
async def test_get_embedding_returns_none_on_does_not_exist(repo, mock_session):
    """get_embedding should return None when table 'does not exist'."""
    mock_session.execute.side_effect = FakeProgrammingError(
        'relation "protocol_embeddings" does not exist'
    )

    result = await repo.get_embedding(uuid4())
    assert result is None


@pytest.mark.asyncio
async def test_get_embedding_propagates_other_programming_errors(repo, mock_session):
    """get_embedding should re-raise ProgrammingError for unrecognized messages."""

    class OtherProgrammingError(ProgrammingError):
        def __init__(self):
            self.orig = Exception("column embedding is ambiguous")

    mock_session.execute.side_effect = OtherProgrammingError()

    with pytest.raises(ProgrammingError):
        await repo.get_embedding(uuid4())


# ---------------------------------------------------------------------------
# find_similar
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_find_similar_returns_empty_list_when_table_missing(repo, mock_session):
    """find_similar should return [] when embedding tables don't exist."""
    mock_session.execute.side_effect = FakeProgrammingError("UndefinedTable")

    embedding = [0.1] * 512
    results = await repo.find_similar(
        query_embedding=embedding, entity_type="Protocol", limit=5
    )
    assert results == []


@pytest.mark.asyncio
async def test_find_similar_returns_empty_on_does_not_exist(repo, mock_session):
    """find_similar should return [] on 'does not exist' error."""
    mock_session.execute.side_effect = FakeProgrammingError(
        'relation "entity_embeddings" does not exist'
    )

    embedding = [0.1] * 512
    results = await repo.find_similar(query_embedding=embedding, limit=5)
    assert results == []


# ---------------------------------------------------------------------------
# count_embeddings
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_count_embeddings_returns_zero_when_table_missing(repo, mock_session):
    """count_embeddings should return 0 when embedding tables don't exist."""
    mock_session.execute.side_effect = FakeProgrammingError("UndefinedTable")

    count = await repo.count_embeddings()
    assert count == 0


@pytest.mark.asyncio
async def test_count_embeddings_returns_zero_on_does_not_exist(repo, mock_session):
    """count_embeddings should return 0 on 'does not exist' error."""
    mock_session.execute.side_effect = FakeProgrammingError(
        "protocol_embeddings does not exist"
    )

    count = await repo.count_embeddings(entity_type="Protocol")
    assert count == 0
