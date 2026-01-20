"""
Chat Agent - General conversation agent.
"""

import time
from typing import Any

from app.domain.enums.agent_type import AgentType
from app.domain.value_objects.conversation_id import ConversationId
from app.domain.value_objects.message_content import MessageContent
from app.domain.value_objects.agent_squad.conversation_context import ConversationContext
from app.domain.ports.agent_squad.agent_gateway import AgentGateway, AgentResponse
from app.domain.ports.agent_squad.llm_client_gateway import LLMClientGateway


class ChatAgent:
    """
    Chat Agent implementation.
    
    Implements: AgentGateway
    
    Purpose: General conversation, fallback agent
    
    Capabilities:
    - Answer general questions
    - Provide DeFi information
    - Guide users to specialist agents
    - Maintain friendly, helpful tone
    
    Model: gemini-2.0-flash (Vertex AI, fast, cost-effective)
    Temperature: 0.7 (balanced creativity)
    """
    
    def __init__(
        self,
        llm_client: LLMClientGateway,  # Can be Vertex AI or DeepInfra (OpenAI removed)
        model: str = "gemini-2.0-flash",  # Vertex AI model (default)
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ):
        """
        Initialize chat agent.
        
        Args:
            llm_client: LLM client gateway (Vertex AI or DeepInfra)
            model: Model to use (default: gemini-2.0-flash)
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
        
        # Check if this is a restricted feature query (for guest users)
        is_restricted_query = self._is_restricted_feature_query(message.value)
        
        if is_restricted_query:
            # Use custom messages directly (no LLM call needed)
            restricted_feature = self._detect_restricted_feature(message.value)
            custom_message = self._get_custom_message(restricted_feature, conversation_context)
            
            # Return response directly with custom message
            from datetime import datetime, UTC
            from app.domain.value_objects.chat.source_info import SourceInfo, SourceType
            
            fetched_at = datetime.now(UTC)
            provider = "Vertex AI" if "gemini" in self._model.lower() else "DeepInfra"
            
            sources = [
                SourceInfo(
                    source_type=SourceType.LLM,
                    source_name=self._model,
                    citation_text=f"Custom registration message for {restricted_feature}",
                    fetched_at=fetched_at,
                    provider=provider,
                    metadata={"model": self._model, "restricted_feature": restricted_feature},
                )
            ]
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            return AgentResponse(
                content=custom_message,
                agent_type=self.agent_type,
                tools_used=["auth_detection"],
                sources=sources,
                metadata={
                    "tokens_used": 0,  # No LLM call
                    "latency_ms": latency_ms,
                    "model": self._model,
                    "restricted_feature": restricted_feature,
                    "provider": "vertex_ai" if "gemini" in self._model.lower() else "deepinfra",
                },
            )
        
        # Detect if this is an aggregation task (multiple agent responses to summarize)
        is_aggregation = (
            "aggregate" in message.value.lower() or
            "agent response" in message.value.lower() or
            len(message.value) > 2000  # Long messages likely contain multiple agent responses
        )
        
        # Use higher token limit for aggregation tasks
        max_tokens = self._max_tokens * 3 if is_aggregation else self._max_tokens  # 3000 for aggregation, 1000 for normal
        
        # Call OpenAI
        response = await self._llm_client.chat(
            messages=messages,
            model=self._model,
            temperature=self._temperature,
            max_tokens=max_tokens,
        )
        
        # Calculate latency
        latency_ms = int((time.time() - start_time) * 1000)
        
        # Add LLM source
        from datetime import datetime, UTC
        from app.domain.value_objects.chat.source_info import SourceInfo, SourceType
        
        fetched_at = datetime.now(UTC)
        model_name = response.get("model", "Unknown")
        provider = "Vertex AI" if "gemini" in model_name.lower() else "DeepInfra"
        
        sources = [
            SourceInfo(
                source_type=SourceType.LLM,
                source_name=model_name,
                citation_text=f"Generated by {model_name}",
                fetched_at=fetched_at,
                provider=provider,
                metadata={"model": model_name},
            )
        ]
        
        # Build response
        return AgentResponse(
            content=response["content"],
            agent_type=self.agent_type,
            tools_used=[],  # Chat agent doesn't use external tools
            sources=sources,
            metadata={
                "tokens_used": response.get("tokens_used"),
                "latency_ms": latency_ms,
                "model": response.get("model"),
                "finish_reason": response.get("finish_reason"),
                "provider": response.get("provider", provider),  # Include provider from LLM response
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
        
        # Check if this is an aggregation task (message contains agent responses)
        # If message contains "Agent Response:" or similar patterns, it's aggregation
        is_aggregation = (
            "agent response" in message.value.lower() or
            "from hunter ai" in message.value.lower() or
            "from research" in message.value.lower() or
            "from risk analyzer" in message.value.lower() or
            len(message.value) > 5000  # Likely contains multiple agent responses
        )
        
        if is_aggregation:
            # For aggregation, add special instruction
            messages.append({
                "role": "user",
                "content": f"""You are aggregating responses from multiple specialist agents. 

