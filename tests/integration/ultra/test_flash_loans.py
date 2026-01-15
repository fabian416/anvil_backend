"""Integration tests for Flash Loan Engine (Phase 8 Week 1).

Tests flash loan protocols, simulation, and execution.
"""

import pytest
from decimal import Decimal

from app.application.ultra.flash_loan_engine import (
    FlashLoanEngine,
    FlashLoanConfig,
    FlashLoanProtocol,
    FlashLoanRequest,
    LoanStatus,
)


class TestFlashLoanConfig:
    """Test flash loan configuration."""

    def test_config_defaults(self):
        """Test default configuration values."""
        config = FlashLoanConfig()

        assert config.aave_v3_fee == Decimal("0.0009")
        assert config.balancer_fee == Decimal("0.0000")
        assert config.uniswap_v3_fee == Decimal("0.0000")
        assert config.min_profit_threshold == Decimal("10.0")


class TestProtocolInfo:
    """Test protocol information."""

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_get_protocols(self):
        """Test getting available protocols."""
        engine = FlashLoanEngine()

        protocols = await engine.get_protocols()

        assert len(protocols) == 3
        protocol_names = [p.protocol for p in protocols]
        assert FlashLoanProtocol.AAVE_V3 in protocol_names
        assert FlashLoanProtocol.BALANCER in protocol_names
        assert FlashLoanProtocol.UNISWAP_V3 in protocol_names

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_get_protocols",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate information about Aave protocol. Response must explain what the protocol does, its key features, and relevant DeFi concepts in an accessible way."
                ),
                additional_context={'test_category': 'defi_protocol', 'protocol': 'Aave'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))


    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_protocol_fees(self):
        """Test protocol fee structures."""
        engine = FlashLoanEngine()

        protocols = await engine.get_protocols()

        # Aave V3 has fee
        aave = [p for p in protocols if p.protocol == FlashLoanProtocol.AAVE_V3][0]
        assert aave.fee_percentage == Decimal("0.0009")

        # Balancer has no fee
        balancer = [p for p in protocols if p.protocol == FlashLoanProtocol.BALANCER][0]
        assert balancer.fee_percentage == Decimal("0.0000")

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_protocol_fees",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate information about Aave protocol. Response must explain what the protocol does, its key features, and relevant DeFi concepts in an accessible way."
                ),
                additional_context={'test_category': 'defi_protocol', 'protocol': 'Aave'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))


    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_protocol_max_loans(self):
        """Test protocol maximum loan amounts."""
        engine = FlashLoanEngine()

        protocols = await engine.get_protocols()

        for protocol in protocols:
            assert protocol.max_loan_usd > 0

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_protocol_max_loans",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate information about DeFi protocol. Response must explain what the protocol does, its key features, and relevant DeFi concepts in an accessible way."
                ),
                additional_context={'test_category': 'defi_protocol', 'protocol': 'DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))



class TestBestProtocolSelection:
    """Test best protocol selection logic."""

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_get_best_protocol_usdc(self):
        """Test best protocol for USDC loan."""
        engine = FlashLoanEngine()

        # Balancer should be best (no fee)
        protocol = await engine.get_best_protocol("USDC", Decimal("100000"))

        assert protocol == FlashLoanProtocol.BALANCER

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_get_best_protocol_usdc",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate information about DeFi protocol. Response must explain what the protocol does, its key features, and relevant DeFi concepts in an accessible way."
                ),
                additional_context={'test_category': 'defi_protocol', 'protocol': 'DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))


    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_get_best_protocol_unsupported_token(self):
        """Test best protocol for unsupported token."""
        engine = FlashLoanEngine()

        protocol = await engine.get_best_protocol("UNKNOWN", Decimal("100000"))

        assert protocol is None

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_get_best_protocol_unsupported_token",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate information about DeFi protocol. Response must explain what the protocol does, its key features, and relevant DeFi concepts in an accessible way."
                ),
                additional_context={'test_category': 'defi_protocol', 'protocol': 'DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))


    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_get_best_protocol_large_amount(self):
        """Test best protocol for large loan."""
        engine = FlashLoanEngine()

        # $15M exceeds Balancer max ($5M), should return Uniswap V3
        protocol = await engine.get_best_protocol("USDC", Decimal("15000000"))

        assert protocol == FlashLoanProtocol.UNISWAP_V3

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_get_best_protocol_large_amount",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate information about Uniswap protocol. Response must explain what the protocol does, its key features, and relevant DeFi concepts in an accessible way."
                ),
                additional_context={'test_category': 'defi_protocol', 'protocol': 'Uniswap'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))



