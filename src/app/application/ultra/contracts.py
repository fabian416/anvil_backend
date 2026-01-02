"""Smart Contract ABIs and Addresses for ULTRA.

Contains contract addresses and ABIs for:
- Flash Loan protocols (Aave, Balancer, Uniswap)
- DEX routers (Uniswap, SushiSwap)
- Token contracts (ERC20)

These are used by FlashLoanEngine and ArbitrageExecutor
for real blockchain interactions.
"""

from enum import Enum

from app.infrastructure.adapters.external.web3_client import Chain


class ContractType(str, Enum):
    """Contract types."""

    AAVE_V3_POOL = "aave_v3_pool"
    BALANCER_VAULT = "balancer_vault"
    UNISWAP_V3_FACTORY = "uniswap_v3_factory"
    UNISWAP_V3_ROUTER = "uniswap_v3_router"
    SUSHISWAP_ROUTER = "sushiswap_router"


# =============================================================================
# Contract Addresses by Chain
# =============================================================================

CONTRACT_ADDRESSES: dict[Chain, dict[ContractType, str]] = {
    Chain.ETHEREUM: {
        ContractType.AAVE_V3_POOL: "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2",
        ContractType.BALANCER_VAULT: "0xBA12222222228d8Ba445958a75a0704d566BF2C8",
        ContractType.UNISWAP_V3_FACTORY: "0x1F98431c8aD98523631AE4a59f267346ea31F984",
        ContractType.UNISWAP_V3_ROUTER: "0xE592427A0AEce92De3Edee1F18E0157C05861564",
        ContractType.SUSHISWAP_ROUTER: "0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F",
    },
    Chain.ARBITRUM: {
        ContractType.AAVE_V3_POOL: "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
        ContractType.BALANCER_VAULT: "0xBA12222222228d8Ba445958a75a0704d566BF2C8",
        ContractType.UNISWAP_V3_FACTORY: "0x1F98431c8aD98523631AE4a59f267346ea31F984",
        ContractType.UNISWAP_V3_ROUTER: "0xE592427A0AEce92De3Edee1F18E0157C05861564",
        ContractType.SUSHISWAP_ROUTER: "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506",
    },
    Chain.OPTIMISM: {
        ContractType.AAVE_V3_POOL: "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
        ContractType.BALANCER_VAULT: "0xBA12222222228d8Ba445958a75a0704d566BF2C8",
        ContractType.UNISWAP_V3_FACTORY: "0x1F98431c8aD98523631AE4a59f267346ea31F984",
        ContractType.UNISWAP_V3_ROUTER: "0xE592427A0AEce92De3Edee1F18E0157C05861564",
        ContractType.SUSHISWAP_ROUTER: "0x0000000000000000000000000000000000000000",  # Not deployed
    },
    Chain.BASE: {
        ContractType.AAVE_V3_POOL: "0xA238Dd80C259a72e81d7e4664a9801593F98d1c5",
        ContractType.BALANCER_VAULT: "0xBA12222222228d8Ba445958a75a0704d566BF2C8",
        ContractType.UNISWAP_V3_FACTORY: "0x33128a8fC17869897dcE68Ed026d694621f6FDfD",
        ContractType.UNISWAP_V3_ROUTER: "0x2626664c2603336E57B271c5C0b26F421741e481",
        ContractType.SUSHISWAP_ROUTER: "0x0000000000000000000000000000000000000000",  # Not deployed
    },
    Chain.POLYGON: {
        ContractType.AAVE_V3_POOL: "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
        ContractType.BALANCER_VAULT: "0xBA12222222228d8Ba445958a75a0704d566BF2C8",
        ContractType.UNISWAP_V3_FACTORY: "0x1F98431c8aD98523631AE4a59f267346ea31F984",
        ContractType.UNISWAP_V3_ROUTER: "0xE592427A0AEce92De3Edee1F18E0157C05861564",
        ContractType.SUSHISWAP_ROUTER: "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506",
    },
}

# =============================================================================
# Token Addresses by Chain
# =============================================================================

TOKEN_ADDRESSES: dict[Chain, dict[str, str]] = {
    Chain.ETHEREUM: {
        "ETH": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
        "WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
        "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
        "DAI": "0x6B175474E89094C44Da98b954EecsdeC1b5AeD5f9",
        "WBTC": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
    },
    Chain.ARBITRUM: {
        "ETH": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
        "WETH": "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",
        "USDC": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",  # Native USDC
        "USDC.e": "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8",  # Bridged
        "USDT": "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9",
        "DAI": "0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1",
        "WBTC": "0x2f2a2543B76A4166549F7aaB2e75Bef0aefC5B0f",
    },
    Chain.OPTIMISM: {
        "ETH": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
        "WETH": "0x4200000000000000000000000000000000000006",
        "USDC": "0x0b2C639c533813f4Aa9D7837CAf62653d097Ff85",  # Native USDC
        "USDC.e": "0x7F5c764cBc14f9669B88837ca1490cCa17c31607",  # Bridged
        "USDT": "0x94b008aA00579c1307B0EF2c499aD98a8ce58e58",
        "DAI": "0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1",
        "WBTC": "0x68f180fcCe6836688e9084f035309E29Bf0A2095",
    },
    Chain.BASE: {
        "ETH": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
        "WETH": "0x4200000000000000000000000000000000000006",
        "USDC": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",  # Native USDC
        "USDbC": "0xd9aAEc86B65D86f6A7B5B1b0c42FFA531710b6CA",  # Bridged
        "DAI": "0x50c5725949A6F0c72E6C4a641F24049A917DB0Cb",
    },
    Chain.POLYGON: {
        "MATIC": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
        "WMATIC": "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270",
        "WETH": "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619",
        "USDC": "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359",  # Native USDC
        "USDC.e": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",  # Bridged
        "USDT": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",
        "DAI": "0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063",
        "WBTC": "0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6",
    },
}

