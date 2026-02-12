"""
Swap Handler v2.

Multi-turn conversational swap handler with full flow support.

Uses Hyperliquid for real-time spot swap quotes.
"""

import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING

from app.application.chat.services.conversation_memory import ConversationContext

if TYPE_CHECKING:
    from app.infrastructure.adapters.external.hyperliquid_client import (
        HyperliquidClient,
    )
    from app.domain.chat.entities.user_context_aware import UserContextAware

logger = logging.getLogger(__name__)


# Supported tokens on Hyperliquid Spot (440+ tokens + USDC)
# NOTE: Some major L1 tokens (ETH, BTC, SOL) may not be on HL Spot
# Those are available on Hyperliquid Perps (perpetual futures)
SUPPORTED_TOKENS = [
    # Quote currency (required for all swaps)
    "USDC",
    # Popular tokens on Hyperliquid Spot (440+ available)
    "PURR",
    "HFUN",
    "TRUMP",
    "PEPE",
    "MOG",
    "POINTS",
    "JEFF",
    "GMEOW",
    "LICK",
    "MANLET",
    "SIX",
    "WAGMI",
    "CAPPY",
    "XULIAN",
    "RUG",
    "CZ",
    "BAGS",
    "ANSEM",
    "TATE",
    "FUN",
    "BIGBEN",
    "KOBE",
    "VEGAS",
    "PUMP",
    "SCHIZO",
    "CATNIP",
    "HAPPY",
    "SELL",
    "HBOOST",
    "GPT",
    "PANDA",
    "HODL",
    "RAGE",
    "ASI",
    "LEAP",
    "VAPOR",
    "X",
    "PILL",
    "CAT",
    "HPEPE",
    "MBAPPE",
    "MAGA",
    "OMNIX",
    "COKE",
    "MEOW",
    "ANT",
    "NEIRO",
]

# Major tokens NOT supported on Hyperliquid Spot (for error messaging)
MAJOR_TOKENS_NOT_SUPPORTED = [
    "ETH",
    "BTC",
    "SOL",
    "WBTC",
    "WETH",
    "LINK",
    "UNI",
    "AAVE",
    "CRV",
    "MKR",
    "DAI",
    "USDT",
    "MATIC",
    "ARB",
    "OP",
    "AVAX",
    "DOT",
    "ATOM",
    "APT",
    "SUI",
    "SEI",
    "TIA",
    "INJ",
    "FTM",
]


@dataclass
class SwapInfo:
    """Information for a swap operation."""

    from_token: str | None = None
    to_token: str | None = None
    amount: str | None = None
    from_chain: str | None = None  # Source chain for cross-chain swaps
    to_chain: str | None = None  # Destination chain for cross-chain swaps

    @property
    def is_complete(self) -> bool:
        """Check if we have all required info."""
        return bool(self.from_token and self.to_token and self.amount)

    @property
    def next_step(self) -> str | None:
        """Get the next step needed."""
        if not self.from_token:
            return "from_token"
        if not self.to_token:
            return "to_token"
        if not self.amount:
            return "amount"
        return None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "from_token": self.from_token,
            "to_token": self.to_token,
            "amount": self.amount,
            "from_chain": self.from_chain,
            "to_chain": self.to_chain,
            "is_complete": self.is_complete,
        }


@dataclass
class HandlerResult:
    """Result from a handler."""

    content: str
    pending_action: str | None = None
    requires_registration: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
    enrichment: dict[str, Any] | None = None
    execute_data: dict[str, Any] | None = (
        None  # Execute action data for /execute endpoint
    )


