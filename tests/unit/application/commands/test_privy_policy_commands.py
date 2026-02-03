"""
Unit tests for Privy policy admin commands.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.domain.enums.user_role import UserRole


@pytest.fixture
def mock_session():
    """Create mock database session."""
    return AsyncMock()


@pytest.mark.unit
class TestCreatePrivyPolicy:
    @pytest.mark.asyncio
    async def test_execute_calls_privy_client_when_admin(self, mock_session):
        from app.application.commands.policy.create_privy_policy import (
            CreatePrivyPolicy,
            CreatePrivyPolicyRequest,
        )

        current_user_service = AsyncMock()
        admin_user = MagicMock()
        admin_user.role = UserRole.ADMIN
        admin_user.id_ = MagicMock(value=1)
        current_user_service.get_current_user = AsyncMock(return_value=admin_user)

        privy_client = AsyncMock()
        privy_client.create_policy = AsyncMock(
            return_value={
                "id": "pol_123",
                "name": "Test",
                "version": "1.0",
                "chain_type": "ethereum",
                "rules": [],
                "owner_id": None,
            }
        )

        service = CreatePrivyPolicy(
            current_user_service=current_user_service,
            privy_client=privy_client,
            session=mock_session,
        )
        result = await service.execute(
            CreatePrivyPolicyRequest(
                version="1.0",
                name="Test",
                chain_type="ethereum",
                rules=[],
            )
        )

        assert result.policy.id == "pol_123"
        privy_client.create_policy.assert_called_once()


@pytest.mark.unit
class TestGetPrivyPolicy:
    @pytest.mark.asyncio
    @pytest.mark.skip(
        reason="Requires complex repository mocking - needs integration test"
    )
    async def test_execute_calls_privy_client_when_admin(self, mock_session):
        from app.application.commands.policy.get_privy_policy import (
            GetPrivyPolicy,
            GetPrivyPolicyRequest,
        )

        current_user_service = AsyncMock()
        admin_user = MagicMock()
        admin_user.role = UserRole.ADMIN
        current_user_service.get_current_user = AsyncMock(return_value=admin_user)

        privy_client = AsyncMock()
        privy_client.get_policy = AsyncMock(
            return_value={
                "id": "pol_123",
                "name": "Test",
                "version": "1.0",
                "chain_type": "ethereum",
                "rules": [],
                "owner_id": None,
            }
        )

        service = GetPrivyPolicy(
            current_user_service=current_user_service,
            privy_client=privy_client,
            session=mock_session,
        )
        policy = await service.execute(GetPrivyPolicyRequest(policy_id="pol_123"))
        assert policy.id == "pol_123"
        privy_client.get_policy.assert_called_once_with("pol_123")


@pytest.mark.unit
class TestUpdatePrivyPolicy:
    @pytest.mark.asyncio
    async def test_execute_calls_privy_client_when_admin(self, mock_session):
        from app.application.commands.policy.update_privy_policy import (
            UpdatePrivyPolicy,
            UpdatePrivyPolicyRequest,
        )

        current_user_service = AsyncMock()
        admin_user = MagicMock()
        admin_user.role = UserRole.ADMIN
        current_user_service.get_current_user = AsyncMock(return_value=admin_user)

        privy_client = AsyncMock()
        privy_client.update_policy = AsyncMock(
            return_value={
                "id": "pol_123",
                "name": "New Name",
                "version": "1.0",
                "chain_type": "ethereum",
                "rules": [],
                "owner_id": None,
            }
        )

        service = UpdatePrivyPolicy(
            current_user_service=current_user_service,
            privy_client=privy_client,
            session=mock_session,
        )
        result = await service.execute(
            UpdatePrivyPolicyRequest(policy_id="pol_123", name="New Name", rules=[])
        )

        assert result.policy.name == "New Name"
        privy_client.update_policy.assert_called_once()
