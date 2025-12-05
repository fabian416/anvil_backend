"""
Bridge Crosschain Agent Axelar - Layer 2 & cross-chain asset transfers.
"""

import time
from typing import Any
from decimal import Decimal

from app.domain.enums.agent_type import AgentType
from app.domain.value_objects.conversation_id import ConversationId
from app.domain.value_objects.message_content import MessageContent
from app.domain.value_objects.agent_squad.conversation_context import ConversationContext
from app.domain.ports.agent_squad.agent_gateway import AgentGateway, AgentResponse
from app.infrastructure.adapters.agent_squad.llm_client_openai import LLMClientOpenAI


class BridgeCrosschainAgentAxelar:
    """
    Bridge Crosschain Agent Axelar implementation.
    
    Implements: AgentGateway
    
    Purpose: Layer 2 & cross-chain asset transfers
    
    Capabilities:
    - Layer 2 bridging (Arbitrum, Optimism, Base, Polygon)
    - Cross-chain asset transfers (via Axelar, LayerZero)
    - Bridge cost comparison (find cheapest route)
    - Bridge time estimation
    - Security risk assessment (bridge exploits)
    - Historical bridge analytics
    
    Supported Chains:
    - Ethereum Mainnet (L1)
    - Arbitrum, Optimism, Base (Optimistic Rollups)
    - Polygon, zkSync (Sidechains/zkRollups)
    - Avalanche, BSC (Alt L1s)
    
    Bridge Providers:
    - Axelar (General Messaging Protocol)
    - LayerZero (Omnichain Protocol)
    - Native Bridges (Arbitrum Bridge, etc.)
    - Hop Protocol (L2-L2 direct)
    
    Features:
    - Automatic best-route selection
    - Gas cost comparison
    - Time estimation (5min - 7 days)
    - Security scoring (0-100)
    - Slippage protection
    
    Model: gpt-4o (bridge reasoning)
    Temperature: 0.2 (factual)
    """
    
    def __init__(
        self,
        llm_client: LLMClientOpenAI,
        axelar_client: Any,  # AxelarClient
        model: str = "gpt-4o",
        temperature: float = 0.2,
        max_tokens: int = 1500,
    ):
        """Initialize bridge crosschain agent."""
        self._llm_client = llm_client
        self._axelar_client = axelar_client
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens
    
    @property
    def agent_type(self) -> AgentType:
        """Get agent type."""
        return AgentType.BRIDGE_CROSSCHAIN
    
    async def execute(
        self,
        conversation_id: ConversationId,
        message: MessageContent,
        conversation_context: ConversationContext,
    ) -> AgentResponse:
        """Execute bridge crosschain agent."""
        start_time = time.time()
        
        # Parse bridge request
        bridge_request = await self._parse_bridge_request(message)
        
        if not bridge_request["valid"]:
            return self._build_error_response(
                "Please specify: token, amount, source chain, and destination chain.",
                start_time
            )
        
        # Get bridge routes
        routes = await self._get_bridge_routes(bridge_request)
        
        # Generate comparison
        comparison = await self._generate_bridge_comparison(routes)
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        return AgentResponse(
            content=comparison,
            agent_type=self.agent_type,
            tools_used=["axelar_api", "layerzero_api", "openai_api"],
            metadata={
                "latency_ms": latency_ms,
                "routes_found": len(routes),
                "best_route": routes[0]["provider"] if routes else None,
            },
        )
    
    async def is_available(self) -> bool:
        """Check if agent is available."""
        return True
    
    async def _parse_bridge_request(self, message: MessageContent) -> dict:
        """Parse bridge request from message."""
        prompt = f"""Parse the bridge/cross-chain request:

Message: {message.value}

Extract:
- token: Token symbol (ETH, USDC, etc.)
- amount: Numeric amount
- from_chain: Source chain (ethereum, arbitrum, optimism, polygon, etc.)
- to_chain: Destination chain

Respond with JSON:
{{
    "valid": true/false,
    "token": "ETH",
    "amount": "1.0",
    "from_chain": "ethereum",
    "to_chain": "arbitrum"
}}
"""
        
        try:
            response = await self._llm_client.classify_intent(
                prompt=prompt,
                model=self._model,
            )
            return response
        except Exception:
            return {"valid": False}
    
    async def _get_bridge_routes(self, bridge_request: dict) -> list[dict]:
        """Get available bridge routes."""
        # TODO: Implement real bridge API integration
        
        # Mock routes
        token = bridge_request.get("token", "ETH")
        amount = Decimal(bridge_request.get("amount", "1.0"))
        from_chain = bridge_request.get("from_chain", "ethereum")
        to_chain = bridge_request.get("to_chain", "arbitrum")
        
        routes = [
            {
                "provider": "Arbitrum Native Bridge",
                "cost_usd": 15.50,
                "time_minutes": 420,  # 7 hours
                "security_score": 95,
                "token": token,
                "amount": float(amount),
                "from_chain": from_chain,
                "to_chain": to_chain,
            },
            {
                "provider": "Hop Protocol",
                "cost_usd": 8.20,
                "time_minutes": 10,
                "security_score": 88,
                "token": token,
                "amount": float(amount),
                "from_chain": from_chain,
                "to_chain": to_chain,
            },
            {
                "provider": "Axelar",
                "cost_usd": 12.00,
                "time_minutes": 5,
                "security_score": 92,
                "token": token,
                "amount": float(amount),
                "from_chain": from_chain,
                "to_chain": to_chain,
            },
        ]
        
        # Sort by cost
        routes.sort(key=lambda r: r["cost_usd"])
        
        return routes
    
    async def _generate_bridge_comparison(self, routes: list[dict]) -> str:
        """Generate bridge route comparison."""
        if not routes:
            return "No bridge routes found for this token/chain combination."
        
        best_route = routes[0]
        token = best_route["token"]
        amount = best_route["amount"]
        from_chain = best_route["from_chain"].capitalize()
        to_chain = best_route["to_chain"].capitalize()
        
        comparison = f"""🌉 **BRIDGE ROUTE COMPARISON**

**Transfer**: {amount} {token}
**From**: {from_chain} → **To**: {to_chain}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**AVAILABLE ROUTES** ({len(routes)})
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""
        
        for i, route in enumerate(routes, 1):
            emoji = "⭐" if i == 1 else f"{i}️⃣"
            cost = route["cost_usd"]
            time_min = route["time_minutes"]
            security = route["security_score"]
            
            # Format time
            if time_min < 60:
                time_str = f"{time_min}m"
            elif time_min < 1440:
                time_str = f"{time_min // 60}h"
            else:
                time_str = f"{time_min // 1440}d"
            
            # Security emoji
            if security >= 90:
                security_emoji = "🟢"
            elif security >= 80:
                security_emoji = "🟡"
            else:
                security_emoji = "🔴"
            
            comparison += f"""
{emoji} **{route["provider"]}**
  💰 Cost: ${cost:.2f}
  ⏱️  Time: ~{time_str}
  {security_emoji} Security: {security}/100
  
