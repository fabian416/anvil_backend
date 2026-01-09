"""
Buy Handler for Chat - On-ramp crypto purchase operations.

Provides information for buying crypto with fiat via Privy on-ramp:
- MoonPay/Coinbase integration (via Privy)
- Supported assets and networks
- Frontend-triggered flow (Privy modal)

Note: The actual on-ramp flow is handled by Privy SDK on the frontend.
This handler provides instructional content and signals the frontend
to open the Privy funding modal.
"""

import time
from dataclasses import dataclass
from typing import Optional

from app.domain.ports.wallet.wallet_repository import WalletRepository
from app.domain.enums.wallet_provider import WalletProvider
from app.domain.value_objects.user_id import UserId


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

    def __init__(self, wallet_repository: WalletRepository):
        """
        Initialize buy handler.

        Args:
            wallet_repository: Repository for wallet data
        """
        self._wallet_repo = wallet_repository

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
            # Get user's wallet to display address
            wallets = await self._wallet_repo.get_by_user_id(UserId(user_id))
            
            # Log for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f"BuyHandler: Found {len(wallets)} wallets for user {user_id}")

            # Filter to EVM wallets only
            evm_wallets = [
                w for w in wallets
                if w.address.startswith("0x")
            ]
            
            logger.debug(f"BuyHandler: Found {len(evm_wallets)} EVM wallets for user {user_id}")

            # Prefer PRIVY provider
            wallet = next(
                (w for w in evm_wallets if getattr(w, "provider", None) == WalletProvider.PRIVY),
                None,
            )
            if wallet is None and evm_wallets:
                wallet = evm_wallets[0]
            if wallet is None and wallets:
                wallet = wallets[0]

            latency_ms = int((time.time() - start_time) * 1000)

            if not wallet:
                logger.warning(f"BuyHandler: No wallet found for user {user_id} (checked {len(wallets)} wallets)")
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
                wallet_address=wallet.address,
                msgs=msgs,
            )

            return BuyHandlerResult(
                content=content,
                wallet_address=wallet.address,
                supported_assets=self.SUPPORTED_ASSETS,
                supported_networks=self.SUPPORTED_NETWORKS,
                requires_privy_modal=True,
                latency_ms=latency_ms,
                language=lang,
            )

        except Exception as e:
            # Log the error for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Error getting wallet for user {user_id} in buy handler: {e}", exc_info=True)
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            # Provide user-friendly error message instead of technical error
            # Check if it's a database error
            from app.infrastructure.exceptions.gateway import DataMapperError
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
        """Format buy info as chat response."""
        assets_list = ", ".join(self.SUPPORTED_ASSETS)
        networks_list = ", ".join(self.SUPPORTED_NETWORKS)

        response = f"""{msgs["title"]}

{msgs["description"]}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**{msgs["supported_assets"]}:**
{assets_list}

**{msgs["supported_networks"]}:**
{networks_list}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**{msgs["how_to_buy"]}:**
1. {msgs["step_1"]}
2. {msgs["step_2"]}
3. {msgs["step_3"]}
4. {msgs["step_4"]}

💡 **{msgs["note_title"]}:** {msgs["note_content"]}

📬 **Deposit Address:** `{wallet_address}`
"""
        return response

