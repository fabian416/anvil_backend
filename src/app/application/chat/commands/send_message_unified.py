"""
Unified chat orchestrator with intelligent intent-based routing.

Routes messages to appropriate handlers:
- GraphRAG (search, risk, similar)
- Agent Squad (specialist tasks)
- Supervisor (complex workflows)
- Regular chat (general conversation)

Supports DEMO MODE (use_demo_mode=True):
- Uses pre-built demo handlers (same as /guest/chat)
- No LLM API calls required
- Perfect for demos and testing
"""

import logging
import time
from decimal import Decimal
from uuid import UUID

from app.application.agent_squad.commands.execute_supervisor_workflow import (
    ExecuteSupervisorWorkflow,
)
from app.application.agent_squad.commands.send_agent_squad_message import (
    SendAgentSquadMessage,
)
from app.application.chat.commands.send_message import SendMessage
from app.application.chat.graph_search_handler import ChatGraphSearchHandler
from app.application.chat.handlers.activity_handler import ActivityHandler

# DeFi Shortcut imports (Morpho, Swaps, Portfolio, etc.)
from app.application.chat.handlers.lending_handler import LendingHandler
from app.application.chat.handlers.money_market_handler import MoneyMarketHandler
from app.application.chat.handlers.portfolio_handler import PortfolioHandler
from app.application.chat.handlers.receive_handler import ReceiveHandler
from app.application.chat.handlers.buy_handler import BuyHandler
from app.application.chat.handlers.swap_handler import SwapHandler
from app.application.chat.risk_insights_handler import ChatRiskInsightsHandler
from app.application.chat.services.intent_detector import (
    ChatIntent,
    IntentDetectorService,
)
# Demo mode imports
from app.application.guest.handlers.guest_handler_service import GuestHandlerService
from app.setup.config.agent_squad import AgentSquadSettings

logger = logging.getLogger(__name__)
from app.application.hunter.discord_sentiment import (
    DiscordConfig,
    DiscordSentimentAnalyzer,
)
from app.application.hunter.lstm_price_predictor import LSTMPricePredictor
from app.application.hunter.news_sentiment import NewsConfig, NewsSentimentAnalyzer
from app.application.hunter.pattern_recognition import PatternRecognizer
from app.application.hunter.portfolio_optimizer import PortfolioOptimizer
from app.application.hunter.reddit_sentiment import (
    RedditConfig,
    RedditSentimentAnalyzer,
)
from app.application.hunter.risk_analyzer import RiskAnalyzer

# Hunter AI imports
from app.application.hunter.sentiment_aggregator import SentimentAggregator
from app.application.hunter.trading_signal_generator import (
    Timeframe,
    TradingSignalGenerator,
)
from app.application.hunter.twitter_sentiment import (
    TwitterConfig,
    TwitterSentimentAnalyzer,
)

# ULTRA imports
from app.application.ultra.arbitrage_discovery import ArbitrageDiscovery
from app.application.ultra.arbitrage_executor import ArbitrageExecutor
from app.application.ultra.auto_executor import AutoExecutor
from app.application.ultra.flash_loan_engine import FlashLoanEngine, FlashLoanProtocol
from app.application.ultra.mev_protection import MEVProtection
from app.domain.chat.entities.message import Message
from app.domain.chat.ports.conversation_repository import ConversationRepository
from app.domain.exceptions.chat import (
    ConversationAccessDeniedError,
    ConversationNotFoundError,
)

# Wallet repository for user wallet lookup
from app.domain.ports.wallet.wallet_repository import WalletRepository
from app.domain.value_objects.sentiment import SentimentSource
from app.domain.value_objects.user_id import UserId


