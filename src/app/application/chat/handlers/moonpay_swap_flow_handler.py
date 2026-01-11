"""
MoonPay Swap Flow Handler.

Implements the complete conversational swap flow using MoonPay API:
- Step-by-step parameter collection (from_token, to_token, amount)
- Intelligent parameter detection from initial message
- MoonPay quote integration
- Execute object generation for frontend confirmation banner
- Multi-language support

Note: The actual swap execution is handled by Privy SDK on the frontend.
This handler manages the conversational flow and provides quote data.
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from app.application.chat.services.conversation_memory import ConversationContext

logger = logging.getLogger(__name__)


# ============================================================================
# Data Classes
# ============================================================================


@dataclass
class MoonPaySwapInfo:
    """Information for a MoonPay swap operation."""

    from_token: str | None = None
    to_token: str | None = None
    amount: str | None = None

    # MoonPay supported tokens for swaps
    SUPPORTED_TOKENS: list[str] = field(
        default_factory=lambda: ["ETH", "USDC", "USDT", "BTC", "SOL"]
    )

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
        """Convert to dictionary for serialization."""
        return {
            "from_token": self.from_token,
            "to_token": self.to_token,
            "amount": self.amount,
            "is_complete": self.is_complete,
            "next_step": self.next_step,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MoonPaySwapInfo":
        """Create from dictionary."""
        return cls(
            from_token=data.get("from_token"),
            to_token=data.get("to_token"),
            amount=data.get("amount"),
        )


@dataclass
class MoonPaySwapHandlerResult:
    """Result from MoonPay swap handler."""

    content: str
    pending_action: str | None = None
    requires_registration: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
    enrichment: dict[str, Any] | None = None
    execute_data: dict[str, Any] | None = None
    language: str = "en"
    handler: str = "moonpay_swap_flow_handler"


# ============================================================================
# Localized Messages
# ============================================================================

SWAP_FLOW_MESSAGES = {
    "en": {
        "ask_from_token": """🔄 **Let's Start Your Swap!**

Great choice! Swapping crypto is easy with MoonPay.

**Step 1 of 4:** Which crypto do you want to swap FROM?

{options}

💡 *Just type the token symbol, like "ETH"*""",

        "ask_to_token": """✨ **Perfect! You're swapping {from_emoji} {from_token}**

**Step 2 of 4:** What crypto would you like to receive?

{options}

💡 *Type the token you want to get, like "USDC"*""",

        "ask_amount": """🎯 **Almost There!**

Swapping {from_emoji} **{from_token}** → {to_emoji} **{to_token}**

**Step 3 of 4:** How much {from_token} would you like to swap?

💡 *Just enter a number, like:*
• `1` (one {from_token})
• `0.5` (half a {from_token})
• `100` (one hundred {from_token})""",

        "quote_ready": """✅ **Swap Ready to Execute**

🔄 **Intercambio:** {amount} {from_token} → {quote_amount} {to_token}
📊 **Rate:** 1 {from_token} = {exchange_rate} {to_token}
💸 **Network Fee:** ~${network_fee_usd}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Click **Confirm** to execute the swap.""",

        "error_invalid_token": """❌ I didn't recognize that token. Let's try again!

{options}""",

        "error_invalid_amount": """❌ That doesn't look like a valid amount. Let's try again!

💡 *Enter a number like: 1, 0.5, or 100*""",

        "error_quote_failed": """⚠️ Unable to get quote for {from_token} → {to_token}.

Please try again or choose different tokens.""",
    },
    "es": {
        "ask_from_token": """🔄 **¡Comencemos tu Swap!**

¡Excelente elección! Intercambiar cripto es fácil con MoonPay.

**Paso 1 de 4:** ¿Qué cripto quieres intercambiar?

{options}

💡 *Solo escribe el símbolo, como "ETH"*""",

        "ask_to_token": """✨ **¡Perfecto! Vas a intercambiar {from_emoji} {from_token}**

**Paso 2 de 4:** ¿Qué cripto te gustaría recibir?

{options}

💡 *Escribe el token que quieres recibir, como "USDC"*""",

        "ask_amount": """🎯 **¡Casi Listo!**

Intercambiando {from_emoji} **{from_token}** → {to_emoji} **{to_token}**

**Paso 3 de 4:** ¿Cuánto {from_token} te gustaría intercambiar?

💡 *Solo ingresa un número, como:*
• `1` (un {from_token})
• `0.5` (medio {from_token})
• `100` (cien {from_token})""",

        "quote_ready": """✅ **Swap Listo para Ejecutar**

