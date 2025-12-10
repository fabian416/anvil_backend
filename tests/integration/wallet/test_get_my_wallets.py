"""
Integration tests for GetMyWalletsHandler.

Tests the /api/v1/wallet/me endpoint with:
- Privy wallets
- Imported wallets from local database
- Combined data sources with deduplication
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from app.infrastructure.auth.handlers.wallet_me import (
    GetMyWalletsHandler,
    WalletResponse,
    WalletsResponse,
)
from app.application.common.services.current_user import CurrentUserService
from app.domain.ports.wallet.embedded_wallet_provider import (
    EmbeddedWalletProviderPort,
    WalletInfo,
    ChainType as ProviderChainType,
    WalletType,
)
from app.domain.ports.wallet.wallet_repository import WalletRepository
from app.domain.entities.wallet import Wallet, WalletId
from app.domain.enums.wallet_provider import WalletProvider
from app.domain.enums.chain_type import ChainType
from app.domain.enums.wallet_status import WalletStatus
from app.domain.value_objects.user_id import UserId
from app.domain.value_objects.created_at import CreatedAt
from app.domain.value_objects.updated_at import UpdatedAt


def make_wallet(
    wallet_id: int,
    user_id: int,
    address: str,
    provider: WalletProvider = WalletProvider.IMPORTED,
    chain: ChainType = ChainType.ETHEREUM,
) -> Wallet:
    """Helper to create wallet test fixtures."""
    now = datetime.utcnow()
    return Wallet(
        id_=WalletId(wallet_id),
        user_id=UserId(user_id),
        privy_wallet_id=f"imported:{address.lower()}",
        address=address.lower(),
        provider=provider,
        default_chain=chain,
        status=WalletStatus.ACTIVE,
        created_at=CreatedAt(now),
        updated_at=UpdatedAt(now),
    )


class TestGetMyWalletsHandler:
    """Tests for GetMyWalletsHandler."""

    @pytest.fixture
    def mock_user(self):
        """Create a mock user."""
        user = MagicMock()
        user.id_.value = 123
        user.privy_user_id.value = "did:privy:abc123"
        user.primary_wallet_address.value = "0x1234567890abcdef1234567890abcdef12345678"
        return user

    @pytest.fixture
    def mock_user_no_privy(self):
        """Create a mock user without Privy."""
        user = MagicMock()
        user.id_.value = 456
        user.privy_user_id = None
        user.primary_wallet_address.value = "0xabcdef1234567890abcdef1234567890abcdef12"
        return user

    @pytest.fixture
    def mock_current_user_service(self, mock_user):
        """Create a mock CurrentUserService."""
        service = MagicMock(spec=CurrentUserService)
        service.get_current_user = AsyncMock(return_value=mock_user)
        return service

    @pytest.fixture
    def mock_wallet_provider(self):
        """Create a mock EmbeddedWalletProviderPort."""
        provider = MagicMock(spec=EmbeddedWalletProviderPort)
        
        # Default: return empty list
        provider.list_user_wallets = AsyncMock(return_value=[])
        return provider

    @pytest.fixture
    def mock_wallet_repository(self):
        """Create a mock WalletRepository."""
        repo = MagicMock(spec=WalletRepository)
        
        # Default: return empty list for imported wallets
        repo.get_by_user_and_provider = AsyncMock(return_value=[])
        return repo

    @pytest.fixture
    def handler(self, mock_current_user_service, mock_wallet_provider, mock_wallet_repository):
        """Create handler instance."""
        return GetMyWalletsHandler(
            current_user_service=mock_current_user_service,
            wallet_provider=mock_wallet_provider,
            wallet_repository=mock_wallet_repository,
        )

    @pytest.mark.asyncio
    async def test_get_wallets_from_privy_only(self, handler, mock_wallet_provider):
        """Test getting wallets from Privy only."""
        # Setup Privy wallets
        mock_wallet_provider.list_user_wallets = AsyncMock(return_value=[
            WalletInfo(
                wallet_id="wallet_1",
                address="0x1234567890abcdef1234567890abcdef12345678",
                chain_type=ProviderChainType.ETHEREUM,
                wallet_type=WalletType.EMBEDDED,
                created_at=datetime.utcnow(),
            ),
        ])

        result = await handler.execute()

        assert isinstance(result, WalletsResponse)
        assert result.user_id == 123
        assert result.privy_connected is True
        assert len(result.wallets) == 1
        assert result.wallets[0].wallet_type == "embedded"
        assert result.wallets[0].source == "privy"
        assert result.wallets[0].is_primary is True  # Matches primary address

    @pytest.mark.asyncio
    async def test_get_wallets_from_local_only(
        self, mock_current_user_service, mock_user_no_privy, 
        mock_wallet_provider, mock_wallet_repository
    ):
        """Test getting wallets from local database only (no Privy)."""
        # User without Privy
        mock_current_user_service.get_current_user = AsyncMock(return_value=mock_user_no_privy)
        
        handler = GetMyWalletsHandler(
            current_user_service=mock_current_user_service,
            wallet_provider=mock_wallet_provider,
            wallet_repository=mock_wallet_repository,
        )
        
        # Setup imported wallet in local DB
        mock_wallet_repository.get_by_user_and_provider = AsyncMock(return_value=[
            make_wallet(1, 456, "0ximported123"),
        ])

        result = await handler.execute()

        assert isinstance(result, WalletsResponse)
        assert result.user_id == 456
        assert result.privy_connected is False
        assert len(result.wallets) >= 1
        
        # Find the imported wallet
        imported_wallet = next((w for w in result.wallets if w.wallet_type == "imported"), None)
        assert imported_wallet is not None
        assert imported_wallet.source == "local"

    @pytest.mark.asyncio
    async def test_get_wallets_combined_privy_and_imported(
        self, handler, mock_wallet_provider, mock_wallet_repository
    ):
        """Test getting wallets from both Privy and local database."""
        # Setup Privy wallet
        mock_wallet_provider.list_user_wallets = AsyncMock(return_value=[
            WalletInfo(
                wallet_id="wallet_privy",
                address="0x1234567890abcdef1234567890abcdef12345678",
                chain_type=ProviderChainType.ETHEREUM,
                wallet_type=WalletType.EMBEDDED,
                created_at=datetime.utcnow(),
            ),
        ])
        
        # Setup imported wallet in local DB
        mock_wallet_repository.get_by_user_and_provider = AsyncMock(return_value=[
            make_wallet(1, 123, "0ximportedwallet", chain=ChainType.BASE),
        ])

        result = await handler.execute()

        assert isinstance(result, WalletsResponse)
        assert result.privy_connected is True
        assert len(result.wallets) == 2
        
        # Check wallet types
        types = {w.wallet_type for w in result.wallets}
        assert types == {"embedded", "imported"}
        
        # Check sources
        sources = {w.source for w in result.wallets}
        assert sources == {"privy", "local"}

    @pytest.mark.asyncio
    async def test_get_wallets_deduplicates_by_address(
        self, handler, mock_wallet_provider, mock_wallet_repository
    ):
        """Test that wallets are deduplicated by address."""
        # Same address in both Privy and local DB
        duplicate_address = "0x1234567890abcdef1234567890abcdef12345678"
        
        # Setup Privy wallet
        mock_wallet_provider.list_user_wallets = AsyncMock(return_value=[
            WalletInfo(
                wallet_id="wallet_privy",
                address=duplicate_address,
                chain_type=ProviderChainType.ETHEREUM,
                wallet_type=WalletType.EMBEDDED,
                created_at=datetime.utcnow(),
            ),
        ])
        
        # Setup same address as imported in local DB
        mock_wallet_repository.get_by_user_and_provider = AsyncMock(return_value=[
            make_wallet(1, 123, duplicate_address),
        ])

        result = await handler.execute()

        # Should only have 1 wallet (Privy takes priority)
        assert len(result.wallets) == 1
        assert result.wallets[0].source == "privy"
        assert result.wallets[0].wallet_type == "embedded"

    @pytest.mark.asyncio
    async def test_get_wallets_primary_detection(
        self, handler, mock_wallet_provider, mock_wallet_repository
    ):
        """Test that primary wallet is correctly identified."""
        primary_address = "0x1234567890abcdef1234567890abcdef12345678"
        
        # Setup multiple wallets
        mock_wallet_provider.list_user_wallets = AsyncMock(return_value=[
            WalletInfo(
                wallet_id="wallet_1",
                address="0xother1111111111111111111111111111111111",
                chain_type=ProviderChainType.ETHEREUM,
                wallet_type=WalletType.EMBEDDED,
                created_at=datetime.utcnow(),
            ),
            WalletInfo(
                wallet_id="wallet_2",
                address=primary_address,
                chain_type=ProviderChainType.ETHEREUM,
                wallet_type=WalletType.EMBEDDED,
                created_at=datetime.utcnow(),
            ),
        ])

        result = await handler.execute()

        assert len(result.wallets) == 2
        
        # Primary wallet should be first
        assert result.wallets[0].is_primary is True
        assert result.wallets[0].address.lower() == primary_address.lower()
        
        # Other wallet should not be primary
        assert result.wallets[1].is_primary is False

    @pytest.mark.asyncio
    async def test_get_wallets_handles_privy_error(
        self, handler, mock_wallet_provider, mock_wallet_repository
    ):
        """Test that Privy errors are handled gracefully."""
        from app.domain.ports.wallet.embedded_wallet_provider import WalletProviderError
        
        # Privy fails
        mock_wallet_provider.list_user_wallets = AsyncMock(
            side_effect=WalletProviderError("API error", "privy")
        )
        
        # But we have imported wallets
        mock_wallet_repository.get_by_user_and_provider = AsyncMock(return_value=[
            make_wallet(1, 123, "0ximported"),
        ])

        result = await handler.execute()

        # Should still return imported wallets
        assert result.privy_connected is False
        assert result.message is not None  # Error message
        assert len(result.wallets) >= 1
        
        # Imported wallet should be present
        imported = next((w for w in result.wallets if w.wallet_type == "imported"), None)
        assert imported is not None
