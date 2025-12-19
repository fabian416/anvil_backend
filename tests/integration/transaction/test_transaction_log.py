"""
Integration tests for transaction logging and history endpoints.

Tests the /api/v1/user/transactions endpoints for logging and retrieving
transaction history.
"""

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.common.services.current_user import CurrentUserService
from app.domain.transactions.entities.transaction import Transaction, TransactionId
from app.domain.entities.wallet import Wallet, WalletId
from app.domain.enums.chain_type import ChainType
from app.domain.enums.transaction_status import TransactionStatus
from app.domain.enums.transaction_type import TransactionType
from app.domain.enums.wallet_provider import WalletProvider
from app.domain.enums.wallet_status import WalletStatus
from app.domain.transactions.ports.transaction.transaction_repository import TransactionRepository
from app.domain.ports.wallet.wallet_repository import WalletRepository
from app.domain.value_objects.created_at import CreatedAt
from app.domain.value_objects.updated_at import UpdatedAt
from app.domain.value_objects.user_id import UserId
from app.infrastructure.auth.handlers.transaction_log import (
    GetTransactionHistoryHandler,
    LogTransactionHandler,
    LogTransactionInput,
    LogTransactionResult,
    TransactionHistoryResult,
    WalletNotFoundForTransactionError,
)


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

        # Only return wallet for sender's address, not for receiver
        async def mock_get_by_address(address: str):
            if address.lower() == mock_wallet.address.lower():
                return mock_wallet
            return None  # Receiver not registered

        repo.get_by_address = AsyncMock(side_effect=mock_get_by_address)
        return repo

    @pytest.fixture
    def mock_transaction_repository(self):
        """Create a mock TransactionRepository."""
        repo = MagicMock(spec=TransactionRepository)
        repo.get_by_tx_hash = AsyncMock(return_value=None)
        repo.get_by_user_and_tx_hash = AsyncMock(return_value=None)

        async def mock_save(tx):
            now = datetime.now(UTC)
            return Transaction(
                id_=TransactionId(1),
                user_id=tx.user_id,
                wallet_id=tx.wallet_id,
                to_address=tx.to_address,
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
                gas_used=tx.gas_used,
                gas_price=tx.gas_price,
                tx_metadata=tx.tx_metadata,
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
    async def test_log_transaction_base_sepolia(
        self, handler, mock_transaction_repository
    ):
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
            to_address="0xabcdef1234567890abcdef1234567890abcdef12",
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
            gas_used=21000,
            gas_price=30000000000,
            tx_metadata=None,
        )
        # Now we check per-user, not globally
        mock_transaction_repository.get_by_user_and_tx_hash = AsyncMock(
            return_value=existing_tx
        )

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


