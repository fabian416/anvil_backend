"""
Authenticated Supervisor Coordinator.

LLM-based multi-agent orchestration for authenticated users.
Extends the base SupervisorCoordinator with:
- Real wallet/portfolio data access via UserDataService
- User preferences and history
- Transaction preparation capabilities
- Higher privileges for DeFi operations

This supervisor is optimized for logged-in users who have:
- Connected wallets
- Transaction history
- Portfolio data
- User preferences

Integration with AGNO agents:
- Can delegate to AGNO PortfolioAgent for complex portfolio operations
- Uses MCP tools via AGNO for real-time data
"""

import logging
from typing import TYPE_CHECKING, Any

from app.domain.enums.agent_type import AgentType
from app.domain.value_objects.conversation_id import ConversationId
from app.domain.value_objects.message_content import MessageContent
from app.domain.services.agent_squad.supervisor_coordinator import (
    SupervisorCoordinator,
    WorkflowPlan,
    AgentTask,
    TaskStatus,
)

if TYPE_CHECKING:
    from app.domain.value_objects.agent_squad.conversation_context import (
        ConversationContext,
    )
    from app.domain.ports.agent_squad.llm_client_gateway import LLMClientGateway
    from app.domain.ports.agent_squad.agent_executor_gateway import AgentExecutorPort
    from app.application.chat.services.user_data_service import (
        UserDataService,
        UserDataContext,
    )
    from app.domain.chat.entities.user_context_aware import UserContextAware
    from app.application.chat.services.response_template_service import (
        ResponseTemplateService,
    )

logger = logging.getLogger(__name__)


