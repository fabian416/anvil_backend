"""
Integration tests for transaction logging and history endpoints.

Tests the /api/v1/transactions endpoints for logging and retrieving
transaction history.
"""

import pytest
from datetime import datetime, UTC
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

from app.infrastructure.auth.handlers.transaction_log import (
    LogTransactionHandler,
    LogTransactionInput,
    LogTransactionResult,
    GetTransactionHistoryHandler,
    TransactionHistoryItem,
    TransactionHistoryResult,
    WalletNotFoundForTransactionError,
)
from app.application.common.services.current_user import CurrentUserService
from app.domain.ports.transaction.transaction_repository import TransactionRepository
from app.domain.ports.wallet.wallet_repository import WalletRepository
from app.domain.entities.transaction import Transaction, TransactionId
from app.domain.entities.wallet import Wallet, WalletId
from app.domain.enums.chain_type import ChainType
from app.domain.enums.transaction_type import TransactionType
from app.domain.enums.transaction_status import TransactionStatus
from app.domain.enums.wallet_provider import WalletProvider
from app.domain.enums.wallet_status import WalletStatus
from app.domain.value_objects.user_id import UserId
from app.domain.value_objects.created_at import CreatedAt
from app.domain.value_objects.updated_at import UpdatedAt


class TestLogTransactionHandler:
    """Tests for LogTransactionHandler."""

    @pytest.fixture
    def mock_user(self):
        """Create a mock user."""
        user = MagicMock()
        user.id_.value = 123
        user.privy_user_id = MagicMock()
        user.privy_user_id.value = "did:privy:abc123"
        user.primary_wallet_address = MagicMock()
        user.primary_wallet_address.value = "0x1234567890abcdef1234567890abcdef12345678"
        return user

    @pytest.fixture
    def mock_current_user_service(self, mock_user):
        """Create a mock CurrentUserService."""
        service = MagicMock(spec=CurrentUserService)
        service.get_current_user = AsyncMock(return_value=mock_user)
        return service

    @pytest.fixture
    def mock_wallet(self):
        """Create a mock wallet."""
        now = datetime.now(UTC)
        return Wallet(
            id_=WalletId(1),
            user_id=UserId(123),
            privy_wallet_id="wallet_123",
            address="0x1234567890abcdef1234567890abcdef12345678",
            provider=WalletProvider.PRIVY,
            default_chain=ChainType.ETHEREUM,
            status=WalletStatus.ACTIVE,
            created_at=CreatedAt(now),
            updated_at=UpdatedAt(now),
        )

    @pytest.fixture
    def mock_wallet_repository(self, mock_wallet):
        """Create a mock WalletRepository."""
        repo = MagicMock(spec=WalletRepository)
        repo.get_by_user_and_address = AsyncMock(return_value=mock_wallet)
        repo.get_by_address = AsyncMock(return_value=mock_wallet)
        return repo

    @pytest.fixture
    def mock_transaction_repository(self):
        """Create a mock TransactionRepository."""
        repo = MagicMock(spec=TransactionRepository)
        repo.get_by_tx_hash = AsyncMock(return_value=None)

        async def mock_save(tx):
            now = datetime.now(UTC)
            return Transaction(
                id_=TransactionId(1),
                user_id=tx.user_id,
                wallet_id=tx.wallet_id,
                type=tx.type,
                chain=tx.chain,
                asset_in=tx.asset_in,
                amount_in=tx.amount_in,
                asset_out=tx.asset_out,
                amount_out=tx.amount_out,
                fee=tx.fee,
                fee_usd=tx.fee_usd,
                tx_hash=tx.tx_hash,
                status=tx.status,
                dex_aggregator=tx.dex_aggregator,
                dex_route=tx.dex_route,
                slippage=tx.slippage,
                error_message=tx.error_message,
                block_number=tx.block_number,
                confirmed_at=tx.confirmed_at,
                created_at=CreatedAt(now),
            )

        repo.save = AsyncMock(side_effect=mock_save)
        return repo

    @pytest.fixture
    def handler(
        self,
        mock_current_user_service,
        mock_transaction_repository,
        mock_wallet_repository,
    ):
        """Create handler instance."""
        return LogTransactionHandler(
            current_user_service=mock_current_user_service,
            transaction_repository=mock_transaction_repository,
            wallet_repository=mock_wallet_repository,
        )

    @pytest.mark.asyncio
    async def test_log_transaction_success(self, handler, mock_transaction_repository):
        """Test logging a transaction successfully."""
        input_data = LogTransactionInput(
            tx_hash="0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
            from_address="0x1234567890abcdef1234567890abcdef12345678",
            to_address="0xabcdef1234567890abcdef1234567890abcdef12",
            value="1000000000000000000",  # 1 ETH in wei
            chain_id=1,
            tx_type="send",
            asset_symbol="ETH",
        )

        result = await handler.execute(input_data)

        assert isinstance(result, LogTransactionResult)
        assert result.id == 1
        assert result.tx_hash.startswith("0x")
        assert result.status == "pending"
        assert result.chain == "ethereum"
        assert result.tx_type == "send"
        mock_transaction_repository.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_log_transaction_base_sepolia(self, handler, mock_transaction_repository):
        """Test logging a transaction on Base Sepolia."""
        input_data = LogTransactionInput(
            tx_hash="0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
            from_address="0x1234567890abcdef1234567890abcdef12345678",
            to_address="0xabcdef1234567890abcdef1234567890abcdef12",
            value="0",
            chain_id=84532,  # Base Sepolia
            tx_type="send",
        )

        result = await handler.execute(input_data)

        assert result.chain == "base"
        assert result.status == "pending"

    @pytest.mark.asyncio
    async def test_log_transaction_already_exists(
        self, handler, mock_transaction_repository
    ):
        """Test that logging an existing transaction returns the existing record."""
        now = datetime.now(UTC)
        existing_tx = Transaction(
            id_=TransactionId(42),
            user_id=UserId(123),
            wallet_id=WalletId(1),
            type=TransactionType.SEND,
            chain=ChainType.ETHEREUM,
            asset_in="ETH",
            amount_in=Decimal("1000000000000000000"),
            asset_out=None,
            amount_out=None,
            fee=None,
            fee_usd=None,
            tx_hash="0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
            status=TransactionStatus.SUCCESS,
            dex_aggregator=None,
            dex_route=None,
            slippage=None,
            error_message=None,
            block_number=18500000,
            confirmed_at=now,
            created_at=CreatedAt(now),
        )
        mock_transaction_repository.get_by_tx_hash = AsyncMock(return_value=existing_tx)

        input_data = LogTransactionInput(
            tx_hash="0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
            from_address="0x1234567890abcdef1234567890abcdef12345678",
            to_address="0xabcdef1234567890abcdef1234567890abcdef12",
            value="1000000000000000000",
            chain_id=1,
        )

        result = await handler.execute(input_data)

        assert result.id == 42  # Existing ID
        assert result.status == "success"  # Existing status
        mock_transaction_repository.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_log_transaction_wallet_not_found(
        self,
        mock_current_user_service,
        mock_transaction_repository,
    ):
        """Test that logging fails when wallet is not found."""
        mock_wallet_repository = MagicMock(spec=WalletRepository)
        mock_wallet_repository.get_by_user_and_address = AsyncMock(return_value=None)
        mock_wallet_repository.get_by_address = AsyncMock(return_value=None)

        handler = LogTransactionHandler(
            current_user_service=mock_current_user_service,
            transaction_repository=mock_transaction_repository,
            wallet_repository=mock_wallet_repository,
        )

        input_data = LogTransactionInput(
            tx_hash="0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
            from_address="0xunknownwallet1234567890abcdef1234567890",
            to_address="0xabcdef1234567890abcdef1234567890abcdef12",
            value="1000000000000000000",
            chain_id=1,
        )

        with pytest.raises(WalletNotFoundForTransactionError):
            await handler.execute(input_data)


