"""RPC Provider Configuration.

Configuration for blockchain RPC providers (Alchemy, Infura).
Used by Web3Client for blockchain interactions.
"""

from pydantic import BaseModel


class RPCSettings(BaseModel):
    """RPC provider settings."""

    # Alchemy (Primary)
    alchemy_api_key: str = ""
    alchemy_ethereum_url: str = ""
    alchemy_arbitrum_url: str = ""
    alchemy_optimism_url: str = ""
    alchemy_polygon_zkevm_url: str = ""
    alchemy_base_url: str = ""

    # Infura (Backup)
    infura_api_key: str = ""

    # Default chain
    default_chain: str = "ethereum"


class WalletSettings(BaseModel):
    """Wallet configuration for transaction signing."""

    # Private key (64 hex chars, no 0x prefix)
    private_key: str = ""

    # Public address
    address: str = ""

    # Deployed receiver contracts
    aave_receiver_ethereum: str = ""
    aave_receiver_arbitrum: str = ""
    balancer_receiver_ethereum: str = ""
    balancer_receiver_arbitrum: str = ""

    @property
    def is_configured(self) -> bool:
        """Check if wallet is configured."""
        return bool(self.private_key and self.address)

    @property
    def has_receivers(self) -> bool:
        """Check if any receiver contracts are deployed."""
        return bool(
            self.aave_receiver_ethereum
            or self.aave_receiver_arbitrum
            or self.balancer_receiver_ethereum
            or self.balancer_receiver_arbitrum
        )

    @property
    def has_alchemy(self) -> bool:
        """Check if Alchemy is configured."""
        return bool(self.alchemy_api_key)

    @property
    def has_infura(self) -> bool:
        """Check if Infura is configured."""
        return bool(self.infura_api_key)

    @property
    def is_configured(self) -> bool:
        """Check if any RPC provider is configured."""
        return self.has_alchemy or self.has_infura

    def get_ethereum_url(self) -> str | None:
        """Get Ethereum RPC URL."""
        if self.alchemy_ethereum_url:
            return self.alchemy_ethereum_url
        if self.alchemy_api_key:
            return f"https://eth-mainnet.g.alchemy.com/v2/{self.alchemy_api_key}"
        if self.infura_api_key:
            return f"https://mainnet.infura.io/v3/{self.infura_api_key}"
        return None

    def get_arbitrum_url(self) -> str | None:
        """Get Arbitrum RPC URL."""
        if self.alchemy_arbitrum_url:
            return self.alchemy_arbitrum_url
        if self.alchemy_api_key:
            return f"https://arb-mainnet.g.alchemy.com/v2/{self.alchemy_api_key}"
        if self.infura_api_key:
            return f"https://arbitrum-mainnet.infura.io/v3/{self.infura_api_key}"
        return None

    def get_base_url(self) -> str | None:
        """Get Base RPC URL."""
        if self.alchemy_base_url:
            return self.alchemy_base_url
        if self.alchemy_api_key:
            return f"https://base-mainnet.g.alchemy.com/v2/{self.alchemy_api_key}"
        if self.infura_api_key:
            return f"https://base-mainnet.infura.io/v3/{self.infura_api_key}"
        return None
