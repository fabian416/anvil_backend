"""
Tests for MoneyMarketRateComparison entity.

Tests entity creation, validation, and properties.
"""

import pytest
from datetime import datetime, timezone
from uuid import uuid4

from app.domain.entities.money_market.rate_comparison import (
    MoneyMarketRateComparison,
)


@pytest.mark.unit
class TestMoneyMarketRateComparison:
    """Test suite for MoneyMarketRateComparison entity."""

    @pytest.fixture
    def valid_user_comparison_data(self):
        """Return valid comparison data for authenticated user."""
        now = datetime.now(timezone.utc)
        return {
            "id": uuid4(),
            "user_id": uuid4(),
            "guest_session_id": None,
            "asset": "USDC",
            "chain": "ethereum",
            "protocols_compared": [
                {"protocol": "aave_v3", "supply_apy": "5.25", "borrow_apy": "3.50"},
                {"protocol": "compound_v3", "supply_apy": "4.80", "borrow_apy": "3.20"},
            ],
            "best_supply_protocol": "aave_v3",
            "best_supply_apy": "5.25",
            "best_borrow_protocol": "compound_v3",
            "best_borrow_apy": "3.20",
            "latency_ms": 150,
            "language": "en",
            "created_at": now,
        }

    @pytest.fixture
    def valid_guest_comparison_data(self):
        """Return valid comparison data for guest user."""
        now = datetime.now(timezone.utc)
        return {
            "id": uuid4(),
            "user_id": None,
            "guest_session_id": "guest_abc123",
            "asset": "USDT",
            "chain": "polygon",
            "protocols_compared": [
                {"protocol": "aave_v3", "supply_apy": "4.50", "borrow_apy": "2.80"},
            ],
            "best_supply_protocol": "aave_v3",
            "best_supply_apy": "4.50",
            "best_borrow_protocol": "aave_v3",
            "best_borrow_apy": "2.80",
            "latency_ms": 200,
            "language": "es",
            "created_at": now,
        }

    def test_valid_user_comparison_creation(self, valid_user_comparison_data):
        """Should create valid entity for authenticated user."""
        entity = MoneyMarketRateComparison(**valid_user_comparison_data)

        assert entity.id == valid_user_comparison_data["id"]
        assert entity.user_id == valid_user_comparison_data["user_id"]
        assert entity.guest_session_id is None
        assert entity.asset == "USDC"
        assert entity.chain == "ethereum"
        assert len(entity.protocols_compared) == 2
        assert entity.best_supply_protocol == "aave_v3"
        assert entity.latency_ms == 150
        assert entity.language == "en"

    def test_valid_guest_comparison_creation(self, valid_guest_comparison_data):
        """Should create valid entity for guest user."""
        entity = MoneyMarketRateComparison(**valid_guest_comparison_data)

        assert entity.user_id is None
        assert entity.guest_session_id == "guest_abc123"
        assert entity.asset == "USDT"
        assert entity.chain == "polygon"

    def test_validation_xor_both_ids_present(self, valid_user_comparison_data):
        """Should raise error if both user_id and guest_session_id provided."""
        valid_user_comparison_data["guest_session_id"] = "guest_xyz"

        with pytest.raises(ValueError, match="Cannot provide both"):
            MoneyMarketRateComparison(**valid_user_comparison_data)

    def test_validation_xor_neither_id_present(self, valid_user_comparison_data):
        """Should raise error if neither user_id nor guest_session_id provided."""
        valid_user_comparison_data["user_id"] = None
        valid_user_comparison_data["guest_session_id"] = None

        with pytest.raises(ValueError, match="Must provide either"):
            MoneyMarketRateComparison(**valid_user_comparison_data)

    def test_validation_empty_asset(self, valid_user_comparison_data):
        """Should raise error for empty asset."""
        valid_user_comparison_data["asset"] = ""

        with pytest.raises(ValueError, match="Asset symbol cannot be empty"):
            MoneyMarketRateComparison(**valid_user_comparison_data)

    def test_validation_lowercase_asset(self, valid_user_comparison_data):
        """Should raise error for lowercase asset."""
        valid_user_comparison_data["asset"] = "usdc"

        with pytest.raises(ValueError, match="Asset symbol must be uppercase"):
            MoneyMarketRateComparison(**valid_user_comparison_data)

    def test_validation_empty_chain(self, valid_user_comparison_data):
        """Should raise error for empty chain."""
        valid_user_comparison_data["chain"] = ""

        with pytest.raises(ValueError, match="Chain cannot be empty"):
            MoneyMarketRateComparison(**valid_user_comparison_data)

    def test_validation_empty_protocols_compared(self, valid_user_comparison_data):
        """Should raise error for empty protocols list."""
        valid_user_comparison_data["protocols_compared"] = []

        with pytest.raises(ValueError, match="at least one protocol"):
            MoneyMarketRateComparison(**valid_user_comparison_data)

    def test_validation_empty_best_supply_protocol(self, valid_user_comparison_data):
        """Should raise error for empty best_supply_protocol."""
        valid_user_comparison_data["best_supply_protocol"] = ""

        with pytest.raises(ValueError, match="best_supply_protocol cannot be empty"):
            MoneyMarketRateComparison(**valid_user_comparison_data)

    def test_validation_non_positive_latency(self, valid_user_comparison_data):
        """Should raise error for non-positive latency."""
        valid_user_comparison_data["latency_ms"] = 0

        with pytest.raises(ValueError, match="latency_ms must be positive"):
            MoneyMarketRateComparison(**valid_user_comparison_data)

    def test_validation_invalid_language(self, valid_user_comparison_data):
        """Should raise error for invalid language code."""
        valid_user_comparison_data["language"] = "invalid"

        with pytest.raises(ValueError, match="Invalid language"):
            MoneyMarketRateComparison(**valid_user_comparison_data)

    def test_is_guest_comparison_property(self, valid_guest_comparison_data):
        """Should correctly identify guest comparisons."""
        entity = MoneyMarketRateComparison(**valid_guest_comparison_data)
        assert entity.is_guest_comparison is True

    def test_is_authenticated_comparison(self, valid_user_comparison_data):
        """Should correctly identify authenticated comparisons."""
        entity = MoneyMarketRateComparison(**valid_user_comparison_data)
        assert entity.is_authenticated_comparison is True

    def test_comparison_count_property(self, valid_user_comparison_data):
        """Should count protocols compared."""
        entity = MoneyMarketRateComparison(**valid_user_comparison_data)
        assert entity.comparison_count == 2

    def test_is_fast_response_property(self, valid_user_comparison_data):
        """Should identify fast responses (< 500ms)."""
        entity = MoneyMarketRateComparison(**valid_user_comparison_data)
        assert entity.is_fast_response is True

        valid_user_comparison_data["id"] = uuid4()
        valid_user_comparison_data["latency_ms"] = 600
        entity2 = MoneyMarketRateComparison(**valid_user_comparison_data)
        assert entity2.is_fast_response is False

    def test_is_stablecoin_property(self, valid_user_comparison_data):
        """Should correctly identify stablecoin comparisons."""
        entity = MoneyMarketRateComparison(**valid_user_comparison_data)
        assert entity.is_stablecoin is True

        valid_user_comparison_data["id"] = uuid4()
        valid_user_comparison_data["asset"] = "WETH"
        entity2 = MoneyMarketRateComparison(**valid_user_comparison_data)
        assert entity2.is_stablecoin is False

    def test_is_ethereum_mainnet_property(self, valid_user_comparison_data):
        """Should correctly identify Ethereum mainnet comparisons."""
        entity = MoneyMarketRateComparison(**valid_user_comparison_data)
        assert entity.is_ethereum_mainnet is True

    def test_is_layer2_property(self, valid_guest_comparison_data):
        """Should correctly identify Layer 2 comparisons."""
        entity = MoneyMarketRateComparison(**valid_guest_comparison_data)
        assert entity.is_layer2 is True
