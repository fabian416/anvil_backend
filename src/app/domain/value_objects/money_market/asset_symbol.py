"""
Asset symbol value object for money market assets.
"""

from dataclasses import dataclass

from app.domain.exceptions.base import DomainFieldError
from app.domain.value_objects.base import ValueObject


@dataclass(frozen=True, repr=False)
class AssetSymbol(ValueObject[str]):
    """
    Asset symbol value object with validation.

    Requirements:
    - Must be uppercase
    - Must be 2-10 characters
    - No whitespace allowed
    """

    value: str

    def __post_init__(self) -> None:
        """
        Validate asset symbol.

        :raises DomainFieldError: If symbol is invalid
        """
        super().__post_init__()
        self._validate_format()
        self._validate_length()
        self._validate_uppercase()

    def _validate_format(self) -> None:
        """Validate symbol contains only alphanumeric characters."""
        if not self.value.isalnum():
            raise DomainFieldError(
                f"Asset symbol must be alphanumeric: {self.value}"
            )

    def _validate_length(self) -> None:
        """Validate symbol length (2-10 characters)."""
        if len(self.value) < 2:
            raise DomainFieldError(
                f"Asset symbol too short: {self.value}. Minimum 2 characters."
            )
        if len(self.value) > 10:
            raise DomainFieldError(
                f"Asset symbol too long: {self.value}. Maximum 10 characters."
            )

    def _validate_uppercase(self) -> None:
        """Validate symbol is uppercase."""
        if not self.value.isupper():
            raise DomainFieldError(
                f"Asset symbol must be uppercase: {self.value}"
            )

    @property
    def is_stablecoin(self) -> bool:
        """Check if asset is a common stablecoin."""
        stablecoins = ("USDC", "USDT", "DAI", "BUSD", "FRAX", "LUSD", "USDD")
        return self.value in stablecoins

    @property
    def is_eth(self) -> bool:
        """Check if asset is ETH or WETH."""
        return self.value in ("ETH", "WETH")

    @property
    def is_btc(self) -> bool:
        """Check if asset is BTC or WBTC."""
        return self.value in ("BTC", "WBTC")

    @property
    def is_wrapped_asset(self) -> bool:
        """Check if asset is a wrapped token."""
        return self.value.startswith("W")
