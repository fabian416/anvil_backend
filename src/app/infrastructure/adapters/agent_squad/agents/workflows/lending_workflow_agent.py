"""
Lending Workflow Agent - Multi-Step Deposit/Withdraw Operations.

Handles the complete lending workflow for authenticated users:
1. Parse request: Extract asset and amount from user message
2. Fetch vaults/positions: Get yield options or user positions
3. Confirm: Show quote and wait for user confirmation
4. Execute: Generate execute_data for frontend execution

Integration:
- Primary: Morpho MetaMorpho vaults (Base chain)
- Fallback: Aave V3 markets
- Execution: Frontend uses Privy SDK with execute_data

Supported Actions:
- Deposit: Supply assets to vaults for yield
- Withdraw: Retrieve assets from vaults

Example Conversation (Deposit):
    User: "deposit 1000 USDC"
    Agent: "📊 Best Vault: Steakhouse USDC (12.5% APY). Monthly: ~$10.42. Confirm?"
    User: "yes"
    Agent: "✅ Ready to deposit!" + execute_data for frontend modal

Example Conversation (Withdraw):
    User: "withdraw my USDC"
    Agent: "📊 Your Position: 1000 USDC in Steakhouse. Confirm?"
    User: "yes"
    Agent: "✅ Ready to withdraw!" + execute_data for frontend modal
"""

import logging
import re
from typing import TYPE_CHECKING, Any

from app.domain.enums.agent_type import AgentType
from app.domain.value_objects.message_content import MessageContent

from .base_workflow_agent import (
    BaseWorkflowAgent,
    UserContext,
    WorkflowState,
    WorkflowStep,
)

if TYPE_CHECKING:
    from app.domain.ports.aave_gateway import AaveGateway
    from app.domain.ports.agent_squad.llm_client_gateway import LLMClientGateway
    from app.domain.ports.morpho_gateway import MorphoGateway
    from app.infrastructure.adapters.external.coingecko_client import CoinGeckoClient

logger = logging.getLogger(__name__)


# Supported assets for lending
SUPPORTED_ASSETS = {
    "usdc": {"symbol": "USDC", "name": "USD Coin", "emoji": "💵", "decimals": 6},
    "usdt": {"symbol": "USDT", "name": "Tether", "emoji": "💵", "decimals": 6},
    "dai": {"symbol": "DAI", "name": "Dai", "emoji": "💰", "decimals": 18},
    "eth": {"symbol": "ETH", "name": "Ethereum", "emoji": "Ξ", "decimals": 18},
    "weth": {
        "symbol": "WETH",
        "name": "Wrapped Ethereum",
        "emoji": "Ξ",
        "decimals": 18,
    },
    "wbtc": {"symbol": "WBTC", "name": "Wrapped Bitcoin", "emoji": "₿", "decimals": 8},
}

# Vaults with known issues (exclude from selection)
EXCLUDED_VAULTS = {
    "0x8773447e6369472D9B72f064Ea62e405216E9084",  # MEV Frontier USDC
    "0x1D3b1Cd0a0f242d598834b3F2d126dC6bd774657",  # Clearstar USDC Reactor
    "0xB7890CEE6CF4792cdCC13489D36D9d42726ab863",  # Universal USDC (UUSDC)
    "0x23479229e52Ab6aaD312D0B03DF9F33B46753B5e",  # Extrafi XLend USDC
}

# Aave V3 pool addresses by chain
AAVE_POOL_ADDRESSES = {
    "ethereum": "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2",
    "polygon": "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
    "arbitrum": "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
    "optimism": "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
    "avalanche": "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
    "base": "0xA238Dd80C259a72e81d7e4664a9801593F98d1c5",
}


