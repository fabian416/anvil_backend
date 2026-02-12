"""
Swap Workflow Agent - Multi-Step Token Swap Operations.

Handles the complete swap workflow for authenticated users:
1. Parse request: Extract tokens and amount from user message
2. Fetch quote: Get best quote from appropriate provider:
   - Hyperliquid Spot: For 440+ tokens (PURR, TRUMP, PEPE, etc.) paired with USDC
   - 1inch: For major tokens same-chain swaps (ETH, BTC, USDC, etc.)
   - LiFi: For cross-chain swaps
3. Confirm: Show quote and wait for user confirmation
4. Execute: Generate execute_data for frontend execution

Integration:
- Token swaps: Uses Hyperliquid Spot API (440+ tokens, zero gas fees, high performance)
- Same-chain major tokens: Uses 1inch API
- Cross-chain swaps: Uses LiFi API
- Execution: Frontend uses Privy SDK with execute_data

Hyperliquid Spot has 440+ tokens paired with USDC.
Some major L1 tokens (ETH, BTC, SOL) may not be on HL Spot — use 1inch or LiFi for those.

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
    from app.infrastructure.adapters.external.hyperliquid_client import (
        HyperliquidClient,
    )
    from app.domain.ports.agent_squad.llm_client_gateway import LLMClientGateway
    from app.infrastructure.adapters.wallet_balance_db import WalletBalanceDbAdapter

logger = logging.getLogger(__name__)


async def _get_token_balances_for_wallet(
    wallet_address: str,
) -> dict[str, dict[str, Any]]:
    """
    Query all token balances from the token_balances table.

    Returns dict mapping chain name to token info:
    {
        "ethereum": {
            "eth_balance": 0.00070785,
            "can_pay_gas": True,
            "usdc_balance": 2.80,
            "weth_balance": 0.00081710,
            "total_usd": 6.16
        },
        ...
    }
    """
    try:
        from sqlalchemy import create_engine, text
        from sqlalchemy.pool import NullPool
        import os

        # Get database URL from environment or config
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            # Try to construct from individual vars
            db_host = os.environ.get("POSTGRES_HOST", "localhost")
            db_port = os.environ.get("POSTGRES_PORT", "5432")
            db_user = os.environ.get("POSTGRES_USER", "postgres")
            db_pass = os.environ.get("POSTGRES_PASSWORD", "changethis")
            db_name = os.environ.get("POSTGRES_DB", "anvil_db")
            db_url = f"postgresql+psycopg://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"

        # Use sync engine with NullPool for one-off queries
        engine = create_engine(db_url, poolclass=NullPool)

        chain_balances: dict[str, dict[str, Any]] = {}

        with engine.connect() as conn:
            result = conn.execute(
                text("""
                SELECT 
                    tb.chain,
                    tb.token_symbol,
                    tb.balance_human,
                    tb.balance_usd,
                    tb.can_pay_gas,
                    tb.is_stablecoin
                FROM token_balances tb
                JOIN wallets w ON w.id = tb.wallet_id
                WHERE LOWER(w.address) = LOWER(:addr)
                ORDER BY tb.chain, tb.token_symbol
            """),
                {"addr": wallet_address},
            )

            for row in result:
                chain = str(row[0])
                symbol = str(row[1])
                balance = float(row[2]) if row[2] else 0.0
                usd = float(row[3]) if row[3] else 0.0
                can_gas = bool(row[4])
                is_stable = bool(row[5])

                if chain not in chain_balances:
                    chain_balances[chain] = {
                        "eth_balance": 0.0,
                        "can_pay_gas": False,
                        "usdc_balance": 0.0,
                        "weth_balance": 0.0,
                        "total_usd": 0.0,
                        "tokens": {},
                    }

                chain_balances[chain]["tokens"][symbol] = {
                    "balance": balance,
                    "usd": usd,
                    "can_pay_gas": can_gas,
                    "is_stablecoin": is_stable,
                }
                chain_balances[chain]["total_usd"] += usd

                # Set convenience fields
                if symbol == "ETH" and can_gas:
                    chain_balances[chain]["eth_balance"] = balance
                    chain_balances[chain]["can_pay_gas"] = (
                        balance > 0.0001
                    )  # Min ~$0.20 for gas
                elif symbol == "USDC":
                    chain_balances[chain]["usdc_balance"] = balance
                elif symbol == "WETH":
                    chain_balances[chain]["weth_balance"] = balance

        engine.dispose()
        return chain_balances

    except Exception as e:
        logger.warning(f"Failed to query token balances from DB: {e}")
        return {}


def _find_best_chain_for_gas(
    chain_balances: dict[str, dict[str, Any]],
    supported_chains: list[str],
    min_eth_required: float = 0.0002,
) -> tuple[str | None, dict[str, Any]]:
    """
    Find the best chain for gas fees from supported chains.

    Uses the token_balances table with can_pay_gas flag.

    Args:
        chain_balances: Dict from _get_token_balances_for_wallet()
        supported_chains: List of chain names to consider
        min_eth_required: Minimum ETH required for gas (default ~$0.40)

    Returns:
        Tuple of (chain name, gas info dict) or (None, error info)
    """
    gas_info: dict[str, Any] = {
        "chains_checked": {},
        "best_chain": None,
        "min_eth_required": min_eth_required,
    }

    for chain in supported_chains:
        chain_data = chain_balances.get(chain, {})
        eth_balance = chain_data.get("eth_balance", 0.0)
        can_pay = chain_data.get("can_pay_gas", False)

        gas_info["chains_checked"][chain] = {
            "eth_balance": eth_balance,
            "can_pay_gas": can_pay,
            "has_enough": eth_balance >= min_eth_required,
        }

        if can_pay and eth_balance >= min_eth_required:
            logger.info(
                f"Best chain for gas: {chain} ({eth_balance:.6f} ETH >= {min_eth_required})"
            )
            gas_info["best_chain"] = chain
            return chain, gas_info

    logger.warning(f"No chain has sufficient ETH for gas. Checked: {supported_chains}")
    gas_info["error"] = "No chain has sufficient native ETH for gas fees"
    return None, gas_info


# =============================================================================
# HYPERLIQUID SPOT TOKENS - PRIMARY SWAP PROVIDER
# =============================================================================
# Anvil uses Hyperliquid Spot as the primary swap provider.
# Hyperliquid Spot has 440+ tokens paired with USDC.
# Some major L1 tokens (ETH, BTC, etc.) may not be on HL Spot.
# =============================================================================

HYPERLIQUID_SPOT_TOKENS = {
    "USDC",  # Quote currency (required for all Hyperliquid spot swaps)
    # Popular tokens on Hyperliquid Spot (440+ available)
    "PURR",
    "HFUN",
    "TRUMP",
    "PEPE",
    "MOG",
    "POINTS",
    "JEFF",
    "GMEOW",
    "LICK",
    "MANLET",
    "SIX",
    "WAGMI",
    "CAPPY",
    "XULIAN",
    "RUG",
    "CZ",
    "BAGS",
    "ANSEM",
    "TATE",
    "FUN",
    "BIGBEN",
    "KOBE",
    "VEGAS",
    "PUMP",
    "SCHIZO",
    "CATNIP",
    "HAPPY",
    "SELL",
    "HBOOST",
    "GPT",
    "PANDA",
    "HODL",
    "RAGE",
    "ASI",
    "LEAP",
    "VAPOR",
    "X",
    "PILL",
    "CAT",
    "HPEPE",
    "MBAPPE",
    "MAGA",
    "OMNIX",
    "COKE",
    "MEOW",
    "ANT",
    "NEIRO",
    # Bridged/wrapped major tokens on Hyperliquid Spot
    "UBTC",
    "UETH",
    "USOL",
    "LINK0",
    "AAVE0",
    "AVAX0",
    "FXRP",
    "HSEI",
}

# ---------------------------------------------------------------------------
# Major-token → Hyperliquid wrapper mapping
# ---------------------------------------------------------------------------
# Hyperliquid uses bridged/wrapped versions of major L1 tokens.
# When a user says "swap BTC" we transparently route to "UBTC" on HL Spot.
# The mapping is {GENERIC_SYMBOL: HL_WRAPPER_SYMBOL}.
MAJOR_TOKEN_TO_HL_WRAPPER: dict[str, str] = {
    "BTC": "UBTC",
    "ETH": "UETH",
    "SOL": "USOL",
    "LINK": "LINK0",
    "AAVE": "AAVE0",
    "AVAX": "AVAX0",
    "XRP": "FXRP",
    "SEI": "HSEI",
}

# Reverse lookup: wrapper → generic name (for display purposes)
HL_WRAPPER_TO_MAJOR: dict[str, str] = {
    v: k for k, v in MAJOR_TOKEN_TO_HL_WRAPPER.items()
}

# Major tokens that are NOT supported for swaps on Anvil
# Users should use external DEXs for these tokens
# NOTE: tokens present in MAJOR_TOKEN_TO_HL_WRAPPER are handled via
# wrapper mapping and should NOT appear here.
UNSUPPORTED_SWAP_TOKENS = {
    "WBTC",
    "WETH",
    "UNI",
    "CRV",
    "MKR",
    "DAI",
    "USDT",
    "MATIC",
    "ARB",
    "OP",
    "DOT",
    "ATOM",
    "APT",
    "SUI",
    "TIA",
    "INJ",
    "FTM",
    "ADA",
    "DOGE",
    "LTC",
    "SHIB",
}


# Popular tokens for selection menu (ordered by trading volume)
# Major tokens first (auto-mapped to HL wrappers), then popular meme tokens
POPULAR_TOKENS = [
    ("BTC", "Bitcoin (via UBTC)"),
    ("ETH", "Ethereum (via UETH)"),
    ("SOL", "Solana (via USOL)"),
    ("XRP", "Ripple (via FXRP)"),
    ("LINK", "Chainlink (via LINK0)"),
    ("AAVE", "Aave (via AAVE0)"),
    ("AVAX", "Avalanche (via AVAX0)"),
    ("PURR", "Hyperliquid's native token"),
    ("HFUN", "Hyperliquid Fun token"),
    ("TRUMP", "Political token"),
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
        # Tokens on Base (Hyperliquid Spot uses these for swaps)
        "PURR": "0x9b4e2579374e1b3ce1b31e0c55e8e7c3e2d5b0e1",  # Placeholder - will be updated from API
        "TRUMP": "0xCf20a0a767f4513C1c3C8B1c1e0e4F3E7c8b0F9A",  # Placeholder - will be updated from API
    },
}

# =============================================================================
# HYPERLIQUID BRIDGE CONTRACTS
# =============================================================================
# Users must bridge USDC to Hyperliquid before swapping tokens.
# The bridge deposits to Hyperliquid Perps account, then user transfers to Spot.
# Flow: EVM USDC → Bridge → Hyperliquid Perps → Transfer → Hyperliquid Spot → Swap
# =============================================================================

HYPERLIQUID_BRIDGE_CONTRACTS = {
    # Arbitrum is the primary supported chain for Hyperliquid deposits
    "arbitrum": {
        "bridge": "0x2Df1c51E09aECF9cacB7bc98cB1742757f163dF7",  # Hyperliquid deposit contract
        "usdc": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",  # Native USDC on Arbitrum
        "chain_id": 42161,
    },
    # Base support (may require bridging to Arbitrum first)
    "base": {
        "bridge": None,  # No direct bridge - must go via Arbitrum
        "usdc": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",  # Native USDC on Base
        "chain_id": 8453,
    },
}

# Hyperliquid token identifiers (tokens on Hyperliquid L1)
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
       - Hyperliquid Spot for 440+ tokens (PURR, TRUMP, etc.)
       - 1inch for major tokens same-chain
       - LiFi for cross-chain
    3. confirm: Show quote, wait for user confirmation
    4. execute: Generate execute_data for frontend

    Features:
    - Intelligent provider routing based on token type
    - Token swaps via Hyperliquid Spot (440+ tokens, zero gas fees)
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
            hyperliquid_client: Hyperliquid client for spot token swaps
        """
        super().__init__(llm_client=llm_client)
        self._oneinch = oneinch_client
        self._lifi = lifi_client
        self._coingecko = coingecko_client
        self._hyperliquid = hyperliquid_client
        # Cached set of base-token names with active HL spot markets.
        # Populated lazily by _get_tradeable_spot_tokens(); used by
        # _is_hyperliquid_swap() so routing covers all 263+ tokens,
        # not just the hardcoded HYPERLIQUID_SPOT_TOKENS subset.
        self._cached_tradeable_spot: set[str] | None = None

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

        logger.info(
            f"[SwapWorkflow] Processing step={step}, message={message.value[:50]}..."
        )

        # ── "My swaps" position viewing ──────────────────────────────
        # Detect position-viewing keywords and route to positions handler.
        # This must be checked BEFORE normal swap flow so "my swaps" is
        # handled even when the user is mid-workflow.
        my_swaps_keywords = [
            "my swaps",
            "my swap",
            "my trades",
            "my positions",
            "swap positions",
            "show my swaps",
            "show swaps",
            "mis swaps",
            "mis intercambios",
            "mis trades",
            "meus swaps",
            "meus trades",
            "我的交换",
        ]
        if any(kw in text_lower for kw in my_swaps_keywords):
            logger.info("[SwapWorkflow] 'my swaps' detected → showing positions")
            state = WorkflowState()
            state.step = WorkflowStep.PARSE_REQUEST.value
            state.data["action"] = "view_positions"
            return await self._handle_my_swaps_request(message, state, user_context)

        # Handle "refresh" – trigger on-demand sync then re-show positions
        if text_lower in ("refresh", "actualizar", "atualizar", "refrescar"):
            logger.info("[SwapWorkflow] 'refresh' detected → on-demand sync")
            await self._trigger_on_demand_sync(user_context)
            state = WorkflowState()
            state.step = WorkflowStep.PARSE_REQUEST.value
            state.data["action"] = "view_positions"
            return await self._handle_my_swaps_request(message, state, user_context)

        # If awaiting swap-from-position selection, route there
        if state.data.get("awaiting_swap_position_selection"):
            return await self._handle_swap_position_selection(
                message, state, user_context
            )

        # If awaiting destination token after position selection, route there
        if state.data.get("awaiting_swap_destination"):
            return await self._handle_swap_destination(message, state, user_context)

        # If awaiting amount after destination was chosen, handle it
        if state.data.get("awaiting_swap_amount_from_position"):
            return await self._handle_swap_amount_from_position(
                message, state, user_context
            )

        # Check if user wants to continue or start new after EXECUTE/COMPLETED
        # If user just says "swap" without full params after an executed swap,
        # ask if they want to repeat the last swap or start fresh
        if step in (WorkflowStep.EXECUTE.value, WorkflowStep.COMPLETED.value):
            # Check if user is saying just "swap" without specific params
            simple_swap_keywords = [
                "swap",
                "exchange",
                "trade",
                "cambiar",
                "trocar",
                "intercambiar",
            ]
            is_simple_swap = text_lower in simple_swap_keywords or text_lower in [
                "i want to swap",
                "quiero cambiar",
                "quiero intercambiar",
                "swap again",
                "another swap",
                "repeat",
                "again",
                "repetir",
                "de nuevo",
                "otra vez",
            ]

            # Check if user wants to continue with last swap
            continue_keywords = [
                "yes",
                "si",
                "sí",
                "sim",
                "continue",
                "continuar",
                "repeat",
                "repetir",
                "again",
                "de nuevo",
            ]
            wants_continue = text_lower in continue_keywords

            # Check if user wants to start fresh
            fresh_keywords = [
                "new",
                "nuevo",
                "nova",
                "fresh",
                "start over",
                "empezar de nuevo",
                "começar de novo",
                "different",
                "diferente",
            ]
            wants_fresh = any(kw in text_lower for kw in fresh_keywords)

            if (
                wants_continue
                and state.data.get("from_token")
                and state.data.get("to_token")
            ):
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

            elif (
                is_simple_swap
                and state.data.get("from_token")
                and state.data.get("to_token")
            ):
                # User said "swap" without params after a completed swap - ask what they want
                logger.info(
                    f"[SwapWorkflow] User said 'swap' after execute - asking if continue or new"
                )
                state.data["awaiting_continue_choice"] = True
                state.execute_data = None  # Don't show execute until user confirms
                return self._get_continue_or_new_prompt(state, language), state

        # Check if user is responding to continue/new prompt
        if state.data.get("awaiting_continue_choice"):
            continue_keywords = [
                "yes",
                "si",
                "sí",
                "sim",
                "continue",
                "continuar",
                "1",
                "repeat",
                "repetir",
                "last",
                "anterior",
            ]
            fresh_keywords = [
                "no",
                "new",
                "nuevo",
                "nova",
                "2",
                "fresh",
                "different",
                "diferente",
                "start",
            ]

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
                    return await self._handle_parse_request(
                        message, state, user_context
                    )
                # Re-prompt
                return self._get_continue_or_new_prompt(state, language), state

        # Check if user wants to start a NEW swap flow (restart detection)
        # This resets state when user says "swap 100 USDC to ETH", etc.
        # while already in an ongoing flow (FETCH_DATA, CONFIRM step)
        if step in (WorkflowStep.FETCH_DATA.value, WorkflowStep.CONFIRM.value):
            # Only restart if user provides specific swap params (not just "swap")
            new_params = await self._extract_swap_params(message.value)
            has_specific_params = (
                new_params.get("from_token")
                and new_params.get("to_token")
                and new_params.get("amount")
            )

            if has_specific_params:
                # User provided complete new swap params - start fresh
                logger.info(
                    f"[SwapWorkflow] New swap params detected - starting fresh swap"
                )
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

        Anvil uses Hyperliquid Spot as the primary swap provider.
        Hyperliquid Spot has 440+ tokens paired with USDC.
        Some major L1 tokens (ETH, BTC, etc.) may not be on HL Spot.
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
                logger.info(
                    f"[SwapWorkflow] User provided amount '{amount_match}' for {existing_from} → {existing_to}"
                )
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

        # ── Map major tokens to their Hyperliquid wrappers ──────────
        # e.g. "BTC" → "UBTC", "ETH" → "UETH"
        from_token, to_token, wrapper_note = self._resolve_hl_wrapper(
            from_token, to_token
        )
        if wrapper_note:
            logger.info(
                "[SwapWorkflow] Wrapper mapping applied: %s",
                wrapper_note,
            )
            state.data["wrapper_note"] = wrapper_note

        # Check if tokens are supported on Hyperliquid Spot
        unsupported_error = self._check_unsupported_tokens(
            from_token, to_token, user_context.language
        )
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
            if 0 <= index < len(POPULAR_TOKENS):
                selected_token = POPULAR_TOKENS[index][0]

        # Check if it's a token symbol
        if not selected_token:
            # Clean up the input - might be "purr", "PURR", "1. PURR", etc.
            clean_input = user_input.replace(".", "").strip()
            if clean_input in HYPERLIQUID_SPOT_TOKENS:
                selected_token = clean_input
            elif clean_input in MAJOR_TOKEN_TO_HL_WRAPPER:
                # Map major token to HL wrapper (e.g. BTC → UBTC)
                selected_token = MAJOR_TOKEN_TO_HL_WRAPPER[clean_input]
                state.data["wrapper_note"] = (
                    f"{clean_input} → {selected_token}"
                    " (Hyperliquid wrapped)"
                )

        if not selected_token:
            # Invalid selection - show menu again
            state.data["awaiting_token_selection"] = True

            response = self._get_invalid_selection_response(
                user_input=message.value,
                language=user_context.language,
            )
            return response, state

        # ── Apply wrapper mapping (e.g. BTC → UBTC) ──────────
        hl_wrapper = MAJOR_TOKEN_TO_HL_WRAPPER.get(
            selected_token.upper()
        )
        if hl_wrapper:
            state.data["wrapper_note"] = (
                f"{selected_token} → {hl_wrapper}"
                " (Hyperliquid wrapped)"
            )
            selected_token = hl_wrapper

        # Update state with selected token
        state.data["to_token"] = selected_token

        # Now we have all params - proceed to fetch quote
        state.step = WorkflowStep.FETCH_DATA.value

        # Create a dummy message to pass to fetch_quote
        return await self._handle_fetch_quote(message, state, user_context)

    @staticmethod
    def _resolve_hl_wrapper(
        from_token: str,
        to_token: str,
    ) -> tuple[str, str, str | None]:
        """Map generic major-token names to their HL wrapper equivalents.

        Returns ``(resolved_from, resolved_to, wrapper_note)`` where
        *wrapper_note* is a human-readable hint like
        ``"BTC → UBTC (Hyperliquid wrapped)"`` when a mapping was applied,
        or ``None`` if no mapping was needed.
        """
        notes: list[str] = []
        resolved_from = from_token
        resolved_to = to_token

        hl_from = MAJOR_TOKEN_TO_HL_WRAPPER.get(from_token.upper())
        if hl_from:
            resolved_from = hl_from
            notes.append(
                f"{from_token} → {hl_from} (Hyperliquid wrapped)"
            )

        hl_to = MAJOR_TOKEN_TO_HL_WRAPPER.get(to_token.upper())
        if hl_to:
            resolved_to = hl_to
            notes.append(
                f"{to_token} → {hl_to} (Hyperliquid wrapped)"
            )

        wrapper_note = ", ".join(notes) if notes else None
        return resolved_from, resolved_to, wrapper_note

    def _check_unsupported_tokens(
        self,
        from_token: str,
        to_token: str,
        language: str,
    ) -> str | None:
        """
        Check if tokens are supported on Hyperliquid Spot.

        Anvil uses Hyperliquid Spot as the primary swap provider:
        - 440+ tokens paired with USDC are supported
        - Major L1 tokens (BTC, ETH, …) are auto-mapped to their
          Hyperliquid wrappers (UBTC, UETH, …) before this check.

        Returns an error message if tokens are not supported, or None
        if valid.
        """
        # Combine hardcoded set with live cached set for full coverage
        known = HYPERLIQUID_SPOT_TOKENS
        if self._cached_tradeable_spot:
            known = known | self._cached_tradeable_spot

        from_supported = (
            from_token.upper() in known
            or from_token.upper() == "USDC"
        )
        to_supported = (
            to_token.upper() in known
            or to_token.upper() == "USDC"
        )

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
        # (two-hop via USDC is handled transparently in _fetch_quote)
        if from_token != "USDC" and to_token != "USDC":
            return self._build_usdc_required_message(
                from_token, to_token, language
            )

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

