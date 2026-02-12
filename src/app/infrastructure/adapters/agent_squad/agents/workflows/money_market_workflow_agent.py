"""
Money Market Workflow Agent - Multi-Step Protocol Rate Comparison.

Handles the complete money market workflow for authenticated users (Aave and Compound only):
1. Parse request: Extract asset and comparison type
2. Fetch data: Get rates from Aave and Compound
3. Compare: Show side-by-side comparison with recommendations
4. Select: Allow user to proceed with best option
5. Positions: List supply positions on Aave and Compound; withdraw supported for Aave

Integration:
- Aave V3 via AaveGateway
- Compound V3 via CompoundGateway

Example Conversation:
    User: "compare USDC rates"
    Agent: "📊 Rate Comparison:\n- Aave: 4.2% APY\n- Compound: 3.8% APY\n Best: Aave"
    User: "deposit with Aave"
    Agent: "✅ Ready to deposit with Aave!" + execute_data
"""

import logging
import re
from decimal import Decimal
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
    from app.domain.ports.aave_gateway import AaveGateway
    from app.domain.ports.asset_sentiment_provider import AssetSentimentProvider
    from app.domain.ports.compound_gateway import CompoundGateway
    from app.domain.ports.morpho_gateway import MorphoGateway
    from app.infrastructure.adapters.external.defillama_client import DefiLlamaClient

# Import clients directly for real API access
from app.infrastructure.adapters.external.morpho_client import MorphoClient, CHAIN_IDS
from app.infrastructure.adapters.external.compound_client import CompoundClient
from app.infrastructure.adapters.external.defillama_client import (
    DefiLlamaClient as DefiLlamaClientDirect,
)

logger = logging.getLogger(__name__)

# DeFiLlama chain name mappings
DEFILLAMA_CHAIN_MAP = {
    "ethereum": "Ethereum",
    "base": "Base",
    "polygon": "Polygon",
    "arbitrum": "Arbitrum",
    "optimism": "Optimism",
    "avalanche": "Avalanche",
}

# Aave V3 pool addresses by chain (required for production execute payload)
AAVE_POOL_ADDRESSES = {
    "ethereum": "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2",
    "base": "0xA238Dd80C259a72e81d7e4664a9801593F98d1C5",
    "polygon": "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
    "arbitrum": "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
    "optimism": "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
    "avalanche": "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
}


# Supported assets for comparison
SUPPORTED_ASSETS = {
    "usdc": {"symbol": "USDC", "name": "USD Coin", "emoji": "💵"},
    "usdt": {"symbol": "USDT", "name": "Tether", "emoji": "💵"},
    "dai": {"symbol": "DAI", "name": "Dai", "emoji": "💰"},
    "eth": {"symbol": "ETH", "name": "Ethereum", "emoji": "Ξ"},
    "weth": {"symbol": "WETH", "name": "Wrapped Ethereum", "emoji": "Ξ"},
    "wbtc": {"symbol": "WBTC", "name": "Wrapped Bitcoin", "emoji": "₿"},
}

# Assets that have lending rates on Base (used for default asset menu; USDT excluded)
ASSETS_AVAILABLE_ON_BASE = ["USDC", "DAI", "ETH"]

# Knowledge snippets for enterprise-grade responses (mirrors anvil_knowledge/features/money_market.json workflow_snippets)
WORKFLOW_SNIPPETS: dict[str, dict[str, str]] = {
    "positions_intro": {
        "en": "\n\n💡 Your positions earn variable APY from Aave and Compound. Withdrawals are on-chain and typically confirm within a few seconds.",
        "es": "\n\n💡 Tus posiciones generan APY variable en Aave y Compound. Los retiros son on-chain y suelen confirmarse en pocos segundos.",
        "pt": "\n\n💡 Suas posições geram APY variável na Aave e na Compound. Saques são on-chain e costumam confirmar em poucos segundos.",
    },
    "withdraw_confirm": {
        "en": "\n\n💡 Confirming will prepare the transaction for your wallet. You'll sign in your wallet to complete the withdrawal.",
        "es": "\n\n💡 Al confirmar se preparará la transacción para tu wallet. Firmarás en tu wallet para completar el retiro.",
        "pt": "\n\n💡 Ao confirmar, a transação será preparada para sua carteira. Você assinará na carteira para concluir a retirada.",
    },
    "ready": {
        "en": "\n\n💡 After you sign in your wallet, funds will move from the protocol to your wallet. You can check your balance once the transaction confirms.",
        "es": "\n\n💡 Después de firmar en tu wallet, los fondos pasarán del protocolo a tu wallet. Puedes revisar tu saldo cuando la transacción confirme.",
        "pt": "\n\n💡 Após assinar na carteira, os fundos serão transferidos do protocolo para sua carteira. Você pode conferir o saldo quando a transação for confirmada.",
    },
}


