"""
Transfer Workflow Agent - Multi-Step Token Transfer Operations.

Handles the complete token transfer workflow for authenticated users:
1. Parse request: Extract token, amount, and recipient from user message
2. Validate recipient: Verify address format and detect network
3. Confirm: Show transfer details and wait for user confirmation
4. Execute: Generate execute_data for frontend execution

Integration:
- Address validation for EVM and Solana
- Network detection from address format
- Privy SDK for execution

Example Conversation:
    User: "send 100 USDC to 0x742d..."
    Agent: "📤 Sending 100 USDC to 0x742d...1234. Confirm?"
    User: "yes"
    Agent: "✅ Ready to send!" + execute_data for frontend modal
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


# Supported tokens for transfer
SUPPORTED_TOKENS = {
    "eth": {"symbol": "ETH", "name": "Ethereum", "emoji": "Ξ", "decimals": 18},
    "weth": {"symbol": "WETH", "name": "Wrapped Ethereum", "emoji": "Ξ", "decimals": 18},
    "usdc": {"symbol": "USDC", "name": "USD Coin", "emoji": "💵", "decimals": 6},
    "usdt": {"symbol": "USDT", "name": "Tether", "emoji": "💵", "decimals": 6},
    "dai": {"symbol": "DAI", "name": "Dai", "emoji": "💰", "decimals": 18},
    "wbtc": {"symbol": "WBTC", "name": "Wrapped Bitcoin", "emoji": "₿", "decimals": 8},
}

# Network detection by address format
NETWORK_PATTERNS = {
    "ethereum": r"^0x[a-fA-F0-9]{40}$",  # EVM addresses
    "solana": r"^[1-9A-HJ-NP-Za-km-z]{32,44}$",  # Solana addresses
    "bitcoin": r"^(bc1[a-z0-9]{39,59}|[13][a-km-zA-HJ-NP-Z1-9]{25,34})$",  # Bitcoin
}

# Chain IDs
CHAIN_IDS = {
    "ethereum": 1,
    "base": 8453,
    "polygon": 137,
    "arbitrum": 42161,
    "optimism": 10,
}


class TransferWorkflowAgent(BaseWorkflowAgent):
    """
    AGNO-based multi-step token transfer workflow agent.
    
    Steps:
    1. parse_request: Extract token, amount, recipient
    2. validate: Validate address format and detect network
    3. confirm: Show transfer details, wait for user confirmation
    4. execute: Generate execute_data for frontend
    
    Features:
    - Natural language parameter extraction
    - Multi-chain address validation
    - Network detection from address format
    - User modification support
    - Multi-language support
    """
    
    def __init__(
        self,
        llm_client: "LLMClientGateway | None" = None,
    ):
        """
        Initialize transfer workflow agent.
        
        Args:
            llm_client: LLM client for parameter extraction
        """
        super().__init__(llm_client=llm_client)
    
    @property
    def agent_type(self) -> AgentType:
        return AgentType.TRANSFER_WORKFLOW
    
    @property
    def workflow_name(self) -> str:
        return "TransferWorkflow"
    
    async def process_step(
        self,
        message: MessageContent,
        state: WorkflowState,
        user_context: UserContext,
    ) -> tuple[str, WorkflowState]:
        """Process transfer workflow step."""
        
        step = state.step
        language = user_context.language
        
        logger.info(f"[TransferWorkflow] Processing step={step}, message={message.value[:50]}...")
        
        # Step 1: Parse request
        if step == WorkflowStep.PARSE_REQUEST.value:
            return await self._handle_parse_request(message, state, user_context)
        
        # Step 2: Fetch/Validate (validate address)
        if step == WorkflowStep.FETCH_DATA.value:
            return await self._handle_validate(message, state, user_context)
        
        # Step 3: Confirm
        if step == WorkflowStep.CONFIRM.value:
            return await self._handle_confirm(message, state, user_context)
        
        # Step 4: Execute
        if step == WorkflowStep.EXECUTE.value:
            return await self._handle_execute(message, state, user_context)
        
        # Unknown step - reset
        logger.warning(f"[TransferWorkflow] Unknown step: {step}")
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
        """Parse transfer request from user message."""
        
        language = user_context.language
        text = message.value.lower()
        
        # Try to extract parameters from message
        params = await self._extract_transfer_params(text, message.value)
        
        token = params.get("token")
        amount = params.get("amount")
        recipient = params.get("recipient")
        
        # If we have all parameters, proceed to validate
        if token and amount and recipient:
            state.data["token"] = token.upper()
            state.data["amount"] = amount
            state.data["recipient"] = recipient
            state.data["chain"] = params.get("chain", "base")
            state.step = WorkflowStep.FETCH_DATA.value
            return await self._handle_validate(message, state, user_context)
        
        # If we have token and amount but no recipient, ask for recipient
        if token and amount and not recipient:
            state.data["token"] = token.upper()
            state.data["amount"] = amount
            state.data["chain"] = params.get("chain", "base")
            return self._ask_for_recipient(state.data, language), state
        
        # If we have token but no amount, ask for amount
        if token and not amount:
            state.data["token"] = token.upper()
            return self._ask_for_amount(state.data, language), state
        
        # No token detected - ask user to specify
        return self._ask_for_token(language), state
    
    async def _handle_validate(
        self,
        message: MessageContent,
        state: WorkflowState,
        user_context: UserContext,
    ) -> tuple[str, WorkflowState]:
        """Validate recipient address."""
        
        language = user_context.language
        recipient = state.data.get("recipient", "")
        
        # Validate address format
        validation = self._validate_address(recipient)
        
        if not validation["valid"]:
            # Invalid address
            response = self._format_invalid_address(recipient, language)
            state.data["recipient"] = None  # Clear invalid address
            return response, state
        
        # Store network info
        state.data["network"] = validation["network"]
        state.step = WorkflowStep.CONFIRM.value
        
        # Build execute_data
        state.execute_data = self._build_transfer_execute_data(
            token=state.data.get("token", "ETH"),
            amount=state.data.get("amount", "0"),
            recipient=recipient,
            chain=state.data.get("chain", "base"),
        )
        
        # Format confirmation response
        response = self._format_transfer_review(
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
        modification = await self._parse_modification(text, message.value)
        if modification:
            if modification.get("amount"):
                state.data["amount"] = modification["amount"]
            if modification.get("token"):
                state.data["token"] = modification["token"].upper()
            if modification.get("recipient"):
                state.data["recipient"] = modification["recipient"]
                # Re-validate new recipient
                state.step = WorkflowStep.FETCH_DATA.value
                return await self._handle_validate(message, state, user_context)
            
            # Rebuild execute_data with modifications
            state.execute_data = self._build_transfer_execute_data(
                token=state.data.get("token", "ETH"),
                amount=state.data.get("amount", "0"),
                recipient=state.data.get("recipient", ""),
                chain=state.data.get("chain", "base"),
            )
            
            # Show updated review
            response = self._format_transfer_review(state.data, language)
            return response, state
        
        # Check if user is providing a missing recipient
        potential_address = self._extract_address(message.value)
        if potential_address and not state.data.get("recipient"):
            state.data["recipient"] = potential_address
            state.step = WorkflowStep.FETCH_DATA.value
            return await self._handle_validate(message, state, user_context)
        
        # Unclear response - ask again
        return self._ask_for_confirmation(language), state
    
    async def _handle_execute(
        self,
        message: MessageContent,
        state: WorkflowState,
        user_context: UserContext,
    ) -> tuple[str, WorkflowState]:
        """Handle execute step - transaction is done by frontend."""
        
        language = user_context.language
        
        # The actual transaction is handled by the frontend using execute_data
        state.step = WorkflowStep.COMPLETED.value
        
        return self._format_execution_pending(state.data, language), state
    
    # ========================================
    # Parameter Extraction
    # ========================================
    
    async def _extract_transfer_params(
        self,
        text: str,
        original_text: str,
    ) -> dict[str, Any]:
        """Extract transfer parameters from text."""
        
        params: dict[str, Any] = {}
        
        # Try LLM extraction first
        if self._llm_client:
            try:
                llm_params = await self._llm_extract_params(
                    text,
                    param_schema={
                        "token": "Token symbol to transfer (ETH, USDC, DAI, etc.)",
                        "amount": "Amount to transfer (numeric value)",
                        "recipient": "Recipient wallet address (0x... or Solana format)",
                        "chain": "Blockchain network (base, ethereum, etc.)",
                    },
                )
                if llm_params:
                    params.update(llm_params)
            except Exception as e:
                logger.warning(f"[TransferWorkflow] LLM extraction failed: {e}")
        
        # Regex fallback for amount
        if not params.get("amount"):
            amount_match = re.search(
                r"(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:eth|usdc|usdt|dai|wbtc)?",
                text,
                re.I,
            )
            if amount_match:
                params["amount"] = amount_match.group(1).replace(",", "")
        
        # Regex fallback for token
        if not params.get("token"):
            for key, info in SUPPORTED_TOKENS.items():
                if key in text or info["symbol"].lower() in text:
                    params["token"] = info["symbol"]
                    break
        
        # Regex fallback for recipient address
        if not params.get("recipient"):
            address = self._extract_address(original_text)
            if address:
                params["recipient"] = address
        
        # Default chain
        if not params.get("chain"):
            params["chain"] = "base"
        
        return params
    
    def _extract_address(self, text: str) -> str | None:
        """Extract wallet address from text."""
        
        # Ethereum/EVM address (0x + 40 hex chars)
        eth_match = re.search(r"(0x[a-fA-F0-9]{40})", text)
        if eth_match:
            return eth_match.group(1)
        
        # Solana address (base58, 32-44 chars)
        sol_match = re.search(r"\b([1-9A-HJ-NP-Za-km-z]{32,44})\b", text)
        if sol_match:
            return sol_match.group(1)
        
        return None
    
    def _validate_address(self, address: str) -> dict[str, Any]:
        """Validate wallet address format."""
        
        if not address:
            return {"valid": False, "network": None, "error": "No address provided"}
        
        # Check EVM format
        if re.match(NETWORK_PATTERNS["ethereum"], address):
            return {"valid": True, "network": "ethereum", "error": None}
        
        # Check Solana format
        if re.match(NETWORK_PATTERNS["solana"], address):
            return {"valid": True, "network": "solana", "error": None}
        
        # Check Bitcoin format
        if re.match(NETWORK_PATTERNS["bitcoin"], address):
            return {"valid": True, "network": "bitcoin", "error": None}
        
        return {"valid": False, "network": None, "error": "Invalid address format"}
    
    async def _parse_modification(
        self,
        text: str,
        original_text: str,
    ) -> dict[str, Any] | None:
        """Parse modification request from user."""
        
        modification: dict[str, Any] = {}
        
        # Check for amount modification
        amount_match = re.search(
            r"(?:change|update|make it|use)\s+(?:to\s+)?(\d+(?:,\d{3})*(?:\.\d+)?)",
            text,
            re.I,
        )
        if amount_match:
            modification["amount"] = amount_match.group(1).replace(",", "")
        
        # Check for token change
        for key, info in SUPPORTED_TOKENS.items():
            if key in text or info["symbol"].lower() in text:
                modification["token"] = info["symbol"]
                break
        
        # Check for recipient change
        address_match = self._extract_address(original_text)
        if address_match and "address" in text.lower():
            modification["recipient"] = address_match
        
        return modification if modification else None
    
    # ========================================
    # Response Formatting
    # ========================================
    
    def _ask_for_token(self, language: str) -> str:
        """Ask user which token to send."""
        
        msgs = {
            "en": """📤 **Send Crypto to Another Wallet**