Anvil uses **Hyperliquid Spot** for swaps with **440+ tokens paired with USDC**.

**Tokens like {", ".join(unsupported_tokens)} are not currently available on Hyperliquid Spot.**

---

**✅ What you CAN do on Anvil:**

**Token Swaps** (via Hyperliquid Spot):
• `swap 100 USDC to PURR`
• `swap 50 USDC to TRUMP`
• `swap 1000 USDC to PEPE`

**440+ tokens available:** PURR, TRUMP, PEPE, MOG, HFUN, JEFF, WAGMI, and many more

---

**💡 For tokens not on Hyperliquid Spot ({", ".join(unsupported_tokens)}), you can:**

• **Check prices:** "what's the price of ETH?"
• **Track portfolio:** "show my portfolio"
• **Buy crypto:** "buy ETH" (fiat on-ramp via MoonPay)
• **Use external DEXs:** Uniswap, 1inch, or other DEX aggregators
""",
            "es": f"""❌ **Swap no soportado: {from_token} → {to_token}**

Anvil usa **Hyperliquid Spot** para swaps con **440+ tokens con USDC**.

**Tokens como {", ".join(unsupported_tokens)} no están disponibles en Hyperliquid Spot actualmente.**

**✅ Qué PUEDES hacer en Anvil:**

