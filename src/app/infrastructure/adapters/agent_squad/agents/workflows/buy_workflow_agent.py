"""
Buy Workflow Agent - Multi-Step Fiat On-Ramp Operations.

Handles the complete crypto purchase workflow for authenticated users:
1. Parse request: Extract crypto, fiat amount, and currency
2. Validate: Check supported assets and networks
3. Confirm: Show purchase details and wait for confirmation
4. Execute: Generate execute_data for Privy on-ramp modal

Integration:
- Privy SDK for MoonPay/Coinbase on-ramp
- Supported assets: ETH, USDC, USDT, BTC
- Frontend triggers Privy funding modal

Example Conversation:
    User: "buy 100 dollars of ETH"
    Agent: "💳 Buying $100 of ETH. Confirm?"
    User: "yes"
    Agent: "✅ Opening purchase flow..." + execute_data for Privy modal
"""

import logging
import re
from typing import Any, TYPE_CHECKING

from app.domain.enums.agent_type import AgentType
from app.domain.value_objects.message_content import MessageContent
from app.domain.ports.agent_squad.agent_gateway import AgentResponse

from .base_workflow_agent import (
    BaseWorkflowAgent,
    WorkflowState,
    WorkflowStep,
    UserContext,
)

if TYPE_CHECKING:
    from app.domain.ports.agent_squad.llm_client_gateway import LLMClientGateway

logger = logging.getLogger(__name__)


# Supported cryptocurrencies for purchase (USDC only)
# Note: Currently only USDC is available for purchase via on-ramp
SUPPORTED_CRYPTOS = {
    "usdc": {"symbol": "USDC", "name": "USD Coin", "emoji": "💵"},
}

# Unsupported cryptos - used for friendly error messages
UNSUPPORTED_CRYPTOS = {
    "eth": {"symbol": "ETH", "name": "Ethereum", "emoji": "Ξ"},
    "usdt": {"symbol": "USDT", "name": "Tether", "emoji": "💵"},
    "btc": {"symbol": "BTC", "name": "Bitcoin", "emoji": "₿"},
    "bitcoin": {"symbol": "BTC", "name": "Bitcoin", "emoji": "₿"},
    "sol": {"symbol": "SOL", "name": "Solana", "emoji": "◎"},
    "solana": {"symbol": "SOL", "name": "Solana", "emoji": "◎"},
    "matic": {"symbol": "MATIC", "name": "Polygon", "emoji": "🟣"},
    "polygon": {"symbol": "MATIC", "name": "Polygon", "emoji": "🟣"},
}

# Supported fiat currencies
SUPPORTED_FIATS = {"USD", "EUR", "GBP", "CAD", "AUD"}

# Supported networks
SUPPORTED_NETWORKS = ["Base", "Ethereum", "Polygon", "Arbitrum"]