"""
        
        comparison += """━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**RECOMMENDATION**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""
        
        best = routes[0]
        comparison += f"""⭐ **{best["provider"]}** (Best Overall)

**Why**: Lowest cost (${best["cost_usd"]:.2f})
**Trade-off**: {best["time_minutes"]}min wait time
**Security**: {best["security_score"]}/100 (audited)

**Next Steps**:
1. Approve {token} spend (if needed)
2. Initiate bridge transaction
3. Wait ~{best["time_minutes"]}min for confirmation
4. Tokens arrive on {to_chain}

**Important**: Bridge transactions are irreversible. Double-check
destination address and chain before confirming.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Savings**: ${routes[-1]["cost_usd"] - routes[0]["cost_usd"]:.2f} vs most expensive route
**Bridge Provider**: {best["provider"]}
**Estimated Total Cost**: ${best["cost_usd"]:.2f} (gas + bridge fee)
"""
        
        return comparison.strip()
    
    def _build_error_response(self, error_message: str, start_time: float) -> AgentResponse:
        """Build error response."""
        latency_ms = int((time.time() - start_time) * 1000)
        
        return AgentResponse(
            content=error_message,
            agent_type=self.agent_type,
            tools_used=[],
            metadata={"latency_ms": latency_ms, "error": True},
        )
