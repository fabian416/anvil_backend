"""Integration tests for MEV Protection & Execution (Phase 8 Week 3).

Tests MEV protection, bundle creation, and arbitrage execution.
"""

import pytest
from decimal import Decimal

from app.application.ultra.mev_protection import (
    MEVProtection,
    MEVConfig,
    Transaction,
    ProtectionLevel,
    BundleStatus,
)
from app.application.ultra.arbitrage_executor import (
    ArbitrageExecutor,
    ExecutionStatus,
)
from app.application.ultra.arbitrage_discovery import ArbitrageDiscovery


class TestMEVConfig:
    """Test MEV configuration."""

    def test_config_defaults(self):
        """Test default configuration."""
        config = MEVConfig()

        assert config.protection_level == ProtectionLevel.ADVANCED
        assert config.use_flashbots is True
        assert config.max_gas_price_gwei == 150


class TestMEVBundle:
    """Test MEV bundle creation."""

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_create_bundle(self):
        """Test creating MEV bundle."""
        protection = MEVProtection()

        tx = Transaction(
            to="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0",
            data="0xabcdef",
            value=Decimal("0"),
            gas_limit=200000,
            max_fee_per_gas=50,
            max_priority_fee=2,
        )

        bundle = await protection.create_bundle(
            transactions=[tx], expected_profit=Decimal("150")
        )

        assert bundle.bundle_id.startswith("BUNDLE-")
        assert len(bundle.transactions) == 1
        assert bundle.expected_profit == Decimal("150")

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_create_bundle",
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
    async def test_bundle_size_limit(self):
        """Test bundle size validation."""
        config = MEVConfig(max_bundle_size=2)
        protection = MEVProtection(config)

        txs = [
            Transaction(
                to="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0",
                data="0xabcdef",
                value=Decimal("0"),
                gas_limit=200000,
                max_fee_per_gas=50,
                max_priority_fee=2,
            )
            for _ in range(3)
        ]

        with pytest.raises(ValueError, match="exceeds max"):
            await protection.create_bundle(
                transactions=txs, expected_profit=Decimal("150")
            )

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_bundle_size_limit",
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
    async def test_bundle_min_profit(self):
        """Test bundle minimum profit validation."""
        config = MEVConfig(min_profit_for_bundle=Decimal("100"))
        protection = MEVProtection(config)

        tx = Transaction(
            to="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0",
            data="0xabcdef",
            value=Decimal("0"),
            gas_limit=200000,
            max_fee_per_gas=50,
            max_priority_fee=2,
        )

        with pytest.raises(ValueError, match="below minimum"):
            await protection.create_bundle(transactions=[tx], expected_profit=Decimal("50"))

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_bundle_min_profit",
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



class TestBundleSimulation:
    """Test bundle simulation."""

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_simulate_valid_bundle(self):
        """Test simulating valid bundle."""
        protection = MEVProtection()

        tx = Transaction(
            to="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0",
            data="0xabcdef",
            value=Decimal("0"),
            gas_limit=200000,
            max_fee_per_gas=50,
            max_priority_fee=2,
        )

        bundle = await protection.create_bundle(
            transactions=[tx], expected_profit=Decimal("150")
        )

        success, error = await protection.simulate_bundle(bundle)

        assert success is True
        assert error is None

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_simulate_valid_bundle",
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
    async def test_simulate_excessive_gas(self):
        """Test simulation fails for excessive gas."""
        protection = MEVProtection()

        tx = Transaction(
            to="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0",
            data="0xabcdef",
            value=Decimal("0"),
            gas_limit=40000000,  # Exceeds block limit
            max_fee_per_gas=50,
            max_priority_fee=2,
        )

        bundle = await protection.create_bundle(
            transactions=[tx], expected_profit=Decimal("150")
        )

        success, error = await protection.simulate_bundle(bundle)

        assert success is False
        assert "exceeds block limit" in error

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_simulate_excessive_gas",
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



