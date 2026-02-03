"""
Unit tests for lending shortcuts configuration.

Tests pattern matching, parameter extraction, agent routing, balance check
integration, and health factor validation for all 6 lending shortcuts across
all 4 supported languages (en, es, pt, zh).
"""

import json
import re
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


# Load shortcuts.json fixture
@pytest.fixture(scope="module")
def shortcuts_config() -> dict[str, Any]:
    """Load shortcuts.json configuration."""
    shortcuts_path = Path(__file__).parent.parent.parent.parent.parent / "anvil_knowledge" / "features" / "shortcuts.json"
    with open(shortcuts_path, "r") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def lending_shortcuts(shortcuts_config: dict[str, Any]) -> dict[str, Any]:
    """Extract lending shortcuts from config."""
    return shortcuts_config["lending"]


class TestLendingShortcutsStructure:
    """Test basic structure and metadata of lending shortcuts."""

    def test_lending_category_exists(self, shortcuts_config: dict[str, Any]) -> None:
        """Test that lending category exists in shortcuts.json."""
        assert "lending" in shortcuts_config
        assert shortcuts_config["lending"]["title"] == "💰 Lending & Yield"

    def test_all_six_intents_defined(self, lending_shortcuts: dict[str, Any]) -> None:
        """Test that all 6 lending intents are defined."""
        expected_intents = [
            "LENDING_HEALTH_CHECK",
            "LENDING_SUPPLY",
            "LENDING_BORROW",
            "LENDING_LOOP",
            "LENDING_COMPARE",
            "LENDING_POSITION",
        ]

        intent_group = lending_shortcuts["intent_group"]
        assert len(intent_group) == 6
        assert set(intent_group) == set(expected_intents)

    def test_protocols_supported(self, lending_shortcuts: dict[str, Any]) -> None:
        """Test that Morpho and Aave V3 are supported."""
        protocols = lending_shortcuts["protocols_supported"]
        assert "Morpho" in protocols
        assert "Aave V3" in protocols

    def test_chains_supported(self, lending_shortcuts: dict[str, Any]) -> None:
        """Test that major chains are supported."""
        chains = lending_shortcuts["chains_supported"]
        assert "Ethereum" in chains
        assert "Base" in chains
        assert "Arbitrum" in chains
        assert "Optimism" in chains


class TestHealthCheckShortcut:
    """Test LENDING_HEALTH_CHECK shortcut."""

    @pytest.fixture
    def health_check_shortcut(self, lending_shortcuts: dict[str, Any]) -> dict[str, Any]:
        """Get LENDING_HEALTH_CHECK shortcut config."""
        commands = lending_shortcuts["commands"]
        return next(cmd for cmd in commands if cmd["intent"] == "LENDING_HEALTH_CHECK")

    def test_intent_and_category(self, health_check_shortcut: dict[str, Any]) -> None:
        """Test intent and category are correct."""
        assert health_check_shortcut["intent"] == "LENDING_HEALTH_CHECK"
        assert health_check_shortcut["category"] == "lending"

    def test_multi_language_descriptions(self, health_check_shortcut: dict[str, Any]) -> None:
        """Test that descriptions exist for all 4 languages."""
        descriptions = health_check_shortcut["description"]
        assert "en" in descriptions
        assert "es" in descriptions
        assert "pt" in descriptions
        assert "zh" in descriptions

        # Check English description
        assert "health factor" in descriptions["en"].lower()

    def test_english_patterns(self, health_check_shortcut: dict[str, Any]) -> None:
        """Test English pattern matching."""
        patterns = health_check_shortcut["patterns"]["en"]

        # Must have key patterns
        assert any("lending health" in p.lower() for p in patterns)
        assert any("health factor" in p.lower() for p in patterns)
        assert any("liquidation" in p.lower() for p in patterns)

    def test_spanish_patterns(self, health_check_shortcut: dict[str, Any]) -> None:
        """Test Spanish pattern matching."""
        patterns = health_check_shortcut["patterns"]["es"]

        # Check Spanish-specific patterns
        assert any("factor de salud" in p.lower() for p in patterns)
        assert any("liquidación" in p.lower() for p in patterns)

    def test_portuguese_patterns(self, health_check_shortcut: dict[str, Any]) -> None:
        """Test Portuguese pattern matching."""
        patterns = health_check_shortcut["patterns"]["pt"]

        # Check Portuguese-specific patterns
        assert any("fator de saúde" in p.lower() or "fator de saude" in p.lower() for p in patterns)
        assert any("liquidação" in p.lower() or "liquidacao" in p.lower() for p in patterns)

    def test_chinese_patterns(self, health_check_shortcut: dict[str, Any]) -> None:
        """Test Chinese pattern matching."""
        patterns = health_check_shortcut["patterns"]["zh"]

        # Check Chinese-specific patterns
        assert any("健康因子" in p for p in patterns)
        assert any("清算" in p for p in patterns)

    def test_agent_routing(self, health_check_shortcut: dict[str, Any]) -> None:
        """Test agent routing configuration."""
        assert health_check_shortcut["agent"] == "LENDING_WORKFLOW"
        assert health_check_shortcut["parameters"]["action"] == "health_check"

    def test_authentication_requirements(self, health_check_shortcut: dict[str, Any]) -> None:
        """Test authentication and wallet requirements."""
        assert health_check_shortcut["requires_auth"] is True
        assert health_check_shortcut["requires_wallet"] is True


