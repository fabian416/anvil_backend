"""
Lending Handler for Chat - Morpho vault operations.

Per CEO spec: Lending = Morpho only (top 3 vaults by APY)
Uses filters from product stack document.

Provides real-time lending vault data via Morpho GraphQL API:
- Top 3 vaults by APY (per CEO spec)
- Vault discovery on Ethereum and Base
- Whitelisted (curated) vault recommendations
- ERC-4626 deposit guidance

Note: Money Market (Aave/Compound) is handled separately.
"""

import time
import logging
from typing import Optional
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime
from uuid import UUID, uuid4

from app.domain.ports.morpho_gateway import MorphoGateway
from app.domain.ports.balance_checker import IBalanceChecker
from app.domain.ports.lending_repository import ILendingRepository
from app.domain.entities.lending.morpho_vault import MorphoVault
from app.domain.entities.lending.leverage_loop_execution import LeverageLoopExecution
from app.domain.entities.lending.lending_alert import LendingAlert
from app.application.lending.interactors.leverage_loop_interactor import (
    LeverageLoopInteractor,
    InsufficientBalanceError,
    UnsupportedAssetError,
)
from app.application.lending.commands.leverage_loop_command import (
    LeverageLoopCommand,
    LeverageLoopResult,
)

logger = logging.getLogger(__name__)


@dataclass
class LendingHandlerResult:
    """Result from lending handler."""

    content: str
    vaults: list[dict]
    chain: str
    asset: str
    best_apy: float
    latency_ms: int
    language: str = "en"
    handler: str = "lending_handler"
    pending_action: str | None = None  # For multi-turn flows (e.g., "lending_no_vaults", "lending_awaiting_asset", "lending_awaiting_chain")
    lending_info: dict | None = None  # Lending info for continuation (chain, asset, awaiting_asset, awaiting_chain)
    execute_data: dict | None = None  # Execute data for frontend transaction execution