• Swaps de tokens: `swap 100 USDC to PURR`
• Ver precios: "precio de ETH"
• Comprar cripto: "comprar ETH"
""",
            "pt": f"""❌ **Swap não suportado: {from_token} → {to_token}**

Anvil usa **Hyperliquid Spot** para swaps com **440+ tokens com USDC**.

**Tokens como {", ".join(unsupported_tokens)} não estão disponíveis no Hyperliquid Spot atualmente.**

**✅ O que você PODE fazer no Anvil:**

• Swaps de tokens: `swap 100 USDC to PURR`
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

        # Safety: apply wrapper mapping if not already resolved
        from_token, to_token, note = self._resolve_hl_wrapper(
            from_token, to_token
        )
        if note and not state.data.get("wrapper_note"):
            state.data["wrapper_note"] = note
            state.data["from_token"] = from_token
            state.data["to_token"] = to_token

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
            response = self._get_quote_error_response(
                quote_result["error"], user_context.language
            )
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
                        logger.debug(
                            f"[SwapWorkflow] Failed to fetch {from_token} price: {e}"
                        )

                if to_id and to_id not in [
                    "usd-coin",
                    "tether",
                    "dai",
                ]:  # Skip stablecoin prices
                    try:
                        price_data = await self._coingecko.get_price(to_id)
                        market_data["to_token_price"] = price_data.usd
                    except Exception as e:
                        logger.debug(
                            f"[SwapWorkflow] Failed to fetch {to_token} price: {e}"
                        )

            # Estimate gas costs
            gas_estimate = 200000  # Default estimate
            gas_price_gwei = 0.01 if chain == "base" else 30  # Base L2 vs mainnet

            # Calculate USD gas cost
            eth_price = (
                market_data.get("from_token_price") or 3000
            )  # Fallback ETH price
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
                market_data["gas_timing"] = (
                    "Consider executing during low-traffic hours (weekends, early morning UTC)"
                )
            else:
                market_data["gas_timing"] = (
                    "L2 networks typically have lower and stable fees"
                )

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
                new_quote_response, state = await self._handle_fetch_quote(
                    message, state, user_context
                )
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
            exchange_rate = (
                str(output_float / amount_float) if amount_float > 0 else "0"
            )
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
            value_usd = (
                str(float(amount) * from_token_price) if from_token_price else None
            )
        except (ValueError, TypeError):
            value_usd = None

        # Calculate minimum output with slippage
        slippage_pct = 1.0  # 1% default slippage
        try:
            min_amount_out = float(output_amount) * (1 - slippage_pct / 100)
            min_amount_out_str = f"{min_amount_out:.6f}".rstrip("0").rstrip(".")
        except (ValueError, TypeError):
            min_amount_out_str = None

        # Convert numeric fields to strings for Pydantic validation
        from_token_price_str = (
            str(from_token_price) if from_token_price is not None else None
        )
        from_token_24h_change_str = (
            str(from_token_24h_change) if from_token_24h_change is not None else None
        )
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
            from_token_address = state.data.get(
                "from_token_address"
            ) or self._resolve_token_address(from_token, chain)
            to_token_address = state.data.get(
                "to_token_address"
            ) or self._resolve_token_address(to_token, chain)

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
                from_token_address=from_token_address
                if from_token_address and from_token_address.startswith("0x")
                else None,
                to_token_address=to_token_address
                if to_token_address and to_token_address.startswith("0x")
                else None,
                # Price data
                from_token_price_usd=from_token_price_str,
                from_token_24h_change=from_token_24h_change_str,
                value_usd=value_usd,
            )

        # Store execute_data in state
        state.execute_data = execute_data
        state.step = WorkflowStep.COMPLETED.value

        # Format ready-to-execute response (pass execute_data for multi-step info)
        response = self._format_execute_response(
            state.data, user_context.language, execute_data
        )
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
        3. Swap: Execute spot swap USDC → token

        Returns execute_data with steps[] array for frontend to process.
        """
        amount_float = self._parse_amount_float(amount)

        # Check Hyperliquid balances to determine which steps are needed
        hl_perps_usdc = 0.0
        hl_spot_usdc = 0.0
        hl_spot_from_token = 0.0

        if self._hyperliquid and user_context.wallet_address:
            try:
                all_balances = await self._hyperliquid.get_all_balances(
                    user_context.wallet_address
                )
                hl_perps_usdc = all_balances.get("perps", {}).get("USDC", 0.0)
                hl_spot_usdc = all_balances.get("spot", {}).get("USDC", 0.0)
                hl_spot_from_token = all_balances.get("spot", {}).get(
                    from_token.upper(), 0.0
                )

                logger.info(
                    f"[SwapWorkflow] Hyperliquid balances for {user_context.wallet_address}: "
                    f"Perps USDC={hl_perps_usdc}, Spot USDC={hl_spot_usdc}, "
                    f"Spot {from_token}={hl_spot_from_token}"
                )
            except Exception as e:
                logger.warning(
                    f"[SwapWorkflow] Failed to get Hyperliquid balances: {e}"
                )

        # Determine which steps are needed
        # If swapping FROM USDC, check USDC balance
        # If swapping FROM token (e.g., PURR → USDC), check token balance
        is_selling_usdc = from_token.upper() == "USDC"

        if is_selling_usdc:
            # User wants to swap USDC → token
            available_on_spot = hl_spot_usdc
            available_on_perps = hl_perps_usdc
        else:
            # User wants to swap token → USDC
            available_on_spot = hl_spot_from_token
            available_on_perps = 0  # Spot tokens are only on Spot

        # Build steps based on what's needed
        steps = []
        current_step = 1

        # Step 1: Deposit via LiFi (if not enough on Hyperliquid)
        total_on_hyperliquid = available_on_spot + available_on_perps
        needs_deposit = total_on_hyperliquid < amount_float and is_selling_usdc

        # Supported source chains for LiFi bridge to Hyperliquid
        SUPPORTED_SOURCE_CHAINS = {
            "base": {
                "chain_id": 8453,
                "usdc": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
            },
            "arbitrum": {
                "chain_id": 42161,
                "usdc": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
            },
            "ethereum": {
                "chain_id": 1,
                "usdc": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
            },
        }

        # Find best source chain based on where user has ETH for gas (can_pay_gas=True)
        best_source_chain: str | None = None
        chain_balances: dict[str, dict[str, Any]] = {}
        gas_info: dict[str, Any] = {}
        no_gas_error: str | None = None

        if user_context.wallet_address and needs_deposit:
            try:
                # Query ALL token balances from token_balances table
                chain_balances = await _get_token_balances_for_wallet(
                    user_context.wallet_address
                )

                # Find best chain (minimum 0.0002 ETH for gas ~$0.40)
                MIN_ETH_FOR_GAS = 0.0002
                best_source_chain, gas_info = _find_best_chain_for_gas(
                    chain_balances,
                    list(SUPPORTED_SOURCE_CHAINS.keys()),
                    MIN_ETH_FOR_GAS,
                )

                if best_source_chain:
                    chain_data = chain_balances.get(best_source_chain, {})
                    logger.info(
                        f"[SwapWorkflow] Best chain for gas: {best_source_chain} "
                        f"(ETH: {chain_data.get('eth_balance', 0):.6f}, can_pay_gas: {chain_data.get('can_pay_gas')})"
                    )
                else:
                    logger.warning(
                        f"[SwapWorkflow] No chain has enough ETH for gas. "
                        f"Gas info: {gas_info}"
                    )
                    no_gas_error = gas_info.get("error", "insufficient_gas")
            except Exception as e:
                logger.warning(f"[SwapWorkflow] Failed to check token balances: {e}")

        # Use best source chain or fall back to default
        source_chain = best_source_chain or "base"
        source_chain_id = SUPPORTED_SOURCE_CHAINS[source_chain]["chain_id"]
        source_usdc = SUPPORTED_SOURCE_CHAINS[source_chain]["usdc"]

        # LiFi bridge configuration - includes all supported chains and token balances
        lifi_config = {
            "source_chain": source_chain,
            "source_chain_id": source_chain_id,
            "destination_chain": "hyperliquid",
            "destination_chain_id": 1337,
            # USDC addresses
            "source_usdc": source_usdc,
            "destination_usdc": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",  # HL Perps USDC
            # LiFi API endpoint for quote
            "lifi_quote_url": "https://li.quest/v1/quote",
            # All supported source chains
            "supported_source_chains": SUPPORTED_SOURCE_CHAINS,
            # Full token balances per chain (includes can_pay_gas, usdc, weth)
            "token_balances": {
                chain: {
                    "eth_balance": data.get("eth_balance", 0),
                    "can_pay_gas": data.get("can_pay_gas", False),
                    "usdc_balance": data.get("usdc_balance", 0),
                    "weth_balance": data.get("weth_balance", 0),
                    "total_usd": data.get("total_usd", 0),
                }
                for chain, data in chain_balances.items()
            },
            # Best chain selected by backend (has enough ETH for gas)
            "best_source_chain": best_source_chain,
            # Gas check details
            "gas_info": gas_info,
            # Error if no chain has enough gas
            "gas_error": no_gas_error,
        }

        if needs_deposit:
            deposit_amount = amount_float - total_on_hyperliquid

            steps.append({
                "step": 1,
                "action": "lifi_bridge",
                "status": "pending",
                "description": f"Bridge {deposit_amount:.2f} USDC to Hyperliquid via LiFi from {source_chain.capitalize()}",
                # Best source chain (has ETH for gas) - determined by backend
                "source_chain": source_chain,
                "source_chain_id": source_chain_id,
                "destination_chain": "hyperliquid",
                "destination_chain_id": 1337,
                "amount": f"{deposit_amount:.2f}",
                "token": "USDC",
                "source_token_address": source_usdc,
                "destination_token_address": lifi_config["destination_usdc"],
                "bridge_provider": "lifi",
                "estimated_time": "~30 seconds",
                # ETH balance on selected chain
                "gas_chain_eth_balance": chain_balances.get(source_chain, {}).get(
                    "eth_balance", 0
                ),
                # All supported chains (for fallback)
                "supported_source_chains": list(SUPPORTED_SOURCE_CHAINS.keys()),
            })
            current_step = 1

        # Step 2: Transfer to Spot (if balance is in Perps)
        needs_transfer = (
            is_selling_usdc
            and available_on_spot < amount_float
            and (available_on_perps > 0 or needs_deposit)
        )

        if needs_transfer:
            transfer_amount = min(
                amount_float - available_on_spot,
                available_on_perps
                + (amount_float - total_on_hyperliquid if needs_deposit else 0),
            )
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
                        "output": '{"from_token": "USDC", "to_token": "PURR", "amount": "100", "chain": "base", "to_chain": null}',
                    },
                    {
                        "input": "swap 50 USDC to TRUMP",
                        "output": '{"from_token": "USDC", "to_token": "TRUMP", "amount": "50", "chain": "base", "to_chain": null}',
                    },
                    {
                        "input": "swap 1000 PEPE to USDC",
                        "output": '{"from_token": "PEPE", "to_token": "USDC", "amount": "1000", "chain": "base", "to_chain": null}',
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
        amount_match = re.search(r"(\d+\.?\d*)", message)
        if amount_match:
            params["amount"] = amount_match.group(1)

        # Extract tokens (common DeFi tokens)
        tokens = [
            "ETH",
            "WETH",
            "USDC",
            "USDT",
            "DAI",
            "WBTC",
            "BTC",
            "MATIC",
            "WMATIC",
            "SOL",
        ]
        found_tokens = []
        for token in tokens:
            if token in message_upper:
                found_tokens.append(token)

        # Assign tokens based on position/context
        if len(found_tokens) >= 2:
            # Check for "X to Y" pattern
            to_match = re.search(r"(\w+)\s+to\s+(\w+)", message, re.IGNORECASE)
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

    def _is_hyperliquid_swap(
        self, from_token: str | None, to_token: str | None
    ) -> bool:
        """
        Check if this swap should use Hyperliquid Spot.

        Uses both the hardcoded ``HYPERLIQUID_SPOT_TOKENS`` (fast path) and
        the cached live set from ``_get_tradeable_spot_tokens()`` so that all
        263+ tokens with an active Core spot market are routed correctly.
        """
        # Safety check for None values
        if not from_token or not to_token:
            return False

        from_upper = from_token.upper()
        to_upper = to_token.upper()

        # Same token swap is a no-op, not a Hyperliquid swap
        if from_upper == to_upper:
            return False

        # Combine hardcoded set with live cached set for full coverage
        known = HYPERLIQUID_SPOT_TOKENS
        if self._cached_tradeable_spot:
            known = known | self._cached_tradeable_spot

        from_supported = from_upper in known or from_upper == "USDC"
        to_supported = to_upper in known or to_upper == "USDC"

        # Both tokens must be known HL Spot tokens (including USDC)
        if not (from_supported and to_supported):
            return False

        # At least one side must be non-USDC
        if from_upper == "USDC" and to_upper == "USDC":
            return False

        return True

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
        1. Hyperliquid Spot: For 440+ tokens (PURR, TRUMP, etc.) paired with USDC
        2. 1inch: For major tokens same-chain swaps
        3. LiFi: For cross-chain swaps
        """
        is_cross_chain = to_chain and to_chain.lower() != chain.lower()

        try:
            # Warm the tradeable-token cache so _is_hyperliquid_swap covers
            # all 263+ tokens, not just the hardcoded subset.
            if self._cached_tradeable_spot is None and self._hyperliquid:
                await self._get_tradeable_spot_tokens()

            # ============================================================
            # HYPERLIQUID SPOT: 263+ tokens with active Core spot markets
            # ============================================================
            if self._is_hyperliquid_swap(from_token, to_token) and not is_cross_chain:
                if self._hyperliquid:
                    logger.info(
                        f"[SwapWorkflow] Using Hyperliquid Spot for token swap: "
                        f"{amount} {from_token} → {to_token}"
                    )
                    amount_float = float(amount)
                    from_upper = from_token.upper()
                    to_upper = to_token.upper()

                    # 1) Try direct market (e.g. PURR/USDC or PURR/FUN if it exists)
                    try:
                        quote = await self._hyperliquid.get_spot_quote(
                            from_token=from_upper,
                            to_token=to_upper,
                            amount=amount_float,
                        )
                        return {
                            "output_amount": f"{quote.to_amount:.6f}".rstrip(
                                "0"
                            ).rstrip("."),
                            "price_impact": quote.spread_bps / 100,
                            "gas_estimate": 0,
                            "aggregator": "hyperliquid",
                            "mid_price": quote.mid_price,
                            "effective_price": quote.price,
                            "from_token_address": None,
                            "to_token_address": None,
                        }
                    except Exception as direct_err:
                        logger.info(
                            "[SwapWorkflow] Direct HL quote failed %s/%s: %s",
                            from_upper,
                            to_upper,
                            direct_err,
                        )

                    # 2) Token-to-token with no direct market: two-hop via USDC
                    #    HL Spot typically has only X/USDC markets
                    if from_upper != "USDC" and to_upper != "USDC":
                        try:
                            quote1 = await self._hyperliquid.get_spot_quote(
                                from_token=from_upper,
                                to_token="USDC",
                                amount=amount_float,
                            )
                            quote2 = await self._hyperliquid.get_spot_quote(
                                from_token="USDC",
                                to_token=to_upper,
                                amount=quote1.to_amount,
                            )
                            effective_price = (
                                amount_float / quote2.to_amount
                                if quote2.to_amount > 0
                                else 0
                            )
                            return {
                                "output_amount": f"{quote2.to_amount:.6f}".rstrip(
                                    "0"
                                ).rstrip("."),
                                "price_impact": (quote1.spread_bps + quote2.spread_bps)
                                / 100,
                                "gas_estimate": 0,
                                "aggregator": "hyperliquid",
                                "mid_price": effective_price,
                                "effective_price": effective_price,
                                "from_token_address": None,
                                "to_token_address": None,
                                "via_usdc": True,
                            }
                        except Exception as two_hop_err:
                            logger.warning(
                                "[SwapWorkflow] Hyperliquid two-hop quote failed "
                                "%s → USDC → %s: %s",
                                from_upper,
                                to_upper,
                                two_hop_err,
                            )

                    # This pair is Hyperliquid-only; do not fall through to 1inch/LiFi
                    if self._hyperliquid:
                        return {
                            "error": (
                                "This token pair is on Hyperliquid but we couldn't get a quote "
                                "(e.g. low liquidity or temporary issue). Try again in a moment, "
                                "or try swapping to USDC first."
                            )
                        }
                    # Fall through only when HL client was not configured
                else:
                    logger.warning(
                        f"[SwapWorkflow] Hyperliquid client not configured, "
                        f"cannot swap tokens via HL Spot: {from_token}/{to_token}"
                    )

            amount_wei = self._to_wei(amount, from_token)

            # ============================================================
            # CROSS-CHAIN: Use LiFi
            # ============================================================
            if is_cross_chain:
                if not self._lifi:
                    return {
                        "error": "Cross-chain swaps require LiFi client (not configured)"
                    }

                # Use a valid placeholder address if no wallet connected
                # LiFi requires a valid ETH address format
                sender_address = (
                    wallet_address or "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
                )
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
                    "price_impact": getattr(quote, "price_impact", 0),
                    "gas_estimate": int(getattr(quote, "estimated_gas", 250000)),
                    "aggregator": "lifi",
                    "from_token_address": from_token_addr
                    if from_token_addr.startswith("0x")
                    else None,
                    "to_token_address": to_token_addr
                    if to_token_addr.startswith("0x")
                    else None,
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
                    "price_impact": getattr(quote, "price_impact", 0),
                    "gas_estimate": int(getattr(quote, "estimated_gas", 200000)),
                    "aggregator": "1inch",
                    "from_token_address": from_addr
                    if from_addr.startswith("0x")
                    else None,
                    "to_token_address": to_addr if to_addr.startswith("0x") else None,
                }
            elif self._lifi:
                # Fallback: Use LiFi for same-chain swaps
                logger.info("[SwapWorkflow] Using LiFi fallback for same-chain swap")
                sender_address = (
                    wallet_address or "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
                )

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
                    "price_impact": getattr(quote, "price_impact", 0),
                    "gas_estimate": int(getattr(quote, "estimated_gas", 250000)),
                    "aggregator": "lifi",
                    "from_token_address": from_token_addr
                    if from_token_addr.startswith("0x")
                    else None,
                    "to_token_address": to_token_addr
                    if to_token_addr.startswith("0x")
                    else None,
                }
            else:
                return {
                    "error": "Swap quote unavailable - no swap aggregator configured"
                }

        except Exception as e:
            logger.error(f"[SwapWorkflow] Quote fetch failed: {e}")
            return {"error": str(e)}

    def _to_wei(self, amount: str, token: str) -> str:
        """Convert human readable amount to wei."""
        decimals = TOKEN_DECIMALS.get(token.upper(), 18)
        try:
            value = float(amount) * (10**decimals)
            return str(int(value))
        except ValueError:
            return "0"

    def _from_wei(self, amount_wei: str, token: str) -> str:
        """Convert wei to human readable amount."""
        decimals = TOKEN_DECIMALS.get(token.upper(), 18)
        try:
            value = int(amount_wei) / (10**decimals)
            return f"{value:.6f}".rstrip("0").rstrip(".")
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

        # Then check Hyperliquid token addresses (for HL Spot tokens)
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
        - Knowledge about Hyperliquid Spot tokens
        - User's current balance (if available)
        - Real-time prices from CoinGecko
        """
        language = user_context.language

        # Try to fetch prices for popular tokens
        prices = await self._fetch_token_prices()

        # Build token list with prices
        token_lines = []
        for i, (symbol, description) in enumerate(POPULAR_TOKENS, 1):
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

**Select a token to receive:**

{token_list}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Reply with:**
• A number (1-10) to select
• Or type the token name (e.g., PURR)

💡 All swaps via **Hyperliquid Spot** (0.02% fee, zero gas)""",
            "es": f"""🔄 **Intercambiar {amount} {from_token}**

{knowledge_section}

{user_balance_section}

**Selecciona un token para recibir:**

{token_list}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Responde con:**
• Un número (1-10) para seleccionar
• O escribe el nombre del token (ej: PURR)

💡 Swaps via **Hyperliquid Spot** (0.02% comisión, sin gas)""",
            "pt": f"""🔄 **Trocar {amount} {from_token}**

{knowledge_section}

{user_balance_section}

**Selecione um token para receber:**

{token_list}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Responda com:**
• Um número (1-10) para selecionar
• Ou digite o nome do token (ex: PURR)

💡 Swaps via **Hyperliquid Spot** (0.02% taxa, sem gas)""",
            "zh": f"""🔄 **兑换 {amount} {from_token}**

{knowledge_section}

{user_balance_section}

**选择要接收的代币：**

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
        Fetch current prices for popular tokens.

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
Trade 440+ tokens with zero gas fees and 0.02% trading fee.
High-speed execution (20,000+ TPS) on Hyperliquid L1.
Real-time order book pricing - no slippage surprises.""",
            "es": """**¿Qué es Hyperliquid Spot?**
Opera 440+ tokens con cero gas y 0.02% comisión.
Ejecución de alta velocidad (20,000+ TPS) en Hyperliquid L1.
Precios en tiempo real - sin sorpresas de slippage.""",
            "pt": """**O que é Hyperliquid Spot?**
Negocie 440+ tokens com zero gas e 0.02% de taxa.
Execução de alta velocidade (20,000+ TPS) no Hyperliquid L1.
Preços em tempo real - sem surpresas de slippage.""",
            "zh": """**什么是 Hyperliquid Spot？**
零 gas 费交易 440+ 代币，仅 0.02% 交易费。
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
        token_names = ", ".join([t[0] for t in POPULAR_TOKENS])

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

    async def _get_missing_params_response(
        self, params: dict, user_context: "UserContext"
    ) -> str:
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
            }.get(
                language,
                f"💰 **Your Balance:** ${user_balance_usd:.2f}\n\n💡 **Tip:** Say `buy crypto` to get USDC first!",
            )
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

What token would you like to swap?

{examples_section}

**440+ tokens available:** PURR, TRUMP, PEPE, HFUN, MOG, GMEOW and many more
**Note:** All swaps use USDC pairs. Some major L1 tokens (ETH, BTC, SOL) may not be on HL Spot.""",
            "es": f"""🔄 **Swaps en Hyperliquid Spot**

{balance_section}

¿Qué token te gustaría intercambiar?

{examples_section}

**440+ tokens disponibles:** PURR, TRUMP, PEPE, HFUN, MOG, GMEOW y muchos más
**Nota:** Todos los swaps usan pares USDC. Algunos tokens L1 (ETH, BTC, SOL) pueden no estar en HL Spot.""",
            "pt": f"""🔄 **Swaps no Hyperliquid Spot**

{balance_section}

Qual token você gostaria de trocar?

{examples_section}

**440+ tokens disponíveis:** PURR, TRUMP, PEPE, HFUN, MOG, GMEOW e muitos mais
**Nota:** Todas as trocas usam pares USDC. Alguns tokens L1 (ETH, BTC, SOL) podem não estar no HL Spot.""",
            "zh": f"""🔄 **Hyperliquid Spot 交易**

{balance_section}

您想交换哪个代币？

{examples_section}

**440+代币可用：** PURR, TRUMP, PEPE, HFUN, MOG, GMEOW 等更多
**注意：** 所有交易使用USDC交易对。部分L1代币（ETH, BTC, SOL）可能不在HL Spot上。""",
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
• `swap {small_amt:.0f} USDC to PURR` (~{small_amt / user_balance_usd * 100:.0f}% of balance)
• `swap {med_amt:.0f} USDC to TRUMP` (~{med_amt / user_balance_usd * 100:.0f}% of balance)""",
                "es": f"""**Ejemplos basados en tu saldo:**
