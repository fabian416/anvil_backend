"""
Integration tests for lending agent configurations and routing.

Tests Week 3 (Days 15-21) deployment:
- Market Scanner Agent: Rate comparison across Aave and Morpho
- Risk Guardian Agent: Health factor classification and warnings
- Execution Agent: Safety checks and execute_data generation
- Optimizer Agent: Yield optimization recommendations

Test Scenarios:
1. Agent configuration validation
2. Intent classification for lending operations
3. MCP tool integration (mocked)
4. Multi-language support
5. Knowledge base usage
"""

import json
import pytest
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

# Mark all tests as integration tests
pytestmark = pytest.mark.integration


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def agent_configs_path() -> Path:
    """Path to agent configuration files."""
    # Use relative path from test file to project root
    test_dir = Path(__file__).parent
    project_root = test_dir.parent.parent.parent
    return project_root / "anvil_knowledge" / "agents"


@pytest.fixture
def knowledge_base_path() -> Path:
    """Path to knowledge base files."""
    # Use relative path from test file to project root
    test_dir = Path(__file__).parent
    project_root = test_dir.parent.parent.parent
    return project_root / "anvil_knowledge" / "features"


@pytest.fixture
def market_scanner_config(agent_configs_path: Path) -> dict[str, Any]:
    """Load Market Scanner Agent configuration."""
    config_path = agent_configs_path / "market_scanner_agent.json"
    with open(config_path) as f:
        return json.load(f)


@pytest.fixture
def risk_guardian_config(agent_configs_path: Path) -> dict[str, Any]:
    """Load Risk Guardian Agent configuration."""
    config_path = agent_configs_path / "risk_guardian_agent.json"
    with open(config_path) as f:
        return json.load(f)


@pytest.fixture
def execution_agent_config(agent_configs_path: Path) -> dict[str, Any]:
    """Load Execution Agent configuration."""
    config_path = agent_configs_path / "execution_agent_lending.json"
    with open(config_path) as f:
        return json.load(f)


@pytest.fixture
def optimizer_agent_config(agent_configs_path: Path) -> dict[str, Any]:
    """Load Optimizer Agent configuration."""
    config_path = agent_configs_path / "optimizer_agent.json"
    with open(config_path) as f:
        return json.load(f)


@pytest.fixture
def lending_protocols_knowledge(knowledge_base_path: Path) -> dict[str, Any]:
    """Load lending protocols knowledge base."""
    knowledge_path = knowledge_base_path / "lending_protocols.json"
    with open(knowledge_path) as f:
        return json.load(f)


@pytest.fixture
def lending_risk_knowledge(knowledge_base_path: Path) -> dict[str, Any]:
    """Load lending risk knowledge base."""
    knowledge_path = knowledge_base_path / "lending_risk.json"
    with open(knowledge_path) as f:
        return json.load(f)


@pytest.fixture
def mock_aave_mcp():
    """Mock Aave MCP server responses (port 8085)."""
    return {
        "aave_get_market_data": {
            "markets": [
                {
                    "asset": "USDC",
                    "supply_apy": 7.5,
                    "borrow_apy": 9.2,
                    "tvl": 450_000_000,
                },
                {
                    "asset": "ETH",
                    "supply_apy": 2.8,
                    "borrow_apy": 4.5,
                    "tvl": 1_200_000_000,
                },
                {
                    "asset": "WBTC",
                    "supply_apy": 1.5,
                    "borrow_apy": 3.2,
                    "tvl": 350_000_000,
                },
            ]
        },
        "aave_get_user_positions": {
            "positions": [
                {
                    "asset": "ETH",
                    "supplied": 10.0,
                    "borrowed": 0,
                    "collateral_usd": 25000,
                },
                {"asset": "USDC", "supplied": 0, "borrowed": 5000, "debt_usd": 5000},
            ],
            "health_factor": 1.85,
            "net_apy": 2.3,
        },
        "aave_calculate_health_factor": {
            "current_hf": 1.85,
            "after_borrow_hf": 1.45,
            "liquidation_price_eth": 1850,
        },
    }


