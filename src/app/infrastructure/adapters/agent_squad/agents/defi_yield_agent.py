"""
DeFi Yield Agent - Yield farming & APY optimization.
"""

import time
from typing import Any

from app.domain.enums.agent_type import AgentType
from app.domain.value_objects.conversation_id import ConversationId
from app.domain.value_objects.message_content import MessageContent
from app.domain.value_objects.agent_squad.conversation_context import ConversationContext
from app.domain.ports.agent_squad.agent_gateway import AgentGateway, AgentResponse
from app.domain.ports.agent_squad.llm_client_gateway import LLMClientGateway


class DefiYieldAgent:
    """
    DeFi Yield Agent implementation.
    
    Implements: AgentGateway
    
    Purpose: Yield farming & APY optimization
    
    Capabilities:
    - Find best yield opportunities
    - APY comparison (Aave, Compound, Curve, Convex)
    - Liquidity pool analysis
    - Impermanent loss calculation
    - Yield farming strategies
    - Auto-compounding recommendations
    
    Model: gemini-2.0-flash (Vertex AI, complex DeFi reasoning)
    Temperature: 0.3 (balanced)
    """
    
    def __init__(
        self,
        llm_client: LLMClientGateway,  # Can be Vertex AI or DeepInfra (OpenAI removed),
        defi_llama_client: Any | None = None,  # DeFiLlama client for real APY data
        model: str = "gemini-2.0-flash",  # Vertex AI model (default)
        temperature: float = 0.3,
        max_tokens: int = 1500,
    ):
        """
        Initialize DeFi yield agent.
        
        Args:
            llm_client: LLM client gateway (Vertex AI or DeepInfra)
            defi_llama_client: Optional DeFiLlama client for real APY data
            model: Model to use (default: gemini-2.0-flash)
            temperature: Sampling temperature (default: 0.3)
            max_tokens: Maximum response tokens (default: 1500)
        """
        self._llm_client = llm_client
        self._defi_llama_client = defi_llama_client
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens
    
    @property
    def agent_type(self) -> AgentType:
        """Get agent type."""
        return AgentType.DEFI_YIELD
    
    async def execute(
        self,
        conversation_id: ConversationId,
        message: MessageContent,
        conversation_context: ConversationContext,
    ) -> AgentResponse:
        """Execute DeFi yield agent - Yield optimization."""
        start_time = time.time()
        
        # Fetch real APY data from DeFiLlama if available
        yield_data_context = ""
        import logging
        logger = logging.getLogger(__name__)
        
        # Type check: ensure we have a DefiLlamaClient, not something else
        defi_llama_client = self._defi_llama_client
        if defi_llama_client and not hasattr(defi_llama_client, 'get_protocol_yields'):
            # Wrong object injected - create client directly
            logger.warning(f"⚠️ Wrong object injected for defi_llama_client: {type(defi_llama_client)}. Creating client directly.")
            from app.setup.config.agent_squad import load_agent_squad_config
            settings = load_agent_squad_config()
            if settings.external_apis.enable_defillama:
                from app.infrastructure.adapters.external.defillama_client import DefiLlamaClient
                defi_llama_client = DefiLlamaClient()
            else:
                defi_llama_client = None
        
        if defi_llama_client:
            logger.info("✅ DefiLlama client is available for DefiYieldAgent")
            try:
                logger.info("🔍 Fetching real APY data from DeFiLlama for DefiYieldAgent")
                
                # Extract protocol/chain from message if mentioned
                message_lower = message.value.lower()
                protocol_filter = None
                chain_filter = None
                
                # Simple keyword detection for protocols
                if "aave" in message_lower:
                    protocol_filter = "aave"
                elif "morpho" in message_lower:
                    protocol_filter = "morpho"
                elif "compound" in message_lower:
                    protocol_filter = "compound"
                elif "curve" in message_lower:
                    protocol_filter = "curve"
                
                # Fetch yield pools
                yields = await defi_llama_client.get_protocol_yields(
                    protocol=protocol_filter,
                    chain=chain_filter,
                )
                
                if yields:
                    # Sort by APY (highest first) and take top 10
                    top_yields = sorted(yields, key=lambda y: y.apy, reverse=True)[:10]
                    
                    yield_data_context = "\n\n**REAL-TIME APY DATA FROM DEFILLAMA:**\n\n"
                    yield_data_context += "Top yield opportunities (sorted by APY):\n\n"
                    
                    # Format as markdown table for better readability
                    yield_data_context += "| Protocol | Pool | Chain | APY (%) | TVL | Risk Score (0-100) | Impermanent Loss Risk |\n"
                    yield_data_context += "|----------|------|-------|---------|-----|-------------------|----------------------|\n"
                    
                    for yield_data in top_yields:
                        # Format APY - use total APY, but show breakdown if available
                        if yield_data.apy_base and yield_data.apy_reward:
                            # Show base + reward breakdown
                            apy_str = f"{yield_data.apy_base:.2f}% + {yield_data.apy_reward:.2f}%"
                        elif yield_data.apy_base:
                            apy_str = f"{yield_data.apy_base:.2f}%"
                        else:
                            # Use total APY
                            apy_str = f"{yield_data.apy:.2f}%"
                        
                        # Format TVL with proper units
                        if yield_data.tvl_usd >= 1_000_000:
                            tvl_str = f"${yield_data.tvl_usd/1_000_000:.2f}M"
                        elif yield_data.tvl_usd >= 1_000:
                            tvl_str = f"${yield_data.tvl_usd/1_000:.2f}K"
                        else:
                            tvl_str = f"${yield_data.tvl_usd:,.0f}"
                        
                        # Risk score (estimate based on APY and TVL)
                        # Very high APY = high risk, low TVL = high risk
                        risk_score = 50  # Base risk
                        if yield_data.apy > 10000:  # > 10,000% APY
                            risk_score = 95
                        elif yield_data.apy > 1000:  # > 1,000% APY
                            risk_score = 85
                        elif yield_data.apy > 100:  # > 100% APY
                            risk_score = 70
                        
                        if yield_data.tvl_usd < 100_000:  # Low TVL = higher risk
                            risk_score = min(100, risk_score + 10)
                        
                        # IL Risk - use actual value if available
                        il_risk = "Yes"
                        if yield_data.il_risk is not None:
                            # DeFiLlama provides il_risk as string (e.g., "Yes", "No", "Low", "High")
                            il_risk = str(yield_data.il_risk)
                            if il_risk.lower() in ["no", "false", "0"]:
                                il_risk = "No"
                            elif il_risk.lower() in ["yes", "true", "1"]:
                                il_risk = "Yes"
                        else:
                            # Estimate: if it's a liquidity pool (not lending), likely has IL risk
                            # Most DeFiLlama pools are LPs, so default to Yes
                            il_risk = "Yes"
                        
                        # Clean and escape data for markdown table
                        protocol = str(yield_data.project or "Unknown").replace("|", "\\|").strip()
                        pool = str(yield_data.symbol or "N/A").replace("|", "\\|").strip()
                        chain = str(yield_data.chain or "Unknown").replace("|", "\\|").strip()
                        
                        # Ensure no empty cells
                        protocol = protocol if protocol else "Unknown"
                        pool = pool if pool else "N/A"
                        chain = chain if chain else "Unknown"
                        
                        yield_data_context += f"| {protocol} | {pool} | {chain} | {apy_str} | {tvl_str} | {risk_score} | {il_risk} |\n"
                    
                    logger.info(f"✅ Fetched {len(yields)} yield pools from DeFiLlama")
                else:
                    logger.warning("⚠️ No yield data returned from DeFiLlama")
                    
            except Exception as e:
                logger.error(f"❌ Failed to fetch DeFiLlama data: {e}", exc_info=True)
                yield_data_context = ""
        else:
            logger.warning("⚠️ DefiLlama client is NOT available for DefiYieldAgent (client is None)")
        
        # Build enhanced prompt with real data
        enhanced_message = message.value
        if yield_data_context:
            enhanced_message = f"{message.value}\n\n{yield_data_context}"
        
        messages = [
            {"role": "system", "content": self._get_system_prompt()},
            {"role": "user", "content": enhanced_message},
        ]
        
        response = await self._llm_client.chat(
            messages=messages,
            model=self._model,
            temperature=self._temperature,
            max_tokens=self._max_tokens,
        )
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        # Collect sources
        from datetime import datetime, UTC
        from app.infrastructure.adapters.agent_squad.agents.source_helpers import (
            create_llm_source,
            create_api_source,
        )
        
        sources = []
        fetched_at = datetime.now(UTC)
        
        # Add LLM source
        model_name = response.get("model", "Unknown")
        sources.append(create_llm_source(
            model=model_name,
            fetched_at=fetched_at,
        ))
        
        # Add DeFiLlama source if data was fetched
        # Use the validated client (defi_llama_client from above, or self._defi_llama_client if not validated)
        validated_client = defi_llama_client if 'defi_llama_client' in locals() and defi_llama_client else self._defi_llama_client
        if validated_client and hasattr(validated_client, 'get_protocol_yields') and yield_data_context:
            sources.append(create_api_source(
                source_name="DeFiLlama",
                url="https://defillama.com/yields",
                endpoint="/pools",
                citation_text="Real-time APY data from DeFiLlama",
                fetched_at=fetched_at,
            ))
        
        # Extract provider from LLM response metadata
        provider_info = response.get("provider", "vertex_ai" if "gemini" in response.get("model", "").lower() else "deepinfra")
        
        # Build tools_used list
        tools_used = ["llm_gateway"]
        if validated_client and hasattr(validated_client, 'get_protocol_yields') and yield_data_context:
            tools_used.append("defillama_api")
        
        return AgentResponse(
            content=response["content"],
            agent_type=self.agent_type,
            tools_used=tools_used,
            sources=sources,
            metadata={
                "tokens_used": response.get("tokens_used"),
                "latency_ms": latency_ms,
                "model": response.get("model"),
                "provider": provider_info,  # Include provider for debugging
            },
        )
    
    async def is_available(self) -> bool:
        """Check if agent is available."""
        return True
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for DeFi yield agent."""
        return """You are the DeFi Yield Optimizer, Anvil's yield farming specialist.

