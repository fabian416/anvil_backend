"""
Transfer Workflow Agent - Multi-Step Token Transfer Operations.

Handles the complete token transfer workflow for authenticated users:
1. Parse request: Extract token, amount, and recipient from user message
2. Validate recipient: Verify address format and detect network
3. Safety check: Analyze recipient wallet safety (EOA vs Contract, first-time, etc.)
4. Confirm: Show transfer details with safety info and wait for user confirmation
5. Execute: Generate execute_data for frontend execution

Integration:
- Address validation for EVM and Solana
- Network detection from address format
- Wallet safety analysis (contract detection, interaction history)
- Privy SDK for execution

Safety Features:
- EOA vs Smart Contract detection
- First-time recipient warning
- Known address detection (exchanges, protocols)
- Safety score (0-100)

Example Conversation:
    User: "send 100 USDC to 0x742d..."
    Agent: "📤 Sending 100 USDC to 0x742d...1234
           🔒 Safety: 75/100 (Low Risk) - First-time recipient
           Confirm?"
    User: "yes"
    Agent: "✅ Ready to send!" + execute_data for frontend modal
"""

import logging
import re
from typing import Any, TYPE_CHECKING
from dataclasses import dataclass, field

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
    from app.infrastructure.adapters.external.web3_client import Web3Client
    from app.infrastructure.adapters.external.etherscan_client import EtherscanClient

logger = logging.getLogger(__name__)


# ========================================
# Safety Check Data Structures
# ========================================

@dataclass
class SafetyCheck:
    """Result of a single safety check."""
    name: str
    status: str  # "pass", "warn", "fail"
    emoji: str
    details: str | None = None


@dataclass
class RecipientSafetyAnalysis:
    """Complete safety analysis for a recipient address."""
    address: str
    safety_score: int  # 0-100
    risk_level: str  # "low", "medium", "high", "critical"
    address_type: str  # "eoa", "contract", "unknown"
    is_first_time: bool
    checks: list[SafetyCheck] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    
    @property
    def risk_emoji(self) -> str:
        """Get emoji for risk level."""
        return {
            "low": "🟢",
            "medium": "🟡",
            "high": "🟠",
            "critical": "🔴",
        }.get(self.risk_level, "⚪")
    
    @property
    def is_safe(self) -> bool:
        """Check if transfer should be allowed."""
        return len(self.blockers) == 0


# Known contract labels (exchanges, protocols, etc.)
KNOWN_CONTRACTS = {
    # Exchanges (Base chain)
    "0x3fc91a3afd70395cd496c647d5a6cc9d4b2b7fad": {"name": "Uniswap Universal Router", "category": "exchange", "safe": True},
    "0x2626664c2603336e57b271c5c0b26f421741e481": {"name": "Uniswap V3 Router", "category": "exchange", "safe": True},
    "0x6131b5fae19ea4f9d964eac0408e4408b66337b5": {"name": "Hyperliquid Bridge", "category": "bridge", "safe": True},
    # Coinbase
    "0xcdac0d6c6c59727a65f871236188350531885c43": {"name": "Coinbase Commerce", "category": "exchange", "safe": True},
    # Add more known addresses as needed
}

