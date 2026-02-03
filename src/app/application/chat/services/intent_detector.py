"""
Intent detection service for unified chat routing.

Detects user intent from messages to route to appropriate handlers.

This service follows hexagonal architecture:
- Delegates to IntentDetectionPort for actual classification
- Port implementations (LLM, keyword, hybrid) handle the logic
- Service provides stable interface for consumers
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional

from app.domain.chat.entities.message import Message
from app.domain.ports.chat.intent_detection_port import (
    IntentDetectionPort,
    IntentDetectionRequest,
    IntentDetectionResult as PortResult,
)


class ChatIntent(Enum):
    """Chat intent types for routing."""

    # GraphRAG intents
    PROTOCOL_SEARCH = "protocol_search"
    RISK_ASSESSMENT = "risk_assessment"
    SIMILAR_PROTOCOLS = "similar_protocols"

    # Hunter AI intents (direct routing to Hunter tools)
    HUNTER_SENTIMENT = (
        "hunter_sentiment"  # Sentiment analysis (Twitter, Reddit, Discord, News)
    )
    HUNTER_PRICE_PREDICTION = "hunter_price_prediction"  # Price forecasting
    HUNTER_RISK_SIGNALS = "hunter_risk_signals"  # Market risk warnings
    HUNTER_TRADING_SIGNALS = "hunter_trading_signals"  # Buy/sell signals
    HUNTER_PATTERNS = "hunter_patterns"  # Chart patterns and trends
    HUNTER_PORTFOLIO = "hunter_portfolio"  # Portfolio optimization

    # ULTRA intents (DeFi automation and MEV)
    ULTRA_ARBITRAGE = "ultra_arbitrage"  # Arbitrage opportunity discovery
    ULTRA_FLASH_LOANS = "ultra_flash_loans"  # Flash loan protocol selection
    ULTRA_MEV_PROTECTION = "ultra_mev_protection"  # MEV-protected execution
    ULTRA_AUTO_EXECUTOR = "ultra_auto_executor"  # Automated trading bot control

    # DeFi Shortcut intents (direct routing to specialized handlers)
    LENDING = "lending"  # Morpho vaults, Aave, Compound - deposit/earn/supply
    MONEY_MARKET = "money_market"  # Compare lending rates across protocols
    SWAP = "swap"  # Token swaps via 1inch, Hyperliquid, UniswapX
    SWAP_MOONPAY = (
        "swap_moonpay"  # MoonPay crypto-to-crypto swaps (BTC, ETH, SOL, USDC)
    )
    BUY = "buy"  # Buy crypto with fiat (on-ramp)
    SEND = "send"  # Send tokens to another wallet
    BALANCE = "balance"  # Show user balance in USDC
    PORTFOLIO = "portfolio"  # Full portfolio enumeration
    ACTIVITY = "activity"  # Transaction history
    RECEIVE = "receive"  # Show QR code, handle, and copy address

    # Agent Squad & Supervisor intents
    SPECIALIST_TASK = "specialist_task"
    COMPLEX_WORKFLOW = "complex_workflow"

    # Fallback intents
    OUT_OF_SCOPE = (
        "out_of_scope"  # For non-Anvil, off-topic queries (weather, jokes, etc.)
    )
    GENERAL_CONVERSATION = "general_conversation"  # Contextual questions about chat history, clarifications


@dataclass
class IntentDetectionResult:
    """Intent detection result with confidence and extracted entities."""

    intent: ChatIntent
    confidence: float  # 0-1
    extracted_entities: dict  # Protocol names, tokens, amounts, chains, etc.
    reasoning: str  # Why this intent was chosen
    suggested_agent: Optional[str] = None  # For SPECIALIST_TASK


class IntentDetectorService:
    """
    Detect user intent from chat messages.

    Delegates to IntentDetectionPort for classification logic.
    This service provides a stable interface for consumers while
    allowing different classification implementations (LLM, keyword, hybrid).

    Architecture:
        IntentDetectorService (Application Layer)
            ↓ delegates to
        IntentDetectionPort (Domain Port)
            ↑ implemented by
        KeywordAdapter | LLMAdapter | HybridAdapter (Infrastructure)
    """

    def __init__(self, intent_port: IntentDetectionPort):
        """
        Initialize intent detector.

        Args:
            intent_port: Port implementation for intent detection
                        (injected by DI - hybrid in production, keyword in tests)
        """
        self._intent_port = intent_port

    async def detect_intent(
        self,
        message: str,
        conversation_history: Optional[list[Message]] = None,
    ) -> IntentDetectionResult:
        """
        Detect intent from user message.

        Args:
            message: User message
            conversation_history: Previous messages (for context)

        Returns:
            Intent detection result with confidence and entities
        """
        # Build request for port
        request = IntentDetectionRequest(
            message=message,
            conversation_history=conversation_history,
        )

        # Delegate to port implementation
        port_result = await self._intent_port.detect_intent(request)

        # Convert port result to service result
        # (maintains backward compatibility with existing consumers)
        return IntentDetectionResult(
            intent=port_result.intent,
            confidence=port_result.confidence,
            extracted_entities=port_result.entities,
            reasoning=port_result.reasoning,
            suggested_agent=port_result.suggested_agent,
        )
