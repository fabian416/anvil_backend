"""
Enhanced Intent Detector v2.

Multi-language intent detection with conversational context support.
"""

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any

from app.application.chat.services.conversation_memory import ConversationContext

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
    LENDING = "LENDING"
    MONEY_MARKET = "MONEY_MARKET"
    
    # Restricted (require registration)
    BALANCE = "BALANCE"
    PORTFOLIO = "PORTFOLIO"
    ACTIVITY = "ACTIVITY"
    RECEIVE = "RECEIVE"
    TRANSFER = "TRANSFER"
    
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
            "predict", "prediction", "forecast", "will go", "next week",
            "tomorrow", "price target", "where will", "future price",
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
        ],
        "es": [
            "portafolio", "mis posiciones", "mis inversiones",
            "mi portafolio", "ver portafolio",
        ],
        "pt": [
            "portfólio", "minhas posições", "meus investimentos",
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
            "is it safe", "how safe", "safe to use",
            "what are the risks", "risks of", "risk assessment",
        ],
        "es": [
            "es seguro", "es seguro usar", "qué tan seguro",
            "cuáles son los riesgos", "riesgos de",
        ],
        "pt": [
            "é seguro", "é seguro usar", "quais são os riscos",
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
            "trading signal", "buy signal", "sell signal",
            "should i buy", "should i sell", "entry point",
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
}

