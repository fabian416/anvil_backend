"""
Knowledge Base Injector for LLM Context Enhancement

This module dynamically injects relevant knowledge from JSON files into LLM prompts
to provide accurate, detailed responses about Anvil features for users and investors.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from enum import Enum


class KnowledgeFile(str, Enum):
    """Available knowledge base files"""
    OVERVIEW = "overview"
    SWAP = "swap"
    HUNTER_AI = "hunter_ai"
    ULTRA = "ultra"
    SHORTCUTS = "shortcuts"
    PORTFOLIO = "portfolio"
    WALLET = "wallet"
    LENDING_MORPHO = "lending_morpho"
    GAS_OPTIMIZER = "gas_optimizer"
    RISK_ANALYZER = "risk_analyzer"
    MONEY_MARKET = "money_market"


class KnowledgeInjector:
    """
    Dynamically selects and injects relevant knowledge into LLM prompts based on
    user queries and detected intents.
    """

    def __init__(self, knowledge_base_path: Optional[Path] = None):
        """
        Initialize knowledge injector with path to knowledge base directory.

        Args:
            knowledge_base_path: Path to anvil_knowledge directory.
                                Defaults to project root / anvil_knowledge
        """
        if knowledge_base_path is None:
            # Default to project root / anvil_knowledge
            # File is at: src/app/application/chat/services/knowledge_injector.py
            # Need 6 parents to get to project root: services -> chat -> application -> app -> src -> anvil_backend
            current_file = Path(__file__)
            project_root = current_file.parent.parent.parent.parent.parent.parent
            knowledge_base_path = project_root / "anvil_knowledge"

        self.knowledge_base_path = knowledge_base_path
        self.features_path = knowledge_base_path / "features"

        # Cache for loaded JSON files to avoid repeated file I/O
        self._cache: Dict[str, Dict[str, Any]] = {}

    def _load_json(self, filename: KnowledgeFile) -> Dict[str, Any]:
        """
        Load JSON file from features directory with caching.

        Args:
            filename: Name of JSON file (without .json extension)

        Returns:
            Parsed JSON as dictionary
        """
        if filename not in self._cache:
            file_path = self.features_path / f"{filename.value}.json"
            with open(file_path, 'r', encoding='utf-8') as f:
                self._cache[filename] = json.load(f)

        return self._cache[filename]

    def get_knowledge_for_intent(
        self,
        user_query: str,
        detected_intent: str,
        user_type: str = "user"  # "user" or "investor"
    ) -> Dict[str, Any]:
        """
        Get relevant knowledge sections based on intent and user type.

        Args:
            user_query: The user's original message
            detected_intent: Intent detected by intent_detector_v2
            user_type: "user" for end users, "investor" for investor queries

        Returns:
            Dictionary with relevant knowledge sections
        """
        query_lower = user_query.lower()

        # Overview queries - "what can you do?"
        if any(kw in query_lower for kw in ["what can you do", "capabilities", "features", "what is anvil"]):
            return self._get_overview_knowledge(user_type)

        # Hunter AI intents
        if detected_intent.startswith("HUNTER_"):
            return self._get_hunter_ai_knowledge(detected_intent, query_lower, user_type)

        # ULTRA intents
        if detected_intent.startswith("ULTRA_"):
            return self._get_ultra_knowledge(detected_intent, query_lower, user_type)

        # Swap intent
        if detected_intent == "SWAP":
            return self._get_swap_knowledge(query_lower, user_type)

        # Command help / shortcuts
        if any(kw in query_lower for kw in ["command", "how do i", "how to", "syntax", "example"]):
            return self._get_shortcuts_knowledge(detected_intent)

        # Portfolio queries
        if any(kw in query_lower for kw in ["portfolio", "balance", "holdings", "my assets", "my tokens"]):
            return self._get_portfolio_knowledge(user_type)

        # Wallet queries
        if any(kw in query_lower for kw in ["wallet", "wallets", "my wallet", "export wallet", "sync wallet"]):
            return self._get_wallet_knowledge(user_type)

        # Lending queries (Morpho)
        if any(kw in query_lower for kw in ["lending", "lend", "morpho", "vault", "supply", "deposit assets", "earn yield"]):
            return self._get_lending_morpho_knowledge(user_type)

        # Gas optimizer queries
        if any(kw in query_lower for kw in ["gas", "gas price", "gas cost", "transaction fee", "optimize gas"]):
            return self._get_gas_optimizer_knowledge(user_type)

        # Risk analyzer queries
        if any(kw in query_lower for kw in ["risk", "safe", "safety", "protocol risk", "tvl", "risk analysis"]):
            return self._get_risk_analyzer_knowledge(user_type)

        # Money market queries (rate comparison, Aave vs Compound)
        if any(kw in query_lower for kw in ["money market", "lending rate", "borrowing rate", "apy comparison", "compare rates", "aave rate", "compound rate", "best rate", "supply apy", "borrow apy"]):
            return self._get_money_market_knowledge(user_type)

        # Default to overview
        return self._get_overview_knowledge(user_type)

    def _get_overview_knowledge(self, user_type: str) -> Dict[str, Any]:
        """Get overview knowledge tailored to user type"""
        overview = self._load_json(KnowledgeFile.OVERVIEW)

        if user_type == "investor":
            return {
                "feature_name": overview["feature_name"],
                "core_capabilities": overview["core_capabilities"],
                "unique_features": overview["unique_features"],
                "competitive_advantages": overview["getting_started"]["for_investors"]["competitive_advantages"],
                "value_proposition": overview["getting_started"]["for_investors"]["value_proposition"],
                "market_position": overview["getting_started"]["for_investors"]["market_position"],
                "supported_protocols": overview["supported_protocols"]
            }
        else:
            return {
                "feature_name": overview["feature_name"],
                "tagline": overview["tagline"],
                "core_capabilities": overview["core_capabilities"],
                "unique_features": overview["unique_features"],
                "getting_started": overview["getting_started"]["for_users"],
                "example_use_cases": overview["example_use_cases"]
            }

    def _get_hunter_ai_knowledge(
        self,
        detected_intent: str,
        query_lower: str,
        user_type: str
    ) -> Dict[str, Any]:
        """Get Hunter AI knowledge based on specific intent"""
        hunter_ai = self._load_json(KnowledgeFile.HUNTER_AI)

        # Map intent to capability index
        capability_map = {
            "HUNTER_SENTIMENT": 0,
            "HUNTER_PRICE_PREDICTION": 1,
            "HUNTER_RISK_SIGNALS": 2,
            "HUNTER_TRADING_SIGNALS": 3,
            "HUNTER_PATTERNS": 4,
            "HUNTER_PORTFOLIO": 5
        }

        base_knowledge = {
            "feature_name": hunter_ai["feature_name"],
            "tagline": hunter_ai["tagline"],
            "description": hunter_ai["description"]
        }

        # Add specific capability if intent matches
        if detected_intent in capability_map:
            idx = capability_map[detected_intent]
            base_knowledge["capability"] = hunter_ai["core_capabilities"][idx]

        # Add accuracy metrics if query mentions accuracy, performance, or reliability
        if any(kw in query_lower for kw in ["accurate", "accuracy", "reliable", "performance", "work"]):
            base_knowledge["accuracy_metrics"] = hunter_ai["accuracy_metrics"]
            base_knowledge["real_vs_demo_data"] = hunter_ai["real_vs_demo_data"]

        # Add investor highlights for investors
        if user_type == "investor":
            base_knowledge["competitive_advantages"] = hunter_ai["competitive_advantages"]
            base_knowledge["investor_highlights"] = hunter_ai["investor_highlights"]

        # Add data sources if query mentions sources or data
        if any(kw in query_lower for kw in ["source", "data", "where", "how"]):
            base_knowledge["data_sources_detail"] = hunter_ai["data_sources_detail"]

        return base_knowledge

    def _get_ultra_knowledge(
        self,
        detected_intent: str,
        query_lower: str,
        user_type: str
    ) -> Dict[str, Any]:
        """Get ULTRA knowledge based on specific intent"""
        ultra = self._load_json(KnowledgeFile.ULTRA)

        # Map intent to capability index
        capability_map = {
            "ULTRA_ARBITRAGE": 0,
            "ULTRA_FLASH_LOANS": 1,
            "ULTRA_MEV_PROTECTION": 2,
            "ULTRA_AUTO_EXECUTOR": 3
        }

        base_knowledge = {
            "feature_name": ultra["feature_name"],
            "tagline": ultra["tagline"],
            "description": ultra["description"]
        }

        # Add specific capability if intent matches
        if detected_intent in capability_map:
            idx = capability_map[detected_intent]
            base_knowledge["capability"] = ultra["core_capabilities"][idx]

        # Add accuracy/performance metrics
        if any(kw in query_lower for kw in ["accurate", "accuracy", "performance", "profit", "roi"]):
            base_knowledge["accuracy_metrics"] = ultra["accuracy_metrics"]

        # Add investor highlights for investors
        if user_type == "investor":
            base_knowledge["competitive_advantages"] = ultra["competitive_advantages"]
            base_knowledge["investor_highlights"] = ultra["investor_highlights"]

        # Add data sources and real vs demo
        if any(kw in query_lower for kw in ["source", "data", "real", "simulated"]):
            base_knowledge["real_vs_demo_data"] = ultra["real_vs_demo_data"]
            base_knowledge["data_sources_detail"] = ultra["data_sources_detail"]

        # Add common questions if user seems confused
        if any(kw in query_lower for kw in ["how", "what", "why", "explain"]):
            base_knowledge["common_questions"] = ultra["common_questions"]

        return base_knowledge

    def _get_swap_knowledge(self, query_lower: str, user_type: str) -> Dict[str, Any]:
        """Get swap knowledge"""
        swap = self._load_json(KnowledgeFile.SWAP)

        base_knowledge = {
            "feature_name": swap["feature_name"],
            "description": swap["description"],
        }
        
        # Always include aggregator details for "what type" queries
        if any(kw in query_lower for kw in ["what type", "what types", "what can", "types of", "which", "what swaps"]):
            base_knowledge["supported_aggregators"] = swap["supported_aggregators"]
            base_knowledge["supported_tokens"] = swap.get("supported_tokens", {})
            base_knowledge["features"] = swap.get("features", [])
            base_knowledge["command_formats"] = swap.get("command_formats", {})
        else:
            base_knowledge["how_it_works"] = swap.get("how_it_works", {})
            base_knowledge["supported_aggregators"] = swap["supported_aggregators"]

        # Add rate comparison example if asking about rates or savings
        if any(kw in query_lower for kw in ["rate", "price", "cost", "save", "cheap", "best"]):
            base_knowledge["rate_comparison_example"] = swap["rate_comparison_example"]

        # Add safety features if asking about safety, risk, or security
        if any(kw in query_lower for kw in ["safe", "risk", "secure", "protect", "mev"]):
            base_knowledge["safety_features"] = swap["safety_features"]
            base_knowledge["features"] = swap["features"]

        # Add investor highlights for investors
        if user_type == "investor":
            base_knowledge["investor_highlights"] = swap["investor_highlights"]

        # Add common questions
        if any(kw in query_lower for kw in ["how", "what", "why"]):
            base_knowledge["common_questions"] = swap["common_questions"]

        return base_knowledge

    def _get_shortcuts_knowledge(self, detected_intent: str) -> Dict[str, Any]:
        """Get shortcuts/commands knowledge"""
        shortcuts = self._load_json(KnowledgeFile.SHORTCUTS)

        return {
            "feature_name": shortcuts["feature_name"],
            "overview": shortcuts["overview"],
            "quick_start_commands": shortcuts["quick_start_commands"],
            "command_categories": shortcuts["command_categories"],
            "power_user_tips": shortcuts["power_user_tips"],
            "multi_step_flows": shortcuts["multi_step_flows"]
        }

    def _get_portfolio_knowledge(self, user_type: str) -> Dict[str, Any]:
        """Get portfolio management knowledge"""
        portfolio = self._load_json(KnowledgeFile.PORTFOLIO)

        base_knowledge = {
            "feature_name": portfolio["feature_name"],
            "tagline": portfolio["tagline"],
            "description": portfolio["description"],
            "core_capabilities": portfolio["core_capabilities"],
            "api_endpoints": portfolio["api_endpoints"],
            "features": portfolio["features"]
        }

        if user_type == "investor":
            base_knowledge["competitive_advantages"] = portfolio["competitive_advantages"]
            base_knowledge["getting_started"] = portfolio["getting_started"]["for_investors"]

        return base_knowledge

    def _get_wallet_knowledge(self, user_type: str) -> Dict[str, Any]:
        """Get wallet management knowledge"""
        wallet = self._load_json(KnowledgeFile.WALLET)

        base_knowledge = {
            "feature_name": wallet["feature_name"],
            "tagline": wallet["tagline"],
            "description": wallet["description"],
            "core_capabilities": wallet["core_capabilities"],
            "api_endpoints": wallet["api_endpoints"],
            "features": wallet["features"]
        }

        if user_type == "investor":
            base_knowledge["competitive_advantages"] = wallet["competitive_advantages"]
            base_knowledge["getting_started"] = wallet["getting_started"]["for_investors"]

        return base_knowledge

    def _get_lending_morpho_knowledge(self, user_type: str) -> Dict[str, Any]:
        """Get Morpho lending knowledge"""
        lending = self._load_json(KnowledgeFile.LENDING_MORPHO)

        base_knowledge = {
            "feature_name": lending["feature_name"],
            "tagline": lending["tagline"],
            "description": lending["description"],
            "core_capabilities": lending["core_capabilities"],
            "api_endpoints": lending["api_endpoints"],
            "features": lending["features"],
            "important_notes": lending.get("important_notes", [])
        }

        if user_type == "investor":
            base_knowledge["competitive_advantages"] = lending["competitive_advantages"]
            base_knowledge["getting_started"] = lending["getting_started"]["for_investors"]

        return base_knowledge

    def _get_gas_optimizer_knowledge(self, user_type: str) -> Dict[str, Any]:
        """Get gas optimizer agent knowledge"""
        gas_optimizer = self._load_json(KnowledgeFile.GAS_OPTIMIZER)

        base_knowledge = {
            "feature_name": gas_optimizer["feature_name"],
            "tagline": gas_optimizer["tagline"],
            "description": gas_optimizer["description"],
            "core_capabilities": gas_optimizer["core_capabilities"],
            "supported_chains": gas_optimizer["supported_chains"],
            "features": gas_optimizer["features"]
        }

        if user_type == "investor":
            base_knowledge["competitive_advantages"] = gas_optimizer["competitive_advantages"]
            base_knowledge["getting_started"] = gas_optimizer["getting_started"]["for_investors"]

        return base_knowledge

    def _get_risk_analyzer_knowledge(self, user_type: str) -> Dict[str, Any]:
        """Get risk analyzer agent knowledge"""
        risk_analyzer = self._load_json(KnowledgeFile.RISK_ANALYZER)

        base_knowledge = {
            "feature_name": risk_analyzer["feature_name"],
            "tagline": risk_analyzer["tagline"],
            "description": risk_analyzer["description"],
            "core_capabilities": risk_analyzer["core_capabilities"],
            "risk_score_scale": risk_analyzer["risk_score_scale"],
            "features": risk_analyzer["features"]
        }

        if user_type == "investor":
            base_knowledge["competitive_advantages"] = risk_analyzer["competitive_advantages"]
            base_knowledge["getting_started"] = risk_analyzer["getting_started"]["for_investors"]

        return base_knowledge

    def _get_money_market_knowledge(self, user_type: str) -> Dict[str, Any]:
        """Get money market rate comparison knowledge"""
        money_market = self._load_json(KnowledgeFile.MONEY_MARKET)

        base_knowledge = {
            "feature_name": money_market["feature_name"],
            "description": money_market["description"],
            "supported_protocols": money_market["supported_protocols"],
            "caching_system": money_market["caching_system"],
            "rate_comparison_features": money_market["rate_comparison_features"],
            "supported_assets": money_market["supported_assets"],
            "supported_chains": money_market["supported_chains"],
            "features": money_market["features"],
            "api_endpoints": money_market["api_endpoints"],
            "common_questions": money_market["common_questions"]
        }

        if user_type == "investor":
            base_knowledge["competitive_advantages"] = money_market["competitive_advantages"]
            base_knowledge["background_tasks"] = money_market["background_tasks"]
            base_knowledge["technical_details"] = money_market["technical_details"]
            base_knowledge["getting_started"] = money_market["getting_started"]["for_investors"]
        else:
            base_knowledge["command_formats"] = money_market["command_formats"]
            base_knowledge["natural_language_examples"] = money_market["natural_language_examples"]
            base_knowledge["getting_started"] = money_market["getting_started"]["for_users"]

        return base_knowledge

    def augment_system_prompt(
        self,
        user_query: str,
        detected_intent: str,
        user_type: str = "user",
        base_system_prompt: Optional[str] = None,
        compression_level: str = "medium"
    ) -> str:
        """
        Create enhanced system prompt with injected knowledge.

        Args:
            user_query: The user's original message
            detected_intent: Intent detected by intent_detector_v2
            user_type: "user" for end users, "investor" for investor queries
            base_system_prompt: Optional base system prompt to enhance
            compression_level: Token compression level - "none", "light", "medium", or "aggressive"
                             - none: Full knowledge (baseline)
                             - light: ~30% token reduction
                             - medium: ~60% token reduction (recommended)
                             - aggressive: ~80% token reduction

        Returns:
            Enhanced system prompt with knowledge injection
        """
        knowledge = self.get_knowledge_for_intent(user_query, detected_intent, user_type)

        # Apply compression if requested
        if compression_level != "none":
            from app.application.chat.services.knowledge_compressor import compress_knowledge
            compressed_text, estimated_tokens = compress_knowledge(
                knowledge=knowledge,
                intent=detected_intent,
                user_query=user_query,
                level=compression_level
            )
            knowledge_text = compressed_text
        else:
            # Format knowledge as structured text (no compression)
            knowledge_text = self._format_knowledge(knowledge)

        if base_system_prompt is None:
            base_system_prompt = """You are Anvil, a specialized DeFi assistant focused on decentralized finance,
