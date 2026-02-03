"""
Internationalization (i18n) for chat responses.

Provides localized response templates for DeFi shortcut handlers.
Supports: English (en), Spanish (es), French (fr), Mandarin (zh), Portuguese (pt).
"""

from typing import Optional


# Language names
LANGUAGE_NAMES = {
    "en": "English",
    "es": "Español",
    "fr": "Français",
    "zh": "中文",
    "pt": "Português",
}

# Response translations
TRANSLATIONS = {
    # Lending Handler translations
    "lending": {
        "title": {
            "en": "{asset} MORPHO VAULTS ON {chain}",
            "es": "BÓVEDAS MORPHO DE {asset} EN {chain}",
            "fr": "COFFRES MORPHO {asset} SUR {chain}",
            "zh": "{chain} 上的 {asset} MORPHO 金库",
            "pt": "COFRES MORPHO DE {asset} EM {chain}",
        },
        "top_vaults": {
            "en": "Top {count} vaults by APY (Morpho Protocol):",
            "es": "Top {count} bóvedas por APY (Protocolo Morpho):",
            "fr": "Top {count} coffres par APY (Protocole Morpho):",
            "zh": "按 APY 排名前 {count} 金库 (Morpho 协议):",
            "pt": "Top {count} cofres por APY (Protocolo Morpho):",
        },
        "no_vaults": {
            "en": "No {asset} Vaults Found on {chain}",
            "es": "No se encontraron bóvedas de {asset} en {chain}",
            "fr": "Aucun coffre {asset} trouvé sur {chain}",
            "zh": "在 {chain} 上未找到 {asset} 金库",
            "pt": "Nenhum cofre {asset} encontrado em {chain}",
        },
        "recommendation": {
            "en": "RECOMMENDATION",
            "es": "RECOMENDACIÓN",
            "fr": "RECOMMANDATION",
            "zh": "推荐",
            "pt": "RECOMENDAÇÃO",
        },
        "best_vault": {
            "en": "Best Vault",
            "es": "Mejor Bóveda",
            "fr": "Meilleur Coffre",
            "zh": "最佳金库",
            "pt": "Melhor Cofre",
        },
        "how_to_deposit": {
            "en": "How to Deposit",
            "es": "Cómo Depositar",
            "fr": "Comment Déposer",
            "zh": "如何存款",
            "pt": "Como Depositar",
        },
        "risk_level": {
            "en": "Risk Level",
            "es": "Nivel de Riesgo",
            "fr": "Niveau de Risque",
            "zh": "风险等级",
            "pt": "Nível de Risco",
        },
        "curated": {
            "en": "Curated",
            "es": "Curado",
            "fr": "Vérifié",
            "zh": "精选",
            "pt": "Curado",
        },
        "low": {
            "en": "Low",
            "es": "Bajo",
            "fr": "Faible",
            "zh": "低",
            "pt": "Baixo",
        },
        "medium": {
            "en": "Medium",
            "es": "Medio",
            "fr": "Moyen",
            "zh": "中",
            "pt": "Médio",
        },
    },
    # Money Market Handler translations
    "money_market": {
        "title": {
            "en": "Money Market Comparison - {asset}",
            "es": "Comparación de Mercado Monetario - {asset}",
            "fr": "Comparaison du Marché Monétaire - {asset}",
            "zh": "货币市场对比 - {asset}",
            "pt": "Comparação do Mercado Monetário - {asset}",
        },
        "comparing": {
            "en": "Comparing Aave & Compound rates on {chain}:",
            "es": "Comparando tasas de Aave y Compound en {chain}:",
            "fr": "Comparaison des taux Aave & Compound sur {chain}:",
            "zh": "在 {chain} 上比较 Aave 和 Compound 利率:",
            "pt": "Comparando taxas Aave & Compound em {chain}:",
        },
        "protocol": {
            "en": "Protocol",
            "es": "Protocolo",
            "fr": "Protocole",
            "zh": "协议",
            "pt": "Protocolo",
        },
        "supply_apy": {
            "en": "Supply APY",
            "es": "APY de Suministro",
            "fr": "APY d'Approvisionnement",
            "zh": "供应 APY",
            "pt": "APY de Fornecimento",
        },
        "borrow_apy": {
            "en": "Borrow APY",
            "es": "APY de Préstamo",
            "fr": "APY d'Emprunt",
            "zh": "借贷 APY",
            "pt": "APY de Empréstimo",
        },
        "best_supply": {
            "en": "Best Supply Rate",
            "es": "Mejor Tasa de Suministro",
            "fr": "Meilleur Taux d'Approvisionnement",
            "zh": "最佳供应利率",
            "pt": "Melhor Taxa de Fornecimento",
        },
        "best_borrow": {
            "en": "Best Borrow Rate",
            "es": "Mejor Tasa de Préstamo",
            "fr": "Meilleur Taux d'Emprunt",
            "zh": "最佳借贷利率",
            "pt": "Melhor Taxa de Empréstimo",
        },
        "real_time": {
            "en": "Real-time",
            "es": "Tiempo real",
            "fr": "Temps réel",
            "zh": "实时",
            "pt": "Tempo real",
        },
        "estimated": {
            "en": "Estimated",
            "es": "Estimado",
            "fr": "Estimé",
            "zh": "估计",
            "pt": "Estimado",
        },
        "tip_morpho": {
            "en": 'For higher yields on stablecoins, try: "deposit USDC on Morpho"',
            "es": 'Para mayores rendimientos en stablecoins, prueba: "depositar USDC en Morpho"',
            "fr": 'Pour des rendements plus élevés sur les stablecoins, essayez: "déposer USDC sur Morpho"',
            "zh": '要获得更高的稳定币收益，请尝试: "在 Morpho 存入 USDC"',
            "pt": 'Para maiores rendimentos em stablecoins, tente: "depositar USDC no Morpho"',
        },
    },
    # Swap Handler translations
    "swap": {
        "title": {
            "en": "Swap Quote on {chain}",
            "es": "Cotización de Intercambio en {chain}",
            "fr": "Devis d'Échange sur {chain}",
            "zh": "{chain} 上的交换报价",
            "pt": "Cotação de Troca em {chain}",
        },
        "cross_chain": {
            "en": "Cross-Chain Swap",
            "es": "Intercambio Cross-Chain",
            "fr": "Échange Cross-Chain",
            "zh": "跨链交换",
            "pt": "Troca Cross-Chain",
        },
        "details": {
            "en": "DETAILS",
            "es": "DETALLES",
            "fr": "DÉTAILS",
            "zh": "详情",
            "pt": "DETALHES",
        },
        "rate": {
            "en": "Rate",
            "es": "Tasa",
            "fr": "Taux",
            "zh": "汇率",
            "pt": "Taxa",
        },
        "price_impact": {
            "en": "Price Impact",
            "es": "Impacto de Precio",
            "fr": "Impact sur le Prix",
            "zh": "价格影响",
            "pt": "Impacto no Preço",
        },
        "estimated_gas": {
            "en": "Estimated Gas",
            "es": "Gas Estimado",
            "fr": "Gas Estimé",
            "zh": "预估 Gas",
            "pt": "Gas Estimado",
        },
        "aggregator": {
            "en": "Aggregator",
            "es": "Agregador",
            "fr": "Agrégateur",
            "zh": "聚合器",
            "pt": "Agregador",
        },
        "confirm_swap": {
            "en": "Review the swap details above.",
            "es": "Revisa los detalles del intercambio.",
            "fr": "Vérifiez les détails de l'échange.",
            "zh": "查看上方的交换详情。",
            "pt": "Revise os detalhes da troca.",
        },
        "slippage": {
            "en": "Slippage",
            "es": "Deslizamiento",
            "fr": "Glissement",
            "zh": "滑点",
            "pt": "Deslizamento",
        },
    },
    # Portfolio Handler translations
    "portfolio": {
        "title": {
            "en": "Your Portfolio",
            "es": "Tu Portafolio",
            "fr": "Votre Portefeuille",
            "zh": "您的投资组合",
            "pt": "Seu Portfólio",
        },
        "total_value": {
            "en": "Total Value",
            "es": "Valor Total",
            "fr": "Valeur Totale",
            "zh": "总价值",
            "pt": "Valor Total",
        },
        "token_holdings": {
            "en": "Token Holdings",
            "es": "Tenencias de Tokens",
            "fr": "Avoirs en Tokens",
            "zh": "代币持仓",
            "pt": "Holdings de Tokens",
        },
        "chain": {
            "en": "Chain",
            "es": "Cadena",
            "fr": "Chaîne",
            "zh": "链",
            "pt": "Rede",
        },
        "no_holdings": {
            "en": "No token holdings found",
            "es": "No se encontraron tenencias de tokens",
            "fr": "Aucun avoir en tokens trouvé",
            "zh": "未找到代币持仓",
            "pt": "Nenhum holding de tokens encontrado",
        },
    },
    # Balance Handler translations
    "balance": {
        "title": {
            "en": "Your Balance",
            "es": "Tu Saldo",
            "fr": "Votre Solde",
            "zh": "您的余额",
            "pt": "Seu Saldo",
        },
        "total_usd": {
            "en": "Total in USD",
            "es": "Total en USD",
            "fr": "Total en USD",
            "zh": "美元总额",
            "pt": "Total em USD",
        },
    },
    # Activity Handler translations
    "activity": {
        "title": {
            "en": "Transaction History",
            "es": "Historial de Transacciones",
            "fr": "Historique des Transactions",
            "zh": "交易历史",
            "pt": "Histórico de Transações",
        },
        "recent": {
            "en": "Recent Transactions",
            "es": "Transacciones Recientes",
            "fr": "Transactions Récentes",
            "zh": "最近交易",
            "pt": "Transações Recentes",
        },
        "no_transactions": {
            "en": "No transactions found",
            "es": "No se encontraron transacciones",
            "fr": "Aucune transaction trouvée",
            "zh": "未找到交易",
            "pt": "Nenhuma transação encontrada",
        },
        "type": {
            "en": "Type",
            "es": "Tipo",
            "fr": "Type",
            "zh": "类型",
            "pt": "Tipo",
        },
        "amount": {
            "en": "Amount",
            "es": "Monto",
            "fr": "Montant",
            "zh": "金额",
            "pt": "Valor",
        },
        "date": {
            "en": "Date",
            "es": "Fecha",
            "fr": "Date",
            "zh": "日期",
            "pt": "Data",
        },
    },
    # Receive Handler translations
    "receive": {
        "title": {
            "en": "Receive Crypto",
            "es": "Recibir Cripto",
            "fr": "Recevoir des Cryptos",
            "zh": "接收加密货币",
            "pt": "Receber Cripto",
        },
        "your_address": {
            "en": "Your Wallet Address",
            "es": "Tu Dirección de Billetera",
            "fr": "Votre Adresse de Portefeuille",
            "zh": "您的钱包地址",
            "pt": "Seu Endereço de Carteira",
        },
        "copy_address": {
            "en": "Copy this address to receive tokens",
            "es": "Copia esta dirección para recibir tokens",
            "fr": "Copiez cette adresse pour recevoir des tokens",
            "zh": "复制此地址以接收代币",
            "pt": "Copie este endereço para receber tokens",
        },
        "qr_code": {
            "en": "QR Code",
            "es": "Código QR",
            "fr": "Code QR",
            "zh": "二维码",
            "pt": "Código QR",
        },
        "ens_handle": {
            "en": "ENS Handle",
            "es": "Handle ENS",
            "fr": "Identifiant ENS",
            "zh": "ENS 域名",
            "pt": "Handle ENS",
        },
        "chains_supported": {
            "en": "Supported Chains",
            "es": "Cadenas Soportadas",
            "fr": "Chaînes Supportées",
            "zh": "支持的链",
            "pt": "Redes Suportadas",
        },
    },
    # Common translations
    "common": {
        "error": {
            "en": "Error",
            "es": "Error",
            "fr": "Erreur",
            "zh": "错误",
            "pt": "Erro",
        },
        "loading": {
            "en": "Loading...",
            "es": "Cargando...",
            "fr": "Chargement...",
            "zh": "加载中...",
            "pt": "Carregando...",
        },
        "try_again": {
            "en": "Please try again",
            "es": "Por favor intenta de nuevo",
            "fr": "Veuillez réessayer",
            "zh": "请重试",
            "pt": "Por favor tente novamente",
        },
        "not_found": {
            "en": "Not found",
            "es": "No encontrado",
            "fr": "Non trouvé",
            "zh": "未找到",
            "pt": "Não encontrado",
        },
    },
}


def get_translation(
    category: str,
    key: str,
    language: str = "en",
    **kwargs,
) -> str:
    """
    Get a translated string.

    Args:
        category: Category of the translation (lending, swap, etc.)
        key: Key for the specific translation
        language: Language code (en, es, fr, zh, pt)
        **kwargs: Format arguments for the string

    Returns:
        Translated string, or English fallback if not found
    """
    # Default to English if language not supported
    if language not in LANGUAGE_NAMES:
        language = "en"

    # Get category translations
    category_translations = TRANSLATIONS.get(category, {})
    if not category_translations:
        return f"[Missing category: {category}]"

    # Get key translations
    key_translations = category_translations.get(key, {})
    if not key_translations:
        return f"[Missing key: {category}.{key}]"

    # Get translation for language (fallback to English)
    translation = key_translations.get(language) or key_translations.get("en", "")

    # Format with kwargs
    if kwargs:
        try:
            return translation.format(**kwargs)
        except KeyError:
            return translation

    return translation


def t(category: str, key: str, language: str = "en", **kwargs) -> str:
    """Shorthand for get_translation."""
    return get_translation(category, key, language, **kwargs)