class TestSupplyShortcut:
    """Test LENDING_SUPPLY shortcut."""

    @pytest.fixture
    def supply_shortcut(self, lending_shortcuts: dict[str, Any]) -> dict[str, Any]:
        """Get LENDING_SUPPLY shortcut config."""
        commands = lending_shortcuts["commands"]
        return next(cmd for cmd in commands if cmd["intent"] == "LENDING_SUPPLY")

    def test_intent_and_category(self, supply_shortcut: dict[str, Any]) -> None:
        """Test intent and category are correct."""
        assert supply_shortcut["intent"] == "LENDING_SUPPLY"
        assert supply_shortcut["category"] == "lending"

    def test_parameter_extraction_amount(self, supply_shortcut: dict[str, Any]) -> None:
        """Test amount parameter extraction configuration."""
        amount_config = supply_shortcut["parameter_extraction"]["amount"]

        assert amount_config["type"] == "decimal"
        assert amount_config["required"] is False
        assert "regex" in amount_config

        # Test regex can match numbers
        regex = amount_config["regex"]
        assert re.search(regex, "supply 1000 USDC")
        assert re.search(regex, "supply 1000.5 USDC")

    def test_parameter_extraction_asset(self, supply_shortcut: dict[str, Any]) -> None:
        """Test asset parameter extraction configuration."""
        asset_config = supply_shortcut["parameter_extraction"]["asset"]

        assert asset_config["type"] == "string"
        assert asset_config["required"] is True
        assert asset_config["case_insensitive"] is True

        # Check valid values
        valid_assets = asset_config["valid_values"]
        assert "USDC" in valid_assets
        assert "ETH" in valid_assets
        assert "DAI" in valid_assets

        # Test regex
        regex = asset_config["regex"]
        assert re.search(regex, "supply 1000 USDC")
        assert re.search(regex, "supply 1 ETH")
        assert re.search(regex, "supply 5000 DAI")

    def test_parameter_extraction_protocol(self, supply_shortcut: dict[str, Any]) -> None:
        """Test protocol parameter extraction configuration."""
        protocol_config = supply_shortcut["parameter_extraction"]["protocol"]

        assert protocol_config["type"] == "string"
        assert protocol_config["default"] == "morpho"
        assert "aave" in protocol_config["valid_values"]
        assert "morpho" in protocol_config["valid_values"]

    def test_balance_validation_config(self, supply_shortcut: dict[str, Any]) -> None:
        """Test balance check configuration."""
        validation = supply_shortcut["validation"]

        assert validation["balance_check"] is True
        assert validation["balance_checker_port"] == "IBalanceChecker"
        assert "minimum_gas" in validation
        assert "0.01" in validation["minimum_gas"]

    def test_multi_language_prompts(self, supply_shortcut: dict[str, Any]) -> None:
        """Test that parameter prompts support all languages."""
        amount_prompts = supply_shortcut["parameter_extraction"]["amount"]["prompt_if_missing"]
        asset_prompts = supply_shortcut["parameter_extraction"]["asset"]["prompt_if_missing"]

        for prompts in [amount_prompts, asset_prompts]:
            assert "en" in prompts
            assert "es" in prompts
            assert "pt" in prompts
            assert "zh" in prompts


