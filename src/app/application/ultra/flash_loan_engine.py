"""Flash Loan Engine for ULTRA Arbitrage Bot.

Implements multi-protocol flash loan support:
- Aave V3 flash loans
- Balancer flash loans
- Uniswap V3 flash swaps

Based on ULTRA Arbitrage Bot's flash loan module.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, UTC
from enum import Enum
from decimal import Decimal


class FlashLoanProtocol(str, Enum):
    """Flash loan protocol types."""

    AAVE_V3 = "aave_v3"
    BALANCER = "balancer"
    UNISWAP_V3 = "uniswap_v3"


class LoanStatus(str, Enum):
    """Flash loan execution status."""

    PENDING = "pending"
    SIMULATING = "simulating"
    EXECUTING = "executing"
    SUCCESS = "success"
    FAILED = "failed"
    REVERTED = "reverted"


@dataclass
class FlashLoanConfig:
    """Configuration for flash loan operations."""

    # Protocol fees (as decimal, e.g., 0.0009 = 0.09%)
    aave_v3_fee: Decimal = Decimal("0.0009")  # 0.09%
    balancer_fee: Decimal = Decimal("0.0000")  # 0% (gas only)
    uniswap_v3_fee: Decimal = Decimal("0.0000")  # 0% (gas only)

    # Gas limits
    max_gas_price_gwei: int = 100  # Max gas price
    gas_limit: int = 500000  # Gas limit per loan

    # Safety parameters
    min_profit_threshold: Decimal = Decimal("10.0")  # Min $10 profit
    max_loan_amount_usd: Decimal = Decimal("1000000")  # Max $1M loan
    slippage_tolerance: Decimal = Decimal("0.005")  # 0.5%

    # Execution
    enable_simulation: bool = True  # Simulate before execution
    enable_auto_execute: bool = False  # Manual approval by default


@dataclass
class FlashLoanRequest:
    """Flash loan request parameters."""

    protocol: FlashLoanProtocol
    token_address: str
    amount: Decimal
    receiver_address: str
    callback_data: bytes
    params: Optional[Dict] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "protocol": self.protocol.value,
            "token_address": self.token_address,
            "amount": str(self.amount),
            "receiver_address": self.receiver_address,
            "callback_data": self.callback_data.hex(),
            "params": self.params or {},
        }


@dataclass
class FlashLoanResult:
    """Flash loan execution result."""

    request: FlashLoanRequest
    status: LoanStatus
    tx_hash: Optional[str]
    gas_used: Optional[int]
    gas_price_gwei: Optional[int]
    profit_usd: Optional[Decimal]
    fees_paid: Decimal
    execution_time: datetime
    error_message: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "request": self.request.to_dict(),
            "status": self.status.value,
            "tx_hash": self.tx_hash,
            "gas_used": self.gas_used,
            "gas_price_gwei": self.gas_price_gwei,
            "profit_usd": str(self.profit_usd) if self.profit_usd else None,
            "fees_paid": str(self.fees_paid),
            "execution_time": self.execution_time.isoformat(),
            "error_message": self.error_message,
        }


@dataclass
class ProtocolInfo:
    """Flash loan protocol information."""

    protocol: FlashLoanProtocol
    name: str
    fee_percentage: Decimal
    max_loan_usd: Decimal
    supported_tokens: List[str]
    requires_collateral: bool

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "protocol": self.protocol.value,
            "name": self.name,
            "fee_percentage": float(self.fee_percentage * 100),  # As %
            "max_loan_usd": str(self.max_loan_usd),
            "supported_tokens": self.supported_tokens,
            "requires_collateral": self.requires_collateral,
        }


class FlashLoanEngine:
    """Flash loan execution engine.

    Supports multiple protocols with unified interface:
    - Aave V3: Standard flash loans with 0.09% fee
    - Balancer: Flash loans with no fee (gas only)
    - Uniswap V3: Flash swaps with no fee (gas only)
    """

    def __init__(self, config: FlashLoanConfig = None):
        """Initialize flash loan engine.

        Args:
            config: Flash loan configuration
        """
        self.config = config or FlashLoanConfig()
        self._protocols = self._initialize_protocols()

    def _initialize_protocols(self) -> Dict[FlashLoanProtocol, ProtocolInfo]:
        """Initialize protocol information."""
        return {
            FlashLoanProtocol.AAVE_V3: ProtocolInfo(
                protocol=FlashLoanProtocol.AAVE_V3,
                name="Aave V3",
                fee_percentage=self.config.aave_v3_fee,
                max_loan_usd=Decimal("10000000"),  # $10M
                supported_tokens=["USDC", "USDT", "DAI", "WETH", "WBTC"],
                requires_collateral=False,
            ),
            FlashLoanProtocol.BALANCER: ProtocolInfo(
                protocol=FlashLoanProtocol.BALANCER,
                name="Balancer",
                fee_percentage=self.config.balancer_fee,
                max_loan_usd=Decimal("5000000"),  # $5M
                supported_tokens=["USDC", "USDT", "DAI", "WETH"],
                requires_collateral=False,
            ),
            FlashLoanProtocol.UNISWAP_V3: ProtocolInfo(
                protocol=FlashLoanProtocol.UNISWAP_V3,
                name="Uniswap V3",
                fee_percentage=self.config.uniswap_v3_fee,
                max_loan_usd=Decimal("20000000"),  # $20M
                supported_tokens=["USDC", "USDT", "DAI", "WETH", "WBTC"],
                requires_collateral=False,
            ),
        }

    async def get_protocols(self) -> List[ProtocolInfo]:
        """Get available flash loan protocols.

        Returns:
            List of protocol information

        Example:
            >>> engine = FlashLoanEngine()
            >>> protocols = await engine.get_protocols()
            >>> for p in protocols:
            ...     print(f"{p.name}: {p.fee_percentage}% fee")
        """
        return list(self._protocols.values())

    async def get_best_protocol(
        self, token: str, amount_usd: Decimal
    ) -> Optional[FlashLoanProtocol]:
        """Get best protocol for loan.

        Selects protocol based on:
        1. Token support
        2. Lowest fees
        3. Sufficient liquidity

        Args:
            token: Token symbol
            amount_usd: Loan amount in USD

        Returns:
            Best protocol or None if unavailable

        Example:
            >>> engine = FlashLoanEngine()
            >>> protocol = await engine.get_best_protocol("USDC", Decimal("100000"))
            >>> print(protocol)  # BALANCER (no fee)
        """
        # Filter protocols that support token and amount
        candidates = []
        for protocol, info in self._protocols.items():
            if token in info.supported_tokens and amount_usd <= info.max_loan_usd:
                candidates.append((protocol, info))

        if not candidates:
            return None

        # Sort by fee (lowest first)
        candidates.sort(key=lambda x: x[1].fee_percentage)

        return candidates[0][0]

    async def calculate_fees(
        self, protocol: FlashLoanProtocol, amount_usd: Decimal
    ) -> Decimal:
        """Calculate flash loan fees.

        Args:
            protocol: Flash loan protocol
            amount_usd: Loan amount in USD

        Returns:
            Total fees in USD

        Example:
            >>> engine = FlashLoanEngine()
            >>> fees = await engine.calculate_fees(FlashLoanProtocol.AAVE_V3, Decimal("100000"))
            >>> print(fees)  # 90.0 (0.09% of $100k)
        """
        protocol_info = self._protocols[protocol]
        loan_fee = amount_usd * protocol_info.fee_percentage

        # Add estimated gas cost (simplified)
        gas_cost_usd = Decimal("5.0")  # ~$5 average

        return loan_fee + gas_cost_usd

    async def estimate_gas(
        self, protocol: FlashLoanProtocol, operation_complexity: int = 1
    ) -> Tuple[int, Decimal]:
        """Estimate gas usage and cost.

        Args:
            protocol: Flash loan protocol
            operation_complexity: Complexity multiplier (1-5)

        Returns:
            (gas_units, cost_usd)

        Example:
            >>> engine = FlashLoanEngine()
            >>> gas, cost = await engine.estimate_gas(FlashLoanProtocol.AAVE_V3, 2)
            >>> print(f"Gas: {gas}, Cost: ${cost}")
        """
        # Base gas estimates
        base_gas = {
            FlashLoanProtocol.AAVE_V3: 150000,
            FlashLoanProtocol.BALANCER: 120000,
            FlashLoanProtocol.UNISWAP_V3: 100000,
        }

        gas_units = base_gas[protocol] * operation_complexity
        gas_price_gwei = 30  # Assume 30 gwei
        gas_cost_eth = Decimal(gas_units * gas_price_gwei) / Decimal(1e9)
        gas_cost_usd = gas_cost_eth * Decimal("2000")  # Assume $2000 ETH

        return gas_units, gas_cost_usd

    async def validate_loan_request(
        self, request: FlashLoanRequest
    ) -> Tuple[bool, Optional[str]]:
        """Validate flash loan request.

        Args:
            request: Flash loan request

        Returns:
            (is_valid, error_message)

        Example:
            >>> engine = FlashLoanEngine()
            >>> request = FlashLoanRequest(...)
            >>> valid, error = await engine.validate_loan_request(request)
            >>> if not valid:
            ...     print(f"Invalid: {error}")
        """
        # Check protocol support
        if request.protocol not in self._protocols:
            return False, f"Unsupported protocol: {request.protocol}"

        protocol_info = self._protocols[request.protocol]

        # Check token support (simplified - would check token address)
        # In production, would validate actual token address

        # Check amount limits
        if request.amount <= 0:
            return False, "Amount must be positive"

        if request.amount > self.config.max_loan_amount_usd:
            return False, f"Amount exceeds max: ${self.config.max_loan_amount_usd}"

        # Check receiver address (42 chars with 0x prefix)
        if not request.receiver_address or not request.receiver_address.startswith("0x") or len(request.receiver_address) != 42:
            return False, "Invalid receiver address (must be 42 chars with 0x prefix)"

        return True, None

    async def simulate_loan(
        self, request: FlashLoanRequest
    ) -> FlashLoanResult:
        """Simulate flash loan execution.

        Args:
            request: Flash loan request

        Returns:
            Simulation result

        Example:
            >>> engine = FlashLoanEngine()
            >>> request = FlashLoanRequest(...)
            >>> result = await engine.simulate_loan(request)
            >>> if result.status == LoanStatus.SUCCESS:
            ...     print(f"Estimated profit: ${result.profit_usd}")
        """
        # Validate request
        is_valid, error = await self.validate_loan_request(request)
        if not is_valid:
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

        # Calculate fees
        fees = await self.calculate_fees(request.protocol, request.amount)

        # Estimate gas
        gas_units, gas_cost = await self.estimate_gas(request.protocol, 2)

        # Simulate profit (simplified - would run actual simulation)
        # Assume 0.5% profit on loan amount for simulation
        estimated_profit = request.amount * Decimal("0.005") - fees

        # Check profitability
        if estimated_profit < self.config.min_profit_threshold:
            return FlashLoanResult(
                request=request,
                status=LoanStatus.FAILED,
                tx_hash=None,
                gas_used=gas_units,
                gas_price_gwei=30,
                profit_usd=estimated_profit,
                fees_paid=fees,
                execution_time=datetime.now(UTC),
                error_message=f"Profit ${estimated_profit} below threshold ${self.config.min_profit_threshold}",
            )

        return FlashLoanResult(
            request=request,
            status=LoanStatus.SUCCESS,
            tx_hash="0xsimulated",
            gas_used=gas_units,
            gas_price_gwei=30,
            profit_usd=estimated_profit,
            fees_paid=fees,
            execution_time=datetime.now(UTC),
        )

    async def execute_loan(
        self, request: FlashLoanRequest, simulate_first: bool = True
    ) -> FlashLoanResult:
        """Execute flash loan.

        Args:
            request: Flash loan request
            simulate_first: Run simulation before execution

        Returns:
            Execution result

        Example:
            >>> engine = FlashLoanEngine()
            >>> request = FlashLoanRequest(...)
            >>> result = await engine.execute_loan(request)
            >>> if result.status == LoanStatus.SUCCESS:
            ...     print(f"TX: {result.tx_hash}, Profit: ${result.profit_usd}")
        """
        # Simulate first if enabled
        if simulate_first and self.config.enable_simulation:
            sim_result = await self.simulate_loan(request)
            if sim_result.status != LoanStatus.SUCCESS:
                return sim_result

        # In production, would execute actual blockchain transaction
        # For now, return simulated result with "real" tx hash
        result = await self.simulate_loan(request)
        if result.status == LoanStatus.SUCCESS:
            result.tx_hash = f"0x{'1234567890abcdef' * 4}"  # Mock tx hash

        return result

    async def execute_batch_loans(
        self, requests: List[FlashLoanRequest]
    ) -> List[FlashLoanResult]:
        """Execute multiple flash loans.

        Args:
            requests: List of flash loan requests

        Returns:
            List of execution results

        Example:
            >>> engine = FlashLoanEngine()
            >>> requests = [request1, request2, request3]
            >>> results = await engine.execute_batch_loans(requests)
            >>> successful = [r for r in results if r.status == LoanStatus.SUCCESS]
            >>> print(f"{len(successful)}/{len(results)} successful")
        """
        results = []
        for request in requests:
            result = await self.execute_loan(request)
            results.append(result)
        return results

    async def get_protocol_liquidity(
        self, protocol: FlashLoanProtocol, token: str
    ) -> Decimal:
        """Get available liquidity for protocol.

        Args:
            protocol: Flash loan protocol
            token: Token symbol

        Returns:
            Available liquidity in USD

        Example:
            >>> engine = FlashLoanEngine()
            >>> liquidity = await engine.get_protocol_liquidity(FlashLoanProtocol.AAVE_V3, "USDC")
            >>> print(f"Available: ${liquidity}")
        """
        # In production, would query actual protocol liquidity
        # For now, return mock data
        protocol_info = self._protocols[protocol]

        if token not in protocol_info.supported_tokens:
            return Decimal("0")

        # Mock liquidity (would be real-time in production)
        mock_liquidity = {
            (FlashLoanProtocol.AAVE_V3, "USDC"): Decimal("5000000"),
            (FlashLoanProtocol.BALANCER, "USDC"): Decimal("2000000"),
            (FlashLoanProtocol.UNISWAP_V3, "USDC"): Decimal("10000000"),
        }

        return mock_liquidity.get((protocol, token), Decimal("1000000"))

    def get_protocol_info(self, protocol: FlashLoanProtocol) -> ProtocolInfo:
        """Get protocol information.

        Args:
            protocol: Flash loan protocol

        Returns:
            Protocol information

        Example:
            >>> engine = FlashLoanEngine()
            >>> info = engine.get_protocol_info(FlashLoanProtocol.AAVE_V3)
            >>> print(f"{info.name}: {info.fee_percentage}% fee")
        """
        return self._protocols[protocol]
