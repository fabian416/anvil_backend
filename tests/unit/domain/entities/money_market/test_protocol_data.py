"""
Tests for MoneyMarketProtocolData entity.

Tests entity creation, validation, and rich domain properties.
"""

import pytest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

from app.domain.entities.money_market.protocol_data import (
    MoneyMarketProtocolData,
)


@pytest.mark.unit
class TestMoneyMarketProtocolData:
    """Test suite for MoneyMarketProtocolData entity."""

    def test_valid_entity_creation(self):
        """Should create valid entity with correct attributes."""
        # Arrange
        now = datetime.now(timezone.utc)
        valid_until = now + timedelta(seconds=60)
        entity_id = uuid4()

        # Act
        entity = MoneyMarketProtocolData(
            id=entity_id,
            protocol_id="aave_v3",
            asset="USDC",
            chain="ethereum",
            supply_apy=Decimal("5.25"),
            borrow_apy_variable=Decimal("3.75"),
            borrow_apy_stable=Decimal("4.00"),
            total_supplied_usd=Decimal("1000000"),
            total_borrowed_usd=Decimal("750000"),
            utilization_rate=Decimal("0.75"),
            liquidity_available=Decimal("250000"),
            data_source="on_chain",
            valid_until=valid_until,
            created_at=now,
        )

        # Assert
        assert entity.id == entity_id
        assert entity.protocol_id == "aave_v3"
        assert entity.asset == "USDC"
        assert entity.chain == "ethereum"
        assert entity.supply_apy == Decimal("5.25")
        assert entity.borrow_apy_variable == Decimal("3.75")
        assert entity.borrow_apy_stable == Decimal("4.00")
        assert entity.total_supplied_usd == Decimal("1000000")
        assert entity.total_borrowed_usd == Decimal("750000")
        assert entity.utilization_rate == Decimal("0.75")
        assert entity.liquidity_available == Decimal("250000")
        assert entity.data_source == "on_chain"
        assert entity.valid_until == valid_until
        assert entity.created_at == now

    def test_validation_invalid_protocol(self):
        """Should raise error for invalid protocol."""
        # Arrange
        now = datetime.now(timezone.utc)

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid protocol_id"):
            MoneyMarketProtocolData(
                id=uuid4(),
                protocol_id="invalid_protocol",  # Invalid
                asset="USDC",
                chain="ethereum",
                supply_apy=Decimal("5.25"),
                borrow_apy_variable=Decimal("3.75"),
                borrow_apy_stable=None,
                total_supplied_usd=Decimal("1000000"),
                total_borrowed_usd=Decimal("750000"),
                utilization_rate=Decimal("0.75"),
                liquidity_available=Decimal("250000"),
                data_source="on_chain",
                valid_until=now + timedelta(seconds=60),
                created_at=now,
            )

    def test_validation_negative_apy(self):
        """Should raise error for negative APY."""
        # Arrange
        now = datetime.now(timezone.utc)

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid supply_apy"):
            MoneyMarketProtocolData(
                id=uuid4(),
                protocol_id="aave_v3",
                asset="USDC",
                chain="ethereum",
                supply_apy=Decimal("-1.0"),  # Negative
                borrow_apy_variable=Decimal("3.75"),
                borrow_apy_stable=None,
                total_supplied_usd=Decimal("1000000"),
                total_borrowed_usd=Decimal("750000"),
                utilization_rate=Decimal("0.75"),
                liquidity_available=Decimal("250000"),
                data_source="on_chain",
                valid_until=now + timedelta(seconds=60),
                created_at=now,
            )

    def test_validation_apy_too_high(self):
        """Should raise error for APY > 100%."""
        # Arrange
        now = datetime.now(timezone.utc)

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid supply_apy"):
            MoneyMarketProtocolData(
                id=uuid4(),
                protocol_id="aave_v3",
                asset="USDC",
                chain="ethereum",
                supply_apy=Decimal("150.0"),  # Too high
                borrow_apy_variable=Decimal("3.75"),
                borrow_apy_stable=None,
                total_supplied_usd=Decimal("1000000"),
                total_borrowed_usd=Decimal("750000"),
                utilization_rate=Decimal("0.75"),
                liquidity_available=Decimal("250000"),
                data_source="on_chain",
                valid_until=now + timedelta(seconds=60),
                created_at=now,
            )

    def test_validation_invalid_utilization_rate(self):
        """Should raise error for utilization rate > 1."""
        # Arrange
        now = datetime.now(timezone.utc)

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid utilization_rate"):
            MoneyMarketProtocolData(
                id=uuid4(),
                protocol_id="aave_v3",
                asset="USDC",
                chain="ethereum",
                supply_apy=Decimal("5.25"),
                borrow_apy_variable=Decimal("3.75"),
                borrow_apy_stable=None,
                total_supplied_usd=Decimal("1000000"),
                total_borrowed_usd=Decimal("750000"),
                utilization_rate=Decimal("1.5"),  # > 1
                liquidity_available=Decimal("250000"),
                data_source="on_chain",
                valid_until=now + timedelta(seconds=60),
                created_at=now,
            )

    def test_validation_invalid_data_source(self):
        """Should raise error for invalid data source."""
        # Arrange
        now = datetime.now(timezone.utc)

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid data_source"):
            MoneyMarketProtocolData(
                id=uuid4(),
                protocol_id="aave_v3",
                asset="USDC",
                chain="ethereum",
                supply_apy=Decimal("5.25"),
                borrow_apy_variable=Decimal("3.75"),
                borrow_apy_stable=None,
                total_supplied_usd=Decimal("1000000"),
                total_borrowed_usd=Decimal("750000"),
                utilization_rate=Decimal("0.75"),
                liquidity_available=Decimal("250000"),
                data_source="invalid_source",  # Invalid
                valid_until=now + timedelta(seconds=60),
                created_at=now,
            )

    def test_validation_empty_asset(self):
        """Should raise error for empty asset symbol."""
        # Arrange
        now = datetime.now(timezone.utc)

        # Act & Assert
        with pytest.raises(ValueError, match="Asset symbol cannot be empty"):
            MoneyMarketProtocolData(
                id=uuid4(),
                protocol_id="aave_v3",
                asset="",  # Empty
                chain="ethereum",
                supply_apy=Decimal("5.25"),
                borrow_apy_variable=Decimal("3.75"),
                borrow_apy_stable=None,
                total_supplied_usd=Decimal("1000000"),
                total_borrowed_usd=Decimal("750000"),
                utilization_rate=Decimal("0.75"),
                liquidity_available=Decimal("250000"),
                data_source="on_chain",
                valid_until=now + timedelta(seconds=60),
                created_at=now,
            )

    def test_cache_is_valid_when_not_expired(self):
        """Should return True when cache has not expired."""
        # Arrange
        now = datetime.now(timezone.utc)
        valid_until = now + timedelta(seconds=30)  # Valid for 30 more seconds

        entity = MoneyMarketProtocolData(
            id=uuid4(),
            protocol_id="aave_v3",
            asset="USDC",
            chain="ethereum",
            supply_apy=Decimal("5.25"),
            borrow_apy_variable=Decimal("3.75"),
            borrow_apy_stable=None,
            total_supplied_usd=Decimal("1000000"),
            total_borrowed_usd=Decimal("750000"),
            utilization_rate=Decimal("0.75"),
            liquidity_available=Decimal("250000"),
            data_source="on_chain",
            valid_until=valid_until,
            created_at=now,
        )

        # Act & Assert
        assert entity.is_valid
        assert not entity.is_expired

    def test_cache_is_expired_when_past_ttl(self):
        """Should return True when cache has expired."""
        # Arrange
        now = datetime.now(timezone.utc)
        past = now - timedelta(seconds=10)  # Expired 10s ago

        entity = MoneyMarketProtocolData(
            id=uuid4(),
            protocol_id="aave_v3",
            asset="USDC",
            chain="ethereum",
            supply_apy=Decimal("5.25"),
            borrow_apy_variable=Decimal("3.75"),
            borrow_apy_stable=None,
            total_supplied_usd=Decimal("1000000"),
            total_borrowed_usd=Decimal("750000"),
            utilization_rate=Decimal("0.75"),
            liquidity_available=Decimal("250000"),
            data_source="on_chain",
            valid_until=past,  # Already expired
            created_at=now - timedelta(seconds=70),
        )

        # Act & Assert
        assert entity.is_expired
        assert not entity.is_valid

    def test_time_until_expiry_calculation(self):
        """Should calculate remaining time until expiry."""
        # Arrange
        now = datetime.now(timezone.utc)
        valid_until = now + timedelta(seconds=45)

        entity = MoneyMarketProtocolData(
            id=uuid4(),
            protocol_id="aave_v3",
            asset="USDC",
            chain="ethereum",
            supply_apy=Decimal("5.25"),
            borrow_apy_variable=Decimal("3.75"),
            borrow_apy_stable=None,
            total_supplied_usd=Decimal("1000000"),
            total_borrowed_usd=Decimal("750000"),
            utilization_rate=Decimal("0.75"),
            liquidity_available=Decimal("250000"),
            data_source="on_chain",
            valid_until=valid_until,
            created_at=now,
        )

        # Act
        time_until = entity.time_until_expiry
        seconds_until = entity.seconds_until_expiry

        # Assert
        assert 40 <= time_until.total_seconds() <= 45  # Allow small timing difference
        assert 40 <= seconds_until <= 45

    def test_is_real_data_property(self):
        """Should identify real on-chain data."""
        # Arrange
        now = datetime.now(timezone.utc)

        entity = MoneyMarketProtocolData(
            id=uuid4(),
            protocol_id="aave_v3",
            asset="USDC",
            chain="ethereum",
            supply_apy=Decimal("5.25"),
            borrow_apy_variable=Decimal("3.75"),
            borrow_apy_stable=None,
            total_supplied_usd=Decimal("1000000"),
            total_borrowed_usd=Decimal("750000"),
            utilization_rate=Decimal("0.75"),
            liquidity_available=Decimal("250000"),
            data_source="on_chain",  # Real data
            valid_until=now + timedelta(seconds=60),
            created_at=now,
        )

        # Act & Assert
        assert entity.is_real_data
        assert not entity.is_estimated

    def test_is_estimated_property(self):
        """Should identify estimated data."""
        # Arrange
        now = datetime.now(timezone.utc)

        entity = MoneyMarketProtocolData(
            id=uuid4(),
            protocol_id="aave_v3",
            asset="USDC",
            chain="ethereum",
            supply_apy=Decimal("5.25"),
            borrow_apy_variable=Decimal("3.75"),
            borrow_apy_stable=None,
            total_supplied_usd=Decimal("1000000"),
            total_borrowed_usd=Decimal("750000"),
            utilization_rate=Decimal("0.75"),
            liquidity_available=Decimal("250000"),
            data_source="estimated",  # Estimated
            valid_until=now + timedelta(seconds=60),
            created_at=now,
        )

        # Act & Assert
        assert entity.is_estimated
        assert not entity.is_real_data

    def test_protocol_identification_properties(self):
        """Should identify protocol type."""
        # Arrange
        now = datetime.now(timezone.utc)

        aave_entity = MoneyMarketProtocolData(
            id=uuid4(),
            protocol_id="aave_v3",
            asset="USDC",
            chain="ethereum",
            supply_apy=Decimal("5.25"),
            borrow_apy_variable=Decimal("3.75"),
            borrow_apy_stable=Decimal("4.00"),
            total_supplied_usd=Decimal("1000000"),
            total_borrowed_usd=Decimal("750000"),
            utilization_rate=Decimal("0.75"),
            liquidity_available=Decimal("250000"),
            data_source="on_chain",
            valid_until=now + timedelta(seconds=60),
            created_at=now,
        )

        compound_entity = MoneyMarketProtocolData(
            id=uuid4(),
            protocol_id="compound_v3",
            asset="USDC",
            chain="ethereum",
            supply_apy=Decimal("5.25"),
            borrow_apy_variable=Decimal("3.75"),
            borrow_apy_stable=None,
            total_supplied_usd=Decimal("1000000"),
            total_borrowed_usd=Decimal("750000"),
            utilization_rate=Decimal("0.75"),
            liquidity_available=Decimal("250000"),
            data_source="on_chain",
            valid_until=now + timedelta(seconds=60),
            created_at=now,
        )

        # Act & Assert
        assert aave_entity.is_aave
        assert not aave_entity.is_compound
        assert aave_entity.has_stable_borrow

        assert compound_entity.is_compound
        assert not compound_entity.is_aave
        assert not compound_entity.has_stable_borrow

    def test_utilization_percentage_property(self):
        """Should convert utilization rate to percentage."""
        # Arrange
        now = datetime.now(timezone.utc)

        entity = MoneyMarketProtocolData(
            id=uuid4(),
            protocol_id="aave_v3",
            asset="USDC",
            chain="ethereum",
            supply_apy=Decimal("5.25"),
            borrow_apy_variable=Decimal("3.75"),
            borrow_apy_stable=None,
            total_supplied_usd=Decimal("1000000"),
            total_borrowed_usd=Decimal("750000"),
            utilization_rate=Decimal("0.85"),  # 85%
            liquidity_available=Decimal("150000"),
            data_source="on_chain",
            valid_until=now + timedelta(seconds=60),
            created_at=now,
        )

        # Act & Assert
        assert entity.utilization_percentage == Decimal("85")
        assert entity.is_high_utilization  # > 80%

    def test_liquidity_risk_detection(self):
        """Should detect low liquidity."""
        # Arrange
        now = datetime.now(timezone.utc)

        low_liquidity_entity = MoneyMarketProtocolData(
            id=uuid4(),
            protocol_id="aave_v3",
            asset="USDC",
            chain="ethereum",
            supply_apy=Decimal("5.25"),
            borrow_apy_variable=Decimal("3.75"),
            borrow_apy_stable=None,
            total_supplied_usd=Decimal("1000000"),
            total_borrowed_usd=Decimal("950000"),
            utilization_rate=Decimal("0.95"),
            liquidity_available=Decimal("500000"),  # < $1M
            data_source="on_chain",
            valid_until=now + timedelta(seconds=60),
            created_at=now,
        )

        high_liquidity_entity = MoneyMarketProtocolData(
            id=uuid4(),
            protocol_id="aave_v3",
            asset="USDC",
            chain="ethereum",
            supply_apy=Decimal("5.25"),
            borrow_apy_variable=Decimal("3.75"),
            borrow_apy_stable=None,
            total_supplied_usd=Decimal("10000000"),
            total_borrowed_usd=Decimal("7500000"),
            utilization_rate=Decimal("0.75"),
            liquidity_available=Decimal("2500000"),  # > $1M
            data_source="on_chain",
            valid_until=now + timedelta(seconds=60),
            created_at=now,
        )

        # Act & Assert
        assert low_liquidity_entity.is_low_liquidity
        assert not high_liquidity_entity.is_low_liquidity
