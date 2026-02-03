"""
Integration tests for transaction confirmation service.

Tests the TransactionConfirmationService that monitors pending transactions
and updates their status when confirmed on-chain.
"""

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.application.transactions.services.confirmation_service import (
    ConfirmationResult,
    TransactionConfirmationService,
    TransactionReceipt,
)
from app.domain.transactions.entities.transaction import Transaction, TransactionId
from app.domain.entities.wallet import WalletId
from app.domain.enums.chain_type import ChainType
from app.domain.enums.transaction_status import TransactionStatus
from app.domain.enums.transaction_type import TransactionType
from app.domain.transactions.ports.transaction.transaction_repository import (
    TransactionRepository,
)
from app.domain.value_objects.created_at import CreatedAt
from app.domain.value_objects.user_id import UserId


class TestTransactionConfirmationService:
    """Tests for TransactionConfirmationService."""

    @pytest.fixture
    def mock_pending_transactions(self):
        """Create mock pending transactions."""
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
                fee=None,
                fee_usd=None,
                tx_hash="0x1111111111111111111111111111111111111111111111111111111111111111",
                status=TransactionStatus.PENDING,
                dex_aggregator=None,
                dex_route=None,
                slippage=None,
                error_message=None,
                block_number=None,
                confirmed_at=None,
                created_at=CreatedAt(now),
                gas_used=None,
                gas_price=None,
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
                amount_in=Decimal("100000000"),
                asset_out="ETH",
                amount_out=None,
                fee=None,
                fee_usd=None,
                tx_hash="0x2222222222222222222222222222222222222222222222222222222222222222",
                status=TransactionStatus.PENDING,
                dex_aggregator="1inch",
                dex_route=None,
                slippage=Decimal("0.5"),
                error_message=None,
                block_number=None,
                confirmed_at=None,
                created_at=CreatedAt(now),
                gas_used=None,
                gas_price=None,
                tx_metadata=None,
            ),
        ]

    @pytest.fixture
    def mock_transaction_repository(self, mock_pending_transactions):
        """Create a mock TransactionRepository."""
        repo = MagicMock(spec=TransactionRepository)
        repo.get_pending_transactions = AsyncMock(
            return_value=mock_pending_transactions
        )
        repo.update_status = AsyncMock(return_value=True)
        return repo

    @pytest.fixture
    def service(self, mock_transaction_repository):
        """Create service instance."""
        return TransactionConfirmationService(
            transaction_repository=mock_transaction_repository,
            use_testnet=True,
        )

    @pytest.mark.asyncio
    async def test_confirm_transaction_success(self, service):
        """Test confirming a successful transaction."""
        # Mock successful receipt
        with patch.object(service, "_fetch_receipt_via_rpc") as mock_fetch:
            mock_fetch.return_value = TransactionReceipt(
                status=True,
                block_number=18500000,
                gas_used=21000,
                effective_gas_price=50000000000,  # 50 Gwei
            )

            result = await service.confirm_transaction(
                transaction_id=1,
                tx_hash="0x1111111111111111111111111111111111111111111111111111111111111111",
                chain=ChainType.ETHEREUM,
            )

            assert isinstance(result, ConfirmationResult)
            assert result.success is True
            assert result.status == TransactionStatus.SUCCESS
            assert result.block_number == 18500000
            assert result.confirmed_at is not None
            assert result.fee_wei == 21000 * 50000000000

    @pytest.mark.asyncio
    async def test_confirm_transaction_failed(self, service):
        """Test confirming a reverted transaction."""
        with patch.object(service, "_fetch_receipt_via_rpc") as mock_fetch:
            mock_fetch.return_value = TransactionReceipt(
                status=False,  # Reverted
                block_number=18500001,
                gas_used=50000,
                effective_gas_price=40000000000,
            )

            result = await service.confirm_transaction(
                transaction_id=1,
                tx_hash="0x1111111111111111111111111111111111111111111111111111111111111111",
                chain=ChainType.ETHEREUM,
            )

            assert result.status == TransactionStatus.FAILED
            assert result.error == "Transaction reverted"
            assert result.block_number == 18500001

    @pytest.mark.asyncio
    async def test_confirm_transaction_pending(self, service):
        """Test checking a transaction that is still pending."""
        with patch.object(service, "_fetch_receipt_via_rpc") as mock_fetch:
            mock_fetch.return_value = None  # Not yet mined

            result = await service.confirm_transaction(
                transaction_id=1,
                tx_hash="0x1111111111111111111111111111111111111111111111111111111111111111",
                chain=ChainType.ETHEREUM,
            )

            assert result.status == TransactionStatus.PENDING
            assert result.block_number is None
            assert result.confirmed_at is None

    @pytest.mark.asyncio
    async def test_confirm_transaction_unsupported_chain(self, service):
        """Test confirming on an unsupported chain."""
        result = await service.confirm_transaction(
            transaction_id=1,
            tx_hash="0x1111111111111111111111111111111111111111111111111111111111111111",
            chain=ChainType.HYPERLIQUID,  # No RPC endpoint
        )

        assert result.success is False
        assert result.status == TransactionStatus.PENDING
        assert "No RPC endpoint" in result.error

    @pytest.mark.asyncio
    async def test_process_pending_transactions(
        self, service, mock_transaction_repository
    ):
        """Test processing multiple pending transactions."""
        with patch.object(service, "_fetch_receipt_via_rpc") as mock_fetch:
            # First tx confirmed, second still pending
            async def mock_fetch_side_effect(rpc_url, tx_hash):
                if tx_hash.startswith("0x1111"):
                    return TransactionReceipt(
                        status=True,
                        block_number=18500000,
                        gas_used=21000,
                        effective_gas_price=50000000000,
                    )
                return None  # Still pending

            mock_fetch.side_effect = mock_fetch_side_effect

            results = await service.process_pending_transactions(limit=10)

            assert len(results) == 2
            # First one should be confirmed
            assert results[0].status == TransactionStatus.SUCCESS
            # Second one should still be pending
            assert results[1].status == TransactionStatus.PENDING

            # update_status should be called only for confirmed transaction
            mock_transaction_repository.update_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_pending_transactions_empty(
        self, mock_transaction_repository
    ):
        """Test processing when there are no pending transactions."""
        mock_transaction_repository.get_pending_transactions = AsyncMock(
            return_value=[]
        )

        service = TransactionConfirmationService(
            transaction_repository=mock_transaction_repository,
            use_testnet=True,
        )

        results = await service.process_pending_transactions()

        assert results == []
        mock_transaction_repository.update_status.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_pending_transactions_with_older_than(
        self, service, mock_transaction_repository
    ):
        """Test that older_than_seconds is passed correctly."""
        with patch.object(service, "_fetch_receipt_via_rpc") as mock_fetch:
            mock_fetch.return_value = None

            await service.process_pending_transactions(
                limit=50,
                older_than_seconds=60,
            )

            mock_transaction_repository.get_pending_transactions.assert_called_once_with(
                limit=50,
                older_than_seconds=60,
            )
