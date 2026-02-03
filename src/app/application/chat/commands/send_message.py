"""
Send message command with Hunter AI tool integration.
"""

from uuid import UUID, uuid4
from typing import Optional, Dict, Any
import asyncio
import re

from app.domain.chat.entities.message import Message
from app.domain.value_objects.message_role import MessageRole
from app.domain.chat.entities.conversation import Conversation
from app.domain.projects.entities.project import Project
from app.domain.chat.ports.conversation_repository import ConversationRepository
from app.domain.projects.ports.project_repository import ProjectRepository
from app.domain.exceptions.chat import (
    ConversationNotFoundError,
    ConversationAccessDeniedError,
)
from app.domain.ports.ai.agent_gateway import AgentGateway
from app.application.chat.services.hunter_tool_executor import HunterToolExecutor
from app.application.chat.services.ultra_tool_executor import ULTRAToolExecutor
from app.application.projects.services.project_tool_executor import (
    ProjectToolExecutor,
    ToolExecutionError,
)
from app.domain.value_objects.agent_tools.hunter_tools import (
    HunterToolType,
    get_hunter_tool_by_name,
)
from app.domain.value_objects.agent_tools.ultra_tools import (
    ULTRAToolType,
    get_ultra_tool_by_name,
)
from app.setup.config.integrations import IntegrationSettings
from app.application.common.ports.transaction_manager import TransactionManager


