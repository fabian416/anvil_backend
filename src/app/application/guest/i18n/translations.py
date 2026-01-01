"""
Guest Chat i18n translations.

Multi-language support for guest chat responses.
Supports: English (en), Spanish (es), Portuguese (pt), Mandarin (zh).
"""


# ========================================
# Registration Required Messages
# ========================================

GUEST_REGISTRATION_MESSAGES: dict[str, dict[str, str]] = {
    "portfolio_access": {
        "en": "Create a free account to view your portfolio and track your DeFi positions.",
        "es": "Crea una cuenta gratuita para ver tu portafolio y rastrear tus posiciones DeFi.",
        "pt": "Crie uma conta gratuita para ver seu portfólio e rastrear suas posições DeFi.",
        "zh": "创建免费账户以查看您的投资组合并跟踪您的 DeFi 头寸。",
    },
    "balance_access": {
        "en": "Sign up to connect your wallet and view your balance.",
        "es": "Regístrate para conectar tu billetera y ver tu saldo.",
        "pt": "Cadastre-se para conectar sua carteira e ver seu saldo.",
        "zh": "注册以连接您的钱包并查看余额。",
    },
    "activity_access": {
        "en": "Create an account to view your transaction history.",
        "es": "Crea una cuenta para ver tu historial de transacciones.",
        "pt": "Crie uma conta para ver seu histórico de transações.",
        "zh": "创建账户以查看您的交易历史。",
    },
    "receive_access": {
        "en": "Sign up to get your personal wallet address for receiving funds.",
        "es": "Regístrate para obtener tu dirección de billetera personal.",
        "pt": "Cadastre-se para obter seu endereço de carteira pessoal.",
        "zh": "注册以获取您的个人钱包地址。",
    },
    "execute_swap": {
        "en": "Create an account to execute token swaps securely.",
        "es": "Crea una cuenta para ejecutar intercambios de tokens de forma segura.",
        "pt": "Crie uma conta para executar trocas de tokens com segurança.",
        "zh": "创建账户以安全执行代币交换。",
    },
    "execute_deposit": {
        "en": "Sign up to deposit funds into DeFi protocols.",
        "es": "Regístrate para depositar fondos en protocolos DeFi.",
        "pt": "Cadastre-se para depositar fundos em protocolos DeFi.",
        "zh": "注册以将资金存入 DeFi 协议。",
    },
    "execute_withdraw": {
        "en": "Create an account to withdraw funds from DeFi protocols.",
        "es": "Crea una cuenta para retirar fondos de protocolos DeFi.",
        "pt": "Crie uma conta para retirar fundos de protocolos DeFi.",
        "zh": "创建账户以从 DeFi 协议提取资金。",
    },
    "execute_transfer": {
        "en": "Sign up to transfer tokens to other wallets.",
        "es": "Regístrate para transferir tokens a otras billeteras.",
        "pt": "Cadastre-se para transferir tokens para outras carteiras.",
        "zh": "注册以将代币转移到其他钱包。",
    },
    "execute_action": {
        "en": "Create an account to execute DeFi transactions securely.",
        "es": "Crea una cuenta para ejecutar transacciones DeFi de forma segura.",
        "pt": "Crie uma conta para executar transações DeFi com segurança.",
        "zh": "创建账户以安全执行 DeFi 交易。",
    },
}

# ========================================
# Call-to-Action Messages
# ========================================

GUEST_CTA_MESSAGES: dict[str, str] = {
    "en": "Sign Up Free",
    "es": "Regístrate Gratis",
    "pt": "Cadastre-se Grátis",
    "zh": "免费注册",
}

# ========================================
# Demo Disclaimer Messages
# ========================================

GUEST_DEMO_DISCLAIMER: dict[str, str] = {
    "en": "You're in demo mode. Some features require registration.",
    "es": "Estás en modo demo. Algunas funciones requieren registro.",
    "pt": "Você está no modo demo. Alguns recursos requerem registro.",
    "zh": "您处于演示模式。某些功能需要注册。",
}

# ========================================
# Rate Limit Messages
# ========================================

GUEST_RATE_LIMIT_MESSAGES: dict[str, str] = {
    "en": "You've reached the message limit for demo mode. Sign up for unlimited access.",
    "es": "Has alcanzado el límite de mensajes del modo demo. Regístrate para acceso ilimitado.",
    "pt": "Você atingiu o limite de mensagens do modo demo. Cadastre-se para acesso ilimitado.",
    "zh": "您已达到演示模式的消息限制。注册以获得无限访问。",
}

# ========================================
# Welcome Messages
# ========================================

GUEST_WELCOME_MESSAGES: dict[str, str] = {
    "en": "Welcome to Anvil! I'm your AI assistant for DeFi. Ask me about protocols, yields, or risks. Note: Some features require registration.",
    "es": "¡Bienvenido a Anvil! Soy tu asistente de IA para DeFi. Pregúntame sobre protocolos, rendimientos o riesgos. Nota: Algunas funciones requieren registro.",
    "pt": "Bem-vindo ao Anvil! Sou seu assistente de IA para DeFi. Pergunte-me sobre protocolos, rendimentos ou riscos. Nota: Alguns recursos requerem registro.",
    "zh": "欢迎来到 Anvil！我是您的 DeFi AI 助手。问我关于协议、收益或风险的问题。注意：某些功能需要注册。",
}


# ========================================
# Helper Functions
# ========================================


def get_registration_message(reason: str, language: str = "en") -> dict[str, str]:
    """
    Get registration required message with all languages.

    Returns dict with messages in all supported languages.
    """
    messages = GUEST_REGISTRATION_MESSAGES.get(
        reason, GUEST_REGISTRATION_MESSAGES["execute_action"]
    )
    return messages


def get_cta_message(language: str = "en") -> str:
    """Get call-to-action message for specified language."""
    return GUEST_CTA_MESSAGES.get(language, GUEST_CTA_MESSAGES["en"])


def get_demo_disclaimer(language: str = "en") -> str:
    """Get demo disclaimer for specified language."""
    return GUEST_DEMO_DISCLAIMER.get(language, GUEST_DEMO_DISCLAIMER["en"])


def get_rate_limit_message(language: str = "en") -> str:
    """Get rate limit message for specified language."""
    return GUEST_RATE_LIMIT_MESSAGES.get(language, GUEST_RATE_LIMIT_MESSAGES["en"])


def get_welcome_message(language: str = "en") -> str:
    """Get welcome message for specified language."""
    return GUEST_WELCOME_MESSAGES.get(language, GUEST_WELCOME_MESSAGES["en"])


# ========================================
# Intent to Reason Mapping
# ========================================

RESTRICTED_INTENT_TO_REASON: dict[str, str] = {
    "PORTFOLIO": "portfolio_access",
    "BALANCE": "balance_access",
    "ACTIVITY": "activity_access",
    "RECEIVE": "receive_access",
    "SWAP": "execute_swap",  # Only when confirmed=true
    "DEPOSIT": "execute_deposit",
    "WITHDRAW": "execute_withdraw",
    "TRANSFER": "execute_transfer",
    "APPROVE": "execute_action",
    "BRIDGE": "execute_action",
}


def get_reason_for_intent(intent: str) -> str:
    """Get registration reason for a restricted intent."""
    return RESTRICTED_INTENT_TO_REASON.get(intent.upper(), "execute_action")
