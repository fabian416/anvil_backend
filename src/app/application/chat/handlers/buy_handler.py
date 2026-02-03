"""
Buy Handler for Chat - On-ramp crypto purchase operations.

Provides information for buying crypto with fiat via Privy on-ramp:
- MoonPay/Coinbase integration (via Privy)
- Supported assets and networks
- Frontend-triggered flow (Privy modal)
- Multi-turn conversational flow for collecting buy parameters

Note: The actual on-ramp flow is handled by Privy SDK on the frontend.
This handler provides instructional content, collects buy parameters,
and signals the frontend to open the Privy funding modal with pre-configured data.
"""

import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any, Optional

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


# ============================================================================
# Data Classes
# ============================================================================


@dataclass
class BuyInfo:
    """Information for a buy operation."""

    amount: str | None = None  # Amount in fiat (e.g., "100")
    fiat_currency: str = "USD"  # Fiat currency
    crypto_currency: str | None = "USDC"  # Crypto to buy (USDC only)

    # Only USDC is supported for direct purchase
    SUPPORTED_CRYPTOS: list[str] = field(default_factory=lambda: ["USDC"])

    # Unsupported cryptos (for helpful error messages)
    UNSUPPORTED_CRYPTOS: list[str] = field(
        default_factory=lambda: ["ETH", "USDT", "BTC", "MATIC", "SOL"]
    )

    @property
    def is_complete(self) -> bool:
        """Check if we have all required info."""
        # Only need amount since USDC is the only option
        return bool(self.amount)

    @property
    def next_step(self) -> str | None:
        """Get the next step needed."""
        if not self.amount:
            return "amount"
        return None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "amount": self.amount,
            "fiat_currency": self.fiat_currency,
            "crypto_currency": self.crypto_currency or "USDC",
            "is_complete": self.is_complete,
            "next_step": self.next_step,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BuyInfo":
        """Create from dictionary."""
        return cls(
            amount=data.get("amount"),
            fiat_currency=data.get("fiat_currency", "USD"),
            crypto_currency="USDC",  # Always USDC
        )


@dataclass
class BuyHandlerResult:
    """Result from buy handler."""

    content: str
    wallet_address: Optional[str]
    supported_assets: list[str]
    supported_networks: list[str]
    requires_privy_modal: bool
    latency_ms: int
    language: str = "en"
    handler: str = "buy_handler"
    # Multi-turn flow fields
    pending_action: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    execute_data: dict[str, Any] | None = None