class SwapHandlerV2:
    """
    Multi-turn conversational swap handler powered by Hyperliquid Spot.

    Hyperliquid Spot has 440+ tokens paired with USDC.
    Some major L1 tokens (ETH, BTC, SOL) may not be on HL Spot — available via Perps.

    Supports:
    - Single message complete swaps: "swap 100 USDC to PURR"
    - Multi-turn flows: conversational swap building
    - Real-time Hyperliquid spot quotes (primary provider)

    Hyperliquid Spot Coverage (440+ Tokens):
    ✅ USDC (quote currency - required for all swaps)
    ✅ PURR, HFUN, TRUMP, PEPE, MOG, POINTS, JEFF, GMEOW
    ✅ 440+ tokens available on Hyperliquid Spot

    ⚠️ NOTE (Some Major L1 Tokens):
    ETH, BTC, SOL may not be on HL Spot.
    These are available on Hyperliquid Perps (perpetual futures).
    """

    # Tokens supported by Hyperliquid Spot (440+ tokens + USDC)
    # All pairs are XXX/USDC - USDC is the only quote currency
    HYPERLIQUID_SPOT_TOKENS = {
        "USDC",  # Quote currency (required for all swaps)
        # Popular tokens on Hyperliquid Spot (440+ available)
        "PURR",
        "HFUN",
        "TRUMP",
        "PEPE",
        "MOG",
        "POINTS",
        "JEFF",
        "GMEOW",
        "LICK",
        "MANLET",
        "SIX",
        "WAGMI",
        "CAPPY",
        "XULIAN",
        "RUG",
        "CZ",
        "BAGS",
        "ANSEM",
        "TATE",
        "FUN",
        "BIGBEN",
        "KOBE",
        "VEGAS",
        "PUMP",
        "SCHIZO",
        "CATNIP",
        "HAPPY",
        "SELL",
        "HBOOST",
        "GPT",
        "PANDA",
        "HODL",
        "RAGE",
        "ASI",
        "LEAP",
        "VAPOR",
        "X",
        "PILL",
        "CAT",
        "HPEPE",
        "MBAPPE",
        "MAGA",
        "OMNIX",
        "COKE",
        "MEOW",
        "ANT",
        "NEIRO",
    }

    # Major tokens that users commonly request but are NOT on Hyperliquid Spot
    MAJOR_TOKENS_NOT_SUPPORTED = {
        "ETH",
        "BTC",
        "SOL",
        "WBTC",
        "WETH",
        "LINK",
        "UNI",
        "AAVE",
        "CRV",
        "MKR",
        "DAI",
        "USDT",
        "MATIC",
        "ARB",
        "OP",
        "AVAX",
        "DOT",
        "ATOM",
        "APT",
        "SUI",
        "SEI",
        "TIA",
        "INJ",
        "FTM",
    }

    def __init__(self, hyperliquid_client: "HyperliquidClient | None" = None):
        """
        Initialize swap handler.

        Args:
            hyperliquid_client: Hyperliquid client for real-time spot quotes.
                               Required for swap functionality.
        """
        self._hyperliquid = hyperliquid_client

        # Popular tokens for quick selection (Hyperliquid Spot supported)
        self._popular_tokens = ["USDC", "PURR", "TRUMP", "PEPE", "HFUN", "MOG"]

        self._messages = {
            "ask_from_token": {
                "en": "🔄 I can help you swap tokens!\n\nWhat token do you want to swap **from**?\n\n{options}",
                "es": "🔄 ¡Puedo ayudarte a intercambiar tokens!\n\n¿**De qué** token quieres hacer swap?\n\n{options}",
                "pt": "🔄 Posso ajudá-lo a trocar tokens!\n\n**De qual** token você quer fazer swap?\n\n{options}",
            },
            "ask_to_token": {
                "en": "Got it! You want to swap **{from_token}**.\n\nWhat token do you want to receive?\n\n{options}",
                "es": "¡Entendido! Quieres cambiar **{from_token}**.\n\n¿Qué token quieres recibir?\n\n{options}",
                "pt": "Entendi! Você quer trocar **{from_token}**.\n\nQual token você quer receber?\n\n{options}",
            },
            "ask_amount": {
                "en": "Perfect! Swapping **{from_token}** → **{to_token}**\n\nHow much {from_token} do you want to swap?\n\n{options}",
                "es": "¡Perfecto! Intercambio **{from_token}** → **{to_token}**\n\n¿Cuántos {from_token} quieres cambiar?\n\n{options}",
                "pt": "Perfeito! Troca **{from_token}** → **{to_token}**\n\nQuantos {from_token} você quer trocar?\n\n{options}",
            },
            "quote": {
                "en": """💱 **Swap Quote**

**From:** {amount} {from_token}
**To:** ~{output_amount} {to_token}

**Rate:** 1 {from_token} = {rate} {to_token}
**Price Impact:** {price_impact}%
**Network:** {network}

Ready to execute? Type **1** to confirm and proceed with the swap.""",
                "es": """💱 **Cotización de Swap**

**De:** {amount} {from_token}
**A:** ~{output_amount} {to_token}

**Tasa:** 1 {from_token} = {rate} {to_token}
**Impacto en precio:** {price_impact}%
**Red:** {network}

¿Listo para ejecutar? Escribe **1** para confirmar y proceder con el swap.""",
                "pt": """💱 **Cotação de Swap**

**De:** {amount} {from_token}
**Para:** ~{output_amount} {to_token}

**Taxa:** 1 {from_token} = {rate} {to_token}
**Impacto no preço:** {price_impact}%
**Rede:** {network}

Pronto para executar? Digite **1** para confirmar e prosseguir com o swap.""",
            },
        }

        # Cache for Hyperliquid quotes (short TTL)
        self._quote_cache: dict[
            str, tuple[float, Any]
        ] = {}  # key -> (timestamp, quote)
        self._cache_ttl = 30  # 30 seconds

    async def handle(
        self,
        message: str,
        context: ConversationContext | None = None,
        language: str = "en",
        continuation_step: str | None = None,
        continuation_value: str | None = None,
        previous_swap_info: dict | None = None,
        user_context: "UserContextAware | None" = None,
    ) -> HandlerResult:
        """
        Handle swap request with multi-turn support.

        Args:
            message: User message
            context: Conversation context
            language: Language code
            continuation_step: If continuing a flow, which step
            continuation_value: Value for the continuation step
            previous_swap_info: Previous swap info for continuation
            user_context: User context-aware data (balance, portfolio state, etc.)

        Returns:
            HandlerResult with response and pending action
        """
        # Store user context for balance checking
        self._user_context = user_context
        # Check if user is confirming execution after seeing quote
        # If previous_swap_info exists and is complete, and user says "1" or "confirm", return the same quote with execute_data
        message_lower = message.lower().strip()
        if previous_swap_info and previous_swap_info.get("is_complete"):
            # Check if user is confirming (says "1", "confirm", "yes", "execute", etc.)
            confirmation_keywords = [
                "1",
                "confirm",
                "yes",
                "sí",
                "sim",
                "execute",
                "ejecutar",
                "executar",
                "proceed",
                "proceder",
            ]
            if any(keyword in message_lower for keyword in confirmation_keywords):
                # User confirmed, return the same quote with execute_data
                swap_info = SwapInfo(
                    from_token=previous_swap_info.get("from_token"),
                    to_token=previous_swap_info.get("to_token"),
                    amount=previous_swap_info.get("amount"),
                    from_chain=previous_swap_info.get("from_chain"),
                    to_chain=previous_swap_info.get("to_chain"),
                )
                # Return the quote again, but this time it will have execute_data
                return await self._generate_quote(swap_info, language)

        # Initialize swap_info from previous state if available
        if previous_swap_info:
            swap_info = SwapInfo(
                from_token=previous_swap_info.get("from_token"),
                to_token=previous_swap_info.get("to_token"),
                amount=previous_swap_info.get("amount"),
                from_chain=previous_swap_info.get("from_chain"),
                to_chain=previous_swap_info.get("to_chain"),
            )
        else:
            # Extract swap info from message and context
            swap_info = self._extract_swap_info(message, context)
            # Store message for rate query detection
            self._last_message = message

        # Handle continuation of pending flow
        if continuation_step:
            # Special handling for confirmation step
            if continuation_step == "confirm_execution":
                # User confirmed execution, return quote with execute_data
                if swap_info.from_token and swap_info.to_token and swap_info.amount:
                    return await self._generate_quote(swap_info, language)
                else:
                    # Missing info, ask for it
                    return await self._process_swap_flow(swap_info, language)
            else:
                # Regular continuation (from_token, to_token, amount)
                swap_info = self._apply_continuation(
                    swap_info,
                    continuation_step,
                    continuation_value or message,
                )

        # Determine next step
        return await self._process_swap_flow(swap_info, language)

    async def _process_swap_flow(
        self,
        swap_info: SwapInfo,
        language: str,
    ) -> HandlerResult:
        """Process swap flow based on current info."""

        # Ask for from_token
        if not swap_info.from_token:
            options = self._format_token_options(self._popular_tokens, language)
            return HandlerResult(
                content=self._get_message("ask_from_token", language).format(
                    options=options
                ),
                pending_action="swap_awaiting_from_token",
                metadata=swap_info.to_dict(),
            )

        # Ask for to_token
        if not swap_info.to_token:
            # Exclude from_token from options
            available_tokens = [
                t for t in self._popular_tokens if t != swap_info.from_token
            ]
            options = self._format_token_options(available_tokens, language)
            return HandlerResult(
                content=self._get_message("ask_to_token", language).format(
                    from_token=swap_info.from_token, options=options
                ),
                pending_action="swap_awaiting_to_token",
                metadata=swap_info.to_dict(),
            )

        # Ask for amount
        if not swap_info.amount:
            # For "best rate" queries, show rate info with default amount (1 token)
            # Check if message contains "rate" or "best" keywords
            message_lower = getattr(self, "_last_message", "").lower()
            if any(
                keyword in message_lower
                for keyword in ["rate", "best", "top", "highest", "mejor", "melhor"]
            ):
                # Use default amount of 1 for rate display
                swap_info.amount = "1"
                return await self._generate_quote(swap_info, language)

            # Regular flow: ask for amount
            options = self._format_amount_options(language)
            return HandlerResult(
                content=self._get_message("ask_amount", language).format(
                    from_token=swap_info.from_token,
                    to_token=swap_info.to_token,
                    options=options,
                ),
                pending_action="swap_awaiting_amount",
                metadata=swap_info.to_dict(),
            )

        # Generate quote
        return await self._generate_quote(swap_info, language)

    async def _generate_quote(
        self,
        swap_info: SwapInfo,
        language: str,
    ) -> HandlerResult:
        """
        Generate swap quote using Hyperliquid spot (ONLY provider).

        Hyperliquid provides:
        - Real-time order book-based quotes
        - Zero gas fees
        - High-speed execution (20,000+ TPS)
        - 0.02% trading fee
        """
        start_time = time.time()

        # Check if Hyperliquid client is available
        if not self._hyperliquid:
            error_messages = {
                "en": "⚠️ **Swap Unavailable**\n\nHyperliquid service is not configured. Please contact support.",
                "es": "⚠️ **Swap No Disponible**\n\nEl servicio de Hyperliquid no está configurado. Por favor contacta soporte.",
                "pt": "⚠️ **Swap Indisponível**\n\nO serviço Hyperliquid não está configurado. Por favor, entre em contato com o suporte.",
            }
            return HandlerResult(
                content=error_messages.get(language, error_messages["en"]),
                pending_action=None,
                requires_registration=False,
                metadata={"error": "hyperliquid_not_configured"},
            )

        # Check if tokens are supported - with special messaging for major tokens
        unsupported_from = swap_info.from_token not in self.HYPERLIQUID_SPOT_TOKENS
        unsupported_to = swap_info.to_token not in self.HYPERLIQUID_SPOT_TOKENS
        from_is_major = swap_info.from_token in self.MAJOR_TOKENS_NOT_SUPPORTED
        to_is_major = swap_info.to_token in self.MAJOR_TOKENS_NOT_SUPPORTED

        # Check if BOTH tokens are major tokens (common case like ETH to BTC)
        if unsupported_from and unsupported_to and from_is_major and to_is_major:
            error_messages = {
                "en": f"""⚠️ **{swap_info.from_token} → {swap_info.to_token} Swap Not Available**

**Both {swap_info.from_token} and {swap_info.to_token}** are not currently available on Hyperliquid Spot.

Hyperliquid Spot has **440+ tokens** paired with USDC.

**✅ Swaps you CAN do on Anvil:**
• Swap USDC to tokens: PURR, TRUMP, PEPE, HFUN, MOG, GMEOW, and 440+ more
• Swap tokens back to USDC
• Example: "swap 100 USDC to PURR" or "swap 500 PEPE to USDC"

**For {swap_info.from_token}/{swap_info.to_token} trading:**
• Use DEX aggregators like **1inch**, **Uniswap**, or **0x Protocol**
• Hyperliquid offers **perpetual futures** (perps) for major tokens

**What Anvil CAN do for {swap_info.from_token} & {swap_info.to_token}:**
• 📈 Check prices and market data
• 📊 Portfolio tracking
• 🔮 Price predictions via Hunter AI
• 📊 Sentiment analysis""",
                "es": f"""⚠️ **Swap {swap_info.from_token} → {swap_info.to_token} No Disponible**

**Tanto {swap_info.from_token} como {swap_info.to_token}** son tokens principales que **NO están disponibles en Hyperliquid Spot**.

Hyperliquid Spot tiene **440+ tokens** pareados con USDC.

**✅ Swaps que SÍ puedes hacer en Anvil:**
• Cambiar USDC a tokens: PURR, TRUMP, PEPE, HFUN, MOG, GMEOW, y 440+ más
• Cambiar tokens a USDC
• Ejemplo: "cambiar 100 USDC a PURR" o "cambiar 500 PEPE a USDC"

**Para trading de {swap_info.from_token}/{swap_info.to_token}:**
• Usa agregadores DEX como **1inch**, **Uniswap**, o **0x Protocol**
• Hyperliquid ofrece **futuros perpetuos** (perps) para tokens principales

**Lo que Anvil SÍ puede hacer con {swap_info.from_token} y {swap_info.to_token}:**
• 📈 Consultar precios y datos de mercado
• 📊 Seguimiento de portafolio
• 🔮 Predicciones de precio via Hunter AI
• 📊 Análisis de sentimiento""",
                "pt": f"""⚠️ **Swap {swap_info.from_token} → {swap_info.to_token} Não Disponível**

**Tanto {swap_info.from_token} quanto {swap_info.to_token}** são tokens principais que **NÃO estão disponíveis no Hyperliquid Spot**.

Hyperliquid Spot tem **440+ tokens** pareados com USDC.

**✅ Swaps que você PODE fazer no Anvil:**
• Trocar USDC por tokens: PURR, TRUMP, PEPE, HFUN, MOG, GMEOW, e 440+ mais
• Trocar tokens de volta para USDC
• Exemplo: "trocar 100 USDC para PURR" ou "trocar 500 PEPE para USDC"

**Para trading de {swap_info.from_token}/{swap_info.to_token}:**
• Use agregadores DEX como **1inch**, **Uniswap**, ou **0x Protocol**
• Hyperliquid oferece **futuros perpétuos** (perps) para tokens principais

**O que o Anvil PODE fazer com {swap_info.from_token} e {swap_info.to_token}:**
• 📈 Verificar preços e dados de mercado
• 📊 Rastreamento de portfólio
• 🔮 Previsões de preço via Hunter AI
• 📊 Análise de sentimento""",
            }
            return HandlerResult(
                content=error_messages.get(language, error_messages["en"]),
                pending_action=None,
                requires_registration=False,
                metadata={
                    "error": "major_tokens_not_supported",
                    "from_token": swap_info.from_token,
                    "to_token": swap_info.to_token,
                    "suggestion": "use_external_dex",
                },
            )

        # Check for single unsupported token
        unsupported_token = None
        is_major_token = False

        if unsupported_from:
            unsupported_token = swap_info.from_token
            is_major_token = from_is_major
        elif unsupported_to:
            unsupported_token = swap_info.to_token
            is_major_token = to_is_major

        if unsupported_token:
            if is_major_token:
                # Special message for major tokens (ETH, BTC, etc.)
                error_messages = {
                    "en": f"""⚠️ **{unsupported_token} Not Available for Spot Swap**

**{unsupported_token}** is a major token that is **NOT available on Hyperliquid Spot**.

Hyperliquid Spot has **440+ tokens** paired with USDC, but {unsupported_token} is not among them.

**For {unsupported_token} trading:**
• Hyperliquid offers **perpetual futures** (perps) for {unsupported_token}
• For spot swaps, use DEX aggregators like 1inch, Uniswap, or 0x

**Available on Anvil for {unsupported_token}:**
• 📈 Check price and market data
• 📊 Portfolio tracking
• 🔮 Price predictions via Hunter AI""",
                    "es": f"""⚠️ **{unsupported_token} No Disponible para Swap Spot**

**{unsupported_token}** no está disponible en Hyperliquid Spot actualmente.

Hyperliquid Spot tiene **440+ tokens** pareados con USDC, pero {unsupported_token} no está entre ellos.

**Para trading de {unsupported_token}:**
• Hyperliquid ofrece **futuros perpetuos** (perps) para {unsupported_token}
• Para swaps spot, usa agregadores DEX como 1inch, Uniswap o 0x

**Disponible en Anvil para {unsupported_token}:**
• 📈 Consultar precio y datos de mercado
• 📊 Seguimiento de portafolio
• 🔮 Predicciones de precio via Hunter AI""",
                    "pt": f"""⚠️ **{unsupported_token} Não Disponível para Swap Spot**

**{unsupported_token}** não está disponível no Hyperliquid Spot atualmente.

Hyperliquid Spot tem **440+ tokens** pareados com USDC, mas {unsupported_token} não está entre eles.

**Para trading de {unsupported_token}:**
• Hyperliquid oferece **futuros perpétuos** (perps) para {unsupported_token}
• Para swaps spot, use agregadores DEX como 1inch, Uniswap ou 0x

**Disponível no Anvil para {unsupported_token}:**
• 📈 Verificar preço e dados de mercado
• 📊 Rastreamento de portfólio
• 🔮 Previsões de preço via Hunter AI""",
                }
            else:
                # Generic message for unknown tokens
                popular_tokens = ", ".join(
                    sorted(list(self.HYPERLIQUID_SPOT_TOKENS)[:10])
                )
                error_messages = {
                    "en": f"""⚠️ **Token Not Supported**

**{unsupported_token}** is not available on Hyperliquid Spot.

**Popular tokens (440+ available):**
{popular_tokens}... and many more.

💡 All swaps on Hyperliquid Spot are paired with USDC.""",
                    "es": f"""⚠️ **Token No Soportado**

**{unsupported_token}** no está disponible en Hyperliquid Spot.

**Tokens populares (440+ disponibles):**
{popular_tokens}... y muchos más.

💡 Todos los swaps en Hyperliquid Spot están pareados con USDC.""",
                    "pt": f"""⚠️ **Token Não Suportado**

**{unsupported_token}** não está disponível no Hyperliquid Spot.

**Tokens populares (440+ disponíveis):**
{popular_tokens}... e muitos mais.

💡 Todas as trocas no Hyperliquid Spot são pareadas com USDC.""",
                }

            return HandlerResult(
                content=error_messages.get(language, error_messages["en"]),
                pending_action=None,
                requires_registration=False,
                metadata={
                    "error": "token_not_supported",
                    "token": unsupported_token,
                    "is_major_token": is_major_token,
                    "suggestion": "use_perps_or_dex"
                    if is_major_token
                    else "check_supported_tokens",
                },
            )

        # Parse amount
        try:
            amount = float(swap_info.amount)
        except (ValueError, TypeError):
            amount = 100.0

        # Check user balance and add recommendation if insufficient
        insufficient_balance_warning = ""
        if hasattr(self, "_user_context") and self._user_context:
            user_balance = (
                float(self._user_context.total_balance_usd)
                if self._user_context.total_balance_usd
                else 0
            )
            portfolio_state = self._user_context.portfolio_state
            has_wallet = self._user_context.has_connected_wallet

            # Check if user has no balance or very low balance (empty/starter portfolio)
            if portfolio_state in ["empty", "starter"] or user_balance < 10:
                buy_recommendation = {
                    "en": f"""
💡 **Quick Tip:** Your portfolio appears to have limited funds.

To complete this swap, you'll need **{swap_info.from_token}** in your wallet.

**Get started:**
• 💳 Say **"buy crypto"** to purchase with card/Apple Pay/Google Pay
• 📥 Or transfer {swap_info.from_token} from another wallet

""",
                    "es": f"""
💡 **Consejo:** Tu portafolio parece tener fondos limitados.

Para completar este swap, necesitarás **{swap_info.from_token}** en tu wallet.

**Cómo empezar:**
• 💳 Di **"comprar cripto"** para comprar con tarjeta/Apple Pay/Google Pay
• 📥 O transfiere {swap_info.from_token} desde otra wallet

""",
                    "pt": f"""
💡 **Dica:** Seu portfólio parece ter fundos limitados.

Para completar esta troca, você precisará de **{swap_info.from_token}** na sua carteira.

**Como começar:**
• 💳 Diga **"comprar cripto"** para comprar com cartão/Apple Pay/Google Pay
• 📥 Ou transfira {swap_info.from_token} de outra carteira

""",
                }
                insufficient_balance_warning = buy_recommendation.get(
                    language, buy_recommendation["en"]
                )
                logger.info(
                    f"[SWAP] User has insufficient balance (${user_balance:.2f}, state={portfolio_state}). "
                    f"Adding buy recommendation."
                )

        # Get Hyperliquid spot quote
        quote_result = await self._get_hyperliquid_quote(
            swap_info.from_token,
            swap_info.to_token,
            amount,
        )

        if not quote_result:
            # Hyperliquid quote failed
            error_messages = {
                "en": f"⚠️ **Quote Failed**\n\nUnable to get quote for **{swap_info.from_token}/{swap_info.to_token}** from Hyperliquid.\n\nThis pair may have insufficient liquidity. Please try again or use a different pair.",
                "es": f"⚠️ **Cotización Fallida**\n\nNo se pudo obtener cotización para **{swap_info.from_token}/{swap_info.to_token}** de Hyperliquid.\n\nEste par puede tener liquidez insuficiente. Por favor intenta de nuevo o usa otro par.",
                "pt": f"⚠️ **Cotação Falhou**\n\nNão foi possível obter cotação para **{swap_info.from_token}/{swap_info.to_token}** do Hyperliquid.\n\nEste par pode ter liquidez insuficiente. Por favor tente novamente ou use outro par.",
            }
            return HandlerResult(
                content=error_messages.get(language, error_messages["en"]),
                pending_action=None,
                requires_registration=False,
                metadata={
                    "error": "quote_failed",
                    "from_token": swap_info.from_token,
                    "to_token": swap_info.to_token,
                },
            )

        # Real Hyperliquid quote
        rate = quote_result["rate"]
        output_amount = quote_result["output_amount"]
        spread_bps = quote_result["spread_bps"]
        price_impact = spread_bps / 100  # Convert bps to percentage

        latency_ms = int((time.time() - start_time) * 1000)
        logger.info(
            f"✅ Hyperliquid spot quote: {amount} {swap_info.from_token} → "
            f"{output_amount:.6f} {swap_info.to_token} @ {rate:.6f} "
            f"(spread: {spread_bps:.2f} bps, latency: {latency_ms}ms)"
        )

        # Extract chain information from swap_info or default to hyperliquid
        chain = swap_info.from_chain or "hyperliquid"
        to_chain = swap_info.to_chain

        # Format quote
        content = self._get_message("quote", language).format(
            amount=swap_info.amount,
            from_token=swap_info.from_token,
            to_token=swap_info.to_token,
            output_amount=f"{output_amount:.6f}",
            rate=f"{rate:.6f}",
            price_impact=f"{price_impact:.2f}",
            network="Hyperliquid",
        )

        # Add Hyperliquid branding
        content = f"🔵 **HYPERLIQUID SPOT**\n\n{content}"

        # Add insufficient balance warning if applicable (recommend to buy)
        if insufficient_balance_warning:
            content = insufficient_balance_warning + content

        # Build execute data for when swap is complete and ready
        execute_data = {
            "action_type": "swap",
            "provider": "hyperliquid",
            "chain": chain,
            "from_token": swap_info.from_token,
            "to_token": swap_info.to_token,
            "amount": swap_info.amount,
            "slippage": 1.0,
            "to_chain": to_chain,
            "quote_amount": f"{output_amount:.6f}",
            "exchange_rate": f"{rate:.6f}",
            "spread_bps": spread_bps,
            "fee_percent": 0.02,  # Hyperliquid 0.02% fee
        }

        # Mark swap as complete in metadata so it can be detected for confirmation
        swap_metadata = swap_info.to_dict()
        swap_metadata["is_complete"] = True

        return HandlerResult(
            content=content,
            pending_action=None,
            requires_registration=True,
            metadata=swap_metadata,
            enrichment={
                "swap_quote": {
                    "from_token": swap_info.from_token,
                    "to_token": swap_info.to_token,
                    "from_amount": swap_info.amount,
                    "to_amount": f"{output_amount:.6f}",
                    "rate": rate,
                    "price_impact": price_impact,
                    "network": "hyperliquid",
                    "provider": "hyperliquid",
                    "spread_bps": spread_bps,
                    "fee_percent": 0.02,
                    "latency_ms": latency_ms,
                },
            },
            execute_data=execute_data,
        )

    def _extract_swap_info(
        self,
        message: str,
        context: ConversationContext | None,
    ) -> SwapInfo:
        """Extract swap information from message and context."""
        swap_info = SwapInfo()
        message_lower = message.lower()

        # Build combined text for parsing
        combined = message_lower
        if context and context.summary:
            combined = f"{context.summary.lower()}\n{message_lower}"

        # ALL tokens to look for - includes both supported HL Spot tokens AND major tokens
        # We extract major tokens too so we can show proper error messages
        ALL_TOKENS_TO_EXTRACT = set(SUPPORTED_TOKENS) | set(MAJOR_TOKENS_NOT_SUPPORTED)

        # Supported chains
        SUPPORTED_CHAINS = {
            "ethereum": "ethereum",
            "eth": "ethereum",
            "base": "base",
            "arbitrum": "arbitrum",
            "arb": "arbitrum",
            "optimism": "optimism",
            "op": "optimism",
            "polygon": "polygon",
            "matic": "polygon",
            "avalanche": "avalanche",
            "avax": "avalanche",
            "bsc": "bsc",
            "binance": "bsc",
            "solana": "solana",
            "sol": "solana",
        }

        # Extract chains for cross-chain swaps
        # Pattern: "from Ethereum to Base", "desde Ethereum a Base"
        chain_patterns = [
            r"(?:from|desde|de)\s+(\w+)\s+(?:to|a|para|hacia)\s+(\w+)",
            r"on\s+(\w+)\s+(?:to|a|para|hacia)\s+(\w+)",
        ]
        for pattern in chain_patterns:
            match = re.search(pattern, combined, re.IGNORECASE)
            if match:
                from_chain_name = match.group(1).lower()
                to_chain_name = match.group(2).lower()
                if from_chain_name in SUPPORTED_CHAINS:
                    swap_info.from_chain = SUPPORTED_CHAINS[from_chain_name]
                if to_chain_name in SUPPORTED_CHAINS:
                    swap_info.to_chain = SUPPORTED_CHAINS[to_chain_name]
                break

        # Extract tokens mentioned (avoid chains that were already extracted)
        excluded_words = set()
        if swap_info.from_chain:
            excluded_words.add(swap_info.from_chain.lower())
        if swap_info.to_chain:
            excluded_words.add(swap_info.to_chain.lower())
        # Also exclude chain aliases
        for chain_alias in [
            "ethereum",
            "eth",
            "base",
            "arbitrum",
            "arb",
            "optimism",
            "op",
            "polygon",
            "matic",
            "avalanche",
            "avax",
            "bsc",
            "binance",
            "solana",
            "sol",
        ]:
            excluded_words.add(chain_alias)

        # Find all tokens mentioned in the message
        # Include BOTH supported HL Spot tokens AND major tokens (for error messaging)
        found_tokens = []
        for token in ALL_TOKENS_TO_EXTRACT:
            if token.lower() in combined and token.lower() not in excluded_words:
                found_tokens.append(token)

        # Try to extract source token with patterns
        # Pattern 1: "Swap USDC from Ethereum" -> USDC is the token (before "from chain")
        # Pattern 2: "Swap 100 USDC to ETH" -> USDC is the token (before "to token")
        # Pattern 3: "Swap USDC" -> USDC is the token
        from_token_patterns = [
            r"(?:swap|cambiar|trocar|exchange|bridge)\s+(?:\d+\.?\d*\s*)?(\w+)",
            r"(\w+)\s+(?:from|desde|de)\s+(?:ethereum|base|arbitrum|optimism|polygon|avalanche|bsc|binance|solana)",
        ]
        for pattern in from_token_patterns:
            match = re.search(pattern, combined, re.IGNORECASE)
            if match:
                token = match.group(1).upper()
                # Include major tokens too for proper error messaging
                if (
                    token in ALL_TOKENS_TO_EXTRACT
                    and token.lower() not in excluded_words
                ):
                    swap_info.from_token = token
                    break

        # Try to extract target token (after "to" but not if it's a chain)
        # Pattern: "to ETH" or "a ETH" (not "to Base" which is a chain)
        # Only extract if we haven't already identified it as a chain
        to_token_patterns = [
            r"(?:to|a|hacia|por|for|para)\s+(\w+)",
        ]
        for pattern in to_token_patterns:
            match = re.search(pattern, combined, re.IGNORECASE)
            if match:
                token = match.group(1).upper()
                # Check if it's a token (not a chain that was already extracted)
                # Include major tokens too for proper error messaging
                if (
                    token in ALL_TOKENS_TO_EXTRACT
                    and token.lower() not in excluded_words
                    and token != swap_info.from_token
                ):
                    # Only set if we haven't already set to_chain (cross-chain swaps don't need different to_token)
                    # For cross-chain, to_token will be set to from_token later
                    if not swap_info.to_chain:
                        swap_info.to_token = token
                    break

        # For cross-chain swaps (when we have chains but no to_token),
        # the to_token is the same as from_token (bridging the same token)
        if swap_info.from_chain and swap_info.to_chain and not swap_info.to_token:
            swap_info.to_token = swap_info.from_token

        # Try to extract amount
        amount_patterns = [
            r"(\d+\.?\d*)\s*(?:tokens?)?",
        ]
        for pattern in amount_patterns:
            match = re.search(pattern, combined)
            if match:
                swap_info.amount = match.group(1)
                break

        # If we found tokens but couldn't determine source/target, use order
        # But only if we don't have chains (for cross-chain, we handle it differently)
        if (
            found_tokens
            and not swap_info.from_token
            and not swap_info.to_token
            and not swap_info.from_chain
        ):
            if len(found_tokens) >= 1:
                swap_info.from_token = found_tokens[0]
            if len(found_tokens) >= 2:
                swap_info.to_token = found_tokens[1]

        # For cross-chain swaps (when we have chains but no to_token),
        # the to_token is the same as from_token (bridging the same token)
        if (
            swap_info.from_chain
            and swap_info.to_chain
            and not swap_info.to_token
            and swap_info.from_token
        ):
            swap_info.to_token = swap_info.from_token

        # Use context entities if available
        if context and context.detected_entities:
            entities = context.detected_entities
            if entities.get("tokens"):
                context_tokens = entities["tokens"]
                if not swap_info.from_token and len(context_tokens) >= 1:
                    swap_info.from_token = context_tokens[0]
                if not swap_info.to_token and len(context_tokens) >= 2:
                    swap_info.to_token = context_tokens[1]
            if entities.get("amounts") and not swap_info.amount:
                swap_info.amount = str(entities["amounts"][0])

        return swap_info

    def _apply_continuation(
        self,
        swap_info: SwapInfo,
        step: str,
        value: str,
    ) -> SwapInfo:
        """Apply continuation value to swap info."""
        value_upper = value.upper().strip()
        value_lower = value.lower().strip()

        # Check if user selected a numbered option (1, 2, 3, etc.)
        number_match = re.search(r"^(\d+)", value_lower)
        if number_match:
            option_num = int(number_match.group(1))
            # Map number to token/amount based on step
            if step == "from_token":
                if 1 <= option_num <= len(self._popular_tokens):
                    swap_info.from_token = self._popular_tokens[option_num - 1]
                    return swap_info
            elif step == "to_token":
                # Exclude from_token from options
                available_tokens = [
                    t for t in self._popular_tokens if t != swap_info.from_token
                ]
                if 1 <= option_num <= len(available_tokens):
                    swap_info.to_token = available_tokens[option_num - 1]
                    return swap_info
            elif step == "amount":
                # Common amounts for quick selection
                common_amounts = ["10", "50", "100", "500", "1000"]
                if 1 <= option_num <= len(common_amounts):
                    swap_info.amount = common_amounts[option_num - 1]
                    return swap_info

        # Fallback to original logic for text-based responses
        # Include major tokens for proper error messaging
        ALL_TOKENS = set(SUPPORTED_TOKENS) | set(MAJOR_TOKENS_NOT_SUPPORTED)

        if step == "from_token":
            # Extract token from value
            for token in ALL_TOKENS:
                if token in value_upper:
                    swap_info.from_token = token
                    break
            else:
                # Maybe just the token name
                if value_upper in ALL_TOKENS:
                    swap_info.from_token = value_upper

        elif step == "to_token":
            for token in ALL_TOKENS:
                if token in value_upper:
                    swap_info.to_token = token
                    break
            else:
                if value_upper in ALL_TOKENS:
                    swap_info.to_token = value_upper

        elif step == "amount":
            # Extract number
            match = re.search(r"(\d+\.?\d*)", value)
            if match:
                swap_info.amount = match.group(1)
            else:
                swap_info.amount = value.strip()

        return swap_info

    async def _get_hyperliquid_quote(
        self,
        from_token: str,
        to_token: str,
        amount: float,
    ) -> dict[str, Any] | None:
        """
        Get real-time swap quote from Hyperliquid spot.

        Args:
            from_token: Source token symbol
            to_token: Destination token symbol
            amount: Amount to swap

        Returns:
            Quote dict with rate, output_amount, spread_bps, or None if unavailable
        """
        if not self._hyperliquid:
            return None

        # Check cache
        cache_key = f"{from_token}:{to_token}:{amount}"
        now = time.time()
        if cache_key in self._quote_cache:
            cached_time, cached_quote = self._quote_cache[cache_key]
            if now - cached_time < self._cache_ttl:
                logger.debug(f"Using cached quote for {from_token}/{to_token}")
                return cached_quote

        try:
            quote = await self._hyperliquid.get_spot_quote(
                from_token=from_token,
                to_token=to_token,
                amount=amount,
            )

            result = {
                "rate": quote.price,
                "output_amount": quote.to_amount,
                "spread_bps": quote.spread_bps,
                "mid_price": quote.mid_price,
                "from_token": from_token,
                "to_token": to_token,
            }

            # Cache the result
            self._quote_cache[cache_key] = (now, result)

            return result

        except Exception as e:
            logger.warning(f"Hyperliquid quote failed for {from_token}/{to_token}: {e}")
            return None

    def _get_message(self, key: str, language: str) -> str:
        """Get localized message."""
        messages = self._messages.get(key, {})
        return messages.get(language, messages.get("en", ""))

    def _format_token_options(self, tokens: list[str], language: str) -> str:
        """Format token options as numbered list."""
        options_text = {
            "en": "Select a token:",
            "es": "Selecciona un token:",
            "pt": "Selecione um token:",
        }
        header = options_text.get(language, options_text["en"])

        options = []
        for i, token in enumerate(tokens[:6], 1):  # Limit to 6 options
            options.append(f"{i}. {token}")

        return f"{header}\n" + "\n".join(options)

    def _format_amount_options(self, language: str) -> str:
        """Format amount options as numbered list."""
        common_amounts = ["10", "50", "100", "500", "1000"]
        options_text = {
            "en": "Select an amount:",
            "es": "Selecciona una cantidad:",
            "pt": "Selecione uma quantidade:",
        }
        header = options_text.get(language, options_text["en"])

        options = []
        for i, amount in enumerate(common_amounts, 1):
            options.append(f"{i}. {amount}")

        return f"{header}\n" + "\n".join(options) + "\n\nOr type a custom amount."