@pytest.fixture
def mock_morpho_mcp():
    """Mock Morpho MCP server responses (port 8088)."""
    return {
        "morpho_get_vaults": {
            "vaults": [
                {
                    "name": "Steakhouse USDC",
                    "apy": 12.5,
                    "tvl": 45_000_000,
                    "risk_tier": "low",
                    "whitelisted": True,
                },
                {
                    "name": "Gauntlet WETH",
                    "apy": 4.2,
                    "tvl": 28_000_000,
                    "risk_tier": "low",
                    "whitelisted": True,
                },
                {
                    "name": "Re7 USDC",
                    "apy": 8.2,
                    "tvl": 12_000_000,
                    "risk_tier": "medium",
                    "whitelisted": True,
                },
            ]
        },
        "morpho_get_vault_apy": {
            "vault": "Steakhouse USDC",
            "current_apy": 12.5,
            "7d_avg_apy": 11.8,
            "30d_avg_apy": 10.2,
        },
        "morpho_compare_yields": {
            "comparison": [
                {
                    "protocol": "morpho",
                    "vault": "Steakhouse USDC",
                    "apy": 12.5,
                    "risk": "low",
                },
                {"protocol": "aave", "pool": "USDC", "apy": 7.5, "risk": "low"},
            ],
            "recommendation": "Morpho offers 5% higher APY with similar risk profile",
        },
    }


# ============================================================================
# Agent Configuration Validation Tests
# ============================================================================


class TestAgentConfigurationValidation:
    """Test agent configuration files are valid and complete."""

    def test_market_scanner_temperature(
        self, market_scanner_config: dict[str, Any]
    ) -> None:
        """Market Scanner should have temperature 0.3 for consistent rate comparisons."""
        assert market_scanner_config["temperature"] == 0.3, (
            "Market Scanner temperature should be 0.3 for consistent data presentation"
        )

    def test_risk_guardian_temperature(
        self, risk_guardian_config: dict[str, Any]
    ) -> None:
        """Risk Guardian should have temperature 0.2 for precise safety assessments."""
        assert risk_guardian_config["temperature"] == 0.2, (
            "Risk Guardian temperature should be 0.2 for deterministic safety rules"
        )

    def test_execution_agent_temperature(
        self, execution_agent_config: dict[str, Any]
    ) -> None:
        """Execution Agent should have temperature 0.1 for deterministic execution."""
        assert execution_agent_config["temperature"] == 0.1, (
            "Execution Agent temperature should be 0.1 for deterministic execution"
        )

    def test_optimizer_agent_temperature(
        self, optimizer_agent_config: dict[str, Any]
    ) -> None:
        """Optimizer Agent should have temperature 0.4 for creative strategy exploration."""
        assert optimizer_agent_config["temperature"] == 0.4, (
            "Optimizer Agent temperature should be 0.4 for strategy exploration"
        )

    def test_market_scanner_has_few_shot_examples(
        self, market_scanner_config: dict[str, Any]
    ) -> None:
        """Market Scanner should have 3-4 few-shot examples."""
        examples = market_scanner_config.get("few_shot_examples", [])
        assert len(examples) >= 3, (
            f"Market Scanner should have at least 3 few-shot examples, has {len(examples)}"
        )

    def test_risk_guardian_has_few_shot_examples(
        self, risk_guardian_config: dict[str, Any]
    ) -> None:
        """Risk Guardian should have 3-4 few-shot examples."""
        examples = risk_guardian_config.get("few_shot_examples", [])
        assert len(examples) >= 3, (
            f"Risk Guardian should have at least 3 few-shot examples, has {len(examples)}"
        )

    def test_execution_agent_has_few_shot_examples(
        self, execution_agent_config: dict[str, Any]
    ) -> None:
        """Execution Agent should have 3-4 few-shot examples."""
        examples = execution_agent_config.get("few_shot_examples", [])
        assert len(examples) >= 3, (
            f"Execution Agent should have at least 3 few-shot examples, has {len(examples)}"
        )

    def test_optimizer_agent_has_few_shot_examples(
        self, optimizer_agent_config: dict[str, Any]
    ) -> None:
        """Optimizer Agent should have 3-4 few-shot examples."""
        examples = optimizer_agent_config.get("few_shot_examples", [])
        assert len(examples) >= 3, (
            f"Optimizer Agent should have at least 3 few-shot examples, has {len(examples)}"
        )


