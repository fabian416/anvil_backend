"""Integration tests for Auto-Executor & Risk Management (Phase 8 Week 4)."""

import pytest
from decimal import Decimal

from app.application.ultra.auto_executor import AutoExecutor, AutoExecutorConfig, AutoExecutorStatus
from app.application.ultra.risk_manager import RiskManager, RiskProfile


class TestRiskProfile:
    """Test risk profile."""

    def test_risk_profile_defaults(self):
        """Test default risk profile."""
        profile = RiskProfile()

        assert profile.max_capital_per_trade == Decimal("100000")
        assert profile.max_daily_exposure == Decimal("500000")
        assert profile.max_concurrent_trades == 5


class TestRiskManager:
    """Test risk manager."""

    def test_check_position_limit(self):
        """Test position limit checking."""
        manager = RiskManager()

        allowed, reason = manager.check_position_limit(Decimal("50000"))

        assert allowed is True
        assert reason is None

    def test_position_limit_exceeded(self):
        """Test position limit exceeded."""
        manager = RiskManager()

        allowed, reason = manager.check_position_limit(Decimal("200000"))

        assert allowed is False
        assert "exceeds max" in reason

    def test_validate_trade(self):
        """Test trade validation."""
        manager = RiskManager()

        allowed, reason = manager.validate_trade(
            capital=Decimal("50000"),
            expected_profit=Decimal("100"),
            gas_cost=Decimal("10"),
        )

        assert allowed is True


class TestAutoExecutor:
    """Test auto-executor."""

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_start_executor(self):
        """Test starting executor."""
        executor = AutoExecutor()

        result = await executor.start()

        assert result["status"] == "started"
        assert executor._status == AutoExecutorStatus.RUNNING

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_start_executor",
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
    async def test_stop_executor(self):
        """Test stopping executor."""
        executor = AutoExecutor()

        await executor.start()
        result = await executor.stop()

        assert result["status"] == "stopped"
        assert executor._status == AutoExecutorStatus.STOPPED

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_stop_executor",
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
    async def test_pause_resume(self):
        """Test pause and resume."""
        executor = AutoExecutor()

        await executor.start()
        pause_result = await executor.pause()
        assert pause_result["status"] == "paused"

        resume_result = await executor.resume()
        assert resume_result["status"] == "resumed"

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_pause_resume",
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


    def test_get_status(self):
        """Test getting status."""
        executor = AutoExecutor()

        status = executor.get_status()

        assert "status" in status
        assert "metrics" in status
        assert "risk_score" in status

    def test_update_config(self):
        """Test updating configuration."""
        executor = AutoExecutor()

        result = executor.update_config(min_profit_usd=75.0)

        assert result["status"] == "updated"
        assert executor.config.min_profit_usd == Decimal("75.0")


class TestMetrics:
    """Test metrics tracking."""

    def test_record_trade(self):
        """Test recording trade."""
        manager = RiskManager()

        manager.record_trade(
            trade_id="TEST-001",
            opportunity_id="ARB-001",
            profit=Decimal("100"),
            gas_cost=Decimal("10"),
            capital=Decimal("10000"),
            success=True,
        )

        metrics = manager.get_metrics()

        assert metrics.total_trades == 1
        assert metrics.successful_trades == 1

    def test_metrics_calculation(self):
        """Test metrics calculation."""
        manager = RiskManager()

        # Record successful trade
        manager.record_trade(
            "T1", "O1", Decimal("100"), Decimal("10"), Decimal("10000"), True
        )

        # Record failed trade
        manager.record_trade(
            "T2", "O2", Decimal("-50"), Decimal("10"), Decimal("10000"), False
        )

        metrics = manager.get_metrics()

        assert metrics.total_trades == 2
        assert metrics.win_rate == 0.5


class TestRiskScoring:
    """Test risk scoring."""

    def test_risk_score_calculation(self):
        """Test risk score calculation."""
        manager = RiskManager()

        score = manager.get_risk_score()

        assert 0.0 <= score <= 1.0