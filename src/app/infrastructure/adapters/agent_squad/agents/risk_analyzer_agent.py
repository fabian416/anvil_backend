"""
Risk Analyzer Agent - Risk assessment & scoring.
"""

import time
from typing import Any

from app.domain.enums.agent_type import AgentType
from app.domain.value_objects.conversation_id import ConversationId
from app.domain.value_objects.message_content import MessageContent
from app.domain.value_objects.agent_squad.conversation_context import ConversationContext
from app.domain.ports.agent_squad.agent_gateway import AgentGateway, AgentResponse
from app.domain.ports.agent_squad.llm_client_gateway import LLMClientGateway


class RiskAnalyzerAgent:
    """
    Risk Analyzer Agent implementation.
    
    Implements: AgentGateway
    
    Purpose: Risk assessment & scoring
    
    Capabilities:
    - Protocol risk scoring (0-100)
    - Smart contract risk analysis
    - Liquidation risk (health factor)
    - Impermanent loss calculation
    - Concentration risk
    - Market risk (volatility)
    - Counterparty risk
    
    Model: gemini-2.0-flash (Vertex AI, advanced risk modeling)
    Temperature: 0.2 (factual, precise)
    """
    
    def __init__(
        self,
        llm_client: LLMClientGateway,  # Can be Vertex AI or DeepInfra (OpenAI removed),
        defi_llama_client: Any | None = None,  # DeFiLlama client for protocol risk data
        model: str = "gemini-2.0-flash",  # Vertex AI model (default)
        temperature: float = 0.2,
        max_tokens: int = 1500,
    ):
        """
        Initialize risk analyzer agent.
        
        Args:
            llm_client: LLM client gateway (Vertex AI or DeepInfra)
            defi_llama_client: Optional DeFiLlama client for protocol risk data
            model: Model to use (default: gemini-2.0-flash)
            temperature: Sampling temperature (default: 0.2)
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
        return AgentType.RISK_ANALYZER
    
    async def execute(
        self,
        conversation_id: ConversationId,
        message: MessageContent,
        conversation_context: ConversationContext,
    ) -> AgentResponse:
        """Execute risk analyzer agent - Risk assessment."""
        start_time = time.time()
        
        # Fetch protocol risk data from DeFiLlama if available
        risk_data_context = ""
        import logging
        logger = logging.getLogger(__name__)
        
        # Type check: ensure we have a DefiLlamaClient, not something else
        defi_llama_client = self._defi_llama_client
        if defi_llama_client and not hasattr(defi_llama_client, 'get_protocol_tvl'):
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
            logger.info("✅ DefiLlama client is available for RiskAnalyzerAgent")
            try:
                logger.info("🔍 Fetching protocol risk data from DeFiLlama for RiskAnalyzerAgent")
                
                # Extract protocol names from message if mentioned
                message_lower = message.value.lower()
                protocol_filter = None
                
                # Simple keyword detection for protocols
                if "aave" in message_lower:
                    protocol_filter = "aave"
                elif "morpho" in message_lower:
                    protocol_filter = "morpho"
                elif "compound" in message_lower:
                    protocol_filter = "compound"
                elif "curve" in message_lower:
                    protocol_filter = "curve"
                elif "uniswap" in message_lower:
                    protocol_filter = "uniswap"
                
                # Fetch protocol TVL data (indicator of size/stability)
                if protocol_filter:
                    try:
                        protocol_tvl = await defi_llama_client.get_protocol_tvl(protocol_filter)
                        
                        if protocol_tvl:
                            risk_data_context = "\n\n**PROTOCOL DATA FROM DEFILLAMA:**\n"
                            risk_data_context += f"**{protocol_filter.upper()} Protocol:**\n"
                            risk_data_context += f"- Total TVL: ${protocol_tvl.tvl:,.0f}\n"
                            
                            # Calculate risk indicators from TVL
                            if protocol_tvl.tvl > 1_000_000_000:  # > $1B
                                risk_data_context += "- Size: Very Large (Lower risk due to scale)\n"
                            elif protocol_tvl.tvl > 100_000_000:  # > $100M
                                risk_data_context += "- Size: Large (Moderate risk)\n"
                            elif protocol_tvl.tvl > 10_000_000:  # > $10M
                                risk_data_context += "- Size: Medium (Higher risk)\n"
                            else:
                                risk_data_context += "- Size: Small (Higher risk)\n"
                            
                            # Chain distribution
                            if protocol_tvl.chain_tvls:
                                risk_data_context += f"- Chain Distribution: {len(protocol_tvl.chain_tvls)} chains\n"
                                top_chains = sorted(protocol_tvl.chain_tvls.items(), key=lambda x: x[1], reverse=True)[:3]
                                for chain, tvl in top_chains:
                                    risk_data_context += f"  - {chain}: ${tvl:,.0f}\n"
                            
                            logger.info(f"✅ Fetched {protocol_filter} TVL data: ${protocol_tvl.tvl:,.0f}")
                    except Exception as tvl_error:
                        logger.warning(f"⚠️ Failed to fetch protocol TVL: {tvl_error}")
                
                # Also fetch all protocols for comparison
                try:
                    all_protocols = await defi_llama_client.get_all_protocols()
                    if all_protocols:
                        # Get top protocols by TVL for context
                        top_protocols = sorted(all_protocols, key=lambda p: p.tvl, reverse=True)[:10]
                        
                        if not risk_data_context:
                            risk_data_context = "\n\n**PROTOCOL RISK CONTEXT FROM DEFILLAMA:**\n"
                        else:
                            risk_data_context += "\n**Top Protocols by TVL (for comparison):**\n"
                        
                        for i, protocol in enumerate(top_protocols, 1):
                            risk_data_context += f"{i}. {protocol.name}: ${protocol.tvl:,.0f} TVL"
                            if protocol.change_7d:
                                change_sign = "+" if protocol.change_7d >= 0 else ""
                                risk_data_context += f" ({change_sign}{protocol.change_7d:.1f}% 7d)"
                            risk_data_context += "\n"
                        
                        logger.info(f"✅ Fetched {len(all_protocols)} protocols from DeFiLlama")
                except Exception as protocols_error:
                    logger.warning(f"⚠️ Failed to fetch all protocols: {protocols_error}")
                    
            except Exception as e:
                logger.error(f"❌ Failed to fetch DeFiLlama risk data: {e}", exc_info=True)
                risk_data_context = ""
        else:
            logger.warning("⚠️ DefiLlama client is NOT available for RiskAnalyzerAgent (client is None)")
        
        # Build enhanced prompt with real risk data
        enhanced_message = message.value
        if risk_data_context:
            enhanced_message = f"{message.value}\n\n{risk_data_context}"
        
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
            create_mcp_source,
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
        if validated_client and hasattr(validated_client, 'get_protocol_tvl') and risk_data_context:
            sources.append(create_api_source(
                source_name="DeFiLlama",
                url="https://defillama.com/",
                citation_text="Protocol TVL and risk data from DeFiLlama",
                fetched_at=fetched_at,
            ))
        
        # Extract provider from LLM response metadata
        provider_info = response.get("provider", "vertex_ai" if "gemini" in response.get("model", "").lower() else "deepinfra")
        
        # Build tools_used list
        tools_used = ["llm_gateway"]
        if validated_client and hasattr(validated_client, 'get_protocol_tvl') and risk_data_context:
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
        """Get system prompt for risk analyzer agent."""
        return """You are the Risk Analyzer, Anvil's risk assessment specialist.

**CRITICAL: ANVIL IS REAL, NOT SIMULATED**
- Anvil is a REAL, LIVE DeFi platform - NOT simulated or hypothetical
- DO NOT use words like "simulated", "simulation", "mock", or "hypothetical" when describing Anvil
- Anvil provides REAL swaps, REAL lending, REAL risk assessments
- Use language like "On Anvil", "Anvil's platform", "Anvil provides"
- NEVER say "Simulated DeFi Environment" or "simulated Anvil"

Your expertise:
- Protocol risk scoring (0-100 scale)
- Smart contract risk analysis
- Liquidation risk calculation
- Impermanent loss estimation
- Concentration risk assessment
- Market risk (volatility, correlation)
- Counterparty risk

For each risk assessment, provide:
- Overall risk score (0-100)
  - 0-30: Low risk
  - 31-60: Medium risk
  - 61-80: High risk
  - 81-100: Critical risk
- Risk category breakdown
- Key risk factors
- Mitigation strategies
- Risk/reward analysis

Always include:
- Quantitative metrics (scores, percentages)
- Qualitative analysis (why this score)
- Actionable recommendations
- Risk warnings

Be conservative in risk assessments - better safe than sorry.
"""