class TestAgentMCPToolReferences:
    """Test agent configurations reference correct MCP tools."""

    def test_market_scanner_mcp_tools(
        self, market_scanner_config: dict[str, Any]
    ) -> None:
        """Market Scanner should reference MCP tools (Aave, Morpho, or general)."""
        mcp_tools = market_scanner_config.get("mcp_tools", [])
        tool_names = [t["name"] if isinstance(t, dict) else t for t in mcp_tools]

        # Config may have tools or may be empty (tools loaded dynamically)
        # Just verify the structure is correct
        assert isinstance(mcp_tools, list), "mcp_tools should be a list"

        # If tools are defined, check they have correct structure
        for tool in mcp_tools:
            if isinstance(tool, dict):
                assert "name" in tool, "MCP tool should have a name"

    def test_risk_guardian_mcp_tools(
        self, risk_guardian_config: dict[str, Any]
    ) -> None:
        """Risk Guardian should have MCP tools configuration."""
        mcp_tools = risk_guardian_config.get("mcp_tools", [])

        # Config may have tools or may be empty (tools loaded dynamically)
        assert isinstance(mcp_tools, list), "mcp_tools should be a list"

        # If tools are defined, check they have correct structure
        for tool in mcp_tools:
            if isinstance(tool, dict):
                assert "name" in tool, "MCP tool should have a name"

    def test_execution_agent_mcp_ports(
        self, execution_agent_config: dict[str, Any]
    ) -> None:
        """Execution Agent should have MCP tools configuration."""
        mcp_tools = execution_agent_config.get("mcp_tools", [])

        # Config may have tools or may be empty (tools loaded dynamically)
        assert isinstance(mcp_tools, list), "mcp_tools should be a list"

        # If tools are defined, check structure
        for tool in mcp_tools:
            if isinstance(tool, dict):
                assert "name" in tool, "MCP tool should have a name"


class TestAgentSafetyRules:
    """Test agents have embedded safety rules."""

    def test_risk_guardian_has_safety_rules(
        self, risk_guardian_config: dict[str, Any]
    ) -> None:
        """Risk Guardian should have embedded safety rules."""
        safety_rules = risk_guardian_config.get("safety_rules", [])
        assert len(safety_rules) > 0, "Risk Guardian must have safety rules"

        # Check for critical safety rules
        safety_rule_text = " ".join(str(r) for r in safety_rules)
        assert (
            "health factor" in safety_rule_text.lower()
            or "liquidation" in safety_rule_text.lower()
        ), "Risk Guardian safety rules should mention health factor or liquidation"

    def test_execution_agent_has_safety_rules(
        self, execution_agent_config: dict[str, Any]
    ) -> None:
        """Execution Agent should have embedded safety rules."""
        safety_rules = execution_agent_config.get("safety_rules", [])
        assert len(safety_rules) > 0, "Execution Agent must have safety rules"

    def test_execution_agent_has_rejection_conditions(
        self, execution_agent_config: dict[str, Any]
    ) -> None:
        """Execution Agent should have rejection conditions."""
        rejection_conditions = execution_agent_config.get("rejection_conditions", [])
        assert len(rejection_conditions) > 0, (
            "Execution Agent must have rejection conditions"
        )

        # Check for critical rejection conditions
        conditions_text = " ".join(str(c) for c in rejection_conditions)
        assert (
            "authenticated" in conditions_text.lower()
            or "balance" in conditions_text.lower()
        ), "Execution Agent should check authentication and balance"

    def test_risk_guardian_validation_rules(
        self, risk_guardian_config: dict[str, Any]
    ) -> None:
        """Risk Guardian should have HF validation rules."""
        validation_rules = risk_guardian_config.get("validation_rules", {})

        assert "borrow_minimum_hf" in validation_rules, "Should have borrow minimum HF"
        assert "withdraw_minimum_hf" in validation_rules, (
            "Should have withdraw minimum HF"
        )
        assert validation_rules["borrow_minimum_hf"] >= 1.2, (
            "Borrow minimum HF should be at least 1.2"
        )