• `swap {small_amt:.0f} USDC to PURR` (~{small_amt / user_balance_usd * 100:.0f}% del saldo)
• `swap {med_amt:.0f} USDC to TRUMP` (~{med_amt / user_balance_usd * 100:.0f}% del saldo)""",
                "pt": f"""**Exemplos baseados no seu saldo:**
• `swap {small_amt:.0f} USDC to PURR` (~{small_amt / user_balance_usd * 100:.0f}% do saldo)
• `swap {med_amt:.0f} USDC to TRUMP` (~{med_amt / user_balance_usd * 100:.0f}% do saldo)""",
                "zh": f"""**基于您余额的示例：**
• `swap {small_amt:.0f} USDC to PURR` (~{small_amt / user_balance_usd * 100:.0f}% 的余额)
• `swap {med_amt:.0f} USDC to TRUMP` (~{med_amt / user_balance_usd * 100:.0f}% 的余额)""",
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

        # Wrapper mapping note (e.g. "BTC → UBTC (Hyperliquid wrapped)")
        wrapper_note = data.get("wrapper_note")

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
            market_context += (
                f"💰 **{from_token} Price:** ${from_price:,.2f}{change_str}\n"
            )

        if usd_value:
            market_context += f"💵 **Value:** ~${usd_value:,.2f} USD\n"

        # Gas info section
        gas_info = ""
        if gas_usd is not None:
            gas_info = f"⛽ **Est. Gas:** ~${gas_usd:.4f}"
            if gas_timing:
                gas_info += f"\n💡 {gas_timing}"

        # Wrapper mapping info (shown when BTC→UBTC etc.)
        wrapper_info = ""
        if wrapper_note:
            wrapper_info = f"🔄 **Auto-mapped:** {wrapper_note}\n"

        msgs = {
            "en": f"""📊 **Swap Quote**

