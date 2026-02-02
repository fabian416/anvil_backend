"""
Swap Workflow Agent - Multi-Step Token Swap Operations.

Handles the complete swap workflow for authenticated users:
1. Parse request: Extract tokens and amount from user message
2. Fetch quote: Get best quote from appropriate provider:
   - Hyperliquid Spot: For meme tokens (PURR, TRUMP, PEPE, etc.) paired with USDC
   - 1inch: For major tokens same-chain swaps (ETH, BTC, USDC, etc.)
   - LiFi: For cross-chain swaps
3. Confirm: Show quote and wait for user confirmation
4. Execute: Generate execute_data for frontend execution

Integration:
- Meme token swaps: Uses Hyperliquid Spot API (zero gas fees, high performance)
- Same-chain major tokens: Uses 1inch API
- Cross-chain swaps: Uses LiFi API
- Execution: Frontend uses Privy SDK with execute_data

⚠️ IMPORTANT: Hyperliquid Spot only supports meme tokens paired with USDC.
Major tokens (ETH, BTC, SOL) require 1inch or LiFi.

Example Conversation:
    User: "swap 100 USDC to PURR"
    Agent: "📊 Swap Quote: 100 USDC → 50,000 PURR via Hyperliquid. Confirm?"
    User: "yes"
    Agent: "✅ Ready to execute!" + execute_data for frontend modal
"""

import logging
import re
from typing import Any, TYPE_CHECKING

from app.domain.enums.agent_type import AgentType
from app.domain.value_objects.message_content import MessageContent
from app.domain.ports.agent_squad.agent_gateway import AgentResponse

from .base_workflow_agent import (
    BaseWorkflowAgent,
    WorkflowState,
    WorkflowStep,
    UserContext,
)

if TYPE_CHECKING:
    from app.infrastructure.adapters.external.oneinch_client import OneInchClient
    from app.infrastructure.adapters.external.lifi_client import LiFiClient
    from app.infrastructure.adapters.external.coingecko_client import CoinGeckoClient
    from app.infrastructure.adapters.external.hyperliquid_client import HyperliquidClient
    from app.domain.ports.agent_squad.llm_client_gateway import LLMClientGateway

logger = logging.getLogger(__name__)


# =============================================================================
# HYPERLIQUID SPOT TOKENS - THE ONLY SUPPORTED SWAP PROVIDER
# =============================================================================
# Anvil ONLY supports swaps via Hyperliquid Spot.
# Hyperliquid Spot supports meme tokens paired with USDC.
# Major tokens (ETH, BTC, etc.) are NOT supported for swaps.
# =============================================================================

HYPERLIQUID_SPOT_TOKENS = {
    "USDC",  # Quote currency (required for all Hyperliquid spot swaps)
    # Popular meme tokens on Hyperliquid Spot
    "PURR", "HFUN", "TRUMP", "PEPE", "MOG", "POINTS", "JEFF",
    "GMEOW", "LICK", "MANLET", "SIX", "WAGMI", "CAPPY",
    "XULIAN", "RUG", "CZ", "BAGS", "ANSEM", "TATE", "FUN",
    "BIGBEN", "KOBE", "VEGAS", "PUMP", "SCHIZO", "CATNIP",
    "HAPPY", "SELL", "HBOOST", "GPT", "PANDA", "HODL", "RAGE",
    "ASI", "LEAP", "VAPOR", "X", "PILL", "CAT", "HPEPE",
    "MBAPPE", "MAGA", "OMNIX", "COKE", "MEOW", "ANT", "NEIRO",
}

# Major tokens that are NOT supported for swaps on Anvil
# Users should use external DEXs for these tokens
UNSUPPORTED_SWAP_TOKENS = {
    "ETH", "BTC", "SOL", "WBTC", "WETH", "LINK", "UNI", "AAVE",
    "CRV", "MKR", "DAI", "USDT", "MATIC", "ARB", "OP", "AVAX",
    "DOT", "ATOM", "APT", "SUI", "SEI", "TIA", "INJ", "FTM",
    "XRP", "ADA", "DOGE", "LTC", "SHIB", "AVAX",
}


# Popular meme tokens for selection menu (ordered by popularity/volume)
POPULAR_MEME_TOKENS = [
    ("PURR", "Hyperliquid's native meme token"),
    ("TRUMP", "Political meme token"),
    ("PEPE", "Classic frog meme"),
    ("HFUN", "Hyperliquid Fun token"),
    ("MOG", "Mog Coin"),
    ("JEFF", "Jeff token"),
    ("WAGMI", "We're All Gonna Make It"),
    ("GMEOW", "Cat meme token"),
    ("CAPPY", "Cappy token"),
    ("MANLET", "Manlet meme"),
]

# Common token addresses by chain
# Use 0xEeee...eE for native ETH (LiFi standard)
NATIVE_ETH_ADDRESS = "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"

TOKEN_ADDRESSES = {
    "ethereum": {
        "ETH": NATIVE_ETH_ADDRESS,
        "WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
        "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
        "WBTC": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
        "DAI": "0x6B175474E89094C44Da98b954EedeAC495271d0F",
    },
    "polygon": {
        "MATIC": NATIVE_ETH_ADDRESS,
        "WMATIC": "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270",
        "USDC": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
        "USDT": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",
    },
    "arbitrum": {
        "ETH": NATIVE_ETH_ADDRESS,
        "WETH": "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",
        "USDC": "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8",
    },
    "base": {
        "ETH": NATIVE_ETH_ADDRESS,
        "WETH": "0x4200000000000000000000000000000000000006",
        "USDC": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
        # Meme tokens on Base (Hyperliquid Spot uses these for swaps)
        "PURR": "0x9b4e2579374e1b3ce1b31e0c55e8e7c3e2d5b0e1",  # Placeholder - will be updated from API
        "TRUMP": "0xCf20a0a767f4513C1c3C8B1c1e0e4F3E7c8b0F9A",  # Placeholder - will be updated from API
    },
}

# =============================================================================
# HYPERLIQUID BRIDGE CONTRACTS
# =============================================================================
# Users must bridge USDC to Hyperliquid before swapping meme tokens.
# The bridge deposits to Hyperliquid Perps account, then user transfers to Spot.
# Flow: EVM USDC → Bridge → Hyperliquid Perps → Transfer → Hyperliquid Spot → Swap
# =============================================================================

HYPERLIQUID_BRIDGE_CONTRACTS = {
    # Arbitrum is the primary supported chain for Hyperliquid deposits
    "arbitrum": {
        "bridge": "0x2Df1c51E09aECF9cacB7bc98cB1742757f163dF7",  # Hyperliquid deposit contract
        "usdc": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",    # Native USDC on Arbitrum
        "chain_id": 42161,
    },
    # Base support (may require bridging to Arbitrum first)
    "base": {
        "bridge": None,  # No direct bridge - must go via Arbitrum
        "usdc": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",   # Native USDC on Base
        "chain_id": 8453,
    },
}

# Hyperliquid token identifiers (meme tokens on Hyperliquid L1)
# NOTE: Hyperliquid uses its own internal token system, NOT EVM contract addresses.
# These tokens are traded via Hyperliquid's Spot API, not via on-chain ERC-20 transfers.
# We use None/null for token addresses since balanceOf won't work on these.
# The frontend should use Hyperliquid's API directly for these swaps.
HYPERLIQUID_TOKEN_ADDRESSES = {
    # Hyperliquid native tokens - no EVM contract addresses
    # The frontend should detect provider="hyperliquid" and use Hyperliquid SDK
    "USDC": None,  # Hyperliquid native USDC (not ERC-20)
    "PURR": None,  # Hyperliquid PURR
    "TRUMP": None,  # Hyperliquid TRUMP
    "PEPE": None,
    "HFUN": None,
    "MOG": None,
    "JEFF": None,
    "WAGMI": None,
    "GMEOW": None,
    "CAPPY": None,
    "MANLET": None,
}

# Token decimals
TOKEN_DECIMALS = {
    "ETH": 18,
    "WETH": 18,
    "MATIC": 18,
    "WMATIC": 18,
    "USDC": 6,
    "USDT": 6,
    "DAI": 18,
    "WBTC": 8,
    "BTC": 8,
}