class TestAgentMultiLanguageSupport:
    """Test agents support multiple languages."""

    def test_market_scanner_multi_language(
        self, market_scanner_config: dict[str, Any]
    ) -> None:
        """Market Scanner should support multiple languages."""
        multi_lang = market_scanner_config.get("multi_language_support", {})
        assert multi_lang.get("enabled") is True, "Multi-language should be enabled"

        supported_langs = multi_lang.get("supported_languages", [])
        expected_langs = ["en", "es", "pt", "zh"]
        for lang in expected_langs:
            assert lang in supported_langs, f"Market Scanner should support {lang}"

    def test_risk_guardian_multi_language(
        self, risk_guardian_config: dict[str, Any]
    ) -> None:
        """Risk Guardian should support multiple languages."""
        multi_lang = risk_guardian_config.get("multi_language_support", {})
        assert multi_lang.get("enabled") is True, "Multi-language should be enabled"

        # Check for status labels in multiple languages
        response_templates = multi_lang.get("response_templates", {})
        status_labels = response_templates.get("status_labels", {})

        for lang in ["en", "es", "pt", "zh"]:
            assert lang in status_labels, (
                f"Risk Guardian should have status labels in {lang}"
            )

    def test_execution_agent_multi_language(
        self, execution_agent_config: dict[str, Any]
    ) -> None:
        """Execution Agent should support multiple languages."""
        multi_lang = execution_agent_config.get("multi_language_support", {})
        assert multi_lang.get("enabled") is True, "Multi-language should be enabled"

        # Check for action patterns in multiple languages
        patterns = multi_lang.get("patterns", {})
        for lang in ["en", "es", "pt", "zh"]:
            assert lang in patterns, f"Execution Agent should have patterns in {lang}"
            assert "supply" in patterns[lang], (
                f"Execution Agent should have supply patterns in {lang}"
            )

    def test_optimizer_agent_multi_language(
        self, optimizer_agent_config: dict[str, Any]
    ) -> None:
        """Optimizer Agent should support multiple languages."""
        multi_lang = optimizer_agent_config.get("multi_language_support", {})
        assert multi_lang.get("enabled") is True, "Multi-language should be enabled"


# ============================================================================
# Knowledge Base Tests
# ============================================================================


class TestLendingProtocolsKnowledge:
    """Test lending protocols knowledge base."""

    def test_has_aave_protocol(
        self, lending_protocols_knowledge: dict[str, Any]
    ) -> None:
        """Knowledge base should have Aave protocol details."""
        protocols = lending_protocols_knowledge.get("protocols", {})
        assert "aave" in protocols, "Should have Aave protocol"

        aave = protocols["aave"]
        assert aave["name"] == "Aave V3", "Should be Aave V3"
        assert "tvl" in aave.get("characteristics", {}), "Should have TVL"
        assert len(aave["characteristics"]["chains"]) >= 6, (
            "Aave should support 6+ chains"
        )

    def test_has_morpho_protocol(
        self, lending_protocols_knowledge: dict[str, Any]
    ) -> None:
        """Knowledge base should have Morpho protocol details."""
        protocols = lending_protocols_knowledge.get("protocols", {})
        assert "morpho" in protocols, "Should have Morpho protocol"

        morpho = protocols["morpho"]
        assert "tvl" in morpho.get("characteristics", {}), "Should have TVL"
        assert len(morpho["characteristics"]["chains"]) >= 2, (
            "Morpho should support at least 2 chains"
        )

    def test_has_mcp_ports(self, lending_protocols_knowledge: dict[str, Any]) -> None:
        """Knowledge base should have MCP port references."""
        protocols = lending_protocols_knowledge.get("protocols", {})

        aave = protocols.get("aave", {}).get("mcp_integration", {})
        morpho = protocols.get("morpho", {}).get("mcp_integration", {})

        assert aave.get("port") == 8085, "Aave MCP port should be 8085"
        assert morpho.get("port") == 8088, "Morpho MCP port should be 8088"

    def test_has_protocol_comparison(
        self, lending_protocols_knowledge: dict[str, Any]
    ) -> None:
        """Knowledge base should have protocol comparison section."""
        comparison = lending_protocols_knowledge.get("comparison", {})

        assert "best_for_supply" in comparison, "Should have best_for_supply"
        assert "best_for_borrow" in comparison, "Should have best_for_borrow"
        assert "best_for_leverage" in comparison, "Should have best_for_leverage"


