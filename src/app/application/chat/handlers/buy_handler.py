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
    crypto_currency: str | None = None  # Crypto to buy (ETH, USDC, etc.)

    # Cryptos supported by MoonPay
    SUPPORTED_CRYPTOS: list[str] = field(
        default_factory=lambda: ["ETH", "USDC", "USDT", "BTC", "MATIC"]
    )

    @property
    def is_complete(self) -> bool:
        """Check if we have all required info."""
        return bool(self.amount and self.crypto_currency)

    @property
    def next_step(self) -> str | None:
        """Get the next step needed."""
        if not self.amount:
            return "amount"
        if not self.crypto_currency:
            return "crypto_currency"
        return None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "amount": self.amount,
            "fiat_currency": self.fiat_currency,
            "crypto_currency": self.crypto_currency,
            "is_complete": self.is_complete,
            "next_step": self.next_step,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BuyInfo":
        """Create from dictionary."""
        return cls(
            amount=data.get("amount"),
            fiat_currency=data.get("fiat_currency", "USD"),
            crypto_currency=data.get("crypto_currency"),
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


# Messages for multi-turn buy flow
BUY_FLOW_MESSAGES = {
    "en": {
        "ask_amount": "💵 How much would you like to buy?\n\nEnter an amount in USD (e.g., 50, 100, 500)\n\n💡 *Minimum purchase: $30*",
        "ask_crypto": "🪙 Which cryptocurrency would you like to buy?\n\n{options}\n\nReply with the number or name.",
        "confirm_buy": """✅ **Ready to buy {crypto_currency}**

💵 **Amount:** ${amount} USD
🪙 **Crypto:** {crypto_currency}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Click **Continue** to complete your purchase with MoonPay.""",
        "invalid_amount": "❌ Please enter a valid amount (minimum $30).\n\nExample: 50, 100, or 500",
        "invalid_crypto": "❌ Please select a valid cryptocurrency from the list.\n\n{options}",
    },
    "es": {
        "ask_amount": "💵 ¿Cuánto deseas comprar?\n\nIngresa un monto en USD (ej: 50, 100, 500)\n\n💡 *Compra mínima: $30*",
        "ask_crypto": "🪙 ¿Qué criptomoneda deseas comprar?\n\n{options}\n\nResponde con el número o nombre.",
        "confirm_buy": """✅ **Listo para comprar {crypto_currency}**

💵 **Monto:** ${amount} USD
🪙 **Crypto:** {crypto_currency}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Haz clic en **Continuar** para completar tu compra con MoonPay.""",
        "invalid_amount": "❌ Por favor ingresa un monto válido (mínimo $30).\n\nEjemplo: 50, 100, o 500",
        "invalid_crypto": "❌ Por favor selecciona una criptomoneda válida de la lista.\n\n{options}",
    },
    "pt": {
        "ask_amount": "💵 Quanto você gostaria de comprar?\n\nDigite um valor em USD (ex: 50, 100, 500)\n\n💡 *Compra mínima: $30*",
        "ask_crypto": "🪙 Qual criptomoeda você gostaria de comprar?\n\n{options}\n\nResponda com o número ou nome.",
        "confirm_buy": """✅ **Pronto para comprar {crypto_currency}**

💵 **Valor:** ${amount} USD
🪙 **Crypto:** {crypto_currency}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Clique em **Continuar** para completar sua compra com MoonPay.""",
        "invalid_amount": "❌ Por favor digite um valor válido (mínimo $30).\n\nExemplo: 50, 100, ou 500",
        "invalid_crypto": "❌ Por favor selecione uma criptomoeda válida da lista.\n\n{options}",
    },
    "zh": {
        "ask_amount": "💵 您想购买多少？\n\n输入美元金额（例如：50、100、500）\n\n💡 *最低购买金额：$30*",
        "ask_crypto": "🪙 您想购买哪种加密货币？\n\n{options}\n\n请回复数字或名称。",
        "confirm_buy": """✅ **准备购买 {crypto_currency}**

💵 **金额：** ${amount} USD
🪙 **加密货币：** {crypto_currency}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

点击 **继续** 使用 MoonPay 完成购买。""",
        "invalid_amount": "❌ 请输入有效金额（最低 $30）。\n\n示例：50、100 或 500",
        "invalid_crypto": "❌ 请从列表中选择有效的加密货币。\n\n{options}",
    },
    "fr": {
        "ask_amount": "💵 Combien souhaitez-vous acheter ?\n\nEntrez un montant en USD (ex: 50, 100, 500)\n\n💡 *Achat minimum : $30*",
        "ask_crypto": "🪙 Quelle cryptomonnaie souhaitez-vous acheter ?\n\n{options}\n\nRépondez avec le numéro ou le nom.",
        "confirm_buy": """✅ **Prêt à acheter {crypto_currency}**

💵 **Montant :** ${amount} USD
🪙 **Crypto :** {crypto_currency}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Cliquez sur **Continuer** pour finaliser votre achat avec MoonPay.""",
        "invalid_amount": "❌ Veuillez entrer un montant valide (minimum $30).\n\nExemple : 50, 100, ou 500",
        "invalid_crypto": "❌ Veuillez sélectionner une cryptomonnaie valide dans la liste.\n\n{options}",
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
            logger.debug(f"BuyHandler: Resolved wallet address for user {user_id}: {wallet_address[:10] + '...' if wallet_address else 'None'}")

            latency_ms = int((time.time() - start_time) * 1000)

            if not wallet_address:
                logger.warning(f"BuyHandler: No wallet found for user {user_id} after checking DB, Privy, and primary_wallet_address")
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
            logger.warning(f"Error getting wallet for user {user_id} in buy handler: {e}", exc_info=True)
            
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
        networks_list = "\n".join([f"• {network}" for network in self.SUPPORTED_NETWORKS])

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
        Extract crypto from user message.

        Args:
            message: User's message
            supported: List of supported cryptocurrencies

        Returns:
            Crypto symbol if found, None otherwise
        """
        message_upper = message.upper().strip()

        # Direct match
        if message_upper in supported:
            return message_upper

        # Number selection (1, 2, 3, etc.)
        if message.strip().isdigit():
            index = int(message.strip()) - 1
            if 0 <= index < len(supported):
                return supported[index]

        # Partial match
        for crypto in supported:
            if crypto in message_upper:
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
        Process the buy flow step by step.

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
        options = self._format_crypto_options(buy_info.SUPPORTED_CRYPTOS)

        # Step 1: Ask for amount
        if not buy_info.amount:
            logger.info(f"[BUY_DEBUG] Step 1: Asking for amount, pending_action=buy_awaiting_amount")
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

        # Step 2: Ask for crypto
        if not buy_info.crypto_currency:
            logger.info(f"[BUY_DEBUG] Step 2: Asking for crypto, pending_action=buy_awaiting_crypto")
            return BuyHandlerResult(
                content=msgs["ask_crypto"].format(options=options),
                wallet_address=wallet_address,
                supported_assets=buy_info.SUPPORTED_CRYPTOS,
                supported_networks=self.SUPPORTED_NETWORKS,
                requires_privy_modal=False,
                latency_ms=0,
                language=language,
                pending_action="buy_awaiting_crypto",
                metadata=buy_info.to_dict(),
            )

        # Step 3: All data collected - Generate execute_data
        logger.info(f"[BUY_DEBUG] Step 3: All data collected, generating execute_data")
        execute_data = {
            "action_type": "buy",
            "chain": "base",
            "from_token": buy_info.fiat_currency,
            "to_token": buy_info.crypto_currency,
            "amount": buy_info.amount,
        }
        logger.info(f"[BUY_DEBUG] execute_data: {execute_data}")

        return BuyHandlerResult(
            content=msgs["confirm_buy"].format(
                amount=buy_info.amount,
                crypto_currency=buy_info.crypto_currency,
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

        Args:
            user_id: User's database ID
            message: User's initial message
            language: Language code for messages

        Returns:
            BuyHandlerResult with first step or confirmation if all info provided
        """
        logger.info(f"[BUY_DEBUG] start_buy_flow() called with user_id={user_id}, message='{message}', language={language}")
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

        # Try to extract info from initial message
        buy_info = BuyInfo()

        # Try to extract amount
        amount = self._parse_amount(message)
        if amount:
            buy_info.amount = amount

        # Try to extract crypto
        crypto = self._parse_crypto(message, buy_info.SUPPORTED_CRYPTOS)
        if crypto:
            buy_info.crypto_currency = crypto

        # Process the flow with extracted info
        result = await self.process_buy_flow(buy_info, language, wallet_address)
        result.latency_ms = int((time.time() - start_time) * 1000)
        return result

