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
    infura_ethereum_url: str = ""
    infura_arbitrum_url: str = ""
    infura_optimism_url: str = ""
    infura_polygon_url: str = ""
    infura_base_url: str = ""

    # Default chain
    default_chain: str = "ethereum"

    @property
    def has_alchemy(self) -> bool:
        """Check if Alchemy is configured."""
        return bool(self.alchemy_api_key)

    @property
    def has_infura(self) -> bool:
        """Check if Infura is configured."""
        return bool(self.infura_api_key)

    def get_rpc_url(self, chain: str, provider: str = "auto") -> str:
        """Get RPC URL for a specific chain.

        Args:
            chain: Chain name (ethereum, arbitrum, optimism, polygon, base)
            provider: Provider preference (alchemy, infura, auto)

        Returns:
            RPC URL or empty string if not configured
        """
        # Chain to URL mapping
        alchemy_urls = {
            "ethereum": self.alchemy_ethereum_url,
            "arbitrum": self.alchemy_arbitrum_url,
            "optimism": self.alchemy_optimism_url,
            "base": self.alchemy_base_url,
            "polygon_zkevm": self.alchemy_polygon_zkevm_url,
        }
        infura_urls = {
            "ethereum": self.infura_ethereum_url,
            "arbitrum": self.infura_arbitrum_url,
            "optimism": self.infura_optimism_url,
            "polygon": self.infura_polygon_url,
            "base": self.infura_base_url,
        }

        if provider == "alchemy" and chain in alchemy_urls:
            return alchemy_urls[chain]
        if provider == "infura" and chain in infura_urls:
            return infura_urls[chain]

        # Auto: try Alchemy first, then Infura
        if chain in alchemy_urls and alchemy_urls[chain]:
            return alchemy_urls[chain]
        if chain in infura_urls and infura_urls[chain]:
            return infura_urls[chain]

        return ""


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
