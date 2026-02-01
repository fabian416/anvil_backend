"""Etherscan API V2 Configuration.

Configuration for Etherscan block explorer API used for:
- ERC-20 token balance checking
- Transaction verification
- Contract interaction data

Etherscan V2 uses a single API key across 60+ EVM chains via chainid parameter.
Documentation: https://docs.etherscan.io/etherscan-v2
"""

from pydantic import BaseModel


class EtherscanSettings(BaseModel):
    """Etherscan API settings."""

    # API Key - single key works for all supported chains
    api_key: str = ""

    # Base URL for Etherscan V2 unified endpoint
    base_url: str = "https://api.etherscan.io/v2/api"

    # Rate limiting (free tier: 5 calls/sec, 100k calls/day)
    max_calls_per_second: int = 5
    max_calls_per_day: int = 100_000

    # Timeout for API requests (seconds)
    request_timeout: float = 15.0

    # Retry configuration
    max_retries: int = 3
    retry_backoff_base: float = 2.0  # Exponential backoff: 2^attempt seconds
    retry_backoff_max: float = 60.0  # Cap backoff at 60 seconds

    # Balance sync configuration
    balance_check_interval_seconds: int = 300  # 5 minutes between checks per wallet
    max_wallets_per_batch: int = 20  # Max wallets per periodic run
    high_value_threshold_usd: float = 10_000.0  # Threshold for priority queue
    high_value_check_interval_seconds: int = 120  # 2 minutes for high-value wallets

    # Anomaly detection thresholds
    anomaly_pct_change_threshold: float = 50.0  # Alert if balance changes >50%
    anomaly_absolute_threshold_usd: float = 1_000.0  # Alert if change >$1000

    # Supported chain IDs (Etherscan V2 chainid parameter)
    # Maps chain name -> Etherscan chain ID
    CHAIN_IDS: dict[str, int] = {
        "ethereum": 1,
        "base": 8453,
        "arbitrum": 42161,
        "polygon": 137,
        "optimism": 10,
        "avalanche": 43114,
        "bsc": 56,
    }

    # Common token contracts per chain (address -> (symbol, decimals))
    # Populated at runtime from database or config
    TOKEN_CONTRACTS: dict[str, dict[str, tuple[str, int]]] = {
        "ethereum": {
            "0xdAC17F958D2ee523a2206206994597C13D831ec7": ("USDT", 6),
            "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48": ("USDC", 6),
            "0x6B175474E89094C44Da98b954EedeAC495271d0F": ("DAI", 18),
        },
        "base": {
            "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913": ("USDC", 6),
            "0x50c5725949A6F0c72E6C4a641F24049A917DB0Cb": ("DAI", 18),
        },
        "arbitrum": {
            "0xaf88d065e77c8cC2239327C5EDb3A432268e5831": ("USDC", 6),
            "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9": ("USDT", 6),
            "0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1": ("DAI", 18),
        },
    }

    @property
    def is_configured(self) -> bool:
        """Check if Etherscan API key is set."""
        return bool(self.api_key)

    def get_chain_id(self, chain: str) -> int | None:
        """Get Etherscan chain ID for a chain name."""
        return self.CHAIN_IDS.get(chain.lower())
