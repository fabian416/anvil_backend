"""Search history service for tracking and retrieving user searches."""

from typing import List, Optional
from uuid import UUID, uuid4
from datetime import datetime, timedelta, UTC


class SearchHistoryEntry:
    """Search history entry entity."""

    def __init__(
        self,
        id: UUID,
        user_id: UUID,
        query: str,
        search_type: str,  # 'graphrag', 'protocol', 'token', 'general'
        results_count: int,
        filters_applied: Optional[dict] = None,
        created_at: Optional[datetime] = None,
    ):
        self.id = id
        self.user_id = user_id
        self.query = query
        self.search_type = search_type
        self.results_count = results_count
        self.filters_applied = filters_applied or {}
        self.created_at = created_at or datetime.now(UTC)


class SearchHistoryService:
    """
    Service for managing user search history.

    Tracks all searches performed by users, enabling:
    - Recent search retrieval
    - Search analytics
    - Personalized search suggestions
    - Query autocomplete
    """

    def __init__(self):
        # TODO: Inject repository for database persistence
        # For now, using in-memory storage
        self._history: dict[UUID, List[SearchHistoryEntry]] = {}

    async def record_search(
        self,
        user_id: UUID,
        query: str,
        search_type: str,
        results_count: int,
        filters_applied: Optional[dict] = None,
    ) -> SearchHistoryEntry:
        """
        Record a search in user's history.

        Args:
            user_id: User UUID
            query: Search query string
            search_type: Type of search performed
            results_count: Number of results returned
            filters_applied: Optional dict of filters used

        Returns:
            Created search history entry
        """
        entry = SearchHistoryEntry(
            id=uuid4(),
            user_id=user_id,
            query=query,
            search_type=search_type,
            results_count=results_count,
            filters_applied=filters_applied,
        )

        # Store in memory (TODO: Persist to database)
        if user_id not in self._history:
            self._history[user_id] = []

        self._history[user_id].append(entry)

        # Keep only last 100 searches per user
        if len(self._history[user_id]) > 100:
            self._history[user_id] = self._history[user_id][-100:]

        return entry

    async def get_recent_searches(
        self,
        user_id: UUID,
        limit: int = 10,
        search_type: Optional[str] = None,
    ) -> List[SearchHistoryEntry]:
        """
        Get user's recent searches.

        Args:
            user_id: User UUID
            limit: Maximum number of entries to return
            search_type: Optional filter by search type

        Returns:
            List of search history entries, most recent first
        """
        user_searches = self._history.get(user_id, [])

        # Filter by type if specified
        if search_type:
            user_searches = [s for s in user_searches if s.search_type == search_type]

        # Sort by created_at descending
        user_searches.sort(key=lambda x: x.created_at, reverse=True)

        # Return limited results
        return user_searches[:limit]

    async def get_popular_queries(
        self,
        user_id: UUID,
        limit: int = 5,
        days: int = 30,
    ) -> List[dict]:
        """
        Get user's most popular search queries.

        Args:
            user_id: User UUID
            limit: Maximum number of queries to return
            days: Look back period in days

        Returns:
            List of popular queries with counts
        """
        user_searches = self._history.get(user_id, [])

        # Filter by date range
        cutoff_date = datetime.now(UTC) - timedelta(days=days)
        recent_searches = [s for s in user_searches if s.created_at >= cutoff_date]

        # Count query frequencies
        query_counts: dict[str, int] = {}
        for search in recent_searches:
            query = search.query.lower().strip()
            query_counts[query] = query_counts.get(query, 0) + 1

        # Sort by count descending
        popular = sorted(
            [{"query": q, "count": c} for q, c in query_counts.items()],
            key=lambda x: x["count"],
            reverse=True,
        )

        return popular[:limit]

    async def get_search_suggestions(
        self,
        user_id: UUID,
        prefix: str,
        limit: int = 5,
    ) -> List[str]:
        """
        Get search suggestions based on user's history.

        Args:
            user_id: User UUID
            prefix: Query prefix to match
            limit: Maximum number of suggestions

        Returns:
            List of suggested queries
        """
        user_searches = self._history.get(user_id, [])

        # Find queries starting with prefix (case-insensitive)
        prefix_lower = prefix.lower().strip()
        matching_queries = set()

        for search in user_searches:
            query = search.query.strip()
            if query.lower().startswith(prefix_lower):
                matching_queries.add(query)

        # Sort by frequency (approximate by counting in history)
        query_frequencies = {}
        for search in user_searches:
            query = search.query.strip()
            if query in matching_queries:
                query_frequencies[query] = query_frequencies.get(query, 0) + 1

        # Sort by frequency descending
        suggestions = sorted(
            matching_queries,
            key=lambda q: query_frequencies.get(q, 0),
            reverse=True,
        )

        return suggestions[:limit]

    async def delete_search(
        self,
        user_id: UUID,
        search_id: UUID,
    ) -> bool:
        """
        Delete a specific search from history.

        Args:
            user_id: User UUID
            search_id: Search entry UUID

        Returns:
            True if deleted, False if not found
        """
        user_searches = self._history.get(user_id, [])

        for i, search in enumerate(user_searches):
            if search.id == search_id:
                del self._history[user_id][i]
                return True

        return False

    async def clear_history(
        self,
        user_id: UUID,
        search_type: Optional[str] = None,
    ) -> int:
        """
        Clear user's search history.

        Args:
            user_id: User UUID
            search_type: Optional - clear only specific type

        Returns:
            Number of entries cleared
        """
        if user_id not in self._history:
            return 0

        if search_type is None:
            # Clear all
            count = len(self._history[user_id])
            self._history[user_id] = []
            return count
        else:
            # Clear only specific type
            original_count = len(self._history[user_id])
            self._history[user_id] = [
                s for s in self._history[user_id] if s.search_type != search_type
            ]
            return original_count - len(self._history[user_id])

    async def get_search_analytics(
        self,
        user_id: UUID,
        days: int = 30,
    ) -> dict:
        """
        Get search analytics for user.

        Args:
            user_id: User UUID
            days: Look back period in days

        Returns:
            Dictionary with analytics data
        """
        user_searches = self._history.get(user_id, [])

        # Filter by date range
        cutoff_date = datetime.now(UTC) - timedelta(days=days)
        recent_searches = [s for s in user_searches if s.created_at >= cutoff_date]

        if not recent_searches:
            return {
                "total_searches": 0,
                "by_type": {},
                "average_results": 0,
                "most_common_filters": [],
            }

        # Count by type
        by_type = {}
        for search in recent_searches:
            by_type[search.search_type] = by_type.get(search.search_type, 0) + 1

        # Average results
        total_results = sum(s.results_count for s in recent_searches)
        avg_results = total_results / len(recent_searches) if recent_searches else 0

        # Most common filters
        filter_counts: dict[str, int] = {}
        for search in recent_searches:
            if search.filters_applied:
                for key, value in search.filters_applied.items():
                    filter_key = f"{key}:{value}"
                    filter_counts[filter_key] = filter_counts.get(filter_key, 0) + 1

        most_common_filters = sorted(
            [{"filter": k, "count": v} for k, v in filter_counts.items()],
            key=lambda x: x["count"],
            reverse=True,
        )[:5]

        return {
            "total_searches": len(recent_searches),
            "by_type": by_type,
            "average_results": round(avg_results, 1),
            "most_common_filters": most_common_filters,
        }
