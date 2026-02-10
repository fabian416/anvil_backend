"""
Receive Handler for Chat - Wallet address and QR code operations.

Provides wallet address information for receiving funds:
- User's wallet address from Privy/WalletRepository
- ENS handle (if registered)
- Multi-chain support
- QR code generation (placeholder for frontend)
"""

import logging
import time
from dataclasses import dataclass
from typing import Optional

from app.application.common.services.current_user import CurrentUserService
from app.domain.ports.wallet.wallet_repository import WalletRepository
from app.domain.ports.wallet.embedded_wallet_provider import (
    EmbeddedWalletProviderPort,
    WalletProviderError,
)
from app.domain.enums.wallet_provider import WalletProvider
from app.domain.value_objects.user_id import UserId
from app.infrastructure.exceptions.gateway import DataMapperError
from app.setup.config.privy import PrivySettings

logger = logging.getLogger(__name__)


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
    pending_action: str | None = None  # For multi-turn flows

    # QR Code fields (from database, pre-generated)
    qr_image_url: str | None = None  # Pre-generated QR image URL (CDN or local)
    qr_data: str | None = None  # EIP-681 URI for client-side generation fallback
    qr_chain_id: int = 8453  # Chain ID encoded in QR (default: Base)


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

    def __init__(
        self,
        wallet_repository: WalletRepository,
        current_user_service: CurrentUserService | None = None,
        wallet_provider: EmbeddedWalletProviderPort | None = None,
        privy_settings: PrivySettings | None = None,
    ):
        """
        Initialize receive handler.

        Args:
            wallet_repository: Repository for wallet data
        """
        self._wallet_repo = wallet_repository
        self._current_user_service = current_user_service
        self._wallet_provider = wallet_provider
        self._privy_settings = privy_settings

    async def _resolve_user_wallet_address(
        self, user_id: int
    ) -> tuple[str | None, dict | None, "Wallet | None"]:
        """
        Resolve wallet address and optional metadata (e.g. ENS) for receive flow.

        Priority:
        1) Wallets in local DB (WalletRepository)
        2) Privy provider (if configured and user has privy_user_id)
        3) primary_wallet_address on the user record (if set)

        Returns:
            Tuple of (address, metadata, wallet_entity)
        """
        from app.domain.entities.wallet import Wallet

        # 1) DB wallets
        wallets = await self._wallet_repo.get_by_user_id(UserId(user_id))
        if wallets:
            evm_wallets = [w for w in wallets if w.address.startswith("0x")]
            wallet = next(
                (
                    w
                    for w in evm_wallets
                    if getattr(w, "provider", None) == WalletProvider.PRIVY
                ),
                None,
            )
            if wallet is None and evm_wallets:
                wallet = evm_wallets[0]
            if wallet is None:
                wallet = wallets[0]
            if wallet:
                meta = wallet.metadata if hasattr(wallet, "metadata") else None
                return wallet.address, meta, wallet

        # 2) Privy provider
        if (
            self._current_user_service
            and self._wallet_provider
            and self._privy_settings
            and self._privy_settings.should_call_privy
        ):
            try:
                user = await self._current_user_service.get_current_user()
                privy_user_id = user.privy_user_id.value if user.privy_user_id else None
                if privy_user_id:
                    privy_wallets = await self._wallet_provider.list_user_wallets(
                        privy_user_id
                    )
                    evm = [w for w in privy_wallets if w.address.startswith("0x")]
                    if evm:
                        if self._privy_settings.should_persist_to_db:
                            for pw in evm:
                                try:
                                    await self._wallet_repo.upsert(
                                        user_id=UserId(user_id),
                                        address=pw.address,
                                        provider=WalletProvider.PRIVY,
                                        privy_wallet_id=pw.wallet_id,
                                        chain_type=pw.chain_type.value,
                                    )
                                except DataMapperError:
                                    logger.debug(
                                        "Failed to persist privy wallet %s...",
                                        pw.address[:10],
                                    )
                        # Fetch the wallet entity from DB to get QR info
                        db_wallet = await self._wallet_repo.get_by_user_and_address(
                            UserId(user_id), evm[0].address
                        )
                        return evm[0].address, evm[0].metadata, db_wallet
            except WalletProviderError as e:
                logger.warning("Privy wallet fetch failed for receive flow: %s", e)
            except Exception as e:
                logger.warning("Unexpected wallet fetch error for receive flow: %s", e)

        # 3) primary_wallet_address fallback
        if self._current_user_service:
            try:
                user = await self._current_user_service.get_current_user()
                if user.primary_wallet_address:
                    return user.primary_wallet_address.value, None, None
            except Exception:
                return None, None, None

        return None, None, None

    async def get_receive_info(
        self,
        user_id: int,
        chain: str = "base",
        language: str = "en",
    ) -> ReceiveHandlerResult:
        """
        Get receive information for a user.

        Args:
            user_id: User's database ID
            chain: Preferred chain (for display purposes)

        Returns:
            ReceiveHandlerResult with wallet address, QR code info, and formatted content
        """
        start_time = time.time()

        try:
            wallet_address, meta, wallet = await self._resolve_user_wallet_address(
                user_id
            )

            latency_ms = int((time.time() - start_time) * 1000)

            if not wallet_address:
                return ReceiveHandlerResult(
                    content=self._format_no_wallet_response(language),
                    wallet_address="",
                    ens_handle=None,
                    supported_networks=[n["name"] for n in self.SUPPORTED_NETWORKS],
                    chain=chain,
                    latency_ms=latency_ms,
                    language=language,
                    pending_action="receive_no_wallet",
                )

            # Get ENS handle (if available in metadata)
            ens_handle = None
            if isinstance(meta, dict):
                ens_handle = meta.get("ens")

            # Extract QR info from wallet entity (if available)
            qr_image_url = None
            qr_chain_id = 8453  # Default to Base
            if wallet:
                qr_image_url = wallet.qr_image_url
                qr_chain_id = wallet.qr_chain_id or 8453

            # Build QR data for client-side fallback
            qr_data = f"ethereum:{qr_chain_id}:{wallet_address}"

            # Format response
            content = self._format_receive_response(
                wallet_address=wallet_address,
                ens_handle=ens_handle,
                chain=chain,
                language=language,
            )

            return ReceiveHandlerResult(
                content=content,
                wallet_address=wallet_address,
                ens_handle=ens_handle,
                supported_networks=[n["name"] for n in self.SUPPORTED_NETWORKS],
                chain=chain,
                latency_ms=latency_ms,
                language=language,
                # QR code fields
                qr_image_url=qr_image_url,
                qr_data=qr_data,
                qr_chain_id=qr_chain_id,
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
                language=language,
            )

    def _format_receive_response(
        self,
        wallet_address: str,
        ens_handle: Optional[str],
        chain: str,
        language: str = "en",
    ) -> str:
        """Format receive info as chat response with improved formatting."""
        chain_emoji = "🔵" if chain == "base" else "⟠"

        receive_msgs = {
            "en": {
                "title": "Receive Funds",
                "wallet_address": "Your Wallet Address",
                "ens_handle": "ENS Handle",
                "qr_code": "QR Code",
                "scan_to_deposit": "Scan to deposit",
                "supported_networks": "Supported Networks",
                "important": "Important",
                "important_tips": [
                    "Only send tokens on the **correct network** to avoid loss",
                    "This address works for **all EVM chains** listed above",
                    "Double-check the address before sending",
                ],
                "tap_to_copy": "Tap address to copy",
                "currently_viewing": "Currently viewing",
            },
            "es": {
                "title": "Recibir Fondos",
                "wallet_address": "Tu Dirección de Billetera",
                "ens_handle": "ENS Handle",
                "qr_code": "Código QR",
                "scan_to_deposit": "Escanear para depositar",
                "supported_networks": "Redes Soportadas",
                "important": "Importante",
                "important_tips": [
                    "Solo envía tokens en la **red correcta** para evitar pérdidas",
                    "Esta dirección funciona para **todas las cadenas EVM** listadas arriba",
                    "Verifica la dirección antes de enviar",
                ],
                "tap_to_copy": "Toca la dirección para copiar",
                "currently_viewing": "Viendo actualmente",
            },
            "pt": {
                "title": "Receber Fundos",
                "wallet_address": "Seu Endereço de Carteira",
                "ens_handle": "ENS Handle",
                "qr_code": "Código QR",
                "scan_to_deposit": "Escanear para depositar",
                "supported_networks": "Redes Suportadas",
                "important": "Importante",
                "important_tips": [
                    "Envie tokens apenas na **rede correta** para evitar perdas",
                    "Este endereço funciona para **todas as redes EVM** listadas acima",
                    "Verifique o endereço antes de enviar",
                ],
                "tap_to_copy": "Toque no endereço para copiar",
                "currently_viewing": "Visualizando atualmente",
            },
            "zh": {
                "title": "接收资金",
                "wallet_address": "您的钱包地址",
                "ens_handle": "ENS 名称",
                "qr_code": "二维码",
                "scan_to_deposit": "扫描以存款",
                "supported_networks": "支持的网络",
                "important": "重要提示",
                "important_tips": [
                    "仅在**正确的网络**上发送代币以避免损失",
                    "此地址适用于上面列出的**所有 EVM 链**",
                    "发送前请仔细检查地址",
                ],
                "tap_to_copy": "点击地址以复制",
                "currently_viewing": "当前查看",
            },
        }

        msgs = receive_msgs.get(language, receive_msgs["en"])

        ens_section = ""
        if ens_handle:
            ens_section = f"""
**{msgs["ens_handle"]}:**
`{ens_handle}`
"""

        response = f"""📥 **{msgs["title"]}**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**{msgs["wallet_address"]}:**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

`{wallet_address}`
{ens_section}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📱 **{msgs["qr_code"]}:** [{msgs["scan_to_deposit"]}]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**{msgs["supported_networks"]}:**
"""
        for network in self.SUPPORTED_NETWORKS:
            response += f"• **{network['name']}** ({network['tokens']})\n"

        important_tips = "\n".join([f"• {tip}" for tip in msgs["important_tips"]])

        response += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ **{msgs["important"]}:**
{important_tips}

