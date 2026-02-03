"""
Unit tests for HealthFactorValidator domain service.

These tests verify the pure business logic for health factor
validation WITHOUT any infrastructure dependencies.
"""

import pytest
from decimal import Decimal

from app.domain.services.lending.health_factor_validator import HealthFactorValidator
from app.domain.value_objects.lending.health_factor_result import (
    HealthFactorLevel,
    HealthFactorResult,
)


class TestHealthFactorCalculation:
    """Test core health factor calculation logic."""

    def test_calculate_hf_with_debt(self):
        """Test HF calculation with debt: HF = (Collateral * LT) / Debt."""
        validator = HealthFactorValidator()

        hf = validator._calculate_health_factor(
            collateral_usd=Decimal("5000"),  # $5000 collateral
            debt_usd=Decimal("2000"),  # $2000 debt
            liquidation_threshold=Decimal("0.825"),  # 82.5% LT
        )

        # Expected: (5000 * 0.825) / 2000 = 2.0625
        assert hf == Decimal("2.0625")

    def test_calculate_hf_no_debt(self):
        """Test HF calculation without debt returns infinity."""
        validator = HealthFactorValidator()

        hf = validator._calculate_health_factor(
            collateral_usd=Decimal("5000"),
            debt_usd=Decimal("0"),
            liquidation_threshold=Decimal("0.825"),
        )

        assert hf == Decimal("inf")

    def test_calculate_hf_at_liquidation_threshold(self):
        """Test HF = 1.0 when debt equals max borrowable."""
        validator = HealthFactorValidator()

        # At liquidation: Debt = Collateral * LT
        hf = validator._calculate_health_factor(
            collateral_usd=Decimal("5000"),
            debt_usd=Decimal("4125"),  # 5000 * 0.825
            liquidation_threshold=Decimal("0.825"),
        )

        assert hf == Decimal("1.0")


class TestRiskLevelDetermination:
    """Test risk level classification."""

    def test_safe_level_hf_above_2(self):
        """Test SAFE level for HF >= 2.0."""
        validator = HealthFactorValidator()

        level = validator._determine_level(Decimal("2.5"))
        assert level == HealthFactorLevel.SAFE

        level = validator._determine_level(Decimal("2.0"))
        assert level == HealthFactorLevel.SAFE

    def test_caution_level_hf_1_5_to_2(self):
        """Test CAUTION level for 1.5 <= HF < 2.0."""
        validator = HealthFactorValidator()

        level = validator._determine_level(Decimal("1.8"))
        assert level == HealthFactorLevel.CAUTION

        level = validator._determine_level(Decimal("1.5"))
        assert level == HealthFactorLevel.CAUTION

    def test_danger_level_hf_1_2_to_1_5(self):
        """Test DANGER level for 1.2 <= HF < 1.5."""
        validator = HealthFactorValidator()

        level = validator._determine_level(Decimal("1.3"))
        assert level == HealthFactorLevel.DANGER

        level = validator._determine_level(Decimal("1.2"))
        assert level == HealthFactorLevel.DANGER

    def test_critical_level_hf_1_to_1_2(self):
        """Test CRITICAL level for 1.0 <= HF < 1.2."""
        validator = HealthFactorValidator()

        level = validator._determine_level(Decimal("1.1"))
        assert level == HealthFactorLevel.CRITICAL

        level = validator._determine_level(Decimal("1.0"))
        assert level == HealthFactorLevel.CRITICAL

    def test_liquidatable_level_hf_below_1(self):
        """Test LIQUIDATABLE level for HF < 1.0."""
        validator = HealthFactorValidator()

        level = validator._determine_level(Decimal("0.95"))
        assert level == HealthFactorLevel.LIQUIDATABLE

        level = validator._determine_level(Decimal("0.5"))
        assert level == HealthFactorLevel.LIQUIDATABLE


