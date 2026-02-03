"""
Integration tests for Privy login flow.

Tests:
- Privy API client functionality
- Privy wallet ID fetching
- Celery balance sync tasks
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.mark.integration
@pytest.mark.auth
class TestPrivyApiClient:
    """Integration tests for Privy API client."""

    def test_privy_api_client_import(self):
        """
        WHEN importing PrivyApiClient
        THEN import SHALL succeed
        """
        from app.infrastructure.adapters.privy.privy_api_client import PrivyApiClient

        assert PrivyApiClient is not None

    def test_privy_api_client_initialization(self):
        """
        WHEN creating PrivyApiClient with settings
        THEN client SHALL be created successfully
        """
        from app.infrastructure.adapters.privy.privy_api_client import PrivyApiClient
        from app.setup.config.privy import PrivySettings

        settings = PrivySettings(
            APP_ID="test_app_id",
            APP_SECRET="test_secret",
        )

        client = PrivyApiClient(settings)
        assert client is not None

    def test_privy_api_client_headers(self):
        """
        WHEN getting headers from PrivyApiClient
        THEN headers SHALL include authorization and app ID
        """
        from app.infrastructure.adapters.privy.privy_api_client import PrivyApiClient
        from app.setup.config.privy import PrivySettings

        settings = PrivySettings(
            APP_ID="test_app_id",
            APP_SECRET="test_secret",
        )

        client = PrivyApiClient(settings)
        headers = client._get_headers()

        assert "Authorization" in headers
        assert headers["Authorization"].startswith("Basic ")
        assert headers["privy-app-id"] == "test_app_id"


@pytest.mark.integration
@pytest.mark.auth
class TestPrivyWalletSync:
    """Integration tests for wallet sync during Privy login."""

    def test_privy_wallet_data_class(self):
        """
        WHEN creating PrivyWallet dataclass
        THEN all fields SHALL be set correctly
        """
        from app.infrastructure.adapters.privy.privy_api_client import PrivyWallet

        wallet = PrivyWallet(
            wallet_id="test_wallet_id",
            address="0x1234567890123456789012345678901234567890",
            chain_type="ethereum",
            wallet_client="privy",
            connector_type="embedded",
            is_imported=False,
        )

        assert wallet.wallet_id == "test_wallet_id"
        assert wallet.address == "0x1234567890123456789012345678901234567890"
        assert wallet.chain_type == "ethereum"
        assert wallet.is_imported is False

    def test_privy_user_data_class(self):
        """
        WHEN creating PrivyUserData dataclass
        THEN wallets list SHALL be accessible
        """
        from app.infrastructure.adapters.privy.privy_api_client import (
            PrivyUserData,
            PrivyWallet,
        )

        wallet = PrivyWallet(
            wallet_id="test_wallet_id",
            address="0x1234567890123456789012345678901234567890",
            chain_type="ethereum",
            wallet_client="privy",
            connector_type="embedded",
            is_imported=False,
        )

        user_data = PrivyUserData(
            privy_user_id="did:privy:test123",
            wallets=[wallet],
            email="test@example.com",
            name="Test User",
        )

        assert user_data.privy_user_id == "did:privy:test123"
        assert len(user_data.wallets) == 1
        assert user_data.wallets[0].wallet_id == "test_wallet_id"


@pytest.mark.integration
@pytest.mark.auth
class TestPrivyBalanceSyncTask:
    """Integration tests for Privy balance sync Celery task."""

    def test_privy_balance_sync_task_exists(self):
        """
        WHEN importing privy balance sync task
        THEN import SHALL succeed
        """
        from app.infrastructure.celery.tasks.privy_balance_tasks import (
            sync_wallet_balances,
        )

        assert sync_wallet_balances is not None
        assert callable(sync_wallet_balances)

    def test_privy_single_wallet_sync_task_exists(self):
        """
        WHEN importing single wallet sync task
        THEN import SHALL succeed
        """
        from app.infrastructure.celery.tasks.privy_balance_tasks import (
            sync_single_wallet_balance,
        )

        assert sync_single_wallet_balance is not None
        assert callable(sync_single_wallet_balance)

    def test_privy_balance_fetch_function_exists(self):
        """
        WHEN importing fetch_privy_wallet_balance function
        THEN import SHALL succeed
        """
        from app.infrastructure.celery.tasks.privy_balance_tasks import (
            fetch_privy_wallet_balance,
        )

        assert fetch_privy_wallet_balance is not None

    def test_chain_id_map_configured(self):
        """
        WHEN checking CHAIN_ID_MAP
        THEN common chains SHALL be mapped
        """
        from app.infrastructure.celery.tasks.privy_balance_tasks import CHAIN_ID_MAP

        assert "base" in CHAIN_ID_MAP
        assert "ethereum" in CHAIN_ID_MAP or "arbitrum" in CHAIN_ID_MAP


@pytest.mark.integration
@pytest.mark.auth
class TestPrivyLoginIntegration:
    """End-to-end integration tests for Privy login with mocked API."""

    @pytest.mark.asyncio
    async def test_privy_api_client_parse_user_response(self):
        """
        WHEN parsing Privy API user response
        THEN wallets SHALL be extracted correctly
        """
        from app.infrastructure.adapters.privy.privy_api_client import PrivyApiClient
        from app.setup.config.privy import PrivySettings

        settings = PrivySettings(
            APP_ID="test_app_id",
            APP_SECRET="test_secret",
        )

        client = PrivyApiClient(settings)

        # Mock Privy API response
        mock_response = {
            "id": "did:privy:test123",
            "linked_accounts": [
                {
                    "id": "wallet_abc123",
                    "type": "wallet",
                    "address": "0x1234567890123456789012345678901234567890",
                    "chain_type": "ethereum",
                    "wallet_client": "privy",
                    "connector_type": "embedded",
                    "imported": False,
                },
                {
                    "type": "google_oauth",
                    "email": "test@example.com",
                    "name": "Test User",
                },
            ],
        }

        user_data = client._parse_user_response(mock_response)

        assert user_data.privy_user_id == "did:privy:test123"
        assert len(user_data.wallets) == 1
        assert user_data.wallets[0].wallet_id == "wallet_abc123"
        assert (
            user_data.wallets[0].address == "0x1234567890123456789012345678901234567890"
        )
        assert user_data.email == "test@example.com"
        assert user_data.name == "Test User"