# Known scam/risky addresses (would be updated via external service in production)
KNOWN_RISKY_ADDRESSES: set[str] = set()  # TODO: Integrate with external scam database


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
    3. safety_check: Analyze recipient wallet safety
    4. confirm: Show transfer details with safety info, wait for confirmation
    5. execute: Generate execute_data for frontend
    
    Features:
    - Natural language parameter extraction
    - Multi-chain address validation
    - Network detection from address format
    - Wallet safety analysis (EOA vs Contract, first-time detection)
    - User modification support
    - Multi-language support
    
    Safety Features:
    - EOA vs Smart Contract detection
    - First-time recipient warning
    - Known address labeling (exchanges, protocols)
    - Safety score (0-100) with risk level
    """
    
    def __init__(
        self,
        llm_client: "LLMClientGateway | None" = None,
        web3_client: "Web3Client | None" = None,
        etherscan_client: "EtherscanClient | None" = None,
    ):
        """
        Initialize transfer workflow agent.
        
        Args:
            llm_client: LLM client for parameter extraction
            web3_client: Web3 client for blockchain queries (contract detection)
            etherscan_client: Etherscan client for address labels and history
        """
        super().__init__(llm_client=llm_client)
        self._web3_client = web3_client
        self._etherscan_client = etherscan_client
    
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
        text_lower = message.value.lower().strip()
        
        logger.info(f"[TransferWorkflow] Processing step={step}, message={message.value[:50]}...")
        
        # Check if user wants to start a NEW transfer flow (restart detection)
        # This resets state when user says "send", "transfer", etc.
        # while already in an ongoing flow (FETCH_DATA, CONFIRM, or EXECUTE step)
        if step not in (WorkflowStep.PARSE_REQUEST.value, WorkflowStep.CANCELLED.value, WorkflowStep.COMPLETED.value):
            restart_keywords = [
                "send", "transfer", "enviar", "transferir",
                "i want to send", "i want to transfer",
                "quiero enviar", "quiero transferir",
            ]
            is_restart_request = any(text_lower.startswith(kw) or f" {kw}" in f" {text_lower}" for kw in restart_keywords)
            
            if is_restart_request:
                logger.info(f"[TransferWorkflow] Restart detected - user starting new transfer flow, resetting state")
                state = WorkflowState()
                state.step = WorkflowStep.PARSE_REQUEST.value
                return await self._handle_parse_request(message, state, user_context)
        
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
        text = message.value.lower().strip()
        original_text = message.value
        
        # Check if we already have some params from previous turn and user is just providing missing info
        existing_token = state.data.get("token", "").upper()
        existing_amount = state.data.get("amount")
        existing_recipient = state.data.get("recipient")
        
        # If we already have token and amount, and user provides just an address, treat as recipient
        if existing_token and existing_amount and not existing_recipient:
            potential_address = self._extract_address(original_text)
            if potential_address:
                logger.info(f"[TransferWorkflow] User provided recipient address: {potential_address[:10]}...")
                state.data["recipient"] = potential_address
                state.step = WorkflowStep.FETCH_DATA.value
                return await self._handle_validate(message, state, user_context)
        
        # If we have token but no amount, and user provides just a number, treat as amount
        if existing_token and not existing_amount:
            clean_input = text.replace("$", "").replace(",", "").strip()
            if clean_input.replace(".", "").isdigit():
                logger.info(f"[TransferWorkflow] User provided amount: {clean_input}")
                state.data["amount"] = clean_input
                # Now ask for recipient
                return self._ask_for_recipient(state.data, language), state
        
        # Try to extract parameters from message
        params = await self._extract_transfer_params(text, original_text)
        
        # Merge with existing state
        token = params.get("token") or existing_token
        amount = params.get("amount") or existing_amount
        recipient = params.get("recipient") or existing_recipient
        
        # If we have all parameters, proceed to validate
        if token and amount and recipient:
            state.data["token"] = token.upper()
            state.data["amount"] = amount
            state.data["recipient"] = recipient
            state.data["chain"] = params.get("chain", state.data.get("chain", "base"))
            state.step = WorkflowStep.FETCH_DATA.value
            return await self._handle_validate(message, state, user_context)
        
        # If we have token and amount but no recipient, ask for recipient
        if token and amount and not recipient:
            state.data["token"] = token.upper()
            state.data["amount"] = amount
            state.data["chain"] = params.get("chain", state.data.get("chain", "base"))
            return self._ask_for_recipient(state.data, language), state
        
        # If we have token but no amount, ask for amount
        if token and not amount:
            state.data["token"] = token.upper()
            state.data["chain"] = params.get("chain", state.data.get("chain", "base"))
            return self._ask_for_amount(state.data, language), state
        
        # No token detected - ask user to specify
        return self._ask_for_token(language), state
    
    async def _handle_validate(
        self,
        message: MessageContent,
        state: WorkflowState,
        user_context: UserContext,
    ) -> tuple[str, WorkflowState]:
        """Validate recipient address and perform safety checks.
        
        If user has insufficient funds, shows a helpful recommendation to buy crypto
        but still provides transfer information so they know what to expect.
        """
        
        language = user_context.language
        
        # First, check if we're receiving the address from user input
        # This happens when user provides address after we asked for it
        user_input = message.value.strip()
        recipient = state.data.get("recipient")
        
        # If no recipient in state, try to extract from user message
        if not recipient:
            # Check if user message looks like an address
            potential_address = self._extract_address(user_input)
            if potential_address:
                recipient = potential_address
                state.data["recipient"] = recipient
                logger.info(f"[TransferWorkflow] Extracted recipient from user input: {recipient[:10]}...")
            else:
                # User input doesn't contain a valid address
                logger.info(f"[TransferWorkflow] No valid address in user input: {user_input[:30]}...")
                response = self._format_invalid_address(user_input or "empty", language)
                return response, state
        
        # Validate address format
        validation = self._validate_address(recipient)
        
        if not validation["valid"]:
            # Invalid address
            response = self._format_invalid_address(recipient or "empty", language)
            state.data["recipient"] = None  # Clear invalid address
            return response, state
        
        # Store network info
        state.data["network"] = validation["network"]
        
        # Check user balance and prepare recommendation if insufficient
        funding_recommendation = ""
        if user_context.needs_funding_recommendation:
            token = state.data.get("token", "ETH")
            logger.info(
                f"[TransferWorkflow] User has insufficient funds: "
                f"portfolio_state={user_context.portfolio_state}, "
                f"balance=${user_context.total_balance_usd:.2f}"
            )
            funding_recommendation = self._get_funding_recommendation(
                token=token,
                language=language,
            )
        
        # Perform safety analysis on recipient
        safety_analysis = await self._analyze_recipient_safety(
            recipient=recipient,
            user_context=user_context,
        )
        
        # Store safety analysis in state
        state.data["safety_analysis"] = {
            "score": safety_analysis.safety_score,
            "risk_level": safety_analysis.risk_level,
            "address_type": safety_analysis.address_type,
            "is_first_time": safety_analysis.is_first_time,
            "warnings": safety_analysis.warnings,
            "blockers": safety_analysis.blockers,
        }
        
        # Check for blockers (critical safety issues)
        if not safety_analysis.is_safe:
            response = self._format_blocked_transfer(safety_analysis, language)
            state.error = "safety_blocked"
            return response, state
        
        # Only move to confirm step if user has sufficient funds
        # If user needs funding, stay in informational mode
        if not user_context.needs_funding_recommendation:
            state.step = WorkflowStep.CONFIRM.value
            
            # Build execute_data only if user has funds
            state.execute_data = self._build_transfer_execute_data(
                token=state.data.get("token", "ETH"),
                amount=state.data.get("amount", "0"),
                recipient=recipient,
                chain=state.data.get("chain", "base"),
            )
        else:
            # User needs to fund first - stay in parse_request
            # Don't advance to confirm so frontend won't expect action
            state.step = WorkflowStep.PARSE_REQUEST.value
            state.execute_data = None  # No execute_data when user has no funds
            logger.info(
                f"[TransferWorkflow] Not advancing to confirm - user needs funding first"
            )
        
        # Format confirmation response with user balance section
        response = self._format_transfer_review(
            state.data,
            language,
            user_context=user_context,
        )
        
        # Prepend funding recommendation if user has insufficient funds
        if funding_recommendation:
            response = funding_recommendation + "\n" + response
        
        return response, state
    
    def _get_funding_recommendation(self, token: str, language: str) -> str:
        """
        Get a helpful recommendation for users with insufficient funds.
        
        This is shown before the transfer details to guide users on how to fund their wallet.
        """
        recommendations = {
            "en": f"""💡 **Heads up:** Your portfolio appears to have limited funds.