class TestBorrowShortcut:
    """Test LENDING_BORROW shortcut."""

    @pytest.fixture
    def borrow_shortcut(self, lending_shortcuts: dict[str, Any]) -> dict[str, Any]:
        """Get LENDING_BORROW shortcut config."""
        commands = lending_shortcuts["commands"]
        return next(cmd for cmd in commands if cmd["intent"] == "LENDING_BORROW")

    def test_intent_and_category(self, borrow_shortcut: dict[str, Any]) -> None:
        """Test intent and category are correct."""
        assert borrow_shortcut["intent"] == "LENDING_BORROW"
        assert borrow_shortcut["category"] == "lending"

    def test_health_factor_validation_config(self, borrow_shortcut: dict[str, Any]) -> None:
        """Test health factor validation configuration."""
        validation = borrow_shortcut["validation"]

        assert validation["health_factor_check"] is True
        assert validation["minimum_health_factor_after"] == 1.2
        assert validation["warn_if_hf_below"] == 1.5
        assert validation["reject_if_hf_below"] == 1.1

    def test_collateral_requirement(self, borrow_shortcut: dict[str, Any]) -> None:
        """Test that collateral is required."""
        assert borrow_shortcut["requires_collateral"] is True

    def test_safety_warnings(self, borrow_shortcut: dict[str, Any]) -> None:
        """Test that safety warnings exist for all languages."""
        warnings = borrow_shortcut["safety_warning"]

        assert "en" in warnings
        assert "es" in warnings
        assert "pt" in warnings
        assert "zh" in warnings

        # Check English warning mentions key risks
        en_warning = warnings["en"].lower()
        assert "liquidation" in en_warning or "risk" in en_warning
        assert "health factor" in en_warning or "1.5" in warnings["en"]

    def test_agent_routing(self, borrow_shortcut: dict[str, Any]) -> None:
        """Test agent routing for borrow operations."""
        assert borrow_shortcut["agent"] == "LENDING_BORROWING"
        assert borrow_shortcut["parameters"]["action"] == "borrow"


class TestLeverageLoopShortcut:
    """Test LENDING_LOOP shortcut."""

    @pytest.fixture
    def loop_shortcut(self, lending_shortcuts: dict[str, Any]) -> dict[str, Any]:
        """Get LENDING_LOOP shortcut config."""
        commands = lending_shortcuts["commands"]
        return next(cmd for cmd in commands if cmd["intent"] == "LENDING_LOOP")

    def test_intent_and_category(self, loop_shortcut: dict[str, Any]) -> None:
        """Test intent and category are correct."""
        assert loop_shortcut["intent"] == "LENDING_LOOP"
        assert loop_shortcut["category"] == "lending"

    def test_leverage_multiplier_extraction(self, loop_shortcut: dict[str, Any]) -> None:
        """Test leverage multiplier parameter extraction."""
        multiplier_config = loop_shortcut["parameter_extraction"]["leverage_multiplier"]

        assert multiplier_config["type"] == "integer"
        assert multiplier_config["default"] == 3
        assert multiplier_config["min"] == 2
        assert multiplier_config["max"] == 4

        # Test regex can match leverage multipliers
        regex = multiplier_config["regex"]
        assert re.search(regex, "3x leverage")
        assert re.search(regex, "2x ETH")
        assert re.search(regex, "4x wstETH")

    def test_multi_step_approval(self, loop_shortcut: dict[str, Any]) -> None:
        """Test multi-step approval configuration."""
        assert loop_shortcut["multi_step_approval"] is True
        assert loop_shortcut["approval_steps"] == 3

    def test_risk_level(self, loop_shortcut: dict[str, Any]) -> None:
        """Test that risk level is marked as HIGH."""
        assert loop_shortcut["risk_level"] == "HIGH"

    def test_high_risk_warnings(self, loop_shortcut: dict[str, Any]) -> None:
        """Test that high-risk warnings exist and mention key risks."""
        warnings = loop_shortcut["safety_warning"]

        for lang in ["en", "es", "pt", "zh"]:
            assert lang in warnings

        # English warning should mention:
        # 1. High risk
        # 2. Leverage amplifies gains and losses
        # 3. Multiple transactions required
        en_warning = warnings["en"]
        assert "HIGH RISK" in en_warning or "ALTO RIESGO" in warnings["es"]
        assert "3+" in en_warning or "3" in en_warning  # Multiple transactions

    def test_supported_assets(self, loop_shortcut: dict[str, Any]) -> None:
        """Test that only ETH-based assets are supported for loops."""
        asset_config = loop_shortcut["parameter_extraction"]["asset"]
        valid_assets = asset_config["valid_values"]

        # Only ETH, WETH, wstETH should be supported (not stablecoins)
        assert "ETH" in valid_assets
        assert "WETH" in valid_assets
        assert "wstETH" in valid_assets
        assert "USDC" not in valid_assets  # Stablecoins not supported for loops