# Intents that require registration
RESTRICTED_INTENTS = {
    ChatIntentV2.BALANCE,
    ChatIntentV2.PORTFOLIO,
    ChatIntentV2.ACTIVITY,
    ChatIntentV2.RECEIVE,
    ChatIntentV2.TRANSFER,
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
            ChatIntentV2.LENDING: "lending_handler",
            ChatIntentV2.MONEY_MARKET: "money_market_handler",
            ChatIntentV2.BALANCE: "restricted_handler",
            ChatIntentV2.PORTFOLIO: "restricted_handler",
            ChatIntentV2.ACTIVITY: "restricted_handler",
            ChatIntentV2.RECEIVE: "restricted_handler",
            ChatIntentV2.TRANSFER: "restricted_handler",
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
        
        # 1. Check for pending flow continuation
        if context and context.pending_intent:
            continuation_result = self._handle_continuation(message, context)
            if continuation_result:
                return continuation_result
        
        # 2. Check for follow-up questions using context
        if context and context.has_context:
            follow_up_result = self._detect_follow_up(message_lower, context)
            if follow_up_result:
                return follow_up_result
        
        # 3. Check restricted intents first (security)
        restricted_result = self._detect_restricted(message_lower, language)
        if restricted_result:
            return restricted_result

        # 4. Check analysis intents first (price/sentiment/etc.)
        # Enterprise fix: prevents action keywords (e.g. "cambiar") from hijacking clear questions
        # like "¿Cuál es el precio de Bitcoin?"
        analysis_result = self._detect_analysis_intent(message_lower, language)
        if analysis_result:
            return analysis_result

        # 5. Check action intents (swap, lending, etc.)
        action_result = self._detect_action_intent(message_lower, language)
        if action_result:
            return action_result
        
        # 6. Check exploration intents (protocol search, risk, etc.)
        exploration_result = self._detect_exploration_intent(message_lower, language)
        if exploration_result:
            return exploration_result
        
        # 7. Fallback to general conversation
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
            # Check if message is a token or amount
            tokens = ["eth", "usdc", "usdt", "dai", "wbtc", "weth", "btc", "sol", "matic", "arb", "op"]
            
            # Token mentioned
            if any(token in message for token in tokens):
                return IntentResult(
                    intent=ChatIntentV2.SWAP,
                    confidence=0.90,
                    handler=self._handler_map[ChatIntentV2.SWAP],
                )
            
            # Amount pattern
            if re.match(r"^\d+\.?\d*$", message.strip()):
                return IntentResult(
                    intent=ChatIntentV2.SWAP,
                    confidence=0.90,
                    handler=self._handler_map[ChatIntentV2.SWAP],
                )
            
            # Partial patterns like "de USDC" or "a ETH"
            partial_patterns = [
                r"^(?:de|from|del)\s+\w+",
                r"^(?:a|to|hacia|por|for)\s+\w+",
            ]
            for pattern in partial_patterns:
                if re.match(pattern, message, re.IGNORECASE):
                    return IntentResult(
                        intent=ChatIntentV2.SWAP,
                        confidence=0.90,
                        handler=self._handler_map[ChatIntentV2.SWAP],
                    )
        
        return None
    
    def _detect_restricted(
        self,
        message: str,
        language: str,
    ) -> IntentResult | None:
        """Detect restricted action intents."""
        # Balance keywords
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
        
        # Activity patterns
        activity_patterns = [
            "my activity", "transaction history", "my transactions",
            "mi actividad", "historial de transacciones",
            "minha atividade", "histórico de transações",
        ]
        for pattern in activity_patterns:
            if pattern in message:
                return IntentResult(
                    intent=ChatIntentV2.ACTIVITY,
                    confidence=0.95,
                    handler=self._handler_map[ChatIntentV2.ACTIVITY],
                )
        
        # Receive address patterns
        receive_patterns = [
            "receive address", "my address", "deposit address", "wallet address",
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
        
        return None
    
    def _detect_action_intent(
        self,
        message: str,
        language: str,
    ) -> IntentResult | None:
        """Detect action intents (swap, lending, etc.)."""
        # Enterprise fix: do NOT route to SWAP purely on loose substring keywords.
        # Only route to SWAP if the message looks like:
        # - an explicit swap command (amount + from token + to token), OR
        # - an explicit swap initiation ("quiero swap", "hacer swap", etc.)
        # This reduces false positives on questions like "¿Cuál es el precio de Bitcoin?"
        import re

        token_pattern = r"(ETH|USDC|USDT|DAI|WBTC|WETH|BTC|SOL|MATIC|ARB|OP|LINK|UNI|AAVE|CRV|MKR)"
        amount_pattern = r"(\d+\.?\d*)"

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
                    intent=ChatIntentV2.SWAP,
                    confidence=0.90,
                    handler=self._handler_map[ChatIntentV2.SWAP],
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
                    intent=ChatIntentV2.SWAP,
                    confidence=0.85,
                    handler=self._handler_map[ChatIntentV2.SWAP],
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
            r"deposit.*in.*vault",
            r"supply\s+\d+\.?\d*\s*(usdc|eth|usdt|dai)",
            r"supply\s+to\s+aave",
            r"lend\s+my",
            r"earn\s+yield",
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
        
        return None
    
    def _detect_analysis_intent(
        self,
        message: str,
        language: str,
    ) -> IntentResult | None:
        """Detect analysis intents (sentiment, prediction, etc.)."""
        # Sentiment keywords
        sentiment_keywords = self._get_all_keywords("sentiment")
        for kw in sentiment_keywords:
            if kw in message:
                return IntentResult(
                    intent=ChatIntentV2.HUNTER_SENTIMENT,
                    confidence=0.85,
                    handler=self._handler_map[ChatIntentV2.HUNTER_SENTIMENT],
                )
        
        # Price/Prediction keywords
        price_keywords = self._get_all_keywords("price")
        prediction_keywords = self._get_all_keywords("prediction")
        all_price = price_keywords + prediction_keywords
        for kw in all_price:
            if kw in message:
                return IntentResult(
                    intent=ChatIntentV2.HUNTER_PRICE_PREDICTION,
                    confidence=0.85,
                    handler=self._handler_map[ChatIntentV2.HUNTER_PRICE_PREDICTION],
                )
        
        # Trading signals
        signal_keywords = self._get_all_keywords("trading_signals")
        for kw in signal_keywords:
            if kw in message:
                return IntentResult(
                    intent=ChatIntentV2.HUNTER_TRADING_SIGNALS,
                    confidence=0.85,
                    handler=self._handler_map[ChatIntentV2.HUNTER_TRADING_SIGNALS],
                )
        
        # Arbitrage
        arb_keywords = self._get_all_keywords("arbitrage")
        for kw in arb_keywords:
            if kw in message:
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
        
        # Similar protocols
        similar_patterns = [
            "similar to", "like", "alternative to", "alternatives for",
            "similar a", "parecido a", "alternativa a",
            "similar a", "parecido com", "alternativa para",
        ]
        for pattern in similar_patterns:
            if pattern in message:
                return IntentResult(
                    intent=ChatIntentV2.SIMILAR_PROTOCOLS,
                    confidence=0.85,
                    handler=self._handler_map[ChatIntentV2.SIMILAR_PROTOCOLS],
                )
        
        return None
    
    def _get_all_keywords(self, category: str) -> list[str]:
        """Get all keywords for a category across all languages."""
        all_keywords = []
        if category in INTENT_KEYWORDS:
            for lang_keywords in INTENT_KEYWORDS[category].values():
                all_keywords.extend(lang_keywords)
        return all_keywords

