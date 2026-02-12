"""
Base Workflow Agent for AGNO-based Multi-Step Operations.

Provides the foundation for multi-step DeFi workflow agents that:
1. Maintain conversation state across turns
2. Generate execute_data for frontend execution modal
3. Handle user confirmations and modifications
4. Support natural conversation flow

Architecture:
- Subclasses implement specific workflows (swap, lending, etc.)
- State is stored in WorkflowState and passed via conversation context
- execute_data follows ExecuteActionData schema for /execute endpoint
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, TYPE_CHECKING

from app.domain.enums.agent_type import AgentType
from app.domain.ports.agent_squad.agent_gateway import AgentGateway, AgentResponse
from app.domain.value_objects.message_content import MessageContent

if TYPE_CHECKING:
    from app.domain.value_objects.agent_squad.conversation_context import (
        ConversationContext,
    )
    from app.domain.value_objects.conversation_id import ConversationId
    from app.domain.ports.agent_squad.llm_client_gateway import LLMClientGateway

logger = logging.getLogger(__name__)


class WorkflowStep(str, Enum):
    """Standard workflow steps."""

    # Initial step - parse user request
    PARSE_REQUEST = "parse_request"

    # Get quotes/data from external sources
    FETCH_DATA = "fetch_data"

    # Show quote and ask for confirmation
    CONFIRM = "confirm"

    # Ready for execution
    EXECUTE = "execute"

    # Workflow completed
    COMPLETED = "completed"

    # Workflow cancelled
    CANCELLED = "cancelled"


@dataclass
class WorkflowState:
    """
    State of a multi-step workflow.

    This state is passed through conversation context and allows
    the workflow to continue across multiple turns.

    Attributes:
        step: Current step in the workflow
        data: Accumulated data from previous steps (tokens, amounts, quotes)
        confirmed: User has confirmed the action
        cancelled: User cancelled the workflow
        execute_data: Data for frontend execution modal (matches ExecuteActionData schema)
        error: Error message if workflow failed
    """

    step: str = WorkflowStep.PARSE_REQUEST.value
    data: dict[str, Any] = field(default_factory=dict)
    confirmed: bool = False
    cancelled: bool = False
    execute_data: dict[str, Any] | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert state to dictionary for serialization."""
        return {
            "step": self.step,
            "data": self.data,
            "confirmed": self.confirmed,
            "cancelled": self.cancelled,
            "execute_data": self.execute_data,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorkflowState":
        """Create state from dictionary."""
        return cls(
            step=data.get("step", WorkflowStep.PARSE_REQUEST.value),
            data=data.get("data", {}),
            confirmed=data.get("confirmed", False),
            cancelled=data.get("cancelled", False),
            execute_data=data.get("execute_data"),
            error=data.get("error"),
        )


@dataclass
class UserContext:
    """
    User context for workflow execution.

    Contains user-specific data needed for workflow execution,
    including portfolio state for context-aware recommendations.
    """

    user_id: int | None = None
    wallet_address: str | None = None
    language: str = "en"
    is_authenticated: bool = False
    preferences: dict[str, Any] = field(default_factory=dict)
    display_name: str | None = None  # First name or display name for personalization

    # Portfolio/balance context for workflow agents
    # Agents use this to show helpful recommendations when user has insufficient funds
    portfolio_state: str = "unknown"  # empty, starter, active, whale
    total_balance_usd: float = 0.0
    has_connected_wallet: bool = False

    def has_insufficient_funds_for_amount(self, amount: float) -> bool:
        """Check if user has insufficient funds for a specific amount."""
        # Add small buffer (5%) for gas/fees
        required = amount * 1.05
        return self.total_balance_usd < required

    @property
    def has_insufficient_funds(self) -> bool:
        """Check if user likely has insufficient funds (empty portfolio)."""
        # Only flag as insufficient if truly empty or near-zero
        return self.portfolio_state == "empty" or self.total_balance_usd < 1.0

    @property
    def needs_funding_recommendation(self) -> bool:
        """Check if we should recommend buying crypto (empty portfolio)."""
        return self.has_insufficient_funds and self.is_authenticated


class BaseWorkflowAgent(AgentGateway, ABC):
    """
    Base class for AGNO-based multi-step workflow agents.

    Subclasses implement specific workflows (swap, lending, etc.)
    while this base class handles:
    - State management via WorkflowState
    - LLM-based parameter extraction
    - Response formatting with execute_data
    - Error handling

    Integration with ExecuteActionData:
    The execute_data generated by workflow agents must match the
    ExecuteActionData schema used by the /execute endpoint:

    ```python
    execute_data = {
        "action_type": "swap",  # swap, deposit, withdraw, transfer, approve, bridge
        "provider": "1inch",    # 1inch, lifi, morpho, aave, privy
        "chain": "base",        # ethereum, base, arbitrum, polygon
        "from_token": "ETH",    # Source token symbol or address
        "to_token": "USDC",     # Destination token symbol
        "amount": "0.5",        # Human readable amount
        "protocol": "morpho",   # For deposit/withdraw
        "vault_address": "0x...",  # For Morpho deposits
        "recipient": "0x...",   # For transfers
        "slippage": 1.0,        # Slippage tolerance
        "to_chain": "ethereum", # For cross-chain
    }
    ```
    """

    def __init__(
        self,
        llm_client: "LLMClientGateway | None" = None,
    ):
        """
        Initialize base workflow agent.

        Args:
            llm_client: LLM client for natural language understanding
        """
        self._llm = llm_client

    @property
    @abstractmethod
    def agent_type(self) -> AgentType:
        """Return the agent type for this workflow."""
        pass

    @property
    @abstractmethod
    def workflow_name(self) -> str:
        """Human-readable name for this workflow."""
        pass

    @property
    def workflow_steps(self) -> list[str]:
        """
        Define the steps in this workflow.

        Subclasses can override to customize steps.
        Default flow: parse → fetch → confirm → execute
        """
        return [
            WorkflowStep.PARSE_REQUEST.value,
            WorkflowStep.FETCH_DATA.value,
            WorkflowStep.CONFIRM.value,
            WorkflowStep.EXECUTE.value,
        ]

    @abstractmethod
    async def process_step(
        self,
        message: MessageContent,
        state: WorkflowState,
        user_context: UserContext,
    ) -> tuple[str, WorkflowState]:
        """
        Process current workflow step.

        This is the main method subclasses implement. It should:
        1. Handle the current step based on state.step
        2. Update state with new data/step
        3. Return (response_content, updated_state)

        Args:
            message: Current user message
            state: Current workflow state
            user_context: User-specific context (wallet, language)

        Returns:
            Tuple of (response_content, updated_state)
        """
        pass

    def _detect_different_workflow_intent(
        self,
        message: str,
    ) -> tuple[bool, str | None]:
        """
        Detect if user message is intended for a DIFFERENT workflow.

        This allows workflows to recognize when user is switching to a different
        operation and gracefully hand off. Generic detection based on keywords.

        Returns:
            Tuple of (is_different_workflow, detected_workflow_type or None)
        """
        message_lower = message.lower().strip()

        # Map keywords to workflow types
        workflow_keywords = {
            "swap_workflow": [
                "swap",
                "exchange",
                "trade",
                "convert",
                "cambiar",
                "intercambiar",
                "trocar",
            ],
            "lending_workflow": [
                "lend",
                "deposit",
                "supply",
                "earn yield",
                "earn interest",
                "deposit to",
                "supply to",
                "lend to",
                "depositar",
                "prestar",
                "emprestar",
                "morpho",
                "aave",
                "compound",  # Protocol names
            ],
            "buy_workflow": [
                "buy crypto",
                "buy usdc",
                "buy token",
                "purchase",
                "comprar cripto",
                "comprar",
                "quero comprar",
                "on-ramp",
                "onramp",
                "fiat",
            ],
            "transfer_workflow": [
                "send",
                "transfer",
                "send to",
                "transfer to",
                "enviar",
                "transferir",
            ],
            "money_market_workflow": [
                "compare rates",
                "money market",
                "best rates",
                "yield comparison",
                "comparar tasas",
                "comparar taxas",
            ],
        }

        # Don't detect different workflow for confirmation/cancellation messages
        # or single-word protocol selections (aave, compound, morpho, etc.)
        skip_keywords = [
            "yes",
            "no",
            "confirm",
            "cancel",
            "ok",
            "okay",
            "sí",
            "si",
            "não",
            "não",
            "cancelar",
            "confirmar",
            # Protocol names (for selection, not redirect)
            "aave",
            "compound",
            "morpho",
        ]
        # Skip if message is a skip keyword OR is very short (likely a selection response)
        # Single words under 10 chars without "to" or action verbs are likely selections
        is_short_selection = (
            len(message_lower) < 10
            and " " not in message_lower
            and not any(
                word in message_lower
                for word in ["to", "swap", "send", "buy", "deposit", "lend"]
            )
        )
        if (
            message_lower in skip_keywords
            or len(message_lower) < 3
            or is_short_selection
        ):
            return False, None

        # Check if message matches a DIFFERENT workflow
        # Normalize workflow names by removing underscores for comparison
        current_workflow = self.workflow_name.lower().replace("_", "")

        for workflow_type, keywords in workflow_keywords.items():
            # Skip if it's the current workflow
            # Normalize both for comparison (remove underscores)
            workflow_type_normalized = workflow_type.replace("_", "")
            if (
                workflow_type_normalized in current_workflow
                or current_workflow in workflow_type_normalized
            ):
                continue

            for keyword in keywords:
                if (
                    message_lower.startswith(keyword)
                    or f" {keyword}" in f" {message_lower}"
                ):
                    logger.info(
                        f"[{self.workflow_name}] Detected different workflow intent: "
                        f"{workflow_type} (keyword: {keyword})"
                    )
                    return True, workflow_type

        return False, None

    def _get_workflow_redirect_message(
        self,
        detected_workflow: str,
        language: str = "en",
    ) -> str:
        """Get message when redirecting to a different workflow."""
        workflow_names = {
            "swap_workflow": {"en": "swap", "es": "intercambio", "pt": "troca"},
            "lending_workflow": {
                "en": "deposit/lending",
                "es": "depósito",
                "pt": "depósito",
            },
            "buy_workflow": {
                "en": "buy crypto",
                "es": "comprar cripto",
                "pt": "comprar cripto",
            },
            "transfer_workflow": {
                "en": "transfer",
                "es": "transferencia",
                "pt": "transferência",
            },
            "money_market_workflow": {
                "en": "rate comparison",
                "es": "comparación de tasas",
                "pt": "comparação de taxas",
            },
        }

        workflow_display = workflow_names.get(detected_workflow, {}).get(
            language, detected_workflow
        )

        msgs = {
            "en": f"🔄 Switching to **{workflow_display}** operation...",
            "es": f"🔄 Cambiando a operación de **{workflow_display}**...",
            "pt": f"🔄 Mudando para operação de **{workflow_display}**...",
        }
        return msgs.get(language, msgs["en"])

    async def execute(
        self,
        conversation_id: "ConversationId",
        message: MessageContent,
        conversation_context: "ConversationContext",
    ) -> AgentResponse:
        """
        Execute workflow agent.

        This method:
        1. Checks if message is for a different workflow (and signals redirect)
        2. Loads or initializes workflow state
        3. Extracts user context (wallet, language)
        4. Delegates to process_step()
        5. Returns AgentResponse with state and execute_data

        Args:
            conversation_id: Conversation identifier
            message: User message
            conversation_context: Conversation history and metadata
        """
        # Get user context first (needed for language)
        user_context = self._extract_user_context(conversation_context)

        # Check if message is intended for a DIFFERENT workflow
        # This handles cases like user saying "deposit to morpho" while in swap flow
        is_different, detected_workflow = self._detect_different_workflow_intent(
            message.value
        )

        if is_different and detected_workflow:
            # Signal to supervisor that this workflow should be cancelled
            # and the request should be re-routed to the correct workflow
            logger.info(
                f"[{self.workflow_name}] Redirecting to {detected_workflow} - user intent changed"
            )

            # Create cancelled state with redirect signal
            # The content is empty - supervisor will replace with redirect workflow response
            cancelled_state = WorkflowState()
            cancelled_state.step = WorkflowStep.CANCELLED.value
            cancelled_state.cancelled = True
            cancelled_state.data["redirect_to"] = detected_workflow

            return AgentResponse(
                content="",  # Empty - will be replaced by redirect workflow
                agent_type=self.agent_type,
                sources=[],
                tools_used=["workflow_redirect"],
                metadata={
                    "workflow_name": self.workflow_name,
                    "workflow_state": cancelled_state.to_dict(),
                    "current_step": WorkflowStep.CANCELLED.value,
                    "redirect_to": detected_workflow,
                    "workflow_cancelled": True,
                },
            )

        # Load state from conversation context or initialize
        state = self._load_state(conversation_context) or WorkflowState()

        logger.info(
            f"[{self.workflow_name}] Processing step={state.step}, "
            f"user={user_context.user_id}, wallet={user_context.wallet_address[:8] if user_context.wallet_address else 'None'}..."
        )

        try:
            # Process current step
            response_content, new_state = await self.process_step(
                message=message,
                state=state,
                user_context=user_context,
            )

            # Build response metadata
            metadata = {
                "workflow_name": self.workflow_name,
                "workflow_state": new_state.to_dict(),
                "current_step": new_state.step,
            }

            # Add execute_data to metadata if available
            if new_state.execute_data:
                metadata["execute_data"] = new_state.execute_data
            # Pass through enrichment (e.g. sentiment_analysis from money market)
            if new_state.data.get("sentiment_analysis") is not None:
                metadata["sentiment_analysis"] = new_state.data["sentiment_analysis"]

            logger.info(
                f"[{self.workflow_name}] Completed step={new_state.step}, "
                f"has_execute_data={new_state.execute_data is not None}"
            )

            # Build sources based on data fetched in the workflow
            from datetime import datetime, UTC
            from app.infrastructure.adapters.agent_squad.agents.source_helpers import (
                create_api_source,
            )

            sources = []
            fetched_at = datetime.now(UTC)

            # Add sources based on workflow type and data sources used
            workflow_lower = self.workflow_name.lower()

            if "swap" in workflow_lower:
                sources.append(
                    create_api_source(
                        source_name="Hyperliquid/LiFi",
                        citation_text="Swap quote from Hyperliquid Spot or LiFi aggregator",
                        fetched_at=fetched_at,
                        metadata={
                            "workflow": self.workflow_name,
                            "data_type": "swap_quote",
                        },
                    )
                )
            elif "lending" in workflow_lower:
                sources.append(
                    create_api_source(
                        source_name="Morpho Protocol",
                        citation_text="Lending rates from Morpho vaults",
                        fetched_at=fetched_at,
                        metadata={
                            "workflow": self.workflow_name,
                            "data_type": "lending_rates",
                        },
                    )
                )
            elif "money_market" in workflow_lower or "moneymarket" in workflow_lower:
                sources.append(
                    create_api_source(
                        source_name="DeFi Protocols",
                        citation_text="Rates from Morpho, Aave, and Compound protocols",
                        fetched_at=fetched_at,
                        metadata={
                            "workflow": self.workflow_name,
                            "data_type": "money_market_rates",
                        },
                    )
                )
            elif "buy" in workflow_lower:
                sources.append(
                    create_api_source(
                        source_name="MoonPay/Coinbase",
                        citation_text="On-ramp quote from payment providers",
                        fetched_at=fetched_at,
                        metadata={
                            "workflow": self.workflow_name,
                            "data_type": "buy_quote",
                        },
                    )
                )
            elif "transfer" in workflow_lower:
                sources.append(
                    create_api_source(
                        source_name="Anvil",
                        citation_text="Transfer execution via Anvil",
                        fetched_at=fetched_at,
                        metadata={
                            "workflow": self.workflow_name,
                            "data_type": "transfer",
                        },
                    )
                )

            return AgentResponse(
                content=response_content,
                agent_type=self.agent_type,
                tools_used=[self.workflow_name],
                metadata=metadata,
                sources=sources,
            )

        except Exception as e:
            logger.error(
                f"[{self.workflow_name}] Error processing step: {e}", exc_info=True
            )

            # Update state with error (internal use only)
            state.error = str(e)

            # User-friendly error message (don't expose technical details)
            user_friendly_content = f"""⚠️ **Something went wrong**

We encountered an issue processing your request. Please try again.

**What you can try:**
• Rephrase your request
• Try a different amount or token
• Try again in a moment

💡 If the issue persists, contact support."""

            return AgentResponse(
                content=user_friendly_content,
                agent_type=self.agent_type,
                tools_used=[self.workflow_name],
                metadata={
                    "workflow_name": self.workflow_name,
                    "workflow_state": state.to_dict(),
                    "error": str(e),  # Keep for internal debugging
                },
                sources=[],
            )

    def _load_state(
        self, conversation_context: "ConversationContext"
    ) -> WorkflowState | None:
        """
        Load workflow state from conversation context.

        Checks for existing workflow state in:
        1. conversation_context.metadata.workflow_state
        2. Most recent assistant message metadata
        """
        # Check context metadata
        if hasattr(conversation_context, "metadata") and conversation_context.metadata:
            state_dict = conversation_context.metadata.get("workflow_state")
            if state_dict:
                logger.debug(
                    f"[{self.workflow_name}] Loaded state from context metadata"
                )
                return WorkflowState.from_dict(state_dict)

        # Check most recent messages for workflow state
        if (
            hasattr(conversation_context, "conversation_history")
            and conversation_context.conversation_history
        ):
            for msg in reversed(conversation_context.conversation_history[-5:]):
                if isinstance(msg, dict):
                    msg_metadata = msg.get("metadata", {})
                    if (
                        msg_metadata
                        and msg_metadata.get("workflow_name") == self.workflow_name
                    ):
                        state_dict = msg_metadata.get("workflow_state")
                        if state_dict:
                            logger.debug(
                                f"[{self.workflow_name}] Loaded state from message history"
                            )
                            return WorkflowState.from_dict(state_dict)

        logger.debug(f"[{self.workflow_name}] No existing state found, starting fresh")
        return None

    def _extract_user_context(
        self, conversation_context: "ConversationContext"
    ) -> UserContext:
        """
        Extract user context from conversation context.

        Gets user ID, wallet address, language, preferences, and portfolio state.
        Portfolio state is used for context-aware recommendations in workflow agents.
        """
        user_context = UserContext()

        # Extract from user_data if available
        if (
            hasattr(conversation_context, "user_data")
            and conversation_context.user_data
        ):
            user_data = conversation_context.user_data
            user_context.user_id = user_data.get("user_id")
            user_context.wallet_address = user_data.get("wallet_address")
            user_context.language = user_data.get("language", "en")
            user_context.is_authenticated = user_data.get("is_authenticated", False)
            user_context.preferences = user_data.get("preferences", {})

        # Try user_metadata (injected by supervisor with context_aware data)
        if (
            hasattr(conversation_context, "user_metadata")
            and conversation_context.user_metadata
        ):
            metadata = conversation_context.user_metadata
            if not user_context.user_id:
                user_context.user_id = metadata.get("user_id")
            if not user_context.wallet_address:
                user_context.wallet_address = metadata.get("wallet_address")
            if metadata.get("language"):
                user_context.language = metadata.get("language", "en")
            if metadata.get("is_authenticated"):
                user_context.is_authenticated = metadata.get("is_authenticated", False)
            if metadata.get("display_name"):
                user_context.display_name = (
                    str(metadata.get("display_name")).strip() or None
                )

            # Extract portfolio/balance context for workflow agents
            # The supervisor injects balance data in multiple formats:
            # 1. portfolio_summary.total_value_usd (for non-workflow agents)
            # 2. total_balance_usd (direct from context_aware)

            # Try portfolio_summary first (used by some agents)
            if metadata.get("portfolio_summary"):
                portfolio = metadata.get("portfolio_summary", {})
                user_context.total_balance_usd = float(
                    portfolio.get("total_value_usd", 0) or 0
                )
                user_context.has_connected_wallet = bool(user_context.wallet_address)

            # Also try direct total_balance_usd (set by authenticated supervisor)
            # This takes precedence if available
            if metadata.get("total_balance_usd") is not None:
                user_context.total_balance_usd = float(
                    metadata.get("total_balance_usd", 0) or 0
                )
                user_context.has_connected_wallet = metadata.get(
                    "has_connected_wallet", bool(user_context.wallet_address)
                )

            # Portfolio state from context_aware classification
            if metadata.get("portfolio_state"):
                user_context.portfolio_state = metadata.get(
                    "portfolio_state", "unknown"
                )

        # Try metadata as fallback
        if hasattr(conversation_context, "metadata") and conversation_context.metadata:
            metadata = conversation_context.metadata
            if not user_context.user_id:
                user_context.user_id = metadata.get("user_id")
            if not user_context.wallet_address:
                user_context.wallet_address = metadata.get("wallet_address")
            if metadata.get("language"):
                user_context.language = metadata.get("language", "en")

        return user_context

    async def _extract_params_with_llm(
        self,
        message: str,
        param_schema: dict[str, str],
        examples: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """
        Use LLM to extract parameters from user message.

        Args:
            message: User message
            param_schema: Schema of parameters to extract, e.g.:
                {"from_token": "string", "to_token": "string", "amount": "number"}
            examples: Optional few-shot examples

        Returns:
            Dictionary of extracted parameters
        """
        if not self._llm:
            logger.warning(
                f"[{self.workflow_name}] No LLM client, using basic extraction"
            )
            return {}

        # Build prompt for parameter extraction
        schema_str = "\n".join([f"- {k}: {v}" for k, v in param_schema.items()])

        examples_str = ""
        if examples:
            examples_str = "\n\nExamples:\n"
            for ex in examples:
                examples_str += f'Input: "{ex["input"]}"\nOutput: {ex["output"]}\n\n'

        prompt = f"""Extract parameters from the user message. Return JSON only.

Parameters to extract:
{schema_str}
{examples_str}
User message: "{message}"

Return JSON with extracted parameters. Use null for missing values.
"""

        try:
            # Build messages in correct format for AgentLLMGateway
            messages = [{"role": "user", "content": prompt}]
            response = await self._llm.generate(
                model="gemini-2.0-flash-001",  # Default to fast Gemini model
                messages=messages,
                max_tokens=200,
                temperature=0.1,  # Low temperature for parameter extraction
            )
            # Parse JSON from response
            import json
            import re

            # Extract JSON from response
            json_match = re.search(r"\{[^{}]*\}", response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            logger.warning(f"[{self.workflow_name}] LLM extraction failed: {e}")

        return {}

    def _parse_user_intent(self, message: str) -> str:
        """
        Parse user intent from message (confirm, cancel, modify).

        Returns: "confirm", "cancel", "modify", or "unclear"
        """
        message_lower = message.lower().strip()

        # Confirmation keywords (multilingual)
        confirm_keywords = [
            "yes",
            "confirm",
            "ok",
            "proceed",
            "do it",
            "execute",
            "go",
            "sí",
            "si",
            "confirmar",
            "dale",
            "hazlo",
            "sim",
            "confirmar",
            "fazer",
            "是",
            "确认",
            "好",
            "执行",
            "oui",
            "confirmer",
        ]

        # Cancellation keywords
        cancel_keywords = [
            "no",
            "cancel",
            "stop",
            "abort",
            "nevermind",
            "forget it",
            "cancelar",
            "parar",
            "olvidar",
            "cancelar",
            "parar",
            "取消",
            "不要",
            "annuler",
            "non",
        ]

        # Check for confirm
        if any(kw in message_lower for kw in confirm_keywords):
            return "confirm"

        # Check for cancel
        if any(kw in message_lower for kw in cancel_keywords):
            return "cancel"

        # Check for modification (contains numbers or token symbols)
        import re

        if re.search(r"\d+\.?\d*", message) or any(
            t in message.upper() for t in ["ETH", "USDC", "BTC", "USDT", "DAI"]
        ):
            return "modify"

        return "unclear"

    def _build_execute_data(
        self,
        action_type: str,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Build execute_data dictionary matching ExecuteActionData schema.

        This is the data that will be passed to the /execute endpoint.

        Args:
            action_type: Type of action (swap, deposit, withdraw, transfer, approve, bridge)
            **kwargs: Action-specific parameters

        Returns:
            Dictionary matching ExecuteActionData schema
        """
        execute_data = {
            "action_type": action_type,
            "chain": kwargs.get("chain", "base"),
        }

        # Add optional fields if provided
        optional_fields = [
            "provider",
            "from_token",
            "to_token",
            "amount",
            "protocol",
            "vault_address",
            "asset_address",
            "asset_symbol",
            "pool_address",
            "referral_code",  # Aave fields
            "recipient",
            "slippage",
            "to_chain",
            # Additional Morpho/Aave fields
            "vault_name",
            "vault_apy",
            "vault_tvl",
            "supply_apy",
            "available_liquidity_usd",
            # Swap quote fields
            "quote_amount",
            "price_impact",
            "gas_estimate",
            "exchange_rate",
            "network_fee_usd",
            "min_amount_out",
            # Token address fields
            "from_token_address",
            "to_token_address",
            # Price data
            "from_token_price_usd",
            "to_token_price_usd",
            "from_token_24h_change",
            "value_usd",
            # Transaction data for withdraw/direct execution
            "tx_to",
            "tx_data",
            "tx_value",
        ]

        for field in optional_fields:
            if field in kwargs and kwargs[field] is not None:
                execute_data[field] = kwargs[field]

        # Ensure amount is in decimal format (not scientific notation like 1e-05)
        if "amount" in execute_data and execute_data["amount"]:
            try:
                amount_float = float(execute_data["amount"])
                # Format with enough precision, strip trailing zeros
                execute_data["amount"] = f"{amount_float:.10f}".rstrip("0").rstrip(".")
            except (ValueError, TypeError):
                pass  # Keep original value if conversion fails

        return execute_data
