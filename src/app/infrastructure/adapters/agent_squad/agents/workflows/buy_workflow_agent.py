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


# Supported cryptocurrencies for purchase
SUPPORTED_CRYPTOS = {
    "eth": {"symbol": "ETH", "name": "Ethereum", "emoji": "Ξ"},
    "usdc": {"symbol": "USDC", "name": "USD Coin", "emoji": "💵"},
    "usdt": {"symbol": "USDT", "name": "Tether", "emoji": "💵"},
    "btc": {"symbol": "BTC", "name": "Bitcoin", "emoji": "₿"},
    "matic": {"symbol": "MATIC", "name": "Polygon", "emoji": "🟣"},
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
        
        logger.info(f"[BuyWorkflow] Processing step={step}, message={message.value[:50]}...")
        
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
        
        # Try to extract parameters from message
        params = await self._extract_buy_params(text)
        
        crypto = params.get("crypto")
        amount = params.get("amount")
        fiat = params.get("fiat", "USD")
        
        # If we have crypto and amount, proceed to validate
        if crypto and amount:
            state.data["crypto"] = crypto.upper()
            state.data["amount"] = amount
            state.data["fiat"] = fiat.upper()
            state.step = WorkflowStep.FETCH_DATA.value
            return await self._handle_validate(message, state, user_context)
        
        # If we have crypto but no amount, ask for amount
        if crypto and not amount:
            state.data["crypto"] = crypto.upper()
            state.data["fiat"] = fiat.upper()
            return self._ask_for_amount(state.data, language), state
        
        # If we have amount but no crypto, ask for crypto
        if amount and not crypto:
            state.data["amount"] = amount
            state.data["fiat"] = fiat.upper()
            return self._ask_for_crypto(state.data, language), state
        
        # No parameters detected - show buy menu
        return self._show_buy_menu(language), state
    
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
        
        # Check for cancellation
        if self._is_cancellation(text):
            state.cancelled = True
            state.step = WorkflowStep.CANCELLED.value
            return self._format_cancelled(language), state
        
        # Check for modification
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
        """Extract buy parameters from text."""
        
        params: dict[str, Any] = {}
        
        # Try LLM extraction first
        if self._llm_client:
            try:
                llm_params = await self._llm_extract_params(
                    text,
                    param_schema={
                        "crypto": "Cryptocurrency to buy (ETH, USDC, BTC, etc.)",
                        "amount": "Fiat amount to spend (numeric value)",
                        "fiat": "Fiat currency (USD, EUR, GBP, etc.)",
                    },
                )
                if llm_params:
                    params.update(llm_params)
            except Exception as e:
                logger.warning(f"[BuyWorkflow] LLM extraction failed: {e}")
        
        # Regex fallback for amount (with currency symbols)
        if not params.get("amount"):
            # Match: $100, 100 dollars, 100 USD, €50, etc.
            amount_match = re.search(
                r"(?:[\$€£])?(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:dollars?|usd|eur|gbp)?",
                text,
                re.I,
            )
            if amount_match:
                params["amount"] = amount_match.group(1).replace(",", "")
        
        # Detect fiat currency
        if not params.get("fiat"):
            if "$" in text or "dollar" in text or "usd" in text:
                params["fiat"] = "USD"
            elif "€" in text or "euro" in text or "eur" in text:
                params["fiat"] = "EUR"
            elif "£" in text or "pound" in text or "gbp" in text:
                params["fiat"] = "GBP"
            else:
                params["fiat"] = "USD"  # Default
        
        # Regex fallback for crypto
        if not params.get("crypto"):
            for key, info in SUPPORTED_CRYPTOS.items():
                if key in text or info["symbol"].lower() in text:
                    params["crypto"] = info["symbol"]
                    break
        
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
    
    def _show_buy_menu(self, language: str) -> str:
        """Show buy crypto menu."""
        
        msgs = {
            "en": """💳 **Buy Crypto**

Purchase cryptocurrency with card, Apple Pay, or Google Pay.

**Available Cryptocurrencies:**
• Ξ **ETH** (Ethereum)
• 💵 **USDC** (USD Coin)
• 💵 **USDT** (Tether)
• ₿ **BTC** (Bitcoin)

**Supported Payment Methods:**
• Credit/Debit Card
• Apple Pay
• Google Pay
• Bank Transfer

💬 Tell me what you'd like to buy (e.g., "buy $100 of ETH")""",
            
            "es": """💳 **Comprar Cripto**

Compra criptomonedas con tarjeta, Apple Pay o Google Pay.

**Criptomonedas Disponibles:**
• Ξ **ETH** (Ethereum)
• 💵 **USDC** (USD Coin)
• 💵 **USDT** (Tether)
• ₿ **BTC** (Bitcoin)

**Métodos de Pago Soportados:**
• Tarjeta de Crédito/Débito
• Apple Pay
• Google Pay
• Transferencia Bancaria

💬 Dime qué te gustaría comprar (ej: "comprar $100 de ETH")""",
            
            "pt": """💳 **Comprar Cripto**

Compre criptomoedas com cartão, Apple Pay ou Google Pay.

**Criptomoedas Disponíveis:**
• Ξ **ETH** (Ethereum)
• 💵 **USDC** (USD Coin)
• 💵 **USDT** (Tether)
• ₿ **BTC** (Bitcoin)

**Métodos de Pagamento Suportados:**
• Cartão de Crédito/Débito
• Apple Pay
• Google Pay
• Transferência Bancária

💬 Me diga o que você gostaria de comprar (ex: "comprar $100 de ETH")""",
            
            "zh": """💳 **购买加密货币**

使用银行卡、Apple Pay 或 Google Pay 购买加密货币。

**可用加密货币：**
• Ξ **ETH** (以太坊)
• 💵 **USDC** (USD Coin)
• 💵 **USDT** (Tether)
• ₿ **BTC** (比特币)

**支持的支付方式：**
• 信用卡/借记卡
• Apple Pay
• Google Pay
• 银行转账

💬 告诉我您想购买什么（例如："购买 $100 的 ETH"）""",
        }
        
        return msgs.get(language, msgs["en"])
    
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
    
    def _ask_for_crypto(self, data: dict[str, Any], language: str) -> str:
        """Ask user which crypto to buy."""
        
        amount = data.get("amount", "0")
        fiat = data.get("fiat", "USD")
        
        msgs = {
            "en": f"""💳 **Buying ${amount} {fiat} of Crypto**

Which cryptocurrency would you like to buy?

**Available:**
1. Ξ **ETH** (Ethereum)
2. 💵 **USDC** (USD Coin)
3. 💵 **USDT** (Tether)
4. ₿ **BTC** (Bitcoin)

💬 Reply with the crypto name (e.g., "ETH")""",
            
            "es": f"""💳 **Comprando ${amount} {fiat} de Cripto**

¿Qué criptomoneda te gustaría comprar?

**Disponibles:**
1. Ξ **ETH** (Ethereum)
2. 💵 **USDC** (USD Coin)
3. 💵 **USDT** (Tether)
4. ₿ **BTC** (Bitcoin)

💬 Responde con el nombre de la cripto (ej: "ETH")""",
            
            "pt": f"""💳 **Comprando ${amount} {fiat} de Cripto**

Qual criptomoeda você gostaria de comprar?

**Disponíveis:**
1. Ξ **ETH** (Ethereum)
2. 💵 **USDC** (USD Coin)
3. 💵 **USDT** (Tether)
4. ₿ **BTC** (Bitcoin)

💬 Responda com o nome da cripto (ex: "ETH")""",
            
            "zh": f"""💳 **购买 ${amount} {fiat} 的加密货币**

您想购买哪种加密货币？

**可用：**
1. Ξ **ETH** (以太坊)
2. 💵 **USDC** (USD Coin)
3. 💵 **USDT** (Tether)
4. ₿ **BTC** (比特币)

💬 回复加密货币名称（例如："ETH"）""",
        }
        
        return msgs.get(language, msgs["en"])
    
    def _format_unsupported_crypto(self, crypto: str, language: str) -> str:
        """Format unsupported crypto error message."""
        
        msgs = {
            "en": f"""❌ **Unsupported Cryptocurrency**

Sorry, **{crypto}** is not available for purchase.

**You can buy:**
• ETH • USDC • USDT • BTC

Please select one of these cryptocurrencies.""",
            
            "es": f"""❌ **Criptomoneda No Soportada**

Lo siento, **{crypto}** no está disponible para compra.

**Puedes comprar:**
• ETH • USDC • USDT • BTC

Por favor selecciona una de estas criptomonedas.""",
            
            "pt": f"""❌ **Criptomoeda Não Suportada**

Desculpe, **{crypto}** não está disponível para compra.

**Você pode comprar:**
• ETH • USDC • USDT • BTC

Por favor selecione uma dessas criptomoedas.""",
            
            "zh": f"""❌ **不支持的加密货币**

抱歉，**{crypto}** 不可购买。

**您可以购买：**
• ETH • USDC • USDT • BTC

请选择其中一种加密货币。""",
        }
        
        return msgs.get(language, msgs["en"])
    
    def _format_buy_review(
        self,
        data: dict[str, Any],
        language: str,
    ) -> str:
        """Format buy review for confirmation."""
        
        crypto = data.get("crypto", "ETH")
        amount = data.get("amount", "0")
        fiat = data.get("fiat", "USD")
        
        crypto_info = SUPPORTED_CRYPTOS.get(crypto.lower(), {"emoji": "💎"})
        emoji = crypto_info.get("emoji", "💎")
        
        # Format fiat amount with currency symbol
        currency_symbols = {"USD": "$", "EUR": "€", "GBP": "£", "CAD": "C$", "AUD": "A$"}
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
• Apple Pay / Google Pay

**Ready to purchase?**
Reply "yes" to open payment or "cancel" to abort.
You can also modify: "change to $200" """,
            
            "es": f"""💳 **Revisa Tu Compra**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 **Comprando:** {crypto} {emoji}
💵 **Cantidad:** {symbol}{amount} {fiat}
🌐 **Red:** Base

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Opciones de Pago:**
• Tarjeta de Crédito/Débito
• Apple Pay / Google Pay

**¿Listo para comprar?**
Responde "sí" para abrir el pago o "cancelar" para abortar.
También puedes modificar: "cambiar a $200" """,
            
            "pt": f"""💳 **Revise Sua Compra**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 **Comprando:** {crypto} {emoji}
💵 **Valor:** {symbol}{amount} {fiat}
🌐 **Rede:** Base

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Opções de Pagamento:**
• Cartão de Crédito/Débito
• Apple Pay / Google Pay

**Pronto para comprar?**
Responda "sim" para abrir o pagamento ou "cancelar" para abortar.
Você também pode modificar: "alterar para $200" """,
            
            "zh": f"""💳 **审核您的购买**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 **购买：** {crypto} {emoji}
💵 **金额：** {symbol}{amount} {fiat}
🌐 **网络：** Base

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**支付方式：**
• 信用卡/借记卡
• Apple Pay / Google Pay

**准备购买了吗？**
回复'是'打开支付或'取消'中止。
您也可以修改："改为 $200" """,
        }
        
        return msgs.get(language, msgs["en"])
    
    def _ask_for_confirmation(self, language: str) -> str:
        """Ask user to confirm."""
        
        msgs = {
            "en": """Would you like to confirm this purchase? Reply "yes" or "cancel".""",
            "es": """¿Te gustaría confirmar esta compra? Responde "sí" o "cancelar".""",
            "pt": """Gostaria de confirmar esta compra? Responda "sim" ou "cancelar".""",
            "zh": """您想确认此购买吗？回复"是"或"取消"。""",
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
        """Build execute_data for buy action."""
        
        return {
            "action_type": "buy",
            "provider": "privy",
            "crypto_currency": crypto,
            "fiat_amount": amount,
            "fiat_currency": fiat,
            "wallet_address": wallet_address,
            "on_ramp_provider": "moonpay",  # or "coinbase"
            "chain": "base",
        }
    
    # ========================================
    # Helpers
    # ========================================
    
    def _is_confirmation(self, text: str) -> bool:
        """Check if text is a confirmation."""
        confirm_words = [
            "yes", "y", "confirm", "ok", "proceed", "continue", "do it", "buy",
            "sí", "si", "confirmar", "vale", "continuar", "comprar",
            "sim", "confirmar", "prosseguir",
            "是", "确认", "好", "继续", "购买",
        ]
        return any(word in text for word in confirm_words)
    
    def _is_cancellation(self, text: str) -> bool:
        """Check if text is a cancellation."""
        cancel_words = [
            "no", "n", "cancel", "abort", "stop", "nevermind", "forget it",
            "cancelar", "abortar", "parar",
            "取消", "不", "停止",
        ]
        return any(word in text for word in cancel_words)