class TestFeeCalculation:
    """Test fee calculation."""

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_calculate_fees_aave(self):
        """Test Aave V3 fee calculation."""
        engine = FlashLoanEngine()

        fees = await engine.calculate_fees(FlashLoanProtocol.AAVE_V3, Decimal("100000"))

        # 0.09% of $100k = $90 + ~$5 gas = ~$95
        assert fees >= Decimal("90")
        assert fees <= Decimal("100")

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_calculate_fees_aave",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate information about Aave protocol. Response must explain what the protocol does, its key features, and relevant DeFi concepts in an accessible way."
                ),
                additional_context={'test_category': 'defi_protocol', 'protocol': 'Aave'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))


    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_calculate_fees_balancer(self):
        """Test Balancer fee calculation (gas only)."""
        engine = FlashLoanEngine()

        fees = await engine.calculate_fees(FlashLoanProtocol.BALANCER, Decimal("100000"))

        # Only gas cost (~$5)
        assert fees <= Decimal("10")

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_calculate_fees_balancer",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))



class TestGasEstimation:
    """Test gas estimation."""

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_estimate_gas_simple(self):
        """Test gas estimation for simple operation."""
        engine = FlashLoanEngine()

        gas_units, gas_cost = await engine.estimate_gas(FlashLoanProtocol.AAVE_V3, 1)

        assert gas_units > 0
        assert gas_cost > 0

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_estimate_gas_simple",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))


    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_estimate_gas_complex(self):
        """Test gas estimation scales with complexity."""
        engine = FlashLoanEngine()

        gas1, cost1 = await engine.estimate_gas(FlashLoanProtocol.AAVE_V3, 1)
        gas3, cost3 = await engine.estimate_gas(FlashLoanProtocol.AAVE_V3, 3)

        # Gas should scale with complexity
        assert gas3 > gas1
        assert cost3 > cost1

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_estimate_gas_complex",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))



class TestLoanValidation:
    """Test loan request validation."""

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_validate_valid_request(self):
        """Test validation of valid request."""
        engine = FlashLoanEngine()

        request = FlashLoanRequest(
            protocol=FlashLoanProtocol.BALANCER,
            token_address="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
            amount=Decimal("100000"),
            receiver_address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0",
            callback_data=b"",
        )

        is_valid, error = await engine.validate_loan_request(request)

        assert is_valid is True
        assert error is None

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_validate_valid_request",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))


    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_validate_negative_amount(self):
        """Test validation rejects negative amount."""
        engine = FlashLoanEngine()

        request = FlashLoanRequest(
            protocol=FlashLoanProtocol.BALANCER,
            token_address="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
            amount=Decimal("-100"),
            receiver_address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0",
            callback_data=b"",
        )

        is_valid, error = await engine.validate_loan_request(request)

        assert is_valid is False
        assert "positive" in error.lower()

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_validate_negative_amount",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))


    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_validate_excessive_amount(self):
        """Test validation rejects excessive amount."""
        engine = FlashLoanEngine()

        request = FlashLoanRequest(
            protocol=FlashLoanProtocol.BALANCER,
            token_address="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
            amount=Decimal("10000000"),  # $10M exceeds config max
            receiver_address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0",
            callback_data=b"",
        )

        is_valid, error = await engine.validate_loan_request(request)

        assert is_valid is False
        assert "exceeds" in error.lower()

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_validate_excessive_amount",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))



class TestLoanSimulation:
    """Test loan simulation."""

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_simulate_profitable_loan(self):
        """Test simulation of profitable loan."""
        engine = FlashLoanEngine()

        request = FlashLoanRequest(
            protocol=FlashLoanProtocol.BALANCER,
            token_address="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
            amount=Decimal("100000"),
            receiver_address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0",
            callback_data=b"",
        )

        result = await engine.simulate_loan(request)

        assert result.status == LoanStatus.SUCCESS
        assert result.profit_usd > 0
        assert result.gas_used > 0

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_simulate_profitable_loan",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))


    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_simulate_unprofitable_loan(self):
        """Test simulation of unprofitable loan."""
        config = FlashLoanConfig(min_profit_threshold=Decimal("1000"))
        engine = FlashLoanEngine(config)

        request = FlashLoanRequest(
            protocol=FlashLoanProtocol.BALANCER,
            token_address="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
            amount=Decimal("1000"),  # Small amount = low profit
            receiver_address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0",
            callback_data=b"",
        )

        result = await engine.simulate_loan(request)

        assert result.status == LoanStatus.FAILED
        assert "threshold" in result.error_message.lower()

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_simulate_unprofitable_loan",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))