class AuthenticatedSupervisorCoordinator(SupervisorCoordinator):
    """
    Supervisor Coordinator optimized for authenticated users.

    Key Differences from Guest Supervisor:
    1. Access to real wallet data and portfolio via UserDataService
    2. Can prepare actual transactions (not just demos)
    3. User preferences and history context
    4. No demo mode disclaimers
    5. Higher complexity workflows allowed
    6. Integration with AGNO agents for complex operations

    Architecture:
    - Inherits from SupervisorCoordinator for core workflow logic
    - Overrides prompt building to include auth-specific context
    - Adds wallet/portfolio context injection via UserDataService
    - Can delegate to AGNO agents for specialized operations
    """

    def __init__(
        self,
        llm_client: "LLMClientGateway",
        agent_executor: "AgentExecutorPort",
        user_data_service: "UserDataService | None" = None,
        response_template_service: "ResponseTemplateService | None" = None,
        max_agents: int = 6,  # Higher limit for authenticated users
        timeout_seconds: int = 180,  # Longer timeout for complex workflows
    ):
        """
        Initialize authenticated supervisor.

        Args:
            llm_client: LLM client for workflow planning
            agent_executor: Agent executor for running agents
            user_data_service: Optional service for fetching user wallet/portfolio/tx data
            response_template_service: Optional service for pre-defined response templates
            max_agents: Maximum agents per workflow (default 6, higher than guest)
            timeout_seconds: Workflow timeout (default 180s, longer than guest)
        """
        super().__init__(
            llm_client=llm_client,
            agent_executor=agent_executor,
            max_agents=max_agents,
            timeout_seconds=timeout_seconds,
        )
        self._user_data_service = user_data_service
        self._response_template_service = response_template_service
        self._user_context: dict[str, Any] = {}
        self._user_data_context: "UserDataContext | None" = None
        # Context-aware agent responses
        self._context_aware: "UserContextAware | None" = None

    def set_user_context(
        self,
        user_id: str | None = None,
        wallet_address: str | None = None,
        portfolio_summary: dict[str, Any] | None = None,
        preferences: dict[str, Any] | None = None,
    ) -> None:
        """
        Set user-specific context for workflow planning.

        This context is injected into the planning prompt to give
        the LLM awareness of the user's situation.

        Args:
            user_id: User identifier
            wallet_address: Connected wallet address
            portfolio_summary: Summary of user's holdings
            preferences: User preferences (risk tolerance, favorite chains, etc.)
        """
        self._user_context = {
            "user_id": user_id,
            "wallet_address": wallet_address,
            "portfolio_summary": portfolio_summary or {},
            "preferences": preferences or {},
            "is_authenticated": True,
        }

    def set_context_aware(self, context: "UserContextAware | None") -> None:
        """
        Set pre-computed user context for context-aware agent responses.

        This context comes from the user_context_aware table and includes:
        - Portfolio state (empty, starter, active, whale)
        - Activity level (new, active, inactive, etc.)
        - User type (new_user, casual, trader, yield_farmer, power_user)
        - Execution history (swap_count, buy_count, lending_count, etc.)

        The context is used to:
        1. Enhance the system prompt with user-specific instructions
        2. Pre-validate workflows (e.g., prevent swap for empty portfolios)
        3. Personalize response tone and recommendations

        Args:
            context: The UserContextAware entity or None
        """
        self._context_aware = context
        if context:
            logger.debug(
                f"Set context-aware: portfolio={context.portfolio_state}, "
                f"activity={context.activity_level}, type={context.user_type}"
            )

    async def load_user_data(self, user_id: str) -> None:
        """
        Load complete user data from repositories via UserDataService.

        This fetches wallet, portfolio, and transaction data for the user
        and stores it for context injection into workflows.

        Args:
            user_id: The user's ID to fetch data for
        """
        if not self._user_data_service:
            logger.debug("UserDataService not available, skipping user data load")
            return

        try:
            self._user_data_context = await self._user_data_service.get_user_context(
                user_id=user_id,
                include_portfolio=True,
                include_transactions=True,
                transaction_limit=5,  # Only need recent for context
            )

            # Update user_context with loaded data
            if self._user_data_context:
                if self._user_data_context.primary_wallet:
                    self._user_context["wallet_address"] = (
                        self._user_data_context.primary_wallet.address
                    )
                    self._user_context["wallet_chain"] = (
                        self._user_data_context.primary_wallet.chain_type
                    )
                    # QR code data for receive flows
                    self._user_context["qr_image_url"] = (
                        self._user_data_context.primary_wallet.qr_image_url
                    )
                    self._user_context["qr_data"] = (
                        self._user_data_context.primary_wallet.qr_data
                    )
                    self._user_context["qr_chain_id"] = (
                        self._user_data_context.primary_wallet.qr_chain_id
                    )

                    # Also set primary_wallet dict for agents to consume
                    self._user_context["primary_wallet"] = {
                        "address": self._user_data_context.primary_wallet.address,
                        "chain_type": self._user_data_context.primary_wallet.chain_type,
                        "provider": self._user_data_context.primary_wallet.provider,
                        "qr_image_url": self._user_data_context.primary_wallet.qr_image_url,
                        "qr_data": self._user_data_context.primary_wallet.qr_data,
                        "qr_chain_id": self._user_data_context.primary_wallet.qr_chain_id,
                    }

                # Convert wallets to dicts for agents
                if self._user_data_context.wallets:
                    self._user_context["wallets"] = [
                        {
                            "wallet_id": w.wallet_id,
                            "address": w.address,
                            "chain_type": w.chain_type,
                            "provider": w.provider,
                            "is_primary": w.is_primary,
                            "qr_image_url": w.qr_image_url,
                            "qr_data": w.qr_data,
                            "qr_chain_id": w.qr_chain_id,
                        }
                        for w in self._user_data_context.wallets
                    ]

                if self._user_data_context.portfolio:
                    self._user_context["portfolio_summary"] = {
                        "total_value_usd": self._user_data_context.portfolio.total_value_usd,
                        "token_count": self._user_data_context.portfolio.token_count,
                        "top_holdings": [
                            h["symbol"]
                            for h in self._user_data_context.portfolio.top_holdings[:3]
                        ],
                    }

                if self._user_data_context.transactions:
                    self._user_context["transaction_count"] = (
                        self._user_data_context.transactions.total_count
                    )
                    self._user_context["volume_30d"] = (
                        self._user_data_context.transactions.volume_last_30_days
                    )
                    # Pass full transactions object so TransactionHistoryAgent
                    # can display recent_transactions, volume, chain data
                    self._user_context["transactions"] = (
                        self._user_data_context.transactions
                    )

            logger.info(
                f"✅ Loaded user data for authenticated supervisor",
                extra={
                    "user_id": user_id,
                    "has_wallet": bool(self._user_context.get("wallet_address")),
                    "portfolio_value": self._user_context.get(
                        "portfolio_summary", {}
                    ).get("total_value_usd", 0),
                },
            )

        except Exception as e:
            logger.warning(f"Failed to load user data: {e}")

    async def get_transaction_history(
        self,
        user_id: str,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """
        Get user's transaction history.

        Args:
            user_id: User identifier
            limit: Maximum transactions to return

        Returns:
            List of transaction dictionaries
        """
        if not self._user_data_service:
            return []

        return await self._user_data_service.get_transaction_history(
            user_id=user_id,
            limit=limit,
        )

    async def get_wallet_balances(
        self,
        wallet_address: str,
    ) -> dict[str, Any]:
        """
        Get token balances for a wallet.

        Args:
            wallet_address: The wallet address

        Returns:
            Dictionary with balance information
        """
        if not self._user_data_service:
            return {"error": "User data service not available"}

        return await self._user_data_service.get_wallet_balances(
            wallet_address=wallet_address,
        )

    def can_execute_workflow(self, workflow_type: str) -> tuple[bool, str | None]:
        """
        Check if the user can execute a specific workflow type based on context.

        This provides pre-validation to prevent users from attempting workflows
        that will fail due to insufficient balance or missing prerequisites.

        Args:
            workflow_type: The workflow type (swap, buy, lending, etc.)

        Returns:
            Tuple of (can_execute, reason_if_blocked)
        """
        if not self._context_aware:
            # No context available, allow all
            return True, None

        portfolio_state = self._context_aware.portfolio_state_enum

        # Check portfolio state requirements
        if workflow_type in ("swap", "swap_workflow", "transfer", "transfer_workflow"):
            if not portfolio_state.can_swap:
                return False, (
                    "Your portfolio is empty. You need to buy some crypto first "
                    'before you can swap or transfer. Try: "buy $50 of ETH"'
                )

        # Warn about gas costs for small portfolios
        if workflow_type in ("swap", "swap_workflow", "lending", "lending_workflow"):
            if portfolio_state.warn_gas_costs:
                # Don't block, but the prompt enhancement will warn
                pass

        return True, None

    def get_onboarding_suggestion(self) -> str | None:
        """
        Get an onboarding suggestion based on user context.

        Returns:
            Suggestion string or None if user doesn't need onboarding
        """
        if not self._context_aware:
            return None

        portfolio_state = self._context_aware.portfolio_state_enum
        activity_level = self._context_aware.activity_level_enum

        if portfolio_state.needs_onboarding:
            return (
                "Welcome to Anvil! 🎉 Start your DeFi journey:\n"
                '• **Buy crypto** - Type "buy $50 of ETH" to get started\n'
                '• **Explore rates** - Ask "best yield for USDC" to see earning opportunities\n'
                '• **Get market data** - Try "what\'s the price of ETH?"'
            )

        if activity_level.needs_reengagement:
            return (
                "Welcome back! 👋 Here's what you can do:\n"
                '• **Check portfolio** - "my portfolio" to see your holdings\n'
                '• **Swap tokens** - "swap ETH to USDC" to trade\n'
                '• **Earn yield** - "deposit USDC" to start earning'
            )

        return None

    def set_response_template_service(
        self,
        service: "ResponseTemplateService | None",
    ) -> None:
        """
        Set the response template service for template-based responses.

        Args:
            service: ResponseTemplateService instance or None
        """
        self._response_template_service = service

    def get_template_response(
        self,
        message_key: str,
        language: str = "en",
        **variables: Any,
    ) -> str | None:
        """
        Get a template-based response if available.

        This checks if a pre-defined template exists for the user's
        current context and returns it instead of calling LLM.

        Args:
            message_key: Template message key (e.g., "portfolio_query")
            language: Target language code
            **variables: Variables for template rendering

        Returns:
            Rendered template message or None if no template found
        """
        if not self._response_template_service or not self._context_aware:
            return None

        # Try portfolio state template first
        result = self._response_template_service.get_portfolio_response(
            portfolio_state=self._context_aware.portfolio_state,
            message_key=message_key,
            language=language,
            total_usd=f"{float(self._context_aware.total_balance_usd):,.2f}",
            **variables,
        )

        if result.message:
            return result.message

        # Try activity level template
        result = self._response_template_service.get_activity_response(
            activity_level=self._context_aware.activity_level,
            message_key=message_key,
            language=language,
            **variables,
        )

        if result.message:
            return result.message

        return None

    def check_workflow_blocked_with_template(
        self,
        workflow_type: str,
        language: str = "en",
    ) -> tuple[bool, str | None]:
        """
        Check if workflow is blocked and return template response.

        Combines can_execute_workflow check with template messaging
        for consistent, localized blocked workflow responses.

        Args:
            workflow_type: Workflow type (swap, lending, transfer, etc.)
            language: Target language code

        Returns:
            Tuple of (is_blocked, blocked_message or None)
        """
        # First check basic workflow blocking
        can_execute, reason = self.can_execute_workflow(workflow_type)

        if can_execute:
            return False, None

        # If blocked, try to get template response
        if self._response_template_service and self._context_aware:
            is_blocked, template_msg = (
                self._response_template_service.check_workflow_blocked(
                    portfolio_state=self._context_aware.portfolio_state,
                    workflow=workflow_type,
                    language=language,
                )
            )
            if is_blocked and template_msg:
                return True, template_msg

        # Fallback to basic reason
        return True, reason

    def get_response_style(self) -> str:
        """
        Get the recommended response style for this user.

        Returns:
            Response style: "educational", "concise", "expert", etc.
        """
        if not self._response_template_service or not self._context_aware:
            return "default"

        return self._response_template_service.get_response_style(
            self._context_aware.user_type
        )

    def should_include_explanations(self) -> bool:
        """
        Check if explanations should be included in responses.

        Returns:
            True if explanations should be included
        """
        if not self._response_template_service or not self._context_aware:
            return True

        return self._response_template_service.should_include_explanations(
            self._context_aware.user_type
        )

    def _detect_fresh_workflow_start(
        self,
        message: str,
    ) -> tuple[bool, str | None]:
        """
        Detect if user is starting a fresh/new workflow.

        This is used to cancel any pending workflow when user starts a new one.
        For example, if user has a pending buy confirmation and says "swap ETH to USDC",
        this detects it's a fresh swap workflow request.

        Returns:
            Tuple of (is_fresh_workflow, workflow_type or None)
            workflow_type: "buy", "swap", "lending", "transfer", "money_market", "cashout"
        """
        message_lower = message.lower().strip()

        # Fresh workflow start keywords (multilingual)
        # These indicate user wants to START a new workflow, not continue an existing one
        workflow_keywords = {
            "buy": [
                # English
                "buy crypto",
                "buy usdc",
                "buy token",
                "purchase crypto",
                "purchase usdc",
                "i want to buy",
                "let me buy",
                "can i buy",
                # Spanish
                "comprar cripto",
                "comprar usdc",
                "quiero comprar",
                # Portuguese
                "comprar cripto",
                "comprar usdc",
                "quero comprar",
            ],
            "swap": [
                # English
                "swap",
                "exchange",
                "trade",
                "convert",
                "i want to swap",
                "let me swap",
                "can i swap",
                "swap eth",
                "swap usdc",
                "swap btc",
                # Spanish
                "cambiar",
                "intercambiar",
                "quiero cambiar",
                # Portuguese
                "trocar",
                "quero trocar",
            ],
            "lending": [
                # English - Deposit
                "lend",
                "deposit",
                "supply",
                "earn yield",
                "earn interest",
                "i want to lend",
                "i want to deposit",
                "i want to supply",
                "deposit usdc",
                "supply usdc",
                "lend usdc",
                # English - Withdraw
                "withdraw from",
                "withdraw my",
                "remove from vault",
                "take out from",
                "i want to withdraw",
                "withdraw usdc",
                "withdraw eth",
                "my lendings",
                "my deposits",
                "my lending positions",
                # Spanish - Deposit
                "depositar",
                "prestar",
                "quiero depositar",
                # Spanish - Withdraw
                "retirar de",
                "retirar mi",
                "quiero retirar",
                "sacar de",
                "mis prestamos",
                "mis depositos",
                # Portuguese - Deposit
                "depositar",
                "emprestar",
                "quero depositar",
                # Portuguese - Withdraw
                "retirar de",
                "retirar meu",
                "quero retirar",
                "sacar de",
                "meus emprestimos",
                "meus depositos",
            ],
            "transfer": [
                # English
                "send",
                "transfer",
                "send crypto",
                "transfer crypto",
                "i want to send",
                "i want to transfer",
                "send eth",
                "send usdc",
                "transfer to",
                # Spanish
                "enviar",
                "transferir",
                "quiero enviar",
                # Portuguese
                "enviar",
                "transferir",
                "quero enviar",
            ],
            "money_market": [
                # English - rate comparison
                "compare rates",
                "money market",
                "best rates",
                "yield comparison",
                "check rates",
                "show rates",
                # English - positions + withdraw (Option A)
                "my money market positions",
                "money market positions",
                "withdraw from money market",
                "what am I earning in money market",
                "show my money market",
                "my positions money market",
                # Typo-tolerant
                "my money market possitions",
                "money market possitions",
                # Spanish
                "comparar tasas",
                "mercado de dinero",
                "mejores tasas",
                "mis posiciones mercado monetario",
                "retirar del mercado monetario",
                "qué estoy ganando en mercado monetario",
                # Portuguese
                "comparar taxas",
                "melhores taxas",
                "minhas posições mercado monetário",
                "retirar do mercado monetário",
                "o que estou ganhando no mercado monetário",
            ],
            "cashout": [
                # English - NOTE: "withdraw" alone goes to lending, "withdraw to bank/fiat" goes to cashout
                "cashout",
                "cash out",
                "sell crypto",
                "offramp",
                "off-ramp",
                "i want to cashout",
                "i want to sell",
                "convert to fiat",
                "withdraw to bank",
                "withdraw to fiat",
                "sell to fiat",
                # Spanish
                "vender cripto",
                "quiero vender",
                "convertir a fiat",
                # Portuguese
                "vender cripto",
                "quero vender",
                "converter para fiat",
            ],
        }

        for workflow_type, keywords in workflow_keywords.items():
            for keyword in keywords:
                # Check if message starts with keyword or contains it as a clear command
                if message_lower.startswith(keyword) or message_lower == keyword:
                    logger.info(
                        f"🆕 Fresh workflow detected: {workflow_type} (keyword: {keyword})"
                    )
                    return True, workflow_type
                # Also check "i want to X" patterns
                if (
                    f"want to {keyword}" in message_lower
                    or f"quiero {keyword}" in message_lower
                ):
                    logger.info(
                        f"🆕 Fresh workflow detected: {workflow_type} (pattern: want to {keyword})"
                    )
                    return True, workflow_type

        return False, None

    def _has_pending_workflow(
        self,
        conversation_context: "ConversationContext",
    ) -> tuple[bool, str | None, dict | None]:
        """
        Check if there's a pending workflow in conversation history.

        Returns:
            Tuple of (has_pending, workflow_name, workflow_state)
        """
        if not conversation_context.conversation_history:
            return False, None, None

        # Check recent messages for pending workflow state
        found_non_workflow_response = False
        for msg in reversed(conversation_context.conversation_history[-5:]):
            if isinstance(msg, dict) and msg.get("role") == "assistant":
                metadata = msg.get("metadata", {})
                workflow_state = metadata.get("workflow_state")
                workflow_name = metadata.get("workflow_name")

                # If we see a non-workflow assistant response (portfolio, chat, etc.)
                # before finding a workflow, any older workflow state is stale
                if not workflow_name and not workflow_state:
                    found_non_workflow_response = True

                if workflow_state:
                    # If a non-workflow response came after this workflow,
                    # the user already moved on — workflow is stale, not pending
                    if found_non_workflow_response:
                        logger.info(
                            f"✅ Workflow {workflow_name} is stale (non-workflow response came after) - not pending"
                        )
                        return False, None, None

                    step = workflow_state.get("step", "")
                    # Workflow is pending if it's in confirm, fetch_data, or execute step
                    # NEVER treat "completed" workflows as pending
                    if step in ("confirm", "fetch_data", "execute"):
                        logger.info(
                            f"📋 Found pending workflow: {workflow_name}, step: {step}"
                        )
                        return True, workflow_name, workflow_state
                    elif step == "completed":
                        logger.info(
                            f"✅ Workflow {workflow_name} already completed - not pending"
                        )
                        return False, None, None

                # Also check for execute_data (transaction ready for execution)
                # But NOT if the workflow is already completed
                if metadata.get("execute_data"):
                    if found_non_workflow_response:
                        logger.info(
                            f"✅ Ignoring stale execute_data for {workflow_name} (non-workflow response came after)"
                        )
                        return False, None, None
                    ws = metadata.get("workflow_state", {})
                    if ws.get("step") != "completed":
                        logger.info(
                            f"📋 Found pending execute_data in workflow: {workflow_name}"
                        )
                        return True, workflow_name, workflow_state
                    else:
                        logger.info(
                            f"✅ Ignoring execute_data for completed workflow: {workflow_name}"
                        )
                        return False, None, None

        return False, None, None

    def _is_workflow_continuation(
        self,
        message: str,
        conversation_context: "ConversationContext",
    ) -> tuple[bool, str | None]:
        """
        Check if this message is a continuation of an existing workflow.

        IMPORTANT: If user is starting a FRESH workflow (e.g., says "swap" while
        having a pending buy), this returns (False, None) so the old workflow
        is cancelled and the new one starts fresh.

        Returns:
            Tuple of (is_continuation, workflow_name or None)
        """
        message_lower = message.lower().strip()
        logger.info(f"🔍 Checking workflow continuation for: '{message_lower}'")

        # FIRST: Check if user is starting a fresh/new workflow
        # This takes priority - if user says "swap" while in buy flow, cancel buy and start swap
        is_fresh, fresh_workflow_type = self._detect_fresh_workflow_start(message)
        has_pending, pending_workflow_name, _ = self._has_pending_workflow(
            conversation_context
        )

        # If user is starting a fresh workflow, route directly to it
        # This bypasses LLM planning for reliable routing
        if is_fresh:
            workflow_name = f"{fresh_workflow_type}_workflow"
            if has_pending:
                # Normalize pending workflow name for comparison
                pending_type = (
                    (pending_workflow_name or "")
                    .lower()
                    .replace("workflow", "")
                    .replace("_", "")
                    .strip()
                )

                if fresh_workflow_type != pending_type:
                    logger.info(
                        f"🔄 Fresh workflow '{fresh_workflow_type}' cancels pending '{pending_workflow_name}' - routing directly"
                    )
                else:
                    logger.info(
                        f"🔄 Restarting same workflow type '{fresh_workflow_type}' - routing directly"
                    )
            else:
                logger.info(f"🆕 Fresh workflow detected - routing to {workflow_name}")

            # Mark as fresh start so _load_state ignores old state
            if hasattr(conversation_context, "metadata"):
                if conversation_context.metadata is None:
                    conversation_context.metadata = {}
                conversation_context.metadata["fresh_workflow_start"] = True
                conversation_context.metadata["fresh_workflow_type"] = fresh_workflow_type

            # Route directly to the detected workflow (bypasses LLM)
            return True, workflow_name

        # Confirmation phrases in multiple languages
        confirmation_phrases = {
            # English
            "yes",
            "y",
            "confirm",
            "confirmed",
            "proceed",
            "ok",
            "okay",
            "sure",
            "go ahead",
            "do it",
            "execute",
            "approve",
            # Spanish
            "sí",
            "si",
            "confirmar",
            "confirmado",
            "proceder",
            "vale",
            "adelante",
            "hazlo",
            "ejecutar",
            "aprobar",
            # Portuguese
            "sim",
            "confirmar",
            "confirmado",
            "prosseguir",
            "ok",
            "fazer",
            "executar",
            "aprovar",
            # Chinese
            "是",
            "确认",
            "好",
            "可以",
            "执行",
        }

        # Check if message is a simple confirmation
        is_confirmation = message_lower in confirmation_phrases or any(
            message_lower.startswith(phrase + " ")
            or message_lower.endswith(" " + phrase)
            for phrase in confirmation_phrases
        )

        if conversation_context.conversation_history:
            # FIRST: Check the most recent assistant message's metadata for workflow_name
            # This is the most reliable indicator of which workflow is active
            found_non_workflow_response = False
            for msg in reversed(conversation_context.conversation_history[-3:]):
                if msg.get("role") == "assistant":
                    metadata = msg.get("metadata", {})
                    workflow_name = metadata.get("workflow_name")
                    workflow_state = metadata.get("workflow_state", {})
                    content = msg.get("content", "").lower()

                    # If the most recent assistant message has NO workflow_name,
                    # it means the user already moved on to a non-workflow agent
                    # (portfolio, transaction_history, etc.). Any older workflow
                    # state in history is stale — don't continue it.
                    if not workflow_name:
                        found_non_workflow_response = True

                    if workflow_name:
                        if found_non_workflow_response:
                            logger.info(
                                f"🔍 Stale workflow {workflow_name} found behind non-workflow response — not continuing"
                            )
                            break
                        # Normalize PascalCase to snake_case
                        import re

                        normalized_name = re.sub(
                            r"(?<!^)(?=[A-Z])", "_", workflow_name
                        ).lower()

                        # Check if this workflow is awaiting input (step is parse_request with data)
                        step = workflow_state.get("step", "")
                        data = workflow_state.get("data", {})

                        # Skip completed workflows — they are done
                        if step == "completed":
                            logger.info(
                                f"✅ Workflow {normalized_name} is completed - not continuing"
                            )
                            break

                        # Workflow is awaiting parameters if:
                        # 1. In parse_request step with some data (awaiting more input)
                        # 2. In fetch_data step (just fetched data, might need confirmation)
                        # 3. In confirm step (awaiting user confirmation/selection)
                        # 4. Content asks for input (amount, selection, etc.)
                        is_awaiting = (
                            (step == "parse_request" and data)
                            or step == "fetch_data"
                            or step == "confirm"
                            or any(
                                phrase in content
                                for phrase in [
                                    "enter the amount",
                                    "how much",
                                    "which",
                                    "select",
                                    "enter",
                                    "💬",
                                    "examples:",
                                    "reply",  # "Reply aave, compound, or morpho"
                                    "respond",  # Spanish/Portuguese
                                ]
                            )
                        )

                        if is_awaiting:
                            # CRITICAL: Only continue workflow if user's message looks like a parameter
                            # Don't continue if user is asking something completely different
                            user_msg_lower = message.lower().strip()
                            user_msg_original = message.strip()

                            # Check if user message is a valid workflow continuation:
                            # - Numeric value (amount)
                            # - Confirmation words
                            # - Token/crypto names
                            # - Wallet addresses (EVM or Solana)
                            # - Very short responses (1-2 words, likely selection)
                            is_parameter_like = (
                                # Numeric (with or without decimals, optional $ prefix)
                                re.match(r"^[\$]?\d+\.?\d*$", user_msg_lower)
                                or
                                # Confirmation words
                                user_msg_lower
                                in (
                                    "yes",
                                    "no",
                                    "confirm",
                                    "cancel",
                                    "sí",
                                    "sim",
                                    "não",
                                    "cancelar",
                                )
                                or
                                # Token symbols (short uppercase words)
                                re.match(r"^[a-z]{2,6}$", user_msg_lower)
                                or
                                # Menu selection (1, 2, 3, etc. or "option 1")
                                re.match(r"^(option\s*)?\d$", user_msg_lower)
                                or
                                # "all" for depositing entire balance
                                user_msg_lower == "all"
                                or
                                # EVM wallet addresses (0x followed by 40 hex chars)
                                re.match(r"^0x[a-fA-F0-9]{40}$", user_msg_original)
                                or
                                # Solana wallet addresses (32-44 alphanumeric base58)
                                re.match(
                                    r"^[1-9A-HJ-NP-Za-km-z]{32,44}$", user_msg_original
                                )
                            )

                            # Check if user is asking a different question (not a parameter)
                            is_different_intent = any(
                                phrase in user_msg_lower
                                for phrase in [
                                    "list",
                                    "show",
                                    "what",
                                    "how",
                                    "tell",
                                    "my",
                                    "portfolio",
                                    "holdings",
                                    "balance",
                                    "price",
                                    "help",
                                    "?",
                                ]
                            )

                            if is_parameter_like and not is_different_intent:
                                logger.info(
                                    f"🔄 Parameter-awaiting workflow from metadata: {normalized_name} "
                                    f"(step={step}, has_data={bool(data)}, msg='{user_msg_lower[:20]}')"
                                )
                                return True, normalized_name
                            else:
                                logger.info(
                                    f"🔍 Workflow {normalized_name} awaiting input, but user message "
                                    f"'{user_msg_lower[:30]}' looks like a different intent - not continuing"
                                )

                    # Only check the most recent assistant message
                    break

        if not is_confirmation:
            logger.info(f"🔍 Not a confirmation phrase, skipping workflow continuation")
            return False, None

        logger.info(f"🔍 Detected confirmation phrase, checking history...")
        logger.info(
            f"🔍 History length: {len(conversation_context.conversation_history) if conversation_context.conversation_history else 0}"
        )

        # Check conversation history for pending workflow
        # Note: conversation_history is in chronological order (oldest first)
        # We iterate in reverse to check newest messages first
        if conversation_context.conversation_history:
            for msg in reversed(conversation_context.conversation_history[-10:]):
                if isinstance(msg, dict):
                    metadata = msg.get("metadata", {})

                    # Check for workflow state
                    workflow_state = metadata.get("workflow_state")
                    if workflow_state and workflow_state.get("step") == "confirm":
                        workflow_name = metadata.get("workflow_name")
                        # Normalize workflow name to snake_case for agent mapping
                        # e.g., "LendingWorkflow" -> "lending_workflow"
                        if workflow_name:
                            import re

                            # Convert PascalCase to snake_case
                            workflow_name = re.sub(
                                r"(?<!^)(?=[A-Z])", "_", workflow_name
                            ).lower()
                        logger.info(
                            f"🔄 Found pending workflow continuation: {workflow_name}"
                        )
                        return True, workflow_name

                    # Check for pending action (execute data in previous message)
                    content = msg.get("content", "")
                    if content and any(
                        phrase in content.lower()
                        for phrase in [
                            "ready to swap",
                            "ready to deposit",
                            "ready to buy",
                            "listo para",
                            "pronto para",
                            "准备好了",
                            'reply "yes"',
                            "reply 'yes'",
                            'responde "sí"',
                        ]
                    ):
                        # Infer workflow from content
                        if "swap" in content.lower():
                            return True, "swap_workflow"
                        elif (
                            "deposit" in content.lower() or "lending" in content.lower()
                        ):
                            return True, "lending_workflow"
                        elif "buy" in content.lower() or "purchase" in content.lower():
                            return True, "buy_workflow"
                        elif "transfer" in content.lower() or "send" in content.lower():
                            return True, "transfer_workflow"

        return False, None

    async def create_workflow_plan(
        self,
        conversation_id: "ConversationId",
        message: "MessageContent",
        conversation_context: "ConversationContext",
        available_agents: list["AgentType"],
    ) -> "WorkflowPlan":
        """
        Create workflow plan with continuation support.

        Overrides parent to check for workflow continuations first.
        If user is confirming a pending workflow, routes to same agent.
        """
        # Check for workflow continuation
        is_continuation, workflow_name = self._is_workflow_continuation(
            message.value, conversation_context
        )

        if is_continuation and workflow_name:
            # Route to the workflow agent that's awaiting confirmation
            from app.domain.enums.agent_type import AgentType

            workflow_to_agent = {
                "swap_workflow": AgentType.SWAP_WORKFLOW,
                "lending_workflow": AgentType.LENDING_WORKFLOW,
                "buy_workflow": AgentType.BUY_WORKFLOW,
                "transfer_workflow": AgentType.TRANSFER_WORKFLOW,
                "money_market_workflow": AgentType.MONEY_MARKET_WORKFLOW,
                # Cashout maps to buy workflow for now (same fiat on/off ramp logic)
                "cashout_workflow": AgentType.BUY_WORKFLOW,
            }

            agent_type = workflow_to_agent.get(workflow_name)
            if not agent_type:
                # Unknown workflow - let LLM decide
                logger.warning(
                    f"⚠️ Unknown workflow '{workflow_name}', falling back to LLM planning"
                )
                return await super().create_workflow_plan(
                    conversation_id=conversation_id,
                    message=message,
                    conversation_context=conversation_context,
                    available_agents=available_agents,
                )

            logger.info(
                f"🔄 Continuing workflow {workflow_name} with agent {agent_type.value}"
            )

            # Create a simple workflow plan that continues the existing workflow
            task = AgentTask(
                agent_type=agent_type,
                task_description=f"Continue {workflow_name} - user confirmed",
                depends_on=[],
            )

            return WorkflowPlan(
                tasks=[task],
                execution_order=[0],
                estimated_time_seconds=5,
            )

        # Otherwise, use normal workflow planning
        return await super().create_workflow_plan(
            conversation_id=conversation_id,
            message=message,
            conversation_context=conversation_context,
            available_agents=available_agents,
        )

    def _build_planning_prompt(
        self,
        message: MessageContent,
        conversation_context: "ConversationContext",
        available_agents: list[AgentType],
    ) -> str:
        """
        Build workflow planning prompt for authenticated users.

        Extends base prompt with:
        - User wallet context
        - Real data access instructions
        - No demo mode disclaimers
        - Transaction preparation capabilities
        """
        agents_str = ", ".join([agent.value for agent in available_agents])

        # Build conversation history context (keep minimal)
        context_section = ""
        if conversation_context.conversation_history:
            recent = conversation_context.conversation_history[-3:]
            if recent:
                context_section = "\n<context>\n"
                for msg in recent:
                    role = msg.get("role", "user")
                    content = msg.get("content", "")[:150]
                    if content:
                        context_section += f"{role}: {content}\n"
                context_section += "</context>\n"

        # Build user context section for authenticated users
        user_context_section = ""
        if self._user_context or self._user_data_context or self._context_aware:
            user_context_section = "\n<user_profile>\n"
            user_context_section += (
                "User Status: AUTHENTICATED (can execute REAL transactions)\n"
            )

            # Add context-aware classification if available
            if self._context_aware:
                user_context_section += (
                    f"Portfolio State: {self._context_aware.portfolio_state}\n"
                )
                user_context_section += (
                    f"Activity Level: {self._context_aware.activity_level}\n"
                )
                user_context_section += f"User Type: {self._context_aware.user_type}\n"

                # Add execution history summary
                total_executions = (
                    self._context_aware.swap_count
                    + self._context_aware.buy_count
                    + self._context_aware.lending_count
                    + self._context_aware.money_market_count
                )
                if total_executions > 0:
                    user_context_section += f"Total Executions: {total_executions} ("
                    exec_parts = []
                    if self._context_aware.swap_count:
                        exec_parts.append(f"{self._context_aware.swap_count} swaps")
                    if self._context_aware.buy_count:
                        exec_parts.append(f"{self._context_aware.buy_count} buys")
                    if self._context_aware.lending_count:
                        exec_parts.append(
                            f"{self._context_aware.lending_count} deposits"
                        )
                    user_context_section += ", ".join(exec_parts) + ")\n"

                # Add context-aware prompt enhancements
                prompt_enhancements = (
                    self._context_aware.get_combined_prompt_enhancement()
                )
                if prompt_enhancements:
                    user_context_section += (
                        f"\n⚠️ CONTEXT-AWARE INSTRUCTIONS:\n{prompt_enhancements}\n"
                    )

            # Use loaded user data context if available
            if self._user_data_context:
                user_context_section += (
                    self._user_data_context.to_context_string() + "\n"
                )
            elif self._user_context:
                # Fallback to basic user context
                if self._user_context.get("wallet_address"):
                    addr = self._user_context["wallet_address"]
                    user_context_section += f"Wallet: {addr[:10]}...{addr[-6:]}\n"
                if self._user_context.get("portfolio_summary"):
                    portfolio = self._user_context["portfolio_summary"]
                    if portfolio.get("total_value_usd"):
                        user_context_section += (
                            f"Portfolio Value: ${portfolio['total_value_usd']:,.2f}\n"
                        )
                    if portfolio.get("top_holdings"):
                        holdings = portfolio["top_holdings"][:3]
                        if isinstance(holdings[0], dict):
                            holdings = [h.get("symbol", str(h)) for h in holdings]
                        user_context_section += f"Top Holdings: {', '.join(holdings)}\n"
                if self._user_context.get("transaction_count"):
                    user_context_section += f"Transaction History: {self._user_context['transaction_count']} total\n"
                if self._user_context.get("volume_30d"):
                    user_context_section += (
                        f"30-Day Volume: ${self._user_context['volume_30d']:,.2f}\n"
                    )

            user_context_section += "</user_profile>\n"

        return f"""You are a DeFi workflow router for AUTHENTICATED users. Route the CURRENT request only. JSON only.

<request>{message.value}</request>
{context_section}{user_context_section}
<agents>{agents_str}</agents>

<rules>
CRITICAL: Route based on the CURRENT <request> ONLY. Ignore conversation history for routing decisions.
CRITICAL: "my transactions", "transaction history", "recent activity", "my activity" → ALWAYS route to "transaction_history" agent, NEVER to money_market_workflow or any workflow agent.

⚠️ AUTHENTICATED USER CAPABILITIES:
- User has a connected wallet and can execute REAL transactions
- Portfolio queries return REAL data (not demo)
- Swap/lending queries can prepare ACTUAL transactions
- No need for registration prompts - user is logged in

⚠️ GREETINGS - ALWAYS route to "chat" agent:
- "hi", "hello", "hey", "hola", "oi", "olá" → ALWAYS route to "chat" agent, single task, ignore history
- If the CURRENT request is ONLY a greeting (1-2 words), return: {{"tasks":[{{"agent_type":"chat","task_description":"Greet warmly","depends_on":[]}}]}}
- Do NOT continue previous conversation context for standalone greetings

⚠️ CREATIVE REQUESTS (poems, stories, analogies about crypto) → ALWAYS route to "chat" agent:
- "write a poem about gas fees", "haceme un poema sobre ETH", "poem about bitcoin" → ALWAYS use "chat" agent
- Creative writing about crypto topics is ALLOWED and should go to "chat" (which is more creative)
- If user asks for POEM + DATA (e.g., "poem about gas + current price"), use BOTH "chat" (for poem) AND the data agent (e.g., "gas_optimizer" for price)

⚠️ IMPORTANT DISTINCTION - SWAP RATE vs YIELD:
- "swap rate", "exchange rate", "convert X to Y", "best rate for ETH to USDC" → ALWAYS use "hunter_ai" (token exchange pricing)
- "yield", "APY", "yield farms", "lending rates" → use "defi_yield" (interest/returns on deposits)
- If the query mentions converting/swapping one token to another → "hunter_ai", NOT defi_yield!

⚠️ MULTI-INTENT QUERIES (CRITICAL - PARALLEL EXECUTION):
When user asks MULTIPLE questions in ONE message, create MULTIPLE PARALLEL tasks:
- Each distinct question/request = separate task with depends_on: []
- Tasks without dependencies execute IN PARALLEL (simultaneously)
- Look for conjunctions: "and", "also", "plus", "tell me X and Y", "what about X? also Y"
- Look for multiple question marks or sentence breaks

EXAMPLES OF MULTI-INTENT PARALLEL:
- "what swaps can I do AND price of PEPE" → TWO parallel tasks:
  1. knowledge (swap info) - depends_on: []
  2. hunter_ai (PEPE price) - depends_on: []
- "my portfolio and best yields" → TWO parallel tasks:
  1. portfolio - depends_on: []
  2. defi_yield - depends_on: []
- "price of BTC, ETH, and SOL" → ONE task (hunter_ai handles multiple tokens)
- "what is DeFi? also check gas prices" → TWO parallel tasks:
  1. knowledge (DeFi explanation) - depends_on: []
  2. gas_optimizer (gas prices) - depends_on: []

DO NOT merge unrelated requests into single task - split them for parallel execution!

1. OFF-TOPIC DETECTION (check FIRST):
   - Cooking, recipes, non-crypto topics → Single "chat" task with "Explain DeFi focus"
   
2. WALLET QUERIES (authenticated - REAL data):
   - "my wallets", "connected wallets", "wallet address" → "wallet" agent (REAL wallet data)
   - "wallet info", "list wallets", "show wallets" → "wallet" agent
   - "receive crypto", "receive funds", "QR code", "my QR", "deposit address" → "wallet" agent (shows address + QR)
   
3. TRANSACTION HISTORY (authenticated - REAL data):
   - "my transactions", "transaction history", "recent activity" → "transaction_history" agent
   - "show transactions", "past swaps", "activity summary" → "transaction_history" agent
   - "my activity", "show activity", "what have I done" → "transaction_history" agent
   
4. PORTFOLIO (authenticated - REAL data):
   - "my portfolio", "my balance", "my holdings" → "portfolio" agent (returns REAL data)
   - "portfolio value", "total holdings" → "portfolio" agent
   
5. SWAP EXECUTION (CRITICAL - Multi-step workflow):
   - "swap X to Y", "exchange X for Y", "convert X to Y" (with specific amounts) → "swap_workflow" agent ONLY
   - The swap_workflow agent handles the COMPLETE multi-step swap process autonomously
   - Use "swap_workflow" when user wants to EXECUTE a swap (has specific amount like "0.5 ETH")
   - Examples: "swap 1 ETH to USDC", "exchange 100 USDC for ETH", "convert 0.5 ETH to DAI"
   - DO NOT combine swap_workflow with other agents - it handles everything internally

5b. SWAP POSITIONS / MY SWAPS (CRITICAL - shows Hyperliquid positions):
   - "my swaps", "my swap positions", "show my swaps", "my trades" → "swap_workflow" agent ONLY
   - "mis swaps", "mis intercambios", "meus swaps", "meus trades" → "swap_workflow" agent ONLY
   - The swap_workflow agent shows Hyperliquid spot balances, perps positions, and recent swap history
   - Users can then select a position to swap from, or start a new swap
   - This is analogous to "my lendings" → lending_workflow
   - DO NOT route "my swaps" to transaction_history – it MUST go to swap_workflow
   
6. SWAP INFORMATION (what swaps are available - educational):
   - "what type of swaps can I do", "what swaps can I make", "what tokens can I swap" → "knowledge" agent
   - "can I swap ETH", "can I swap BTC", "how do swaps work on Anvil" → "knowledge" agent
   - Anvil uses Hyperliquid Spot with 440+ tokens (PURR, TRUMP, PEPE, etc.) paired with USDC
   - Some major L1 tokens (ETH, BTC, SOL) may not be available on Hyperliquid Spot
   - Use "knowledge" when user asks ABOUT swap capabilities (informational), not executing a swap
   
7. SWAP RATE INFO (price information only - no execution):
   - "what's the rate for ETH to USDC", "best swap rate" (NO specific amount) → "hunter_ai"
   - "price of ETH", "ETH price in USDC" → "hunter_ai"
   - Use hunter_ai only when user wants PRICE INFO without execution intent
   
8. LENDING/DEPOSIT/WITHDRAW EXECUTION (CRITICAL - Multi-step workflow):
   - "deposit X USDC", "lend X ETH", "earn yield on X USDC" (with specific amounts) → "lending_workflow" agent ONLY
   - "withdraw my USDC", "withdraw from vault", "remove my deposit" → "lending_workflow" agent ONLY
   - The lending_workflow agent handles BOTH deposit AND withdraw operations autonomously
   - Use "lending_workflow" when user wants to EXECUTE a deposit OR withdraw from lending positions
   - Deposit Examples: "deposit 1000 USDC", "lend 0.5 ETH", "deposit into morpho", "earn yield on 500 DAI"
   - Withdraw Examples: "withdraw my USDC", "withdraw from morpho", "remove my lending", "my lendings"
   - "my lendings", "my deposits", "my lending positions" → "lending_workflow" (shows positions for withdrawal)
   - DO NOT combine lending_workflow with other agents - it handles everything internally
   - NOTE: "withdraw to bank/fiat" or "sell crypto" → use "buy_workflow" (cashout flow), NOT lending_workflow
   
9. YIELD INFO (rates information only - no execution):
   - "best yield for USDC", "compare lending rates" (NO specific amount) → "defi_yield"
   - "what APY can I get", "yield farming options" → "defi_yield" + "risk_analyzer"
   - Use defi_yield when user wants RATE INFO without deposit intent

9b. HEALTH FACTOR / LENDING POSITION MONITORING (Aave positions):
   - "what's my health factor", "check my health factor", "health factor" → "lending_borrowing" agent
   - "my lending position", "my Aave position", "am I at risk of liquidation" → "lending_borrowing" agent
   - "liquidation risk", "collateral health", "borrow limit" → "lending_borrowing" agent
   - The lending_borrowing agent checks REAL Aave positions and health factors
   - Examples: "what's my health factor", "check my lending position", "am I safe from liquidation"
   - NOTE: This is for MONITORING existing positions, not for CREATING new deposits (use lending_workflow for deposits)

10. TRANSFER/SEND EXECUTION (CRITICAL - Multi-step workflow):
    - "send X ETH to 0x...", "transfer X USDC to wallet" (with specific amounts) → "transfer_workflow" agent ONLY
    - The transfer_workflow agent handles the COMPLETE multi-step transfer process autonomously
    - Use "transfer_workflow" when user wants to SEND/TRANSFER tokens (has specific amount AND recipient)
    - Examples: "send 100 USDC to 0x123...", "transfer 0.5 ETH to my friend", "send tokens"
    - DO NOT combine transfer_workflow with other agents - it handles everything internally

11. BUY CRYPTO EXECUTION (CRITICAL - Multi-step workflow):
    - "buy $100 of ETH", "purchase crypto", "buy USDC with card" → "buy_workflow" agent ONLY
    - The buy_workflow agent handles the COMPLETE multi-step purchase process autonomously
    - Use "buy_workflow" when user wants to BUY crypto with fiat (card, Apple Pay, etc.)
    - Examples: "buy $50 of ETH", "purchase 100 dollars of USDC", "buy crypto"
    - DO NOT combine buy_workflow with other agents - it handles everything internally

12. MONEY MARKET / LENDING PROTOCOL RATES (CRITICAL - Multi-step workflow):
    - "compare rates", "best APY for USDC", "where should I deposit" → "money_market_workflow" agent ONLY
    - "my money market positions", "withdraw from money market", "what am I earning in money market" → "money_market_workflow" (positions + withdraw flow)
    - The money_market_workflow agent handles COMPLETE rate comparison AND money market positions/withdraw
    - Use "money_market_workflow" when user wants to COMPARE rates, VIEW positions, or WITHDRAW from money market
    - PROTOCOL-SPECIFIC QUERIES (IMPORTANT): When user mentions "Aave rates", "Compound rates", "Morpho rates", 
      "Aave APY", "lending rates on X protocol" → ALWAYS use "money_market_workflow" (NOT hunter_ai!)
    - NOTE: "Aave" as a PROTOCOL for lending rates → money_market_workflow
            "AAVE" as a TOKEN for price → hunter_ai (only when asking for token PRICE)
    - Examples: "compare USDC rates", "best lending rates", "where to deposit ETH", "money market"
    - Examples: "Aave rates for ETH", "what are Compound rates", "Morpho APY", "lending rates on Aave"
    - SPANISH: "comparar tasas", "mejores tasas", "donde depositar" → "money_market_workflow"
    - PORTUGUESE: "comparar taxas", "melhores taxas", "onde depositar" → "money_market_workflow"
    - DO NOT combine money_market_workflow with other agents - it handles comparison and deposit selection
   
13. PRICE/MARKET DATA:
    - Token prices → "hunter_ai"
    - Gas prices → "gas_optimizer"
    - Market sentiment → "hunter_ai"
   
14. RISK/SECURITY:
    - Protocol risk → "risk_analyzer"
    - Security audit → "security_auditor"
   
15. EDUCATIONAL:
    - DeFi explanations → "knowledge"
    - Protocol comparisons → "knowledge"
    - Swap capabilities → "knowledge" (what swaps can I do, what tokens are supported)

16. ADVANCED MARKET ANALYSIS (CRITICAL - route to appropriate agents):
    - Historical patterns, bull/bear market cycles → "hunter_ai" (market analysis)
    - "Bitcoin price patterns during bull markets" → "hunter_ai"
    - "are we in a bull market or bear market" → "hunter_ai"
    - Market regime detection, cycle analysis → "hunter_ai"
    - Correlation analysis between tokens → "hunter_ai"
    - Liquidity depth, order book analysis → "hunter_ai"
    - Whale activity, large transactions → "hunter_ai"
    - DEX volume analysis → "hunter_ai"
    - Token unlocks, vesting schedules → "hunter_ai"
    - Market cap, FDV analysis → "hunter_ai"
   
17. CROSS-CHAIN ANALYSIS:
    - Cross-chain arbitrage → "hunter_ai" + "risk_analyzer"
    - Bridge opportunities → "hunter_ai"
    - Multi-chain portfolio analysis → "portfolio" + "hunter_ai"
   
18. PORTFOLIO ANALYSIS (authenticated - use REAL data):
    - Portfolio rebalancing suggestions → "portfolio" + "hunter_ai"
    - Risk-adjusted recommendations → "portfolio" + "risk_analyzer"
    - "Should I rebalance my portfolio" → "portfolio" + "hunter_ai"
    - Allocation optimization → "portfolio" + "defi_yield"
</rules>

<examples>
"hi" → {{"tasks":[{{"agent_type":"chat","task_description":"Greet warmly","depends_on":[]}}]}}
"hello" → {{"tasks":[{{"agent_type":"chat","task_description":"Greet warmly","depends_on":[]}}]}}
"hola" → {{"tasks":[{{"agent_type":"chat","task_description":"Greet warmly in Spanish","depends_on":[]}}]}}
"my wallets" → {{"tasks":[{{"agent_type":"wallet","task_description":"Show user's connected wallets","depends_on":[]}}]}}
"show my wallet address" → {{"tasks":[{{"agent_type":"wallet","task_description":"Display user's wallet addresses","depends_on":[]}}]}}
"receive crypto" → {{"tasks":[{{"agent_type":"wallet","task_description":"Show wallet address for receiving crypto with QR code","depends_on":[]}}]}}
"give me my QR code" → {{"tasks":[{{"agent_type":"wallet","task_description":"Show wallet QR code for receiving funds","depends_on":[]}}]}}
"QR code" → {{"tasks":[{{"agent_type":"wallet","task_description":"Show wallet QR code","depends_on":[]}}]}}
"my transactions" → {{"tasks":[{{"agent_type":"transaction_history","task_description":"Show user's transaction history","depends_on":[]}}]}}
"recent activity" → {{"tasks":[{{"agent_type":"transaction_history","task_description":"Show recent transaction activity","depends_on":[]}}]}}
"my activity" → {{"tasks":[{{"agent_type":"transaction_history","task_description":"Show user's activity and transactions","depends_on":[]}}]}}
"my portfolio" → {{"tasks":[{{"agent_type":"portfolio","task_description":"Get user's real portfolio data","depends_on":[]}}]}}
"my balance" → {{"tasks":[{{"agent_type":"portfolio","task_description":"Get user's wallet balance","depends_on":[]}}]}}
"swap 1 ETH to USDC" → {{"tasks":[{{"agent_type":"swap_workflow","task_description":"Execute swap: 1 ETH to USDC","depends_on":[]}}]}}
"exchange 100 USDC for ETH" → {{"tasks":[{{"agent_type":"swap_workflow","task_description":"Execute swap: 100 USDC to ETH","depends_on":[]}}]}}
"convert 0.5 ETH to DAI" → {{"tasks":[{{"agent_type":"swap_workflow","task_description":"Execute swap: 0.5 ETH to DAI","depends_on":[]}}]}}
"my swaps" → {{"tasks":[{{"agent_type":"swap_workflow","task_description":"Show user's Hyperliquid swap positions and recent swap history","depends_on":[]}}]}}
"my swap positions" → {{"tasks":[{{"agent_type":"swap_workflow","task_description":"Show user's swap positions on Hyperliquid","depends_on":[]}}]}}
"show my swaps" → {{"tasks":[{{"agent_type":"swap_workflow","task_description":"Show user's swap positions and trade history","depends_on":[]}}]}}
"mis swaps" → {{"tasks":[{{"agent_type":"swap_workflow","task_description":"Show user's swap positions (Spanish)","depends_on":[]}}]}}
"meus swaps" → {{"tasks":[{{"agent_type":"swap_workflow","task_description":"Show user's swap positions (Portuguese)","depends_on":[]}}]}}
"best swap rate ETH to USDC" → {{"tasks":[{{"agent_type":"hunter_ai","task_description":"Get swap rate for ETH to USDC","depends_on":[]}}]}}
"deposit 1000 USDC" → {{"tasks":[{{"agent_type":"lending_workflow","task_description":"Execute deposit: 1000 USDC into vault","depends_on":[]}}]}}
"lend 0.5 ETH" → {{"tasks":[{{"agent_type":"lending_workflow","task_description":"Execute deposit: 0.5 ETH into vault","depends_on":[]}}]}}
"earn yield on 500 DAI" → {{"tasks":[{{"agent_type":"lending_workflow","task_description":"Execute deposit: 500 DAI into vault","depends_on":[]}}]}}
"withdraw my USDC" → {{"tasks":[{{"agent_type":"lending_workflow","task_description":"Execute withdraw: user USDC from lending position","depends_on":[]}}]}}
"withdraw from morpho" → {{"tasks":[{{"agent_type":"lending_workflow","task_description":"Execute withdraw: from Morpho vault","depends_on":[]}}]}}
"remove my deposit" → {{"tasks":[{{"agent_type":"lending_workflow","task_description":"Execute withdraw: remove user's lending deposit","depends_on":[]}}]}}
"my lendings" → {{"tasks":[{{"agent_type":"lending_workflow","task_description":"Show user's lending positions for potential withdrawal","depends_on":[]}}]}}
"my deposits" → {{"tasks":[{{"agent_type":"lending_workflow","task_description":"Show user's lending deposits","depends_on":[]}}]}}
"retirar mi USDC" → {{"tasks":[{{"agent_type":"lending_workflow","task_description":"Execute withdraw: user USDC from lending (Spanish)","depends_on":[]}}]}}
"quiero retirar" → {{"tasks":[{{"agent_type":"lending_workflow","task_description":"Execute withdraw: from lending position (Spanish)","depends_on":[]}}]}}
"retirar meu deposito" → {{"tasks":[{{"agent_type":"lending_workflow","task_description":"Execute withdraw: from lending position (Portuguese)","depends_on":[]}}]}}
"best yield for USDC" → {{"tasks":[{{"agent_type":"defi_yield","task_description":"Find best yield opportunities for USDC","depends_on":[]}},{{"agent_type":"risk_analyzer","task_description":"Assess risk of top yield options","depends_on":["defi_yield"]}}]}}
"send 100 USDC to 0x742d35Cc6634C0532925a3b844Bc454e4438f44e" → {{"tasks":[{{"agent_type":"transfer_workflow","task_description":"Execute transfer: 100 USDC to 0x742d35Cc6634C0532925a3b844Bc454e4438f44e","depends_on":[]}}]}}
"transfer 0.5 ETH to my friend" → {{"tasks":[{{"agent_type":"transfer_workflow","task_description":"Execute transfer: 0.5 ETH - need recipient address","depends_on":[]}}]}}
"send ETH" → {{"tasks":[{{"agent_type":"transfer_workflow","task_description":"Execute transfer: ETH - need amount and recipient","depends_on":[]}}]}}
"buy $100 of ETH" → {{"tasks":[{{"agent_type":"buy_workflow","task_description":"Execute buy: $100 of ETH","depends_on":[]}}]}}
"purchase 50 dollars of USDC" → {{"tasks":[{{"agent_type":"buy_workflow","task_description":"Execute buy: $50 of USDC","depends_on":[]}}]}}
"buy crypto" → {{"tasks":[{{"agent_type":"buy_workflow","task_description":"Execute buy: need crypto and amount","depends_on":[]}}]}}
"compare USDC rates" → {{"tasks":[{{"agent_type":"money_market_workflow","task_description":"Compare USDC rates across Aave, Compound, Morpho","depends_on":[]}}]}}
"compare rates for USDC" → {{"tasks":[{{"agent_type":"money_market_workflow","task_description":"Compare USDC rates across protocols","depends_on":[]}}]}}
"USDC rate comparison" → {{"tasks":[{{"agent_type":"money_market_workflow","task_description":"Compare USDC lending rates","depends_on":[]}}]}}
"Morpho vs Aave rates" → {{"tasks":[{{"agent_type":"money_market_workflow","task_description":"Compare Morpho vs Aave lending rates","depends_on":[]}}]}}
"Morpho vs Aave for USDC" → {{"tasks":[{{"agent_type":"money_market_workflow","task_description":"Compare Morpho vs Aave rates for USDC","depends_on":[]}}]}}
"best lending rates for ETH" → {{"tasks":[{{"agent_type":"money_market_workflow","task_description":"Compare ETH lending rates across protocols","depends_on":[]}}]}}
"Aave rates for ETH" → {{"tasks":[{{"agent_type":"money_market_workflow","task_description":"Get Aave lending/supply rates for ETH","depends_on":[]}}]}}
"what are Aave rates" → {{"tasks":[{{"agent_type":"money_market_workflow","task_description":"Get Aave protocol lending rates","depends_on":[]}}]}}
"Aave APY" → {{"tasks":[{{"agent_type":"money_market_workflow","task_description":"Get Aave protocol APY rates","depends_on":[]}}]}}
"Compound rates for USDC" → {{"tasks":[{{"agent_type":"money_market_workflow","task_description":"Get Compound lending rates for USDC","depends_on":[]}}]}}
"Morpho rates" → {{"tasks":[{{"agent_type":"money_market_workflow","task_description":"Get Morpho protocol rates","depends_on":[]}}]}}
"lending rates on Aave" → {{"tasks":[{{"agent_type":"money_market_workflow","task_description":"Get Aave lending/supply rates","depends_on":[]}}]}}
"supply rates on Compound" → {{"tasks":[{{"agent_type":"money_market_workflow","task_description":"Get Compound supply rates","depends_on":[]}}]}}
"compare lending protocols" → {{"tasks":[{{"agent_type":"money_market_workflow","task_description":"Compare lending protocols and rates","depends_on":[]}}]}}
"compare lending rates" → {{"tasks":[{{"agent_type":"money_market_workflow","task_description":"Compare lending rates across protocols","depends_on":[]}}]}}
"where should I deposit DAI" → {{"tasks":[{{"agent_type":"money_market_workflow","task_description":"Compare DAI deposit rates and recommend best protocol","depends_on":[]}}]}}
"comparar tasas de USDC" → {{"tasks":[{{"agent_type":"money_market_workflow","task_description":"Compare USDC rates across protocols (Spanish)","depends_on":[]}}]}}
"comparar tasas" → {{"tasks":[{{"agent_type":"money_market_workflow","task_description":"Compare lending rates across protocols (Spanish)","depends_on":[]}}]}}
"mejores tasas para USDC" → {{"tasks":[{{"agent_type":"money_market_workflow","task_description":"Find best USDC rates (Spanish)","depends_on":[]}}]}}
"donde depositar" → {{"tasks":[{{"agent_type":"money_market_workflow","task_description":"Recommend best deposit protocol (Spanish)","depends_on":[]}}]}}
"comparar taxas de USDC" → {{"tasks":[{{"agent_type":"money_market_workflow","task_description":"Compare USDC rates across protocols (Portuguese)","depends_on":[]}}]}}
"melhores taxas" → {{"tasks":[{{"agent_type":"money_market_workflow","task_description":"Find best rates (Portuguese)","depends_on":[]}}]}}
"my money market positions" → {{"tasks":[{{"agent_type":"money_market_workflow","task_description":"Show user's money market positions (Aave/Morpho) for withdrawal","depends_on":[]}}]}}
"withdraw from money market" → {{"tasks":[{{"agent_type":"money_market_workflow","task_description":"Withdraw from money market position","depends_on":[]}}]}}
"what am I earning in money market" → {{"tasks":[{{"agent_type":"money_market_workflow","task_description":"Show money market positions and earnings","depends_on":[]}}]}}
"what's my health factor" → {{"tasks":[{{"agent_type":"lending_borrowing","task_description":"Check user health factor on Aave","depends_on":[]}}]}}
"check my health factor" → {{"tasks":[{{"agent_type":"lending_borrowing","task_description":"Check user health factor on Aave","depends_on":[]}}]}}
"my health factor" → {{"tasks":[{{"agent_type":"lending_borrowing","task_description":"Check user health factor on Aave","depends_on":[]}}]}}
"health factor" → {{"tasks":[{{"agent_type":"lending_borrowing","task_description":"Check user health factor on Aave","depends_on":[]}}]}}
"my lending position" → {{"tasks":[{{"agent_type":"lending_borrowing","task_description":"Check user lending positions on Aave","depends_on":[]}}]}}
"am I at risk of liquidation" → {{"tasks":[{{"agent_type":"lending_borrowing","task_description":"Check liquidation risk for user positions","depends_on":[]}}]}}
"liquidation risk" → {{"tasks":[{{"agent_type":"lending_borrowing","task_description":"Check user liquidation risk on Aave","depends_on":[]}}]}}
"my Aave position" → {{"tasks":[{{"agent_type":"lending_borrowing","task_description":"Check user Aave lending position","depends_on":[]}}]}}
"what type of swaps can I do" → {{"tasks":[{{"agent_type":"knowledge","task_description":"Explain Anvil swap capabilities: Hyperliquid Spot with 440+ tokens, USDC pairs","depends_on":[]}}]}}
"what swaps can I make" → {{"tasks":[{{"agent_type":"knowledge","task_description":"Explain Anvil swap capabilities: Hyperliquid Spot with 440+ tokens","depends_on":[]}}]}}
"what tokens can I swap" → {{"tasks":[{{"agent_type":"knowledge","task_description":"Explain supported swap tokens: 440+ tokens on Hyperliquid Spot (PURR, TRUMP, PEPE, etc.) paired with USDC","depends_on":[]}}]}}
"can I swap ETH" → {{"tasks":[{{"agent_type":"knowledge","task_description":"Explain ETH may not be on Hyperliquid Spot - 440+ other tokens available via HL Spot, ETH available via Perps","depends_on":[]}}]}}
"can I swap BTC" → {{"tasks":[{{"agent_type":"knowledge","task_description":"Explain BTC may not be on Hyperliquid Spot - 440+ other tokens available via HL Spot, BTC available via Perps","depends_on":[]}}]}}
"how do swaps work" → {{"tasks":[{{"agent_type":"knowledge","task_description":"Explain how swaps work on Anvil via Hyperliquid Spot with 440+ tokens","depends_on":[]}}]}}
"write a poem about gas fees" → {{"tasks":[{{"agent_type":"chat","task_description":"Write a creative poem about Ethereum gas fees","depends_on":[]}}]}}
"btc price" → {{"tasks":[{{"agent_type":"hunter_ai","task_description":"Get BTC price","depends_on":[]}}]}}
"what is defi" → {{"tasks":[{{"agent_type":"knowledge","task_description":"Explain DeFi concepts","depends_on":[]}}]}}
"Show me Bitcoin's price patterns during the last 3 bull markets" → {{"tasks":[{{"agent_type":"hunter_ai","task_description":"Analyze Bitcoin historical price patterns and bull market cycles","depends_on":[]}}]}}
"are we in a bull market or bear market" → {{"tasks":[{{"agent_type":"hunter_ai","task_description":"Analyze current market regime and cycle phase","depends_on":[]}}]}}
"BTC trading signals" → {{"tasks":[{{"agent_type":"hunter_ai","task_description":"Get BTC trading signals and indicators","depends_on":[]}}]}}
"will ETH go up" → {{"tasks":[{{"agent_type":"hunter_ai","task_description":"Analyze ETH price prediction and market direction","depends_on":[]}}]}}
"bitcoin social sentiment" → {{"tasks":[{{"agent_type":"hunter_ai","task_description":"Analyze Bitcoin social media sentiment","depends_on":[]}}]}}
"crypto news" → {{"tasks":[{{"agent_type":"hunter_ai","task_description":"Get latest crypto news and market updates","depends_on":[]}}]}}
"when is the best time to execute Ethereum transactions to save on gas" → {{"tasks":[{{"agent_type":"gas_optimizer","task_description":"Analyze optimal gas timing for Ethereum transactions","depends_on":[]}}]}}
"how correlated are BTC, ETH, and SOL" → {{"tasks":[{{"agent_type":"hunter_ai","task_description":"Analyze correlation between BTC, ETH, and SOL price movements","depends_on":[]}}]}}
"find arbitrage opportunities between Ethereum and Polygon" → {{"tasks":[{{"agent_type":"hunter_ai","task_description":"Find cross-chain arbitrage opportunities ETH-Polygon","depends_on":[]}},{{"agent_type":"risk_analyzer","task_description":"Assess risk of arbitrage opportunities","depends_on":["hunter_ai"]}}]}}
"I have 70% ETH and 30% BTC. Should I rebalance?" → {{"tasks":[{{"agent_type":"portfolio","task_description":"Analyze current portfolio allocation","depends_on":[]}},{{"agent_type":"hunter_ai","task_description":"Provide market-based rebalancing recommendation","depends_on":["portfolio"]}}]}}
"suggest low-risk DeFi yield opportunities" → {{"tasks":[{{"agent_type":"defi_yield","task_description":"Find low-risk yield opportunities","depends_on":[]}},{{"agent_type":"risk_analyzer","task_description":"Filter by risk level","depends_on":["defi_yield"]}}]}}
"whale activity for BTC" → {{"tasks":[{{"agent_type":"hunter_ai","task_description":"Analyze whale activity and large BTC transactions","depends_on":[]}}]}}
"DEX volume for Uniswap" → {{"tasks":[{{"agent_type":"hunter_ai","task_description":"Analyze Uniswap DEX trading volume","depends_on":[]}}]}}
"token unlocks this week" → {{"tasks":[{{"agent_type":"hunter_ai","task_description":"Get upcoming token unlock schedules","depends_on":[]}}]}}
"DeFi protocols by market cap" → {{"tasks":[{{"agent_type":"hunter_ai","task_description":"List DeFi protocols ranked by market capitalization","depends_on":[]}}]}}
"ETH staking yield" → {{"tasks":[{{"agent_type":"hunter_ai","task_description":"Get current ETH staking yields across validators","depends_on":[]}}]}}
"what type of swaps can I do? tell me the price of PEPE and TRUMP" → {{"tasks":[{{"agent_type":"knowledge","task_description":"Explain Anvil swap capabilities: Hyperliquid Spot with 440+ tokens","depends_on":[]}},{{"agent_type":"hunter_ai","task_description":"Get current prices for PEPE and TRUMP","depends_on":[]}}]}}
"my portfolio and price of BTC" → {{"tasks":[{{"agent_type":"portfolio","task_description":"Get user's real portfolio data","depends_on":[]}},{{"agent_type":"hunter_ai","task_description":"Get current BTC price","depends_on":[]}}]}}
"what is defi? also check gas prices" → {{"tasks":[{{"agent_type":"knowledge","task_description":"Explain DeFi concepts","depends_on":[]}},{{"agent_type":"gas_optimizer","task_description":"Get current gas prices","depends_on":[]}}]}}
"best yields and my balance" → {{"tasks":[{{"agent_type":"defi_yield","task_description":"Find best yield opportunities","depends_on":[]}},{{"agent_type":"portfolio","task_description":"Get user's wallet balance","depends_on":[]}}]}}
"price of PEPE, TRUMP, and MOG" → {{"tasks":[{{"agent_type":"hunter_ai","task_description":"Get current prices for PEPE, TRUMP, and MOG","depends_on":[]}}]}}
</examples>

Output ONLY valid JSON: {{"tasks":[{{"agent_type":"...","task_description":"...","depends_on":[]}}]}}"""

    async def execute_workflow(
        self,
        conversation_id: ConversationId,
        workflow_plan: WorkflowPlan,
        conversation_context: "ConversationContext",
        original_message: str | None = None,
    ) -> tuple[str, list[Any], list[dict[str, Any]]]:
        """
        Execute workflow with authenticated user context.

        Injects user context into the conversation context before execution.
        User context (including balance state) is passed to agents so they can
        handle insufficient funds with helpful recommendations (not blocking).

        Args:
            conversation_id: Conversation identifier
            workflow_plan: Workflow plan to execute
            conversation_context: Conversation context
            original_message: The current user message (CRITICAL: prevents context pollution)
        """
        # NOTE: Balance checking is done IN the workflow agents (swap, lending, money_market)
        # They show helpful recommendations when user has insufficient funds
        # We do NOT block here - agents handle it with context-aware messaging

        # Inject user context into conversation context metadata
        if self._user_context and conversation_context.user_metadata:
            conversation_context.user_metadata.update(self._user_context)
        elif self._user_context:
            conversation_context.user_metadata = self._user_context.copy()

        # Inject context_aware data for workflow agents to use
        # This enables agents to show personalized recommendations based on portfolio state
        if self._context_aware:
            if conversation_context.user_metadata is None:
                conversation_context.user_metadata = {}

            total_balance = float(self._context_aware.total_balance_usd or 0)

            # For workflow agents (use direct properties)
            conversation_context.user_metadata["portfolio_state"] = (
                self._context_aware.portfolio_state
            )
            conversation_context.user_metadata["total_balance_usd"] = total_balance
            conversation_context.user_metadata["has_connected_wallet"] = (
                self._context_aware.has_connected_wallet
            )

            # For non-workflow agents (wallet, portfolio, transaction_history)
            # These agents expect portfolio_summary dict with total_value_usd key
            conversation_context.user_metadata["portfolio_summary"] = {
                "total_value_usd": total_balance,
                "token_count": self._context_aware.token_count or 0,
                "chain": self._context_aware.primary_chain,
            }

            logger.debug(
                f"Injected context_aware into workflow: portfolio={self._context_aware.portfolio_state}, "
                f"balance=${total_balance:.2f}"
            )

        # Execute using parent implementation with original_message
        return await super().execute_workflow(
            conversation_id=conversation_id,
            workflow_plan=workflow_plan,
            conversation_context=conversation_context,
            original_message=original_message,
        )

    async def _aggregate_results(
        self,
        workflow_plan: "WorkflowPlan",
    ) -> str:
        """
        Override to filter out auth prompts for authenticated users.

        When the user is logged in, never show "Account Required" or "Sign up"
        from any single agent (e.g. transaction_history when context is missing).
        """
        content = await super()._aggregate_results(workflow_plan)
        if not content:
            return content
        auth_keywords = [
            "account required",
            "wallet required",
            "sign up",
            "create an account",
        ]
        if any(kw in content.lower() for kw in auth_keywords):
            logger.warning(
                "Filtering auth prompt from agent response for authenticated user"
            )
            return (
                "Your request was received. If you were asking about transaction "
                "history or activity, try again in a moment—your data may still be syncing."
            )
        return content

    def _build_aggregation_message(
        self,
        workflow_plan: "WorkflowPlan",
        chat_task: "AgentTask",
    ) -> str:
        """
        Build aggregation message for authenticated users.

        Override parent method to be more explicit about using ONLY agent data,
        preventing conversation history from polluting the response.
        """
        from app.domain.services.agent_squad.supervisor_coordinator import TaskStatus
        from app.domain.ports.agent_squad.agent_gateway import AgentResponse

        # Get all completed tasks except the CHAT aggregator task
        other_tasks = [
            task
            for task in workflow_plan.tasks
            if task.status == TaskStatus.COMPLETED and task != chat_task
        ]

        if not other_tasks:
            return chat_task.task_description

        # Build aggregation message - more explicit for authenticated users
        parts = [
            "CRITICAL: Your ONLY job is to aggregate the specialist agent responses below.",
            "DO NOT add information from conversation history or your own knowledge.",
            "ONLY use the data provided in 'Agent Responses' section below.",
            "",
            "Instructions:",
            "- Remove duplicates and create a single coherent response",
            "- Include only ONE disclaimer at the end",
            "- Focus on the ACTUAL DATA returned by the agents (prices, rates, percentages, etc.)",
            "- DO NOT mention swaps, yield farming, or other topics unless they appear in Agent Responses",
            "- FILTER OUT authentication messages ('Account Required', 'Sign up') - the user is already authenticated",
            "",
            "Agent Responses (USE ONLY THIS DATA):",
            "",
        ]

        for i, task in enumerate(other_tasks, 1):
            if isinstance(task.result, AgentResponse):
                content = task.result.content or "(No response)"
            elif isinstance(task.result, str):
                content = task.result
            else:
                content = str(task.result) if task.result else "(No response)"

            # Skip authentication messages for authenticated users
            if content and any(
                kw in content.lower()
                for kw in [
                    "account required",
                    "wallet required",
                    "sign up",
                    "create an account",
                ]
            ):
                continue

            parts.append(f"--- Response from {task.agent_type.value.upper()} Agent ---")
            parts.append(content)
            parts.append("")

        return "\n".join(parts)
