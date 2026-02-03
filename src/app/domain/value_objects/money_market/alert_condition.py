"""
Alert condition value object for rate change thresholds.
"""

from dataclasses import dataclass
from decimal import Decimal

from app.domain.exceptions.base import DomainFieldError
from app.domain.value_objects.base import ValueObject


@dataclass(frozen=True, repr=False)
class AlertCondition(ValueObject[Decimal]):
    """
    Alert threshold condition value object.

    Represents the minimum APY change percentage that triggers an alert.
    Range: 0.01% (very sensitive) to 10.00% (only major changes)
    """

    value: Decimal

    def __post_init__(self) -> None:
        """
        Validate alert condition threshold.

        :raises DomainFieldError: If threshold is invalid
        """
        super().__post_init__()
        self._validate_range()
        self._validate_precision()

    def _validate_range(self) -> None:
        """Validate threshold is within valid range (0.01-10%)."""
        if self.value < Decimal("0.01"):
            raise DomainFieldError(
                f"Alert threshold too low: {self.value}%. "
                "Minimum 0.01% to avoid excessive alerts."
            )
        if self.value > Decimal("10.0"):
            raise DomainFieldError(
                f"Alert threshold too high: {self.value}%. "
                "Maximum 10% to ensure meaningful alerts."
            )

    def _validate_precision(self) -> None:
        """Validate threshold has reasonable precision (max 2 decimal places)."""
        value_str = str(self.value)
        if "." in value_str:
            decimal_places = len(value_str.split(".")[1])
            if decimal_places > 2:
                raise DomainFieldError(
                    f"Alert threshold has too many decimal places: {self.value}%. "
                    "Maximum 2 decimal places allowed."
                )

    @property
    def as_percentage(self) -> str:
        """Get threshold as formatted percentage string (e.g., '0.50%')."""
        return f"{self.value:.2f}%"

    @property
    def as_decimal(self) -> Decimal:
        """Get threshold as decimal (e.g., 0.005 for 0.50%)."""
        return self.value / Decimal("100")

    @property
    def is_very_sensitive(self) -> bool:
        """Check if threshold is very sensitive (<0.1%)."""
        return self.value < Decimal("0.1")

    @property
    def is_sensitive(self) -> bool:
        """Check if threshold is sensitive (0.1-0.5%)."""
        return Decimal("0.1") <= self.value < Decimal("0.5")

    @property
    def is_normal(self) -> bool:
        """Check if threshold is normal (0.5-2%)."""
        return Decimal("0.5") <= self.value <= Decimal("2.0")

    @property
    def is_relaxed(self) -> bool:
        """Check if threshold is relaxed (2-5%)."""
        return Decimal("2.0") < self.value <= Decimal("5.0")

    @property
    def is_very_relaxed(self) -> bool:
        """Check if threshold is very relaxed (>5%)."""
        return self.value > Decimal("5.0")

    def should_trigger(self, apy_change_percent: Decimal) -> bool:
        """
        Check if APY change exceeds this threshold.

        Args:
            apy_change_percent: Absolute value of APY change percentage

        Returns:
            True if change meets or exceeds threshold
        """
        return abs(apy_change_percent) >= self.value

    @property
    def sensitivity_level(self) -> str:
        """Get human-readable sensitivity level."""
        if self.is_very_sensitive:
            return "very_sensitive"
        elif self.is_sensitive:
            return "sensitive"
        elif self.is_normal:
            return "normal"
        elif self.is_relaxed:
            return "relaxed"
        else:
            return "very_relaxed"
