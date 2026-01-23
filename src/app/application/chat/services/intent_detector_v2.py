"""
Enhanced Intent Detector v2.

Multi-language intent detection with conversational context support.
"""

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List

from app.application.chat.services.conversation_memory import ConversationContext
from app.application.chat.services.conversation_state_manager import ConversationStateManager

logger = logging.getLogger(__name__)


class ChatIntentV2(str, Enum):
    """Chat intent types."""
    
    # Hunter AI
    HUNTER_SENTIMENT = "HUNTER_SENTIMENT"
    HUNTER_PRICE_PREDICTION = "HUNTER_PRICE_PREDICTION"
    HUNTER_RISK_SIGNALS = "HUNTER_RISK_SIGNALS"
    HUNTER_TRADING_SIGNALS = "HUNTER_TRADING_SIGNALS"
    HUNTER_PATTERNS = "HUNTER_PATTERNS"
    HUNTER_PORTFOLIO = "HUNTER_PORTFOLIO"
    
    # ULTRA
    ULTRA_ARBITRAGE = "ULTRA_ARBITRAGE"
    ULTRA_FLASH_LOANS = "ULTRA_FLASH_LOANS"
    ULTRA_MEV_PROTECTION = "ULTRA_MEV_PROTECTION"
    ULTRA_AUTO_EXECUTOR = "ULTRA_AUTO_EXECUTOR"
    
    # GraphRAG
    PROTOCOL_SEARCH = "PROTOCOL_SEARCH"
    RISK_ASSESSMENT = "RISK_ASSESSMENT"
    SIMILAR_PROTOCOLS = "SIMILAR_PROTOCOLS"
    
    # DeFi Actions
    SWAP = "SWAP"
    SWAP_CONTINUE = "SWAP_CONTINUE"  # Multi-turn continuation
    MOONPAY_SWAP = "MOONPAY_SWAP"  # MoonPay swap flow
    MOONPAY_SWAP_CONTINUE = "MOONPAY_SWAP_CONTINUE"  # MoonPay swap multi-turn continuation
    LENDING = "LENDING"
    MONEY_MARKET = "MONEY_MARKET"
    BUY = "BUY"  # On-ramp crypto purchase
    BUY_CONTINUE = "BUY_CONTINUE"  # Multi-turn continuation for buy flow
    
    # Restricted (require registration)
    BALANCE = "BALANCE"
    PORTFOLIO = "PORTFOLIO"
    ACTIVITY = "ACTIVITY"
    RECEIVE = "RECEIVE"
    TRANSFER = "TRANSFER"
    SEND = "SEND"  # Send tokens to another wallet
    
    # General
    GENERAL_CONVERSATION = "GENERAL_CONVERSATION"


# Multi-language keywords by intent
INTENT_KEYWORDS: dict[str, dict[str, list[str]]] = {
    "sentiment": {
        "en": [
            "sentiment", "feeling", "mood", "bullish", "bearish", "opinion",
            "what do people think", "market mood", "community sentiment",
            "twitter", "reddit", "social", "news", "hype",
        ],
        "es": [
            "sentimiento", "opinión", "opiniones", "alcista", "bajista",
            "qué opina", "qué piensan", "clima del mercado", "percepción",
            "sentimiento de mercado", "sentimiento para",
        ],
        "pt": [
            "sentimento", "opinião", "humor", "altista", "baixista",
            "o que as pessoas pensam", "clima do mercado",
        ],
    },
    "price": {
        "en": [
            "price", "cost", "value", "worth", "how much is",
            "what's the price", "current price", "price of",
        ],
        "es": [
            "precio", "valor", "costo", "cuánto vale", "cuánto cuesta",
            "cuál es el precio", "precio de", "precio actual",
        ],
        "pt": [
            "preço", "valor", "custo", "quanto vale", "quanto custa",
        ],
    },
    "prediction": {
        "en": [
            "predict", "prediction", "forecast", "will go", "go up", "go down",
            "next week", "tomorrow", "price target", "where will", "future price",
            "will rise", "will fall", "will increase", "will decrease",
            "going up", "going down", "bullish", "bearish",
        ],
        "es": [
            "predecir", "predicción", "pronóstico", "mañana", "próxima semana",
            "objetivo de precio", "a dónde irá", "va a subir", "va a bajar",
        ],
        "pt": [
            "prever", "previsão", "amanhã", "próxima semana",
            "vai subir", "vai cair",
        ],
    },
    "token_info": {
        "en": [
            "what is bitcoin", "what is ethereum", "what is btc", "what is eth",
            "what is usdc", "what is usdt", "what is solana", "what is sol",
            "what is bnb", "what is cardano", "what is ada", "what is polygon",
            "what is matic", "what is avalanche", "what is avax", "what is chainlink",
            "what is link", "what is uniswap", "what is uni", "what is aave",
            "tell me about bitcoin", "tell me about ethereum", "tell me about",
            "what is defi", "what is nft", "what is dao", "what is stablecoin",
            "explain bitcoin", "explain ethereum", "explain defi",
            # Additional variations for better detection
            "bitcoin explained", "what does btc mean", "bitcoin definition",
            "what is crypto", "what is cryptocurrency", "what is blockchain",
            "bitcoin basics", "bitcoin for beginners", "learn about bitcoin",
            "ethereum explained", "what does eth mean", "ethereum definition",
            "tell me about btc", "explain btc", "what's bitcoin", "what's btc",
        ],
        "es": [
            "qué es bitcoin", "qué es ethereum", "qué es btc", "qué es eth",
            "qué es usdc", "qué es usdt", "qué es solana", "qué es defi",
            "cuéntame sobre bitcoin", "háblame de ethereum", "explica bitcoin",
            # Additional variations
            "qué es cripto", "qué es criptomoneda", "qué es blockchain",
            "bitcoin explicado", "qué significa btc", "definición de bitcoin",
            "cuéntame sobre btc", "explica btc", "qué es el bitcoin",
        ],
        "pt": [
            "o que é bitcoin", "o que é ethereum", "o que é btc", "o que é eth",
            "o que é usdc", "o que é usdt", "o que é solana", "o que é defi",
            "fale sobre bitcoin", "me conte sobre ethereum", "explique bitcoin",
            # Additional variations
            "o que é cripto", "o que é criptomoeda", "o que é blockchain",
            "bitcoin explicado", "o que significa btc", "definição de bitcoin",
            "fale sobre btc", "explique btc", "o que é o bitcoin",
        ],
        "zh": [
            "什么是比特币", "什么是以太坊", "什么是btc", "什么是eth",
            "告诉我关于比特币", "解释比特币",
        ],
    },
    "swap": {
        "en": [
            "swap", "exchange", "convert", "trade", "change",
            "swap from", "swap to", "exchange for",
        ],
        "es": [
            "swap", "cambiar", "intercambiar", "convertir", "canjear",
            "quiero swap", "hacer swap", "swap de",
        ],
        "pt": [
            "swap", "trocar", "converter", "cambiar",
            "quero swap", "fazer swap",
        ],
    },
    "balance": {
        "en": [
            "balance", "my wallet", "my funds", "how much do i have",
            "show balance", "check balance", "wallet balance",
        ],
        "es": [
            "saldo", "mi billetera", "mis fondos", "cuánto tengo",
            "mi saldo", "ver saldo", "mostrar saldo",
        ],
        "pt": [
            "saldo", "minha carteira", "meus fundos",
            "meu saldo", "ver saldo",
        ],
    },
    "portfolio": {
        "en": [
            "portfolio", "my positions", "my holdings", "my investments",
            "show portfolio", "portfolio performance",
            "my tokens", "what tokens", "list my tokens", "tokens i have",
            "tokens i own", "what do i own", "what do i have",
        ],
        "es": [
            "portafolio", "mis posiciones", "mis inversiones",
            "mi portafolio", "ver portafolio",
            "mis tokens", "qué tokens tengo", "listar mis tokens",
        ],
        "pt": [
            "portfólio", "minhas posições", "meus investimentos",
            "meus tokens", "quais tokens", "listar meus tokens",
            "meu portfólio", "ver portfólio",
        ],
    },
    "protocol_search": {
        "en": [
            "find protocol", "search protocol", "list protocols",
            "staking protocols", "best protocols", "top protocols",
            "protocols on ethereum", "lending protocols", "dex protocols",
        ],
        "es": [
            "buscar protocolo", "protocolos de staking", "listar protocolos",
            "mejores protocolos", "protocolos de préstamo",
        ],
        "pt": [
            "buscar protocolo", "protocolos de staking",
            "melhores protocolos", "listar protocolos",
        ],
    },
    "risk_assessment": {
        "en": [
            "is it safe", "how safe", "safe to use", "is safe", "safe?",
            "what are the risks", "risks of", "risk assessment",
            "is aave safe", "is uniswap safe", "is compound safe",
        ],
        "es": [
            "es seguro", "es seguro usar", "qué tan seguro",
            "cuáles son los riesgos", "riesgos de", "seguro?",
        ],
        "pt": [
            "é seguro", "é seguro usar", "quais são os riscos", "seguro?",
        ],
    },
    "arbitrage": {
        "en": [
            "arbitrage", "arb", "price difference", "spread",
            "profit opportunity", "cross dex",
        ],
        "es": [
            "arbitraje", "diferencia de precio", "oportunidad de ganancia",
        ],
        "pt": [
            "arbitragem", "diferença de preço", "oportunidade",
        ],
    },
    "flash_loans": {
        "en": [
            "flash loan", "flashloan", "flash borrow",
            "instant loan", "uncollateralized",
        ],
        "es": [
            "préstamo flash", "préstamo instantáneo", "sin colateral",
        ],
        "pt": [
            "empréstimo flash", "empréstimo instantâneo",
        ],
    },
    "trading_signals": {
        "en": [
            "trading signal", "trading signals", "buy signal", "sell signal",
            "should i buy", "should i sell", "entry point", "signals",
            "buy signals", "sell signals", "trade signals",
        ],
        "es": [
            "señal de trading", "señal de compra", "señal de venta",
            "debería comprar", "debería vender",
        ],
        "pt": [
            "sinal de trading", "sinal de compra", "sinal de venda",
            "devo comprar", "devo vender",
        ],
    },
    "buy": {
        "en": [
            "buy", "buy tokens", "buy token", "buy crypto", "buy bitcoin", "buy eth", "buy usdc",
            "buy with card", "purchase crypto", "i want to buy crypto",
            "i want to buy", "buy cryptocurrency", "on-ramp",
            "fund wallet", "add funds", "deposit fiat", "purchase tokens",
        ],
        "es": [
            "comprar", "comprar tokens", "comprar token", "comprar cripto", "comprar bitcoin", "comprar eth", "comprar usdc",
            "comprar con tarjeta", "quiero comprar cripto", "quiero comprar",
            "comprar criptomoneda", "fondear wallet", "agregar fondos",
        ],
        "pt": [
            "comprar", "comprar tokens", "comprar token", "comprar cripto", "comprar bitcoin", "comprar eth", "comprar usdc",
            "comprar com cartão", "quero comprar cripto", "quero comprar",
            "comprar criptomoeda", "fundear carteira", "adicionar fundos",
        ],
        "zh": [
            "购买", "购买代币", "购买加密货币", "购买比特币", "购买以太坊", "购买USDC",
            "用卡购买", "我想购买加密货币", "我想购买",
        ],
    },
    "hunter_risk_signals": {
        "en": [
            "risk signal", "risk signals", "risk signals for", "show risks",
            "risk analysis", "security risk", "vulnerabilities", "threats",
            "risk score", "danger signals", "warning signs",
        ],
        "es": [
            "señal de riesgo", "señales de riesgo", "mostrar riesgos",
            "análisis de riesgo", "vulnerabilidades", "amenazas",
        ],
        "pt": [
            "sinal de risco", "sinais de risco", "mostrar riscos",
            "análise de risco", "vulnerabilidades", "ameaças",
        ],
    },
    "hunter_patterns": {
        "en": [
            "pattern", "patterns", "pattern recognition", "trading patterns",
            "market patterns", "behavior patterns", "pattern analysis",
            "detect patterns", "find patterns", "pattern for",
        ],
        "es": [
            "patrón", "patrones", "reconocimiento de patrones", "patrones de trading",
            "patrones de mercado", "análisis de patrones",
        ],
        "pt": [
            "padrão", "padrões", "reconhecimento de padrões", "padrões de trading",
            "padrões de mercado", "análise de padrões",
        ],
    },
    "ultra_mev": {
        "en": [
            "mev", "mev protection", "protect from mev", "prevent mev",
            "mev shield", "frontrunning protection", "sandwich attack",
            "maximal extractable value", "miner extractable value",
            "flashbots", "execute with flashbots", "use flashbots",
        ],
        "es": [
            "protección mev", "proteger de mev", "prevenir mev",
            "ataque sandwich", "valor extraíble máximo", "flashbots",
        ],
        "pt": [
            "proteção mev", "proteger de mev", "prevenir mev",
            "ataque sandwich", "valor extraível máximo", "flashbots",
        ],
    },
    "ultra_auto_executor": {
        "en": [
            "auto executor", "auto execute", "automatic execution",
            "auto trade", "automated trading", "execute automatically",
            "smart execution", "intelligent execution",
            "trading bot", "start trading bot", "bot", "trading algorithm",
        ],
        "es": [
            "ejecución automática", "ejecutar automáticamente", "trading automatizado",
            "ejecutar auto", "ejecución inteligente", "bot de trading",
        ],
        "pt": [
            "execução automática", "executar automaticamente", "trading automatizado",
            "executar auto", "execução inteligente", "bot de trading",
        ],
    },
    "graphrag_similar": {
        "en": [
            "similar protocol", "similar protocols", "protocols like",
            "alternatives to", "comparable protocols", "similar to",
            "other protocols like", "protocols similar to",
        ],
        "es": [
            "protocolo similar", "protocolos similares", "protocolos como",
            "alternativas a", "protocolos comparables",
        ],
        "pt": [
            "protocolo similar", "protocolos similares", "protocolos como",
            "alternativas a", "protocolos comparáveis",
        ],
    },
    "agent_squad_specialist": {
        "en": [
            "specialist", "specialist task", "agent squad", "specialized agent",
            "expert agent", "domain expert", "specialist agent",
            "yield strategy", "yield", "best yield", "defi yield",
        ],
        "es": [
            "especialista", "tarea especializada", "agente especializado",
            "agente experto", "escuadrón de agentes", "estrategia de rendimiento",
        ],
        "pt": [
            "especialista", "tarefa especializada", "agente especializado",
            "agente especialista", "esquadrão de agentes", "estratégia de rendimento",
        ],
    },
    "agent_squad_workflow": {
        "en": [
            "complex workflow", "multi-step", "coordinated tasks",
            "workflow automation", "multi agent", "agent coordination",
            "orchestrated workflow", "complex task",
            "portfolio strategy", "balanced portfolio", "create portfolio",
        ],
        "es": [
            "flujo complejo", "multi-paso", "tareas coordinadas",
            "automatización de flujo", "multi agente", "estrategia de portafolio",
        ],
        "pt": [
            "fluxo complexo", "multi-etapa", "tarefas coordenadas",
            "automação de fluxo", "multi agente", "estratégia de portfólio",
        ],
    },
    "lending": {
        "en": [
            "lending", "lend", "deposit", "earn yield", "supply", "provide liquidity",
            "lending rates", "deposit rates", "best apy", "earn on", "stake",
            "lending protocol", "deposit protocol", "where to lend",
        ],
        "es": [
            "préstamo", "prestar", "depositar", "ganar rendimiento", "proveer liquidez",
            "tasas de préstamo", "mejores apy", "ganar con", "protocolo de préstamo",
        ],
        "pt": [
            "empréstimo", "emprestar", "depositar", "ganhar rendimento", "prover liquidez",
            "taxas de empréstimo", "melhores apy", "ganhar com", "protocolo de empréstimo",
        ],
    },
}

