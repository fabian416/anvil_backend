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
                "command": "Lending & Yield",
                "description": "Supply assets to earn yield, borrow against collateral, and manage lending positions via Morpho and Aave",
                "examples": [
                    "Check my lending position",
                    "What's my health factor",
                    "Supply 1000 USDC to Morpho",
                    "Deposit ETH to earn yield",
                    "Borrow 5000 USDC",
                    "Show my lending positions",
                    "Best yield for USDC",
                    "Compare lending rates",
                    "Loop ETH for leverage",
                    "Am I at risk of liquidation",
                    "Show best lending vaults",
                    "Where should I lend my USDC",
                    "Morpho vs Aave rates",
                ],
                "icon": "🏦",
            },
            {
                "intent": "money_market",
                "command": "Compare Rates",
                "description": "Compare lending and borrowing rates across Aave V3 and Compound V3 protocols with real-time data",
                "examples": [
                    "Compare USDC rates on Base",
                    "Show me best USDC lending rates",
                    "What are Aave rates for ETH",
                    "Compare Aave vs Compound for USDC",
                    "Best protocol to lend USDC",
                    "Compare lending rates for ETH",
                    "Where should I lend 10,000 USDC",
                    "USDC rates comparison",
                    "Best money market rates",
                    "Compare rates on Base",
                ],
                "icon": "📊",
            },
            {
                "intent": "swap",
                "command": "Swap",
                "description": "Swap 440+ tokens via Hyperliquid Spot (PURR, TRUMP, PEPE + USDC pairs)",
                "examples": [
                    "Swap 100 USDC to PURR",
                    "Swap 50 USDC to TRUMP",
                    "Swap 1000 USDC to PEPE",
                    "Swap PURR to USDC",
                    "Swap TRUMP to USDC",
                    "Swap 200 USDC to HFUN",
                    "Swap 500 USDC to MOG",
                    "Swap PEPE to USDC",
                ],
                "icon": "🔄",
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
                "command": "Préstamos y Rendimiento",
                "description": "Suministrar activos para ganar rendimiento, pedir prestado contra colateral y gestionar posiciones de préstamo vía Morpho y Aave",
                "examples": [
                    "Verificar mi posición de préstamo",
                    "Cuál es mi factor de salud",
                    "Suministrar 1000 USDC a Morpho",
                    "Depositar ETH para ganar rendimiento",
                    "Pedir prestado 5000 USDC",
                    "Mostrar mis posiciones de préstamo",
                    "Mejor rendimiento para USDC",
                    "Comparar tasas de préstamo",
                    "Apalancar mi ETH",
                    "Estoy en riesgo de liquidación",
                    "Mostrar mejores bóvedas de préstamo",
                    "Dónde debería prestar mi USDC",
                    "Tasas Morpho vs Aave",
                ],
                "icon": "🏦",
            },
            {
                "intent": "money_market",
                "command": "Comparar Tasas",
                "description": "Comparar tasas de préstamo y préstamo entre protocolos Aave V3 y Compound V3 con datos en tiempo real",
                "examples": [
                    "Comparar tasas de USDC en Base",
                    "Muéstrame las mejores tasas de préstamo USDC",
                    "Cuáles son las tasas de Aave para ETH",
                    "Comparar Aave vs Compound para USDC",
                    "Mejor protocolo para prestar USDC",
                    "Comparar tasas de préstamo para ETH",
                    "Dónde debería prestar 10,000 USDC",
                    "Comparación de tasas USDC",
                    "Mejores tasas de mercado de dinero",
                    "Comparar tasas en Base",
                ],
                "icon": "📊",
            },
            {
                "intent": "swap",
                "command": "Intercambiar",
                "description": "Intercambiar 440+ tokens vía Hyperliquid Spot (PURR, TRUMP, PEPE + pares USDC)",
                "examples": [
                    "Cambiar 100 USDC a PURR",
                    "Cambiar 50 USDC a TRUMP",
                    "Cambiar 1000 USDC a PEPE",
                    "Cambiar PURR a USDC",
                    "Cambiar TRUMP a USDC",
                    "Cambiar 200 USDC a HFUN",
                    "Cambiar 500 USDC a MOG",
                    "Cambiar PEPE a USDC",
                ],
                "icon": "🔄",
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
                "command": "Prêts et Rendement",
                "description": "Fournir des actifs pour gagner un rendement, emprunter contre garantie et gérer les positions de prêt via Morpho et Aave",
                "examples": [
                    "Vérifier ma position de prêt",
                    "Quel est mon facteur de santé",
                    "Fournir 1000 USDC à Morpho",
                    "Déposer ETH pour gagner un rendement",
                    "Emprunter 5000 USDC",
                    "Afficher mes positions de prêt",
                    "Meilleur rendement pour USDC",
                    "Comparer les taux de prêt",
                    "Effet de levier sur mon ETH",
                    "Suis-je à risque de liquidation",
                    "Afficher les meilleurs coffres",
                    "Où devrais-je prêter mon USDC",
                    "Taux Morpho vs Aave",
                ],
                "icon": "🏦",
            },
            {
                "intent": "money_market",
                "command": "Comparer les Taux",
                "description": "Comparer les taux de prêt et d'emprunt entre les protocoles Aave V3 et Compound V3 avec des données en temps réel",
                "examples": [
                    "Comparer les taux USDC sur Base",
                    "Montre-moi les meilleurs taux de prêt USDC",
                    "Quels sont les taux Aave pour ETH",
                    "Comparer Aave vs Compound pour USDC",
                    "Meilleur protocole pour prêter USDC",
                    "Comparer les taux de prêt pour ETH",
                    "Où devrais-je prêter 10,000 USDC",
                    "Comparaison des taux USDC",
                    "Meilleurs taux du marché monétaire",
                    "Comparer les taux sur Base",
                ],
                "icon": "📊",
            },
            {
                "intent": "swap",
                "command": "Échanger",
                "description": "Échanger 440+ tokens via Hyperliquid Spot (PURR, TRUMP, PEPE + paires USDC)",
                "examples": [
                    "Échanger 100 USDC contre PURR",
                    "Échanger 50 USDC contre TRUMP",
                    "Échanger 1000 USDC contre PEPE",
                    "Échanger PURR contre USDC",
                    "Échanger TRUMP contre USDC",
                    "Échanger 200 USDC contre HFUN",
                    "Échanger 500 USDC contre MOG",
                    "Échanger PEPE contre USDC",
                ],
                "icon": "🔄",
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
                "command": "借贷与收益",
                "description": "通过Morpho和Aave供应资产赚取收益、抵押借贷和管理借贷仓位",
                "examples": [
                    "检查我的借贷仓位",
                    "我的健康因子是多少",
                    "向Morpho供应1000 USDC",
                    "存入ETH赚取收益",
                    "借入5000 USDC",
                    "显示我的借贷仓位",
                    "USDC的最佳收益",
                    "比较借贷利率",
                    "循环ETH获得杠杆",
                    "我有清算风险吗",
                    "显示最佳借贷金库",
                    "我应该在哪里借出USDC",
                    "Morpho vs Aave利率",
                ],
                "icon": "🏦",
            },
            {
                "intent": "money_market",
                "command": "比较利率",
                "description": "实时比较Aave V3和Compound V3协议的借贷和借款利率",
                "examples": [
                    "比较Base上的USDC利率",
                    "显示USDC最佳借贷利率",
                    "Aave的ETH利率是多少",
                    "比较USDC的Aave vs Compound",
                    "最佳USDC借贷协议",
                    "比较ETH的借贷利率",
                    "我应该在哪里借出10,000 USDC",
                    "USDC利率比较",
                    "最佳货币市场利率",
                    "比较Base上的利率",
                ],
                "icon": "📊",
            },
            {
                "intent": "swap",
                "command": "交换",
                "description": "通过Hyperliquid Spot交换meme代币 (PURR, TRUMP, PEPE + USDC交易对)",
                "examples": [
                    "将100 USDC换成PURR",
                    "将50 USDC换成TRUMP",
                    "将1000 USDC换成PEPE",
                    "将PURR换成USDC",
                    "将TRUMP换成USDC",
                    "将200 USDC换成HFUN",
                    "将500 USDC换成MOG",
                    "将PEPE换成USDC",
                ],
                "icon": "🔄",
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
                "command": "Empréstimos e Rendimento",
                "description": "Fornecer ativos para ganhar rendimento, emprestar contra garantia e gerenciar posições de empréstimo via Morpho e Aave",
                "examples": [
                    "Verificar minha posição de empréstimo",
                    "Qual é meu fator de saúde",
                    "Fornecer 1000 USDC ao Morpho",
                    "Depositar ETH para ganhar rendimento",
                    "Emprestar 5000 USDC",
                    "Mostrar minhas posições de empréstimo",
                    "Melhor rendimento para USDC",
                    "Comparar taxas de empréstimo",
                    "Alavancar meu ETH",
                    "Estou em risco de liquidação",
                    "Mostrar melhores cofres de empréstimo",
                    "Onde devo emprestar meu USDC",
                    "Taxas Morpho vs Aave",
                ],
                "icon": "🏦",
            },
            {
                "intent": "money_market",
                "command": "Comparar Taxas",
                "description": "Comparar taxas de empréstimo e empréstimo entre protocolos Aave V3 e Compound V3 com dados em tempo real",
                "examples": [
                    "Comparar taxas de USDC na Base",
                    "Mostre-me as melhores taxas de empréstimo USDC",
                    "Quais são as taxas da Aave para ETH",
                    "Comparar Aave vs Compound para USDC",
                    "Melhor protocolo para emprestar USDC",
                    "Comparar taxas de empréstimo para ETH",
                    "Onde devo emprestar 10,000 USDC",
                    "Comparação de taxas USDC",
                    "Melhores taxas de mercado monetário",
                    "Comparar taxas na Base",
                ],
                "icon": "📊",
            },
            {
                "intent": "swap",
                "command": "Trocar",
                "description": "Trocar 440+ tokens via Hyperliquid Spot (PURR, TRUMP, PEPE + pares USDC)",
                "examples": [
                    "Trocar 100 USDC por PURR",
                    "Trocar 50 USDC por TRUMP",
                    "Trocar 1000 USDC por PEPE",
                    "Trocar PURR por USDC",
                    "Trocar TRUMP por USDC",
                    "Trocar 200 USDC por HFUN",
                    "Trocar 500 USDC por MOG",
                    "Trocar PEPE por USDC",
                ],
                "icon": "🔄",
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