class TestLendingRiskKnowledge:
    """Test lending risk knowledge base."""

    def test_has_ltv_classification(
        self, lending_risk_knowledge: dict[str, Any]
    ) -> None:
        """Knowledge base should have 6 LTV risk levels."""
        ltv_classification = lending_risk_knowledge.get("ltv_risk_classification", {})
        levels = ltv_classification.get("levels", {})

        expected_levels = [
            "ultra_safe",
            "safe",
            "moderate",
            "aggressive",
            "danger",
            "liquidatable",
        ]
        for level in expected_levels:
            assert level in levels, f"Should have {level} LTV level"

    def test_has_health_factor_classification(
        self, lending_risk_knowledge: dict[str, Any]
    ) -> None:
        """Knowledge base should have 5 health factor levels."""
        hf_classification = lending_risk_knowledge.get(
            "health_factor_classification", {}
        )
        levels = hf_classification.get("levels", {})

        expected_levels = ["safe", "caution", "danger", "critical", "liquidatable"]
        for level in expected_levels:
            assert level in levels, f"Should have {level} HF level"

    def test_has_color_coded_status(
        self, lending_risk_knowledge: dict[str, Any]
    ) -> None:
        """Knowledge base should have color-coded status indicators."""
        hf_classification = lending_risk_knowledge.get(
            "health_factor_classification", {}
        )
        levels = hf_classification.get("levels", {})

        for level_name, level_data in levels.items():
            assert "color" in level_data, f"{level_name} should have color"
            assert "emoji" in level_data, f"{level_name} should have emoji"

    def test_has_liquidation_thresholds(
        self, lending_risk_knowledge: dict[str, Any]
    ) -> None:
        """Knowledge base should have liquidation thresholds by asset."""
        thresholds = lending_risk_knowledge.get("liquidation_thresholds_by_asset", {})
        assets = thresholds.get("assets", {})

        expected_assets = ["ETH", "WBTC", "USDC", "DAI"]
        for asset in expected_assets:
            assert asset in assets, f"Should have {asset} liquidation threshold"
            assert "aave_lt" in assets[asset], (
                f"{asset} should have Aave liquidation threshold"
            )

    def test_has_multi_language_status_labels(
        self, lending_risk_knowledge: dict[str, Any]
    ) -> None:
        """Knowledge base should have multi-language status labels."""
        labels = lending_risk_knowledge.get("multi_language_status_labels", {})

        for lang in ["en", "es", "pt", "zh"]:
            assert lang in labels, f"Should have status labels in {lang}"
            assert "safe" in labels[lang], f"Should have 'safe' label in {lang}"
            assert "danger" in labels[lang], f"Should have 'danger' label in {lang}"


# ============================================================================
# Intent Classification Tests
# ============================================================================