# Intents that require registration
RESTRICTED_INTENTS = {
    ChatIntentV2.BALANCE,
    ChatIntentV2.PORTFOLIO,
    ChatIntentV2.ACTIVITY,
    ChatIntentV2.RECEIVE,
    ChatIntentV2.TRANSFER,
    ChatIntentV2.SEND,
}


@dataclass
class IntentResult:
    """Result of intent detection."""
    
    intent: ChatIntentV2
    confidence: float
    handler: str | None = None
    is_restricted: bool = False
    metadata: dict[str, Any] | None = None
    
    def __post_init__(self):
        self.is_restricted = self.intent in RESTRICTED_INTENTS


class IntentDetectorV2:
    """
    Enhanced intent detector with multi-language and context support.
    
    Features:
    - Multi-language keywords (EN, ES, PT)
    - Conversational context awareness
    - Multi-turn flow handling (e.g., swap continuation)
    - Follow-up question detection
    """
    
    def __init__(self):
        # Initialize conversation state manager for auto-clearing flows
        self.state_manager = ConversationStateManager()

        self._handler_map = {
            ChatIntentV2.HUNTER_SENTIMENT: "hunter_sentiment_handler",
            ChatIntentV2.HUNTER_PRICE_PREDICTION: "hunter_prediction_handler",
            ChatIntentV2.HUNTER_RISK_SIGNALS: "hunter_risk_handler",
            ChatIntentV2.HUNTER_TRADING_SIGNALS: "hunter_signals_handler",
            ChatIntentV2.HUNTER_PATTERNS: "hunter_patterns_handler",
            ChatIntentV2.HUNTER_PORTFOLIO: "hunter_portfolio_handler",
            ChatIntentV2.ULTRA_ARBITRAGE: "ultra_arbitrage_handler",
            ChatIntentV2.ULTRA_FLASH_LOANS: "ultra_flashloan_handler",
            ChatIntentV2.ULTRA_MEV_PROTECTION: "ultra_mev_handler",
            ChatIntentV2.ULTRA_AUTO_EXECUTOR: "ultra_executor_handler",
            ChatIntentV2.PROTOCOL_SEARCH: "graphrag_handler",
            ChatIntentV2.RISK_ASSESSMENT: "graphrag_handler",
            ChatIntentV2.SIMILAR_PROTOCOLS: "graphrag_handler",
            ChatIntentV2.SWAP: "swap_handler",
            ChatIntentV2.SWAP_CONTINUE: "swap_handler",
            ChatIntentV2.MOONPAY_SWAP: "moonpay_swap_flow_handler",
            ChatIntentV2.MOONPAY_SWAP_CONTINUE: "moonpay_swap_flow_handler",
            ChatIntentV2.LENDING: "lending_handler",
            ChatIntentV2.MONEY_MARKET: "money_market_handler",
            ChatIntentV2.BUY: "buy_handler",
            ChatIntentV2.BUY_CONTINUE: "buy_handler",
            ChatIntentV2.BALANCE: "restricted_handler",
            ChatIntentV2.PORTFOLIO: "restricted_handler",
            ChatIntentV2.ACTIVITY: "restricted_handler",
            ChatIntentV2.RECEIVE: "restricted_handler",
            ChatIntentV2.TRANSFER: "restricted_handler",
            ChatIntentV2.SEND: "send_handler",  # Send tokens handler
            ChatIntentV2.GENERAL_CONVERSATION: "general_handler",
        }
    
    def detect(
        self,
        message: str,
        language: str = "en",
        context: ConversationContext | None = None,
    ) -> IntentResult:
        """
        Detect intent from message with context awareness.
        
        Args:
            message: User message
            language: Language code (en, es, pt)
            context: Optional conversation context
            
        Returns:
            IntentResult with intent, confidence, and metadata
        """
        message_lower = message.lower().strip()
        
        # [BUY_DEBUG] Log incoming message and context
        logger.info(f"[BUY_DEBUG] detect() called with message: '{message}'")
        logger.info(f"[BUY_DEBUG] Language: {language}")
        if context:
            logger.info(f"[BUY_DEBUG] Context pending_intent: {context.pending_intent}")
            logger.info(f"[BUY_DEBUG] Context pending_buy_info: {context.pending_buy_info}")

        # 0. AUTO-CLEARING STATE MANAGEMENT (Preventive Layer)
        # Check if pending flow should be automatically cleared due to:
        # - Timeout (5 min inactivity)
        # - Consecutive off-topic messages (2+)
        # - Explicit cancellation keywords
        if context and context.pending_intent:
            should_clear, reason = self.state_manager.should_clear_pending_flow(
                context, message, language
            )

            if should_clear:
                logger.info(
                    f"🧹 Auto-clearing stale flow: {reason}",
                    extra={
                        "pending_intent": context.pending_intent,
                        "reason": reason,
                        "user_message": message[:100],
                    },
                )
                self.state_manager.clear_flow_state(context)
            else:
                # Track message relevance for off-topic counter
                self.state_manager.track_message_relevance(context, message)

        # 1. Check for swap confirmation (when swap is complete and waiting for execution)
        if context and context.pending_swap_info:
            swap_info = context.pending_swap_info
            if swap_info.get("is_complete"):
                # Check if user is confirming execution
                confirmation_keywords = [
                    "1", "confirm", "yes", "sí", "sim", "execute", "ejecutar", "executar",
                    "proceed", "proceder", "go", "vamos", "vamos lá", "best rate", "best rates",
                    "execute swap", "ejecutar swap", "proceed with swap"
                ]
                if any(keyword in message_lower for keyword in confirmation_keywords):
                    # User confirmed, return SWAP_CONTINUE with confirmation metadata
                    return IntentResult(
                        intent=ChatIntentV2.SWAP_CONTINUE,
                        confidence=0.95,
                        handler=self._handler_map[ChatIntentV2.SWAP_CONTINUE],
                        metadata={"step": "confirm_execution", "value": message},
                    )
        
        # 2. Check for pending flow continuation
        if context and context.pending_intent:
            continuation_result = self._handle_continuation(message, context)
            if continuation_result:
                return continuation_result
        
        # 3. Check for follow-up questions using context
        if context and context.has_context:
            follow_up_result = self._detect_follow_up(message_lower, context)
            if follow_up_result:
                return follow_up_result
        
        # 4. Check restricted intents first (security)
        restricted_result = self._detect_restricted(message_lower, language)
        if restricted_result:
            return restricted_result

        # 5. Check analysis intents first (price/sentiment/etc.)
        # Enterprise fix: prevents action keywords (e.g. "cambiar") from hijacking clear questions
        # like "¿Cuál es el precio de Bitcoin?"
        logger.info(f"[INTENT_DEBUG] Step 5: Checking analysis intents for: '{message_lower[:50]}'")
        analysis_result = self._detect_analysis_intent(message_lower, language)
        if analysis_result:
            logger.info(f"[INTENT_DEBUG] ✅ Analysis intent found: {analysis_result.intent.value}")
            return analysis_result
        logger.info(f"[INTENT_DEBUG] ❌ No analysis intent found, continuing to action intents")

        # 6. Check action intents (swap, lending, etc.)
        action_result = self._detect_action_intent(message_lower, language)
        if action_result:
            logger.info(f"[BUY_DEBUG] Action intent detected: {action_result.intent.value}, handler: {action_result.handler}")
            return action_result

        # 7. Check exploration intents (protocol search, risk, etc.)
        exploration_result = self._detect_exploration_intent(message_lower, language)
        if exploration_result:
            logger.info(f"[BUY_DEBUG] Exploration intent detected: {exploration_result.intent.value}")
            return exploration_result

        # 8. Fallback to general conversation
        logger.info("[BUY_DEBUG] Fallback to GENERAL_CONVERSATION")
        return IntentResult(
            intent=ChatIntentV2.GENERAL_CONVERSATION,
            confidence=0.5,
            handler=self._handler_map[ChatIntentV2.GENERAL_CONVERSATION],
        )
    
    def _handle_continuation(
        self,
        message: str,
        context: ConversationContext,
    ) -> IntentResult | None:
        """Handle continuation of pending flow (e.g., swap multi-turn)."""
        pending = context.pending_intent
        message_lower = message.lower().strip()
        
        # Check if the message indicates a completely different intent
        # If so, break out of the pending flow and return None to allow normal detection
        if self._is_new_intent(message_lower):
            logger.debug(f"Breaking out of pending flow '{pending}' for new intent in: {message}")
            return None
        
        # Swap flow continuations
        if pending == "swap_awaiting_from_token":
            return IntentResult(
                intent=ChatIntentV2.SWAP_CONTINUE,
                confidence=0.95,
                handler=self._handler_map[ChatIntentV2.SWAP_CONTINUE],
                metadata={"step": "from_token", "value": message},
            )
        
        if pending == "swap_awaiting_to_token":
            return IntentResult(
                intent=ChatIntentV2.SWAP_CONTINUE,
                confidence=0.95,
                handler=self._handler_map[ChatIntentV2.SWAP_CONTINUE],
                metadata={"step": "to_token", "value": message},
            )
        
        if pending == "swap_awaiting_amount":
            return IntentResult(
                intent=ChatIntentV2.SWAP_CONTINUE,
                confidence=0.95,
                handler=self._handler_map[ChatIntentV2.SWAP_CONTINUE],
                metadata={"step": "amount", "value": message},
            )

        # MoonPay Swap flow continuations
        if pending == "moonpay_swap_awaiting_from_token":
            return IntentResult(
                intent=ChatIntentV2.MOONPAY_SWAP_CONTINUE,
                confidence=0.95,
                handler=self._handler_map[ChatIntentV2.MOONPAY_SWAP_CONTINUE],
                metadata={"step": "from_token", "value": message},
            )

        if pending == "moonpay_swap_awaiting_to_token":
            return IntentResult(
                intent=ChatIntentV2.MOONPAY_SWAP_CONTINUE,
                confidence=0.95,
                handler=self._handler_map[ChatIntentV2.MOONPAY_SWAP_CONTINUE],
                metadata={"step": "to_token", "value": message},
            )

        if pending == "moonpay_swap_awaiting_amount":
            return IntentResult(
                intent=ChatIntentV2.MOONPAY_SWAP_CONTINUE,
                confidence=0.95,
                handler=self._handler_map[ChatIntentV2.MOONPAY_SWAP_CONTINUE],
                metadata={"step": "amount", "value": message},
            )

        # Buy flow continuations
        if pending == "buy_awaiting_amount":
            logger.info(f"[BUY_DEBUG] Detected buy_awaiting_amount continuation, returning BUY_CONTINUE")
            return IntentResult(
                intent=ChatIntentV2.BUY_CONTINUE,
                confidence=0.95,
                handler=self._handler_map[ChatIntentV2.BUY_CONTINUE],
                metadata={"step": "amount", "value": message},
            )

        if pending == "buy_awaiting_crypto":
            logger.info(f"[BUY_DEBUG] Detected buy_awaiting_crypto continuation, returning BUY_CONTINUE")
            return IntentResult(
                intent=ChatIntentV2.BUY_CONTINUE,
                confidence=0.95,
                handler=self._handler_map[ChatIntentV2.BUY_CONTINUE],
                metadata={"step": "crypto", "value": message},
            )

        # Lending flow continuations (standard multi-step flow)
        if pending == "lending_awaiting_asset":
            return IntentResult(
                intent=ChatIntentV2.LENDING,
                confidence=0.95,
                handler=self._handler_map[ChatIntentV2.LENDING],
                metadata={"step": "lending_awaiting_asset", "value": message},
            )

        if pending == "lending_awaiting_amount":
            return IntentResult(
                intent=ChatIntentV2.LENDING,
                confidence=0.95,
                handler=self._handler_map[ChatIntentV2.LENDING],
                metadata={"step": "lending_awaiting_amount", "value": message},
            )

        if pending == "lending_awaiting_confirmation":
            return IntentResult(
                intent=ChatIntentV2.LENDING,
                confidence=0.95,
                handler=self._handler_map[ChatIntentV2.LENDING],
                metadata={"step": "lending_awaiting_confirmation", "value": message},
            )

        # Lending flow continuations (when no vaults found)
        if pending == "lending_no_vaults":
            # Check if user selected a numbered option (1, 2, 3)
            import re
            number_match = re.search(r"^(\d+)", message_lower)
            if number_match:
                option_num = int(number_match.group(1))
                if option_num == 1:
                    # Try different asset
                    return IntentResult(
                        intent=ChatIntentV2.LENDING,
                        confidence=0.90,
                        handler=self._handler_map[ChatIntentV2.LENDING],
                        metadata={"step": "select_asset", "value": message},
                    )
                elif option_num == 2:
                    # Try different chain
                    return IntentResult(
                        intent=ChatIntentV2.LENDING,
                        confidence=0.90,
                        handler=self._handler_map[ChatIntentV2.LENDING],
                        metadata={"step": "select_chain", "value": message},
                    )
                elif option_num == 3:
                    # Check back later
                    return IntentResult(
                        intent=ChatIntentV2.LENDING,
                        confidence=0.90,
                        handler=self._handler_map[ChatIntentV2.LENDING],
                        metadata={"step": "check_later", "value": message},
                    )
            # If not a number, treat as regular lending query
            return IntentResult(
                intent=ChatIntentV2.LENDING,
                confidence=0.85,
                handler=self._handler_map[ChatIntentV2.LENDING],
            )
        
        # Lending awaiting asset selection
        if pending == "lending_awaiting_asset":
            return IntentResult(
                intent=ChatIntentV2.LENDING,
                confidence=0.95,
                handler=self._handler_map[ChatIntentV2.LENDING],
                metadata={"step": "lending_awaiting_asset", "value": message},
            )

        # Lending awaiting amount input
        if pending == "lending_awaiting_amount":
            return IntentResult(
                intent=ChatIntentV2.LENDING,
                confidence=0.95,
                handler=self._handler_map[ChatIntentV2.LENDING],
                metadata={"step": "lending_awaiting_amount", "value": message},
            )

        # Lending awaiting confirmation
        if pending == "lending_awaiting_confirmation":
            return IntentResult(
                intent=ChatIntentV2.LENDING,
                confidence=0.95,
                handler=self._handler_map[ChatIntentV2.LENDING],
                metadata={"step": "lending_awaiting_confirmation", "value": message},
            )

        # Lending awaiting chain selection
        if pending == "lending_awaiting_chain":
            return IntentResult(
                intent=ChatIntentV2.LENDING,
                confidence=0.95,
                handler=self._handler_map[ChatIntentV2.LENDING],
                metadata={"step": "lending_awaiting_chain", "value": message},
            )
        
        # Portfolio flow continuations (when no portfolio found)
        if pending == "portfolio_no_portfolio":
            import re
            number_match = re.search(r"^(\d+)", message_lower)
            if number_match:
                option_num = int(number_match.group(1))
                if option_num == 1:
                    # Try different chain
                    return IntentResult(
                        intent=ChatIntentV2.PORTFOLIO,
                        confidence=0.90,
                        handler=self._handler_map[ChatIntentV2.PORTFOLIO],
                        metadata={"step": "select_chain", "value": message},
                    )
                elif option_num == 2:
                    # Receive funds
                    return IntentResult(
                        intent=ChatIntentV2.RECEIVE,
                        confidence=0.90,
                        handler=self._handler_map[ChatIntentV2.RECEIVE],
                    )
                elif option_num == 3:
                    # Check back later
                    return IntentResult(
                        intent=ChatIntentV2.PORTFOLIO,
                        confidence=0.85,
                        handler=self._handler_map[ChatIntentV2.PORTFOLIO],
                        metadata={"step": "check_later", "value": message},
                    )
        
        # Activity flow continuations (when no activity found)
        if pending == "activity_no_activity":
            import re
            number_match = re.search(r"^(\d+)", message_lower)
            if number_match:
                option_num = int(number_match.group(1))
                if option_num == 1:
                    # Receive funds
                    return IntentResult(
                        intent=ChatIntentV2.RECEIVE,
                        confidence=0.90,
                        handler=self._handler_map[ChatIntentV2.RECEIVE],
                    )
                elif option_num == 2:
                    # Make a swap
                    return IntentResult(
                        intent=ChatIntentV2.SWAP,
                        confidence=0.90,
                        handler=self._handler_map[ChatIntentV2.SWAP],
                    )
                elif option_num == 3:
                    # Earn yield
                    return IntentResult(
                        intent=ChatIntentV2.LENDING,
                        confidence=0.90,
                        handler=self._handler_map[ChatIntentV2.LENDING],
                    )
        
        # Money market flow continuations (when no rates found)
        if pending == "money_market_no_rates":
            import re
            number_match = re.search(r"^(\d+)", message_lower)
            if number_match:
                option_num = int(number_match.group(1))
                if option_num == 1:
                    # Try different asset
                    return IntentResult(
                        intent=ChatIntentV2.MONEY_MARKET,
                        confidence=0.90,
                        handler=self._handler_map[ChatIntentV2.MONEY_MARKET],
                        metadata={"step": "select_asset", "value": message},
                    )
                elif option_num == 2:
                    # Try different chain
                    return IntentResult(
                        intent=ChatIntentV2.MONEY_MARKET,
                        confidence=0.90,
                        handler=self._handler_map[ChatIntentV2.MONEY_MARKET],
                        metadata={"step": "select_chain", "value": message},
                    )
                elif option_num == 3:
                    # Check back later
                    return IntentResult(
                        intent=ChatIntentV2.MONEY_MARKET,
                        confidence=0.85,
                        handler=self._handler_map[ChatIntentV2.MONEY_MARKET],
                        metadata={"step": "check_later", "value": message},
                    )
        
        return None
    
    def _is_new_intent(self, message: str) -> bool:
        """
        Check if message clearly indicates a new, different intent.
        
        This prevents pending swap flows from "contaminating" other intents.
        Returns True if the message looks like a new question/command rather
        than a continuation of the pending swap.
        """
        # Keywords that indicate a clear new intent (not a token/amount for swap)
        new_intent_patterns = [
            # Sentiment/Analysis questions (English)
            r"\b(sentiment|opinion|mood|bullish|bearish|feeling|hype)\b",
            r"\b(what do people think|market mood|community sentiment)\b",
            r"\b(twitter|reddit|social|news)\b",
            # Sentiment/Analysis (Spanish)
            r"\b(sentimiento|opinión|opiniones|alcista|bajista)\b",
            r"\b(qué opina|qué piensan|clima del mercado|percepción)\b",
            # Sentiment/Analysis (Portuguese)
            r"\b(sentimento|opinião|humor|altista|baixista)\b",
            r"\b(o que as pessoas pensam|clima do mercado)\b",
            # Price questions (English)
            r"\b(what.+price|how much|price of|current price)\b",
            r"\b(what's the price|what is the price|price for)\b",
            r"\b(how much is|what is .+ worth|value of)\b",
            # Price questions (Spanish)
            r"\b(cuánto vale|cuánto cuesta|cuál es el precio|precio de|precio actual)\b",
            # Price questions (Portuguese)
            r"\b(quanto vale|quanto custa|qual é o preço|preço de|preço atual)\b",
            # Prediction questions (English)
            r"\b(predict|prediction|forecast|will go|next week|tomorrow)\b",
            r"\b(price target|where will|future price|going to)\b",
            # Prediction questions (Spanish)
            r"\b(predecir|predicción|pronóstico|mañana|próxima semana)\b",
            r"\b(objetivo de precio|a dónde irá|va a subir|va a bajar)\b",
            # Prediction questions (Portuguese)
            r"\b(prever|previsão|amanhã|próxima semana|vai subir|vai cair)\b",
            # Portfolio/Balance (restricted) - English
            r"\b(my balance|my portfolio|my holdings|my wallet|my funds)\b",
            r"\b(show my|check my|how much do i have|what's in my)\b",
            # Portfolio/Balance (restricted) - Spanish
            r"\b(mi saldo|mi portafolio|mi billetera|mis fondos|cuánto tengo)\b",
            r"\b(ver mi|mostrar mi|revisar mi)\b",
            # Portfolio/Balance (restricted) - Portuguese
            r"\b(meu saldo|meu portfólio|minha carteira|meus fundos)\b",
            r"\b(ver meu|mostrar meu)\b",
            # Protocol search/Risk (English)
            r"\b(tell me about|what is|how does|about the|info on|search for)\b",
            r"\b(find protocol|search protocol|list protocols|best protocols)\b",
            r"\b(is it safe|how safe|safe to use|what are the risks|risks of)\b",
            # Protocol search/Risk (Spanish)
            r"\b(explícame|qué es|cómo funciona|dime sobre|información de)\b",
            r"\b(buscar protocolo|listar protocolos|mejores protocolos)\b",
            r"\b(es seguro|qué tan seguro|cuáles son los riesgos|riesgos de)\b",
            # Protocol search/Risk (Portuguese)
            r"\b(me fala sobre|o que é|como funciona|informação sobre)\b",
            r"\b(buscar protocolo|listar protocolos|melhores protocolos)\b",
            r"\b(é seguro|quão seguro|quais são os riscos|riscos de)\b",
            # Risk keyword standalone
            r"\b(risk|riesgo|risco)\b",
            # Trading signals (English)
            r"\b(trading signal|buy signal|sell signal|should i buy|should i sell)\b",
            r"\b(entry point|exit point)\b",
            # Trading signals (Spanish)
            r"\b(señal de trading|señal de compra|señal de venta)\b",
            r"\b(debería comprar|debería vender|punto de entrada)\b",
            # Trading signals (Portuguese)
            r"\b(sinal de trading|sinal de compra|sinal de venda)\b",
            r"\b(devo comprar|devo vender)\b",
            # Arbitrage/MEV/Flash loans (English)
            r"\b(arbitrage|arb|flash loan|flashloan|mev|front run)\b",
            # Arbitrage/MEV/Flash loans (Spanish)
            r"\b(arbitraje|préstamo flash|préstamo instantáneo)\b",
            # Arbitrage/MEV/Flash loans (Portuguese)
            r"\b(arbitragem|empréstimo flash)\b",
            # Other actions (English)
            r"\b(lend|borrow|stake|deposit|withdraw|supply)\b",
            # Other actions (Spanish)
            r"\b(prestar|pedir prestado|staking|depositar|retirar)\b",
            # Other actions (Portuguese)
            r"\b(emprestar|tomar emprestado|depositar|retirar)\b",
            # Question words with context (less strict - anywhere in message)
            r"\b(what is the|how is the|why is|when will|where can)\b",
            r"\b(qué es el|cómo es el|por qué|cuándo|dónde)\b",
            r"\b(o que é o|como é o|por que|quando|onde)\b",
            # Question words at start of message
            r"^(what|how|why|when|where|who|which|can you|could you|tell me)\b",
            r"^(qué|cómo|por qué|cuándo|dónde|quién|cuál|puedes|dime)\b",
            r"^(o que|como|por que|quando|onde|quem|qual|pode|me fala)\b",
        ]
        
        for pattern in new_intent_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                return True
        
        return False
    
    def _detect_follow_up(
        self,
        message: str,
        context: ConversationContext,
    ) -> IntentResult | None:
        """Detect follow-up questions that reference previous context."""
        # Follow-up patterns
        follow_up_patterns = [
            r"^and what about\s+",
            r"^what about\s+",
            r"^how about\s+",
            r"^and for\s+",
            r"^y qué hay de\s+",  # Spanish
            r"^qué tal\s+",  # Spanish
            r"^y para\s+",  # Spanish
            r"^e sobre\s+",  # Portuguese
        ]
        
        for pattern in follow_up_patterns:
            if re.match(pattern, message, re.IGNORECASE):
                # Check previous intent from context
                for msg in reversed(context.messages):
                    if msg.intent:
                        prev_intent = msg.intent
                        if "SENTIMENT" in prev_intent:
                            return IntentResult(
                                intent=ChatIntentV2.HUNTER_SENTIMENT,
                                confidence=0.85,
                                handler=self._handler_map[ChatIntentV2.HUNTER_SENTIMENT],
                            )
                        if "PREDICTION" in prev_intent or "PRICE" in prev_intent:
                            return IntentResult(
                                intent=ChatIntentV2.HUNTER_PRICE_PREDICTION,
                                confidence=0.85,
                                handler=self._handler_map[ChatIntentV2.HUNTER_PRICE_PREDICTION],
                            )
                        break
        
        # Check for partial swap commands in context
        context_text = context.summary.lower()
        swap_keywords = ["swap", "cambiar", "intercambiar", "exchange", "trocar"]

        if any(kw in context_text for kw in swap_keywords):
            # ⚠️ IMPORTANT: Check for off-topic intent keywords FIRST
            # If user is asking for information (not continuing swap), don't treat as swap
            off_topic_keywords = [
                "price", "precio", "preço", "价格",
                "what is", "qué es", "o que é", "什么是",
                "tell me", "cuéntame", "me fale", "告诉我",
                "explain", "explica", "explicar", "解释",
                "how does", "cómo funciona", "como funciona", "如何",
            ]

            # If message contains off-topic keywords, it's NOT a swap continuation
            if any(keyword in message for keyword in off_topic_keywords):
                return None  # Let it be detected as fresh intent (price prediction, etc.)

            # Check if message is a token or amount
            tokens = ["eth", "usdc", "usdt", "dai", "wbtc", "weth", "btc", "sol", "matic", "arb", "op"]

            # Token mentioned
            if any(token in message for token in tokens):
                return IntentResult(
                    intent=ChatIntentV2.MOONPAY_SWAP,
                    confidence=0.90,
                    handler=self._handler_map[ChatIntentV2.MOONPAY_SWAP],
                )

            # Amount pattern
            if re.match(r"^\d+\.?\d*$", message.strip()):
                return IntentResult(
                    intent=ChatIntentV2.MOONPAY_SWAP,
                    confidence=0.90,
                    handler=self._handler_map[ChatIntentV2.MOONPAY_SWAP],
                )

            # Partial patterns like "de USDC" or "a ETH"
            partial_patterns = [
                r"^(?:de|from|del)\s+\w+",
                r"^(?:a|to|hacia|por|for)\s+\w+",
            ]
            for pattern in partial_patterns:
                if re.match(pattern, message, re.IGNORECASE):
                    return IntentResult(
                        intent=ChatIntentV2.MOONPAY_SWAP,
                        confidence=0.90,
                        handler=self._handler_map[ChatIntentV2.MOONPAY_SWAP],
                    )
        
        return None
    
    def _detect_restricted(
        self,
        message: str,
        language: str,
    ) -> IntentResult | None:
        """Detect restricted action intents."""
        # Check specific patterns first before general keywords

        # Receive address patterns (check before balance - more specific)
        receive_patterns = [
            "receive", "receive address", "my address", "deposit address", "wallet address",
            "show address", "qr code", "qr", "código qr", "código qr",
            "dirección de recepción", "mi dirección",
            "endereço de recebimento", "meu endereço",
        ]
        for pattern in receive_patterns:
            if pattern in message:
                return IntentResult(
                    intent=ChatIntentV2.RECEIVE,
                    confidence=0.95,
                    handler=self._handler_map[ChatIntentV2.RECEIVE],
                )

        # Activity patterns (check before balance - more specific)
        activity_patterns = [
            "activity", "transaction history", "my transactions",
            "recent activity", "show activity", "wallet activity",
            "my trades", "what did i do", "what i did",  # Casual activity queries
            "mi actividad", "historial de transacciones", "mis operaciones",
            "qué hice", "lo que hice",
            "minha atividade", "histórico de transações", "minhas operações",
            "o que fiz", "o que eu fiz",
        ]
        for pattern in activity_patterns:
            if pattern in message:
                return IntentResult(
                    intent=ChatIntentV2.ACTIVITY,
                    confidence=0.95,
                    handler=self._handler_map[ChatIntentV2.ACTIVITY],
                )

        # Agent Squad: Portfolio strategy (check before general portfolio to avoid false match)
        # Use PORTFOLIO intent for portfolio strategy workflows (test expects "portfolio" keyword)
        workflow_keywords = self._get_all_keywords("agent_squad_workflow")
        for kw in workflow_keywords:
            if kw in message:
                return IntentResult(
                    intent=ChatIntentV2.PORTFOLIO,
                    confidence=0.95,
                    handler=self._handler_map[ChatIntentV2.PORTFOLIO],
                )

        # Balance keywords (after more specific checks)
        balance_keywords = self._get_all_keywords("balance")
        for kw in balance_keywords:
            if kw in message:
                return IntentResult(
                    intent=ChatIntentV2.BALANCE,
                    confidence=0.95,
                    handler=self._handler_map[ChatIntentV2.BALANCE],
                )

        # Portfolio keywords
        portfolio_keywords = self._get_all_keywords("portfolio")
        for kw in portfolio_keywords:
            if kw in message:
                return IntentResult(
                    intent=ChatIntentV2.PORTFOLIO,
                    confidence=0.95,
                    handler=self._handler_map[ChatIntentV2.PORTFOLIO],
                )

        return None
    
    def _detect_action_intent(
        self,
        message: str,
        language: str,
    ) -> IntentResult | None:
        """Detect action intents (swap, lending, etc.)."""
        # Priority checks for premium features to prevent false matches
        # Check these BEFORE generic action patterns

        # GraphRAG: Similar protocols (check before swap to avoid "Uniswap" -> "swap" false match)
        similar_keywords = self._get_all_keywords("graphrag_similar")
        for kw in similar_keywords:
            if kw in message:
                return IntentResult(
                    intent=ChatIntentV2.SIMILAR_PROTOCOLS,
                    confidence=0.85,
                    handler=self._handler_map[ChatIntentV2.SIMILAR_PROTOCOLS],
                )

        # Agent Squad: Specialist/Yield tasks (check before generic lending patterns)
        # Use LENDING intent for yield strategy queries (test expects "yield" or "lending" keyword)
        specialist_keywords = self._get_all_keywords("agent_squad_specialist")
        for kw in specialist_keywords:
            if kw in message:
                return IntentResult(
                    intent=ChatIntentV2.LENDING,
                    confidence=0.88,
                    handler=self._handler_map[ChatIntentV2.LENDING],
                )

        # Money Market: Rate comparison queries (MUST be checked BEFORE lending_keywords)
        # "Compare lending rates" should go to MONEY_MARKET, not LENDING
        import re
        money_market_rate_patterns = [
            r"\bcompare\s+(?:lending\s+)?rates?\b",
            r"\b(?:lending|borrow)\s+rates?\s+for\b",
            r"\b(best|top)\s+(?:lending|borrow)\s+rates?\b",
            r"\bcomparar\s+tasas\b",
            r"\bmejores\s+tasas\b",
            r"\bcomparar\s+taxas\b",
            r"\bmelhores\s+taxas\b",
        ]
        for pattern in money_market_rate_patterns:
            if re.search(pattern, message, flags=re.IGNORECASE):
                return IntentResult(
                    intent=ChatIntentV2.MONEY_MARKET,
                    confidence=0.92,  # Higher than lending_keywords (0.90)
                    handler=self._handler_map[ChatIntentV2.MONEY_MARKET],
                )

        # Lending: Check for lending/deposit keywords
        lending_keywords = self._get_all_keywords("lending")
        for kw in lending_keywords:
            if kw in message:
                return IntentResult(
                    intent=ChatIntentV2.LENDING,
                    confidence=0.90,
                    handler=self._handler_map[ChatIntentV2.LENDING],
                )

        # Enterprise fix: do NOT route to SWAP purely on loose substring keywords.
        # Only route to SWAP if the message looks like:
        # - an explicit swap command (amount + from token + to token), OR
        # - an explicit swap initiation ("quiero swap", "hacer swap", etc.)
        # This reduces false positives on questions like "¿Cuál es el precio de Bitcoin?"
        import re

        token_pattern = r"(ETH|USDC|USDT|DAI|WBTC|WETH|BTC|SOL|MATIC|ARB|OP|LINK|UNI|AAVE|CRV|MKR)"
        chain_pattern = r"(ethereum|base|arbitrum|optimism|polygon|avalanche|bsc|binance|solana|fantom|avax)"
        amount_pattern = r"(\d+\.?\d*)"

        # Best swap rate queries (check early, before other patterns)
        # Examples: "Best swap rate for ETH to USDC", "Mejor tasa para ETH a USDC"
        best_rate_patterns = [
            rf"\b(best|top|highest|mejor|melhor)\s+(?:swap\s+)?rate(?:s)?\s+(?:for|para|por)\s+{token_pattern}\s+(?:to|for|a|para)\s+{token_pattern}\b",
            rf"\b(best|top|highest|mejor|melhor)\s+(?:swap\s+)?rate(?:s)?\s+{token_pattern}\s+(?:to|for|a|para)\s+{token_pattern}\b",
            rf"\b(best|top|highest|mejor|melhor)\s+(?:swap\s+)?(?:rate|price)\s+(?:for|para|por)\s+{token_pattern}\s+(?:to|for|a|para)\s+{token_pattern}\b",
            rf"\b(?:find|show|get|buscar|mostrar|obtener)\s+(?:the\s+)?(?:best|top|highest|mejor|melhor)\s+(?:swap\s+)?rate(?:s)?\s+(?:for|para|por)?\s*{token_pattern}\s+(?:to|for|a|para)\s+{token_pattern}\b",
        ]
        
        for pattern in best_rate_patterns:
            if re.search(pattern, message, flags=re.IGNORECASE):
                return IntentResult(
                    intent=ChatIntentV2.MOONPAY_SWAP,
                    confidence=0.92,  # High confidence for rate queries
                    handler=self._handler_map[ChatIntentV2.MOONPAY_SWAP],
                )

        # Cross-chain swap/bridge patterns (check first, before simple swaps)
        # Examples: "Swap USDC from Ethereum to Base", "Bridge ETH from Base to Arbitrum"
        cross_chain_patterns = [
            # English: swap/bridge token from chain to chain
            rf"\b(swap|bridge|transfer|send)\b\s*{token_pattern}\s*(?:from|on)\s*{chain_pattern}\s*(?:to|on)\s*{chain_pattern}\b",
            # English: swap/bridge amount token from chain to chain
            rf"\b(swap|bridge|transfer|send)\b\s*{amount_pattern}\s*{token_pattern}\s*(?:from|on)\s*{chain_pattern}\s*(?:to|on)\s*{chain_pattern}\b",
            # Spanish: cambiar/enviar token desde cadena a cadena
            rf"\b(swap|cambiar|enviar|transferir|bridge)\b\s*{token_pattern}\s*(?:desde|de|en)\s*{chain_pattern}\s*(?:a|hacia|para|en)\s*{chain_pattern}\b",
            # Spanish: cambiar/enviar cantidad token desde cadena a cadena
            rf"\b(swap|cambiar|enviar|transferir|bridge)\b\s*{amount_pattern}\s*{token_pattern}\s*(?:desde|de|en)\s*{chain_pattern}\s*(?:a|hacia|para|en)\s*{chain_pattern}\b",
            # Portuguese: trocar/enviar token de cadeia para cadeia
            rf"\b(swap|trocar|enviar|transferir|bridge)\b\s*{token_pattern}\s*(?:de|desde|em)\s*{chain_pattern}\s*(?:para|a|em)\s*{chain_pattern}\b",
            # Portuguese: trocar/enviar quantidade token de cadeia para cadeia
            rf"\b(swap|trocar|enviar|transferir|bridge)\b\s*{amount_pattern}\s*{token_pattern}\s*(?:de|desde|em)\s*{chain_pattern}\s*(?:para|a|em)\s*{chain_pattern}\b",
        ]
        
        for pattern in cross_chain_patterns:
            if re.search(pattern, message, flags=re.IGNORECASE):
                return IntentResult(
                    intent=ChatIntentV2.MOONPAY_SWAP,
                    confidence=0.95,  # High confidence for cross-chain swaps
                    handler=self._handler_map[ChatIntentV2.MOONPAY_SWAP],
                )

        # Full/structured swap commands (single-shot)
        swap_command_patterns = [
            # English
            rf"\b(swap|exchange|convert)\b\s*{amount_pattern}\s*{token_pattern}\s*(?:to|for)\s*{token_pattern}\b",
            # Spanish
            rf"\b(swap|cambiar|intercambiar|convertir|canjear)\b\s*{amount_pattern}\s*{token_pattern}\s*(?:a|por|hacia|para)\s*{token_pattern}\b",
            # Portuguese
            rf"\b(swap|trocar|converter)\b\s*{amount_pattern}\s*{token_pattern}\s*(?:para|por)\s*{token_pattern}\b",
            # Amount-less but still explicit (useful for some users)
            rf"\b(swap|exchange|convert)\b\s*{token_pattern}\s*(?:to|for)\s*{token_pattern}\b",
        ]

        for pattern in swap_command_patterns:
            if re.search(pattern, message, flags=re.IGNORECASE):
                return IntentResult(
                    intent=ChatIntentV2.MOONPAY_SWAP,
                    confidence=0.90,
                    handler=self._handler_map[ChatIntentV2.MOONPAY_SWAP],
                )

        # Multi-turn swap initiation (intentionally incomplete)
        # Examples: "quiero hacer swap", "help me swap", "hacer swap", "swap"
        swap_initiation_patterns = [
            r"\b(quiero|hacer|haz|ayúdame|ayudame)\b.*\bswap\b",
            r"\b(help|help me)\b.*\b(swap|exchange|convert)\b",
            r"\b(fazer|quero)\b.*\bswap\b",
            r"^\s*swap\s*$",
        ]
        for pattern in swap_initiation_patterns:
            if re.search(pattern, message, flags=re.IGNORECASE):
                return IntentResult(
                    intent=ChatIntentV2.MOONPAY_SWAP,
                    confidence=0.85,
                    handler=self._handler_map[ChatIntentV2.MOONPAY_SWAP],
                )

        # Swap patterns with token mention (without full command structure)
        # Examples: "intercambiar USDC", "cambiar ETH", "swap bitcoin", "convertir usdt"
        # These should trigger the multi-turn MoonPay swap flow
        swap_with_token_patterns = [
            # Spanish: intercambiar/cambiar/convertir + token
            rf"\b(intercambiar|cambiar|convertir|canjear)\s+{token_pattern}\b",
            rf"\b(quiero|necesito)\s+(intercambiar|cambiar|convertir)\s+{token_pattern}\b",
            # English: swap/exchange/convert + token (single token, triggers multi-turn)
            rf"\b(swap|exchange|convert|trade)\s+{token_pattern}\b",
            rf"\b(i want to|want to|wanna)\s+(swap|exchange|convert)\s+{token_pattern}\b",
            # Portuguese: trocar/converter + token
            rf"\b(trocar|converter)\s+{token_pattern}\b",
            rf"\b(quero|preciso)\s+(trocar|converter)\s+{token_pattern}\b",
        ]
        for pattern in swap_with_token_patterns:
            if re.search(pattern, message, flags=re.IGNORECASE):
                return IntentResult(
                    intent=ChatIntentV2.MOONPAY_SWAP,
                    confidence=0.88,
                    handler=self._handler_map[ChatIntentV2.MOONPAY_SWAP],
                )

        # Generic swap keywords (lowest priority, catches "intercambiar", "swap", etc.)
        # These trigger multi-turn flow when user mentions swap action without details
        swap_generic_keywords = self._get_all_keywords("swap")
        for kw in swap_generic_keywords:
            if kw in message:
                return IntentResult(
                    intent=ChatIntentV2.MOONPAY_SWAP,
                    confidence=0.80,
                    handler=self._handler_map[ChatIntentV2.MOONPAY_SWAP],
                )
        
        # Money market patterns (Aave / Compound / Morpho comparisons & rate queries)
        # NOTE: This intent is handled by MoneyMarketHandler and MUST be checked BEFORE lending.
        # These patterns match rate comparisons and protocol comparisons.
        money_market_patterns = [
            # Explicit "money market" phrasing
            r"\bmoney\s+market\b",
            r"\bmercado\s+(?:monetario|de\s+dinero)\b",
            r"\bmercado\s+monetário\b",
            # Rate comparison queries (best rates, compare rates)
            r"\b(best|top|compare)\s+(?:borrow|lending|money\s+market)\s+rates?\b",
            r"\bcompare\s+(?:lending\s+)?rates?\b",
            r"\b(?:lending|borrow)\s+rates?\s+for\b",
            r"\bbest\s+rates?\s+for\s+(usdc|eth|usdt|dai|btc)\b",
            r"\bmejores\s+tasas\b",
            r"\bcomparar\s+tasas\b",
            r"\bmelhores\s+taxas\b",
            r"\bcomparar\s+taxas\b",
            # Protocol comparisons (Aave/Compound/Morpho)
            r"\bcompare\s+aave\b",
            r"\baave\s+vs\s+compound\b",
            r"\bcompound\s+vs\s+aave\b",
            r"\b(compare|comparar)\b.*\b(aave|compound)\b",
            r"\b(aave|compound|morpho)\b\s*(?:vs|versus|or)\s*\b(aave|compound|morpho)\b",
            # Where should I deposit (rate comparison intent)
            r"\bwhere\s+(?:should\s+i|to)\s+deposit\b",
            r"\bdonde\s+(?:debo|puedo)\s+depositar\b",
            r"\bonde\s+(?:devo|posso)\s+depositar\b",
        ]
        for pattern in money_market_patterns:
            if re.search(pattern, message, flags=re.IGNORECASE):
                return IntentResult(
                    intent=ChatIntentV2.MONEY_MARKET,
                    confidence=0.88,
                    handler=self._handler_map[ChatIntentV2.MONEY_MARKET],
                )
        
        # Send/Transfer patterns (send tokens to another wallet)
        # Must be checked before lending to catch "send USDC to..." properly
        send_patterns = [
            # English send patterns
            r"\bsend\s+(?:\d+\.?\d*\s*)?(usdc|eth|usdt|dai|btc|crypto|tokens?)\b",
            r"\bsend\s+(?:to|crypto|tokens?)\b",
            r"\btransfer\s+(?:\d+\.?\d*\s*)?(usdc|eth|usdt|dai|btc)\s+to\b",
            r"\btransfer\s+(?:to|crypto|tokens?)\b",
            r"\bi\s+want\s+to\s+send\b",
            # Spanish patterns
            r"\benviar\s+(?:\d+\.?\d*\s*)?(usdc|eth|usdt|dai|btc|crypto)\b",
            r"\benviar\s+(?:a|crypto|tokens?)\b",
            r"\btransferir\s+(?:\d+\.?\d*\s*)?(usdc|eth|usdt|dai|btc)\b",
            r"\bquiero\s+enviar\b",
            # Portuguese patterns
            r"\benviar\s+(?:\d+\.?\d*\s*)?(usdc|eth|usdt|dai|btc|crypto)\b",
            r"\btransferir\s+(?:\d+\.?\d*\s*)?(usdc|eth|usdt|dai|btc)\b",
            r"\bquero\s+enviar\b",
        ]
        for pattern in send_patterns:
            if re.search(pattern, message, flags=re.IGNORECASE):
                return IntentResult(
                    intent=ChatIntentV2.SEND,
                    confidence=0.88,
                    handler=self._handler_map[ChatIntentV2.SEND],
                )

        # Lending patterns (improved to handle amounts and variations)
        # Use regex patterns to allow numbers and intermediate words
        lending_patterns = [
            # Spanish patterns with amounts
            r"depositar\s+\d+\.?\d*\s*(usdc|eth|usdt|dai|wbtc|weth|btc)",
            r"depositar\s+(usdc|eth|usdt|dai|wbtc|weth|btc)",
            r"depositar.*vault.*morpho",
            r"depositar.*en.*vault",
            r"prestar\s+\d+\.?\d*\s*(usdc|eth|usdt|dai)",
            r"prestar\s+(usdc|eth|usdt|dai)",
            r"prestar\s+en",
            r"emprestar",
            # English patterns with amounts
            r"deposit\s+\d+\.?\d*\s*(usdc|eth|usdt|dai|wbtc|weth|btc)",
            r"deposit\s+(usdc|eth|usdt|dai|wbtc|weth|btc)",
            r"deposit.*vault.*morpho",
            r"deposit.*(?:into|in).*vault",
            r"supply\s+\d+\.?\d*\s*(usdc|eth|usdt|dai)",
            r"supply\s+to\s+(?:aave|morpho|compound)\b",
            r"lend\s+my",
            r"earn\s+yield\s+on",
            r"earn\s+on\s+morpho",
            # Portuguese patterns
            r"depositar\s+\d+\.?\d*\s*(usdc|eth|usdt|dai)",
            r"depositar\s+(usdc|eth|usdt|dai)",
            r"emprestar\s+\d+\.?\d*",
        ]
        for pattern in lending_patterns:
            if re.search(pattern, message, flags=re.IGNORECASE):
                return IntentResult(
                    intent=ChatIntentV2.LENDING,
                    confidence=0.85,
                    handler=self._handler_map[ChatIntentV2.LENDING],
                )
        
        # Buy crypto patterns (on-ramp purchase)
        buy_keywords = self._get_all_keywords("buy")
        for kw in buy_keywords:
            if kw in message:
                return IntentResult(
                    intent=ChatIntentV2.BUY,
                    confidence=0.90,
                    handler=self._handler_map[ChatIntentV2.BUY],
                )
        
        return None
    
    def _match_keyword_with_word_boundary(self, keyword: str, message: str) -> bool:
        """
        Match keyword with word boundary to prevent false positives.

        Examples:
        - "hype" matches "check the hype" ✓
        - "hype" does NOT match "hyperliquid" ✗
        - "liquid" matches "liquid staking" ✓
        - "liquid" does NOT match "hyperliquid" ✗
        """
        import re
        # Use word boundary \b to match complete words only
        pattern = r'\b' + re.escape(keyword) + r'\b'
        return bool(re.search(pattern, message, re.IGNORECASE))

    def _detect_analysis_intent(
        self,
        message: str,
        language: str,
    ) -> IntentResult | None:
        """Detect analysis intents (sentiment, prediction, etc.)."""
        # Token info queries (What is Bitcoin?, Tell me about Ethereum, etc.)
        # Check this FIRST to prevent false matches with price/prediction patterns
        token_info_keywords = self._get_all_keywords("token_info")
        for kw in token_info_keywords:
            if kw in message:
                return IntentResult(
                    intent=ChatIntentV2.PROTOCOL_SEARCH,
                    confidence=0.90,
                    handler=self._handler_map[ChatIntentV2.PROTOCOL_SEARCH],
                    metadata={"query_type": "token_info"},
                )

        # Sentiment keywords - use word boundary matching to prevent false positives
        sentiment_keywords = self._get_all_keywords("sentiment")
        for kw in sentiment_keywords:
            if self._match_keyword_with_word_boundary(kw, message):
                return IntentResult(
                    intent=ChatIntentV2.HUNTER_SENTIMENT,
                    confidence=0.85,
                    handler=self._handler_map[ChatIntentV2.HUNTER_SENTIMENT],
                )
        
        # Price/Prediction keywords - use word boundary matching
        price_keywords = self._get_all_keywords("price")
        prediction_keywords = self._get_all_keywords("prediction")
        all_price = price_keywords + prediction_keywords

        # DEBUG: Log price keyword detection
        logger.debug(f"[PRICE_DEBUG] Checking price keywords in message: '{message[:50]}'")
        logger.debug(f"[PRICE_DEBUG] Price keywords: {price_keywords}")

        for kw in all_price:
            # Price keywords often contain phrases like "price of", so keep substring matching
            if kw in message:
                logger.info(f"[PRICE_DEBUG] ✅ PRICE keyword matched: '{kw}' in message")
                return IntentResult(
                    intent=ChatIntentV2.HUNTER_PRICE_PREDICTION,
                    confidence=0.85,
                    handler=self._handler_map[ChatIntentV2.HUNTER_PRICE_PREDICTION],
                )

        logger.debug(f"[PRICE_DEBUG] ❌ No price keywords matched")

        # Trading signals - use word boundary matching
        signal_keywords = self._get_all_keywords("trading_signals")
        for kw in signal_keywords:
            if self._match_keyword_with_word_boundary(kw, message):
                return IntentResult(
                    intent=ChatIntentV2.HUNTER_TRADING_SIGNALS,
                    confidence=0.85,
                    handler=self._handler_map[ChatIntentV2.HUNTER_TRADING_SIGNALS],
                )

        # Hunter AI: Risk Signals - use word boundary matching
        risk_signal_keywords = self._get_all_keywords("hunter_risk_signals")
        for kw in risk_signal_keywords:
            if self._match_keyword_with_word_boundary(kw, message):
                return IntentResult(
                    intent=ChatIntentV2.HUNTER_RISK_SIGNALS,
                    confidence=0.85,
                    handler=self._handler_map[ChatIntentV2.HUNTER_RISK_SIGNALS],
                )

        # Hunter AI: Pattern Recognition - use word boundary matching
        pattern_keywords = self._get_all_keywords("hunter_patterns")
        for kw in pattern_keywords:
            if self._match_keyword_with_word_boundary(kw, message):
                return IntentResult(
                    intent=ChatIntentV2.HUNTER_PATTERNS,
                    confidence=0.85,
                    handler=self._handler_map[ChatIntentV2.HUNTER_PATTERNS],
                )

        # ULTRA: MEV Protection - use word boundary matching
        mev_keywords = self._get_all_keywords("ultra_mev")
        for kw in mev_keywords:
            if self._match_keyword_with_word_boundary(kw, message):
                return IntentResult(
                    intent=ChatIntentV2.ULTRA_MEV_PROTECTION,
                    confidence=0.85,
                    handler=self._handler_map[ChatIntentV2.ULTRA_MEV_PROTECTION],
                )

        # ULTRA: Auto Executor - use word boundary matching
        auto_exec_keywords = self._get_all_keywords("ultra_auto_executor")
        for kw in auto_exec_keywords:
            if self._match_keyword_with_word_boundary(kw, message):
                return IntentResult(
                    intent=ChatIntentV2.ULTRA_AUTO_EXECUTOR,
                    confidence=0.85,
                    handler=self._handler_map[ChatIntentV2.ULTRA_AUTO_EXECUTOR],
                )

        # Arbitrage - use word boundary matching
        arb_keywords = self._get_all_keywords("arbitrage")
        for kw in arb_keywords:
            if self._match_keyword_with_word_boundary(kw, message):
                return IntentResult(
                    intent=ChatIntentV2.ULTRA_ARBITRAGE,
                    confidence=0.80,
                    handler=self._handler_map[ChatIntentV2.ULTRA_ARBITRAGE],
                )
        
        # Flash loans
        flash_keywords = self._get_all_keywords("flash_loans")
        for kw in flash_keywords:
            if kw in message:
                return IntentResult(
                    intent=ChatIntentV2.ULTRA_FLASH_LOANS,
                    confidence=0.80,
                    handler=self._handler_map[ChatIntentV2.ULTRA_FLASH_LOANS],
                )
        
        return None
    
    def _detect_exploration_intent(
        self,
        message: str,
        language: str,
    ) -> IntentResult | None:
        """Detect exploration intents (protocol search, risk, etc.)."""
        # Protocol search
        protocol_keywords = self._get_all_keywords("protocol_search")
        for kw in protocol_keywords:
            if kw in message:
                return IntentResult(
                    intent=ChatIntentV2.PROTOCOL_SEARCH,
                    confidence=0.90,
                    handler=self._handler_map[ChatIntentV2.PROTOCOL_SEARCH],
                )
        
        # Risk assessment
        risk_keywords = self._get_all_keywords("risk_assessment")
        for kw in risk_keywords:
            if kw in message:
                return IntentResult(
                    intent=ChatIntentV2.RISK_ASSESSMENT,
                    confidence=0.90,
                    handler=self._handler_map[ChatIntentV2.RISK_ASSESSMENT],
                )
        
        # Note: GraphRAG similar protocols and Agent Squad checks
        # are now handled earlier in _detect_restricted and _detect_action_intent
        # to prevent false matches with more generic patterns

        return None
    
    def _get_all_keywords(self, category: str) -> list[str]:
        """Get all keywords for a category across all languages."""
        all_keywords = []
        if category in INTENT_KEYWORDS:
            for lang_keywords in INTENT_KEYWORDS[category].values():
                all_keywords.extend(lang_keywords)
        return all_keywords

    # ========================================================================
    # Multi-Intent Detection (Solution B)
    # ========================================================================

    def detect_multi_intent(
        self,
        message: str,
        language: str = "en",
        context: ConversationContext | None = None,
    ) -> "MultiIntentResult":
        """
        Detect multiple intents in a single user message.

        This method implements Solution B: Multi-Intent Detection Layer,
        enabling the system to handle messages like:
        - "show btc eth ada prices" → 3 PRICE intents (parallel)
        - "swap usdc to eth and show balance" → 2 intents with dependency (sequential)
        - "buy bitcoin if price drops below 90k" → 2 intents with condition

        Args:
            message: User message
            language: Language code (en, es, pt, zh)
            context: Optional conversation context

        Returns:
            MultiIntentResult with detected intents, orchestration strategy, and dependencies

        Example:
            >>> result = detector.detect_multi_intent("show btc eth prices")
            >>> result.intents  # [IntentResult(BTC), IntentResult(ETH)]
            >>> result.orchestration_strategy  # OrchestrationStrategy.PARALLEL
        """
        from app.domain.value_objects.chat.multi_intent_result import (
            MultiIntentResult,
            OrchestrationStrategy,
            IntentDependency,
        )
        from app.domain.value_objects.chat.intent_prediction import (
            IntentResult as DomainIntentResult,
        )

        message_lower = message.lower().strip()

        # Step 1: Extract entities (tokens, amounts, chains) from message
        entities_map = self._extract_entities_from_message(message_lower)

        # Step 2: Detect all intents (expand by entities where applicable)
        detected_intents = self._detect_all_intents(
            message_lower, language, entities_map, context
        )

        # Step 3: Convert application IntentResult to domain IntentResult
        domain_intents = []
        for app_intent in detected_intents:
            domain_intent = DomainIntentResult(
                intent=app_intent.intent,
                confidence=app_intent.confidence,
                entities=app_intent.metadata.get("entities", []) if app_intent.metadata else [],
                metadata=app_intent.metadata or {},
            )
            domain_intents.append(domain_intent)

        # Step 4: Detect dependencies between intents
        dependencies = self._detect_intent_dependencies(domain_intents, message_lower)

        # Step 5: Determine orchestration strategy
        orchestration_strategy = self._determine_orchestration_strategy(
            domain_intents, dependencies, message_lower
        )

        # Step 6: Create and return MultiIntentResult
        return MultiIntentResult(
            intents=domain_intents,
            orchestration_strategy=orchestration_strategy,
            dependencies=dependencies,
            metadata={
                "original_message": message,
                "language": language,
                "entities_map": entities_map,
            },
        )

    def _extract_entities_from_message(self, message: str) -> Dict[str, List[str]]:
        """
        Extract entities from message (tokens, amounts, chains).

        Args:
            message: Lowercased user message

        Returns:
            Dictionary with entity types and their values

        Example:
            >>> _extract_entities_from_message("show btc eth ada prices")
            {"tokens": ["btc", "eth", "ada"]}
        """
        import re

        entities = {
            "tokens": [],
            "amounts": [],
            "chains": [],
        }

        # Extract token symbols
        token_pattern = r"\b(btc|bitcoin|eth|ethereum|usdc|usdt|dai|wbtc|weth|sol|solana|matic|polygon|arb|arbitrum|op|optimism|ada|cardano|dot|polkadot|link|chainlink|uni|uniswap|aave|crv|curve|mkr|maker|comp|compound|avax|avalanche|bnb|binance)\b"
        tokens = re.findall(token_pattern, message, re.IGNORECASE)
        entities["tokens"] = list(dict.fromkeys(tokens))  # Remove duplicates, preserve order

        # Extract amounts (numbers)
        amount_pattern = r"\b\d+(?:\.\d+)?\b"
        amounts = re.findall(amount_pattern, message)
        entities["amounts"] = amounts

        # Extract chain names
        chain_pattern = r"\b(ethereum|base|arbitrum|optimism|polygon|avalanche|avax|bsc|binance|solana|fantom)\b"
        chains = re.findall(chain_pattern, message, re.IGNORECASE)
        entities["chains"] = list(dict.fromkeys(chains))

        return entities

    def _detect_all_intents(
        self,
        message: str,
        language: str,
        entities_map: Dict[str, List[str]],
        context: ConversationContext | None,
    ) -> List["IntentResult"]:
        """
        Detect all intents in the message, expanding by entities where applicable.

        For messages like "show btc eth ada prices", this will detect:
        - 3 separate PRICE intents (one per token)

        Args:
            message: Lowercased message
            language: Language code
            entities_map: Extracted entities
            context: Conversation context

        Returns:
            List of detected intents (application-layer IntentResult)
        """
        detected_intents = []

        # Check if message has multiple tokens + price/sentiment keywords
        # Example: "show btc eth prices" → 2 PRICE intents
        tokens = entities_map.get("tokens", [])

        # Price/sentiment multi-entity expansion
        price_keywords = ["price", "precio", "preço", "cost", "value", "worth"]
        sentiment_keywords = ["sentiment", "sentimiento", "sentimento", "mood", "feeling"]

        has_price_keyword = any(kw in message for kw in price_keywords)
        has_sentiment_keyword = any(kw in message for kw in sentiment_keywords)

        # Multi-entity price queries
        if has_price_keyword and len(tokens) > 1:
            for token in tokens:
                detected_intents.append(
                    IntentResult(
                        intent=ChatIntentV2.HUNTER_PRICE_PREDICTION,
                        confidence=0.90,
                        handler=self._handler_map[ChatIntentV2.HUNTER_PRICE_PREDICTION],
                        metadata={"entities": [token.upper()]},
                    )
                )
            return detected_intents

        # Multi-entity sentiment queries
        if has_sentiment_keyword and len(tokens) > 1:
            for token in tokens:
                detected_intents.append(
                    IntentResult(
                        intent=ChatIntentV2.HUNTER_SENTIMENT,
                        confidence=0.90,
                        handler=self._handler_map[ChatIntentV2.HUNTER_SENTIMENT],
                        metadata={"entities": [token.upper()]},
                    )
                )
            return detected_intents

        # Check for multi-step commands (e.g., "swap and balance")
        # Pattern: "action1 and action2"
        swap_keywords = ["swap", "cambiar", "intercambiar", "exchange", "trocar"]
        balance_keywords = ["balance", "saldo", "wallet"]

        has_swap = any(kw in message for kw in swap_keywords)
        has_balance = any(kw in message for kw in balance_keywords)

        if has_swap and has_balance and " and " in message or " y " in message or " e " in message:
            # Sequential: swap first, then balance
            detected_intents.append(
                IntentResult(
                    intent=ChatIntentV2.SWAP,
                    confidence=0.90,
                    handler=self._handler_map[ChatIntentV2.SWAP],
                    metadata={"entities": []},
                )
            )
            detected_intents.append(
                IntentResult(
                    intent=ChatIntentV2.BALANCE,
                    confidence=0.90,
                    handler=self._handler_map[ChatIntentV2.BALANCE],
                    metadata={"entities": []},
                )
            )
            return detected_intents

        # Fallback: single intent detection using existing detect() method
        single_intent = self.detect(message, language, context)

        # Populate entities from extracted tokens for single intent
        if tokens and single_intent.metadata:
            single_intent.metadata["entities"] = [tokens[0].upper()]
        elif tokens:
            single_intent.metadata = {"entities": [tokens[0].upper()]}

        detected_intents.append(single_intent)

        return detected_intents

    def _detect_intent_dependencies(
        self,
        intents: List["DomainIntentResult"],
        message: str,
    ) -> List["IntentDependency"]:
        """
        Detect dependencies between intents.

        Dependencies occur when:
        - Sequential keywords: "and then", "después", "depois"
        - Data flow: balance depends on swap completing
        - Conditional: "if price drops, then buy"

        Args:
            intents: List of detected domain intents
            message: Original message

        Returns:
            List of intent dependencies
        """
        from app.domain.value_objects.chat.multi_intent_result import IntentDependency

        dependencies = []

        # Single intent → no dependencies
        if len(intents) <= 1:
            return dependencies

        # Check for sequential keywords
        sequential_keywords = [
            " and then ", " y luego ", " e então ",
            " después ", " depois ", " then ",
        ]
        has_sequential = any(kw in message for kw in sequential_keywords)

        # Check for data flow dependencies
        # Example: SWAP → BALANCE (balance needs swap result)
        for i, intent in enumerate(intents):
            for j, prev_intent in enumerate(intents[:i]):
                # BALANCE depends on SWAP
                if intent.intent.value == "BALANCE" and prev_intent.intent.value == "SWAP":
                    dependencies.append(
                        IntentDependency(
                            dependent_index=i,
                            dependency_index=j,
                            dependency_type="data_flow",
                        )
                    )

                # General sequential dependency if keywords present
                elif has_sequential and i > j:
                    dependencies.append(
                        IntentDependency(
                            dependent_index=i,
                            dependency_index=j,
                            dependency_type="sequential",
                        )
                    )

        # Check for conditional dependencies
        conditional_keywords = [" if ", " si ", " se "]
        has_conditional = any(kw in message for kw in conditional_keywords)

        if has_conditional and len(intents) == 2:
            # Second intent depends on first (conditional)
            dependencies.append(
                IntentDependency(
                    dependent_index=1,
                    dependency_index=0,
                    dependency_type="conditional",
                )
            )

        return dependencies

    def _determine_orchestration_strategy(
        self,
        intents: List["DomainIntentResult"],
        dependencies: List["IntentDependency"],
        message: str,
    ) -> "OrchestrationStrategy":
        """
        Determine how intents should be orchestrated.

        Strategy selection:
        - PARALLEL: Independent intents (e.g., "show btc eth prices")
        - SEQUENTIAL: Dependent intents (e.g., "swap and balance")
        - CONDITIONAL: If-then logic (e.g., "buy if price drops")

        Args:
            intents: Detected intents
            dependencies: Intent dependencies
            message: Original message

        Returns:
            OrchestrationStrategy enum value
        """
        from app.domain.value_objects.chat.multi_intent_result import OrchestrationStrategy

        # Single intent → PARALLEL (no orchestration needed)
        if len(intents) <= 1:
            return OrchestrationStrategy.PARALLEL

        # Check for conditional keywords
        conditional_keywords = [" if ", " si ", " se "]
        has_conditional = any(kw in message for kw in conditional_keywords)

        if has_conditional:
            return OrchestrationStrategy.CONDITIONAL

        # Check if any dependencies exist
        if len(dependencies) > 0:
            # Check dependency types
            has_data_flow = any(dep.dependency_type == "data_flow" for dep in dependencies)
            has_conditional_dep = any(dep.dependency_type == "conditional" for dep in dependencies)

            if has_conditional_dep:
                return OrchestrationStrategy.CONDITIONAL
            elif has_data_flow:
                return OrchestrationStrategy.SEQUENTIAL
            else:
                return OrchestrationStrategy.SEQUENTIAL

        # No dependencies → PARALLEL execution
        return OrchestrationStrategy.PARALLEL

