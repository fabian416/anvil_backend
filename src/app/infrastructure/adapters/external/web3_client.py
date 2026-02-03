"""Web3 Client for Blockchain Interactions.

Provides connection to Ethereum and L2 networks via RPC providers:
- Alchemy (primary)
- Infura (backup)

Used by:
- Flash Loan Engine (execute flash loans)
- Arbitrage Discovery (get real-time prices)
- Transaction Execution (swap, transfer, etc.)
"""

import logging
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class Chain(str, Enum):
    """Supported blockchain networks."""

    ETHEREUM = "ethereum"
    ARBITRUM = "arbitrum"
    BASE = "base"
    OPTIMISM = "optimism"
    POLYGON = "polygon"
    POLYGON_ZKEVM = "polygon_zkevm"


# Chain IDs
CHAIN_IDS = {
    Chain.ETHEREUM: 1,
    Chain.ARBITRUM: 42161,
    Chain.BASE: 8453,
    Chain.OPTIMISM: 10,
    Chain.POLYGON: 137,
    Chain.POLYGON_ZKEVM: 1101,
}

# Native token symbols
NATIVE_TOKENS = {
    Chain.ETHEREUM: "ETH",
    Chain.ARBITRUM: "ETH",
    Chain.BASE: "ETH",
    Chain.OPTIMISM: "ETH",
    Chain.POLYGON: "MATIC",
    Chain.POLYGON_ZKEVM: "ETH",
}


@dataclass
class BlockInfo:
    """Blockchain block information."""

    number: int
    timestamp: int
    hash: str
    gas_limit: int
    gas_used: int
    base_fee_gwei: float | None = None


@dataclass
class GasPrice:
    """Current gas prices."""

    chain: Chain
    base_fee_gwei: float
    priority_fee_gwei: float
    max_fee_gwei: float
    estimated_cost_usd: float  # For a standard transfer


@dataclass
class TransactionReceipt:
    """Transaction receipt."""

    tx_hash: str
    status: bool  # True = success
    block_number: int
    gas_used: int
    effective_gas_price: int
    logs: list[dict]


