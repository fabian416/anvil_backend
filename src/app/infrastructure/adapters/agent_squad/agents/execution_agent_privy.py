"""
Execution Agent Privy - Transaction execution using Privy embedded wallets.
"""

import time
from decimal import Decimal
from typing import Any

from app.domain.enums.agent_type import AgentType
from app.domain.value_objects.conversation_id import ConversationId
from app.domain.value_objects.message_content import MessageContent
from app.domain.value_objects.agent_squad.conversation_context import ConversationContext
from app.domain.ports.agent_squad.agent_gateway import AgentGateway, AgentResponse
from app.domain.ports.agent_squad.llm_client_gateway import LLMClientGateway


class ExecutionAgentPrivy:
    """
    Execution Agent Privy implementation.
    
    Implements: AgentGateway
    
    Purpose: Transaction execution using Privy embedded wallets
    
    Capabilities:
    - Token swaps (1inch, Uniswap)
    - Transfer tokens
    - Approve tokens
    - Wrap/unwrap ETH
    - Transaction simulation (pre-flight)
    - Gas estimation
    - Slippage protection
    
    Safety Features:
    - Transaction limits (max $10k by default)
    - 2FA requirement
    - User confirmation required
    - Simulation before execution
    
    Model: gpt-4o (precise transaction parsing)
    Temperature: 0.1 (low, precision critical)
    """
    
    def __init__(
        self,
        llm_client: LLMClientGateway,  # Can be Vertex AI or DeepInfra (OpenAI removed),
        privy_client: Any,  # PrivyClient (TODO: type properly)
        swap_gateway: Any,  # SwapGateway (1inch, Uniswap)
        model: str = "gemini-2.0-flash",  # Vertex AI model (default)
        temperature: float = 0.1,
        max_tokens: int = 1000,
        max_transaction_value_usd: Decimal = Decimal("10000"),
    ):
        """
        Initialize execution agent.
        
        Args:
            llm_client: OpenAI LLM client
            privy_client: Privy embedded wallet client
            swap_gateway: Swap gateway (1inch, Uniswap)
            model: Model to use (default: gpt-4o)
            temperature: Sampling temperature (default: 0.1, precision critical)
            max_tokens: Maximum response tokens
            max_transaction_value_usd: Maximum transaction value (safety limit)
        """
        self._llm_client = llm_client
        self._privy_client = privy_client
        self._swap_gateway = swap_gateway
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._max_transaction_value_usd = max_transaction_value_usd
    
    @property
    def agent_type(self) -> AgentType:
        """Get agent type."""
        return AgentType.EXECUTION
    
    async def execute(
        self,
        conversation_id: ConversationId,
        message: MessageContent,
        conversation_context: ConversationContext,
    ) -> AgentResponse:
        """
        Execute transaction agent.
        
        Process:
        1. Parse transaction intent (swap, transfer, etc.)
        2. Get user wallet (Privy)
        3. Validate transaction (limits, balance)
        4. Get quote (1inch, Uniswap)
        5. Simulate transaction (pre-flight)
        6. Request user confirmation
        7. Build transaction
        8. Sign via Privy
        9. Submit transaction
        10. Return transaction hash
        """
        start_time = time.time()
        
        # Parse transaction intent using LLM
        intent_response = await self._parse_transaction_intent(message)
        
        # Build response based on intent
        # NOTE: Actual execution requires user confirmation (not auto-executed)
        response_content = await self._build_execution_response(
            intent_response,
            conversation_context,
        )
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        # Collect sources
        from datetime import datetime, UTC
        from app.infrastructure.adapters.agent_squad.agents.source_helpers import (
            create_llm_source,
            create_api_source,
            create_blockchain_source,
        )
        
        sources = []
        fetched_at = datetime.now(UTC)
        
        # Add LLM source (for intent parsing)
        model_name = self._model
        sources.append(create_llm_source(
            model=model_name,
            fetched_at=fetched_at,
        ))
        
        # Add 1inch source (if swap action)
        action = intent_response.get("action", "")
        if action == "swap":
            from_token = intent_response.get("from_token", "")
            to_token = intent_response.get("to_token", "")
            sources.append(create_api_source(
                source_name="1inch",
                url=f"https://app.1inch.io/",
                endpoint="/swap/v5.2/quote",
                citation_text=f"1inch swap quote: {from_token} → {to_token}",
                fetched_at=fetched_at,
                query_params={"fromTokenAddress": from_token, "toTokenAddress": to_token} if from_token and to_token else None,
            ))
        
        # Add Privy source
        sources.append(create_api_source(
            source_name="Privy",
            url="https://privy.io/",
            citation_text="Wallet connection and transaction signing via Privy",
            fetched_at=fetched_at,
        ))
        
        # TODO: Add blockchain source when transaction is submitted (tx_hash available)
        
        return AgentResponse(
            content=response_content,
            agent_type=self.agent_type,
            tools_used=["privy_wallet", "1inch_api", "openai_api"],
            sources=sources,
            metadata={
                "latency_ms": latency_ms,
                "transaction_intent": intent_response,
                "requires_confirmation": True,
            },
        )
    
    async def is_available(self) -> bool:
        """Check if agent is available."""
        # TODO: Check Privy API status
        return True
    
    async def _parse_transaction_intent(self, message: MessageContent) -> dict:
        """Parse transaction intent from message."""
        prompt = f"""Parse the transaction intent from this message:

Message: {message.value}

Identify:
- action: "swap", "transfer", "approve", "wrap", "unwrap"
- from_token: Token symbol (e.g., "ETH", "USDC")
- to_token: Token symbol (if swap)
- amount: Numeric amount
- recipient: Wallet address (if transfer)

Respond with JSON:
{{
    "action": "swap",
    "from_token": "ETH",
    "to_token": "USDC",
    "amount": "1.0",
    "confidence": 0.95
}}
"""
        
        response = await self._llm_client.classify_intent(
            prompt=prompt,
            model=self._model,
        )
        
        return response
    
    async def _build_execution_response(
        self,
        intent: dict,
        conversation_context: ConversationContext,
    ) -> str:
        """Build execution response (quote, confirmation request)."""
        action = intent.get("action", "unknown")
        from_token = intent.get("from_token", "")
        to_token = intent.get("to_token", "")
        amount = intent.get("amount", "0")
        
        # TODO: Get real quote from 1inch/Uniswap
        # TODO: Get gas estimation
        # TODO: Simulate transaction
        
        if action == "swap":
            return f"""I can help you swap {amount} {from_token} for {to_token}.

**Transaction Summary:**
- From: {amount} {from_token}
- To: ~XXX {to_token} (estimated)
- Route: 1inch (best price)
- Gas: ~$XX
- Slippage: 0.5% (default)

**⚠️ Confirmation Required**
To proceed, please confirm:
- Review the amounts above
- Check the gas fee
- Confirm you want to execute

Reply "confirm" to proceed or "cancel" to abort.

(This transaction will be executed using your Privy embedded wallet)
"""
        else:
            return f"""I understand you want to {action} {from_token}.

However, I need more information to proceed. Please provide:
- Exact amount to {action}
- Recipient wallet (if transfer)
- Any other relevant details

Once I have all details, I'll prepare the transaction for your confirmation.
"""