# Localized messages
MESSAGES = {
    "en": {
        "title": "💳 **Buy Crypto**",
        "description": "Purchase crypto with card, Apple Pay, or Google Pay via MoonPay/Coinbase.",
        "supported_assets": "Supported Assets",
        "supported_networks": "Supported Networks",
        "how_to_buy": "How to Buy",
        "step_1": "Click the button below or use the 'Buy Crypto' shortcut",
        "step_2": "Select the asset and amount you want to purchase",
        "step_3": "Complete payment via MoonPay or Coinbase",
        "step_4": "Funds will be deposited to your wallet",
        "note_title": "Note",
        "note_content": "Processing time varies from a few minutes to 24 hours depending on payment method and verification status.",
        "no_wallet": """⚠️ **No Wallet Found**

You need to connect or create a wallet first to buy crypto.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**To get started:**

1. **Connect your wallet** via the app settings
2. **Or create an embedded wallet** using Privy
3. **Then try buying crypto again**

Once your wallet is connected, you'll be able to:
• Buy crypto with card, Apple Pay, or Google Pay
• Receive funds directly to your wallet
• Track your portfolio and transactions

💡 **Tip:** If you're using Privy, your wallet should be created automatically when you sign up.""",
        "open_privy": "Opening crypto purchase flow...",
    },
    "es": {
        "title": "💳 **Comprar Cripto**",
        "description": "Compra cripto con tarjeta, Apple Pay o Google Pay vía MoonPay/Coinbase.",
        "supported_assets": "Activos Soportados",
        "supported_networks": "Redes Soportadas",
        "how_to_buy": "Cómo Comprar",
        "step_1": "Haz clic en el botón o usa el atajo 'Comprar cripto'",
        "step_2": "Selecciona el activo y el monto que deseas comprar",
        "step_3": "Completa el pago vía MoonPay o Coinbase",
        "step_4": "Los fondos se depositarán en tu wallet",
        "note_title": "Nota",
        "note_content": "El tiempo de procesamiento varía de minutos a 24 horas según el método de pago y estado de verificación.",
        "no_wallet": """⚠️ **No se encontró Wallet**

Necesitas conectar o crear una wallet primero para comprar cripto.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Para comenzar:**

1. **Conecta tu wallet** desde la configuración de la app
2. **O crea una wallet integrada** usando Privy
3. **Luego intenta comprar cripto nuevamente**

Una vez que tu wallet esté conectada, podrás:
• Comprar cripto con tarjeta, Apple Pay o Google Pay
• Recibir fondos directamente en tu wallet
• Rastrear tu portafolio y transacciones

💡 **Consejo:** Si estás usando Privy, tu wallet debería crearse automáticamente al registrarte.""",
        "open_privy": "Abriendo el flujo de compra de cripto...",
    },
    "pt": {
        "title": "💳 **Comprar Cripto**",
        "description": "Compre cripto com cartão, Apple Pay ou Google Pay via MoonPay/Coinbase.",
        "supported_assets": "Ativos Suportados",
        "supported_networks": "Redes Suportadas",
        "how_to_buy": "Como Comprar",
        "step_1": "Clique no botão ou use o atalho 'Comprar cripto'",
        "step_2": "Selecione o ativo e o valor que deseja comprar",
        "step_3": "Complete o pagamento via MoonPay ou Coinbase",
        "step_4": "Os fundos serão depositados em sua wallet",
        "note_title": "Nota",
        "note_content": "O tempo de processamento varia de minutos a 24 horas dependendo do método de pagamento e status de verificação.",
        "no_wallet": """⚠️ **Wallet não encontrada**

Você precisa conectar ou criar uma wallet primeiro para comprar cripto.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Para começar:**

1. **Conecte sua wallet** nas configurações do app
2. **Ou crie uma wallet integrada** usando Privy
3. **Depois tente comprar cripto novamente**

Assim que sua wallet estiver conectada, você poderá:
• Comprar cripto com cartão, Apple Pay ou Google Pay
• Receber fundos diretamente na sua wallet
• Acompanhar seu portfólio e transações

💡 **Dica:** Se você está usando Privy, sua wallet deve ser criada automaticamente ao se registrar.""",
        "open_privy": "Abrindo o fluxo de compra de cripto...",
    },
    "zh": {
        "title": "💳 **购买加密货币**",
        "description": "通过MoonPay/Coinbase使用银行卡、Apple Pay或Google Pay购买加密货币。",
        "supported_assets": "支持的资产",
        "supported_networks": "支持的网络",
        "how_to_buy": "如何购买",
        "step_1": "点击下方按钮或使用'购买加密货币'快捷方式",
        "step_2": "选择您想购买的资产和金额",
        "step_3": "通过MoonPay或Coinbase完成支付",
        "step_4": "资金将存入您的钱包",
        "note_title": "注意",
        "note_content": "处理时间因支付方式和验证状态而异，从几分钟到24小时不等。",
        "no_wallet": """⚠️ **未找到钱包**

您需要先连接或创建钱包才能购买加密货币。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**开始使用：**

1. **在应用设置中连接您的钱包**
2. **或使用Privy创建嵌入式钱包**
3. **然后再次尝试购买加密货币**

连接钱包后，您将能够：
• 使用银行卡、Apple Pay或Google Pay购买加密货币
• 直接将资金接收到您的钱包
• 跟踪您的投资组合和交易

💡 **提示：** 如果您使用Privy，注册时钱包应自动创建。""",
        "open_privy": "正在打开加密货币购买流程...",
    },
    "fr": {
        "title": "💳 **Acheter des Cryptos**",
        "description": "Achetez des cryptos par carte, Apple Pay ou Google Pay via MoonPay/Coinbase.",
        "supported_assets": "Actifs Supportés",
        "supported_networks": "Réseaux Supportés",
        "how_to_buy": "Comment Acheter",
        "step_1": "Cliquez sur le bouton ou utilisez le raccourci 'Acheter des cryptos'",
        "step_2": "Sélectionnez l'actif et le montant que vous souhaitez acheter",
        "step_3": "Complétez le paiement via MoonPay ou Coinbase",
        "step_4": "Les fonds seront déposés dans votre wallet",
        "note_title": "Note",
        "note_content": "Le temps de traitement varie de quelques minutes à 24 heures selon le mode de paiement et le statut de vérification.",
        "no_wallet": """⚠️ **Wallet non trouvé**

Vous devez connecter ou créer un wallet d'abord pour acheter des cryptos.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Pour commencer :**

1. **Connectez votre wallet** via les paramètres de l'application
2. **Ou créez un wallet intégré** en utilisant Privy
3. **Puis réessayez d'acheter des cryptos**

Une fois votre wallet connecté, vous pourrez :
• Acheter des cryptos par carte, Apple Pay ou Google Pay
• Recevoir des fonds directement sur votre wallet
• Suivre votre portefeuille et vos transactions

💡 **Astuce :** Si vous utilisez Privy, votre wallet devrait être créé automatiquement lors de l'inscription.""",
        "open_privy": "Ouverture du flux d'achat de cryptos...",
    },
}


