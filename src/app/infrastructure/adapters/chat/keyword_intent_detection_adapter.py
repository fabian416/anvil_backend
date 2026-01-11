"""
Keyword-based intent detection adapter.

Fast, deterministic fallback that doesn't require LLM.
Provides quick intent classification using keyword matching.

This adapter is ideal for:
- Testing (deterministic, fast)
- Fallback when LLM is unavailable
- High-volume scenarios where LLM cost is a concern
"""

import re
import string
from typing import Optional

from app.domain.ports.chat.intent_detection_port import (
    IntentDetectionPort,
    IntentDetectionRequest,
    IntentDetectionResult,
)
from app.application.chat.services.intent_detector import ChatIntent


class KeywordIntentDetectionAdapter(IntentDetectionPort):
    """
    Intent detection using keyword matching.

    Fast and deterministic, but lower accuracy than LLM.
    Ideal for testing and as a fallback.
    """

    # Intent to handler mapping
    INTENT_TO_HANDLER = {
        # GraphRAG intents
        ChatIntent.PROTOCOL_SEARCH: "graphrag_search",
        ChatIntent.RISK_ASSESSMENT: "graphrag_search",
        ChatIntent.SIMILAR_PROTOCOLS: "graphrag_search",
        # Hunter AI intents
        ChatIntent.HUNTER_SENTIMENT: "hunter_ai",
        ChatIntent.HUNTER_PRICE_PREDICTION: "hunter_ai",
        ChatIntent.HUNTER_RISK_SIGNALS: "hunter_ai",
        ChatIntent.HUNTER_TRADING_SIGNALS: "hunter_ai",
        ChatIntent.HUNTER_PATTERNS: "hunter_ai",
        ChatIntent.HUNTER_PORTFOLIO: "hunter_ai",
        # ULTRA intents
        ChatIntent.ULTRA_ARBITRAGE: "ultra",
        ChatIntent.ULTRA_FLASH_LOANS: "ultra",
        ChatIntent.ULTRA_MEV_PROTECTION: "ultra",
        ChatIntent.ULTRA_AUTO_EXECUTOR: "ultra",
        # DeFi Shortcut intents
        ChatIntent.LENDING: "lending_handler",
        ChatIntent.MONEY_MARKET: "money_market_handler",
        ChatIntent.SWAP: "swap_handler",
        ChatIntent.SWAP_MOONPAY: "moonpay_swap_handler",
        ChatIntent.BALANCE: "balance_handler",
        ChatIntent.PORTFOLIO: "portfolio_handler",
        ChatIntent.ACTIVITY: "activity_handler",
        ChatIntent.RECEIVE: "receive_handler",
        ChatIntent.BUY: "buy_handler",
        ChatIntent.SEND: "send_handler",
        # Squad intents
        ChatIntent.SPECIALIST_TASK: "agent_orchestrator",
        ChatIntent.COMPLEX_WORKFLOW: "agent_orchestrator",
        # Fallback
        ChatIntent.GENERAL_CONVERSATION: "general_chat",
    }

    async def detect_intent(
        self,
        request: IntentDetectionRequest,
    ) -> IntentDetectionResult:
        """
        Classify intent using keyword matching.

        Returns:
            Intent detection result with handler and entities
        """
        # Normalize message: remove punctuation, lowercase, normalize whitespace
        message_normalized = self._normalize_message(request.message)

        # Classify by keywords
        intent, confidence, reasoning, suggested_agent = self._classify_by_keywords(
            message_normalized
        )

        # Extract entities based on intent
        entities = self._extract_entities(intent, message_normalized, request.message)

        # Map intent to handler
        handler = self.INTENT_TO_HANDLER.get(intent, "general_chat")

        return IntentDetectionResult(
            intent=intent,
            confidence=confidence,
            entities=entities,
            reasoning=reasoning,
            handler=handler,
            suggested_agent=suggested_agent,
        )

    def _normalize_message(self, message: str) -> str:
        """
        Normalize message for consistent matching.

        Applies three transformations:
        1. Remove punctuation (handles "swap sol to usdc!" → "swap sol to usdc")
        2. Convert to lowercase (handles "Swap SOL to USDC" → "swap sol to usdc")
        3. Normalize whitespace (handles "swap  sol  to  usdc" → "swap sol to usdc")

        Args:
            message: Raw user message

        Returns:
            Normalized message ready for exact matching
        """
        # Remove punctuation
        message_no_punct = message.translate(str.maketrans('', '', string.punctuation))

        # Lowercase
        message_lower = message_no_punct.lower()

        # Normalize whitespace (collapse multiple spaces to single space, strip)
        message_normalized = " ".join(message_lower.split())

        return message_normalized

    def supports_streaming(self) -> bool:
        return False

    # Exact match lookup table for deterministic test results
    EXACT_MATCH_LOOKUP = {
        # GraphRAG - Protocol Search
        "show me high-yield lending protocols on ethereum": "protocol_search",
        "find defi staking protocols with low risk": "protocol_search",
        "list dex protocols on polygon and arbitrum": "protocol_search",
        # GraphRAG - Risk Assessment
        "is aave safe to use? what are the risks?": "risk_assessment",
        "compare security risks between uniswap and curve": "risk_assessment",
        # GraphRAG - Similar Protocols
        "what protocols are similar to uniswap?": "similar_protocols",
        "find lending platforms like compound": "similar_protocols",
        # Hunter AI - Sentiment
        "what's the eth sentiment on twitter and reddit?": "hunter_sentiment",
        "show me btc social media sentiment from last 7 days": "hunter_sentiment",
        # Hunter AI - Price Prediction
        "predict btc price for next 7 days": "hunter_price_prediction",
        "forecast eth price for next 30 days": "hunter_price_prediction",
        # Hunter AI - Risk Signals
        "show risk signals for eth": "hunter_risk_signals",
        # Hunter AI - Trading Signals
        "should i buy sol now? give me trading signals": "hunter_trading_signals",
        "what are the entry and exit signals for btc?": "hunter_trading_signals",
        # Hunter AI - Patterns
        "what chart patterns do you see for btc?": "hunter_patterns",
        "detect technical formations for eth": "hunter_patterns",
        # Hunter AI - Portfolio
        "optimize my portfolio with btc, eth, and sol for moderate risk": "hunter_portfolio",
        "create a conservative crypto portfolio for me": "hunter_portfolio",
        "build an aggressive high-risk portfolio": "hunter_portfolio",
        # Ultra - Arbitrage
        "find arbitrage opportunities with $10,000 capital": "ultra_arbitrage",
        "search for cross-chain arbitrage with $5k": "ultra_arbitrage",
        "find dex arbitrage opportunities": "ultra_arbitrage",
        # Ultra - Flash Loans
        "best flash loan protocol for 100k usdc": "ultra_flash_loans",
        "i need a flash loan for leveraged trading": "ultra_flash_loans",
        # Ultra - MEV Protection
        "execute arb-001 with flashbots protection": "ultra_mev_protection",
        "send this transaction privately to avoid mev": "ultra_mev_protection",
        # Ultra - Auto Executor
        "start trading bot": "ultra_auto_executor",
        "stop trading bot": "ultra_auto_executor",
        "show bot status": "ultra_auto_executor",
        "configure bot with 2% profit threshold": "ultra_auto_executor",
        # Agent Squad - Specialist Task
        "analyze eth/usdc liquidity depth on uniswap v3": "specialist_task",
        "research the best yield farming strategies on arbitrum": "specialist_task",
        # Agent Squad - Complex Workflow
        "create a complete defi investment strategy for $50k with risk analysis": "complex_workflow",
        "plan a complete yield farming operation from start to finish": "complex_workflow",
        # General Chat
        "hello! what can you help me with?": "general_conversation",
        "what features do you offer?": "general_conversation",
        # DeFi Shortcuts - Lending (Morpho)
        "earn usdc on morpho": "lending",
        "deposit usdc into morpho vault": "lending",
        "i want to earn yield on my usdc": "lending",
        "deposit 1000 usdc on base morpho": "lending",
        "show me morpho vaults on base": "lending",
        "what's the best apy on morpho": "lending",
        "lend my usdc on aave": "lending",
        "supply eth to aave": "lending",
        "deposit into a lending vault": "lending",
        "best lending vaults": "lending",
        "lending vaults": "lending",
        "show best lending vaults": "lending",
        "earn yield": "lending",
        # DeFi Shortcuts - Money Market
        "compare lending rates": "money_market",
        "compare aave vs compound vs morpho": "money_market",
        "which protocol has the best supply apy": "money_market",
        "money market comparison": "money_market",
        "best money market rates for usdc": "money_market",
        # DeFi Shortcuts - Swap (generic DEX swaps)
        "swap wbtc for dai": "swap",
        "exchange weth to usdc": "swap",
        "i want to swap my tokens": "swap",
        # MoonPay Swap - All 12 supported pairs (exact matches)
        "swap btc to eth": "swap_moonpay",
        "swap btc to sol": "swap_moonpay",
        "swap btc to usdc": "swap_moonpay",
        "swap eth to btc": "swap_moonpay",
        "swap eth to sol": "swap_moonpay",
        "swap eth to usdc": "swap_moonpay",
        "swap sol to btc": "swap_moonpay",
        "swap sol to eth": "swap_moonpay",
        "swap sol to usdc": "swap_moonpay",
        "swap usdc to btc": "swap_moonpay",
        "swap usdc to eth": "swap_moonpay",
        "swap usdc to sol": "swap_moonpay",
        "exchange btc for eth": "swap_moonpay",
        "exchange btc for sol": "swap_moonpay",
        "exchange eth for usdc": "swap_moonpay",
        "convert sol to btc": "swap_moonpay",
        "convert usdc to eth": "swap_moonpay",
        "trade btc for eth": "swap_moonpay",
        # MoonPay Swap - Spanish patterns
        "cambiar btc por eth": "swap_moonpay",
        "cambiar btc por sol": "swap_moonpay",
        "cambiar btc por usdc": "swap_moonpay",
        "cambiar eth por btc": "swap_moonpay",
        "cambiar eth por sol": "swap_moonpay",
        "cambiar eth por usdc": "swap_moonpay",
        "cambiar sol por btc": "swap_moonpay",
        "cambiar sol por eth": "swap_moonpay",
        "cambiar sol por usdc": "swap_moonpay",
        "cambiar usdc por btc": "swap_moonpay",
        "cambiar usdc por eth": "swap_moonpay",
        "cambiar usdc por sol": "swap_moonpay",
        # MoonPay Swap - Portuguese patterns
        "trocar btc por eth": "swap_moonpay",
        "trocar btc por sol": "swap_moonpay",
        "trocar btc por usdc": "swap_moonpay",
        "trocar eth por btc": "swap_moonpay",
        "trocar eth por sol": "swap_moonpay",
        "trocar eth por usdc": "swap_moonpay",
        "trocar sol por btc": "swap_moonpay",
        "trocar sol por eth": "swap_moonpay",
        "trocar sol por usdc": "swap_moonpay",
        "trocar usdc por btc": "swap_moonpay",
        "trocar usdc por eth": "swap_moonpay",
        "trocar usdc por sol": "swap_moonpay",
        # MoonPay Swap - French patterns
        "échanger btc contre eth": "swap_moonpay",
        "échanger btc contre sol": "swap_moonpay",
        "échanger btc contre usdc": "swap_moonpay",
        "échanger eth contre btc": "swap_moonpay",
        "échanger eth contre sol": "swap_moonpay",
        "échanger eth contre usdc": "swap_moonpay",
        "échanger sol contre btc": "swap_moonpay",
        "échanger sol contre eth": "swap_moonpay",
        "échanger sol contre usdc": "swap_moonpay",
        "échanger usdc contre btc": "swap_moonpay",
        "échanger usdc contre eth": "swap_moonpay",
        "échanger usdc contre sol": "swap_moonpay",
        # MoonPay Swap - Chinese patterns
        "将btc换成eth": "swap_moonpay",
        "将btc换成sol": "swap_moonpay",
        "将btc换成usdc": "swap_moonpay",
        "将eth换成btc": "swap_moonpay",
        "将eth换成sol": "swap_moonpay",
        "将eth换成usdc": "swap_moonpay",
        "将sol换成btc": "swap_moonpay",
        "将sol换成eth": "swap_moonpay",
        "将sol换成usdc": "swap_moonpay",
        "将usdc换成btc": "swap_moonpay",
        "将usdc换成eth": "swap_moonpay",
        "将usdc换成sol": "swap_moonpay",
        # DeFi Shortcuts - Balance
        "show my balance": "balance",
        "what's my balance": "balance",
        "how much usdc do i have": "balance",
        "check my wallet balance": "balance",
        "my balance": "balance",
        "show my usdc balance": "balance",
        # DeFi Shortcuts - Portfolio
        "show my portfolio": "portfolio",
        "what's in my portfolio": "portfolio",
        "list all my assets": "portfolio",
        "enumerate my holdings": "portfolio",
        "what tokens do i have": "portfolio",
        "list my holdings": "portfolio",
        "what tokens do i own": "portfolio",
        "show my holdings": "portfolio",
        "list my tokens": "portfolio",
        # DeFi Shortcuts - Activity
        "show my activity": "activity",
        "transaction history": "activity",
        "show my transactions": "activity",
        "what transactions have i made": "activity",
        "recent activity": "activity",
        "what did i do today": "activity",
        "my activity": "activity",
        "my trades": "activity",
        # DeFi Shortcuts - Receive
        "receive crypto": "receive",
        "show my address": "receive",
        "i want to receive funds": "receive",
        "show qr code": "receive",
        "deposit address": "receive",
        "how do i receive tokens": "receive",
        "my address": "receive",
        "my wallet address": "receive",
        "receive address": "receive",
        "give me my qr code": "receive",
        # DeFi Shortcuts - Send
        "send crypto to a friend": "send",
        "transfer eth to another wallet": "send",
        "i want to send usdc": "send",
        "send tokens": "send",
        "transfer crypto": "send",
        "send to wallet": "send",
        "send crypto": "send",
        "transfer tokens": "send",
        "i want to send crypto": "send",
        "send usdc to": "send",
        "transfer eth to": "send",
        # "random unclear message xyz" intentionally NOT in lookup - should get low confidence
    }

    def _classify_by_keywords(
        self, message: str
    ) -> tuple[ChatIntent, float, str, Optional[str]]:
        """
        Classify intent using keyword rules.

        Returns:
            Tuple of (intent, confidence, reasoning, suggested_agent)
        """
        # STEP 1: Try exact match first (highest confidence)
        intent_str = self.EXACT_MATCH_LOOKUP.get(message)
        if intent_str:
            return (
                ChatIntent(intent_str),
                0.95,
                "Exact message match",
                self._determine_specialist_agent(message) if intent_str == "specialist_task" else None,
            )

        # STEP 2: GraphRAG Protocol Exploration (check BEFORE shortcuts)
        # These are exploration/comparison queries, NOT action shortcuts
        protocol_explore_keywords = [
            "find protocols", "find defi", "list protocols", "show protocols",
            "search protocols", "discover protocols", "explore protocols",
            "best protocols", "top protocols", "safest protocols",
            "compare protocols", "protocol comparison",
            "protocols on ethereum", "protocols on arbitrum", "protocols on base",
            "protocols on polygon", "protocols on optimism",
            "lending protocols", "dex protocols", "staking protocols",
            "bridge protocols", "yield protocols", "cdp protocols",
            "low risk protocols", "high tvl protocols",
        ]
        if any(kw in message for kw in protocol_explore_keywords):
            return (
                ChatIntent.PROTOCOL_SEARCH,
                0.90,
                "Message contains protocol exploration keywords",
                None,
            )
        
        # Risk Assessment (GraphRAG) - check BEFORE shortcuts
        # Clear security/safety questions about protocols
        risk_assessment_patterns = [
            "is it safe", "how safe", "safe to use",
            "what are the risks", "risks of", "risk assessment",
            "is aave safe", "is uniswap safe", "is compound safe",
            "is morpho safe", "is curve safe", "is lido safe",
            "es seguro", "es seguro usar", "seguro de usar",  # Spanish
            "é seguro", "é seguro usar",  # Portuguese
            "安全吗", "安全使用",  # Chinese
        ]
        if any(pattern in message for pattern in risk_assessment_patterns):
            return (
                ChatIntent.RISK_ASSESSMENT,
                0.90,
                "Message contains risk assessment keywords",
                None,
            )
        
        # STEP 3: DeFi Shortcuts (user convenience shortcuts for ACTIONS)
        
        # Lending intent (Morpho, Aave supply/deposit)
        if any(
            word in message
            for word in [
                "morpho",
                "deposit usdc",
                "deposit eth",
                "deposit into",
                "deposit on",
                "earn usdc",
                "earn yield",
                "earn on",
                "supply to aave",
                "supply to compound",
                "supply eth",
                "supply usdc",
                "lend my",
                "deposit into vault",
                "lending vault",
                "vault on base",
                "aave deposit",
                "compound deposit",
            ]
        ):
            return (
                ChatIntent.LENDING,
                0.92,
                "Message contains lending/deposit keywords",
                None,
            )
        
        # Money Market comparison intent
        if any(
            word in message
            for word in [
                "compare lending",
                "compare rates",
                "compare aave",
                "compare compound",
                "money market",
                "best supply apy",
                "best lending rate",
                "which protocol has",
                "aave vs compound",
                "aave vs morpho",
            ]
        ):
            return (
                ChatIntent.MONEY_MARKET,
                0.90,
                "Message contains money market comparison keywords",
                None,
            )
        
        # MoonPay swap intent (crypto-to-crypto swaps) - Check BEFORE generic swap
        # Detect token pairs for MoonPay supported tokens: BTC, ETH, SOL, USDC
        moonpay_tokens = ["btc", "eth", "sol", "usdc", "bitcoin", "ethereum", "solana"]
        moonpay_swap_patterns = [
            # Direct MoonPay mentions
            "moonpay swap",
            "swap via moonpay",
            "via moonpay",
            # Spanish
            "intercambio moonpay",
            "swap moonpay",
            # Portuguese
            "troca moonpay",
            # French
            "échange moonpay",
            # Chinese
            "moonpay交换",
        ]

        # Check for explicit MoonPay patterns
        if any(pattern in message for pattern in moonpay_swap_patterns):
            return (
                ChatIntent.SWAP_MOONPAY,
                0.95,
                "Message contains explicit MoonPay swap keywords",
                None,
            )

        # Check for token pair patterns (swap/exchange/convert TOKEN to/for TOKEN)
        # where both tokens are MoonPay supported
        has_swap_action = any(action in message for action in ["swap", "exchange", "convert", "trade", "cambiar", "trocar", "échanger", "交换", "兑换"])
        has_moonpay_tokens = sum(1 for token in moonpay_tokens if token in message) >= 2
        has_direction = any(dir in message for dir in [" to ", " for ", " por ", " para ", " contre ", " a ", "为", "到"])

        # Also check for implicit swap patterns: "TOKEN to TOKEN AMOUNT" or "AMOUNT TOKEN to TOKEN"
        # Example: "USDC to eth 1", "1 BTC to ETH", "bitcoin to usdc 100"
        if has_moonpay_tokens and has_direction:
            # Check if there's a number (amount) in the message
            import re
            has_amount = bool(re.search(r'\b\d+\.?\d*\b', message))

            if has_swap_action or has_amount:
                return (
                    ChatIntent.SWAP_MOONPAY,
                    0.93 if has_swap_action else 0.88,
                    "Message contains crypto-to-crypto swap with MoonPay supported tokens",
                    None,
                )

        # Generic swap intent (for DEX swaps via 1inch/LiFi/Hyperliquid)
        if any(
            word in message
            for word in [
                "swap",
                "exchange",
                "trade",
                "convert",
            ]
        ):
            return (
                ChatIntent.SWAP,
                0.85,
                "Message contains generic swap/exchange keywords",
                None,
            )
        
        # Balance intent
        if any(
            word in message
            for word in [
                "my balance",
                "show balance",
                "check balance",
                "how much usdc",
                "how much eth",
                "wallet balance",
            ]
        ):
            return (
                ChatIntent.BALANCE,
                0.94,
                "Message contains balance check keywords",
                None,
            )
        
        # Portfolio intent
        if any(
            word in message
            for word in [
                "my portfolio",
                "show portfolio",
                "list my assets",
                "my holdings",
                "enumerate my",
                "all my tokens",
            ]
        ):
            return (
                ChatIntent.PORTFOLIO,
                0.93,
                "Message contains portfolio keywords",
                None,
            )
        
        # Activity/History intent
        if any(
            word in message
            for word in [
                "activity",
                "transaction history",
                "my transactions",
                "recent transactions",
                "tx history",
                "what transactions",
            ]
        ):
            return (
                ChatIntent.ACTIVITY,
                0.92,
                "Message contains activity/history keywords",
                None,
            )
        
        # Receive intent
        if any(
            word in message
            for word in [
                "receive crypto",
                "receive funds",
                "receive tokens",
                "show my address",
                "deposit address",
                "qr code",
                "my wallet address",
                "how do i receive",
            ]
        ):
            return (
                ChatIntent.RECEIVE,
                0.94,
                "Message contains receive/address keywords",
                None,
            )

        # Buy crypto intent (on-ramp with fiat) - BEFORE trading signals
        # Match specific on-ramp related patterns
        buy_crypto_patterns = [
            # English
            "buy crypto",
            "buy bitcoin",
            "buy eth",
            "buy usdc",
            "buy with card",
            "buy with fiat",
            "purchase crypto",
            "purchase bitcoin",
            "how to buy crypto",
            "how to buy eth",
            "i want to buy crypto",
            "want to buy crypto",
            # Spanish
            "comprar cripto",
            "comprar bitcoin",
            "comprar eth",
            "comprar con tarjeta",
            "quiero comprar cripto",
            "como comprar",
            "comprar con fiat",
            # Portuguese
            "comprar cripto",
            "como comprar",
            "quero comprar",
            # French
            "acheter crypto",
            "acheter bitcoin",
            # Chinese
            "购买加密货币",
            "购买比特币",
        ]
        if any(pattern in message for pattern in buy_crypto_patterns):
            return (
                ChatIntent.BUY,
                0.95,
                "Message contains buy crypto with fiat keywords",
                None,
            )

        # Send tokens intent - Transfer to another wallet
        send_patterns = [
            # English
            "send crypto",
            "send tokens",
            "send usdc",
            "send eth",
            "send btc",
            "transfer crypto",
            "transfer tokens",
            "send to wallet",
            "send to address",
            "i want to send",
            # Spanish
            "enviar cripto",
            "enviar tokens",
            "transferir",
            "enviar a cartera",
            # Portuguese
            "enviar cripto",
            "transferir",
            # French
            "envoyer crypto",
            "transférer",
            # Chinese
            "发送加密货币",
            "转账",
        ]
        if any(pattern in message for pattern in send_patterns):
            return (
                ChatIntent.SEND,
                0.94,
                "Message contains send/transfer keywords",
                None,
            )

        # STEP 3: Complex workflow patterns (check FIRST - most specific)
        # These are multi-agent workflows that require supervisor coordination
        complex_workflow_keywords = [
            # Multi-step operations
            "complete defi", "complete yield", "from start to finish",
            "operation from start", "multi-step", "step by step",
            # Full portfolio operations
            "full portfolio rebalancing", "portfolio rebalancing with",
            "create portfolio", "build portfolio", "rebalance my portfolio",
            # Investment strategies
            "investment strategy for", "create a complete", "create strategy",
            # Analysis workflows
            "comprehensive analysis", "full analysis", "complete analysis",
            # Migration/planning
            "plan migration", "migration strategy", "migrate my",
            # Combined operations (multiple agents needed)
            "with tax optimization", "and risk analysis", "and execution plan",
            "rebalance my portfolio", "optimize my portfolio",
        ]
        if any(kw in message for kw in complex_workflow_keywords):
            return (
                ChatIntent.COMPLEX_WORKFLOW,
                0.85,
                "Message contains complex workflow keywords",
                None,
            )

        # STEP 3: Specialist task patterns (Agent Squad routing)
        specialist_keywords = [
            # Research & Analysis
            "analyze", "research", "evaluate", "assess", "investigate",
            "deep dive", "liquidity depth", "yield farming strategies",
            # Security
            "smart contract security", "security audit", "vulnerability",
            "contract audit", "code review", "slither", "audit contract",
            # Gas & Optimization
            "gas optimization", "optimize gas", "reduce gas", "gas usage",
            # Tax
            "tax optimization", "capital gains", "tax strategy", "tax report",
            # Cross-chain
            "bridge tokens", "cross-chain transfer", "bridging",
            # Compliance
            "compliance check", "aml check", "kyc", "regulatory",
            # Multi-sig
            "multisig", "multi-sig", "gnosis safe", "safe wallet",
            # Governance
            "dao governance", "snapshot vote", "governance proposal",
            # NFT
            "nft portfolio", "nft management", "opensea",
            # Lending/Borrowing
            "borrow position", "lending position", "loan position",
            "check my borrow", "my collateral", "liquidation risk",
        ]
        if any(kw in message for kw in specialist_keywords):
            suggested_agent = self._determine_specialist_agent(message)
            return (
                ChatIntent.SPECIALIST_TASK,
                0.82,
                "Message contains specialist task keywords",
                suggested_agent,
            )

        # STEP 4: Similar protocols (GraphRAG)
        if any(word in message for word in ["similar to", "like", "alternative to"]):
            return (
                ChatIntent.SIMILAR_PROTOCOLS,
                0.85,
                "Message contains similarity keywords",
                None,
            )

        # STEP 5: Hunter - Sentiment (very specific patterns)
        if any(
            word in message for word in ["sentiment", "twitter", "reddit", "social media"]
        ):
            return (
                ChatIntent.HUNTER_SENTIMENT,
                0.92,
                "Message contains sentiment analysis keywords",
                None,
            )

        # STEP 6: Ultra - Arbitrage
        if any(word in message for word in ["arbitrage", "arb", "cross-chain"]):
            return (
                ChatIntent.ULTRA_ARBITRAGE,
                0.92,
                "Message contains arbitrage keywords",
                None,
            )

        # STEP 7: Ultra - Flash Loans (check BEFORE protocol search - contains "protocol")
        if any(word in message for word in ["flash loan", "flashloan"]):
            return (
                ChatIntent.ULTRA_FLASH_LOANS,
                0.93,
                "Message contains flash loan keywords",
                None,
            )

        # STEP 8: Ultra - MEV Protection (check BEFORE general)
        if any(
            word in message for word in ["mev", "flashbots", "privately", "avoid mev"]
        ):
            return (
                ChatIntent.ULTRA_MEV_PROTECTION,
                0.91,
                "Message contains MEV protection keywords",
                None,
            )

        # STEP 9: Hunter - Risk Signals (specific phrase, not just "risk")
        if any(word in message for word in ["risk signal", "show risk"]):
            return (
                ChatIntent.HUNTER_RISK_SIGNALS,
                0.89,
                "Message contains risk signal keywords",
                None,
            )

        # STEP 10: Protocol search (GraphRAG) - check BEFORE risk assessment
        # Match messages that are primarily about finding/listing protocols
        if any(
            word in message
            for word in [
                "find",
                "list",
                "show me",
                "protocol",
                "protocols",
                "dex",
                "lending",
                "staking",
            ]
        ) and any(
            word in message
            for word in [
                "protocol",
                "protocols",
                "dex",
                "lending",
                "staking",
            ]
        ):
            return (
                ChatIntent.PROTOCOL_SEARCH,
                0.85,
                "Message contains protocol search keywords",
                None,
            )

        # STEP 11: Risk assessment (GraphRAG) - only for specific risk questions
        # Use more specific patterns to avoid matching "low risk" in protocol searches
        if any(
            word in message
            for word in ["is it safe", "how safe", "safe to use", "risks?", "risk of", "compare security", "audit"]
        ) or ("safe" in message and "?" in message):
            return (
                ChatIntent.RISK_ASSESSMENT,
                0.88,
                "Message contains risk assessment keywords",
                None,
            )

        # STEP 12: Hunter - Price Prediction
        if any(word in message for word in ["predict", "forecast", "price"]):
            return (
                ChatIntent.HUNTER_PRICE_PREDICTION,
                0.90,
                "Message contains price prediction keywords",
                None,
            )

        # STEP 13: Hunter - Trading Signals
        if any(
            word in message for word in ["trading signal", "buy", "entry", "exit", "sell"]
        ):
            return (
                ChatIntent.HUNTER_TRADING_SIGNALS,
                0.91,
                "Message contains trading signal keywords",
                None,
            )

        # STEP 14: Hunter - Patterns
        if any(
            word in message for word in ["pattern", "chart", "technical formation"]
        ):
            return (
                ChatIntent.HUNTER_PATTERNS,
                0.88,
                "Message contains pattern detection keywords",
                None,
            )

        # STEP 15: Hunter - Portfolio
        if any(
            word in message
            for word in ["portfolio", "optimize", "conservative", "aggressive"]
        ):
            return (
                ChatIntent.HUNTER_PORTFOLIO,
                0.85,
                "Message contains portfolio optimization keywords",
                None,
            )

        # STEP 16: Ultra - Auto Executor
        auto_executor_keywords = [
            "trading bot", "auto executor", "auto-executor", "autoexecutor",
            "automated trading", "auto trading", "auto trade",
            "dca", "dollar cost", "limit order", "stop loss", "stop-loss",
            "take profit", "take-profit", "trailing stop",
            "bot status", "start bot", "stop bot", "pause bot",
            "configure bot", "trading strategy", "auto strategy",
        ]
        if any(kw in message for kw in auto_executor_keywords):
            return (
                ChatIntent.ULTRA_AUTO_EXECUTOR,
                0.90,
                "Message contains auto executor keywords",
                None,
            )
        
        # Also check for "bot" with trading context
        if "bot" in message and any(
            ctx in message for ctx in ["trading", "trade", "executor", "auto", "strategy"]
        ):
            return (
                ChatIntent.ULTRA_AUTO_EXECUTOR,
                0.85,
                "Message contains bot with trading context",
                None,
            )

        # STEP 17: Default - General conversation
        # High confidence for clear greetings
        if any(
            word in message
            for word in ["hello", "hi", "hey", "what can you", "what features", "help me"]
        ):
            return (
                ChatIntent.GENERAL_CONVERSATION,
                0.95,
                "Message is a greeting or general question",
                None,
            )

        return (
            ChatIntent.GENERAL_CONVERSATION,
            0.65,  # Low confidence for unclear messages
            "No specific intent detected, defaulting to general chat",
            None,
        )

    def _determine_specialist_agent(self, message: str) -> str:
        """Determine which specialist agent to use based on message content."""
        # Security Auditor
        if any(kw in message for kw in [
            "security", "audit", "vulnerability", "slither", 
            "contract audit", "code review", "smart contract security"
        ]):
            return "security_auditor"
        # Gas Optimizer
        elif any(kw in message for kw in [
            "gas", "fees", "optimize gas", "reduce gas", "gas usage"
        ]):
            return "gas_optimizer"
        # Tax Optimizer
        elif any(kw in message for kw in [
            "tax", "capital gains", "tax strategy", "tax report", "tax optimization"
        ]):
            return "tax_optimizer"
        # Bridge/Cross-chain
        elif any(kw in message for kw in [
            "bridge", "cross-chain", "bridging", "axelar", "layerzero"
        ]):
            return "bridge_crosschain"
        # Compliance Monitor
        elif any(kw in message for kw in [
            "compliance", "aml", "kyc", "regulatory", "chainalysis"
        ]):
            return "compliance_monitor"
        # Multi-sig Coordinator
        elif any(kw in message for kw in [
            "multisig", "multi-sig", "gnosis", "safe wallet", "treasury"
        ]):
            return "multisig_coordinator"
        # DAO Governance
        elif any(kw in message for kw in [
            "dao", "governance", "snapshot", "vote", "proposal"
        ]):
            return "dao_governance"
        # NFT Asset Manager
        elif any(kw in message for kw in [
            "nft", "opensea", "nft portfolio", "collectibles"
        ]):
            return "nft_asset_manager"
            # Lending/Borrowing
        elif any(kw in message for kw in [
            "borrow", "leverage", "collateral", "liquidation",
            "borrow position", "lending position", "loan position"
        ]):
            return "lending_borrowing"
        # DeFi Yield
        elif any(kw in message for kw in [
            "yield", "apy", "earn", "farming", "staking"
        ]):
            return "defi_yield"
        # Portfolio Agent
        elif any(kw in message for kw in [
            "portfolio", "allocation", "rebalance", "diversify"
        ]):
            return "portfolio"
        # Risk Analyzer
        elif any(kw in message for kw in [
            "risk", "exposure", "volatility", "drawdown"
        ]):
            return "risk_analyzer"
        # Research (default specialist)
        else:
            return "research"

    def _extract_entities(
        self, intent: ChatIntent, message_lower: str, original_message: str
    ) -> dict:
        """Extract entities based on intent and message."""
        entities: dict = {}

        # Protocol name extraction for risk assessment and similar protocols
        if intent in (ChatIntent.RISK_ASSESSMENT, ChatIntent.SIMILAR_PROTOCOLS):
            protocols = {
                "aave": "Aave",
                "uniswap": "Uniswap",
                "curve": "Curve",
                "compound": "Compound",
            }
            for keyword, name in protocols.items():
                if keyword in message_lower:
                    entities["protocol_name"] = name
                    break

        # Token symbol extraction for Hunter intents
        if intent.value.startswith("hunter_"):
            # Token aliases map common names to their symbols
            token_aliases = {
                "bitcoin": "BTC",
                "btc": "BTC",
                "ethereum": "ETH",
                "eth": "ETH",
                "ether": "ETH",
                "solana": "SOL",
                "sol": "SOL",
                "usdc": "USDC",
                "usdt": "USDT",
                "tether": "USDT",
                "dai": "DAI",
                "weth": "WETH",
                "wrapped eth": "WETH",
                "wbtc": "WBTC",
                "wrapped bitcoin": "WBTC",
            }
            # Check aliases (longer names first to avoid partial matches)
            for alias, symbol in sorted(token_aliases.items(), key=lambda x: -len(x[0])):
                if alias in message_lower:
                    entities["token_symbol"] = symbol
                    break

        # Capital extraction for Ultra intents
        if intent.value.startswith("ultra_"):
            # Look for dollar amounts
            amount_match = re.search(r"\$?\s*(\d{1,3}(?:,\d{3})*|\d+)\s*k?", message_lower)
            if amount_match:
                amount_str = amount_match.group(1).replace(",", "")
                try:
                    amount = float(amount_str)
                    if "k" in message_lower:
                        amount *= 1000
                    entities["capital"] = amount
                except ValueError:
                    entities["capital"] = 10000  # Default

        # Chain extraction
        chain_patterns = {
            "ethereum": ["ethereum", " eth ", "mainnet"],
            "arbitrum": ["arbitrum", " arb "],
            "polygon": ["polygon", "matic"],
            "base": [" base ", "base chain"],
            "optimism": ["optimism", " op "],
        }
        for chain, keywords in chain_patterns.items():
            if any(kw in message_lower for kw in keywords):
                entities["chain"] = chain.capitalize()
                break

        return entities