crypto trading, and blockchain technology."""

        enhanced_prompt = f"""{base_system_prompt}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
KNOWLEDGE BASE (Use this for accurate, detailed responses)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{knowledge_text}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RESPONSE GUIDELINES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ DO:
- Answer based on the knowledge base above
- Be specific with numbers, features, and technical details
- Cite data sources when discussing accuracy or real-time data
- Use examples from the knowledge base
- Explain complex concepts clearly

⚠️ FOR INVESTORS:
- Emphasize competitive advantages and market opportunity
- Include specific metrics (accuracy %, cost savings, market size)
- Highlight unique features vs competitors
- Mention revenue model and unit economics

💡 FOR USERS:
- Focus on how to use features with step-by-step examples
- Include command syntax and multi-language support
- Explain safety features and protections
- Keep tone friendly and encouraging

USER QUERY: {user_query}
"""

        return enhanced_prompt

    def _format_knowledge(self, knowledge: Dict[str, Any]) -> str:
        """
        Format knowledge dictionary as readable text for LLM prompt.

        Args:
            knowledge: Knowledge dictionary from get_knowledge_for_intent

        Returns:
            Formatted knowledge as string
        """
        lines = []

        for key, value in knowledge.items():
            # Format key as section header
            header = key.replace("_", " ").title()
            lines.append(f"\n## {header}\n")

            # Format value based on type
            if isinstance(value, dict):
                lines.append(self._format_dict(value, indent=0))
            elif isinstance(value, list):
                lines.append(self._format_list(value, indent=0))
            else:
                lines.append(f"{value}\n")

        return "\n".join(lines)

    def _format_dict(self, d: Dict[str, Any], indent: int = 0) -> str:
        """Format dictionary as readable text"""
        lines = []
        indent_str = "  " * indent

        for key, value in d.items():
            key_formatted = key.replace("_", " ").title()

            if isinstance(value, dict):
                lines.append(f"{indent_str}**{key_formatted}:**")
                lines.append(self._format_dict(value, indent + 1))
            elif isinstance(value, list):
                lines.append(f"{indent_str}**{key_formatted}:**")
                lines.append(self._format_list(value, indent + 1))
            else:
                lines.append(f"{indent_str}**{key_formatted}:** {value}")

        return "\n".join(lines)

    def _format_list(self, lst: list, indent: int = 0) -> str:
        """Format list as readable text"""
        lines = []
        indent_str = "  " * indent

        for item in lst:
            if isinstance(item, dict):
                # For dict items, format as bullet points with nested content
                lines.append(f"{indent_str}- ")
                lines.append(self._format_dict(item, indent + 1))
            else:
                lines.append(f"{indent_str}- {item}")

        return "\n".join(lines)

    def clear_cache(self):
        """Clear cached JSON files (useful after updates)"""
        self._cache.clear()


# Singleton instance for global use
_injector_instance: Optional[KnowledgeInjector] = None


def get_knowledge_injector() -> KnowledgeInjector:
    """
    Get singleton instance of KnowledgeInjector.

    Returns:
        Singleton KnowledgeInjector instance
    """
    global _injector_instance
    if _injector_instance is None:
        _injector_instance = KnowledgeInjector()
    return _injector_instance


# Convenience function for quick usage
def inject_knowledge(
    user_query: str,
    detected_intent: str,
    user_type: str = "user",
    base_system_prompt: Optional[str] = None,
    compression_level: str = "medium"
) -> str:
    """
    Convenience function to inject knowledge into system prompt with token optimization.

    Args:
        user_query: The user's original message
        detected_intent: Intent detected by intent_detector_v2
        user_type: "user" for end users, "investor" for investor queries
        base_system_prompt: Optional base system prompt to enhance
        compression_level: Token compression level - "none", "light", "medium", or "aggressive"
                         - medium (default): 60% token reduction, recommended for most cases
                         - aggressive: 80% reduction for token-constrained scenarios
                         - light: 30% reduction, preserves more detail
                         - none: Full knowledge without compression

    Returns:
        Enhanced system prompt with knowledge injection

    Examples:
        # Default usage with 60% token reduction
        enhanced_prompt = inject_knowledge(
            user_query="What is Hunter AI?",
            detected_intent="GENERAL_CONVERSATION",
            user_type="user"
        )

        # Aggressive compression for long conversations
        enhanced_prompt = inject_knowledge(
            user_query="Tell me about arbitrage",
            detected_intent="ULTRA_ARBITRAGE",
            user_type="user",
            compression_level="aggressive"
        )

        # No compression for critical queries
        enhanced_prompt = inject_knowledge(
            user_query="Detailed comparison of all features",
            detected_intent="GENERAL_CONVERSATION",
            user_type="investor",
            compression_level="none"
        )
    """
    injector = get_knowledge_injector()
    return injector.augment_system_prompt(
        user_query=user_query,
        detected_intent=detected_intent,
        user_type=user_type,
        base_system_prompt=base_system_prompt,
        compression_level=compression_level
    )
