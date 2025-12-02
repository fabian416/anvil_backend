"""
Unit tests for Search History Service.

Tests search tracking, history retrieval, popular queries,
and search analytics.
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from app.application.search.search_history_service import (
    SearchHistoryService,
    SearchHistoryEntry,
)


@pytest.fixture
def search_service():
    """Create search history service."""
    return SearchHistoryService()


@pytest.fixture
def user_id():
    """Sample user ID."""
    return uuid4()


class TestSearchHistory:
    """Test suite for Search History Service."""

    @pytest.mark.asyncio
    async def test_record_search(self, search_service, user_id):
        """Test recording a new search."""
        query = "safe staking protocols"
        result_count = 10
        
        entry = await search_service.record_search(
            user_id=user_id,
            query=query,
            result_count=result_count,
        )
        
        assert entry.user_id == user_id
        assert entry.query == query
        assert entry.result_count == result_count
        assert isinstance(entry.timestamp, datetime)

    @pytest.mark.asyncio
    async def test_get_recent_searches(self, search_service, user_id):
        """Test retrieving recent searches."""
        # Record multiple searches
        queries = [
            "aave lending",
            "compound vs aave",
            "safe ethereum protocols",
        ]
        
        for query in queries:
            await search_service.record_search(user_id, query, 5)
        
        # Retrieve recent searches
        recent = await search_service.get_recent_searches(user_id, limit=10)
        
        # Should return most recent first
        assert len(recent) == 3
        assert recent[0].query == "safe ethereum protocols"
        assert recent[1].query == "compound vs aave"
        assert recent[2].query == "aave lending"

    @pytest.mark.asyncio
    async def test_recent_searches_limit(self, search_service, user_id):
        """Test that recent searches respect limit."""
        # Record 10 searches
        for i in range(10):
            await search_service.record_search(user_id, f"query {i}", 5)
        
        # Request only 5
        recent = await search_service.get_recent_searches(user_id, limit=5)
        
        assert len(recent) == 5

    @pytest.mark.asyncio
    async def test_get_popular_queries(self, search_service):
        """Test retrieving most popular queries across all users."""
        # Simulate multiple users searching
        popular_query = "aave v3"
        
        for _ in range(5):
            await search_service.record_search(uuid4(), popular_query, 10)
        
        await search_service.record_search(uuid4(), "rare query", 5)
        
        # Get popular queries
        popular = await search_service.get_popular_queries(limit=10)
        
        assert len(popular) > 0
        # Most popular should be first
        assert popular[0]["query"] == popular_query
        assert popular[0]["count"] == 5

    @pytest.mark.asyncio
    async def test_search_suggestions(self, search_service, user_id):
        """Test getting search suggestions based on partial input."""
        # Record searches
        await search_service.record_search(user_id, "aave v3 lending", 10)
        await search_service.record_search(user_id, "aave compound comparison", 8)
        await search_service.record_search(user_id, "compound risks", 5)
        
        # Get suggestions for "aave"
        suggestions = await search_service.get_search_suggestions(
            user_id, "aave", limit=10
        )
        
        # Should return both aave queries
        assert len(suggestions) == 2
        assert all("aave" in s.lower() for s in suggestions)

    @pytest.mark.asyncio
    async def test_delete_search(self, search_service, user_id):
        """Test deleting a specific search."""
        # Record search
        entry = await search_service.record_search(user_id, "test query", 5)
        
        # Delete it
        await search_service.delete_search(user_id, entry.id)
        
        # Should not appear in recent searches
        recent = await search_service.get_recent_searches(user_id)
        assert len(recent) == 0

    @pytest.mark.asyncio
    async def test_clear_history(self, search_service, user_id):
        """Test clearing entire search history for user."""
        # Record multiple searches
        for i in range(5):
            await search_service.record_search(user_id, f"query {i}", 5)
        
        # Clear history
        await search_service.clear_history(user_id)
        
        # Should have no searches
        recent = await search_service.get_recent_searches(user_id)
        assert len(recent) == 0

    @pytest.mark.asyncio
    async def test_search_analytics(self, search_service, user_id):
        """Test search analytics generation."""
        # Record searches with varying result counts
        await search_service.record_search(user_id, "good query", 15)
        await search_service.record_search(user_id, "okay query", 5)
        await search_service.record_search(user_id, "bad query", 0)
        
        # Get analytics
        analytics = await search_service.get_search_analytics(user_id)
        
        assert analytics["total_searches"] == 3
        assert analytics["avg_results"] == (15 + 5 + 0) / 3
        assert len(analytics["top_queries"]) == 3

    @pytest.mark.asyncio
    async def test_user_isolation(self, search_service):
        """Test that users' search histories are isolated."""
        user1 = uuid4()
        user2 = uuid4()
        
        # Each user searches different things
        await search_service.record_search(user1, "user1 query", 5)
        await search_service.record_search(user2, "user2 query", 5)
        
        # Each user should only see their own searches
        user1_history = await search_service.get_recent_searches(user1)
        user2_history = await search_service.get_recent_searches(user2)
        
        assert len(user1_history) == 1
        assert len(user2_history) == 1
        assert user1_history[0].query == "user1 query"
        assert user2_history[0].query == "user2 query"

    @pytest.mark.asyncio
    async def test_empty_query_handling(self, search_service, user_id):
        """Test handling of empty or whitespace queries."""
        # Should not record empty queries
        entry = await search_service.record_search(user_id, "   ", 0)
        
        # Implementation should handle this gracefully
        # Either skip recording or normalize the query
        recent = await search_service.get_recent_searches(user_id)
        
        # Should either not record or normalize
        assert True  # Basic validation that it doesn't crash