To complete this transfer, you'll need **{token}** in your wallet.

**Get started:**
• 💳 Say **"buy crypto"** to purchase USDC with card/Apple Pay/Google Pay
• 📥 Or transfer {token} from another wallet

Here's the transfer details you requested:
""",
            "es": f"""💡 **Aviso:** Tu portafolio parece tener fondos limitados.

Para completar esta transferencia, necesitarás **{token}** en tu billetera.

**Comienza:**
• 💳 Di **"comprar cripto"** para comprar USDC con tarjeta/Apple Pay/Google Pay
• 📥 O transfiere {token} desde otra billetera

Aquí están los detalles de la transferencia que solicitaste:
""",
            "pt": f"""💡 **Atenção:** Seu portfólio parece ter fundos limitados.

Para completar esta transferência, você precisará de **{token}** em sua carteira.

**Comece:**
• 💳 Diga **"comprar cripto"** para comprar USDC com cartão/Apple Pay/Google Pay
• 📥 Ou transfira {token} de outra carteira

Aqui estão os detalhes da transferência que você solicitou:
""",
            "zh": f"""💡 **提示:** 您的投资组合似乎资金有限。

要完成此转账，您需要在钱包中有 **{token}**。

**开始：**
• 💳 说 **"买加密货币"** 用卡/Apple Pay/Google Pay 购买 USDC
• 📥 或从另一个钱包转入 {token}