class LendingWorkflowAgent(BaseWorkflowAgent):
    """
    AGNO-based multi-step lending/deposit workflow agent.

    Steps:
    1. parse_request: Extract asset, amount, and optional protocol preference
    2. fetch_data: Get vault options from Morpho, fallback to Aave
    3. confirm: Show best vault with APY, wait for user confirmation
    4. execute: Generate execute_data for frontend

    Features:
    - Natural language parameter extraction
    - Morpho vault selection with APY optimization
    - Aave V3 fallback for unsupported assets
    - User modification support ("change to 500 USDC")
    - Multi-language support
    """

    def __init__(
        self,
        llm_client: "LLMClientGateway | None" = None,
        morpho_gateway: "MorphoGateway | None" = None,
        aave_gateway: "AaveGateway | None" = None,
        coingecko_client: "CoinGeckoClient | None" = None,
    ):
        """
        Initialize lending workflow agent.

        Args:
            llm_client: LLM client for parameter extraction
            morpho_gateway: Morpho gateway for vault data
            aave_gateway: Aave gateway for fallback markets
            coingecko_client: CoinGecko client for token price lookups
        """
        super().__init__(llm_client=llm_client)
        self._morpho = morpho_gateway
        self._aave = aave_gateway
        self._coingecko = coingecko_client

    @property
    def agent_type(self) -> AgentType:
        return AgentType.LENDING_WORKFLOW

    @property
    def workflow_name(self) -> str:
        return "LendingWorkflow"

    async def process_step(
        self,
        message: MessageContent,
        state: WorkflowState,
        user_context: UserContext,
    ) -> tuple[str, WorkflowState]:
        """Process lending workflow step."""

        step = state.step
        text_lower = message.value.lower().strip()

        logger.info(
            f"[LendingWorkflow] Processing step={step}, message={message.value[:50]}..."
        )

        # Check if user wants to start a NEW lending flow (restart detection)
        # This resets state when user says "lend", "deposit", "supply", "withdraw", etc.
        # while already in an ongoing flow (FETCH_DATA, CONFIRM, or EXECUTE step)
        if step not in {
            WorkflowStep.PARSE_REQUEST.value,
            WorkflowStep.CANCELLED.value,
            WorkflowStep.COMPLETED.value,
        }:
            restart_keywords = [
                # Deposit keywords
                "lend",
                "deposit",
                "supply",
                "depositar",
                "prestar",
                "suministrar",
                "i want to lend",
                "i want to deposit",
                "i want to supply",
                "quiero depositar",
                "quiero prestar",
                # Withdraw keywords
                "withdraw",
                "remove",
                "take out",
                "retirar",
                "sacar",
                "i want to withdraw",
                "quiero retirar",
                # Position viewing (triggers withdraw flow)
                "my lendings",
                "my lending",
                "my deposits",
                "my deposit",
                "mis préstamos",
                "mis depositos",
                "meus empréstimos",
                "meus depósitos",
                "my positions",
                "lending positions",
            ]
            is_restart_request = any(
                text_lower.startswith(kw) or f" {kw}" in f" {text_lower}"
                for kw in restart_keywords
            )

            if is_restart_request:
                logger.info("[LendingWorkflow] Restart detected - resetting state")
                state = WorkflowState()
                state.step = WorkflowStep.PARSE_REQUEST.value
                return await self._handle_parse_request(message, state, user_context)

        # Step 1: Parse request
        if step == WorkflowStep.PARSE_REQUEST.value:
            return await self._handle_parse_request(message, state, user_context)

        # Step 2: Fetch vault data
        if step == WorkflowStep.FETCH_DATA.value:
            return await self._handle_fetch_data(message, state, user_context)

        # Step 3: Confirm
        if step == WorkflowStep.CONFIRM.value:
            return await self._handle_confirm(message, state, user_context)

        # Step 4: Execute
        if step == WorkflowStep.EXECUTE.value:
            return await self._handle_execute(message, state, user_context)

        # Unknown step - reset
        logger.warning(f"[LendingWorkflow] Unknown step: {step}")
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
        """Parse deposit or withdraw request from user message."""

        text = message.value.lower().strip()

        # Detect if this is a withdraw request or position view
        withdraw_keywords = [
            "withdraw",
            "remove",
            "take out",
            "retirar",
            "sacar",
            "提款",
            "取出",
            # Position viewing patterns (trigger withdraw flow to show positions)
            "my lendings",
            "my lending",
            "my deposits",
            "my deposit",
            "mis préstamos",
            "mis depositos",
            "meus empréstimos",
            "meus depósitos",
            "我的贷款",
            "我的存款",
            "my positions",
            "lending positions",
            "show my supply",
            "show my lending",
        ]
        is_withdraw = any(kw in text for kw in withdraw_keywords)

        if is_withdraw:
            state.data["action"] = "withdraw"
            logger.info("[LendingWorkflow] Detected withdraw action")
            return await self._handle_withdraw_request(message, state, user_context)

        # Default to deposit action
        state.data["action"] = "deposit"

        # Check if we're awaiting asset selection from previous turn
        if state.data.get("awaiting_asset_selection"):
            return await self._handle_asset_selection(message, state, user_context)

        # Check if we're awaiting amount from previous turn (asset already selected)
        if state.data.get("awaiting_amount"):
            return await self._handle_amount_input(message, state, user_context)

        # Try to extract parameters from message
        params = await self._extract_lending_params(text)

        asset = params.get("asset")
        amount = params.get("amount")
        protocol = params.get(
            "protocol"
        )  # User's protocol preference (aave, morpho, etc.)

        # If we have both asset and amount, proceed to fetch data
        if asset and amount:
            state.data["asset"] = asset.upper()
            state.data["amount"] = amount
            state.data["chain"] = params.get("chain", "base")
            if protocol:
                state.data["protocol"] = protocol  # Store protocol preference
            state.step = WorkflowStep.FETCH_DATA.value
            return await self._handle_fetch_data(message, state, user_context)

        # If we have asset but no amount, ask for amount with user context
        if asset and not amount:
            state.data["asset"] = asset.upper()
            state.data["awaiting_amount"] = True  # Set flag for next turn
            if protocol:
                state.data["protocol"] = protocol  # Store protocol preference
            state.step = WorkflowStep.PARSE_REQUEST.value
            return await self._ask_for_amount(asset.upper(), user_context), state

        # No asset detected - show interactive asset selection with APY rates
        state.data["awaiting_asset_selection"] = True
        response = await self._get_asset_selection_prompt(user_context)
        return response, state

    async def _handle_withdraw_request(
        self,
        message: MessageContent,
        state: WorkflowState,
        user_context: UserContext,
    ) -> tuple[str, WorkflowState]:
        """
        Handle withdraw request - fetch user positions and prepare withdrawal.

        Flow:
        1. Fetch user's lending positions (Morpho + Aave)
        2. If multiple positions, show selection
        3. If specific asset mentioned, filter to that position
        4. Show position details and confirm withdrawal
        """
        language = user_context.language
        text = message.value.lower().strip()
        wallet_address = user_context.wallet_address

        # Check if user has connected wallet
        if not wallet_address:
            if language == "es":
                return (
                    "🔗 Para retirar tus fondos, necesitas conectar tu wallet primero.\n\n"
                    "Por favor, conecta tu wallet y vuelve a intentarlo.",
                    state,
                )
            if language == "pt":
                return (
                    "🔗 Para retirar seus fundos, você precisa conectar sua carteira primeiro.\n\n"
                    "Por favor, conecte sua carteira e tente novamente.",
                    state,
                )
            return (
                "🔗 To withdraw your funds, you need to connect your wallet first.\n\n"
                "Please connect your wallet and try again.",
                state,
            )

        # Check if awaiting position selection
        if state.data.get("awaiting_position_selection"):
            return await self._handle_position_selection(message, state, user_context)

        # Check if awaiting withdraw amount
        if state.data.get("awaiting_withdraw_amount"):
            return await self._handle_withdraw_amount_input(
                message, state, user_context
            )

        # Try to extract asset from message
        params = await self._extract_lending_params(text)
        requested_asset = (
            params.get("asset", "").upper() if params.get("asset") else None
        )
        requested_amount = params.get("amount")

        # Fetch user positions from Morpho and Aave
        positions = await self._fetch_user_positions(wallet_address, user_context)

        if not positions:
            if language == "es":
                return (
                    "📭 No encontré posiciones de préstamo activas en tu wallet.\n\n"
                    "¿Te gustaría depositar fondos para ganar rendimiento?",
                    state,
                )
            if language == "pt":
                return (
                    "📭 Não encontrei posições de empréstimo ativas na sua carteira.\n\n"
                    "Gostaria de depositar fundos para ganhar rendimento?",
                    state,
                )
            return (
                "📭 I didn't find any active lending positions in your wallet.\n\n"
                "Would you like to deposit funds to earn yield?",
                state,
            )

        # Filter by requested asset if specified
        if requested_asset:
            matching_positions = [
                p for p in positions if p.get("asset", "").upper() == requested_asset
            ]
            if matching_positions:
                positions = matching_positions

        # If single position or specific asset matched, proceed to confirm
        if len(positions) == 1:
            position = positions[0]
            state.data["selected_position"] = position
            state.data["withdraw_amount"] = requested_amount or "max"

            # If amount specified, go to confirm
            if requested_amount:
                state.step = WorkflowStep.CONFIRM.value
                return await self._show_withdraw_confirmation(
                    position, requested_amount, user_context, state
                )

            # Ask for amount or offer max withdrawal
            state.data["awaiting_withdraw_amount"] = True
            return await self._ask_withdraw_amount(position, user_context), state

        # Multiple positions - show selection
        state.data["positions"] = positions
        state.data["awaiting_position_selection"] = True
        return await self._show_position_selection(positions, user_context), state

    async def _fetch_user_positions(
        self,
        wallet_address: str,
        user_context: UserContext,
    ) -> list[dict]:
        """Fetch user's lending positions from Morpho and Aave."""
        positions = []

        # Fetch Morpho positions
        try:
            morpho_result = await self._call_tool(
                "morpho_get_user_positions",
                {"user_address": wallet_address, "chain": "base"},
            )
            if morpho_result and morpho_result.get("positions"):
                for pos in morpho_result["positions"]:
                    # MCP returns supplied_amount, supplied_usd, apy_numeric (and display apy string)
                    apy_val = pos.get("apy_numeric")
                    if apy_val is None and isinstance(pos.get("apy"), (int, float)):
                        apy_val = pos.get("apy")
                    positions.append({
                        "protocol": "morpho",
                        "vault_address": pos.get("vault_address"),
                        "vault_name": pos.get("vault_name", "Morpho Vault"),
                        "asset": pos.get("asset", "UNKNOWN"),
                        "supplied_amount": pos.get("supplied_amount", "0"),
                        "supplied_usd": pos.get("supplied_usd", 0),
                        "apy": apy_val if apy_val is not None else 0,
                        "chain": "base",
                    })
        except Exception as e:
            logger.warning(f"[LendingWorkflow] Failed to fetch Morpho positions: {e}")

        # Fetch Aave positions
        try:
            aave_result = await self._call_tool(
                "aave_get_user_positions",
                {"user_address": wallet_address, "chain": "base"},
            )
            if aave_result and aave_result.get("supplies"):
                for supply in aave_result["supplies"]:
                    positions.append({
                        "protocol": "aave",
                        "asset": supply.get("symbol", "UNKNOWN"),
                        "supplied_amount": supply.get("balance", "0"),
                        "supplied_usd": supply.get("balance_usd", 0),
                        "apy": supply.get("supply_apy", 0),
                        "chain": "base",
                    })
        except Exception as e:
            logger.warning(f"[LendingWorkflow] Failed to fetch Aave positions: {e}")

        return positions

    async def _show_position_selection(
        self,
        positions: list[dict],
        user_context: UserContext,
    ) -> str:
        """Show user their positions for selection."""
        language = user_context.language

        if language == "es":
            header = "📊 **Tus Posiciones de Préstamo**\n\n"
            footer = "\n\n💡 Responde con el número para seleccionar una posición."
        elif language == "pt":
            header = "📊 **Suas Posições de Empréstimo**\n\n"
            footer = "\n\n💡 Responda com o número para selecionar uma posição."
        else:
            header = "📊 **Your Lending Positions**\n\n"
            footer = "\n\n💡 Reply with the number to select a position."

        lines = []
        for i, pos in enumerate(positions, 1):
            protocol = pos.get("protocol", "").upper()
            asset = pos.get("asset", "UNKNOWN")
            amount = pos.get("supplied_amount", "0")
            usd_value = pos.get("supplied_usd", 0)
            apy = pos.get("apy", 0)
            vault_name = pos.get("vault_name", "")

            if vault_name:
                lines.append(
                    f"**{i}.** {vault_name} ({protocol})\n"
                    f"   • {amount} {asset} (~${usd_value:,.2f})\n"
                    f"   • APY: {apy:.2f}%"
                )
            else:
                lines.append(
                    f"**{i}.** {asset} on {protocol}\n"
                    f"   • {amount} {asset} (~${usd_value:,.2f})\n"
                    f"   • APY: {apy:.2f}%"
                )

        return header + "\n\n".join(lines) + footer

    async def _handle_position_selection(
        self,
        message: MessageContent,
        state: WorkflowState,
        user_context: UserContext,
    ) -> tuple[str, WorkflowState]:
        """Handle user's position selection."""
        text = message.value.strip()
        positions = state.data.get("positions", [])

        # Try to parse as number
        try:
            selection = int(text)
            if 1 <= selection <= len(positions):
                position = positions[selection - 1]
                state.data["selected_position"] = position
                state.data["awaiting_position_selection"] = False
                state.data["awaiting_withdraw_amount"] = True
                return await self._ask_withdraw_amount(position, user_context), state
        except ValueError:
            pass

        # Try to match by asset symbol
        text_upper = text.upper()
        for pos in positions:
            if pos.get("asset", "").upper() == text_upper:
                state.data["selected_position"] = pos
                state.data["awaiting_position_selection"] = False
                state.data["awaiting_withdraw_amount"] = True
                return await self._ask_withdraw_amount(pos, user_context), state

        # Invalid selection
        language = user_context.language
        if language == "es":
            return (
                f"❓ No entendí tu selección. Por favor, responde con un número (1-{len(positions)}).",
                state,
            )
        if language == "pt":
            return (
                f"❓ Não entendi sua seleção. Por favor, responda com um número (1-{len(positions)}).",
                state,
            )
        return (
            f"❓ I didn't understand your selection. Please reply with a number (1-{len(positions)}).",
            state,
        )

    async def _ask_withdraw_amount(
        self,
        position: dict,
        user_context: UserContext,
    ) -> str:
        """Ask user how much they want to withdraw."""
        language = user_context.language
        asset = position.get("asset", "")
        amount = position.get("supplied_amount", "0")
        usd_value = position.get("supplied_usd", 0)

        if language == "es":
            return (
                f"💰 **Retiro de {asset}**\n\n"
                f"Tienes **{amount} {asset}** (~${usd_value:,.2f}) disponible.\n\n"
                f"¿Cuánto quieres retirar?\n"
                f"• Escribe un monto (ej: `500`)\n"
                f"• O escribe `max` para retirar todo"
            )
        if language == "pt":
            return (
                f"💰 **Retirada de {asset}**\n\n"
                f"Você tem **{amount} {asset}** (~${usd_value:,.2f}) disponível.\n\n"
                f"Quanto você quer retirar?\n"
                f"• Digite um valor (ex: `500`)\n"
                f"• Ou digite `max` para retirar tudo"
            )
        return (
            f"💰 **{asset} Withdrawal**\n\n"
            f"You have **{amount} {asset}** (~${usd_value:,.2f}) available.\n\n"
            f"How much would you like to withdraw?\n"
            f"• Enter an amount (e.g., `500`)\n"
            f"• Or type `max` to withdraw everything"
        )

    async def _handle_withdraw_amount_input(
        self,
        message: MessageContent,
        state: WorkflowState,
        user_context: UserContext,
    ) -> tuple[str, WorkflowState]:
        """Handle user's withdraw amount input."""
        text = message.value.strip().lower()
        position = state.data.get("selected_position", {})
        supplied_amount = position.get("supplied_amount", "0")

        # Parse amount
        if text == "max" or text == "all" or text == "todo" or text == "tudo":
            withdraw_amount = supplied_amount
        else:
            # Try to extract numeric amount
            import re

            amount_match = re.search(r"[\d,]+\.?\d*", text.replace(",", ""))
            if amount_match:
                withdraw_amount = amount_match.group()
            else:
                language = user_context.language
                if language == "es":
                    return (
                        "❓ No pude entender el monto. Por favor, escribe un número o 'max'.",
                        state,
                    )
                if language == "pt":
                    return (
                        "❓ Não consegui entender o valor. Por favor, digite um número ou 'max'.",
                        state,
                    )
                return (
                    "❓ I couldn't understand the amount. Please enter a number or 'max'.",
                    state,
                )

        state.data["withdraw_amount"] = withdraw_amount
        state.data["awaiting_withdraw_amount"] = False
        state.step = WorkflowStep.CONFIRM.value

        return await self._show_withdraw_confirmation(
            position, withdraw_amount, user_context, state
        )

    async def _show_withdraw_confirmation(
        self,
        position: dict,
        amount: str,
        user_context: UserContext,
        state: WorkflowState,
    ) -> tuple[str, WorkflowState]:
        """Show withdrawal confirmation to user."""
        language = user_context.language
        asset = position.get("asset", "")
        protocol = position.get("protocol", "").upper()
        vault_name = position.get("vault_name", "")
        supplied_amount = position.get("supplied_amount", "0")
        supplied_usd = position.get("supplied_usd", 0)

        # Calculate USD value of withdrawal
        try:
            withdraw_ratio = (
                float(amount) / float(supplied_amount)
                if float(supplied_amount) > 0
                else 0
            )
            withdraw_usd = supplied_usd * withdraw_ratio
        except (ValueError, ZeroDivisionError):
            withdraw_usd = supplied_usd  # Assume max if parsing fails

        display_name = vault_name if vault_name else f"{asset} on {protocol}"

        if language == "es":
            response = (
                f"📤 **Confirmar Retiro**\n\n"
                f"**De:** {display_name}\n"
                f"**Monto:** {amount} {asset} (~${withdraw_usd:,.2f})\n\n"
                f"¿Confirmas este retiro?\n"
                f"• Escribe **sí** o **confirmar** para continuar\n"
                f"• Escribe **no** o **cancelar** para cancelar"
            )
        elif language == "pt":
            response = (
                f"📤 **Confirmar Retirada**\n\n"
                f"**De:** {display_name}\n"
                f"**Valor:** {amount} {asset} (~${withdraw_usd:,.2f})\n\n"
                f"Você confirma esta retirada?\n"
                f"• Digite **sim** ou **confirmar** para continuar\n"
                f"• Digite **não** ou **cancelar** para cancelar"
            )
        else:
            response = (
                f"📤 **Confirm Withdrawal**\n\n"
                f"**From:** {display_name}\n"
                f"**Amount:** {amount} {asset} (~${withdraw_usd:,.2f})\n\n"
                f"Do you confirm this withdrawal?\n"
                f"• Type **yes** or **confirm** to proceed\n"
                f"• Type **no** or **cancel** to cancel"
            )

        return response, state

    async def _handle_asset_selection(
        self,
        message: MessageContent,
        state: WorkflowState,
        user_context: UserContext,
    ) -> tuple[str, WorkflowState]:
        """
        Handle user's asset selection response.

        User can respond with:
        - Number (1-5) to select from the list
        - Asset symbol (USDC, ETH, etc.)
        - Amount + asset (e.g., "1000 USDC")
        """
        text = message.value.strip()

        # Clear the awaiting flag
        state.data["awaiting_asset_selection"] = False

        # First try to extract full params (user might have typed "1000 USDC")
        params = await self._extract_lending_params(text.lower())

        if params.get("asset"):
            # User provided asset (and maybe amount)
            state.data["asset"] = params["asset"].upper()
            if params.get("amount"):
                state.data["amount"] = params["amount"]
                state.data["chain"] = params.get("chain", "base")
                state.step = WorkflowStep.FETCH_DATA.value
                return await self._handle_fetch_data(message, state, user_context)
            # Have asset but no amount - ask for amount with user context
            state.data["awaiting_amount"] = True
            return await self._ask_for_amount(
                params["asset"].upper(), user_context
            ), state

        # Check if it's a number selection
        user_input = text.upper()
        asset_list = ["USDC", "USDT", "DAI", "ETH", "WBTC"]

        if user_input.isdigit():
            index = int(user_input) - 1  # 1-based to 0-based
            if 0 <= index < len(asset_list):
                state.data["asset"] = asset_list[index]
                state.data["awaiting_amount"] = True
                return await self._ask_for_amount(
                    asset_list[index], user_context
                ), state

        # Check if it's a valid asset symbol
        if (
            user_input in [a.upper() for a in SUPPORTED_ASSETS]
            or user_input in asset_list
        ):
            state.data["asset"] = user_input
            state.data["awaiting_amount"] = True
            return await self._ask_for_amount(user_input, user_context), state

        # Invalid selection - show menu again
        state.data["awaiting_asset_selection"] = True
        response = self._get_invalid_asset_selection_response(
            text, user_context.language
        )
        return response, state

    async def _handle_amount_input(
        self,
        message: MessageContent,
        state: WorkflowState,
        user_context: UserContext,
    ) -> tuple[str, WorkflowState]:
        """
        Handle user's amount input after asset has been selected.

        User can respond with:
        - A number (100, 1000, 0.5)
        - "all" or "max" to deposit entire balance
        - Amount + asset confirmation (e.g., "100 USDC")
        """
        text = message.value.strip().lower()
        language = user_context.language
        asset = state.data.get("asset", "USDC")

        # Clear the awaiting flag
        state.data["awaiting_amount"] = False

        # Check for "all" or "max" keywords
        if text in ["all", "max", "todo", "tudo", "全部", "maximo", "máximo"]:
            # Use "all" as a special marker - will be handled by execution
            state.data["amount"] = "all"
            state.data["chain"] = state.data.get("chain", "base")
            state.step = WorkflowStep.FETCH_DATA.value
            return await self._handle_fetch_data(message, state, user_context)

        # Try to extract amount from message
        params = await self._extract_lending_params(text)

        # If user typed "100 USDC", params will have both
        if params.get("amount"):
            amount = params["amount"]
            # If they also specified asset, make sure it matches or update
            if params.get("asset"):
                asset = params["asset"].upper()
                state.data["asset"] = asset

            state.data["amount"] = amount
            state.data["chain"] = state.data.get("chain", "base")
            state.step = WorkflowStep.FETCH_DATA.value
            return await self._handle_fetch_data(message, state, user_context)

        # Try to parse as pure number
        try:
            # Remove commas and try to parse
            clean_text = text.replace(",", "").replace(" ", "")
            amount = float(clean_text)
            if amount > 0:
                state.data["amount"] = str(amount)
                state.data["chain"] = state.data.get("chain", "base")
                state.step = WorkflowStep.FETCH_DATA.value
                return await self._handle_fetch_data(message, state, user_context)
        except ValueError:
            pass

        # Invalid input - ask again
        state.data["awaiting_amount"] = True
        response = self._get_invalid_amount_response(text, asset, language)
        return response, state

    def _get_invalid_amount_response(
        self, user_input: str, asset: str, language: str
    ) -> str:
        """Generate response for invalid amount input."""
        msgs = {
            "en": f"""❌ I couldn't understand "{user_input}" as an amount.

Please enter a valid number for your **{asset}** deposit:

💡 *Examples:*
• `0.5` - deposit 0.5 {asset}
• `10` - deposit 10 {asset}
• `all` - deposit your entire balance

💬 Enter the amount to continue""",
            "es": f"""❌ No pude entender "{user_input}" como cantidad.

Por favor ingresa un número válido para tu depósito de **{asset}**:

💡 *Ejemplos:*
• `0.5` - depositar 0.5 {asset}
• `10` - depositar 10 {asset}
• `all` - depositar todo tu saldo

💬 Ingresa la cantidad para continuar""",
            "pt": f"""❌ Não consegui entender "{user_input}" como um valor.

Por favor digite um número válido para seu depósito de **{asset}**:

💡 *Exemplos:*
• `0.5` - depositar 0.5 {asset}
• `10` - depositar 10 {asset}
• `all` - depositar todo seu saldo

💬 Digite a quantia para continuar""",
            "zh": f"""❌ 我无法将 "{user_input}" 识别为金额。

请输入有效的 **{asset}** 存款金额：

💡 *示例：*
• `0.5` - 存入 0.5 {asset}
• `10` - 存入 10 {asset}
• `all` - 存入全部余额

💬 输入金额以继续""",
        }
        return msgs.get(language, msgs["en"])

    async def _handle_fetch_data(
        self,
        message: MessageContent,
        state: WorkflowState,
        user_context: UserContext,
    ) -> tuple[str, WorkflowState]:
        """Fetch vault data from Morpho/Aave.

        Like swap workflow:
        - Always show quote regardless of balance
        - Add confirmation prompt with yes/no instructions
        - Don't set execute_data here (only in _handle_execute after confirmation)
        """

        language = user_context.language
        asset = state.data.get("asset", "USDC")
        amount = state.data.get("amount", "0")
        chain = state.data.get("chain", "base")
        protocol_preference = state.data.get("protocol")  # User's protocol preference
        wallet_address = user_context.wallet_address

        # Handle "all" - convert to actual token amount using CoinGecko price
        if str(amount).lower() == "all":
            user_balance_usd = user_context.total_balance_usd
            token_price_usd = await self._get_token_price_usd(asset)

            if user_balance_usd > 0 and token_price_usd > 0:
                # Calculate token amount from USD balance (leave 10% for gas)
                available_usd = user_balance_usd * 0.90
                token_amount = available_usd / token_price_usd

                # Format without scientific notation
                amount = self._format_token_amount(token_amount)
                state.data["amount"] = amount

                logger.info(
                    f"[LendingWorkflow] Converted 'all' to {amount} {asset} "
                    f"(balance=${user_balance_usd:.2f}, price=${token_price_usd:.2f})"
                )
            else:
                # User has no balance
                amount = "0"
                state.data["amount"] = amount
                logger.info(
                    "[LendingWorkflow] User has no balance for 'all' conversion"
                )

        logger.info(
            f"[LendingWorkflow] Fetching vaults for {asset} on {chain}, preference={protocol_preference}"
        )

        # Clear any previous execute_data when fetching new quote
        state.execute_data = None

        vault_data = None

        # Respect user's protocol preference if specified
        if protocol_preference == "aave" and self._aave:
            # User explicitly wants Aave
            vault_data = await self._fetch_aave_market(asset, chain)
        elif protocol_preference == "morpho":
            # User explicitly wants Morpho
            vault_data = await self._fetch_morpho_vault(asset, chain)
        else:
            # No preference - try Morpho first, then Aave
            vault_data = await self._fetch_morpho_vault(asset, chain)
            if not vault_data and self._aave:
                vault_data = await self._fetch_aave_market(asset, chain)

        if not vault_data:
            # No vault available
            response = self._format_no_vault_available(asset, chain, language)
            state.step = WorkflowStep.CANCELLED.value
            state.cancelled = True
            return response, state

        # Store vault data
        state.data["vault"] = vault_data

        # Move to CONFIRM step - execute_data will be built after user confirms
        state.step = WorkflowStep.CONFIRM.value

        # Format quote response with confirmation prompt (async for price lookup)
        response = await self._format_vault_quote(
            vault_data=vault_data,
            asset=asset,
            amount=amount,
            user_context=user_context,
            language=language,
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
        action = state.data.get("action", "deposit")

        # Check for confirmation
        if self._is_confirmation(text):
            state.confirmed = True
            state.step = WorkflowStep.EXECUTE.value

            # Route to appropriate execute handler based on action
            if action == "withdraw":
                return await self._handle_withdraw_execute(message, state, user_context)
            # Call _handle_execute directly to check balance before showing "Ready to Execute"
            return await self._handle_execute(message, state, user_context)

        # Check for cancellation
        if self._is_cancellation(text):
            state.cancelled = True
            state.step = WorkflowStep.CANCELLED.value
            return self._format_cancelled(language), state

        # Check for modification (e.g., "change to 500 USDC")
        modification = await self._parse_modification(text)
        if modification:
            if modification.get("amount"):
                if action == "withdraw":
                    state.data["withdraw_amount"] = modification["amount"]
                else:
                    state.data["amount"] = modification["amount"]
            if modification.get("asset"):
                state.data["asset"] = modification["asset"].upper()

            # Re-fetch with new parameters
            if action == "withdraw":
                # For withdraw, go back to position selection or amount input
                position = state.data.get("selected_position")
                if position:
                    state.step = WorkflowStep.CONFIRM.value
                    return await self._show_withdraw_confirmation(
                        position,
                        modification.get(
                            "amount", state.data.get("withdraw_amount", "max")
                        ),
                        user_context,
                        state,
                    )
            else:
                state.step = WorkflowStep.FETCH_DATA.value
                return await self._handle_fetch_data(message, state, user_context)

        # Unclear response - ask again
        return self._ask_for_confirmation(language), state

    async def _handle_execute(
        self,
        message: MessageContent,
        state: WorkflowState,
        user_context: UserContext,
    ) -> tuple[str, WorkflowState]:
        """Handle execute step - transaction is done by frontend.

        IMPORTANT: Smart balance checking like swap workflow:
        - For stablecoins: compare requested amount against user balance
        - If insufficient: auto-adjust to 90% of available balance and re-fetch quote
        - If zero balance: show buy crypto message
        """
        language = user_context.language
        # Use 'or' to handle both missing keys AND None values
        asset = (state.data.get("asset") or "USDC").upper()
        amount = state.data.get("amount") or "0"
        chain = state.data.get("chain") or "base"
        vault_data = state.data.get("vault", {})

        user_balance = user_context.total_balance_usd

        # Get real token price for non-stablecoins
        token_price_usd = await self._get_token_price_usd(asset)

        # Handle "all" - convert to actual token amount (should have been done in fetch_data, but handle here too)
        if str(amount).lower() == "all":
            if user_balance > 0 and token_price_usd > 0:
                # Calculate token amount from USD balance (leave 10% for gas)
                available_usd = user_balance * 0.90
                token_amount = available_usd / token_price_usd
                amount = self._format_token_amount(token_amount)
                state.data["amount"] = amount
                logger.info(
                    f"[LendingWorkflow] Execute: Converted 'all' to {amount} {asset} "
                    f"(balance=${user_balance:.2f}, price=${token_price_usd:.2f})"
                )
            else:
                # User has no balance
                response = self._get_zero_balance_message(
                    asset=asset, language=language
                )
                state.error = "insufficient_balance"
                return response, state

        # Smart balance check: compare requested amount against user balance
        try:
            amount_float = float(str(amount).replace(",", ""))
        except (ValueError, TypeError):
            amount_float = 0

        has_sufficient_funds = True

        if asset.upper() in ("USDC", "USDT", "DAI", "BUSD", "FRAX"):
            # Stablecoin: direct USD comparison with 10% buffer for gas
            required_amount_usd = amount_float * 1.10
        else:
            # Non-stablecoin: use real price from CoinGecko
            required_amount_usd = (
                amount_float * token_price_usd * 1.10
            )  # 10% buffer for gas

        has_sufficient_funds = user_balance >= required_amount_usd

        logger.info(
            f"[LendingWorkflow] Balance check: requested={amount} {asset} "
            f"(price=${token_price_usd:.2f}, total~${required_amount_usd:.2f}), "
            f"balance=${user_balance:.2f}, sufficient={has_sufficient_funds}"
        )

        if not has_sufficient_funds:
            logger.info(
                f"[LendingWorkflow] Blocking execution - insufficient funds: "
                f"requested={amount} {asset}, balance=${user_balance:.2f}"
            )
            # Calculate recommended USD amount (90% of balance to leave room for gas)
            recommended_usd = max(0, user_balance * 0.90)

            # Convert USD to token amount using the token price
            # For stablecoins, 1:1 with USD
            # For non-stablecoins, divide USD by token price
            if asset.upper() in ("USDC", "USDT", "DAI", "BUSD", "FRAX"):
                recommended_token_amount = recommended_usd
            else:
                # Convert USD to token amount: $2.70 / $2302 per ETH = 0.00117 ETH
                recommended_token_amount = (
                    recommended_usd / token_price_usd if token_price_usd > 0 else 0
                )

            logger.info(
                f"[LendingWorkflow] Auto-adjusting: ${recommended_usd:.2f} USD = "
                f"{recommended_token_amount:.6f} {asset} (at ${token_price_usd:.2f}/{asset})"
            )

            # Auto-update state with recommended token amount and re-fetch quote
            # Use appropriate decimal places based on token type
            if recommended_token_amount >= 0.000001:  # Minimum viable amount
                if asset.upper() in ("USDC", "USDT", "DAI", "BUSD", "FRAX"):
                    formatted_amount = f"{recommended_token_amount:.2f}"
                else:
                    # For ETH/WBTC use more decimal places
                    formatted_amount = f"{recommended_token_amount:.6f}".rstrip(
                        "0"
                    ).rstrip(".")

                state.data["amount"] = formatted_amount
                state.step = WorkflowStep.FETCH_DATA.value
                # Show message that we're adjusting to available balance
                response = self._get_auto_adjust_message(
                    original_amount=amount,
                    recommended_amount=formatted_amount,
                    asset=asset,
                    recommended_usd=recommended_usd,
                    user_balance=user_balance,
                    language=language,
                )
                # Fetch new quote with adjusted amount
                new_quote_response, state = await self._handle_fetch_data(
                    message, state, user_context
                )
                return f"{response}\n\n{new_quote_response}", state
            # User has no usable balance - show buy crypto message
            response = self._get_zero_balance_message(
                asset=asset,
                language=language,
            )
            state.error = "insufficient_balance"
            return response, state

        # Build execute_data with all numeric fields as strings (for Pydantic validation)
        apy = vault_data.get("apy", 0)
        tvl = vault_data.get("tvl", 0)

        execute_data = self._build_execute_data(
            action_type="deposit",
            provider=vault_data.get("provider", "morpho"),
            chain=chain,
            amount=str(amount),
            # Vault-specific fields
            asset_symbol=asset,
            asset_address=vault_data.get("asset_address"),
            vault_address=vault_data.get("address")
            if vault_data.get("protocol") == "morpho"
            else None,
            pool_address=vault_data.get("address")
            if vault_data.get("protocol") != "morpho"
            else None,
            supply_apy=str(apy) if apy else None,
            available_liquidity_usd=str(tvl) if tvl else None,
            referral_code="0",
            slippage=0.5,
        )

        # Store execute_data in state
        state.execute_data = execute_data
        state.step = WorkflowStep.COMPLETED.value

        # Format ready-to-execute response
        response = self._format_ready_to_execute(state.data, language)
        return response, state

    async def _handle_withdraw_execute(
        self,
        message: MessageContent,
        state: WorkflowState,
        user_context: UserContext,
    ) -> tuple[str, WorkflowState]:
        """Handle withdraw execute step - build transaction for frontend.

        Uses morpho_withdraw MCP tool to build the withdrawal transaction.
        Frontend will handle the actual transaction signing and submission.
        """
        language = user_context.language
        position = state.data.get("selected_position", {})
        withdraw_amount = state.data.get("withdraw_amount", "max")
        wallet_address = user_context.wallet_address

        if not wallet_address:
            if language == "es":
                return "❌ Wallet no conectada. Por favor, conecta tu wallet.", state
            if language == "pt":
                return (
                    "❌ Carteira não conectada. Por favor, conecte sua carteira.",
                    state,
                )
            return "❌ Wallet not connected. Please connect your wallet.", state

        protocol = position.get("protocol", "morpho")
        asset = position.get("asset", "UNKNOWN")
        chain = position.get("chain", "base")
        vault_address = position.get("vault_address")
        vault_name = position.get("vault_name", f"{asset} Vault")

        # Build withdrawal transaction based on protocol
        if protocol == "morpho":
            if not vault_address:
                logger.error(
                    "[LendingWorkflow] Missing vault_address for Morpho withdraw"
                )
                if language == "es":
                    return "❌ Error: Falta la dirección del vault.", state
                if language == "pt":
                    return "❌ Erro: Endereço do vault ausente.", state
                return "❌ Error: Missing vault address.", state

            # Call morpho_withdraw MCP tool
            try:
                withdraw_result = await self._call_tool(
                    "morpho_withdraw",
                    {
                        "user_address": wallet_address,
                        "vault_address": vault_address,
                        "amount": str(withdraw_amount),
                        "chain": chain,
                    },
                )

                if not withdraw_result or withdraw_result.get("error"):
                    error_msg = (
                        withdraw_result.get("error", "Unknown error")
                        if withdraw_result
                        else "No response"
                    )
                    logger.error(
                        f"[LendingWorkflow] morpho_withdraw failed: {error_msg}"
                    )
                    if language == "es":
                        return f"❌ Error al preparar el retiro: {error_msg}", state
                    if language == "pt":
                        return f"❌ Erro ao preparar a retirada: {error_msg}", state
                    return f"❌ Error preparing withdrawal: {error_msg}", state

                # Build execute_data for frontend
                execute_data = self._build_execute_data(
                    action_type="withdraw",
                    provider="morpho",
                    chain=chain,
                    amount=str(withdraw_amount),
                    asset_symbol=asset,
                    asset_address=position.get("asset_address"),
                    vault_address=vault_address,
                    # Transaction data from MCP tool
                    tx_to=withdraw_result.get("to"),
                    tx_data=withdraw_result.get("data"),
                    tx_value=withdraw_result.get("value", "0"),
                )

            except Exception as e:
                logger.error(f"[LendingWorkflow] Error calling morpho_withdraw: {e}")
                if language == "es":
                    return f"❌ Error al preparar el retiro: {e!s}", state
                if language == "pt":
                    return f"❌ Erro ao preparar a retirada: {e!s}", state
                return f"❌ Error preparing withdrawal: {e!s}", state

        elif protocol == "aave":
            # Call aave_withdraw_supply MCP tool
            try:
                withdraw_result = await self._call_tool(
                    "aave_withdraw_supply",
                    {
                        "user_address": wallet_address,
                        "asset_symbol": asset,
                        "amount": str(withdraw_amount),
                        "chain": chain,
                    },
                )

                if not withdraw_result or withdraw_result.get("error"):
                    error_msg = (
                        withdraw_result.get("error", "Unknown error")
                        if withdraw_result
                        else "No response"
                    )
                    logger.error(
                        f"[LendingWorkflow] aave_withdraw_supply failed: {error_msg}"
                    )
                    if language == "es":
                        return f"❌ Error al preparar el retiro: {error_msg}", state
                    if language == "pt":
                        return f"❌ Erro ao preparar a retirada: {error_msg}", state
                    return f"❌ Error preparing withdrawal: {error_msg}", state

                # Build execute_data for frontend
                execute_data = self._build_execute_data(
                    action_type="withdraw",
                    provider="aave",
                    chain=chain,
                    amount=str(withdraw_amount),
                    asset_symbol=asset,
                    asset_address=withdraw_result.get("asset_address"),
                    pool_address=withdraw_result.get("to"),
                    tx_to=withdraw_result.get("to"),
                    tx_data=withdraw_result.get("data"),
                    tx_value=withdraw_result.get("value", "0"),
                )

            except Exception as e:
                logger.error(
                    f"[LendingWorkflow] Error calling aave_withdraw_supply: {e}"
                )
                if language == "es":
                    return f"❌ Error al preparar el retiro: {e!s}", state
                if language == "pt":
                    return f"❌ Erro ao preparar a retirada: {e!s}", state
                return f"❌ Error preparing withdrawal: {e!s}", state
        elif language == "es":
            return f"❌ Protocolo no soportado: {protocol}", state
        elif language == "pt":
            return f"❌ Protocolo não suportado: {protocol}", state
        else:
            return f"❌ Unsupported protocol: {protocol}", state

        # Store execute_data in state
        state.execute_data = execute_data
        state.step = WorkflowStep.COMPLETED.value

        # Format ready-to-execute response for withdrawal
        response = self._format_withdraw_ready_to_execute(
            asset=asset,
            amount=withdraw_amount,
            vault_name=vault_name,
            protocol=protocol,
            language=language,
        )
        return response, state

    def _format_withdraw_ready_to_execute(
        self,
        asset: str,
        amount: str,
        vault_name: str,
        protocol: str,
        language: str,
    ) -> str:
        """Format the ready-to-execute message for withdrawal."""
        if language == "es":
            return (
                f"✅ **¡Listo para retirar!**\n\n"
                f"📤 **Retirando:** {amount} {asset}\n"
                f"🏦 **De:** {vault_name} ({protocol.upper()})\n\n"
                f"Por favor, confirma la transacción en tu wallet."
            )
        if language == "pt":
            return (
                f"✅ **Pronto para retirar!**\n\n"
                f"📤 **Retirando:** {amount} {asset}\n"
                f"🏦 **De:** {vault_name} ({protocol.upper()})\n\n"
                f"Por favor, confirme a transação na sua carteira."
            )
        return (
            f"✅ **Ready to withdraw!**\n\n"
            f"📤 **Withdrawing:** {amount} {asset}\n"
            f"🏦 **From:** {vault_name} ({protocol.upper()})\n\n"
            f"Please confirm the transaction in your wallet."
        )

    def _get_funding_recommendation(self, asset: str, language: str) -> str:
        """
        Get a helpful recommendation for users with insufficient funds.

        This is shown before the vault quote to guide users on how to fund their wallet.
        Matches the swap workflow behavior.
        """
        recommendations = {
            "en": f"""💡 **Heads up:** Your portfolio appears to have limited funds.

To complete this deposit, you'll need **{asset}** in your wallet.

**Get started:**
• 💳 Say **"buy crypto"** to purchase with card/Apple Pay/Google Pay
• 📥 Or transfer {asset} from another wallet

Here's the deposit quote you requested:
""",
            "es": f"""💡 **Aviso:** Tu portafolio parece tener fondos limitados.

Para completar este depósito, necesitarás **{asset}** en tu billetera.

**Comienza:**
• 💳 Di **"comprar cripto"** para comprar con tarjeta
• 📥 O transfiere {asset} desde otra billetera

Aquí está la cotización de depósito que solicitaste:
""",
            "pt": f"""💡 **Atenção:** Seu portfólio parece ter fundos limitados.

Para completar este depósito, você precisará de **{asset}** na sua carteira.

**Comece:**
• 💳 Diga **"comprar cripto"** para comprar com cartão
• 📥 Ou transfira {asset} de outra carteira

Aqui está a cotação de depósito que você solicitou:
""",
            "zh": f"""💡 **注意：** 您的投资组合资金似乎有限。

要完成此存款，您的钱包中需要 **{asset}**。

**开始：**
• 💳 说 **"买加密货币"** 用卡购买
• 📥 或从其他钱包转入 {asset}

以下是您请求的存款报价：
""",
        }
        return recommendations.get(language, recommendations["en"])

    def _build_insufficient_balance_message(
        self,
        asset: str,
        amount: str,
        user_balance: float,
        language: str,
    ) -> str:
        """Build message when user has insufficient balance to execute deposit."""
        messages = {
            # Note: Only USDC is available for purchase via card
            "en": f"""❌ **Unable to execute deposit**

**Deposit requested:** {amount} {asset}
**Your current balance:** ${user_balance:.2f}

You don't have enough {asset} in your wallet to complete this deposit.

---

**💳 Get crypto to start earning yield:**

1. **Buy USDC with card/Apple Pay/Google Pay:**
   Say: **"buy crypto"** or **"buy 100"**

2. **Transfer {asset} from another wallet:**
   Send {asset} to your Anvil wallet address

---

Once you have {asset} in your wallet, come back and try:
**"deposit {amount} {asset}"**
""",
            "es": f"""❌ **No se puede ejecutar el depósito**

**Depósito solicitado:** {amount} {asset}
**Tu saldo actual:** ${user_balance:.2f}

No tienes suficiente {asset} en tu billetera.

**💳 Obtén cripto:**
• Di: **"comprar cripto"** para comprar USDC con tarjeta
• O transfiere {asset} desde otra billetera
""",
            "pt": f"""❌ **Não é possível executar o depósito**

**Depósito solicitado:** {amount} {asset}
**Seu saldo atual:** ${user_balance:.2f}

Você não tem {asset} suficiente na sua carteira.

**💳 Obtenha cripto:**
• Diga: **"comprar cripto"** para comprar USDC com cartão
• Ou transfira {asset} de outra carteira
""",
        }
        return messages.get(language, messages["en"])

    # ========================================
    # Data Fetching
    # ========================================

    async def _fetch_morpho_vault(
        self,
        asset: str,
        chain: str,
    ) -> dict[str, Any] | None:
        """Fetch best Morpho vault for asset."""

        if not self._morpho:
            logger.warning("[LendingWorkflow] Morpho gateway not available")
            return None

        try:
            # Map ETH to WETH for vault lookup (Morpho vaults use WETH, not ETH)
            lookup_asset = asset.upper()
            if lookup_asset == "ETH":
                lookup_asset = "WETH"
                logger.info("[LendingWorkflow] Mapped ETH → WETH for vault lookup")

            vaults = await self._morpho.get_vaults(asset=lookup_asset, chain=chain)

            if not vaults:
                logger.info(
                    f"[LendingWorkflow] No Morpho vaults for {lookup_asset} on {chain}"
                )
                return None

            # Filter whitelisted vaults and exclude problematic ones
            valid_vaults = [
                v for v in vaults if v.whitelisted and v.address not in EXCLUDED_VAULTS
            ]

            if not valid_vaults:
                logger.info(
                    f"[LendingWorkflow] No valid whitelisted vaults for {asset}"
                )
                return None

            # Sort by APY (highest first)
            sorted_vaults = sorted(
                valid_vaults, key=lambda v: float(v.apy), reverse=True
            )
            best_vault = sorted_vaults[0]

            logger.info(
                f"[LendingWorkflow] Best vault: {best_vault.name} ({best_vault.apy}% APY)"
            )

            return {
                "protocol": "morpho",
                "provider": "morpho",
                "name": best_vault.name,
                "address": best_vault.address,
                "asset_address": best_vault.asset_address,
                "asset_symbol": best_vault.asset,
                "apy": float(best_vault.apy),
                "tvl": float(best_vault.total_assets),
                "chain": chain,
            }

        except Exception as e:
            logger.error(f"[LendingWorkflow] Error fetching Morpho vaults: {e}")
            return None

    async def _fetch_aave_market(
        self,
        asset: str,
        chain: str,
    ) -> dict[str, Any] | None:
        """Fetch Aave V3 market for asset."""

        if not self._aave:
            logger.warning("[LendingWorkflow] Aave gateway not available")
            return None

        try:
            market = await self._aave.get_market_details(asset=asset, chain=chain)

            if not market or not market.is_suppliable:
                logger.info(
                    f"[LendingWorkflow] No active Aave market for {asset} on {chain}"
                )
                return None

            pool_address = AAVE_POOL_ADDRESSES.get(chain)
            if not pool_address:
                logger.warning(f"[LendingWorkflow] No Aave pool address for {chain}")
                return None

            logger.info(
                f"[LendingWorkflow] Aave market: {market.symbol} ({market.supply_apy}% APY)"
            )

            return {
                "protocol": "aave_v3",
                "provider": "aave",
                "name": f"Aave V3 {market.symbol}",
                "address": pool_address,
                "asset_address": market.asset_address,
                "asset_symbol": market.symbol,
                "apy": float(market.supply_apy),
                "tvl": float(market.total_supplied_usd),
                "chain": chain,
                "available_liquidity_usd": float(market.available_liquidity_usd),
            }

        except Exception as e:
            logger.error(f"[LendingWorkflow] Error fetching Aave market: {e}")
            return None

    # ========================================
    # Parameter Extraction
    # ========================================

    async def _extract_lending_params(self, text: str) -> dict[str, Any]:
        """Extract lending parameters from text."""

        params: dict[str, Any] = {}

        # Try LLM extraction first
        if self._llm:
            try:
                llm_params = await self._extract_params_with_llm(
                    text,
                    param_schema={
                        "asset": "Token symbol to deposit (USDC, ETH, DAI, etc.)",
                        "amount": "Amount to deposit (numeric value)",
                        "chain": "Blockchain network (base, ethereum, polygon, arbitrum, etc.)",
                        "protocol": "DeFi protocol preference (aave, morpho, or null if not specified)",
                    },
                )
                if llm_params:
                    params.update(llm_params)
            except Exception as e:
                logger.warning(f"[LendingWorkflow] LLM extraction failed: {e}")

        # Regex fallback for amount
        if not params.get("amount"):
            amount_match = re.search(
                r"(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:usdc|usdt|dai|eth|wbtc)?", text, re.I
            )
            if amount_match:
                params["amount"] = amount_match.group(1).replace(",", "")

        # Regex fallback for asset
        if not params.get("asset"):
            for key, info in SUPPORTED_ASSETS.items():
                if key in text or info["symbol"].lower() in text:
                    params["asset"] = info["symbol"]
                    break

        # Regex fallback for protocol preference
        if not params.get("protocol"):
            text_lower = text.lower()
            if "aave" in text_lower:
                params["protocol"] = "aave"
            elif "morpho" in text_lower:
                params["protocol"] = "morpho"
            elif "compound" in text_lower:
                params["protocol"] = "compound"

        # Regex fallback for chain
        if not params.get("chain"):
            text_lower = text.lower()
            if "ethereum" in text_lower or "mainnet" in text_lower:
                params["chain"] = "ethereum"
            elif "polygon" in text_lower or "matic" in text_lower:
                params["chain"] = "polygon"
            elif "arbitrum" in text_lower:
                params["chain"] = "arbitrum"
            elif "optimism" in text_lower:
                params["chain"] = "optimism"
            else:
                params["chain"] = "base"  # Default to Base

        return params

    async def _parse_modification(self, text: str) -> dict[str, Any] | None:
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

        # Check for asset change
        for key, info in SUPPORTED_ASSETS.items():
            if key in text or info["symbol"].lower() in text:
                modification["asset"] = info["symbol"]
                break

        return modification if modification else None

    # ========================================
    # Response Formatting
    # ========================================

    async def _get_asset_selection_prompt(self, user_context: UserContext) -> str:
        """
        Build asset selection prompt with current APY rates and user context.

        Includes:
        - Knowledge paragraph explaining DeFi lending benefits
        - User's current balance (if available)
        - Live APY rates from Morpho/Aave
        - Personalized recommendations based on portfolio state
        """
        language = user_context.language

        # Try to fetch current APY rates for popular assets
        apy_rates = await self._fetch_asset_apy_rates()

        # Build asset list with APY rates
        asset_lines = []
        assets = [
            ("USDC", "💵", "USD Coin"),
            ("USDT", "💵", "Tether"),
            ("DAI", "💰", "Dai"),
            ("ETH", "Ξ", "Ethereum"),
            ("WBTC", "₿", "Wrapped Bitcoin"),
        ]

        for i, (symbol, emoji, name) in enumerate(assets, 1):
            apy_info = ""
            if apy_rates.get(symbol.lower()):
                apy = apy_rates[symbol.lower()]
                apy_info = f" • **{apy:.2f}% APY**"
            asset_lines.append(f"**{i}.** {emoji} **{symbol}**{apy_info}")

        asset_list = "\n".join(asset_lines)

        # Build user context section
        user_balance_section = self._build_user_balance_section(user_context, language)

        # Build knowledge section
        knowledge_section = self._get_lending_knowledge(language)

        # Build recommendation based on user context
        recommendation = self._get_personalized_recommendation(
            user_context, apy_rates, language
        )

        msgs = {
            "en": f"""🏦 **DeFi Lending - Earn Passive Income**

{knowledge_section}

{user_balance_section}

**Select an asset to deposit:**

{asset_list}

{recommendation}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Reply with:**
• A number (1-5) to select an asset
• Or type the asset name with amount (e.g., `1000 USDC`)

💡 Powered by **Morpho** and **Aave V3** on Base""",
            "es": f"""🏦 **Préstamos DeFi - Gana Ingresos Pasivos**

{knowledge_section}

{user_balance_section}

**Selecciona un activo para depositar:**

{asset_list}

{recommendation}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Responde con:**
• Un número (1-5) para seleccionar
• O escribe el activo con cantidad (ej: `1000 USDC`)

💡 Potenciado por **Morpho** y **Aave V3** en Base""",
            "pt": f"""🏦 **Empréstimos DeFi - Ganhe Renda Passiva**

{knowledge_section}

{user_balance_section}

**Selecione um ativo para depositar:**

{asset_list}

{recommendation}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Responda com:**
• Um número (1-5) para selecionar
• Ou digite o ativo com quantidade (ex: `1000 USDC`)

💡 Powered by **Morpho** e **Aave V3** na Base""",
            "zh": f"""🏦 **DeFi 借贷 - 赚取被动收入**

{knowledge_section}

{user_balance_section}

**选择要存入的资产：**

{asset_list}

{recommendation}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**回复：**
• 数字 (1-5) 选择资产
• 或输入资产和金额（如：`1000 USDC`）

💡 由 **Morpho** 和 **Aave V3** 在 Base 上提供支持""",
        }
        return msgs.get(language, msgs["en"])

    def _build_user_balance_section(
        self, user_context: UserContext, language: str
    ) -> str:
        """Build user balance context section."""
        if not user_context.is_authenticated:
            return ""

        balance = user_context.total_balance_usd
        portfolio_state = user_context.portfolio_state

        if portfolio_state == "empty" or balance < 1:
            msgs = {
                "en": "💰 **Your Balance:** $0.00\n\n💡 **Tip:** Buy crypto first with `buy USDC` to start earning yield!",
                "es": "💰 **Tu Saldo:** $0.00\n\n💡 **Consejo:** ¡Compra cripto primero con `buy USDC` para comenzar a ganar rendimiento!",
                "pt": "💰 **Seu Saldo:** $0.00\n\n💡 **Dica:** Compre cripto primeiro com `buy USDC` para começar a ganhar rendimento!",
                "zh": "💰 **您的余额：** $0.00\n\n💡 **提示：** 先用 `buy USDC` 购买加密货币，开始赚取收益！",
            }
        elif portfolio_state == "starter" or balance < 100:
            msgs = {
                "en": f"💰 **Your Balance:** ~${balance:,.2f}\n\n💡 **Tip:** Even small deposits earn yield! Try depositing what you have.",
                "es": f"💰 **Tu Saldo:** ~${balance:,.2f}\n\n💡 **Consejo:** ¡Incluso depósitos pequeños generan rendimiento!",
                "pt": f"💰 **Seu Saldo:** ~${balance:,.2f}\n\n💡 **Dica:** Mesmo depósitos pequenos geram rendimento!",
                "zh": f"💰 **您的余额：** ~${balance:,.2f}\n\n💡 **提示：** 即使小额存款也能赚取收益！",
            }
        else:
            msgs = {
                "en": f"💰 **Your Balance:** ~${balance:,.2f}\n\n✨ Ready to put your crypto to work!",
                "es": f"💰 **Tu Saldo:** ~${balance:,.2f}\n\n✨ ¡Listo para poner tu cripto a trabajar!",
                "pt": f"💰 **Seu Saldo:** ~${balance:,.2f}\n\n✨ Pronto para colocar seu cripto para trabalhar!",
                "zh": f"💰 **您的余额：** ~${balance:,.2f}\n\n✨ 准备让您的加密货币为您工作！",
            }

        return msgs.get(language, msgs["en"])

    def _get_lending_knowledge(self, language: str) -> str:
        """Get knowledge paragraph about DeFi lending."""
        msgs = {
            "en": """**What is DeFi Lending?**
Deposit your crypto into secure, audited vaults and earn yield automatically.
Your funds are supplied to borrowers through smart contracts, generating
interest for you 24/7. No lockups - withdraw anytime.""",
            "es": """**¿Qué es el Préstamo DeFi?**
Deposita tu cripto en vaults seguros y auditados y gana rendimiento automáticamente.
Tus fondos se prestan a través de contratos inteligentes, generando
intereses para ti 24/7. Sin bloqueos - retira cuando quieras.""",
            "pt": """**O que é Empréstimo DeFi?**
Deposite seu cripto em cofres seguros e auditados e ganhe rendimento automaticamente.
Seus fundos são emprestados através de contratos inteligentes, gerando
juros para você 24/7. Sem bloqueios - retire quando quiser.""",
            "zh": """**什么是 DeFi 借贷？**
将您的加密货币存入安全、经过审计的金库，自动赚取收益。
您的资金通过智能合约借给借款人，为您
24/7 产生利息。无锁定期 - 随时可以提取。""",
        }
        return msgs.get(language, msgs["en"])

    def _get_personalized_recommendation(
        self,
        user_context: UserContext,
        apy_rates: dict[str, float],
        language: str,
    ) -> str:
        """Get personalized recommendation based on user context."""
        # Find best APY
        best_asset = None
        best_apy = 0.0
        for asset, apy in apy_rates.items():
            if apy > best_apy:
                best_apy = apy
                best_asset = asset.upper()

        if not best_asset:
            return ""

        balance = user_context.total_balance_usd

        # Calculate potential monthly earnings
        monthly_earnings = (balance * (best_apy / 100)) / 12 if balance > 0 else 0

        if balance > 100 and monthly_earnings > 0.5:
            msgs = {
                "en": f"📈 **Recommended:** {best_asset} ({best_apy:.2f}% APY)\n💵 Potential monthly earnings: ~${monthly_earnings:.2f}",
                "es": f"📈 **Recomendado:** {best_asset} ({best_apy:.2f}% APY)\n💵 Ganancias mensuales potenciales: ~${monthly_earnings:.2f}",
                "pt": f"📈 **Recomendado:** {best_asset} ({best_apy:.2f}% APY)\n💵 Ganhos mensais potenciais: ~${monthly_earnings:.2f}",
                "zh": f"📈 **推荐：** {best_asset} ({best_apy:.2f}% APY)\n💵 潜在月收益：~${monthly_earnings:.2f}",
            }
            return msgs.get(language, msgs["en"])
        if best_apy > 5:
            msgs = {
                "en": f"📈 **Top Yield:** {best_asset} at {best_apy:.2f}% APY",
                "es": f"📈 **Mayor Rendimiento:** {best_asset} al {best_apy:.2f}% APY",
                "pt": f"📈 **Maior Rendimento:** {best_asset} a {best_apy:.2f}% APY",
                "zh": f"📈 **最高收益：** {best_asset} {best_apy:.2f}% APY",
            }
            return msgs.get(language, msgs["en"])

        return ""

    async def _fetch_asset_apy_rates(self) -> dict[str, float]:
        """
        Fetch current APY rates for supported assets.

        Tries Morpho first, then Aave as fallback.
        Returns dict mapping asset symbol (lowercase) to APY percentage.
        """
        rates = {}

        # Try to get rates from Morpho
        if self._morpho:
            try:
                for asset in ["USDC", "USDT", "DAI", "ETH", "WBTC"]:
                    vault_data = await self._fetch_morpho_vault(asset, "base")
                    if vault_data and vault_data.get("apy"):
                        rates[asset.lower()] = vault_data["apy"]
            except Exception as e:
                logger.warning(
                    f"[LendingWorkflow] Failed to fetch Morpho APY rates: {e}"
                )

        # Fill missing rates from Aave
        if self._aave:
            try:
                for asset in ["USDC", "USDT", "DAI", "ETH", "WBTC"]:
                    if asset.lower() not in rates:
                        market_data = await self._fetch_aave_market(asset, "base")
                        if market_data and market_data.get("apy"):
                            rates[asset.lower()] = market_data["apy"]
            except Exception as e:
                logger.warning(f"[LendingWorkflow] Failed to fetch Aave APY rates: {e}")

        return rates

    def _get_invalid_asset_selection_response(
        self, user_input: str, language: str
    ) -> str:
        """Response when user enters invalid asset selection."""
        msgs = {
            "en": f"""❌ **Invalid selection:** "{user_input}"

Please enter:
• A number from **1-5** to select an asset
• Or type a valid asset like **USDC**, **ETH**, **DAI**
• Or include an amount like **1000 USDC**

**Available assets:** USDC, USDT, DAI, ETH, WBTC""",
            "es": f"""❌ **Selección inválida:** "{user_input}"

Por favor ingresa:
• Un número del **1-5** para seleccionar
• O escribe un activo válido como **USDC**, **ETH**, **DAI**
• O incluye una cantidad como **1000 USDC**

**Activos disponibles:** USDC, USDT, DAI, ETH, WBTC""",
            "pt": f"""❌ **Seleção inválida:** "{user_input}"

Por favor insira:
• Um número de **1-5** para selecionar
• Ou digite um ativo válido como **USDC**, **ETH**, **DAI**
• Ou inclua uma quantidade como **1000 USDC**

**Ativos disponíveis:** USDC, USDT, DAI, ETH, WBTC""",
            "zh": f"""❌ **选择无效：** "{user_input}"

请输入：
• **1-5** 之间的数字选择资产
• 或输入有效资产如 **USDC**, **ETH**, **DAI**
• 或包含金额如 **1000 USDC**

**可用资产：** USDC, USDT, DAI, ETH, WBTC""",
        }
        return msgs.get(language, msgs["en"])

    def _ask_for_asset(self, language: str) -> str:
        """Ask user which asset to deposit (legacy fallback)."""

        msgs = {
            "en": """💰 **Earn Yield on Your Crypto**

Deposit into DeFi vaults to earn passive income. Which asset would you like to deposit?

**Available Assets:**
1. 💵 **USDC** (USD Coin)
2. 💵 **USDT** (Tether)
3. 💰 **DAI** (Dai)
4. Ξ **ETH** (Ethereum)
5. ₿ **WBTC** (Wrapped Bitcoin)

💬 Reply with the asset name (e.g., "USDC" or "1000 USDC")""",
            "es": """💰 **Gana Rendimiento con tus Cripto**

Deposita en vaults DeFi para ganar ingresos pasivos. ¿Qué activo te gustaría depositar?

**Activos Disponibles:**
1. 💵 **USDC** (USD Coin)
2. 💵 **USDT** (Tether)
3. 💰 **DAI** (Dai)
4. Ξ **ETH** (Ethereum)
5. ₿ **WBTC** (Wrapped Bitcoin)

💬 Responde con el nombre del activo (ej: "USDC" o "1000 USDC")""",
            "pt": """💰 **Ganhe Rendimento com suas Cripto**

Deposite em vaults DeFi para ganhar renda passiva. Qual ativo você gostaria de depositar?

**Ativos Disponíveis:**
1. 💵 **USDC** (USD Coin)
2. 💵 **USDT** (Tether)
3. 💰 **DAI** (Dai)
4. Ξ **ETH** (Ethereum)
5. ₿ **WBTC** (Wrapped Bitcoin)

💬 Responda com o nome do ativo (ex: "USDC" ou "1000 USDC")""",
            "zh": """💰 **赚取加密货币收益**

存入 DeFi 金库以赚取被动收入。您想存入哪种资产？

**可用资产：**
1. 💵 **USDC** (USD Coin)
2. 💵 **USDT** (Tether)
3. 💰 **DAI** (Dai)
4. Ξ **ETH** (以太坊)
5. ₿ **WBTC** (封装比特币)

💬 回复资产名称（例如："USDC" 或 "1000 USDC"）""",
        }

        return msgs.get(language, msgs["en"])

    async def _ask_for_amount(self, asset: str, user_context: UserContext) -> str:
        """Ask user for deposit amount with balance context and smart examples."""

        language = user_context.language
        asset_info = SUPPORTED_ASSETS.get(asset.lower(), {"emoji": "💰", "name": asset})
        emoji = asset_info["emoji"]

        # Build user balance section
        balance_section = self._build_amount_balance_section(
            user_context, asset, language
        )

        # Get token price for smart examples
        token_price_usd = await self._get_token_price_usd(asset)
        user_balance_usd = user_context.total_balance_usd

        # Calculate smart examples based on user's actual balance
        examples_section = self._build_smart_examples(
            asset, user_balance_usd, token_price_usd, language
        )

        msgs = {
            "en": f"""{emoji} **Deposit {asset}**

{balance_section}

How much **{asset}** would you like to deposit?

{examples_section}

💬 Enter the amount to continue""",
            "es": f"""{emoji} **Depositar {asset}**

{balance_section}

¿Cuánto **{asset}** te gustaría depositar?

{examples_section}

💬 Ingresa la cantidad para continuar""",
            "pt": f"""{emoji} **Depositar {asset}**

{balance_section}

Quanto **{asset}** você gostaria de depositar?

{examples_section}

💬 Digite a quantia para continuar""",
            "zh": f"""{emoji} **存入 {asset}**

{balance_section}

您想存入多少 **{asset}**？

{examples_section}

💬 输入金额以继续""",
        }

        return msgs.get(language, msgs["en"])

    def _build_smart_examples(
        self,
        asset: str,
        user_balance_usd: float,
        token_price_usd: float,
        language: str,
    ) -> str:
        """Build balance-appropriate examples for deposit amounts."""

        # Calculate how much of this token the user can afford
        if token_price_usd > 0:
            max_token_amount = user_balance_usd / token_price_usd
        else:
            max_token_amount = user_balance_usd  # Assume stablecoin

        # Format examples based on actual balance
        if user_balance_usd < 1:
            # Very low balance - just show "all" option
            msgs = {
                "en": "💡 *Tip:* Even small deposits earn yield! Say `all` to deposit your entire balance.",
                "es": "💡 *Consejo:* ¡Incluso pequeños depósitos generan rendimiento! Di `all` para depositar todo tu saldo.",
                "pt": "💡 *Dica:* Mesmo pequenos depósitos geram rendimento! Diga `all` para depositar todo seu saldo.",
                "zh": "💡 *提示：* 即使小额存款也能赚取收益！说 `all` 存入您的全部余额。",
            }
        elif user_balance_usd < 10:
            # Small balance - show realistic small amounts
            small_amount = max_token_amount * 0.5  # 50% of max

            # Format based on asset type
            if asset.upper() in ("USDC", "USDT", "DAI"):
                example1 = f"{small_amount:.2f}"
                example2 = f"{max_token_amount * 0.9:.2f}"
            else:
                # For crypto like ETH, use more decimals
                example1 = self._format_token_amount(small_amount)
                example2 = self._format_token_amount(max_token_amount * 0.9)

            msgs = {
                "en": f"""💡 *Examples based on your balance:*
• `{example1}` (~50% of your balance)
• `{example2}` (~90% of your balance)
• `all` (deposit your entire {asset} balance)""",
                "es": f"""💡 *Ejemplos basados en tu saldo:*
• `{example1}` (~50% de tu saldo)
• `{example2}` (~90% de tu saldo)
• `all` (depositar todo tu saldo de {asset})""",
                "pt": f"""💡 *Exemplos baseados no seu saldo:*
• `{example1}` (~50% do seu saldo)
• `{example2}` (~90% do seu saldo)
• `all` (depositar todo seu saldo de {asset})""",
                "zh": f"""💡 *基于您余额的示例：*
• `{example1}` (~50% 的余额)
• `{example2}` (~90% 的余额)
• `all` (存入全部 {asset} 余额)""",
            }
        # Reasonable balance - show meaningful amounts
        elif asset.upper() in ("USDC", "USDT", "DAI"):
            # Stablecoins - show round numbers
            example1 = min(10, user_balance_usd * 0.3)
            example2 = min(50, user_balance_usd * 0.5)
            example3 = user_balance_usd * 0.9

            msgs = {
                "en": f"""💡 *Examples:*
• `{example1:.0f}` (~${example1:.0f})
• `{example2:.0f}` (~${example2:.0f})
• `all` (deposit ~${example3:.0f} {asset})""",
                "es": f"""💡 *Ejemplos:*
• `{example1:.0f}` (~${example1:.0f})
• `{example2:.0f}` (~${example2:.0f})
• `all` (depositar ~${example3:.0f} {asset})""",
                "pt": f"""💡 *Exemplos:*
• `{example1:.0f}` (~${example1:.0f})
• `{example2:.0f}` (~${example2:.0f})
• `all` (depositar ~${example3:.0f} {asset})""",
                "zh": f"""💡 *示例：*
• `{example1:.0f}` (~${example1:.0f})
• `{example2:.0f}` (~${example2:.0f})
• `all` (存入 ~${example3:.0f} {asset})""",
            }
        else:
            # Crypto tokens - calculate token amounts
            example1 = self._format_token_amount(max_token_amount * 0.3)
            example2 = self._format_token_amount(max_token_amount * 0.5)
            example3 = self._format_token_amount(max_token_amount * 0.9)

            msgs = {
                "en": f"""💡 *Examples based on your balance:*
• `{example1}` (~30% of your balance)
• `{example2}` (~50% of your balance)
• `all` (deposit ~{example3} {asset})""",
                "es": f"""💡 *Ejemplos basados en tu saldo:*
• `{example1}` (~30% de tu saldo)
• `{example2}` (~50% de tu saldo)
• `all` (depositar ~{example3} {asset})""",
                "pt": f"""💡 *Exemplos baseados no seu saldo:*
• `{example1}` (~30% do seu saldo)
• `{example2}` (~50% do seu saldo)
• `all` (depositar ~{example3} {asset})""",
                "zh": f"""💡 *基于您余额的示例：*
• `{example1}` (~30% 的余额)
• `{example2}` (~50% 的余额)
• `all` (存入 ~{example3} {asset})""",
            }

        return msgs.get(language, msgs["en"])

    def _format_token_amount(self, amount: float) -> str:
        """Format token amount for display, avoiding scientific notation."""
        if amount == 0:
            return "0"
        if amount < 0.0001:
            return f"{amount:.8f}".rstrip("0").rstrip(".")
        if amount < 0.01:
            return f"{amount:.6f}".rstrip("0").rstrip(".")
        if amount < 1:
            return f"{amount:.4f}".rstrip("0").rstrip(".")
        if amount < 100:
            return f"{amount:.2f}".rstrip("0").rstrip(".")
        return f"{amount:.0f}"

    def _build_amount_balance_section(
        self,
        user_context: UserContext,
        asset: str,
        language: str,
    ) -> str:
        """Build balance section for amount prompt."""
        if not user_context.is_authenticated:
            return ""

        balance = user_context.total_balance_usd
        portfolio_state = user_context.portfolio_state

        if portfolio_state == "empty" or balance < 1:
            # Note: Only USDC is available for purchase, so always suggest "buy crypto" or "buy USDC"
            msgs = {
                "en": f"💰 **Your Balance:** $0.00\n\n⚠️ You'll need to get {asset} first:\n• Say `buy crypto` to purchase USDC with card\n• Or transfer {asset} from another wallet",
                "es": f"💰 **Tu Saldo:** $0.00\n\n⚠️ Necesitas obtener {asset} primero:\n• Di `comprar cripto` para comprar USDC con tarjeta\n• O transfiere {asset} desde otra billetera",
                "pt": f"💰 **Seu Saldo:** $0.00\n\n⚠️ Você precisa obter {asset} primeiro:\n• Diga `comprar cripto` para comprar USDC com cartão\n• Ou transfira {asset} de outra carteira",
                "zh": f"💰 **您的余额：** $0.00\n\n⚠️ 您需要先获取 {asset}：\n• 说 `买加密货币` 用卡购买 USDC\n• 或从其他钱包转入 {asset}",
            }
        elif balance < 100:
            msgs = {
                "en": f"💰 **Your Balance:** ~${balance:,.2f}\n\n💡 Even small deposits earn yield! Start with what you have.",
                "es": f"💰 **Tu Saldo:** ~${balance:,.2f}\n\n💡 ¡Incluso depósitos pequeños generan rendimiento! Comienza con lo que tienes.",
                "pt": f"💰 **Seu Saldo:** ~${balance:,.2f}\n\n💡 Mesmo depósitos pequenos geram rendimento! Comece com o que você tem.",
                "zh": f"💰 **您的余额：** ~${balance:,.2f}\n\n💡 即使小额存款也能赚取收益！从您拥有的开始。",
            }
        else:
            msgs = {
                "en": f"💰 **Your Balance:** ~${balance:,.2f} ✅\n\n✨ Ready to start earning yield!",
                "es": f"💰 **Tu Saldo:** ~${balance:,.2f} ✅\n\n✨ ¡Listo para comenzar a ganar rendimiento!",
                "pt": f"💰 **Seu Saldo:** ~${balance:,.2f} ✅\n\n✨ Pronto para começar a ganhar rendimento!",
                "zh": f"💰 **您的余额：** ~${balance:,.2f} ✅\n\n✨ 准备开始赚取收益！",
            }

        return msgs.get(language, msgs["en"])

    async def _format_vault_quote(
        self,
        vault_data: dict[str, Any],
        asset: str,
        amount: str | int | float,
        user_context: UserContext,
        language: str,
    ) -> str:
        """Format vault quote for display with confirmation prompts.

        Like swap workflow:
        - Shows user balance
        - Warns if insufficient funds (using real token prices)
        - Includes confirmation instructions
        """

        try:
            # Handle amount as string, int, or float
            amount_str = str(amount).replace(",", "")
            amount_float = float(amount_str)
        except (ValueError, TypeError):
            amount_float = 0

        # Format amount to avoid scientific notation (e.g., 1e-06 -> 0.000001)
        if amount_float < 0.0001:
            amount_formatted = f"{amount_float:.8f}".rstrip("0").rstrip(".")
        elif amount_float < 1:
            amount_formatted = f"{amount_float:.6f}".rstrip("0").rstrip(".")
        else:
            amount_formatted = f"{amount_float:.4f}".rstrip("0").rstrip(".")

        apy = vault_data.get("apy", 0)
        yearly_earnings = amount_float * (apy / 100)
        monthly_earnings = yearly_earnings / 12

        protocol = vault_data.get("protocol", "morpho")
        protocol_name = "Morpho" if protocol == "morpho" else "Aave V3"
        vault_name = vault_data.get("name", f"{protocol_name} Vault")

        # Get real token price and calculate USD value of deposit
        token_price_usd = await self._get_token_price_usd(asset)
        deposit_value_usd = amount_float * token_price_usd

        # Build user balance section with USD comparison
        user_balance_section = self._build_quote_balance_section(
            user_context=user_context,
            asset=asset,
            deposit_amount=amount_float,
            deposit_value_usd=deposit_value_usd,
            language=language,
        )

        # Build confirmation prompt (use formatted amount)
        confirm_section = self._get_confirmation_prompt(
            amount_formatted, asset, language
        )

        msgs = {
            "en": f"""📊 **Deposit Quote**

**{vault_name}**

💰 **Deposit Amount:** {amount_formatted} {asset}
📈 **Current APY:** {apy:.2f}%
💵 **Monthly Earnings:** ~{monthly_earnings:.6f} {asset}
📆 **Yearly Earnings:** ~{yearly_earnings:.6f} {asset}

{user_balance_section}

{confirm_section}""",
            "es": f"""📊 **Cotización de Depósito**

**{vault_name}**

💰 **Cantidad a Depositar:** {amount_formatted} {asset}
📈 **APY Actual:** {apy:.2f}%
💵 **Ganancias Mensuales:** ~{monthly_earnings:.6f} {asset}
📆 **Ganancias Anuales:** ~{yearly_earnings:.6f} {asset}

{user_balance_section}

{confirm_section}""",
            "pt": f"""📊 **Cotação de Depósito**

**{vault_name}**

💰 **Valor do Depósito:** {amount_formatted} {asset}
📈 **APY Atual:** {apy:.2f}%
💵 **Ganhos Mensais:** ~{monthly_earnings:.6f} {asset}
📆 **Ganhos Anuais:** ~{yearly_earnings:.6f} {asset}

{user_balance_section}

{confirm_section}""",
            "zh": f"""📊 **存款报价**

**{vault_name}**

💰 **存款金额：** {amount_formatted} {asset}
📈 **当前 APY：** {apy:.2f}%
💵 **月收益：** ~{monthly_earnings:.6f} {asset}
📆 **年收益：** ~{yearly_earnings:.6f} {asset}

{user_balance_section}

{confirm_section}""",
        }

        return msgs.get(language, msgs["en"])

    def _format_no_vault_available(
        self,
        asset: str,
        chain: str,
        language: str,
    ) -> str:
        """Format message when no vault is available."""

        msgs = {
            "en": f"""❌ **No Vault Available**

Unfortunately, there are no active vaults for **{asset}** on {chain.title()} network.

**Available assets:** USDC, USDT, DAI

Would you like to deposit one of these instead?""",
            "es": f"""❌ **Vault No Disponible**

Desafortunadamente, no hay vaults activos para **{asset}** en la red {chain.title()}.

**Activos disponibles:** USDC, USDT, DAI

¿Te gustaría depositar alguno de estos en su lugar?""",
            "pt": f"""❌ **Vault Não Disponível**

Infelizmente, não há vaults ativos para **{asset}** na rede {chain.title()}.

**Ativos disponíveis:** USDC, USDT, DAI

Gostaria de depositar algum destes em seu lugar?""",
            "zh": f"""❌ **金库不可用**

抱歉，{chain.title()} 网络上没有 **{asset}** 的活跃金库。

**可用资产：** USDC, USDT, DAI

您想存入其中一种吗？""",
        }

        return msgs.get(language, msgs["en"])

    def _ask_for_confirmation(self, language: str) -> str:
        """Ask user to confirm (not used - frontend handles via execute_data card)."""

        msgs = {
            "en": "Review the deposit details above.",
            "es": "Revisa los detalles del depósito.",
            "pt": "Revise os detalhes do depósito.",
            "zh": "查看上方的存款详情。",
        }

        return msgs.get(language, msgs["en"])

    def _format_ready_to_execute(
        self,
        data: dict[str, Any],
        language: str,
    ) -> str:
        """Format ready-to-execute message."""

        asset = data.get("asset", "USDC")
        amount_raw = data.get("amount", "0")
        vault = data.get("vault", {})
        protocol = vault.get("protocol", "morpho")
        protocol_name = "Morpho" if protocol == "morpho" else "Aave V3"

        # Format amount to avoid scientific notation (e.g., 1e-05 -> 0.00001)
        try:
            amount_float = float(amount_raw)
            # Use appropriate precision based on value
            if amount_float < 0.0001:
                amount = f"{amount_float:.8f}".rstrip("0").rstrip(".")
            elif amount_float < 1:
                amount = f"{amount_float:.6f}".rstrip("0").rstrip(".")
            else:
                amount = f"{amount_float:.4f}".rstrip("0").rstrip(".")
        except (ValueError, TypeError):
            amount = str(amount_raw)

        # Get vault APY for display
        apy = vault.get("apy", 0)
        vault_name = vault.get("name", f"{protocol_name} Vault")

        msgs = {
            "en": f"""✅ **Ready to Execute!**

**Deposit Details:**
• Amount: {amount} {asset}
• Vault: {vault_name}
• APY: {apy:.2f}%
• Network: Base

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👉 Click **Execute** below to sign the transaction with your wallet.""",
            "es": f"""✅ **¡Listo para Ejecutar!**

**Detalles del Depósito:**
• Cantidad: {amount} {asset}
• Vault: {vault_name}
• APY: {apy:.2f}%
• Red: Base

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👉 Haz clic en **Ejecutar** abajo para firmar la transacción con tu billetera.""",
            "pt": f"""✅ **Pronto para Executar!**

**Detalhes do Depósito:**
• Quantidade: {amount} {asset}
• Vault: {vault_name}
• APY: {apy:.2f}%
• Rede: Base

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👉 Clique em **Executar** abaixo para assinar a transação com sua carteira.""",
            "zh": f"""✅ **准备执行！**

**存款详情：**
• 金额：{amount} {asset}
• 金库：{vault_name}
• APY：{apy:.2f}%
• 网络：Base

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👉 点击下方 **执行** 使用您的钱包签署交易。""",
        }

        return msgs.get(language, msgs["en"])

    def _format_cancelled(self, language: str) -> str:
        """Format cancellation message."""

        msgs = {
            "en": "❌ Deposit cancelled. Let me know if you'd like to try again!",
            "es": "❌ Depósito cancelado. ¡Avísame si quieres intentarlo de nuevo!",
            "pt": "❌ Depósito cancelado. Me avise se quiser tentar novamente!",
            "zh": "❌ 存款已取消。如果您想再试一次，请告诉我！",
        }

        return msgs.get(language, msgs["en"])

    def _format_execution_pending(
        self,
        data: dict[str, Any],
        language: str,
    ) -> str:
        """Format message while execution is pending."""

        asset = data.get("asset", "USDC")
        amount = data.get("amount", "0")

        msgs = {
            "en": f"""⏳ **Processing Deposit**

Depositing **{amount} {asset}**...

Please confirm the transaction in your wallet.""",
            "es": f"""⏳ **Procesando Depósito**

Depositando **{amount} {asset}**...

Por favor confirma la transacción en tu wallet.""",
            "pt": f"""⏳ **Processando Depósito**

Depositando **{amount} {asset}**...

Por favor confirme a transação na sua carteira.""",
            "zh": f"""⏳ **处理存款中**

正在存入 **{amount} {asset}**...

请在您的钱包中确认交易。""",
        }

        return msgs.get(language, msgs["en"])

    # ========================================
    # Execute Data Builder
    # ========================================

    def _build_deposit_execute_data(
        self,
        vault_data: dict[str, Any],
        amount: str,
        chain: str,
    ) -> dict[str, Any]:
        """Build execute_data for deposit action."""

        protocol = vault_data.get("protocol", "morpho")

        execute_data = {
            "action_type": "deposit",
            "provider": vault_data.get("provider", "morpho"),
            "protocol": protocol,
            "chain": chain,
            "amount": amount,
            "slippage": 0.5,
        }

        if protocol == "morpho":
            execute_data.update({
                "vault_address": vault_data.get("address"),
                "asset_address": vault_data.get("asset_address"),
                "asset_symbol": vault_data.get("asset_symbol"),
                "vault_name": vault_data.get("name"),
                "supply_apy": vault_data.get("apy"),
            })
        else:
            # Aave V3
            execute_data.update({
                "pool_address": vault_data.get("address"),
                "asset_address": vault_data.get("asset_address"),
                "asset_symbol": vault_data.get("asset_symbol"),
                "supply_apy": vault_data.get("apy"),
                "available_liquidity_usd": vault_data.get("available_liquidity_usd"),
                "referral_code": 0,
            })

        return execute_data

    # ========================================
    # Helpers
    # ========================================

    def _build_quote_balance_section(
        self,
        user_context: UserContext,
        asset: str,
        deposit_amount: float,
        deposit_value_usd: float,
        language: str,
    ) -> str:
        """Build user balance context section for deposit quote.

        Args:
            user_context: User context with balance info
            asset: Token symbol (ETH, USDC, etc.)
            deposit_amount: Raw deposit amount (e.g., 1 ETH)
            deposit_value_usd: USD value of deposit (e.g., $3500 for 1 ETH)
            language: User language
        """
        if not user_context.is_authenticated:
            return ""

        balance = user_context.total_balance_usd
        portfolio_state = user_context.portfolio_state

        # Compare USD balance against USD value of deposit
        if portfolio_state == "empty" or balance < 1:
            msgs = {
                "en": "💰 **Your Balance:** $0.00\n\n⚠️ You don't have funds to complete this deposit.\n💡 Say `buy crypto` to get USDC first.",
                "es": "💰 **Tu Saldo:** $0.00\n\n⚠️ No tienes fondos para completar este depósito.\n💡 Di `comprar cripto` para obtener USDC primero.",
                "pt": "💰 **Seu Saldo:** $0.00\n\n⚠️ Você não tem fundos para completar este depósito.\n💡 Diga `comprar cripto` para obter USDC primeiro.",
                "zh": "💰 **您的余额：** $0.00\n\n⚠️ 您没有资金完成此存款。\n💡 先说 `买加密货币` 获取 USDC。",
            }
        elif balance < deposit_value_usd:
            # User doesn't have enough - show warning with USD values
            msgs = {
                "en": f"💰 **Your Balance:** ~${balance:,.2f}\n\n⚠️ Deposit value (~${deposit_value_usd:,.2f} for {deposit_amount} {asset}) exceeds your balance.\n💡 When you confirm, I'll adjust to your available balance.",
                "es": f"💰 **Tu Saldo:** ~${balance:,.2f}\n\n⚠️ El valor del depósito (~${deposit_value_usd:,.2f} por {deposit_amount} {asset}) excede tu saldo.\n💡 Cuando confirmes, ajustaré a tu saldo disponible.",
                "pt": f"💰 **Seu Saldo:** ~${balance:,.2f}\n\n⚠️ O valor do depósito (~${deposit_value_usd:,.2f} por {deposit_amount} {asset}) excede seu saldo.\n💡 Quando você confirmar, ajustarei ao seu saldo disponível.",
                "zh": f"💰 **您的余额：** ~${balance:,.2f}\n\n⚠️ 存款价值 (~${deposit_value_usd:,.2f} 对于 {deposit_amount} {asset}) 超过您的余额。\n💡 当您确认时，我会调整到您的可用余额。",
            }
        else:
            msgs = {
                "en": f"💰 **Your Balance:** ~${balance:,.2f} ✅",
                "es": f"💰 **Tu Saldo:** ~${balance:,.2f} ✅",
                "pt": f"💰 **Seu Saldo:** ~${balance:,.2f} ✅",
                "zh": f"💰 **您的余额：** ~${balance:,.2f} ✅",
            }

        return msgs.get(language, msgs["en"])

    def _get_confirmation_prompt(
        self,
        amount: str | int | float,
        asset: str,
        language: str,
    ) -> str:
        """Get confirmation prompt for deposit quote."""
        msgs = {
            "en": f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Ready to deposit {amount} {asset}?**

• Say **"yes"** or **"confirm"** to execute
• Say **"deposit [amount] {asset}"** to change amount
• Say **"cancel"** to abort""",
            "es": f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**¿Listo para depositar {amount} {asset}?**

• Di **"sí"** o **"confirmar"** para ejecutar
• Di **"depositar [cantidad] {asset}"** para cambiar
• Di **"cancelar"** para abortar""",
            "pt": f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Pronto para depositar {amount} {asset}?**

• Diga **"sim"** ou **"confirmar"** para executar
• Diga **"depositar [valor] {asset}"** para alterar
• Diga **"cancelar"** para abortar""",
            "zh": f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**准备存入 {amount} {asset}？**

• 说 **"是"** 或 **"确认"** 执行
• 说 **"存入 [金额] {asset}"** 更改金额
• 说 **"取消"** 中止""",
        }
        return msgs.get(language, msgs["en"])

    def _get_auto_adjust_message(
        self,
        original_amount: str,
        recommended_amount: str,
        asset: str,
        recommended_usd: float,
        user_balance: float,
        language: str,
    ) -> str:
        """Message when auto-adjusting to available balance.

        Args:
            original_amount: Original requested amount (e.g., "1")
            recommended_amount: Adjusted token amount (e.g., "0.00117")
            asset: Token symbol (e.g., "ETH")
            recommended_usd: USD value of recommendation (e.g., 2.70)
            user_balance: User's total USD balance
            language: User language
        """
        msgs = {
            "en": f"""⚠️ **Adjusting to your available balance**

You requested **{original_amount} {asset}** but only have ~**${user_balance:.2f}** available.

I'm adjusting your deposit to **{recommended_amount} {asset}** (~${recommended_usd:.2f}, keeping some for gas).

Here's the updated quote:""",
            "es": f"""⚠️ **Ajustando a tu saldo disponible**

Solicitaste **{original_amount} {asset}** pero solo tienes ~**${user_balance:.2f}** disponibles.

Estoy ajustando tu depósito a **{recommended_amount} {asset}** (~${recommended_usd:.2f}, reservando algo para gas).

Aquí está la cotización actualizada:""",
            "pt": f"""⚠️ **Ajustando ao seu saldo disponível**

Você solicitou **{original_amount} {asset}** mas só tem ~**${user_balance:.2f}** disponíveis.

Estou ajustando seu depósito para **{recommended_amount} {asset}** (~${recommended_usd:.2f}, reservando para gas).

Aqui está a cotação atualizada:""",
            "zh": f"""⚠️ **调整到您的可用余额**

您请求 **{original_amount} {asset}** 但只有 ~**${user_balance:.2f}** 可用。

我正在将您的存款调整为 **{recommended_amount} {asset}**（~${recommended_usd:.2f}，保留一些作为gas费）。

以下是更新的报价：""",
        }
        return msgs.get(language, msgs["en"])

    def _get_zero_balance_message(self, asset: str, language: str) -> str:
        """Message when user has zero usable balance."""
        msgs = {
            "en": f"""❌ **Unable to deposit - No funds available**

Your wallet balance is too low to complete this deposit.

**💳 Get crypto to start earning yield:**

1. **Buy USDC with card/Apple Pay/Google Pay:**
   Say: **"buy crypto"** or **"buy 100"**

2. **Transfer {asset} from another wallet:**
   Say: **"my wallet address"** to get your address

Once you have funds, come back and try:
**"deposit [amount] {asset}"**""",
            "es": f"""❌ **No se puede depositar - Sin fondos disponibles**

Tu saldo es muy bajo para completar este depósito.

**💳 Obtén cripto para comenzar a ganar rendimiento:**

1. **Compra USDC con tarjeta:**
   Di: **"comprar cripto"** o **"comprar 100"**

2. **Transfiere {asset} desde otra billetera:**
   Di: **"mi dirección de wallet"**

Una vez que tengas fondos, vuelve e intenta:
**"depositar [cantidad] {asset}"**""",
            "pt": f"""❌ **Não é possível depositar - Sem fundos disponíveis**

Seu saldo é muito baixo para completar este depósito.

**💳 Obtenha cripto para começar a ganhar rendimento:**

1. **Compre USDC com cartão:**
   Diga: **"comprar cripto"** ou **"comprar 100"**

2. **Transfira {asset} de outra carteira:**
   Diga: **"meu endereço de carteira"**

Quando tiver fundos, volte e tente:
**"depositar [valor] {asset}"**""",
            "zh": f"""❌ **无法存款 - 没有可用资金**

您的钱包余额太低，无法完成此存款。

**💳 获取加密货币开始赚取收益：**

1. **用卡购买 USDC：**
   说：**"买加密货币"** 或 **"买 100"**

2. **从其他钱包转入 {asset}：**
   说：**"我的钱包地址"** 获取您的地址

有了资金后，回来尝试：
**"存入 [金额] {asset}"**""",
        }
        return msgs.get(language, msgs["en"])

    async def _get_token_price_usd(self, asset: str) -> float:
        """
        Get real-time token price in USD from CoinGecko.

        Falls back to hardcoded estimates if CoinGecko unavailable.
        """
        # Stablecoins are always $1
        if asset.upper() in ("USDC", "USDT", "DAI", "BUSD", "FRAX"):
            return 1.0

        # Map asset symbols to CoinGecko IDs
        ASSET_TO_COINGECKO = {
            "ETH": "ethereum",
            "WETH": "ethereum",
            "WBTC": "bitcoin",
            "BTC": "bitcoin",
            "MATIC": "matic-network",
            "AVAX": "avalanche-2",
            "SOL": "solana",
            "ARB": "arbitrum",
            "OP": "optimism",
            "LINK": "chainlink",
        }

        # Fallback prices if CoinGecko fails
        FALLBACK_PRICES = {
            "ETH": 3500,
            "WETH": 3500,
            "WBTC": 95000,
            "BTC": 95000,
            "MATIC": 0.50,
            "AVAX": 35,
            "SOL": 180,
            "ARB": 1.0,
            "OP": 2.0,
            "LINK": 15,
        }

        coingecko_id = ASSET_TO_COINGECKO.get(asset.upper())

        if coingecko_id and self._coingecko:
            try:
                price_data = await self._coingecko.get_price(coingecko_id)
                if price_data and hasattr(price_data, "usd") and price_data.usd:
                    logger.info(
                        f"[LendingWorkflow] Got real price for {asset}: ${price_data.usd:.2f}"
                    )
                    return float(price_data.usd)
            except Exception as e:
                logger.warning(
                    f"[LendingWorkflow] Failed to fetch {asset} price from CoinGecko: {e}"
                )

        # Fallback to hardcoded estimate
        fallback_price = FALLBACK_PRICES.get(asset.upper(), 1.0)
        logger.info(
            f"[LendingWorkflow] Using fallback price for {asset}: ${fallback_price:.2f}"
        )
        return fallback_price

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
            "execute",
            "sí",
            "si",
            "confirmar",
            "vale",
            "continuar",
            "sim",
            "confirmar",
            "prosseguir",
            "是",
            "确认",
            "好",
            "继续",
        ]
        return any(word in text for word in confirm_words)

    def _is_cancellation(self, text: str) -> bool:
        """Check if text is a cancellation."""
        cancel_words = [
            "no",
            "n",
            "cancel",
            "abort",
            "stop",
            "nevermind",
            "forget it",
            "cancelar",
            "abortar",
            "parar",
            "取消",
            "不",
            "停止",
        ]
        return any(word in text for word in cancel_words)
