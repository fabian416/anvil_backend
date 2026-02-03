"""
Restricted Action Handler.

Provides specific, localized messages for actions that require registration.
"""

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class HandlerResult:
    """Result from a handler."""

    content: str
    requires_registration: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


# Localized messages for each restricted action
RESTRICTED_MESSAGES = {
    "balance": {
        "en": """🔒 **Wallet Access Required**

To view your balance, you need to connect your wallet.

👉 [Sign Up Free](/signup) to access:
• Real-time balance across all chains
• Transaction history
• Portfolio tracking
• Price alerts""",
        "es": """🔒 **Acceso a Billetera Requerido**

Para ver tu saldo, necesitas conectar tu billetera.

👉 [Regístrate Gratis](/signup) para acceder a:
• Saldo en tiempo real en todas las cadenas
• Historial de transacciones
• Seguimiento de portafolio
• Alertas de precio""",
        "pt": """🔒 **Acesso à Carteira Necessário**

Para ver seu saldo, você precisa conectar sua carteira.

👉 [Cadastre-se Grátis](/signup) para acessar:
• Saldo em tempo real em todas as redes
• Histórico de transações
• Acompanhamento de portfólio
• Alertas de preço""",
    },
    "portfolio": {
        "en": """🔒 **Account Required**

To view your portfolio, please sign up or log in.

👉 [Sign Up Free](/signup) to access:
• Complete portfolio overview
• Performance analytics
• Risk assessment
• AI-powered recommendations""",
        "es": """🔒 **Cuenta Requerida**

Para ver tu portafolio, regístrate o inicia sesión.

👉 [Regístrate Gratis](/signup) para acceder a:
• Vista completa del portafolio
• Análisis de rendimiento
• Evaluación de riesgo
• Recomendaciones con IA""",
        "pt": """🔒 **Conta Necessária**

Para ver seu portfólio, cadastre-se ou faça login.

👉 [Cadastre-se Grátis](/signup) para acessar:
• Visão completa do portfólio
• Análise de desempenho
• Avaliação de risco
• Recomendações com IA""",
    },
    "activity": {
        "en": """🔒 **Account Required**

To view your transaction history, please sign up or log in.

👉 [Sign Up Free](/signup) to access:
• Complete transaction history
• Profit/loss tracking
• Tax reporting exports
• Activity alerts""",
        "es": """🔒 **Cuenta Requerida**

Para ver tu historial de transacciones, regístrate o inicia sesión.

👉 [Regístrate Gratis](/signup) para acceder a:
• Historial completo de transacciones
• Seguimiento de ganancias/pérdidas
• Exportaciones para impuestos
• Alertas de actividad""",
        "pt": """🔒 **Conta Necessária**

Para ver seu histórico de transações, cadastre-se ou faça login.

👉 [Cadastre-se Grátis](/signup) para acessar:
• Histórico completo de transações
• Acompanhamento de lucros/perdas
• Exportações para impostos
• Alertas de atividade""",
    },
    "receive": {
        "en": """🔒 **Wallet Required**

To get your receive address, you need to connect or create a wallet.

👉 [Sign Up Free](/signup) to:
• Get your personal wallet address
• Receive crypto from any chain
• QR codes for easy deposits
• Automatic notifications""",
        "es": """🔒 **Billetera Requerida**

Para obtener tu dirección de recepción, necesitas conectar o crear una billetera.

👉 [Regístrate Gratis](/signup) para:
• Obtener tu dirección personal
• Recibir cripto de cualquier cadena
• Códigos QR para depósitos fáciles
• Notificaciones automáticas""",
        "pt": """🔒 **Carteira Necessária**

Para obter seu endereço de recebimento, você precisa conectar ou criar uma carteira.

👉 [Cadastre-se Grátis](/signup) para:
• Obter seu endereço pessoal
• Receber cripto de qualquer rede
• Códigos QR para depósitos fáceis
• Notificações automáticas""",
    },
    "transfer": {
        "en": """🔒 **Wallet Required**

To send tokens, you need to connect your wallet.

👉 [Sign Up Free](/signup) to:
• Send tokens to any address
• Cross-chain transfers
• MEV protection
• Transaction tracking""",
        "es": """🔒 **Billetera Requerida**

Para enviar tokens, necesitas conectar tu billetera.

👉 [Regístrate Gratis](/signup) para:
• Enviar tokens a cualquier dirección
• Transferencias cross-chain
• Protección MEV
• Seguimiento de transacciones""",
        "pt": """🔒 **Carteira Necessária**

Para enviar tokens, você precisa conectar sua carteira.

👉 [Cadastre-se Grátis](/signup) para:
• Enviar tokens para qualquer endereço
• Transferências cross-chain
• Proteção MEV
• Acompanhamento de transações""",
    },
}

# CTA messages
CTA_MESSAGES = {
    "en": "Sign Up Free",
    "es": "Regístrate Gratis",
    "pt": "Cadastre-se Grátis",
}


class RestrictedActionHandler:
    """
    Handler for restricted actions that require registration.

    Provides specific, localized messages explaining why registration
    is needed and what features become available.
    """

    def __init__(self):
        self._messages = RESTRICTED_MESSAGES
        self._cta = CTA_MESSAGES

    async def handle(
        self,
        intent: str,
        language: str = "en",
    ) -> HandlerResult:
        """
        Handle a restricted action request.

        Args:
            intent: The restricted intent (balance, portfolio, etc.)
            language: Language code

        Returns:
            HandlerResult with localized message
        """
        # Map intent to message key
        intent_lower = intent.lower().replace("_", "")

        message_key = None
        if "balance" in intent_lower:
            message_key = "balance"
        elif "portfolio" in intent_lower:
            message_key = "portfolio"
        elif "activity" in intent_lower:
            message_key = "activity"
        elif "receive" in intent_lower:
            message_key = "receive"
        elif "transfer" in intent_lower or "send" in intent_lower:
            message_key = "transfer"
        else:
            # Default to portfolio message
            message_key = "portfolio"

        # Get localized message
        messages = self._messages.get(message_key, {})
        content = messages.get(
            language, messages.get("en", "This action requires registration.")
        )

        return HandlerResult(
            content=content,
            requires_registration=True,
            metadata={
                "registration_required": True,
                "reason": self._get_reason(message_key),
                "signup_url": "/signup",
                "cta": self._cta,
            },
        )

    def _get_reason(self, message_key: str) -> str:
        """Get reason code for restricted action."""
        reasons = {
            "balance": "wallet_access",
            "portfolio": "account_required",
            "activity": "account_required",
            "receive": "wallet_required",
            "transfer": "wallet_required",
        }
        return reasons.get(message_key, "account_required")

    def get_registration_required_response(
        self,
        reason: str,
        language: str,
    ) -> dict[str, Any]:
        """Build registration_required response object."""
        messages = RESTRICTED_MESSAGES.get(
            reason, RESTRICTED_MESSAGES.get("portfolio", {})
        )

        return {
            "required": True,
            "reason": reason,
            "message": {lang: msg.split("\n")[0] for lang, msg in messages.items()},
            "cta": CTA_MESSAGES,
            "signup_url": "/signup",
        }