以下是您请求的转账详情：
""",
        }
        return recommendations.get(language, recommendations["en"])
    
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
            # Call _handle_execute directly to check balance before showing "Ready"
            return await self._handle_execute(message, state, user_context)
        
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
            response = self._format_transfer_review(state.data, language, user_context=user_context)
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
        """Handle execute step - transaction is done by frontend.
        
        IMPORTANT: Checks user balance before allowing execution.
        If user has insufficient funds, shows helpful message to buy crypto.
        """
        language = user_context.language
        # Use 'or' to handle both missing keys AND None values
        token = (state.data.get("token") or "ETH").upper()
        amount = state.data.get("amount") or "0"
        recipient = state.data.get("recipient") or ""
        
        # Check user balance before allowing execution
        if user_context.needs_funding_recommendation:
            logger.info(
                f"[TransferWorkflow] Blocking execution - insufficient funds: "
                f"portfolio_state={user_context.portfolio_state}, "
                f"balance=${user_context.total_balance_usd:.2f}"
            )
            response = self._build_insufficient_balance_message(
                token=token,
                amount=amount,
                recipient=recipient,
                user_balance=user_context.total_balance_usd,
                language=language,
            )
            state.error = "insufficient_balance"
            return response, state
        
        # The actual transaction is handled by the frontend using execute_data
        state.step = WorkflowStep.COMPLETED.value
        
        return self._format_execution_pending(state.data, language), state
    
    def _build_insufficient_balance_message(
        self,
        token: str,
        amount: str,
        recipient: str,
        user_balance: float,
        language: str,
    ) -> str:
        """Build message when user has insufficient balance to execute transfer."""
        short_recipient = f"{recipient[:8]}...{recipient[-6:]}" if len(recipient) > 16 else recipient
        messages = {
            "en": f"""❌ **Unable to execute transfer**

**Transfer requested:** {amount} {token} to {short_recipient}
**Your current balance:** ${user_balance:.2f}

You don't have enough {token} in your wallet to complete this transfer.

---

**💳 Get {token} to send:**

1. **Buy with card/Apple Pay/Google Pay:**
   Say: **"buy {token}"** or **"buy 100 {token}"**

2. **Transfer from another wallet:**
   Send {token} to your Anvil wallet address

---

Once you have {token} in your wallet, come back and try:
**"send {amount} {token} to {short_recipient}"**
""",
            "es": f"""❌ **No se puede ejecutar la transferencia**

**Transferencia solicitada:** {amount} {token} a {short_recipient}
**Tu saldo actual:** ${user_balance:.2f}

No tienes suficiente {token} en tu billetera.

**💳 Obtén {token}:**
• Di: **"comprar {token}"**
• O transfiere {token} desde otra billetera
""",
            "pt": f"""❌ **Não é possível executar a transferência**

**Transferência solicitada:** {amount} {token} para {short_recipient}
**Seu saldo atual:** ${user_balance:.2f}

Você não tem {token} suficiente na sua carteira.

**💳 Obtenha {token}:**
• Diga: **"comprar {token}"**
• Ou transfira {token} de outra carteira
""",
        }
        return messages.get(language, messages["en"])
    
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
        if self._llm:
            try:
                llm_params = await self._extract_params_with_llm(
                    message=text,
                    param_schema={
                        "token": "string (Token symbol to transfer: ETH, USDC, DAI, etc.)",
                        "amount": "number (Amount to transfer)",
                        "recipient": "string (Recipient wallet address 0x... or Solana format)",
                        "chain": "string (Blockchain network: base, ethereum, etc.)",
                    },
                    examples=[
                        {
                            "input": "send 100 USDC to 0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
                            "output": '{"token": "USDC", "amount": "100", "recipient": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e", "chain": "base"}'
                        },
                        {
                            "input": "transfer 0.5 ETH to 0xABC123...",
                            "output": '{"token": "ETH", "amount": "0.5", "recipient": "0xABC123...", "chain": "base"}'
                        },
                    ],
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
    
    def _format_invalid_address(self, address: str | None, language: str) -> str:
        """Format invalid address error message."""
        
        # Handle None or empty address
        if not address:
            address = "empty"
        
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
        user_context: UserContext | None = None,
    ) -> str:
        """Format transfer review for confirmation with safety info and user balance."""
        
        token = data.get("token", "ETH")
        amount = data.get("amount", "0")
        recipient = data.get("recipient", "")
        network = data.get("network", "ethereum")
        safety = data.get("safety_analysis", {})
        
        token_info = SUPPORTED_TOKENS.get(token.lower(), {"emoji": "💎"})
        emoji = token_info.get("emoji", "💎")
        
        # Truncate address for display
        display_addr = f"{recipient[:8]}...{recipient[-6:]}" if len(recipient) > 14 else recipient
        
        # Build safety section
        safety_section = self._format_safety_section(safety, language)
        
        # Build user balance section
        user_balance_section = self._build_transfer_user_balance_section(
            user_context=user_context,
            token=token,
            amount=amount,
            language=language,
        )
        
        msgs = {
            "en": f"""🔍 **Review Your Transfer**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📤 **Sending:** {amount} {token} {emoji}