class LendingHandler:
    """
    Handler for lending-related chat intents.
    
    Per CEO spec: Morpho only for lending, top 3 vaults by APY.
    Uses filters from product stack document.
    
    Uses MorphoGateway to fetch real vault data from
    the Morpho GraphQL API (supports Ethereum + Base).
    
    Features:
    - Top 3 vaults by APY (per CEO spec)
    - Whitelisted vault filtering
    - Multi-chain support (Ethereum, Base)
    - ERC-4626 deposit flow guidance
    """
    
    # Per CEO spec: Show top 3 vaults
    MAX_VAULTS_TO_SHOW = 3

    def __init__(
        self,
        morpho_gateway: MorphoGateway,
        balance_checker: Optional[IBalanceChecker] = None,
        leverage_loop_interactor: Optional[LeverageLoopInteractor] = None,
        lending_repository: Optional[ILendingRepository] = None,
    ):
        """
        Initialize lending handler.

        Args:
            morpho_gateway: Gateway to Morpho protocol data
            balance_checker: Optional balance checker for validation before execute_data generation
            leverage_loop_interactor: Optional interactor for leverage loop operations
            lending_repository: Optional repository for lending position persistence
        """
        self._morpho = morpho_gateway
        self._balance_checker = balance_checker
        self._leverage_loop_interactor = leverage_loop_interactor
        self._lending_repository = lending_repository
    
    async def execute(
        self,
        message: str,
        chain: str = "base",
        asset: str = "USDC",
        whitelisted_only: bool = True,
        language: str = "en",
        continuation_step: str | None = None,
        previous_lending_info: dict | None = None,
        wallet_address: str | None = None,
    ) -> LendingHandlerResult:
        """
        Handle lending intent and return vault recommendations.

        Args:
            message: User's message (for context)
            chain: Blockchain (ethereum, base)
            asset: Asset symbol (USDC, ETH, etc.)
            whitelisted_only: Only return curated vaults
            language: Response language (en, es, fr, zh, pt)
            continuation_step: If continuing a flow, which step (select_asset, select_chain, check_later)
            previous_lending_info: Previous lending info for continuation
            wallet_address: User's wallet address for balance checking (optional)

        Returns:
            LendingHandlerResult with formatted content and vault data
        """
        start_time = time.time()
        
        # Handle continuation from previous lending query (when no vaults found)
        if continuation_step and previous_lending_info:
            if continuation_step == "select_asset":
                # User selected option 1 from "no vaults" message
                # Always show asset options first
                result = self._handle_asset_selection(previous_lending_info, language)
                return result
            elif continuation_step == "select_chain":
                # User selected option 2 from "no vaults" message
                # Always show chain options first
                result = self._handle_chain_selection(previous_lending_info, language)
                return result
            elif continuation_step == "check_later":
                # User selected option 3 - check back later message
                return self._handle_check_later(language)
        
        # Handle asset/chain selection continuations (when user is selecting from options)
        # This happens when user selects an option after seeing the numbered list
        if previous_lending_info:
            if previous_lending_info.get("awaiting_asset"):
                # User is selecting an asset from the options (e.g., "1" for USDC)
                chain, asset = self._apply_asset_selection(message, previous_lending_info)
                # Continue with new asset (fall through to fetch vaults)
            elif previous_lending_info.get("awaiting_chain"):
                # User is selecting a chain from the options (e.g., "1" for Ethereum)
                chain, asset = self._apply_chain_selection(message, previous_lending_info)
                # Continue with new chain (fall through to fetch vaults)
            else:
                # Use previous info as-is (for regular continuation)
                chain = previous_lending_info.get("chain", chain)
                asset = previous_lending_info.get("asset", asset)
        else:
            # Extract chain and asset from message if not provided
            extracted_chain, extracted_asset = self._extract_params_from_message(message)
            chain = extracted_chain if chain == "base" else chain
            asset = extracted_asset if asset == "USDC" else asset
        
        # Fetch vaults from Morpho
        vaults = await self._morpho.get_vaults(
            asset=asset,
            chain=chain,
        )
        
        # Filter whitelisted if requested
        if whitelisted_only:
            vaults = [v for v in vaults if v.whitelisted]
        
        # Sort by APY (highest first)
        vaults = sorted(vaults, key=lambda v: v.apy, reverse=True)
        
        # Generate response content - TOP 3 per CEO spec with i18n
        content = self._format_vault_response(
            vaults=vaults[:self.MAX_VAULTS_TO_SHOW],
            chain=chain,
            asset=asset,
            message=message,
            language=language,
        )
        
        # Prepare vault data for response - TOP 3 per CEO spec
        vault_data = [self._vault_to_dict(v) for v in vaults[:self.MAX_VAULTS_TO_SHOW]]
        
        best_apy = vaults[0].apy if vaults else 0.0
        latency_ms = int((time.time() - start_time) * 1000)
        
        # Set pending_action if no vaults found (for multi-turn flow)
        pending_action = None
        lending_info = None
        if not vaults:
            pending_action = "lending_no_vaults"
            lending_info = {
                "chain": chain,
                "asset": asset,
            }

        # Generate execute data if vaults found and no pending action
        execute_data = None
        insufficient_balance_error = None

        if not pending_action and vaults:
            # Use best vault (highest APY) for execute data
            best_vault = vaults[0]
            default_amount = "1000"  # Default amount (can be made configurable)

            # Check balance BEFORE generating execute_data (critical for UX)
            if self._balance_checker and wallet_address:
                has_balance = await self._check_sufficient_balance(
                    wallet_address=wallet_address,
                    token_address=best_vault.asset_address,
                    required_amount=Decimal(default_amount),
                    chain=chain,
                    asset_symbol=best_vault.asset,
                )

                if not has_balance:
                    # Get current balance for error message
                    current_balance = await self._balance_checker.get_balance(
                        wallet_address=wallet_address,
                        token_address=best_vault.asset_address,
                        chain=chain,
                    )
                    insufficient_balance_error = self._format_insufficient_balance_error(
                        asset=best_vault.asset,
                        current_balance=current_balance,
                        required_amount=Decimal(default_amount),
                        language=language,
                    )
                    # Don't generate execute_data if insufficient balance
                    execute_data = None
                else:
                    # Balance is sufficient, generate execute_data
                    execute_data = self._generate_execute_data(
                        vault=best_vault,
                        amount=default_amount,
                        chain=chain,
                    )
            else:
                # No balance checker or wallet address - generate execute_data anyway
                # (Balance will be checked on frontend before transaction submission)
                execute_data = self._generate_execute_data(
                    vault=best_vault,
                    amount=default_amount,
                    chain=chain,
                )

        # Prepend insufficient balance error to content if applicable
        if insufficient_balance_error:
            content = insufficient_balance_error + "\n\n" + content

        result = LendingHandlerResult(
            content=content,
            vaults=vault_data,
            chain=chain,
            asset=asset,
            best_apy=best_apy,
            latency_ms=latency_ms,
            language=language,
            pending_action=pending_action,
            execute_data=execute_data,
        )

        # Store lending_info in result for metadata
        if lending_info:
            result.lending_info = lending_info

        return result

    def _generate_execute_data(
        self,
        vault: MorphoVault,
        amount: str = "1000",
        chain: str = "base",
    ) -> dict:
        """
        Generate execute data for Morpho vault deposit.

        Follows the same pattern as SwapHandlerV2 (lines 318-350)
        and BuyHandler (lines 726-732).

        Args:
            vault: MorphoVault entity with address and asset details
            amount: Default deposit amount in token units (e.g., "1000" for 1000 USDC)
            chain: Blockchain network (base, ethereum)

        Returns:
            Execute data dictionary for frontend transaction execution
        """
        return {
            "action_type": "deposit",
            "provider": "morpho",  # Protocol identifier
            "protocol": "morpho",
            "chain": chain,
            "vault_address": vault.address,
            "asset_address": vault.asset_address,
            "asset_symbol": vault.asset,
            "amount": amount,
            "slippage": 0.5,  # 0.5% slippage tolerance for deposits
            # Additional metadata for frontend display
            "vault_name": vault.name,
            "vault_apy": vault.apy,
            "vault_tvl": vault.total_assets,
        }

    async def get_vault_details(
        self,
        vault_address: str,
        chain: str = "ethereum",
    ) -> Optional[MorphoVault]:
        """
        Get detailed vault information.
        
        Args:
            vault_address: Vault contract address
            chain: Blockchain network
        
        Returns:
            MorphoVault if found, None otherwise
        """
        return await self._morpho.get_vault_details(
            vault_address=vault_address,
            chain=chain,
        )
    
    async def compare_yields(
        self,
        asset: str = "USDC",
        chains: Optional[list[str]] = None,
    ) -> dict:
        """
        Compare yields across chains and protocols.
        
        Args:
            asset: Asset to compare yields for
            chains: List of chains to compare (default: ethereum, base)
        
        Returns:
            Comparison data with best opportunities
        """
        if chains is None:
            chains = ["ethereum", "base"]
        
        results = await self._morpho.compare_yields(
            asset=asset,
            chains=chains,
        )
        
        return {
            "asset": asset,
            "chains": chains,
            "best_opportunity": results.get("best", {}),
            "all_opportunities": results.get("opportunities", []),
        }
    
    def _format_vault_response(
        self,
        vaults: list[MorphoVault],
        chain: str,
        asset: str,
        message: str,
        language: str = "en",
    ) -> str:
        """Format vault data as chat response with i18n support."""
        from app.application.chat.i18n import t
        
        if not vaults:
            no_vaults_msg = t("lending", "no_vaults", language, asset=asset, chain=chain.capitalize())
            
            # Numbered options for user selection with improved formatting
            options_msgs = {
                "en": {
                    "header": "What would you like to try?",
                    "options": [
                        ("💎", "Try a different asset", "USDC, USDT, DAI, ETH, WBTC"),
                        ("🌐", "Try a different chain", "Ethereum, Base, Arbitrum"),
                        ("⏰", "Check back later", "New vaults may be available soon")
                    ]
                },
                "es": {
                    "header": "¿Qué te gustaría intentar?",
                    "options": [
                        ("💎", "Probar otro activo", "USDC, USDT, DAI, ETH, WBTC"),
                        ("🌐", "Probar otra cadena", "Ethereum, Base, Arbitrum"),
                        ("⏰", "Verificar más tarde", "Puede haber nuevos vaults disponibles pronto")
                    ]
                },
                "pt": {
                    "header": "O que você gostaria de tentar?",
                    "options": [
                        ("💎", "Tentar outro ativo", "USDC, USDT, DAI, ETH, WBTC"),
                        ("🌐", "Tentar outra rede", "Ethereum, Base, Arbitrum"),
                        ("⏰", "Verificar mais tarde", "Novos vaults podem estar disponíveis em breve")
                    ]
                },
                "zh": {
                    "header": "您想尝试什么？",
                    "options": [
                        ("💎", "尝试其他资产", "USDC, USDT, DAI, ETH, WBTC"),
                        ("🌐", "尝试其他链", "Ethereum, Base, Arbitrum"),
                        ("⏰", "稍后查看", "可能很快会有新的金库")
                    ]
                },
            }
            
            options = options_msgs.get(language, options_msgs["en"])
            options_text = "\n".join([
                f"**{i}.** {emoji} **{title}**\n   {details}" 
                for i, (emoji, title, details) in enumerate(options["options"], 1)
            ])
            
            return f"""🔍 **{no_vaults_msg}**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**{options["header"]}**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{options_text}

💬 **Reply with the number (1, 2, or 3) to continue.**
"""
        
        chain_emoji = "🔵" if chain == "base" else "⟠"
        
        response = f"""{chain_emoji} **{asset} MORPHO VAULTS ON {chain.upper()}**

Top {len(vaults)} vaults by APY (Morpho Protocol):

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**TOP {len(vaults)} VAULTS** (by APY)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""
        
        for i, vault in enumerate(vaults[:self.MAX_VAULTS_TO_SHOW], 1):
            apy_pct = vault.apy * 100
            curated = "⭐" if vault.whitelisted else ""
            tvl = self._format_tvl(vault.total_assets)
            
            response += f"""**{i}. {vault.name}** {curated}
   • APY: **{apy_pct:.2f}%**
   • TVL: {tvl}
   • Address: `{vault.address[:10]}...{vault.address[-6:]}`