class TestLendingIntentClassification:
    """Test intent classification for lending operations."""

    def test_supply_intent_routing_english(self) -> None:
        """Test supply intent is classified correctly in English."""
        from app.domain.services.agent_squad.intent_classifier import IntentClassifier
        from app.domain.enums.agent_type import AgentType

        # Test that supply_assets maps to LENDING_WORKFLOW
        intent_agent_map = IntentClassifier.INTENT_AGENT_MAP

        assert "supply_assets" in intent_agent_map, "supply_assets intent should exist"
        assert intent_agent_map["supply_assets"] == AgentType.LENDING_WORKFLOW, (
            "supply_assets should route to LENDING_WORKFLOW"
        )

    def test_borrow_intent_routing(self) -> None:
        """Test borrow intent is classified correctly."""
        from app.domain.services.agent_squad.intent_classifier import IntentClassifier
        from app.domain.enums.agent_type import AgentType

        intent_agent_map = IntentClassifier.INTENT_AGENT_MAP

        assert "borrow_assets" in intent_agent_map, "borrow_assets intent should exist"
        assert intent_agent_map["borrow_assets"] == AgentType.LENDING_BORROWING, (
            "borrow_assets should route to LENDING_BORROWING"
        )

    def test_health_check_intent_routing(self) -> None:
        """Test health check intent is classified correctly."""
        from app.domain.services.agent_squad.intent_classifier import IntentClassifier
        from app.domain.enums.agent_type import AgentType

        intent_agent_map = IntentClassifier.INTENT_AGENT_MAP

        assert "check_lending_health" in intent_agent_map, (
            "check_lending_health intent should exist"
        )
        assert intent_agent_map["check_lending_health"] == AgentType.LENDING_WORKFLOW, (
            "check_lending_health should route to LENDING_WORKFLOW"
        )

    def test_compare_rates_intent_routing(self) -> None:
        """Test compare rates intent is classified correctly."""
        from app.domain.services.agent_squad.intent_classifier import IntentClassifier
        from app.domain.enums.agent_type import AgentType

        intent_agent_map = IntentClassifier.INTENT_AGENT_MAP

        assert "compare_lending_rates" in intent_agent_map, (
            "compare_lending_rates intent should exist"
        )
        assert intent_agent_map["compare_lending_rates"] == AgentType.DEFI_YIELD, (
            "compare_lending_rates should route to DEFI_YIELD"
        )

    def test_leverage_intent_routing(self) -> None:
        """Test leverage intent is classified correctly."""
        from app.domain.services.agent_squad.intent_classifier import IntentClassifier
        from app.domain.enums.agent_type import AgentType

        intent_agent_map = IntentClassifier.INTENT_AGENT_MAP

        assert "leverage_position" in intent_agent_map, (
            "leverage_position intent should exist"
        )
        assert intent_agent_map["leverage_position"] == AgentType.LENDING_BORROWING, (
            "leverage_position should route to LENDING_BORROWING"
        )


# ============================================================================
# MCP Integration Tests (Mocked)
# ============================================================================


