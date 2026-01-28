"""
Protocol ID value object for money market protocols.
"""

from dataclasses import dataclass

from app.domain.exceptions.base import DomainFieldError
from app.domain.value_objects.base import ValueObject


@dataclass(frozen=True, repr=False)
class ProtocolId(ValueObject[str]):
    """
    Protocol identifier value object with validation.

    Valid protocols: 'aave_v3', 'compound_v3'
    """

    value: str

    def __post_init__(self) -> None:
        """
        Validate protocol identifier.

        :raises DomainFieldError: If protocol is invalid
        """
        super().__post_init__()
        self._validate_protocol()

    def _validate_protocol(self) -> None:
        """Validate protocol is one of the supported values."""
        valid_protocols = ("aave_v3", "compound_v3")
        if self.value not in valid_protocols:
            raise DomainFieldError(
                f"Invalid protocol: {self.value}. "
                f"Must be one of {valid_protocols}."
            )

    @property
    def is_aave(self) -> bool:
        """Check if protocol is Aave V3."""
        return self.value == "aave_v3"

    @property
    def is_compound(self) -> bool:
        """Check if protocol is Compound V3."""
        return self.value == "compound_v3"

    @property
    def display_name(self) -> str:
        """Get human-readable protocol name."""
        display_names = {
            "aave_v3": "Aave V3",
            "compound_v3": "Compound V3",
        }
        return display_names.get(self.value, self.value)