Which token would you like to send?

**Available Tokens:**
1. Ξ **ETH** (Ethereum)
2. 💵 **USDC** (USD Coin)
3. 💵 **USDT** (Tether)
4. 💰 **DAI** (Dai)
5. ₿ **WBTC** (Wrapped Bitcoin)

💬 Reply with the token name and amount (e.g., "100 USDC")""",
            
            "es": """📤 **Enviar Cripto a Otra Billetera**

¿Qué token te gustaría enviar?

**Tokens Disponibles:**
1. Ξ **ETH** (Ethereum)
2. 💵 **USDC** (USD Coin)
3. 💵 **USDT** (Tether)
4. 💰 **DAI** (Dai)
5. ₿ **WBTC** (Wrapped Bitcoin)

💬 Responde con el nombre del token y la cantidad (ej: "100 USDC")""",
            
            "pt": """📤 **Enviar Cripto para Outra Carteira**

Qual token você gostaria de enviar?

**Tokens Disponíveis:**
1. Ξ **ETH** (Ethereum)
2. 💵 **USDC** (USD Coin)
3. 💵 **USDT** (Tether)
4. 💰 **DAI** (Dai)
5. ₿ **WBTC** (Wrapped Bitcoin)

💬 Responda com o nome do token e a quantia (ex: "100 USDC")""",
            
            "zh": """📤 **发送加密货币到另一个钱包**