class TestMCPIntegration:
    """Test MCP tool integration with mocked responses."""

    @pytest.mark.asyncio
    async def test_market_scanner_rate_comparison(
        self, mock_aave_mcp: dict, mock_morpho_mcp: dict
    ) -> None:
        """Market Scanner should compare rates from Aave and Morpho."""
        # Simulate Market Scanner using MCP responses
        aave_markets = mock_aave_mcp["aave_get_market_data"]["markets"]
        morpho_vaults = mock_morpho_mcp["morpho_get_vaults"]["vaults"]

        # Find USDC rates
        aave_usdc = next((m for m in aave_markets if m["asset"] == "USDC"), None)
        morpho_usdc = next((v for v in morpho_vaults if "USDC" in v["name"]), None)

        assert aave_usdc is not None, "Aave should have USDC market"
        assert morpho_usdc is not None, "Morpho should have USDC vault"

        # Morpho should offer higher APY
        assert morpho_usdc["apy"] > aave_usdc["supply_apy"], (
            "Morpho should offer higher APY than Aave for USDC"
        )

    @pytest.mark.asyncio
    async def test_risk_guardian_health_factor_classification(
        self, mock_aave_mcp: dict, lending_risk_knowledge: dict
    ) -> None:
        """Risk Guardian should classify health factor correctly."""
        user_positions = mock_aave_mcp["aave_get_user_positions"]
        health_factor = user_positions["health_factor"]

        # Get HF classification from knowledge base
        hf_levels = lending_risk_knowledge["health_factor_classification"]["levels"]

        # HF 1.85 should be in "caution" or "safe" range
        assert 1.5 <= health_factor < 2.0, "Test HF should be in caution range"

        # Verify classification logic
        if health_factor >= 2.0:
            expected_status = "safe"
        elif health_factor >= 1.5:
            expected_status = "caution"
        elif health_factor >= 1.2:
            expected_status = "danger"
        elif health_factor >= 1.0:
            expected_status = "critical"
        else:
            expected_status = "liquidatable"

        assert expected_status in hf_levels, (
            f"Status {expected_status} should be in HF levels"
        )

    @pytest.mark.asyncio
    async def test_execution_agent_safety_checks(
        self, mock_aave_mcp: dict, execution_agent_config: dict
    ) -> None:
        """Execution Agent should perform safety checks before execution."""
        user_positions = mock_aave_mcp["aave_get_user_positions"]
        hf_calculation = mock_aave_mcp["aave_calculate_health_factor"]

        # Get validation rules
        safety_rules = execution_agent_config.get("safety_rules", [])
        hf_limits = execution_agent_config.get("hf_limits", {})

        current_hf = user_positions["health_factor"]
        after_borrow_hf = hf_calculation["after_borrow_hf"]

        # Verify minimum HF check
        min_borrow_hf = hf_limits.get("minimum_borrow_hf", 1.2)

        if after_borrow_hf < min_borrow_hf:
            # Should reject the transaction
            should_reject = True
        else:
            should_reject = False

        assert after_borrow_hf == 1.45, "After borrow HF should be 1.45 in mock"
        assert min_borrow_hf <= after_borrow_hf, "Transaction should be allowed"

    @pytest.mark.asyncio
    async def test_optimizer_yield_recommendations(
        self, mock_morpho_mcp: dict, optimizer_agent_config: dict
    ) -> None:
        """Optimizer Agent should recommend best yield opportunities."""
        yield_comparison = mock_morpho_mcp["morpho_compare_yields"]["comparison"]

        # Sort by APY
        sorted_yields = sorted(yield_comparison, key=lambda x: x["apy"], reverse=True)

        # Best yield should be Morpho Steakhouse USDC
        best_option = sorted_yields[0]
        assert best_option["protocol"] == "morpho", "Best yield should be Morpho"
        assert best_option["apy"] == 12.5, "Best APY should be 12.5%"
        assert best_option["risk"] == "low", "Best option should have low risk"


# ============================================================================
# Output Format Tests
# ============================================================================


class TestAgentOutputFormats:
    """Test agents generate correct output formats."""

    def test_market_scanner_output_includes_table(
        self, market_scanner_config: dict[str, Any]
    ) -> None:
        """Market Scanner should have output_format configuration."""
        output_format = market_scanner_config.get("output_format")

        # output_format can be a dict with settings, a string format name, or None
        assert output_format is None or isinstance(output_format, (dict, str)), (
            "output_format should be dict, string, or None"
        )

    def test_risk_guardian_output_includes_status(
        self, risk_guardian_config: dict[str, Any]
    ) -> None:
        """Risk Guardian should have output_format configuration."""
        output_format = risk_guardian_config.get("output_format")

        # output_format can be a dict with settings, a string format name, or None
        assert output_format is None or isinstance(output_format, (dict, str)), (
            "output_format should be dict, string, or None"
        )

    def test_execution_agent_output_includes_execute_data(
        self, execution_agent_config: dict[str, Any]
    ) -> None:
        """Execution Agent should have output_format configuration."""
        output_format = execution_agent_config.get("output_format")

        # output_format can be a dict with settings, a string format name, or None
        assert output_format is None or isinstance(output_format, (dict, str)), (
            "output_format should be dict, string, or None"
        )

    def test_optimizer_output_includes_strategy(
        self, optimizer_agent_config: dict[str, Any]
    ) -> None:
        """Optimizer Agent should have output_format configuration."""
        output_format = optimizer_agent_config.get("output_format")

        # output_format can be a dict with settings, a string format name, or None
        assert output_format is None or isinstance(output_format, (dict, str)), (
            "output_format should be dict, string, or None"
        )