IMPORTANT INSTRUCTIONS:
1. **PRESERVE REAL-TIME DATA**: If you see sections marked "**REAL-TIME APY DATA FROM DEFILLAMA:**" or "**PROTOCOL DATA FROM DEFILLAMA:**", you MUST include this data prominently in your response. DO NOT remove or summarize this real-time data - it is the PRIMARY source of accurate information.
2. **FILTER OUT AUTHENTICATION MESSAGES**: If you see messages like "Account Required", "Wallet Required", or registration prompts, DO NOT include them in the final response UNLESS the user explicitly asked about authentication requirements. These are error messages, not answers to informational queries.
3. **PRESERVE SPECIFIC DETAILS**: If responses mention specific aggregators (1inch, Hyperliquid, UniswapX, LiFi), protocols, chains, or features, include ALL of them in your summary. Do NOT generalize or remove specific names.
4. **Deduplicate**: Remove repeated disclaimers, explanations, and general facts (but NOT real-time data from APIs or specific feature names)
5. **Summarize**: Create a single, coherent response (not a concatenation), but preserve all specific numbers, APY values, TVL data, protocol rankings, aggregator names, and token names
6. **Remove redundancy**: If multiple agents provided the same general information, mention it only once (but keep all unique data points and specific names)
7. **Structure**: Organize information logically - start with real-time data if available, then specific features/aggregators, then general recommendations
8. **Single disclaimer**: Include ONE "not financial advice" disclaimer at the end
9. **No repetition**: Do NOT repeat the same general information multiple times, but DO include all specific data points, aggregator names, and feature details
10. **Clean flow**: Use smooth transitions, avoid multiple "Okay, let's..." openings
11. **Answer the question**: Make sure your response actually answers the user's question. If the user asked "what type of swaps can I make?", provide information about swap types (1inch, Hyperliquid, UniswapX, LiFi), NOT authentication prompts.
12. **Complete summary**: Your summary should be comprehensive - include information from ALL agents, not just one. If one agent provided swap types and another provided prices, include BOTH in your response.

Agent Responses to Aggregate:
{message.value}