class Web3Client:
    """
    Web3 client for blockchain interactions.

    Uses JSON-RPC to interact with Ethereum and L2 networks.
    Supports Alchemy (primary) and Infura (backup).

    Usage:
        client = Web3Client(
            alchemy_api_key="your-key",
            chain=Chain.ETHEREUM
        )
        block = await client.get_latest_block()
        print(f"Latest block: {block.number}")
    """

    # Alchemy RPC URLs
    ALCHEMY_URLS = {
        Chain.ETHEREUM: "https://eth-mainnet.g.alchemy.com/v2",
        Chain.ARBITRUM: "https://arb-mainnet.g.alchemy.com/v2",
        Chain.BASE: "https://base-mainnet.g.alchemy.com/v2",
        Chain.OPTIMISM: "https://opt-mainnet.g.alchemy.com/v2",
        Chain.POLYGON: "https://polygon-mainnet.g.alchemy.com/v2",
        Chain.POLYGON_ZKEVM: "https://polygonzkevm-mainnet.g.alchemy.com/v2",
    }

    # Infura RPC URLs (backup)
    INFURA_URLS = {
        Chain.ETHEREUM: "https://mainnet.infura.io/v3",
        Chain.ARBITRUM: "https://arbitrum-mainnet.infura.io/v3",
        Chain.BASE: "https://base-mainnet.infura.io/v3",
        Chain.OPTIMISM: "https://optimism-mainnet.infura.io/v3",
        Chain.POLYGON: "https://polygon-mainnet.infura.io/v3",
        Chain.POLYGON_ZKEVM: "https://polygon-zkevm-mainnet.infura.io/v3",
    }

    def __init__(
        self,
        alchemy_api_key: str | None = None,
        infura_api_key: str | None = None,
        chain: Chain = Chain.ETHEREUM,
        rpc_url: str | None = None,
    ):
        """
        Initialize Web3 client.

        Args:
            alchemy_api_key: Alchemy API key (primary)
            infura_api_key: Infura API key (backup)
            chain: Blockchain network
            rpc_url: Custom RPC URL (overrides alchemy/infura)
        """
        self._alchemy_key = alchemy_api_key
        self._infura_key = infura_api_key
        self._chain = chain
        self._custom_rpc = rpc_url
        self._request_id = 0
        self._client = httpx.AsyncClient(timeout=30.0)

    @property
    def rpc_url(self) -> str:
        """Get the RPC URL to use."""
        if self._custom_rpc:
            return self._custom_rpc

        if self._alchemy_key:
            base_url = self.ALCHEMY_URLS.get(self._chain)
            if base_url:
                return f"{base_url}/{self._alchemy_key}"

        if self._infura_key:
            base_url = self.INFURA_URLS.get(self._chain)
            if base_url:
                return f"{base_url}/{self._infura_key}"

        raise ValueError(
            f"No RPC provider configured for {self._chain}. "
            "Provide alchemy_api_key, infura_api_key, or rpc_url."
        )

    @property
    def chain_id(self) -> int:
        """Get current chain ID."""
        return CHAIN_IDS[self._chain]

    async def close(self):
        """Close HTTP client."""
        await self._client.aclose()

    async def _call_rpc(self, method: str, params: list | None = None) -> Any:
        """
        Make JSON-RPC call to blockchain node.

        Args:
            method: RPC method name
            params: Method parameters

        Returns:
            RPC result

        Raises:
            Exception: If RPC call fails
        """
        self._request_id += 1
        payload = {
            "jsonrpc": "2.0",
            "id": self._request_id,
            "method": method,
            "params": params or [],
        }

        response = await self._client.post(
            self.rpc_url,
            json=payload,
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()

        data = response.json()

        if "error" in data:
            error = data["error"]
            raise Exception(f"RPC Error: {error.get('message', error)}")

        return data.get("result")

    async def get_block_number(self) -> int:
        """
        Get latest block number.

        Returns:
            Current block number

        Example:
            >>> client = Web3Client(alchemy_api_key="...")
            >>> block_num = await client.get_block_number()
            >>> print(f"Current block: {block_num}")
        """
        result = await self._call_rpc("eth_blockNumber")
        return int(result, 16)

    async def get_latest_block(self) -> BlockInfo:
        """
        Get latest block information.

        Returns:
            BlockInfo with block details

        Example:
            >>> block = await client.get_latest_block()
            >>> print(f"Block {block.number}, gas: {block.gas_used}")
        """
        result = await self._call_rpc("eth_getBlockByNumber", ["latest", False])

        base_fee = None
        if "baseFeePerGas" in result:
            base_fee = int(result["baseFeePerGas"], 16) / 1e9  # Convert to Gwei

        return BlockInfo(
            number=int(result["number"], 16),
            timestamp=int(result["timestamp"], 16),
            hash=result["hash"],
            gas_limit=int(result["gasLimit"], 16),
            gas_used=int(result["gasUsed"], 16),
            base_fee_gwei=base_fee,
        )

    async def get_gas_price(self) -> GasPrice:
        """
        Get current gas prices.

        Returns:
            GasPrice with current gas estimates

        Example:
            >>> gas = await client.get_gas_price()
            >>> print(f"Base fee: {gas.base_fee_gwei} Gwei")
            >>> print(f"Estimated transfer cost: ${gas.estimated_cost_usd}")
        """
        # Get base fee from latest block
        block = await self.get_latest_block()
        base_fee = block.base_fee_gwei or 30.0  # Default if not available

        # Get priority fee (max priority fee per gas)
        priority_result = await self._call_rpc("eth_maxPriorityFeePerGas")
        priority_fee = int(priority_result, 16) / 1e9 if priority_result else 1.5

        # Calculate max fee (base + priority + buffer)
        max_fee = base_fee + priority_fee + 2.0

        # Estimate cost for standard transfer (21000 gas)
        gas_units = 21000
        gas_cost_eth = (max_fee * gas_units) / 1e9
        eth_price = 3000  # TODO: Get from price feed
        estimated_cost = gas_cost_eth * eth_price

        return GasPrice(
            chain=self._chain,
            base_fee_gwei=base_fee,
            priority_fee_gwei=priority_fee,
            max_fee_gwei=max_fee,
            estimated_cost_usd=estimated_cost,
        )

    async def get_balance(self, address: str) -> Decimal:
        """
        Get ETH balance of address.

        Args:
            address: Wallet address (0x...)

        Returns:
            Balance in ETH

        Example:
            >>> balance = await client.get_balance("0x...")
            >>> print(f"Balance: {balance} ETH")
        """
        result = await self._call_rpc("eth_getBalance", [address, "latest"])
        wei = int(result, 16)
        return Decimal(wei) / Decimal(10**18)

    async def get_token_balance(
        self,
        token_address: str,
        wallet_address: str,
        decimals: int = 18,
    ) -> Decimal:
        """
        Get ERC20 token balance.

        Args:
            token_address: Token contract address
            wallet_address: Wallet address
            decimals: Token decimals (default 18)

        Returns:
            Token balance

        Example:
            >>> usdc = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
            >>> balance = await client.get_token_balance(usdc, "0x...", 6)
            >>> print(f"USDC Balance: {balance}")
        """
        # ERC20 balanceOf(address) function selector
        # keccak256("balanceOf(address)")[:4] = 0x70a08231
        padded_address = wallet_address[2:].lower().zfill(64)
        data = f"0x70a08231{padded_address}"

        result = await self._call_rpc(
            "eth_call",
            [{"to": token_address, "data": data}, "latest"],
        )

        if result == "0x" or not result:
            return Decimal("0")

        balance_wei = int(result, 16)
        return Decimal(balance_wei) / Decimal(10**decimals)

    async def get_transaction_receipt(self, tx_hash: str) -> TransactionReceipt | None:
        """
        Get transaction receipt.

        Args:
            tx_hash: Transaction hash

        Returns:
            TransactionReceipt or None if not found

        Example:
            >>> receipt = await client.get_transaction_receipt("0x...")
            >>> if receipt and receipt.status:
            ...     print("Transaction successful!")
        """
        result = await self._call_rpc("eth_getTransactionReceipt", [tx_hash])

        if not result:
            return None

        return TransactionReceipt(
            tx_hash=result["transactionHash"],
            status=int(result["status"], 16) == 1,
            block_number=int(result["blockNumber"], 16),
            gas_used=int(result["gasUsed"], 16),
            effective_gas_price=int(result["effectiveGasPrice"], 16),
            logs=result.get("logs", []),
        )

    async def estimate_gas(
        self,
        to: str,
        data: str = "0x",
        value: int = 0,
        from_address: str | None = None,
    ) -> int:
        """
        Estimate gas for transaction.

        Args:
            to: Destination address
            data: Transaction data (hex)
            value: ETH value in wei
            from_address: Sender address (optional)

        Returns:
            Estimated gas units

        Example:
            >>> gas = await client.estimate_gas("0x...", "0x...")
            >>> print(f"Estimated gas: {gas}")
        """
        tx = {"to": to, "data": data, "value": hex(value)}
        if from_address:
            tx["from"] = from_address

        result = await self._call_rpc("eth_estimateGas", [tx])
        return int(result, 16)

    async def call_contract(
        self,
        contract_address: str,
        data: str,
        block: str = "latest",
    ) -> str:
        """
        Call contract (read-only).

        Args:
            contract_address: Contract address
            data: Encoded function call
            block: Block number or 'latest'

        Returns:
            Hex-encoded result

        Example:
            >>> result = await client.call_contract("0x...", "0x70a08231...")
            >>> balance = int(result, 16)
        """
        result = await self._call_rpc(
            "eth_call",
            [{"to": contract_address, "data": data}, block],
        )
        return result

    async def is_connected(self) -> bool:
        """
        Check if connected to blockchain.

        Returns:
            True if connected

        Example:
            >>> if await client.is_connected():
            ...     print("Connected to blockchain!")
        """
        try:
            await self.get_block_number()
            return True
        except Exception as e:
            logger.debug(f"Connection check failed: {e!s}")
            return False

    async def check_chain_available(self, chain: Chain) -> bool:
        """
        Check if a specific chain is available.

        Some chains may require additional Alchemy plan.

        Args:
            chain: Chain to check

        Returns:
            True if chain is accessible
        """
        temp_client = Web3Client(
            alchemy_api_key=self._alchemy_key,
            infura_api_key=self._infura_key,
            chain=chain,
        )
        try:
            connected = await temp_client.is_connected()
            return connected
        except Exception:
            return False
        finally:
            await temp_client.close()

    async def get_chain_info(self) -> dict:
        """
        Get chain information.

        Returns:
            Dict with chain details

        Example:
            >>> info = await client.get_chain_info()
            >>> print(f"Chain: {info['name']}, Block: {info['block_number']}")
        """
        block = await self.get_latest_block()
        gas = await self.get_gas_price()

        return {
            "chain": self._chain.value,
            "chain_id": self.chain_id,
            "native_token": NATIVE_TOKENS[self._chain],
            "block_number": block.number,
            "block_timestamp": block.timestamp,
            "gas_price_gwei": gas.max_fee_gwei,
            "is_eip1559": block.base_fee_gwei is not None,
        }

    async def is_contract(self, address: str) -> bool:
        """
        Check if an address is a smart contract or EOA (Externally Owned Account).

        Uses eth_getCode to check if there's bytecode at the address.
        - If code exists (not "0x" or "0x0"), it's a contract.
        - If no code, it's an EOA (regular wallet).

        Args:
            address: Ethereum address to check (0x...)

        Returns:
            True if contract, False if EOA

        Example:
            >>> is_contract = await client.is_contract("0x...")
            >>> if is_contract:
            ...     print("This is a smart contract!")
            ... else:
            ...     print("This is a regular wallet.")
        """
        try:
            result = await self._call_rpc("eth_getCode", [address, "latest"])
            # No code = EOA, has code = contract
            return result is not None and result not in ("0x", "0x0", "")
        except Exception as e:
            logger.warning(f"Failed to check if {address[:10]}... is contract: {e}")
            return False  # Assume EOA on error

    async def get_transaction_count(self, address: str) -> int:
        """
        Get the number of transactions sent from an address (nonce).

        Useful to check if an address has ever been used.

        Args:
            address: Ethereum address (0x...)

        Returns:
            Number of transactions sent from this address

        Example:
            >>> count = await client.get_transaction_count("0x...")
            >>> if count == 0:
            ...     print("This address has never sent a transaction!")
        """
        try:
            result = await self._call_rpc("eth_getTransactionCount", [address, "latest"])
            return int(result, 16)
        except Exception as e:
            logger.warning(f"Failed to get tx count for {address[:10]}...: {e}")
            return 0
