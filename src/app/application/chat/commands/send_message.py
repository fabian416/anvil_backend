"""
Send message command with Hunter AI tool integration.
"""

from uuid import UUID
from typing import Optional
import asyncio
import re

from app.domain.entities.message import Message
from app.domain.entities.conversation import Conversation
from app.domain.ports.conversation_repository import ConversationRepository
from app.domain.ports.ai.agent_gateway import AgentGateway
from app.application.chat.services.hunter_tool_executor import HunterToolExecutor
from app.domain.value_objects.agent_tools.hunter_tools import (
    HunterToolType,
    get_hunter_tool_by_name,
)


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
        hunter_executor: Optional[HunterToolExecutor] = None,
    ):
        """
        Initialize interactor.
        
        Args:
            repository: Conversation repository
            agent_gateway: Agent gateway for processing messages
            hunter_executor: Hunter AI tool executor (optional)
        """
        self._repository = repository
        self._agent_gateway = agent_gateway
        self._hunter_executor = hunter_executor or HunterToolExecutor()
    
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
            ValueError: If conversation not found or not owned by user
        """
        # Get conversation
        conversation = await self._repository.get_conversation(conversation_id)
        
        if conversation is None:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        if conversation.user_id != user_id:
            raise ValueError("Conversation does not belong to user")
        
        # Create and save user message
        user_message = Message.create_user_message(
            conversation_id=conversation_id,
            content=content,
        )
        await self._repository.add_message(user_message)
        
        # Process with agent gateway
        agent_response = await self._agent_gateway.process_message(
            user_id=user_id,
            session_id=str(conversation_id),
            message=content,
        )
        
        # Detect and execute Hunter AI tools if applicable
        hunter_results = await self._execute_hunter_tools(content)
        
        # Combine agent response with Hunter AI tool results
        if hunter_results:
            final_response = agent_response + "\n\n" + hunter_results
        else:
            final_response = agent_response
        
        # Create and save agent message
        agent_message = Message.create_agent_message(
            conversation_id=conversation_id,
            content=final_response,
        )
        await self._repository.add_message(agent_message)
        
        # Update conversation timestamp
        conversation.touch()
        await self._repository.add_conversation(conversation)  # Update
        
        # Broadcast agent message via WebSocket (fire and forget)
        asyncio.create_task(self._broadcast_message(conversation_id, agent_message))
        
        return user_message, agent_message
    
    async def _execute_hunter_tools(self, message: str) -> str:
        """
        Detect and execute Hunter AI tools based on message content.
        
        Args:
            message: User message content
        
        Returns:
            Formatted tool results (or empty string if no tools detected)
        """
        message_lower = message.lower()
        results = []
        
        # Extract token symbol (look for common crypto tickers)
        token_match = re.search(
            r'\b(BTC|ETH|UNI|AAVE|LINK|MATIC|SOL|AVAX|ARB|OP|USDC|USDT|DAI|WBTC|WETH)\b',
            message.upper()
        )
        token = token_match.group(1) if token_match else None
        
        if not token:
            return ""  # No token detected, skip Hunter AI
        
        try:
            # Sentiment analysis keywords
            if any(keyword in message_lower for keyword in [
                "sentiment", "social", "buzz", "feeling", "mood", "twitter",
                "reddit", "discord", "news", "community"
            ]):
                result = await self._hunter_executor.execute_tool(
                    tool_type=HunterToolType.SENTIMENT_ANALYSIS,
                    parameters={"token_symbol": token}
                )
                results.append(result)
            
            # Price prediction keywords
            if any(keyword in message_lower for keyword in [
                "predict", "forecast", "future", "price target", "will", "going to",
                "expect", "prediction", "tomorrow", "next week"
            ]):
                result = await self._hunter_executor.execute_tool(
                    tool_type=HunterToolType.PRICE_PREDICTION,
                    parameters={"token_symbol": token, "horizon_hours": 24}
                )
                results.append(result)
            
            # Risk analysis keywords
            if any(keyword in message_lower for keyword in [
                "risk", "safe", "risky", "volatile", "danger", "secure",
                "volatility", "liquidity", "audit", "contract risk"
            ]):
                result = await self._hunter_executor.execute_tool(
                    tool_type=HunterToolType.RISK_ANALYSIS,
                    parameters={"token_symbol": token}
                )
                results.append(result)
            
            # Trading signal keywords
            if any(keyword in message_lower for keyword in [
                "buy", "sell", "trade", "signal", "entry", "exit",
                "should i", "good time", "when to", "recommend"
            ]):
                result = await self._hunter_executor.execute_tool(
                    tool_type=HunterToolType.TRADING_SIGNALS,
                    parameters={"token_symbol": token, "timeframe": "1d"}
                )
                results.append(result)
            
            # Pattern recognition keywords
            if any(keyword in message_lower for keyword in [
                "pattern", "chart", "technical", "support", "resistance",
                "triangle", "head and shoulders", "flag", "doji", "candlestick"
            ]):
                result = await self._hunter_executor.execute_tool(
                    tool_type=HunterToolType.PATTERN_RECOGNITION,
                    parameters={"token_symbol": token, "min_confidence": 0.6}
                )
                results.append(result)
            
            # Comprehensive analysis keywords (execute all tools)
            if any(keyword in message_lower for keyword in [
                "analyze", "analysis", "complete", "full", "everything",
                "comprehensive", "report", "breakdown"
            ]):
                # Execute all tools for comprehensive analysis
                all_results = await asyncio.gather(
                    self._hunter_executor.execute_tool(
                        HunterToolType.SENTIMENT_ANALYSIS,
                        {"token_symbol": token}
                    ),
                    self._hunter_executor.execute_tool(
                        HunterToolType.PRICE_PREDICTION,
                        {"token_symbol": token, "horizon_hours": 24}
                    ),
                    self._hunter_executor.execute_tool(
                        HunterToolType.RISK_ANALYSIS,
                        {"token_symbol": token}
                    ),
                    self._hunter_executor.execute_tool(
                        HunterToolType.TRADING_SIGNALS,
                        {"token_symbol": token, "timeframe": "1d"}
                    ),
                    return_exceptions=True
                )
                results.extend([r for r in all_results if isinstance(r, str)])
        
        except Exception as e:
            # Log error but don't fail the message
            import logging
            logging.error(f"Hunter AI tool execution error: {e}")
            return ""
        
        # Join all results with separators
        if results:
            return "\n\n---\n\n".join(results)
        return ""
    
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
                    }
                }
            )
        except Exception as e:
            # Don't fail the request if WebSocket broadcast fails
            import logging
            logging.error(f"Failed to broadcast message via WebSocket: {e}")