class TestBorrowValidation:
    """Test borrow validation scenarios."""

    def test_safe_borrow_approval(self):
        """Test that safe borrow (HF >= 2.0) is approved."""
        validator = HealthFactorValidator()

        result = validator.validate_borrow(
            current_collateral_usd=Decimal("5000"),  # $5000 ETH
            current_debt_usd=Decimal("0"),
            new_borrow_usd=Decimal("2000"),  # Borrow $2000
            liquidation_threshold=Decimal("0.825"),
        )

        # HF = (5000 * 0.825) / 2000 = 2.0625
        assert result.projected_hf == Decimal("2.0625")
        assert result.level == HealthFactorLevel.SAFE
        assert result.is_safe is True
        assert "SAFE" in result.warning_message

    def test_caution_borrow_approval(self):
        """Test that caution borrow (1.5 <= HF < 2.0) is approved."""
        validator = HealthFactorValidator()

        result = validator.validate_borrow(
            current_collateral_usd=Decimal("5000"),
            current_debt_usd=Decimal("0"),
            new_borrow_usd=Decimal("2750"),  # Results in HF = 1.5
            liquidation_threshold=Decimal("0.825"),
        )

        # HF = (5000 * 0.825) / 2750 = 1.5
        assert result.projected_hf == Decimal("1.5")
        assert result.level == HealthFactorLevel.CAUTION
        assert result.is_safe is True  # Still above 1.2 minimum
        assert "CAUTION" in result.warning_message

    def test_danger_borrow_blocked(self):
        """Test that danger borrow (1.2 <= HF < 1.5) is still approved but warned."""
        validator = HealthFactorValidator()

        result = validator.validate_borrow(
            current_collateral_usd=Decimal("5000"),
            current_debt_usd=Decimal("0"),
            new_borrow_usd=Decimal("3437.5"),  # Results in HF = 1.2
            liquidation_threshold=Decimal("0.825"),
        )

        # HF = (5000 * 0.825) / 3437.5 = 1.2
        assert result.projected_hf == Decimal("1.2")
        assert result.level == HealthFactorLevel.DANGER
        assert result.is_safe is True  # Exactly at threshold
        assert "DANGER" in result.warning_message

    def test_critical_borrow_blocked(self):
        """Test that critical borrow (1.0 <= HF < 1.2) is BLOCKED."""
        validator = HealthFactorValidator()

        result = validator.validate_borrow(
            current_collateral_usd=Decimal("5000"),
            current_debt_usd=Decimal("0"),
            new_borrow_usd=Decimal("3750"),  # Results in HF = 1.1
            liquidation_threshold=Decimal("0.825"),
        )

        # HF = (5000 * 0.825) / 3750 = 1.1
        assert result.projected_hf == Decimal("1.1")
        assert result.level == HealthFactorLevel.CRITICAL
        assert result.is_safe is False  # BLOCKED
        assert "CRITICAL" in result.warning_message
        assert "BLOCKED" in result.warning_message

    def test_liquidatable_borrow_blocked(self):
        """Test that liquidatable borrow (HF < 1.0) is BLOCKED."""
        validator = HealthFactorValidator()

        result = validator.validate_borrow(
            current_collateral_usd=Decimal("5000"),
            current_debt_usd=Decimal("0"),
            new_borrow_usd=Decimal("4500"),  # Results in HF < 1.0
            liquidation_threshold=Decimal("0.825"),
        )

        # HF = (5000 * 0.825) / 4500 = 0.917
        assert result.projected_hf < Decimal("1.0")
        assert result.level == HealthFactorLevel.LIQUIDATABLE
        assert result.is_safe is False  # BLOCKED
        assert "LIQUIDATABLE" in result.warning_message

    def test_additional_borrow_with_existing_debt(self):
        """Test borrow validation with existing debt."""
        validator = HealthFactorValidator()

        result = validator.validate_borrow(
            current_collateral_usd=Decimal("5000"),
            current_debt_usd=Decimal("1000"),  # Already $1000 debt
            new_borrow_usd=Decimal("1000"),  # Borrow additional $1000
            liquidation_threshold=Decimal("0.825"),
        )

        # Current HF = (5000 * 0.825) / 1000 = 4.125
        # Projected HF = (5000 * 0.825) / 2000 = 2.0625
        assert result.current_hf == Decimal("4.125")
        assert result.projected_hf == Decimal("2.0625")
        assert result.is_safe is True


class TestMaxSafeBorrow:
    """Test maximum safe borrow calculations."""

    def test_max_safe_borrow_no_existing_debt(self):
        """Test max borrow calculation with no existing debt."""
        validator = HealthFactorValidator()

        max_borrow = validator._calculate_max_safe_borrow(
            current_collateral_usd=Decimal("5000"),
            current_debt_usd=Decimal("0"),
            liquidation_threshold=Decimal("0.825"),
        )

        # Max debt for HF = 1.5: (5000 * 0.825) / 1.5 = 2750
        assert max_borrow == Decimal("2750")

    def test_max_safe_borrow_with_existing_debt(self):
        """Test max borrow calculation with existing debt."""
        validator = HealthFactorValidator()

        max_borrow = validator._calculate_max_safe_borrow(
            current_collateral_usd=Decimal("5000"),
            current_debt_usd=Decimal("1000"),  # Already $1000 borrowed
            liquidation_threshold=Decimal("0.825"),
        )

        # Max total debt for HF = 1.5: 2750
        # Additional borrow: 2750 - 1000 = 1750
        assert max_borrow == Decimal("1750")

    def test_max_safe_borrow_at_limit(self):
        """Test max borrow when already at recommended HF."""
        validator = HealthFactorValidator()

        max_borrow = validator._calculate_max_safe_borrow(
            current_collateral_usd=Decimal("5000"),
            current_debt_usd=Decimal("2750"),  # Already at HF = 1.5
            liquidation_threshold=Decimal("0.825"),
        )

        # Already at limit, cannot borrow more
        assert max_borrow == Decimal("0")


