"""
Gas Optimizer Agent - Gas fee optimization & timing.
"""

import time
from typing import Any

from app.domain.enums.agent_type import AgentType
from app.domain.value_objects.conversation_id import ConversationId
from app.domain.value_objects.message_content import MessageContent
from app.domain.value_objects.agent_squad.conversation_context import ConversationContext
from app.domain.ports.agent_squad.agent_gateway import AgentGateway, AgentResponse
from app.domain.ports.agent_squad.llm_client_gateway import LLMClientGateway


class GasOptimizerAgent:
    """
    Gas Optimizer Agent implementation.
    
    Implements: AgentGateway
    
    Purpose: Gas fee optimization & timing
    
    Capabilities:
    - Current gas price analysis
    - Gas price predictions (next hour, day)
    - Optimal transaction timing
    - Layer 2 migration recommendations
    - Batch transaction suggestions
    - Gas-efficient alternatives
    
    Model: gemini-2.0-flash (Vertex AI, fast, cost-effective)
    Temperature: 0.2 (factual)
    """
    
    def __init__(
        self,
        llm_client: LLMClientGateway,  # Can be Vertex AI or DeepInfra (OpenAI removed),
        web3_client: Any | None = None,  # Web3 client for real-time gas prices
        model: str = "gemini-2.0-flash",  # Vertex AI model (default)
        temperature: float = 0.2,
        max_tokens: int = 1000,
    ):
        """
        Initialize gas optimizer agent.
        
        Args:
            llm_client: LLM client gateway (Vertex AI or DeepInfra)
            web3_client: Optional Web3 client for real-time gas prices
            model: Model to use (default: gemini-2.0-flash)
            temperature: Sampling temperature (default: 0.2)
            max_tokens: Maximum response tokens (default: 1000)
        """
        self._llm_client = llm_client
        self._web3_client = web3_client
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens
    
    @property
    def agent_type(self) -> AgentType:
        """Get agent type."""
        return AgentType.GAS_OPTIMIZER
    
    async def execute(
        self,
        conversation_id: ConversationId,
        message: MessageContent,
        conversation_context: ConversationContext,
    ) -> AgentResponse:
        """Execute gas optimizer agent - Gas optimization."""
        start_time = time.time()
        
        # Fetch real-time gas prices from Web3Client if available
        # Support multiple chains based on user query
        gas_price_context = ""
        import logging
        logger = logging.getLogger(__name__)
        
        # Type check: ensure we have a Web3Client, not something else
        web3_client = self._web3_client
        if web3_client and not hasattr(web3_client, 'get_gas_price'):
            # Wrong object injected - create client directly
            logger.warning(f"⚠️ Wrong object injected for web3_client: {type(web3_client)}. Creating client directly.")
            from app.setup.config.agent_squad import load_agent_squad_config
            settings = load_agent_squad_config()
            # Try both direct env vars and RPC_ prefixed (from .secrets.toml export)
            alchemy_key = os.getenv("ALCHEMY_API_KEY") or os.getenv("RPC_ALCHEMY_API_KEY", "")
            infura_key = os.getenv("INFURA_API_KEY") or os.getenv("RPC_INFURA_API_KEY", "")
            if alchemy_key or infura_key:
                from app.infrastructure.adapters.external.web3_client import Web3Client, Chain
                web3_client = Web3Client(
                    alchemy_api_key=alchemy_key if alchemy_key else None,
                    infura_api_key=infura_key if infura_key else None,
                    chain=Chain.ETHEREUM,
                )
            else:
                web3_client = None
        
        if web3_client:
            try:
                import logging
                import re
                logger = logging.getLogger(__name__)
                logger.info("🔍 Fetching real-time gas prices from Web3Client for GasOptimizerAgent")
                
                # Detect chain from message
                message_lower = message.value.lower()
                chains_to_check = []
                
                # Chain detection patterns
                if any(word in message_lower for word in ["ethereum", "eth", "mainnet", "ethereum mainnet"]):
                    chains_to_check.append("ethereum")
                if any(word in message_lower for word in ["polygon", "matic", "polygon network"]):
                    chains_to_check.append("polygon")
                if any(word in message_lower for word in ["arbitrum", "arb"]):
                    chains_to_check.append("arbitrum")
                if any(word in message_lower for word in ["optimism", "op"]):
                    chains_to_check.append("optimism")
                if any(word in message_lower for word in ["base", "base network"]):
                    chains_to_check.append("base")
                if any(word in message_lower for word in ["avalanche", "avax"]):
                    chains_to_check.append("avalanche")
                if any(word in message_lower for word in ["bsc", "binance", "bnb"]):
                    chains_to_check.append("bsc")
                
                # Default to Ethereum if no chain specified
                if not chains_to_check:
                    chains_to_check = ["ethereum"]
                
                # Fetch gas prices for detected chains
                for chain_name in chains_to_check:
                    try:
                        # Note: Web3Client currently supports Ethereum primarily
                        # For other chains, we'd need chain-specific clients
                        # For now, fetch Ethereum and provide general guidance for others
                        if chain_name == "ethereum":
                            gas_price = await web3_client.get_gas_price()
                            
                            if gas_price:
                                # Calculate slow/standard/fast from base fee and priority fee
                                slow_gwei = gas_price.base_fee_gwei
                                standard_gwei = gas_price.base_fee_gwei + gas_price.priority_fee_gwei
                                fast_gwei = gas_price.max_fee_gwei
                                
                                # Estimate USD costs
                                slow_usd = (slow_gwei * 21000 / 1e9) * 3000  # Approximate ETH price
                                standard_usd = gas_price.estimated_cost_usd
                                fast_usd = (fast_gwei * 21000 / 1e9) * 3000
                                
                                gas_price_context += f"\n\n**REAL-TIME GAS PRICES - {chain_name.upper()}:**\n"
                                gas_price_context += f"- Slow: {slow_gwei:.1f} gwei (${slow_usd:.2f} for standard transfer)\n"
                                gas_price_context += f"- Standard: {standard_gwei:.1f} gwei (${standard_usd:.2f} for standard transfer)\n"
                                gas_price_context += f"- Fast: {fast_gwei:.1f} gwei (${fast_usd:.2f} for standard transfer)\n"
                                gas_price_context += f"- Base Fee: {gas_price.base_fee_gwei:.1f} gwei\n"
                                gas_price_context += f"- Priority Fee: {gas_price.priority_fee_gwei:.1f} gwei\n"
                                
                                # Add timing recommendations
                                if slow_gwei < 30:
                                    gas_price_context += "\n💡 **Recommendation**: Gas prices are LOW - good time to send transactions\n"
                                elif slow_gwei > 100:
                                    gas_price_context += "\n⚠️ **Recommendation**: Gas prices are HIGH - consider waiting or using Layer 2 (Arbitrum, Optimism, Base)\n"
                                else:
                                    gas_price_context += "\n✅ **Recommendation**: Gas prices are MODERATE - standard transactions should work well\n"
                                
                                logger.info(f"✅ Fetched {chain_name} gas prices: Slow={slow_gwei:.1f}, Standard={standard_gwei:.1f}, Fast={fast_gwei:.1f} gwei")
                        else:
                            # For other chains, provide general guidance
                            gas_price_context += f"\n\n**GAS PRICE GUIDANCE - {chain_name.upper()}:**\n"
                            if chain_name == "polygon":
                                gas_price_context += "- Typical: 30-100 gwei (~$0.01-0.05 per transaction)\n"
                                gas_price_context += "- ~95% cheaper than Ethereum\n"
                            elif chain_name == "arbitrum":
                                gas_price_context += "- Typical: 0.1-0.5 gwei (~$0.10-0.50 per transaction)\n"
                                gas_price_context += "- ~90% cheaper than Ethereum\n"
                            elif chain_name == "optimism":
                                gas_price_context += "- Typical: 0.1-1 gwei (~$0.10-1.00 per transaction)\n"
                                gas_price_context += "- ~85% cheaper than Ethereum\n"
                            elif chain_name == "base":
                                gas_price_context += "- Typical: 0.1-0.5 gwei (~$0.10-0.50 per transaction)\n"
                                gas_price_context += "- ~90% cheaper than Ethereum\n"
                            elif chain_name == "avalanche":
                                gas_price_context += "- Typical: 25-30 nAVAX (~$0.01-0.05 per transaction)\n"
                                gas_price_context += "- Very cheap\n"
                            elif chain_name == "bsc":
                                gas_price_context += "- Typical: 3-5 gwei (~$0.10-0.50 per transaction)\n"
                                gas_price_context += "- Much cheaper than Ethereum\n"
                            
                            gas_price_context += "- Note: Real-time prices require chain-specific RPC access\n"
                            
                    except Exception as chain_error:
                        logger.warning(f"⚠️ Failed to fetch {chain_name} gas prices: {chain_error}")
                        continue
                    
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"⚠️ Failed to fetch gas prices: {e}, continuing with LLM-only response")
                gas_price_context = ""
        
        # Build enhanced prompt with real gas data
        enhanced_message = message.value
        if gas_price_context:
            enhanced_message = f"{message.value}\n\n{gas_price_context}"
        
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
            create_blockchain_source,
        )
        
        sources = []
        fetched_at = datetime.now(UTC)
        
        # Add LLM source
        model_name = response.get("model", "Unknown")
        sources.append(create_llm_source(
            model=model_name,
            fetched_at=fetched_at,
        ))
        
        # Add blockchain source if gas prices were fetched
        # Use the validated client (web3_client from above, or self._web3_client if not validated)
        validated_web3_client = web3_client if 'web3_client' in locals() else self._web3_client
        if validated_web3_client and hasattr(validated_web3_client, 'get_gas_price') and gas_price_context:
            # Extract chain names from context
            chains_mentioned = []
            if "ethereum" in gas_price_context.lower():
                chains_mentioned.append("Ethereum")
            if "polygon" in gas_price_context.lower():
                chains_mentioned.append("Polygon")
            if "arbitrum" in gas_price_context.lower():
                chains_mentioned.append("Arbitrum")
            if "optimism" in gas_price_context.lower():
                chains_mentioned.append("Optimism")
            if "base" in gas_price_context.lower():
                chains_mentioned.append("Base")
            if "avalanche" in gas_price_context.lower():
                chains_mentioned.append("Avalanche")
            if "bsc" in gas_price_context.lower() or "binance" in gas_price_context.lower():
                chains_mentioned.append("BSC")
            
            chain_name = ", ".join(chains_mentioned) if chains_mentioned else "Multiple Chains"
            sources.append(create_blockchain_source(
                chain=chain_name,
                citation_text=f"Real-time gas prices from {chain_name} network(s)",
                fetched_at=fetched_at,
            ))
        
        # Build tools_used list
        tools_used = ["llm_gateway"]
        if validated_web3_client and hasattr(validated_web3_client, 'get_gas_price') and gas_price_context:
            tools_used.append("web3_client")
        
        # Extract provider from LLM response metadata
        provider_info = response.get("provider", "vertex_ai" if "gemini" in response.get("model", "").lower() else "deepinfra")
        
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
        """Get system prompt for gas optimizer agent."""
        return """You are the Gas Optimizer, Anvil's multi-chain gas fee optimization specialist.

**CRITICAL: SUPPORT ALL BLOCKCHAINS**
- You optimize gas for ALL chains: Ethereum, Polygon, Arbitrum, Optimism, Base, Avalanche, BSC, etc.
- Each chain has different gas mechanisms and costs
- Provide chain-specific recommendations

Your expertise:
- Real-time gas price analysis (ALL chains)
- Gas price predictions (hourly, daily trends)
- Optimal transaction timing
- Cross-chain gas comparison
- Layer 2 migration recommendations
- Batch transaction optimization
- Gas-efficient alternatives

**Multi-Chain Gas Support:**

**Ethereum (ETH):**
- Gas measured in gwei
- EIP-1559: base fee + priority fee
- Price Levels: Low (10-30 gwei), Standard (30-50 gwei), Fast (50-100 gwei), Urgent (100+ gwei)

**Polygon (MATIC):**
- Gas measured in gwei (much cheaper)
- Typical: 30-100 gwei (~$0.01-0.05 per transaction)
- ~95% cheaper than Ethereum

**Arbitrum (ETH):**
- Gas measured in gwei (L2)
- Typical: 0.1-0.5 gwei (~$0.10-0.50 per transaction)
- ~90% cheaper than Ethereum

**Optimism (ETH):**
- Gas measured in gwei (L2)
- Typical: 0.1-1 gwei (~$0.10-1.00 per transaction)
- ~85% cheaper than Ethereum

**Base (ETH):**
- Gas measured in gwei (L2)
- Typical: 0.1-0.5 gwei
- ~90% cheaper than Ethereum

**Avalanche (AVAX):**
- Gas measured in nAVAX (nano-AVAX)
- Typical: 25-30 nAVAX (~$0.01-0.05 per transaction)
- Very cheap

**BSC (BNB):**
- Gas measured in gwei
- Typical: 3-5 gwei (~$0.10-0.50 per transaction)
- Much cheaper than Ethereum

**Solana (SOL):**
- Transaction fees: ~0.000005 SOL (~$0.0001-0.001)
- Fixed fee per transaction
- Very cheap

For gas optimization, provide:
- Current gas prices for the relevant chain(s)
- Gas price trends (rising, falling, stable)
- Timing recommendations (send now vs wait)
- Cost estimates (USD) for the chain
- Cross-chain comparison (if applicable)
- Layer 2 alternatives (if on Ethereum)
- Batch transaction suggestions

Always include:
- Chain name and native token
- Current gas prices (with units: gwei, nAVAX, etc.)
- USD cost estimates
- Time estimates
- Chain-specific recommendations
- Layer 2 migration options (if on Ethereum)
- Timing strategy (urgent vs can wait)
"""
