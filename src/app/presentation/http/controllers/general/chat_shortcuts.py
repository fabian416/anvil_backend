"""
Public Chat Shortcuts Endpoint.

Provides localized shortcut commands for DeFi chat intents.
Supports: English, Spanish, French, Mandarin, Portuguese.

No authentication required - public endpoint.
"""

from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Optional


# Supported languages
SUPPORTED_LANGUAGES = ["en", "es", "fr", "zh", "pt"]
DEFAULT_LANGUAGE = "en"


class ShortcutCommand(BaseModel):
    """A single shortcut command."""

    intent: str
    command: str
    description: str
    examples: list[str]
    icon: str


class ChatShortcutsResponse(BaseModel):
    """Response containing all chat shortcuts."""

    language: str
    language_name: str
    shortcuts: list[ShortcutCommand]


# Shortcuts data by language
SHORTCUTS_DATA = {
    "en": {
        "language_name": "English",
        "shortcuts": [
            {
                "intent": "lending",
                "command": "Lend",
                "description": "Deposit into Morpho vaults for yield",
                "examples": [
                    "Deposit USDC on Morpho",
                    "Show best lending vaults",
                    "Earn yield on my ETH",
                    "Best lending vaults",
                    "Lending vaults",
                    "Earn yield",
                ],
                "icon": "🏦",
            },
            {
                "intent": "money_market",
                "command": "Compare Rates",
                "description": "Compare Aave and Compound lending rates",
                "examples": [
                    "Compare Aave vs Compound",
                    "Best money market rates for USDC",
                    "Compare lending rates for ETH",
                ],
                "icon": "📊",
            },
            {
                "intent": "swap",
                "command": "Swap",
                "description": "Exchange tokens via 1inch, LiFi, or Hyperliquid",
                "examples": [
                    "Swap 100 USDC for ETH",
                    "Swap USDC from Ethereum to Base",
                    "Best swap rate for ETH to USDC",
                ],
                "icon": "🔄",
            },
            {
                "intent": "swap_moonpay",
                "command": "MoonPay Swap",
                "description": "Quick crypto-to-crypto swap via MoonPay (BTC, ETH, SOL, USDC)",
                "examples": [
                    "Swap BTC to ETH",
                    "Exchange 0.5 ETH for USDC",
                    "Convert SOL to BTC",
                    "Swap 100 USDC to SOL",
                ],
                "icon": "🌙",
            },
            {
                "intent": "portfolio",
                "command": "Portfolio",
                "description": "View all your token holdings",
                "examples": [
                    "Show my portfolio",
                    "What tokens do I have?",
                    "List my holdings",
                    "What tokens do I own?",
                    "Show my holdings",
                    "List my tokens",
                ],
                "icon": "💼",
            },
            {
                "intent": "balance",
                "command": "Balance",
                "description": "Check your wallet balance in USD",
                "examples": [
                    "What's my balance?",
                    "Check my balance",
                    "My balance",
                    "Show my balance",
                    "How much do I have?",
                    "Show my USDC balance",
                ],
                "icon": "💰",
            },
            {
                "intent": "activity",
                "command": "Activity",
                "description": "View your transaction history",
                "examples": [
                    "Show my transactions",
                    "Recent activity",
                    "What did I do today?",
                    "My activity",
                    "Transaction history",
                    "My trades",
                ],
                "icon": "📜",
            },
            {
                "intent": "receive",
                "command": "Receive",
                "description": "Get your wallet address or QR code",
                "examples": [
                    "I want to receive crypto",
                    "Receive crypto",
                    "My address",
                    "My wallet address",
                    "Deposit address",
                    "Receive address",
                    "Give me my QR code",
                ],
                "icon": "📥",
            },
            {
                "intent": "buy",
                "command": "Buy",
                "description": "Buy crypto with card or bank transfer",
                "examples": [
                    "I want to buy crypto",
                    "Buy Bitcoin with card",
                    "How to buy ETH",
                    "Buy crypto",
                    "Purchase Bitcoin",
                    "Buy with fiat",
                ],
                "icon": "💳",
            },
            {
                "intent": "send",
                "command": "Send",
                "description": "Send tokens to another wallet",
                "examples": [
                    "Send crypto to a friend",
                    "Transfer ETH to another wallet",
                    "I want to send USDC",
                    "Send tokens",
                    "Transfer crypto",
                    "Send to wallet",
                ],
                "icon": "📤",
            },
        ],
    },
    "es": {
        "language_name": "Español",
        "shortcuts": [
            {
                "intent": "lending",
                "command": "Prestar",
                "description": "Depositar en bóvedas Morpho para obtener rendimiento",
                "examples": [
                    "Depositar USDC en Morpho",
                    "Mostrar mejores bóvedas de préstamo",
                    "Ganar rendimiento con mi ETH",
                ],
                "icon": "🏦",
            },
            {
                "intent": "money_market",
                "command": "Comparar Tasas",
                "description": "Comparar tasas de préstamo entre Aave y Compound",
                "examples": [
                    "Comparar Aave vs Compound",
                    "Mejores tasas de mercado de dinero para USDC",
                    "Comparar tasas de préstamo para ETH",
                ],
                "icon": "📊",
            },
            {
                "intent": "swap",
                "command": "Intercambiar",
                "description": "Intercambiar tokens vía 1inch, LiFi o Hyperliquid",
                "examples": [
                    "Intercambiar 100 USDC por ETH",
                    "Cambiar USDC de Ethereum a Base",
                    "Mejor tasa para cambiar ETH a USDC",
                ],
                "icon": "🔄",
            },
            {
                "intent": "swap_moonpay",
                "command": "Swap MoonPay",
                "description": "Intercambio rápido cripto-a-cripto vía MoonPay (BTC, ETH, SOL, USDC)",
                "examples": [
                    "Cambiar BTC por ETH",
                    "Intercambiar 0.5 ETH por USDC",
                    "Convertir SOL a BTC",
                    "Cambiar 100 USDC por SOL",
                ],
                "icon": "🌙",
            },
            {
                "intent": "portfolio",
                "command": "Portafolio",
                "description": "Ver todos tus tokens",
                "examples": [
                    "Mostrar mi portafolio",
                    "¿Qué tokens tengo?",
                    "Listar mis activos",
                    "¿Qué tokens poseo?",
                    "Mostrar mis holdings",
                    "Listar mis tokens",
                ],
                "icon": "💼",
            },
            {
                "intent": "balance",
                "command": "Saldo",
                "description": "Consultar el saldo de tu billetera en USD",
                "examples": [
                    "¿Cuál es mi saldo?",
                    "¿Cuánto vale mi billetera?",
                    "Mostrar mi saldo en USDC",
                ],
                "icon": "💰",
            },
            {
                "intent": "activity",
                "command": "Actividad",
                "description": "Ver tu historial de transacciones",
                "examples": [
                    "Mostrar mis transacciones",
                    "Actividad reciente",
                    "¿Qué hice hoy?",
                    "Mi actividad",
                    "Historial de transacciones",
                    "Mis intercambios",
                ],
                "icon": "📜",
            },
            {
                "intent": "receive",
                "command": "Recibir",
                "description": "Obtener tu dirección de billetera o código QR",
                "examples": [
                    "Mostrar mi dirección",
                    "Quiero recibir cripto",
                    "Mi dirección de billetera",
                ],
                "icon": "📥",
            },
            {
                "intent": "buy",
                "command": "Comprar",
                "description": "Comprar cripto con tarjeta o transferencia bancaria",
                "examples": [
                    "Quiero comprar cripto",
                    "Comprar Bitcoin con tarjeta",
                    "Cómo comprar ETH",
                    "Comprar cripto",
                    "Comprar con tarjeta",
                    "Comprar con fiat",
                ],
                "icon": "💳",
            },
            {
                "intent": "send",
                "command": "Enviar",
                "description": "Enviar tokens a otra billetera",
                "examples": [
                    "Enviar cripto a un amigo",
                    "Transferir ETH a otra billetera",
                    "Quiero enviar USDC",
                    "Enviar tokens",
                    "Transferir cripto",
                    "Enviar a billetera",
                ],
                "icon": "📤",
            },
        ],
    },
    "fr": {
        "language_name": "Français",
        "shortcuts": [
            {
                "intent": "lending",
                "command": "Prêter",
                "description": "Déposer dans les coffres Morpho pour obtenir un rendement",
                "examples": [
                    "Déposer USDC sur Morpho",
                    "Afficher les meilleurs coffres",
                    "Gagner du rendement sur mon ETH",
                ],
                "icon": "🏦",
            },
            {
                "intent": "money_market",
                "command": "Comparer les Taux",
                "description": "Comparer les taux de prêt Aave et Compound",
                "examples": [
                    "Comparer Aave vs Compound",
                    "Meilleurs taux de marché monétaire pour USDC",
                    "Comparer les taux de prêt pour ETH",
                ],
                "icon": "📊",
            },
            {
                "intent": "swap",
                "command": "Échanger",
                "description": "Échanger des tokens via 1inch, LiFi ou Hyperliquid",
                "examples": [
                    "Échanger 100 USDC contre ETH",
                    "Échanger USDC d'Ethereum à Base",
                    "Meilleur taux pour échanger ETH vers USDC",
                ],
                "icon": "🔄",
            },
            {
                "intent": "swap_moonpay",
                "command": "Swap MoonPay",
                "description": "Échange rapide crypto-à-crypto via MoonPay (BTC, ETH, SOL, USDC)",
                "examples": [
                    "Échanger BTC contre ETH",
                    "Échanger 0.5 ETH contre USDC",
                    "Convertir SOL en BTC",
                    "Échanger 100 USDC contre SOL",
                ],
                "icon": "🌙",
            },
            {
                "intent": "portfolio",
                "command": "Portefeuille",
                "description": "Voir tous vos tokens",
                "examples": [
                    "Afficher mon portefeuille",
                    "Quels tokens ai-je?",
                    "Lister mes actifs",
                    "Quels tokens je possède?",
                    "Afficher mes actifs",
                    "Lister mes tokens",
                ],
                "icon": "💼",
            },
            {
                "intent": "balance",
                "command": "Solde",
                "description": "Vérifier le solde de votre portefeuille en USD",
                "examples": [
                    "Quel est mon solde?",
                    "Combien vaut mon portefeuille?",
                    "Afficher mon solde USDC",
                ],
                "icon": "💰",
            },
            {
                "intent": "activity",
                "command": "Activité",
                "description": "Voir votre historique de transactions",
                "examples": [
                    "Afficher mes transactions",
                    "Activité récente",
                    "Qu'ai-je fait aujourd'hui?",
                    "Mon activité",
                    "Historique de transactions",
                    "Mes échanges",
                ],
                "icon": "📜",
            },
            {
                "intent": "receive",
                "command": "Recevoir",
                "description": "Obtenir votre adresse de portefeuille ou code QR",
                "examples": [
                    "Afficher mon adresse",
                    "Je veux recevoir des cryptos",
                    "Mon adresse de portefeuille",
                ],
                "icon": "📥",
            },
            {
                "intent": "buy",
                "command": "Acheter",
                "description": "Acheter des cryptos par carte ou virement bancaire",
                "examples": [
                    "Je veux acheter des cryptos",
                    "Acheter Bitcoin par carte",
                    "Comment acheter ETH",
                    "Acheter des cryptos",
                    "Acheter par carte",
                    "Acheter avec fiat",
                ],
                "icon": "💳",
            },
            {
                "intent": "send",
                "command": "Envoyer",
                "description": "Envoyer des tokens vers un autre portefeuille",
                "examples": [
                    "Envoyer des cryptos à un ami",
                    "Transférer ETH vers un autre portefeuille",
                    "Je veux envoyer USDC",
                    "Envoyer des tokens",
                    "Transférer des cryptos",
                    "Envoyer au portefeuille",
                ],
                "icon": "📤",
            },
        ],
    },
    "zh": {
        "language_name": "中文",
        "shortcuts": [
            {
                "intent": "lending",
                "command": "借贷",
                "description": "存入Morpho金库获取收益",
                "examples": [
                    "在Morpho存入USDC",
                    "显示最佳借贷金库",
                    "用我的ETH赚取收益",
                ],
                "icon": "🏦",
            },
            {
                "intent": "money_market",
                "command": "比较利率",
                "description": "比较Aave和Compound的借贷利率",
                "examples": [
                    "比较Aave和Compound",
                    "USDC最佳货币市场利率",
                    "比较ETH的借贷利率",
                ],
                "icon": "📊",
            },
            {
                "intent": "swap",
                "command": "交换",
                "description": "通过1inch、LiFi或Hyperliquid交换代币",
                "examples": [
                    "将100 USDC换成ETH",
                    "交换USDC从以太坊到Base",
                    "ETH换USDC最佳汇率",
                ],
                "icon": "🔄",
            },
            {
                "intent": "swap_moonpay",
                "command": "MoonPay交换",
                "description": "通过MoonPay快速加密货币互换 (BTC, ETH, SOL, USDC)",
                "examples": [
                    "将BTC换成ETH",
                    "交换0.5 ETH换USDC",
                    "将SOL转换为BTC",
                    "交换100 USDC换SOL",
                ],
                "icon": "🌙",
            },
            {
                "intent": "portfolio",
                "command": "投资组合",
                "description": "查看您所有的代币持仓",
                "examples": [
                    "显示我的投资组合",
                    "我有哪些代币？",
                    "列出我的资产",
                    "我拥有哪些代币？",
                    "显示我的持仓",
                    "列出我的代币",
                ],
                "icon": "💼",
            },
            {
                "intent": "balance",
                "command": "余额",
                "description": "查看您的钱包余额（美元）",
                "examples": [
                    "我的余额是多少？",
                    "我的钱包价值多少？",
                    "显示我的USDC余额",
                ],
                "icon": "💰",
            },
            {
                "intent": "activity",
                "command": "活动",
                "description": "查看您的交易历史",
                "examples": [
                    "显示我的交易",
                    "最近活动",
                    "我今天做了什么？",
                    "我的活动",
                    "交易历史",
                    "我的交易",
                ],
                "icon": "📜",
            },
            {
                "intent": "receive",
                "command": "接收",
                "description": "获取您的钱包地址或二维码",
                "examples": [
                    "显示我的钱包地址",
                    "我想接收加密货币",
                    "我的钱包地址",
                ],
                "icon": "📥",
            },
            {
                "intent": "buy",
                "command": "购买",
                "description": "用卡或银行转账购买加密货币",
                "examples": [
                    "我想买加密货币",
                    "用卡购买比特币",
                    "如何购买ETH",
                    "购买加密货币",
                    "用卡购买",
                    "用法币购买",
                ],
                "icon": "💳",
            },
            {
                "intent": "send",
                "command": "发送",
                "description": "向另一个钱包发送代币",
                "examples": [
                    "发送加密货币给朋友",
                    "转账ETH到另一个钱包",
                    "我想发送USDC",
                    "发送代币",
                    "转账加密货币",
                    "发送到钱包",
                ],
                "icon": "📤",
            },
        ],
    },
    "pt": {
        "language_name": "Português",
        "shortcuts": [
            {
                "intent": "lending",
                "command": "Emprestar",
                "description": "Depositar em cofres Morpho para rendimento",
                "examples": [
                    "Depositar USDC no Morpho",
                    "Mostrar melhores cofres de empréstimo",
                    "Ganhar rendimento com meu ETH",
                ],
                "icon": "🏦",
            },
            {
                "intent": "money_market",
                "command": "Comparar Taxas",
                "description": "Comparar taxas de empréstimo entre Aave e Compound",
                "examples": [
                    "Comparar Aave vs Compound",
                    "Melhores taxas de mercado monetário para USDC",
                    "Comparar taxas de empréstimo para ETH",
                ],
                "icon": "📊",
            },
            {
                "intent": "swap",
                "command": "Trocar",
                "description": "Trocar tokens via 1inch, LiFi ou Hyperliquid",
                "examples": [
                    "Trocar 100 USDC por ETH",
                    "Trocar USDC de Ethereum para Base",
                    "Melhor taxa para trocar ETH por USDC",
                ],
                "icon": "🔄",
            },
            {
                "intent": "swap_moonpay",
                "command": "Swap MoonPay",
                "description": "Troca rápida cripto-a-cripto via MoonPay (BTC, ETH, SOL, USDC)",
                "examples": [
                    "Trocar BTC por ETH",
                    "Trocar 0.5 ETH por USDC",
                    "Converter SOL para BTC",
                    "Trocar 100 USDC por SOL",
                ],
                "icon": "🌙",
            },
            {
                "intent": "portfolio",
                "command": "Portfólio",
                "description": "Ver todos os seus tokens",
                "examples": [
                    "Mostrar meu portfólio",
                    "Quais tokens eu tenho?",
                    "Listar meus ativos",
                    "Quais tokens eu possuo?",
                    "Mostrar meus holdings",
                    "Listar meus tokens",
                ],
                "icon": "💼",
            },
            {
                "intent": "balance",
                "command": "Saldo",
                "description": "Verificar o saldo da sua carteira em USD",
                "examples": [
                    "Qual é meu saldo?",
                    "Quanto vale minha carteira?",
                    "Mostrar meu saldo em USDC",
                ],
                "icon": "💰",
            },
            {
                "intent": "activity",
                "command": "Atividade",
                "description": "Ver seu histórico de transações",
                "examples": [
                    "Mostrar minhas transações",
                    "Atividade recente",
                    "O que eu fiz hoje?",
                    "Minha atividade",
                    "Histórico de transações",
                    "Minhas transações",
                ],
                "icon": "📜",
            },
            {
                "intent": "receive",
                "command": "Receber",
                "description": "Obter seu endereço de carteira ou código QR",
                "examples": [
                    "Mostrar meu endereço",
                    "Quero receber cripto",
                    "Meu endereço de carteira",
                ],
                "icon": "📥",
            },
            {
                "intent": "buy",
                "command": "Comprar",
                "description": "Comprar cripto com cartão ou transferência bancária",
                "examples": [
                    "Quero comprar cripto",
                    "Comprar Bitcoin com cartão",
                    "Como comprar ETH",
                    "Comprar cripto",
                    "Comprar com cartão",
                    "Comprar com fiat",
                ],
                "icon": "💳",
            },
            {
                "intent": "send",
                "command": "Enviar",
                "description": "Enviar tokens para outra carteira",
                "examples": [
                    "Enviar cripto para um amigo",
                    "Transferir ETH para outra carteira",
                    "Quero enviar USDC",
                    "Enviar tokens",
                    "Transferir cripto",
                    "Enviar para carteira",
                ],
                "icon": "📤",
            },
        ],
    },
}


