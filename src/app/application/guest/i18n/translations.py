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
        "en": """💼 **Unlock Your Complete Portfolio Dashboard**

Track all your DeFi positions in one place! With a free account, you'll get:

✨ **Real-time Portfolio Tracking**
• View all your assets across multiple chains
• Monitor your total portfolio value
• Track performance over time

📊 **Advanced Analytics**
• Asset allocation breakdown
• Profit/loss analysis
• Risk exposure metrics

🔔 **Smart Alerts**
• Price movement notifications
• Liquidation risk warnings
• Yield opportunity alerts

🎯 **AI-Powered Insights**
• Portfolio optimization suggestions
• Rebalancing recommendations
• Tax optimization strategies

**It's free and takes less than 30 seconds to sign up!**""",
        "es": """💼 **Desbloquea Tu Panel de Portafolio Completo**

¡Rastrea todas tus posiciones DeFi en un solo lugar! Con una cuenta gratuita, obtendrás:

✨ **Seguimiento de Portafolio en Tiempo Real**
• Ver todos tus activos en múltiples cadenas
• Monitorear el valor total de tu portafolio
• Rastrear el rendimiento a lo largo del tiempo

📊 **Análisis Avanzados**
• Desglose de asignación de activos
• Análisis de ganancias/pérdidas
• Métricas de exposición al riesgo

🔔 **Alertas Inteligentes**
• Notificaciones de movimientos de precios
• Advertencias de riesgo de liquidación
• Alertas de oportunidades de rendimiento

🎯 **Insights Impulsados por IA**
• Sugerencias de optimización de portafolio
• Recomendaciones de reequilibrio
• Estrategias de optimización fiscal

**¡Es gratis y toma menos de 30 segundos registrarse!**""",
        "pt": """💼 **Desbloqueie Seu Painel Completo de Portfólio**

Rastreie todas as suas posições DeFi em um só lugar! Com uma conta gratuita, você terá:

✨ **Rastreamento de Portfólio em Tempo Real**
• Ver todos os seus ativos em múltiplas redes
• Monitorar o valor total do seu portfólio
• Acompanhar o desempenho ao longo do tempo

📊 **Análises Avançadas**
• Divisão de alocação de ativos
• Análise de lucro/perda
• Métricas de exposição ao risco

🔔 **Alertas Inteligentes**
• Notificações de movimentos de preços
• Avisos de risco de liquidação
• Alertas de oportunidades de rendimento

🎯 **Insights Impulsionados por IA**
• Sugestões de otimização de portfólio
• Recomendações de rebalanceamento
• Estratégias de otimização fiscal

**É grátis e leva menos de 30 segundos para se cadastrar!**""",
        "zh": """💼 **解锁您的完整投资组合仪表板**

在一个地方跟踪您所有的 DeFi 头寸！使用免费账户，您将获得：

✨ **实时投资组合跟踪**
• 查看跨多条链的所有资产
• 监控您的总投资组合价值
• 跟踪长期表现

📊 **高级分析**
• 资产配置细分
• 盈亏分析
• 风险敞口指标

🔔 **智能警报**
• 价格变动通知
• 清算风险警告
• 收益机会提醒

🎯 **AI 驱动的洞察**
• 投资组合优化建议
• 再平衡推荐
• 税务优化策略

**免费注册，只需不到 30 秒！**""",
    },
    "wallet_access": {
        "en": "🔐 **Wallet Access Required**\n\nTo view your balance and wallet holdings, you need to create an account and connect your wallet.\n\nSign up to:\n• View real-time balances\n• Track your holdings\n• Monitor your positions",
        "es": "🔐 **Acceso a Billetera Requerido**\n\nPara ver tu saldo y holdings, necesitas crear una cuenta y conectar tu billetera.\n\nRegístrate para:\n• Ver saldos en tiempo real\n• Rastrear tus holdings\n• Monitorear tus posiciones",
        "pt": "🔐 **Acesso à Carteira Necessário**\n\nPara ver seu saldo e holdings, você precisa criar uma conta e conectar sua carteira.\n\nCadastre-se para:\n• Ver saldos em tempo real\n• Rastrear seus holdings\n• Monitorar suas posições",
        "zh": "🔐 **需要钱包访问权限**\n\n要查看您的余额和持仓，您需要创建账户并连接钱包。\n\n注册后可以：\n• 查看实时余额\n• 跟踪您的持仓\n• 监控您的头寸",
    },
    "balance_access": {
        "en": "Sign up to connect your wallet and view your balance.",
        "es": "Regístrate para conectar tu billetera y ver tu saldo.",
        "pt": "Cadastre-se para conectar sua carteira e ver seu saldo.",
        "zh": "注册以连接您的钱包并查看余额。",
    },
    "transaction_history": {
        "en": "🔐 **Account Required**\n\nTo view your transaction history and past activity, you need to create an account.\n\nSign up to:\n• View all transactions\n• Track your trading history\n• Export transaction records",
        "es": "🔐 **Cuenta Requerida**\n\nPara ver tu historial de transacciones y actividad pasada, necesitas crear una cuenta.\n\nRegístrate para:\n• Ver todas las transacciones\n• Rastrear tu historial de trading\n• Exportar registros de transacciones",
        "pt": "🔐 **Conta Necessária**\n\nPara ver seu histórico de transações e atividade passada, você precisa criar uma conta.\n\nCadastre-se para:\n• Ver todas as transações\n• Rastrear seu histórico de trading\n• Exportar registros de transações",
        "zh": "🔐 **需要账户**\n\n要查看您的交易历史和过去的活动，您需要创建账户。\n\n注册后可以：\n• 查看所有交易\n• 跟踪您的交易历史\n• 导出交易记录",
    },
    "wallet_address": {
        "en": "🔐 **Wallet Required**\n\nTo get your deposit address, you need to create an account and set up your wallet.\n\nSign up to:\n• Get your personal wallet address\n• Receive crypto deposits\n• Manage multiple chains",
        "es": "🔐 **Billetera Requerida**\n\nPara obtener tu dirección de depósito, necesitas crear una cuenta y configurar tu billetera.\n\nRegístrate para:\n• Obtener tu dirección de billetera personal\n• Recibir depósitos de cripto\n• Gestionar múltiples cadenas",
        "pt": "🔐 **Carteira Necessária**\n\nPara obter seu endereço de depósito, você precisa criar uma conta e configurar sua carteira.\n\nCadastre-se para:\n• Obter seu endereço de carteira pessoal\n• Receber depósitos de cripto\n• Gerenciar múltiplas redes",
        "zh": "🔐 **需要钱包**\n\n要获取您的存款地址，您需要创建账户并设置钱包。\n\n注册后可以：\n• 获取您的个人钱包地址\n• 接收加密货币存款\n• 管理多条链",
    },
    "buy_crypto": {
        "en": "🔐 **Account Required**\n\nTo buy crypto with fiat, you need to create an account and complete verification.\n\nSign up to:\n• Buy crypto with card or bank transfer\n• Access multiple on-ramp providers\n• Get the best rates",
        "es": "🔐 **Cuenta Requerida**\n\nPara comprar cripto con dinero fiat, necesitas crear una cuenta y completar la verificación.\n\nRegístrate para:\n• Comprar cripto con tarjeta o transferencia bancaria\n• Acceder a múltiples proveedores\n• Obtener las mejores tasas",
        "pt": "🔐 **Conta Necessária**\n\nPara comprar cripto com moeda fiat, você precisa criar uma conta e completar a verificação.\n\nCadastre-se para:\n• Comprar cripto com cartão ou transferência bancária\n• Acessar múltiplos provedores\n• Obter as melhores taxas",
        "zh": "🔐 **需要账户**\n\n要用法币购买加密货币，您需要创建账户并完成验证。\n\n注册后可以：\n• 用卡或银行转账购买加密货币\n• 访问多个入金渠道\n• 获得最优汇率",
    },
    "send_crypto": {
        "en": "🔐 **Wallet Required**\n\nTo send crypto to another wallet, you need to create an account and connect your wallet.\n\nSign up to:\n• Send tokens to any address\n• Transfer across multiple chains\n• Track your transfers",
        "es": "🔐 **Billetera Requerida**\n\nPara enviar cripto a otra billetera, necesitas crear una cuenta y conectar tu billetera.\n\nRegístrate para:\n• Enviar tokens a cualquier dirección\n• Transferir entre múltiples cadenas\n• Rastrear tus transferencias",
        "pt": "🔐 **Carteira Necessária**\n\nPara enviar cripto para outra carteira, você precisa criar uma conta e conectar sua carteira.\n\nCadastre-se para:\n• Enviar tokens para qualquer endereço\n• Transferir entre múltiplas redes\n• Rastrear suas transferências",
        "zh": "🔐 **需要钱包**\n\n要向其他钱包发送加密货币，您需要创建账户并连接钱包。\n\n注册后可以：\n• 向任何地址发送代币\n• 跨链转账\n• 跟踪您的转账",
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
