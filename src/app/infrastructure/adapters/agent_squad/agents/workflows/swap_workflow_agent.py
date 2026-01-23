"""
Swap Workflow Agent - Multi-Step Token Swap Operations.

Handles the complete swap workflow for authenticated users:
1. Parse request: Extract tokens and amount from user message
2. Fetch quote: Get best quote from 1inch (same-chain) or LiFi (cross-chain)
3. Confirm: Show quote and wait for user confirmation
4. Execute: Generate execute_data for frontend execution

Integration:
- Same-chain swaps: Uses 1inch API
- Cross-chain swaps: Uses LiFi API
- Execution: Frontend uses Privy SDK with execute_data

Example Conversation:
    User: "swap 0.5 ETH to USDC"
    Agent: "📊 Swap Quote: 0.5 ETH → 1,245 USDC (price impact: 0.02%). Confirm?"
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
    from app.domain.ports.agent_squad.llm_client_gateway import LLMClientGateway

logger = logging.getLogger(__name__)


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
    },
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
    2. fetch_data: Get quotes from 1inch/LiFi
    3. confirm: Show quote, wait for user confirmation
    4. execute: Generate execute_data for frontend
    
    Features:
    - Natural language parameter extraction
    - Same-chain swaps via 1inch
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
    ):
        """
        Initialize swap workflow agent.
        
        Args:
            llm_client: LLM client for parameter extraction
            oneinch_client: 1inch API client for same-chain swaps
            lifi_client: LiFi API client for cross-chain swaps
            coingecko_client: CoinGecko client for market data enrichment
        """
        super().__init__(llm_client=llm_client)
        self._oneinch = oneinch_client
        self._lifi = lifi_client
        self._coingecko = coingecko_client
    
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
        
        logger.info(f"[SwapWorkflow] Processing step={step}, message={message.value[:50]}...")
        
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
        """
        params = await self._extract_swap_params(message.value)
        
        # Check for required parameters
        if not params.get("from_token") or not params.get("to_token"):
            # Ask for missing info
            response = self._get_missing_params_response(params, user_context.language)
            return response, state
        
        # Update state with extracted params
        state.data.update(params)
        
        # If amount is missing, ask for it
        if not params.get("amount"):
            response = self._get_amount_prompt(
                params["from_token"],
                params["to_token"],
                user_context.language,
            )
            state.step = WorkflowStep.PARSE_REQUEST.value  # Stay in parse step
            return response, state
        
        # All params available - proceed to fetch quote
        state.step = WorkflowStep.FETCH_DATA.value
        return await self._handle_fetch_quote(message, state, user_context)
    
    async def _handle_fetch_quote(
        self,
        message: MessageContent,
        state: WorkflowState,
        user_context: UserContext,
    ) -> tuple[str, WorkflowState]:
        """
        Step 2: Fetch swap quote from 1inch/LiFi with enhanced market data.
        """
        from_token = state.data.get("from_token", "ETH")
        to_token = state.data.get("to_token", "USDC")
        amount = state.data.get("amount", "0")
        chain = state.data.get("chain", "base")
        to_chain = state.data.get("to_chain")
        
        is_cross_chain = to_chain and to_chain.lower() != chain.lower()
        
        logger.info(
            f"[SwapWorkflow] Fetching quote: {amount} {from_token} → {to_token} "
            f"on {chain}" + (f" → {to_chain}" if is_cross_chain else "")
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
            return response, state
        
        # Store quote in state
        state.data["quote"] = quote_result
        state.data["output_amount"] = quote_result.get("output_amount", "0")
        state.data["price_impact"] = quote_result.get("price_impact", 0)
        state.data["aggregator"] = quote_result.get("aggregator", "unknown")
        state.data["gas_estimate"] = quote_result.get("gas_estimate", 200000)
        
        # Fetch enhanced market data (prices, gas info)
        market_data = await self._fetch_market_enrichment(from_token, to_token, chain)
        state.data["market_data"] = market_data
        
        # Move to confirm step
        state.step = WorkflowStep.CONFIRM.value
        
        # Format quote response with enhanced market data
        response = self._format_quote_response(state.data, user_context.language)
        return response, state
    
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
            # User cancelled
            state.cancelled = True
            state.step = WorkflowStep.CANCELLED.value
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
        """
        from_token = state.data.get("from_token", "ETH")
        to_token = state.data.get("to_token", "USDC")
        amount = state.data.get("amount", "0")
        chain = state.data.get("chain", "base")
        to_chain = state.data.get("to_chain")
        aggregator = state.data.get("aggregator", "1inch")
        
        # Build execute_data for frontend
        execute_data = self._build_execute_data(
            action_type="swap",
            provider=aggregator,
            chain=chain,
            from_token=from_token,
            to_token=to_token,
            amount=amount,
            slippage=1.0,  # Default 1% slippage
            to_chain=to_chain,
        )
        
        # Store execute_data in state
        state.execute_data = execute_data
        state.step = WorkflowStep.COMPLETED.value
        
        # Format ready-to-execute response
        response = self._format_execute_response(state.data, user_context.language)
        return response, state
    
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
                        "input": "swap 0.5 ETH to USDC",
                        "output": '{"from_token": "ETH", "to_token": "USDC", "amount": "0.5", "chain": "base", "to_chain": null}'
                    },
                    {
                        "input": "convert 100 USDC to ETH on arbitrum",
                        "output": '{"from_token": "USDC", "to_token": "ETH", "amount": "100", "chain": "arbitrum", "to_chain": null}'
                    },
                    {
                        "input": "bridge 1 ETH from ethereum to base",
                        "output": '{"from_token": "ETH", "to_token": "ETH", "amount": "1", "chain": "ethereum", "to_chain": "base"}'
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
        Fetch swap quote from 1inch or LiFi.
        """
        is_cross_chain = to_chain and to_chain.lower() != chain.lower()
        
        try:
            amount_wei = self._to_wei(amount, from_token)
            
            if is_cross_chain:
                # Cross-chain: Use LiFi
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
                
                return {
                    "output_amount": self._from_wei(quote.to_amount, to_token),
                    "price_impact": getattr(quote, 'price_impact', 0),
                    "gas_estimate": int(getattr(quote, 'estimated_gas', 250000)),
                    "aggregator": "lifi",
                    # Note: raw_quote removed to ensure JSON serialization
                }
            else:
                # Same-chain: Try 1inch first, fallback to LiFi
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
                        # Note: raw_quote removed to ensure JSON serialization
                    }
                elif self._lifi:
                    # Fallback: Use LiFi for same-chain swaps
                    logger.info("[SwapWorkflow] Using LiFi fallback for same-chain swap")
                    # Use a valid placeholder address if no wallet connected
                    sender_address = wallet_address or "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
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
                        # Note: raw_quote removed to ensure JSON serialization
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
        
        chain_tokens = TOKEN_ADDRESSES.get(chain.lower(), {})
        return chain_tokens.get(token.upper(), token)
    
    # Response formatting methods
    
    def _get_missing_params_response(self, params: dict, language: str) -> str:
        """Response when tokens are missing."""
        msgs = {
            "en": "What tokens would you like to swap? For example: 'swap 0.5 ETH to USDC'",
            "es": "¿Qué tokens te gustaría intercambiar? Por ejemplo: 'swap 0.5 ETH to USDC'",
            "pt": "Quais tokens você gostaria de trocar? Por exemplo: 'swap 0.5 ETH to USDC'",
            "zh": "您想交换哪些代币？例如：'swap 0.5 ETH to USDC'",
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
        """Response when quote fetch fails."""
        msgs = {
            "en": f"❌ Unable to get swap quote: {error}\n\nPlease try again or adjust your swap parameters.",
            "es": f"❌ No se pudo obtener la cotización: {error}\n\nIntenta de nuevo o ajusta los parámetros.",
            "pt": f"❌ Não foi possível obter a cotação: {error}\n\nTente novamente ou ajuste os parâmetros.",
            "zh": f"❌ 无法获取报价: {error}\n\n请重试或调整参数。",
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

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Ready to swap?**
Reply "yes" to confirm or "cancel" to abort.
You can also modify: "change to 1 ETH" """,

            "es": f"""📊 **Cotización de Swap**

**{amount} {from_token}** → **{output} {to_token}**

{market_context}
• Impacto en precio: {impact:.2f}%
• Red: {chain.upper()}
• Agregador: {aggregator.upper()}
{gas_info}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**¿Listo para intercambiar?**
Responde "sí" para confirmar o "cancelar" para abortar.""",

            "pt": f"""📊 **Cotação de Swap**

**{amount} {from_token}** → **{output} {to_token}**

{market_context}
• Impacto no preço: {impact:.2f}%
• Rede: {chain.upper()}
• Agregador: {aggregator.upper()}
{gas_info}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Pronto para trocar?**
Responda "sim" para confirmar ou "cancelar" para abortar.""",
        }
        
        return msgs.get(language, msgs["en"])
    
    def _get_confirm_prompt(self, language: str) -> str:
        """Re-prompt for confirmation."""
        msgs = {
            "en": "Would you like to proceed with this swap? Reply 'yes' to confirm or 'cancel' to abort.",
            "es": "¿Te gustaría proceder con este intercambio? Responde 'sí' para confirmar o 'cancelar' para abortar.",
            "pt": "Gostaria de prosseguir com esta troca? Responda 'sim' para confirmar ou 'cancelar' para abortar.",
            "zh": "您想继续这次交换吗？回复'是'确认或'取消'中止。",
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
    
    def _format_execute_response(self, data: dict, language: str) -> str:
        """Format ready-to-execute response."""
        from_token = data.get("from_token", "?")
        to_token = data.get("to_token", "?")
        amount = data.get("amount", "0")
        output = data.get("output_amount", "0")
        chain = data.get("chain", "base")
        
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
