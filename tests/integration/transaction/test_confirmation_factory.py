"""
Tests for Transaction Confirmation Factory and CLI Worker.

Tests the factory functions that create TransactionConfirmationService
instances and the CLI worker components.
"""

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.application.transactions.services.confirmation_service import (
    TransactionConfirmationService,
    TransactionReceipt,
)
from app.application.transactions.services.factory import (
    ConfirmationServiceFactory,
    create_confirmation_service,
    create_confirmation_service_from_settings,
)
from app.domain.enums.transaction_status import TransactionStatus
from app.setup.config.transaction_confirmation import TransactionConfirmationSettings


class TestCreateConfirmationService:
    """Tests for create_confirmation_service factory function."""

    def test_creates_service_with_defaults(self):
        """Test creating service with default settings."""
        mock_session = MagicMock()

        service = create_confirmation_service(mock_session)

        assert isinstance(service, TransactionConfirmationService)
        assert service._use_testnet is True  # Default
        assert service._http_timeout == 30  # Default

    def test_creates_service_with_testnet_false(self):
        """Test creating service for mainnet."""
        mock_session = MagicMock()

        service = create_confirmation_service(
            mock_session,
            use_testnet=False,
            http_timeout=60,
        )

        assert service._use_testnet is False
        assert service._http_timeout == 60

    def test_creates_service_with_testnet_true(self):
        """Test creating service for testnet."""
        mock_session = MagicMock()

        service = create_confirmation_service(
            mock_session,
            use_testnet=True,
        )

        assert service._use_testnet is True


class TestCreateConfirmationServiceFromSettings:
    """Tests for create_confirmation_service_from_settings factory function."""

    def test_creates_service_from_settings(self):
        """Test creating service from TransactionConfirmationSettings."""
        mock_session = MagicMock()
        settings = TransactionConfirmationSettings(
            use_testnet=False,
            http_timeout=45,
            interval_seconds=60,
            batch_limit=100,
        )

        service = create_confirmation_service_from_settings(mock_session, settings)

        assert isinstance(service, TransactionConfirmationService)
        assert service._use_testnet is False
        assert service._http_timeout == 45

    def test_uses_default_settings(self):
        """Test creating service with default TransactionConfirmationSettings."""
        mock_session = MagicMock()
        settings = TransactionConfirmationSettings()  # All defaults

        service = create_confirmation_service_from_settings(mock_session, settings)

        assert service._use_testnet is True  # Default is testnet
        assert service._http_timeout == 30  # Default timeout


class TestTransactionConfirmationSettings:
    """Tests for TransactionConfirmationSettings configuration."""

    def test_default_settings(self):
        """Test default configuration values."""
        settings = TransactionConfirmationSettings()

        assert settings.use_testnet is True
        assert settings.interval_seconds == 30
        assert settings.batch_limit == 50
        assert settings.older_than_seconds == 10
        assert settings.http_timeout == 30
        assert settings.enabled is True

    def test_custom_settings(self):
        """Test custom configuration values."""
        settings = TransactionConfirmationSettings(
            use_testnet=False,
            interval_seconds=60,
            batch_limit=100,
            older_than_seconds=30,
            http_timeout=45,
            enabled=False,
        )

        assert settings.use_testnet is False
        assert settings.interval_seconds == 60
        assert settings.batch_limit == 100
        assert settings.older_than_seconds == 30
        assert settings.http_timeout == 45
        assert settings.enabled is False

    def test_settings_from_alias(self):
        """Test settings can be loaded using aliases (for TOML compatibility)."""
        settings = TransactionConfirmationSettings(
            USE_TESTNET=False,
            INTERVAL_SECONDS=45,
            BATCH_LIMIT=25,
        )

        assert settings.use_testnet is False
        assert settings.interval_seconds == 45
        assert settings.batch_limit == 25


class TestConfirmationServiceFactory:
    """Tests for ConfirmationServiceFactory class."""

    @pytest.fixture
    def mock_session_factory(self):
        """Create a mock session factory."""
        mock_session = AsyncMock()
        mock_factory = MagicMock()
        mock_factory.return_value = mock_session
        mock_factory.__aenter__ = AsyncMock(return_value=mock_session)
        mock_factory.__aexit__ = AsyncMock(return_value=None)
        return mock_factory

    @pytest.fixture
    def default_settings(self):
        """Create default settings for tests."""
        return TransactionConfirmationSettings()

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_create_service(self, mock_session_factory, default_settings):
        """Test creating a service from the factory."""
        factory = ConfirmationServiceFactory(mock_session_factory, default_settings)

        service = await factory.create_service()

        assert isinstance(service, TransactionConfirmationService)

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_create_service",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))


    def test_factory_settings_property(self, mock_session_factory, default_settings):
        """Test that factory exposes settings."""
        factory = ConfirmationServiceFactory(mock_session_factory, default_settings)

        assert factory.settings == default_settings
        assert factory.settings.use_testnet is True


