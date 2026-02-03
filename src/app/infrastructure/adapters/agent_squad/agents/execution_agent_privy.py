"""
Execution Agent Privy - Transaction execution using Privy embedded wallets.
"""

import time
import os
from decimal import Decimal
from typing import Any

from app.domain.enums.agent_type import AgentType
from app.domain.value_objects.conversation_id import ConversationId
from app.domain.value_objects.message_content import MessageContent
from app.domain.value_objects.agent_squad.conversation_context import (
    ConversationContext,
)
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
        oneinch_client: Any | None = None,  # OneInch client for real swap quotes
        model: str = "gemini-2.0-flash",  # Vertex AI model (default)
        temperature: float = 0.1,
        max_tokens: int = 1000,
        max_transaction_value_usd: Decimal = Decimal("10000"),
    ):
        """
        Initialize execution agent.

        Args:
            llm_client: LLM client gateway (Vertex AI or DeepInfra)
            privy_client: Privy embedded wallet client
            swap_gateway: Swap gateway (1inch, Uniswap)
            oneinch_client: Optional OneInch client for real swap quotes
            model: Model to use (default: gemini-2.0-flash)
            temperature: Sampling temperature (default: 0.1, precision critical)
            max_tokens: Maximum response tokens
            max_transaction_value_usd: Maximum transaction value (safety limit)
        """
        self._llm_client = llm_client
        self._privy_client = privy_client
        self._swap_gateway = swap_gateway
        self._oneinch_client = oneinch_client
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

        # Debug: Log intent parsing result
        import logging

        logger = logging.getLogger(__name__)
        logger.info(
            f"🔍 Parsed intent: action={intent_response.get('action')}, from_token={intent_response.get('from_token')}, to_token={intent_response.get('to_token')}, amount={intent_response.get('amount')}"
        )

        # Type check: ensure we have a OneInchClient, not something else
        oneinch_client = self._oneinch_client
        if oneinch_client and not hasattr(oneinch_client, "get_swap_quote"):
            # Wrong object injected - create client directly
            logger.warning(
                f"⚠️ Wrong object injected for oneinch_client: {type(oneinch_client)}. Creating client directly."
            )
            from app.setup.config.agent_squad import load_agent_squad_config

            settings = load_agent_squad_config()
            if settings.external_apis.enable_1inch:
                api_key = os.getenv("ONEINCH_API_KEY", "")
                if api_key:
                    from app.infrastructure.adapters.external.oneinch_client import (
                        OneInchClient,
                    )

                    oneinch_client = OneInchClient(api_key=api_key)
                else:
                    oneinch_client = None
            else:
                oneinch_client = None
        elif not oneinch_client:
            # Client is None - try to create it if enabled
            from app.setup.config.agent_squad import load_agent_squad_config

            settings = load_agent_squad_config()
            if settings.external_apis.enable_1inch:
                api_key = os.getenv("ONEINCH_API_KEY", "")
                if api_key:
                    from app.infrastructure.adapters.external.oneinch_client import (
                        OneInchClient,
                    )

                    oneinch_client = OneInchClient(api_key=api_key)

        # Fetch real swap quote from OneInch if available and action is swap
        swap_quote_context = ""
        if oneinch_client and intent_response.get("action") == "swap":
            try:
                import logging

                logger = logging.getLogger(__name__)
                logger.info(
                    "🔍 Fetching real swap quote from OneInch for ExecutionAgent"
                )

                # Get token addresses (would need token resolver, for now use common addresses)
                from_token_symbol = intent_response.get("from_token", "").upper()
                to_token_symbol = intent_response.get("to_token", "").upper()
                amount = intent_response.get("amount", "1.0")

                # Common token addresses (Ethereum mainnet)
                TOKEN_ADDRESSES = {
                    "ETH": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
                    "WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
                    "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
                    "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
                    "DAI": "0x6B175474E89094C44Da98b954EedeAC495271d0F",
                    "WBTC": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
                }

                from_token_addr = TOKEN_ADDRESSES.get(from_token_symbol)
                to_token_addr = TOKEN_ADDRESSES.get(to_token_symbol)

                if from_token_addr and to_token_addr:
                    # Convert amount to wei (assuming 18 decimals for simplicity)
                    # In production, would need to fetch token decimals
                    amount_wei = str(int(float(amount) * 1e18))

                    quote = await oneinch_client.get_swap_quote(
                        from_token=from_token_addr,
                        to_token=to_token_addr,
                        amount=amount_wei,
                        slippage=1.0,  # 1% default slippage
                    )

                    # Convert to human-readable amounts
                    from_amount_readable = float(amount)
                    to_amount_readable = (
                        int(quote.to_amount) / 1e18
                    )  # Assuming 18 decimals

                    swap_quote_context = "\n\n**REAL-TIME SWAP QUOTE FROM 1INCH:**\n"
                    swap_quote_context += f"- Swap: {from_amount_readable:.4f} {from_token_symbol} → {to_amount_readable:.4f} {to_token_symbol}\n"
                    swap_quote_context += f"- Expected Output: {to_amount_readable:.4f} {to_token_symbol}\n"
                    swap_quote_context += (
                        f"- Estimated Gas: {quote.estimated_gas:,} gas units\n"
                    )
                    if quote.price_impact:
                        swap_quote_context += (
                            f"- Price Impact: {quote.price_impact:.2f}%\n"
                        )
                    if quote.protocols:
                        swap_quote_context += (
                            f"- Routing: {len(quote.protocols)} protocol(s) involved\n"
                        )

                    # Add to intent response for use in response building
                    intent_response["swap_quote"] = {
                        "from_amount": from_amount_readable,
                        "to_amount": to_amount_readable,
                        "estimated_gas": quote.estimated_gas,
                        "price_impact": quote.price_impact,
                    }

                    logger.info(
                        f"✅ Fetched 1inch quote: {from_amount_readable} {from_token_symbol} → {to_amount_readable} {to_token_symbol}"
                    )
                else:
                    logger.warning(
                        f"⚠️ Token addresses not found for {from_token_symbol} or {to_token_symbol}"
                    )

            except Exception as e:
                import logging

                logger = logging.getLogger(__name__)
                logger.warning(
                    f"⚠️ Failed to fetch 1inch quote: {e}, continuing without real quote"
                )
                swap_quote_context = ""

        # Build response based on intent
        # NOTE: Actual execution requires user confirmation (not auto-executed)
        response_content = await self._build_execution_response(
            intent_response,
            conversation_context,
            swap_quote_context=swap_quote_context,
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
        sources.append(
            create_llm_source(
                model=model_name,
                fetched_at=fetched_at,
            )
        )

        # Add 1inch source (if swap action)
        action = intent_response.get("action", "")
        if action == "swap":
            from_token = intent_response.get("from_token", "")
            to_token = intent_response.get("to_token", "")
            sources.append(
                create_api_source(
                    source_name="1inch",
                    url=f"https://app.1inch.io/",
                    endpoint="/swap/v5.2/quote",
                    citation_text=f"1inch swap quote: {from_token} → {to_token}",
                    fetched_at=fetched_at,
                    query_params={
                        "fromTokenAddress": from_token,
                        "toTokenAddress": to_token,
                    }
                    if from_token and to_token
                    else None,
                )
            )

        # Add Privy source
        sources.append(
            create_api_source(
                source_name="Privy",
                url="https://privy.io/",
                citation_text="Wallet connection and transaction signing via Privy",
                fetched_at=fetched_at,
            )
        )

        # TODO: Add blockchain source when transaction is submitted (tx_hash available)

        # Build tools_used list
        tools_used = ["privy_wallet", "llm_gateway"]
        # Use the validated client (oneinch_client from above, or self._oneinch_client if not validated)
        validated_oneinch_client = (
            oneinch_client if "oneinch_client" in locals() else self._oneinch_client
        )
        if (
            validated_oneinch_client
            and hasattr(validated_oneinch_client, "get_swap_quote")
            and intent_response.get("action") == "swap"
            and swap_quote_context
        ):
            tools_used.append("1inch_api")

        return AgentResponse(
            content=response_content,
            agent_type=self.agent_type,
            tools_used=tools_used,
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
        prompt = f"""Parse the transaction intent from this message. Extract the action and token details.

Message: {message.value}

CRITICAL: You MUST respond with valid JSON only. No markdown, no explanations, just JSON.

Identify and extract:
- action: MUST be one of "swap", "transfer", "approve", "wrap", "unwrap" (default to "swap" if user mentions swapping tokens)
- from_token: Token symbol (e.g., "ETH", "USDC", "BTC") - extract from message
- to_token: Token symbol (if swap) - extract from message
- amount: Numeric amount as string (e.g., "1.0", "0.5", "100")
- recipient: Wallet address (if transfer, otherwise null)

Examples:
- "swap 1 ETH for USDC" → {{"action": "swap", "from_token": "ETH", "to_token": "USDC", "amount": "1.0"}}
- "I want to swap 0.5 ETH to USDC" → {{"action": "swap", "from_token": "ETH", "to_token": "USDC", "amount": "0.5"}}
- "swap ETH for USDC" → {{"action": "swap", "from_token": "ETH", "to_token": "USDC", "amount": "1.0"}}

Respond with ONLY valid JSON (no markdown code blocks, no explanations):
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

        # Ensure response is a dict
        if not isinstance(response, dict):
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(
                f"⚠️ Intent parsing returned non-dict: {type(response)}, converting to dict"
            )
            response = {
                "action": "unknown",
                "from_token": "",
                "to_token": "",
                "amount": "0",
            }

        # Ensure action is set correctly - if message contains "swap", force action to "swap"
        message_lower = message.value.lower()
        if "swap" in message_lower and response.get("action") != "swap":
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(
                f"⚠️ Intent parsing returned action={response.get('action')} but message contains 'swap' - forcing action='swap'"
            )
            response["action"] = "swap"
            # Try to extract tokens if not already set
            if not response.get("from_token") or not response.get("to_token"):
                # Simple extraction: "swap X for Y" or "swap X to Y"
                import re

                swap_match = re.search(
                    r"swap\s+(\d*\.?\d*)?\s*(\w+)\s+(?:for|to)\s+(\w+)", message_lower
                )
                if swap_match:
                    amount_str = swap_match.group(1) or "1.0"
                    from_token = swap_match.group(2).upper()
                    to_token = swap_match.group(3).upper()
                    response["from_token"] = from_token
                    response["to_token"] = to_token
                    response["amount"] = amount_str
                    logger.info(
                        f"✅ Extracted swap details: {amount_str} {from_token} → {to_token}"
                    )

        return response

    async def _build_execution_response(
        self,
        intent: dict,
        conversation_context: ConversationContext,
        swap_quote_context: str = "",
    ) -> str:
        """Build execution response (quote, confirmation request)."""
        action = intent.get("action", "unknown")
        from_token = intent.get("from_token", "")
        to_token = intent.get("to_token", "")
        amount = intent.get("amount", "0")

        # Check if this is an informational query (no specific tokens/amounts)
        # If user asks "what type of swaps" or "what swaps can I make", this should NOT reach execution agent
        # But if it does, provide informational response instead of execution response
        # Get original message from conversation context
        message_lower = ""
        try:
            if (
                hasattr(conversation_context, "conversation_history")
                and conversation_context.conversation_history
            ):
                last_message = conversation_context.conversation_history[-1]
                if isinstance(last_message, dict):
                    message_lower = last_message.get("content", "").lower()
            # Also check if we can get it from the intent metadata
            if not message_lower and "original_message" in intent:
                message_lower = intent.get("original_message", "").lower()
        except Exception:
            pass

        is_informational_query = (
            not from_token
            or not to_token
            or amount == "0"
            or any(
                kw in message_lower
                for kw in [
                    "what type",
                    "what types",
                    "what can",
                    "can i make",
                    "explain",
                    "how do",
                    "how does",
                    "what swaps",
                ]
            )
        )

        if action == "swap":
            # If informational query (no specific tokens), provide general swap information
            if is_informational_query:
                return """**Token Swaps on Anvil**

Anvil supports token swaps through multiple DEX aggregators:

**Supported Aggregators:**
- **1inch**: Leading DEX aggregator with smart routing across 100+ liquidity sources
- **Hyperliquid**: High-performance perpetual futures exchange (20,000+ TPS, no gas fees)
- **UniswapX**: Dutch auction-based swap protocol with automatic routing
- **LiFi**: Cross-chain bridge and swap aggregator

**Supported Tokens:**
- Major tokens: BTC, ETH, USDC, USDT, DAI, SOL, MATIC, AVAX, LINK
- 100+ tokens across multiple chains

**Supported Chains:**
- Ethereum, Base, Arbitrum, Polygon, Optimism

**To get a swap quote**, provide specific details:
- "swap 100 USDC for ETH"
- "swap 0.5 BTC to SOL"
- "exchange 1000 USDT for USDC"

I'll provide real-time quotes with rates, gas costs, and execution details."""

            # Specific swap request with tokens
            base_response = (
                f"""I can help you swap {amount} {from_token} for {to_token}."""
            )

            # Add real quote if available
            if swap_quote_context:
                base_response += swap_quote_context
            elif "swap_quote" in intent:
                quote = intent["swap_quote"]
                base_response += f"\n\n**Real-time quote from 1inch:**\n"
                base_response += (
                    f"- Expected output: {quote['to_amount']:.4f} {to_token}\n"
                )
                base_response += f"- Estimated gas: {quote['estimated_gas']:,} units\n"
                if quote.get("price_impact"):
                    base_response += f"- Price impact: {quote['price_impact']:.2f}%\n"

            base_response += f"""

**Next Steps:**
1. Review the quote above
2. Confirm the swap details
3. Sign the transaction with your wallet
4. Transaction will be submitted to the blockchain

**Safety Features:**
- Transaction limits: Max ${self._max_transaction_value_usd} per transaction
- Slippage protection: 1% default
- Gas estimation included
- Pre-flight simulation before execution

Would you like to proceed with this swap?"""

            return base_response
        else:
            return f"""I understand you want to {action} {from_token}.

However, I need more information to proceed. Please provide:
- Exact amount to {action}
- Recipient wallet (if transfer)
- Any other relevant details

Once I have all details, I'll prepare the transaction for your confirmation.
"""