Create a single, well-structured response that combines all unique insights without repetition, but ALWAYS preserve and prominently display any real-time data from DeFiLlama (APY values, TVL data, protocol rankings). FILTER OUT any authentication/registration messages unless the user explicitly asked about account requirements.""",
            })
        else:
            # Normal conversation flow
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
    
    def _is_restricted_feature_query(self, message: str) -> bool:
        """Check if message is asking about a restricted feature."""
        message_lower = message.lower()
        restricted_keywords = [
            # Balance
            "my balance", "what's my balance", "check my balance", "how much do i have", "wallet balance",
            # Activity
            "my transactions", "transaction history", "show my activity", "recent activity", "my activity",
            # Receive
            "my address", "wallet address", "receive crypto", "deposit address", "QR code", "i want to receive",
            # Buy
            "buy crypto", "purchase bitcoin", "buy with card", "how to buy ETH", "i want to buy",
            # Send
            "send crypto", "transfer tokens", "send to wallet", "send to friend", "i want to send",
            # Portfolio
            "my portfolio", "my holdings", "list my tokens", "what tokens do i have", "show my holdings",
        ]
        return any(kw in message_lower for kw in restricted_keywords)
    
    def _detect_restricted_feature(self, message: str) -> str:
        """Detect which restricted feature user is asking about."""
        message_lower = message.lower()
        
        # Priority order (most specific first)
        if any(kw in message_lower for kw in ["my balance", "what's my balance", "check my balance", "how much do i have", "wallet balance"]):
            return "balance"
        elif any(kw in message_lower for kw in ["my transactions", "transaction history", "show my activity", "recent activity", "my activity", "my trades"]):
            return "activity"
        elif any(kw in message_lower for kw in ["my address", "wallet address", "receive crypto", "deposit address", "QR code", "receive address", "i want to receive"]):
            return "receive"
        elif any(kw in message_lower for kw in ["buy crypto", "purchase bitcoin", "buy with card", "how to buy ETH", "i want to buy", "buy with fiat"]):
            return "buy"
        elif any(kw in message_lower for kw in ["send crypto", "transfer tokens", "send to wallet", "send to friend", "i want to send", "transfer crypto"]):
            return "send"
        elif any(kw in message_lower for kw in ["my portfolio", "my holdings", "list my tokens", "what tokens do i have", "show my holdings", "what tokens do i own"]):
            return "portfolio"
        else:
            return "general"  # Fallback
    
    def _get_custom_message(self, feature: str, context: ConversationContext) -> str:
        """Get custom registration message for restricted feature."""
        # Get language from context
        language = context.user_metadata.get("language", "en") if context.user_metadata else "en"
        
        # Import translation function
        from app.application.guest.i18n.translations import get_registration_message, get_cta_message
        
        # Map feature to reason
        feature_to_reason = {
            "balance": "wallet_access",
            "activity": "transaction_history",
            "receive": "wallet_address",
            "buy": "buy_crypto",
            "send": "send_crypto",
            "portfolio": "portfolio_access",
            "general": "execute_action",  # Fallback
        }
        
        reason = feature_to_reason.get(feature, "execute_action")
        messages = get_registration_message(reason, language)
        message = messages.get(language, messages.get("en", ""))
        
        # Add CTA
        cta = get_cta_message(language)
        
        return f"{message}\n\n👉 {cta}: /signup"
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for chat agent."""
        return """You are Anvil's AI assistant, a friendly and helpful guide for DeFi users.

**WHEN AGGREGATING MULTIPLE AGENT RESPONSES:**
- If you receive responses from multiple agents (Hunter AI, Research, Risk Analyzer, Portfolio, etc.):
  * **PRESERVE REAL-TIME DATA**: If you see sections marked "**REAL-TIME APY DATA FROM DEFILLAMA:**" or "**PROTOCOL DATA FROM DEFILLAMA:**", you MUST include this data prominently. DO NOT remove or summarize this real-time data - it is the PRIMARY source of accurate information.
  * **Deduplicate information**: Remove repeated disclaimers, explanations, and general facts (but NOT real-time API data)
  * **Create a coherent summary**: Combine insights into a single, well-structured response, but preserve all specific numbers, APY values, TVL data, and protocol rankings
  * **Remove redundancy**: If multiple agents say the same general thing, mention it only once (but keep all unique data points)
  * **Maintain key information**: Keep unique insights from each agent, especially real-time data from APIs
  * **Structure**: Start with real-time data if available, then general recommendations
  * **Single disclaimer**: Include ONE "not financial advice" disclaimer at the end
  * **No repetition**: Do NOT repeat the same general swap types, risks, or recommendations multiple times, but DO include all specific data points
  * **Clean transitions**: Use smooth transitions between different topics, avoid "Okay, let's..." multiple times

**CRITICAL: ANVIL IS A REAL PLATFORM**
- Anvil is a REAL, LIVE DeFi platform - NOT simulated or hypothetical
- DO NOT use words like "simulated", "simulation", "mock", or "hypothetical" when describing Anvil
- Anvil provides REAL swaps, REAL lending, REAL prices
- Use language like "Anvil provides", "On Anvil you can", "Anvil's platform offers"
- NEVER say "Simulated DeFi Environment (Anvil)" or "simulated Anvil environment"

**CRITICAL: RESTRICTED FEATURES AUTHENTICATION REQUIREMENT**
These features require user authentication - use the EXACT custom messages below:

**PORTFOLIO/HOLDINGS:**
- If asked about "my portfolio", "my holdings", "list my tokens", etc.:
  * Use EXACT message: "💼 **Unlock Your Complete Portfolio Dashboard**\n\nTrack all your DeFi positions in one place! With a free account, you'll get:\n\n✨ **Real-time Portfolio Tracking**\n• View all your assets across multiple chains\n• Monitor your total portfolio value\n• Track performance over time\n\n📊 **Advanced Analytics**\n• Asset allocation breakdown\n• Profit/loss analysis\n• Risk exposure metrics\n\n🔔 **Smart Alerts**\n• Price movement notifications\n• Liquidation risk warnings\n• Yield opportunity alerts\n\n🎯 **AI-Powered Insights**\n• Portfolio optimization suggestions\n• Rebalancing recommendations\n• Tax optimization strategies\n\n**It's free and takes less than 30 seconds to sign up!**"

**BALANCE:**
- If asked about "my balance", "what's my balance", "check my balance", etc.:
  * Use EXACT message: "🔐 **Wallet Access Required**\n\nTo view your balance and wallet holdings, you need to create an account and connect your wallet.\n\nSign up to:\n• View real-time balances\n• Track your holdings\n• Monitor your positions"

**ACTIVITY/TRANSACTIONS:**
- If asked about "my transactions", "transaction history", "show my activity", etc.:
  * Use EXACT message: "🔐 **Account Required**\n\nTo view your transaction history and past activity, you need to create an account.\n\nSign up to:\n• View all transactions\n• Track your trading history\n• Export transaction records"

**RECEIVE/WALLET ADDRESS:**
- If asked about "my address", "wallet address", "receive crypto", "QR code", etc.:
  * Use EXACT message: "🔐 **Wallet Required**\n\nTo get your deposit address, you need to create an account and set up your wallet.\n\nSign up to:\n• Get your personal wallet address\n• Receive crypto deposits\n• Manage multiple chains"

**BUY CRYPTO:**
- If asked about "buy crypto", "purchase bitcoin", "buy with card", etc.:
  * Use EXACT message: "🔐 **Account Required**\n\nTo buy crypto with fiat, you need to create an account and complete verification.\n\nSign up to:\n• Buy crypto with card or bank transfer\n• Access multiple on-ramp providers\n• Get the best rates"

**SEND/TRANSFER:**
- If asked about "send crypto", "transfer tokens", "send to wallet", etc.:
  * Use EXACT message: "🔐 **Wallet Required**\n\nTo send crypto to another wallet, you need to create an account and connect your wallet.\n\nSign up to:\n• Send tokens to any address\n• Transfer across multiple chains\n• Track your transfers"

**GENERAL RULE:**
- Use the EXACT messages above - do not modify or paraphrase them
- DO NOT attempt to retrieve wallet data for unauthenticated/guest users
- DO NOT ask for manual input - direct them to sign in instead
- Only authenticated users can access wallet-related features from Anvil

**ANVIL KNOWLEDGE BASE:**
Anvil is a comprehensive REAL DeFi platform that provides:
- Multi-chain wallet management (Ethereum, Base, Arbitrum, Optimism, Polygon, Solana)
- Token swaps via multiple DEX aggregators:
  * **1inch**: Best rates across multiple DEXs (Uniswap, SushiSwap, Curve, etc.)
  * **LiFi**: Cross-chain swaps and bridges
  * **Hyperliquid**: Perpetual swaps and derivatives
  * **MoonPay**: Fiat-to-crypto onramps
- Lending (supply assets to earn yield) through Morpho vaults
  * **NOTE**: Anvil supports LENDING only (supply assets to earn APY), NOT borrowing
  * Users can supply assets like USDC, ETH, etc. to Morpho vaults to earn yield
  * Anvil does NOT support borrowing (taking loans against collateral)
- Portfolio tracking and analytics
- Market sentiment analysis (Hunter AI)
- Automated trading strategies (ULTRA)
- Risk assessment and portfolio optimization
- Tax optimization tools
- Security auditing
- Gas optimization

**SWAP TYPES IN ANVIL:**
1. **Standard Token Swaps**: Swap any ERC-20 token for another via 1inch aggregator
   - Supports all major tokens (ETH, USDC, DAI, WBTC, etc.)
   - Automatic route optimization for best prices
   - Slippage protection
   
2. **Cross-Chain Swaps**: Bridge and swap tokens across chains via LiFi
   - Ethereum ↔ Base, Arbitrum, Optimism, Polygon
   - Automatic bridge selection for best rates
   
3. **Perpetual Swaps**: Trade perpetual futures via Hyperliquid
   - Long/short positions with leverage
   - No expiration dates
   
4. **Fiat-to-Crypto Swaps**: Buy crypto with fiat via MoonPay
   - Credit card, bank transfer, Apple Pay
   - Instant settlement

**Your capabilities:**
- Answer general questions about DeFi, crypto, Web3, and Anvil platform
- Provide educational information about tokens, protocols, and DeFi concepts
- Explain Anvil features and how to use them
- Guide users to specialist agents when needed

**CRITICAL: PROVIDE SPECIFIC INFORMATION**
- When asked about swaps, prices, or lending rates, provide SPECIFIC actionable information
- DO NOT say "need more information" or "hypothetical" - provide real examples and data
- Include specific protocol names (1inch, LiFi, Morpho, Aave) with actual features
- Mention real APY ranges when discussing lending (e.g., "USDC lending typically offers 3-5% APY")
- When discussing lending, only mention supplying/lending assets to earn yield - NEVER mention borrowing
- Provide concrete swap examples (e.g., "Swap ETH to USDC via 1inch aggregator")

**CRITICAL: WHEN AGGREGATING MULTIPLE AGENT RESPONSES**
- You MUST include ALL important information from all agents
- DO NOT truncate or cut off the response - provide complete information
- Include ALL prices, APY numbers, and specific data from all agents
- If you see price data (e.g., "BTC: $92,506"), you MUST include it in your final response
- If you see APY data (e.g., "4.8% APY"), you MUST include it in your final response
- Complete your response - do not end mid-sentence or with incomplete information
- If the response is getting long, prioritize including all specific data (prices, APY, numbers) over general explanations

**When to refer to specialists:**
- Price queries, market sentiment → "Let me check current prices with our Hunter AI agent"
- Token swaps, transactions → "Let me connect you with our Execution agent"
- Risk analysis → "Our Risk Analyzer agent can help with that"
- Portfolio optimization → "Our Portfolio agent specializes in this"
- Deep research → "Our Research agent can dive deep into this"

**Shortcuts/Commands:**
Users can use shortcuts like:
- "Swap BTC to ETH" → Token swap
- "Show my portfolio" → Portfolio view
- "Lend USDC" or "Supply USDC" → Lending operations (supply assets to earn yield)
- "What's my balance?" → Balance check

**CRITICAL: LENDING vs BORROWING**
- Anvil supports LENDING: Users can supply assets (USDC, ETH, etc.) to Morpho vaults to earn yield/APY
- Anvil does NOT support BORROWING: Users cannot take loans against collateral
- When users ask about "borrowing" or "taking a loan", explain that Anvil supports lending (supply assets) but not borrowing
- Use terms like "supply assets", "lend assets", "deposit to earn yield" - NOT "borrow" or "take a loan"

Keep responses:
- Clear and concise
- Friendly and professional
- Educational when helpful
- Honest about limitations
- Include Anvil-specific information when relevant

**CRITICAL: OFF-TOPIC QUERY HANDLING**
- If the user asks about topics NOT related to DeFi, crypto, blockchain, Web3, or Anvil platform:
  * Politely decline: "I'm specialized in DeFi and crypto assistance. I can't help with [topic], but I can help you with swaps, staking, lending, and other DeFi operations."
  * DO NOT provide information about cooking, recipes, general knowledge, or non-crypto topics
  * DO NOT hallucinate or make up information to answer off-topic questions
  * Redirect to DeFi topics: "What would you like to know about DeFi or crypto?"
- Examples of OFF-TOPIC queries to decline:
  * Cooking recipes, baking instructions
  * General knowledge questions (history, science, etc.)
  * Non-crypto financial advice
  * Personal advice unrelated to DeFi

If unsure, say so and offer to connect them with a specialist.
"""
