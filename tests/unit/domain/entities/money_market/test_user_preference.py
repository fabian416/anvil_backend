"""
Tests for MoneyMarketUserPreference entity.

Tests entity creation, validation, and properties.
"""

import pytest
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from app.domain.entities.money_market.user_preference import (
    MoneyMarketUserPreference,
)


@pytest.mark.unit
class TestMoneyMarketUserPreference:
    """Test suite for MoneyMarketUserPreference entity."""

    @pytest.fixture
    def valid_preference_data(self):
        """Return valid preference data for testing."""
        now = datetime.now(timezone.utc)
        return {
            "id": uuid4(),
            "user_id": uuid4(),
            "enable_rate_alerts": True,
            "alert_threshold_apy_change": Decimal("0.50"),
            "watched_assets": ["USDC", "USDT", "DAI"],
            "watched_chains": ["ethereum", "polygon", "arbitrum"],
            "preferred_protocol": "aave_v3",
            "notification_enabled": True,
            "created_at": now,
            "updated_at": now,
        }

    def test_valid_entity_creation(self, valid_preference_data):
        """Should create valid entity with correct attributes."""
        entity = MoneyMarketUserPreference(**valid_preference_data)

        assert entity.id == valid_preference_data["id"]
        assert entity.user_id == valid_preference_data["user_id"]
        assert entity.enable_rate_alerts is True
        assert entity.alert_threshold_apy_change == Decimal("0.50")
        assert entity.watched_assets == ["USDC", "USDT", "DAI"]
        assert entity.watched_chains == ["ethereum", "polygon", "arbitrum"]
        assert entity.preferred_protocol == "aave_v3"
        assert entity.notification_enabled is True

    def test_valid_entity_with_empty_lists(self, valid_preference_data):
        """Should create valid entity with empty watched lists."""
        valid_preference_data["watched_assets"] = []
        valid_preference_data["watched_chains"] = []
        valid_preference_data["preferred_protocol"] = None

        entity = MoneyMarketUserPreference(**valid_preference_data)

        assert entity.watched_assets == []
        assert entity.watched_chains == []
        assert entity.preferred_protocol is None

    def test_validation_threshold_too_low(self, valid_preference_data):
        """Should raise error for threshold below minimum."""
        valid_preference_data["alert_threshold_apy_change"] = Decimal("0.001")

        with pytest.raises(ValueError, match="Invalid alert_threshold_apy_change"):
            MoneyMarketUserPreference(**valid_preference_data)

    def test_validation_threshold_too_high(self, valid_preference_data):
        """Should raise error for threshold above maximum."""
        valid_preference_data["alert_threshold_apy_change"] = Decimal("15.0")

        with pytest.raises(ValueError, match="Invalid alert_threshold_apy_change"):
            MoneyMarketUserPreference(**valid_preference_data)

    def test_validation_valid_threshold_boundary_low(self, valid_preference_data):
        """Should accept threshold at minimum boundary."""
        valid_preference_data["alert_threshold_apy_change"] = Decimal("0.01")

        entity = MoneyMarketUserPreference(**valid_preference_data)
        assert entity.alert_threshold_apy_change == Decimal("0.01")

    def test_validation_valid_threshold_boundary_high(self, valid_preference_data):
        """Should accept threshold at maximum boundary."""
        valid_preference_data["alert_threshold_apy_change"] = Decimal("10.0")

        entity = MoneyMarketUserPreference(**valid_preference_data)
        assert entity.alert_threshold_apy_change == Decimal("10.0")

    def test_validation_watched_asset_lowercase(self, valid_preference_data):
        """Should raise error for lowercase asset."""
        valid_preference_data["watched_assets"] = ["usdc"]

        with pytest.raises(ValueError, match="Watched asset must be uppercase"):
            MoneyMarketUserPreference(**valid_preference_data)

    def test_validation_watched_asset_empty_string(self, valid_preference_data):
        """Should raise error for empty asset string."""
        valid_preference_data["watched_assets"] = [""]

        with pytest.raises(ValueError, match="Watched asset cannot be empty"):
            MoneyMarketUserPreference(**valid_preference_data)

    def test_validation_watched_chain_uppercase(self, valid_preference_data):
        """Should raise error for uppercase chain."""
        valid_preference_data["watched_chains"] = ["ETHEREUM"]

        with pytest.raises(ValueError, match="Watched chain must be lowercase"):
            MoneyMarketUserPreference(**valid_preference_data)

    def test_validation_watched_chain_empty_string(self, valid_preference_data):
        """Should raise error for empty chain string."""
        valid_preference_data["watched_chains"] = [""]

        with pytest.raises(ValueError, match="Watched chain cannot be empty"):
            MoneyMarketUserPreference(**valid_preference_data)

    def test_validation_invalid_protocol(self, valid_preference_data):
        """Should raise error for invalid protocol."""
        valid_preference_data["preferred_protocol"] = "invalid_protocol"

        with pytest.raises(ValueError, match="Invalid preferred_protocol"):
            MoneyMarketUserPreference(**valid_preference_data)

    def test_is_watching_asset_property(self, valid_preference_data):
        """Should correctly check if watching an asset."""
        entity = MoneyMarketUserPreference(**valid_preference_data)

        assert entity.is_watching_asset("USDC") is True
        assert entity.is_watching_asset("WETH") is False

    def test_is_watching_chain_property(self, valid_preference_data):
        """Should correctly check if watching a chain."""
        entity = MoneyMarketUserPreference(**valid_preference_data)

        assert entity.is_watching_chain("ethereum") is True
        assert entity.is_watching_chain("optimism") is False

    def test_prefers_aave_property(self, valid_preference_data):
        """Should correctly identify Aave preference."""
        entity = MoneyMarketUserPreference(**valid_preference_data)
        assert entity.prefers_aave is True
        assert entity.prefers_compound is False

    def test_prefers_compound_property(self, valid_preference_data):
        """Should correctly identify Compound preference."""
        valid_preference_data["preferred_protocol"] = "compound_v3"
        entity = MoneyMarketUserPreference(**valid_preference_data)
        assert entity.prefers_compound is True
        assert entity.prefers_aave is False

    def test_has_no_protocol_preference(self, valid_preference_data):
        """Should handle no protocol preference."""
        valid_preference_data["preferred_protocol"] = None
        entity = MoneyMarketUserPreference(**valid_preference_data)
        assert entity.prefers_aave is False
        assert entity.prefers_compound is False
        assert entity.has_preferred_protocol is False

    def test_has_preferred_protocol_property(self, valid_preference_data):
        """Should correctly identify if has protocol preference."""
        entity = MoneyMarketUserPreference(**valid_preference_data)
        assert entity.has_preferred_protocol is True

    def test_has_rate_alerts_property(self, valid_preference_data):
        """Should reflect alerts enabled status."""
        entity = MoneyMarketUserPreference(**valid_preference_data)
        assert entity.has_rate_alerts is True

        valid_preference_data["id"] = uuid4()
        valid_preference_data["enable_rate_alerts"] = False
        entity2 = MoneyMarketUserPreference(**valid_preference_data)
        assert entity2.has_rate_alerts is False

    def test_watched_asset_count_property(self, valid_preference_data):
        """Should count watched assets."""
        entity = MoneyMarketUserPreference(**valid_preference_data)
        assert entity.watched_asset_count == 3

    def test_watched_chain_count_property(self, valid_preference_data):
        """Should count watched chains."""
        entity = MoneyMarketUserPreference(**valid_preference_data)
        assert entity.watched_chain_count == 3