class TestGetTransactionHistoryHandler:
    """Tests for GetTransactionHistoryHandler."""

    @pytest.fixture
    def mock_user(self):
        """Create a mock user."""
        user = MagicMock()
        user.id_.value = 123
        return user

    @pytest.fixture
    def mock_current_user_service(self, mock_user):
        """Create a mock CurrentUserService."""
        service = MagicMock(spec=CurrentUserService)
        service.get_current_user = AsyncMock(return_value=mock_user)
        return service

    @pytest.fixture
    def mock_transactions(self):
        """Create mock transactions."""
        now = datetime.now(UTC)
        return [
            Transaction(
                id_=TransactionId(1),
                user_id=UserId(123),
                wallet_id=WalletId(1),
                type=TransactionType.SEND,
                chain=ChainType.ETHEREUM,
                asset_in="ETH",
                amount_in=Decimal("1000000000000000000"),
                asset_out=None,
                amount_out=None,
                fee=Decimal("0.001"),
                fee_usd=Decimal("2.50"),
                tx_hash="0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
                status=TransactionStatus.SUCCESS,
                dex_aggregator=None,
                dex_route=None,
                slippage=None,
                error_message=None,
                block_number=18500000,
                confirmed_at=now,
                created_at=CreatedAt(now),
            ),
            Transaction(
                id_=TransactionId(2),
                user_id=UserId(123),
                wallet_id=WalletId(1),
                type=TransactionType.SWAP,
                chain=ChainType.BASE,
                asset_in="USDC",
                amount_in=Decimal("100000000"),  # 100 USDC
                asset_out="ETH",
                amount_out=Decimal("50000000000000000"),  # 0.05 ETH
                fee=Decimal("0.0005"),
                fee_usd=Decimal("1.25"),
                tx_hash="0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
                status=TransactionStatus.PENDING,
                dex_aggregator="1inch",
                dex_route={"path": ["USDC", "ETH"]},
                slippage=Decimal("0.5"),
                error_message=None,
                block_number=None,
                confirmed_at=None,
                created_at=CreatedAt(now),
            ),
        ]

    @pytest.fixture
    def mock_transaction_repository(self, mock_transactions):
        """Create a mock TransactionRepository."""
        repo = MagicMock(spec=TransactionRepository)
        repo.get_by_user_id = AsyncMock(return_value=mock_transactions)
        repo.count_by_user_id = AsyncMock(return_value=2)
        return repo

    @pytest.fixture
    def handler(self, mock_current_user_service, mock_transaction_repository):
        """Create handler instance."""
        return GetTransactionHistoryHandler(
            current_user_service=mock_current_user_service,
            transaction_repository=mock_transaction_repository,
        )

    @pytest.mark.asyncio
    async def test_get_history_success(self, handler):
        """Test getting transaction history successfully."""
        result = await handler.execute()

        assert isinstance(result, TransactionHistoryResult)
        assert result.user_id == 123
        assert len(result.transactions) == 2
        assert result.total == 2

    @pytest.mark.asyncio
    async def test_get_history_with_pagination(self, handler, mock_transaction_repository):
        """Test pagination parameters are passed correctly."""
        await handler.execute(limit=10, offset=5)

        mock_transaction_repository.get_by_user_id.assert_called_once()
        call_kwargs = mock_transaction_repository.get_by_user_id.call_args.kwargs
        assert call_kwargs["limit"] == 10
        assert call_kwargs["offset"] == 5

    @pytest.mark.asyncio
    async def test_get_history_with_chain_filter(self, handler, mock_transaction_repository):
        """Test chain filter is applied correctly."""
        await handler.execute(chain="ethereum")

        call_kwargs = mock_transaction_repository.get_by_user_id.call_args.kwargs
        assert call_kwargs["chain"] == ChainType.ETHEREUM

    @pytest.mark.asyncio
    async def test_get_history_with_status_filter(self, handler, mock_transaction_repository):
        """Test status filter is applied correctly."""
        await handler.execute(status="pending")

        call_kwargs = mock_transaction_repository.get_by_user_id.call_args.kwargs
        assert call_kwargs["status"] == TransactionStatus.PENDING

    @pytest.mark.asyncio
    async def test_get_history_includes_explorer_urls(self, handler):
        """Test that explorer URLs are generated for transactions."""
        result = await handler.execute()

        # First transaction is on Ethereum
        eth_tx = next(t for t in result.transactions if t.chain == "ethereum")
        assert eth_tx.explorer_url is not None
        assert "etherscan.io" in eth_tx.explorer_url

        # Second transaction is on Base
        base_tx = next(t for t in result.transactions if t.chain == "base")
        assert base_tx.explorer_url is not None
        assert "basescan.org" in base_tx.explorer_url

    @pytest.mark.asyncio
    async def test_get_history_empty(self, mock_current_user_service):
        """Test getting empty transaction history."""
        mock_repo = MagicMock(spec=TransactionRepository)
        mock_repo.get_by_user_id = AsyncMock(return_value=[])
        mock_repo.count_by_user_id = AsyncMock(return_value=0)

        handler = GetTransactionHistoryHandler(
            current_user_service=mock_current_user_service,
            transaction_repository=mock_repo,
        )

        result = await handler.execute()

        assert result.transactions == []
        assert result.total == 0