class TestCompareShortcut:
    """Test LENDING_COMPARE shortcut."""

    @pytest.fixture
    def compare_shortcut(self, lending_shortcuts: dict[str, Any]) -> dict[str, Any]:
        """Get LENDING_COMPARE shortcut config."""
        commands = lending_shortcuts["commands"]
        return next(cmd for cmd in commands if cmd["intent"] == "LENDING_COMPARE")

    def test_intent_and_category(self, compare_shortcut: dict[str, Any]) -> None:
        """Test intent and category are correct."""
        assert compare_shortcut["intent"] == "LENDING_COMPARE"
        assert compare_shortcut["category"] == "lending"

    def test_guest_access(self, compare_shortcut: dict[str, Any]) -> None:
        """Test that guests can access comparison feature."""
        assert compare_shortcut["requires_auth"] is False
        assert compare_shortcut["guest_allowed"] is True

    def test_response_format_config(self, compare_shortcut: dict[str, Any]) -> None:
        """Test response format configuration."""
        response_format = compare_shortcut["response_format"]

        assert response_format["include_table"] is True
        assert response_format["sort_by"] == "apy"
        assert response_format["limit"] == 5
        assert response_format["include_risk_tier"] is True
        assert response_format["include_tvl"] is True

    def test_default_parameters(self, compare_shortcut: dict[str, Any]) -> None:
        """Test default parameter values."""
        asset_config = compare_shortcut["parameter_extraction"]["asset"]
        chain_config = compare_shortcut["parameter_extraction"]["chain"]

        assert asset_config["default"] == "USDC"
        assert chain_config["default"] == "base"

    def test_agent_routing(self, compare_shortcut: dict[str, Any]) -> None:
        """Test agent routing for comparison."""
        assert compare_shortcut["agent"] == "DEFI_YIELD"
        assert compare_shortcut["parameters"]["action"] == "compare_rates"


class TestPositionShortcut:
    """Test LENDING_POSITION shortcut."""

    @pytest.fixture
    def position_shortcut(self, lending_shortcuts: dict[str, Any]) -> dict[str, Any]:
        """Get LENDING_POSITION shortcut config."""
        commands = lending_shortcuts["commands"]
        return next(cmd for cmd in commands if cmd["intent"] == "LENDING_POSITION")

    def test_intent_and_category(self, position_shortcut: dict[str, Any]) -> None:
        """Test intent and category are correct."""
        assert position_shortcut["intent"] == "LENDING_POSITION"
        assert position_shortcut["category"] == "lending"

    def test_authentication_requirements(self, position_shortcut: dict[str, Any]) -> None:
        """Test authentication and wallet requirements."""
        assert position_shortcut["requires_auth"] is True
        assert position_shortcut["requires_wallet"] is True

    def test_response_format_config(self, position_shortcut: dict[str, Any]) -> None:
        """Test response format configuration."""
        response_format = position_shortcut["response_format"]

        assert response_format["group_by_protocol"] is True
        assert response_format["show_total_value"] is True
        assert response_format["show_weighted_apy"] is True
        assert response_format["show_earnings_summary"] is True
        assert response_format["show_optimization_opportunities"] is True


