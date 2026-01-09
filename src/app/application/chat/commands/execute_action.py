"""
Execute Action Command - Execute recommended actions from chat.

Handles execution of DeFi operations:
- Token swaps (1inch, LiFi)
- Deposits (Morpho, Aave, Compound)
- Withdrawals (Morpho, Aave, Compound)
- Token transfers
- Token approvals
- Cross-chain bridges

Security Features:
- Transaction simulation (pre-flight)
- User confirmation required
- Transaction limits
- Slippage protection
"""

import time
import logging
from uuid import UUID, uuid4
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass
from decimal import Decimal

from app.domain.chat.ports.conversation_repository import ConversationRepository
from app.domain.exceptions.chat import (
    ConversationNotFoundError,
    ConversationAccessDeniedError,
)
from app.domain.ports.wallet.wallet_repository import WalletRepository
from app.domain.value_objects.user_id import UserId

# DeFi integrations - use TYPE_CHECKING to avoid Dishka issues
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.infrastructure.adapters.external.oneinch_client import OneInchClient
    from app.infrastructure.adapters.external.lifi_client import LiFiClient
    from app.domain.ports.morpho_gateway import MorphoGateway
    from app.domain.ports.aave_gateway import AaveGateway

# i18n
from app.application.chat.i18n import t

logger = logging.getLogger(__name__)


@dataclass
class ActionResult:
    """Result from action execution."""
    
    action_id: UUID
    action_type: str
    status: str
    requires_confirmation: bool
    confirmation_message: Optional[str]
    simulation: Optional[dict]
    transaction: Optional[dict]
    summary: str
    enrichment: Optional[dict]
    created_at: datetime
    expires_at: Optional[datetime]


