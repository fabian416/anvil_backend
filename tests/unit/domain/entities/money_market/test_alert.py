"""
Tests for MoneyMarketAlert entity.

Tests entity creation, validation, and properties.
"""

import pytest
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from app.domain.entities.money_market.alert import MoneyMarketAlert


@pytest.mark.unit
class TestMoneyMarketAlert:
    """Test suite for MoneyMarketAlert entity."""

    @pytest.fixture
    def valid_alert_data(self):
        """Return valid alert data for testing."""
        now = datetime.now(timezone.utc)
        return {
            "id": uuid4(),
            "user_id": uuid4(),
            "alert_type": "rate_increase",
            "protocol": "aave_v3",
            "asset": "USDC",
            "chain": "ethereum",
            "previous_apy": Decimal("5.00"),
            "new_apy": Decimal("6.00"),
            "apy_change_percent": Decimal("20.00"),  # (6-5)/5 * 100 = 20%
            "severity": "info",
            "message": "USDC supply rate increased by 20%",
            "is_read": False,
            "notification_sent": False,
            "sent_at": None,
            "created_at": now,
        }

    def test_valid_entity_creation(self, valid_alert_data):
        """Should create valid entity with correct attributes."""
        entity = MoneyMarketAlert(**valid_alert_data)

        assert entity.id == valid_alert_data["id"]
        assert entity.user_id == valid_alert_data["user_id"]
        assert entity.protocol == "aave_v3"
        assert entity.asset == "USDC"
        assert entity.chain == "ethereum"
        assert entity.alert_type == "rate_increase"
        assert entity.previous_apy == Decimal("5.00")
        assert entity.new_apy == Decimal("6.00")
        assert entity.notification_sent is False

    def test_valid_entity_with_notification_sent(self, valid_alert_data):
        """Should create valid entity with notification sent."""
        now = datetime.now(timezone.utc)
        valid_alert_data["notification_sent"] = True
        valid_alert_data["sent_at"] = now

        entity = MoneyMarketAlert(**valid_alert_data)

        assert entity.notification_sent is True
        assert entity.sent_at == now

    def test_validation_invalid_protocol(self, valid_alert_data):
        """Should raise error for invalid protocol."""
        valid_alert_data["protocol"] = "invalid_protocol"

        with pytest.raises(ValueError, match="Invalid protocol"):
            MoneyMarketAlert(**valid_alert_data)

    def test_validation_invalid_alert_type(self, valid_alert_data):
        """Should raise error for invalid alert_type."""
        valid_alert_data["alert_type"] = "invalid_type"

        with pytest.raises(ValueError, match="Invalid alert_type"):
            MoneyMarketAlert(**valid_alert_data)

    def test_validation_negative_apy(self, valid_alert_data):
        """Should raise error for negative APY values."""
        valid_alert_data["previous_apy"] = Decimal("-1.00")

        with pytest.raises(ValueError, match="Invalid previous_apy"):
            MoneyMarketAlert(**valid_alert_data)

    def test_validation_empty_asset(self, valid_alert_data):
        """Should raise error for empty asset."""
        valid_alert_data["asset"] = ""

        with pytest.raises(ValueError, match="Asset symbol cannot be empty"):
            MoneyMarketAlert(**valid_alert_data)

    def test_validation_asset_lowercase(self, valid_alert_data):
        """Should raise error for lowercase asset."""
        valid_alert_data["asset"] = "usdc"

        with pytest.raises(ValueError, match="Asset symbol must be uppercase"):
            MoneyMarketAlert(**valid_alert_data)

    def test_is_rate_increase_property(self, valid_alert_data):
        """Should correctly identify rate increase alerts."""
        valid_alert_data["alert_type"] = "rate_increase"
        entity = MoneyMarketAlert(**valid_alert_data)

        assert entity.is_rate_increase is True
        assert entity.is_rate_decrease is False

    def test_is_rate_decrease_property(self, valid_alert_data):
        """Should correctly identify rate decrease alerts."""
        valid_alert_data["alert_type"] = "rate_decrease"
        # Adjust APY for decrease: previous > new
        valid_alert_data["previous_apy"] = Decimal("6.00")
        valid_alert_data["new_apy"] = Decimal("5.00")
        valid_alert_data["apy_change_percent"] = Decimal("-16.6667")  # (5-6)/6 * 100
        entity = MoneyMarketAlert(**valid_alert_data)

        assert entity.is_rate_decrease is True
        assert entity.is_rate_increase is False

    def test_apy_increased_property(self, valid_alert_data):
        """Should correctly identify APY increase."""
        entity = MoneyMarketAlert(**valid_alert_data)

        assert entity.apy_increased is True
        assert entity.apy_decreased is False

    def test_is_significant_property(self, valid_alert_data):
        """Should correctly identify significant changes (>1%)."""
        entity = MoneyMarketAlert(**valid_alert_data)

        assert entity.is_significant is True

    def test_is_stablecoin_property(self, valid_alert_data):
        """Should correctly identify stablecoin assets."""
        entity = MoneyMarketAlert(**valid_alert_data)
        assert entity.is_stablecoin is True

        valid_alert_data["id"] = uuid4()
        valid_alert_data["asset"] = "WETH"
        entity2 = MoneyMarketAlert(**valid_alert_data)
        assert entity2.is_stablecoin is False

    def test_is_aave_property(self, valid_alert_data):
        """Should correctly identify Aave protocol."""
        entity = MoneyMarketAlert(**valid_alert_data)
        assert entity.is_aave is True
        assert entity.is_compound is False

    def test_is_compound_property(self, valid_alert_data):
        """Should correctly identify Compound protocol."""
        valid_alert_data["protocol"] = "compound_v3"
        entity = MoneyMarketAlert(**valid_alert_data)
        assert entity.is_compound is True
        assert entity.is_aave is False

    def test_severity_info(self, valid_alert_data):
        """Should correctly identify info severity."""
        entity = MoneyMarketAlert(**valid_alert_data)
        assert entity.is_info is True
        assert entity.is_warning is False

    def test_severity_warning(self, valid_alert_data):
        """Should correctly identify warning severity."""
        valid_alert_data["severity"] = "warning"
        entity = MoneyMarketAlert(**valid_alert_data)
        assert entity.is_warning is True
        assert entity.is_info is False

    def test_notification_sent_requires_timestamp(self, valid_alert_data):
        """Should raise error if notification_sent is True but sent_at is None."""
        valid_alert_data["notification_sent"] = True
        valid_alert_data["sent_at"] = None

        with pytest.raises(ValueError, match="notification_sent is True but sent_at is None"):
            MoneyMarketAlert(**valid_alert_data)

    def test_formatted_change_property(self, valid_alert_data):
        """Should format change with correct sign."""
        entity = MoneyMarketAlert(**valid_alert_data)
        assert entity.formatted_change == "+20.00%"

    def test_apy_change_absolute_property(self, valid_alert_data):
        """Should calculate absolute APY change."""
        entity = MoneyMarketAlert(**valid_alert_data)
        assert entity.apy_change_absolute == Decimal("1.00")