class TestAgentRouting:
    """Test agent routing configuration for all lending shortcuts."""

    def test_all_intents_have_routing(self, lending_shortcuts: dict[str, Any]) -> None:
        """Test that all 6 intents have routing configuration."""
        routing = lending_shortcuts["routing"]
        expected_intents = [
            "LENDING_HEALTH_CHECK",
            "LENDING_SUPPLY",
            "LENDING_BORROW",
            "LENDING_LOOP",
            "LENDING_COMPARE",
            "LENDING_POSITION",
        ]

        for intent in expected_intents:
            assert intent in routing
            assert "agent" in routing[intent]
            assert "action" in routing[intent]
            assert "mcp_tools" in routing[intent]
            assert "validation" in routing[intent]

    def test_health_check_routing(self, lending_shortcuts: dict[str, Any]) -> None:
        """Test LENDING_HEALTH_CHECK routing configuration."""
        routing = lending_shortcuts["routing"]["LENDING_HEALTH_CHECK"]

        assert routing["agent"] == "LENDING_WORKFLOW"
        assert routing["action"] == "health_check"
        assert "aave_get_user_positions" in routing["mcp_tools"]
        assert "aave_calculate_health_factor" in routing["mcp_tools"]

    def test_supply_routing(self, lending_shortcuts: dict[str, Any]) -> None:
        """Test LENDING_SUPPLY routing configuration."""
        routing = lending_shortcuts["routing"]["LENDING_SUPPLY"]

        assert routing["agent"] == "LENDING_WORKFLOW"
        assert routing["action"] == "supply"
        assert "balance_check" in routing["validation"]
        assert "gas_check" in routing["validation"]
        assert "morpho_get_vaults" in routing["mcp_tools"]

    def test_borrow_routing(self, lending_shortcuts: dict[str, Any]) -> None:
        """Test LENDING_BORROW routing configuration."""
        routing = lending_shortcuts["routing"]["LENDING_BORROW"]

        assert routing["agent"] == "LENDING_BORROWING"
        assert routing["action"] == "borrow"
        assert "health_factor_check" in routing["validation"]
        assert "collateral_check" in routing["validation"]

    def test_loop_routing(self, lending_shortcuts: dict[str, Any]) -> None:
        """Test LENDING_LOOP routing configuration."""
        routing = lending_shortcuts["routing"]["LENDING_LOOP"]

        assert routing["agent"] == "LENDING_BORROWING"
        assert routing["action"] == "leverage_loop"
        assert routing["workflow_type"] == "multi_step"
        assert "multi_step_approval" in routing["validation"]


class TestImplementationNotes:
    """Test implementation notes for proper guidance."""

    def test_implementation_notes_exist(self, lending_shortcuts: dict[str, Any]) -> None:
        """Test that implementation notes exist."""
        assert "implementation_notes" in lending_shortcuts
        notes = lending_shortcuts["implementation_notes"]

        # Check all critical implementation notes exist
        assert "balance_validation" in notes
        assert "health_factor_validation" in notes
        assert "leverage_loop_approvals" in notes
        assert "guest_restrictions" in notes
        assert "multi_language_support" in notes

    def test_critical_safety_notes(self, lending_shortcuts: dict[str, Any]) -> None:
        """Test that critical safety notes are present."""
        notes = lending_shortcuts["implementation_notes"]

        # Balance validation note
        assert "BEFORE" in notes["balance_validation"]

        # Health factor validation note
        assert "1.2" in notes["health_factor_validation"]

        # No batch processing note
        assert "NO batch" in notes["leverage_loop_approvals"] or "3+" in notes["leverage_loop_approvals"]


