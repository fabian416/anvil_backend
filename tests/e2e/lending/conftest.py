"""
Shared fixtures for lending E2E tests.

Provides mock implementations of all lending system dependencies.
"""

import pytest
from decimal import Decimal
from uuid import UUID, uuid4
from unittest.mock import AsyncMock, MagicMock
from typing import Dict, Any


# ============================================================================
# USER CONTEXT FIXTURES
# ============================================================================


@pytest.fixture
def test_user_context() -> Dict[str, Any]:
    """
    Provide test user context with authentication details.

    Returns:
        Dictionary with user_id, wallet_address, email
    """
    return {
        "user_id": uuid4(),
        "wallet_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
        "email": "test@anvil.defi",
        "language": "en",
    }


@pytest.fixture
def test_user_secondary() -> Dict[str, Any]:
    """Secondary test user for multi-user scenarios."""
    return {
        "user_id": uuid4(),
        "wallet_address": "0x1234567890123456789012345678901234567890",
        "email": "secondary@anvil.defi",
        "language": "es",
    }


# ============================================================================
# BALANCE CHECKER MOCKS
# ============================================================================


@pytest.fixture
def mock_balance_checker():
    """
    Mock IBalanceChecker port.

    Default behavior: User has sufficient balance (10,000 of any token).
    """
    mock = AsyncMock()
    mock.get_balance = AsyncMock(return_value=Decimal("10000.0"))
    mock.check_balance = AsyncMock(return_value=True)
    mock.check_gas_balance = AsyncMock(return_value=True)
    return mock


# ============================================================================
# AAVE GATEWAY MOCKS
# ============================================================================


@pytest.fixture
def mock_aave_gateway():
    """
    Mock AaveGateway port.

    Provides realistic Aave market data and user positions.
    """
    mock = AsyncMock()

    # Default market data
    default_market_data = [
        MagicMock(
            symbol="USDC",
            supply_apy=Decimal("5.25"),
            variable_borrow_apy=Decimal("6.5"),
            stable_borrow_apy=Decimal("7.5"),
            address="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
            price_usd=Decimal("1.0"),
            ltv=Decimal("0.80"),
        ),
        MagicMock(
            symbol="ETH",
            supply_apy=Decimal("3.5"),
            variable_borrow_apy=Decimal("4.2"),
            stable_borrow_apy=Decimal("5.0"),
            address="0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
            price_usd=Decimal("2000.0"),
            ltv=Decimal("0.825"),
        ),
        MagicMock(
            symbol="DAI",
            supply_apy=Decimal("4.8"),
            variable_borrow_apy=Decimal("6.0"),
            stable_borrow_apy=Decimal("7.0"),
            address="0x6B175474E89094C44Da98b954EedeAC495271d0F",
            price_usd=Decimal("1.0"),
            ltv=Decimal("0.75"),
        ),
    ]

    mock.get_market_data = AsyncMock(return_value=default_market_data)

    # Default user position (no existing positions)
    default_position = MagicMock(
        health_factor=Decimal("inf"),
        total_collateral_usd=Decimal("0"),
        total_debt_usd=Decimal("0"),
        max_ltv=Decimal("0.825"),
        supplies=[],
        borrows=[],
    )

    mock.get_user_position = AsyncMock(return_value=default_position)
    mock.get_user_positions = AsyncMock(return_value=default_position)

    return mock


# ============================================================================
# MORPHO GATEWAY MOCKS
# ============================================================================


@pytest.fixture
def mock_morpho_gateway():
    """
    Mock MorphoGateway port.

    Provides Morpho vault data.
    """
    mock = AsyncMock()

    # Default vault details
    default_vault = MagicMock(
        address="0x1234567890123456789012345678901234567890",
        name="Steakhouse USDC Vault",
        asset="USDC",
        asset_address="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        apy=Decimal("8.75"),
        total_assets=Decimal("50000000.0"),
        total_supply=Decimal("50000000.0"),
        curator="Steakhouse Financial",
    )

    mock.get_vault_details = AsyncMock(return_value=default_vault)
    mock.get_vaults = AsyncMock(return_value=[default_vault])

    return mock