您想发送哪种代币？

**可用代币：**
1. Ξ **ETH** (以太坊)
2. 💵 **USDC** (USD Coin)
3. 💵 **USDT** (Tether)
4. 💰 **DAI** (Dai)
5. ₿ **WBTC** (封装比特币)

💬 回复代币名称和金额（例如："100 USDC"）""",
        }
        
        return msgs.get(language, msgs["en"])
    
    def _ask_for_amount(self, data: dict[str, Any], language: str) -> str:
        """Ask user for transfer amount."""
        
        token = data.get("token", "ETH")
        token_info = SUPPORTED_TOKENS.get(token.lower(), {"emoji": "💎"})
        emoji = token_info.get("emoji", "💎")
        
        msgs = {
            "en": f"""{emoji} **Send {token}**

How much **{token}** would you like to send?

💡 *Examples:*
• `100` (one hundred {token})
• `0.5` (half a {token})
• `1000` (one thousand {token})

💬 Enter the amount to continue""",
            
            "es": f"""{emoji} **Enviar {token}**

¿Cuánto **{token}** te gustaría enviar?

💡 *Ejemplos:*
• `100` (cien {token})
• `0.5` (medio {token})
• `1000` (mil {token})

💬 Ingresa la cantidad para continuar""",
            
            "pt": f"""{emoji} **Enviar {token}**

