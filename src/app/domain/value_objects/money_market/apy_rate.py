"""
APY rate value object with precision handling.
"""

from dataclasses import dataclass
from decimal import Decimal

from app.domain.exceptions.base import DomainFieldError
from app.domain.value_objects.base import ValueObject


@dataclass(frozen=True, repr=False)
class ApyRate(ValueObject[Decimal]):
    """
    APY rate value object with precision handling.

    Stores APY as a percentage value (e.g., 5.25 for 5.25% APY).
    Range: 0.00% to 100.00%
    """

    value: Decimal

    def __post_init__(self) -> None:
        """
        Validate APY rate.

        :raises DomainFieldError: If rate is invalid
        """
        super().__post_init__()
        self._validate_range()
        self._validate_precision()

    def _validate_range(self) -> None:
        """Validate APY is within valid range (0-100%)."""
        if self.value < Decimal("0"):
            raise DomainFieldError(
                f"APY rate cannot be negative: {self.value}%"
            )
        if self.value > Decimal("100"):
            raise DomainFieldError(
                f"APY rate cannot exceed 100%: {self.value}%"
            )

    def _validate_precision(self) -> None:
        """Validate APY has reasonable precision (max 4 decimal places)."""
        # Check if more than 4 decimal places
        value_str = str(self.value)
        if "." in value_str:
            decimal_places = len(value_str.split(".")[1])
            if decimal_places > 4:
                raise DomainFieldError(
                    f"APY rate has too many decimal places: {self.value}. "
                    "Maximum 4 decimal places allowed."
                )

    @property
    def as_percentage(self) -> str:
        """Get APY as formatted percentage string (e.g., '5.25%')."""
        return f"{self.value:.2f}%"

    @property
    def as_precise_percentage(self) -> str:
        """Get APY as precise percentage string with 4 decimals."""
        return f"{self.value:.4f}%"

    @property
    def as_decimal(self) -> Decimal:
        """Get APY as decimal (e.g., 0.0525 for 5.25%)."""
        return self.value / Decimal("100")

    @property
    def is_zero(self) -> bool:
        """Check if APY is zero."""
        return self.value == Decimal("0")

    @property
    def is_low(self) -> bool:
        """Check if APY is low (<1%)."""
        return self.value < Decimal("1")

    @property
    def is_medium(self) -> bool:
        """Check if APY is medium (1-5%)."""
        return Decimal("1") <= self.value <= Decimal("5")

    @property
    def is_high(self) -> bool:
        """Check if APY is high (>5%)."""
        return self.value > Decimal("5")

    @property
    def is_very_high(self) -> bool:
        """Check if APY is very high (>10%)."""
        return self.value > Decimal("10")

    @property
    def is_suspicious(self) -> bool:
        """Check if APY is suspiciously high (>20%)."""
        return self.value > Decimal("20")

    def compare_with(self, other: "ApyRate") -> Decimal:
        """
        Compare this APY with another and return the difference.

        Args:
            other: Another APY rate to compare with

        Returns:
            Difference in percentage points (can be negative)
        """
        return self.value - other.value

    def percentage_change_from(self, other: "ApyRate") -> Decimal:
        """
        Calculate percentage change from another APY rate.

        Args:
            other: Previous APY rate

        Returns:
            Percentage change (e.g., 10.5 for 10.5% increase)
        """
        if other.value == Decimal("0"):
            return Decimal("0")
        return ((self.value - other.value) / other.value) * Decimal("100")