🔄 **Intercambio:** {amount} {from_token} → {quote_amount} {to_token}
📊 **Tasa:** 1 {from_token} = {exchange_rate} {to_token}
💸 **Fee de red:** ~${network_fee_usd}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Haz clic en **Confirmar** para ejecutar el swap.""",

        "error_invalid_token": """❌ No reconocí ese token. ¡Intentemos de nuevo!

{options}""",

        "error_invalid_amount": """❌ Eso no parece una cantidad válida. ¡Intentemos de nuevo!

💡 *Ingresa un número como: 1, 0.5, o 100*""",

        "error_quote_failed": """⚠️ No se pudo obtener cotización para {from_token} → {to_token}.

Por favor intenta de nuevo o elige tokens diferentes.""",
    },
    "pt": {
        "ask_from_token": """🔄 **Vamos Começar seu Swap!**

Ótima escolha! Trocar cripto é fácil com MoonPay.

**Passo 1 de 4:** Qual cripto você quer trocar?

{options}

💡 *Apenas digite o símbolo, como "ETH"*""",

        "ask_to_token": """✨ **Perfeito! Você vai trocar {from_emoji} {from_token}**

**Passo 2 de 4:** Qual cripto você gostaria de receber?

{options}

💡 *Digite o token que você quer receber, como "USDC"*""",

        "ask_amount": """🎯 **Quase Lá!**

Trocando {from_emoji} **{from_token}** → {to_emoji} **{to_token}**

**Passo 3 de 4:** Quanto {from_token} você gostaria de trocar?

💡 *Apenas digite um número, como:*
• `1` (um {from_token})
• `0.5` (meio {from_token})
• `100` (cem {from_token})""",

        "quote_ready": """✅ **Swap Pronto para Executar**

🔄 **Troca:** {amount} {from_token} → {quote_amount} {to_token}
📊 **Taxa:** 1 {from_token} = {exchange_rate} {to_token}
💸 **Taxa de rede:** ~${network_fee_usd}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Clique em **Confirmar** para executar o swap.""",

        "error_invalid_token": """❌ Não reconheci esse token. Vamos tentar de novo!

{options}""",

        "error_invalid_amount": """❌ Isso não parece uma quantidade válida. Vamos tentar de novo!

💡 *Digite um número como: 1, 0.5, ou 100*""",

        "error_quote_failed": """⚠️ Não foi possível obter cotação para {from_token} → {to_token}.