Quanto **{token}** você gostaria de enviar?

💡 *Exemplos:*
• `100` (cem {token})
• `0.5` (meio {token})
• `1000` (mil {token})

💬 Digite a quantia para continuar""",
            
            "zh": f"""{emoji} **发送 {token}**

您想发送多少 **{token}**？

💡 *示例：*
• `100` (一百 {token})
• `0.5` (半个 {token})
• `1000` (一千 {token})

💬 输入金额以继续""",
        }
        
        return msgs.get(language, msgs["en"])
    
    def _ask_for_recipient(self, data: dict[str, Any], language: str) -> str:
        """Ask user for recipient address."""
        
        token = data.get("token", "ETH")
        amount = data.get("amount", "0")
        token_info = SUPPORTED_TOKENS.get(token.lower(), {"emoji": "💎"})
        emoji = token_info.get("emoji", "💎")
        
        msgs = {
            "en": f"""📤 **Sending {amount} {emoji} {token}**

Where should I send this?

💡 *Paste the destination wallet address:*

⚠️ **IMPORTANT:**
• Double-check the address carefully
• Sending to wrong address = permanent loss
• Copy-paste recommended (avoid typing)

💬 Paste the recipient's wallet address""",
            
            "es": f"""📤 **Enviando {amount} {emoji} {token}**

¿A dónde debo enviarlo?

💡 *Pega la dirección de la billetera destino:*

⚠️ **IMPORTANTE:**
• Verifica la dirección cuidadosamente
• Enviar a dirección incorrecta = pérdida permanente
• Se recomienda copiar-pegar (evita escribir)

💬 Pega la dirección de la billetera del destinatario""",
            
            "pt": f"""📤 **Enviando {amount} {emoji} {token}**

Para onde devo enviar?

💡 *Cole o endereço da carteira de destino:*

⚠️ **IMPORTANTE:**
• Verifique o endereço cuidadosamente
• Enviar para endereço errado = perda permanente
• Recomenda-se copiar-colar (evite digitar)

💬 Cole o endereço da carteira do destinatário""",
            
            "zh": f"""📤 **发送 {amount} {emoji} {token}**

我应该发送到哪里？

💡 *粘贴目标钱包地址：*

⚠️ **重要：**
• 仔细核对地址
• 发送到错误地址 = 永久丢失
• 建议复制粘贴（避免手动输入）

💬 粘贴收件人的钱包地址""",
        }
        
        return msgs.get(language, msgs["en"])
    
    def _format_invalid_address(self, address: str, language: str) -> str:
        """Format invalid address error message."""
        
        truncated = f"{address[:10]}..." if len(address) > 10 else address
        
        msgs = {
            "en": f"""❌ **Invalid Address**

The address `{truncated}` doesn't appear to be valid.

**Supported formats:**
• Ethereum/Base: `0x` followed by 40 hex characters
• Solana: 32-44 alphanumeric characters

Please paste a valid wallet address.""",
            
            "es": f"""❌ **Dirección Inválida**

La dirección `{truncated}` no parece ser válida.

**Formatos soportados:**
• Ethereum/Base: `0x` seguido de 40 caracteres hex
• Solana: 32-44 caracteres alfanuméricos

Por favor pega una dirección de billetera válida.""",
            
            "pt": f"""❌ **Endereço Inválido**

O endereço `{truncated}` não parece ser válido.

**Formatos suportados:**
• Ethereum/Base: `0x` seguido de 40 caracteres hex
• Solana: 32-44 caracteres alfanuméricos

Por favor cole um endereço de carteira válido.""",
            
            "zh": f"""❌ **地址无效**

地址 `{truncated}` 似乎无效。

**支持的格式：**
• Ethereum/Base：`0x` 后跟 40 个十六进制字符
• Solana：32-44 个字母数字字符

请粘贴有效的钱包地址。""",
        }
        
        return msgs.get(language, msgs["en"])
    
    def _format_transfer_review(
        self,
        data: dict[str, Any],
        language: str,
    ) -> str:
        """Format transfer review for confirmation."""
        
        token = data.get("token", "ETH")
        amount = data.get("amount", "0")
        recipient = data.get("recipient", "")
        network = data.get("network", "ethereum")
        
        token_info = SUPPORTED_TOKENS.get(token.lower(), {"emoji": "💎"})
        emoji = token_info.get("emoji", "💎")
        
        # Truncate address for display
        display_addr = f"{recipient[:8]}...{recipient[-6:]}" if len(recipient) > 14 else recipient
        
        msgs = {
            "en": f"""🔍 **Review Your Transfer**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📤 **Sending:** {amount} {token} {emoji}
📍 **To:** `{display_addr}`
🌐 **Network:** {network.title()}
⚡ **Est. Fee:** ~$1-3 (varies)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ **WARNING:**
• Once confirmed, this transaction CANNOT be reversed
• Double-check the destination address
• Make sure you trust the recipient

**Ready to send?**
Reply "yes" to confirm or "cancel" to abort.""",
            
            "es": f"""🔍 **Revisa Tu Transferencia**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📤 **Enviando:** {amount} {token} {emoji}
📍 **A:** `{display_addr}`
🌐 **Red:** {network.title()}
⚡ **Tarifa Est.:** ~$1-3 (varía)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ **ADVERTENCIA:**
• Una vez confirmado, esta transacción NO SE PUEDE REVERTIR
• Verifica la dirección de destino
• Asegúrate de confiar en el destinatario

**¿Listo para enviar?**
Responde "sí" para confirmar o "cancelar" para abortar.""",
            
            "pt": f"""🔍 **Revise Sua Transferência**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📤 **Enviando:** {amount} {token} {emoji}
📍 **Para:** `{display_addr}`
🌐 **Rede:** {network.title()}
⚡ **Taxa Est.:** ~$1-3 (varia)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ **AVISO:**
• Uma vez confirmado, esta transação NÃO PODE ser revertida
• Verifique o endereço de destino
• Certifique-se de confiar no destinatário

**Pronto para enviar?**
Responda "sim" para confirmar ou "cancelar" para abortar.""",
            
            "zh": f"""🔍 **审核您的转账**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📤 **发送：** {amount} {token} {emoji}
📍 **到：** `{display_addr}`
🌐 **网络：** {network.title()}
⚡ **预计费用：** ~$1-3（变化）

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ **警告：**
• 一旦确认，此交易无法撤销
• 仔细核对目标地址
• 确保您信任收款人

**准备发送了吗？**
回复'是'确认或'取消'中止。""",
        }
        
        return msgs.get(language, msgs["en"])
    
    def _ask_for_confirmation(self, language: str) -> str:
        """Ask user to confirm."""
        
        msgs = {
            "en": """Would you like to confirm this transfer? Reply "yes" or "cancel".""",
            "es": """¿Te gustaría confirmar esta transferencia? Responde "sí" o "cancelar".""",
            "pt": """Gostaria de confirmar esta transferência? Responda "sim" ou "cancelar".""",
            "zh": """您想确认此转账吗？回复"是"或"取消"。""",
        }
        
        return msgs.get(language, msgs["en"])
    
    def _format_ready_to_execute(
        self,
        data: dict[str, Any],
        language: str,
    ) -> str:
        """Format ready-to-execute message."""
        
        token = data.get("token", "ETH")
        amount = data.get("amount", "0")
        recipient = data.get("recipient", "")
        
        display_addr = f"{recipient[:8]}...{recipient[-6:]}" if len(recipient) > 14 else recipient
        token_info = SUPPORTED_TOKENS.get(token.lower(), {"emoji": "💎"})
        emoji = token_info.get("emoji", "💎")
        
        msgs = {
            "en": f"""✅ **Transfer Ready to Execute**

🔄 **Sending:** {amount} {token} {emoji}
📍 **To:** `{display_addr}`
⛓️ **Network:** Base

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Click **Confirm** to execute the transfer.""",
            
            "es": f"""✅ **Transferencia Lista para Ejecutar**

🔄 **Enviando:** {amount} {token} {emoji}
📍 **A:** `{display_addr}`
⛓️ **Red:** Base

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Haz clic en **Confirmar** para ejecutar la transferencia.""",
            
            "pt": f"""✅ **Transferência Pronta para Executar**

🔄 **Enviando:** {amount} {token} {emoji}
📍 **Para:** `{display_addr}`
⛓️ **Rede:** Base

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Clique em **Confirmar** para executar a transferência.""",
            
            "zh": f"""✅ **转账准备执行**

🔄 **发送：** {amount} {token} {emoji}
📍 **到：** `{display_addr}`
⛓️ **网络：** Base

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

点击 **确认** 执行转账。""",
        }
        
        return msgs.get(language, msgs["en"])
    
    def _format_cancelled(self, language: str) -> str:
        """Format cancellation message."""
        
        msgs = {
            "en": "❌ Transfer cancelled. Your crypto is safe! Let me know if you'd like to try again.",
            "es": "❌ Transferencia cancelada. ¡Tu cripto está seguro! Avísame si quieres intentarlo de nuevo.",
            "pt": "❌ Transferência cancelada. Sua cripto está segura! Me avise se quiser tentar novamente.",
            "zh": "❌ 转账已取消。您的加密货币是安全的！如果您想再试一次，请告诉我。",
        }
        
        return msgs.get(language, msgs["en"])
    
    def _format_execution_pending(
        self,
        data: dict[str, Any],
        language: str,
    ) -> str:
        """Format message while execution is pending."""
        
        token = data.get("token", "ETH")
        amount = data.get("amount", "0")
        recipient = data.get("recipient", "")
        
        display_addr = f"{recipient[:8]}...{recipient[-6:]}" if len(recipient) > 14 else recipient
        
        msgs = {
            "en": f"""⏳ **Processing Transfer**

Sending **{amount} {token}** to `{display_addr}`...

Please confirm the transaction in your wallet.""",
            
            "es": f"""⏳ **Procesando Transferencia**

Enviando **{amount} {token}** a `{display_addr}`...

Por favor confirma la transacción en tu wallet.""",
            
            "pt": f"""⏳ **Processando Transferência**

Enviando **{amount} {token}** para `{display_addr}`...

Por favor confirme a transação na sua carteira.""",
            
            "zh": f"""⏳ **处理转账中**

正在发送 **{amount} {token}** 到 `{display_addr}`...

请在您的钱包中确认交易。""",
        }
        
        return msgs.get(language, msgs["en"])
    
    # ========================================
    # Execute Data Builder
    # ========================================
    
    def _build_transfer_execute_data(
        self,
        token: str,
        amount: str,
        recipient: str,
        chain: str,
    ) -> dict[str, Any]:
        """Build execute_data for transfer action."""
        
        return {
            "action_type": "transfer",
            "provider": "privy",
            "chain": chain,
            "from_token": token,
            "amount": amount,
            "recipient": recipient,
            "slippage": 0.5,
        }
    
    # ========================================
    # Helpers
    # ========================================
    
    def _is_confirmation(self, text: str) -> bool:
        """Check if text is a confirmation."""
        confirm_words = [
            "yes", "y", "confirm", "ok", "proceed", "continue", "do it", "execute", "send",
            "sí", "si", "confirmar", "vale", "continuar",
            "sim", "confirmar", "prosseguir",
            "是", "确认", "好", "继续",
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