class MoneyMarketWorkflowAgent(BaseWorkflowAgent):
    """
    AGNO-based multi-step money market comparison workflow agent.

    Steps:
    1. parse_request: Extract asset for comparison
    2. fetch_data: Get rates from Aave and Compound
    3. compare: Show comparison with best recommendation
    4. select: Allow user to select protocol for deposit
    5. positions: List positions and withdraw (Aave withdraw; Compound list-only)

    Features:
    - Real-time rate comparison (Aave and Compound only)
    - Positions and withdraw (Aave and Compound; withdraw Aave only)
    - Supply and borrow APY comparison
    - Direct deposit integration via lending_workflow
    - Multi-language support
    """

    def __init__(
        self,
        llm_client: "LLMClientGateway | None" = None,
        aave_gateway: "AaveGateway | None" = None,
        compound_gateway: "CompoundGateway | None" = None,
        morpho_gateway: "MorphoGateway | None" = None,
        defillama_client: "DefiLlamaClient | None" = None,
        sentiment_provider: "AssetSentimentProvider | None" = None,
    ):
        """
        Initialize money market workflow agent.

        Args:
            llm_client: LLM client for parameter extraction
            aave_gateway: Gateway for Aave V3 data
            compound_gateway: Gateway for Compound V3 data
            morpho_gateway: Gateway for Morpho vault data
            defillama_client: DeFiLlama client for fallback rate data
            sentiment_provider: Optional Hunter sentiment for response enrichment
        """
        super().__init__(llm_client=llm_client)
        self._aave = aave_gateway
        self._compound = compound_gateway
        self._morpho = morpho_gateway
        self._defillama = defillama_client
        self._sentiment = sentiment_provider

    @property
    def agent_type(self) -> AgentType:
        return AgentType.MONEY_MARKET_WORKFLOW

    @property
    def workflow_name(self) -> str:
        return "MoneyMarketWorkflow"

    async def process_step(
        self,
        message: MessageContent,
        state: WorkflowState,
        user_context: UserContext,
    ) -> tuple[str, WorkflowState]:
        """Process money market workflow step."""

        step = state.step
        language = user_context.language
        text_lower = message.value.lower().strip()

        logger.info(
            f"[MoneyMarketWorkflow] Processing step={step}, message={message.value[:50]}..."
        )

        # Positions flow: handle position selection and withdraw amount sub-steps
        if state.data.get("flow") == "positions" and (
            state.data.get("awaiting_position_selection")
            or state.data.get("awaiting_withdraw_amount")
        ):
            return await self._handle_positions_request(message, state, user_context)

        # Check if user wants to start a NEW money market flow (restart detection)
        # This resets state when user says "compare rates", "money market", etc.
        # while already in an ongoing flow (FETCH_DATA, CONFIRM, or EXECUTE step)
        if step not in (
            WorkflowStep.PARSE_REQUEST.value,
            WorkflowStep.CANCELLED.value,
            WorkflowStep.COMPLETED.value,
        ):
            restart_keywords = [
                "compare rates",
                "money market",
                "best rates",
                "yield comparison",
                "aave rates",
                "compound rates",
                "morpho rates",  # Protocol-specific rate queries
                "what are",
                "what's the",
                "show me rates",
                "lending rates",
                "comparar tasas",
                "mercado de dinero",
                "mejores tasas",
                "tasas de aave",
                "tasas de compound",  # Spanish protocol queries
                # Positions + withdraw (Option A: money market positions in this workflow)
                "my money market positions",
                "money market positions",
                "withdraw from money market",
                "what am I earning in money market",
            ]
            is_restart_request = any(
                text_lower.startswith(kw) or f" {kw}" in f" {text_lower}"
                for kw in restart_keywords
            )

            if is_restart_request:
                logger.info(
                    f"[MoneyMarketWorkflow] Restart detected - user starting new flow, resetting state"
                )
                state = WorkflowState()
                state.step = WorkflowStep.PARSE_REQUEST.value
                return await self._handle_parse_request(message, state, user_context)

        # Step 1: Parse request
        if step == WorkflowStep.PARSE_REQUEST.value:
            return await self._handle_parse_request(message, state, user_context)

        # Step 2: Fetch data (compare rates)
        if step == WorkflowStep.FETCH_DATA.value:
            return await self._handle_fetch_data(message, state, user_context)

        # Step 3: Confirm (select protocol)
        if step == WorkflowStep.CONFIRM.value:
            return await self._handle_confirm(message, state, user_context)

        # Step 4: Execute (redirect to deposit)
        if step == WorkflowStep.EXECUTE.value:
            return await self._handle_execute(message, state, user_context)

        # Unknown step - reset
        logger.warning(f"[MoneyMarketWorkflow] Unknown step: {step}")
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
        """Parse comparison request or positions/withdraw request from user message."""

        language = user_context.language
        text = message.value.strip()
        text_lower = text.lower()

        # Positions / withdraw from money market (Option A)
        positions_keywords = [
            "my money market positions",
            "money market positions",
            "withdraw from money market",
            "what am I earning in money market",
            "show my money market",
            "my positions money market",
            # Common typos so "my money market possitions" still works
            "my money market possitions",
            "money market possitions",
            "my money market positons",
            "money market positons",
        ]
        if any(kw in text_lower for kw in positions_keywords):
            state.data["flow"] = "positions"
            state.data["action"] = "withdraw"
            state.data["chain"] = state.data.get("chain", "base")
            return await self._handle_positions_request(message, state, user_context)

        # Typo-tolerant: "money market" + position/earning/withdraw (e.g. "my money market possitions")
        if "money market" in text_lower and any(
            p in text_lower
            for p in (
                "position",
                "possition",
                "positon",
                "positons",
                "earning",
                "withdraw",
            )
        ):
            state.data["flow"] = "positions"
            state.data["action"] = "withdraw"
            state.data["chain"] = state.data.get("chain", "base")
            return await self._handle_positions_request(message, state, user_context)

        # Number selection (e.g. "1", "2", "3") for default Base assets
        if text.isdigit():
            index = int(text) - 1
            if 0 <= index < len(ASSETS_AVAILABLE_ON_BASE):
                asset = ASSETS_AVAILABLE_ON_BASE[index]
                state.data["asset"] = asset
                state.data["comparison_type"] = "supply"
                state.data["chain"] = "base"
                state.step = WorkflowStep.FETCH_DATA.value
                return await self._handle_fetch_data(message, state, user_context)

        # Try to extract parameters from message (asset name, "USDT on Ethereum", etc.)
        params = await self._extract_comparison_params(text_lower)

        asset = params.get("asset")
        comparison_type = params.get("type", "supply")  # supply or borrow

        if asset:
            state.data["asset"] = asset.upper()
            state.data["comparison_type"] = comparison_type
            state.data["chain"] = params.get("chain", "base")
            state.step = WorkflowStep.FETCH_DATA.value
            return await self._handle_fetch_data(message, state, user_context)

        # No asset detected - show asset selection (numbered list, no USDT on Base)
        return self._ask_for_asset(language), state

    async def _handle_fetch_data(
        self,
        message: MessageContent,
        state: WorkflowState,
        user_context: UserContext,
    ) -> tuple[str, WorkflowState]:
        """Fetch and compare rates from protocols using REAL APIs."""

        language = user_context.language
        asset = state.data.get("asset", "USDC")
        chain = state.data.get("chain", "base")
        comparison_type = state.data.get("comparison_type", "supply")

        logger.info(
            f"[MoneyMarketWorkflow] Comparing {asset} rates on {chain} using REAL APIs"
        )

        rates = []

        # 1. Fetch Compound rates directly (REAL RPC - works great)
        compound_rate = await self._fetch_compound_rate_direct(asset, chain)
        if compound_rate:
            rates.append(compound_rate)
            logger.info(
                f"[MoneyMarketWorkflow] Compound rate: {compound_rate.get('supply_apy', 0):.2f}%"
            )

        # 2. Fetch Aave rates from DeFiLlama (aggregated, reliable)
        aave_rate = await self._fetch_aave_rate_defillama(asset, chain)
        if aave_rate:
            rates.append(aave_rate)
            logger.info(
                f"[MoneyMarketWorkflow] Aave rate: {aave_rate.get('supply_apy', 0):.2f}%"
            )

        # Fallback: Try gateway-based methods if no rates yet
        if not rates:
            logger.info("[MoneyMarketWorkflow] Using gateway fallbacks...")

            aave_rate = await self._fetch_aave_rate(asset, chain)
            if aave_rate:
                rates.append(aave_rate)

            compound_rate = await self._fetch_compound_rate(asset, chain)
            if compound_rate:
                rates.append(compound_rate)

        if not rates:
            response = self._format_no_rates_available(asset, chain, language)
            state.step = WorkflowStep.CANCELLED.value
            state.cancelled = True
            return response, state

        # Sort by APY (highest first)
        rates.sort(key=lambda r: r.get("supply_apy", 0), reverse=True)

        # Store rates data
        state.data["rates"] = rates
        state.data["best_protocol"] = rates[0]["protocol"]
        state.step = WorkflowStep.CONFIRM.value

        # Format comparison response
        response = self._format_rate_comparison(
            rates=rates,
            asset=asset,
            comparison_type=comparison_type,
            language=language,
        )

        return response, state

    async def _handle_confirm(
        self,
        message: MessageContent,
        state: WorkflowState,
        user_context: UserContext,
    ) -> tuple[str, WorkflowState]:
        """Handle protocol selection, cancellation, or positions withdraw confirmation."""

        language = user_context.language
        text = message.value.lower().strip()
        rates = state.data.get("rates", [])

        # Positions flow: user confirming withdraw
        if state.data.get("flow") == "positions":
            if self._is_cancellation(text):
                state.cancelled = True
                state.step = WorkflowStep.CANCELLED.value
                state.data["flow"] = None
                return self._format_cancelled(language), state
            if self._is_confirmation(text):
                state.confirmed = True
                state.step = WorkflowStep.EXECUTE.value
                return await self._handle_positions_withdraw_execute(
                    message, state, user_context
                )
            # Unclear - ask again (step 2: no sentiment, contextual copy only)
            position = state.data.get("selected_position", {})
            amount = state.data.get("withdraw_amount", "max")
            reply, state = await self._show_withdraw_confirmation_mm(
                position, amount, user_context, state
            )
            content = self._greeting(user_context) + reply
            content += self._get_confirm_step_snippet(
                amount, position.get("asset", ""), position.get("protocol", ""), user_context.language
            )
            return content, state

        # Check for cancellation
        if self._is_cancellation(text):
            state.cancelled = True
            state.step = WorkflowStep.CANCELLED.value
            return self._format_cancelled(language), state

        # Check for protocol selection
        selected_protocol = self._detect_protocol_selection(text, rates)

        if selected_protocol:
            state.data["selected_protocol"] = selected_protocol
            state.step = WorkflowStep.EXECUTE.value

            # Get selected rate for display
            selected_rate = next(
                (r for r in rates if r["protocol"] == selected_protocol),
                rates[0] if rates else None,
            )

            # Build response showing user's balance so they know how much they can deposit
            response = self._format_protocol_selected(
                selected_protocol,
                state.data,
                language,
                balance=user_context.total_balance_usd,
            )

            # Add funding recommendation if user has empty portfolio
            if user_context.has_insufficient_funds:
                funding_msg = self._get_funding_recommendation(
                    state.data.get("asset", "USDC"),
                    language,
                    balance=user_context.total_balance_usd,
                )
                response = funding_msg + "\n" + response
                logger.info(
                    f"[MoneyMarketWorkflow] User has low balance - showing funding info"
                )

            # DON'T set execute_data here - wait for user to enter amount
            # execute_data will be set in _handle_execute after amount is provided
            state.execute_data = None

            return response, state

        # Check if user wants to deposit amount
        amount = self._extract_amount(text)
        if amount:
            state.data["amount"] = amount
            # Use best protocol if none explicitly selected
            selected_protocol = state.data.get("best_protocol", "aave")
            state.data["selected_protocol"] = selected_protocol
            state.step = WorkflowStep.EXECUTE.value

            selected_rate = next(
                (r for r in rates if r["protocol"] == selected_protocol),
                rates[0] if rates else None,
            )

            # Only build execute_data if user has sufficient funds
            if not user_context.needs_funding_recommendation and selected_rate:
                state.execute_data = self._build_deposit_execute_data(
                    protocol=selected_protocol,
                    asset=state.data.get("asset", "USDC"),
                    chain=state.data.get("chain", "base"),
                    rate_data=selected_rate,
                    amount=amount,
                )
            else:
                state.execute_data = None
                logger.info(
                    f"[MoneyMarketWorkflow] User needs funding - not setting execute_data for amount"
                )

            # Call _handle_execute directly to check balance before showing "Ready"
            return await self._handle_execute(message, state, user_context)

        # Unclear response - show options again
        return self._ask_for_selection(rates, language), state

    async def _handle_execute(
        self,
        message: MessageContent,
        state: WorkflowState,
        user_context: UserContext,
    ) -> tuple[str, WorkflowState]:
        """Handle deposit execution.

        IMPORTANT: Checks user balance before allowing execution.
        If user has insufficient funds, shows helpful message to buy crypto.
        """
        language = user_context.language
        text = message.value.strip()

        # Check if user is providing an amount (e.g., "10", "100", "$50")
        # This handles the case where workflow asked for amount after protocol selection
        if not state.data.get("amount"):
            extracted_amount = self._extract_amount(text.lower())
            if extracted_amount:
                state.data["amount"] = extracted_amount
                logger.info(
                    f"[MoneyMarketWorkflow] Extracted amount from message: {extracted_amount}"
                )

        # Use 'or' to handle both missing keys AND None values
        asset = (state.data.get("asset") or "USDC").upper()
        amount = state.data.get("amount") or "0"

        # Parse amount for balance check
        try:
            amount_float = float(str(amount).replace(",", "").replace("$", ""))
        except (ValueError, TypeError):
            amount_float = 0.0

        # Check user balance before allowing execution
        # Use amount-based check if amount is specified, otherwise use general check
        has_insufficient = (
            user_context.has_insufficient_funds_for_amount(amount_float)
            if amount_float > 0
            else user_context.has_insufficient_funds
        )

        if has_insufficient and user_context.is_authenticated:
            logger.info(
                f"[MoneyMarketWorkflow] Insufficient funds for ${amount_float:.2f} - "
                f"balance=${user_context.total_balance_usd:.2f}"
            )

            # Build response with funding recommendation + quote info
            funding_msg = self._get_funding_recommendation(
                asset, language, balance=user_context.total_balance_usd
            )
            quote_info = self._format_deposit_quote_info(state.data, language)
            response = funding_msg + "\n" + quote_info

            # Don't set execute_data - user needs to fund first
            state.execute_data = None
            # Stay in EXECUTE step to allow retry after funding
            state.step = WorkflowStep.EXECUTE.value

            return response, state

        # User has sufficient funds - build execute_data with amount
        selected_protocol = state.data.get("selected_protocol", "aave")
        rates = state.data.get("rates", [])
        selected_rate = next(
            (r for r in rates if r["protocol"] == selected_protocol),
            rates[0] if rates else None,
        )

        if selected_rate:
            chain = state.data.get("chain", "base")
            state.execute_data = self._build_deposit_execute_data(
                protocol=selected_protocol,
                asset=asset,
                chain=chain,
                rate_data=selected_rate,
                amount=amount,  # Include the amount
            )
            logger.info(
                f"[MoneyMarketWorkflow] User has funds (${user_context.total_balance_usd:.2f}) - "
                f"setting execute_data for {amount} {asset} on {selected_protocol}"
            )

            # Record pending earn transaction for tracking
            if selected_protocol in ("aave", "compound"):
                await self._record_earn_transaction(
                    user_context=user_context,
                    protocol=selected_protocol,
                    chain=chain,
                    action_type="supply",
                    asset_symbol=asset,
                    amount=amount,
                    apy=selected_rate.get("supply_apy"),
                    pool_address=selected_rate.get("pool_address")
                    or AAVE_POOL_ADDRESSES.get(chain.lower()),
                )

        # The actual deposit is handled by lending_workflow or frontend
        state.step = WorkflowStep.COMPLETED.value

        return self._format_execution_info(state.data, language), state

    # ========================================
    # Money Market Positions + Withdraw (Option A)
    # ========================================

    async def _handle_positions_request(
        self,
        message: MessageContent,
        state: WorkflowState,
        user_context: UserContext,
    ) -> tuple[str, WorkflowState]:
        """Handle money market positions list and withdraw flow."""
        language = user_context.language
        text = message.value.lower().strip()
        wallet_address = user_context.wallet_address

        if not wallet_address:
            if language == "es":
                return (
                    "🔗 Para ver tus posiciones o retirar, conecta tu wallet primero.",
                    state,
                )
            if language == "pt":
                return (
                    "🔗 Para ver suas posições ou retirar, conecte sua carteira primeiro.",
                    state,
                )
            return (
                "🔗 Connect your wallet to see your money market positions or withdraw.",
                state,
            )

        if state.data.get("awaiting_position_selection"):
            return await self._handle_position_selection_mm(
                message, state, user_context
            )
        if state.data.get("awaiting_withdraw_amount"):
            return await self._handle_withdraw_amount_input_mm(
                message, state, user_context
            )

        positions = await self._fetch_user_positions_mm(wallet_address, user_context)
        if not positions:
            if language == "es":
                base_msg = (
                    "📭 No tienes posiciones en el mercado monetario (Aave/Compound).\n\n"
                    "¿Quieres comparar tasas para depositar?"
                )
            elif language == "pt":
                base_msg = (
                    "📭 Você não tem posições no mercado monetário (Aave/Compound).\n\n"
                    "Quer comparar taxas para depositar?"
                )
            else:
                base_msg = (
                    "📭 You have no money market positions (Aave/Compound).\n\n"
                    "Would you like to compare rates to deposit?"
                )
            msg = (
                self._greeting(user_context)
                + base_msg
                + self._get_knowledge_snippet("positions_intro", language)
            )
            return msg, state

        if len(positions) == 1:
            position = positions[0]
            state.data["selected_position"] = position
            state.data["awaiting_withdraw_amount"] = True
            reply = await self._ask_withdraw_amount_mm(position, user_context)
            content = self._greeting(user_context) + reply
            content, state = await self._enrich_with_sentiment(
                content, state, position.get("asset", "USDC"), user_context.language
            )
            content += self._get_knowledge_snippet(
                "positions_intro", user_context.language
            )
            return content, state

        state.data["positions"] = positions
        state.data["awaiting_position_selection"] = True
        reply = await self._show_position_selection_mm(positions, user_context)
        asset = positions[0].get("asset", "USDC") if positions else "USDC"
        content = self._greeting(user_context) + reply
        content, state = await self._enrich_with_sentiment(
            content, state, asset, user_context.language
        )
        content += self._get_knowledge_snippet(
            "positions_intro", user_context.language
        )
        return content, state

    async def _fetch_user_positions_mm(
        self,
        wallet_address: str,
        user_context: UserContext,
    ) -> list[dict[str, Any]]:
        """Fetch user supply positions from Aave and Compound only (Base)."""
        positions: list[dict[str, Any]] = []
        chain = "base"

        if self._aave:
            try:
                aave_position = await self._aave.get_user_position(
                    address=wallet_address,
                    chain=chain,
                )
                if aave_position and aave_position.supplies:
                    for supply in aave_position.supplies:
                        positions.append({
                            "protocol": "aave",
                            "asset": supply.symbol,
                            "supplied_amount": str(supply.balance),
                            "supplied_usd": float(supply.balance_usd),
                            "apy": float(supply.apy),
                            "chain": chain,
                        })
            except Exception as e:
                logger.debug(
                    "[MoneyMarketWorkflow] Aave positions (none or error): %s", e
                )

        if self._compound:
            for asset in ("USDC", "WETH"):
                try:
                    pos = await self._compound.get_user_position(
                        user_address=wallet_address,
                        asset=asset,
                        chain=chain,
                    )
                    if pos and pos.supplied > 0:
                        apy = await self._compound.get_supply_apy(
                            asset=asset,
                            chain=chain,
                        )
                        supplied_usd = (
                            float(pos.supplied)
                            if asset == "USDC"
                            else 0.0
                        )
                        positions.append({
                            "protocol": "compound",
                            "asset": pos.base_asset,
                            "supplied_amount": str(pos.supplied),
                            "supplied_usd": supplied_usd,
                            "apy": float(apy),
                            "chain": chain,
                        })
                except Exception as e:
                    logger.debug(
                        "[MoneyMarketWorkflow] Compound position %s: %s",
                        asset,
                        e,
                    )

        return positions

    async def _show_position_selection_mm(
        self,
        positions: list[dict[str, Any]],
        user_context: UserContext,
    ) -> str:
        """Show money market positions for selection."""
        language = user_context.language
        if language == "es":
            header = "📊 **Tus posiciones en el mercado monetario**\n\n"
            footer = "\n\n💡 Responde con el número para seleccionar y retirar."
        elif language == "pt":
            header = "📊 **Suas posições no mercado monetário**\n\n"
            footer = "\n\n💡 Responda com o número para selecionar e retirar."
        else:
            header = "📊 **Your money market positions**\n\n"
            footer = "\n\n💡 Reply with the number to select and withdraw."

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
                    f"   • {amount} {asset} (~${usd_value:,.2f}) · APY: {apy:.2f}%"
                )
            else:
                lines.append(
                    f"**{i}.** {asset} on {protocol}\n"
                    f"   • {amount} {asset} (~${usd_value:,.2f}) · APY: {apy:.2f}%"
                )
        return header + "\n\n".join(lines) + footer

    async def _handle_position_selection_mm(
        self,
        message: MessageContent,
        state: WorkflowState,
        user_context: UserContext,
    ) -> tuple[str, WorkflowState]:
        """Handle user position selection by number or asset."""
        text = message.value.strip()
        positions = state.data.get("positions", [])

        try:
            selection = int(text)
            if 1 <= selection <= len(positions):
                position = positions[selection - 1]
                state.data["selected_position"] = position
                state.data["awaiting_position_selection"] = False
                state.data["awaiting_withdraw_amount"] = True
                return await self._ask_withdraw_amount_mm(
                    position, user_context
                ), state
        except ValueError:
            pass

        text_upper = text.upper()
        for pos in positions:
            if pos.get("asset", "").upper() == text_upper:
                state.data["selected_position"] = pos
                state.data["awaiting_position_selection"] = False
                state.data["awaiting_withdraw_amount"] = True
                return await self._ask_withdraw_amount_mm(pos, user_context), state

        language = user_context.language
        if language == "es":
            return (f"❓ Responde con un número (1-{len(positions)}).", state)
        if language == "pt":
            return (f"❓ Responda com um número (1-{len(positions)}).", state)
        return (f"❓ Please reply with a number (1-{len(positions)}).", state)

    async def _ask_withdraw_amount_mm(
        self,
        position: dict[str, Any],
        user_context: UserContext,
    ) -> str:
        """Ask user how much to withdraw."""
        language = user_context.language
        asset = position.get("asset", "")
        amount = position.get("supplied_amount", "0")
        usd_value = position.get("supplied_usd", 0)
        if language == "es":
            return (
                f"💰 **Retiro de {asset}**\n\n"
                f"Tienes **{amount} {asset}** (~${usd_value:,.2f}).\n\n"
                f"¿Cuánto retirar? Escribe un monto o **max**."
            )
        if language == "pt":
            return (
                f"💰 **Retirada de {asset}**\n\n"
                f"Você tem **{amount} {asset}** (~${usd_value:,.2f}).\n\n"
                f"Quanto retirar? Digite um valor ou **max**."
            )
        return (
            f"💰 **Withdraw {asset}**\n\n"
            f"You have **{amount} {asset}** (~${usd_value:,.2f}).\n\n"
            f"How much to withdraw? Enter an amount or **max**."
        )

    async def _handle_withdraw_amount_input_mm(
        self,
        message: MessageContent,
        state: WorkflowState,
        user_context: UserContext,
    ) -> tuple[str, WorkflowState]:
        """Handle withdraw amount (number or max)."""
        text = message.value.strip().lower()
        position = state.data.get("selected_position", {})
        supplied = position.get("supplied_amount", "0")

        if text in ("max", "all", "todo", "tudo"):
            withdraw_amount = supplied
        else:
            amount_match = re.search(r"[\d,]+\.?\d*", text.replace(",", ""))
            if amount_match:
                withdraw_amount = amount_match.group()
            else:
                language = user_context.language
                if language == "es":
                    return ("❓ Escribe un número o 'max'.", state)
                if language == "pt":
                    return ("❓ Digite um número ou 'max'.", state)
                return ("❓ Please enter a number or 'max'.", state)

        state.data["withdraw_amount"] = withdraw_amount
        state.data["awaiting_withdraw_amount"] = False
        state.step = WorkflowStep.CONFIRM.value
        reply, state = await self._show_withdraw_confirmation_mm(
            position, withdraw_amount, user_context, state
        )
        content = self._greeting(user_context) + reply
        content += self._get_confirm_step_snippet(
            withdraw_amount, position.get("asset", ""), position.get("protocol", ""), user_context.language
        )
        return content, state

    async def _show_withdraw_confirmation_mm(
        self,
        position: dict[str, Any],
        amount: str,
        user_context: UserContext,
        state: WorkflowState,
    ) -> tuple[str, WorkflowState]:
        """Show withdraw confirmation."""
        language = user_context.language
        asset = position.get("asset", "")
        protocol = position.get("protocol", "").upper()
        vault_name = position.get("vault_name", "")
        supplied_usd = position.get("supplied_usd", 0)
        supplied_amount = position.get("supplied_amount", "0")
        try:
            ratio = (
                float(amount) / float(supplied_amount)
                if float(supplied_amount) > 0
                else 0
            )
            withdraw_usd = supplied_usd * ratio
        except (ValueError, ZeroDivisionError):
            withdraw_usd = supplied_usd
        display_name = vault_name or f"{asset} on {protocol}"
        if language == "es":
            response = (
                f"📤 **Confirmar retiro**\n\n"
                f"**De:** {display_name}\n"
                f"**Monto:** {amount} {asset} (~${withdraw_usd:,.2f})\n\n"
                f"¿Confirmar? Responde **sí** o **cancelar**."
            )
        elif language == "pt":
            response = (
                f"📤 **Confirmar retirada**\n\n"
                f"**De:** {display_name}\n"
                f"**Valor:** {amount} {asset} (~${withdraw_usd:,.2f})\n\n"
                f"Confirmar? Responda **sim** ou **cancelar**."
            )
        else:
            response = (
                f"📤 **Confirm withdrawal**\n\n"
                f"**From:** {display_name}\n"
                f"**Amount:** {amount} {asset} (~${withdraw_usd:,.2f})\n\n"
                f"Confirm? Reply **yes** or **cancel**."
            )
        return response, state

    def _greeting(self, user_context: UserContext) -> str:
        """Return a short personalized greeting when display_name is available."""
        name = (user_context.display_name or "").strip()
        if not name:
            return ""
        lang = user_context.language or "en"
        if lang == "es":
            return f"Hola **{name}**,\n\n"
        if lang == "pt":
            return f"Olá **{name}**,\n\n"
        return f"Hi **{name}**,\n\n"

    def _get_knowledge_snippet(self, section: str, language: str) -> str:
        """Return workflow knowledge snippet for enterprise-grade responses."""
        lang = (language or "en").lower()
        if lang not in ("en", "es", "pt"):
            lang = "en"
        sections = WORKFLOW_SNIPPETS.get(section, {})
        return sections.get(lang, sections.get("en", ""))

    def _get_confirm_step_snippet(
        self, amount: str, asset: str, protocol: str, language: str
    ) -> str:
        """Contextual, human snippet for confirm step (no sentiment)."""
        protocol_name = (protocol or "protocol").upper()
        amt = (amount or "").strip() or "—"
        asset = (asset or "USD").strip()
        lang = (language or "en").lower()
        if lang == "es":
            return (
                f"\n\n💡 Responde **sí** para enviar {amt} {asset} desde {protocol_name} "
                "a tu wallet, o **cancelar** para cambiar el monto."
            )
        if lang == "pt":
            return (
                f"\n\n💡 Responda **sim** para enviar {amt} {asset} da {protocol_name} "
                "para sua carteira, ou **cancelar** para alterar o valor."
            )
        return (
            f"\n\n💡 Reply **yes** to send {amt} {asset} from {protocol_name} "
            "to your wallet, or **cancel** to change the amount."
        )

    def _get_ready_step_snippet(
        self, amount: str, asset: str, protocol: str, language: str
    ) -> str:
        """Contextual, human snippet for ready step (no sentiment)."""
        protocol_name = (protocol or "protocol").upper()
        amt = (amount or "").strip() or "—"
        asset = (asset or "USD").strip()
        lang = (language or "en").lower()
        if lang == "es":
            return (
                f"\n\n💡 Al firmar, {amt} {asset} pasarán de {protocol_name} "
                "a tu wallet; los verás en unos instantes."
            )
        if lang == "pt":
            return (
                f"\n\n💡 Ao assinar, {amt} {asset} serão transferidos da {protocol_name} "
                "para sua carteira; você os verá em instantes."
            )
        return (
            f"\n\n💡 Once you sign, {amt} {asset} will move from {protocol_name} "
            "to your wallet—you’ll see it there shortly."
        )

    def _format_sentiment_block_enterprise(
        self,
        sentiment: dict[str, Any],
        asset_symbol: str,
        language: str,
    ) -> str:
        """
        Format enterprise-grade sentiment block for new and mid-level traders.

        Clear heading, plain-language interpretation, context, and disclaimer.
        """
        interpretation = (sentiment.get("interpretation") or "").strip() or "neutral"
        score = sentiment.get("score")
        confidence = sentiment.get("confidence")
        time_horizon = sentiment.get("time_horizon") or "24h"
        asset = (asset_symbol or "").strip() or "USD"
        score_str = f"{score:.0f}" if score is not None else "—"
        confidence_note = ""
        if isinstance(confidence, (int, float)) and confidence < 0.7 and confidence > 0:
            if language == "es":
                confidence_note = " (confianza moderada)"
            elif language == "pt":
                confidence_note = " (confiança moderada)"
            else:
                confidence_note = " (moderate confidence)"

        if language == "es":
            heading = f"📊 **Sentimiento de mercado ({time_horizon})**"
            body = (
                f"El sentimiento reciente para **{asset}** es **{interpretation}** "
                f"(puntuación {score_str}/100, basado en noticias{confidence_note}). "
                "Solo como contexto; no modifica la acción recomendada para tu retiro."
            )
            footer = "*No es asesoramiento financiero.*"
        elif language == "pt":
            heading = f"📊 **Sentimento de mercado ({time_horizon})**"
            body = (
                f"O sentimento recente para **{asset}** é **{interpretation}** "
                f"(pontuação {score_str}/100, com base em notícias{confidence_note}). "
                "Apenas como contexto; não altera a ação recomendada para sua retirada."
            )
            footer = "*Não é aconselhamento financeiro.*"
        else:
            heading = f"📊 **Market sentiment ({time_horizon})**"
            body = (
                f"Short-term sentiment for **{asset}** is **{interpretation}** "
                f"(score {score_str}/100, news-based{confidence_note}). "
                "Use as context only; it does not change the recommended action for your withdrawal."
            )
            footer = "*Not financial advice.*"

        return f"\n\n---\n\n{heading}\n\n{body}\n\n{footer}"

    async def _enrich_with_sentiment(
        self,
        content: str,
        state: WorkflowState,
        asset_symbol: str,
        language: str,
    ) -> tuple[str, WorkflowState]:
        """
        Optionally append enterprise-grade Hunter sentiment block and set state.data['sentiment_analysis'].

        Best-effort; returns (content, state) unchanged if no provider or sentiment.
        """
        if not self._sentiment or not (asset_symbol or "").strip():
            return content, state
        try:
            sentiment = await self._sentiment.get_sentiment(asset_symbol.strip())
        except Exception as e:
            logger.debug("[MoneyMarket] Sentiment fetch failed for %s: %s", asset_symbol, e)
            return content, state
        if not sentiment or not isinstance(sentiment, dict):
            return content, state
        state.data["sentiment_analysis"] = sentiment
        block = self._format_sentiment_block_enterprise(
            sentiment, asset_symbol.strip(), language
        )
        return content + block, state

    async def _handle_positions_withdraw_execute(
        self,
        message: MessageContent,
        state: WorkflowState,
        user_context: UserContext,
    ) -> tuple[str, WorkflowState]:
        """Build withdraw execute_data for frontend (Aave only; Compound list-only)."""
        language = user_context.language
        position = state.data.get("selected_position", {})
        withdraw_amount = state.data.get("withdraw_amount", "max")
        wallet_address = user_context.wallet_address

        if not wallet_address:
            msg = (
                "❌ Conecta tu wallet."
                if language == "es"
                else "❌ Conecte sua carteira."
                if language == "pt"
                else "❌ Wallet not connected. Please connect your wallet."
            )
            return msg, state

        protocol = position.get("protocol", "aave")
        asset = position.get("asset", "UNKNOWN")
        chain = position.get("chain", "base")
        vault_name = position.get("vault_name", f"{asset}")

        execute_data: dict[str, Any] | None = None

        if protocol == "compound" and self._compound:
            try:
                withdraw_result = await self._compound.build_withdraw_supply_transaction(
                    user_address=wallet_address,
                    asset_symbol=asset,
                    amount=str(withdraw_amount),
                    chain=chain,
                )
                if withdraw_result.get("success") and not withdraw_result.get("error"):
                    execute_data = self._build_execute_data(
                        action_type="withdraw",
                        provider="compound",
                        chain=chain,
                        amount=withdraw_result.get("amount", str(withdraw_amount)),
                        asset_symbol=withdraw_result.get("asset", asset),
                        asset_address=withdraw_result.get("asset_address"),
                        pool_address=withdraw_result.get("to"),
                        tx_to=withdraw_result.get("to"),
                        tx_data=withdraw_result.get("data"),
                        tx_value=withdraw_result.get("value", "0"),
                    )
                else:
                    err = withdraw_result.get("error", "Unknown error")
                    return f"❌ {err}", state
            except Exception as e:
                logger.error(
                    "[MoneyMarketWorkflow] Compound withdraw build error: %s", e
                )
                return f"❌ Error preparing withdrawal: {e!s}", state
        elif protocol == "aave" and self._aave:
            try:
                withdraw_result = await self._aave.build_withdraw_supply_transaction(
                    user_address=wallet_address,
                    asset_symbol=asset,
                    amount=str(withdraw_amount),
                    chain=chain,
                )
                if withdraw_result.get("success") and not withdraw_result.get("error"):
                    execute_data = self._build_execute_data(
                        action_type="withdraw",
                        provider="aave",
                        chain=chain,
                        amount=withdraw_result.get("amount", str(withdraw_amount)),
                        asset_symbol=withdraw_result.get("asset", asset),
                        asset_address=withdraw_result.get("asset_address"),
                        pool_address=withdraw_result.get("to"),
                        tx_to=withdraw_result.get("to"),
                        tx_data=withdraw_result.get("data"),
                        tx_value=withdraw_result.get("value", "0"),
                    )
                else:
                    err = withdraw_result.get("error", "Unknown error")
                    return f"❌ {err}", state
            except Exception as e:
                logger.error(
                    "[MoneyMarketWorkflow] Aave withdraw build error: %s", e
                )
                return f"❌ Error preparing withdrawal: {e!s}", state
        else:
            msg = (
                f"❌ Protocolo no soportado: {protocol}"
                if language == "es"
                else f"❌ Protocolo não suportado: {protocol}"
                if language == "pt"
                else f"❌ Unsupported protocol: {protocol}"
            )
            return msg, state

        if execute_data:
            state.execute_data = execute_data
            state.step = WorkflowStep.COMPLETED.value
            if language == "es":
                response = (
                    f"✅ **Listo para retirar**\n\n"
                    f"📤 {withdraw_amount} {asset} desde {vault_name or protocol.upper()}\n\n"
                    f"Confirma en tu wallet."
                )
            elif language == "pt":
                response = (
                    f"✅ **Pronto para retirar**\n\n"
                    f"📤 {withdraw_amount} {asset} de {vault_name or protocol.upper()}\n\n"
                    f"Confirme na sua carteira."
                )
            else:
                response = (
                    f"✅ **Ready to withdraw**\n\n"
                    f"📤 {withdraw_amount} {asset} from {vault_name or protocol.upper()}\n\n"
                    f"Please confirm in your wallet."
                )
            content = self._greeting(user_context) + response
            content += self._get_ready_step_snippet(
                withdraw_amount, asset, protocol, language
            )
            return content, state

        return "❌ Could not build transaction.", state

    def _build_insufficient_balance_message(
        self,
        asset: str,
        amount: str,
        user_balance: float,
        language: str,
    ) -> str:
        """Build message when user has insufficient balance to execute deposit."""
        messages = {
            "en": f"""❌ **Unable to execute deposit**

**Deposit requested:** {amount} {asset}
**Your current balance:** ${user_balance:.2f}

You don't have enough {asset} in your wallet to complete this deposit.

---

**💳 Get {asset} to start earning yield:**

1. **Buy with card/Apple Pay/Google Pay:**
   Say: **"buy {asset}"** or **"buy 100 {asset}"**

2. **Transfer from another wallet:**
   Send {asset} to your Anvil wallet address

---

Once you have {asset} in your wallet, come back and try:
**"deposit {amount} {asset}"**
""",
            "es": f"""❌ **No se puede ejecutar el depósito**

**Depósito solicitado:** {amount} {asset}
**Tu saldo actual:** ${user_balance:.2f}

No tienes suficiente {asset} en tu billetera.

**💳 Obtén {asset}:**
• Di: **"comprar {asset}"**
• O transfiere {asset} desde otra billetera
""",
            "pt": f"""❌ **Não é possível executar o depósito**

**Depósito solicitado:** {amount} {asset}
**Seu saldo atual:** ${user_balance:.2f}

Você não tem {asset} suficiente na sua carteira.

**💳 Obtenha {asset}:**
• Diga: **"comprar {asset}"**
• Ou transfira {asset} de outra carteira
""",
        }
        return messages.get(language, messages["en"])

    def _get_funding_recommendation(
        self, asset: str, language: str, balance: float = 0.0
    ) -> str:
        """Build funding recommendation message with balance display."""
        balance_str = f"${balance:,.2f}" if balance > 0 else "$0.00"
        messages = {
            "en": f"""💡 **Heads up:** Your current balance is **{balance_str}**.

To complete this deposit, you'll need {asset} in your wallet.

**Get started:**
• 💳 Say **"buy crypto"** to purchase USDC with card/Apple Pay/Google Pay
• 📥 Or transfer {asset} from another wallet

Here's the deposit quote you requested:""",
            "es": f"""💡 **Aviso:** Tu saldo actual es **{balance_str}**.

Para completar este depósito, necesitas {asset} en tu billetera.

**Comienza:**
• 💳 Di **"comprar cripto"** para comprar USDC con tarjeta
• 📥 O transfiere {asset} desde otra billetera

Aquí está la cotización del depósito:""",
            "pt": f"""💡 **Aviso:** Seu saldo atual é **{balance_str}**.

Para completar este depósito, você precisa de {asset} na sua carteira.

**Comece:**
• 💳 Diga **"comprar cripto"** para comprar USDC com cartão
• 📥 Ou transfira {asset} de outra carteira

Aqui está a cotação do depósito:""",
            "zh": f"""💡 **提示：** 您当前的余额是 **{balance_str}**。

要完成此存款，您需要在钱包中有 {asset}。

**开始：**
• 💳 说 **"买加密货币"** 用卡购买 USDC
• 📥 或从其他钱包转入 {asset}

这是您请求的存款报价：""",
        }
        return messages.get(language, messages["en"])

    def _format_deposit_quote_info(self, data: dict, language: str) -> str:
        """Format deposit quote information for display."""
        protocol = data.get("selected_protocol", "").title()
        asset = data.get("asset", "USDC")
        amount = data.get("amount", "")
        rates = data.get("rates", [])

        # Find rate for selected protocol
        selected_rate = next(
            (r for r in rates if r.get("protocol", "").lower() == protocol.lower()),
            rates[0] if rates else {},
        )
        apy = selected_rate.get("supply_apy", 0)

        amount_str = f"{amount} {asset}" if amount else asset

        messages = {
            "en": f"""📊 **Deposit Quote**

• **Protocol:** {protocol}
• **Asset:** {amount_str}
• **APY:** {apy:.2f}%

Once you have funds, say **"deposit {amount or "100"} {asset}"** to continue.""",
            "es": f"""📊 **Cotización de Depósito**

• **Protocolo:** {protocol}
• **Activo:** {amount_str}
• **APY:** {apy:.2f}%

Una vez que tengas fondos, di **"depositar {amount or "100"} {asset}"** para continuar.""",
            "pt": f"""📊 **Cotação de Depósito**

• **Protocolo:** {protocol}
• **Ativo:** {amount_str}
• **APY:** {apy:.2f}%

Quando tiver fundos, diga **"depositar {amount or "100"} {asset}"** para continuar.""",
        }
        return messages.get(language, messages["en"])

    # ========================================
    # DIRECT API Data Fetching (REAL APIs)
    # ========================================

    async def _fetch_morpho_rate_direct(
        self,
        asset: str,
        chain: str,
    ) -> dict[str, Any] | None:
        """Fetch Morpho vault rate using DIRECT GraphQL API."""

        try:
            client = MorphoClient()
            chain_id = CHAIN_IDS.get(chain.lower(), 8453)  # Default to Base

            # Map ETH to WETH for Morpho lookup (Morpho vaults use WETH)
            lookup_asset = asset.upper()
            if lookup_asset == "ETH":
                lookup_asset = "WETH"
                logger.info(
                    f"[MoneyMarketWorkflow] Mapped ETH → WETH for Morpho lookup"
                )

            # Use token address map so USDT, DAI, etc. get rates when vaults exist
            asset_address = self._get_asset_address(lookup_asset, chain)
            if not asset_address and lookup_asset == "WETH":
                asset_address = self._get_asset_address("ETH", chain)

            # Fetch vaults
            if asset_address:
                vaults = await client.get_vaults(
                    chain_id=chain_id,
                    asset_address=asset_address,
                    whitelisted=True,
                    first=5,
                )
            else:
                vaults = await client.get_vaults(
                    chain_id=chain_id,
                    whitelisted=True,
                    first=10,
                )
                # Filter by asset symbol (use lookup_asset which maps ETH → WETH)
                vaults = [v for v in vaults if lookup_asset in v.asset_symbol.upper()]

            await client.close()

            if not vaults:
                logger.debug(
                    f"[MoneyMarketWorkflow] No Morpho vaults for {asset} on {chain}"
                )
                return None

            # Get best vault by APY
            best_vault = max(vaults, key=lambda v: float(v.net_apy or "0"))
            apy = float(best_vault.net_apy or "0") * 100  # Convert to percentage

            # Convert total_assets from wei to human readable
            decimals = best_vault.asset_decimals or 6
            tvl = (
                float(best_vault.total_assets) / (10**decimals)
                if best_vault.total_assets
                else 0
            )

            logger.info(
                f"[MoneyMarketWorkflow] Morpho {best_vault.name}: {apy:.2f}% APY"
            )

            return {
                "protocol": "morpho",
                "name": f"Morpho ({best_vault.name})",
                "vault_address": best_vault.id,
                "supply_apy": apy,
                "borrow_apy": 0,
                "tvl": tvl,
                "utilization": 0,
            }

        except Exception as e:
            logger.error(f"[MoneyMarketWorkflow] Morpho direct API error: {e}")
            return None

    async def _fetch_compound_rate_direct(
        self,
        asset: str,
        chain: str,
    ) -> dict[str, Any] | None:
        """Fetch Compound V3 rate using DIRECT RPC calls."""

        try:
            client = CompoundClient()
            market = await client.get_market(asset=asset.upper(), chain=chain.lower())
            await client.close()

            if not market:
                logger.debug(
                    f"[MoneyMarketWorkflow] No Compound market for {asset} on {chain}"
                )
                return None

            logger.info(
                f"[MoneyMarketWorkflow] Compound {asset}: {market.supply_apy:.2f}% APY"
            )

            return {
                "protocol": "compound",
                "name": "Compound V3",
                "supply_apy": market.supply_apy,
                "borrow_apy": market.borrow_apy,
                "tvl": market.total_supply,
                "utilization": market.utilization * 100,
            }

        except Exception as e:
            logger.error(f"[MoneyMarketWorkflow] Compound direct API error: {e}")
            return None

    async def _fetch_aave_rate_defillama(
        self,
        asset: str,
        chain: str,
    ) -> dict[str, Any] | None:
        """Fetch Aave V3 rate from DeFiLlama (aggregated data)."""

        try:
            client = DefiLlamaClientDirect()
            yields = await client.get_protocol_yields(protocol="aave-v3")
            await client.close()

            if not yields:
                return None

            # Filter by chain and asset
            chain_name = DEFILLAMA_CHAIN_MAP.get(chain.lower(), chain.title())
            asset_upper = asset.upper()

            matching = [
                y
                for y in yields
                if y.chain.lower() == chain_name.lower()
                and self._symbol_contains_asset(y.symbol, asset_upper)
            ]

            if not matching:
                logger.debug(
                    f"[MoneyMarketWorkflow] No Aave yields for {asset} on {chain}"
                )
                return None

            # Get best yield
            best = max(matching, key=lambda y: y.apy)

            logger.info(f"[MoneyMarketWorkflow] Aave {asset}: {best.apy:.2f}% APY")

            return {
                "protocol": "aave",
                "name": "Aave V3",
                "supply_apy": best.apy,
                "borrow_apy": 0,  # DeFiLlama doesn't provide borrow rates
                "tvl": best.tvl_usd,
                "utilization": 0,
            }

        except Exception as e:
            logger.error(f"[MoneyMarketWorkflow] Aave DeFiLlama error: {e}")
            return None

    # ========================================
    # Gateway-based Data Fetching (Fallback)
    # ========================================

    async def _fetch_aave_rate(
        self,
        asset: str,
        chain: str,
    ) -> dict[str, Any] | None:
        """Fetch Aave V3 rate for asset."""

        if not self._aave:
            logger.warning("[MoneyMarketWorkflow] Aave gateway not available")
            return None

        try:
            market = await self._aave.get_market_details(asset=asset, chain=chain)

            if not market:
                return None

            return {
                "protocol": "aave",
                "name": "Aave V3",
                "supply_apy": float(market.supply_apy),
                "borrow_apy": float(market.borrow_apy_variable),
                "tvl": float(market.total_supplied_usd),
                "utilization": float(market.utilization_rate),
            }

        except Exception as e:
            logger.error(f"[MoneyMarketWorkflow] Error fetching Aave rate: {e}")
            return None

    async def _fetch_compound_rate(
        self,
        asset: str,
        chain: str,
    ) -> dict[str, Any] | None:
        """Fetch Compound V3 rate for asset."""

        if not self._compound:
            logger.warning("[MoneyMarketWorkflow] Compound gateway not available")
            return None

        try:
            market = await self._compound.get_market_details(asset=asset, chain=chain)

            if not market:
                return None

            return {
                "protocol": "compound",
                "name": "Compound V3",
                "supply_apy": float(market.supply_apy)
                if hasattr(market, "supply_apy")
                else 0,
                "borrow_apy": float(market.borrow_apy)
                if hasattr(market, "borrow_apy")
                else 0,
                "tvl": float(market.total_supplied_usd)
                if hasattr(market, "total_supplied_usd")
                else 0,
                "utilization": float(market.utilization_rate)
                if hasattr(market, "utilization_rate")
                else 0,
            }

        except Exception as e:
            logger.error(f"[MoneyMarketWorkflow] Error fetching Compound rate: {e}")
            return None

    async def _fetch_morpho_rate(
        self,
        asset: str,
        chain: str,
    ) -> dict[str, Any] | None:
        """Fetch best Morpho vault rate for asset."""

        if not self._morpho:
            logger.warning("[MoneyMarketWorkflow] Morpho gateway not available")
            return None

        try:
            vaults = await self._morpho.get_vaults(asset=asset, chain=chain)

            if not vaults:
                return None

            # Filter whitelisted and get best vault
            valid_vaults = [v for v in vaults if v.whitelisted]
            if not valid_vaults:
                valid_vaults = vaults

            best_vault = max(valid_vaults, key=lambda v: float(v.apy), default=None)

            if not best_vault:
                return None

            return {
                "protocol": "morpho",
                "name": f"Morpho ({best_vault.name})",
                "vault_address": best_vault.address,
                "supply_apy": float(best_vault.apy),
                "borrow_apy": 0,  # Morpho vaults are supply-only
                "tvl": float(best_vault.total_assets),
                "utilization": 0,
            }

        except Exception as e:
            logger.error(f"[MoneyMarketWorkflow] Error fetching Morpho rate: {e}")
            return None

    async def _fetch_defillama_rates(
        self,
        asset: str,
        chain: str,
    ) -> list[dict[str, Any]]:
        """
        Fetch rates from DeFiLlama as fallback.

        Returns rates for Aave, Compound, and Morpho from DeFiLlama yields API.
        """
        rates = []

        if not self._defillama:
            return rates

        try:
            # Get all yields and filter by protocol
            all_yields = await self._defillama.get_protocol_yields()

            chain_name = DEFILLAMA_CHAIN_MAP.get(chain.lower(), chain.title())
            asset_upper = asset.upper()

            # Protocol mappings
            protocol_map = {
                "aave-v3": ("aave", "Aave V3"),
                "aave-v2": ("aave", "Aave V2"),
                "compound-v3": ("compound", "Compound V3"),
                "compound": ("compound", "Compound"),
                "morpho-blue": ("morpho", "Morpho Blue"),
                "morpho-aave": ("morpho", "Morpho Aave"),
            }

            protocol_rates: dict[str, dict[str, Any]] = {}

            for pool in all_yields:
                # Check chain
                if pool.chain.lower() != chain_name.lower():
                    continue

                # Check asset in symbol
                if not self._symbol_contains_asset(pool.symbol, asset_upper):
                    continue

                # Check if it's a supported protocol
                project_lower = pool.project.lower()
                protocol_info = protocol_map.get(project_lower)

                if not protocol_info:
                    continue

                protocol_id, protocol_name = protocol_info

                # Keep best rate per protocol
                if protocol_id not in protocol_rates or pool.apy > protocol_rates[
                    protocol_id
                ].get("supply_apy", 0):
                    protocol_rates[protocol_id] = {
                        "protocol": protocol_id,
                        "name": protocol_name,
                        "supply_apy": pool.apy,
                        "borrow_apy": 0,
                        "tvl": pool.tvl_usd,
                        "utilization": 0,
                        "pool_id": pool.pool,
                    }

            rates = list(protocol_rates.values())
            logger.info(
                f"[MoneyMarketWorkflow] Found {len(rates)} rates from DeFiLlama for {asset} on {chain}"
            )

        except Exception as e:
            logger.error(f"[MoneyMarketWorkflow] Error fetching DeFiLlama rates: {e}")

        return rates

    def _symbol_contains_asset(self, symbol: str, asset: str) -> bool:
        """Check if pool symbol contains the target asset."""
        symbol_upper = symbol.upper()
        asset_upper = asset.upper()

        # Direct match
        if symbol_upper == asset_upper:
            return True

        # Common variants
        asset_variants = {
            "USDC": ["USDC", "AUSDC", "CUSDC", "USDC.E"],
            "ETH": ["ETH", "WETH", "AETH", "STETH"],
            "DAI": ["DAI", "ADAI", "CDAI", "SDAI"],
            "USDT": ["USDT", "AUSDT", "CUSDT"],
            "WBTC": ["WBTC", "AWBTC", "CWBTC"],
        }

        variants = asset_variants.get(asset_upper, [asset_upper])

        for variant in variants:
            if variant in symbol_upper:
                return True

        return False

    # ========================================
    # Parameter Extraction
    # ========================================

    async def _extract_comparison_params(self, text: str) -> dict[str, Any]:
        """Extract comparison parameters from text."""

        params: dict[str, Any] = {}

        # Try LLM extraction first
        if self._llm:
            try:
                llm_params = await self._extract_params_with_llm(
                    message=text,
                    param_schema={
                        "asset": "string (Token symbol: USDC, ETH, DAI, etc.)",
                        "type": "string (Comparison type: supply or borrow)",
                        "chain": "string (Blockchain network: base, ethereum, etc.)",
                    },
                    examples=[
                        {
                            "input": "compare USDC rates",
                            "output": '{"asset": "USDC", "type": "supply", "chain": "base"}',
                        },
                        {
                            "input": "best ETH borrow rates",
                            "output": '{"asset": "ETH", "type": "borrow", "chain": "base"}',
                        },
                    ],
                )
                if llm_params:
                    params.update(llm_params)
            except Exception as e:
                logger.warning(f"[MoneyMarketWorkflow] LLM extraction failed: {e}")

        # Regex fallback for asset
        if not params.get("asset"):
            for key, info in SUPPORTED_ASSETS.items():
                if key in text or info["symbol"].lower() in text:
                    params["asset"] = info["symbol"]
                    break

        # Detect comparison type
        if "borrow" in text:
            params["type"] = "borrow"
        else:
            params["type"] = "supply"

        # Default chain
        if not params.get("chain"):
            params["chain"] = "base"

        return params

    def _detect_protocol_selection(
        self,
        text: str,
        rates: list[dict[str, Any]],
    ) -> str | None:
        """Detect if user selected a specific protocol."""

        text = text.lower()

        # Direct protocol mention
        if "aave" in text:
            return "aave"
        if "compound" in text:
            return "compound"
        if "morpho" in text:
            return "morpho"

        # Number selection (e.g., "1", "first", "option 1")
        for i, rate in enumerate(rates, 1):
            if str(i) in text or f"option {i}" in text:
                return rate["protocol"]

        # "best" or "top" selection
        if any(word in text for word in ["best", "top", "highest", "first"]):
            return rates[0]["protocol"] if rates else None

        return None

    def _extract_amount(self, text: str) -> str | None:
        """Extract deposit amount from text."""

        match = re.search(r"(\d+(?:,\d{3})*(?:\.\d+)?)", text)
        return match.group(1).replace(",", "") if match else None

    # ========================================
    # Response Formatting
    # ========================================

    def _ask_for_asset(self, language: str, chain: str = "base") -> str:
        """Ask user which asset to compare. Shows only assets with rates on the default chain (Base)."""
        # Numbered list for assets that have rates on Base (no USDT)
        assets = ASSETS_AVAILABLE_ON_BASE
        lines = []
        for i, symbol in enumerate(assets, 1):
            info = SUPPORTED_ASSETS.get(symbol.lower(), {"name": symbol, "emoji": "💰"})
            emoji = info.get("emoji", "💰")
            name = info.get("name", symbol)
            lines.append(f"{i}. {emoji} **{symbol}** ({name})")
        asset_list = "\n".join(lines)
        n = len(assets)

        msgs = {
            "en": f"""📊 **Money Market Rate Comparison**

Compare lending rates across DeFi protocols to find the best yield.

**Available Assets (on Base):**
{asset_list}

**Protocols Compared:**
• Aave V3
• Compound V3

💬 Which asset do you want to compare?
• Reply with a **number (1-{n})** or asset name (e.g., USDC)
• For USDT say **"USDT on Ethereum"**""",
            "es": f"""📊 **Comparación de Tasas del Mercado Monetario**

Compara tasas de préstamo entre protocolos DeFi para encontrar el mejor rendimiento.

**Activos Disponibles (en Base):**
{asset_list}

**Protocolos Comparados:**
• Aave V3
• Compound V3

💬 ¿Qué activo quieres comparar?
• Responde con un **número (1-{n})** o el nombre (ej: USDC)
• Para USDT di **"USDT en Ethereum"**""",
            "pt": f"""📊 **Comparação de Taxas do Mercado Monetário**

Compare taxas de empréstimo entre protocolos DeFi para encontrar o melhor rendimento.

**Ativos Disponíveis (na Base):**
{asset_list}

**Protocolos Comparados:**
• Aave V3
• Compound V3

💬 Qual ativo você quer comparar?
• Responda com um **número (1-{n})** ou nome (ex: USDC)
• Para USDT diga **"USDT na Ethereum"**""",
            "zh": f"""📊 **货币市场利率比较**

比较 DeFi 协议的借贷利率，找到最佳收益。

**可用资产（Base 网络）：**
{asset_list}

**比较的协议：**
• Aave V3
• Compound V3

💬 您想比较哪种资产？
• 回复 **数字 (1-{n})** 或资产名称（如 USDC）
• 比较 USDT 请说 **「USDT on Ethereum」**""",
        }

        return msgs.get(language, msgs["en"])

    def _format_rate_comparison(
        self,
        rates: list[dict[str, Any]],
        asset: str,
        comparison_type: str,
        language: str,
    ) -> str:
        """Format rate comparison table."""

        asset_info = SUPPORTED_ASSETS.get(asset.lower(), {"emoji": "💰"})
        emoji = asset_info.get("emoji", "💰")

        # Build rate rows
        rate_rows = []
        for i, rate in enumerate(rates, 1):
            apy = rate.get("supply_apy", 0)
            name = rate.get("name", rate.get("protocol", "Unknown"))
            protocol = rate.get("protocol", "")

            # Best badge
            badge = "🏆 " if i == 1 else ""

            rate_rows.append(f"{i}. {badge}**{name}**: {apy:.2f}% APY")

        rate_list = "\n".join(rate_rows)
        best_rate = rates[0] if rates else {}
        best_name = best_rate.get("name", "Unknown")
        best_apy = best_rate.get("supply_apy", 0)

        msgs = {
            "en": f"""📊 **{asset} Rate Comparison** {emoji}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Supply APY Rankings:**
{rate_list}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏆 **Best Option:** {best_name} at **{best_apy:.2f}% APY**

**What would you like to do?**
• Reply "aave" or "compound" to deposit
• Enter an amount (e.g., "deposit 1000") to proceed
• Reply "cancel" to exit""",
            "es": f"""📊 **Comparación de Tasas de {asset}** {emoji}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Rankings de APY de Suministro:**
{rate_list}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏆 **Mejor Opción:** {best_name} con **{best_apy:.2f}% APY**

**¿Qué te gustaría hacer?**
• Responde "aave" o "compound" para depositar
• Ingresa una cantidad (ej: "depositar 1000") para continuar
• Responde "cancelar" para salir""",
            "pt": f"""📊 **Comparação de Taxas de {asset}** {emoji}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Rankings de APY de Fornecimento:**
{rate_list}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏆 **Melhor Opção:** {best_name} com **{best_apy:.2f}% APY**

**O que você gostaria de fazer?**
• Responda "aave" ou "compound" para depositar
• Digite uma quantia (ex: "depositar 1000") para continuar
• Responda "cancelar" para sair""",
            "zh": f"""📊 **{asset} 利率比较** {emoji}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**供应 APY 排名：**
{rate_list}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏆 **最佳选择：** {best_name}，**{best_apy:.2f}% APY**

**您想做什么？**
• 回复 "aave" 或 "compound" 进行存款
• 输入金额（例如："存入 1000"）继续
• 回复"取消"退出""",
        }

        return msgs.get(language, msgs["en"])

    def _format_no_rates_available(
        self,
        asset: str,
        chain: str,
        language: str,
    ) -> str:
        """Format message when no rates are available."""
        chain_lower = chain.lower()
        asset_upper = asset.upper()
        # Hint when USDT on Base (limited protocol support)
        usdt_base_hint = ""
        if asset_upper == "USDT" and chain_lower == "base":
            usdt_base_hint = (
                "\n\n💡 USDT has limited lending support on Base. "
                "Try **USDC** or **DAI** on Base, or compare **USDT on Ethereum**."
            )
        hint = usdt_base_hint if usdt_base_hint else ""

        msgs = {
            "en": f"""❌ **No Rates Available**

Sorry, I couldn't fetch rates for **{asset}** on {chain.title()}.{hint}

**Try:**
• Using a different asset (USDC, DAI, ETH)
• Checking back later

Would you like to compare a different asset?""",
            "es": f"""❌ **Tasas No Disponibles**

Lo siento, no pude obtener tasas para **{asset}** en {chain.title()}.{hint}

**Intenta:**
• Usar un activo diferente (USDC, DAI, ETH)
• Verificar más tarde

¿Te gustaría comparar un activo diferente?""",
            "pt": f"""❌ **Taxas Não Disponíveis**

Desculpe, não consegui obter taxas para **{asset}** em {chain.title()}.{hint}

**Tente:**
• Usar um ativo diferente (USDC, DAI, ETH)
• Verificar mais tarde

Gostaria de comparar um ativo diferente?""",
            "zh": f"""❌ **无可用利率**

抱歉，无法获取 {chain.title()} 上 **{asset}** 的利率。{hint}

**尝试：**
• 使用其他资产（USDC、DAI、ETH）
• 稍后再试

您想比较其他资产吗？""",
        }

        return msgs.get(language, msgs["en"])

    def _ask_for_selection(
        self,
        rates: list[dict[str, Any]],
        language: str,
    ) -> str:
        """Ask user to select a protocol."""

        protocols = ", ".join([r.get("name", r.get("protocol", "")) for r in rates])

        msgs = {
            "en": f"""Please select a protocol to proceed:

**Available:** {protocols}

Reply with the protocol name (e.g., "aave") or "cancel" to exit.""",
            "es": f"""Por favor selecciona un protocolo para continuar:

**Disponibles:** {protocols}

Responde con el nombre del protocolo (ej: "aave") o "cancelar" para salir.""",
            "pt": f"""Por favor selecione um protocolo para continuar:

**Disponíveis:** {protocols}

Responda com o nome do protocolo (ex: "aave") ou "cancelar" para sair.""",
            "zh": f"""请选择一个协议继续：

**可用：** {protocols}

回复协议名称（例如："aave"）或"取消"退出。""",
        }

        return msgs.get(language, msgs["en"])

    def _format_protocol_selected(
        self,
        protocol: str,
        data: dict[str, Any],
        language: str,
        balance: float = 0.0,
    ) -> str:
        """Format protocol selection confirmation with user balance."""

        asset = data.get("asset", "USDC")
        rates = data.get("rates", [])
        selected_rate = next((r for r in rates if r["protocol"] == protocol), {})
        apy = selected_rate.get("supply_apy", 0)
        name = selected_rate.get("name", protocol.title())
        balance_str = f"${balance:,.2f}" if balance > 0 else "$0.00"

        msgs = {
            "en": f"""✅ **{name} Selected**

You've chosen to deposit **{asset}** in {name} at **{apy:.2f}% APY**.

💰 **Your available balance:** {balance_str}

Enter the amount you'd like to deposit, or say "cancel" to exit.""",
            "es": f"""✅ **{name} Seleccionado**

Has elegido depositar **{asset}** en {name} al **{apy:.2f}% APY**.

💰 **Tu saldo disponible:** {balance_str}

Ingresa la cantidad que te gustaría depositar, o di "cancelar" para salir.""",
            "pt": f"""✅ **{name} Selecionado**

Você escolheu depositar **{asset}** em {name} a **{apy:.2f}% APY**.

💰 **Seu saldo disponível:** {balance_str}

Digite a quantia que gostaria de depositar, ou diga "cancelar" para sair.""",
            "zh": f"""✅ **已选择 {name}**

您已选择在 {name} 存入 **{asset}**，APY 为 **{apy:.2f}%**。

💰 **您的可用余额：** {balance_str}

输入您想存入的金额，或说"取消"退出。""",
        }

        return msgs.get(language, msgs["en"])

    def _format_deposit_ready(
        self,
        data: dict[str, Any],
        language: str,
    ) -> str:
        """Format deposit ready message."""

        asset = data.get("asset", "USDC")
        amount = data.get("amount", "0")
        protocol = data.get("selected_protocol", "aave")
        rates = data.get("rates", [])
        selected_rate = next((r for r in rates if r["protocol"] == protocol), {})
        name = selected_rate.get("name", protocol.title())
        apy = selected_rate.get("supply_apy", 0)

        msgs = {
            "en": f"""✅ **Deposit Ready**

📊 **Protocol:** {name}
💰 **Amount:** {amount} {asset}
📈 **APY:** {apy:.2f}%

Click **Confirm** to proceed with the deposit.""",
            "es": f"""✅ **Depósito Listo**

📊 **Protocolo:** {name}
💰 **Cantidad:** {amount} {asset}
📈 **APY:** {apy:.2f}%

Haz clic en **Confirmar** para proceder con el depósito.""",
            "pt": f"""✅ **Depósito Pronto**

📊 **Protocolo:** {name}
💰 **Quantia:** {amount} {asset}
📈 **APY:** {apy:.2f}%

Clique em **Confirmar** para prosseguir com o depósito.""",
            "zh": f"""✅ **存款准备就绪**

📊 **协议：** {name}
💰 **金额：** {amount} {asset}
📈 **APY：** {apy:.2f}%

点击 **确认** 继续存款。""",
        }

        return msgs.get(language, msgs["en"])

    def _format_cancelled(self, language: str) -> str:
        """Format cancellation message."""

        msgs = {
            "en": "❌ Rate comparison cancelled. Let me know if you'd like to compare rates again!",
            "es": "❌ Comparación de tasas cancelada. ¡Avísame si quieres comparar tasas de nuevo!",
            "pt": "❌ Comparação de taxas cancelada. Me avise se quiser comparar taxas novamente!",
            "zh": "❌ 利率比较已取消。如果您想再次比较利率，请告诉我！",
        }

        return msgs.get(language, msgs["en"])

    def _format_execution_info(
        self,
        data: dict[str, Any],
        language: str,
    ) -> str:
        """Format execution info message."""

        protocol = data.get("selected_protocol", "aave")
        asset = data.get("asset", "USDC")

        msgs = {
            "en": f"""⏳ **Processing Deposit**

Depositing **{asset}** into **{protocol.title()}**...

Please confirm the transaction in your wallet.""",
            "es": f"""⏳ **Procesando Depósito**

Depositando **{asset}** en **{protocol.title()}**...

Por favor confirma la transacción en tu wallet.""",
            "pt": f"""⏳ **Processando Depósito**

Depositando **{asset}** em **{protocol.title()}**...

Por favor confirme a transação na sua carteira.""",
            "zh": f"""⏳ **处理存款中**

正在将 **{asset}** 存入 **{protocol.title()}**...

请在您的钱包中确认交易。""",
        }

        return msgs.get(language, msgs["en"])

    # ========================================
    # Execute Data Builder
    # ========================================

    # Token addresses by chain
    TOKEN_ADDRESSES: dict[str, dict[str, str]] = {
        "base": {
            "USDC": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
            "USDT": "0xfde4C96c8593536E31F229EA8f37b2ADa2699bb2",
            "WETH": "0x4200000000000000000000000000000000000006",
            "ETH": "0x4200000000000000000000000000000000000006",
            "DAI": "0x50c5725949A6F0c72E6C4a641F24049A917DB0Cb",
            "cbETH": "0x2Ae3F1Ec7F1F5012CFEab0185bfc7aa3cf0DEc22",
        },
        "ethereum": {
            "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
            "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
            "WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
            "DAI": "0x6B175474E89094C44Da98b954EescdeCB5D6F0A",
        },
        "arbitrum": {
            "USDC": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
            "USDT": "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9",
            "WETH": "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",
        },
    }

    def _get_asset_address(self, asset: str, chain: str) -> str | None:
        """Get token contract address for asset on chain."""
        chain_tokens = self.TOKEN_ADDRESSES.get(chain.lower(), {})
        return chain_tokens.get(asset.upper())

    def _build_deposit_execute_data(
        self,
        protocol: str,
        asset: str,
        chain: str,
        rate_data: dict[str, Any],
        amount: str | None = None,
    ) -> dict[str, Any]:
        """Build execute_data for deposit action."""

        # Get asset address for the chain
        asset_address = self._get_asset_address(asset, chain)

        execute_data = {
            "action_type": "deposit",
            "provider": protocol,
            "protocol": protocol,
            "chain": chain,
            "amount": amount,
            "asset_symbol": asset,
            "asset_address": asset_address,
            "supply_apy": rate_data.get("supply_apy", 0),
            "slippage": 0.5,
        }

        # Add protocol-specific fields
        if protocol == "morpho":
            execute_data["vault_address"] = rate_data.get("vault_address")

        # Aave requires pool_address for production (direct pool call, reliable)
        if protocol == "aave":
            execute_data["pool_address"] = rate_data.get("pool_address") or (
                AAVE_POOL_ADDRESSES.get(chain.lower()) if chain else None
            )

        return execute_data

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
            "execute",
            "sí",
            "si",
            "confirmar",
            "vale",
            "continuar",
            "sim",
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
            "exit",
            "cancelar",
            "abortar",
            "parar",
            "salir",
            "取消",
            "不",
            "停止",
            "退出",
        ]
        return any(word in text for word in cancel_words)