def create_chat_shortcuts_router() -> APIRouter:
    """Create router for public chat shortcuts endpoint."""
    router = APIRouter(prefix="/chat", tags=["Chat Shortcuts"])

    @router.get(
        "/shortcuts",
        response_model=ChatShortcutsResponse,
        summary="Get chat shortcuts",
        description="Get localized chat shortcut commands for DeFi operations. "
        "Supports: English (en), Spanish (es), French (fr), Mandarin (zh), Portuguese (pt).",
    )
    async def get_chat_shortcuts(
        lang: Optional[str] = Query(
            default="en",
            description="Language code: en, es, fr, zh, pt",
            pattern="^(en|es|fr|zh|pt)$",
        ),
    ) -> ChatShortcutsResponse:
        """
        Get chat shortcuts in the specified language.

        Returns a list of shortcut commands that users can use to interact
        with the DeFi chat features.

        **Available Languages:**
        - `en` - English (default)
        - `es` - Spanish (Español)
        - `fr` - French (Français)
        - `zh` - Mandarin (中文)
        - `pt` - Portuguese (Português)

        **Available Shortcuts:**
        - **Lend** - Deposit into Morpho vaults
        - **Compare Rates** - Compare Aave vs Compound
        - **Swap** - Exchange tokens (1inch, LiFi, Hyperliquid)
        - **Portfolio** - View token holdings
        - **Balance** - Check wallet balance
        - **Activity** - Transaction history
        - **Receive** - Get wallet address/QR
        """
        language = lang if lang in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE
        lang_data = SHORTCUTS_DATA[language]

        shortcuts = [
            ShortcutCommand(
                intent=s["intent"],
                command=s["command"],
                description=s["description"],
                examples=s["examples"],
                icon=s["icon"],
            )
            for s in lang_data["shortcuts"]
        ]

        return ChatShortcutsResponse(
            language=language,
            language_name=lang_data["language_name"],
            shortcuts=shortcuts,
        )

    @router.get(
        "/shortcuts/languages",
        summary="Get supported languages",
        description="Get list of supported languages for chat shortcuts.",
    )
    async def get_supported_languages() -> dict:
        """
        Get list of supported languages.

        Returns a dictionary of language codes and their names.
        """
        return {
            "languages": [
                {"code": code, "name": SHORTCUTS_DATA[code]["language_name"]}
                for code in SUPPORTED_LANGUAGES
            ],
            "default": DEFAULT_LANGUAGE,
        }

    return router