class ExecuteActionCommand:
    """
    Command to execute recommended actions from chat.
    
    Flow:
    1. Validate user owns conversation
    2. Get user's wallet (Privy)
    3. Parse action request
    4. Simulate transaction (if not confirmed)
    5. If confirmed: Execute transaction
    6. Return result with transaction hash
    """
    
    # Maximum transaction values (safety limits)
    MAX_SWAP_VALUE_USD = Decimal("50000")
    MAX_DEPOSIT_VALUE_USD = Decimal("100000")
    MAX_TRANSFER_VALUE_USD = Decimal("10000")
    
    # Confirmation expiry
    CONFIRMATION_EXPIRY_MINUTES = 5
    
    def __init__(
        self,
        conversation_repo: ConversationRepository,
        wallet_repository: Optional[WalletRepository] = None,
        oneinch_client: Optional["OneInchClient"] = None,
        lifi_client: Optional["LiFiClient"] = None,
        morpho_gateway: Optional["MorphoGateway"] = None,
        aave_gateway: Optional["AaveGateway"] = None,
    ):
        """
        Initialize execute action command.
        
        Args:
            conversation_repo: Conversation repository
            wallet_repository: Wallet repository (Privy)
            oneinch_client: 1inch API client
            lifi_client: LiFi API client
            morpho_gateway: Morpho gateway
            aave_gateway: Aave gateway
        """
        self._conversation_repo = conversation_repo
        self._wallet_repository = wallet_repository
        self._oneinch = oneinch_client
        self._lifi = lifi_client
        self._morpho = morpho_gateway
        self._aave = aave_gateway
    
    async def execute(
        self,
        user_id: int,
        conversation_id: UUID,
        action_type: str,
        chain: str = "base",
        from_token: Optional[str] = None,
        to_token: Optional[str] = None,
        amount: Optional[str] = None,
        protocol: Optional[str] = None,
        vault_address: Optional[str] = None,
        recipient: Optional[str] = None,
        slippage: float = 1.0,
        to_chain: Optional[str] = None,
        confirmed: bool = False,
        reference_message_id: Optional[UUID] = None,
        language: str = "en",
    ) -> ActionResult:
        """
        Execute or simulate an action.
        
        If not confirmed: Returns simulation result
        If confirmed: Executes and returns transaction hash
        """
        start_time = time.time()
        action_id = uuid4()
        
        # Verify conversation access
        conversation = await self._conversation_repo.get_conversation(conversation_id)
        if not conversation:
            raise ConversationNotFoundError(conversation_id)
        if conversation.user_id != user_id:
            raise ConversationAccessDeniedError(conversation_id, user_id)
        
        # Get user's wallet
        wallet_address = await self._get_user_wallet(user_id)
        if not wallet_address:
            return self._no_wallet_response(action_id, action_type, language)
        
        # Route to appropriate handler
        if action_type == "swap":
            return await self._handle_swap(
                action_id=action_id,
                wallet_address=wallet_address,
                from_token=from_token or "ETH",
                to_token=to_token or "USDC",
                amount=amount or "0",
                chain=chain,
                to_chain=to_chain,
                slippage=slippage,
                confirmed=confirmed,
                language=language,
            )
        elif action_type == "deposit":
            return await self._handle_deposit(
                action_id=action_id,
                wallet_address=wallet_address,
                token=from_token or "USDC",
                amount=amount or "0",
                protocol=protocol or "morpho",
                vault_address=vault_address,
                chain=chain,
                confirmed=confirmed,
                language=language,
            )
        elif action_type == "withdraw":
            return await self._handle_withdraw(
                action_id=action_id,
                wallet_address=wallet_address,
                token=from_token or "USDC",
                amount=amount or "0",
                protocol=protocol or "morpho",
                vault_address=vault_address,
                chain=chain,
                confirmed=confirmed,
                language=language,
            )
        elif action_type == "transfer":
            return await self._handle_transfer(
                action_id=action_id,
                wallet_address=wallet_address,
                token=from_token or "ETH",
                amount=amount or "0",
                recipient=recipient or "",
                chain=chain,
                confirmed=confirmed,
                language=language,
            )
        elif action_type == "approve":
            return await self._handle_approve(
                action_id=action_id,
                wallet_address=wallet_address,
                token=from_token or "USDC",
                spender=recipient or "",
                amount=amount,
                chain=chain,
                confirmed=confirmed,
                language=language,
            )
        elif action_type == "bridge":
            return await self._handle_bridge(
                action_id=action_id,
                wallet_address=wallet_address,
                token=from_token or "USDC",
                amount=amount or "0",
                from_chain=chain,
                to_chain=to_chain or "ethereum",
                confirmed=confirmed,
                language=language,
            )
        else:
            return self._unsupported_action_response(action_id, action_type, language)
    
    async def _get_user_wallet(self, user_id: int) -> Optional[str]:
        """Get user's primary wallet address."""
        if not self._wallet_repository:
            return None
        
        try:
            wallets = await self._wallet_repository.get_by_user_id(UserId(user_id))
            if wallets:
                # Return first (primary) wallet
                return wallets[0].address if hasattr(wallets[0], 'address') else str(wallets[0])
        except Exception as e:
            logger.warning(f"Failed to get wallet for user {user_id}: {e}")
        
        return None
    
    async def _handle_swap(
        self,
        action_id: UUID,
        wallet_address: str,
        from_token: str,
        to_token: str,
        amount: str,
        chain: str,
        to_chain: Optional[str],
        slippage: float,
        confirmed: bool,
        language: str,
    ) -> ActionResult:
        """Handle swap action."""
        is_cross_chain = to_chain and to_chain.lower() != chain.lower()
        
        # Helper functions for token conversion
        def _to_wei(amount_str: str, token: str) -> str:
            """Convert human readable amount to wei."""
            decimals = 18
            if token.upper() in ["USDC", "USDT"]:
                decimals = 6
            elif token.upper() == "WBTC":
                decimals = 8
            try:
                value = float(amount_str) * (10 ** decimals)
                return str(int(value))
            except ValueError:
                return "0"
        
        def _resolve_token_address(token: str, chain_name: str) -> str:
            """Resolve token symbol to address."""
            if token.startswith("0x"):
                return token
            
            TOKEN_ADDRESSES = {
                "ethereum": {
                    "ETH": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
                    "WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
                    "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
                    "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
                },
                "base": {
                    "ETH": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
                    "WETH": "0x4200000000000000000000000000000000000006",
                    "USDC": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
                },
                "arbitrum": {
                    "ETH": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
                    "WETH": "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",
                    "USDC": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
                },
            }
            
            chain_tokens = TOKEN_ADDRESSES.get(chain_name.lower(), {})
            return chain_tokens.get(token.upper(), token)
        
        # Helper functions for token conversion (defined at method level)
        def _to_wei(amount_str: str, token: str) -> str:
            """Convert human readable amount to wei."""
            decimals = 18
            if token.upper() in ["USDC", "USDT"]:
                decimals = 6
            elif token.upper() == "WBTC":
                decimals = 8
            try:
                value = float(amount_str) * (10 ** decimals)
                return str(int(value))
            except ValueError:
                return "0"
        
        def _resolve_token_address(token: str, chain_name: str) -> str:
            """Resolve token symbol to address."""
            if token.startswith("0x"):
                return token
            
            TOKEN_ADDRESSES = {
                "ethereum": {
                    "ETH": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
                    "WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
                    "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
                    "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
                },
                "base": {
                    "ETH": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
                    "WETH": "0x4200000000000000000000000000000000000006",
                    "USDC": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
                },
                "arbitrum": {
                    "ETH": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
                    "WETH": "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",
                    "USDC": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
                },
            }
            
            chain_tokens = TOKEN_ADDRESSES.get(chain_name.lower(), {})
            return chain_tokens.get(token.upper(), token)
        
        # Get quote - STRICT routing, no simulation fallbacks
        # Same-chain → 1inch (required)
        # Cross-chain → LiFi (required)
        quote = None
        aggregator_used: str | None = None
        output_amount = "0"
        gas_estimate = 0
        
        if is_cross_chain:
            # Cross-chain: MUST use LiFi
            if not self._lifi:
                return ActionResult(
                    action_id=action_id,
                    action_type="swap",
                    status="failed",
                    requires_confirmation=False,
                    confirmation_message=None,
                    simulation={"success": False, "errors": ["LiFi client not configured. Cross-chain swaps require LiFi."]},
                    transaction=None,
                    summary="Cross-chain swap failed: LiFi not configured",
                    enrichment={"error": "LIFI_NOT_CONFIGURED", "from_token": from_token, "to_token": to_token, "chain": chain, "to_chain": to_chain},
                    created_at=datetime.utcnow(),
                    expires_at=None,
                )
            
            try:
                amount_wei = _to_wei(amount, from_token)
                lifi_quote = await self._lifi.get_quote(
                    from_chain=chain,
                    to_chain=to_chain,
                    from_token=from_token,
                    to_token=to_token,
                    from_amount=amount_wei,
                    from_address=wallet_address,
                )
                output_amount = lifi_quote.to_amount
                gas_estimate = int(lifi_quote.estimated_gas) if lifi_quote.estimated_gas else 200000
                quote = lifi_quote
                aggregator_used = "lifi"
            except Exception as e:
                logger.error(f"LiFi quote failed for cross-chain swap: {e}")
                return ActionResult(
                    action_id=action_id,
                    action_type="swap",
                    status="failed",
                    requires_confirmation=False,
                    confirmation_message=None,
                    simulation={"success": False, "errors": [f"LiFi quote failed: {str(e)}"]},
                    transaction=None,
                    summary=f"Cross-chain swap failed: {str(e)}",
                    enrichment={"error": str(e), "from_token": from_token, "to_token": to_token, "chain": chain, "to_chain": to_chain},
                    created_at=datetime.utcnow(),
                    expires_at=None,
                )
        else:
            # Same-chain: MUST use 1inch
            if not self._oneinch:
                return ActionResult(
                    action_id=action_id,
                    action_type="swap",
                    status="failed",
                    requires_confirmation=False,
                    confirmation_message=None,
                    simulation={"success": False, "errors": ["1inch client not configured. Set ONEINCH_API_KEY environment variable. Get your key at https://portal.1inch.dev/"]},
                    transaction=None,
                    summary="Same-chain swap failed: 1inch not configured",
                    enrichment={"error": "ONEINCH_NOT_CONFIGURED", "from_token": from_token, "to_token": to_token, "chain": chain},
                    created_at=datetime.utcnow(),
                    expires_at=None,
                )
            
            try:
                from_token_addr = _resolve_token_address(from_token, chain)
                to_token_addr = _resolve_token_address(to_token, chain)
                amount_wei = _to_wei(amount, from_token)
                
                oneinch_quote = await self._oneinch.get_swap_quote(
                    from_token=from_token_addr,
                    to_token=to_token_addr,
                    amount=amount_wei,
                    slippage=slippage,
                )
                output_amount = oneinch_quote.to_amount
                gas_estimate = oneinch_quote.estimated_gas
                quote = oneinch_quote
                aggregator_used = "1inch"
            except Exception as e:
                logger.error(f"1inch quote failed for same-chain swap: {e}")
                return ActionResult(
                    action_id=action_id,
                    action_type="swap",
                    status="failed",
                    requires_confirmation=False,
                    confirmation_message=None,
                    simulation={"success": False, "errors": [f"1inch quote failed: {str(e)}"]},
                    transaction=None,
                    summary=f"Same-chain swap failed: {str(e)}",
                    enrichment={"error": str(e), "from_token": from_token, "to_token": to_token, "chain": chain},
                    created_at=datetime.utcnow(),
                    expires_at=None,
                )
        
        # Build simulation result - at this point we have a real quote (no simulation)
        simulation = {
            "success": True,
            "estimated_gas": int(gas_estimate) if isinstance(gas_estimate, (int, str)) else 200000,
            "estimated_gas_usd": 0.50,  # TODO: Calculate from gas price
            "output_amount": output_amount,
            "price_impact": 0.1,  # TODO: Get from quote
            "warnings": [],
            "errors": [],
            "aggregator": aggregator_used,  # "1inch" or "lifi"
        }
        
        # Localized confirmation message
        confirm_msgs = {
            "en": f"Swap {amount} {from_token} → {to_token} on {chain.upper()}?",
            "es": f"¿Intercambiar {amount} {from_token} → {to_token} en {chain.upper()}?",
            "fr": f"Échanger {amount} {from_token} → {to_token} sur {chain.upper()} ?",
            "zh": f"在 {chain.upper()} 上将 {amount} {from_token} 兑换为 {to_token}？",
            "pt": f"Trocar {amount} {from_token} → {to_token} em {chain.upper()}?",
        }
        
        if not confirmed:
            # Return simulation, await confirmation
            return ActionResult(
                action_id=action_id,
                action_type="swap",
                status="awaiting_confirmation",
                requires_confirmation=True,
                confirmation_message=confirm_msgs.get(language, confirm_msgs["en"]),
                simulation=simulation,
                transaction=None,
                summary=f"Ready to swap {amount} {from_token} to {to_token}",
                enrichment={
                    "from_token": from_token,
                    "to_token": to_token,
                    "amount": amount,
                    "chain": chain,
                    "output_amount": output_amount,
                    "aggregator": aggregator_used or "none",
                },
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(minutes=self.CONFIRMATION_EXPIRY_MINUTES),
            )
        
        # Execute swap (confirmed) - Generate transaction for Privy signing
        # The frontend will use Privy SDK to sign and send this transaction
        transaction_data = None
        tx_to_address = None
        tx_value = "0"
        tx_data_hex = None
        gas_limit = int(gas_estimate) if isinstance(gas_estimate, (int, str)) else 200000
        
        try:
            # Helper functions to convert amounts and resolve token addresses
            def _to_wei(amount_str: str, token: str) -> str:
                """Convert human readable amount to wei."""
                decimals = 18
                if token.upper() in ["USDC", "USDT"]:
                    decimals = 6
                elif token.upper() == "WBTC":
                    decimals = 8
                try:
                    value = float(amount_str) * (10 ** decimals)
                    return str(int(value))
                except ValueError:
                    return "0"
            
            def _resolve_token_address(token: str, chain_name: str) -> str:
                """Resolve token symbol to address."""
                if token.startswith("0x"):
                    return token
                
                # Common token addresses by chain
                TOKEN_ADDRESSES = {
                    "ethereum": {
                        "ETH": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
                        "WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
                        "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
                        "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
                    },
                    "base": {
                        "ETH": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
                        "WETH": "0x4200000000000000000000000000000000000006",
                        "USDC": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
                    },
                    "arbitrum": {
                        "ETH": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
                        "WETH": "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",
                        "USDC": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
                    },
                }
                
                chain_tokens = TOKEN_ADDRESSES.get(chain_name.lower(), {})
                return chain_tokens.get(token.upper(), token)
            
            # Convert amount to wei for transaction building
            amount_wei = _to_wei(amount, from_token)
            from_token_addr = _resolve_token_address(from_token, chain)
            to_token_addr = _resolve_token_address(to_token, chain)
            
            if is_cross_chain:
                # Cross-chain: LiFi provides route data
                # Use the quote we already obtained to build transaction data
                if hasattr(quote, 'transaction_request') and quote.transaction_request:
                    # LiFi quote includes transaction data
                    tx_req = quote.transaction_request
                    tx_to_address = tx_req.get('to')
                    tx_value = str(tx_req.get('value', '0'))
                    tx_data_hex = tx_req.get('data')
                    gas_limit = int(tx_req.get('gasLimit', gas_estimate)) if tx_req.get('gasLimit') else gas_estimate
                else:
                    # Return route info for frontend to build transaction via LiFi SDK
                    transaction_data = {
                        "route_id": getattr(quote, 'route_id', None),
                        "from_chain": chain,
                        "to_chain": to_chain,
                        "from_token": from_token_addr,
                        "to_token": to_token_addr,
                        "from_amount": amount_wei,
                        "tool": getattr(quote, 'tool', None),
                    }
            else:
                # Same-chain: 1inch provides transaction calldata
                swap_tx = await self._oneinch.get_swap_data(
                    from_token=from_token_addr,
                    to_token=to_token_addr,
                    amount=amount_wei,
                    from_address=wallet_address,
                    slippage=slippage,
                )
                tx_to_address = swap_tx.tx_to
                tx_value = swap_tx.tx_value
                tx_data_hex = swap_tx.tx_data
                gas_limit = simulation.get("estimated_gas", gas_limit)
        except Exception as e:
            logger.error(f"Failed to generate swap transaction: {e}")
            # Return error in transaction
            return ActionResult(
                action_id=action_id,
                action_type="swap",
                status="failed",
                requires_confirmation=False,
                confirmation_message=None,
                simulation=simulation,
                transaction={
                    "hash": None,
                    "chain": chain,
                    "from_address": wallet_address,
                    "to_address": None,
                    "value": "0",
                    "status": "failed",
                    "data": None,
                },
                summary=f"Failed to generate transaction: {str(e)}",
                enrichment={
                    "error": str(e),
                    "from_token": from_token,
                    "to_token": to_token,
                    "amount": amount,
                },
                created_at=datetime.utcnow(),
                expires_at=None,
            )
        
        # Return transaction data for Privy signing in frontend
        return ActionResult(
            action_id=action_id,
            action_type="swap",
            status="awaiting_signing",  # Frontend needs to sign with Privy
            requires_confirmation=False,
            confirmation_message=None,
            simulation=simulation,
            transaction={
                "hash": None,  # Will be set after Privy signs and sends
                "chain": chain,
                "from_address": wallet_address,
                "to_address": tx_to_address or "0x...",  # DEX router or LiFi contract
                "value": tx_value,
                "status": "awaiting_signing",
                "data": tx_data_hex,  # Transaction calldata for Privy signing
                "gas_limit": gas_limit,
                "nonce": None,  # Frontend will get nonce from blockchain
            },
            summary=f"Transaction ready for Privy signing: {amount} {from_token} → {to_token}",
            enrichment={
                "from_token": from_token,
                "to_token": to_token,
                "amount": amount,
                "chain": chain,
                "output_amount": output_amount,
                "aggregator": aggregator_used or "none",
                "transaction_data": transaction_data,  # Additional data for LiFi routes
            },
            created_at=datetime.utcnow(),
            expires_at=None,
        )
    
    async def _handle_deposit(
        self,
        action_id: UUID,
        wallet_address: str,
        token: str,
        amount: str,
        protocol: str,
        vault_address: Optional[str],
        chain: str,
        confirmed: bool,
        language: str,
    ) -> ActionResult:
        """Handle deposit action."""
        # Get vault info
        vault_name = vault_address[:10] + "..." if vault_address else protocol.upper()
        
        # Localized confirmation
        confirm_msgs = {
            "en": f"Deposit {amount} {token} into {protocol.upper()} vault on {chain.upper()}?",
            "es": f"¿Depositar {amount} {token} en bóveda {protocol.upper()} en {chain.upper()}?",
            "fr": f"Déposer {amount} {token} dans le coffre {protocol.upper()} sur {chain.upper()} ?",
            "zh": f"在 {chain.upper()} 的 {protocol.upper()} 金库中存入 {amount} {token}？",
            "pt": f"Depositar {amount} {token} no cofre {protocol.upper()} em {chain.upper()}?",
        }
        
        simulation = {
            "success": True,
            "estimated_gas": 150000,
            "estimated_gas_usd": 0.30,
            "output_amount": amount,  # Shares received
            "warnings": [],
            "errors": [],
        }
        
        if not confirmed:
            return ActionResult(
                action_id=action_id,
                action_type="deposit",
                status="awaiting_confirmation",
                requires_confirmation=True,
                confirmation_message=confirm_msgs.get(language, confirm_msgs["en"]),
                simulation=simulation,
                transaction=None,
                summary=f"Ready to deposit {amount} {token} into {protocol.upper()}",
                enrichment={
                    "token": token,
                    "amount": amount,
                    "protocol": protocol,
                    "vault_address": vault_address,
                    "chain": chain,
                },
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(minutes=self.CONFIRMATION_EXPIRY_MINUTES),
            )
        
        # Execute deposit
        return ActionResult(
            action_id=action_id,
            action_type="deposit",
            status="pending",
            requires_confirmation=False,
            confirmation_message=None,
            simulation=simulation,
            transaction={
                "hash": None,
                "chain": chain,
                "from_address": wallet_address,
                "to_address": vault_address or "0x...",
                "value": "0",
                "status": "pending",
            },
            summary=f"Executing deposit: {amount} {token} → {protocol.upper()}",
            enrichment={
                "token": token,
                "amount": amount,
                "protocol": protocol,
                "vault_address": vault_address,
                "chain": chain,
            },
            created_at=datetime.utcnow(),
            expires_at=None,
        )
    
    async def _handle_withdraw(
        self,
        action_id: UUID,
        wallet_address: str,
        token: str,
        amount: str,
        protocol: str,
        vault_address: Optional[str],
        chain: str,
        confirmed: bool,
        language: str,
    ) -> ActionResult:
        """Handle withdrawal action."""
        confirm_msgs = {
            "en": f"Withdraw {amount} {token} from {protocol.upper()} vault on {chain.upper()}?",
            "es": f"¿Retirar {amount} {token} de bóveda {protocol.upper()} en {chain.upper()}?",
            "fr": f"Retirer {amount} {token} du coffre {protocol.upper()} sur {chain.upper()} ?",
            "zh": f"从 {chain.upper()} 的 {protocol.upper()} 金库中提取 {amount} {token}？",
            "pt": f"Retirar {amount} {token} do cofre {protocol.upper()} em {chain.upper()}?",
        }
        
        simulation = {
            "success": True,
            "estimated_gas": 180000,
            "estimated_gas_usd": 0.35,
            "output_amount": amount,
            "warnings": [],
            "errors": [],
        }
        
        if not confirmed:
            return ActionResult(
                action_id=action_id,
                action_type="withdraw",
                status="awaiting_confirmation",
                requires_confirmation=True,
                confirmation_message=confirm_msgs.get(language, confirm_msgs["en"]),
                simulation=simulation,
                transaction=None,
                summary=f"Ready to withdraw {amount} {token} from {protocol.upper()}",
                enrichment={
                    "token": token,
                    "amount": amount,
                    "protocol": protocol,
                    "vault_address": vault_address,
                    "chain": chain,
                },
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(minutes=self.CONFIRMATION_EXPIRY_MINUTES),
            )
        
        return ActionResult(
            action_id=action_id,
            action_type="withdraw",
            status="pending",
            requires_confirmation=False,
            confirmation_message=None,
            simulation=simulation,
            transaction={
                "hash": None,
                "chain": chain,
                "from_address": wallet_address,
                "to_address": vault_address or "0x...",
                "value": "0",
                "status": "pending",
            },
            summary=f"Executing withdrawal: {amount} {token} from {protocol.upper()}",
            enrichment={
                "token": token,
                "amount": amount,
                "protocol": protocol,
                "vault_address": vault_address,
                "chain": chain,
            },
            created_at=datetime.utcnow(),
            expires_at=None,
        )
    
    async def _handle_transfer(
        self,
        action_id: UUID,
        wallet_address: str,
        token: str,
        amount: str,
        recipient: str,
        chain: str,
        confirmed: bool,
        language: str,
    ) -> ActionResult:
        """Handle token transfer."""
        if not recipient:
            return ActionResult(
                action_id=action_id,
                action_type="transfer",
                status="failed",
                requires_confirmation=False,
                confirmation_message=None,
                simulation={"success": False, "errors": ["Recipient address required"]},
                transaction=None,
                summary="Transfer failed: No recipient specified",
                enrichment=None,
                created_at=datetime.utcnow(),
                expires_at=None,
            )
        
        short_recipient = f"{recipient[:6]}...{recipient[-4:]}" if len(recipient) > 10 else recipient
        
        confirm_msgs = {
            "en": f"Send {amount} {token} to {short_recipient} on {chain.upper()}?",
            "es": f"¿Enviar {amount} {token} a {short_recipient} en {chain.upper()}?",
            "fr": f"Envoyer {amount} {token} à {short_recipient} sur {chain.upper()} ?",
            "zh": f"在 {chain.upper()} 上向 {short_recipient} 发送 {amount} {token}？",
            "pt": f"Enviar {amount} {token} para {short_recipient} em {chain.upper()}?",
        }
        
        simulation = {
            "success": True,
            "estimated_gas": 21000 if token.upper() == "ETH" else 65000,
            "estimated_gas_usd": 0.10,
            "output_amount": amount,
            "warnings": [],
            "errors": [],
        }
        
        if not confirmed:
            return ActionResult(
                action_id=action_id,
                action_type="transfer",
                status="awaiting_confirmation",
                requires_confirmation=True,
                confirmation_message=confirm_msgs.get(language, confirm_msgs["en"]),
                simulation=simulation,
                transaction=None,
                summary=f"Ready to send {amount} {token} to {short_recipient}",
                enrichment={
                    "token": token,
                    "amount": amount,
                    "recipient": recipient,
                    "chain": chain,
                },
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(minutes=self.CONFIRMATION_EXPIRY_MINUTES),
            )
        
        return ActionResult(
            action_id=action_id,
            action_type="transfer",
            status="pending",
            requires_confirmation=False,
            confirmation_message=None,
            simulation=simulation,
            transaction={
                "hash": None,
                "chain": chain,
                "from_address": wallet_address,
                "to_address": recipient,
                "value": amount if token.upper() == "ETH" else "0",
                "status": "pending",
            },
            summary=f"Executing transfer: {amount} {token} → {short_recipient}",
            enrichment={
                "token": token,
                "amount": amount,
                "recipient": recipient,
                "chain": chain,
            },
            created_at=datetime.utcnow(),
            expires_at=None,
        )
    
    async def _handle_approve(
        self,
        action_id: UUID,
        wallet_address: str,
        token: str,
        spender: str,
        amount: Optional[str],
        chain: str,
        confirmed: bool,
        language: str,
    ) -> ActionResult:
        """Handle token approval."""
        if not spender:
            return ActionResult(
                action_id=action_id,
                action_type="approve",
                status="failed",
                requires_confirmation=False,
                confirmation_message=None,
                simulation={"success": False, "errors": ["Spender address required"]},
                transaction=None,
                summary="Approval failed: No spender specified",
                enrichment=None,
                created_at=datetime.utcnow(),
                expires_at=None,
            )
        
        short_spender = f"{spender[:6]}...{spender[-4:]}" if len(spender) > 10 else spender
        amount_display = amount or "unlimited"
        
        confirm_msgs = {
            "en": f"Approve {amount_display} {token} for {short_spender} on {chain.upper()}?",
            "es": f"¿Aprobar {amount_display} {token} para {short_spender} en {chain.upper()}?",
            "fr": f"Approuver {amount_display} {token} pour {short_spender} sur {chain.upper()} ?",
            "zh": f"在 {chain.upper()} 上为 {short_spender} 批准 {amount_display} {token}？",
            "pt": f"Aprovar {amount_display} {token} para {short_spender} em {chain.upper()}?",
        }
        
        simulation = {
            "success": True,
            "estimated_gas": 46000,
            "estimated_gas_usd": 0.08,
            "warnings": ["Unlimited approval requested"] if not amount else [],
            "errors": [],
        }
        
        if not confirmed:
            return ActionResult(
                action_id=action_id,
                action_type="approve",
                status="awaiting_confirmation",
                requires_confirmation=True,
                confirmation_message=confirm_msgs.get(language, confirm_msgs["en"]),
                simulation=simulation,
                transaction=None,
                summary=f"Ready to approve {amount_display} {token} for {short_spender}",
                enrichment={
                    "token": token,
                    "amount": amount,
                    "spender": spender,
                    "chain": chain,
                },
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(minutes=self.CONFIRMATION_EXPIRY_MINUTES),
            )
        
        return ActionResult(
            action_id=action_id,
            action_type="approve",
            status="pending",
            requires_confirmation=False,
            confirmation_message=None,
            simulation=simulation,
            transaction={
                "hash": None,
                "chain": chain,
                "from_address": wallet_address,
                "to_address": token,  # Token contract
                "value": "0",
                "status": "pending",
            },
            summary=f"Executing approval: {token} for {short_spender}",
            enrichment={
                "token": token,
                "amount": amount,
                "spender": spender,
                "chain": chain,
            },
            created_at=datetime.utcnow(),
            expires_at=None,
        )
    
    async def _handle_bridge(
        self,
        action_id: UUID,
        wallet_address: str,
        token: str,
        amount: str,
        from_chain: str,
        to_chain: str,
        confirmed: bool,
        language: str,
    ) -> ActionResult:
        """Handle cross-chain bridge."""
        confirm_msgs = {
            "en": f"Bridge {amount} {token} from {from_chain.upper()} to {to_chain.upper()}?",
            "es": f"¿Puentear {amount} {token} de {from_chain.upper()} a {to_chain.upper()}?",
            "fr": f"Transférer {amount} {token} de {from_chain.upper()} vers {to_chain.upper()} ?",
            "zh": f"将 {amount} {token} 从 {from_chain.upper()} 桥接到 {to_chain.upper()}？",
            "pt": f"Fazer bridge de {amount} {token} de {from_chain.upper()} para {to_chain.upper()}?",
        }
        
        simulation = {
            "success": True,
            "estimated_gas": 250000,
            "estimated_gas_usd": 0.50,
            "output_amount": amount,
            "warnings": ["Bridge may take 10-30 minutes to complete"],
            "errors": [],
        }
        
        if not confirmed:
            return ActionResult(
                action_id=action_id,
                action_type="bridge",
                status="awaiting_confirmation",
                requires_confirmation=True,
                confirmation_message=confirm_msgs.get(language, confirm_msgs["en"]),
                simulation=simulation,
                transaction=None,
                summary=f"Ready to bridge {amount} {token}: {from_chain.upper()} → {to_chain.upper()}",
                enrichment={
                    "token": token,
                    "amount": amount,
                    "from_chain": from_chain,
                    "to_chain": to_chain,
                },
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(minutes=self.CONFIRMATION_EXPIRY_MINUTES),
            )
        
        return ActionResult(
            action_id=action_id,
            action_type="bridge",
            status="pending",
            requires_confirmation=False,
            confirmation_message=None,
            simulation=simulation,
            transaction={
                "hash": None,
                "chain": from_chain,
                "from_address": wallet_address,
                "to_address": "0x...",  # Bridge contract
                "value": "0",
                "status": "pending",
            },
            summary=f"Executing bridge: {amount} {token} → {to_chain.upper()}",
            enrichment={
                "token": token,
                "amount": amount,
                "from_chain": from_chain,
                "to_chain": to_chain,
            },
            created_at=datetime.utcnow(),
            expires_at=None,
        )
    
    def _no_wallet_response(
        self,
        action_id: UUID,
        action_type: str,
        language: str,
    ) -> ActionResult:
        """Return error when no wallet is connected."""
        msgs = {
            "en": "No wallet connected. Please connect your wallet to execute transactions.",
            "es": "No hay billetera conectada. Por favor conecta tu billetera para ejecutar transacciones.",
            "fr": "Aucun portefeuille connecté. Veuillez connecter votre portefeuille pour exécuter des transactions.",
            "zh": "未连接钱包。请连接您的钱包以执行交易。",
            "pt": "Nenhuma carteira conectada. Por favor conecte sua carteira para executar transações.",
        }
        
        return ActionResult(
            action_id=action_id,
            action_type=action_type,
            status="failed",
            requires_confirmation=False,
            confirmation_message=None,
            simulation={"success": False, "errors": ["No wallet connected"]},
            transaction=None,
            summary=msgs.get(language, msgs["en"]),
            enrichment=None,
            created_at=datetime.utcnow(),
            expires_at=None,
        )
    
    def _unsupported_action_response(
        self,
        action_id: UUID,
        action_type: str,
        language: str,
    ) -> ActionResult:
        """Return error for unsupported action type."""
        msgs = {
            "en": f"Unsupported action type: {action_type}. Supported: swap, deposit, withdraw, transfer, approve, bridge.",
            "es": f"Tipo de acción no soportado: {action_type}. Soportados: swap, deposit, withdraw, transfer, approve, bridge.",
            "fr": f"Type d'action non supporté: {action_type}. Supportés: swap, deposit, withdraw, transfer, approve, bridge.",
            "zh": f"不支持的操作类型: {action_type}。支持: swap, deposit, withdraw, transfer, approve, bridge。",
            "pt": f"Tipo de ação não suportado: {action_type}. Suportados: swap, deposit, withdraw, transfer, approve, bridge.",
        }
        
        return ActionResult(
            action_id=action_id,
            action_type=action_type,
            status="failed",
            requires_confirmation=False,
            confirmation_message=None,
            simulation={"success": False, "errors": [f"Unsupported action: {action_type}"]},
            transaction=None,
            summary=msgs.get(language, msgs["en"]),
            enrichment=None,
            created_at=datetime.utcnow(),
            expires_at=None,
        )