Por favor tente novamente ou escolha tokens diferentes.""",
    },
}

# Token emoji mapping
TOKEN_EMOJIS = {
    "BTC": "₿",
    "ETH": "Ξ",
    "SOL": "◎",
    "USDC": "💵",
    "USDT": "💵",
}


class MoonPaySwapFlowHandler:
    """
    Handler for MoonPay swap conversational flow.

    Manages the multi-turn conversation for collecting swap parameters
    and integrates with MoonPay API for quotes.

    Flow:
    1. User indicates swap intent → Ask for FROM token
    2. User provides FROM token → Ask for TO token
    3. User provides TO token → Ask for AMOUNT
    4. User provides AMOUNT → Get quote, return execute object
    5. User confirms → Frontend executes via Privy
    """

    def __init__(self, moonpay_swap_handler=None):
        """
        Initialize the handler.

        Args:
            moonpay_swap_handler: Optional MoonPay swap handler for quotes
        """
        self._moonpay_handler = moonpay_swap_handler
        self._supported_tokens = ["ETH", "USDC", "USDT", "BTC", "SOL"]

    # ========================================================================
    # Main Entry Point
    # ========================================================================

    async def handle(
        self,
        message: str,
        context: ConversationContext | None = None,
        language: str = "en",
        continuation_step: str | None = None,
        continuation_value: str | None = None,
        previous_swap_info: dict | None = None,
    ) -> MoonPaySwapHandlerResult:
        """
        Handle swap request with multi-turn support.

        Args:
            message: User message
            context: Conversation context
            language: Language code
            continuation_step: If continuing a flow, which step
            continuation_value: Value for the continuation step
            previous_swap_info: Previous swap info for continuation

        Returns:
            MoonPaySwapHandlerResult with response and pending action
        """
        logger.info(f"[MOONPAY_SWAP] handle() called with message: '{message}'")
        logger.info(f"[MOONPAY_SWAP] continuation_step: {continuation_step}")
        logger.info(f"[MOONPAY_SWAP] previous_swap_info: {previous_swap_info}")

        # Initialize swap_info from previous state if available
        if previous_swap_info:
            swap_info = MoonPaySwapInfo.from_dict(previous_swap_info)
        else:
            swap_info = MoonPaySwapInfo()

        # Try to extract info from initial message
        extracted = self._parse_swap_intent(message)
        if extracted.get("from_token"):
            swap_info.from_token = extracted["from_token"]
        if extracted.get("to_token"):
            swap_info.to_token = extracted["to_token"]
        if extracted.get("amount"):
            swap_info.amount = extracted["amount"]

        # Handle continuation of pending flow
        if continuation_step:
            swap_info = self._apply_continuation(
                swap_info,
                continuation_step,
                continuation_value or message,
            )

        # Process the flow
        return await self._process_swap_flow(swap_info, language)

    # ========================================================================
    # Flow Processing
    # ========================================================================

    async def _process_swap_flow(
        self,
        swap_info: MoonPaySwapInfo,
        language: str,
    ) -> MoonPaySwapHandlerResult:
        """Process swap flow based on current info."""
        msgs = SWAP_FLOW_MESSAGES.get(language, SWAP_FLOW_MESSAGES["en"])

        # Phase 1: Ask for FROM token
        if not swap_info.from_token:
            options = self._format_token_options(self._supported_tokens)
            return MoonPaySwapHandlerResult(
                content=msgs["ask_from_token"].format(options=options),
                pending_action="moonpay_swap_awaiting_from_token",
                metadata=swap_info.to_dict(),
                execute_data=None,  # No execute until complete
                language=language,
            )

        # Phase 2: Ask for TO token
        if not swap_info.to_token:
            available_tokens = [t for t in self._supported_tokens if t != swap_info.from_token]
            options = self._format_token_options(available_tokens)
            from_emoji = TOKEN_EMOJIS.get(swap_info.from_token, "💎")
            return MoonPaySwapHandlerResult(
                content=msgs["ask_to_token"].format(
                    from_token=swap_info.from_token,
                    from_emoji=from_emoji,
                    options=options,
                ),
                pending_action="moonpay_swap_awaiting_to_token",
                metadata=swap_info.to_dict(),
                execute_data=None,
                language=language,
            )

        # Phase 3: Ask for AMOUNT
        if not swap_info.amount:
            from_emoji = TOKEN_EMOJIS.get(swap_info.from_token, "💎")
            to_emoji = TOKEN_EMOJIS.get(swap_info.to_token, "💎")
            return MoonPaySwapHandlerResult(
                content=msgs["ask_amount"].format(
                    from_token=swap_info.from_token,
                    to_token=swap_info.to_token,
                    from_emoji=from_emoji,
                    to_emoji=to_emoji,
                ),
                pending_action="moonpay_swap_awaiting_amount",
                metadata=swap_info.to_dict(),
                execute_data=None,
                language=language,
            )

        # Phase 4: All data collected - Get quote and generate execute object
        return await self._generate_quote_and_execute(swap_info, language)

    async def _generate_quote_and_execute(
        self,
        swap_info: MoonPaySwapInfo,
        language: str,
    ) -> MoonPaySwapHandlerResult:
        """Generate quote from MoonPay and create execute object."""
        msgs = SWAP_FLOW_MESSAGES.get(language, SWAP_FLOW_MESSAGES["en"])

        try:
            # Get quote from MoonPay
            if self._moonpay_handler:
                logger.info(f"[MOONPAY_SWAP] Calling MoonPay API for quote: {swap_info.from_token} -> {swap_info.to_token}, amount: {swap_info.amount}")
                quote_result = await self._moonpay_handler.get_swap_quote(
                    from_currency=swap_info.from_token.lower(),
                    to_currency=swap_info.to_token.lower(),
                    amount=swap_info.amount,
                    language=language,
                )
                # MoonPaySwapHandler returns quote dict with these fields:
                # quote_amount, exchange_rate, network_fee_usd, expires_at
                quote = quote_result.quote if hasattr(quote_result, "quote") and quote_result.quote else {}
                logger.info(f"[MOONPAY_SWAP] MoonPay quote received: {quote}")
            else:
                # Demo quote if no handler available
                logger.warning("[MOONPAY_SWAP] No MoonPay handler available, using demo quote")
                quote = self._get_demo_quote(swap_info)

            # Extract quote data - handle both MoonPay API format and demo format
            # MoonPaySwapHandler returns: quote_amount, exchange_rate, network_fee_usd
            # Demo returns: quoteCurrencyAmount, exchangeRate, networkFee
            quote_amount = (
                quote.get("quote_amount") or 
                quote.get("quoteCurrencyAmount") or 
                self._calculate_demo_output(swap_info)
            )
            exchange_rate = (
                quote.get("exchange_rate") or 
                quote.get("exchangeRate") or 
                self._get_demo_rate(swap_info.from_token, swap_info.to_token)
            )
            network_fee = (
                quote.get("network_fee_usd") or 
                quote.get("networkFee") or 
                "0.01"
            )
            quote_id = quote.get("id", f"quote-{datetime.utcnow().timestamp()}")
            expires_at = quote.get("expires_at") or quote.get("expiresAt") or (datetime.utcnow() + timedelta(minutes=1)).isoformat()

            # Format the response
            content = msgs["quote_ready"].format(
                amount=swap_info.amount,
                from_token=swap_info.from_token,
                to_token=swap_info.to_token,
                quote_amount=f"{float(quote_amount):.6f}",
                exchange_rate=f"{float(exchange_rate):.6f}",
                network_fee_usd=network_fee,
            )

            # Build execute object - ONLY when all data is complete
            # Use "moonpay_swap" to differentiate from regular swaps
            execute_data = {
                "action_type": "moonpay_swap",
                "from_token": swap_info.from_token,
                "to_token": swap_info.to_token,
                "amount": swap_info.amount,
                "quote_id": quote_id,
                "quote_amount": str(quote_amount),
                "exchange_rate": str(exchange_rate),
                "network_fee_usd": str(network_fee),
                "expires_at": expires_at,
            }

            # Mark metadata as complete
            metadata = swap_info.to_dict()
            metadata["is_complete"] = True
            metadata["quote"] = quote

            return MoonPaySwapHandlerResult(
                content=content,
                pending_action=None,  # Flow complete - no pending action
                requires_registration=True,
                metadata=metadata,
                enrichment={
                    "swap_quote": {
                        "from_token": swap_info.from_token,
                        "to_token": swap_info.to_token,
                        "from_amount": swap_info.amount,
                        "to_amount": str(quote_amount),
                        "rate": str(exchange_rate),
                        "network_fee_usd": str(network_fee),
                        "quote_id": quote_id,
                        "expires_at": expires_at,
                    },
                },
                execute_data=execute_data,  # Execute object triggers banner
                language=language,
            )

        except Exception as e:
            logger.error(f"Error getting MoonPay quote: {e}", exc_info=True)
            return MoonPaySwapHandlerResult(
                content=msgs["error_quote_failed"].format(
                    from_token=swap_info.from_token,
                    to_token=swap_info.to_token,
                ),
                pending_action=None,
                metadata=swap_info.to_dict(),
                execute_data=None,
                language=language,
            )

    # ========================================================================
    # Parsing and Extraction
    # ========================================================================

    def _parse_swap_intent(self, message: str) -> dict:
        """
        Extract from_token, to_token and amount from message.

        Examples:
        - "swap 1 ETH por USDC" → {from_token: "ETH", to_token: "USDC", amount: "1"}
        - "intercambiar 100 USDC por ETH" → {from_token: "USDC", to_token: "ETH", amount: "100"}
        - "cambiar 0.5 BTC a SOL" → {from_token: "BTC", to_token: "SOL", amount: "0.5"}
        """
        result = {
            "from_token": None,
            "to_token": None,
            "amount": None,
        }

        message_lower = message.lower()

        # Pattern 1: "swap 1 ETH por USDC" / "intercambiar 100 USDC por ETH"
        pattern1 = re.compile(
            r"(?:swap|intercambiar|cambiar|convertir|trocar)\s+(\d+(?:\.\d+)?)\s*(\w+)\s+(?:por|a|to|for|en|para)\s+(\w+)",
            re.IGNORECASE
        )
        match = pattern1.search(message_lower)
        if match:
            result["amount"] = match.group(1)
            from_token = match.group(2).upper()
            to_token = match.group(3).upper()
            if from_token in self._supported_tokens:
                result["from_token"] = from_token
            if to_token in self._supported_tokens:
                result["to_token"] = to_token
            return result

        # Pattern 2: "1 ETH a USDC" (without verb)
        pattern2 = re.compile(
            r"(\d+(?:\.\d+)?)\s*(\w+)\s+(?:a|por|to|for|en|para)\s+(\w+)",
            re.IGNORECASE
        )
        match = pattern2.search(message_lower)
        if match:
            result["amount"] = match.group(1)
            from_token = match.group(2).upper()
            to_token = match.group(3).upper()
            if from_token in self._supported_tokens:
                result["from_token"] = from_token
            if to_token in self._supported_tokens:
                result["to_token"] = to_token
            return result

        # Pattern 3: "swap ETH por USDC" (tokens without amount)
        pattern3 = re.compile(
            r"(?:swap|intercambiar|cambiar|convertir|trocar)\s+(\w+)\s+(?:por|a|to|for|en|para)\s+(\w+)",
            re.IGNORECASE
        )
        match = pattern3.search(message_lower)
        if match:
            from_token = match.group(1).upper()
            to_token = match.group(2).upper()
            if from_token in self._supported_tokens:
                result["from_token"] = from_token
            if to_token in self._supported_tokens:
                result["to_token"] = to_token
            return result

        # Pattern 4: "swap ETH" (single token)
        pattern4 = re.compile(
            r"(?:swap|intercambiar|cambiar|convertir|trocar)\s+(\w+)",
            re.IGNORECASE
        )
        match = pattern4.search(message_lower)
        if match:
            from_token = match.group(1).upper()
            if from_token in self._supported_tokens:
                result["from_token"] = from_token
            return result

        return result

    def _apply_continuation(
        self,
        swap_info: MoonPaySwapInfo,
        step: str,
        value: str,
    ) -> MoonPaySwapInfo:
        """Apply continuation value to swap info."""
        value_upper = value.upper().strip()
        value_lower = value.lower().strip()

        # Check if user selected a numbered option (1, 2, 3, etc.)
        number_match = re.search(r"^(\d+)$", value_lower)
        if number_match:
            option_num = int(number_match.group(1))
            if step == "from_token":
                if 1 <= option_num <= len(self._supported_tokens):
                    swap_info.from_token = self._supported_tokens[option_num - 1]
                    return swap_info
            elif step == "to_token":
                available_tokens = [t for t in self._supported_tokens if t != swap_info.from_token]
                if 1 <= option_num <= len(available_tokens):
                    swap_info.to_token = available_tokens[option_num - 1]
                    return swap_info

        # Handle token selection
        if step == "from_token":
            for token in self._supported_tokens:
                if token in value_upper or value_upper == token:
                    swap_info.from_token = token
                    break
        elif step == "to_token":
            for token in self._supported_tokens:
                if token in value_upper or value_upper == token:
                    if token != swap_info.from_token:
                        swap_info.to_token = token
                        break
        elif step == "amount":
            # Extract number
            match = re.search(r"(\d+\.?\d*)", value)
            if match:
                swap_info.amount = match.group(1)

        return swap_info

    # ========================================================================
    # Formatting Helpers
    # ========================================================================

    def _format_token_options(self, tokens: list[str]) -> str:
        """Format token options as numbered list with emojis."""
        options = []
        for i, token in enumerate(tokens, 1):
            emoji = TOKEN_EMOJIS.get(token, "💎")
            options.append(f"{i}. {emoji} **{token}**")
        return "\n".join(options)

    # ========================================================================
    # Demo Quote Helpers (fallback when MoonPay handler not available)
    # ========================================================================

    def _get_demo_quote(self, swap_info: MoonPaySwapInfo) -> dict:
        """Generate a demo quote for testing."""
        rate = self._get_demo_rate(swap_info.from_token, swap_info.to_token)
        amount = float(swap_info.amount or "1")
        output = amount * rate

        return {
            "quoteCurrencyAmount": str(output),
            "exchangeRate": str(rate),
            "networkFee": "0.01",
            "id": f"demo-{datetime.utcnow().timestamp()}",
            "expiresAt": (datetime.utcnow() + timedelta(minutes=1)).isoformat(),
        }

    def _get_demo_rate(self, from_token: str, to_token: str) -> float:
        """Get demo exchange rate."""
        rates = {
            ("ETH", "USDC"): 3333.33,
            ("USDC", "ETH"): 0.0003,
            ("ETH", "USDT"): 3333.33,
            ("USDT", "ETH"): 0.0003,
            ("BTC", "USDC"): 66666.67,
            ("USDC", "BTC"): 0.000015,
            ("BTC", "ETH"): 20.0,
            ("ETH", "BTC"): 0.05,
            ("SOL", "USDC"): 150.0,
            ("USDC", "SOL"): 0.0067,
            ("SOL", "ETH"): 0.045,
            ("ETH", "SOL"): 22.22,
            ("USDC", "USDT"): 1.0,
            ("USDT", "USDC"): 1.0,
        }
        return rates.get((from_token, to_token), 1.0)

    def _calculate_demo_output(self, swap_info: MoonPaySwapInfo) -> str:
        """Calculate demo output amount."""
        rate = self._get_demo_rate(swap_info.from_token, swap_info.to_token)
        amount = float(swap_info.amount or "1")
        return str(amount * rate)

