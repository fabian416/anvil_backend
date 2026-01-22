"""
Knowledge Anvil Agent - Specialized agent for educational and knowledge queries.

Handles:
- Anvil platform knowledge
- DeFi/crypto educational questions
- Token explanations
- Protocol information
- General knowledge about blockchain/Web3
"""

import time
from typing import Any

from app.domain.enums.agent_type import AgentType
from app.domain.value_objects.conversation_id import ConversationId
from app.domain.value_objects.message_content import MessageContent
from app.domain.value_objects.agent_squad.conversation_context import ConversationContext
from app.domain.ports.agent_squad.agent_gateway import AgentGateway, AgentResponse
from app.domain.ports.agent_squad.llm_client_gateway import LLMClientGateway


class KnowledgeAgent:
    """
    Knowledge Anvil Agent implementation.
    
    Implements: AgentGateway
    
    Purpose: Educational queries, Anvil knowledge, DeFi/crypto explanations
    
    Capabilities:
    - Answer "what is X?" questions
    - Explain Anvil platform features
    - Provide educational content about DeFi/crypto
    - Access dynamic knowledge base (JSON files)
    - Multi-language support
    
    Model: gemini-2.0-flash (Vertex AI, fast, cost-effective)
    Temperature: 0.5 (more factual, less creative)
    """
    
    def __init__(
        self,
        llm_client: LLMClientGateway,
        model: str = "gemini-2.0-flash",
        temperature: float = 0.5,  # Lower temperature for factual responses
        max_tokens: int = 1500,  # More tokens for detailed explanations
    ):
        """
        Initialize knowledge agent.
        
        Args:
            llm_client: LLM client gateway (Vertex AI or DeepInfra)
            model: Model to use (default: gemini-2.0-flash)
            temperature: Sampling temperature (default: 0.5 for factual responses)
            max_tokens: Maximum response tokens (default: 1500)
        """
        self._llm_client = llm_client
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._knowledge_injector = None  # Lazy load
    
    @property
    def agent_type(self) -> AgentType:
        """Get agent type."""
        return AgentType.KNOWLEDGE
    
    async def execute(
        self,
        conversation_id: ConversationId,
        message: MessageContent,
        conversation_context: ConversationContext,
    ) -> AgentResponse:
        """
        Execute knowledge agent.
        
        Provides educational responses with access to Anvil knowledge base.
        """
        start_time = time.time()
        
        # Load knowledge injector lazily
        if self._knowledge_injector is None:
            try:
                from app.application.chat.services.knowledge_injector import KnowledgeInjector
                self._knowledge_injector = KnowledgeInjector()
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Could not load KnowledgeInjector: {e}")
                self._knowledge_injector = None
        
        # Detect intent/keywords for knowledge selection
        query_lower = message.value.lower()
        detected_intent = self._detect_knowledge_intent(query_lower)
        
        # Get relevant knowledge from knowledge base
        knowledge_context = ""
        if self._knowledge_injector:
            try:
                # Determine user type (guest vs authenticated)
                user_type = "guest"  # Default for guest chat
                if conversation_context.user_metadata:
                    user_type = conversation_context.user_metadata.get("user_type", "guest")
                
                # Map knowledge agent intents to KnowledgeInjector intents
                # KnowledgeInjector expects specific intent formats
                injector_intent = detected_intent
                if detected_intent == "SWAP":
                    injector_intent = "SWAP"  # KnowledgeInjector handles SWAP
                elif detected_intent.startswith("HUNTER_"):
                    injector_intent = detected_intent  # Keep as is
                elif detected_intent.startswith("ULTRA_"):
                    injector_intent = detected_intent  # Keep as is
                # For other intents, pass as is
                
                # Get knowledge for this intent
                knowledge_dict = self._knowledge_injector.get_knowledge_for_intent(
                    user_query=message.value,
                    detected_intent=injector_intent,
                    user_type=user_type,
                )
                
                # Format knowledge as context
                if knowledge_dict:
                    knowledge_context = self._format_knowledge_context(knowledge_dict)
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Error loading knowledge: {e}")
        
        # Build messages with knowledge context
        messages = self._build_messages(message, conversation_context, knowledge_context)
        
        # Call LLM
        response = await self._llm_client.chat(
            messages=messages,
            model=self._model,
            temperature=self._temperature,
            max_tokens=self._max_tokens,
        )
        
        # Calculate latency
        latency_ms = int((time.time() - start_time) * 1000)
        
        # Add sources
        from datetime import datetime, UTC
        from app.domain.value_objects.chat.source_info import SourceInfo, SourceType
        
        fetched_at = datetime.now(UTC)
        model_name = response.get("model", "Unknown")
        provider = "Vertex AI" if "gemini" in model_name.lower() else "DeepInfra"
        
        sources = [
            SourceInfo(
                source_type=SourceType.LLM,
                source_name=model_name,
                citation_text=f"Generated by {model_name} with Anvil knowledge base",
                fetched_at=fetched_at,
                provider=provider,
                relevance_score=1.0,  # LLM generates the response
                metadata={
                    "model": model_name,
                    "knowledge_base_used": bool(knowledge_context),
                    "intent": detected_intent,
                },
            )
        ]
        
        # Add knowledge base source if used
        if knowledge_context:
            # Use API as source type (knowledge base is loaded from JSON files via KnowledgeInjector)
            sources.append(
                SourceInfo(
                    source_type=SourceType.API,  # Knowledge base is accessed via KnowledgeInjector (API-like)
                    source_name="Anvil Knowledge Base",
                    citation_text="Anvil platform knowledge and features",
                    fetched_at=fetched_at,
                    provider="Anvil",
                    relevance_score=1.0,  # Knowledge base provides relevant data
                    metadata={"intent": detected_intent, "knowledge_base": True},
                )
            )
        
        return AgentResponse(
            content=response["content"],
            agent_type=self.agent_type,
            tools_used=["knowledge_base"] if knowledge_context else [],
            sources=sources,
            metadata={
                "tokens_used": response.get("tokens_used"),
                "latency_ms": latency_ms,
                "model": response.get("model"),
                "finish_reason": response.get("finish_reason"),
                "provider": response.get("provider", provider),
                "knowledge_base_used": bool(knowledge_context),
                "intent": detected_intent,
            },
        )
    
    async def is_available(self) -> bool:
        """Check if agent is available."""
        # Always available (no external dependencies)
        return True
    
    def _detect_knowledge_intent(self, query: str) -> str:
        """Detect knowledge intent from query."""
        query_lower = query.lower()
        
        # Anvil-specific queries
        if any(kw in query_lower for kw in ["anvil", "what is anvil", "how does anvil"]):
            return "anvil_knowledge"
        
        # Hunter AI queries
        if any(kw in query_lower for kw in ["hunter", "hunter ai", "sentiment", "price prediction"]):
            return "HUNTER_SENTIMENT"
        
        # ULTRA queries
        if any(kw in query_lower for kw in ["ultra", "arbitrage", "flash loan", "mev"]):
            return "ULTRA_ARBITRAGE"
        
        # Swap queries
        if any(kw in query_lower for kw in ["swap", "exchange", "trade tokens", "what type of swaps", "what swaps can", "types of swaps"]):
            return "SWAP"
        
        # Portfolio queries
        if any(kw in query_lower for kw in ["portfolio", "balance", "holdings", "my assets", "my tokens"]):
            return "PORTFOLIO"
        
        # Wallet queries
        if any(kw in query_lower for kw in ["wallet", "wallets", "my wallet", "export wallet"]):
            return "WALLET"
        
        # DeFi Protocol comparisons and specific protocols
        defi_protocols = [
            "aave", "compound", "maker", "makerdao", "morpho", "spark", "venus", "benqi",  # Lending
            "uniswap", "sushiswap", "curve", "balancer", "pancakeswap",  # DEXs
            "yearn", "convex", "beefy",  # Yield aggregators
            "lido", "rocket pool", "frax",  # Liquid staking
        ]
        if any(protocol in query_lower for protocol in defi_protocols):
            return "defi_protocol"
        
        # Protocol comparison queries
        if any(kw in query_lower for kw in ["compare", "vs", "versus", "difference between", "which is better"]):
            return "defi_protocol"
        
        # Lending queries (Morpho)
        if any(kw in query_lower for kw in ["lending", "lend", "morpho", "vault", "supply", "deposit assets", "earn yield"]):
            return "LENDING_MORPHO"
        
        # Gas optimizer queries
        if any(kw in query_lower for kw in ["gas", "gas price", "gas cost", "transaction fee", "optimize gas"]):
            return "GAS_OPTIMIZER"
        
        # Risk analyzer queries
        if any(kw in query_lower for kw in ["risk", "safe", "safety", "protocol risk", "tvl", "risk analysis"]):
            return "RISK_ANALYZER"
        
        # General DeFi/crypto
        if any(kw in query_lower for kw in ["defi", "yield", "staking"]):
            return "general_question"
        
        # Default
        return "general_question"
    
    def _format_knowledge_context(self, knowledge_dict: dict) -> str:
        """Format knowledge dictionary as context string."""
        context_parts = []
        
        if "feature_name" in knowledge_dict:
            context_parts.append(f"Feature: {knowledge_dict['feature_name']}")
        
        if "tagline" in knowledge_dict:
            context_parts.append(f"Tagline: {knowledge_dict['tagline']}")
        
        if "description" in knowledge_dict:
            context_parts.append(f"Description: {knowledge_dict['description']}")
        
        if "capability" in knowledge_dict:
            if isinstance(knowledge_dict["capability"], dict):
                cap = knowledge_dict["capability"]
                context_parts.append(f"Capability: {cap.get('name', '')} - {cap.get('description', '')}")
        
        # Format supported aggregators (for swap queries)
        if "supported_aggregators" in knowledge_dict:
            aggregators = knowledge_dict["supported_aggregators"]
            if isinstance(aggregators, list):
                context_parts.append("\n**Supported Aggregators:**")
                for agg in aggregators:
                    if isinstance(agg, dict):
                        name = agg.get("name", "")
                        desc = agg.get("description", "")
                        chains = agg.get("supported_chains", [])
                        if chains:
                            chains_str = ", ".join(chains) if isinstance(chains, list) else str(chains)
                            context_parts.append(f"- {name}: {desc} (Chains: {chains_str})")
                        else:
                            context_parts.append(f"- {name}: {desc}")
        
        # Format supported tokens (for swap queries)
        if "supported_tokens" in knowledge_dict:
            tokens = knowledge_dict["supported_tokens"]
            if isinstance(tokens, dict):
                context_parts.append("\n**Supported Tokens:**")
                if "major_tokens" in tokens:
                    context_parts.append(f"Major tokens: {', '.join(tokens['major_tokens'])}")
                if "total_supported" in tokens:
                    context_parts.append(f"Total: {tokens['total_supported']}")
        
        # Format features
        if "features" in knowledge_dict:
            features = knowledge_dict["features"]
            if isinstance(features, list):
                context_parts.append(f"\n**Features:** {', '.join(features[:5])}")  # First 5 features
        
        if "competitive_advantages" in knowledge_dict:
            advantages = knowledge_dict["competitive_advantages"]
            if isinstance(advantages, list):
                context_parts.append(f"\n**Competitive Advantages:** {', '.join(advantages[:3])}")  # First 3
        
        return "\n".join(context_parts) if context_parts else ""
    
    def _build_messages(
        self,
        message: MessageContent,
        conversation_context: ConversationContext,
        knowledge_context: str = "",
    ) -> list[dict]:
        """Build messages for LLM API."""
        messages = [
            {
                "role": "system",
                "content": self._get_system_prompt(knowledge_context),
            }
        ]
        
        query_lower = message.value.lower().strip()
        
        # Detect direct questions that should be answered immediately without conversation history
        # This includes: "what is X", "X vs Y", "compare X and Y", short questions with "?"
        is_direct_question = (
            query_lower.startswith(("what is", "que es", "qué es", "what are", "que son", "qué son", "explain ", "compare ")) or
            " vs " in query_lower or  # "aave vs compound"
            " versus " in query_lower or  # "aave versus compound"
            "difference between" in query_lower or  # "difference between aave and compound"
            "?" in message.value and len(message.value.split()) < 10
        )
        
        # For direct questions, DON'T include conversation history to avoid topic mixing
        if not is_direct_question:
            # For complex questions, include minimal history (last 1 message only)
            history = conversation_context.last_n_messages(1)
            for msg in history:
                msg_content = msg.get("content", "")
                if msg_content and len(msg_content) > 0:
                    messages.append({
                        "role": msg.get("role", "user"),
                        "content": msg_content,
                    })
        
        # Add current message with explicit instruction to answer directly
        # For comparison queries, add specific instruction to provide detailed comparison
        instruction_suffix = ""
        if " vs " in query_lower or " versus " in query_lower or "compare" in query_lower or "difference between" in query_lower:
            instruction_suffix = "\n\nCRITICAL: This is a COMPARISON question. Provide a detailed comparison with key differences, pros/cons, and use cases. Do NOT ask for clarification - answer the comparison directly."
        elif is_direct_question:
            instruction_suffix = "\n\nCRITICAL: Answer ONLY this question. Do NOT include information about other topics. Respond in the SAME language as the question. Provide a SINGLE response without duplication."
        
        messages.append({
            "role": "user",
            "content": message.value + instruction_suffix,
        })
        
        return messages
    
    def _get_system_prompt(self, knowledge_context: str = "") -> str:
        """Get system prompt for knowledge agent."""
        base_prompt = """You are Anvil's Knowledge Assistant, a specialized educational agent for DeFi and crypto knowledge.

**YOUR ROLE:**
- Provide accurate, educational information about DeFi, crypto, blockchain, and Web3
- Explain Anvil platform features and capabilities
- Answer "what is X?" questions with clear, concise explanations
- Help users understand complex DeFi concepts
- Guide users to appropriate Anvil features when relevant

**CRITICAL: ANSWER ONLY THE CURRENT QUESTION**
- Answer ONLY the user's current question - do NOT include information about topics from previous messages
- If the user asks "What is Anvil?", answer ONLY about Anvil - do NOT include information about NFTs, Bitcoin, or other topics
- Do NOT repeat or summarize previous conversation topics unless explicitly asked
- Focus your response on the specific question being asked in the current message
- Respond in the SAME language as the question (if question is in Spanish, respond in Spanish; if in English, respond in English)
- Do NOT provide the same answer in multiple languages - provide ONE answer in the question's language
- Do NOT duplicate content - provide a SINGLE, focused response without repetition

**KNOWLEDGE AREAS:**
1. **Anvil Platform**
   - Multi-chain wallet management
   - Token swaps via multiple DEX aggregators:
     * **1inch**: Leading DEX aggregator with smart routing across 100+ liquidity sources
     * **Hyperliquid**: High-performance perpetual futures exchange (20,000+ TPS, no gas fees)
     * **UniswapX**: Dutch auction-based swap protocol with automatic routing
     * **LiFi**: Cross-chain bridge and swap aggregator
     * **MoonPay**: Fiat-to-crypto onramps
   - Lending (Morpho vaults) - NOTE: Anvil supports LENDING only, NOT borrowing
   - Portfolio tracking
   - Market analysis and price tracking
   - Automated trading strategies
   - Risk assessment
   - Tax optimization
   - Security auditing
   - Gas optimization
   
   **IMPORTANT: ANVIL FEATURES - LENDING vs BORROWING**
   - Anvil supports LENDING (supply assets to earn yield) through Morpho vaults
   - Anvil does NOT support BORROWING (taking loans against collateral)
   - **CRITICAL: Spanish terminology**
     * DO NOT use "préstamos" (this means borrowing/loans in Spanish)
     * Use "suministro de activos" (supply assets) or "depositar activos" (deposit assets)
     * Example: "suministro de activos para ganar rendimiento" (supply assets to earn yield)
   - **CRITICAL: English terminology**
     * Use "supply assets", "lend assets", "deposit assets" - NOT "borrow" or "take a loan"
     * Example: "supply assets to earn yield" or "lend assets to earn interest"
   - NEVER say Anvil supports "préstamos" (borrowing) - only "suministro de activos" (supply/lending)

2. **DeFi Concepts & Protocols**
   - Decentralized exchanges (DEXs): Uniswap, SushiSwap, Curve, Balancer, PancakeSwap
   - Liquidity pools and AMMs (Automated Market Makers)
   - Yield farming and yield aggregators (Yearn, Convex, Beefy)
   - Staking and liquid staking (Lido, Rocket Pool, Frax)
   - **Lending/Borrowing Protocols**: Aave, Compound, MakerDAO, Morpho, Spark, Venus, Benqi
     * Aave: Leading lending protocol with flash loans, multi-chain support
     * Compound: Pioneer DeFi lending protocol with cTokens
     * MakerDAO: DAI stablecoin and CDP-based lending
     * Morpho: Peer-to-peer lending optimization layer
   - Stablecoins (USDC, USDT, DAI, FRAX, LUSD)
   - Governance tokens
   - DAOs (Decentralized Autonomous Organizations)
   - NFTs (Non-Fungible Tokens)
   - NFT marketplaces (OpenSea, Blur, Magic Eden, etc.)
   - NFT collections and art
   - Protocol comparisons and analysis (e.g., "Aave vs Compound", "which protocol is better")

3. **Cryptocurrencies & Tokens**
   - Bitcoin (BTC)
   - Ethereum (ETH)
   - Stablecoins (USDC, USDT, DAI)
   - Layer 2 tokens
   - DeFi tokens

4. **Blockchain Technology**
   - How blockchains work
   - Smart contracts
   - Gas fees
   - Layer 2 solutions
   - Cross-chain bridges

**RESPONSE STYLE:**
- Clear and educational
- Use examples when helpful
- Break down complex concepts
- Be concise but thorough
- Use bullet points for lists
- Include relevant Anvil features when applicable

**CRITICAL: NEVER ASK FOR CLARIFICATION ON DeFi TOPICS**
- If user says "aave vs compound" → PROVIDE THE COMPARISON, don't ask "what would you like to know?"
- If user says "compare X and Y" → PROVIDE THE COMPARISON directly
- If user mentions ANY DeFi protocol or concept → ANSWER with information, don't ask for more details
- Short queries like "X vs Y" or "what is X" are COMPLETE questions - answer them directly
- NEVER respond with "What would you like to know about DeFi or crypto?" for DeFi-related queries

**CRITICAL: ANVIL IS A REAL PLATFORM**
- Anvil is a REAL, LIVE DeFi platform - NOT simulated
- DO NOT use words like "simulated", "simulation", "mock", or "hypothetical"
- Use language like "Anvil provides", "On Anvil you can", "Anvil's platform offers"

**OFF-TOPIC HANDLING:**
- If asked about topics NOT related to DeFi, crypto, blockchain, Web3, NFTs, or Anvil:
  * Politely decline: "I'm specialized in DeFi and crypto knowledge. I can't help with [topic], but I can explain DeFi concepts, tokens, protocols, NFTs, and Anvil features."
  * DO NOT provide information about cooking, recipes, general knowledge, or non-crypto topics
  * Redirect to DeFi/crypto topics: "What would you like to know about DeFi, crypto, or NFTs?"

**CREATIVE REQUESTS (poems, stories about crypto):**
- If asked to write poems, stories, or creative content about crypto/DeFi topics:
  * You CAN provide creative content about crypto topics! Poems about gas fees, Bitcoin analogies, Ethereum stories are all ALLOWED.
  * If you have real data available (gas prices, token prices, APY rates), incorporate it into your creative writing.
  * Be creative, engaging, and accurate about the crypto facts included.
  
**NFTs ARE ON-TOPIC:**
- NFTs (Non-Fungible Tokens) are part of crypto/Web3 and should be answered
- Questions about NFTs, NFT marketplaces, NFT art, NFT collections are all valid
- Provide educational information about NFTs, how they work, where to buy them, etc.

**KNOWLEDGE BASE CONTEXT:**
"""
        
        if knowledge_context:
            base_prompt += f"""
The following information from Anvil's knowledge base is relevant to this query:

{knowledge_context}

Use this information to provide accurate, detailed responses about Anvil features and capabilities.
"""
        
        base_prompt += """
**EXAMPLES:**

User: "What is Anvil?"
You: "Anvil is a comprehensive DeFi platform that provides multi-chain wallet management, token swaps, lending (supply assets to earn yield), portfolio tracking, and advanced features like market analysis and automated trading. [Detailed explanation...]"

User: "What type of swaps can I make?"
You: "On Anvil, you can make token swaps through multiple DEX aggregators: 1inch (leading aggregator with 100+ liquidity sources), Hyperliquid (high-performance exchange, 20,000+ TPS, no gas fees), UniswapX (Dutch auction-based routing), and LiFi (cross-chain swaps). Anvil supports 100+ tokens including BTC, ETH, USDC, USDT, DAI, SOL, MATIC, and more across Ethereum, Base, Arbitrum, Polygon, and Optimism chains."

User: "¿Qué es Anvil?" (Spanish)
You: "Anvil es una plataforma DeFi integral que proporciona gestión de billeteras multi-cadena, intercambios de tokens, suministro de activos (para ganar rendimiento), seguimiento de cartera y características avanzadas como análisis de mercado y comercio automatizado. [Detailed explanation in Spanish...]"
Note: Use "suministro de activos" NOT "préstamos" (préstamos means borrowing, which Anvil does NOT support)

User: "What is yield farming?"
You: "Yield farming is a DeFi strategy where users provide liquidity to protocols in exchange for rewards. [Detailed explanation with examples...]"

User: "What is BTC?"
You: "BTC (Bitcoin) is the first and largest cryptocurrency. [Detailed explanation...]"

User: "What is an NFT?"
You: "An NFT (Non-Fungible Token) is a unique digital token that represents ownership of a digital asset. Unlike cryptocurrencies like Bitcoin where each unit is identical, each NFT is unique and cannot be directly exchanged for another NFT. [Detailed explanation with examples...]"

User: "Where can I buy NFTs?"
You: "You can buy NFTs on various marketplaces like OpenSea, Blur, Magic Eden, and others. [Detailed explanation with marketplace information...]"

User: "Compare Aave vs Compound"
You: "Aave and Compound are both leading DeFi lending protocols, but they have key differences:

**Aave:**
- Multi-chain support (Ethereum, Polygon, Arbitrum, Optimism, Avalanche, etc.)
- Flash loans (uncollateralized instant loans within one transaction)
- Variable and stable interest rates
- Larger TVL (~$10B+)
- More advanced features (credit delegation, isolation mode)

**Compound:**
- Pioneer in DeFi lending (launched 2018)
- cToken model (interest-bearing tokens)
- Primarily on Ethereum mainnet
- Simpler, battle-tested architecture
- COMP governance token

**Which to choose?** Aave offers more features and multi-chain access. Compound is simpler and highly battle-tested. Both are reputable protocols."

User: "What is the difference between Uniswap and SushiSwap?"
You: "Uniswap and SushiSwap are both AMM-based DEXs with similar mechanics but different approaches... [Detailed comparison...]"

**CRITICAL: NO TOPIC MIXING**
- If user asks "What is Anvil?", answer ONLY about Anvil - do NOT add information about NFTs, Bitcoin, or other topics
- If user asks "What is Bitcoin?", answer ONLY about Bitcoin - do NOT add information about Anvil, NFTs, or other topics
- Each question should be answered independently - do NOT combine multiple topics in one response unless explicitly asked

Keep responses educational, accurate, and helpful. If you don't know something, say so and offer to help with related topics.
"""
        
        return base_prompt