class SwapWorkflowAgent(BaseWorkflowAgent):
    """
    AGNO-based multi-step swap workflow agent.
    
    Steps:
    1. parse_request: Extract from_token, to_token, amount, chain
    2. fetch_data: Get quotes from appropriate provider:
       - Hyperliquid Spot for meme tokens (PURR, TRUMP, etc.)
       - 1inch for major tokens same-chain
       - LiFi for cross-chain
    3. confirm: Show quote, wait for user confirmation
    4. execute: Generate execute_data for frontend
    
    Features:
    - Intelligent provider routing based on token type
    - Meme token swaps via Hyperliquid Spot (zero gas fees)
    - Same-chain major token swaps via 1inch
    - Cross-chain swaps via LiFi
    - User modification support ("change to 1 ETH instead")
    - Multi-language support
    """
    
    def __init__(
        self,
        llm_client: "LLMClientGateway | None" = None,
        oneinch_client: "OneInchClient | None" = None,
        lifi_client: "LiFiClient | None" = None,
        coingecko_client: "CoinGeckoClient | None" = None,
        hyperliquid_client: "HyperliquidClient | None" = None,
    ):
        """
        Initialize swap workflow agent.
        
        Args:
            llm_client: LLM client for parameter extraction
            oneinch_client: 1inch API client for same-chain major token swaps
            lifi_client: LiFi API client for cross-chain swaps
            coingecko_client: CoinGecko client for market data enrichment
            hyperliquid_client: Hyperliquid client for meme token spot swaps
        """
        super().__init__(llm_client=llm_client)
        self._oneinch = oneinch_client
        self._lifi = lifi_client
        self._coingecko = coingecko_client
        self._hyperliquid = hyperliquid_client
    
    @property
    def agent_type(self) -> AgentType:
        return AgentType.SWAP_WORKFLOW
    
    @property
    def workflow_name(self) -> str:
        return "SwapWorkflow"
    
    async def process_step(
        self,
        message: MessageContent,
        state: WorkflowState,
        user_context: UserContext,
    ) -> tuple[str, WorkflowState]:
        """Process swap workflow step."""
        
        step = state.step
        language = user_context.language
        text_lower = message.value.lower().strip()
        
        logger.info(f"[SwapWorkflow] Processing step={step}, message={message.value[:50]}...")
        
        # Check if user wants to continue or start new after EXECUTE/COMPLETED
        # If user just says "swap" without full params after an executed swap,
        # ask if they want to repeat the last swap or start fresh
        if step in (WorkflowStep.EXECUTE.value, WorkflowStep.COMPLETED.value):
            # Check if user is saying just "swap" without specific params
            simple_swap_keywords = ["swap", "exchange", "trade", "cambiar", "trocar", "intercambiar"]
            is_simple_swap = text_lower in simple_swap_keywords or text_lower in [
                "i want to swap", "quiero cambiar", "quiero intercambiar",
                "swap again", "another swap", "repeat", "again",
                "repetir", "de nuevo", "otra vez",
            ]
            
            # Check if user wants to continue with last swap
            continue_keywords = ["yes", "si", "sí", "sim", "continue", "continuar", "repeat", "repetir", "again", "de nuevo"]
            wants_continue = text_lower in continue_keywords
            
            # Check if user wants to start fresh
            fresh_keywords = ["new", "nuevo", "nova", "fresh", "start over", "empezar de nuevo", "começar de novo", "different", "diferente"]
            wants_fresh = any(kw in text_lower for kw in fresh_keywords)
            
            if wants_continue and state.data.get("from_token") and state.data.get("to_token"):
                # User wants to repeat last swap - go directly to fetch quote
                logger.info(f"[SwapWorkflow] User wants to continue with last swap")
                state.step = WorkflowStep.FETCH_DATA.value
                state.confirmed = False
                state.execute_data = None
                return await self._handle_fetch_quote(message, state, user_context)
            
            elif wants_fresh:
                # User explicitly wants a new swap
                logger.info(f"[SwapWorkflow] User wants to start fresh swap")
                state = WorkflowState()
                state.step = WorkflowStep.PARSE_REQUEST.value
                return await self._handle_parse_request(message, state, user_context)
            
            elif is_simple_swap and state.data.get("from_token") and state.data.get("to_token"):
                # User said "swap" without params after a completed swap - ask what they want
                logger.info(f"[SwapWorkflow] User said 'swap' after execute - asking if continue or new")
                state.data["awaiting_continue_choice"] = True
                state.execute_data = None  # Don't show execute until user confirms
                return self._get_continue_or_new_prompt(state, language), state
        
        # Check if user is responding to continue/new prompt
        if state.data.get("awaiting_continue_choice"):
            continue_keywords = ["yes", "si", "sí", "sim", "continue", "continuar", "1", "repeat", "repetir", "last", "anterior"]
            fresh_keywords = ["no", "new", "nuevo", "nova", "2", "fresh", "different", "diferente", "start"]
            
            if any(kw in text_lower for kw in continue_keywords):
                # Continue with last swap
                state.data.pop("awaiting_continue_choice", None)
                state.step = WorkflowStep.FETCH_DATA.value
                state.confirmed = False
                state.execute_data = None
                logger.info(f"[SwapWorkflow] User chose to continue with last swap")
                return await self._handle_fetch_quote(message, state, user_context)
            elif any(kw in text_lower for kw in fresh_keywords):
                # Start fresh
                state.data.pop("awaiting_continue_choice", None)
                state = WorkflowState()
                state.step = WorkflowStep.PARSE_REQUEST.value
                logger.info(f"[SwapWorkflow] User chose to start new swap")
                return await self._handle_parse_request(message, state, user_context)
            else:
                # Check if user provided new swap params directly
                new_params = await self._extract_swap_params(message.value)
                if new_params.get("from_token") and new_params.get("to_token"):
                    # User provided new swap details - start fresh with these
                    state.data.pop("awaiting_continue_choice", None)
                    state = WorkflowState()
                    state.step = WorkflowStep.PARSE_REQUEST.value
                    return await self._handle_parse_request(message, state, user_context)
                # Re-prompt
                return self._get_continue_or_new_prompt(state, language), state
        
        # Check if user wants to start a NEW swap flow (restart detection)
        # This resets state when user says "swap 100 USDC to ETH", etc.
        # while already in an ongoing flow (FETCH_DATA, CONFIRM step)
        if step in (WorkflowStep.FETCH_DATA.value, WorkflowStep.CONFIRM.value):
            # Only restart if user provides specific swap params (not just "swap")
            new_params = await self._extract_swap_params(message.value)
            has_specific_params = new_params.get("from_token") and new_params.get("to_token") and new_params.get("amount")
            
            if has_specific_params:
                # User provided complete new swap params - start fresh
                logger.info(f"[SwapWorkflow] New swap params detected - starting fresh swap")
                state = WorkflowState()
                state.step = WorkflowStep.PARSE_REQUEST.value
                return await self._handle_parse_request(message, state, user_context)
        
        # Step 1: Parse request
        if step == WorkflowStep.PARSE_REQUEST.value:
            return await self._handle_parse_request(message, state, user_context)
        
        # Step 2: Fetch quote
        if step == WorkflowStep.FETCH_DATA.value:
            return await self._handle_fetch_quote(message, state, user_context)
        
        # Step 3: Confirm
        if step == WorkflowStep.CONFIRM.value:
            return await self._handle_confirm(message, state, user_context)
        
        # Step 4: Execute
        if step == WorkflowStep.EXECUTE.value:
            return await self._handle_execute(message, state, user_context)
        
        # Unknown step - restart
        logger.warning(f"[SwapWorkflow] Unknown step={step}, restarting")
        state.step = WorkflowStep.PARSE_REQUEST.value
        return await self._handle_parse_request(message, state, user_context)
    
    async def _handle_parse_request(
        self,
        message: MessageContent,
        state: WorkflowState,
        user_context: UserContext,
    ) -> tuple[str, WorkflowState]:
        """
        Step 1: Parse swap parameters from user message.
        
        Extracts: from_token, to_token, amount, chain, to_chain
        
        Enhanced with token selection:
        - If only from_token + amount provided, show numbered token list
        - User can respond with "1" or "PURR" to select destination token
        
        IMPORTANT: Anvil only supports swaps via Hyperliquid Spot.
        Hyperliquid Spot only supports meme tokens paired with USDC.
        Major tokens (ETH, BTC, etc.) are NOT supported for swaps.
        """
        # Check if we're awaiting token selection from a previous turn
        if state.data.get("awaiting_token_selection"):
            return await self._handle_token_selection(message, state, user_context)
        
        # Check if we already have from_token and to_token from previous turn
        # and user is just providing the amount
        existing_from = state.data.get("from_token", "").upper()
        existing_to = state.data.get("to_token", "").upper()
        user_input = message.value.strip()
        
        # If we have both tokens and user provides just a number, treat it as amount
        if existing_from and existing_to and not state.data.get("amount"):
            # Check if user input is just a number (amount)
            amount_match = None
            try:
                # Try to parse as number (handles "1", "100", "1.5", "$50", etc.)
                clean_input = user_input.replace("$", "").replace(",", "").strip()
                if clean_input.replace(".", "").isdigit():
                    amount_match = clean_input
            except ValueError:
                pass
            
            if amount_match:
                logger.info(f"[SwapWorkflow] User provided amount '{amount_match}' for {existing_from} → {existing_to}")
                state.data["amount"] = amount_match
                # Proceed to fetch quote
                state.step = WorkflowStep.FETCH_DATA.value
                return await self._handle_fetch_quote(message, state, user_context)
        
        params = await self._extract_swap_params(message.value)
        
        # Check for partial request: has from_token (likely USDC) but missing to_token
        from_token = params.get("from_token", "").upper() or existing_from
        to_token = params.get("to_token", "").upper() or existing_to
        amount = params.get("amount") or state.data.get("amount")
        
        # If we have USDC + amount but no destination token, show selection menu
        if from_token == "USDC" and amount and not to_token:
            state.data["from_token"] = from_token
            state.data["amount"] = amount
            state.data["chain"] = params.get("chain", "base")
            state.data["awaiting_token_selection"] = True
            
            response = await self._get_token_selection_prompt(
                from_token=from_token,
                amount=amount,
                user_context=user_context,
            )
            return response, state
        
        # If neither token is provided, show smart help based on balance
        if not from_token or not to_token:
            response = await self._get_missing_params_response(params, user_context)
            return response, state
        
        # Check if tokens are supported on Hyperliquid Spot
        unsupported_error = self._check_unsupported_tokens(from_token, to_token, user_context.language)
        if unsupported_error:
            state.error = "unsupported_token"
            return unsupported_error, state
        
        # Update state with extracted params
        state.data.update(params)
        
        # If amount is missing, ask for it
        if not amount:
            response = self._get_amount_prompt(
                from_token,
                to_token,
                user_context.language,
            )
            state.step = WorkflowStep.PARSE_REQUEST.value  # Stay in parse step
            return response, state
        
        # All params available - proceed to fetch quote
        state.step = WorkflowStep.FETCH_DATA.value
        return await self._handle_fetch_quote(message, state, user_context)
    
    async def _handle_token_selection(
        self,
        message: MessageContent,
        state: WorkflowState,
        user_context: UserContext,
    ) -> tuple[str, WorkflowState]:
        """
        Handle user's token selection response.
        
        User can respond with:
        - Number (1-10) to select from the list
        - Token symbol (PURR, TRUMP, etc.)
        """
        user_input = message.value.strip().upper()
        
        # Clear the awaiting flag
        state.data["awaiting_token_selection"] = False
        
        selected_token = None
        
        # Check if it's a number selection
        if user_input.isdigit():
            index = int(user_input) - 1  # 1-based to 0-based
            if 0 <= index < len(POPULAR_MEME_TOKENS):
                selected_token = POPULAR_MEME_TOKENS[index][0]
        
        # Check if it's a token symbol
        if not selected_token:
            # Clean up the input - might be "purr", "PURR", "1. PURR", etc.
            clean_input = user_input.replace(".", "").strip()
            if clean_input in HYPERLIQUID_SPOT_TOKENS:
                selected_token = clean_input
        
        if not selected_token:
            # Invalid selection - show menu again
            state.data["awaiting_token_selection"] = True
            
            response = self._get_invalid_selection_response(
                user_input=message.value,
                language=user_context.language,
            )
            return response, state
        
        # Update state with selected token
        state.data["to_token"] = selected_token
        
        # Now we have all params - proceed to fetch quote
        state.step = WorkflowStep.FETCH_DATA.value
        
        # Create a dummy message to pass to fetch_quote
        return await self._handle_fetch_quote(message, state, user_context)
    
    def _check_unsupported_tokens(
        self,
        from_token: str,
        to_token: str,
        language: str,
    ) -> str | None:
        """
        Check if tokens are supported on Hyperliquid Spot.
        
        Anvil ONLY supports swaps via Hyperliquid Spot, which means:
        - Only meme tokens + USDC are supported
        - Major tokens (ETH, BTC, etc.) are NOT supported
        
        Returns an error message if tokens are not supported, or None if valid.
        """
        from_supported = from_token in HYPERLIQUID_SPOT_TOKENS
        to_supported = to_token in HYPERLIQUID_SPOT_TOKENS
        
        # Both tokens must be in Hyperliquid Spot supported list
        if not from_supported or not to_supported:
            # Determine which token(s) are unsupported
            unsupported = []
            if not from_supported:
                unsupported.append(from_token)
            if not to_supported:
                unsupported.append(to_token)
            
            return self._build_unsupported_message(
                from_token=from_token,
                to_token=to_token,
                unsupported_tokens=unsupported,
                language=language,
            )
        
        # One token must be USDC (Hyperliquid Spot requirement)
        if from_token != "USDC" and to_token != "USDC":
            return self._build_usdc_required_message(from_token, to_token, language)
        
        return None
    
    def _build_unsupported_message(
        self,
        from_token: str,
        to_token: str,
        unsupported_tokens: list[str],
        language: str,
    ) -> str:
        """Build message for unsupported tokens."""
        messages = {
            "en": f"""❌ **Swap not supported: {from_token} → {to_token}**

Anvil uses **Hyperliquid Spot** for swaps, which only supports **meme tokens paired with USDC**.

**Tokens like {', '.join(unsupported_tokens)} are not available for swaps.**

---

**✅ What you CAN do on Anvil:**

**Meme Token Swaps** (via Hyperliquid Spot):
• `swap 100 USDC to PURR`
• `swap 50 USDC to TRUMP`
• `swap 1000 USDC to PEPE`

**Supported meme tokens:** PURR, TRUMP, PEPE, MOG, HFUN, JEFF, WAGMI, and 40+ more

---

**💡 For major tokens ({', '.join(unsupported_tokens)}), you can:**

• **Check prices:** "what's the price of ETH?"
• **Track portfolio:** "show my portfolio"
• **Buy crypto:** "buy ETH" (fiat on-ramp via MoonPay)
• **Use external DEXs:** Uniswap, 1inch, or other DEX aggregators
""",
            "es": f"""❌ **Swap no soportado: {from_token} → {to_token}**

Anvil usa **Hyperliquid Spot** para swaps, que solo soporta **meme tokens con USDC**.

**Tokens como {', '.join(unsupported_tokens)} no están disponibles para swaps.**

**✅ Qué PUEDES hacer en Anvil:**

• Swaps de meme tokens: `swap 100 USDC to PURR`
• Ver precios: "precio de ETH"
• Comprar cripto: "comprar ETH"
""",
            "pt": f"""❌ **Swap não suportado: {from_token} → {to_token}**

Anvil usa **Hyperliquid Spot** para swaps, que só suporta **meme tokens com USDC**.

**Tokens como {', '.join(unsupported_tokens)} não estão disponíveis para swaps.**

**✅ O que você PODE fazer no Anvil:**

• Swaps de meme tokens: `swap 100 USDC to PURR`
• Ver preços: "preço do ETH"
• Comprar cripto: "comprar ETH"
""",
        }
        return messages.get(language, messages["en"])
    
    def _build_usdc_required_message(
        self,
        from_token: str,
        to_token: str,
        language: str,
    ) -> str:
        """Build message when USDC is not in the swap pair."""
        messages = {
            "en": f"""❌ **Swap requires USDC: {from_token} → {to_token}**

Hyperliquid Spot only supports swaps **paired with USDC**.

**Try instead:**
• `swap {from_token} to USDC` - Sell {from_token} for USDC
• `swap USDC to {to_token}` - Buy {to_token} with USDC

**Two-step swap:**
1. First: `swap {from_token} to USDC`
2. Then: `swap USDC to {to_token}`
""",
            "es": f"""❌ **El swap requiere USDC: {from_token} → {to_token}**

Hyperliquid Spot solo soporta swaps **con USDC**.

**Intenta:**
• `swap {from_token} to USDC`
• `swap USDC to {to_token}`
""",
            "pt": f"""❌ **Swap requer USDC: {from_token} → {to_token}**

Hyperliquid Spot só suporta swaps **com USDC**.

**Tente:**
• `swap {from_token} to USDC`
• `swap USDC to {to_token}`
""",
        }
        return messages.get(language, messages["en"])
    
    async def _handle_fetch_quote(
        self,
        message: MessageContent,
        state: WorkflowState,
        user_context: UserContext,
    ) -> tuple[str, WorkflowState]:
        """
        Step 2: Fetch swap quote from 1inch/LiFi with enhanced market data.
        
        If user has insufficient funds, shows a helpful recommendation to buy crypto
        but still provides swap information so they know what to expect.
        """
        # Clear execute_data when fetching a new quote (user hasn't confirmed yet)
        state.execute_data = None
        state.confirmed = False
        state.cancelled = False
        
        # Use 'or' to handle both missing keys AND None values
        from_token = state.data.get("from_token") or "ETH"
        to_token = state.data.get("to_token") or "USDC"
        amount = state.data.get("amount") or "0"
        chain = state.data.get("chain") or "base"
        to_chain = state.data.get("to_chain")
        
        is_cross_chain = to_chain and to_chain.lower() != chain.lower()
        
        logger.info(
            f"[SwapWorkflow] Fetching quote: {amount} {from_token} → {to_token} "
            f"on {chain}" + (f" → {to_chain}" if is_cross_chain else "")
        )
        
        # Smart balance check: compare requested amount against user balance
        # For stablecoins (USDC, USDT, DAI), amount is roughly equal to USD value
        # For other tokens, we still allow the swap if user has some balance
        funding_recommendation = ""
        has_sufficient_funds = True
        amount_float = self._parse_amount_float(amount)
        user_balance = user_context.total_balance_usd
        
        # Determine if user has enough for this specific swap
        if from_token.upper() in ("USDC", "USDT", "DAI", "BUSD", "FRAX"):
            # Stablecoin: direct USD comparison
            # Add 10% buffer for gas fees
            required_amount = amount_float * 1.10
            has_sufficient_funds = user_balance >= required_amount
        elif user_balance < 0.01:
            # User has essentially zero balance
            has_sufficient_funds = False
        else:
            # Non-stablecoin: allow if user has any meaningful balance
            # We can't easily compare ETH amount to USD balance without price data
            has_sufficient_funds = True
        
        if not has_sufficient_funds:
            logger.info(
                f"[SwapWorkflow] User has insufficient funds: "
                f"requested={amount} {from_token} (~${amount_float:.2f}), "
                f"balance=${user_balance:.2f}"
            )
            # Provide smart recommendation
            funding_recommendation = self._get_smart_funding_recommendation(
                from_token=from_token,
                requested_amount=amount_float,
                user_balance=user_balance,
                language=user_context.language,
            )
        
        # Fetch quote
        quote_result = await self._fetch_quote(
            from_token=from_token,
            to_token=to_token,
            amount=amount,
            chain=chain,
            to_chain=to_chain,
            wallet_address=user_context.wallet_address,
        )
        
        if quote_result.get("error"):
            state.error = quote_result["error"]
            response = self._get_quote_error_response(quote_result["error"], user_context.language)
            # Prepend funding recommendation if applicable
            if funding_recommendation:
                response = funding_recommendation + "\n" + response
            return response, state
        
        # Store quote in state
        state.data["quote"] = quote_result
        state.data["output_amount"] = quote_result.get("output_amount", "0")
        state.data["price_impact"] = quote_result.get("price_impact", 0)
        state.data["aggregator"] = quote_result.get("aggregator", "unknown")
        state.data["gas_estimate"] = quote_result.get("gas_estimate", 200000)
        # Store token addresses from quote (for execute_data)
        if quote_result.get("from_token_address"):
            state.data["from_token_address"] = quote_result["from_token_address"]
        if quote_result.get("to_token_address"):
            state.data["to_token_address"] = quote_result["to_token_address"]
        
        # Fetch enhanced market data (prices, gas info)
        market_data = await self._fetch_market_enrichment(from_token, to_token, chain)
        state.data["market_data"] = market_data
        
        # Only move to confirm step if user has sufficient funds
        # If user needs funding, stay in informational mode
        if has_sufficient_funds:
            state.step = WorkflowStep.CONFIRM.value
        else:
            # User needs to fund first - stay in parse_request
            # Don't advance to confirm so frontend won't expect action
            state.step = WorkflowStep.PARSE_REQUEST.value
            logger.info(
                f"[SwapWorkflow] Not advancing to confirm - user needs funding first"
            )
        
        # Format quote response with enhanced market data
        response = self._format_quote_response(state.data, user_context.language)
        
        # Prepend funding recommendation if user has insufficient funds
        if funding_recommendation:
            response = funding_recommendation + "\n" + response
        
        return response, state
    
    def _get_funding_recommendation(self, from_token: str, language: str) -> str:
        """
        Get a helpful recommendation for users with insufficient funds.
        
        This is shown before the swap quote to guide users on how to fund their wallet.
        """
        recommendations = {
            "en": f"""💡 **Heads up:** Your portfolio appears to have limited funds.

To complete this swap, you'll need **{from_token}** in your wallet.

**Get started:**
• 💳 Say **"buy crypto"** to purchase with card/Apple Pay/Google Pay
• 📥 Or transfer {from_token} from another wallet

Here's the swap quote you requested:
""",
            "es": f"""💡 **Aviso:** Tu portafolio parece tener fondos limitados.

Para completar este swap, necesitarás **{from_token}** en tu billetera.

**Comienza:**
• 💳 Di **"comprar cripto"** para comprar con tarjeta/Apple Pay/Google Pay
• 📥 O transfiere {from_token} desde otra billetera

Aquí está la cotización del swap que solicitaste:
""",
            "pt": f"""💡 **Atenção:** Seu portfólio parece ter fundos limitados.

Para completar este swap, você precisará de **{from_token}** em sua carteira.

**Comece:**
• 💳 Diga **"comprar cripto"** para comprar com cartão/Apple Pay/Google Pay
• 📥 Ou transfira {from_token} de outra carteira

Aqui está a cotação do swap que você solicitou:
""",
        }
        return recommendations.get(language, recommendations["en"])
    
    def _parse_amount_float(self, amount: str) -> float:
        """Parse amount string to float, handling edge cases."""
        try:
            # Remove common formatting characters
            clean = str(amount).replace(",", "").replace("$", "").strip()
            return float(clean)
        except (ValueError, TypeError):
            return 0.0
    
    def _get_smart_funding_recommendation(
        self,
        from_token: str,
        requested_amount: float,
        user_balance: float,
        language: str,
    ) -> str:
        """
        Get smart funding recommendation based on the gap between requested and available.
        
        Suggests:
        1. If user has some balance: adjust amount to available balance
        2. If user has zero: recommend buying crypto
        """
        if user_balance > 0.01:
            # User has some balance - suggest adjusting amount
            available = user_balance * 0.90  # Leave 10% for gas
            recommendations = {
                "en": f"""💡 **Insufficient balance for this swap**

**Requested:** {requested_amount:.2f} {from_token}
**Available:** ~${user_balance:.2f}

**Options:**
• ✅ Swap a smaller amount: **"swap {available:.2f} {from_token}"**
• 💳 Or buy more crypto: **"buy crypto"**

Here's the quote for your requested amount:
""",
                "es": f"""💡 **Saldo insuficiente para este swap**

**Solicitado:** {requested_amount:.2f} {from_token}
**Disponible:** ~${user_balance:.2f}

**Opciones:**
• ✅ Intercambia una cantidad menor: **"swap {available:.2f} {from_token}"**
• 💳 O compra más cripto: **"comprar cripto"**

Aquí está la cotización para la cantidad solicitada:
""",
                "pt": f"""💡 **Saldo insuficiente para este swap**

**Solicitado:** {requested_amount:.2f} {from_token}
**Disponível:** ~${user_balance:.2f}

**Opções:**
• ✅ Troque uma quantidade menor: **"swap {available:.2f} {from_token}"**
• 💳 Ou compre mais cripto: **"comprar cripto"**

Aqui está a cotação para a quantidade solicitada:
""",
            }
        else:
            # User has no balance - recommend buying
            recommendations = {
                "en": f"""💡 **Your wallet needs funds**

To complete this swap, you'll need **{from_token}** in your wallet.

**Get started:**
• 💳 Say **"buy crypto"** to purchase with card/Apple Pay/Google Pay
• 📥 Or transfer {from_token} from another wallet

Here's the swap quote you requested:
""",
                "es": f"""💡 **Tu billetera necesita fondos**

Para completar este swap, necesitarás **{from_token}** en tu billetera.

**Comienza:**
• 💳 Di **"comprar cripto"** para comprar con tarjeta
• 📥 O transfiere {from_token} desde otra billetera

Aquí está la cotización del swap:
""",
                "pt": f"""💡 **Sua carteira precisa de fundos**

Para completar este swap, você precisará de **{from_token}** em sua carteira.

**Comece:**
• 💳 Diga **"comprar cripto"** para comprar com cartão
• 📥 Ou transfira {from_token} de outra carteira

Aqui está a cotação do swap:
""",
            }
        
        return recommendations.get(language, recommendations["en"])
    
    async def _fetch_market_enrichment(
        self,
        from_token: str,
        to_token: str,
        chain: str,
    ) -> dict:
        """
        Fetch market enrichment data (prices, gas info, market context).
        """
        market_data = {
            "from_token_price": None,
            "from_token_24h_change": None,
            "to_token_price": None,
            "gas_price_gwei": None,
            "gas_usd_estimate": None,
            "gas_timing": None,
        }
        
        try:
            # Fetch token prices from CoinGecko
            if self._coingecko:
                # Map token symbols to CoinGecko IDs
                token_to_coingecko = {
                    "ETH": "ethereum",
                    "WETH": "ethereum",
                    "BTC": "bitcoin",
                    "WBTC": "wrapped-bitcoin",
                    "USDC": "usd-coin",
                    "USDT": "tether",
                    "DAI": "dai",
                    "MATIC": "matic-network",
                    "SOL": "solana",
                }
                
                from_id = token_to_coingecko.get(from_token.upper())
                to_id = token_to_coingecko.get(to_token.upper())
                
                if from_id:
                    try:
                        price_data = await self._coingecko.get_price(from_id)
                        market_data["from_token_price"] = price_data.usd
                        market_data["from_token_24h_change"] = price_data.usd_24h_change
                    except Exception as e:
                        logger.debug(f"[SwapWorkflow] Failed to fetch {from_token} price: {e}")
                
                if to_id and to_id not in ["usd-coin", "tether", "dai"]:  # Skip stablecoin prices
                    try:
                        price_data = await self._coingecko.get_price(to_id)
                        market_data["to_token_price"] = price_data.usd
                    except Exception as e:
                        logger.debug(f"[SwapWorkflow] Failed to fetch {to_token} price: {e}")
            
            # Estimate gas costs
            gas_estimate = 200000  # Default estimate
            gas_price_gwei = 0.01 if chain == "base" else 30  # Base L2 vs mainnet
            
            # Calculate USD gas cost
            eth_price = market_data.get("from_token_price") or 3000  # Fallback ETH price
            if from_token.upper() not in ["ETH", "WETH"]:
                # If not swapping ETH, fetch ETH price for gas calculation
                if self._coingecko:
                    try:
                        eth_data = await self._coingecko.get_price("ethereum")
                        eth_price = eth_data.usd
                    except Exception:
                        pass
            
            gas_cost_eth = (gas_estimate * gas_price_gwei) / 1e9
            gas_cost_usd = gas_cost_eth * eth_price
            
            market_data["gas_price_gwei"] = gas_price_gwei
            market_data["gas_usd_estimate"] = round(gas_cost_usd, 4)
            
            # Gas timing recommendation based on network
            if chain == "base":
                market_data["gas_timing"] = "Base L2 has consistently low fees (~$0.01)"
            elif chain == "ethereum":
                market_data["gas_timing"] = "Consider executing during low-traffic hours (weekends, early morning UTC)"
            else:
                market_data["gas_timing"] = "L2 networks typically have lower and stable fees"
                
        except Exception as e:
            logger.warning(f"[SwapWorkflow] Market enrichment failed: {e}")
        
        return market_data
    
    async def _handle_confirm(
        self,
        message: MessageContent,
        state: WorkflowState,
        user_context: UserContext,
    ) -> tuple[str, WorkflowState]:
        """
        Step 3: Handle user confirmation/modification/cancellation.
        """
        intent = self._parse_user_intent(message.value)
        
        if intent == "confirm":
            # User confirmed - generate execute_data
            state.confirmed = True
            state.step = WorkflowStep.EXECUTE.value
            return await self._handle_execute(message, state, user_context)
        
        elif intent == "cancel":
            # User cancelled - clear execute_data to prevent execution
            state.cancelled = True
            state.step = WorkflowStep.CANCELLED.value
            state.execute_data = None  # Clear execute_data on cancel
            response = self._get_cancel_response(user_context.language)
            return response, state
        
        elif intent == "modify":
            # User wants to modify - extract new params
            new_params = await self._extract_swap_params(message.value)
            
            # Update state with new params (keep existing if not provided)
            if new_params.get("amount"):
                state.data["amount"] = new_params["amount"]
            if new_params.get("from_token"):
                state.data["from_token"] = new_params["from_token"]
            if new_params.get("to_token"):
                state.data["to_token"] = new_params["to_token"]
            
            # Re-fetch quote
            state.step = WorkflowStep.FETCH_DATA.value
            return await self._handle_fetch_quote(message, state, user_context)
        
        else:
            # Unclear response - re-prompt for confirmation
            response = self._get_confirm_prompt(user_context.language)
            return response, state
    
    async def _handle_execute(
        self,
        message: MessageContent,
        state: WorkflowState,
        user_context: UserContext,
    ) -> tuple[str, WorkflowState]:
        """
        Step 4: Generate execute_data for frontend execution.
        
        For Hyperliquid swaps, generates multi-step execute_data:
        1. Deposit USDC to Hyperliquid (if needed)
        2. Transfer from Perps to Spot (if needed)
        3. Execute spot swap
        
        IMPORTANT: Checks user balance before allowing execution.
        If user has insufficient funds, shows helpful message to buy crypto.
        """
        # Use 'or' to handle both missing keys AND None values
        from_token = state.data.get("from_token") or "ETH"
        to_token = state.data.get("to_token") or "USDC"
        amount = state.data.get("amount") or "0"
        chain = state.data.get("chain") or "base"
        to_chain = state.data.get("to_chain")
        aggregator = state.data.get("aggregator") or "hyperliquid"
        
        # Smart balance check: compare requested amount against user balance
        amount_float = self._parse_amount_float(amount)
        user_balance = user_context.total_balance_usd
        has_sufficient_funds = True
        
        if from_token.upper() in ("USDC", "USDT", "DAI", "BUSD", "FRAX"):
            # Stablecoin: direct USD comparison with 10% buffer for gas
            required_amount = amount_float * 1.10
            has_sufficient_funds = user_balance >= required_amount
        elif user_balance < 0.01:
            # User has essentially zero balance
            has_sufficient_funds = False
        # For non-stablecoins, allow if user has any balance
        
        if not has_sufficient_funds:
            logger.info(
                f"[SwapWorkflow] Blocking execution - insufficient funds: "
                f"requested={amount} {from_token}, balance=${user_balance:.2f}"
            )
            # Calculate recommended amount (90% of balance to leave room for gas)
            recommended_amount = max(0, user_balance * 0.90)
            
            # Auto-update state with recommended amount and re-fetch quote
            if recommended_amount >= 0.01:
                state.data["amount"] = f"{recommended_amount:.2f}"
                state.step = WorkflowStep.FETCH_DATA.value
                # Show message that we're adjusting to available balance
                response = self._get_auto_adjust_message(
                    original_amount=amount,
                    recommended_amount=f"{recommended_amount:.2f}",
                    from_token=from_token,
                    to_token=to_token,
                    user_balance=user_balance,
                    language=user_context.language,
                )
                # Fetch new quote with adjusted amount
                new_quote_response, state = await self._handle_fetch_quote(message, state, user_context)
                return f"{response}\n\n{new_quote_response}", state
            else:
                # User has no usable balance - show buy crypto message
                response = self._get_zero_balance_message(
                    from_token=from_token,
                    language=user_context.language,
                )
                state.error = "insufficient_balance"
                return response, state
        
        # Get quote data for execute_data
        output_amount = state.data.get("output_amount", "0")
        price_impact = state.data.get("price_impact", 0)
        gas_estimate = state.data.get("gas_estimate")
        quote_data = state.data.get("quote", {})
        market_data = state.data.get("market_data", {})
        
        # Calculate exchange rate (as string for Pydantic validation)
        try:
            amount_float = float(amount)
            output_float = float(output_amount)
            exchange_rate = str(output_float / amount_float) if amount_float > 0 else "0"
        except (ValueError, TypeError):
            exchange_rate = "0"
        
        # Get market enrichment data
        from_token_price = market_data.get("from_token_price")
        from_token_24h_change = market_data.get("from_token_24h_change")
        gas_usd = market_data.get("gas_usd_estimate")
        
        # Convert gas_usd to string for Pydantic validation
        network_fee_usd_str = str(gas_usd) if gas_usd is not None else None
        
        # Calculate USD value (as string)
        try:
            value_usd = str(float(amount) * from_token_price) if from_token_price else None
        except (ValueError, TypeError):
            value_usd = None
        
        # Calculate minimum output with slippage
        slippage_pct = 1.0  # 1% default slippage
        try:
            min_amount_out = float(output_amount) * (1 - slippage_pct / 100)
            min_amount_out_str = f"{min_amount_out:.6f}".rstrip('0').rstrip('.')
        except (ValueError, TypeError):
            min_amount_out_str = None
        
        # Convert numeric fields to strings for Pydantic validation
        from_token_price_str = str(from_token_price) if from_token_price is not None else None
        from_token_24h_change_str = str(from_token_24h_change) if from_token_24h_change is not None else None
        price_impact_str = str(price_impact) if price_impact is not None else None
        gas_estimate_str = str(gas_estimate) if gas_estimate is not None else None
        
        # ============================================================
        # HYPERLIQUID MULTI-STEP EXECUTION
        # ============================================================
        # Hyperliquid swaps require a 3-step flow:
        # 1. Deposit USDC to Hyperliquid (bridge from Arbitrum/Base)
        # 2. Transfer from Perps to Spot account
        # 3. Execute spot swap
        # ============================================================
        
        is_hyperliquid = aggregator == "hyperliquid"
        
        if is_hyperliquid:
            execute_data = await self._build_hyperliquid_execute_data(
                from_token=from_token,
                to_token=to_token,
                amount=amount,
                output_amount=output_amount,
                min_amount_out=min_amount_out_str,
                price_impact=price_impact_str,
                exchange_rate=exchange_rate,
                slippage=slippage_pct,
                value_usd=value_usd,
                user_context=user_context,
            )
        else:
            # Standard EVM swap (1inch, LiFi)
            # Get token addresses from state (stored during quote fetch) or resolve
            from_token_address = state.data.get("from_token_address") or self._resolve_token_address(from_token, chain)
            to_token_address = state.data.get("to_token_address") or self._resolve_token_address(to_token, chain)
            
            execute_data = self._build_execute_data(
                action_type="swap",
                provider=aggregator,
                chain=chain,
                from_token=from_token,
                to_token=to_token,
                amount=amount,
                quote_amount=output_amount,  # The expected output amount from quote
                min_amount_out=min_amount_out_str,  # Minimum output with slippage applied
                price_impact=price_impact_str,
                gas_estimate=gas_estimate_str,
                network_fee_usd=network_fee_usd_str,
                exchange_rate=exchange_rate,
                slippage=slippage_pct,
                to_chain=to_chain,
                # Token addresses
                from_token_address=from_token_address if from_token_address and from_token_address.startswith("0x") else None,
                to_token_address=to_token_address if to_token_address and to_token_address.startswith("0x") else None,
                # Price data
                from_token_price_usd=from_token_price_str,
                from_token_24h_change=from_token_24h_change_str,
                value_usd=value_usd,
            )
        
        # Store execute_data in state
        state.execute_data = execute_data
        state.step = WorkflowStep.COMPLETED.value
        
        # Format ready-to-execute response (pass execute_data for multi-step info)
        response = self._format_execute_response(state.data, user_context.language, execute_data)
        return response, state
    
    async def _build_hyperliquid_execute_data(
        self,
        from_token: str,
        to_token: str,
        amount: str,
        output_amount: str,
        min_amount_out: str | None,
        price_impact: str | None,
        exchange_rate: str,
        slippage: float,
        value_usd: str | None,
        user_context: UserContext,
    ) -> dict[str, Any]:
        """
        Build multi-step execute_data for Hyperliquid swaps.
        
        Hyperliquid Flow (using LiFi for deposits):
        1. Deposit: Bridge USDC via LiFi from user's chain to Hyperliquid (if no balance)
           - LiFi handles cross-chain bridging (Base/Arbitrum → Hyperliquid)
           - Gas is paid on source chain (no need for ETH on Arbitrum)
        2. Transfer: Move from Perps to Spot account (if balance in Perps)
        3. Swap: Execute spot swap USDC → meme token
        
        Returns execute_data with steps[] array for frontend to process.
        """
        amount_float = self._parse_amount_float(amount)
        
        # Check Hyperliquid balances to determine which steps are needed
        hl_perps_usdc = 0.0
        hl_spot_usdc = 0.0
        hl_spot_from_token = 0.0
        
        if self._hyperliquid and user_context.wallet_address:
            try:
                all_balances = await self._hyperliquid.get_all_balances(user_context.wallet_address)
                hl_perps_usdc = all_balances.get("perps", {}).get("USDC", 0.0)
                hl_spot_usdc = all_balances.get("spot", {}).get("USDC", 0.0)
                hl_spot_from_token = all_balances.get("spot", {}).get(from_token.upper(), 0.0)
                
                logger.info(
                    f"[SwapWorkflow] Hyperliquid balances for {user_context.wallet_address}: "
                    f"Perps USDC={hl_perps_usdc}, Spot USDC={hl_spot_usdc}, "
                    f"Spot {from_token}={hl_spot_from_token}"
                )
            except Exception as e:
                logger.warning(f"[SwapWorkflow] Failed to get Hyperliquid balances: {e}")
        
        # Determine which steps are needed
        # If swapping FROM USDC, check USDC balance
        # If swapping FROM meme token (e.g., PURR → USDC), check meme token balance
        is_selling_usdc = from_token.upper() == "USDC"
        
        if is_selling_usdc:
            # User wants to swap USDC → meme token
            available_on_spot = hl_spot_usdc
            available_on_perps = hl_perps_usdc
        else:
            # User wants to swap meme token → USDC
            available_on_spot = hl_spot_from_token
            available_on_perps = 0  # Meme tokens are only on Spot
        
        # Build steps based on what's needed
        steps = []
        current_step = 1
        
        # Step 1: Deposit via LiFi (if not enough on Hyperliquid)
        total_on_hyperliquid = available_on_spot + available_on_perps
        needs_deposit = total_on_hyperliquid < amount_float and is_selling_usdc
        
        # Default source chain is Base (where user likely has funds)
        # Frontend can override based on user's actual balances
        source_chain = "base"
        source_chain_id = 8453
        
        # LiFi bridge configuration
        lifi_config = {
            "source_chain": source_chain,
            "source_chain_id": source_chain_id,
            "destination_chain": "hyperliquid",
            "destination_chain_id": 1337,
            # USDC addresses
            "source_usdc": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",  # Base USDC
            "destination_usdc": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",  # HL Perps USDC
            # LiFi API endpoint for quote
            "lifi_quote_url": "https://li.quest/v1/quote",
        }
        
        if needs_deposit:
            deposit_amount = amount_float - total_on_hyperliquid
            
            steps.append({
                "step": 1,
                "action": "lifi_bridge",  # Changed from "deposit" to "lifi_bridge"
                "status": "pending",
                "description": f"Bridge {deposit_amount:.2f} USDC to Hyperliquid via LiFi",
                "source_chain": source_chain,
                "source_chain_id": source_chain_id,
                "destination_chain": "hyperliquid",
                "destination_chain_id": 1337,
                "amount": f"{deposit_amount:.2f}",
                "token": "USDC",
                "source_token_address": lifi_config["source_usdc"],
                "destination_token_address": lifi_config["destination_usdc"],
                "bridge_provider": "lifi",
                "estimated_time": "~30 seconds",
                "gas_paid_on": source_chain,  # User pays gas on source chain!
            })
            current_step = 1
        
        # Step 2: Transfer to Spot (if balance is in Perps)
        needs_transfer = (
            is_selling_usdc and 
            available_on_spot < amount_float and 
            (available_on_perps > 0 or needs_deposit)
        )
        
        if needs_transfer:
            transfer_amount = min(amount_float - available_on_spot, available_on_perps + (amount_float - total_on_hyperliquid if needs_deposit else 0))
            steps.append({
                "step": 2 if needs_deposit else 1,
                "action": "transfer_to_spot",
                "status": "pending",
                "description": f"Transfer {transfer_amount:.2f} USDC from Perps to Spot",
                "amount": f"{transfer_amount:.2f}",
                "token": "USDC",
                "estimated_time": "instant",
            })
            if not needs_deposit:
                current_step = 1
        
        # Step 3: Execute Swap (always needed)
        swap_step_num = len(steps) + 1
        steps.append({
            "step": swap_step_num,
            "action": "spot_swap",
            "status": "pending",
            "description": f"Swap {amount} {from_token} → {output_amount} {to_token}",
            "from_token": from_token,
            "to_token": to_token,
            "amount": amount,
            "expected_output": output_amount,
            "min_output": min_amount_out,
            "estimated_time": "instant",
        })
        
        # If no deposit/transfer needed, start at swap step
        if not needs_deposit and not needs_transfer:
            current_step = 1  # Swap is the only step
        
        # Build the complete execute_data
        execute_data = {
            "action_type": "swap",
            "provider": "hyperliquid",
            "execution_mode": "multi_step",
            "chain": "hyperliquid",  # Special chain identifier
            "from_token": from_token,
            "to_token": to_token,
            "amount": amount,
            "quote_amount": output_amount,
            "min_amount_out": min_amount_out,
            "price_impact": price_impact,
            "exchange_rate": exchange_rate,
            "slippage": slippage,
            "gas_estimate": "0",  # Zero gas on Hyperliquid
            "network_fee_usd": "0",
            "value_usd": value_usd,
            # Token addresses are null for Hyperliquid (not EVM)
            "from_token_address": None,
            "to_token_address": None,
            # Multi-step execution data
            "steps": steps,
            "current_step": current_step,
            "total_steps": len(steps),
            # Hyperliquid balance info
            "hyperliquid_balances": {
                "perps_usdc": hl_perps_usdc,
                "spot_usdc": hl_spot_usdc,
                "spot_from_token": hl_spot_from_token,
            },
            "requires_deposit": needs_deposit,
            "requires_transfer": needs_transfer,
            # LiFi bridge config (replaces old Arbitrum bridge config)
            "lifi_config": lifi_config,
            # Keep legacy bridge_config for backward compatibility
            "bridge_config": HYPERLIQUID_BRIDGE_CONTRACTS.get("arbitrum", {}),
        }
        
        return execute_data
    
    def _build_insufficient_balance_message(
        self,
        from_token: str,
        to_token: str,
        amount: str,
        user_balance: float,
        language: str,
    ) -> str:
        """
        Build message when user has insufficient balance to execute swap.
        Suggests adjusting amount if user has some balance.
        """
        amount_float = self._parse_amount_float(amount)
        available = user_balance * 0.90  # Leave 10% for gas
        
        if user_balance > 0.01:
            # User has some balance - suggest adjusting
            messages = {
                "en": f"""⚠️ **Insufficient balance for this swap**

**Swap requested:** {amount} {from_token} → {to_token}
**Your balance:** ${user_balance:.2f}

**Options:**
• ✅ **Swap what you have:** Say **"swap {available:.2f} {from_token} to {to_token}"**
• 💳 **Buy more crypto:** Say **"buy crypto"** or **"buy {amount_float:.0f}"**
• 📥 **Transfer from another wallet:** Send {from_token} to your Anvil wallet
""",
                "es": f"""⚠️ **Saldo insuficiente para este swap**

**Swap solicitado:** {amount} {from_token} → {to_token}
**Tu saldo:** ${user_balance:.2f}

**Opciones:**
• ✅ **Intercambia lo que tienes:** Di **"swap {available:.2f} {from_token} a {to_token}"**
• 💳 **Compra más cripto:** Di **"comprar cripto"**
• 📥 **Transfiere desde otra billetera**
""",
                "pt": f"""⚠️ **Saldo insuficiente para este swap**

**Swap solicitado:** {amount} {from_token} → {to_token}
**Seu saldo:** ${user_balance:.2f}

**Opções:**
• ✅ **Troque o que você tem:** Diga **"swap {available:.2f} {from_token} para {to_token}"**
• 💳 **Compre mais cripto:** Diga **"comprar cripto"**
• 📥 **Transfira de outra carteira**
""",
            }
        else:
            # User has no balance
            messages = {
                "en": f"""❌ **Unable to execute swap**

**Swap requested:** {amount} {from_token} → {to_token}
**Your balance:** $0.00

You need {from_token} in your wallet to complete this swap.

**Get started:**
• 💳 **Buy crypto:** Say **"buy crypto"** or **"buy {amount_float:.0f}"**
• 📥 **Transfer from another wallet:** Send {from_token} to your Anvil wallet
""",
                "es": f"""❌ **No se puede ejecutar el swap**

**Swap solicitado:** {amount} {from_token} → {to_token}
**Tu saldo:** $0.00

Necesitas {from_token} en tu billetera.

**Comienza:**
• 💳 **Compra cripto:** Di **"comprar cripto"**
• 📥 **Transfiere desde otra billetera**
""",
                "pt": f"""❌ **Não é possível executar o swap**

**Swap solicitado:** {amount} {from_token} → {to_token}
**Seu saldo:** $0.00

Você precisa de {from_token} na sua carteira.

**Comece:**
• 💳 **Compre cripto:** Diga **"comprar cripto"**
• 📥 **Transfira de outra carteira**
""",
            }
        return messages.get(language, messages["en"])
    
    async def _extract_swap_params(self, message: str) -> dict[str, Any]:
        """
        Extract swap parameters from user message.
        
        Uses LLM if available, otherwise falls back to regex parsing.
        """
        # Try LLM extraction first
        if self._llm:
            params = await self._extract_params_with_llm(
                message=message,
                param_schema={
                    "from_token": "string (token symbol like ETH, USDC)",
                    "to_token": "string (token symbol like ETH, USDC)",
                    "amount": "number (amount to swap)",
                    "chain": "string (blockchain: ethereum, base, arbitrum, polygon)",
                    "to_chain": "string or null (destination chain for cross-chain)",
                },
                examples=[
                    {
                        "input": "swap 100 USDC to PURR",
                        "output": '{"from_token": "USDC", "to_token": "PURR", "amount": "100", "chain": "base", "to_chain": null}'
                    },
                    {
                        "input": "swap 50 USDC to TRUMP",
                        "output": '{"from_token": "USDC", "to_token": "TRUMP", "amount": "50", "chain": "base", "to_chain": null}'
                    },
                    {
                        "input": "swap 1000 PEPE to USDC",
                        "output": '{"from_token": "PEPE", "to_token": "USDC", "amount": "1000", "chain": "base", "to_chain": null}'
                    },
                ],
            )
            
            if params.get("from_token") and params.get("to_token"):
                # Normalize token symbols
                params["from_token"] = params["from_token"].upper()
                params["to_token"] = params["to_token"].upper()
                if params.get("chain"):
                    params["chain"] = params["chain"].lower()
                if params.get("to_chain"):
                    params["to_chain"] = params["to_chain"].lower()
                return params
        
        # Fallback to regex parsing
        return self._parse_swap_params_regex(message)
    
    def _parse_swap_params_regex(self, message: str) -> dict[str, Any]:
        """Parse swap parameters using regex (fallback)."""
        params: dict[str, Any] = {"chain": "base"}
        
        message_lower = message.lower()
        message_upper = message.upper()
        
        # Extract amount (number with optional decimal)
        amount_match = re.search(r'(\d+\.?\d*)', message)
        if amount_match:
            params["amount"] = amount_match.group(1)
        
        # Extract tokens (common DeFi tokens)
        tokens = ["ETH", "WETH", "USDC", "USDT", "DAI", "WBTC", "BTC", "MATIC", "WMATIC", "SOL"]
        found_tokens = []
        for token in tokens:
            if token in message_upper:
                found_tokens.append(token)
        
        # Assign tokens based on position/context
        if len(found_tokens) >= 2:
            # Check for "X to Y" pattern
            to_match = re.search(r'(\w+)\s+to\s+(\w+)', message, re.IGNORECASE)
            if to_match:
                potential_from = to_match.group(1).upper()
                potential_to = to_match.group(2).upper()
                if potential_from in tokens:
                    params["from_token"] = potential_from
                if potential_to in tokens:
                    params["to_token"] = potential_to
            else:
                params["from_token"] = found_tokens[0]
                params["to_token"] = found_tokens[1]
        elif len(found_tokens) == 1:
            # Only one token - likely the source
            params["from_token"] = found_tokens[0]
        
        # Extract chain
        chains = {
            "ethereum": ["ethereum", "eth mainnet", "mainnet"],
            "base": ["base"],
            "arbitrum": ["arbitrum", "arb"],
            "polygon": ["polygon", "matic"],
            "optimism": ["optimism", "op"],
        }
        
        for chain, keywords in chains.items():
            if any(kw in message_lower for kw in keywords):
                # Check if it's source or destination chain
                if "to " + chain in message_lower or "on " + chain in message_lower:
                    params["chain"] = chain
                elif "from " + chain in message_lower:
                    params["chain"] = chain
                else:
                    params["chain"] = chain
                break
        
        return params
    
    def _is_hyperliquid_swap(self, from_token: str | None, to_token: str | None) -> bool:
        """
        Check if this swap should use Hyperliquid Spot.
        
        Hyperliquid Spot only supports meme tokens paired with USDC.
        One of the tokens MUST be USDC, and the other must be a supported meme token.
        """
        # Safety check for None values
        if not from_token or not to_token:
            return False
        
        from_upper = from_token.upper()
        to_upper = to_token.upper()
        
        # Same token swap is a no-op, not a Hyperliquid swap
        if from_upper == to_upper:
            return False
        
        # Check if one is USDC and the other is a Hyperliquid meme token (not USDC itself)
        if from_upper == "USDC" and to_upper in HYPERLIQUID_SPOT_TOKENS and to_upper != "USDC":
            return True
        if to_upper == "USDC" and from_upper in HYPERLIQUID_SPOT_TOKENS and from_upper != "USDC":
            return True
        
        # Both are meme tokens (rare but possible) - requires USDC as intermediary
        # This case would need two swaps, so we don't route it to Hyperliquid directly
        # Example: PURR → TRUMP would need PURR → USDC → TRUMP
        
        return False

    async def _fetch_quote(
        self,
        from_token: str,
        to_token: str,
        amount: str,
        chain: str,
        to_chain: str | None,
        wallet_address: str | None,
    ) -> dict[str, Any]:
        """
        Fetch swap quote from the appropriate provider.
        
        Provider Selection:
        1. Hyperliquid Spot: For meme tokens (PURR, TRUMP, etc.) paired with USDC
        2. 1inch: For major tokens same-chain swaps
        3. LiFi: For cross-chain swaps
        """
        is_cross_chain = to_chain and to_chain.lower() != chain.lower()
        
        try:
            # ============================================================
            # HYPERLIQUID SPOT: Meme tokens paired with USDC
            # ============================================================
            if self._is_hyperliquid_swap(from_token, to_token) and not is_cross_chain:
                if self._hyperliquid:
                    logger.info(
                        f"[SwapWorkflow] Using Hyperliquid Spot for meme token swap: "
                        f"{amount} {from_token} → {to_token}"
                    )
                    try:
                        # Hyperliquid uses human-readable amounts, not wei
                        amount_float = float(amount)
                        
                        quote = await self._hyperliquid.get_spot_quote(
                            from_token=from_token.upper(),
                            to_token=to_token.upper(),
                            amount=amount_float,
                        )
                        
                        # Hyperliquid uses its own API, NOT EVM contract addresses
                        # Don't provide fake addresses that will fail balanceOf calls
                        # Frontend should detect provider="hyperliquid" and use Hyperliquid SDK
                        
                        return {
                            "output_amount": f"{quote.to_amount:.6f}".rstrip('0').rstrip('.'),
                            "price_impact": quote.spread_bps / 100,  # Convert bps to %
                            "gas_estimate": 0,  # Hyperliquid = zero gas fees
                            "aggregator": "hyperliquid",
                            "mid_price": quote.mid_price,
                            "effective_price": quote.price,
                            # NOTE: No token addresses for Hyperliquid - it's not EVM-based
                            "from_token_address": None,
                            "to_token_address": None,
                        }
                    except Exception as hl_err:
                        logger.warning(
                            f"[SwapWorkflow] Hyperliquid quote failed for {from_token}/{to_token}: {hl_err}"
                        )
                        # Fall through to 1inch/LiFi if Hyperliquid fails
                else:
                    logger.warning(
                        f"[SwapWorkflow] Hyperliquid client not configured, "
                        f"cannot swap meme tokens: {from_token}/{to_token}"
                    )
            
            amount_wei = self._to_wei(amount, from_token)
            
            # ============================================================
            # CROSS-CHAIN: Use LiFi
            # ============================================================
            if is_cross_chain:
                if not self._lifi:
                    return {"error": "Cross-chain swaps require LiFi client (not configured)"}
                
                # Use a valid placeholder address if no wallet connected
                # LiFi requires a valid ETH address format
                sender_address = wallet_address or "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
                quote = await self._lifi.get_quote(
                    from_chain=chain,
                    to_chain=to_chain,
                    from_token=from_token,
                    to_token=to_token,
                    from_amount=amount_wei,
                    from_address=sender_address,
                )
                
                # Resolve addresses for cross-chain
                from_token_addr = self._resolve_token_address(from_token, chain)
                to_token_addr = self._resolve_token_address(to_token, to_chain)
                
                return {
                    "output_amount": self._from_wei(quote.to_amount, to_token),
                    "price_impact": getattr(quote, 'price_impact', 0),
                    "gas_estimate": int(getattr(quote, 'estimated_gas', 250000)),
                    "aggregator": "lifi",
                    "from_token_address": from_token_addr if from_token_addr.startswith("0x") else None,
                    "to_token_address": to_token_addr if to_token_addr.startswith("0x") else None,
                }
            
            # ============================================================
            # SAME-CHAIN MAJOR TOKENS: Try 1inch, fallback to LiFi
            # ============================================================
            if self._oneinch:
                # Primary: Use 1inch
                from_addr = self._resolve_token_address(from_token, chain)
                to_addr = self._resolve_token_address(to_token, chain)
                
                quote = await self._oneinch.get_swap_quote(
                    from_token=from_addr,
                    to_token=to_addr,
                    amount=amount_wei,
                    slippage=1.0,
                )
                
                return {
                    "output_amount": self._from_wei(quote.to_amount, to_token),
                    "price_impact": getattr(quote, 'price_impact', 0),
                    "gas_estimate": int(getattr(quote, 'estimated_gas', 200000)),
                    "aggregator": "1inch",
                    "from_token_address": from_addr if from_addr.startswith("0x") else None,
                    "to_token_address": to_addr if to_addr.startswith("0x") else None,
                }
            elif self._lifi:
                # Fallback: Use LiFi for same-chain swaps
                logger.info("[SwapWorkflow] Using LiFi fallback for same-chain swap")
                sender_address = wallet_address or "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
                
                # Resolve addresses for same-chain LiFi
                from_token_addr = self._resolve_token_address(from_token, chain)
                to_token_addr = self._resolve_token_address(to_token, chain)
                
                quote = await self._lifi.get_quote(
                    from_chain=chain,
                    to_chain=chain,  # Same chain
                    from_token=from_token,
                    to_token=to_token,
                    from_amount=amount_wei,
                    from_address=sender_address,
                )
                
                return {
                    "output_amount": self._from_wei(quote.to_amount, to_token),
                    "price_impact": getattr(quote, 'price_impact', 0),
                    "gas_estimate": int(getattr(quote, 'estimated_gas', 250000)),
                    "aggregator": "lifi",
                    "from_token_address": from_token_addr if from_token_addr.startswith("0x") else None,
                    "to_token_address": to_token_addr if to_token_addr.startswith("0x") else None,
                }
            else:
                return {"error": "Swap quote unavailable - no swap aggregator configured"}
                
        except Exception as e:
            logger.error(f"[SwapWorkflow] Quote fetch failed: {e}")
            return {"error": str(e)}
    
    def _to_wei(self, amount: str, token: str) -> str:
        """Convert human readable amount to wei."""
        decimals = TOKEN_DECIMALS.get(token.upper(), 18)
        try:
            value = float(amount) * (10 ** decimals)
            return str(int(value))
        except ValueError:
            return "0"
    
    def _from_wei(self, amount_wei: str, token: str) -> str:
        """Convert wei to human readable amount."""
        decimals = TOKEN_DECIMALS.get(token.upper(), 18)
        try:
            value = int(amount_wei) / (10 ** decimals)
            return f"{value:.6f}".rstrip('0').rstrip('.')
        except (ValueError, TypeError):
            return "0"
    
    def _resolve_token_address(self, token: str, chain: str) -> str:
        """Resolve token symbol to address."""
        if token.startswith("0x"):
            return token
        
        # First check chain-specific addresses
        chain_tokens = TOKEN_ADDRESSES.get(chain.lower(), {})
        if token.upper() in chain_tokens:
            return chain_tokens[token.upper()]
        
        # Then check Hyperliquid token addresses (for meme tokens)
        if token.upper() in HYPERLIQUID_TOKEN_ADDRESSES:
            return HYPERLIQUID_TOKEN_ADDRESSES[token.upper()]
        
        # Return symbol if no address found
        return token
    
    # Response formatting methods
    
    async def _get_token_selection_prompt(
        self,
        from_token: str,
        amount: str,
        user_context: UserContext,
    ) -> str:
        """
        Build token selection prompt with numbered list, prices, and user context.
        
        Includes:
        - Knowledge about Hyperliquid Spot and meme tokens
        - User's current balance (if available)
        - Real-time prices from CoinGecko
        """
        language = user_context.language
        
        # Try to fetch prices for popular tokens
        prices = await self._fetch_token_prices()
        
        # Build token list with prices
        token_lines = []
        for i, (symbol, description) in enumerate(POPULAR_MEME_TOKENS, 1):
            price_info = ""
            if prices.get(symbol.lower()):
                price = prices[symbol.lower()]
                price_info = f" • ${price:,.6f}"
            token_lines.append(f"**{i}.** {symbol}{price_info}")
        
        token_list = "\n".join(token_lines)
        
        # Build knowledge section
        knowledge_section = self._get_swap_knowledge(language)
        
        # Build user balance section
        user_balance_section = self._build_swap_user_balance_section(
            user_context=user_context,
            from_token=from_token,
            amount=amount,
            language=language,
        )
        
        msgs = {
            "en": f"""🔄 **Swap {amount} {from_token}**

{knowledge_section}

{user_balance_section}

**Select a meme token to receive:**

{token_list}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Reply with:**
• A number (1-10) to select
• Or type the token name (e.g., PURR)

💡 All swaps via **Hyperliquid Spot** (0.02% fee, zero gas)""",

            "es": f"""🔄 **Intercambiar {amount} {from_token}**

{knowledge_section}

{user_balance_section}

**Selecciona un meme token para recibir:**

{token_list}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Responde con:**
• Un número (1-10) para seleccionar
• O escribe el nombre del token (ej: PURR)

💡 Swaps via **Hyperliquid Spot** (0.02% comisión, sin gas)""",

            "pt": f"""🔄 **Trocar {amount} {from_token}**

{knowledge_section}

{user_balance_section}

**Selecione um meme token para receber:**

{token_list}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Responda com:**
• Um número (1-10) para selecionar
• Ou digite o nome do token (ex: PURR)

💡 Swaps via **Hyperliquid Spot** (0.02% taxa, sem gas)""",

            "zh": f"""🔄 **兑换 {amount} {from_token}**

{knowledge_section}

{user_balance_section}

**选择要接收的meme代币：**

{token_list}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**回复：**
• 数字 (1-10) 选择
• 或输入代币名称 (如: PURR)

💡 所有交易通过 **Hyperliquid Spot** (0.02% 手续费，零gas)""",
        }
        return msgs.get(language, msgs["en"])
    
    async def _fetch_token_prices(self) -> dict[str, float]:
        """
        Fetch current prices for popular meme tokens.
        
        Uses CoinGecko API if available, returns empty dict on error.
        """
        prices = {}
        
        if not self._coingecko:
            return prices
        
        try:
            # Map our tokens to CoinGecko IDs
            token_to_coingecko = {
                "purr": "purr-2",
                "trump": "official-trump",
                "pepe": "pepe",
                "mog": "mog-coin",
                "hfun": "hfun",
                "jeff": "jeff-2",
                "wagmi": "wagmi-2",
                "gmeow": "gmeow",
            }
            
            # Fetch prices for tokens we have mappings for
            coin_ids = list(token_to_coingecko.values())
            
            price_data = await self._coingecko.get_prices_bulk(coin_ids)
            
            if price_data:
                # Reverse map back to our symbols
                for symbol, coin_id in token_to_coingecko.items():
                    if coin_id in price_data:
                        price_obj = price_data[coin_id]
                        # Handle both Price object and dict
                        if hasattr(price_obj, "usd"):
                            prices[symbol] = price_obj.usd
                        elif isinstance(price_obj, dict) and "usd" in price_obj:
                            prices[symbol] = price_obj["usd"]
        except Exception as e:
            logger.warning(f"[SwapWorkflow] Failed to fetch token prices: {e}")
        
        return prices
    
    def _get_swap_knowledge(self, language: str) -> str:
        """Get knowledge paragraph about Hyperliquid Spot swaps."""
        msgs = {
            "en": """**What is Hyperliquid Spot?**
Trade meme tokens with zero gas fees and 0.02% trading fee.
High-speed execution (20,000+ TPS) on Hyperliquid L1.
Real-time order book pricing - no slippage surprises.""",

            "es": """**¿Qué es Hyperliquid Spot?**
Opera meme tokens con cero gas y 0.02% comisión.
Ejecución de alta velocidad (20,000+ TPS) en Hyperliquid L1.
Precios en tiempo real - sin sorpresas de slippage.""",

            "pt": """**O que é Hyperliquid Spot?**
Negocie meme tokens com zero gas e 0.02% de taxa.
Execução de alta velocidade (20,000+ TPS) no Hyperliquid L1.
Preços em tempo real - sem surpresas de slippage.""",

            "zh": """**什么是 Hyperliquid Spot？**
零 gas 费交易 meme 代币，仅 0.02% 交易费。
Hyperliquid L1 上的高速执行（20,000+ TPS）。
实时订单簿定价 - 无滑点意外。""",
        }
        return msgs.get(language, msgs["en"])
    
    def _build_swap_user_balance_section(
        self,
        user_context: UserContext,
        from_token: str,
        amount: str,
        language: str,
    ) -> str:
        """Build user balance context section for swap."""
        if not user_context.is_authenticated:
            return ""
        
        balance = user_context.total_balance_usd
        portfolio_state = user_context.portfolio_state
        
        try:
            swap_amount = float(amount)
        except (ValueError, TypeError):
            swap_amount = 0
        
        # Check if user has enough balance
        if portfolio_state == "empty" or balance < 1:
            # Note: Only USDC is available for purchase via card
            msgs = {
                "en": f"💰 **Your Balance:** $0.00\n\n⚠️ You'll need {from_token} first:\n• Say `buy crypto` to purchase USDC with card\n• Or transfer {from_token} from another wallet",
                "es": f"💰 **Tu Saldo:** $0.00\n\n⚠️ Necesitas {from_token} primero:\n• Di `comprar cripto` para comprar USDC\n• O transfiere {from_token} desde otra billetera",
                "pt": f"💰 **Seu Saldo:** $0.00\n\n⚠️ Você precisa de {from_token} primeiro:\n• Diga `comprar cripto` para comprar USDC\n• Ou transfira {from_token} de outra carteira",
                "zh": f"💰 **您的余额：** $0.00\n\n⚠️ 您需要先获取 {from_token}：\n• 说 `买加密货币` 购买 USDC\n• 或从其他钱包转入 {from_token}",
            }
        elif balance < swap_amount:
            msgs = {
                "en": f"💰 **Your Balance:** ~${balance:,.2f}\n\n⚠️ Swap amount (${swap_amount:,.2f}) exceeds your balance.\n💡 Consider a smaller amount or say `buy crypto` to get more USDC.",
                "es": f"💰 **Tu Saldo:** ~${balance:,.2f}\n\n⚠️ El monto del swap (${swap_amount:,.2f}) excede tu saldo.\n💡 Considera un monto menor o di `comprar cripto` para obtener más USDC.",
                "pt": f"💰 **Seu Saldo:** ~${balance:,.2f}\n\n⚠️ O valor do swap (${swap_amount:,.2f}) excede seu saldo.\n💡 Considere um valor menor ou diga `comprar cripto` para obter mais USDC.",
                "zh": f"💰 **您的余额：** ~${balance:,.2f}\n\n⚠️ 兑换金额 (${swap_amount:,.2f}) 超过您的余额。\n💡 考虑较小的金额或说 `买加密货币` 获取更多 USDC。",
            }
        else:
            msgs = {
                "en": f"💰 **Your Balance:** ~${balance:,.2f} ✅",
                "es": f"💰 **Tu Saldo:** ~${balance:,.2f} ✅",
                "pt": f"💰 **Seu Saldo:** ~${balance:,.2f} ✅",
                "zh": f"💰 **您的余额：** ~${balance:,.2f} ✅",
            }
        
        return msgs.get(language, msgs["en"])
    
    def _get_invalid_selection_response(self, user_input: str, language: str) -> str:
        """Response when user enters invalid token selection."""
        token_names = ", ".join([t[0] for t in POPULAR_MEME_TOKENS])
        
        msgs = {
            "en": f"""❌ **Invalid selection:** "{user_input}"

Please enter:
• A number from **1-10** to select a token
• Or type a valid token symbol like **PURR**, **TRUMP**, **PEPE**

**Available tokens:** {token_names}""",

            "es": f"""❌ **Selección inválida:** "{user_input}"

Por favor ingresa:
• Un número del **1-10** para seleccionar
• O escribe un símbolo válido como **PURR**, **TRUMP**, **PEPE**

**Tokens disponibles:** {token_names}""",

            "pt": f"""❌ **Seleção inválida:** "{user_input}"

Por favor insira:
• Um número de **1-10** para selecionar
• Ou digite um símbolo válido como **PURR**, **TRUMP**, **PEPE**

**Tokens disponíveis:** {token_names}""",

            "zh": f"""❌ **选择无效：** "{user_input}"

请输入：
• **1-10** 之间的数字选择代币
• 或输入有效的代币符号如 **PURR**, **TRUMP**, **PEPE**

**可用代币：** {token_names}""",
        }
        return msgs.get(language, msgs["en"])
    
    async def _get_missing_params_response(self, params: dict, user_context: "UserContext") -> str:
        """Response when tokens are missing - with smart examples based on user balance."""
        language = user_context.language
        user_balance_usd = user_context.total_balance_usd
        
        # Build smart examples based on user's actual balance
        examples_section = self._build_smart_swap_examples(user_balance_usd, language)
        
        # Build balance section
        if user_balance_usd < 1:
            balance_section = {
                "en": f"💰 **Your Balance:** ${user_balance_usd:.2f}\n\n💡 **Tip:** Say `buy crypto` to get USDC first!",
                "es": f"💰 **Tu Saldo:** ${user_balance_usd:.2f}\n\n💡 **Consejo:** ¡Di `comprar cripto` para obtener USDC primero!",
                "pt": f"💰 **Seu Saldo:** ${user_balance_usd:.2f}\n\n💡 **Dica:** Diga `comprar cripto` para obter USDC primeiro!",
                "zh": f"💰 **您的余额：** ${user_balance_usd:.2f}\n\n💡 **提示：** 说 `买加密货币` 先获取 USDC！",
            }.get(language, f"💰 **Your Balance:** ${user_balance_usd:.2f}\n\n💡 **Tip:** Say `buy crypto` to get USDC first!")
        else:
            balance_section = {
                "en": f"💰 **Your Balance:** ~${user_balance_usd:.2f}",
                "es": f"💰 **Tu Saldo:** ~${user_balance_usd:.2f}",
                "pt": f"💰 **Seu Saldo:** ~${user_balance_usd:.2f}",
                "zh": f"💰 **您的余额：** ~${user_balance_usd:.2f}",
            }.get(language, f"💰 **Your Balance:** ~${user_balance_usd:.2f}")
        
        msgs = {
            "en": f"""🔄 **Hyperliquid Spot Swaps**

{balance_section}

What meme token would you like to swap?

{examples_section}

**Supported:** PURR, TRUMP, PEPE, HFUN, MOG, GMEOW + 50 more meme tokens
**Note:** All swaps use USDC pairs. Major tokens (ETH, BTC, SOL) are NOT supported.""",
            
            "es": f"""🔄 **Swaps en Hyperliquid Spot**

{balance_section}

¿Qué meme token te gustaría intercambiar?

{examples_section}

**Soportados:** PURR, TRUMP, PEPE, HFUN, MOG, GMEOW + 50 más
**Nota:** Todos los swaps usan pares USDC. Tokens mayores (ETH, BTC, SOL) NO están soportados.""",
            
            "pt": f"""🔄 **Swaps no Hyperliquid Spot**

{balance_section}

Qual meme token você gostaria de trocar?

{examples_section}

**Suportados:** PURR, TRUMP, PEPE, HFUN, MOG, GMEOW + 50 mais
**Nota:** Todas as trocas usam pares USDC. Tokens maiores (ETH, BTC, SOL) NÃO são suportados.""",
            
            "zh": f"""🔄 **Hyperliquid Spot 交易**

{balance_section}

您想交换哪个meme代币？

{examples_section}

**支持：** PURR, TRUMP, PEPE, HFUN, MOG, GMEOW + 50多个meme代币
**注意：** 所有交易使用USDC交易对。主流代币（ETH, BTC, SOL）不支持。""",
        }
        return msgs.get(language, msgs["en"])
    
    def _build_smart_swap_examples(self, user_balance_usd: float, language: str) -> str:
        """Build balance-appropriate swap examples."""
        
        if user_balance_usd < 1:
            # Very low balance - suggest small amounts after buying
            msgs = {
                "en": """**Examples (after buying USDC):**
• `swap 5 USDC to PURR`
• `swap 10 USDC to TRUMP`""",
                "es": """**Ejemplos (después de comprar USDC):**
• `swap 5 USDC to PURR`
• `swap 10 USDC to TRUMP`""",
                "pt": """**Exemplos (após comprar USDC):**
• `swap 5 USDC to PURR`
• `swap 10 USDC to TRUMP`""",
                "zh": """**示例（购买 USDC 后）：**
• `swap 5 USDC to PURR`
• `swap 10 USDC to TRUMP`""",
            }
        elif user_balance_usd < 10:
            # Small balance - show realistic small amounts
            small_amt = max(1, user_balance_usd * 0.3)
            med_amt = max(2, user_balance_usd * 0.5)
            
            msgs = {
                "en": f"""**Examples based on your balance:**
• `swap {small_amt:.0f} USDC to PURR` (~{small_amt/user_balance_usd*100:.0f}% of balance)
• `swap {med_amt:.0f} USDC to TRUMP` (~{med_amt/user_balance_usd*100:.0f}% of balance)""",
                "es": f"""**Ejemplos basados en tu saldo:**
• `swap {small_amt:.0f} USDC to PURR` (~{small_amt/user_balance_usd*100:.0f}% del saldo)
• `swap {med_amt:.0f} USDC to TRUMP` (~{med_amt/user_balance_usd*100:.0f}% del saldo)""",
                "pt": f"""**Exemplos baseados no seu saldo:**
• `swap {small_amt:.0f} USDC to PURR` (~{small_amt/user_balance_usd*100:.0f}% do saldo)
• `swap {med_amt:.0f} USDC to TRUMP` (~{med_amt/user_balance_usd*100:.0f}% do saldo)""",
                "zh": f"""**基于您余额的示例：**
• `swap {small_amt:.0f} USDC to PURR` (~{small_amt/user_balance_usd*100:.0f}% 的余额)
• `swap {med_amt:.0f} USDC to TRUMP` (~{med_amt/user_balance_usd*100:.0f}% 的余额)""",
            }
        elif user_balance_usd < 100:
            # Medium balance
            small_amt = user_balance_usd * 0.2
            med_amt = user_balance_usd * 0.5
            
            msgs = {
                "en": f"""**Examples based on your balance:**
• `swap {small_amt:.0f} USDC to PURR` (~20% of balance)
• `swap {med_amt:.0f} USDC to TRUMP` (~50% of balance)
• `swap {user_balance_usd * 0.9:.0f} USDC to PEPE` (~90% of balance)""",
                "es": f"""**Ejemplos basados en tu saldo:**
• `swap {small_amt:.0f} USDC to PURR` (~20% del saldo)
• `swap {med_amt:.0f} USDC to TRUMP` (~50% del saldo)
• `swap {user_balance_usd * 0.9:.0f} USDC to PEPE` (~90% del saldo)""",
                "pt": f"""**Ejemplos basados no seu saldo:**
• `swap {small_amt:.0f} USDC to PURR` (~20% do saldo)
• `swap {med_amt:.0f} USDC to TRUMP` (~50% do saldo)
• `swap {user_balance_usd * 0.9:.0f} USDC to PEPE` (~90% do saldo)""",
                "zh": f"""**基于您余额的示例：**
• `swap {small_amt:.0f} USDC to PURR` (~20% 的余额)
• `swap {med_amt:.0f} USDC to TRUMP` (~50% 的余额)
• `swap {user_balance_usd * 0.9:.0f} USDC to PEPE` (~90% 的余额)""",
            }
        else:
            # Large balance - show nice round numbers
            msgs = {
                "en": f"""**Examples:**
• `swap 50 USDC to PURR`
• `swap 100 USDC to TRUMP`
• `swap 500 USDC to PEPE`""",
                "es": f"""**Ejemplos:**
• `swap 50 USDC to PURR`
• `swap 100 USDC to TRUMP`
• `swap 500 USDC to PEPE`""",
                "pt": f"""**Exemplos:**
• `swap 50 USDC to PURR`
• `swap 100 USDC to TRUMP`
• `swap 500 USDC to PEPE`""",
                "zh": f"""**示例：**
• `swap 50 USDC to PURR`
• `swap 100 USDC to TRUMP`
• `swap 500 USDC to PEPE`""",
            }
        
        return msgs.get(language, msgs["en"])
    
    def _get_amount_prompt(self, from_token: str, to_token: str, language: str) -> str:
        """Prompt for missing amount."""
        msgs = {
            "en": f"How much {from_token} would you like to swap to {to_token}?",
            "es": f"¿Cuánto {from_token} te gustaría intercambiar por {to_token}?",
            "pt": f"Quanto {from_token} você gostaria de trocar por {to_token}?",
            "zh": f"您想将多少 {from_token} 兑换为 {to_token}？",
        }
        return msgs.get(language, msgs["en"])
    
    def _get_quote_error_response(self, error: str, language: str) -> str:
        """Response when quote fetch fails - user-friendly message without technical details."""
        # Determine user-friendly error reason (without exposing URLs or technical details)
        error_lower = error.lower() if error else ""
        
        if "404" in error_lower or "not found" in error_lower:
            # Token not found or not supported on chain
            reason = {
                "en": "This token pair may not be available on this network.",
                "es": "Este par de tokens puede no estar disponible en esta red.",
                "pt": "Este par de tokens pode não estar disponível nesta rede.",
                "zh": "此代币对可能在该网络上不可用。",
            }
        elif "insufficient" in error_lower or "balance" in error_lower:
            reason = {
                "en": "Insufficient balance for this swap.",
                "es": "Saldo insuficiente para este intercambio.",
                "pt": "Saldo insuficiente para esta troca.",
                "zh": "余额不足以完成此交换。",
            }
        elif "slippage" in error_lower:
            reason = {
                "en": "Price movement too high. Try a smaller amount or increase slippage.",
                "es": "Movimiento de precio muy alto. Intenta con menos cantidad.",
                "pt": "Movimento de preço muito alto. Tente com menor quantidade.",
                "zh": "价格波动过大。尝试较小金额。",
            }
        elif "timeout" in error_lower or "timed out" in error_lower:
            reason = {
                "en": "The request timed out. Please try again.",
                "es": "La solicitud expiró. Por favor intenta de nuevo.",
                "pt": "A solicitação expirou. Por favor, tente novamente.",
                "zh": "请求超时。请重试。",
            }
        else:
            # Generic error - don't expose technical details
            reason = {
                "en": "Unable to get a quote at this time.",
                "es": "No se pudo obtener cotización en este momento.",
                "pt": "Não foi possível obter cotação no momento.",
                "zh": "目前无法获取报价。",
            }
        
        msgs = {
            "en": f"""⚠️ **Swap Quote Unavailable**

{reason.get(language, reason["en"])}

**What you can try:**
• Check if the token is available on this network
• Try a different token pair
• Try again in a moment

💡 Need help? Say "what tokens can I swap?" for supported pairs.""",
            "es": f"""⚠️ **Cotización no disponible**

{reason.get(language, reason["es"])}

**Puedes intentar:**
• Verificar si el token está disponible en esta red
• Probar un par diferente
• Intentar de nuevo en un momento""",
            "pt": f"""⚠️ **Cotação indisponível**

{reason.get(language, reason["pt"])}

**Você pode tentar:**
• Verificar se o token está disponível nesta rede
• Tentar um par diferente
• Tentar novamente em um momento""",
            "zh": f"""⚠️ **报价不可用**

{reason.get(language, reason["zh"])}

**您可以尝试:**
• 检查代币是否在此网络上可用
• 尝试不同的代币对
• 稍后再试""",
        }
        return msgs.get(language, msgs["en"])
    
    def _format_quote_response(self, data: dict, language: str) -> str:
        """Format swap quote response with enhanced market data."""
        from_token = data.get("from_token", "?")
        to_token = data.get("to_token", "?")
        amount = data.get("amount", "0")
        output = data.get("output_amount", "0")
        impact = data.get("price_impact", 0)
        aggregator = data.get("aggregator", "DEX")
        chain = data.get("chain", "base")
        
        # Market enrichment data
        market = data.get("market_data", {})
        from_price = market.get("from_token_price")
        from_24h = market.get("from_token_24h_change")
        gas_usd = market.get("gas_usd_estimate")
        gas_timing = market.get("gas_timing")
        
        # Calculate USD value
        try:
            amount_float = float(amount)
            usd_value = amount_float * from_price if from_price else None
        except (ValueError, TypeError):
            usd_value = None
        
        # Build market context section
        market_context = ""
        if from_price:
            change_str = ""
            if from_24h:
                emoji = "📈" if from_24h >= 0 else "📉"
                change_str = f" ({emoji} {from_24h:+.1f}% 24h)"
            market_context += f"💰 **{from_token} Price:** ${from_price:,.2f}{change_str}\n"
        
        if usd_value:
            market_context += f"💵 **Value:** ~${usd_value:,.2f} USD\n"
        
        # Gas info section
        gas_info = ""
        if gas_usd is not None:
            gas_info = f"⛽ **Est. Gas:** ~${gas_usd:.4f}"
            if gas_timing:
                gas_info += f"\n💡 {gas_timing}"
        
        msgs = {
            "en": f"""📊 **Swap Quote**

**{amount} {from_token}** → **{output} {to_token}**

{market_context}
• Price Impact: {impact:.2f}%
• Network: {chain.upper()}
• Aggregator: {aggregator.upper()}
{gas_info}

---
✅ Say **"yes"** or **"confirm"** to execute this swap
✏️ Or say **"swap [amount] {from_token} to {to_token}"** to change the amount
❌ Say **"cancel"** to cancel""",

            "es": f"""📊 **Cotización de Swap**

**{amount} {from_token}** → **{output} {to_token}**

{market_context}
• Impacto en precio: {impact:.2f}%
• Red: {chain.upper()}
• Agregador: {aggregator.upper()}
{gas_info}

---
✅ Di **"sí"** o **"confirmar"** para ejecutar este swap
✏️ O di **"swap [cantidad] {from_token} a {to_token}"** para cambiar la cantidad
❌ Di **"cancelar"** para cancelar""",

            "pt": f"""📊 **Cotação de Swap**

**{amount} {from_token}** → **{output} {to_token}**

{market_context}
• Impacto no preço: {impact:.2f}%
• Rede: {chain.upper()}
• Agregador: {aggregator.upper()}
{gas_info}

---
✅ Diga **"sim"** ou **"confirmar"** para executar este swap
✏️ Ou diga **"swap [quantidade] {from_token} para {to_token}"** para mudar a quantidade
❌ Diga **"cancelar"** para cancelar""",
        }
        
        return msgs.get(language, msgs["en"])
    
    def _get_confirm_prompt(self, language: str) -> str:
        """Re-prompt for confirmation (not used - frontend handles via execute_data card)."""
        msgs = {
            "en": "Review the swap details above.",
            "es": "Revisa los detalles del intercambio.",
            "pt": "Revise os detalhes da troca.",
            "zh": "查看上方的交换详情。",
        }
        return msgs.get(language, msgs["en"])
    
    def _get_cancel_response(self, language: str) -> str:
        """Response when user cancels."""
        msgs = {
            "en": "❌ Swap cancelled. Let me know if you want to try again!",
            "es": "❌ Intercambio cancelado. ¡Avísame si quieres intentarlo de nuevo!",
            "pt": "❌ Troca cancelada. Me avise se quiser tentar novamente!",
            "zh": "❌ 交换已取消。如果您想重试，请告诉我！",
        }
        return msgs.get(language, msgs["en"])
    
    def _get_continue_or_new_prompt(self, state: WorkflowState, language: str) -> str:
        """Prompt asking if user wants to continue last swap or start new."""
        from_token = state.data.get("from_token", "?")
        to_token = state.data.get("to_token", "?")
        amount = state.data.get("amount", "?")
        
        msgs = {
            "en": f"""🔄 **Continue or New Swap?**

I see you have a previous swap:
**{amount} {from_token} → {to_token}**

Would you like to:
1️⃣ **Continue** with this swap (say "yes" or "continue")
2️⃣ **Start fresh** with a new swap (say "new" or provide new swap details)

💡 Or just tell me what you want to swap, e.g., "swap 50 USDC to PURR\"""",
            "es": f"""🔄 **¿Continuar o Nuevo Intercambio?**

Veo que tienes un intercambio anterior:
**{amount} {from_token} → {to_token}**

¿Te gustaría:
1️⃣ **Continuar** con este intercambio (di "sí" o "continuar")
2️⃣ **Empezar de nuevo** con un nuevo intercambio (di "nuevo" o proporciona nuevos detalles)

💡 O simplemente dime qué quieres intercambiar, ej: "cambiar 50 USDC a PURR\"""",
            "pt": f"""🔄 **Continuar ou Nova Troca?**

Vejo que você tem uma troca anterior:
**{amount} {from_token} → {to_token}**

Você gostaria de:
1️⃣ **Continuar** com esta troca (diga "sim" ou "continuar")
2️⃣ **Começar de novo** com uma nova troca (diga "novo" ou forneça novos detalhes)

💡 Ou apenas me diga o que você quer trocar, ex: "trocar 50 USDC para PURR\"""",
            "zh": f"""🔄 **继续还是新交换？**

我看到您有一个之前的交换：
**{amount} {from_token} → {to_token}**

您想要：
1️⃣ **继续** 这个交换（说"是"或"继续"）
2️⃣ **重新开始** 新的交换（说"新"或提供新的交换详情）

💡 或者直接告诉我您想交换什么，例如："交换 50 USDC 到 PURR\"""",
        }
        return msgs.get(language, msgs["en"])
    
    def _get_auto_adjust_message(
        self,
        original_amount: str,
        recommended_amount: str,
        from_token: str,
        to_token: str,
        user_balance: float,
        language: str,
    ) -> str:
        """Message when auto-adjusting to available balance."""
        msgs = {
            "en": f"""⚠️ **Adjusting to your available balance**

You requested **{original_amount} {from_token}** but only have ~**${user_balance:.2f}** available.

I've adjusted the swap to **{recommended_amount} {from_token}** → **{to_token}**""",
            "es": f"""⚠️ **Ajustando a tu saldo disponible**

Solicitaste **{original_amount} {from_token}** pero solo tienes ~**${user_balance:.2f}** disponibles.

He ajustado el intercambio a **{recommended_amount} {from_token}** → **{to_token}**""",
            "pt": f"""⚠️ **Ajustando ao seu saldo disponível**

Você solicitou **{original_amount} {from_token}** mas só tem ~**${user_balance:.2f}** disponíveis.

Ajustei a troca para **{recommended_amount} {from_token}** → **{to_token}**""",
            "zh": f"""⚠️ **调整到您的可用余额**

您请求 **{original_amount} {from_token}** 但只有 ~**${user_balance:.2f}** 可用。

我已将交换调整为 **{recommended_amount} {from_token}** → **{to_token}**""",
        }
        return msgs.get(language, msgs["en"])
    
    def _get_zero_balance_message(self, from_token: str, language: str) -> str:
        """Message when user has zero usable balance."""
        msgs = {
            "en": f"""💳 **You need {from_token} to swap**

Your wallet doesn't have enough {from_token} for this swap.

**Get started:**
• 💳 Say **"buy crypto"** to purchase with card/Apple Pay/Google Pay
• 📥 Or transfer {from_token} from another wallet

Once you have funds, come back and try your swap again!""",
            "es": f"""💳 **Necesitas {from_token} para intercambiar**

Tu billetera no tiene suficiente {from_token} para este intercambio.

**Para empezar:**
• 💳 Di **"comprar crypto"** para comprar con tarjeta/Apple Pay/Google Pay
• 📥 O transfiere {from_token} desde otra billetera

¡Una vez que tengas fondos, vuelve e intenta tu intercambio de nuevo!""",
            "pt": f"""💳 **Você precisa de {from_token} para trocar**

Sua carteira não tem {from_token} suficiente para esta troca.

**Para começar:**
• 💳 Diga **"comprar crypto"** para comprar com cartão/Apple Pay/Google Pay
• 📥 Ou transfira {from_token} de outra carteira

Quando tiver fundos, volte e tente sua troca novamente!""",
            "zh": f"""💳 **您需要 {from_token} 来交换**

您的钱包没有足够的 {from_token} 进行此交换。

**开始:**
• 💳 说 **"购买加密货币"** 用卡/Apple Pay/Google Pay 购买
• 📥 或从另一个钱包转入 {from_token}

一旦您有资金，回来再试您的交换！""",
        }
        return msgs.get(language, msgs["en"])
    
    def _format_execute_response(
        self, 
        data: dict, 
        language: str,
        execute_data: dict | None = None,
    ) -> str:
        """Format ready-to-execute response."""
        from_token = data.get("from_token", "?")
        to_token = data.get("to_token", "?")
        amount = data.get("amount", "0")
        output = data.get("output_amount", "0")
        chain = data.get("chain", "base")
        
        # Check if this is a Hyperliquid multi-step swap requiring deposit
        is_hyperliquid_deposit = (
            execute_data 
            and execute_data.get("execution_mode") == "multi_step"
            and execute_data.get("requires_deposit")
        )
        
        if is_hyperliquid_deposit:
            total_steps = execute_data.get("total_steps", 3)
            lifi_config = execute_data.get("lifi_config", {})
            source_chain = lifi_config.get("source_chain", "base").capitalize()
            
            msgs = {
                "en": f"""✅ **Ready to Execute!**

**Swap Details:**
• From: {amount} {from_token}
• To: ~{output} {to_token}
• Network: Hyperliquid

**Multi-Step Swap** ({total_steps} steps):
1️⃣ Bridge {from_token} to Hyperliquid via LiFi
2️⃣ Transfer to Spot account
3️⃣ Execute swap

💡 Gas fees (~$0.35) will be paid on {source_chain} - no need for ETH on Arbitrum!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👉 Click **Execute** below to start the multi-step swap.""",

                "es": f"""✅ **¡Listo para Ejecutar!**

**Detalles del Swap:**
• De: {amount} {from_token}
• A: ~{output} {to_token}
• Red: Hyperliquid

**Swap Multi-Paso** ({total_steps} pasos):
1️⃣ Bridge {from_token} a Hyperliquid vía LiFi
2️⃣ Transferir a cuenta Spot
3️⃣ Ejecutar swap

💡 Los costos de gas (~$0.35) se pagarán en {source_chain} - ¡no necesitas ETH en Arbitrum!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👉 Haz clic en **Ejecutar** para iniciar el swap multi-paso.""",

                "pt": f"""✅ **Pronto para Executar!**

**Detalhes do Swap:**
• De: {amount} {from_token}
• Para: ~{output} {to_token}
• Rede: Hyperliquid

**Swap Multi-Etapas** ({total_steps} etapas):
1️⃣ Bridge {from_token} para Hyperliquid via LiFi
2️⃣ Transferir para conta Spot
3️⃣ Executar swap

💡 As taxas de gas (~$0.35) serão pagas em {source_chain} - não precisa de ETH em Arbitrum!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👉 Clique em **Executar** para iniciar o swap multi-etapas.""",
            }
            return msgs.get(language, msgs["en"])
        
        # Standard swap response
        msgs = {
            "en": f"""✅ **Ready to Execute!**

**Swap Details:**
• From: {amount} {from_token}
• To: ~{output} {to_token}
• Network: {chain.upper()}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👉 Click **Execute** below to sign the transaction with your wallet.""",

            "es": f"""✅ **¡Listo para Ejecutar!**

**Detalles del Swap:**
• De: {amount} {from_token}
• A: ~{output} {to_token}
• Red: {chain.upper()}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👉 Haz clic en **Ejecutar** abajo para firmar la transacción con tu billetera.""",

            "pt": f"""✅ **Pronto para Executar!**

**Detalhes do Swap:**
• De: {amount} {from_token}
• Para: ~{output} {to_token}
• Rede: {chain.upper()}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👉 Clique em **Executar** abaixo para assinar a transação com sua carteira.""",
        }
        
        return msgs.get(language, msgs["en"])
