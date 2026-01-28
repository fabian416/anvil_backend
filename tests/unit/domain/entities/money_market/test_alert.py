"""
Tests for MoneyMarketAlert entity.

Tests entity creation, APY change validation, and rich domain properties.
"""

import pytest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

from app.domain.entities.money_market.alert import MoneyMarketAlert


@pytest.mark.unit
class TestMoneyMarketAlert:
    """Test suite for MoneyMarketAlert entity."""

    def test_valid_entity_creation(self):
        """Should create valid entity with correct attributes."""
        # Arrange
        now = datetime.now(timezone.utc)
        entity_id = uuid4()
        user_id = uuid4()
        alert_id = uuid4()

        # Act
        entity = MoneyMarketAlert(
            id=entity_id,
            alert_id=alert_id,
            user_id=user_id,
            protocol_id="aave_v3",
            asset="USDC",
            chain="ethereum",
            alert_type="SUPPLY_RATE_INCREASE",
            old_apy=Decimal("5.00"),
            new_apy=Decimal("6.00"),
            apy_change_percent=Decimal("1.00"),
            threshold_percent=Decimal("0.50"),
            notification_sent=False,
            notification_sent_at=None,
            created_at=now,
        )

        # Assert
        assert entity.id == entity_id
        assert entity.alert_id == alert_id
        assert entity.user_id == user_id
        assert entity.protocol_id == "aave_v3"
        assert entity.asset == "USDC"
        assert entity.chain == "ethereum"
        assert entity.alert_type == "SUPPLY_RATE_INCREASE"
        assert entity.old_apy == Decimal("5.00")
        assert entity.new_apy == Decimal("6.00")
        assert entity.apy_change_percent == Decimal("1.00")
        assert entity.threshold_percent == Decimal("0.50")
        assert entity.notification_sent is False
        assert entity.notification_sent_at is None
        assert entity.created_at == now

    def test_valid_entity_with_notification_sent(self):
        """Should create valid entity with notification sent."""
        # Arrange
        now = datetime.now(timezone.utc)
        sent_at = now - timedelta(minutes=5)

        # Act
        entity = MoneyMarketAlert(
            id=uuid4(),
            alert_id=uuid4(),
            user_id=uuid4(),
            protocol_id="compound_v3",
            asset="USDT",
            chain="polygon",
            alert_type="BORROW_RATE_DECREASE",
            old_apy=Decimal("4.50"),
            new_apy=Decimal("3.50"),
            apy_change_percent=Decimal("1.00"),
            threshold_percent=Decimal("0.75"),
            notification_sent=True,
            notification_sent_at=sent_at,
            created_at=now - timedelta(minutes=5),
        )

        # Assert
        assert entity.notification_sent is True
        assert entity.notification_sent_at == sent_at

    def test_validation_invalid_protocol(self):
        """Should raise error for invalid protocol."""
        # Arrange
        now = datetime.now(timezone.utc)

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid protocol_id"):
            MoneyMarketAlert(
                id=uuid4(),
                alert_id=uuid4(),
                user_id=uuid4(),
                protocol_id="invalid_protocol",  # Invalid
                asset="USDC",
                chain="ethereum",
                alert_type="SUPPLY_RATE_INCREASE",
                old_apy=Decimal("5.00"),
                new_apy=Decimal("6.00"),
                apy_change_percent=Decimal("1.00"),
                threshold_percent=Decimal("0.50"),
                notification_sent=False,
                notification_sent_at=None,
                created_at=now,
            )

    def test_validation_invalid_alert_type(self):
        """Should raise error for invalid alert type."""
        # Arrange
        now = datetime.now(timezone.utc)

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid alert_type"):
            MoneyMarketAlert(
                id=uuid4(),
                alert_id=uuid4(),
                user_id=uuid4(),
                protocol_id="aave_v3",
                asset="USDC",
                chain="ethereum",
                alert_type="INVALID_TYPE",  # Invalid
                old_apy=Decimal("5.00"),
                new_apy=Decimal("6.00"),
                apy_change_percent=Decimal("1.00"),
                threshold_percent=Decimal("0.50"),
                notification_sent=False,
                notification_sent_at=None,
                created_at=now,
            )

    def test_validation_negative_old_apy(self):
        """Should raise error for negative old APY."""
        # Arrange
        now = datetime.now(timezone.utc)

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid old_apy"):
            MoneyMarketAlert(
                id=uuid4(),
                alert_id=uuid4(),
                user_id=uuid4(),
                protocol_id="aave_v3",
                asset="USDC",
                chain="ethereum",
                alert_type="SUPPLY_RATE_INCREASE",
                old_apy=Decimal("-1.00"),  # Negative
                new_apy=Decimal("6.00"),
                apy_change_percent=Decimal("7.00"),
                threshold_percent=Decimal("0.50"),
                notification_sent=False,
                notification_sent_at=None,
                created_at=now,
            )

    def test_validation_negative_new_apy(self):
        """Should raise error for negative new APY."""
        # Arrange
        now = datetime.now(timezone.utc)

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid new_apy"):
            MoneyMarketAlert(
                id=uuid4(),
                alert_id=uuid4(),
                user_id=uuid4(),
                protocol_id="aave_v3",
                asset="USDC",
                chain="ethereum",
                alert_type="SUPPLY_RATE_INCREASE",
                old_apy=Decimal("5.00"),
                new_apy=Decimal("-1.00"),  # Negative
                apy_change_percent=Decimal("6.00"),
                threshold_percent=Decimal("0.50"),
                notification_sent=False,
                notification_sent_at=None,
                created_at=now,
            )

    def test_validation_apy_change_mismatch(self):
        """Should raise error when APY change doesn't match calculation."""
        # Arrange
        now = datetime.now(timezone.utc)

        # Act & Assert (old=5%, new=6%, actual change=1%, but provided=2%)
        with pytest.raises(ValueError, match="apy_change_percent .* does not match"):
            MoneyMarketAlert(
                id=uuid4(),
                alert_id=uuid4(),
                user_id=uuid4(),
                protocol_id="aave_v3",
                asset="USDC",
                chain="ethereum",
                alert_type="SUPPLY_RATE_INCREASE",
                old_apy=Decimal("5.00"),
                new_apy=Decimal("6.00"),
                apy_change_percent=Decimal("2.00"),  # Incorrect (should be 1.00)
                threshold_percent=Decimal("0.50"),
                notification_sent=False,
                notification_sent_at=None,
                created_at=now,
            )

    def test_validation_threshold_too_low(self):
        """Should raise error for threshold < 0.01%."""
        # Arrange
        now = datetime.now(timezone.utc)

        # Act & Assert
        with pytest.raises(ValueError, match="threshold_percent must be between 0.01% and 10%"):
            MoneyMarketAlert(
                id=uuid4(),
                alert_id=uuid4(),
                user_id=uuid4(),
                protocol_id="aave_v3",
                asset="USDC",
                chain="ethereum",
                alert_type="SUPPLY_RATE_INCREASE",
                old_apy=Decimal("5.00"),
                new_apy=Decimal("6.00"),
                apy_change_percent=Decimal("1.00"),
                threshold_percent=Decimal("0.005"),  # Too low
                notification_sent=False,
                notification_sent_at=None,
                created_at=now,
            )

    def test_validation_threshold_too_high(self):
        """Should raise error for threshold > 10%."""
        # Arrange
        now = datetime.now(timezone.utc)

        # Act & Assert
        with pytest.raises(ValueError, match="threshold_percent must be between 0.01% and 10%"):
            MoneyMarketAlert(
                id=uuid4(),
                alert_id=uuid4(),
                user_id=uuid4(),
                protocol_id="aave_v3",
                asset="USDC",
                chain="ethereum",
                alert_type="SUPPLY_RATE_INCREASE",
                old_apy=Decimal("5.00"),
                new_apy=Decimal("6.00"),
                apy_change_percent=Decimal("1.00"),
                threshold_percent=Decimal("15.00"),  # Too high
                notification_sent=False,
                notification_sent_at=None,
                created_at=now,
            )

    def test_validation_empty_asset(self):
        """Should raise error for empty asset symbol."""
        # Arrange
        now = datetime.now(timezone.utc)

        # Act & Assert
        with pytest.raises(ValueError, match="Asset symbol cannot be empty"):
            MoneyMarketAlert(
                id=uuid4(),
                alert_id=uuid4(),
                user_id=uuid4(),
                protocol_id="aave_v3",
                asset="",  # Empty
                chain="ethereum",
                alert_type="SUPPLY_RATE_INCREASE",
                old_apy=Decimal("5.00"),
                new_apy=Decimal("6.00"),
                apy_change_percent=Decimal("1.00"),
                threshold_percent=Decimal("0.50"),
                notification_sent=False,
                notification_sent_at=None,
                created_at=now,
            )

    def test_is_rate_increase_property(self):
        """Should identify rate increase alerts."""
        # Arrange
        now = datetime.now(timezone.utc)

        increase_entity = MoneyMarketAlert(
            id=uuid4(),
            alert_id=uuid4(),
            user_id=uuid4(),
            protocol_id="aave_v3",
            asset="USDC",
            chain="ethereum",
            alert_type="SUPPLY_RATE_INCREASE",
            old_apy=Decimal("5.00"),
            new_apy=Decimal("6.00"),
            apy_change_percent=Decimal("1.00"),
            threshold_percent=Decimal("0.50"),
            notification_sent=False,
            notification_sent_at=None,
            created_at=now,
        )

        decrease_entity = MoneyMarketAlert(
            id=uuid4(),
            alert_id=uuid4(),
            user_id=uuid4(),
            protocol_id="aave_v3",
            asset="USDC",
            chain="ethereum",
            alert_type="SUPPLY_RATE_DECREASE",
            old_apy=Decimal("6.00"),
            new_apy=Decimal("5.00"),
            apy_change_percent=Decimal("1.00"),
            threshold_percent=Decimal("0.50"),
            notification_sent=False,
            notification_sent_at=None,
            created_at=now,
        )

        # Act & Assert
        assert increase_entity.is_rate_increase
        assert not decrease_entity.is_rate_increase

    def test_is_rate_decrease_property(self):
        """Should identify rate decrease alerts."""
        # Arrange
        now = datetime.now(timezone.utc)

        increase_entity = MoneyMarketAlert(
            id=uuid4(),
            alert_id=uuid4(),
            user_id=uuid4(),
            protocol_id="aave_v3",
            asset="USDC",
            chain="ethereum",
            alert_type="SUPPLY_RATE_INCREASE",
            old_apy=Decimal("5.00"),
            new_apy=Decimal("6.00"),
            apy_change_percent=Decimal("1.00"),
            threshold_percent=Decimal("0.50"),
            notification_sent=False,
            notification_sent_at=None,
            created_at=now,
        )

        decrease_entity = MoneyMarketAlert(
            id=uuid4(),
            alert_id=uuid4(),
            user_id=uuid4(),
            protocol_id="aave_v3",
            asset="USDC",
            chain="ethereum",
            alert_type="BORROW_RATE_DECREASE",
            old_apy=Decimal("6.00"),
            new_apy=Decimal("5.00"),
            apy_change_percent=Decimal("1.00"),
            threshold_percent=Decimal("0.50"),
            notification_sent=False,
            notification_sent_at=None,
            created_at=now,
        )

        # Act & Assert
        assert not increase_entity.is_rate_decrease
        assert decrease_entity.is_rate_decrease

    def test_is_supply_alert_property(self):
        """Should identify supply alerts."""
        # Arrange
        now = datetime.now(timezone.utc)

        supply_entity = MoneyMarketAlert(
            id=uuid4(),
            alert_id=uuid4(),
            user_id=uuid4(),
            protocol_id="aave_v3",
            asset="USDC",
            chain="ethereum",
            alert_type="SUPPLY_RATE_INCREASE",
            old_apy=Decimal("5.00"),
            new_apy=Decimal("6.00"),
            apy_change_percent=Decimal("1.00"),
            threshold_percent=Decimal("0.50"),
            notification_sent=False,
            notification_sent_at=None,
            created_at=now,
        )

        borrow_entity = MoneyMarketAlert(
            id=uuid4(),
            alert_id=uuid4(),
            user_id=uuid4(),
            protocol_id="aave_v3",
            asset="USDC",
            chain="ethereum",
            alert_type="BORROW_RATE_DECREASE",
            old_apy=Decimal("6.00"),
            new_apy=Decimal("5.00"),
            apy_change_percent=Decimal("1.00"),
            threshold_percent=Decimal("0.50"),
            notification_sent=False,
            notification_sent_at=None,
            created_at=now,
        )

        # Act & Assert
        assert supply_entity.is_supply_alert
        assert not borrow_entity.is_supply_alert

    def test_is_borrow_alert_property(self):
        """Should identify borrow alerts."""
        # Arrange
        now = datetime.now(timezone.utc)

        supply_entity = MoneyMarketAlert(
            id=uuid4(),
            alert_id=uuid4(),
            user_id=uuid4(),
            protocol_id="aave_v3",
            asset="USDC",
            chain="ethereum",
            alert_type="SUPPLY_RATE_INCREASE",
            old_apy=Decimal("5.00"),
            new_apy=Decimal("6.00"),
            apy_change_percent=Decimal("1.00"),
            threshold_percent=Decimal("0.50"),
            notification_sent=False,
            notification_sent_at=None,
            created_at=now,
        )

        borrow_entity = MoneyMarketAlert(
            id=uuid4(),
            alert_id=uuid4(),
            user_id=uuid4(),
            protocol_id="aave_v3",
            asset="USDC",
            chain="ethereum",
            alert_type="BORROW_RATE_DECREASE",
            old_apy=Decimal("6.00"),
            new_apy=Decimal("5.00"),
            apy_change_percent=Decimal("1.00"),
            threshold_percent=Decimal("0.50"),
            notification_sent=False,
            notification_sent_at=None,
            created_at=now,
        )

        # Act & Assert
        assert not supply_entity.is_borrow_alert
        assert borrow_entity.is_borrow_alert

    def test_is_pending_notification_property(self):
        """Should identify pending notifications."""
        # Arrange
        now = datetime.now(timezone.utc)

        pending_entity = MoneyMarketAlert(
            id=uuid4(),
            alert_id=uuid4(),
            user_id=uuid4(),
            protocol_id="aave_v3",
            asset="USDC",
            chain="ethereum",
            alert_type="SUPPLY_RATE_INCREASE",
            old_apy=Decimal("5.00"),
            new_apy=Decimal("6.00"),
            apy_change_percent=Decimal("1.00"),
            threshold_percent=Decimal("0.50"),
            notification_sent=False,
            notification_sent_at=None,
            created_at=now,
        )

        sent_entity = MoneyMarketAlert(
            id=uuid4(),
            alert_id=uuid4(),
            user_id=uuid4(),
            protocol_id="aave_v3",
            asset="USDC",
            chain="ethereum",
            alert_type="SUPPLY_RATE_INCREASE",
            old_apy=Decimal("5.00"),
            new_apy=Decimal("6.00"),
            apy_change_percent=Decimal("1.00"),
            threshold_percent=Decimal("0.50"),
            notification_sent=True,
            notification_sent_at=now - timedelta(minutes=5),
            created_at=now - timedelta(minutes=5),
        )

        # Act & Assert
        assert pending_entity.is_pending_notification
        assert not sent_entity.is_pending_notification

    def test_severity_level_property(self):
        """Should map APY change to severity level."""
        # Arrange
        now = datetime.now(timezone.utc)

        low_change = MoneyMarketAlert(
            id=uuid4(),
            alert_id=uuid4(),
            user_id=uuid4(),
            protocol_id="aave_v3",
            asset="USDC",
            chain="ethereum",
            alert_type="SUPPLY_RATE_INCREASE",
            old_apy=Decimal("5.00"),
            new_apy=Decimal("5.30"),
            apy_change_percent=Decimal("0.30"),  # Low
            threshold_percent=Decimal("0.25"),
            notification_sent=False,
            notification_sent_at=None,
            created_at=now,
        )

        medium_change = MoneyMarketAlert(
            id=uuid4(),
            alert_id=uuid4(),
            user_id=uuid4(),
            protocol_id="aave_v3",
            asset="USDC",
            chain="ethereum",
            alert_type="SUPPLY_RATE_INCREASE",
            old_apy=Decimal("5.00"),
            new_apy=Decimal("6.00"),
            apy_change_percent=Decimal("1.00"),  # Medium
            threshold_percent=Decimal("0.50"),
            notification_sent=False,
            notification_sent_at=None,
            created_at=now,
        )

        high_change = MoneyMarketAlert(
            id=uuid4(),
            alert_id=uuid4(),
            user_id=uuid4(),
            protocol_id="aave_v3",
            asset="USDC",
            chain="ethereum",
            alert_type="SUPPLY_RATE_INCREASE",
            old_apy=Decimal("5.00"),
            new_apy=Decimal("8.00"),
            apy_change_percent=Decimal("3.00"),  # High
            threshold_percent=Decimal("0.50"),
            notification_sent=False,
            notification_sent_at=None,
            created_at=now,
        )

        critical_change = MoneyMarketAlert(
            id=uuid4(),
            alert_id=uuid4(),
            user_id=uuid4(),
            protocol_id="aave_v3",
            asset="USDC",
            chain="ethereum",
            alert_type="SUPPLY_RATE_INCREASE",
            old_apy=Decimal("5.00"),
            new_apy=Decimal("11.00"),
            apy_change_percent=Decimal("6.00"),  # Critical
            threshold_percent=Decimal("0.50"),
            notification_sent=False,
            notification_sent_at=None,
            created_at=now,
        )

        # Act & Assert
        assert low_change.severity_level == "LOW"
        assert medium_change.severity_level == "MEDIUM"
        assert high_change.severity_level == "HIGH"
        assert critical_change.severity_level == "CRITICAL"

    def test_is_significant_change_property(self):
        """Should identify significant changes (>= 1%)."""
        # Arrange
        now = datetime.now(timezone.utc)

        small_change = MoneyMarketAlert(
            id=uuid4(),
            alert_id=uuid4(),
            user_id=uuid4(),
            protocol_id="aave_v3",
            asset="USDC",
            chain="ethereum",
            alert_type="SUPPLY_RATE_INCREASE",
            old_apy=Decimal("5.00"),
            new_apy=Decimal("5.50"),
            apy_change_percent=Decimal("0.50"),  # Not significant
            threshold_percent=Decimal("0.25"),
            notification_sent=False,
            notification_sent_at=None,
            created_at=now,
        )

        significant_change = MoneyMarketAlert(
            id=uuid4(),
            alert_id=uuid4(),
            user_id=uuid4(),
            protocol_id="aave_v3",
            asset="USDC",
            chain="ethereum",
            alert_type="SUPPLY_RATE_INCREASE",
            old_apy=Decimal("5.00"),
            new_apy=Decimal("6.50"),
            apy_change_percent=Decimal("1.50"),  # Significant
            threshold_percent=Decimal("0.50"),
            notification_sent=False,
            notification_sent_at=None,
            created_at=now,
        )

        # Act & Assert
        assert not small_change.is_significant_change
        assert significant_change.is_significant_change

    def test_notification_delay_property(self):
        """Should calculate notification delay when sent."""
        # Arrange
        created = datetime(2025, 1, 28, 10, 0, 0, tzinfo=timezone.utc)
        sent = datetime(2025, 1, 28, 10, 5, 0, tzinfo=timezone.utc)

        entity = MoneyMarketAlert(
            id=uuid4(),
            alert_id=uuid4(),
            user_id=uuid4(),
            protocol_id="aave_v3",
            asset="USDC",
            chain="ethereum",
            alert_type="SUPPLY_RATE_INCREASE",
            old_apy=Decimal("5.00"),
            new_apy=Decimal("6.00"),
            apy_change_percent=Decimal("1.00"),
            threshold_percent=Decimal("0.50"),
            notification_sent=True,
            notification_sent_at=sent,
            created_at=created,
        )

        # Act
        delay = entity.notification_delay

        # Assert
        assert delay is not None
        assert delay.total_seconds() == 300  # 5 minutes

    def test_notification_delay_when_not_sent(self):
        """Should return None when notification not sent."""
        # Arrange
        now = datetime.now(timezone.utc)

        entity = MoneyMarketAlert(
            id=uuid4(),
            alert_id=uuid4(),
            user_id=uuid4(),
            protocol_id="aave_v3",
            asset="USDC",
            chain="ethereum",
            alert_type="SUPPLY_RATE_INCREASE",
            old_apy=Decimal("5.00"),
            new_apy=Decimal("6.00"),
            apy_change_percent=Decimal("1.00"),
            threshold_percent=Decimal("0.50"),
            notification_sent=False,
            notification_sent_at=None,
            created_at=now,
        )

        # Act & Assert
        assert entity.notification_delay is None

    def test_protocol_display_name_property(self):
        """Should return display name for protocol."""
        # Arrange
        now = datetime.now(timezone.utc)

        aave_entity = MoneyMarketAlert(
            id=uuid4(),
            alert_id=uuid4(),
            user_id=uuid4(),
            protocol_id="aave_v3",
            asset="USDC",
            chain="ethereum",
            alert_type="SUPPLY_RATE_INCREASE",
            old_apy=Decimal("5.00"),
            new_apy=Decimal("6.00"),
            apy_change_percent=Decimal("1.00"),
            threshold_percent=Decimal("0.50"),
            notification_sent=False,
            notification_sent_at=None,
            created_at=now,
        )

        compound_entity = MoneyMarketAlert(
            id=uuid4(),
            alert_id=uuid4(),
            user_id=uuid4(),
            protocol_id="compound_v3",
            asset="USDC",
            chain="ethereum",
            alert_type="SUPPLY_RATE_INCREASE",
            old_apy=Decimal("5.00"),
            new_apy=Decimal("6.00"),
            apy_change_percent=Decimal("1.00"),
            threshold_percent=Decimal("0.50"),
            notification_sent=False,
            notification_sent_at=None,
            created_at=now,
        )

        # Act & Assert
        assert aave_entity.protocol_display_name == "Aave v3"
        assert compound_entity.protocol_display_name == "Compound v3"

    def test_alert_message_property(self):
        """Should generate human-readable alert message."""
        # Arrange
        now = datetime.now(timezone.utc)

        supply_increase = MoneyMarketAlert(
            id=uuid4(),
            alert_id=uuid4(),
            user_id=uuid4(),
            protocol_id="aave_v3",
            asset="USDC",
            chain="ethereum",
            alert_type="SUPPLY_RATE_INCREASE",
            old_apy=Decimal("5.00"),
            new_apy=Decimal("6.00"),
            apy_change_percent=Decimal("1.00"),
            threshold_percent=Decimal("0.50"),
            notification_sent=False,
            notification_sent_at=None,
            created_at=now,
        )

        borrow_decrease = MoneyMarketAlert(
            id=uuid4(),
            alert_id=uuid4(),
            user_id=uuid4(),
            protocol_id="compound_v3",
            asset="USDT",
            chain="polygon",
            alert_type="BORROW_RATE_DECREASE",
            old_apy=Decimal("4.50"),
            new_apy=Decimal("3.50"),
            apy_change_percent=Decimal("1.00"),
            threshold_percent=Decimal("0.50"),
            notification_sent=False,
            notification_sent_at=None,
            created_at=now,
        )

        # Act & Assert
        assert "Aave v3" in supply_increase.alert_message
        assert "USDC" in supply_increase.alert_message
        assert "ethereum" in supply_increase.alert_message
        assert "supply rate increased" in supply_increase.alert_message.lower()
        assert "5.00%" in supply_increase.alert_message
        assert "6.00%" in supply_increase.alert_message

        assert "Compound v3" in borrow_decrease.alert_message
        assert "USDT" in borrow_decrease.alert_message
        assert "polygon" in borrow_decrease.alert_message
        assert "borrow rate decreased" in borrow_decrease.alert_message.lower()
        assert "4.50%" in borrow_decrease.alert_message
        assert "3.50%" in borrow_decrease.alert_message