"""
        
        # Best recommendation
        best = vaults[0]
        best_apy = best.apy * 100
        
        response += f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**🎯 RECOMMENDATION**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Best Vault**: {best.name}
**APY**: {best_apy:.2f}%
**Risk Level**: {"Low" if best.whitelisted else "Medium"} ({"Curated" if best.whitelisted else "Not Curated"})

**How to Deposit**:
1. Approve {asset} spending for the vault
2. Call `vault.deposit(amount, receiver)`
3. Receive vault shares (ERC-4626)

**Safety Checks**:
✅ Verify vault address before depositing
✅ Start with a small test amount
✅ Ensure you have {chain.upper()} ETH for gas

Would you like me to help you deposit into **{best.name}**?
"""
        
        return response
    
    def _vault_to_dict(self, vault: MorphoVault) -> dict:
        """Convert vault to dictionary for API response."""
        return {
            "address": vault.address,
            "name": vault.name,
            "symbol": vault.symbol,
            "asset": vault.asset,
            "asset_address": vault.asset_address,
            "apy": vault.apy,
            "apy_percentage": vault.apy * 100,
            "total_assets": vault.total_assets,
            "whitelisted": vault.whitelisted,
            "chain": vault.chain,
            "risk_tier": vault.risk_tier,
        }
    
    def _format_tvl(self, total_assets: float) -> str:
        """Format total assets as human-readable TVL."""
        if total_assets >= 1_000_000_000:
            return f"${total_assets / 1_000_000_000:.2f}B"
        elif total_assets >= 1_000_000:
            return f"${total_assets / 1_000_000:.2f}M"
        elif total_assets >= 1_000:
            return f"${total_assets / 1_000:.2f}K"
        else:
            return f"${total_assets:.2f}"
    
    def _extract_params_from_message(self, message: str) -> tuple[str, str]:
        """
        Extract chain and asset from user message.
        
        Returns:
            Tuple of (chain, asset)
        """
        message_lower = message.lower()
        
        # Detect chain
        if "base" in message_lower:
            chain = "base"
        elif "ethereum" in message_lower or "eth" in message_lower or "mainnet" in message_lower:
            chain = "ethereum"
        else:
            chain = "base"  # Default to Base (CEO preference)
        
        # Detect asset
        if "eth" in message_lower and "ether" in message_lower:
            asset = "ETH"
        elif "usdt" in message_lower:
            asset = "USDT"
        elif "dai" in message_lower:
            asset = "DAI"
        else:
            asset = "USDC"  # Default to USDC
        
        return chain, asset
    
    def _handle_asset_selection(self, previous_info: dict, language: str) -> LendingHandlerResult:
        """Handle asset selection after user chose option 1."""
        asset_options = {
            "en": {
                "header": "Select an asset to search for vaults:",
                "options": [
                    ("USDC", "USD Coin - Stablecoin"),
                    ("USDT", "Tether - Stablecoin"),
                    ("DAI", "Dai - Decentralized stablecoin"),
                    ("ETH", "Ethereum - Native token"),
                    ("WBTC", "Wrapped Bitcoin - Bitcoin on Ethereum")
                ]
            },
            "es": {
                "header": "Selecciona un activo para buscar vaults:",
                "options": [
                    ("USDC", "USD Coin - Stablecoin"),
                    ("USDT", "Tether - Stablecoin"),
                    ("DAI", "Dai - Stablecoin descentralizado"),
                    ("ETH", "Ethereum - Token nativo"),
                    ("WBTC", "Wrapped Bitcoin - Bitcoin en Ethereum")
                ]
            },
            "pt": {
                "header": "Selecione um ativo para buscar vaults:",
                "options": [
                    ("USDC", "USD Coin - Stablecoin"),
                    ("USDT", "Tether - Stablecoin"),
                    ("DAI", "Dai - Stablecoin descentralizado"),
                    ("ETH", "Ethereum - Token nativo"),
                    ("WBTC", "Wrapped Bitcoin - Bitcoin no Ethereum")
                ]
            },
            "zh": {
                "header": "选择资产以搜索金库:",
                "options": [
                    ("USDC", "USD Coin - 稳定币"),
                    ("USDT", "Tether - 稳定币"),
                    ("DAI", "Dai - 去中心化稳定币"),
                    ("ETH", "以太坊 - 原生代币"),
                    ("WBTC", "Wrapped Bitcoin - 以太坊上的比特币")
                ]
            },
        }
        
        options = asset_options.get(language, asset_options["en"])
        options_text = "\n".join([
            f"**{i}.** 💰 **{symbol}** - {description}" 
            for i, (symbol, description) in enumerate(options["options"], 1)
        ])
        
        content = f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**{options["header"]}**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{options_text}