# Messages for multi-turn buy flow (USDC only)
BUY_FLOW_MESSAGES = {
    "en": {
        "ask_amount": """💵 **Buy USDC**

How much USDC would you like to buy?

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**USDC** is a stablecoin pegged 1:1 to the US Dollar - perfect for:
• 🔄 Swapping to other cryptos (ETH, BTC, SOL...)
• 💰 Earning yield in DeFi
• 📤 Sending to friends

💬 Enter an amount in USD (e.g., 50, 100, 500)

💡 *Minimum purchase: $30*""",
        "ask_crypto": "🪙 Which cryptocurrency would you like to buy?\n\n{options}\n\nReply with the number or name.",
        "confirm_buy": """✅ **Ready to buy USDC**

💵 **Amount:** ${amount} USD
🪙 **Crypto:** USDC (USD Coin)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Click **Continue** to complete your purchase with MoonPay.""",
        "invalid_amount": "❌ Please enter a valid amount (minimum $30).\n\nExample: 50, 100, or 500",
        "invalid_crypto": "❌ Currently only **USDC** is available for purchase.\n\nWould you like to buy USDC instead? You can then swap it for other cryptos!",
        "usdc_only": """💡 **USDC Only Available**

I see you want to buy **{crypto}**, but currently only **USDC** is available for direct purchase.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Here's a tip:** You can buy USDC first, then swap it for {crypto} instantly!

Would you like to buy USDC instead?

💬 Just tell me how much (e.g., "$100" or "500 dollars")""",
    },
    "es": {
        "ask_amount": """💵 **Comprar USDC**

¿Cuánto USDC te gustaría comprar?

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**USDC** es una stablecoin con paridad 1:1 al dólar - perfecta para:
• 🔄 Intercambiar por otras criptos (ETH, BTC, SOL...)
• 💰 Ganar rendimiento en DeFi
• 📤 Enviar a amigos

💬 Ingresa un monto en USD (ej: 50, 100, 500)

💡 *Compra mínima: $30*""",
        "ask_crypto": "🪙 ¿Qué criptomoneda deseas comprar?\n\n{options}\n\nResponde con el número o nombre.",
        "confirm_buy": """✅ **Listo para comprar USDC**

💵 **Monto:** ${amount} USD
🪙 **Crypto:** USDC (USD Coin)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Haz clic en **Continuar** para completar tu compra con MoonPay.""",
        "invalid_amount": "❌ Por favor ingresa un monto válido (mínimo $30).\n\nEjemplo: 50, 100, o 500",
        "invalid_crypto": "❌ Actualmente solo **USDC** está disponible para compra.\n\n¿Te gustaría comprar USDC en su lugar? ¡Luego puedes cambiarlo por otras criptos!",
        "usdc_only": """💡 **Solo USDC Disponible**

Veo que quieres comprar **{crypto}**, pero actualmente solo **USDC** está disponible para compra directa.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Un consejo:** ¡Puedes comprar USDC primero y luego cambiarlo por {crypto} al instante!

¿Te gustaría comprar USDC en su lugar?

💬 Solo dime cuánto (ej: "$100" o "500 dólares")""",
    },
    "pt": {
        "ask_amount": """💵 **Comprar USDC**

Quanto USDC você gostaria de comprar?

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**USDC** é uma stablecoin com paridade 1:1 ao dólar - perfeita para:
• 🔄 Trocar por outras criptos (ETH, BTC, SOL...)
• 💰 Ganhar rendimento em DeFi
• 📤 Enviar para amigos

💬 Digite um valor em USD (ex: 50, 100, 500)

💡 *Compra mínima: $30*""",
        "ask_crypto": "🪙 Qual criptomoeda você gostaria de comprar?\n\n{options}\n\nResponda com o número ou nome.",
        "confirm_buy": """✅ **Pronto para comprar USDC**

💵 **Valor:** ${amount} USD
🪙 **Crypto:** USDC (USD Coin)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Clique em **Continuar** para completar sua compra com MoonPay.""",
        "invalid_amount": "❌ Por favor digite um valor válido (mínimo $30).\n\nExemplo: 50, 100, ou 500",
        "invalid_crypto": "❌ Atualmente apenas **USDC** está disponível para compra.\n\nGostaria de comprar USDC em vez disso? Você pode depois trocar por outras criptos!",
        "usdc_only": """💡 **Apenas USDC Disponível**

Vejo que você quer comprar **{crypto}**, mas atualmente apenas **USDC** está disponível para compra direta.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Uma dica:** Você pode comprar USDC primeiro e depois trocar por {crypto} instantaneamente!

Gostaria de comprar USDC em vez disso?

💬 Apenas me diga quanto (ex: "$100" ou "500 dólares")""",
    },
    "zh": {
        "ask_amount": """💵 **购买 USDC**

您想购买多少 USDC？

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**USDC** 是与美元 1:1 挂钩的稳定币 - 非常适合：
• 🔄 兑换其他加密货币（ETH、BTC、SOL...）
• 💰 在 DeFi 中赚取收益
• 📤 发送给朋友

💬 输入美元金额（例如：50、100、500）

💡 *最低购买金额：$30*""",
        "ask_crypto": "🪙 您想购买哪种加密货币？\n\n{options}\n\n请回复数字或名称。",
        "confirm_buy": """✅ **准备购买 USDC**

💵 **金额：** ${amount} USD
🪙 **加密货币：** USDC (USD Coin)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

点击 **继续** 使用 MoonPay 完成购买。""",
        "invalid_amount": "❌ 请输入有效金额（最低 $30）。\n\n示例：50、100 或 500",
        "invalid_crypto": "❌ 目前仅支持购买 **USDC**。\n\n您想购买 USDC 吗？之后可以兑换其他加密货币！",
        "usdc_only": """💡 **仅支持 USDC**

我看到您想购买 **{crypto}**，但目前只有 **USDC** 可以直接购买。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**小贴士：** 您可以先购买 USDC，然后立即将其兑换成 {crypto}！

您想改为购买 USDC 吗？

💬 告诉我您想要多少（例如："$100" 或 "500美元"）""",
    },
    "fr": {
        "ask_amount": """💵 **Acheter USDC**

Combien d'USDC souhaitez-vous acheter ?

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**USDC** est une stablecoin indexée 1:1 sur le dollar - parfaite pour :
• 🔄 Échanger contre d'autres cryptos (ETH, BTC, SOL...)
• 💰 Gagner des rendements en DeFi
• 📤 Envoyer à des amis

💬 Entrez un montant en USD (ex: 50, 100, 500)

💡 *Achat minimum : $30*""",
        "ask_crypto": "🪙 Quelle cryptomonnaie souhaitez-vous acheter ?\n\n{options}\n\nRépondez avec le numéro ou le nom.",
        "confirm_buy": """✅ **Prêt à acheter USDC**

💵 **Montant :** ${amount} USD
🪙 **Crypto :** USDC (USD Coin)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Cliquez sur **Continuer** pour finaliser votre achat avec MoonPay.""",
        "invalid_amount": "❌ Veuillez entrer un montant valide (minimum $30).\n\nExemple : 50, 100, ou 500",
        "invalid_crypto": "❌ Actuellement, seul **USDC** est disponible à l'achat.\n\nVoulez-vous acheter de l'USDC à la place ? Vous pourrez ensuite l'échanger contre d'autres cryptos !",
        "usdc_only": """💡 **USDC Uniquement Disponible**

Je vois que vous voulez acheter **{crypto}**, mais actuellement seul **USDC** est disponible à l'achat direct.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Astuce :** Vous pouvez d'abord acheter de l'USDC, puis l'échanger instantanément contre {crypto} !

Voulez-vous acheter de l'USDC à la place ?

💬 Dites-moi simplement combien (ex : "$100" ou "500 dollars")""",
    },
}