class SendMessage:
    """
    Send a message in a conversation and get agent response.

    This orchestrates:
    1. Save user message
    2. Process with agent gateway
    3. Detect and execute Hunter AI tools (if requested)
    4. Save agent response (with tool results)
    5. Update conversation timestamp

    Hunter AI Integration:
    - Detects when user asks about sentiment, price, risk, etc.
    - Automatically executes appropriate Hunter AI tools
    - Formats results for natural chat display
    """

    def __init__(
        self,
        repository: ConversationRepository,
        agent_gateway: AgentGateway,
        transaction_manager: TransactionManager,
        project_repository: Optional[ProjectRepository] = None,
        hunter_executor: Optional[HunterToolExecutor] = None,
        ultra_executor: Optional[ULTRAToolExecutor] = None,
        integration_settings: Optional[IntegrationSettings] = None,
    ):
        """
        Initialize interactor.

        Args:
            repository: Conversation repository
            agent_gateway: Agent gateway for processing messages
            transaction_manager: Transaction manager for committing changes
            project_repository: Project repository (for project-scoped conversations)
            hunter_executor: Hunter AI tool executor (optional)
            ultra_executor: ULTRA Arbitrage tool executor (optional)
            integration_settings: Integration feature flags (optional)
        """
        self._repository = repository
        self._tx = transaction_manager
        self._agent_gateway = agent_gateway
        self._project_repository = project_repository
        self._hunter_executor = hunter_executor or HunterToolExecutor()
        self._ultra_executor = ultra_executor or ULTRAToolExecutor()
        self._integration_settings = integration_settings or IntegrationSettings()

    async def execute(
        self,
        user_id: int,
        conversation_id: UUID,
        content: str,
    ) -> tuple[Message, Message]:
        """
        Execute the command.

        Args:
            user_id: User identifier (for verification)
            conversation_id: Conversation identifier
            content: Message content

        Returns:
            Tuple of (user_message, agent_message)

        Raises:
            ConversationNotFoundError: If conversation not found
            ConversationAccessDeniedError: If conversation not owned by user
        """
        # Get conversation
        conversation = await self._repository.get_conversation(conversation_id)

        if conversation is None:
            raise ConversationNotFoundError(conversation_id)

        if conversation.user_id != user_id:
            raise ConversationAccessDeniedError(conversation_id, user_id)

        # Create user message with explicit timestamp for guaranteed ordering
        from datetime import timedelta
        from app.domain.common.datetime_utils import utc_now

        user_timestamp = utc_now()
        user_message = Message(
            id=uuid4(),
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content=content,
            created_at=user_timestamp,
        )
        await self._repository.add_message(user_message)

        # Get project if conversation is project-scoped
        project = None
        if conversation.is_project_scoped and self._project_repository:
            project = await self._project_repository.get(conversation.project_id)

        # Process with agent gateway (use project system prompt if available)
        context = {}
        if project:
            context["system_prompt"] = project.system_prompt

        agent_response = await self._agent_gateway.process_message(
            user_id=user_id,
            session_id=str(conversation_id),
            message=content,
            context=context,
        )

        # Detect and execute tools (project-scoped if applicable)
        tool_results = ""
        if self._integration_settings.chat.enabled:
            tool_results = await self._execute_tools(content, project)

        # Combine agent response with tool results
        if tool_results:
            final_response = agent_response + "\n\n" + tool_results
        else:
            final_response = agent_response

        # Create agent message with timestamp after user message
        # Use current time (which is after agent processing) to ensure proper order
        agent_message = Message(
            id=uuid4(),
            conversation_id=conversation_id,
            role=MessageRole.AGENT,
            content=final_response,
            created_at=utc_now(),  # Will be after user_timestamp due to agent processing time
        )
        await self._repository.add_message(agent_message)

        # Update conversation timestamp
        conversation.touch()
        await self._repository.update_conversation(conversation)

        # Commit transaction to persist all changes
        await self._tx.commit()

        # Broadcast agent message via WebSocket (fire and forget)
        asyncio.create_task(self._broadcast_message(conversation_id, agent_message))

        return user_message, agent_message

    async def _execute_tools(
        self,
        message: str,
        project: Optional[Project] = None,
    ) -> str:
        """
        Detect and execute tools based on message content.

        If project is provided, uses project-scoped tool executor with
        risk limit enforcement. Otherwise, uses general Hunter AI executor.

        Args:
            message: User message content
            project: Optional project for scoped execution

        Returns:
            Formatted tool results (or empty string if no tools detected)
        """
        message_lower = message.lower()
        results = []

        # Extract token symbol (look for common crypto tickers)
        token_match = re.search(
            r"\b(BTC|ETH|UNI|AAVE|LINK|MATIC|SOL|AVAX|ARB|OP|USDC|USDT|DAI|WBTC|WETH)\b",
            message.upper(),
        )
        token = token_match.group(1) if token_match else None

        if not token:
            return ""  # No token detected, skip Hunter AI

        # Create appropriate tool executor
        if project:
            tool_executor = ProjectToolExecutor(
                project, self._hunter_executor, self._ultra_executor
            )
        else:
            tool_executor = None  # Use direct executors

        try:
            # Hunter AI tools (check if enabled)
            if self._integration_settings.chat.hunter_tools_enabled:
                # Sentiment analysis keywords
                if any(
                    keyword in message_lower
                    for keyword in [
                        "sentiment",
                        "social",
                        "buzz",
                        "feeling",
                        "mood",
                        "twitter",
                        "reddit",
                        "discord",
                        "news",
                        "community",
                    ]
                ):
                    result = await self._execute_single_tool(
                        tool_executor,
                        "hunter_sentiment_analysis",
                        HunterToolType.SENTIMENT_ANALYSIS,
                        {"token_symbol": token},
                    )
                    if result:
                        results.append(result)

                # Price prediction keywords
                if any(
                    keyword in message_lower
                    for keyword in [
                        "predict",
                        "forecast",
                        "future",
                        "price target",
                        "will",
                        "going to",
                        "expect",
                        "prediction",
                        "tomorrow",
                        "next week",
                    ]
                ):
                    result = await self._execute_single_tool(
                        tool_executor,
                        "hunter_price_prediction",
                        HunterToolType.PRICE_PREDICTION,
                        {"token_symbol": token, "horizon_hours": 24},
                    )
                    if result:
                        results.append(result)

                # Risk analysis keywords
                if any(
                    keyword in message_lower
                    for keyword in [
                        "risk",
                        "safe",
                        "risky",
                        "volatile",
                        "danger",
                        "secure",
                        "volatility",
                        "liquidity",
                        "audit",
                        "contract risk",
                    ]
                ):
                    result = await self._execute_single_tool(
                        tool_executor,
                        "hunter_risk_analysis",
                        HunterToolType.RISK_ANALYSIS,
                        {"token_symbol": token},
                    )
                    if result:
                        results.append(result)

                # Trading signal keywords
                if any(
                    keyword in message_lower
                    for keyword in [
                        "buy",
                        "sell",
                        "trade",
                        "signal",
                        "entry",
                        "exit",
                        "should i",
                        "good time",
                        "when to",
                        "recommend",
                    ]
                ):
                    result = await self._execute_single_tool(
                        tool_executor,
                        "hunter_trading_signals",
                        HunterToolType.TRADING_SIGNALS,
                        {"token_symbol": token, "timeframe": "1d"},
                    )
                    if result:
                        results.append(result)

                # Pattern recognition keywords
                if any(
                    keyword in message_lower
                    for keyword in [
                        "pattern",
                        "chart",
                        "technical",
                        "support",
                        "resistance",
                        "triangle",
                        "head and shoulders",
                        "flag",
                        "doji",
                        "candlestick",
                    ]
                ):
                    result = await self._execute_single_tool(
                        tool_executor,
                        "hunter_pattern_recognition",
                        HunterToolType.PATTERN_RECOGNITION,
                        {"token_symbol": token, "min_confidence": 0.6},
                    )
                    if result:
                        results.append(result)

            # ULTRA tools (check if enabled)
            if self._integration_settings.chat.ultra_tools_enabled:
                # Flash loan keywords
                if any(
                    keyword in message_lower
                    for keyword in [
                        "flash loan",
                        "borrow",
                        "aave",
                        "balancer",
                        "liquidity",
                    ]
                ):
                    result = await self._execute_single_tool(
                        tool_executor,
                        "ultra_flash_loans",
                        ULTRAToolType.FLASH_LOANS,
                        {"token_symbol": token, "amount": 100},  # Default 100 tokens
                    )
                    if result:
                        results.append(result)

                # Arbitrage discovery keywords
                if any(
                    keyword in message_lower
                    for keyword in [
                        "arbitrage",
                        "opportunity",
                        "profit",
                        "dex",
                        "spread",
                    ]
                ):
                    # Extract capital if mentioned
                    capital_match = re.search(r"\$?([\d,]+)k?", message)
                    capital = 10000  # Default $10K
                    if capital_match:
                        capital_str = capital_match.group(1).replace(",", "")
                        capital = float(capital_str)
                        if "k" in message_lower:
                            capital *= 1000

                    result = await self._execute_single_tool(
                        tool_executor,
                        "ultra_arbitrage_discovery",
                        ULTRAToolType.ARBITRAGE_DISCOVERY,
                        {"token_symbol": token, "capital": capital, "min_profit": 50},
                    )
                    if result:
                        results.append(result)

                # MEV protection keywords
                if any(
                    keyword in message_lower
                    for keyword in [
                        "mev",
                        "front-run",
                        "sandwich",
                        "flashbots",
                        "protect",
                    ]
                ):
                    result = await self._execute_single_tool(
                        tool_executor,
                        "ultra_mev_protection",
                        ULTRAToolType.MEV_PROTECTION,
                        {"protection_level": "high"},
                    )
                    if result:
                        results.append(result)

                # Auto-executor status keywords
                if any(
                    keyword in message_lower
                    for keyword in [
                        "bot status",
                        "auto",
                        "executor",
                        "automated",
                        "running",
                    ]
                ):
                    result = await self._execute_single_tool(
                        tool_executor,
                        "ultra_auto_executor",
                        ULTRAToolType.AUTO_EXECUTOR,
                        {},
                    )
                    if result:
                        results.append(result)

            # Comprehensive analysis keywords (execute all tools)
            if self._integration_settings.chat.comprehensive_analysis_enabled:
                if any(
                    keyword in message_lower
                    for keyword in [
                        "analyze",
                        "analysis",
                        "complete",
                        "full",
                        "everything",
                        "comprehensive",
                        "report",
                        "breakdown",
                    ]
                ):
                    # Execute all tools for comprehensive analysis
                    if tool_executor:
                        # Project-scoped: Execute only enabled tools
                        comp_results = await self._execute_comprehensive_project(
                            tool_executor, token
                        )
                    else:
                        # General chat: Execute all Hunter tools
                        comp_results = await self._execute_comprehensive_general(token)

                    results.extend(comp_results)

        except Exception as e:
            # Log error but don't fail the message
            import logging

            logging.error(f"Hunter AI tool execution error: {e}")
            return ""

        # Join all results with separators
        if results:
            return "\n\n---\n\n".join(results)
        return ""

    async def _execute_single_tool(
        self,
        tool_executor: Optional[ProjectToolExecutor],
        tool_name: str,
        tool_type: HunterToolType | ULTRAToolType,
        parameters: Dict[str, Any],
    ) -> Optional[str]:
        """
        Execute a single tool (project-scoped or general).

        Args:
            tool_executor: Project tool executor (if project-scoped)
            tool_name: Tool name (e.g., "hunter_sentiment_analysis", "ultra_flash_loans")
            tool_type: Tool type enum (Hunter or ULTRA)
            parameters: Tool parameters

        Returns:
            Formatted tool result or None if execution failed
        """
        try:
            if tool_executor:
                # Project-scoped execution with validation
                return await tool_executor.execute_tool(tool_name, parameters)
            else:
                # General execution (no project limits)
                if isinstance(tool_type, HunterToolType):
                    return await self._hunter_executor.execute_tool(
                        tool_type, parameters
                    )
                elif isinstance(tool_type, ULTRAToolType):
                    return await self._ultra_executor.execute_tool(
                        tool_type, parameters
                    )
                else:
                    return None
        except ToolExecutionError as e:
            # Tool not allowed in project
            return f"⚠️ {str(e)}"
        except Exception as e:
            # Other errors - log and skip
            import logging

            logging.error(f"Tool execution error: {e}")
            return None

    async def _execute_comprehensive_project(
        self,
        tool_executor: ProjectToolExecutor,
        token: str,
    ) -> list[str]:
        """
        Execute comprehensive analysis using project-enabled tools only.

        Args:
            tool_executor: Project tool executor
            token: Token symbol

        Returns:
            List of formatted tool results
        """
        project = tool_executor.project
        results = []

        # Build list of tools to execute (only if enabled in project)
        tools_to_execute = []

        if project.can_use_hunter_tool("hunter_sentiment_analysis"):
            tools_to_execute.append((
                "hunter_sentiment_analysis",
                HunterToolType.SENTIMENT_ANALYSIS,
                {"token_symbol": token},
            ))

        if project.can_use_hunter_tool("hunter_price_prediction"):
            tools_to_execute.append((
                "hunter_price_prediction",
                HunterToolType.PRICE_PREDICTION,
                {"token_symbol": token, "horizon_hours": 24},
            ))

        if project.can_use_hunter_tool("hunter_risk_analysis"):
            tools_to_execute.append((
                "hunter_risk_analysis",
                HunterToolType.RISK_ANALYSIS,
                {"token_symbol": token},
            ))

        if project.can_use_hunter_tool("hunter_trading_signals"):
            tools_to_execute.append((
                "hunter_trading_signals",
                HunterToolType.TRADING_SIGNALS,
                {"token_symbol": token, "timeframe": "1d"},
            ))

        # Execute all enabled tools in parallel
        if tools_to_execute:
            all_results = await asyncio.gather(
                *[
                    self._execute_single_tool(tool_executor, name, ttype, params)
                    for name, ttype, params in tools_to_execute
                ],
                return_exceptions=True,
            )
            results.extend([r for r in all_results if isinstance(r, str)])

        return results

    async def _execute_comprehensive_general(self, token: str) -> list[str]:
        """
        Execute comprehensive analysis with all Hunter tools (general chat).

        Args:
            token: Token symbol

        Returns:
            List of formatted tool results
        """
        # Only execute if hunter tools are enabled
        if not self._integration_settings.chat.hunter_tools_enabled:
            return []

        all_results = await asyncio.gather(
            self._hunter_executor.execute_tool(
                HunterToolType.SENTIMENT_ANALYSIS, {"token_symbol": token}
            ),
            self._hunter_executor.execute_tool(
                HunterToolType.PRICE_PREDICTION,
                {"token_symbol": token, "horizon_hours": 24},
            ),
            self._hunter_executor.execute_tool(
                HunterToolType.RISK_ANALYSIS, {"token_symbol": token}
            ),
            self._hunter_executor.execute_tool(
                HunterToolType.TRADING_SIGNALS,
                {"token_symbol": token, "timeframe": "1d"},
            ),
            return_exceptions=True,
        )
        return [r for r in all_results if isinstance(r, str)]

    async def _broadcast_message(self, conversation_id: UUID, message: Message) -> None:
        """
        Broadcast message to WebSocket connections.

        Args:
            conversation_id: Conversation identifier
            message: Message to broadcast
        """
        try:
            from app.presentation.http.websocket.chat_websocket import manager

            await manager.broadcast_to_conversation(
                conversation_id=conversation_id,
                message={
                    "type": "message",
                    "message": {
                        "id": str(message.id),
                        "role": message.role.value,
                        "content": message.content,
                        "agent_type": message.agent_type,
                        "created_at": message.created_at.isoformat(),
                    },
                },
            )
        except Exception as e:
            # Don't fail the request if WebSocket broadcast fails
            import logging

            logging.error(f"Failed to broadcast message via WebSocket: {e}")