📍 **To:** `{display_addr}`
🌐 **Network:** {network.title()}
⚡ **Est. Fee:** ~$0.01-0.10 (Base L2)

{user_balance_section}

{safety_section}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ **REMINDER:**
• Once confirmed, this transaction CANNOT be reversed
• Double-check the destination address""",
            
            "es": f"""🔍 **Revisa Tu Transferencia**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📤 **Enviando:** {amount} {token} {emoji}
📍 **A:** `{display_addr}`
🌐 **Red:** {network.title()}
⚡ **Tarifa Est.:** ~$0.01-0.10 (Base L2)

{user_balance_section}

{safety_section}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ **RECORDATORIO:**
• Una vez confirmado, esta transacción NO SE PUEDE REVERTIR
• Verifica la dirección de destino""",
            
            "pt": f"""🔍 **Revise Sua Transferência**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📤 **Enviando:** {amount} {token} {emoji}
📍 **Para:** `{display_addr}`
🌐 **Rede:** {network.title()}
⚡ **Taxa Est.:** ~$0.01-0.10 (Base L2)

{user_balance_section}

{safety_section}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ **AVISO:**
• Uma vez confirmado, esta transação NÃO PODE ser revertida
• Verifique o endereço de destino""",
            
            "zh": f"""🔍 **审核您的转账**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📤 **发送：** {amount} {token} {emoji}
📍 **到：** `{display_addr}`
🌐 **网络：** {network.title()}
⚡ **预计费用：** ~$1-3（变化）

