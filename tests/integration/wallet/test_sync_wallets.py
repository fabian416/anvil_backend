"""
Integration tests for wallet sync endpoint.

Tests the /api/v1/wallet/sync endpoint with both legacy and new format.
Includes tests for imported wallet persistence.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.infrastructure.auth.handlers.wallet_me import (
    SyncWalletsHandler,
    WalletResponse,
    WalletsResponse,
)
from app.application.common.services.current_user import CurrentUserService
from app.domain.ports.wallet.wallet_repository import WalletRepository
from app.domain.entities.wallet import Wallet, WalletId
from app.domain.enums.wallet_provider import WalletProvider
from app.domain.enums.chain_type import ChainType
from app.domain.enums.wallet_status import WalletStatus
from app.domain.value_objects.user_id import UserId
from app.domain.value_objects.created_at import CreatedAt
from app.domain.value_objects.updated_at import UpdatedAt


class TestSyncWalletsHandler:
    """Tests for SyncWalletsHandler."""

    @pytest.fixture
    def mock_user(self):
        """Create a mock user."""
        user = MagicMock()
        user.id_.value = 123
        user.privy_user_id.value = "did:privy:abc123"
        user.primary_wallet_address.value = "0x1234567890abcdef1234567890abcdef12345678"
        return user

    @pytest.fixture
    def mock_current_user_service(self, mock_user):
        """Create a mock CurrentUserService."""
        service = MagicMock(spec=CurrentUserService)
        service.get_current_user = AsyncMock(return_value=mock_user)
        return service

    @pytest.fixture
    def mock_wallet_repository(self):
        """Create a mock WalletRepository."""
        from datetime import datetime

        repo = MagicMock(spec=WalletRepository)

        # Mock upsert to return a wallet
        async def mock_upsert(
            user_id, address, provider, privy_wallet_id=None, chain_type=None
        ):
            now = datetime.utcnow()
            return Wallet(
                id_=WalletId(1),
                user_id=user_id,
                privy_wallet_id=privy_wallet_id or f"imported:{address.lower()}",
                address=address.lower(),
                provider=provider,
                default_chain=ChainType.ETHEREUM,
                status=WalletStatus.ACTIVE,
                created_at=CreatedAt(now),
                updated_at=UpdatedAt(now),
            )

        repo.upsert = AsyncMock(side_effect=mock_upsert)
        return repo

    @pytest.fixture
    def handler(self, mock_current_user_service, mock_wallet_repository):
        """Create handler instance."""
        return SyncWalletsHandler(
            current_user_service=mock_current_user_service,
            wallet_repository=mock_wallet_repository,
        )

    @pytest.mark.asyncio
    async def test_sync_wallets_with_new_format(self, handler):
        """Test syncing wallets with the new format including wallet type."""
        wallet_data = [
            {
                "address": "0x1234567890abcdef1234567890abcdef12345678",
                "chain_type": "ethereum",
                "wallet_type": "embedded",
                "privy_wallet_id": "wallet_123",
            },
            {
                "address": "0xabcdef1234567890abcdef1234567890abcdef12",
                "chain_type": "ethereum",
                "wallet_type": "imported",
                "privy_wallet_id": None,
            },
        ]

        result = await handler.execute(wallet_data)

        assert isinstance(result, WalletsResponse)
        assert result.user_id == 123
        assert len(result.wallets) == 2

        # First wallet should be primary (matches primary_wallet_address)
        assert result.wallets[0].address == "0x1234567890abcdef1234567890abcdef12345678"
        assert result.wallets[0].is_primary is True
        assert result.wallets[0].wallet_type == "embedded"
        assert result.wallets[0].wallet_id == "wallet_123"

        # Second wallet is imported
        assert result.wallets[1].address == "0xabcdef1234567890abcdef1234567890abcdef12"
        assert result.wallets[1].is_primary is False
        assert result.wallets[1].wallet_type == "imported"
        # Imported wallets get synthetic ID with "imported:" prefix
        assert result.wallets[1].wallet_id.startswith("imported:")

    @pytest.mark.asyncio
    async def test_sync_wallets_with_legacy_format(self, handler):
        """Test syncing wallets with legacy address-only format."""
        wallet_data = [
            {
                "address": "0x1234567890abcdef1234567890abcdef12345678",
                "chain_type": "ethereum",
                "wallet_type": "unknown",
                "privy_wallet_id": None,
            },
        ]

        result = await handler.execute(wallet_data)

        assert isinstance(result, WalletsResponse)
        assert len(result.wallets) == 1
        assert result.wallets[0].wallet_type == "unknown"
        assert result.wallets[0].chain_type == "ethereum"

    @pytest.mark.asyncio
    async def test_sync_imported_wallet(self, handler, mock_wallet_repository):
        """Test syncing a single imported wallet."""
        wallet_data = [
            {
                "address": "0xnewimportedwallet1234567890abcdef12345678",
                "chain_type": "ethereum",
                "wallet_type": "imported",
                "privy_wallet_id": None,
            },
        ]

        result = await handler.execute(wallet_data)

        assert isinstance(result, WalletsResponse)
        assert len(result.wallets) == 1
        assert result.wallets[0].wallet_type == "imported"
        assert result.wallets[0].source == "frontend"
        assert "imported" in result.message.lower()

        # Verify wallet was persisted
        mock_wallet_repository.upsert.assert_called_once()
        call_args = mock_wallet_repository.upsert.call_args
        assert (
            call_args.kwargs["address"] == "0xnewimportedwallet1234567890abcdef12345678"
        )
        assert call_args.kwargs["provider"] == WalletProvider.IMPORTED

    @pytest.mark.asyncio
    async def test_sync_empty_wallets(self, handler):
        """Test syncing with empty wallet list."""
        result = await handler.execute([])

        assert isinstance(result, WalletsResponse)
        assert len(result.wallets) == 0
        assert result.message == "Wallets synced from frontend"

    @pytest.mark.asyncio
    async def test_sync_wallets_primary_detection(self, handler):
        """Test that primary wallet is correctly detected."""
        wallet_data = [
            {
                "address": "0xother1234567890abcdef1234567890abcdef1234",
                "chain_type": "ethereum",
                "wallet_type": "external",
                "privy_wallet_id": None,
            },
            {
                "address": "0x1234567890abcdef1234567890abcdef12345678",  # Primary
                "chain_type": "ethereum",
                "wallet_type": "embedded",
                "privy_wallet_id": None,
            },
        ]

        result = await handler.execute(wallet_data)

        # Find the primary wallet
        primary_wallet = next(w for w in result.wallets if w.is_primary)
        assert (
            primary_wallet.address.lower()
            == "0x1234567890abcdef1234567890abcdef12345678"
        )

    @pytest.mark.asyncio
    async def test_sync_wallets_mixed_types(self, handler, mock_wallet_repository):
        """Test syncing wallets with mixed types."""
        wallet_data = [
            {
                "address": "0x1111111111111111111111111111111111111111",
                "chain_type": "ethereum",
                "wallet_type": "embedded",
                "privy_wallet_id": "wallet_1",
            },
            {
                "address": "0x2222222222222222222222222222222222222222",
                "chain_type": "polygon",
                "wallet_type": "external",
                "privy_wallet_id": None,
            },
            {
                "address": "0x3333333333333333333333333333333333333333",
                "chain_type": "base",
                "wallet_type": "imported",
                "privy_wallet_id": None,
            },
        ]

        result = await handler.execute(wallet_data)

        assert len(result.wallets) == 3

        # Check all types are preserved
        types = {w.wallet_type for w in result.wallets}
        assert types == {"embedded", "external", "imported"}

        # Check chain types are preserved
        chains = {w.chain_type for w in result.wallets}
        assert chains == {"ethereum", "polygon", "base"}

        # Verify only imported wallet was persisted
        assert mock_wallet_repository.upsert.call_count == 1
        call_args = mock_wallet_repository.upsert.call_args
        assert (
            call_args.kwargs["address"] == "0x3333333333333333333333333333333333333333"
        )

    @pytest.mark.asyncio
    async def test_sync_multiple_imported_wallets(
        self, handler, mock_wallet_repository
    ):
        """Test syncing multiple imported wallets persists all of them."""
        wallet_data = [
            {
                "address": "0x1111111111111111111111111111111111111111",
                "chain_type": "ethereum",
                "wallet_type": "imported",
                "privy_wallet_id": None,
            },
            {
                "address": "0x2222222222222222222222222222222222222222",
                "chain_type": "base",
                "wallet_type": "imported",
                "privy_wallet_id": None,
            },
        ]

        result = await handler.execute(wallet_data)

        assert len(result.wallets) == 2
        assert "2 imported" in result.message
        assert "2 persisted" in result.message

        # Verify both wallets were persisted
        assert mock_wallet_repository.upsert.call_count == 2

    @pytest.mark.asyncio
    async def test_sync_handles_database_error_gracefully(
        self, mock_current_user_service, mock_user
    ):
        """Test that database errors during sync don't block the response."""
        from app.infrastructure.exceptions.gateway import DataMapperError

        # Create a repository that fails on upsert
        mock_wallet_repository = MagicMock(spec=WalletRepository)
        mock_wallet_repository.upsert = AsyncMock(
            side_effect=DataMapperError("Database query failed")
        )

        handler = SyncWalletsHandler(
            current_user_service=mock_current_user_service,
            wallet_repository=mock_wallet_repository,
        )

        wallet_data = [
            {
                "address": "0x1111111111111111111111111111111111111111",
                "chain_type": "ethereum",
                "wallet_type": "imported",
                "privy_wallet_id": None,
            },
        ]

        # Should not raise an exception
        result = await handler.execute(wallet_data)

        # Should still return the wallet in the response
        assert len(result.wallets) == 1
        assert result.wallets[0].wallet_type == "imported"

        # Message should indicate 1 imported but 0 persisted
        assert "1 imported" in result.message
        assert "0 persisted" in result.message

    @pytest.mark.asyncio
    async def test_sync_partial_database_failure(
        self, mock_current_user_service, mock_user
    ):
        """Test that partial database failures don't affect successful persists."""
        from datetime import datetime
        from app.infrastructure.exceptions.gateway import DataMapperError

        call_count = 0

        async def mock_upsert_partial_fail(
            user_id, address, provider, privy_wallet_id=None, chain_type=None
        ):
            nonlocal call_count
            call_count += 1

            # Fail on the second call
            if call_count == 2:
                raise DataMapperError("Database query failed")

            now = datetime.utcnow()
            return Wallet(
                id_=WalletId(call_count),
                user_id=user_id,
                privy_wallet_id=privy_wallet_id or f"imported:{address.lower()}",
                address=address.lower(),
                provider=provider,
                default_chain=ChainType.ETHEREUM,
                status=WalletStatus.ACTIVE,
                created_at=CreatedAt(now),
                updated_at=UpdatedAt(now),
            )

        mock_wallet_repository = MagicMock(spec=WalletRepository)
        mock_wallet_repository.upsert = AsyncMock(side_effect=mock_upsert_partial_fail)

        handler = SyncWalletsHandler(
            current_user_service=mock_current_user_service,
            wallet_repository=mock_wallet_repository,
        )

        wallet_data = [
            {
                "address": "0x1111111111111111111111111111111111111111",
                "chain_type": "ethereum",
                "wallet_type": "imported",
                "privy_wallet_id": None,
            },
            {
                "address": "0x2222222222222222222222222222222222222222",
                "chain_type": "ethereum",
                "wallet_type": "imported",
                "privy_wallet_id": None,
            },
            {
                "address": "0x3333333333333333333333333333333333333333",
                "chain_type": "ethereum",
                "wallet_type": "imported",
                "privy_wallet_id": None,
            },
        ]

        result = await handler.execute(wallet_data)

        # All wallets should be in response
        assert len(result.wallets) == 3

        # Message should indicate 3 imported but only 2 persisted (one failed)
        assert "3 imported" in result.message
        assert "2 persisted" in result.message