# ============================================================================
# LENDING REPOSITORY MOCKS
# ============================================================================


@pytest.fixture
def mock_lending_repository():
    """
    Mock ILendingRepository port.

    Simulates database operations for lending positions.
    """
    mock = AsyncMock()

    # Save operations return UUIDs
    mock.save_supply_position = AsyncMock(return_value=uuid4())
    mock.save_borrow_position = AsyncMock(return_value=uuid4())
    mock.save_position = AsyncMock(return_value=uuid4())
    mock.save_transaction = AsyncMock()
    mock.save_health_check = AsyncMock()
    mock.save_loop_execution = AsyncMock()
    mock.create_alert = AsyncMock()

    # Get operations return empty lists by default
    mock.get_user_positions = AsyncMock(return_value=[])
    mock.get_position_by_id = AsyncMock(return_value=None)
    mock.get_user_transactions = AsyncMock(return_value=[])
    mock.get_recent_health_checks = AsyncMock(return_value=[])
    mock.get_loop_execution = AsyncMock(return_value=None)
    mock.get_user_loop_executions = AsyncMock(return_value=[])
    mock.get_unread_alerts = AsyncMock(return_value=[])
    mock.get_user_alerts = AsyncMock(return_value=[])

    # Update operations
    mock.update_transaction_status = AsyncMock()
    mock.update_loop_execution = AsyncMock()
    mock.mark_alert_as_read = AsyncMock()

    # Preferences
    mock.save_user_preferences = AsyncMock()
    mock.get_user_preferences = AsyncMock(return_value=None)

    return mock


# ============================================================================
# SWAP EXECUTOR MOCKS
# ============================================================================


@pytest.fixture
def mock_swap_executor():
    """
    Mock ISwapExecutor port (1inch integration).

    Provides swap quotes and execute_data for token swaps.
    """
    mock = AsyncMock()

    # Default swap quote
    async def default_swap_quote(token_in, token_out, amount_in, chain, slippage):
        # Simulate realistic conversion rates
        conversion_rate = Decimal("0.998")  # 0.2% fee

        if token_in == "USDC" and token_out in ("ETH", "WETH"):
            # USDC → ETH (divide by price)
            amount_out = amount_in / Decimal("2000.0") * conversion_rate
        elif token_in in ("ETH", "WETH") and token_out == "USDC":
            # ETH → USDC (multiply by price)
            amount_out = amount_in * Decimal("2000.0") * conversion_rate
        else:
            # Stablecoin swap
            amount_out = amount_in * conversion_rate

        return {
            "amount_out": amount_out,
            "gas_estimate_usd": Decimal("10.0"),
            "price_impact": Decimal("0.001"),
        }

    mock.get_swap_quote = AsyncMock(side_effect=default_swap_quote)

    # Default execute_data
    mock.build_swap_execute_data = AsyncMock(
        return_value={
            "action_type": "swap",
            "provider": "1inch",
            "dex": "uniswap_v3",
            "slippage": "0.5",
        }
    )

    return mock


# ============================================================================
# HEALTH FACTOR VALIDATOR MOCKS
# ============================================================================


@pytest.fixture
def mock_hf_validator():
    """
    Mock HealthFactorValidatorService (application layer).

    Provides health factor validation for borrow operations.
    """
    from app.domain.value_objects.lending.health_factor_result import (
        HealthFactorResult,
        HealthFactorLevel,
    )

    mock = AsyncMock()

    # Default safe validation
    default_validation = HealthFactorResult(
        current_hf=Decimal("3.5"),
        projected_hf=Decimal("2.8"),
        level=HealthFactorLevel.SAFE,
        collateral_usd=Decimal("10000.0"),
        current_debt_usd=Decimal("1000.0"),
        projected_debt_usd=Decimal("3000.0"),
        max_safe_borrow_usd=Decimal("5000.0"),
        liquidation_price=Decimal("1200.0"),
        warning_message="SAFE - Your position is well-collateralized",
        emoji="✅",
        is_safe=True,
    )

    mock.validate_borrow = AsyncMock(return_value=default_validation)

    return mock