# Token decimals
TOKEN_DECIMALS: dict[str, int] = {
    "ETH": 18,
    "WETH": 18,
    "MATIC": 18,
    "WMATIC": 18,
    "USDC": 6,
    "USDC.e": 6,
    "USDbC": 6,
    "USDT": 6,
    "DAI": 18,
    "WBTC": 8,
}

# =============================================================================
# Contract ABIs (Simplified - only essential functions)
# =============================================================================

# Aave V3 Pool - Flash Loan functions
AAVE_V3_POOL_ABI = [
    {
        "name": "flashLoan",
        "type": "function",
        "inputs": [
            {"name": "receiverAddress", "type": "address"},
            {"name": "assets", "type": "address[]"},
            {"name": "amounts", "type": "uint256[]"},
            {"name": "interestRateModes", "type": "uint256[]"},
            {"name": "onBehalfOf", "type": "address"},
            {"name": "params", "type": "bytes"},
            {"name": "referralCode", "type": "uint16"},
        ],
        "outputs": [],
    },
    {
        "name": "flashLoanSimple",
        "type": "function",
        "inputs": [
            {"name": "receiverAddress", "type": "address"},
            {"name": "asset", "type": "address"},
            {"name": "amount", "type": "uint256"},
            {"name": "params", "type": "bytes"},
            {"name": "referralCode", "type": "uint16"},
        ],
        "outputs": [],
    },
    {
        "name": "FLASHLOAN_PREMIUM_TOTAL",
        "type": "function",
        "inputs": [],
        "outputs": [{"name": "", "type": "uint128"}],
    },
]

# Balancer Vault - Flash Loan functions
BALANCER_VAULT_ABI = [
    {
        "name": "flashLoan",
        "type": "function",
        "inputs": [
            {"name": "recipient", "type": "address"},
            {"name": "tokens", "type": "address[]"},
            {"name": "amounts", "type": "uint256[]"},
            {"name": "userData", "type": "bytes"},
        ],
        "outputs": [],
    },
]

# Uniswap V3 Pool - Flash functions
UNISWAP_V3_POOL_ABI = [
    {
        "name": "flash",
        "type": "function",
        "inputs": [
            {"name": "recipient", "type": "address"},
            {"name": "amount0", "type": "uint256"},
            {"name": "amount1", "type": "uint256"},
            {"name": "data", "type": "bytes"},
        ],
        "outputs": [],
    },
]

# ERC20 Token ABI (essential functions)
ERC20_ABI = [
    {
        "name": "balanceOf",
        "type": "function",
        "inputs": [{"name": "account", "type": "address"}],
        "outputs": [{"name": "", "type": "uint256"}],
    },
    {
        "name": "transfer",
        "type": "function",
        "inputs": [
            {"name": "to", "type": "address"},
            {"name": "amount", "type": "uint256"},
        ],
        "outputs": [{"name": "", "type": "bool"}],
    },
    {
        "name": "approve",
        "type": "function",
        "inputs": [
            {"name": "spender", "type": "address"},
            {"name": "amount", "type": "uint256"},
        ],
        "outputs": [{"name": "", "type": "bool"}],
    },
    {
        "name": "allowance",
        "type": "function",
        "inputs": [
            {"name": "owner", "type": "address"},
            {"name": "spender", "type": "address"},
        ],
        "outputs": [{"name": "", "type": "uint256"}],
    },
    {
        "name": "decimals",
        "type": "function",
        "inputs": [],
        "outputs": [{"name": "", "type": "uint8"}],
    },
    {
        "name": "symbol",
        "type": "function",
        "inputs": [],
        "outputs": [{"name": "", "type": "string"}],
    },
]


# =============================================================================
# Helper Functions
# =============================================================================


def get_contract_address(chain: Chain, contract_type: ContractType) -> str | None:
    """Get contract address for chain."""
    chain_contracts = CONTRACT_ADDRESSES.get(chain, {})
    return chain_contracts.get(contract_type)


def get_token_address(chain: Chain, symbol: str) -> str | None:
    """Get token address for chain."""
    chain_tokens = TOKEN_ADDRESSES.get(chain, {})
    return chain_tokens.get(symbol)


def get_token_decimals(symbol: str) -> int:
    """Get token decimals."""
    # Remove chain suffix like .e
    base_symbol = symbol.split(".")[0]
    return TOKEN_DECIMALS.get(base_symbol, TOKEN_DECIMALS.get(symbol, 18))


def encode_function_call(function_name: str, params: list) -> str:
    """
    Encode a simple function call (for common cases).

    For complex encoding, use web3.py or eth-abi.

    Args:
        function_name: Function name
        params: Function parameters

    Returns:
        Hex-encoded function call
    """
    # This is a simplified encoder for common cases
    # For production, use proper ABI encoding
    from hashlib import sha3_256

    # Function selector (first 4 bytes of keccak256)
    selector = sha3_256(function_name.encode()).hexdigest()[:8]

    # Encode params (simplified - only handles addresses and uint256)
    encoded_params = ""
    for param in params:
        if isinstance(param, str) and param.startswith("0x"):
            # Address - pad to 32 bytes
            encoded_params += param[2:].lower().zfill(64)
        elif isinstance(param, int):
            # uint256 - pad to 32 bytes
            encoded_params += hex(param)[2:].zfill(64)

    return f"0x{selector}{encoded_params}"
