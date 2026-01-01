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
    handler: str = "lending_handler"


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
    ) -> LendingHandlerResult:
        """
        Handle lending intent and return vault recommendations.
        
        Args:
            message: User's message (for context)
            chain: Blockchain (ethereum, base)
            asset: Asset symbol (USDC, ETH, etc.)
            whitelisted_only: Only return curated vaults
        
        Returns:
            LendingHandlerResult with formatted content and vault data
        """
        start_time = time.time()
        
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
        
        # Generate response content - TOP 3 per CEO spec
        content = self._format_vault_response(
            vaults=vaults[:self.MAX_VAULTS_TO_SHOW],
            chain=chain,
            asset=asset,
            message=message,
        )
        
        # Prepare vault data for response - TOP 3 per CEO spec
        vault_data = [self._vault_to_dict(v) for v in vaults[:self.MAX_VAULTS_TO_SHOW]]
        
        best_apy = vaults[0].apy if vaults else 0.0
        latency_ms = int((time.time() - start_time) * 1000)
        
        return LendingHandlerResult(
            content=content,
            vaults=vault_data,
            chain=chain,
            asset=asset,
            best_apy=best_apy,
            latency_ms=latency_ms,
        )
    
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
    ) -> str:
        """Format vault data as chat response."""
        if not vaults:
            return f"""🔍 **No {asset} Vaults Found on {chain.capitalize()}**

I couldn't find any {asset} lending vaults on {chain.capitalize()}.

**Try:**
- Different asset (ETH, USDT, DAI)
- Different chain (ethereum, base)
- Checking back later

Would you like me to search on a different chain?"""
        
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