class TestParameterExtractionRegex:
    """Test parameter extraction regex patterns work correctly."""

    def test_amount_regex_patterns(self, lending_shortcuts: dict[str, Any]) -> None:
        """Test that amount regex can extract decimal numbers."""
        supply_cmd = next(cmd for cmd in lending_shortcuts["commands"] if cmd["intent"] == "LENDING_SUPPLY")
        amount_regex = supply_cmd["parameter_extraction"]["amount"]["regex"]

        # Test various amount formats
        test_cases = [
            ("supply 1000 USDC", "1000"),
            ("deposit 1000.5 ETH", "1000.5"),
            ("lend 0.5 WBTC", "0.5"),
            ("supply 10000000 DAI", "10000000"),
        ]

        for test_input, expected in test_cases:
            match = re.search(amount_regex, test_input)
            assert match is not None, f"Failed to match: {test_input}"
            assert match.group(1) == expected

    def test_asset_regex_patterns(self, lending_shortcuts: dict[str, Any]) -> None:
        """Test that asset regex can extract token symbols."""
        supply_cmd = next(cmd for cmd in lending_shortcuts["commands"] if cmd["intent"] == "LENDING_SUPPLY")
        asset_regex = supply_cmd["parameter_extraction"]["asset"]["regex"]

        # Test various asset symbols
        test_cases = [
            "supply 1000 USDC",
            "deposit ETH to earn",
            "lend my DAI",
            "supply WBTC",
            "deposit wstETH",
        ]

        for test_input in test_cases:
            match = re.search(asset_regex, test_input, re.IGNORECASE)
            assert match is not None, f"Failed to match: {test_input}"

    def test_leverage_multiplier_regex(self, lending_shortcuts: dict[str, Any]) -> None:
        """Test that leverage multiplier regex works."""
        loop_cmd = next(cmd for cmd in lending_shortcuts["commands"] if cmd["intent"] == "LENDING_LOOP")
        multiplier_regex = loop_cmd["parameter_extraction"]["leverage_multiplier"]["regex"]

        # Test multiplier extraction
        test_cases = [
            ("3x leverage on ETH", "3"),
            ("2x ETH", "2"),
            ("4x wstETH", "4"),
        ]

        for test_input, expected in test_cases:
            match = re.search(multiplier_regex, test_input)
            assert match is not None, f"Failed to match: {test_input}"
            assert match.group(1) == expected


class TestMultiLanguageSupport:
    """Test multi-language support across all shortcuts."""

    @pytest.mark.parametrize("language", ["en", "es", "pt", "zh"])
    def test_all_shortcuts_have_language(
        self,
        lending_shortcuts: dict[str, Any],
        language: str
    ) -> None:
        """Test that all shortcuts have patterns for all languages."""
        for command in lending_shortcuts["commands"]:
            patterns = command["patterns"]
            assert language in patterns, f"{command['intent']} missing {language} patterns"
            assert len(patterns[language]) > 0, f"{command['intent']} has empty {language} patterns"

    def test_chinese_characters(self, lending_shortcuts: dict[str, Any]) -> None:
        """Test that Chinese patterns use proper characters."""
        for command in lending_shortcuts["commands"]:
            zh_patterns = command["patterns"]["zh"]

            # Check at least one pattern has Chinese characters
            has_chinese = any(
                any("\u4e00" <= char <= "\u9fff" for char in pattern)
                for pattern in zh_patterns
            )
            assert has_chinese, f"{command['intent']} missing Chinese characters"

    def test_spanish_accents(self, lending_shortcuts: dict[str, Any]) -> None:
        """Test that Spanish patterns use proper accents where needed."""
        for command in lending_shortcuts["commands"]:
            es_patterns = command["patterns"]["es"]

            # Check that common Spanish words have accents
            patterns_text = " ".join(es_patterns).lower()

            # Common lending terms that should have accents
            if "prestamo" in patterns_text or "préstamo" in patterns_text:
                assert "préstamo" in patterns_text, f"{command['intent']} missing Spanish accents"