class TestLoanExecution:
    """Test loan execution."""

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_execute_loan(self):
        """Test loan execution."""
        engine = FlashLoanEngine()

        request = FlashLoanRequest(
            protocol=FlashLoanProtocol.BALANCER,
            token_address="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
            amount=Decimal("100000"),
            receiver_address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0",
            callback_data=b"",
        )

        result = await engine.execute_loan(request)

        assert result.status == LoanStatus.SUCCESS
        assert result.tx_hash is not None
        assert result.tx_hash.startswith("0x")

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_execute_loan",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))


    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_execute_batch_loans(self):
        """Test batch loan execution."""
        engine = FlashLoanEngine()

        requests = [
            FlashLoanRequest(
                protocol=FlashLoanProtocol.BALANCER,
                token_address="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
                amount=Decimal("100000"),
                receiver_address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0",
                callback_data=b"",
            ),
            FlashLoanRequest(
                protocol=FlashLoanProtocol.UNISWAP_V3,
                token_address="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
                amount=Decimal("50000"),
                receiver_address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0",
                callback_data=b"",
            ),
        ]

        results = await engine.execute_batch_loans(requests)

        assert len(results) == 2
        for result in results:
            assert result.status == LoanStatus.SUCCESS

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_execute_batch_loans",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))



class TestProtocolLiquidity:
    """Test protocol liquidity queries."""

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_get_protocol_liquidity(self):
        """Test getting protocol liquidity."""
        engine = FlashLoanEngine()

        liquidity = await engine.get_protocol_liquidity(
            FlashLoanProtocol.AAVE_V3, "USDC"
        )

        assert liquidity > 0

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_get_protocol_liquidity",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate information about Aave protocol. Response must explain what the protocol does, its key features, and relevant DeFi concepts in an accessible way."
                ),
                additional_context={'test_category': 'defi_protocol', 'protocol': 'Aave'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))


    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_get_liquidity_unsupported_token(self):
        """Test liquidity for unsupported token."""
        engine = FlashLoanEngine()

        liquidity = await engine.get_protocol_liquidity(
            FlashLoanProtocol.AAVE_V3, "UNKNOWN"
        )

        assert liquidity == Decimal("0")

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_get_liquidity_unsupported_token",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))



class TestProtocolComparison:
    """Test protocol comparison."""

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_compare_protocol_fees(self):
        """Test comparing fees across protocols."""
        engine = FlashLoanEngine()
        amount = Decimal("100000")

        aave_fees = await engine.calculate_fees(FlashLoanProtocol.AAVE_V3, amount)
        balancer_fees = await engine.calculate_fees(FlashLoanProtocol.BALANCER, amount)

        # Balancer should be cheaper (no protocol fee)
        assert balancer_fees < aave_fees

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_compare_protocol_fees",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate information about Aave protocol. Response must explain what the protocol does, its key features, and relevant DeFi concepts in an accessible way."
                ),
                additional_context={'test_category': 'defi_protocol', 'protocol': 'Aave'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))



class TestSerialization:
    """Test data serialization."""

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_request_to_dict(self):
        """Test flash loan request serialization."""
        request = FlashLoanRequest(
            protocol=FlashLoanProtocol.BALANCER,
            token_address="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
            amount=Decimal("100000"),
            receiver_address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0",
            callback_data=b"\x00\x01",
        )

        data = request.to_dict()

        assert "protocol" in data
        assert "token_address" in data
        assert "amount" in data
        assert "receiver_address" in data
        assert "callback_data" in data

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_request_to_dict",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))


    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_result_to_dict(self):
        """Test flash loan result serialization."""
        engine = FlashLoanEngine()

        request = FlashLoanRequest(
            protocol=FlashLoanProtocol.BALANCER,
            token_address="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
            amount=Decimal("100000"),
            receiver_address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0",
            callback_data=b"",
        )

        result = await engine.simulate_loan(request)
        data = result.to_dict()

        assert "request" in data
        assert "status" in data

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_result_to_dict",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        assert "fees_paid" in data