💬 **Reply with the number (1-5) or type the asset name to continue.**
"""
        
        # Mark that we're awaiting asset selection
        lending_info = {
            "chain": previous_info.get("chain", "base"),
            "asset": previous_info.get("asset", "USDC"),
            "awaiting_asset": True,
        }
        
        return LendingHandlerResult(
            content=content,
            vaults=[],
            chain=previous_info.get("chain", "base"),
            asset=previous_info.get("asset", "USDC"),
            best_apy=0.0,
            latency_ms=0,
            language=language,
            pending_action="lending_awaiting_asset",
        )
    
    def _apply_asset_selection(self, message: str, previous_info: dict) -> tuple[str, str]:
        """Apply user's asset selection (number or name)."""
        import re
        message_upper = message.upper().strip()
        
        # Check if user selected a numbered option (1-5)
        number_match = re.search(r"^(\d+)", message)
        if number_match:
            option_num = int(number_match.group(1))
            assets = ["USDC", "USDT", "DAI", "ETH", "WBTC"]
            if 1 <= option_num <= len(assets):
                return previous_info.get("chain", "base"), assets[option_num - 1]
        
        # Check if message contains asset name
        assets = ["USDC", "USDT", "DAI", "ETH", "WBTC", "WETH", "BTC"]
        for asset in assets:
            if asset in message_upper:
                return previous_info.get("chain", "base"), asset
        
        # Default to USDC
        return previous_info.get("chain", "base"), "USDC"
    
    def _handle_chain_selection(self, previous_info: dict, language: str) -> LendingHandlerResult:
        """Handle chain selection after user chose option 2."""
        chain_options = {
            "en": {
                "header": "Select a blockchain to search for vaults:",
                "options": [
                    ("⟠", "Ethereum", "Mainnet - Largest DeFi ecosystem"),
                    ("🔵", "Base", "Layer 2 - Coinbase's L2 network"),
                    ("🔷", "Arbitrum", "Layer 2 - High-performance scaling solution")
                ]
            },
            "es": {
                "header": "Selecciona una cadena para buscar vaults:",
                "options": [
                    ("⟠", "Ethereum", "Mainnet - Ecosistema DeFi más grande"),
                    ("🔵", "Base", "Layer 2 - Red L2 de Coinbase"),
                    ("🔷", "Arbitrum", "Layer 2 - Solución de escalado de alto rendimiento")
                ]
            },
            "pt": {
                "header": "Selecione uma rede para buscar vaults:",
                "options": [
                    ("⟠", "Ethereum", "Mainnet - Maior ecossistema DeFi"),
                    ("🔵", "Base", "Layer 2 - Rede L2 da Coinbase"),
                    ("🔷", "Arbitrum", "Layer 2 - Solução de escalonamento de alto desempenho")
                ]
            },
            "zh": {
                "header": "选择链以搜索金库:",
                "options": [
                    ("⟠", "Ethereum", "主网 - 最大的 DeFi 生态系统"),
                    ("🔵", "Base", "Layer 2 - Coinbase 的 L2 网络"),
                    ("🔷", "Arbitrum", "Layer 2 - 高性能扩展解决方案")
                ]
            },
        }
        
        options = chain_options.get(language, chain_options["en"])
        options_text = "\n".join([
            f"**{i}.** {emoji} **{chain}** - {description}" 
            for i, (emoji, chain, description) in enumerate(options["options"], 1)
        ])
        
        content = f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**{options["header"]}**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{options_text}

