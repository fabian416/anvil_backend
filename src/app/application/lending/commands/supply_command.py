"""
Supply Command for Lending Operations.

Defines the command pattern for supply/deposit operations following CQRS principles.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional
from uuid import UUID


@dataclass(frozen=True)
class SupplyCommand:
    """
    Command to supply assets to a lending protocol.

    Following CQRS pattern, this is the immutable input contract for the
    supply use case. Commands represent user intent to modify state.

    Attributes:
        user_id: User's unique identifier (UUID)
        protocol: Lending protocol ("aave" or "morpho")
        asset: Asset symbol to supply (e.g., "USDC", "ETH", "WETH")
        amount: Amount in asset units (e.g., 1000.0 for 1000 USDC)
        chain: Blockchain network (ethereum, base, arbitrum, etc.)
        use_as_collateral: Whether to enable asset as collateral (default: True)
        vault_address: Morpho vault address (required for Morpho, optional for Aave)

    Example:
        >>> command = SupplyCommand(
        ...     user_id=UUID("..."),
        ...     protocol="aave",
        ...     asset="USDC",
        ...     amount=Decimal("1000.0"),
        ...     chain="ethereum",
        ...     use_as_collateral=True,
        ... )
    """

    user_id: UUID
    protocol: str  # "aave" or "morpho"
    asset: str
    amount: Decimal
    chain: str
    use_as_collateral: bool = True
    vault_address: Optional[str] = None

    def __post_init__(self) -> None:
        """
        Validate command invariants.

        Raises:
            ValueError: If command validation fails
        """
        # Validate amount
        if self.amount <= 0:
            raise ValueError(f"Amount must be positive, got: {self.amount}")

        # Validate protocol
        if self.protocol.lower() not in ("aave", "morpho"):
            raise ValueError(f"Unsupported protocol: {self.protocol}")

        # Validate asset symbol (basic check)
        if not self.asset or len(self.asset) < 2:
            raise ValueError(f"Invalid asset symbol: {self.asset}")

        # Morpho requires vault_address
        if self.protocol.lower() == "morpho" and not self.vault_address:
            raise ValueError("Morpho protocol requires vault_address")

        # Validate chain
        supported_chains = {
            "ethereum",
            "base",
            "arbitrum",
            "polygon",
            "optimism",
            "avalanche",
        }
        if self.chain.lower() not in supported_chains:
            raise ValueError(
                f"Unsupported chain: {self.chain}. Supported: {supported_chains}"
            )


@dataclass(frozen=True)
class SupplyResult:
    """
    Result of supply command execution.

    Contains transaction data for frontend execution via Privy signature flow.

    Attributes:
        transaction_hash: Transaction hash (None if awaiting signature)
        position_id: UUID of created/updated lending position
        apy: Current supply APY (annual percentage yield)
        execute_data: Transaction data for Privy SDK execution
        protocol: Protocol used (aave or morpho)
        asset: Asset supplied
        amount: Amount supplied
        chain: Blockchain network
        vault_name: Morpho vault name (if applicable)
        status: Transaction status ("awaiting_signature", "pending", "confirmed")
        message: Human-readable success message

    Example:
        >>> result = SupplyResult(
        ...     transaction_hash=None,
        ...     position_id=UUID("..."),
        ...     apy=Decimal("5.25"),
        ...     execute_data={
        ...         "action_type": "supply",
        ...         "provider": "aave",
        ...         "asset_address": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
        ...         "amount": "1000.00",
        ...     },
        ...     protocol="aave",
        ...     asset="USDC",
        ...     amount=Decimal("1000.0"),
        ...     chain="ethereum",
        ...     vault_name=None,
        ...     status="awaiting_signature",
        ...     message="Supply 1000.00 USDC to Aave on Ethereum at 5.25% APY",
        ... )
    """

    transaction_hash: Optional[str]
    position_id: UUID
    apy: Decimal
    execute_data: dict
    protocol: str
    asset: str
    amount: Decimal
    chain: str
    vault_name: Optional[str]
    status: str
    message: str

    def to_dict(self) -> dict:
        """
        Convert result to dictionary for JSON serialization.

        Returns:
            Dictionary representation of result
        """
        return {
            "transaction_hash": self.transaction_hash,
            "position_id": str(self.position_id),
            "apy": str(self.apy),
            "execute_data": self.execute_data,
            "protocol": self.protocol,
            "asset": self.asset,
            "amount": str(self.amount),
            "chain": self.chain,
            "vault_name": self.vault_name,
            "status": self.status,
            "message": self.message,
        }
