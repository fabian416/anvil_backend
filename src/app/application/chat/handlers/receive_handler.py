"""
Receive Handler for Chat - Wallet address and QR code operations.

Provides wallet address information for receiving funds:
- User's wallet address from Privy/WalletRepository
- ENS handle (if registered)
- Multi-chain support
- QR code generation (placeholder for frontend)
"""

import time
from dataclasses import dataclass
from typing import Optional

from app.domain.ports.wallet.wallet_repository import WalletRepository
from app.domain.enums.wallet_provider import WalletProvider
from app.domain.value_objects.user_id import UserId


@dataclass
class ReceiveHandlerResult:
    """Result from receive handler."""

    content: str
    wallet_address: str
    ens_handle: Optional[str]
    supported_networks: list[str]
    chain: str
    latency_ms: int
    language: str = "en"
    handler: str = "receive_handler"


class ReceiveHandler:
    """
    Handler for receive funds chat intents.

    Uses WalletRepository to fetch user's wallet address
    from the database (synced from Privy).

    Features:
    - Wallet address retrieval
    - ENS handle display (if registered)
    - Multi-chain network support display
    - Copy-friendly formatting
    """

    # Supported networks for receiving
    SUPPORTED_NETWORKS = [
        {"name": "Ethereum", "symbol": "ETH", "tokens": "ETH, ERC-20 tokens"},
        {"name": "Base", "symbol": "ETH", "tokens": "ETH, USDC, etc."},
        {"name": "Arbitrum", "symbol": "ETH", "tokens": "ETH, ARB, etc."},
        {"name": "Polygon", "symbol": "MATIC", "tokens": "MATIC, etc."},
        {"name": "Optimism", "symbol": "ETH", "tokens": "ETH, OP, etc."},
    ]

    def __init__(self, wallet_repository: WalletRepository):
        """
        Initialize receive handler.

        Args:
            wallet_repository: Repository for wallet data
        """
        self._wallet_repo = wallet_repository

    async def get_receive_info(
        self,
        user_id: int,
        chain: str = "base",
    ) -> ReceiveHandlerResult:
        """
        Get receive information for a user.

        Args:
            user_id: User's database ID
            chain: Preferred chain (for display purposes)

        Returns:
            ReceiveHandlerResult with wallet address and formatted content
        """
        start_time = time.time()

        try:
            # Get user's wallets.
            # Priority: Ethereum/EVM wallets first (not Bitcoin), then PRIVY provider.
            wallets = await self._wallet_repo.get_by_user_id(UserId(user_id))
            
            # Filter to EVM wallets only (exclude Bitcoin addresses)
            evm_wallets = [
                w for w in wallets
                if w.address.startswith("0x")
            ]
            
            # Prefer PRIVY provider among EVM wallets
            wallet = next(
                (w for w in evm_wallets if getattr(w, "provider", None) == WalletProvider.PRIVY),
                None,
            )
            if wallet is None and evm_wallets:
                wallet = evm_wallets[0]
            # Fallback to any wallet if no EVM wallet found
            if wallet is None and wallets:
                wallet = wallets[0]

            latency_ms = int((time.time() - start_time) * 1000)

            if not wallet:
                return ReceiveHandlerResult(
                    content=self._format_no_wallet_response(),
                    wallet_address="",
                    ens_handle=None,
                    supported_networks=[n["name"] for n in self.SUPPORTED_NETWORKS],
                    chain=chain,
                    latency_ms=latency_ms,
                )

            # Get ENS handle (if available in metadata)
            ens_handle = wallet.metadata.get("ens") if hasattr(wallet, "metadata") else None

            # Format response
            content = self._format_receive_response(
                wallet_address=wallet.address,
                ens_handle=ens_handle,
                chain=chain,
            )

            return ReceiveHandlerResult(
                content=content,
                wallet_address=wallet.address,
                ens_handle=ens_handle,
                supported_networks=[n["name"] for n in self.SUPPORTED_NETWORKS],
                chain=chain,
                latency_ms=latency_ms,
            )

        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)

            return ReceiveHandlerResult(
                content=f"⚠️ **Error Fetching Wallet**\n\n{str(e)}\n\nPlease try again later.",
                wallet_address="",
                ens_handle=None,
                supported_networks=[],
                chain=chain,
                latency_ms=latency_ms,
            )

    def _format_receive_response(
        self,
        wallet_address: str,
        ens_handle: Optional[str],
        chain: str,
    ) -> str:
        """Format receive info as chat response."""
        chain_emoji = "🔵" if chain == "base" else "⟠"

        ens_section = ""
        if ens_handle:
            ens_section = f"""
**ENS Handle:**
`{ens_handle}`
"""

        response = f"""📥 **Receive Funds**

**Your Wallet Address:**
`{wallet_address}`
{ens_section}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📱 **QR Code:** [Scan to deposit]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Supported Networks:**
"""
        for network in self.SUPPORTED_NETWORKS:
            response += f"• **{network['name']}** ({network['tokens']})\n"

        response += f"""
⚠️ **Important:**
• Only send tokens on the **correct network** to avoid loss
• This address works for **all EVM chains** listed above
• Double-check the address before sending

📋 *Tap address to copy*

{chain_emoji} Currently viewing: {chain.upper()}
"""
        return response

    def _format_no_wallet_response(self) -> str:
        """Format response when no wallet found."""
        return """📥 **No Wallet Found**

You don't have a wallet set up yet.

**To get started:**
1. Connect your wallet via the app
2. Or create an embedded wallet

Once connected, you'll be able to:
• View your deposit address
• Receive funds on multiple chains
• Track incoming transactions

Would you like help setting up a wallet?
"""