class TestCLIWorkerComponents:
    """Tests for CLI worker helper functions and components."""

    def test_worker_result_dataclass(self):
        """Test WorkerResult dataclass."""
        from app.cli.confirm_pending_transactions import WorkerResult

        now = datetime.now(UTC)
        result = WorkerResult(
            transactions_processed=10,
            confirmed=5,
            failed=2,
            still_pending=3,
            duration_seconds=1.5,
            started_at=now,
            finished_at=now,
        )

        assert result.transactions_processed == 10
        assert result.confirmed == 5
        assert result.failed == 2
        assert result.still_pending == 3
        assert result.duration_seconds == 1.5

    def test_parse_args_once_mode(self):
        """Test CLI argument parsing for --once mode."""
        import sys

        from app.cli.confirm_pending_transactions import parse_args

        with patch.object(sys, "argv", ["worker", "--once"]):
            args = parse_args()

            assert args.once is True
            assert args.loop is False

    def test_parse_args_loop_mode(self):
        """Test CLI argument parsing for --loop mode."""
        import sys

        from app.cli.confirm_pending_transactions import parse_args

        with patch.object(sys, "argv", ["worker", "--loop"]):
            args = parse_args()

            assert args.once is False
            assert args.loop is True

    def test_parse_args_with_options(self):
        """Test CLI argument parsing with all options."""
        import sys

        from app.cli.confirm_pending_transactions import parse_args

        with patch.object(
            sys,
            "argv",
            [
                "worker",
                "--once",
                "--mainnet",
                "--limit",
                "100",
                "--older-than",
                "30",
                "--log-level",
                "DEBUG",
            ],
        ):
            args = parse_args()

            assert args.once is True
            assert args.mainnet is True
            assert args.testnet is False
            assert args.limit == 100
            assert args.older_than == 30
            assert args.log_level == "DEBUG"

    def test_parse_args_testnet_flag(self):
        """Test CLI argument parsing with --testnet flag."""
        import sys

        from app.cli.confirm_pending_transactions import parse_args

        with patch.object(sys, "argv", ["worker", "--loop", "--testnet"]):
            args = parse_args()

            assert args.testnet is True
            assert args.mainnet is False


class TestIntegrationWithConfirmationService:
    """Integration tests with the actual TransactionConfirmationService."""

    @pytest.fixture
    def mock_transaction_repository(self):
        """Create a mock TransactionRepository."""
        from app.domain.transactions.entities.transaction import Transaction, TransactionId
        from app.domain.entities.wallet import WalletId
        from app.domain.enums.chain_type import ChainType
        from app.domain.enums.transaction_type import TransactionType
        from app.domain.transactions.ports.transaction.transaction_repository import (
            TransactionRepository,
        )
        from app.domain.value_objects.created_at import CreatedAt
        from app.domain.value_objects.user_id import UserId

        now = datetime.now(UTC)
        mock_transactions = [
            Transaction(
                id_=TransactionId(1),
                user_id=UserId(123),
                wallet_id=WalletId(1),
                to_address="0x" + "b" * 40,
                type=TransactionType.SEND,
                chain=ChainType.BASE,
                asset_in="ETH",
                amount_in=Decimal("1000000000000000000"),
                asset_out=None,
                amount_out=None,
                fee=None,
                fee_usd=None,
                tx_hash="0x" + "a" * 64,
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
        ]

        repo = MagicMock(spec=TransactionRepository)
        repo.get_pending_transactions = AsyncMock(return_value=mock_transactions)
        repo.update_status = AsyncMock(return_value=True)
        return repo

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_factory_creates_working_service(self, mock_transaction_repository):
        """Test that factory creates a service that can process transactions."""
        settings = TransactionConfirmationSettings(use_testnet=True)

        service = TransactionConfirmationService(
            transaction_repository=mock_transaction_repository,
            use_testnet=settings.use_testnet,
            http_timeout=settings.http_timeout,
        )

        # Mock the RPC call to return a successful receipt
        with patch.object(service, "_fetch_receipt_via_rpc") as mock_fetch:
            mock_fetch.return_value = TransactionReceipt(
                status=True,
                block_number=12345678,
                gas_used=21000,
                effective_gas_price=50000000000,
            )

            results = await service.process_pending_transactions(limit=10)

            assert len(results) == 1
            assert results[0].status == TransactionStatus.SUCCESS
            assert results[0].block_number == 12345678

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_factory_creates_working_service",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

            mock_transaction_repository.update_status.assert_called_once()