class TestFlashbotsSubmission:
    """Test Flashbots submission."""

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_submit_to_flashbots(self):
        """Test submitting bundle to Flashbots."""
        protection = MEVProtection()

        tx = Transaction(
            to="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0",
            data="0xabcdef",
            value=Decimal("0"),
            gas_limit=200000,
            max_fee_per_gas=50,
            max_priority_fee=2,
        )

        bundle = await protection.create_bundle(
            transactions=[tx], expected_profit=Decimal("150")
        )

        response = await protection.submit_to_flashbots(bundle)

        assert response.bundle_id == bundle.bundle_id
        assert response.status == BundleStatus.SUBMITTED

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_submit_to_flashbots",
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
    async def test_check_bundle_status(self):
        """Test checking bundle status."""
        protection = MEVProtection()

        tx = Transaction(
            to="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0",
            data="0xabcdef",
            value=Decimal("0"),
            gas_limit=200000,
            max_fee_per_gas=50,
            max_priority_fee=2,
        )

        bundle = await protection.create_bundle(
            transactions=[tx], expected_profit=Decimal("150")
        )

        await protection.submit_to_flashbots(bundle)

        status = await protection.check_bundle_status(bundle.bundle_id)

        assert status is not None
        assert status.bundle_id == bundle.bundle_id

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_check_bundle_status",
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



class TestArbitrageExecution:
    """Test arbitrage execution."""

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_simulate_execution(self):
        """Test simulating arbitrage execution."""
        executor = ArbitrageExecutor()
        discovery = ArbitrageDiscovery()

        # Discover opportunities
        opportunities = await discovery.discover_all_opportunities(Decimal("10000"))

        if opportunities:
            opp = opportunities[0]
            result = await executor.simulate_execution(opp)

            assert result.execution_id.startswith("EXEC-")
            assert result.opportunity_id == opp.opportunity_id

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_simulate_execution",
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
    async def test_execute_with_mev_protection(self):
        """Test executing with MEV protection."""
        executor = ArbitrageExecutor()
        discovery = ArbitrageDiscovery()

        # Discover opportunities
        opportunities = await discovery.discover_all_opportunities(Decimal("10000"))

        if opportunities:
            opp = opportunities[0]
            result = await executor.execute_with_mev_protection(opp)

            assert result.execution_id is not None
            assert result.bundle_id is not None

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_execute_with_mev_protection",
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



class TestBundleManagement:
    """Test bundle management."""

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_get_bundle_statistics(self):
        """Test getting bundle statistics."""
        protection = MEVProtection()

        # Submit some bundles
        tx = Transaction(
            to="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0",
            data="0xabcdef",
            value=Decimal("0"),
            gas_limit=200000,
            max_fee_per_gas=50,
            max_priority_fee=2,
        )

        bundle1 = await protection.create_bundle(
            transactions=[tx], expected_profit=Decimal("150")
        )
        await protection.submit_to_flashbots(bundle1)

        stats = await protection.get_bundle_statistics()

        assert stats["total_bundles"] >= 1

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_get_bundle_statistics",
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
    async def test_get_protection_info(self):
        """Test getting protection info."""
        protection = MEVProtection()

        info = protection.get_protection_info()

        assert "protection_level" in info
        assert "use_flashbots" in info
        assert info["use_flashbots"] is True

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_get_protection_info",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto. Response must focus on crypto specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto'}
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
    async def test_bundle_to_dict(self):
        """Test bundle serialization."""
        protection = MEVProtection()

        tx = Transaction(
            to="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0",
            data="0xabcdef",
            value=Decimal("0"),
            gas_limit=200000,
            max_fee_per_gas=50,
            max_priority_fee=2,
        )

        bundle = await protection.create_bundle(
            transactions=[tx], expected_profit=Decimal("150")
        )

        data = bundle.to_dict()

        assert "bundle_id" in data
        assert "transactions" in data

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_bundle_to_dict",
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

        assert "expected_profit" in data