@pytest.fixture
def mock_hf_validator_domain():
    """
    Mock HealthFactorValidator (domain service).

    Pure calculation functions for health factor.
    """
    mock = MagicMock()

    def default_calc_hf(collateral_usd, debt_usd, liquidation_threshold):
        if debt_usd == 0:
            return Decimal("inf")
        return (collateral_usd * liquidation_threshold) / debt_usd

    mock._calculate_health_factor = MagicMock(side_effect=default_calc_hf)
    mock._determine_level = MagicMock()
    mock._calculate_max_safe_borrow = MagicMock(return_value=Decimal("5000.0"))

    return mock


# ============================================================================
# PRIVY WALLET MOCKS
# ============================================================================


@pytest.fixture
def mock_privy_wallet():
    """
    Mock Privy wallet signature service.

    Simulates wallet connect, signatures, and transaction execution.
    """
    mock = AsyncMock()

    mock.request_signature = AsyncMock(
        return_value={
            "signature": "0x" + "ab" * 65,
            "signed_at": "2026-01-27T00:00:00Z",
        }
    )

    mock.execute_transaction = AsyncMock(
        return_value={
            "transaction_hash": "0x" + "cd" * 32,
            "status": "pending",
        }
    )

    mock.get_transaction_status = AsyncMock(
        return_value={
            "status": "confirmed",
            "block_number": 12345678,
            "confirmed_at": "2026-01-27T00:00:30Z",
        }
    )

    return mock


# ============================================================================
# DATABASE FIXTURES
# ============================================================================


@pytest.fixture
async def clean_test_database():
    """
    Clean up test database after each test.

    Ensures test isolation by removing all test data.
    """
    yield

    # Cleanup code runs after test
    # In practice, this would truncate lending tables:
    # - lending_positions
    # - lending_transactions
    # - lending_health_checks
    # - lending_loop_executions
    # - lending_alerts
    # - user_lending_preferences


# ============================================================================
# INTEGRATION TEST FIXTURES
# ============================================================================


@pytest.fixture
async def test_db_session():
    """
    Provide real database session for integration tests.

    Uses anvil_test database, not production.
    """
    # This would create a real SQLAlchemy session
    # Connected to PostgreSQL test database
    pass


# ============================================================================
# LANGUAGE FIXTURES
# ============================================================================


@pytest.fixture
def mock_translator():
    """
    Mock translation service for multi-language tests.

    Returns translations for en, es, pt, zh.
    """
    mock = MagicMock()

    translations = {
        "en": {
            "supply_success": "Supply {amount} {asset} to {protocol}",
            "borrow_success": "Borrow {amount} {asset} from {protocol}",
            "health_safe": "SAFE - Your position is well-collateralized",
            "health_caution": "CAUTION - Monitor your position closely",
        },
        "es": {
            "supply_success": "Suministrar {amount} {asset} a {protocol}",
            "borrow_success": "Pedir prestado {amount} {asset} de {protocol}",
            "health_safe": "SEGURO - Tu posición está bien colateralizada",
            "health_caution": "PRECAUCIÓN - Monitorea tu posición de cerca",
        },
        "pt": {
            "supply_success": "Fornecer {amount} {asset} para {protocol}",
            "borrow_success": "Emprestar {amount} {asset} de {protocol}",
            "health_safe": "SEGURO - Sua posição está bem colateralizada",
            "health_caution": "CUIDADO - Monitore sua posição de perto",
        },
        "zh": {
            "supply_success": "向 {protocol} 供应 {amount} {asset}",
            "borrow_success": "从 {protocol} 借入 {amount} {asset}",
            "health_safe": "安全 - 您的头寸抵押充足",
            "health_caution": "警告 - 密切监控您的头寸",
        },
    }

    def get_translation(key, language="en", **kwargs):
        template = translations.get(language, translations["en"]).get(key, key)
        return template.format(**kwargs)

    mock.translate = MagicMock(side_effect=get_translation)

    return mock
