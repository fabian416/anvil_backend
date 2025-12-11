from enum import Enum


class ChainType(Enum):
    ARBITRUM = "arbitrum"
    BASE = "base"
    ETHEREUM = "ethereum"
    POLYGON = "polygon"
    OPTIMISM = "optimism"
    HYPERLIQUID = "hyperliquid"
    # Bitcoin networks
    BITCOIN = "bitcoin"
    BITCOIN_TESTNET = "bitcoin_testnet"
