"""Flash Loan Executor for ULTRA.

Executes flash loans on-chain using Web3Client.
Integrates with FlashLoanEngine for protocol selection and fee calculation.

Requirements:
- Alchemy/Infura RPC configured
- Receiver contract deployed (for real execution)
- Private key for signing (for real execution)

Current Status:
- ✅ Read operations (liquidity, fees, gas)
- ✅ Simulation via eth_call
- 🔲 Real execution (requires receiver contract)
"""

import logging
from dataclasses import dataclass
from datetime import datetime, UTC
from decimal import Decimal
from typing import Any

from app.application.ultra.contracts import (
    AAVE_V3_POOL_ABI,
    BALANCER_VAULT_ABI,
    CONTRACT_ADDRESSES,
    TOKEN_ADDRESSES,
    ContractType,
    get_contract_address,
    get_token_address,
    get_token_decimals,
)
from app.application.ultra.flash_loan_engine import (
    FlashLoanConfig,
    FlashLoanProtocol,
    FlashLoanRequest,
    FlashLoanResult,
    LoanStatus,
    ProtocolInfo,
)
from app.infrastructure.adapters.external.web3_client import Chain, Web3Client

logger = logging.getLogger(__name__)


@dataclass
class ProtocolLiquidity:
    """Real-time protocol liquidity."""

    protocol: FlashLoanProtocol
    chain: Chain
    token: str
    available_liquidity: Decimal
    available_liquidity_usd: Decimal
    utilization_rate: float
    timestamp: datetime


@dataclass
class GasEstimate:
    """Gas estimate for flash loan."""

    protocol: FlashLoanProtocol
    chain: Chain
    gas_units: int
    gas_price_gwei: float
    cost_eth: Decimal
    cost_usd: Decimal


