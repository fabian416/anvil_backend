"""
Chat Agent OpenAI - General conversation agent.
"""

import time
from typing import Any

from app.domain.enums.agent_type import AgentType
from app.domain.value_objects.conversation_id import ConversationId
from app.domain.value_objects.message_content import MessageContent
from app.domain.value_objects.agent_squad.conversation_context import ConversationContext
from app.domain.ports.agent_squad.agent_gateway import AgentGateway, AgentResponse
from app.infrastructure.adapters.agent_squad.llm_client_openai import LLMClientOpenAI


class ChatAgentOpenAI:
    """
    Chat Agent OpenAI implementation.
    
    Implements: AgentGateway
    
    Purpose: General conversation, fallback agent
    
    Capabilities:
    - Answer general questions
    - Provide DeFi information
    - Guide users to specialist agents
    - Maintain friendly, helpful tone
    
    Model: gpt-4o-mini (fast, cost-effective)
    Temperature: 0.7 (balanced creativity)
    """
    
    def __init__(
        self,
        llm_client: LLMClientOpenAI,
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ):
        """
        Initialize chat agent.
        
        Args:
            llm_client: OpenAI LLM client
            model: Model to use (default: gpt-4o-mini)
            temperature: Sampling temperature (default: 0.7)
            max_tokens: Maximum response tokens (default: 1000)
        """
        self._llm_client = llm_client
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens
    
    @property
    def agent_type(self) -> AgentType:
        """Get agent type."""
        return AgentType.CHAT
    
    async def execute(
        self,
        conversation_id: ConversationId,
        message: MessageContent,
        conversation_context: ConversationContext,
    ) -> AgentResponse:
        """
        Execute chat agent.
        
        Provides general conversation, guidance to specialist agents.
        """
        start_time = time.time()
        
        # Build messages for OpenAI
        messages = self._build_messages(message, conversation_context)
        
        # Call OpenAI
        response = await self._llm_client.chat(
            messages=messages,
            model=self._model,
            temperature=self._temperature,
            max_tokens=self._max_tokens,
        )
        
        # Calculate latency
        latency_ms = int((time.time() - start_time) * 1000)
        
        # Build response
        return AgentResponse(
            content=response["content"],
            agent_type=self.agent_type,
            tools_used=[],  # Chat agent doesn't use external tools
            metadata={
                "tokens_used": response.get("tokens_used"),
                "latency_ms": latency_ms,
                "model": response.get("model"),
                "finish_reason": response.get("finish_reason"),
            },
        )
    
    async def is_available(self) -> bool:
        """Check if agent is available."""
        # Always available (no external dependencies)
        return True
    
    def _build_messages(
        self,
        message: MessageContent,
        conversation_context: ConversationContext,
    ) -> list[dict]:
        """Build messages for OpenAI API."""
        messages = [
            {
                "role": "system",
                "content": self._get_system_prompt(),
            }
        ]
        
        # Add conversation history (last 5 messages)
        history = conversation_context.last_n_messages(5)
        for msg in history:
            messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", ""),
            })
        
        # Add current message
        messages.append({
            "role": "user",
            "content": message.value,
        })
        
        return messages
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for chat agent."""
        return """You are Anvil's AI assistant, a friendly and helpful guide for DeFi users.

Your capabilities:
- Answer general questions about DeFi, crypto, and Web3
- Provide educational information
- Guide users to specialist agents when needed

When to refer to specialists:
- Token swaps, transactions → "Let me connect you with our Execution agent"
- Risk analysis → "Our Risk Analyzer agent can help with that"
- Portfolio optimization → "Our Portfolio agent specializes in this"
- Market sentiment → "Our Hunter AI agent tracks market sentiment"
- Deep research → "Our Research agent can dive deep into this"

Keep responses:
- Clear and concise
- Friendly and professional
- Educational when helpful
- Honest about limitations

If unsure, say so and offer to connect them with a specialist.
"""