**{amount} {from_token}** → **{output} {to_token}**
{wrapper_info}

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
{wrapper_info}
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
{wrapper_info}
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
            supported_chains = list(
                lifi_config.get("supported_source_chains", {}).keys()
            )
            chains_str = (
                ", ".join([c.capitalize() for c in supported_chains])
                if supported_chains
                else "Base, Arbitrum, or Ethereum"
            )

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

⚠️ **Requires:** ~$0.40 of ETH for gas on {chains_str}

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

⚠️ **Requiere:** ~$0.40 de ETH para gas en {chains_str}

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

⚠️ **Requer:** ~$0.40 de ETH para gas em {chains_str}

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

    # ================================================================
    # "My Swaps" – Position Viewing & Swap-from-Position
    # ================================================================

    async def _handle_my_swaps_request(
        self,
        message: MessageContent,
        state: WorkflowState,
        user_context: UserContext,
    ) -> tuple[str, WorkflowState]:
        """
        Handle "my swaps" – show cached Hyperliquid positions + recent swap history.

        Reads from the `swap_positions` table (synced every 60s by Celery)
        instead of making live API calls. This scales to 1000+ users.

        Data sources:
        1. swap_positions table (spot balances + perps positions, cached)
        2. transactions table (recent swap history)

        Note: We do not use the `hyperliquid_positions` table. That table
        exists in the schema but is unused; all HL position data for "my swaps"
        comes from `swap_positions`, populated by swap_position_sync_tasks.
        """
        language = user_context.language
        wallet_address = user_context.wallet_address

        if not wallet_address:
            no_wallet = {
                "en": (
                    "🔗 To view your swap positions, you need to connect your wallet first.\n\n"
                    "Please connect your wallet and try again."
                ),
                "es": (
                    "🔗 Para ver tus posiciones de swap, necesitas conectar tu wallet primero.\n\n"
                    "Por favor, conecta tu wallet y vuelve a intentarlo."
                ),
                "pt": (
                    "🔗 Para ver suas posições de swap, você precisa conectar sua carteira primeiro.\n\n"
                    "Por favor, conecte sua carteira e tente novamente."
                ),
            }
            return no_wallet.get(language, no_wallet["en"]), state

        # ── Read cached positions from swap_positions table ──
        cached_rows = await self._fetch_cached_positions(wallet_address)

        # ── Fetch recent swap history from DB ──
        recent_swaps = await self._fetch_recent_swaps_from_db(
            user_context.user_id, wallet_address
        )

        # ── Build positions list from cached data ──
        positions: list[dict] = []

        for row in cached_rows:
            source = row.get("source", "spot")
            pos_dict: dict = {
                "source": source,
                "token": row.get("token", ""),
                "balance": float(row.get("balance", 0)),
                "usd_value": float(row.get("usd_value", 0)),
                "side": row.get("side", "hold"),
            }
            if source == "perps":
                pos_dict["entry_price"] = float(row.get("entry_price", 0) or 0)
                pos_dict["mark_price"] = float(row.get("mark_price", 0) or 0)
                pos_dict["pnl"] = float(row.get("unrealized_pnl", 0) or 0)
                pos_dict["leverage"] = float(row.get("leverage", 1) or 1)
            positions.append(pos_dict)

        # Sort by USD value descending
        positions.sort(key=lambda p: -p.get("usd_value", 0))

        # Store in state for later selection
        state.data["positions"] = positions
        state.data["recent_swaps"] = recent_swaps

        # ── Render response ──
        if not positions and not recent_swaps:
            empty_msg = {
                "en": (
                    "📭 **No swap positions found** on Hyperliquid for your wallet.\n\n"
                    "You can get started by:\n"
                    "• 🔄 **Swap USDC to a token** – e.g. *\"swap 100 USDC to PURR\"*\n"
                    "• 💰 **Buy crypto first** – e.g. *\"buy $50 of USDC\"*\n\n"
                    "Once you make swaps on Hyperliquid, your positions will appear here!"
                ),
                "es": (
                    "📭 **No se encontraron posiciones de swap** en Hyperliquid para tu wallet.\n\n"
                    "Puedes empezar:\n"
                    "• 🔄 **Swap USDC a un token** – ej. *\"swap 100 USDC a PURR\"*\n"
                    "• 💰 **Compra crypto primero** – ej. *\"comprar $50 de USDC\"*"
                ),
                "pt": (
                    "📭 **Nenhuma posição de swap encontrada** no Hyperliquid para sua carteira.\n\n"
                    "Você pode começar:\n"
                    "• 🔄 **Swap USDC para um token** – ex. *\"swap 100 USDC para PURR\"*\n"
                    "• 💰 **Compre crypto primeiro** – ex. *\"comprar $50 de USDC\"*"
                ),
            }
            return empty_msg.get(language, empty_msg["en"]), state

        # ── Fetch top sentiment tokens for recommendations ──
        top_sentiment_tokens = await self._fetch_top_sentiment_tokens()

        response, numbered_actions = self._render_swap_positions(
            positions, recent_swaps, language, top_sentiment_tokens
        )

        # Store numbered actions so selection handler can dispatch correctly
        state.data["numbered_actions"] = numbered_actions
        # Set state for action selection
        state.data["awaiting_swap_position_selection"] = True

        return response, state

    def _render_swap_positions(
        self,
        positions: list[dict],
        recent_swaps: list[dict],
        language: str,
        top_sentiment_tokens: list[dict] | None = None,
    ) -> tuple[str, list[dict]]:
        """
        Render swap positions with numbered actions and smart recommendations.

        Returns:
            Tuple of (rendered text, list of action dicts).
            Each action dict has keys: action_type, from_token, to_token, amount.
            action_type is one of: swap, swap_all, custom, refresh.
        """

        headers = {
            "en": "📊 **Your Swap Positions (Hyperliquid)**\n\n",
            "es": "📊 **Tus Posiciones de Swap (Hyperliquid)**\n\n",
            "pt": "📊 **Suas Posições de Swap (Hyperliquid)**\n\n",
        }
        header = headers.get(language, headers["en"])

        lines: list[str] = []

        # ── Spot Holdings (unnumbered – display only) ──
        spot_positions = [p for p in positions if p["source"] == "spot"]
        if spot_positions:
            lines.append("**🪙 Spot Holdings**\n")
            for pos in spot_positions:
                token = pos["token"]
                balance = pos["balance"]
                usd = pos["usd_value"]
                usd_str = f" (~${usd:,.2f})" if usd > 0 else ""
                lines.append(
                    f"• **{token}**: {balance:,.4f}{usd_str}"
                )
            lines.append("")

        # ── Perps Positions (unnumbered – display only) ──
        perps_positions = [p for p in positions if p["source"] == "perps"]
        if perps_positions:
            lines.append("**📈 Perpetual Positions**\n")
            for pos in perps_positions:
                token = pos["token"]
                size = pos["balance"]
                side = pos["side"].upper()
                entry = pos.get("entry_price", 0)
                mark = pos.get("mark_price", 0)
                pnl = pos.get("pnl", 0)
                leverage = pos.get("leverage", 1)
                pnl_emoji = "🟢" if pnl >= 0 else "🔴"

                lines.append(
                    f"• **{token}** {side} {leverage:.0f}x\n"
                    f"   Size: {size:,.4f} | Entry: ${entry:,.2f} | Mark: ${mark:,.2f}\n"
                    f"   PnL: {pnl_emoji} ${pnl:,.2f}"
                )
            lines.append("")

        # ── Recent Swap History ──
        if recent_swaps:
            lines.append("**🔄 Recent Swaps**\n")
            for swap in recent_swaps[:5]:
                asset_in = swap.get("asset_in", "?")
                amount_in = swap.get("amount_in", 0)
                asset_out = swap.get("asset_out", "")
                amount_out = swap.get("amount_out", 0)
                ts = swap.get("confirmed_at", "")
                date_str = ts[:10] if ts else ""

                if asset_out and amount_out:
                    lines.append(
                        f"• {amount_in:,.2f} {asset_in} → {amount_out:,.2f} {asset_out}  _{date_str}_"
                    )
                else:
                    lines.append(f"• {amount_in:,.2f} {asset_in}  _{date_str}_")
            lines.append("")

        # ── Build numbered smart actions based on actual holdings ──
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

        what_to_do = {
            "en": "**What would you like to do?**\n",
            "es": "**¿Qué te gustaría hacer?**\n",
            "pt": "**O que você gostaria de fazer?**\n",
        }
        lines.append(what_to_do.get(language, what_to_do["en"]))

        action_num = 1
        # Actions list – each entry maps a number to a swap command
        actions: list[dict] = []
        # Exclude stablecoins from "sell" recommendations
        stables = {"USDC", "USDT", "DAI", "USDbC"}

        # Find the best sentiment token for buy recommendations
        # Exclude tokens the user already holds and stablecoins
        held_tokens = {p["token"].upper() for p in spot_positions}
        best_sentiment_token = None
        best_sentiment_label = ""
        if top_sentiment_tokens:
            for st in top_sentiment_tokens:
                name = st.get("name", "").upper()
                if name not in held_tokens and name not in stables:
                    best_sentiment_token = name
                    best_sentiment_label = st.get(
                        "sentiment_interpretation", ""
                    )
                    break

        # For each holding, generate contextual swap suggestions
        for pos in spot_positions:
            token = pos["token"].upper()
            balance = pos["balance"]
            usd = pos["usd_value"]

            if token in stables:
                # Stablecoin → suggest buying the best sentiment token
                if usd >= 1.0 and best_sentiment_token:
                    suggest_amount = round(balance * 0.8, 2)
                    sentiment_hint = (
                        f" ({best_sentiment_label})"
                        if best_sentiment_label
                        else ""
                    )
                    lines.append(
                        f"**{action_num}.** 🟢 Buy: "
                        f"*\"swap {suggest_amount} {token} to {best_sentiment_token}\"*"
                        f"{sentiment_hint}"
                    )
                    actions.append({
                        "action_type": "swap",
                        "from_token": token,
                        "to_token": best_sentiment_token,
                        "amount": suggest_amount,
                    })
                    action_num += 1
            else:
                # Non-stablecoin → suggest selling to USDC or swapping
                if usd >= 1.0:
                    # Suggest selling ~80% to USDC
                    suggest_sell = round(balance * 0.8, 2)
                    lines.append(
                        f"**{action_num}.** 💰 Sell: "
                        f"*\"swap {suggest_sell} {token} to USDC\"*"
                    )
                    actions.append({
                        "action_type": "swap",
                        "from_token": token,
                        "to_token": "USDC",
                        "amount": suggest_sell,
                    })
                    action_num += 1

                    # If there's a good sentiment token, suggest rotating
                    if best_sentiment_token and best_sentiment_token != token:
                        suggest_rotate = round(balance * 0.5, 2)
                        sentiment_hint = (
                            f" ({best_sentiment_label})"
                            if best_sentiment_label
                            else ""
                        )
                        lines.append(
                            f"**{action_num}.** 🔄 Rotate: "
                            f"*\"swap {suggest_rotate} {token} to "
                            f"{best_sentiment_token}\"*{sentiment_hint}"
                        )
                        actions.append({
                            "action_type": "swap",
                            "from_token": token,
                            "to_token": best_sentiment_token,
                            "amount": suggest_rotate,
                        })
                        action_num += 1

        # Always add a "sell all" option for the largest non-stable holding
        largest_non_stable = None
        for pos in spot_positions:
            if pos["token"].upper() not in stables and pos["usd_value"] >= 1.0:
                if (
                    largest_non_stable is None
                    or pos["usd_value"] > largest_non_stable["usd_value"]
                ):
                    largest_non_stable = pos
        if largest_non_stable:
            token = largest_non_stable["token"].upper()
            lines.append(
                f"**{action_num}.** 🔻 Sell all: "
                f"*\"swap all {token} to USDC\"*"
            )
            actions.append({
                "action_type": "swap_all",
                "from_token": token,
                "to_token": "USDC",
                "amount": largest_non_stable["balance"],
            })
            action_num += 1

        # Custom swap option
        custom_label = {
            "en": "Custom swap",
            "es": "Swap personalizado",
            "pt": "Swap personalizado",
        }
        lines.append(
            f"**{action_num}.** ✏️ {custom_label.get(language, custom_label['en'])}: "
            f"*\"swap [amount] [TOKEN] to [TOKEN]\"*"
        )
        actions.append({"action_type": "custom"})
        action_num += 1

        # Refresh option
        lines.append(
            f"**{action_num}.** 🔃 Refresh: *\"refresh\"*"
        )
        actions.append({"action_type": "refresh"})

        # Sentiment footnote
        if top_sentiment_tokens:
            trending = [
                f"{t['name']} ({t.get('sentiment_interpretation', '?')})"
                for t in top_sentiment_tokens[:3]
                if t["name"].upper() not in stables
            ]
            if trending:
                trending_label = {
                    "en": "Trending",
                    "es": "Tendencia",
                    "pt": "Tendência",
                }
                lines.append(
                    f"\n📈 {trending_label.get(language, trending_label['en'])}: "
                    f"{', '.join(trending)}"
                )

        return header + "\n".join(lines), actions

    async def _handle_swap_position_selection(
        self,
        message: MessageContent,
        state: WorkflowState,
        user_context: UserContext,
    ) -> tuple[str, WorkflowState]:
        """Handle user selecting a position number to swap from."""
        text = message.value.strip()
        text_lower = text.lower()
        positions = state.data.get("positions", [])

        # Check if user typed a new swap command instead of a number
        new_params = await self._extract_swap_params(text)
        if new_params.get("from_token") and new_params.get("to_token"):
            state.data.pop("awaiting_swap_position_selection", None)
            state.data.pop("positions", None)
            state = WorkflowState()
            state.step = WorkflowStep.PARSE_REQUEST.value
            return await self._handle_parse_request(message, state, user_context)

        # Check if user typed "swap all <TOKEN> to <TOKEN>"
        all_match = re.match(
            r"swap\s+(?:all|todo|tudo)\s+(\w+)\s+(?:to|a|para)\s+(\w+)",
            text_lower,
        )
        if all_match:
            from_token = all_match.group(1).upper()
            to_token = all_match.group(2).upper()
            # Find the position to get balance
            for pos in positions:
                if pos["token"].upper() == from_token and pos["source"] == "spot":
                    amount = pos["balance"]
                    state.data.pop("awaiting_swap_position_selection", None)
                    state.data["from_token"] = from_token
                    state.data["to_token"] = to_token
                    state.data["amount"] = amount
                    state.data["provider"] = "hyperliquid"
                    state.step = WorkflowStep.FETCH_DATA.value
                    return await self._handle_fetch_quote(message, state, user_context)
            # Token not found in positions
            return (
                f"❌ Token **{from_token}** not found in your spot positions. "
                f"Please select a number from the list above.",
                state,
            )

        # Try to parse a number as an action selection (numbered recommendations)
        numbered_actions = state.data.get("numbered_actions", [])
        try:
            selection = int(text)

            # Dispatch by numbered action if we have actions from "my swaps"
            if numbered_actions and 1 <= selection <= len(numbered_actions):
                action = numbered_actions[selection - 1]
                action_type = action.get("action_type", "")

                state.data.pop("awaiting_swap_position_selection", None)
                state.data.pop("numbered_actions", None)

                if action_type == "swap":
                    from_token = action.get("from_token", "")
                    to_token = action.get("to_token", "")
                    amount = action.get("amount", 0)
                    state.data["from_token"] = from_token
                    state.data["to_token"] = to_token
                    state.data["amount"] = amount
                    state.data["provider"] = "hyperliquid"
                    state.data["chain"] = "hyperliquid"  # My-swaps actions are HL Spot
                    state.step = WorkflowStep.FETCH_DATA.value
                    return await self._handle_fetch_quote(
                        message, state, user_context
                    )

                if action_type == "swap_all":
                    from_token = action.get("from_token", "")
                    to_token = action.get("to_token", "")
                    amount = action.get("amount", 0)
                    state.data["from_token"] = from_token
                    state.data["to_token"] = to_token
                    state.data["amount"] = amount
                    state.data["provider"] = "hyperliquid"
                    state.data["chain"] = "hyperliquid"  # My-swaps actions are HL Spot
                    state.step = WorkflowStep.FETCH_DATA.value
                    return await self._handle_fetch_quote(
                        message, state, user_context
                    )

                if action_type == "custom":
                    custom_prompt = {
                        "en": (
                            "✏️ **Custom swap**\n\n"
                            "Type your swap command, for example:\n"
                            "• **swap 50 USDC to PURR**\n"
                            "• **swap all PURR to USDC**"
                        ),
                        "es": (
                            "✏️ **Swap personalizado**\n\n"
                            "Escribe tu comando, por ejemplo:\n"
                            "• **swap 50 USDC a PURR**\n"
                            "• **swap todo PURR a USDC**"
                        ),
                        "pt": (
                            "✏️ **Swap personalizado**\n\n"
                            "Digite seu comando, por exemplo:\n"
                            "• **swap 50 USDC para PURR**\n"
                            "• **swap tudo PURR para USDC**"
                        ),
                    }
                    return (
                        custom_prompt.get(
                            user_context.language, custom_prompt["en"]
                        ),
                        state,
                    )

                if action_type == "refresh":
                    await self._trigger_on_demand_sync(user_context)
                    state = WorkflowState()
                    state.step = WorkflowStep.PARSE_REQUEST.value
                    state.data["action"] = "view_positions"
                    return await self._handle_my_swaps_request(
                        message, state, user_context
                    )

            # Legacy: number as position index (when no numbered_actions)
            if positions and 1 <= selection <= len(positions):
                selected = positions[selection - 1]
                token = selected["token"]
                balance = selected["balance"]
                source = selected["source"]

                state.data.pop("awaiting_swap_position_selection", None)

                if source == "spot":
                    state.data["from_token"] = token.upper()
                    state.data["available_balance"] = balance

                    language = user_context.language
                    usd_str = (
                        f" (~${selected['usd_value']:,.2f})"
                        if selected.get("usd_value", 0) > 0
                        else ""
                    )
                    prompt = {
                        "en": (
                            f"🔄 **Swap {token}**\n\n"
                            f"Available: **{balance:,.4f} {token}**{usd_str}\n\n"
                            f"What would you like to swap it to?\n"
                            f"• Say **\"USDC\"** to sell to USDC\n"
                            f"• Say **\"PURR\"**, **\"TRUMP\"**, etc. to swap to another token\n"
                            f"• Say **\"all to USDC\"** to swap the full balance\n"
                            f"• Or specify an amount: **\"50 to USDC\"**"
                        ),
                        "es": (
                            f"🔄 **Swap {token}**\n\n"
                            f"Disponible: **{balance:,.4f} {token}**{usd_str}\n\n"
                            f"¿A qué token quieres cambiarlo?\n"
                            f"• Di **\"USDC\"** para vender a USDC\n"
                            f"• Di **\"todo a USDC\"** para cambiar todo el saldo"
                        ),
                        "pt": (
                            f"🔄 **Swap {token}**\n\n"
                            f"Disponível: **{balance:,.4f} {token}**{usd_str}\n\n"
                            f"Para qual token você quer trocar?\n"
                            f"• Diga **\"USDC\"** para vender para USDC\n"
                            f"• Diga **\"tudo para USDC\"** para trocar todo o saldo"
                        ),
                    }
                    state.data["awaiting_swap_destination"] = True
                    state.step = WorkflowStep.PARSE_REQUEST.value
                    return prompt.get(language, prompt["en"]), state

                if source == "perps":
                    language = user_context.language
                    perps_msg = {
                        "en": (
                            f"📈 **{token} {selected['side'].upper()} Position**\n\n"
                            f"• Size: {balance:,.4f}\n"
                            f"• Entry: ${selected.get('entry_price', 0):,.2f}\n"
                            f"• Mark: ${selected.get('mark_price', 0):,.2f}\n"
                            f"• PnL: ${selected.get('pnl', 0):,.2f}\n\n"
                            f"⚠️ Perpetual position management (close/modify) is coming soon.\n"
                            f"For now, you can manage perps positions directly on "
                            f"[Hyperliquid](https://app.hyperliquid.xyz)."
                        ),
                        "es": (
                            f"📈 **Posición {token} {selected['side'].upper()}**\n\n"
                            f"• Tamaño: {balance:,.4f}\n"
                            f"• Entrada: ${selected.get('entry_price', 0):,.2f}\n"
                            f"• PnL: ${selected.get('pnl', 0):,.2f}\n\n"
                            f"⚠️ La gestión de posiciones perpetuas estará disponible pronto."
                        ),
                        "pt": (
                            f"📈 **Posição {token} {selected['side'].upper()}**\n\n"
                            f"• Tamanho: {balance:,.4f}\n"
                            f"• Entrada: ${selected.get('entry_price', 0):,.2f}\n"
                            f"• PnL: ${selected.get('pnl', 0):,.2f}\n\n"
                            f"⚠️ O gerenciamento de posições perpétuas estará disponível em breve."
                        ),
                    }
                    return perps_msg.get(language, perps_msg["en"]), state

            # Selection out of range
            max_num = len(numbered_actions) if numbered_actions else len(positions)
            return (
                f"❌ Please select a number between 1 and {max_num}.",
                state,
            )
        except ValueError:
            pass

        # Check if user is providing a destination token after selecting a position
        if state.data.get("awaiting_swap_destination"):
            return await self._handle_swap_destination(message, state, user_context)

        # Unrecognized input – re-show positions
        return await self._handle_my_swaps_request(message, state, user_context)

    async def _handle_swap_destination(
        self,
        message: MessageContent,
        state: WorkflowState,
        user_context: UserContext,
    ) -> tuple[str, WorkflowState]:
        """Handle destination token selection after user picked a position."""
        text = message.value.strip()
        text_lower = text.lower()
        from_token = state.data.get("from_token", "")
        available_balance = state.data.get("available_balance", 0)

        state.data.pop("awaiting_swap_destination", None)

        # Parse "all to USDC" / "todo a USDC" / "tudo para USDC"
        all_match = re.match(
            r"(?:all|todo|tudo|max)\s+(?:to|a|para)\s+(\w+)", text_lower
        )
        if all_match:
            to_token = all_match.group(1).upper()
            state.data["to_token"] = to_token
            state.data["amount"] = available_balance
            state.data["provider"] = "hyperliquid"
            state.step = WorkflowStep.FETCH_DATA.value
            return await self._handle_fetch_quote(message, state, user_context)

        # Parse "<amount> to <TOKEN>" / "<amount> a <TOKEN>"
        amount_to_match = re.match(
            r"([\d.,]+)\s+(?:to|a|para)\s+(\w+)", text_lower
        )
        if amount_to_match:
            try:
                amount = float(amount_to_match.group(1).replace(",", ""))
            except ValueError:
                amount = available_balance
            to_token = amount_to_match.group(2).upper()
            state.data["to_token"] = to_token
            state.data["amount"] = min(amount, available_balance)
            state.data["provider"] = "hyperliquid"
            state.step = WorkflowStep.FETCH_DATA.value
            return await self._handle_fetch_quote(message, state, user_context)

        # Just a token name (e.g. "USDC", "PURR")
        token_match = re.match(r"^([A-Za-z]{2,10})$", text.strip())
        if token_match:
            to_token = token_match.group(1).upper()
            # Ask for amount
            state.data["to_token"] = to_token
            language = user_context.language
            prompt = {
                "en": (
                    f"How much **{from_token}** do you want to swap to **{to_token}**?\n\n"
                    f"Available: **{available_balance:,.4f} {from_token}**\n\n"
                    f"• Enter an amount (e.g. **100**)\n"
                    f"• Or say **\"all\"** / **\"max\"** for the full balance"
                ),
                "es": (
                    f"¿Cuánto **{from_token}** quieres cambiar a **{to_token}**?\n\n"
                    f"Disponible: **{available_balance:,.4f} {from_token}**\n\n"
                    f"• Ingresa una cantidad (ej. **100**)\n"
                    f"• O di **\"todo\"** / **\"max\"** para el saldo completo"
                ),
                "pt": (
                    f"Quanto **{from_token}** você quer trocar para **{to_token}**?\n\n"
                    f"Disponível: **{available_balance:,.4f} {from_token}**\n\n"
                    f"• Digite uma quantidade (ex. **100**)\n"
                    f"• Ou diga **\"tudo\"** / **\"max\"** para o saldo completo"
                ),
            }
            state.data["awaiting_swap_amount_from_position"] = True
            state.step = WorkflowStep.PARSE_REQUEST.value
            return prompt.get(language, prompt["en"]), state

        # Try to parse as a full swap command
        new_params = await self._extract_swap_params(text)
        if new_params.get("to_token"):
            to_token = new_params["to_token"].upper()
            amount = new_params.get("amount", available_balance)
            state.data["to_token"] = to_token
            state.data["amount"] = (
                min(float(amount), available_balance) if amount else available_balance
            )
            state.data["provider"] = "hyperliquid"
            state.step = WorkflowStep.FETCH_DATA.value
            return await self._handle_fetch_quote(message, state, user_context)

        # Fallback
        return (
            "Please specify the destination token. "
            "For example: **USDC**, **PURR**, or **\"all to USDC\"**",
            state,
        )

    async def _handle_swap_amount_from_position(
        self,
        message: MessageContent,
        state: WorkflowState,
        user_context: UserContext,
    ) -> tuple[str, WorkflowState]:
        """Handle amount input after from_token and to_token are set from position selection."""
        text = message.value.strip().lower()
        from_token = state.data.get("from_token", "")
        to_token = state.data.get("to_token", "")
        available_balance = state.data.get("available_balance", 0)

        state.data.pop("awaiting_swap_amount_from_position", None)

        # "all" / "max" / "todo" / "tudo"
        if text in ("all", "max", "todo", "tudo", "todo el saldo", "tudo o saldo"):
            state.data["amount"] = available_balance
            state.data["provider"] = "hyperliquid"
            state.step = WorkflowStep.FETCH_DATA.value
            return await self._handle_fetch_quote(message, state, user_context)

        # Try to parse a number
        try:
            clean = text.replace("$", "").replace(",", "").strip()
            amount = float(clean)
            if amount <= 0:
                return ("❌ Amount must be greater than 0.", state)
            state.data["amount"] = min(amount, available_balance)
            state.data["provider"] = "hyperliquid"
            state.step = WorkflowStep.FETCH_DATA.value
            return await self._handle_fetch_quote(message, state, user_context)
        except ValueError:
            pass

        # Unrecognized – re-prompt
        language = user_context.language
        return (
            f"Please enter an amount of **{from_token}** to swap to **{to_token}**, "
            f"or say **\"all\"** for the full balance ({available_balance:,.4f} {from_token}).",
            state,
        )

    async def _trigger_on_demand_sync(
        self,
        user_context: UserContext,
    ) -> None:
        """
        Trigger on-demand Celery sync for this user's wallet.

        Falls back to direct API sync if Celery is unavailable.
        """
        wallet_address = user_context.wallet_address
        user_id = user_context.user_id

        if not wallet_address or not user_id:
            return

        try:
            # Try Celery task first (non-blocking, runs in background)
            from app.infrastructure.celery.tasks.swap_position_sync_tasks import (
                sync_swap_positions_for_wallet,
            )

            sync_swap_positions_for_wallet.delay(int(user_id), wallet_address)
            logger.info(
                "[SwapWorkflow] On-demand sync triggered for %s",
                wallet_address[:10],
            )
            # Give the task a moment to complete
            import asyncio
            await asyncio.sleep(2)
        except Exception as e:
            logger.warning(
                "[SwapWorkflow] Celery on-demand sync failed, using direct API: %s", e
            )
            # Fallback: direct API sync (same as before, but writes to DB)
            if self._hyperliquid:
                try:
                    from datetime import datetime, UTC
                    import os

                    from sqlalchemy import text as sa_text
                    from sqlalchemy.dialects.postgresql import insert as pg_insert
                    from sqlalchemy.ext.asyncio import (
                        create_async_engine,
                        AsyncSession as _AsyncSession,
                    )
                    from sqlalchemy.orm import sessionmaker as _sessionmaker

                    db_url = os.environ.get("DATABASE_URL")
                    if not db_url:
                        db_host = os.environ.get("POSTGRES_HOST", "localhost")
                        db_port = os.environ.get("POSTGRES_PORT", "5432")
                        db_user_env = os.environ.get("POSTGRES_USER", "postgres")
                        db_pass = os.environ.get("POSTGRES_PASSWORD", "changethis")
                        db_name = os.environ.get("POSTGRES_DB", "anvil_db")
                        db_url = (
                            f"postgresql+psycopg://{db_user_env}:{db_pass}"
                            f"@{db_host}:{db_port}/{db_name}"
                        )

                    engine = create_async_engine(db_url, pool_pre_ping=True)
                    async_session = _sessionmaker(
                        engine, class_=_AsyncSession, expire_on_commit=False
                    )
                    now = datetime.now(UTC)

                    spot_balances = await self._hyperliquid.get_spot_balance(
                        wallet_address
                    )

                    async with async_session() as session:
                        for token, balance in spot_balances.items():
                            if balance <= 0:
                                continue
                            usd_value = 0.0
                            if token.upper() in ("USDC", "USDT"):
                                usd_value = balance
                            else:
                                try:
                                    price = await self._hyperliquid.get_spot_price(
                                        token, "USDC"
                                    )
                                    usd_value = balance * price
                                except Exception:
                                    pass
                            await session.execute(
                                sa_text("""
                                    INSERT INTO swap_positions
                                        (user_id, wallet_address, source, token,
                                         balance, usd_value, side, synced_at)
                                    VALUES (:uid, LOWER(:addr), 'spot', :token,
                                            :balance, :usd_val, 'hold', :now)
                                    ON CONFLICT (wallet_address, source, token)
                                    DO UPDATE SET
                                        balance = :balance,
                                        usd_value = :usd_val,
                                        synced_at = :now
                                """),
                                {
                                    "uid": int(user_id),
                                    "addr": wallet_address,
                                    "token": token,
                                    "balance": balance,
                                    "usd_val": round(usd_value, 2),
                                    "now": now,
                                },
                            )
                        await session.commit()
                    await engine.dispose()
                    logger.info(
                        "[SwapWorkflow] Direct API sync done for %s",
                        wallet_address[:10],
                    )
                except Exception as ex:
                    logger.warning(
                        "[SwapWorkflow] Direct API fallback sync failed: %s", ex
                    )

    async def _fetch_cached_positions(
        self,
        wallet_address: str,
    ) -> list[dict]:
        """
        Read cached Hyperliquid positions from swap_positions table.

        Returns list of dicts with source, token, balance, usd_value, side,
        and perps-specific fields (entry_price, mark_price, etc.).
        Data is synced every 60s by the swap_positions.sync Celery task.
        """
        try:
            import os

            from sqlalchemy import text as sa_text
            from sqlalchemy.ext.asyncio import (
                create_async_engine,
                AsyncSession as _AsyncSession,
            )
            from sqlalchemy.orm import sessionmaker as _sessionmaker

            db_url = os.environ.get("DATABASE_URL")
            if not db_url:
                db_host = os.environ.get("POSTGRES_HOST", "localhost")
                db_port = os.environ.get("POSTGRES_PORT", "5432")
                db_user = os.environ.get("POSTGRES_USER", "postgres")
                db_pass = os.environ.get("POSTGRES_PASSWORD", "changethis")
                db_name = os.environ.get("POSTGRES_DB", "anvil_db")
                db_url = (
                    f"postgresql+psycopg://{db_user}:{db_pass}"
                    f"@{db_host}:{db_port}/{db_name}"
                )

            engine = create_async_engine(db_url, pool_pre_ping=True)
            async_session = _sessionmaker(
                engine, class_=_AsyncSession, expire_on_commit=False
            )

            rows: list[dict] = []
            async with async_session() as session:
                result = await session.execute(
                    sa_text("""
                        SELECT source, token, balance::text, usd_value::text,
                               side, entry_price::text, mark_price::text,
                               unrealized_pnl::text, leverage::text,
                               liquidation_price::text, synced_at::text
                        FROM swap_positions
                        WHERE LOWER(wallet_address) = LOWER(:addr)
                        AND balance > 0
                        ORDER BY usd_value DESC
                    """),
                    {"addr": wallet_address},
                )
                for row in result.mappings().all():
                    rows.append({
                        "source": row.get("source", "spot"),
                        "token": row.get("token", ""),
                        "balance": row.get("balance", "0"),
                        "usd_value": row.get("usd_value", "0"),
                        "side": row.get("side", "hold"),
                        "entry_price": row.get("entry_price"),
                        "mark_price": row.get("mark_price"),
                        "unrealized_pnl": row.get("unrealized_pnl"),
                        "leverage": row.get("leverage"),
                        "synced_at": row.get("synced_at", ""),
                    })

            await engine.dispose()
            logger.info(
                "[SwapWorkflow] Fetched %d cached positions for %s",
                len(rows),
                wallet_address[:10],
            )
            return rows

        except Exception as e:
            logger.warning(
                "[SwapWorkflow] Failed to fetch cached positions: %s", e
            )
            return []

    async def _get_tradeable_spot_tokens(self) -> set[str]:
        """
        Return the set of base-token names that have an active spot market
        on Hyperliquid (i.e. appear in ``spotMeta.universe``).

        Tokens that exist only as EVM tokens without a Core spot market
        (e.g. MOON, EUR) are excluded — they cannot be traded via the API.

        The result is cached on the instance for the lifetime of the agent
        so subsequent calls (routing, recommendations) don't re-fetch.
        """
        if self._cached_tradeable_spot is not None:
            return self._cached_tradeable_spot
        if not self._hyperliquid:
            return set()
        try:
            meta = await self._hyperliquid.get_spot_meta()
            self._cached_tradeable_spot = {m.base_token.upper() for m in meta}
            return self._cached_tradeable_spot
        except Exception as e:
            logger.warning(
                "[SwapWorkflow] Failed to fetch tradeable spot tokens: %s", e
            )
            return set()

    async def _fetch_top_sentiment_tokens(
        self,
        limit: int = 10,
    ) -> list[dict]:
        """
        Fetch top-ranked tokens by sentiment score from hl_spot_tokens.

        Only returns tokens that have an **active Core spot market** on
        Hyperliquid (``has_spot_market = true``).  EVM-only tokens that
        cannot be traded via the API are excluded at the SQL level.

        Returns list of dicts with name, sentiment_score,
        sentiment_classification, sentiment_interpretation.
        Ordered by sentiment_score DESC, only enriched tokens.
        """
        try:
            import os

            from sqlalchemy import text as sa_text
            from sqlalchemy.ext.asyncio import (
                create_async_engine,
                AsyncSession as _AsyncSession,
            )
            from sqlalchemy.orm import sessionmaker as _sessionmaker

            db_url = os.environ.get("DATABASE_URL")
            if not db_url:
                db_host = os.environ.get("POSTGRES_HOST", "localhost")
                db_port = os.environ.get("POSTGRES_PORT", "5432")
                db_user = os.environ.get("POSTGRES_USER", "postgres")
                db_pass = os.environ.get("POSTGRES_PASSWORD", "changethis")
                db_name = os.environ.get("POSTGRES_DB", "anvil_db")
                db_url = (
                    f"postgresql+psycopg://{db_user}:{db_pass}"
                    f"@{db_host}:{db_port}/{db_name}"
                )

            engine = create_async_engine(db_url, pool_pre_ping=True)
            async_session = _sessionmaker(
                engine, class_=_AsyncSession, expire_on_commit=False
            )

            tokens: list[dict] = []
            async with async_session() as session:
                result = await session.execute(
                    sa_text("""
                        SELECT name,
                               sentiment_score::text,
                               sentiment_classification,
                               sentiment_interpretation
                        FROM hl_spot_tokens
                        WHERE status = 'enriched'
                          AND has_spot_market = true
                          AND sentiment_score IS NOT NULL
                          AND name NOT IN ('USDC', 'USDT', 'DAI')
                        ORDER BY sentiment_score DESC
                        LIMIT :lim
                    """),
                    {"lim": limit},
                )
                for row in result.mappings().all():
                    tokens.append({
                        "name": row.get("name", ""),
                        "sentiment_score": float(
                            row.get("sentiment_score", "0") or "0"
                        ),
                        "sentiment_classification": row.get(
                            "sentiment_classification", ""
                        ),
                        "sentiment_interpretation": row.get(
                            "sentiment_interpretation", ""
                        ),
                    })

            await engine.dispose()
            logger.info(
                "[SwapWorkflow] Fetched %d tradeable sentiment tokens",
                len(tokens),
            )
            return tokens

        except Exception as e:
            logger.warning(
                "[SwapWorkflow] Failed to fetch sentiment tokens: %s", e
            )
            return []

    async def _fetch_recent_swaps_from_db(
        self,
        user_id: str | None,
        wallet_address: str,
    ) -> list[dict]:
        """Fetch recent swap transactions from the transactions table."""
        if not user_id:
            return []
        try:
            import os

            from sqlalchemy import text as sa_text
            from sqlalchemy.ext.asyncio import (
                create_async_engine,
                AsyncSession as _AsyncSession,
            )
            from sqlalchemy.orm import sessionmaker as _sessionmaker

            # Build DB URL from environment/config
            db_url = os.environ.get("DATABASE_URL")
            if not db_url:
                db_host = os.environ.get("POSTGRES_HOST", "localhost")
                db_port = os.environ.get("POSTGRES_PORT", "5432")
                db_user = os.environ.get("POSTGRES_USER", "postgres")
                db_pass = os.environ.get("POSTGRES_PASSWORD", "changethis")
                db_name = os.environ.get("POSTGRES_DB", "anvil_db")
                db_url = (
                    f"postgresql+psycopg://{db_user}:{db_pass}"
                    f"@{db_host}:{db_port}/{db_name}"
                )

            engine = create_async_engine(db_url, pool_pre_ping=True)
            async_session = _sessionmaker(
                engine, class_=_AsyncSession, expire_on_commit=False
            )

            swaps: list[dict] = []
            async with async_session() as session:
                result = await session.execute(
                    sa_text("""
                        SELECT asset_in, amount_in::text, asset_out, amount_out::text,
                               chain, dex_aggregator, confirmed_at::text, tx_hash
                        FROM transactions
                        WHERE user_id = :uid AND type = 2
                        ORDER BY confirmed_at DESC NULLS LAST
                        LIMIT 10
                    """),
                    {"uid": int(user_id)},
                )
                for row in result.mappings().all():
                    swaps.append({
                        "asset_in": row.get("asset_in", ""),
                        "amount_in": float(row.get("amount_in", 0) or 0),
                        "asset_out": row.get("asset_out", ""),
                        "amount_out": float(row.get("amount_out", 0) or 0),
                        "chain": row.get("chain", ""),
                        "dex_aggregator": row.get("dex_aggregator", ""),
                        "confirmed_at": row.get("confirmed_at", ""),
                        "tx_hash": row.get("tx_hash", ""),
                    })

            await engine.dispose()
            return swaps

        except Exception as e:
            logger.warning("[SwapWorkflow] Failed to fetch recent swaps from DB: %s", e)
            return []
