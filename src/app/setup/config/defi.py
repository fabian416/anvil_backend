"""
DeFi provider configuration.
"""

import os
from dataclasses import dataclass


@dataclass
class DeFiConfig:
    """Configuration for DeFi integrations."""
    
    # 1inch configuration
    oneinch_api_key: str = ""  # Optional - empty means use simulated data
    oneinch_chain_id: int = 1  # Ethereum mainnet
    
    # Hyperliquid configuration
    hyperliquid_testnet: bool = True
    
    # General settings
    default_slippage: float = 1.0  # 1%
    max_slippage: float = 5.0  # 5%
    
    # Rate limiting
    rate_limit_requests_per_minute: int = 60


def load_defi_config() -> DeFiConfig:
    """
    Load DeFi configuration from environment.
    
    Returns:
        DeFiConfig instance
    
    Raises:
        ValueError: If required configuration is missing
    """
    oneinch_api_key = os.getenv("ONEINCH_API_KEY", "")
    
    # Allow None/empty for optional usage (will use simulated data)
    # if not oneinch_api_key:
    #     raise ValueError(
    #         "ONEINCH_API_KEY environment variable is required. "
    #         "Get your API key from https://portal.1inch.dev/"
    #     )
    
    return DeFiConfig(
        oneinch_api_key=oneinch_api_key,
        oneinch_chain_id=int(os.getenv("ONEINCH_CHAIN_ID", "1")),
        hyperliquid_testnet=os.getenv("HYPERLIQUID_TESTNET", "true").lower() == "true",
        default_slippage=float(os.getenv("DEFAULT_SLIPPAGE", "1.0")),
        max_slippage=float(os.getenv("MAX_SLIPPAGE", "5.0")),
        rate_limit_requests_per_minute=int(os.getenv("RATE_LIMIT_RPM", "60")),
    )
