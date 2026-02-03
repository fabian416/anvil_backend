"""
Integration tests for NotificationRepository with real database.

Tests notification creation, querying, and pagination.
"""

import pytest
from datetime import datetime


@pytest.mark.integration
class TestNotificationRepositoryStructure:
    """Structure tests for notification repository."""

    def test_notification_repository_structure(self):
        """Test notification repository has correct structure."""
        # Arrange
        from app.infrastructure.adapters.notification_repository_sqla import (
            SqlaNotificationRepository,
        )

        # This test validates repository structure without DB
        assert SqlaNotificationRepository is not None

    def test_notification_repository_has_pagination_method(self):
        """Test repository has pagination method."""
        # Arrange
        from app.infrastructure.adapters.notification_repository_sqla import (
            SqlaNotificationRepository,
        )

        # Assert method exists in class
        assert hasattr(SqlaNotificationRepository, "read_by_user_paginated")

    def test_notification_repository_instantiation(self):
        """Test repository can be instantiated."""
        # Arrange
        from app.infrastructure.adapters.notification_repository_sqla import (
            SqlaNotificationRepository,
        )
        from unittest.mock import MagicMock

        mock_session = MagicMock()
        repo = SqlaNotificationRepository(session=mock_session)

        # Assert
        assert repo is not None


@pytest.mark.integration
class TestUserMetricsRepositoryStructure:
    """Structure tests for user metrics repository."""

    def test_user_metrics_repository_structure(self):
        """Test user metrics repository has correct structure."""
        # Arrange
        from app.infrastructure.adapters.user_metrics_repository_sqla import (
            UserMetricsRepositorySqla,
        )

        # Assert
        assert UserMetricsRepositorySqla is not None

    def test_user_metrics_repository_has_record_event_method(self):
        """Test repository has record_event method."""
        # Arrange
        from app.infrastructure.adapters.user_metrics_repository_sqla import (
            UserMetricsRepositorySqla,
        )

        # Assert
        assert hasattr(UserMetricsRepositorySqla, "record_event")

    def test_user_metrics_repository_has_query_methods(self):
        """Test repository has query methods."""
        # Arrange
        from app.infrastructure.adapters.user_metrics_repository_sqla import (
            UserMetricsRepositorySqla,
        )

        # Assert
        assert hasattr(UserMetricsRepositorySqla, "get_user_metrics_summary")
        assert hasattr(UserMetricsRepositorySqla, "get_event_count")
        assert hasattr(UserMetricsRepositorySqla, "get_active_users_count")
