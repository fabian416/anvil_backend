"""
MoonPay Swap Handler for Chat - Crypto-to-crypto swap operations.

Provides swap quotes and pair information via MoonPay Swap API:
- Get available swap pairs (12 pairs: BTC, ETH, SOL, USDC)
- Get real-time swap quotes with exchange rates
- Multi-language support (en, es, pt, zh, fr)
- Frontend-triggered execution (Privy modal)

Note: The actual swap execution is handled by Privy SDK on the frontend.
This handler provides pricing information and signals the frontend
to open the swap modal.
"""

import logging
import time
from dataclasses import dataclass
from typing import Optional

from app.infrastructure.adapters.external.moonpay_swap_client import (
    MoonPaySwapClient,
    MoonPaySwapPair,
    MoonPaySwapQuote,
)

logger = logging.getLogger(__name__)


@dataclass
class MoonPaySwapHandlerResult:
    """Result from MoonPay swap handler."""

    content: str
    pairs: list[dict]
    quote: Optional[dict]
    latency_ms: int
    language: str = "en"
    handler: str = "moonpay_swap_handler"
    action: str = "open_swap_modal"


# Localized messages for all 5 languages
SWAP_MESSAGES = {
    "en": {
        "title": "🌙 **MoonPay Swap**",
        "description": "Quick crypto-to-crypto swap with competitive rates",
        "available_pairs": "Available Swap Pairs",
        "supported_assets": "BTC, ETH, SOL, USDC",
        "how_to_swap": "How to Swap",
        "step_1": "Select the crypto pair you want to swap",
        "step_2": "Enter the amount you want to exchange",
        "step_3": "Review the exchange rate and fees",
        "step_4": "Confirm and complete the swap",
        "note": "💡 **Note:** Exchange rates update in real-time. Fees may apply.",
        "pairs_intro": "You can swap between:",
        "quote_template": "**{base_amount} {base} = {quote_amount} {quote}**\n\nExchange Rate: {rate}\nNetwork Fee: ${fee_usd}",
        "choose_pair": "Choose a swap pair:",
    },
    "es": {
        "title": "🌙 **Swap MoonPay**",
        "description": "Intercambio rápido cripto-a-cripto con tasas competitivas",
        "available_pairs": "Pares Disponibles",
        "supported_assets": "BTC, ETH, SOL, USDC",
        "how_to_swap": "Cómo Intercambiar",
        "step_1": "Selecciona el par de cripto que deseas intercambiar",
        "step_2": "Ingresa el monto que deseas cambiar",
        "step_3": "Revisa la tasa de cambio y las tarifas",
        "step_4": "Confirma y completa el intercambio",
        "note": "💡 **Nota:** Las tasas se actualizan en tiempo real. Pueden aplicar tarifas.",
        "pairs_intro": "Puedes intercambiar entre:",
        "quote_template": "**{base_amount} {base} = {quote_amount} {quote}**\n\nTasa de Cambio: {rate}\nTarifa de Red: ${fee_usd}",
        "choose_pair": "Elige un par de intercambio:",
    },
    "pt": {
        "title": "🌙 **Swap MoonPay**",
        "description": "Troca rápida cripto-a-cripto com taxas competitivas",
        "available_pairs": "Pares Disponíveis",
        "supported_assets": "BTC, ETH, SOL, USDC",
        "how_to_swap": "Como Trocar",
        "step_1": "Selecione o par de cripto que deseja trocar",
        "step_2": "Digite o valor que deseja trocar",
        "step_3": "Revise a taxa de câmbio e as taxas",
        "step_4": "Confirme e complete a troca",
        "note": "💡 **Nota:** As taxas são atualizadas em tempo real. Taxas podem ser aplicadas.",
        "pairs_intro": "Você pode trocar entre:",
        "quote_template": "**{base_amount} {base} = {quote_amount} {quote}**\n\nTaxa de Câmbio: {rate}\nTaxa de Rede: ${fee_usd}",
        "choose_pair": "Escolha um par de troca:",
    },
    "zh": {
        "title": "🌙 **MoonPay交换**",
        "description": "快速加密货币互换，汇率优惠",
        "available_pairs": "可用交换对",
        "supported_assets": "BTC, ETH, SOL, USDC",
        "how_to_swap": "如何交换",
        "step_1": "选择您想要交换的加密货币对",
        "step_2": "输入您想要交换的金额",
        "step_3": "查看汇率和费用",
        "step_4": "确认并完成交换",
        "note": "💡 **注意：** 汇率实时更新。可能需要支付费用。",
        "pairs_intro": "您可以交换：",
        "quote_template": "**{base_amount} {base} = {quote_amount} {quote}**\n\n汇率: {rate}\n网络费用: ${fee_usd}",
        "choose_pair": "选择交换对：",
    },
    "fr": {
        "title": "🌙 **Swap MoonPay**",
        "description": "Échange rapide crypto-à-crypto avec taux compétitifs",
        "available_pairs": "Paires Disponibles",
        "supported_assets": "BTC, ETH, SOL, USDC",
        "how_to_swap": "Comment Échanger",
        "step_1": "Sélectionnez la paire de crypto que vous souhaitez échanger",
        "step_2": "Entrez le montant que vous souhaitez échanger",
        "step_3": "Examinez le taux de change et les frais",
        "step_4": "Confirmez et complétez l'échange",
        "note": "💡 **Note:** Les taux sont mis à jour en temps réel. Des frais peuvent s'appliquer.",
        "pairs_intro": "Vous pouvez échanger entre:",
        "quote_template": "**{base_amount} {base} = {quote_amount} {quote}**\n\nTaux de Change: {rate}\nFrais de Réseau: ${fee_usd}",
        "choose_pair": "Choisissez une paire d'échange:",
    },
}