class BuyWorkflowAgent(BaseWorkflowAgent):
    """
    AGNO-based multi-step crypto purchase workflow agent.

    Steps:
    1. parse_request: Extract crypto, fiat amount, and currency
    2. validate: Check supported assets and prepare purchase
    3. confirm: Show purchase details, wait for confirmation
    4. execute: Generate execute_data for Privy modal

    Features:
    - Natural language parameter extraction
    - Fiat currency detection (USD, EUR, etc.)
    - Privy on-ramp integration (MoonPay/Coinbase)
    - User modification support
    - Multi-language support
    """

    def __init__(
        self,
        llm_client: "LLMClientGateway | None" = None,
    ):
        """
        Initialize buy workflow agent.

        Args:
            llm_client: LLM client for parameter extraction
        """
        super().__init__(llm_client=llm_client)

    @property
    def agent_type(self) -> AgentType:
        return AgentType.BUY_WORKFLOW

    @property
    def workflow_name(self) -> str:
        return "BuyWorkflow"

    async def process_step(
        self,
        message: MessageContent,
        state: WorkflowState,
        user_context: UserContext,
    ) -> tuple[str, WorkflowState]:
        """Process buy workflow step."""

        step = state.step
        language = user_context.language
        text_lower = message.value.lower().strip()

        logger.info(
            f"[BuyWorkflow] Processing step={step}, message={message.value[:50]}..."
        )

        # Check if user wants to start a NEW buy flow (restart detection)
        # This resets state when user says "buy crypto", "buy", "purchase", etc.
        # while already in an ongoing flow (FETCH_DATA, CONFIRM, or EXECUTE step)
        if step not in (
            WorkflowStep.PARSE_REQUEST.value,
            WorkflowStep.CANCELLED.value,
            WorkflowStep.COMPLETED.value,
        ):
            restart_keywords = [
                "buy crypto",
                "buy usdc",
                "purchase crypto",
                "purchase usdc",
                "comprar cripto",
                "comprar usdc",
                "i want to buy",
                "quiero comprar",
            ]
            # Also detect simple "buy" at start of message (but not "buy $100" which is amount input)
            is_simple_buy = text_lower in (
                "buy",
                "buy crypto",
                "comprar",
                "comprar cripto",
                "purchase",
            )
            is_restart_request = (
                any(kw in text_lower for kw in restart_keywords) or is_simple_buy
            )

            if is_restart_request:
                logger.info(
                    f"[BuyWorkflow] Restart detected - user starting new buy flow, resetting state"
                )
                # Reset state completely for a fresh start
                state = WorkflowState()
                state.step = WorkflowStep.PARSE_REQUEST.value
                return await self._handle_parse_request(message, state, user_context)

        # Step 1: Parse request
        if step == WorkflowStep.PARSE_REQUEST.value:
            return await self._handle_parse_request(message, state, user_context)

        # Step 2: Validate
        if step == WorkflowStep.FETCH_DATA.value:
            return await self._handle_validate(message, state, user_context)

        # Step 3: Confirm
        if step == WorkflowStep.CONFIRM.value:
            return await self._handle_confirm(message, state, user_context)

        # Step 4: Execute
        if step == WorkflowStep.EXECUTE.value:
            return await self._handle_execute(message, state, user_context)

        # Unknown step - reset
        logger.warning(f"[BuyWorkflow] Unknown step: {step}")
        state.step = WorkflowStep.PARSE_REQUEST.value
        return await self._handle_parse_request(message, state, user_context)

    # ========================================
    # Step Handlers
    # ========================================

    async def _handle_parse_request(
        self,
        message: MessageContent,
        state: WorkflowState,
        user_context: UserContext,
    ) -> tuple[str, WorkflowState]:
        """Parse buy request from user message."""

        language = user_context.language
        text = message.value.lower()

        # Check if we already have parameters from previous state (workflow continuation)
        existing_crypto = state.data.get("crypto")
        existing_amount = state.data.get("amount")
        existing_fiat = state.data.get("fiat", "USD")

        logger.info(
            f"[BuyWorkflow] Parse request - existing_crypto={existing_crypto}, existing_amount={existing_amount}, message={text[:30]}"
        )

        # If we already have both crypto and amount from state, proceed to validate
        if existing_crypto and existing_amount:
            logger.info(
                f"[BuyWorkflow] Using existing parameters from state, proceeding to validate"
            )
            state.step = WorkflowStep.FETCH_DATA.value
            return await self._handle_validate(message, state, user_context)

        # Try to extract parameters from current message
        params = await self._extract_buy_params(text)

        # Merge with existing state (new params take precedence)
        # Only use extracted params if they are explicitly found (not None/empty)
        crypto = params.get("crypto") if params.get("crypto") else existing_crypto
        amount = params.get("amount") if params.get("amount") else existing_amount
        fiat = params.get("fiat") if params.get("fiat") else existing_fiat

        # Check if user requested an unsupported crypto
        unsupported_crypto = params.get("unsupported_crypto")
        if unsupported_crypto:
            logger.info(
                f"[BuyWorkflow] User requested unsupported crypto: {unsupported_crypto}"
            )
            return self._format_usdc_only_message(unsupported_crypto, language), state

        # If we have crypto and amount, proceed to validate
        if crypto and amount:
            state.data["crypto"] = crypto.upper()
            state.data["amount"] = amount
            state.data["fiat"] = fiat.upper() if fiat else "USD"
            state.step = WorkflowStep.FETCH_DATA.value
            logger.info(
                f"[BuyWorkflow] Parameters complete: {crypto} {amount} {fiat}, proceeding to validate"
            )
            return await self._handle_validate(message, state, user_context)

        # If we have crypto but no amount, ask for amount
        if crypto and not amount:
            state.data["crypto"] = crypto.upper()
            state.data["fiat"] = fiat.upper() if fiat else "USD"
            logger.info(f"[BuyWorkflow] Have crypto={crypto}, asking for amount")
            return self._ask_for_amount(state.data, language), state

        # If we have amount but no crypto, default to USDC (only supported option)
        if amount and not crypto:
            state.data["amount"] = amount
            state.data["crypto"] = "USDC"
            state.data["fiat"] = fiat.upper() if fiat else "USD"
            state.step = WorkflowStep.FETCH_DATA.value
            logger.info(f"[BuyWorkflow] Have amount={amount}, defaulting to USDC")
            return await self._handle_validate(message, state, user_context)

        # No parameters detected - ask for amount directly (USDC is the only option)
        logger.info(f"[BuyWorkflow] No parameters detected, asking for USDC amount")
        state.data["crypto"] = "USDC"
        state.data["fiat"] = fiat.upper() if fiat else "USD"
        return self._ask_for_usdc_amount(language), state

    async def _handle_validate(
        self,
        message: MessageContent,
        state: WorkflowState,
        user_context: UserContext,
    ) -> tuple[str, WorkflowState]:
        """Validate buy parameters."""

        language = user_context.language
        crypto = state.data.get("crypto", "ETH")
        amount = state.data.get("amount", "0")
        fiat = state.data.get("fiat", "USD")

        # Validate crypto
        if crypto.lower() not in SUPPORTED_CRYPTOS:
            response = self._format_unsupported_crypto(crypto, language)
            state.data["crypto"] = None  # Clear invalid crypto
            return response, state

        # Validate fiat
        if fiat not in SUPPORTED_FIATS:
            fiat = "USD"
            state.data["fiat"] = fiat

        state.step = WorkflowStep.CONFIRM.value

        # Build execute_data
        state.execute_data = self._build_buy_execute_data(
            crypto=crypto,
            amount=amount,
            fiat=fiat,
            wallet_address=user_context.wallet_address,
        )

        # Format confirmation response
        response = self._format_buy_review(
            state.data,
            language,
        )

        return response, state

    async def _handle_confirm(
        self,
        message: MessageContent,
        state: WorkflowState,
        user_context: UserContext,
    ) -> tuple[str, WorkflowState]:
        """Handle user confirmation or modification."""

        language = user_context.language
        text = message.value.lower().strip()

        # Check for confirmation
        if self._is_confirmation(text):
            state.confirmed = True
            state.step = WorkflowStep.EXECUTE.value
            return self._format_ready_to_execute(state.data, language), state

        # Check for modification BEFORE cancellation (fixes "change" triggering cancellation)
        modification = await self._parse_modification(text)
        if modification:
            if modification.get("amount"):
                state.data["amount"] = modification["amount"]
            if modification.get("crypto"):
                state.data["crypto"] = modification["crypto"].upper()
            if modification.get("fiat"):
                state.data["fiat"] = modification["fiat"].upper()

            # Rebuild execute_data
            state.execute_data = self._build_buy_execute_data(
                crypto=state.data.get("crypto", "ETH"),
                amount=state.data.get("amount", "0"),
                fiat=state.data.get("fiat", "USD"),
                wallet_address=user_context.wallet_address,
            )

            # Show updated review
            response = self._format_buy_review(state.data, language)
            return response, state

        # Check for cancellation AFTER modification
        if self._is_cancellation(text):
            state.cancelled = True
            state.step = WorkflowStep.CANCELLED.value
            return self._format_cancelled(language), state

        # Unclear response - ask again
        return self._ask_for_confirmation(language), state

    async def _handle_execute(
        self,
        message: MessageContent,
        state: WorkflowState,
        user_context: UserContext,
    ) -> tuple[str, WorkflowState]:
        """Handle execute step - Privy modal is opened by frontend."""

        language = user_context.language

        # The actual purchase is handled by Privy modal on frontend
        state.step = WorkflowStep.COMPLETED.value

        return self._format_execution_pending(state.data, language), state

    # ========================================
    # Parameter Extraction
    # ========================================

    async def _extract_buy_params(self, text: str) -> dict[str, Any]:
        """Extract buy parameters from text.

        Returns only explicitly found parameters. Does NOT default values.
        This prevents hallucination of parameters that weren't provided.

        Note: Only USDC is supported for purchase. If user requests other crypto,
        we return unsupported_crypto field to show a friendly redirect message.
        """

        params: dict[str, Any] = {}

        # Regex fallback for amount (with currency symbols)
        # Only match if there's an explicit amount in the text
        if not params.get("amount"):
            # Match: $100, 100 dollars, 100 USD, €50, etc.
            # Also match: "buy 1 btc" -> extract the amount
            amount_match = re.search(
                r"(?:[\$€£])?(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:dollars?|usd|eur|gbp)?",
                text,
                re.I,
            )
            if amount_match:
                amount_value = amount_match.group(1).replace(",", "")
                params["amount"] = amount_value

        # Detect fiat currency (only if explicitly mentioned)
        if not params.get("fiat"):
            if "$" in text or "dollar" in text or "usd" in text:
                params["fiat"] = "USD"
            elif "€" in text or "euro" in text or "eur" in text:
                params["fiat"] = "EUR"
            elif "£" in text or "pound" in text or "gbp" in text:
                params["fiat"] = "GBP"

        # Check for USDC (only supported crypto)
        if re.search(r"\busdc\b", text, re.I):
            params["crypto"] = "USDC"
        else:
            # Check for unsupported cryptos to provide helpful redirect
            for key, info in UNSUPPORTED_CRYPTOS.items():
                if re.search(rf"\b{re.escape(key)}\b", text, re.I) or re.search(
                    rf"\b{re.escape(info['symbol'].lower())}\b", text, re.I
                ):
                    params["unsupported_crypto"] = info["symbol"]
                    break

        logger.info(f"[BuyWorkflow] Extracted params: {params}")
        return params

    async def _parse_modification(self, text: str) -> dict[str, Any] | None:
        """Parse modification request from user."""

        modification: dict[str, Any] = {}

        # Check for amount modification
        amount_match = re.search(
            r"(?:change|update|make it|use)\s+(?:to\s+)?(?:[\$€£])?(\d+(?:,\d{3})*(?:\.\d+)?)",
            text,
            re.I,
        )
        if amount_match:
            modification["amount"] = amount_match.group(1).replace(",", "")

        # Check for crypto change
        for key, info in SUPPORTED_CRYPTOS.items():
            if key in text or info["symbol"].lower() in text:
                modification["crypto"] = info["symbol"]
                break

        return modification if modification else None

    # ========================================
    # Response Formatting
    # ========================================

    def _format_usdc_only_message(self, requested_crypto: str, language: str) -> str:
        """Format message when user requests unsupported crypto."""

        msgs = {
            "en": f"""💡 **USDC Only Available**

I see you want to buy **{requested_crypto}**, but currently only **USDC** is available for direct purchase.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Here's a tip:** You can buy USDC first, then swap it for {requested_crypto} instantly!

Would you like to buy USDC instead?

💬 Just tell me how much (e.g., "$100" or "500 dollars")""",
            "es": f"""💡 **Solo USDC Disponible**

Veo que quieres comprar **{requested_crypto}**, pero actualmente solo **USDC** está disponible para compra directa.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Un consejo:** ¡Puedes comprar USDC primero y luego cambiarlo por {requested_crypto} al instante!

¿Te gustaría comprar USDC en su lugar?

💬 Solo dime cuánto (ej: "$100" o "500 dólares")""",
            "pt": f"""💡 **Apenas USDC Disponível**

Vejo que você quer comprar **{requested_crypto}**, mas atualmente apenas **USDC** está disponível para compra direta.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Uma dica:** Você pode comprar USDC primeiro e depois trocar por {requested_crypto} instantaneamente!

Gostaria de comprar USDC em vez disso?

💬 Apenas me diga quanto (ex: "$100" ou "500 dólares")""",
            "zh": f"""💡 **仅支持 USDC**

我看到您想购买 **{requested_crypto}**，但目前只有 **USDC** 可以直接购买。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**小贴士：** 您可以先购买 USDC，然后立即将其兑换成 {requested_crypto}！

您想改为购买 USDC 吗？

💬 告诉我您想要多少（例如："$100" 或 "500美元"）""",
        }

        return msgs.get(language, msgs["en"])

    def _ask_for_usdc_amount(self, language: str) -> str:
        """Ask user how much USDC they want to buy."""

        msgs = {
            "en": """💵 **Buy USDC**

How much USDC would you like to buy?

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**USDC** is a stablecoin pegged 1:1 to the US Dollar - perfect for:
• 🔄 Swapping to other cryptos (ETH, BTC, SOL...)
• 💰 Earning yield in DeFi
• 📤 Sending to friends

💬 Enter the amount in USD (e.g., "100" or "$500")

💡 *Minimum: $30*""",
            "es": """💵 **Comprar USDC**

¿Cuánto USDC te gustaría comprar?

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**USDC** es una stablecoin con paridad 1:1 al dólar - perfecta para:
• 🔄 Intercambiar por otras criptos (ETH, BTC, SOL...)
• 💰 Ganar rendimiento en DeFi
• 📤 Enviar a amigos

💬 Ingresa la cantidad en USD (ej: "100" o "$500")

💡 *Mínimo: $30*""",
            "pt": """💵 **Comprar USDC**

Quanto USDC você gostaria de comprar?

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**USDC** é uma stablecoin com paridade 1:1 ao dólar - perfeita para:
• 🔄 Trocar por outras criptos (ETH, BTC, SOL...)
• 💰 Ganhar rendimento em DeFi
• 📤 Enviar para amigos

💬 Digite o valor em USD (ex: "100" ou "$500")

💡 *Mínimo: $30*""",
            "zh": """💵 **购买 USDC**

您想购买多少 USDC？

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**USDC** 是与美元 1:1 挂钩的稳定币 - 非常适合：
• 🔄 兑换其他加密货币（ETH、BTC、SOL...）
• 💰 在 DeFi 中赚取收益
• 📤 发送给朋友

💬 输入美元金额（例如："100" 或 "$500"）

💡 *最低：$30*""",
        }

        return msgs.get(language, msgs["en"])

    def _show_buy_menu(self, language: str) -> str:
        """Show buy crypto menu (USDC only)."""

        # Redirect to ask for USDC amount
        return self._ask_for_usdc_amount(language)

    def _ask_for_amount(self, data: dict[str, Any], language: str) -> str:
        """Ask user for purchase amount."""

        crypto = data.get("crypto", "ETH")
        crypto_info = SUPPORTED_CRYPTOS.get(crypto.lower(), {"emoji": "💎"})
        emoji = crypto_info.get("emoji", "💎")

        msgs = {
            "en": f"""{emoji} **Buy {crypto}**

How much would you like to spend?

💡 *Examples:*
• `$50` (fifty dollars)
• `$100` (one hundred dollars)
• `$500` (five hundred dollars)

💬 Enter the amount in USD""",
            "es": f"""{emoji} **Comprar {crypto}**

¿Cuánto te gustaría gastar?

💡 *Ejemplos:*
• `$50` (cincuenta dólares)
• `$100` (cien dólares)
• `$500` (quinientos dólares)

💬 Ingresa la cantidad en USD""",
            "pt": f"""{emoji} **Comprar {crypto}**

Quanto você gostaria de gastar?

💡 *Exemplos:*
• `$50` (cinquenta dólares)
• `$100` (cem dólares)
• `$500` (quinhentos dólares)

💬 Digite a quantia em USD""",
            "zh": f"""{emoji} **购买 {crypto}**

您想花多少钱？

💡 *示例：*
• `$50` (五十美元)
• `$100` (一百美元)
• `$500` (五百美元)

💬 输入美元金额""",
        }

        return msgs.get(language, msgs["en"])

    def _ask_for_crypto_first(self, language: str) -> str:
        """Ask user which crypto to buy first (USDC only - redirect to amount)."""
        # Since only USDC is available, skip crypto selection
        return self._ask_for_usdc_amount(language)

    def _ask_for_crypto(self, data: dict[str, Any], language: str) -> str:
        """Ask user which crypto to buy (USDC only - auto-select and proceed)."""
        # Since only USDC is available, auto-select and ask for amount
        data["crypto"] = "USDC"
        return self._ask_for_amount(data, language)

    def _format_unsupported_crypto(self, crypto: str, language: str) -> str:
        """Format unsupported crypto error message - redirect to USDC."""
        # Use the same message as _format_usdc_only_message
        return self._format_usdc_only_message(crypto, language)

    def _format_buy_review(
        self,
        data: dict[str, Any],
        language: str,
    ) -> str:
        """Format buy review for confirmation."""

        crypto = data.get("crypto", "USDC")
        amount = data.get("amount", "0")
        fiat = data.get("fiat", "USD")

        crypto_info = SUPPORTED_CRYPTOS.get(crypto.lower(), {"emoji": "💵"})
        emoji = crypto_info.get("emoji", "💵")

        # Format fiat amount with currency symbol
        currency_symbols = {
            "USD": "$",
            "EUR": "€",
            "GBP": "£",
            "CAD": "C$",
            "AUD": "A$",
        }
        symbol = currency_symbols.get(fiat, "$")

        msgs = {
            "en": f"""💳 **Review Your Purchase**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 **Buying:** {crypto} {emoji}
💵 **Amount:** {symbol}{amount} {fiat}
🌐 **Network:** Base

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Payment Options:**
• Credit/Debit Card
• Apple Pay / Google Pay""",
            "es": f"""💳 **Revisa Tu Compra**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 **Comprando:** {crypto} {emoji}
💵 **Cantidad:** {symbol}{amount} {fiat}
🌐 **Red:** Base

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Opciones de Pago:**
• Tarjeta de Crédito/Débito
• Apple Pay / Google Pay""",
            "pt": f"""💳 **Revise Sua Compra**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 **Comprando:** {crypto} {emoji}
💵 **Valor:** {symbol}{amount} {fiat}
🌐 **Rede:** Base

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Opções de Pagamento:**
• Cartão de Crédito/Débito
• Apple Pay / Google Pay""",
            "zh": f"""💳 **审核您的购买**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 **购买：** {crypto} {emoji}
💵 **金额：** {symbol}{amount} {fiat}
🌐 **网络：** Base

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**支付方式：**
• 信用卡/借记卡
• Apple Pay / Google Pay""",
        }

        return msgs.get(language, msgs["en"])

    def _ask_for_confirmation(self, language: str) -> str:
        """Ask user to confirm (not used - frontend handles via execute_data card)."""

        msgs = {
            "en": "Review the purchase details above.",
            "es": "Revisa los detalles de la compra.",
            "pt": "Revise os detalhes da compra.",
            "zh": "查看上方的购买详情。",
        }

        return msgs.get(language, msgs["en"])

    def _format_ready_to_execute(
        self,
        data: dict[str, Any],
        language: str,
    ) -> str:
        """Format ready-to-execute message."""

        crypto = data.get("crypto", "ETH")
        amount = data.get("amount", "0")
        fiat = data.get("fiat", "USD")

        currency_symbols = {"USD": "$", "EUR": "€", "GBP": "£"}
        symbol = currency_symbols.get(fiat, "$")

        crypto_info = SUPPORTED_CRYPTOS.get(crypto.lower(), {"emoji": "💎"})
        emoji = crypto_info.get("emoji", "💎")

        msgs = {
            "en": f"""✅ **Purchase Ready**

💳 **Buying:** {symbol}{amount} of {crypto} {emoji}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

The payment window will open now.
Complete your purchase via MoonPay or Coinbase.""",
            "es": f"""✅ **Compra Lista**

💳 **Comprando:** {symbol}{amount} de {crypto} {emoji}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

La ventana de pago se abrirá ahora.
Completa tu compra vía MoonPay o Coinbase.""",
            "pt": f"""✅ **Compra Pronta**

💳 **Comprando:** {symbol}{amount} de {crypto} {emoji}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

A janela de pagamento abrirá agora.
Complete sua compra via MoonPay ou Coinbase.""",
            "zh": f"""✅ **购买准备就绪**

💳 **购买：** {symbol}{amount} 的 {crypto} {emoji}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

支付窗口将立即打开。
通过 MoonPay 或 Coinbase 完成购买。""",
        }

        return msgs.get(language, msgs["en"])

    def _format_cancelled(self, language: str) -> str:
        """Format cancellation message."""

        msgs = {
            "en": "❌ Purchase cancelled. Let me know if you'd like to buy crypto later!",
            "es": "❌ Compra cancelada. ¡Avísame si quieres comprar cripto más tarde!",
            "pt": "❌ Compra cancelada. Me avise se quiser comprar cripto depois!",
            "zh": "❌ 购买已取消。如果您以后想购买加密货币，请告诉我！",
        }

        return msgs.get(language, msgs["en"])

    def _format_execution_pending(
        self,
        data: dict[str, Any],
        language: str,
    ) -> str:
        """Format message while waiting for payment."""

        crypto = data.get("crypto", "ETH")
        amount = data.get("amount", "0")

        msgs = {
            "en": f"""⏳ **Opening Payment...** 

Buying **${amount}** of **{crypto}**

Complete the payment in the modal that appears.
Your crypto will arrive in your wallet shortly after payment!""",
            "es": f"""⏳ **Abriendo Pago...**

Comprando **${amount}** de **{crypto}**

Completa el pago en el modal que aparece.
¡Tu cripto llegará a tu wallet poco después del pago!""",
            "pt": f"""⏳ **Abrindo Pagamento...**

Comprando **${amount}** de **{crypto}**

Complete o pagamento no modal que aparecer.
Sua cripto chegará na sua carteira logo após o pagamento!""",
            "zh": f"""⏳ **正在打开支付...**

购买 **${amount}** 的 **{crypto}**

在出现的弹窗中完成支付。
支付后您的加密货币将很快到达您的钱包！""",
        }

        return msgs.get(language, msgs["en"])

    # ========================================
    # Execute Data Builder
    # ========================================

    def _build_buy_execute_data(
        self,
        crypto: str,
        amount: str,
        fiat: str,
        wallet_address: str | None,
    ) -> dict[str, Any]:
        """Build execute_data for buy action.

        Uses standard ExecuteActionData fields for API consistency:
        - to_token: The crypto being purchased
        - amount: The fiat amount to spend
        - from_token: The fiat currency (USD, EUR, etc.)
        """

        return {
            "action_type": "buy",
            "provider": "privy",
            "chain": "base",
            # Standard fields for ExecuteActionData compatibility
            "to_token": crypto.upper(),  # Crypto being purchased
            "amount": str(amount),  # Fiat amount
            "from_token": fiat.upper(),  # Fiat currency (USD, EUR)
            # Buy-specific metadata
            "recipient": wallet_address,  # Destination wallet
            "quote_id": f"buy-{crypto.lower()}-{amount}",
        }

    # ========================================
    # Helpers
    # ========================================

    def _is_confirmation(self, text: str) -> bool:
        """Check if text is a confirmation."""
        confirm_words = [
            "yes",
            "y",
            "confirm",
            "ok",
            "proceed",
            "continue",
            "do it",
            "buy",
            "sí",
            "si",
            "confirmar",
            "vale",
            "continuar",
            "comprar",
            "sim",
            "confirmar",
            "prosseguir",
            "是",
            "确认",
            "好",
            "继续",
            "购买",
        ]
        return any(word in text for word in confirm_words)

    def _is_cancellation(self, text: str) -> bool:
        """Check if text is a cancellation using word boundary matching."""
        import re

        # Single-character and exact-match words (use word boundaries)
        cancel_patterns = [
            r"\bno\b",
            r"\bn\b",
            r"\bcancel\b",
            r"\babort\b",
            r"\bstop\b",
            r"\bnevermind\b",
            r"\bforget it\b",
            r"\bcancelar\b",
            r"\babortar\b",
            r"\bparar\b",
        ]

        # Check word boundary patterns
        if any(re.search(pattern, text) for pattern in cancel_patterns):
            return True

        # For CJK characters (no word boundaries), use exact substring matching
        cjk_cancel_words = ["取消", "不", "停止"]
        return any(word in text for word in cjk_cancel_words)