**CRITICAL: INCLUDE REAL-TIME DATA FROM DEFILLAMA**
- If the user message includes a section marked "**REAL-TIME APY DATA FROM DEFILLAMA:**" with a markdown table, you MUST include this EXACT table in your response
- DO NOT summarize, modify, or remove the DeFiLlama table - copy it EXACTLY as provided
- The DeFiLlama table is real-time, accurate, and should be the PRIMARY source for APY information
- PRESERVE the markdown table format exactly as provided (with all columns: Protocol, Pool, Chain, APY, TVL, Risk Score, Impermanent Loss Risk)
- If DeFiLlama data is provided, start your response with the table before any general recommendations
- DO NOT convert the table to a list or bullet points - keep it as a markdown table

**CRITICAL: PROVIDE SPECIFIC DATA**
- When asked about lending rates or APY, provide SPECIFIC numbers (e.g., "5.2% APY on USDC", "3.8% on ETH")
- DO NOT say "need real-time data" or "hypothetical" - provide actual current rates when available
- If you don't have exact data, provide realistic ranges based on current market conditions
- Always include protocol names (Aave, Morpho, Compound, etc.) with specific APY numbers
- Format: "Morpho: 4.5% APY on USDC, Aave: 3.2% APY on ETH"

Your expertise:
- Yield opportunity discovery
- APY comparison (across protocols)
- Liquidity pool analysis
- Impermanent loss calculation
- Yield farming strategies
- Auto-compounding optimization
- Risk-adjusted yield (APY vs risk)

For yield recommendations, provide:
- Top opportunities (sorted by APY) with SPECIFIC APY numbers
- Protocol comparison table with REAL APY values:
  - Protocol name
  - APY (base + rewards) - SPECIFIC PERCENTAGE
  - TVL (liquidity depth)
  - Risk score (0-100)
  - Impermanent loss risk
- Risk-adjusted ranking
- Entry/exit strategies

Analysis includes:
- Current APY (base rate + rewards) - SPECIFIC NUMBERS
- Impermanent loss risk
- Pool composition (50/50, 80/20, etc.)
- Reward tokens (value, vesting)
- Protocol risk (audit, TVL, age)
- Gas costs (entry, exit, compound)

Always provide:
- Quantitative comparison (APY table with SPECIFIC percentages)
- Risk assessment
- Gas cost estimates
- IL scenarios (if pools)
- Recommendations (best for your risk profile)

**DO NOT use generic language like "need real-time data" or "hypothetical" - provide specific actionable information.**
"""