class MoonPaySwapHandler:
    """
    Handler for MoonPay crypto-to-crypto swap operations in chat.

    Responsibilities:
    - Fetch available swap pairs from MoonPay API
    - Get real-time swap quotes with pricing
    - Format localized responses for chat
    - Signal frontend to open Privy swap modal

    Usage:
        handler = MoonPaySwapHandler(swap_client)
        result = await handler.get_swap_info(
            from_currency="btc",
            to_currency="eth",
            amount="0.5",
            language="en"
        )
    """

    def __init__(self, swap_client: MoonPaySwapClient):
        """
        Initialize MoonPay swap handler.

        Args:
            swap_client: MoonPaySwapClient for API calls
        """
        self._swap_client = swap_client

    async def get_available_pairs(
        self, language: str = "en"
    ) -> MoonPaySwapHandlerResult:
        """
        Get all available swap pairs.

        Args:
            language: Response language (en, es, pt, zh, fr)

        Returns:
            Handler result with pairs list
        """
        start_time = time.time()
        lang = language if language in SWAP_MESSAGES else "en"
        msgs = SWAP_MESSAGES[lang]

        try:
            # Fetch pairs from MoonPay API
            pairs = await self._swap_client.get_pairs()

            # Format pairs for response
            pairs_data = [
                {
                    "pair_name": p.pair_name,
                    "base": p.base_currency_code.upper(),
                    "quote": p.quote_currency_code.upper(),
                    "base_name": p.base_currency_name,
                    "quote_name": p.quote_currency_name,
                }
                for p in pairs
            ]

            # Build response content
            content = f"""{msgs['title']}

{msgs['description']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**{msgs['available_pairs']}:**
{msgs['supported_assets']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**{msgs['pairs_intro']}**

"""

            # Add pairs list
            for pair in pairs_data[:12]:  # Show max 12 pairs
                content += f"• {pair['base']} ↔ {pair['quote']}\n"

            content += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**{msgs['how_to_swap']}:**

1. {msgs['step_1']}
2. {msgs['step_2']}
3. {msgs['step_3']}
4. {msgs['step_4']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{msgs['note']}
"""

            latency = int((time.time() - start_time) * 1000)

            return MoonPaySwapHandlerResult(
                content=content,
                pairs=pairs_data,
                quote=None,
                latency_ms=latency,
                language=lang,
            )

        except Exception as e:
            logger.error(f"Error fetching MoonPay swap pairs: {e}", exc_info=True)
            latency = int((time.time() - start_time) * 1000)

            # Fallback response
            fallback_content = f"""{msgs['title']}

⚠️ Unable to fetch swap pairs at the moment. Please try again later.

{msgs['note']}
"""

            return MoonPaySwapHandlerResult(
                content=fallback_content,
                pairs=[],
                quote=None,
                latency_ms=latency,
                language=lang,
            )

    async def get_swap_quote(
        self,
        from_currency: str,
        to_currency: str,
        amount: str,
        language: str = "en",
    ) -> MoonPaySwapHandlerResult:
        """
        Get swap quote for a specific pair and amount.

        Args:
            from_currency: Base currency code (e.g., "btc")
            to_currency: Quote currency code (e.g., "eth")
            amount: Amount of base currency to swap
            language: Response language

        Returns:
            Handler result with quote information
        """
        start_time = time.time()
        lang = language if language in SWAP_MESSAGES else "en"
        msgs = SWAP_MESSAGES[lang]

        try:
            # Normalize currency codes
            base = from_currency.lower()
            quote = to_currency.lower()
            pair_name = f"{base}-{quote}"

            # Get quote from MoonPay
            swap_quote = await self._swap_client.get_quote(pair_name, amount)

            # Format quote data
            quote_data = {
                "pair_name": pair_name,
                "base": base.upper(),
                "quote": quote.upper(),
                "base_amount": swap_quote.base_currency_amount,
                "quote_amount": swap_quote.quote_currency_amount,
                "exchange_rate": swap_quote.exchange_rate,
                "network_fee_usd": swap_quote.network_fee_amount_usd,
                "extra_fee_usd": swap_quote.extra_fee_amount_usd,
                "expires_at": swap_quote.expires_at,
            }

            # Build response content
            quote_text = msgs['quote_template'].format(
                base_amount=quote_data['base_amount'],
                base=quote_data['base'],
                quote_amount=quote_data['quote_amount'],
                quote=quote_data['quote'],
                rate=quote_data['exchange_rate'],
                fee_usd=quote_data['network_fee_usd'],
            )

            content = f"""{msgs['title']}

{quote_text}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{msgs['note']}

💡 **Tip:** Click the swap button to complete this transaction through Privy.
"""

            latency = int((time.time() - start_time) * 1000)

            return MoonPaySwapHandlerResult(
                content=content,
                pairs=[],
                quote=quote_data,
                latency_ms=latency,
                language=lang,
            )

        except Exception as e:
            logger.error(
                f"Error fetching swap quote for {from_currency}->{to_currency}: {e}",
                exc_info=True,
            )
            latency = int((time.time() - start_time) * 1000)

            # Fallback response
            fallback_content = f"""{msgs['title']}

⚠️ Unable to get swap quote for {from_currency.upper()} → {to_currency.upper()}.

Please check:
• The swap pair is supported
• The amount is within allowed limits
• Try again in a moment

{msgs['note']}
"""

            return MoonPaySwapHandlerResult(
                content=fallback_content,
                pairs=[],
                quote=None,
                latency_ms=latency,
                language=lang,
            )