{user_balance_section}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ **警告：**
• 一旦确认，此交易无法撤销
• 仔细核对目标地址""",
        }
        
        return msgs.get(language, msgs["en"])
    
    def _build_transfer_user_balance_section(
        self,
        user_context: UserContext | None,
        token: str,
        amount: str,
        language: str,
    ) -> str:
        """Build user balance context section for transfer."""
        if not user_context or not user_context.is_authenticated:
            return ""
        
        balance = user_context.total_balance_usd
        portfolio_state = user_context.portfolio_state
        
        try:
            transfer_amount = float(amount)
        except (ValueError, TypeError):
            transfer_amount = 0
        
        # Check if user has enough balance
        if portfolio_state == "empty" or balance < 1:
            msgs = {
                "en": f"💰 **Your Balance:** $0.00\n\n⚠️ You'll need {token} first:\n• Say `buy crypto` to purchase USDC with card\n• Or transfer {token} from another wallet",
                "es": f"💰 **Tu Saldo:** $0.00\n\n⚠️ Necesitas {token} primero:\n• Di `comprar cripto` para comprar USDC\n• O transfiere {token} desde otra billetera",
                "pt": f"💰 **Seu Saldo:** $0.00\n\n⚠️ Você precisa de {token} primeiro:\n• Diga `comprar cripto` para comprar USDC\n• Ou transfira {token} de outra carteira",
                "zh": f"💰 **您的余额：** $0.00\n\n⚠️ 您需要先获取 {token}：\n• 说 `买加密货币` 购买 USDC\n• 或从其他钱包转入 {token}",
            }
        elif balance < transfer_amount:
            msgs = {
                "en": f"💰 **Your Balance:** ~${balance:,.2f}\n\n⚠️ Transfer amount exceeds your balance.\n💡 Consider a smaller amount or say `buy crypto` to get more funds.",
                "es": f"💰 **Tu Saldo:** ~${balance:,.2f}\n\n⚠️ El monto de la transferencia excede tu saldo.\n💡 Considera un monto menor o di `comprar cripto` para obtener más fondos.",
                "pt": f"💰 **Seu Saldo:** ~${balance:,.2f}\n\n⚠️ O valor da transferência excede seu saldo.\n💡 Considere um valor menor ou diga `comprar cripto` para obter mais fundos.",
                "zh": f"💰 **您的余额：** ~${balance:,.2f}\n\n⚠️ 转账金额超过您的余额。\n💡 考虑较小的金额或说 `买加密货币` 获取更多资金。",
            }
        else:
            msgs = {
                "en": f"💰 **Your Balance:** ~${balance:,.2f} ✅",
                "es": f"💰 **Tu Saldo:** ~${balance:,.2f} ✅",
                "pt": f"💰 **Seu Saldo:** ~${balance:,.2f} ✅",
                "zh": f"💰 **您的余额：** ~${balance:,.2f} ✅",
            }
        
        return msgs.get(language, msgs["en"])
    
    def _ask_for_confirmation(self, language: str) -> str:
        """Ask user to confirm (not used - frontend handles via execute_data card)."""
        
        msgs = {
            "en": "Review the transfer details above.",
            "es": "Revisa los detalles de la transferencia.",
            "pt": "Revise os detalhes da transferência.",
            "zh": "查看上方的转账详情。",
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
    # Safety Check Methods
    # ========================================
    
    async def _analyze_recipient_safety(
        self,
        recipient: str,
        user_context: UserContext,
    ) -> RecipientSafetyAnalysis:
        """
        Analyze recipient wallet safety (Phase 2 - Enhanced).
        
        Checks:
        1. EOA vs Smart Contract detection (web3)
        2. Known address labels - local + Etherscan API
        3. First-time recipient detection via Etherscan interaction history
        4. Known risky addresses (local blocklist)
        5. Contract verification status (Etherscan)
        
        Returns:
            RecipientSafetyAnalysis with score, risk level, and warnings
        """
        recipient_lower = recipient.lower()
        checks: list[SafetyCheck] = []
        warnings: list[str] = []
        blockers: list[str] = []
        
        # Initialize defaults
        address_type = "unknown"
        is_contract = False
        is_first_time = True  # Default to true for safety
        is_known = False
        is_known_safe = False
        is_verified_contract = False
        etherscan_label: str | None = None
        previous_interactions = 0
        
        # ========================================
        # Check 1: Known addresses (local database)
        # ========================================
        known_info = KNOWN_CONTRACTS.get(recipient_lower)
        if known_info:
            is_known = True
            label_name = known_info.get("name", "Known Address")
            label_category = known_info.get("category", "unknown")
            is_known_safe = known_info.get("safe", False)
            
            if is_known_safe:
                checks.append(SafetyCheck(
                    name="Known Address",
                    status="pass",
                    emoji="✅",
                    details=f"{label_name} ({label_category})",
                ))
            else:
                checks.append(SafetyCheck(
                    name="Known Address",
                    status="warn",
                    emoji="⚠️",
                    details=f"{label_name} - Use caution",
                ))
                warnings.append(f"Known risky address: {label_name}")
        
        # ========================================
        # Check 2: Etherscan API label lookup (Phase 2)
        # ========================================
        if self._etherscan_client and not known_info:
            try:
                label_info = await self._etherscan_client.get_address_label(recipient)
                
                if label_info and label_info.label:
                    etherscan_label = label_info.label
                    is_known = True
                    is_verified_contract = label_info.is_verified
                    
                    # Check for risky categories
                    if label_info.is_risky:
                        checks.append(SafetyCheck(
                            name="Address Label",
                            status="fail",
                            emoji="🚫",
                            details=f"{etherscan_label} (Flagged)",
                        ))
                        blockers.append(f"Address flagged as: {label_info.category}")
                    else:
                        is_known_safe = label_info.address_type.value in ("exchange", "defi", "dex")
                        checks.append(SafetyCheck(
                            name="Address Label",
                            status="pass",
                            emoji="🏷️",
                            details=f"{etherscan_label} ({label_info.category or 'verified'})",
                        ))
                        
                        # Use Etherscan type as address type
                        if label_info.address_type.value != "unknown":
                            address_type = label_info.address_type.value
                            if address_type in ("contract", "defi", "dex", "token", "nft", "bridge"):
                                is_contract = True
            except Exception as e:
                logger.warning(f"[TransferWorkflow] Etherscan label lookup failed: {e}")
        
        # ========================================
        # Check 3: Known risky/scam addresses (local blocklist)
        # ========================================
        if recipient_lower in KNOWN_RISKY_ADDRESSES:
            checks.append(SafetyCheck(
                name="Scam Check",
                status="fail",
                emoji="🚫",
                details="Address flagged as risky",
            ))
            blockers.append("This address has been flagged as potentially risky")
        else:
            checks.append(SafetyCheck(
                name="Scam Check",
                status="pass",
                emoji="✅",
                details="Not in blocklist",
            ))
        
        # ========================================
        # Check 4: EOA vs Contract detection (web3)
        # ========================================
        if self._web3_client and address_type == "unknown":
            try:
                is_contract = await self._web3_client.is_contract(recipient)
                address_type = "contract" if is_contract else "eoa"
                
                if is_contract:
                    # Contract - check if known or verified
                    if is_known or is_verified_contract:
                        contract_detail = etherscan_label or known_info.get("name", "Known") if known_info else "Verified"
                        checks.append(SafetyCheck(
                            name="Address Type",
                            status="pass",
                            emoji="📄",
                            details=f"Smart Contract ({contract_detail})",
                        ))
                    else:
                        # Unknown, unverified contract - warn
                        checks.append(SafetyCheck(
                            name="Address Type",
                            status="warn",
                            emoji="📄",
                            details="Smart Contract (Unverified)",
                        ))
                        warnings.append("Sending to an unverified smart contract")
                else:
                    # EOA - regular wallet
                    checks.append(SafetyCheck(
                        name="Address Type",
                        status="pass",
                        emoji="👤",
                        details="External Wallet (EOA)",
                    ))
            except Exception as e:
                logger.warning(f"[TransferWorkflow] Failed to check contract status: {e}")
                checks.append(SafetyCheck(
                    name="Address Type",
                    status="warn",
                    emoji="❓",
                    details="Unable to verify",
                ))
        elif address_type != "unknown":
            # Already determined from Etherscan
            type_label = address_type.upper() if address_type == "eoa" else address_type.title()
            checks.append(SafetyCheck(
                name="Address Type",
                status="pass",
                emoji="📄" if is_contract else "👤",
                details=f"{type_label} ({etherscan_label or 'Identified'})",
            ))
        else:
            # No web3 client - skip contract check
            checks.append(SafetyCheck(
                name="Address Type",
                status="warn",
                emoji="❓",
                details="Verification unavailable",
            ))
        
        # ========================================
        # Check 5: Interaction history (Etherscan - Phase 2)
        # ========================================
        user_wallet = user_context.wallet_address if user_context else None
        
        if self._etherscan_client and user_wallet:
            try:
                interactions = await self._etherscan_client.get_recent_interactions(
                    from_address=user_wallet,
                    to_address=recipient,
                    limit=5,
                )
                
                previous_interactions = len(interactions)
                is_first_time = previous_interactions == 0
                
                if not is_first_time:
                    # Has previous interactions - safer
                    checks.append(SafetyCheck(
                        name="Interaction History",
                        status="pass",
                        emoji="✅",
                        details=f"Previously sent ({previous_interactions}x)",
                    ))
                else:
                    # First time - warn
                    checks.append(SafetyCheck(
                        name="Interaction History",
                        status="warn",
                        emoji="🆕",
                        details="First-time recipient",
                    ))
                    warnings.append("You haven't sent to this address before")
            except Exception as e:
                logger.warning(f"[TransferWorkflow] Interaction history check failed: {e}")
                # Fall back to first-time assumption
                checks.append(SafetyCheck(
                    name="Interaction History",
                    status="warn",
                    emoji="🆕",
                    details="First-time recipient (assumed)",
                ))
                warnings.append("You haven't sent to this address before")
        else:
            # No Etherscan client or no wallet - default to first-time warning
            checks.append(SafetyCheck(
                name="Interaction History",
                status="warn",
                emoji="🆕",
                details="First-time recipient",
            ))
            warnings.append("You haven't sent to this address before")
        
        # ========================================
        # Calculate safety score
        # ========================================
        safety_score = self._calculate_safety_score(
            is_contract=is_contract,
            is_known=is_known,
            is_known_safe=is_known_safe,
            is_first_time=is_first_time,
            has_blockers=len(blockers) > 0,
            is_verified=is_verified_contract,
            previous_interactions=previous_interactions,
        )
        
        # Determine risk level
        if safety_score >= 80:
            risk_level = "low"
        elif safety_score >= 60:
            risk_level = "medium"
        elif safety_score >= 40:
            risk_level = "high"
        else:
            risk_level = "critical"
        
        return RecipientSafetyAnalysis(
            address=recipient,
            safety_score=safety_score,
            risk_level=risk_level,
            address_type=address_type,
            is_first_time=is_first_time,
            checks=checks,
            warnings=warnings,
            blockers=blockers,
        )
    
    def _calculate_safety_score(
        self,
        is_contract: bool,
        is_known: bool,
        is_known_safe: bool,
        is_first_time: bool,
        has_blockers: bool,
        is_verified: bool = False,
        previous_interactions: int = 0,
    ) -> int:
        """
        Calculate safety score (0-100) based on checks (Phase 2 enhanced).
        
        Scoring:
        - Base score: 70
        - Known safe address: +20
        - Known address (not explicitly safe): +10
        - Verified contract: +10
        - EOA (not contract): +5
        - Previous interactions: +5 to +15 (based on count)
        - Unknown contract: -15
        - Unverified contract: -5
        - First-time recipient: -10
        - Has blockers: -50
        """
        score = 70  # Base score
        
        if has_blockers:
            return max(0, score - 50)
        
        # Known address bonuses
        if is_known_safe:
            score += 20
        elif is_known:
            score += 10
        
        # Contract type scoring
        if not is_contract:
            # EOA is generally safer for personal transfers
            score += 5
        else:
            if is_verified:
                # Verified contract is safer
                score += 10
            elif not is_known:
                # Unknown, unverified contract is risky
                score -= 15
            else:
                # Known but unverified
                score -= 5
        
        # Interaction history (Phase 2)
        if previous_interactions > 0:
            # Previous interactions increase trust
            if previous_interactions >= 5:
                score += 15  # Frequent recipient
            elif previous_interactions >= 2:
                score += 10  # Multiple interactions
            else:
                score += 5   # At least one previous interaction
        elif is_first_time:
            score -= 10
        
        return max(0, min(100, score))
    
    def _format_safety_section(
        self,
        safety: dict[str, Any],
        language: str,
    ) -> str:
        """Format safety analysis section for display."""
        if not safety:
            return ""
        
        score = safety.get("score", 0)
        risk_level = safety.get("risk_level", "unknown")
        address_type = safety.get("address_type", "unknown")
        warnings = safety.get("warnings", [])
        
        # Risk emoji and label
        risk_config = {
            "low": ("🟢", "Low Risk"),
            "medium": ("🟡", "Medium Risk"),
            "high": ("🟠", "High Risk"),
            "critical": ("🔴", "Critical Risk"),
        }
        risk_emoji, risk_label = risk_config.get(risk_level, ("⚪", "Unknown"))
        
        # Address type label
        type_labels = {
            "eoa": "👤 External Wallet",
            "contract": "📄 Smart Contract",
            "unknown": "❓ Unknown",
        }
        type_label = type_labels.get(address_type, "❓ Unknown")
        
        # Build section
        section = f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔒 **Safety Analysis**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{risk_emoji} **Safety Score:** {score}/100 ({risk_label})
{type_label}
"""
        
        # Add warnings if any
        if warnings:
            section += "\n**⚠️ Warnings:**\n"
            for warning in warnings:
                section += f"• {warning}\n"
        
        return section.strip()
    
    def _format_blocked_transfer(
        self,
        safety: RecipientSafetyAnalysis,
        language: str,
    ) -> str:
        """Format message when transfer is blocked due to safety issues."""
        display_addr = f"{safety.address[:8]}...{safety.address[-6:]}"
        blockers_text = "\n".join(f"• {b}" for b in safety.blockers)
        
        msgs = {
            "en": f"""🚫 **Transfer Blocked - Safety Issue**

The transfer to `{display_addr}` has been blocked for your protection.

**Issues detected:**
{blockers_text}

**What you can do:**
• Double-check the recipient address
• Contact support if you believe this is an error
• Use a different recipient address

Safety is our priority. We block transfers to known risky addresses.""",
            
            "es": f"""🚫 **Transferencia Bloqueada - Problema de Seguridad**

La transferencia a `{display_addr}` ha sido bloqueada para tu protección.

**Problemas detectados:**
{blockers_text}

**Qué puedes hacer:**
• Verifica la dirección del destinatario
• Contacta soporte si crees que es un error
• Usa una dirección diferente""",
            
            "pt": f"""🚫 **Transferência Bloqueada - Problema de Segurança**

A transferência para `{display_addr}` foi bloqueada para sua proteção.

**Problemas detectados:**
{blockers_text}

**O que você pode fazer:**
• Verifique o endereço do destinatário
• Contate o suporte se acredita ser um erro
• Use um endereço diferente""",
        }
        
        return msgs.get(language, msgs["en"])
    
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