💬 **Reply with the number (1-3) or type the chain name to continue.**
"""
        
        # Mark that we're awaiting chain selection
        lending_info = {
            "chain": previous_info.get("chain", "base"),
            "asset": previous_info.get("asset", "USDC"),
            "awaiting_chain": True,
        }
        
        return LendingHandlerResult(
            content=content,
            vaults=[],
            chain=previous_info.get("chain", "base"),
            asset=previous_info.get("asset", "USDC"),
            best_apy=0.0,
            latency_ms=0,
            language=language,
            pending_action="lending_awaiting_chain",
        )
    
    def _apply_chain_selection(self, message: str, previous_info: dict) -> tuple[str, str]:
        """Apply user's chain selection (number or name)."""
        import re
        message_lower = message.lower().strip()
        
        # Check if user selected a numbered option (1-3)
        number_match = re.search(r"^(\d+)", message_lower)
        if number_match:
            option_num = int(number_match.group(1))
            chains = ["ethereum", "base", "arbitrum"]
            if 1 <= option_num <= len(chains):
                return chains[option_num - 1], previous_info.get("asset", "USDC")
        
        # Check if message contains chain name
        if "ethereum" in message_lower or "eth" in message_lower and "mainnet" in message_lower:
            return "ethereum", previous_info.get("asset", "USDC")
        elif "base" in message_lower:
            return "base", previous_info.get("asset", "USDC")
        elif "arbitrum" in message_lower or "arb" in message_lower:
            return "arbitrum", previous_info.get("asset", "USDC")
        
        # Default to base
        return "base", previous_info.get("asset", "USDC")
    
    def _handle_check_later(self, language: str) -> LendingHandlerResult:
        """Handle check back later message after user chose option 3."""
        messages = {
            "en": """✅ **Noted!**

I'll keep checking for new vaults. Here are some suggestions:

💡 **Tips:**
• Check back in a few hours - new vaults are added regularly
• Try different assets (USDC, USDT, DAI often have more options)
• Explore other chains (Ethereum, Base, Arbitrum)

🔔 **Want alerts?** Sign up to get notified when new vaults become available!""",
            "es": """✅ **¡Anotado!**

Seguiré verificando nuevos vaults. Aquí tienes algunas sugerencias:

💡 **Consejos:**
• Vuelve a verificar en unas horas - se agregan nuevos vaults regularmente
• Prueba diferentes activos (USDC, USDT, DAI suelen tener más opciones)
• Explora otras cadenas (Ethereum, Base, Arbitrum)

🔔 **¿Quieres alertas?** ¡Regístrate para recibir notificaciones cuando haya nuevos vaults disponibles!""",
            "pt": """✅ **Anotado!**

Continuarei verificando novos vaults. Aqui estão algumas sugestões:

💡 **Dicas:**
• Verifique novamente em algumas horas - novos vaults são adicionados regularmente
• Tente diferentes ativos (USDC, USDT, DAI geralmente têm mais opções)
• Explore outras redes (Ethereum, Base, Arbitrum)

🔔 **Quer alertas?** Cadastre-se para ser notificado quando novos vaults estiverem disponíveis!""",
            "zh": """✅ **已记录！**

我会继续检查新的金库。以下是一些建议：

💡 **提示:**
• 几小时后回来查看 - 新金库会定期添加
• 尝试不同的资产（USDC、USDT、DAI 通常有更多选项）
• 探索其他链（Ethereum、Base、Arbitrum）

🔔 **想要提醒？** 注册以在新金库可用时收到通知！""",
        }
        
        return LendingHandlerResult(
            content=messages.get(language, messages["en"]),
            vaults=[],
            chain="base",
            asset="ETH",
            best_apy=0.0,
            latency_ms=0,
            language=language,
            pending_action=None,
        )

    async def _check_sufficient_balance(
        self,
        wallet_address: str,
        token_address: str,
        required_amount: Decimal,
        chain: str,
        asset_symbol: str,
    ) -> bool:
        """
        Check if wallet has sufficient balance for deposit.

        Args:
            wallet_address: User's wallet address
            token_address: Token contract address
            required_amount: Required amount in token units
            chain: Blockchain name
            asset_symbol: Token symbol (for logging)

        Returns:
            True if sufficient balance exists, False otherwise
        """
        import logging

        logger = logging.getLogger(__name__)

        if not self._balance_checker:
            # No balance checker configured - optimistically assume balance exists
            logger.warning(
                "BalanceChecker not configured - skipping balance validation"
            )
            return True

        try:
            has_balance = await self._balance_checker.check_balance(
                wallet_address=wallet_address,
                token_address=token_address,
                required_amount=required_amount,
                chain=chain,
            )

            if has_balance:
                logger.info(
                    f"✅ Balance check passed for {wallet_address}: "
                    f"has sufficient {asset_symbol} on {chain}"
                )
            else:
                logger.warning(
                    f"⚠️ Insufficient balance for {wallet_address}: "
                    f"needs {required_amount} {asset_symbol} on {chain}"
                )

            return has_balance

        except Exception as e:
            logger.error(
                f"❌ Balance check failed for {wallet_address}: {type(e).__name__}: {e}"
            )
            # Conservative approach: return False if check fails
            return False

    def _format_insufficient_balance_error(
        self,
        asset: str,
        current_balance: Decimal,
        required_amount: Decimal,
        language: str,
    ) -> str:
        """
        Format insufficient balance error message with i18n support.

        Args:
            asset: Token symbol (USDC, ETH, etc.)
            current_balance: User's current balance
            required_amount: Required amount for transaction
            language: Response language (en, es, pt, zh)

        Returns:
            Formatted error message
        """
        error_templates = {
            "en": {
                "header": "Insufficient Balance",
                "body": (
                    f"You need **{required_amount} {asset}** to deposit, "
                    f"but you only have **{current_balance} {asset}**."
                ),
                "suggestion": "Please add more funds to your wallet or try a smaller amount.",
            },
            "es": {
                "header": "Saldo Insuficiente",
                "body": (
                    f"Necesitas **{required_amount} {asset}** para depositar, "
                    f"pero solo tienes **{current_balance} {asset}**."
                ),
                "suggestion": "Agrega más fondos a tu billetera o intenta con una cantidad menor.",
            },
            "pt": {
                "header": "Saldo Insuficiente",
                "body": (
                    f"Você precisa de **{required_amount} {asset}** para depositar, "
                    f"mas você tem apenas **{current_balance} {asset}**."
                ),
                "suggestion": "Adicione mais fundos à sua carteira ou tente um valor menor.",
            },
            "zh": {
                "header": "余额不足",
                "body": (
                    f"您需要 **{required_amount} {asset}** 才能存款，"
                    f"但您只有 **{current_balance} {asset}**。"
                ),
                "suggestion": "请向您的钱包添加更多资金或尝试较小的金额。",
            },
        }

        template = error_templates.get(language, error_templates["en"])

        return f"""❌ **{template["header"]}**

{template["body"]}

💡 **{template["suggestion"]}**
"""

    async def handle_leverage_loop(
        self,
        user_id: UUID,
        wallet_address: str,
        asset: str,
        target_leverage: Decimal,
        chain: str = "ethereum",
        min_health_factor: Optional[Decimal] = None,
        language: str = "en",
    ) -> dict:
        """
        Handle LENDING_LOOP shortcut - multi-step leverage workflow.

        CRITICAL: This returns ONLY the first step's execute_data.
        User must approve each step individually (NO batch processing).

        Args:
            user_id: User's unique identifier
            wallet_address: User's wallet address
            asset: Asset to leverage (ETH, WETH, wstETH)
            target_leverage: Target leverage multiplier (2.0-4.0)
            chain: Blockchain network (ethereum, base, etc.)
            min_health_factor: Minimum acceptable health factor (default: 1.5)
            language: Response language (en, es, pt, zh)

        Returns:
            Response dict with message, execute_data, and metadata
        """
        if not self._leverage_loop_interactor:
            return self._format_error(
                message=self._translate("leverage_loop_unavailable", language),
                language=language,
            )

        if not self._balance_checker:
            return self._format_error(
                message=self._translate("balance_checker_unavailable", language),
                language=language,
            )

        try:
            # 1. Get initial balance
            token_address = self._get_token_address(asset, chain)
            balance = await self._balance_checker.get_balance(
                wallet_address=wallet_address,
                token_address=token_address,
                chain=chain
            )

            if balance <= 0:
                return self._format_error(
                    message=self._translate("insufficient_balance", language).format(
                        asset=asset
                    ),
                    language=language
                )

            # 2. Get user preferences for safety thresholds
            if self._lending_repository:
                preferences = await self._lending_repository.get_user_preferences(user_id)
                if preferences:
                    min_hf = preferences.min_health_factor
                    max_leverage = preferences.max_leverage

                    # Check if user's target exceeds their max
                    if target_leverage > max_leverage:
                        return self._format_warning(
                            message=self._translate("leverage_exceeds_preference", language).format(
                                target=target_leverage,
                                max=max_leverage
                            ),
                            language=language
                        )
                else:
                    min_hf = min_health_factor or Decimal("1.5")
            else:
                min_hf = min_health_factor or Decimal("1.5")

            # 3. Create leverage loop command
            command = LeverageLoopCommand(
                user_id=user_id,
                asset=asset,
                initial_amount=balance,
                target_leverage=target_leverage,
                protocol="aave",
                chain=chain,
                min_health_factor=min_hf
            )

            # 4. Calculate loop steps
            result = await self._leverage_loop_interactor.calculate_loop_steps(
                command=command,
                wallet_address=wallet_address,
            )

            # 5. Save loop execution state
            if self._lending_repository:
                await self._lending_repository.save_loop_execution(
                    LeverageLoopExecution(
                        id=result.loop_id,
                        user_id=user_id,
                        protocol="aave",
                        chain=chain,
                        asset_address=token_address,
                        asset_symbol=asset,
                        initial_amount=balance,
                        target_leverage=target_leverage,
                        actual_leverage=result.actual_leverage,
                        total_steps=result.total_steps,
                        current_step=0,
                        steps_completed=[],
                        status="pending",
                        final_health_factor=result.final_health_factor,
                        final_collateral_usd=None,
                        final_debt_usd=None,
                        total_gas_used=None,
                        total_cost_usd=result.total_cost_usd,
                        error_message=None,
                        metadata=result.to_dict(),
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                        completed_at=None,
                    )
                )

            # 6. Format response with execution plan
            response_message = self._format_leverage_loop_plan(
                result=result,
                asset=asset,
                language=language
            )

            # 7. Return ONLY first step's execute_data
            # User must approve each step individually
            return {
                "message": response_message,
                "execute_data": result.steps[0].execute_data if result.steps else None,
                "metadata": {
                    "requires_confirmation": True,
                    "loop_id": str(result.loop_id),
                    "total_steps": result.total_steps,
                    "current_step": 1,
                    "warnings": result.warnings,
                    "action_type": "leverage_loop_start"
                }
            }

        except InsufficientBalanceError as e:
            return self._format_error(
                message=self._translate("insufficient_balance", language).format(
                    asset=asset
                ),
                language=language
            )
        except UnsupportedAssetError as e:
            return self._format_error(
                message=self._translate("unsupported_leverage_asset", language).format(
                    asset=asset
                ),
                language=language
            )
        except ValueError as e:
            if "leverage must be between" in str(e).lower():
                return self._format_error(
                    message=self._translate("leverage_too_high", language).format(
                        max="4.0"
                    ),
                    language=language
                )
            raise

    async def continue_leverage_loop(
        self,
        user_id: UUID,
        wallet_address: str,
        loop_id: UUID,
        completed_tx_hash: str,
        language: str = "en",
    ) -> dict:
        """
        Continue leverage loop after user completes a step.

        Called by /execute endpoint after user approves and signs a step.

        Args:
            user_id: User's unique identifier
            wallet_address: User's wallet address
            loop_id: Leverage loop execution ID
            completed_tx_hash: Transaction hash of completed step
            language: Response language (en, es, pt, zh)

        Returns:
            Response dict with next step or completion message
        """
        if not self._lending_repository:
            return self._format_error(
                message=self._translate("repository_unavailable", language),
                language=language
            )

        # 1. Load loop execution state
        loop_execution = await self._lending_repository.get_loop_execution(loop_id)

        if not loop_execution:
            return self._format_error(
                message=self._translate("loop_not_found", language),
                language=language
            )

        # 2. Update loop state with completed step
        updated_steps = loop_execution.steps_completed + [completed_tx_hash]
        current_step = loop_execution.current_step + 1
        status = "completed" if current_step >= loop_execution.total_steps else "in_progress"

        # Create updated execution
        updated_execution = LeverageLoopExecution(
            id=loop_execution.id,
            user_id=loop_execution.user_id,
            protocol=loop_execution.protocol,
            chain=loop_execution.chain,
            asset_address=loop_execution.asset_address,
            asset_symbol=loop_execution.asset_symbol,
            initial_amount=loop_execution.initial_amount,
            target_leverage=loop_execution.target_leverage,
            actual_leverage=loop_execution.actual_leverage,
            total_steps=loop_execution.total_steps,
            current_step=current_step,
            steps_completed=updated_steps,
            status=status,
            final_health_factor=loop_execution.final_health_factor,
            final_collateral_usd=loop_execution.final_collateral_usd,
            final_debt_usd=loop_execution.final_debt_usd,
            total_gas_used=loop_execution.total_gas_used,
            total_cost_usd=loop_execution.total_cost_usd,
            error_message=None,
            metadata=loop_execution.metadata,
            created_at=loop_execution.created_at,
            updated_at=datetime.utcnow(),
            completed_at=datetime.utcnow() if status == "completed" else None,
        )

        await self._lending_repository.update_loop_execution(updated_execution)

        # 3. Check if loop is complete
        if status == "completed":
            # Create completion alert
            if self._lending_repository:
                await self._lending_repository.create_alert(
                    LendingAlert(
                        id=uuid4(),
                        user_id=user_id,
                        alert_type="loop_completed",
                        severity="info",
                        title=self._translate("loop_completed_title", language),
                        message=self._translate("loop_completed_message", language).format(
                            leverage=loop_execution.actual_leverage
                        ),
                        health_factor=loop_execution.final_health_factor,
                        threshold_value=None,
                        position_id=None,
                        asset_symbol=loop_execution.asset_symbol,
                        metadata=None,
                        is_read=False,
                        created_at=datetime.utcnow(),
                        read_at=None,
                    )
                )

            return {
                "message": self._format_loop_completion(updated_execution, language),
                "execute_data": None,
                "metadata": {
                    "loop_completed": True,
                    "final_leverage": str(updated_execution.actual_leverage),
                    "final_health_factor": str(updated_execution.final_health_factor)
                }
            }

        # 4. Recalculate health factor with latest data (safety check)
        # Get current HF from the loop execution metadata
        result_dict = loop_execution.metadata
        if result_dict and "steps" in result_dict:
            steps = result_dict["steps"]
            if current_step < len(steps):
                next_step_data = steps[current_step]

                # Check if HF is still safe
                health_factor_after = Decimal(next_step_data.get("health_factor_after", "1.5"))

                if health_factor_after < Decimal("1.2"):
                    # Mark loop as failed
                    failed_execution = LeverageLoopExecution(
                        id=updated_execution.id,
                        user_id=updated_execution.user_id,
                        protocol=updated_execution.protocol,
                        chain=updated_execution.chain,
                        asset_address=updated_execution.asset_address,
                        asset_symbol=updated_execution.asset_symbol,
                        initial_amount=updated_execution.initial_amount,
                        target_leverage=updated_execution.target_leverage,
                        actual_leverage=updated_execution.actual_leverage,
                        total_steps=updated_execution.total_steps,
                        current_step=updated_execution.current_step,
                        steps_completed=updated_execution.steps_completed,
                        status="failed",
                        final_health_factor=updated_execution.final_health_factor,
                        final_collateral_usd=updated_execution.final_collateral_usd,
                        final_debt_usd=updated_execution.final_debt_usd,
                        total_gas_used=updated_execution.total_gas_used,
                        total_cost_usd=updated_execution.total_cost_usd,
                        error_message="Health factor dropped below safety threshold",
                        metadata=updated_execution.metadata,
                        created_at=updated_execution.created_at,
                        updated_at=datetime.utcnow(),
                        completed_at=None,
                    )

                    await self._lending_repository.update_loop_execution(failed_execution)

                    # Create critical alert
                    if self._lending_repository:
                        await self._lending_repository.create_alert(
                            LendingAlert(
                                id=uuid4(),
                                user_id=user_id,
                                alert_type="loop_failed",
                                severity="critical",
                                title=self._translate("loop_failed_title", language),
                                message=self._translate("loop_failed_hf", language),
                                health_factor=health_factor_after,
                                threshold_value=Decimal("1.2"),
                                position_id=None,
                                asset_symbol=updated_execution.asset_symbol,
                                metadata=None,
                                is_read=False,
                                created_at=datetime.utcnow(),
                                read_at=None,
                            )
                        )

                    return self._format_error(
                        message=self._translate("loop_hf_unsafe", language).format(
                            hf=health_factor_after
                        ),
                        language=language
                    )

                # 5. Get next step's execute_data
                return {
                    "message": self._format_next_step(
                        execution=updated_execution,
                        next_step_data=next_step_data,
                        language=language
                    ),
                    "execute_data": next_step_data.get("execute_data"),
                    "metadata": {
                        "requires_confirmation": True,
                        "loop_id": str(loop_id),
                        "total_steps": updated_execution.total_steps,
                        "current_step": current_step + 1,
                        "action_type": "leverage_loop_continue"
                    }
                }

        # Fallback if metadata is missing
        return self._format_error(
            message=self._translate("loop_metadata_missing", language),
            language=language
        )

    def _get_token_address(self, asset: str, chain: str) -> str:
        """Get token contract address for asset."""
        TOKEN_ADDRESSES = {
            "ethereum": {
                "ETH": "native",
                "WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
                "wstETH": "0x7f39C581F595B53c5cb19bD0b3f8dA6c935E2Ca0",
            },
            "base": {
                "ETH": "native",
                "WETH": "0x4200000000000000000000000000000000000006",
            },
        }
        return TOKEN_ADDRESSES.get(chain.lower(), {}).get(asset.upper(), "native")

    def _format_leverage_loop_plan(
        self,
        result: LeverageLoopResult,
        asset: str,
        language: str,
    ) -> str:
        """Format leverage loop execution plan for user."""
        translations = {
            "en": {
                "title": "Leverage Loop Execution Plan",
                "leverage": "Target Leverage",
                "actual": "Actual Leverage",
                "steps": "Total Steps",
                "hf": "Final Health Factor",
                "apy": "Estimated Net APY",
                "cost": "Estimated Cost",
                "warning": "WARNING",
                "signatures": "This will require {} separate wallet signatures",
                "risk": "Leverage trading is high risk - you could be liquidated"
            },
            "es": {
                "title": "Plan de Ejecución de Bucle de Apalancamiento",
                "leverage": "Apalancamiento Objetivo",
                "actual": "Apalancamiento Real",
                "steps": "Pasos Totales",
                "hf": "Factor de Salud Final",
                "apy": "APY Neto Estimado",
                "cost": "Costo Estimado",
                "warning": "ADVERTENCIA",
                "signatures": "Esto requerirá {} firmas de billetera separadas",
                "risk": "El trading con apalancamiento es de alto riesgo - podrías ser liquidado"
            },
            "pt": {
                "title": "Plano de Execução de Loop de Alavancagem",
                "leverage": "Alavancagem Alvo",
                "actual": "Alavancagem Real",
                "steps": "Passos Totais",
                "hf": "Fator de Saúde Final",
                "apy": "APY Líquido Estimado",
                "cost": "Custo Estimado",
                "warning": "AVISO",
                "signatures": "Isso exigirá {} assinaturas de carteira separadas",
                "risk": "Trading com alavancagem é de alto risco - você pode ser liquidado"
            },
            "zh": {
                "title": "杠杆循环执行计划",
                "leverage": "目标杠杆",
                "actual": "实际杠杆",
                "steps": "总步骤",
                "hf": "最终健康因子",
                "apy": "预估净APY",
                "cost": "预估成本",
                "warning": "警告",
                "signatures": "这将需要{}个单独的钱包签名",
                "risk": "杠杆交易是高风险的 - 您可能会被清算",
                "continue": "回复'是'以开始步骤1，或'取消'以中止"
            },
        }

        t = translations.get(language, translations["en"])

        return f"""
🔄 **{t['title']}**

{t['leverage']}: {result.target_leverage}x
{t['actual']}: {result.actual_leverage:.2f}x
{t['steps']}: {result.total_steps}
{t['hf']}: {result.final_health_factor:.2f}
{t['apy']}: {result.estimated_apy:.2f}%
{t['cost']}: ${result.total_cost_usd:.2f}

⚠️ **{t['warning']}**:
- {t['signatures'].format(result.total_steps)}
- {t['risk']}

💬 {t['continue']}
"""

    def _format_loop_completion(
        self,
        execution: LeverageLoopExecution,
        language: str,
    ) -> str:
        """Format loop completion message."""
        translations = {
            "en": "Loop completed! Achieved {leverage:.2f}x leverage with final health factor {hf:.2f}",
            "es": "¡Bucle completado! Se logró apalancamiento de {leverage:.2f}x con factor de salud final {hf:.2f}",
            "pt": "Loop concluído! Alavancagem de {leverage:.2f}x alcançada com fator de saúde final {hf:.2f}",
            "zh": "循环完成！达到{leverage:.2f}x杠杆，最终健康因子{hf:.2f}",
        }

        template = translations.get(language, translations["en"])
        return template.format(
            leverage=execution.actual_leverage or 0,
            hf=execution.final_health_factor or 0
        )

    def _format_next_step(
        self,
        execution: LeverageLoopExecution,
        next_step_data: dict,
        language: str,
    ) -> str:
        """Format next step message."""
        action = next_step_data.get("action", "unknown")
        step_num = next_step_data.get("step_number", 0)

        translations = {
            "en": f"Step {step_num}/{execution.total_steps}: {action} - Ready to continue?",
            "es": f"Paso {step_num}/{execution.total_steps}: {action} - ¿Listo para continuar?",
            "pt": f"Passo {step_num}/{execution.total_steps}: {action} - Pronto para continuar?",
            "zh": f"步骤 {step_num}/{execution.total_steps}: {action} - 准备继续？",
        }

        return translations.get(language, translations["en"])

    def _translate(self, key: str, language: str, **kwargs) -> str:
        """Translate a message key to the specified language."""
        # Placeholder translations - should be moved to lending_morpho.json
        translations = {
            "leverage_loop_unavailable": {
                "en": "Leverage loop feature is not available",
                "es": "La función de bucle de apalancamiento no está disponible",
                "pt": "Recurso de loop de alavancagem não disponível",
                "zh": "杠杆循环功能不可用",
            },
            "insufficient_balance": {
                "en": "Insufficient {asset} balance",
                "es": "Saldo de {asset} insuficiente",
                "pt": "Saldo de {asset} insuficiente",
                "zh": "{asset} 余额不足",
            },
            "unsupported_leverage_asset": {
                "en": "Asset {asset} is not supported for leverage loops",
                "es": "El activo {asset} no está soportado para bucles de apalancamiento",
                "pt": "Ativo {asset} não é suportado para loops de alavancagem",
                "zh": "资产 {asset} 不支持杠杆循环",
            },
            "leverage_too_high": {
                "en": "Leverage must be between 2.0x and {max}x",
                "es": "El apalancamiento debe estar entre 2.0x y {max}x",
                "pt": "Alavancagem deve estar entre 2.0x e {max}x",
                "zh": "杠杆必须在 2.0x 和 {max}x 之间",
            },
            "loop_not_found": {
                "en": "Leverage loop not found",
                "es": "Bucle de apalancamiento no encontrado",
                "pt": "Loop de alavancagem não encontrado",
                "zh": "未找到杠杆循环",
            },
            "loop_completed_title": {
                "en": "Leverage Loop Completed",
                "es": "Bucle de Apalancamiento Completado",
                "pt": "Loop de Alavancagem Concluído",
                "zh": "杠杆循环完成",
            },
            "loop_completed_message": {
                "en": "Successfully completed leverage loop with {leverage}x leverage",
                "es": "Bucle de apalancamiento completado exitosamente con {leverage}x apalancamiento",
                "pt": "Loop de alavancagem concluído com sucesso com {leverage}x alavancagem",
                "zh": "成功完成 {leverage}x 杠杆循环",
            },
            "loop_failed_title": {
                "en": "Leverage Loop Failed",
                "es": "Bucle de Apalancamiento Falló",
                "pt": "Loop de Alavancagem Falhou",
                "zh": "杠杆循环失败",
            },
            "loop_failed_hf": {
                "en": "Loop stopped due to unsafe health factor",
                "es": "Bucle detenido debido a factor de salud inseguro",
                "pt": "Loop parado devido a fator de saúde inseguro",
                "zh": "由于不安全的健康因子，循环已停止",
            },
            "loop_hf_unsafe": {
                "en": "Health factor {hf} is too low to continue safely",
                "es": "Factor de salud {hf} es demasiado bajo para continuar de manera segura",
                "pt": "Fator de saúde {hf} está muito baixo para continuar com segurança",
                "zh": "健康因子 {hf} 太低，无法安全继续",
            },
        }

        template_dict = translations.get(key, {})
        template = template_dict.get(language, template_dict.get("en", key))
        return template.format(**kwargs) if kwargs else template

    def _format_error(self, message: str, language: str) -> dict:
        """Format error response."""
        return {
            "message": f"❌ {message}",
            "execute_data": None,
            "metadata": {"error": True}
        }

    def _format_warning(self, message: str, language: str) -> dict:
        """Format warning response."""
        return {
            "message": f"⚠️ {message}",
            "execute_data": None,
            "metadata": {"warning": True}
        }