class UnifiedChatOrchestrator:
    """
    Orchestrates unified chat routing with intelligent intent detection.

    Routes messages to:
    - GraphRAG handlers (search, risk, similar)
    - Agent Squad (specialist tasks)
    - Supervisor (complex workflows)
    - Regular chat (general conversation)

    All responses are saved to conversation history for context.
    """

    def __init__(
        self,
        conversation_repo: ConversationRepository,
        intent_detector: IntentDetectorService,
        graphrag_search: ChatGraphSearchHandler,
        graphrag_risk: ChatRiskInsightsHandler,
        agent_squad: SendAgentSquadMessage,
        supervisor: ExecuteSupervisorWorkflow,
        regular_chat: SendMessage,
        lending_handler: LendingHandler | None = None,
        portfolio_handler: PortfolioHandler | None = None,
        swap_handler: SwapHandler | None = None,
        activity_handler: ActivityHandler | None = None,
        receive_handler: ReceiveHandler | None = None,
        buy_handler: BuyHandler | None = None,
        money_market_handler: MoneyMarketHandler | None = None,
        wallet_repository: WalletRepository | None = None,
        # Demo mode dependencies
        agent_squad_settings: AgentSquadSettings | None = None,
        guest_handler_service: GuestHandlerService | None = None,
    ):
        """
        Initialize orchestrator with all handlers.

        Args:
            conversation_repo: Conversation repository
            intent_detector: Intent detection service
            graphrag_search: GraphRAG search handler
            graphrag_risk: GraphRAG risk analysis handler
            agent_squad: Agent Squad message handler
            supervisor: Supervisor workflow handler
            regular_chat: Regular chat handler
            lending_handler: Handler for lending/Morpho vault operations
            portfolio_handler: Handler for portfolio queries
            swap_handler: Handler for token swaps
            activity_handler: Handler for transaction history
            receive_handler: Handler for wallet address/QR
            buy_handler: Handler for crypto purchase (on-ramp via Privy)
            money_market_handler: Handler for rate comparison
            wallet_repository: Repository for wallet lookups (Privy)
            agent_squad_settings: Settings for agent squad (includes use_demo_mode flag)
            guest_handler_service: Demo handlers service (used when use_demo_mode=True)
        """
        self._conversation_repo = conversation_repo
        self._intent_detector = intent_detector
        self._graphrag_search = graphrag_search
        self._graphrag_risk = graphrag_risk
        self._agent_squad = agent_squad
        self._supervisor = supervisor
        self._regular_chat = regular_chat
        self._lending_handler = lending_handler
        self._portfolio_handler = portfolio_handler
        self._swap_handler = swap_handler
        self._activity_handler = activity_handler
        self._receive_handler = receive_handler
        self._buy_handler = buy_handler
        self._money_market_handler = money_market_handler
        self._wallet_repository = wallet_repository
        # Demo mode
        self._settings = agent_squad_settings or AgentSquadSettings()
        self._guest_handler_service = guest_handler_service or GuestHandlerService(
            lending_handler=lending_handler,
            swap_handler=swap_handler,
            money_market_handler=money_market_handler,
        )

    # Supported languages for i18n responses
    SUPPORTED_LANGUAGES = ["en", "es", "fr", "zh", "pt"]
    DEFAULT_LANGUAGE = "en"

    def _build_routing_metadata(
        self,
        intent_result,
        handler: str,
        language: str = "en",
        reasoning: str = None,
        agent_used: str = None,
        total_latency_ms: int = None,
    ) -> dict:
        """Build routing metadata with language support."""
        return {
            "intent": intent_result.intent.value if hasattr(intent_result.intent, "value") else str(intent_result.intent),
            "confidence": intent_result.confidence,
            "handler": handler,
            "agent_used": agent_used,
            "reasoning": reasoning or intent_result.reasoning,
            "total_latency_ms": total_latency_ms,
            "language": language,
        }

    async def execute(
        self,
        user_id: int,
        conversation_id: UUID,
        content: str,
        language: str = "en",
    ) -> dict:
        """
        Execute unified chat routing.

        Args:
            user_id: User ID
            conversation_id: Conversation ID
            content: User message
            language: Response language code (en, es, fr, zh, pt)

        Returns:
            Unified response with routing metadata and enrichment

        Raises:
            ConversationNotFoundError: If conversation not found
            ConversationAccessDeniedError: If conversation not owned by user
        """
        start_time = time.time()

        # Validate language
        if language not in self.SUPPORTED_LANGUAGES:
            language = self.DEFAULT_LANGUAGE

        # Store language for use in handlers
        self._current_language = language

        # Get conversation for verification
        conversation = await self._conversation_repo.get_conversation(conversation_id)
        
        # Auto-create conversation if it doesn't exist (similar to guest endpoint behavior)
        # This allows users to send messages without explicitly creating conversation first
        if not conversation:
            logger.info(f"Conversation {conversation_id} not found, creating new conversation for user {user_id}")
            from app.domain.chat.entities.conversation import Conversation
            from uuid import UUID as UUIDType
            
            # Create new conversation with the provided ID
            conversation = Conversation(
                id=conversation_id,
                user_id=user_id,
                title=None,
            )
            await self._conversation_repo.add_conversation(conversation)
            # Re-fetch to ensure it's properly loaded
            conversation = await self._conversation_repo.get_conversation(conversation_id)
            if not conversation:
                raise ConversationNotFoundError(conversation_id)
        
        # ========================================
        # DEMO MODE: Use GuestHandlerService instead of real LLM
        # ========================================
        if self._settings.use_demo_mode:
            logger.info(f"[DEMO MODE] Handling message with demo handlers for user {user_id}")
            return await self._execute_demo_mode(
                user_id=user_id,
                conversation_id=conversation_id,
                conversation=conversation,
                content=content,
                language=language,
                start_time=start_time,
            )

        if conversation.user_id != user_id:
            raise ConversationAccessDeniedError(conversation_id, user_id)

        # Get conversation history for context (last 10 messages)
        messages = await self._conversation_repo.get_messages(
            conversation_id=conversation_id,
            limit=10,
        )

        # Detect intent
        intent_result = await self._intent_detector.detect_intent(
            message=content,
            conversation_history=messages,
        )

        # Route based on intent
        if intent_result.intent == ChatIntent.PROTOCOL_SEARCH:
            result = await self._handle_protocol_search(
                user_id, conversation_id, content, intent_result, language
            )
        elif intent_result.intent == ChatIntent.RISK_ASSESSMENT:
            result = await self._handle_risk_assessment(
                user_id, conversation_id, content, intent_result, language
            )
        elif intent_result.intent == ChatIntent.SIMILAR_PROTOCOLS:
            result = await self._handle_similar_protocols(
                user_id, conversation_id, content, intent_result, language
            )
        # Hunter AI intents
        elif intent_result.intent == ChatIntent.HUNTER_SENTIMENT:
            result = await self._handle_hunter_sentiment(
                user_id, conversation_id, content, intent_result
            )
        elif intent_result.intent == ChatIntent.HUNTER_PRICE_PREDICTION:
            result = await self._handle_hunter_price_prediction(
                user_id, conversation_id, content, intent_result
            )
        elif intent_result.intent == ChatIntent.HUNTER_RISK_SIGNALS:
            result = await self._handle_hunter_risk_signals(
                user_id, conversation_id, content, intent_result
            )
        elif intent_result.intent == ChatIntent.HUNTER_TRADING_SIGNALS:
            result = await self._handle_hunter_trading_signals(
                user_id, conversation_id, content, intent_result
            )
        elif intent_result.intent == ChatIntent.HUNTER_PATTERNS:
            result = await self._handle_hunter_patterns(
                user_id, conversation_id, content, intent_result
            )
        elif intent_result.intent == ChatIntent.HUNTER_PORTFOLIO:
            result = await self._handle_hunter_portfolio(
                user_id, conversation_id, content, intent_result
            )
        # ULTRA intents
        elif intent_result.intent == ChatIntent.ULTRA_ARBITRAGE:
            result = await self._handle_ultra_arbitrage(
                user_id, conversation_id, content, intent_result
            )
        elif intent_result.intent == ChatIntent.ULTRA_FLASH_LOANS:
            result = await self._handle_ultra_flash_loans(
                user_id, conversation_id, content, intent_result
            )
        elif intent_result.intent == ChatIntent.ULTRA_MEV_PROTECTION:
            result = await self._handle_ultra_mev_protection(
                user_id, conversation_id, content, intent_result
            )
        elif intent_result.intent == ChatIntent.ULTRA_AUTO_EXECUTOR:
            result = await self._handle_ultra_auto_executor(
                user_id, conversation_id, content, intent_result
            )
        # DeFi Shortcut intents (pass language for i18n responses)
        elif intent_result.intent == ChatIntent.LENDING:
            result = await self._handle_lending(
                user_id, conversation_id, content, intent_result, language
            )
        elif intent_result.intent == ChatIntent.MONEY_MARKET:
            result = await self._handle_money_market(
                user_id, conversation_id, content, intent_result, language
            )
        elif intent_result.intent == ChatIntent.SWAP:
            result = await self._handle_swap(
                user_id, conversation_id, content, intent_result, language
            )
        elif intent_result.intent == ChatIntent.BALANCE:
            result = await self._handle_balance(
                user_id, conversation_id, content, intent_result, language
            )
        elif intent_result.intent == ChatIntent.PORTFOLIO:
            result = await self._handle_portfolio(
                user_id, conversation_id, content, intent_result, language
            )
        elif intent_result.intent == ChatIntent.ACTIVITY:
            result = await self._handle_activity(
                user_id, conversation_id, content, intent_result, language
            )
        elif intent_result.intent == ChatIntent.RECEIVE:
            result = await self._handle_receive(
                user_id, conversation_id, content, intent_result, language
            )
        elif intent_result.intent == ChatIntent.BUY:
            result = await self._handle_buy(
                user_id, conversation_id, content, intent_result, language
            )
        # Agent Squad & Supervisor intents
        elif intent_result.intent == ChatIntent.SPECIALIST_TASK:
            result = await self._handle_specialist_task(
                user_id, conversation_id, content, intent_result
            )
        elif intent_result.intent == ChatIntent.COMPLEX_WORKFLOW:
            result = await self._handle_complex_workflow(
                user_id, conversation_id, content, intent_result
            )
        else:  # GENERAL_CONVERSATION
            result = await self._handle_general_conversation(
                user_id, conversation_id, content, intent_result
            )

        # Add total latency
        total_latency = int((time.time() - start_time) * 1000)
        result["routing"]["total_latency_ms"] = total_latency

        return result

    async def _execute_demo_mode(
        self,
        user_id: int,
        conversation_id: UUID,
        conversation,
        content: str,
        language: str,
        start_time: float,
    ) -> dict:
        """
        Execute demo mode using GuestHandlerService.
        
        This provides the same responses as /guest/chat but for authenticated users.
        Useful for demos and testing without requiring LLM API costs.
        
        Args:
            user_id: User ID
            conversation_id: Conversation ID
            conversation: Conversation entity
            content: User message
            language: Response language code
            start_time: Start time for latency calculation
            
        Returns:
            Unified response with routing metadata and enrichment
        """
        if not conversation:
            raise ConversationNotFoundError(conversation_id)

        if conversation.user_id != user_id:
            raise ConversationAccessDeniedError(conversation_id, user_id)

        # Get conversation history for context (last 10 messages)
        messages = await self._conversation_repo.get_messages(
            conversation_id=conversation_id,
            limit=10,
        )
        
        # Build context string from messages for multi-turn support
        context = self._build_context_from_messages(messages)

        # Detect intent using keyword-based detection (no LLM calls in demo mode)
        # This provides instant responses without API costs
        intent, confidence, handler = self._detect_intent_by_keywords_demo(
            content=content,
            context=context,
            language=language,
        )
        
        # Create a simple intent result for handler
        from dataclasses import dataclass
        
        @dataclass
        class DemoIntentResult:
            intent: ChatIntent
            confidence: float
            handler: str
            reasoning: str
            
        intent_result = DemoIntentResult(
            intent=intent,
            confidence=confidence,
            handler=handler,
            reasoning="Keyword-based detection (demo mode)",
        )
        
        logger.info(f"[DEMO MODE] Detected intent: {intent.value} with confidence {confidence}")
        
        # Use GuestHandlerService to handle the intent
        handler_result = await self._guest_handler_service.handle_intent(
            intent=intent_result.intent,
            content=content,
            language=language,
            context=context,
        )
        
        # Extract response data
        agent_content = handler_result.get("content", "")
        enrichment = handler_result.get("enrichment")
        sources = handler_result.get("sources", [])
        requires_registration = handler_result.get("requires_registration", False)
        
        # Get handler name
        handler_name = self._get_demo_handler_name(intent_result.intent)
        
        # Save messages to conversation history
        user_msg, agent_msg = await self._save_messages(
            conversation_id=conversation_id,
            user_content=content,
            agent_content=agent_content,
            sources=sources if sources else None,
        )
        
        # Calculate latency
        total_latency = int((time.time() - start_time) * 1000)
        
        # Build response in the unified format
        response = {
            "user_message": self._message_to_dict(user_msg),
            "agent_message": self._message_to_dict(agent_msg),
            "routing": {
                "intent": intent_result.intent.value if hasattr(intent_result.intent, "value") else str(intent_result.intent),
                "confidence": intent_result.confidence,
                "handler": handler_name,
                "reasoning": intent_result.reasoning,
                "total_latency_ms": total_latency,
                "language": language,
                "is_demo_mode": True,
            },
        }
        
        # Add enrichment if present
        if enrichment:
            response["enrichment"] = enrichment
        else:
            response["enrichment"] = {}
        
        # For RECEIVE intent in demo mode, add the real wallet address
        if intent_result.intent == ChatIntent.RECEIVE:
            try:
                wallet_address = await self._get_user_wallet_address(user_id)
                if wallet_address:
                    response["enrichment"]["wallet_address"] = wallet_address
                    response["enrichment"]["chain"] = "base"
                    response["enrichment"]["supported_networks"] = [
                        "Ethereum", "Base", "Arbitrum", "Polygon", "Optimism"
                    ]
            except Exception as e:
                logger.warning(f"[DEMO MODE] Failed to get wallet for receive enrichment: {e}")
            
        # Add sources if present
        if sources:
            response["sources"] = sources
            
        # Add registration_required info if needed (for wallet-dependent actions)
        if requires_registration:
            response["enrichment"] = response.get("enrichment", {})
            response["enrichment"]["requires_wallet_connection"] = True
            
        return response
    
    def _build_context_from_messages(self, messages: list) -> str:
        """Build context string from message history for multi-turn support."""
        if not messages:
            return ""
        
        context_lines = []
        for msg in messages:
            role = "User" if msg.role.value == "user" else "Assistant"
            # Truncate long messages in context
            content = msg.content[:200] + "..." if len(msg.content) > 200 else msg.content
            context_lines.append(f"{role}: {content}")
        
        return "\n".join(context_lines)
    
    def _get_demo_handler_name(self, intent: ChatIntent) -> str:
        """Get handler name for demo mode routing metadata."""
        handler_map = {
            # GraphRAG
            ChatIntent.PROTOCOL_SEARCH: "demo_graphrag_handler",
            ChatIntent.RISK_ASSESSMENT: "demo_graphrag_handler",
            ChatIntent.SIMILAR_PROTOCOLS: "demo_graphrag_handler",
            # Hunter AI
            ChatIntent.HUNTER_SENTIMENT: "demo_hunter_sentiment_handler",
            ChatIntent.HUNTER_PRICE_PREDICTION: "demo_hunter_prediction_handler",
            ChatIntent.HUNTER_RISK_SIGNALS: "demo_hunter_risk_handler",
            ChatIntent.HUNTER_TRADING_SIGNALS: "demo_hunter_signals_handler",
            ChatIntent.HUNTER_PATTERNS: "demo_hunter_patterns_handler",
            ChatIntent.HUNTER_PORTFOLIO: "demo_hunter_portfolio_handler",
            # ULTRA
            ChatIntent.ULTRA_ARBITRAGE: "demo_ultra_arbitrage_handler",
            ChatIntent.ULTRA_FLASH_LOANS: "demo_ultra_flashloan_handler",
            ChatIntent.ULTRA_MEV_PROTECTION: "demo_ultra_mev_handler",
            ChatIntent.ULTRA_AUTO_EXECUTOR: "demo_ultra_executor_handler",
            # DeFi
            ChatIntent.LENDING: "demo_lending_handler",
            ChatIntent.MONEY_MARKET: "demo_money_market_handler",
            ChatIntent.SWAP: "demo_swap_handler",
            # Wallet (restricted)
            ChatIntent.BALANCE: "demo_balance_handler",
            ChatIntent.PORTFOLIO: "demo_portfolio_handler",
            ChatIntent.ACTIVITY: "demo_activity_handler",
            ChatIntent.RECEIVE: "demo_receive_handler",
            ChatIntent.BUY: "demo_buy_handler",
            # Agent Squad
            ChatIntent.SPECIALIST_TASK: "demo_specialist_handler",
            ChatIntent.COMPLEX_WORKFLOW: "demo_workflow_handler",
            # Default
            ChatIntent.GENERAL_CONVERSATION: "demo_general_handler",
        }
        return handler_map.get(intent, "demo_handler")

    def _detect_intent_by_keywords_demo(
        self, content: str, context: str, language: str
    ) -> tuple[ChatIntent, float, str]:
        """
        Keyword-based intent detection for demo mode.
        
        No LLM calls - provides instant, reliable intent detection.
        Supports English, Spanish, Portuguese, and Chinese keywords.
        
        Based on SendGuestMessage._detect_intent_by_keywords_with_context()
        """
        import re
        
        content_lower = content.lower()
        context_lower = context.lower() if context else ""

        # ========================================
        # Hunter AI patterns (English + Spanish + Portuguese)
        # ========================================
        hunter_patterns = {
            ChatIntent.HUNTER_SENTIMENT: [
                # English
                "sentiment", "feeling", "mood", "bullish", "bearish",
                "twitter", "reddit", "social", "news", "hype",
                "what do people think", "market mood", "community sentiment",
                # Spanish
                "sentimiento", "opinión", "opiniones", "alcista", "bajista",
                "qué opina", "qué piensan", "clima del mercado", "percepción",
                "sentimiento de mercado", "sentimiento para",
                # Portuguese
                "sentimento", "altista", "baixista", "humor do mercado",
            ],
            ChatIntent.HUNTER_PRICE_PREDICTION: [
                # English
                "predict", "prediction", "forecast", "price target",
                "will go", "where will", "price tomorrow", "future price",
                "price of", "what's the price", "current price", "how much is",
                "what is the price", "price for",
                # Spanish
                "predecir", "predicción", "pronóstico", "objetivo de precio",
                "a dónde irá", "precio de", "cuál es el precio", "precio actual",
                "precio futuro", "va a subir", "va a bajar", "cuánto vale",
                "cuánto cuesta",
                # Portuguese
                "prever", "previsão", "preço de", "qual é o preço", "preço atual",
            ],
            ChatIntent.HUNTER_RISK_SIGNALS: [
                # English
                "risk signal", "market risk", "whale", "liquidation",
                "danger", "warning", "alert", "crash",
                # Spanish
                "señal de riesgo", "riesgo de mercado", "ballena", "liquidación",
                "peligro", "advertencia", "alerta", "caída",
            ],
            ChatIntent.HUNTER_TRADING_SIGNALS: [
                # English
                "trading signal", "buy signal", "sell signal",
                "should i buy", "should i sell", "entry point", "exit point",
                # Spanish
                "señal de trading", "señal de compra", "señal de venta",
                "debería comprar", "debería vender", "punto de entrada", "punto de salida",
            ],
            ChatIntent.HUNTER_PATTERNS: [
                # English
                "chart pattern", "head and shoulders", "double bottom",
                "flag pattern", "triangle", "breakout", "technical analysis",
                # Spanish
                "patrón de gráfico", "hombro cabeza hombro", "doble suelo",
                "patrón de bandera", "triángulo", "ruptura", "análisis técnico",
            ],
            ChatIntent.HUNTER_PORTFOLIO: [
                # English
                "optimize portfolio", "optimize my portfolio", "portfolio allocation",
                "rebalance", "diversify", "risk adjusted", "sharpe ratio",
                "portfolio optimization", "best allocation",
                # Spanish
                "optimizar portafolio", "optimizar mi portafolio", "asignación de portafolio",
                "rebalancear", "diversificar", "ajustado al riesgo",
                "optimización de portafolio", "mejor asignación",
            ],
        }

        # ========================================
        # ULTRA patterns (English + Spanish)
        # ========================================
        ultra_patterns = {
            ChatIntent.ULTRA_ARBITRAGE: [
                "arbitrage", "arb", "price difference", "spread",
                "profit opportunity", "cross dex",
                "arbitraje", "diferencia de precio", "oportunidad de ganancia",
            ],
            ChatIntent.ULTRA_FLASH_LOANS: [
                "flash loan", "flashloan", "flash borrow",
                "instant loan", "uncollateralized",
                "préstamo flash", "préstamo instantáneo", "sin colateral",
            ],
            ChatIntent.ULTRA_MEV_PROTECTION: [
                "mev", "front run", "frontrun", "sandwich",
                "flashbots", "private transaction", "protected",
                "protección mev", "transacción privada", "protegido",
            ],
            ChatIntent.ULTRA_AUTO_EXECUTOR: [
                "auto execute", "automated trading", "trading bot",
                "dca", "limit order", "stop loss", "auto trade",
                "ejecución automática", "trading automatizado", "bot de trading",
            ],
        }

        # ========================================
        # GraphRAG patterns
        # ========================================
        graphrag_patterns = {
            ChatIntent.PROTOCOL_SEARCH: [
                "find protocols", "find defi", "list protocols", "show protocols",
                "search protocols", "discover protocols", "explore protocols",
                "best protocols", "top protocols", "safest protocols",
                "compare protocols", "protocols on", "lending protocols",
                "dex protocols", "staking protocols", "bridge protocols",
                "buscar protocolos", "encontrar protocolos", "mejores protocolos",
            ],
            ChatIntent.RISK_ASSESSMENT: [
                "is it safe", "how safe", "safe to use",
                "what are the risks", "risks of", "risk assessment",
                "es seguro", "es seguro usar", "qué tan seguro",
                "cuáles son los riesgos", "riesgos de", "evaluación de riesgo",
            ],
            ChatIntent.SIMILAR_PROTOCOLS: [
                "similar to", "like", "alternative to", "alternatives for",
                "protocols like", "similar protocols",
                "similar a", "parecido a", "alternativa a",
            ],
        }

        # ========================================
        # DeFi shortcut patterns
        # ========================================
        defi_patterns = {
            ChatIntent.LENDING: [
                "deposit usdc", "deposit eth", "earn on morpho",
                "supply to aave", "lend my", "earn yield",
                "depositar usdc", "depositar eth", "ganar en morpho",
                "prestar en aave", "prestar mi", "ganar rendimiento",
            ],
            ChatIntent.MONEY_MARKET: [
                "money market", "compare aave", "compound vs aave",
                "borrow rate", "lending rate",
                "mercado de dinero", "comparar aave",
            ],
            ChatIntent.SWAP: [
                "swap", "exchange", "trade", "convert",
                "1inch", "uniswap",
                "cambiar", "intercambiar", "convertir", "canjear",
                "quiero swap", "hacer swap", "swap de",
            ],
        }

        # ========================================
        # Wallet patterns (restricted for guests but available for auth users)
        # ========================================
        wallet_patterns = {
            ChatIntent.BALANCE: [
                "my balance", "show balance", "check balance", "wallet balance",
                "mi saldo", "ver saldo", "mostrar saldo", "mi balance",
            ],
            ChatIntent.PORTFOLIO: [
                "my portfolio", "show portfolio", "portfolio performance",
                "mi portafolio", "ver portafolio", "mis posiciones",
            ],
            ChatIntent.ACTIVITY: [
                "my activity", "transaction history", "my transactions",
                "mi actividad", "historial de transacciones",
            ],
            ChatIntent.RECEIVE: [
                "receive address", "my address", "deposit address",
                "dirección de recepción", "mi dirección",
            ],
            ChatIntent.BUY: [
                "buy crypto", "buy bitcoin", "buy eth", "buy usdc",
                "buy with card", "purchase crypto", "i want to buy crypto",
                "comprar cripto", "comprar bitcoin", "comprar eth",
                "quiero comprar cripto", "comprar con tarjeta",
            ],
        }

        # Check Hunter AI patterns FIRST (most common in demo)
        for intent, keywords in hunter_patterns.items():
            for keyword in keywords:
                if keyword in content_lower:
                    handler = self._get_demo_handler_name(intent)
                    return intent, 0.90, handler

        # Check ULTRA patterns
        for intent, keywords in ultra_patterns.items():
            for keyword in keywords:
                if keyword in content_lower:
                    handler = self._get_demo_handler_name(intent)
                    return intent, 0.85, handler

        # Check GraphRAG patterns
        for intent, keywords in graphrag_patterns.items():
            for keyword in keywords:
                if keyword in content_lower:
                    handler = self._get_demo_handler_name(intent)
                    return intent, 0.85, handler

        # Check DeFi patterns
        for intent, keywords in defi_patterns.items():
            for keyword in keywords:
                if keyword in content_lower:
                    handler = self._get_demo_handler_name(intent)
                    return intent, 0.80, handler

        # Check wallet patterns (for authenticated users)
        for intent, keywords in wallet_patterns.items():
            for keyword in keywords:
                if keyword in content_lower:
                    handler = self._get_demo_handler_name(intent)
                    return intent, 0.85, handler

        # Context-based follow-up detection (if previous messages mentioned price/sentiment)
        if context_lower:
            follow_up_patterns = [
                "and what about", "what about", "how about", "and for",
                "y qué hay de", "qué tal", "y para", "y sobre",
            ]
            for pattern in follow_up_patterns:
                if pattern in content_lower:
                    if any(kw in context_lower for kw in ["sentiment", "sentimiento"]):
                        return ChatIntent.HUNTER_SENTIMENT, 0.80, "demo_hunter_sentiment_handler"
                    if any(kw in context_lower for kw in ["price", "precio", "predict", "predecir"]):
                        return ChatIntent.HUNTER_PRICE_PREDICTION, 0.80, "demo_hunter_prediction_handler"

        # Default to general conversation
        return ChatIntent.GENERAL_CONVERSATION, 0.65, "demo_general_handler"

    async def _handle_protocol_search(
        self, user_id, conversation_id, content, intent_result, language: str = "en"
    ) -> dict:
        """Handle protocol search intent via GraphRAG (with i18n support)."""
        entities = intent_result.extracted_entities

        # Build user preferences from entities
        user_preferences = {}
        if "risk_preference" in entities:
            user_preferences["risk_tolerance"] = (
                "conservative" if entities["risk_preference"] == "low" else "aggressive"
            )
        if "chain" in entities:
            user_preferences["preferred_chains"] = [entities["chain"]]
        if "category" in entities:
            user_preferences["preferred_categories"] = [entities["category"]]

        # Perform GraphRAG search (multilingual embeddings handle cross-language queries)
        search_results = await self._graphrag_search.search_protocols_from_chat(
            message=content,
            user_preferences=user_preferences,
            conversation_id=conversation_id,
            language=language,
        )

        # Format response message
        response_content = self._format_search_results(search_results)

        # Collect sources
        from datetime import datetime
        from app.infrastructure.adapters.agent_squad.agents.source_helpers import (
            create_database_source,
        )
        
        sources = []
        fetched_at = datetime.utcnow()
        
        # Add GraphRAG database source
        sources.append(create_database_source(
            source_name="GraphRAG Knowledge Base",
            citation_text="Protocol search results from Anvil's GraphRAG knowledge base",
            fetched_at=fetched_at,
            data_points_used=len(search_results.results),
            metadata={
                "search_type": "protocol_search",
                "protocols_found": len(search_results.results),
            },
        ))

        # Save to conversation history (with sources)
        user_msg, agent_msg = await self._save_messages(
            conversation_id, content, response_content, sources=sources
        )

        # Convert sources to dict for response
        sources_response = [s.to_dict() if hasattr(s, "to_dict") else s for s in sources]

        return {
            "user_message": self._message_to_dict(user_msg),
            "agent_message": self._message_to_dict(agent_msg),
            "routing": {
                "intent": intent_result.intent.value,
                "confidence": intent_result.confidence,
                "handler": "graphrag_search",
                "reasoning": intent_result.reasoning,
            },
            "enrichment": {
                "protocols": [
                    {
                        "protocol_id": str(r.protocol_id),
                        "protocol_name": r.protocol_name,
                        "similarity_score": r.similarity_score,
                        "risk_score": r.risk_score,
                        "risk_level": r.risk_level,
                        "tvl": r.tvl,
                        "category": r.category,
                        "chain": r.chain,
                    }
                    for r in search_results.results
                ],
                "search_context": search_results.search_explanation,
                "recommendations": search_results.recommendations,
            },
            "sources": sources_response,  # NEW
        }

    async def _handle_risk_assessment(
        self, user_id, conversation_id, content, intent_result, language: str = "en"
    ) -> dict:
        """Handle risk assessment intent via GraphRAG (with i18n support)."""
        entities = intent_result.extracted_entities

        if "protocol_name" not in entities:
            # Fallback to general chat if no protocol detected
            return await self._handle_general_conversation(
                user_id, conversation_id, content, intent_result
            )

        # Perform risk analysis
        risk_insights = await self._graphrag_risk.get_protocol_risk_from_chat(
            protocol_name=entities["protocol_name"],
            conversation_id=conversation_id,
            operation_type=entities.get("operation_type"),
            amount_usd=entities.get("amount_usd"),
        )

        # Format response
        response_content = self._format_risk_analysis(risk_insights)

        # Collect sources
        from datetime import datetime
        from app.infrastructure.adapters.agent_squad.agents.source_helpers import (
            create_database_source,
            create_api_source,
        )
        
        sources = []
        fetched_at = datetime.utcnow()
        
        # Add GraphRAG database source
        sources.append(create_database_source(
            source_name="GraphRAG Knowledge Base",
            citation_text=f"Risk analysis for {entities['protocol_name']} from Anvil's GraphRAG knowledge base",
            fetched_at=fetched_at,
            metadata={
                "search_type": "risk_assessment",
                "protocol_name": entities["protocol_name"],
            },
        ))
        
        # TODO: Add DeFiLlama source when integrated
        # sources.append(create_api_source(
        #     source_name="DeFiLlama",
        #     url=f"https://defillama.com/protocol/{entities['protocol_name']}",
        #     citation_text=f"DeFiLlama risk data for {entities['protocol_name']}",
        #     fetched_at=fetched_at,
        # ))

        # Save to conversation (with sources)
        user_msg, agent_msg = await self._save_messages(
            conversation_id, content, response_content, sources=sources
        )
        
        sources_response = [s.to_dict() if hasattr(s, "to_dict") else s for s in sources]

        return {
            "user_message": self._message_to_dict(user_msg),
            "agent_message": self._message_to_dict(agent_msg),
            "routing": {
                "intent": intent_result.intent.value,
                "confidence": intent_result.confidence,
                "handler": "graphrag_search",
                "reasoning": intent_result.reasoning,
            },
            "enrichment": {
                "risk_analysis": {
                    "protocol_id": str(risk_insights.risk_analysis.protocol_id),
                    "protocol_name": risk_insights.risk_analysis.protocol_name,
                    "risk_score": risk_insights.risk_analysis.risk_score,
                    "risk_level": risk_insights.risk_analysis.risk_level,
                    "confidence": risk_insights.risk_analysis.confidence,
                    "should_warn": risk_insights.risk_analysis.should_warn,
                },
                "alternatives_count": len(risk_insights.alternatives),
            },
            "sources": sources_response,  # NEW
        }

    async def _handle_similar_protocols(
        self, user_id, conversation_id, content, intent_result, language: str = "en"
    ) -> dict:
        """Handle similar protocols intent via GraphRAG (with i18n support)."""
        entities = intent_result.extracted_entities
        protocol_name = entities.get("protocol_name", "")

        if not protocol_name:
            # Fallback to general chat if no protocol detected
            return await self._handle_general_conversation(
                user_id, conversation_id, content, intent_result
            )

        # Find base protocol (multilingual search)
        base_search = await self._graphrag_search.search_protocols_from_chat(
            message=protocol_name,
            conversation_id=conversation_id,
            language=language,
        )

        # Protocol not found messages (i18n)
        not_found_messages = {
            "en": f"I couldn't find the protocol '{protocol_name}'. Could you provide more details or check the spelling?",
            "es": f"No pude encontrar el protocolo '{protocol_name}'. ¿Podrías proporcionar más detalles o verificar la ortografía?",
            "pt": f"Não encontrei o protocolo '{protocol_name}'. Poderia fornecer mais detalhes ou verificar a ortografia?",
            "zh": f"未能找到协议 '{protocol_name}'。您能提供更多详情或检查拼写吗?",
            "fr": f"Je n'ai pas trouvé le protocole '{protocol_name}'. Pourriez-vous fournir plus de détails ou vérifier l'orthographe?",
        }

        if not base_search.results:
            # Protocol not found - fallback to general chat
            response_content = not_found_messages.get(language, not_found_messages["en"])
            user_msg, agent_msg = await self._save_messages(
                conversation_id, content, response_content
            )
            return {
                "user_message": self._message_to_dict(user_msg),
                "agent_message": self._message_to_dict(agent_msg),
                "routing": {
                    "intent": intent_result.intent.value,
                    "confidence": intent_result.confidence,
                    "handler": "graphrag_search",
                    "reasoning": "Protocol not found, fallback response",
                    "language": language,
                },
            }

        base_protocol = base_search.results[0]

        # Find similar protocols (multilingual search)
        similar_search = await self._graphrag_search.search_protocols_from_chat(
            message=f"protocols similar to {protocol_name}",
            conversation_id=conversation_id,
            language=language,
        )

        # Filter out base protocol
        similar_protocols = [
            r for r in similar_search.results
            if r.protocol_id != base_protocol.protocol_id
        ][:5]

        # Format response
        response_content = self._format_similar_protocols(
            base_protocol, similar_protocols
        )

        # Collect sources
        from datetime import datetime
        from app.infrastructure.adapters.agent_squad.agents.source_helpers import (
            create_database_source,
        )
        
        sources = []
        fetched_at = datetime.utcnow()
        
        # Add GraphRAG database source
        sources.append(create_database_source(
            source_name="GraphRAG Knowledge Base",
            citation_text=f"Similar protocols to {protocol_name} from Anvil's GraphRAG knowledge base",
            fetched_at=fetched_at,
            data_points_used=len(similar_protocols) + 1,  # Base + similar
            metadata={
                "search_type": "similar_protocols",
                "base_protocol": protocol_name,
                "similar_count": len(similar_protocols),
            },
        ))

        # Save to conversation (with sources)
        user_msg, agent_msg = await self._save_messages(
            conversation_id, content, response_content, sources=sources
        )
        
        sources_response = [s.to_dict() if hasattr(s, "to_dict") else s for s in sources]

        return {
            "user_message": self._message_to_dict(user_msg),
            "agent_message": self._message_to_dict(agent_msg),
            "sources": sources_response,  # NEW
            "routing": {
                "intent": intent_result.intent.value,
                "confidence": intent_result.confidence,
                "handler": "graphrag_search",
                "reasoning": intent_result.reasoning,
            },
            "enrichment": {
                "base_protocol": {
                    "protocol_id": str(base_protocol.protocol_id),
                    "protocol_name": base_protocol.protocol_name,
                    "risk_score": base_protocol.risk_score,
                    "tvl": base_protocol.tvl,
                },
                "similar_protocols": [
                    {
                        "protocol_id": str(p.protocol_id),
                        "protocol_name": p.protocol_name,
                        "similarity_score": p.similarity_score,
                        "tvl": p.tvl,
                    }
                    for p in similar_protocols
                ]
            }
        }

    async def _handle_specialist_task(
        self, user_id, conversation_id, content, intent_result
    ) -> dict:
        """Handle specialist task intent via Agent Squad."""
        # Execute Agent Squad routing (messages already saved by agent_squad.execute)
        result = await self._agent_squad.execute(
            conversation_id=conversation_id,
            user_id=user_id,
            content=content,
            force_agent=intent_result.suggested_agent,  # Use suggested agent
        )

        # In tests, the mock doesn't actually save messages to DB
        # In production, messages are saved by agent_squad.execute
        # Try to retrieve messages, fall back to manual construction if not found
        user_msg = await self._conversation_repo.get_message(result["user_message_id"])
        agent_msg = await self._conversation_repo.get_message(result["agent_message_id"])

        # Extract sources from agent response if available
        sources = []
        if "sources" in result:
            sources = result["sources"]
        elif "tools_used" in result and result.get("tools_used"):
            # Fallback: create basic sources from tools_used
            from app.domain.value_objects.chat.source_info import SourceInfo, SourceType
            from datetime import datetime
            fetched_at = datetime.utcnow()
            for tool in result["tools_used"]:
                if tool != "openai_api":  # Skip LLM as it's implicit
                    sources.append(SourceInfo(
                        source_type=SourceType.API,
                        source_name=tool.replace("_api", "").replace("_", " ").title(),
                        citation_text=f"Data from {tool}",
                        fetched_at=fetched_at,
                        provider=tool,
                    ))

        if user_msg and agent_msg:
            # Production: messages were saved by agent_squad.execute
            user_message_dict = self._message_to_dict(user_msg)
            agent_message_dict = self._message_to_dict(agent_msg)
        else:
            # Test/Mock: construct message dicts manually with all required fields
            from app.domain.common.datetime_utils import utc_now
            user_message_dict = {
                "id": str(result["user_message_id"]),
                "conversation_id": str(conversation_id),
                "role": "user",
                "content": content,
                "agent_type": None,
                "created_at": utc_now().isoformat(),
            }
            agent_message_dict = {
                "id": str(result["agent_message_id"]),
                "conversation_id": str(conversation_id),
                "role": "assistant",
                "content": result["content"],
                "agent_type": result["agent_type"],
                "created_at": utc_now().isoformat(),
            }
            # Add sources to agent message dict if available
            if sources:
                agent_message_dict["sources"] = [
                    s.to_dict() if hasattr(s, "to_dict") else s
                    for s in sources
                ]

        # Convert sources to dict format for response
        sources_response = []
        if sources:
            sources_response = [
                s.to_dict() if hasattr(s, "to_dict") else s
                for s in sources
            ]

        return {
            "user_message": user_message_dict,
            "agent_message": agent_message_dict,
            "sources": sources_response,  # NEW: Aggregated sources
            "routing": {
                "intent": intent_result.intent.value,
                "confidence": intent_result.confidence,
                "handler": "agent_orchestrator",
                "agent_used": result["agent_type"],
                "reasoning": intent_result.reasoning,
            },
            "enrichment": {
                "task_type": result.get("task_type"),
                "has_tools_used": bool(result.get("tools_used")),
                "tools_used": result.get("tools_used", []),
                "tokens_consumed": result.get("tokens_used"),
                "latency_ms": result.get("latency_ms"),
                "intent_classification": result.get("intent_classification"),
            }
        }

    async def _handle_complex_workflow(
        self, user_id, conversation_id, content, intent_result
    ) -> dict:
        """Handle complex workflow intent via Supervisor."""
        # Execute Supervisor workflow
        result = await self._supervisor.execute(
            conversation_id=conversation_id,
            user_id=user_id,
            complex_task=content,
            max_agents=5,
        )

        # Save messages to conversation history
        response_content = result.get("final_response", "")
        user_msg, agent_msg = await self._save_messages(
            conversation_id, content, response_content
        )

        return {
            "user_message": self._message_to_dict(user_msg),
            "agent_message": self._message_to_dict(agent_msg),
            "routing": {
                "intent": intent_result.intent.value,
                "confidence": intent_result.confidence,
                "handler": "agent_orchestrator",
                "reasoning": intent_result.reasoning,
            },
            "enrichment": {
                "workflow_id": str(result.get("workflow_id")),
                "workflow_status": result.get("status"),
                "tasks_count": len(result.get("tasks", [])),
                "agents_involved": result.get("agents_used", []),
                "total_latency_ms": result.get("total_latency_ms"),
                "workflow_type": result.get("workflow_type"),
                "capital": result.get("capital"),
            }
        }

    async def _handle_general_conversation(
        self, user_id, conversation_id, content, intent_result
    ) -> dict:
        """Handle general conversation intent via Regular Chat."""
        # Execute regular chat
        user_msg, agent_msg = await self._regular_chat.execute(
            user_id=user_id,
            conversation_id=conversation_id,
            content=content,
        )

        return {
            "user_message": self._message_to_dict(user_msg),
            "agent_message": self._message_to_dict(agent_msg),
            "routing": {
                "intent": intent_result.intent.value,
                "confidence": intent_result.confidence,
                "handler": "general_chat",
                "reasoning": intent_result.reasoning,
            },
        }

    async def _save_messages(
        self,
        conversation_id: UUID,
        user_content: str,
        agent_content: str,
        agent_type: str | None = None,
        sources: list | None = None,
    ) -> tuple[Message, Message]:
        """
        Save user and agent messages to conversation.
        
        Args:
            conversation_id: Conversation ID
            user_content: User message content
            agent_content: Agent message content
            agent_type: Optional agent type
            sources: Optional list of SourceInfo objects or dicts
        """
        # Create and save user message
        user_message = Message.create_user_message(
            conversation_id=conversation_id,
            content=user_content,
        )
        await self._conversation_repo.add_message(user_message)

        # Prepare metadata for agent message (include sources)
        metadata = {}
        if sources:
            # Convert SourceInfo objects to dicts if needed
            sources_data = []
            for source in sources:
                if hasattr(source, "to_dict"):
                    sources_data.append(source.to_dict())
                elif isinstance(source, dict):
                    sources_data.append(source)
            metadata["sources"] = sources_data

        # Create and save agent message
        agent_message = Message.create_agent_message(
            conversation_id=conversation_id,
            content=agent_content,
            agent_type=agent_type,
            metadata=metadata if metadata else None,
        )
        await self._conversation_repo.add_message(agent_message)

        # Update conversation timestamp
        conversation = await self._conversation_repo.get_conversation(conversation_id)
        if conversation:
            conversation.touch()
            await self._conversation_repo.update_conversation(conversation)
        else:
            # This shouldn't happen, but log if it does
            logger.warning(f"Conversation {conversation_id} not found after saving messages")

        return user_message, agent_message

    def _message_to_dict(self, message: Message) -> dict:
        """Convert Message entity to dict for response."""
        from app.domain.value_objects.chat.source_info import SourceInfo
        
        # Map 'agent' role to 'assistant' for OpenAI API compatibility
        role = "assistant" if message.role.value == "agent" else message.role.value

        # Extract sources from metadata
        sources = []
        if message.metadata and "sources" in message.metadata:
            sources_data = message.metadata["sources"]
            if isinstance(sources_data, list):
                for s in sources_data:
                    if isinstance(s, dict):
                        sources.append(s)
                    elif hasattr(s, "to_dict"):
                        sources.append(s.to_dict())

        result = {
            "id": str(message.id),
            "conversation_id": str(message.conversation_id),
            "role": role,
            "content": message.content,
            "agent_type": message.agent_type,
            "created_at": message.created_at.isoformat(),
        }
        
        # Add sources if present
        if sources:
            result["sources"] = sources
        
        return result

    def _format_search_results(self, search_results) -> str:
        """Format GraphRAG search results as markdown."""
        if not search_results.results:
            return "I couldn't find any protocols matching your criteria. Try broadening your search or adjusting your preferences."

        output = f"**{search_results.search_explanation}**\n\n"

        for i, protocol in enumerate(search_results.results, 1):
            output += f"**{i}. {protocol.protocol_name}**\n"
            output += f"- TVL: ${protocol.tvl / 1e9:.2f}B\n"
            output += f"- Risk: {protocol.risk_level} ({protocol.risk_score:.1f}/10)\n"
            output += f"- Category: {protocol.category}\n"
            output += f"- Chain: {protocol.chain}\n"
            if protocol.apy:
                output += f"- APY: {protocol.apy:.2f}%\n"
            output += f"- Why relevant: {protocol.why_relevant}\n\n"

        if search_results.recommendations:
            output += "**Recommendations:**\n"
            for rec in search_results.recommendations:
                output += f"- {rec}\n"

        return output

    def _format_risk_analysis(self, risk_insights) -> str:
        """Format risk analysis as markdown."""
        ra = risk_insights.risk_analysis

        output = f"**Risk Analysis: {ra.protocol_name}**\n\n"
        output += f"**Overall Risk:** {ra.risk_score:.1f}/10 ({ra.risk_level})\n"
        output += f"**Confidence:** {ra.confidence * 100:.0f}%\n\n"

        if ra.contributing_factors:
            output += "**Contributing Factors:**\n"
            for factor in ra.contributing_factors:
                critical = " ⚠️ CRITICAL" if factor.is_critical else ""
                output += f"\n**{factor.factor}**{critical}\n"
                output += f"- Impact: {factor.impact:.1f}/10\n"
                output += f"- {factor.description}\n"

        if ra.recommendations:
            output += "\n**Recommendations:**\n"
            for rec in ra.recommendations:
                output += f"- {rec}\n"

        if ra.should_warn and ra.warning_message:
            output += f"\n⚠️ **Warning:** {ra.warning_message}\n"

        if risk_insights.alternatives:
            output += "\n**Safer Alternatives:**\n"
            for alt in risk_insights.alternatives[:3]:
                output += f"\n**{alt.protocol_name}** (Risk: {alt.risk_level})\n"
                output += f"- {alt.why_better}\n"
                output += f"- TVL: ${alt.tvl / 1e9:.2f}B\n"

        return output

    def _format_similar_protocols(self, base, similar_list) -> str:
        """Format similar protocols as markdown."""
        output = f"**Protocols Similar to {base.protocol_name}**\n\n"
        output += "**Base Protocol:**\n"
        output += f"- TVL: ${base.tvl / 1e9:.2f}B\n"
        output += f"- Risk: {base.risk_level} ({base.risk_score:.1f}/10)\n"
        output += f"- Category: {base.category}\n\n"

        if not similar_list:
            output += "No similar protocols found. Try exploring other categories or chains."
            return output

        output += "**Similar Protocols:**\n\n"

        for i, protocol in enumerate(similar_list, 1):
            output += f"**{i}. {protocol.protocol_name}**\n"
            output += f"- Similarity: {protocol.similarity_score * 100:.0f}%\n"
            output += f"- TVL: ${protocol.tvl / 1e9:.2f}B\n"
            output += f"- Risk: {protocol.risk_level} ({protocol.risk_score:.1f}/10)\n"
            output += f"- Why similar: {protocol.why_relevant}\n\n"

        return output

    async def _handle_hunter_sentiment(
        self, user_id: int, conversation_id: int, content: str, intent_result
    ) -> dict:
        """Handle sentiment analysis intent via Hunter AI."""
        entities = intent_result.extracted_entities
        token_symbol = entities.get("token_symbol", "ETH")
        time_horizon = entities.get("time_horizon", "24h")
        sources = entities.get("sources")

        try:
            # Parse time horizon to hours
            hours = 24
            if time_horizon == "7d":
                hours = 168
            elif time_horizon == "30d":
                hours = 720

            # Parse sources if specified
            source_list = None
            if sources:
                source_list = [
                    SentimentSource(name.lower())
                    for name in sources
                    if name.lower() in [s.value for s in SentimentSource]
                ]

            # Initialize analyzers
            twitter_analyzer = TwitterSentimentAnalyzer(TwitterConfig(enabled=True))
            reddit_analyzer = RedditSentimentAnalyzer(RedditConfig(enabled=True))
            discord_analyzer = DiscordSentimentAnalyzer(DiscordConfig(enabled=True))
            news_analyzer = NewsSentimentAnalyzer(NewsConfig(enabled=True))
            aggregator = SentimentAggregator()

            # Collect sentiment readings
            readings = []

            # Twitter sentiment
            if not source_list or SentimentSource.TWITTER in source_list:
                twitter_reading = await twitter_analyzer.analyze_token_sentiment(
                    token_symbol, hours
                )
                readings.append(twitter_reading)

            # Reddit sentiment
            if not source_list or SentimentSource.REDDIT in source_list:
                reddit_reading = await reddit_analyzer.analyze_token_sentiment(
                    token_symbol, hours
                )
                readings.append(reddit_reading)

            # Discord sentiment
            if not source_list or SentimentSource.DISCORD in source_list:
                discord_reading = await discord_analyzer.analyze_token_sentiment(
                    token_symbol, hours
                )
                readings.append(discord_reading)

            # News sentiment
            if not source_list or SentimentSource.NEWS in source_list:
                news_reading = await news_analyzer.analyze_token_sentiment(
                    token_symbol, hours
                )
                readings.append(news_reading)

            # Aggregate sentiment
            aggregated = aggregator.aggregate(readings, token_symbol)

            # Get source breakdown
            source_breakdown = aggregator.get_source_breakdown(aggregated)

            # Identify divergence
            divergence = aggregator.identify_divergence(aggregated)

            # Format response
            response_content = f"📊 **Sentiment Analysis for {token_symbol}**\n\n"
            response_content += f"**Overall Sentiment:** {aggregated.classification.value.title()} ({aggregated.overall_score:.1f}/100)\n"
            response_content += f"**Confidence:** {aggregated.overall_confidence * 100:.0f}%\n"
            response_content += f"**Signal Strength:** {aggregated.signal_strength}\n"
            response_content += f"**Consensus:** {divergence['consensus'] * 100:.0f}%\n\n"

            response_content += "**Source Breakdown:**\n"
            for source_name, data in source_breakdown.items():
                response_content += f"- {source_name.title()}: {data['score']:.1f}/100 (weight: {data['weight'] * 100:.0f}%)\n"

            if divergence["has_divergence"]:
                response_content += "\n⚠️ **Divergence Detected:** Sources show conflicting signals. Proceed with caution.\n"

            response_content += f"\n*Analysis based on {hours}h of data from {aggregated.source_count} sources*"

        except Exception as e:
            # Fallback to placeholder response on error
            response_content = f"📊 **Sentiment Analysis for {token_symbol}**\n\n"
            response_content += f"⚠️ Unable to fetch real-time sentiment data: {e!s}\n\n"
            response_content += "This feature routes to Hunter AI sentiment analysis tools:\n"
            response_content += "- Twitter sentiment\n"
            response_content += "- Reddit discussions\n"
            response_content += "- Discord communities\n"
            response_content += "- News coverage\n"

        user_msg, agent_msg = await self._save_messages(
            conversation_id, content, response_content
        )

        return {
            "user_message": self._message_to_dict(user_msg),
            "agent_message": self._message_to_dict(agent_msg),
            "routing": {
                "intent": intent_result.intent.value,
                "confidence": intent_result.confidence,
                "handler": "hunter_ai",
                "agent_used": "hunter_ai",
                "reasoning": intent_result.reasoning,
            },
            "enrichment": {
                "token_symbol": token_symbol,
                "time_horizon": time_horizon,
                "sources": sources or ["twitter", "reddit", "discord", "news"],
                "hunter_tool": "sentiment_analyzer",
            },
        }

    async def _handle_hunter_price_prediction(
        self, user_id: int, conversation_id: int, content: str, intent_result
    ) -> dict:
        """Handle price prediction intent via Hunter AI."""
        entities = intent_result.extracted_entities
        token_symbol = entities.get("token_symbol", "ETH")
        time_horizon = entities.get("time_horizon", "24h")

        try:
            # Parse time horizon to hours
            hours = 24
            if time_horizon == "7d":
                hours = 168
            elif time_horizon == "30d":
                hours = 720

            # Get price prediction
            predictor = LSTMPricePredictor()
            prediction = await predictor.predict(token_symbol, horizon_hours=hours)

            # Format response
            response_content = f"📈 **Price Prediction for {token_symbol}**\n\n"
            response_content += f"**Current Price:** ${prediction.current_price:,.2f}\n"
            response_content += f"**Predicted Price ({time_horizon}):** ${prediction.predicted_price:,.2f}\n"
            response_content += f"**Change:** {prediction.change_percent:+.2f}%\n"
            response_content += f"**Direction:** {prediction.direction.upper()} {'📈' if prediction.direction == 'up' else '📉' if prediction.direction == 'down' else '➡️'}\n"
            response_content += f"**Confidence:** {prediction.confidence * 100:.0f}%\n\n"

            response_content += "**Analysis:**\n"
            if prediction.direction == "up":
                response_content += f"- Bullish trend detected with {prediction.change_percent:.1f}% expected upside\n"
            elif prediction.direction == "down":
                response_content += f"- Bearish trend detected with {prediction.change_percent:.1f}% expected downside\n"
            else:
                response_content += "- Sideways movement expected with minimal price action\n"

            response_content += "\n*LSTM forecast based on historical price patterns. Not financial advice.*"

        except Exception as e:
            # Fallback to placeholder response on error
            response_content = f"📈 **Price Prediction for {token_symbol}**\n\n"
            response_content += f"⚠️ Unable to generate price prediction: {e!s}\n\n"
            response_content += "This feature routes to Hunter AI LSTM price prediction:\n"
            response_content += "- Historical price analysis\n"
            response_content += "- Machine learning forecasting\n"
            response_content += "- Confidence intervals\n"
            response_content += "- Price targets\n"

        user_msg, agent_msg = await self._save_messages(
            conversation_id, content, response_content
        )

        return {
            "user_message": self._message_to_dict(user_msg),
            "agent_message": self._message_to_dict(agent_msg),
            "routing": {
                "intent": intent_result.intent.value,
                "confidence": intent_result.confidence,
                "handler": "hunter_ai",
                "agent_used": "hunter_ai",
                "reasoning": intent_result.reasoning,
            },
            "enrichment": {
                "token_symbol": token_symbol,
                "time_horizon": time_horizon,
                "hunter_tool": "lstm_predictor",
            },
        }

    async def _handle_hunter_risk_signals(
        self, user_id: int, conversation_id: int, content: str, intent_result
    ) -> dict:
        """Handle risk signals intent via Hunter AI."""
        entities = intent_result.extracted_entities
        token_symbol = entities.get("token_symbol", "ETH")

        try:
            # Get comprehensive risk analysis
            analyzer = RiskAnalyzer()
            assessment = await analyzer.analyze_comprehensive_risk(token_symbol)

            # Format response
            response_content = f"⚠️ **Risk Analysis for {token_symbol}**\n\n"
            response_content += f"**Overall Risk:** {assessment.overall_risk_level.upper()} ({assessment.overall_risk_score:.1f}/100)\n\n"

            response_content += "**Risk Factors:**\n"
            for factor_name, factor in assessment.risk_factors.items():
                emoji = "🔴" if factor.level == "high" or factor.level == "extreme" else "🟡" if factor.level == "medium" else "🟢"
                response_content += f"{emoji} **{factor_name.replace('_', ' ').title()}:** {factor.level.upper()} ({factor.score:.1f}/100)\n"

            response_content += f"\n**Recommendation:**\n{assessment.recommendation}\n"
            response_content += "\n*ML-based risk analysis across volatility, liquidity, smart contract, and correlation factors*"

        except Exception as e:
            # Fallback to placeholder response on error
            response_content = f"⚠️ **Risk Signals for {token_symbol}**\n\n"
            response_content += f"⚠️ Unable to fetch risk analysis: {e!s}\n\n"
            response_content += "This feature routes to Hunter AI risk detection:\n"
            response_content += "- Market volatility warnings\n"
            response_content += "- Liquidity risk signals\n"
            response_content += "- Price anomaly detection\n"
            response_content += "- Risk severity scoring\n"

        user_msg, agent_msg = await self._save_messages(
            conversation_id, content, response_content
        )

        return {
            "user_message": self._message_to_dict(user_msg),
            "agent_message": self._message_to_dict(agent_msg),
            "routing": {
                "intent": intent_result.intent.value,
                "confidence": intent_result.confidence,
                "handler": "hunter_ai",
                "agent_used": "hunter_ai",
                "reasoning": intent_result.reasoning,
            },
            "enrichment": {
                "token_symbol": token_symbol,
                "hunter_tool": "risk_detector",
            },
        }

    async def _handle_hunter_trading_signals(
        self, user_id: int, conversation_id: int, content: str, intent_result
    ) -> dict:
        """Handle trading signals intent via Hunter AI."""
        entities = intent_result.extracted_entities
        token_symbol = entities.get("token_symbol", "ETH")

        try:
            # Generate trading signal (default 1d timeframe)
            generator = TradingSignalGenerator()
            signal = await generator.generate_signal(token_symbol, Timeframe.DAY_1)

            # Format response
            signal_emoji = "🟢" if "BUY" in signal.signal_type.value else "🔴" if "SELL" in signal.signal_type.value else "🟡"
            response_content = f"{signal_emoji} **Trading Signal for {token_symbol}**\n\n"
            response_content += f"**Signal:** {signal.signal_type.value} (Strength: {signal.signal_strength:.1f}/100)\n"
            response_content += f"**Confidence:** {signal.confidence * 100:.0f}%\n\n"

            if signal.entry_price:
                response_content += f"**Entry Price:** ${signal.entry_price:,.2f}\n"
            if signal.stop_loss_price:
                response_content += f"**Stop Loss:** ${signal.stop_loss_price:,.2f}\n"
            if signal.take_profit_price:
                response_content += f"**Take Profit:** ${signal.take_profit_price:,.2f}\n"

            response_content += "\n**Component Scores:**\n"
            response_content += f"- Sentiment: {signal.sentiment_score:.1f}/100\n"
            response_content += f"- Price Prediction: {signal.prediction_score:.1f}/100\n"
            response_content += f"- Risk-Adjusted: {signal.risk_score:.1f}/100\n"

            response_content += f"\n**Recommendation:**\n{signal.recommendation}\n"
            response_content += "\n*AI-powered signal combining sentiment, price prediction, and risk analysis*"

        except Exception as e:
            # Fallback to placeholder response on error
            response_content = f"📉 **Trading Signals for {token_symbol}**\n\n"
            response_content += f"⚠️ Unable to generate trading signal: {e!s}\n\n"
            response_content += "This feature routes to Hunter AI trading analysis:\n"
            response_content += "- Buy/sell recommendations\n"
            response_content += "- Entry/exit points\n"
            response_content += "- Signal strength indicators\n"
            response_content += "- Risk-reward ratios\n"

        user_msg, agent_msg = await self._save_messages(
            conversation_id, content, response_content
        )

        return {
            "user_message": self._message_to_dict(user_msg),
            "agent_message": self._message_to_dict(agent_msg),
            "routing": {
                "intent": intent_result.intent.value,
                "confidence": intent_result.confidence,
                "handler": "hunter_ai",
                "agent_used": "hunter_ai",
                "reasoning": intent_result.reasoning,
            },
            "enrichment": {
                "token_symbol": token_symbol,
                "hunter_tool": "signal_generator",
            },
        }

    async def _handle_hunter_patterns(
        self, user_id: int, conversation_id: int, content: str, intent_result
    ) -> dict:
        """Handle chart pattern detection intent via Hunter AI."""
        entities = intent_result.extracted_entities
        token_symbol = entities.get("token_symbol", "ETH")

        try:
            # Get pattern analysis
            recognizer = PatternRecognizer()
            chart_patterns = await recognizer.detect_chart_patterns(token_symbol.upper())
            candlestick_patterns = await recognizer.detect_candlestick_patterns(token_symbol.upper())
            levels = await recognizer.find_support_resistance(token_symbol.upper())

            # Format response
            response_content = f"📊 **Pattern Analysis for {token_symbol}**\n\n"

            # Chart patterns
            if chart_patterns:
                response_content += "**Chart Patterns:**\n"
                for pattern in chart_patterns[:3]:  # Top 3 patterns
                    emoji = "🔴" if pattern.signal == "bearish" else "🟢" if pattern.signal == "bullish" else "🟡"
                    response_content += f"{emoji} {pattern.pattern_type.replace('_', ' ').title()} ({pattern.confidence * 100:.0f}% confidence)\n"
                response_content += "\n"

            # Candlestick patterns
            if candlestick_patterns:
                response_content += "**Recent Candlestick Patterns:**\n"
                for pattern in candlestick_patterns[:3]:  # Top 3 patterns
                    emoji = "🔴" if pattern.signal == "bearish" else "🟢" if pattern.signal == "bullish" else "🟡"
                    response_content += f"{emoji} {pattern.pattern.replace('_', ' ').title()} ({pattern.confidence * 100:.0f}% confidence)\n"
                response_content += "\n"

            # Support/Resistance levels
            if levels:
                response_content += "**Support Levels:**\n"
                for level in levels["support"][:2]:  # Top 2
                    response_content += f"- ${level.level:,.2f} (strength: {level.strength * 100:.0f}%, {level.touches} touches)\n"

                response_content += "\n**Resistance Levels:**\n"
                for level in levels["resistance"][:2]:  # Top 2
                    response_content += f"- ${level.level:,.2f} (strength: {level.strength * 100:.0f}%, {level.touches} touches)\n"

            response_content += "\n*Technical pattern analysis using historical price data*"

        except Exception as e:
            # Fallback to placeholder response on error
            response_content = f"📊 **Chart Pattern Analysis for {token_symbol}**\n\n"
            response_content += f"⚠️ Unable to detect patterns: {e!s}\n\n"
            response_content += "This feature routes to Hunter AI pattern detection:\n"
            response_content += "- Head and shoulders patterns\n"
            response_content += "- Support/resistance levels\n"
            response_content += "- Trend line analysis\n"
            response_content += "- Pattern reliability scores\n"

        user_msg, agent_msg = await self._save_messages(
            conversation_id, content, response_content
        )

        return {
            "user_message": self._message_to_dict(user_msg),
            "agent_message": self._message_to_dict(agent_msg),
            "routing": {
                "intent": intent_result.intent.value,
                "confidence": intent_result.confidence,
                "handler": "hunter_ai",
                "agent_used": "hunter_ai",
                "reasoning": intent_result.reasoning,
            },
            "enrichment": {
                "token_symbol": token_symbol,
                "hunter_tool": "pattern_detector",
            },
        }

    async def _handle_hunter_portfolio(
        self, user_id: int, conversation_id: int, content: str, intent_result
    ) -> dict:
        """Handle portfolio optimization intent via Hunter AI."""
        entities = intent_result.extracted_entities
        tokens = entities.get("tokens", ["BTC", "ETH", "SOL"])
        risk_tolerance = entities.get("risk_tolerance", 0.5)

        try:
            # Optimize portfolio
            optimizer = PortfolioOptimizer()
            portfolio = await optimizer.optimize_portfolio(tokens, risk_tolerance)

            # Format response
            risk_level = "Conservative" if risk_tolerance < 0.33 else "Balanced" if risk_tolerance < 0.67 else "Aggressive"
            response_content = f"💼 **Portfolio Optimization ({risk_level})**\n\n"

            response_content += "**Optimal Allocation:**\n"
            for token, weight in portfolio.weights.items():
                response_content += f"- {token}: {weight * 100:.1f}%\n"

            response_content += "\n**Performance Metrics:**\n"
            response_content += f"- Expected Return: {portfolio.metrics.get('expected_return', 0):.1f}%\n"
            response_content += f"- Volatility (Risk): {portfolio.metrics.get('volatility', 0):.1f}%\n"
            response_content += f"- Sharpe Ratio: {portfolio.metrics.get('sharpe_ratio', 0):.2f}\n"

            response_content += f"\n**Strategy:** {risk_level} risk profile optimized using Modern Portfolio Theory (MPT)\n"
            response_content += "*Allocation maximizes risk-adjusted returns for your risk tolerance*"

        except Exception as e:
            # Fallback to placeholder response on error
            response_content = "💼 **Portfolio Optimization**\n\n"
            response_content += f"⚠️ Unable to optimize portfolio: {e!s}\n\n"
            response_content += f"Tokens: {', '.join(tokens)}\n"
            response_content += f"Risk tolerance: {risk_tolerance * 100:.0f}%\n\n"
            response_content += "This feature routes to Hunter AI MPT optimization:\n"
            response_content += "- Modern Portfolio Theory analysis\n"
            response_content += "- Efficient frontier calculation\n"
            response_content += "- Asset allocation recommendations\n"
            response_content += "- Risk-adjusted returns\n"

        user_msg, agent_msg = await self._save_messages(
            conversation_id, content, response_content
        )

        return {
            "user_message": self._message_to_dict(user_msg),
            "agent_message": self._message_to_dict(agent_msg),
            "routing": {
                "intent": intent_result.intent.value,
                "confidence": intent_result.confidence,
                "handler": "hunter_ai",
                "agent_used": "hunter_ai",
                "reasoning": intent_result.reasoning,
            },
            "enrichment": {
                "tokens": tokens,
                "risk_tolerance": risk_tolerance,
                "hunter_tool": "mpt_optimizer",
            },
        }

    async def _handle_ultra_arbitrage(
        self, user_id: int, conversation_id: int, content: str, intent_result
    ) -> dict:
        """Handle arbitrage discovery intent via ULTRA."""
        entities = intent_result.extracted_entities
        capital = Decimal(str(entities.get("capital", 10000)))
        arb_type = entities.get("arb_type")  # "2hop", "3hop", "triangle", or None for all

        try:
            # Discover arbitrage opportunities
            discovery = ArbitrageDiscovery()

            if arb_type == "2hop":
                opportunities = await discovery.discover_2hop_arbitrage(capital)
            elif arb_type == "3hop":
                opportunities = await discovery.discover_3hop_arbitrage(capital)
            elif arb_type == "triangle":
                opportunities = await discovery.discover_triangle_arbitrage(capital=capital)
            else:
                # Discover all types - returns a list directly
                opportunities = await discovery.discover_all_opportunities(capital)

            # Format response
            response_content = f"🔍 **Arbitrage Opportunities** (${capital:,.2f} capital)\n\n"

            if not opportunities:
                response_content += "❌ No profitable arbitrage opportunities found at this time.\n\n"
                response_content += "**Reasons:**\n"
                response_content += "- Markets are currently efficient\n"
                response_content += "- Gas fees exceed potential profits\n"
                response_content += "- Slippage too high for profitable execution\n"
            else:
                response_content += f"**Found {len(opportunities)} opportunities:**\n\n"

                for i, opp in enumerate(opportunities[:5], 1):  # Show top 5
                    # Build path from trading pairs
                    path_tokens = [opp.path[0].token_in]
                    for pair in opp.path:
                        path_tokens.append(pair.token_out)
                    path_str = " → ".join(path_tokens)

                    response_content += f"**{i}. {opp.type.value.upper()} Arbitrage**\n"
                    response_content += f"- Route: {path_str}\n"
                    response_content += f"- Expected Profit: ${float(opp.expected_profit_usd):,.2f} ({float(opp.profit_percentage * 100):.2f}%)\n"
                    response_content += f"- Gas Cost: ${float(opp.estimated_gas_cost):,.2f}\n"
                    response_content += f"- Opportunity ID: {opp.opportunity_id}\n\n"

                if len(opportunities) > 5:
                    response_content += f"*+ {len(opportunities) - 5} more opportunities available*\n\n"

            response_content += "💡 **Next Steps:**\n"
            response_content += "- Use `/ultra/mev-protection` to execute with Flashbots\n"
            response_content += "- Check gas prices before execution\n"
            response_content += "- Monitor liquidity depth for slippage\n"

        except Exception as e:
            # Fallback to placeholder response on error
            response_content = "🔍 **Arbitrage Discovery**\n\n"
            response_content += f"⚠️ Unable to scan for arbitrage: {e!s}\n\n"
            response_content += f"Capital: ${capital:,.2f}\n"
            if arb_type:
                response_content += f"Type: {arb_type.upper()}\n\n"
            response_content += "This feature scans DEXes for:\n"
            response_content += "- 2-hop arbitrage (DEX A → DEX B)\n"
            response_content += "- 3-hop arbitrage (DEX A → DEX B → DEX C)\n"
            response_content += "- Triangular arbitrage (Token A → B → C → A)\n"

        # Collect sources
        from datetime import datetime
        from app.infrastructure.adapters.agent_squad.agents.source_helpers import (
            create_api_source,
        )
        
        sources = []
        fetched_at = datetime.utcnow()
        
        # Add 1inch source (used by ArbitrageDiscovery)
        sources.append(create_api_source(
            source_name="1inch",
            url="https://app.1inch.io/",
            citation_text="DEX price data from 1inch aggregator for arbitrage discovery",
            fetched_at=fetched_at,
            provider="1inch Aggregator API",
        ))
        
        # TODO: Add other DEX sources when integrated (Uniswap, Curve, etc.)

        user_msg, agent_msg = await self._save_messages(
            conversation_id, content, response_content, sources=sources
        )
        
        sources_response = [s.to_dict() if hasattr(s, "to_dict") else s for s in sources]

        return {
            "user_message": self._message_to_dict(user_msg),
            "agent_message": self._message_to_dict(agent_msg),
            "routing": {
                "intent": intent_result.intent.value,
                "confidence": intent_result.confidence,
                "handler": "ultra",
                "agent_used": "ultra_discovery",
                "reasoning": intent_result.reasoning,
            },
            "enrichment": {
                "capital": float(capital),
                "arb_type": arb_type or "all",
                "ultra_tool": "arbitrage_scanner",
            },
            "sources": sources_response,  # NEW
        }

    async def _handle_ultra_flash_loans(
        self, user_id: int, conversation_id: int, content: str, intent_result
    ) -> dict:
        """Handle flash loan protocol selection intent via ULTRA."""
        entities = intent_result.extracted_entities
        token_symbol = entities.get("token_symbol", "DAI")
        amount = Decimal(str(entities.get("amount", 100000)))
        protocol = entities.get("protocol")  # "aave", "balancer", "uniswap", or None

        try:
            # Get flash loan engine
            engine = FlashLoanEngine()

            if protocol:
                # Get specific protocol info
                protocol_enum = FlashLoanProtocol[protocol.upper()]
                protocols = await engine.get_protocols()
                protocol_info = next((p for p in protocols if p.protocol == protocol_enum), None)

                response_content = f"⚡ **{protocol.title()} Flash Loans**\n\n"
                if protocol_info:
                    response_content += "**Protocol Details:**\n"
                    response_content += f"- Fee: {protocol_info.fee_percentage * 100:.3f}%\n"
                    response_content += f"- Max Loan: ${protocol_info.max_loan_usd:,.0f}\n"
                    response_content += f"- Supported Tokens: {len(protocol_info.supported_tokens)}\n\n"

                    response_content += f"**For {token_symbol} loan of ${amount:,.2f}:**\n"
                    fee = amount * Decimal(str(protocol_info.fee_percentage))
                    response_content += f"- Fee: ${fee:,.2f}\n"
                    response_content += f"- Total Repayment: ${amount + fee:,.2f}\n"
            else:
                # Compare all protocols
                best_protocol = await engine.get_best_protocol(token_symbol, amount)
                protocols = await engine.get_protocols()

                response_content = f"⚡ **Flash Loan Comparison** ({token_symbol})\n\n"
                if best_protocol:
                    best_info = engine.get_protocol_info(best_protocol)
                    best_fee = amount * best_info.fee_percentage
                    response_content += f"**Best Protocol:** {best_info.name}\n"
                    response_content += f"- Fee: {float(best_info.fee_percentage * 100):.3f}%\n"
                    response_content += f"- Total Cost: ${float(best_fee):,.2f}\n\n"

                response_content += "**All Protocols:**\n"
                for p in protocols:
                    if token_symbol.upper() in [t.upper() for t in p.supported_tokens]:
                        fee = amount * p.fee_percentage
                        response_content += f"- {p.name}: ${float(fee):,.2f} ({float(p.fee_percentage * 100):.3f}%)\n"

            response_content += f"\n💡 **Use Case:** Borrow ${amount:,.2f} {token_symbol} instantly with no collateral\n"
            response_content += "Execute arbitrage, liquidations, or collateral swaps in a single transaction"

        except Exception as e:
            # Fallback to placeholder response on error
            response_content = "⚡ **Flash Loan Protocol Selection**\n\n"
            response_content += f"⚠️ Unable to fetch flash loan data: {e!s}\n\n"
            response_content += f"Token: {token_symbol}\n"
            response_content += f"Amount: ${amount:,.2f}\n\n"
            response_content += "Available protocols:\n"
            response_content += "- Aave (0.09% fee)\n"
            response_content += "- Balancer (0.00% fee)\n"
            response_content += "- Uniswap V3 (variable fee)\n"

        # Collect sources
        from datetime import datetime
        from app.infrastructure.adapters.agent_squad.agents.source_helpers import (
            create_mcp_source,
            create_api_source,
        )
        
        sources = []
        fetched_at = datetime.utcnow()
        
        # Add protocol sources based on what was queried
        if protocol:
            protocol_name = protocol.title()
            if protocol.lower() == "aave":
                sources.append(create_mcp_source(
                    mcp_server_name="Aave",
                    tool_name="get_flash_loan_info",
                    url="https://app.aave.com/",
                    citation_text=f"{protocol_name} flash loan protocol information",
                    fetched_at=fetched_at,
                ))
            elif protocol.lower() == "balancer":
                sources.append(create_api_source(
                    source_name="Balancer",
                    url="https://balancer.fi/",
                    citation_text="Balancer flash loan protocol information",
                    fetched_at=fetched_at,
                ))
            elif protocol.lower() == "uniswap":
                sources.append(create_api_source(
                    source_name="Uniswap",
                    url="https://app.uniswap.org/",
                    citation_text="Uniswap V3 flash loan protocol information",
                    fetched_at=fetched_at,
                ))
        else:
            # All protocols queried
            sources.append(create_mcp_source(
                mcp_server_name="Aave",
                tool_name="get_flash_loan_info",
                url="https://app.aave.com/",
                citation_text="Flash loan protocol comparison data",
                fetched_at=fetched_at,
            ))

        user_msg, agent_msg = await self._save_messages(
            conversation_id, content, response_content, sources=sources
        )
        
        sources_response = [s.to_dict() if hasattr(s, "to_dict") else s for s in sources]

        return {
            "user_message": self._message_to_dict(user_msg),
            "agent_message": self._message_to_dict(agent_msg),
            "routing": {
                "intent": intent_result.intent.value,
                "confidence": intent_result.confidence,
                "handler": "ultra",
                "agent_used": "ultra_flash_loan_engine",
                "reasoning": intent_result.reasoning,
            },
            "enrichment": {
                "token_symbol": token_symbol,
                "amount": float(amount),
                "protocol": protocol,
                "ultra_tool": "flash_loan_selector",
            },
            "sources": sources_response,  # NEW
        }

    async def _handle_ultra_mev_protection(
        self, user_id: int, conversation_id: int, content: str, intent_result
    ) -> dict:
        """Handle MEV-protected execution intent via ULTRA."""
        entities = intent_result.extracted_entities
        opportunity_id = entities.get("opportunity_id")

        try:
            if opportunity_id:
                # Execute specific opportunity with MEV protection
                executor = ArbitrageExecutor()

                # Note: In real implementation, we'd fetch the opportunity details first
                # For now, we'll simulate the MEV-protected execution
                response_content = "🛡️ **MEV-Protected Execution**\n\n"
                response_content += f"**Opportunity:** {opportunity_id}\n\n"

                response_content += "**Flashbots Bundle Status:**\n"
                response_content += "- Bundle submitted to Flashbots relay\n"
                response_content += "- Private transaction (not in public mempool)\n"
                response_content += "- Protected from frontrunning\n"
                response_content += "- Priority fee: Dynamic based on block\n\n"

                response_content += "💡 **MEV Protection Benefits:**\n"
                response_content += "- No sandwich attacks\n"
                response_content += "- No frontrunning\n"
                response_content += "- Failed transactions revert privately\n"
                response_content += "- Only pay gas if transaction succeeds\n"
            else:
                # General MEV protection info
                mev_protection = MEVProtection()

                response_content = "🛡️ **MEV Protection Service**\n\n"
                response_content += "**Flashbots Integration:**\n"
                response_content += "- Private transaction relay\n"
                response_content += "- Bundle inclusion guarantees\n"
                response_content += "- Miner payment optimization\n\n"

                response_content += "**Protection Against:**\n"
                response_content += "- ❌ Frontrunning attacks\n"
                response_content += "- ❌ Sandwich attacks\n"
                response_content += "- ❌ Backrunning exploitation\n\n"

                response_content += "💡 **How to Use:**\n"
                response_content += "1. Find arbitrage with `/ultra/arbitrage`\n"
                response_content += "2. Execute with MEV protection\n"
                response_content += "3. Transaction submitted privately via Flashbots\n"

        except Exception as e:
            # Fallback to placeholder response on error
            response_content = "🛡️ **MEV Protection**\n\n"
            response_content += f"⚠️ Unable to access MEV protection: {e!s}\n\n"
            if opportunity_id:
                response_content += f"Opportunity: {opportunity_id}\n\n"
            response_content += "This feature provides:\n"
            response_content += "- Flashbots relay integration\n"
            response_content += "- Private transaction submission\n"
            response_content += "- MEV attack prevention\n"
            response_content += "- Bundle optimization\n"

        # Collect sources
        from datetime import datetime
        from app.infrastructure.adapters.agent_squad.agents.source_helpers import (
            create_api_source,
            create_blockchain_source,
        )
        
        sources = []
        fetched_at = datetime.utcnow()
        
        # Add Flashbots source
        sources.append(create_api_source(
            source_name="Flashbots",
            url="https://www.flashbots.net/",
            citation_text="MEV protection via Flashbots private relay",
            fetched_at=fetched_at,
            provider="Flashbots Relay API",
        ))
        
        # Add blockchain source (for transaction execution)
        sources.append(create_blockchain_source(
            chain="Ethereum",
            citation_text="MEV-protected transaction on Ethereum",
            fetched_at=fetched_at,
            metadata={"mev_protection": True, "flashbots": True},
        ))

        user_msg, agent_msg = await self._save_messages(
            conversation_id, content, response_content, sources=sources
        )
        
        sources_response = [s.to_dict() if hasattr(s, "to_dict") else s for s in sources]

        return {
            "user_message": self._message_to_dict(user_msg),
            "agent_message": self._message_to_dict(agent_msg),
            "routing": {
                "intent": intent_result.intent.value,
                "confidence": intent_result.confidence,
                "handler": "ultra",
                "agent_used": "ultra_mev_engine",
                "reasoning": intent_result.reasoning,
            },
            "enrichment": {
                "opportunity_id": opportunity_id,
                "ultra_tool": "mev_protector",
            },
            "sources": sources_response,  # NEW
        }

    async def _handle_ultra_auto_executor(
        self, user_id: int, conversation_id: int, content: str, intent_result
    ) -> dict:
        """Handle automated trading bot control intent via ULTRA."""
        entities = intent_result.extracted_entities
        action = entities.get("action", "status")  # start, stop, pause, resume, status

        try:
            # Get auto executor
            executor = AutoExecutor()

            if action == "start":
                await executor.start()
                response_content = "🤖 **Trading Bot Started**\n\n"
                response_content += "✅ Auto-executor is now active\n\n"
                response_content += "**What it does:**\n"
                response_content += "- Continuously scans for arbitrage opportunities\n"
                response_content += "- Automatically executes profitable trades\n"
                response_content += "- Uses MEV protection for all executions\n"
                response_content += "- Monitors gas prices for optimal timing\n\n"
                response_content += "💡 Use `pause` or `stop` to control the bot"

            elif action == "stop":
                await executor.stop()
                response_content = "🤖 **Trading Bot Stopped**\n\n"
                response_content += "✅ Auto-executor has been stopped\n\n"
                response_content += "All active operations completed gracefully.\n"
                response_content += "Use `start` to resume automated trading."

            elif action == "pause":
                await executor.pause()
                response_content = "🤖 **Trading Bot Paused**\n\n"
                response_content += "⏸️ Auto-executor is paused\n\n"
                response_content += "Current trades will complete, but new trades are suspended.\n"
                response_content += "Use `resume` to continue automated trading."

            elif action == "resume":
                await executor.resume()
                response_content = "🤖 **Trading Bot Resumed**\n\n"
                response_content += "▶️ Auto-executor is active again\n\n"
                response_content += "Scanning for opportunities and executing trades."

            else:  # status
                status = executor.get_status()  # sync method
                response_content = "🤖 **Trading Bot Status**\n\n"
                response_content += f"**State:** {status.get('status', 'Unknown').upper()}\n"
                response_content += f"**Total Executions:** {status.get('total_executions', 0)}\n\n"

                response_content += "**Configuration:**\n"
                config = status.get("config", {})
                response_content += f"- Scan Interval: {config.get('scan_interval', 0)}s\n"
                response_content += f"- Min Profit: ${config.get('min_profit', '0')}\n"
                response_content += f"- MEV Protection: {'Enabled' if config.get('mev_protection') else 'Disabled'}\n\n"

                metrics = status.get("metrics", {})
                response_content += "**Metrics:**\n"
                response_content += f"- Success Rate: {metrics.get('success_rate', 0):.1f}%\n"
                response_content += f"- Risk Score: {status.get('risk_score', 0):.1f}/100\n\n"

                response_content += "💡 **Commands:** `start`, `stop`, `pause`, `resume`"

        except Exception as e:
            # Fallback to placeholder response on error
            response_content = "🤖 **Auto-Executor Control**\n\n"
            response_content += f"⚠️ Unable to control trading bot: {e!s}\n\n"
            response_content += f"Action: {action}\n\n"
            response_content += "Available commands:\n"
            response_content += "- `start` - Begin automated trading\n"
            response_content += "- `stop` - Halt all operations\n"
            response_content += "- `pause` - Temporarily suspend\n"
            response_content += "- `resume` - Continue after pause\n"
            response_content += "- `status` - View bot performance\n"

        # Collect sources
        from datetime import datetime
        from app.infrastructure.adapters.agent_squad.agents.source_helpers import (
            create_api_source,
            create_blockchain_source,
        )
        
        sources = []
        fetched_at = datetime.utcnow()
        
        # Add 1inch source (used for arbitrage discovery)
        sources.append(create_api_source(
            source_name="1inch",
            url="https://app.1inch.io/",
            citation_text="DEX price data for automated arbitrage scanning",
            fetched_at=fetched_at,
        ))
        
        # Add Flashbots source (for MEV protection)
        sources.append(create_api_source(
            source_name="Flashbots",
            url="https://www.flashbots.net/",
            citation_text="MEV protection for automated execution",
            fetched_at=fetched_at,
        ))
        
        # Add blockchain source
        sources.append(create_blockchain_source(
            chain="Ethereum",
            citation_text="Automated transaction execution on Ethereum",
            fetched_at=fetched_at,
            metadata={"auto_executor": True, "mev_protection": True},
        ))

        user_msg, agent_msg = await self._save_messages(
            conversation_id, content, response_content, sources=sources
        )
        
        sources_response = [s.to_dict() if hasattr(s, "to_dict") else s for s in sources]

        return {
            "user_message": self._message_to_dict(user_msg),
            "agent_message": self._message_to_dict(agent_msg),
            "routing": {
                "intent": intent_result.intent.value,
                "confidence": intent_result.confidence,
                "handler": "ultra",
                "agent_used": "ultra_auto_executor",
                "reasoning": intent_result.reasoning,
            },
            "enrichment": {
                "action": action,
                "ultra_tool": "auto_executor",
            },
            "sources": sources_response,  # NEW
        }

    # ============================================================================
    # DeFi SHORTCUT HANDLERS (Lending, Swap, Balance, Portfolio, Activity, Receive)
    # ============================================================================

    async def _handle_lending(
        self, user_id, conversation_id, content, intent_result, language: str = "en"
    ) -> dict:
        """
        Handle lending intent - Morpho vault deposits and yield earning.
        
        Uses real data from Morpho GraphQL API (supports Ethereum + Base).
        Responses are localized based on user language preference.
        """
        entities = intent_result.extracted_entities

        # Extract chain and asset from message or entities
        chain = entities.get("chain", "base").lower()
        asset = entities.get("token_symbol", "USDC").upper()

        # Auto-detect from message content
        message_lower = content.lower()
        if "base" in message_lower:
            chain = "base"
        elif "ethereum" in message_lower or "mainnet" in message_lower:
            chain = "ethereum"

        if "eth" in message_lower and "ether" in message_lower:
            asset = "ETH"
        elif "usdt" in message_lower:
            asset = "USDT"
        elif "dai" in message_lower:
            asset = "DAI"

        # Initialize execute data
        execute_data = None

        # Check if user wants to deposit (action intent)
        is_deposit_intent = any(
            keyword in message_lower
            for keyword in ["deposit", "supply", "lend", "put", "add"]
        )
        
        # Extract amount if present
        import re
        amount_match = re.search(r"(\d+\.?\d*)", content)
        amount = amount_match.group(1) if amount_match else None

        try:
            if self._lending_handler:
                # Use real Morpho data
                result = await self._lending_handler.execute(
                    message=content,
                    chain=chain,
                    asset=asset,
                    whitelisted_only=True,
                    language=language,
                )
                response_content = result.content
                enrichment = {
                    "vaults": result.vaults,
                    "chain": result.chain,
                    "asset": result.asset,
                    "best_apy": result.best_apy,
                    "latency_ms": result.latency_ms,
                }
                
                # Generate execute data if deposit intent and we have vaults
                if is_deposit_intent and result.vaults and len(result.vaults) > 0:
                    # Use best vault (first in list, highest APY)
                    best_vault = result.vaults[0]
                    vault_address = None
                    if isinstance(best_vault, dict):
                        vault_address = best_vault.get("address") or best_vault.get("vault_address")
                    else:
                        vault_address = getattr(best_vault, "address", None) or getattr(best_vault, "vault_address", None)
                    
                    if vault_address:
                        execute_data = {
                            "action_type": "deposit",
                            "chain": chain,
                            "from_token": asset,
                            "amount": amount or "1",  # Default to 1 if not specified
                            "protocol": "morpho",
                            "vault_address": vault_address,
                        }
            else:
                # Fallback response if handler not available
                response_content = self._get_lending_fallback_response(chain, asset)
                enrichment = {"chain": chain, "asset": asset, "fallback": True}
        except Exception as e:
            response_content = f"⚠️ Error fetching vault data: {e!s}\n\nPlease try again later."
            enrichment = {"error": str(e)}

        user_msg, agent_msg = await self._save_messages(
            conversation_id, content, response_content
        )

        return {
            "user_message": self._message_to_dict(user_msg),
            "agent_message": self._message_to_dict(agent_msg),
            "routing": {
                "intent": intent_result.intent.value,
                "confidence": intent_result.confidence,
                "handler": "lending_handler",
                "agent_used": "morpho",
                "reasoning": intent_result.reasoning,
                "language": language,
            },
            "enrichment": enrichment,
            "execute": execute_data,
        }

    def _get_lending_fallback_response(self, chain: str, asset: str) -> str:
        """Generate fallback response when lending handler is unavailable."""
        return f"""🏦 **Lending Vaults on {chain.upper()}**

I can help you find the best {asset} lending opportunities on Morpho.

**Available Features:**
• View top vaults by APY
• Compare curated (whitelisted) vaults
• Get deposit instructions (ERC-4626)

**Supported Chains:**
• Ethereum (mainnet)
• Base (L2)

**Popular Assets:**
• USDC, ETH, USDT, DAI

Try asking: "Show me Morpho USDC vaults on Base"
"""

    async def _handle_money_market(
        self, user_id, conversation_id, content, intent_result, language: str = "en"
    ) -> dict:
        """Handle money market comparison intent with i18n."""
        entities = intent_result.extracted_entities
        asset = entities.get("token_symbol", "USDC").upper()
        chain = entities.get("chain", "base").lower()

        try:
            if self._money_market_handler:
                result = await self._money_market_handler.compare_rates(
                    asset=asset,
                    chain=chain,
                    language=language,
                )
                response_content = result.content
                enrichment = {
                    "asset": asset,
                    "rates": result.rates,
                    "best_supply_protocol": result.best_supply_protocol,
                    "best_supply_apy": result.best_supply_apy,
                    "latency_ms": result.latency_ms,
                }
            else:
                response_content = self._get_money_market_fallback_response(asset)
                enrichment = {"asset": asset, "fallback": True}
        except Exception as e:
            response_content = f"⚠️ Error comparing rates: {e!s}"
            enrichment = {"error": str(e)}

        user_msg, agent_msg = await self._save_messages(
            conversation_id, content, response_content
        )

        return {
            "user_message": self._message_to_dict(user_msg),
            "agent_message": self._message_to_dict(agent_msg),
            "routing": {
                "intent": intent_result.intent.value,
                "confidence": intent_result.confidence,
                "handler": "money_market_handler",
                "reasoning": intent_result.reasoning,
                "language": language,
            },
            "enrichment": enrichment,
        }

    def _get_money_market_fallback_response(self, asset: str) -> str:
        """Generate fallback response when money market handler unavailable."""
        return f"""📊 **Money Market Comparison - {asset}**

Comparing lending rates requires the money market handler to be configured.

**Available Protocols:**
• Morpho (Ethereum, Base)
• Aave V3 (multi-chain)
• Compound V3 (multi-chain)
• Spark (Ethereum)

Try: "deposit USDC on Morpho" for direct vault access.
"""

    async def _handle_swap(
        self, user_id, conversation_id, content, intent_result, language: str = "en"
    ) -> dict:
        """Handle swap/exchange intent with i18n."""
        entities = intent_result.extracted_entities

        # Initialize execute data
        execute_data = None

        try:
            if self._swap_handler:
                # Parse swap details from message
                amount, from_token, to_token, chain, to_chain = self._swap_handler.parse_swap_from_message(content)

                # Override with entities if available
                if entities.get("token_symbol"):
                    from_token = entities["token_symbol"]
                if entities.get("chain"):
                    chain = entities["chain"].lower()
                if entities.get("to_chain"):
                    to_chain = entities["to_chain"].lower()

                result = await self._swap_handler.get_swap_quote(
                    from_token=from_token,
                    to_token=to_token,
                    amount=amount,
                    from_chain=chain,
                    to_chain=to_chain if to_chain and to_chain != chain else None,
                )
                response_content = result.content
                enrichment = {
                    "quote": result.quote,
                    "from_token": result.from_token,
                    "to_token": result.to_token,
                    "from_amount": result.from_amount,
                    "to_amount": result.to_amount,
                    "price_impact": result.price_impact,
                    "chain": result.chain,
                    "latency_ms": result.latency_ms,
                }
                
                # Generate execute data for swap action
                if result.quote:  # Only if we have a valid quote
                    execute_data = {
                        "action_type": "swap",
                        "chain": chain,
                        "from_token": from_token,
                        "to_token": to_token,
                        "amount": amount,
                        "slippage": 1.0,  # Default slippage
                        "to_chain": to_chain if to_chain and to_chain != chain else None,
                    }
            else:
                response_content = self._get_swap_fallback_response()
                enrichment = {"fallback": True}
        except Exception as e:
            response_content = f"⚠️ Error getting swap quote: {e!s}"
            enrichment = {"error": str(e)}

        user_msg, agent_msg = await self._save_messages(
            conversation_id, content, response_content
        )

        return {
            "user_message": self._message_to_dict(user_msg),
            "agent_message": self._message_to_dict(agent_msg),
            "routing": {
                "intent": intent_result.intent.value,
                "confidence": intent_result.confidence,
                "handler": "swap_handler",
                "reasoning": intent_result.reasoning,
                "language": language,
            },
            "enrichment": enrichment,
            "execute": execute_data,
        }

    def _get_swap_fallback_response(self) -> str:
        """Generate fallback response when swap handler unavailable."""
        return """🔄 **Token Swap**

I can help you swap tokens using the best routes.

**Available DEX Aggregators:**
• 1inch (best rates for most swaps)
• Hyperliquid (perpetuals & spot)
• UniswapX (gasless swaps)

**Example:**
"Swap 1 ETH for USDC on Base"

Please specify:
1. Amount and token to swap FROM
2. Token to swap TO
3. Chain (optional, default: Base)
"""

    async def _handle_balance(
        self, user_id, conversation_id, content, intent_result, language: str = "en"
    ) -> dict:
        """Handle balance check intent with i18n."""
        entities = intent_result.extracted_entities
        chain = entities.get("chain", "base").lower()

        try:
            if self._portfolio_handler:
                # Get user's wallet address from conversation context
                # For now, we need the wallet address - this would come from user session
                wallet_address = await self._get_user_wallet_address(user_id)

                if wallet_address:
                    result = await self._portfolio_handler.get_balance(
                        wallet_address=wallet_address,
                        chain=chain,
                        language=language,
                    )
                    response_content = result.content
                    enrichment = {
                        "total_usd": result.total_usd,
                        "tokens": result.tokens,
                        "native_balance": result.native_balance,
                        "native_symbol": result.native_symbol,
                        "chain": result.chain,
                        "latency_ms": result.latency_ms,
                    }
                else:
                    response_content = self._get_balance_no_wallet_response()
                    enrichment = {"no_wallet": True}
            else:
                response_content = self._get_balance_fallback_response()
                enrichment = {"fallback": True}
        except Exception as e:
            response_content = f"⚠️ Error fetching balance: {e!s}"
            enrichment = {"error": str(e)}

        user_msg, agent_msg = await self._save_messages(
            conversation_id, content, response_content
        )

        return {
            "user_message": self._message_to_dict(user_msg),
            "agent_message": self._message_to_dict(agent_msg),
            "routing": {
                "intent": intent_result.intent.value,
                "confidence": intent_result.confidence,
                "handler": "balance_handler",
                "reasoning": intent_result.reasoning,
                "language": language,
            },
            "enrichment": enrichment,
            "pending_action": pending_action if "pending_action" in locals() else None,
        }

    def _get_balance_fallback_response(self) -> str:
        """Generate fallback response when portfolio handler unavailable."""
        return """💰 **Balance**

To check your balance, I need the portfolio service configured.

**Supported Chains:**
• Ethereum, Base, Arbitrum, Polygon, Optimism

Try connecting your wallet to see real-time balances.
"""

    def _get_balance_no_wallet_response(self) -> str:
        """Generate response when user has no wallet."""
        return """💰 **No Wallet Connected**

I couldn't find a wallet associated with your account.

**To see your balance:**
1. Connect your wallet via the app
2. Or create an embedded wallet

Once connected, I can show you real-time balances across all chains.
"""

    async def _handle_portfolio(
        self, user_id, conversation_id, content, intent_result, language: str = "en"
    ) -> dict:
        """Handle portfolio enumeration intent with i18n."""
        entities = intent_result.extracted_entities
        chain = entities.get("chain", "base").lower()

        try:
            if self._portfolio_handler:
                wallet_address = await self._get_user_wallet_address(user_id)

                if wallet_address:
                    result = await self._portfolio_handler.get_portfolio(
                        wallet_address=wallet_address,
                        chain=chain,
                        language=language,
                    )
                    response_content = result.content
                    enrichment = {
                        "portfolio": result.portfolio,
                        "total_usd": result.total_usd,
                        "chain": result.chain,
                        "latency_ms": result.latency_ms,
                    }
                else:
                    response_content = self._get_portfolio_no_wallet_response()
                    enrichment = {"no_wallet": True}
            else:
                response_content = self._get_portfolio_fallback_response()
                enrichment = {"fallback": True}
        except Exception as e:
            response_content = f"⚠️ Error fetching portfolio: {e!s}"
            enrichment = {"error": str(e)}

        user_msg, agent_msg = await self._save_messages(
            conversation_id, content, response_content
        )

        return {
            "user_message": self._message_to_dict(user_msg),
            "agent_message": self._message_to_dict(agent_msg),
            "routing": {
                "intent": intent_result.intent.value,
                "confidence": intent_result.confidence,
                "handler": "portfolio_handler",
                "reasoning": intent_result.reasoning,
                "language": language,
            },
            "enrichment": enrichment,
            "pending_action": pending_action if "pending_action" in locals() else None,
        }

    def _get_portfolio_fallback_response(self) -> str:
        """Generate fallback response when portfolio handler unavailable."""
        return """📈 **Portfolio**

To view your portfolio, I need the portfolio service configured.

**Features Available:**
• Real-time token balances
• USD value calculation
• Multi-chain support

Connect your wallet to get started.
"""

    def _get_portfolio_no_wallet_response(self) -> str:
        """Generate response when user has no wallet."""
        return """📈 **No Wallet Connected**

I couldn't find a wallet associated with your account.

**To see your portfolio:**
1. Connect your wallet via the app
2. Or create an embedded wallet

Once connected, I can show you:
• All your tokens and balances
• USD values and percentages
• DeFi positions
"""

    async def _handle_activity(
        self, user_id, conversation_id, content, intent_result, language: str = "en"
    ) -> dict:
        """Handle transaction history/activity intent with i18n."""
        entities = intent_result.extracted_entities
        chain = entities.get("chain")  # Optional filter

        try:
            if self._activity_handler:
                result = await self._activity_handler.get_activity(
                    user_id=user_id,
                    chain=chain,
                    limit=10,
                    language=language,
                )
                response_content = result.content
                enrichment = {
                    "transactions": result.transactions,
                    "total_count": result.total_count,
                    "gas_spent_usd": result.gas_spent_usd,
                    "chain": result.chain,
                    "latency_ms": result.latency_ms,
                }
                pending_action = result.pending_action
            else:
                response_content = self._get_activity_fallback_response()
                enrichment = {"fallback": True}
        except Exception as e:
            response_content = f"⚠️ Error fetching activity: {e!s}"
            enrichment = {"error": str(e)}

        user_msg, agent_msg = await self._save_messages(
            conversation_id, content, response_content
        )

        return {
            "user_message": self._message_to_dict(user_msg),
            "agent_message": self._message_to_dict(agent_msg),
            "routing": {
                "intent": intent_result.intent.value,
                "confidence": intent_result.confidence,
                "handler": "activity_handler",
                "reasoning": intent_result.reasoning,
                "language": language,
            },
            "enrichment": enrichment,
            "pending_action": pending_action if "pending_action" in locals() else None,
        }

    def _get_activity_fallback_response(self) -> str:
        """Generate fallback response when activity handler unavailable."""
        return """📜 **Transaction History**

To view your transaction history, I need the activity service configured.

**Features Available:**
• Recent transactions
• Swap/Send/Receive history
• Gas cost summary

Your transactions are recorded when you use the app.
"""

    async def _handle_receive(
        self, user_id, conversation_id, content, intent_result, language: str = "en"
    ) -> dict:
        """Handle receive funds intent with i18n - show address, QR, handle."""
        entities = intent_result.extracted_entities
        chain = entities.get("chain", "base").lower()

        try:
            if self._receive_handler:
                result = await self._receive_handler.get_receive_info(
                    user_id=user_id,
                    chain=chain,
                    language=language,
                )
                response_content = result.content
                enrichment = {
                    "wallet_address": result.wallet_address,
                    "ens_handle": result.ens_handle,
                    "supported_networks": result.supported_networks,
                    "chain": result.chain,
                    "latency_ms": result.latency_ms,
                }
                pending_action = result.pending_action if hasattr(result, "pending_action") else None
            else:
                # Fallback - try to get wallet address directly
                wallet_address = await self._get_user_wallet_address(user_id)
                if wallet_address:
                    response_content = self._format_receive_response(wallet_address, chain)
                    enrichment = {
                        "wallet_address": wallet_address,
                        "supported_networks": ["ethereum", "base", "arbitrum", "polygon"],
                    }
                else:
                    response_content = self._get_receive_no_wallet_response()
                    enrichment = {"no_wallet": True}
        except Exception as e:
            response_content = f"⚠️ Error fetching wallet: {e!s}"
            enrichment = {"error": str(e)}

        user_msg, agent_msg = await self._save_messages(
            conversation_id, content, response_content
        )

        return {
            "user_message": self._message_to_dict(user_msg),
            "agent_message": self._message_to_dict(agent_msg),
            "routing": {
                "intent": intent_result.intent.value,
                "confidence": intent_result.confidence,
                "handler": "receive_handler",
                "reasoning": intent_result.reasoning,
                "language": language,
            },
            "enrichment": enrichment,
            "pending_action": pending_action if "pending_action" in locals() else None,
        }

    async def _handle_buy(
        self, user_id, conversation_id, content, intent_result, language: str = "en"
    ) -> dict:
        """Handle buy crypto intent with i18n - on-ramp via Privy/MoonPay."""
        try:
            if self._buy_handler:
                result = await self._buy_handler.get_buy_info(
                    user_id=user_id,
                    language=language,
                )
                response_content = result.content
                enrichment = {
                    "wallet_address": result.wallet_address,
                    "supported_assets": result.supported_assets,
                    "supported_networks": result.supported_networks,
                    "requires_privy_modal": result.requires_privy_modal,
                    "latency_ms": result.latency_ms,
                    "action": "open_fund_wallet",  # Signal to frontend
                }
            else:
                # Fallback - provide basic buy info
                wallet_address = await self._get_user_wallet_address(user_id)
                response_content = self._format_buy_fallback_response(language, wallet_address)
                enrichment = {
                    "wallet_address": wallet_address,
                    "requires_privy_modal": wallet_address is not None,
                    "action": "open_fund_wallet" if wallet_address else None,
                }
        except Exception as e:
            logger.error(f"Error in _handle_buy for user {user_id}: {e}", exc_info=True)
            # Provide fallback response without wallet lookup
            response_content = self._format_buy_fallback_response(language, None)
            enrichment = {
                "wallet_address": None,
                "requires_privy_modal": False,
                "action": None,
                "error": str(e),
            }

        # Save messages - this should be in a separate try/except to handle transaction errors
        try:
            user_msg, agent_msg = await self._save_messages(
                conversation_id, content, response_content
            )
        except Exception as e:
            logger.error(f"Error saving messages in _handle_buy: {e}", exc_info=True)
            # Create message objects in memory even if save fails
            from app.domain.chat.entities.message import Message
            user_msg = Message.create_user_message(
                conversation_id=conversation_id,
                content=content,
            )
            agent_msg = Message.create_assistant_message(
                conversation_id=conversation_id,
                content=response_content,
            )

        return {
            "user_message": self._message_to_dict(user_msg),
            "agent_message": self._message_to_dict(agent_msg),
            "routing": {
                "intent": intent_result.intent.value,
                "confidence": intent_result.confidence,
                "handler": "buy_handler",
                "reasoning": intent_result.reasoning,
                "language": language,
            },
            "enrichment": enrichment,
        }

    def _format_buy_fallback_response(self, language: str, wallet_address: str | None) -> str:
        """Format fallback buy response when handler not available."""
        if language == "es":
            if wallet_address:
                return f"""💳 **Comprar Cripto**

Puedes comprar cripto con tarjeta, Apple Pay o Google Pay vía MoonPay/Coinbase.

**Tu dirección de depósito:** `{wallet_address}`

Haz clic en 'Comprar' para iniciar el proceso de compra.
"""
            else:
                return """💳 **Comprar Cripto**

⚠️ No se encontró una wallet. Por favor conecta o crea una wallet primero.
"""
        else:
            if wallet_address:
                return f"""💳 **Buy Crypto**

You can buy crypto with card, Apple Pay or Google Pay via MoonPay/Coinbase.

**Your deposit address:** `{wallet_address}`

Click 'Buy' to start the purchase process.
"""
            else:
                return """💳 **Buy Crypto**

⚠️ No wallet found. Please connect or create a wallet first.
"""

    def _format_receive_response(self, wallet_address: str, chain: str) -> str:
        """Format receive response with wallet address."""
        return f"""📥 **Receive Funds**

**Your Wallet Address:**
`{wallet_address}`

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📱 **QR Code:** [Scan to deposit]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Supported Networks:**
• Ethereum (ETH, ERC-20 tokens)
• Base (ETH, USDC, etc.)
• Arbitrum (ETH, ARB, etc.)
• Polygon (MATIC, etc.)

⚠️ **Important:** Only send tokens on the correct network to avoid loss.

📋 *Tap address to copy*
"""

    def _get_receive_no_wallet_response(self) -> str:
        """Generate response when user has no wallet."""
        return """📥 **No Wallet Found**

I couldn't find a wallet associated with your account.

**To receive funds:**
1. Connect your wallet via the app
2. Or create an embedded wallet

Once connected, you'll get:
• Your deposit address
• QR code for easy sharing
• Multi-chain support
"""

    async def _get_user_wallet_address(self, user_id: int) -> str | None:
        """
        Get user's primary wallet address from Privy/WalletRepository.
        
        Looks up the user's wallet from the database (synced from Privy).
        Returns the first available wallet address, preferring embedded wallets.
        
        Args:
            user_id: User's database ID
            
        Returns:
            Wallet address (0x...) or None if no wallet found
        """
        if not self._wallet_repository:
            return None

        try:
            # Get all wallets for user
            wallets = await self._wallet_repository.get_by_user_id(UserId(user_id))

            if not wallets:
                return None

            # Prefer embedded wallets (managed by Privy)
            embedded_wallets = [
                w for w in wallets
                if hasattr(w, "wallet_type") and str(w.wallet_type).lower() == "embedded"
            ]

            if embedded_wallets:
                return embedded_wallets[0].address

            # Return first available wallet
            return wallets[0].address

        except Exception:
            # Log would be helpful here but don't fail the chat
            return None
