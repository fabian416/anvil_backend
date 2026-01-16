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
from typing import Optional
from dataclasses import dataclass

from app.domain.ports.morpho_gateway import MorphoGateway
from app.domain.entities.lending.morpho_vault import MorphoVault


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
    
    def __init__(self, morpho_gateway: MorphoGateway):
        """
        Initialize lending handler.
        
        Args:
            morpho_gateway: Gateway to Morpho protocol data
        """
        self._morpho = morpho_gateway
    
    async def execute(
        self,
        message: str,
        chain: str = "base",
        asset: str = "USDC",
        whitelisted_only: bool = True,
        language: str = "en",
        continuation_step: str | None = None,
        previous_lending_info: dict | None = None,
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
        if not pending_action and vaults:
            # Use best vault (highest APY) for execute data
            best_vault = vaults[0]
            execute_data = self._generate_execute_data(
                vault=best_vault,
                amount="1000",  # Default amount (can be made configurable)
                chain=chain,
            )

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