📋 *{msgs["tap_to_copy"]}*

{chain_emoji} {msgs["currently_viewing"]}: {chain.upper()}
"""
        return response

    def _format_no_wallet_response(self, language: str = "en") -> str:
        """Format response when no wallet found with improved formatting."""
        no_wallet_msgs = {
            "en": {
                "title": "No Wallet Found",
                "message": "You don't have a wallet set up yet.",
                "header": "To get started:",
                "options": [
                    (
                        "🔗",
                        "Connect your wallet",
                        "Link an existing wallet via the app",
                    ),
                    (
                        "✨",
                        "Create embedded wallet",
                        "Set up a new wallet automatically",
                    ),
                    ("💡", "Get help", "Learn more about wallet setup"),
                ],
            },
            "es": {
                "title": "Billetera No Encontrada",
                "message": "Aún no tienes una billetera configurada.",
                "header": "Para comenzar:",
                "options": [
                    (
                        "🔗",
                        "Conectar tu billetera",
                        "Vincula una billetera existente vía la app",
                    ),
                    (
                        "✨",
                        "Crear billetera integrada",
                        "Configura una nueva billetera automáticamente",
                    ),
                    (
                        "💡",
                        "Obtener ayuda",
                        "Aprende más sobre la configuración de billetera",
                    ),
                ],
            },
            "pt": {
                "title": "Carteira Não Encontrada",
                "message": "Você ainda não tem uma carteira configurada.",
                "header": "Para começar:",
                "options": [
                    (
                        "🔗",
                        "Conectar sua carteira",
                        "Vincule uma carteira existente via o app",
                    ),
                    (
                        "✨",
                        "Criar carteira integrada",
                        "Configure uma nova carteira automaticamente",
                    ),
                    (
                        "💡",
                        "Obter ajuda",
                        "Saiba mais sobre a configuração de carteira",
                    ),
                ],
            },
            "zh": {
                "title": "未找到钱包",
                "message": "您还没有设置钱包。",
                "header": "开始使用:",
                "options": [
                    ("🔗", "连接您的钱包", "通过应用链接现有钱包"),
                    ("✨", "创建嵌入式钱包", "自动设置新钱包"),
                    ("💡", "获取帮助", "了解更多关于钱包设置的信息"),
                ],
            },
        }

        msgs = no_wallet_msgs.get(language, no_wallet_msgs["en"])
        options_text = "\n".join([
            f"**{i}.** {emoji} **{title}**\n   {details}"
            for i, (emoji, title, details) in enumerate(msgs["options"], 1)
        ])

        return f"""📥 **{msgs["title"]}**

{msgs["message"]}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**{msgs["header"]}**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{options_text}

💬 **Reply with the number (1, 2, or 3) to continue.**
"""
