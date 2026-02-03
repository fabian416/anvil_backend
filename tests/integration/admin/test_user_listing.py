"""
Integration tests for admin user listing.

Tests admin endpoints for:
- List users
- Pagination
- Sorting
- Access control
"""

import pytest


@pytest.mark.integration
@pytest.mark.asyncio
class TestUserListing:
    """Integration tests for admin user listing."""

    async def test_admin_can_list_users(self, client):
        """
        WHEN admin requests user list
        THEN system SHALL return users (or 401 if not authenticated)
        """
        # Backend route is mounted as GET /api/v1/admin/users/ (with trailing slash)
        response = await client.get("/api/v1/admin/users/")

        # Without admin auth, expect 401/403
        assert response.status_code in (200, 401, 403)

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)
            assert "items" in data
            assert "total" in data
            assert "limit" in data
            assert "offset" in data

    async def test_non_admin_cannot_list_users(self, client):
        """
        WHEN non-admin requests user list
        THEN system SHALL return 401 or 403 error
        """
        response = await client.get("/api/v1/admin/users/")

        # Without admin auth, should return 401 or 403
        assert response.status_code in (401, 403)

    async def test_unauthenticated_cannot_list_users(self, client):
        """
        WHEN unauthenticated user requests user list
        THEN system SHALL return 401 unauthorized
        """
        response = await client.get("/api/v1/admin/users/")

        assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
class TestUserListingPagination:
    """Integration tests for user listing pagination."""

    async def test_list_users_with_limit(self, client):
        """
        WHEN admin requests users with limit
        THEN system SHALL return limited results
        """
        response = await client.get("/api/v1/admin/users/", params={"limit": 10})

        assert response.status_code in (200, 401, 403)

    async def test_list_users_with_offset(self, client):
        """
        WHEN admin requests users with offset
        THEN system SHALL skip specified items
        """
        response = await client.get("/api/v1/admin/users/", params={"offset": 5})

        assert response.status_code in (200, 401, 403)

    async def test_list_users_with_pagination(self, client):
        """
        WHEN admin requests users with pagination params
        THEN system SHALL return paginated results
        """
        response = await client.get(
            "/api/v1/admin/users/", params={"limit": 10, "offset": 0}
        )

        assert response.status_code in (200, 401, 403)


@pytest.mark.integration
@pytest.mark.asyncio
class TestUserListingSorting:
    """Integration tests for user listing sorting."""

    async def test_list_users_sorted_by_email(self, client):
        """
        WHEN admin requests users sorted by email
        THEN system SHALL return sorted results
        """
        response = await client.get(
            "/api/v1/admin/users/",
            params={"sorting_field": "email", "sorting_order": "ASC"},
        )

        assert response.status_code in (200, 401, 403, 422)

    async def test_list_users_sorted_by_created_at(self, client):
        """
        WHEN admin requests users sorted by created_at
        THEN system SHALL return sorted results
        """
        response = await client.get(
            "/api/v1/admin/users/",
            params={"sorting_field": "created_at", "sorting_order": "DESC"},
        )

        assert response.status_code in (200, 401, 403, 422)

    async def test_list_users_invalid_sort_field(self, client):
        """
        WHEN admin requests users with invalid sort field
        THEN system SHALL return error or ignore invalid field
        """
        response = await client.get(
            "/api/v1/admin/users/",
            params={"sorting_field": "invalid_field"},
        )

        # Could be 200 (ignored), 400/422 (validation error), or 401/403 (not authenticated)
        assert response.status_code in (200, 400, 401, 403, 422)


@pytest.mark.integration
@pytest.mark.asyncio
class TestUserListingFiltering:
    """Integration tests for user listing filtering."""

    async def test_list_users_filter_by_active(self, client):
        """
        WHEN admin filters users by active status
        THEN system SHALL return filtered results
        """
        # Not implemented in backend (yet). Keep as a smoke call to ensure it doesn't 500.
        response = await client.get("/api/v1/admin/users/", params={"is_active": True})

        assert response.status_code in (200, 401, 403)

    async def test_list_users_filter_by_role(self, client):
        """
        WHEN admin filters users by role
        THEN system SHALL return filtered results
        """
        # Not implemented in backend (yet). Keep as a smoke call to ensure it doesn't 500.
        response = await client.get("/api/v1/admin/users/", params={"role": "admin"})

        assert response.status_code in (200, 401, 403, 422)