class TestLogTransactionHandlerDualLogging:
    """Tests for dual transaction logging (sender and receiver)."""

    @pytest.fixture
    def mock_sender_user(self):
        """Create a mock sender user."""
        user = MagicMock()
        user.id_.value = 100
        user.privy_user_id = MagicMock()
        user.privy_user_id.value = "did:privy:sender123"
        user.primary_wallet_address = MagicMock()
        user.primary_wallet_address.value = "0x1111111111111111111111111111111111111111"
        return user

    @pytest.fixture
    def mock_sender_wallet(self):
        """Create a mock sender wallet."""
        now = datetime.now(UTC)
        return Wallet(
            id_=WalletId(1),
            user_id=UserId(100),
            privy_wallet_id="sender_wallet_123",
            address="0x1111111111111111111111111111111111111111",
            provider=WalletProvider.PRIVY,
            default_chain=ChainType.ETHEREUM,
            status=WalletStatus.ACTIVE,
            created_at=CreatedAt(now),
            updated_at=UpdatedAt(now),
        )

    @pytest.fixture
    def mock_receiver_wallet(self):
        """Create a mock receiver wallet (different user)."""
        now = datetime.now(UTC)
        return Wallet(
            id_=WalletId(2),
            user_id=UserId(200),  # Different user ID
            privy_wallet_id="receiver_wallet_456",
            address="0x2222222222222222222222222222222222222222",
            provider=WalletProvider.PRIVY,
            default_chain=ChainType.ETHEREUM,
            status=WalletStatus.ACTIVE,
            created_at=CreatedAt(now),
            updated_at=UpdatedAt(now),
        )

    @pytest.fixture
    def mock_current_user_service(self, mock_sender_user):
        """Create a mock CurrentUserService for sender."""
        service = MagicMock(spec=CurrentUserService)
        service.get_current_user = AsyncMock(return_value=mock_sender_user)
        return service

    @pytest.fixture
    def mock_transaction_repository(self):
        """Create a mock TransactionRepository."""
        repo = MagicMock(spec=TransactionRepository)
        repo.get_by_user_and_tx_hash = AsyncMock(return_value=None)
        repo.get_by_tx_hash = AsyncMock(return_value=None)

        saved_tx_counter = [0]  # Use list to allow mutation in closure

        async def mock_save(tx):
            saved_tx_counter[0] += 1
            now = datetime.now(UTC)
            return Transaction(
                id_=TransactionId(saved_tx_counter[0]),
                user_id=tx.user_id,
                wallet_id=tx.wallet_id,
                to_address=tx.to_address,
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
                gas_used=tx.gas_used,
                gas_price=tx.gas_price,
                tx_metadata=tx.tx_metadata,
            )

        repo.save = AsyncMock(side_effect=mock_save)
        return repo

    @pytest.mark.asyncio
    async def test_log_transaction_creates_sender_and_receiver_records(
        self,
        mock_current_user_service,
        mock_transaction_repository,
        mock_sender_wallet,
        mock_receiver_wallet,
    ):
        """Test that transaction is logged for both sender and receiver."""
        # Setup wallet repository to return sender wallet for sender address
        # and receiver wallet for receiver address
        mock_wallet_repository = MagicMock(spec=WalletRepository)

        async def mock_get_by_user_and_address(user_id, address):
            if user_id.value == 100 and address == mock_sender_wallet.address:
                return mock_sender_wallet
            return None

        async def mock_get_by_address(address):
            if address == mock_sender_wallet.address.lower():
                return mock_sender_wallet
            if address == mock_receiver_wallet.address.lower():
                return mock_receiver_wallet
            return None

        mock_wallet_repository.get_by_user_and_address = AsyncMock(
            side_effect=mock_get_by_user_and_address
        )
        mock_wallet_repository.get_by_address = AsyncMock(
            side_effect=mock_get_by_address
        )

        handler = LogTransactionHandler(
            current_user_service=mock_current_user_service,
            transaction_repository=mock_transaction_repository,
            wallet_repository=mock_wallet_repository,
        )

        input_data = LogTransactionInput(
            tx_hash="0xabc123def456789012345678901234567890123456789012345678901234abcd",
            from_address=mock_sender_wallet.address,
            to_address=mock_receiver_wallet.address,
            value="1000000000000000000",  # 1 ETH
            chain_id=1,
            tx_type="send",
            asset_symbol="ETH",
        )

        result = await handler.execute(input_data)

        # Verify the handler returns successfully
        assert isinstance(result, LogTransactionResult)
        assert result.tx_hash.startswith("0x")

        # Verify save was called twice (once for sender, once for receiver)
        assert mock_transaction_repository.save.call_count == 2

        # Verify the first save was for the sender
        first_save_call = mock_transaction_repository.save.call_args_list[0]
        sender_tx = first_save_call[0][0]
        assert sender_tx.user_id.value == 100  # Sender user ID
        assert sender_tx.wallet_id.value == 1  # Sender wallet ID

        # Verify the second save was for the receiver
        second_save_call = mock_transaction_repository.save.call_args_list[1]
        receiver_tx = second_save_call[0][0]
        assert receiver_tx.user_id.value == 200  # Receiver user ID
        assert receiver_tx.wallet_id.value == 2  # Receiver wallet ID
        assert receiver_tx.tx_metadata == {
            "receiver_view": True,
            "from_address": mock_sender_wallet.address.lower(),
        }

    @pytest.mark.asyncio
    async def test_log_transaction_only_sender_when_receiver_not_registered(
        self,
        mock_current_user_service,
        mock_transaction_repository,
        mock_sender_wallet,
    ):
        """Test that only sender's transaction is logged when receiver is not registered."""
        mock_wallet_repository = MagicMock(spec=WalletRepository)

        async def mock_get_by_user_and_address(user_id, address):
            if user_id.value == 100 and address == mock_sender_wallet.address:
                return mock_sender_wallet
            return None

        async def mock_get_by_address(address):
            # Only sender wallet exists, receiver address is not in system
            if address == mock_sender_wallet.address.lower():
                return mock_sender_wallet
            return None  # Receiver not found

        mock_wallet_repository.get_by_user_and_address = AsyncMock(
            side_effect=mock_get_by_user_and_address
        )
        mock_wallet_repository.get_by_address = AsyncMock(
            side_effect=mock_get_by_address
        )

        handler = LogTransactionHandler(
            current_user_service=mock_current_user_service,
            transaction_repository=mock_transaction_repository,
            wallet_repository=mock_wallet_repository,
        )

        input_data = LogTransactionInput(
            tx_hash="0x9999888877776666555544443333222211110000aaabbbbccccddddeeeefffff",
            from_address=mock_sender_wallet.address,
            to_address="0x9999999999999999999999999999999999999999",  # Not registered
            value="500000000000000000",  # 0.5 ETH
            chain_id=1,
            tx_type="send",
        )

        result = await handler.execute(input_data)

        # Verify the handler returns successfully
        assert isinstance(result, LogTransactionResult)

        # Verify save was called only once (for sender only)
        assert mock_transaction_repository.save.call_count == 1

        # Verify it was the sender's transaction
        save_call = mock_transaction_repository.save.call_args_list[0]
        saved_tx = save_call[0][0]
        assert saved_tx.user_id.value == 100

    @pytest.mark.asyncio
    async def test_log_transaction_no_duplicate_when_sender_is_receiver(
        self,
        mock_current_user_service,
        mock_transaction_repository,
        mock_sender_wallet,
    ):
        """Test that only one record is created when sender sends to themselves."""
        mock_wallet_repository = MagicMock(spec=WalletRepository)

        async def mock_get_by_user_and_address(user_id, address):
            if user_id.value == 100:
                return mock_sender_wallet
            return None

        async def mock_get_by_address(address):
            # Same wallet for both sender and receiver
            if address == mock_sender_wallet.address.lower():
                return mock_sender_wallet
            return None

        mock_wallet_repository.get_by_user_and_address = AsyncMock(
            side_effect=mock_get_by_user_and_address
        )
        mock_wallet_repository.get_by_address = AsyncMock(
            side_effect=mock_get_by_address
        )

        handler = LogTransactionHandler(
            current_user_service=mock_current_user_service,
            transaction_repository=mock_transaction_repository,
            wallet_repository=mock_wallet_repository,
        )

        input_data = LogTransactionInput(
            tx_hash="0xeeeedddccccbbbbaaaa0000111122223333444455556666777788889999aaaa",
            from_address=mock_sender_wallet.address,
            to_address=mock_sender_wallet.address,  # Same as sender!
            value="100000000000000000",  # 0.1 ETH
            chain_id=1,
            tx_type="send",
        )

        result = await handler.execute(input_data)

        # Verify the handler returns successfully
        assert isinstance(result, LogTransactionResult)

        # Verify save was called only once (no duplicate for self-send)
        assert mock_transaction_repository.save.call_count == 1

    @pytest.mark.asyncio
    async def test_log_transaction_receiver_error_does_not_break_sender(
        self,
        mock_current_user_service,
        mock_sender_wallet,
        mock_receiver_wallet,
    ):
        """Test that receiver logging error doesn't affect sender's transaction."""
        mock_transaction_repository = MagicMock(spec=TransactionRepository)
        mock_transaction_repository.get_by_user_and_tx_hash = AsyncMock(return_value=None)

        save_call_count = [0]

        async def mock_save(tx):
            save_call_count[0] += 1
            if save_call_count[0] == 1:
                # First call (sender) succeeds
                now = datetime.now(UTC)
                return Transaction(
                    id_=TransactionId(1),
                    user_id=tx.user_id,
                    wallet_id=tx.wallet_id,
                    to_address=tx.to_address,
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
                    gas_used=tx.gas_used,
                    gas_price=tx.gas_price,
                    tx_metadata=tx.tx_metadata,
                )
            else:
                # Second call (receiver) fails
                raise Exception("Database error for receiver")

        mock_transaction_repository.save = AsyncMock(side_effect=mock_save)

        mock_wallet_repository = MagicMock(spec=WalletRepository)

        async def mock_get_by_user_and_address(user_id, address):
            if user_id.value == 100:
                return mock_sender_wallet
            return None

        async def mock_get_by_address(address):
            if address == mock_sender_wallet.address.lower():
                return mock_sender_wallet
            if address == mock_receiver_wallet.address.lower():
                return mock_receiver_wallet
            return None

        mock_wallet_repository.get_by_user_and_address = AsyncMock(
            side_effect=mock_get_by_user_and_address
        )
        mock_wallet_repository.get_by_address = AsyncMock(
            side_effect=mock_get_by_address
        )

        handler = LogTransactionHandler(
            current_user_service=mock_current_user_service,
            transaction_repository=mock_transaction_repository,
            wallet_repository=mock_wallet_repository,
        )

        input_data = LogTransactionInput(
            tx_hash="0xfff000111222333444555666777888999aaabbbcccdddeeefff000111222333",
            from_address=mock_sender_wallet.address,
            to_address=mock_receiver_wallet.address,
            value="1000000000000000000",
            chain_id=1,
            tx_type="send",
        )

        # Should not raise, even though receiver save fails
        result = await handler.execute(input_data)

        # Verify the sender's transaction was still saved successfully
        assert isinstance(result, LogTransactionResult)
        assert result.id == 1


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
                to_address="0x" + "a" * 40,
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
                gas_used=21000,
                gas_price=30000000000,
                tx_metadata=None,
            ),
            Transaction(
                id_=TransactionId(2),
                user_id=UserId(123),
                wallet_id=WalletId(1),
                to_address="0x" + "b" * 40,
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
                gas_used=None,
                gas_price=None,
                tx_metadata={"protocol": "1inch"},
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
    async def test_get_history_with_pagination(
        self, handler, mock_transaction_repository
    ):
        """Test pagination parameters are passed correctly."""
        await handler.execute(limit=10, offset=5)

        mock_transaction_repository.get_by_user_id.assert_called_once()
        call_kwargs = mock_transaction_repository.get_by_user_id.call_args.kwargs
        assert call_kwargs["limit"] == 10
        assert call_kwargs["offset"] == 5

    @pytest.mark.asyncio
    async def test_get_history_with_chain_filter(
        self, handler, mock_transaction_repository
    ):
        """Test chain filter is applied correctly."""
        await handler.execute(chain="ethereum")

        call_kwargs = mock_transaction_repository.get_by_user_id.call_args.kwargs
        assert call_kwargs["chain"] == ChainType.ETHEREUM

    @pytest.mark.asyncio
    async def test_get_history_with_status_filter(
        self, handler, mock_transaction_repository
    ):
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