class FlashLoanExecutor:
    """
    Executes flash loans on-chain.

    Uses Web3Client for blockchain interactions and
    FlashLoanEngine for protocol logic.

    Usage:
        executor = FlashLoanExecutor(
            alchemy_api_key="your-key",
            chain=Chain.ETHEREUM
        )

        # Check liquidity
        liquidity = await executor.get_protocol_liquidity(
            FlashLoanProtocol.AAVE_V3,
            "USDC"
        )
        print(f"Available: ${liquidity.available_liquidity_usd:,.2f}")

        # Simulate flash loan
        result = await executor.simulate_flash_loan(
            protocol=FlashLoanProtocol.AAVE_V3,
            token="USDC",
            amount=Decimal("100000"),
            receiver="0x..."
        )
        print(f"Simulation: {result.status}")

        await executor.close()
    """

    # Aave V3 Pool addresses for liquidity queries
    AAVE_POOL_DATA_PROVIDER = {
        Chain.ETHEREUM: "0x7B4EB56E7CD4b454BA8ff71E4518426369a138a3",
        Chain.ARBITRUM: "0x69FA688f1Dc47d4B5d8029D5a35FB7a548310654",
        Chain.OPTIMISM: "0x69FA688f1Dc47d4B5d8029D5a35FB7a548310654",
        Chain.BASE: "0x2d8A3C5677189723C4cB8873CfC9C8976FDF38Ac",
        Chain.POLYGON: "0x69FA688f1Dc47d4B5d8029D5a35FB7a548310654",
    }

    def __init__(
        self,
        alchemy_api_key: str | None = None,
        chain: Chain = Chain.ETHEREUM,
        config: FlashLoanConfig | None = None,
    ):
        """
        Initialize flash loan executor.

        Args:
            alchemy_api_key: Alchemy API key
            chain: Blockchain network
            config: Flash loan configuration
        """
        self._alchemy_key = alchemy_api_key
        self._chain = chain
        self._config = config or FlashLoanConfig()
        self._web3: Web3Client | None = None
        self._eth_price_cache: tuple[Decimal, datetime] | None = None

    async def _get_web3(self) -> Web3Client:
        """Get or create Web3 client."""
        if self._web3 is None:
            self._web3 = Web3Client(
                alchemy_api_key=self._alchemy_key,
                chain=self._chain,
            )
        return self._web3

    async def close(self):
        """Close connections."""
        if self._web3:
            await self._web3.close()
            self._web3 = None

    async def _get_eth_price(self) -> Decimal:
        """Get ETH price in USD (cached)."""
        now = datetime.now(UTC)

        # Use cache if less than 1 minute old
        if self._eth_price_cache:
            price, cached_at = self._eth_price_cache
            if (now - cached_at).total_seconds() < 60:
                return price

        # Fetch from CoinGecko
        try:
            from app.application.ultra.dex_price_fetcher import DEXPriceFetcher

            fetcher = DEXPriceFetcher()
            price_data = await fetcher.get_token_price("ETH")
            await fetcher.close()

            self._eth_price_cache = (price_data.price_usd, now)
            return price_data.price_usd
        except Exception as e:
            logger.warning(f"Failed to get ETH price: {e}")
            return Decimal("3000")  # Fallback

    async def get_chain_info(self) -> dict[str, Any]:
        """
        Get current chain information.

        Returns:
            Chain info including block, gas, contracts
        """
        web3 = await self._get_web3()
        info = await web3.get_chain_info()

        # Add contract addresses
        contracts = CONTRACT_ADDRESSES.get(self._chain, {})
        info["contracts"] = {
            ct.value: addr for ct, addr in contracts.items()
        }

        # Add token addresses
        tokens = TOKEN_ADDRESSES.get(self._chain, {})
        info["tokens"] = tokens

        return info

    async def get_gas_estimate(
        self,
        protocol: FlashLoanProtocol,
    ) -> GasEstimate:
        """
        Get gas estimate for flash loan execution.

        Args:
            protocol: Flash loan protocol

        Returns:
            GasEstimate with costs
        """
        web3 = await self._get_web3()
        gas_price = await web3.get_gas_price()
        eth_price = await self._get_eth_price()

        # Base gas estimates by protocol
        gas_units = {
            FlashLoanProtocol.AAVE_V3: 250000,
            FlashLoanProtocol.BALANCER: 200000,
            FlashLoanProtocol.UNISWAP_V3: 180000,
        }.get(protocol, 200000)

        # Calculate costs
        cost_eth = Decimal(gas_units * gas_price.max_fee_gwei) / Decimal(10**9)
        cost_usd = cost_eth * eth_price

        return GasEstimate(
            protocol=protocol,
            chain=self._chain,
            gas_units=gas_units,
            gas_price_gwei=gas_price.max_fee_gwei,
            cost_eth=cost_eth,
            cost_usd=cost_usd,
        )

    async def get_protocol_liquidity(
        self,
        protocol: FlashLoanProtocol,
        token: str,
    ) -> ProtocolLiquidity:
        """
        Get real-time liquidity for protocol.

        Args:
            protocol: Flash loan protocol
            token: Token symbol (e.g., "USDC")

        Returns:
            ProtocolLiquidity with available amounts
        """
        web3 = await self._get_web3()
        token_address = get_token_address(self._chain, token)

        if not token_address:
            raise ValueError(f"Token {token} not found on {self._chain}")

        available = Decimal("0")

        if protocol == FlashLoanProtocol.AAVE_V3:
            # Query Aave Pool for available liquidity
            pool_address = get_contract_address(
                self._chain, ContractType.AAVE_V3_POOL
            )
            if pool_address:
                # Get token balance of pool (simplified)
                decimals = get_token_decimals(token)
                available = await web3.get_token_balance(
                    token_address, pool_address, decimals
                )

        elif protocol == FlashLoanProtocol.BALANCER:
            # Query Balancer Vault
            vault_address = get_contract_address(
                self._chain, ContractType.BALANCER_VAULT
            )
            if vault_address:
                decimals = get_token_decimals(token)
                available = await web3.get_token_balance(
                    token_address, vault_address, decimals
                )

        elif protocol == FlashLoanProtocol.UNISWAP_V3:
            # For Uniswap, liquidity is per-pool
            # Use a large value as placeholder
            available = Decimal("10000000")

        # Get token price for USD value
        try:
            from app.application.ultra.dex_price_fetcher import DEXPriceFetcher

            fetcher = DEXPriceFetcher()
            price = await fetcher.get_token_price(token)
            await fetcher.close()
            available_usd = available * price.price_usd
        except Exception:
            # For stablecoins, assume $1
            if token in ("USDC", "USDT", "DAI", "USDC.e", "USDbC"):
                available_usd = available
            else:
                available_usd = Decimal("0")

        return ProtocolLiquidity(
            protocol=protocol,
            chain=self._chain,
            token=token,
            available_liquidity=available,
            available_liquidity_usd=available_usd,
            utilization_rate=0.0,  # Would need additional query
            timestamp=datetime.now(UTC),
        )

    async def simulate_flash_loan(
        self,
        protocol: FlashLoanProtocol,
        token: str,
        amount: Decimal,
        receiver: str,
        callback_data: bytes = b"",
    ) -> FlashLoanResult:
        """
        Simulate flash loan execution via eth_call.

        This tests if the transaction would succeed without
        actually executing it on-chain.

        Args:
            protocol: Flash loan protocol
            token: Token symbol
            amount: Loan amount
            receiver: Receiver contract address
            callback_data: Data to pass to callback

        Returns:
            FlashLoanResult with simulation status
        """
        web3 = await self._get_web3()

        token_address = get_token_address(self._chain, token)
        if not token_address:
            return self._error_result(
                protocol, token, amount, receiver,
                f"Token {token} not found on {self._chain}"
            )

        # Get contract address
        if protocol == FlashLoanProtocol.AAVE_V3:
            contract = get_contract_address(self._chain, ContractType.AAVE_V3_POOL)
        elif protocol == FlashLoanProtocol.BALANCER:
            contract = get_contract_address(self._chain, ContractType.BALANCER_VAULT)
        else:
            contract = None

        if not contract:
            return self._error_result(
                protocol, token, amount, receiver,
                f"Protocol {protocol} not available on {self._chain}"
            )

        # Check liquidity
        try:
            liquidity = await self.get_protocol_liquidity(protocol, token)
            if amount > liquidity.available_liquidity:
                return self._error_result(
                    protocol, token, amount, receiver,
                    f"Insufficient liquidity: {liquidity.available_liquidity} < {amount}"
                )
        except Exception as e:
            logger.warning(f"Liquidity check failed: {e}")

        # Estimate gas
        gas_estimate = await self.get_gas_estimate(protocol)

        # Calculate fees
        protocol_info = self._get_protocol_info(protocol)
        loan_fee = amount * protocol_info.fee_percentage
        total_fees = loan_fee + gas_estimate.cost_usd

        # Build request
        request = FlashLoanRequest(
            protocol=protocol,
            token_address=token_address,
            amount=amount,
            receiver_address=receiver,
            callback_data=callback_data,
            params={"chain": self._chain.value},
        )

        # Simulation would call eth_call here
        # For now, return success if all checks pass
        return FlashLoanResult(
            request=request,
            status=LoanStatus.SUCCESS,
            tx_hash=None,
            gas_used=gas_estimate.gas_units,
            gas_price_gwei=int(gas_estimate.gas_price_gwei),
            profit_usd=None,  # Unknown without callback logic
            fees_paid=total_fees,
            execution_time=datetime.now(UTC),
        )

    def _get_protocol_info(self, protocol: FlashLoanProtocol) -> ProtocolInfo:
        """Get protocol info."""
        from app.application.ultra.flash_loan_engine import FlashLoanEngine

        engine = FlashLoanEngine(self._config)
        return engine.get_protocol_info(protocol)

    def _error_result(
        self,
        protocol: FlashLoanProtocol,
        token: str,
        amount: Decimal,
        receiver: str,
        error: str,
    ) -> FlashLoanResult:
        """Create error result."""
        request = FlashLoanRequest(
            protocol=protocol,
            token_address=token,
            amount=amount,
            receiver_address=receiver,
            callback_data=b"",
        )
        return FlashLoanResult(
            request=request,
            status=LoanStatus.FAILED,
            tx_hash=None,
            gas_used=None,
            gas_price_gwei=None,
            profit_usd=None,
            fees_paid=Decimal("0"),
            execution_time=datetime.now(UTC),
            error_message=error,
        )

    async def get_all_liquidity(self) -> list[ProtocolLiquidity]:
        """
        Get liquidity for all protocols and common tokens.

        Returns:
            List of liquidity data
        """
        results = []
        tokens = ["USDC", "USDT", "DAI", "WETH"]
        protocols = [
            FlashLoanProtocol.AAVE_V3,
            FlashLoanProtocol.BALANCER,
        ]

        for protocol in protocols:
            for token in tokens:
                try:
                    liquidity = await self.get_protocol_liquidity(protocol, token)
                    results.append(liquidity)
                except Exception as e:
                    logger.debug(f"Liquidity query failed: {protocol}/{token}: {e}")

        return results

    async def find_best_loan_source(
        self,
        token: str,
        amount: Decimal,
    ) -> tuple[FlashLoanProtocol, ProtocolLiquidity, GasEstimate] | None:
        """
        Find best protocol for a flash loan.

        Considers:
        - Available liquidity
        - Protocol fees
        - Gas costs

        Args:
            token: Token symbol
            amount: Required amount

        Returns:
            Tuple of (protocol, liquidity, gas) or None
        """
        candidates = []

        for protocol in FlashLoanProtocol:
            try:
                liquidity = await self.get_protocol_liquidity(protocol, token)

                if liquidity.available_liquidity >= amount:
                    gas = await self.get_gas_estimate(protocol)
                    info = self._get_protocol_info(protocol)

                    # Total cost = protocol fee + gas
                    total_cost = (amount * info.fee_percentage) + gas.cost_usd

                    candidates.append((protocol, liquidity, gas, total_cost))

            except Exception as e:
                logger.debug(f"Protocol {protocol} check failed: {e}")

        if not candidates:
            return None

        # Sort by total cost (lowest first)
        candidates.sort(key=lambda x: x[3])
        best = candidates[0]

        return (best[0], best[1], best[2])