class BuyHandler:
    """
    Handler for buy crypto chat intents.

    Provides instructional content about buying crypto via Privy on-ramp.
    The actual purchase flow is handled by the frontend using Privy SDK.

    Features:
    - Informative content about on-ramp process
    - Supported assets and networks display
    - Multi-language support
    - Frontend signal for Privy modal
    """

    # Supported assets for on-ramp
    SUPPORTED_ASSETS = [
        "ETH",
        "USDC",
        "USDT",
        "BTC",
        "MATIC",
    ]

    # Supported networks
    SUPPORTED_NETWORKS = [
        "Ethereum",
        "Base",
        "Polygon",
        "Arbitrum",
        "Optimism",
    ]

    def __init__(
        self,
        wallet_repository: WalletRepository,
        current_user_service: CurrentUserService | None = None,
        wallet_provider: EmbeddedWalletProviderPort | None = None,
        privy_settings: PrivySettings | None = None,
    ):
        """
        Initialize buy handler.

        Args:
            wallet_repository: Repository for wallet data
        """
        self._wallet_repo = wallet_repository
        self._current_user_service = current_user_service
        self._wallet_provider = wallet_provider
        self._privy_settings = privy_settings

    async def _resolve_user_wallet_address(self, user_id: int) -> str | None:
        """
        Resolve the user's wallet address using a best-effort strategy.

        Priority:
        1) Wallets in local DB (WalletRepository)
        2) Privy provider (if configured and user has privy_user_id)
        3) primary_wallet_address on the user record (if set)
        """
        # 1) DB wallets (may be empty if running in PRIVY mode without persistence).
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
            return wallet.address if wallet else None

        # 2) Privy provider (source of truth for embedded wallets)
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
                        # Best-effort persist for later DB reads (hybrid/local modes).
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
                                    # Don't fail chat flow if persistence fails.
                                    logger.debug(
                                        "Failed to persist privy wallet %s...",
                                        pw.address[:10],
                                    )
                        return evm[0].address
            except WalletProviderError as e:
                logger.warning("Privy wallet fetch failed for buy flow: %s", e)
            except Exception as e:
                logger.warning("Unexpected wallet fetch error for buy flow: %s", e)

        # 3) primary wallet address on user record (if present)
        if self._current_user_service:
            try:
                user = await self._current_user_service.get_current_user()
                if user.primary_wallet_address:
                    return user.primary_wallet_address.value
            except Exception:
                return None

        return None

    async def get_buy_info(
        self,
        user_id: int,
        language: str = "en",
    ) -> BuyHandlerResult:
        """
        Get buy information for a user.

        Args:
            user_id: User's database ID
            language: Language code for response

        Returns:
            BuyHandlerResult with formatted content and frontend signals
        """
        start_time = time.time()

        # Get localized messages
        lang = language if language in MESSAGES else "en"
        msgs = MESSAGES[lang]

        try:
            # Resolve wallet address using best-effort strategy (DB -> Privy -> primary_wallet_address)
            wallet_address = await self._resolve_user_wallet_address(user_id)

            # Log for debugging
            logger.debug(
                f"BuyHandler: Resolved wallet address for user {user_id}: {wallet_address[:10] + '...' if wallet_address else 'None'}"
            )

            latency_ms = int((time.time() - start_time) * 1000)

            if not wallet_address:
                logger.warning(
                    f"BuyHandler: No wallet found for user {user_id} after checking DB, Privy, and primary_wallet_address"
                )
                return BuyHandlerResult(
                    content=msgs["no_wallet"],
                    wallet_address=None,
                    supported_assets=self.SUPPORTED_ASSETS,
                    supported_networks=self.SUPPORTED_NETWORKS,
                    requires_privy_modal=False,
                    latency_ms=latency_ms,
                    language=lang,
                )

            # Format response
            content = self._format_buy_response(
                wallet_address=wallet_address,
                msgs=msgs,
            )

            return BuyHandlerResult(
                content=content,
                wallet_address=wallet_address,
                supported_assets=self.SUPPORTED_ASSETS,
                supported_networks=self.SUPPORTED_NETWORKS,
                requires_privy_modal=True,
                latency_ms=latency_ms,
                language=lang,
            )

        except Exception as e:
            # Log the error for debugging
            logger.warning(
                f"Error getting wallet for user {user_id} in buy handler: {e}",
                exc_info=True,
            )

            latency_ms = int((time.time() - start_time) * 1000)

            # Provide user-friendly error message instead of technical error
            # Check if it's a database error
            if isinstance(e, DataMapperError) or "Database query failed" in str(e):
                # Return no_wallet message instead of error - user can still proceed
                return BuyHandlerResult(
                    content=msgs["no_wallet"],
                    wallet_address=None,
                    supported_assets=self.SUPPORTED_ASSETS,
                    supported_networks=self.SUPPORTED_NETWORKS,
                    requires_privy_modal=False,
                    latency_ms=latency_ms,
                    language=lang,
                )
            else:
                # For other errors, show generic error message
                error_content = f"⚠️ **Error**\n\n{str(e)}\n\nPlease try again later."
                return BuyHandlerResult(
                    content=error_content,
                    wallet_address=None,
                    supported_assets=self.SUPPORTED_ASSETS,
                    supported_networks=self.SUPPORTED_NETWORKS,
                    requires_privy_modal=False,
                    latency_ms=latency_ms,
                    language=lang,
                )

    def _format_buy_response(
        self,
        wallet_address: str,
        msgs: dict,
    ) -> str:
        """Format buy info as chat response with improved visual structure."""
        # Format assets and networks as bullet points for better readability
        assets_list = "\n".join([f"• {asset}" for asset in self.SUPPORTED_ASSETS])
        networks_list = "\n".join([
            f"• {network}" for network in self.SUPPORTED_NETWORKS
        ])

        response = f"""{msgs["title"]}

{msgs["description"]}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**{msgs["supported_assets"]}:**
{assets_list}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**{msgs["supported_networks"]}:**
{networks_list}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**{msgs["how_to_buy"]}:**

1. {msgs["step_1"]}
2. {msgs["step_2"]}
3. {msgs["step_3"]}
4. {msgs["step_4"]}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 **{msgs["note_title"]}:** {msgs["note_content"]}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📬 **Your Deposit Address:**
`{wallet_address}`

📋 *Tap to copy address*
"""
        return response

    # ========================================================================
    # Multi-turn Flow Methods
    # ========================================================================

    def _parse_amount(self, message: str) -> str | None:
        """
        Extract amount from user message.

        Args:
            message: User's message

        Returns:
            Amount as string if valid, None otherwise
        """
        # Remove currency symbols and common words
        cleaned = message.lower().replace("$", "").replace("usd", "").strip()

        # Try to find a number
        match = re.search(r"(\d+(?:\.\d{1,2})?)", cleaned)
        if match:
            amount = float(match.group(1))
            # MoonPay minimum is $30
            if amount >= 30:
                return str(amount)
        return None

    def _parse_crypto(self, message: str, supported: list[str]) -> str | None:
        """
        Extract crypto from user message (USDC only).

        Args:
            message: User's message
            supported: List of supported cryptocurrencies

        Returns:
            "USDC" if mentioned, None otherwise
        """
        message_upper = message.upper().strip()

        # Check for USDC
        if "USDC" in message_upper:
            return "USDC"

        return None

    def _detect_unsupported_crypto(self, message: str) -> str | None:
        """
        Detect if user is trying to buy an unsupported crypto.

        Args:
            message: User's message

        Returns:
            Crypto symbol if unsupported crypto detected, None otherwise
        """
        message_upper = message.upper().strip()

        unsupported = [
            "ETH",
            "BTC",
            "BITCOIN",
            "ETHEREUM",
            "SOL",
            "SOLANA",
            "USDT",
            "MATIC",
            "POLYGON",
        ]

        for crypto in unsupported:
            if crypto in message_upper:
                # Normalize to standard symbol
                if crypto in ["BITCOIN"]:
                    return "BTC"
                elif crypto in ["ETHEREUM"]:
                    return "ETH"
                elif crypto in ["SOLANA"]:
                    return "SOL"
                elif crypto in ["POLYGON"]:
                    return "MATIC"
                return crypto

        return None

    def _format_crypto_options(self, cryptos: list[str]) -> str:
        """Format crypto options as numbered list."""
        return "\n".join([f"{i + 1}. {crypto}" for i, crypto in enumerate(cryptos)])

    async def process_buy_flow(
        self,
        buy_info: BuyInfo,
        language: str,
        wallet_address: str,
    ) -> BuyHandlerResult:
        """
        Process the buy flow step by step (USDC only).

        Args:
            buy_info: Current buy info state
            language: Language code for messages
            wallet_address: User's wallet address

        Returns:
            BuyHandlerResult with appropriate content and state
        """
        logger.info(f"[BUY_DEBUG] process_buy_flow() called")
        logger.info(f"[BUY_DEBUG] buy_info.amount: {buy_info.amount}")
        logger.info(f"[BUY_DEBUG] buy_info.crypto_currency: {buy_info.crypto_currency}")
        logger.info(f"[BUY_DEBUG] buy_info.is_complete: {buy_info.is_complete}")
        logger.info(f"[BUY_DEBUG] buy_info.next_step: {buy_info.next_step}")

        msgs = BUY_FLOW_MESSAGES.get(language, BUY_FLOW_MESSAGES["en"])

        # Ensure crypto_currency is always USDC
        buy_info.crypto_currency = "USDC"

        # Step 1: Ask for amount (only step needed since USDC is the only option)
        if not buy_info.amount:
            logger.info(
                f"[BUY_DEBUG] Step 1: Asking for USDC amount, pending_action=buy_awaiting_amount"
            )
            return BuyHandlerResult(
                content=msgs["ask_amount"],
                wallet_address=wallet_address,
                supported_assets=buy_info.SUPPORTED_CRYPTOS,
                supported_networks=self.SUPPORTED_NETWORKS,
                requires_privy_modal=False,
                latency_ms=0,
                language=language,
                pending_action="buy_awaiting_amount",
                metadata=buy_info.to_dict(),
            )

        # Step 2: All data collected - Generate execute_data
        logger.info(
            f"[BUY_DEBUG] Step 2: All data collected, generating execute_data for USDC"
        )
        execute_data = {
            "action_type": "buy",
            "chain": "base",
            "from_token": buy_info.fiat_currency,
            "to_token": "USDC",
            "amount": buy_info.amount,
        }
        logger.info(f"[BUY_DEBUG] execute_data: {execute_data}")

        return BuyHandlerResult(
            content=msgs["confirm_buy"].format(
                amount=buy_info.amount,
                crypto_currency="USDC",
            ),
            wallet_address=wallet_address,
            supported_assets=buy_info.SUPPORTED_CRYPTOS,
            supported_networks=self.SUPPORTED_NETWORKS,
            requires_privy_modal=True,
            latency_ms=0,
            language=language,
            pending_action=None,  # Flow complete
            metadata=buy_info.to_dict(),
            execute_data=execute_data,
        )

    async def handle_buy_continuation(
        self,
        user_id: int,
        message: str,
        step: str,
        previous_buy_info: BuyInfo | None,
        language: str = "en",
    ) -> BuyHandlerResult:
        """
        Handle continuation of the buy flow.

        Args:
            user_id: User's database ID
            message: User's message
            step: Current step (amount, crypto)
            previous_buy_info: Previous buy info state
            language: Language code for messages

        Returns:
            BuyHandlerResult with next step or confirmation
        """
        start_time = time.time()
        msgs = BUY_FLOW_MESSAGES.get(language, BUY_FLOW_MESSAGES["en"])

        # Get wallet address
        wallet_address = await self._resolve_user_wallet_address(user_id)
        if not wallet_address:
            lang = language if language in MESSAGES else "en"
            return BuyHandlerResult(
                content=MESSAGES[lang]["no_wallet"],
                wallet_address=None,
                supported_assets=self.SUPPORTED_ASSETS,
                supported_networks=self.SUPPORTED_NETWORKS,
                requires_privy_modal=False,
                latency_ms=int((time.time() - start_time) * 1000),
                language=language,
            )

        # Initialize or restore buy info
        buy_info = previous_buy_info or BuyInfo()
        options = self._format_crypto_options(buy_info.SUPPORTED_CRYPTOS)

        # Process based on step
        if step == "amount":
            amount = self._parse_amount(message)
            if amount:
                buy_info.amount = amount
            else:
                # Invalid amount - ask again
                return BuyHandlerResult(
                    content=msgs["invalid_amount"],
                    wallet_address=wallet_address,
                    supported_assets=buy_info.SUPPORTED_CRYPTOS,
                    supported_networks=self.SUPPORTED_NETWORKS,
                    requires_privy_modal=False,
                    latency_ms=int((time.time() - start_time) * 1000),
                    language=language,
                    pending_action="buy_awaiting_amount",
                    metadata=buy_info.to_dict(),
                )

        elif step == "crypto":
            crypto = self._parse_crypto(message, buy_info.SUPPORTED_CRYPTOS)
            if crypto:
                buy_info.crypto_currency = crypto
            else:
                # Invalid crypto - ask again
                return BuyHandlerResult(
                    content=msgs["invalid_crypto"].format(options=options),
                    wallet_address=wallet_address,
                    supported_assets=buy_info.SUPPORTED_CRYPTOS,
                    supported_networks=self.SUPPORTED_NETWORKS,
                    requires_privy_modal=False,
                    latency_ms=int((time.time() - start_time) * 1000),
                    language=language,
                    pending_action="buy_awaiting_crypto",
                    metadata=buy_info.to_dict(),
                )

        # Continue the flow with updated info
        result = await self.process_buy_flow(buy_info, language, wallet_address)
        result.latency_ms = int((time.time() - start_time) * 1000)
        return result

    async def start_buy_flow(
        self,
        user_id: int,
        message: str,
        language: str = "en",
    ) -> BuyHandlerResult:
        """
        Start a new buy flow, optionally extracting info from initial message.

        Note: Only USDC is available for purchase. If user requests other crypto,
        we show a helpful message suggesting they buy USDC and swap.

        Args:
            user_id: User's database ID
            message: User's initial message
            language: Language code for messages

        Returns:
            BuyHandlerResult with first step or confirmation if all info provided
        """
        logger.info(
            f"[BUY_DEBUG] start_buy_flow() called with user_id={user_id}, message='{message}', language={language}"
        )
        start_time = time.time()

        # Get wallet address first
        wallet_address = await self._resolve_user_wallet_address(user_id)
        logger.info(f"[BUY_DEBUG] wallet_address resolved: {wallet_address}")
        if not wallet_address:
            lang = language if language in MESSAGES else "en"
            return BuyHandlerResult(
                content=MESSAGES[lang]["no_wallet"],
                wallet_address=None,
                supported_assets=self.SUPPORTED_ASSETS,
                supported_networks=self.SUPPORTED_NETWORKS,
                requires_privy_modal=False,
                latency_ms=int((time.time() - start_time) * 1000),
                language=language,
            )

        # Check if user is trying to buy an unsupported crypto
        unsupported_crypto = self._detect_unsupported_crypto(message)
        if unsupported_crypto:
            logger.info(
                f"[BUY_DEBUG] User requested unsupported crypto: {unsupported_crypto}"
            )
            msgs = BUY_FLOW_MESSAGES.get(language, BUY_FLOW_MESSAGES["en"])
            return BuyHandlerResult(
                content=msgs["usdc_only"].format(crypto=unsupported_crypto),
                wallet_address=wallet_address,
                supported_assets=["USDC"],
                supported_networks=self.SUPPORTED_NETWORKS,
                requires_privy_modal=False,
                latency_ms=int((time.time() - start_time) * 1000),
                language=language,
                pending_action="buy_awaiting_amount",  # Ready to accept amount for USDC
                metadata={
                    "crypto_currency": "USDC",
                    "requested_crypto": unsupported_crypto,
                },
            )

        # Try to extract info from initial message
        buy_info = BuyInfo()
        buy_info.crypto_currency = "USDC"  # Always USDC

        # Try to extract amount
        amount = self._parse_amount(message)
        if amount:
            buy_info.amount = amount

        # Process the flow with extracted info
        result = await self.process_buy_flow(buy_info, language, wallet_address)
        result.latency_ms = int((time.time() - start_time) * 1000)
        return result