class TestLiquidationPrice:
    """Test liquidation price calculations."""

    def test_liquidation_price_calculation(self):
        """Test liquidation price calculation."""
        validator = HealthFactorValidator()

        # User has $5000 in ETH at $3000/ETH = 1.667 ETH
        # Debt: $3000
        # LT: 0.825
        liquidation_price = validator._calculate_liquidation_price(
            current_collateral_usd=Decimal("5000"),
            projected_debt_usd=Decimal("3000"),
            liquidation_threshold=Decimal("0.825"),
            current_price=Decimal("3000"),
        )

        # At liquidation (HF = 1.0):
        # 1.0 = (1.667 * Price * 0.825) / 3000
        # Price = 3000 / (1.667 * 0.825) = 2181.82
        expected = Decimal("3000") / (
            Decimal("5000") / Decimal("3000") * Decimal("0.825")
        )
        assert liquidation_price == expected

    def test_liquidation_price_shows_in_warning(self):
        """Test that liquidation price appears in warning message."""
        validator = HealthFactorValidator()

        result = validator.validate_borrow(
            current_collateral_usd=Decimal("5000"),
            current_debt_usd=Decimal("0"),
            new_borrow_usd=Decimal("2750"),
            liquidation_threshold=Decimal("0.825"),
            collateral_asset="ETH",
            current_price=Decimal("3000"),
        )

        assert result.liquidation_price is not None
        assert (
            "Liquidation" in result.warning_message
            or "liquidation" in result.warning_message
        )


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_zero_collateral(self):
        """Test validation with zero collateral."""
        validator = HealthFactorValidator()

        result = validator.validate_borrow(
            current_collateral_usd=Decimal("0"),
            current_debt_usd=Decimal("0"),
            new_borrow_usd=Decimal("1000"),
            liquidation_threshold=Decimal("0.825"),
        )

        # Cannot borrow with no collateral
        assert result.is_safe is False
        assert result.level == HealthFactorLevel.LIQUIDATABLE

    def test_zero_borrow_amount(self):
        """Test validation with zero borrow amount."""
        validator = HealthFactorValidator()

        result = validator.validate_borrow(
            current_collateral_usd=Decimal("5000"),
            current_debt_usd=Decimal("1000"),
            new_borrow_usd=Decimal("0"),
            liquidation_threshold=Decimal("0.825"),
        )

        # No new borrow, HF stays the same
        assert result.current_hf == result.projected_hf
        assert result.is_safe is True

    def test_very_high_hf(self):
        """Test validation with very high health factor."""
        validator = HealthFactorValidator()

        result = validator.validate_borrow(
            current_collateral_usd=Decimal("100000"),
            current_debt_usd=Decimal("0"),
            new_borrow_usd=Decimal("100"),
            liquidation_threshold=Decimal("0.825"),
        )

        # HF = (100000 * 0.825) / 100 = 825
        assert result.projected_hf == Decimal("825")
        assert result.level == HealthFactorLevel.SAFE
        assert result.is_safe is True

    def test_different_liquidation_thresholds(self):
        """Test with different LT values (different collateral assets)."""
        validator = HealthFactorValidator()

        # ETH: 82.5% LT
        result_eth = validator.validate_borrow(
            current_collateral_usd=Decimal("5000"),
            current_debt_usd=Decimal("0"),
            new_borrow_usd=Decimal("2000"),
            liquidation_threshold=Decimal("0.825"),
        )

        # WBTC: 70% LT (more risky)
        result_wbtc = validator.validate_borrow(
            current_collateral_usd=Decimal("5000"),
            current_debt_usd=Decimal("0"),
            new_borrow_usd=Decimal("2000"),
            liquidation_threshold=Decimal("0.70"),
        )

        # Lower LT = lower HF
        assert result_wbtc.projected_hf < result_eth.projected_hf


class TestResultSerialization:
    """Test HealthFactorResult serialization."""

    def test_to_dict(self):
        """Test serialization to dictionary."""
        validator = HealthFactorValidator()

        result = validator.validate_borrow(
            current_collateral_usd=Decimal("5000"),
            current_debt_usd=Decimal("0"),
            new_borrow_usd=Decimal("2000"),
            liquidation_threshold=Decimal("0.825"),
        )

        data = result.to_dict()

        assert "projected_hf" in data
        assert "level" in data
        assert "is_safe" in data
        assert "warning_message" in data
        assert data["color"] == "green"
        assert data["emoji"] == "✅"

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "current_hf": "4.125",
            "projected_hf": "2.0625",
            "level": "safe",
            "is_safe": True,
            "warning_message": "✅ SAFE",
            "liquidation_price": "2000.00",
            "max_safe_borrow_usd": "1750.00",
            "collateral_usd": "5000.00",
            "current_debt_usd": "1000.00",
            "projected_debt_usd": "2000.00",
        }

        result = HealthFactorResult.from_dict(data)

        assert result.projected_hf == Decimal("2.0625")
        assert result.level == HealthFactorLevel.SAFE
        assert result.is_safe is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
