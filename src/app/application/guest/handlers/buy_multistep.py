"""
Multi-step Buy Flow Handler.

Implements conversational buy flow with:
- Step-by-step parameter collection (crypto → amount)
- Pricing display with fees
- State preservation across messages
- Guest-friendly with signup CTA
"""

import logging
import re
from typing import Any

from app.infrastructure.adapters.external.coingecko_client import CoinGeckoClient

logger = logging.getLogger(__name__)


class BuyMultiStepHandler:
    """Handles multi-step conversational flow for buying crypto (USDC only)."""

    # Only USDC is supported for direct purchase
    SUPPORTED_CRYPTOS = {
        "usdc": {"symbol": "USDC", "name": "USD Coin", "emoji": "💵"},
    }

    # Unsupported cryptos (for helpful error messages)
    UNSUPPORTED_CRYPTOS = {
        "btc": {"symbol": "BTC", "name": "Bitcoin", "emoji": "₿"},
        "bitcoin": {"symbol": "BTC", "name": "Bitcoin", "emoji": "₿"},
        "eth": {"symbol": "ETH", "name": "Ethereum", "emoji": "Ξ"},
        "ethereum": {"symbol": "ETH", "name": "Ethereum", "emoji": "Ξ"},
        "ether": {"symbol": "ETH", "name": "Ethereum", "emoji": "Ξ"},
        "sol": {"symbol": "SOL", "name": "Solana", "emoji": "◎"},
        "solana": {"symbol": "SOL", "name": "Solana", "emoji": "◎"},
        "usdt": {"symbol": "USDT", "name": "Tether", "emoji": "💵"},
        "matic": {"symbol": "MATIC", "name": "Polygon", "emoji": "🔷"},
        "polygon": {"symbol": "MATIC", "name": "Polygon", "emoji": "🔷"},
    }

    def __init__(self):
        """Initialize buy multi-step handler."""
        self._coingecko = CoinGeckoClient()
        # CoinGecko coin ID mapping
        self._coin_id_map = {
            "USDC": "usd-coin",
        }

    async def handle_flow(
        self,
        content: str,
        language: str,
        is_authenticated: bool,
        continuation_step: str | None = None,
        previous_buy_info: dict | None = None,
    ) -> dict[str, Any]:
        """
        Handle multi-step buy flow (USDC only).

        Flow:
        1. User: "buy" → Ask for amount (USDC is the only option)
        2. User: "100" → Show quote, ask confirmation
        3. User: "confirm" → Execute (requires auth)

        If user requests other crypto (BTC, ETH, etc.), show helpful message
        suggesting they buy USDC and swap.
        """
        content_lower = content.lower().strip()

        # Initialize or load buy info
        buy_info = previous_buy_info or {}
        buy_info["crypto"] = "USDC"  # Always USDC

        # Handle continuation steps
        if continuation_step:
            return await self._handle_continuation(
                content,
                content_lower,
                language,
                is_authenticated,
                continuation_step,
                buy_info,
            )

        # Check if user is trying to buy an unsupported crypto
        unsupported_crypto = self._detect_unsupported_crypto(content)
        if unsupported_crypto:
            return self._show_usdc_only_message(
                unsupported_crypto, language, is_authenticated
            )

        # Parse buy request - only look for amount (crypto is always USDC)
        parsed = self._parse_buy_request(content)

        if parsed["amount"]:
            # Amount provided, show quote
            buy_info["amount"] = parsed["amount"]
            return await self._show_quote_and_confirm(
                buy_info, language, is_authenticated
            )

        # Initial "buy" command - ask for amount directly (USDC is the only option)
        if any(
            kw in content_lower
            for kw in ["buy", "purchase", "on-ramp", "onramp", "crypto"]
        ):
            return self._ask_for_usdc_amount(language, is_authenticated)

        # Fallback: ask for USDC amount
        return self._ask_for_usdc_amount(language, is_authenticated)

    async def _handle_continuation(
        self,
        content: str,
        content_lower: str,
        language: str,
        is_authenticated: bool,
        step: str,
        buy_info: dict,
    ) -> dict[str, Any]:
        """Handle continuation from previous step (USDC only flow)."""

        # Always ensure crypto is USDC
        buy_info["crypto"] = "USDC"

        # Handle confirmation
        if step == "buy_awaiting_confirmation":
            if any(
                kw in content_lower
                for kw in ["confirm", "yes", "ok", "proceed", "go", "buy", "sí", "sim"]
            ):
                return self._execute_buy(buy_info, language, is_authenticated)
            elif any(
                kw in content_lower for kw in ["cancel", "no", "stop", "cancelar"]
            ):
                return self._cancel_buy(language)
            elif "change" in content_lower or "edit" in content_lower:
                return await self._handle_edit(
                    content, buy_info, language, is_authenticated
                )

        # Handle amount input
        if step == "buy_awaiting_amount":
            # Check if user is trying to buy unsupported crypto instead of providing amount
            unsupported = self._detect_unsupported_crypto(content)
            if unsupported:
                return self._show_usdc_only_message(
                    unsupported, language, is_authenticated
                )

            amount = self._extract_amount(content)
            if amount:
                buy_info["amount"] = amount
                return await self._show_quote_and_confirm(
                    buy_info, language, is_authenticated
                )
            else:
                return self._ask_for_usdc_amount(language, is_authenticated)

        # Handle crypto input (legacy - redirect to amount)
        if step == "buy_awaiting_crypto":
            # Check for unsupported crypto
            unsupported = self._detect_unsupported_crypto(content)
            if unsupported:
                return self._show_usdc_only_message(
                    unsupported, language, is_authenticated
                )

            # Otherwise, ask for amount (USDC is auto-selected)
            return self._ask_for_usdc_amount(language, is_authenticated)

        # Unknown step
        return self._ask_for_usdc_amount(language, is_authenticated)

    def _parse_buy_request(self, content: str) -> dict:
        """Parse buy request to extract crypto and amount."""
        result = {"crypto": None, "amount": None}

        # Pattern: "buy 100 USD of ETH" or "buy ETH 100"
        pattern = re.compile(
            r"(?:buy|purchase)\s+(?:(\d+\.?\d*)\s+)?(?:usd|dollars?\s+)?(?:of\s+)?(\w+)|(\w+)\s+(?:for\s+)?(\d+\.?\d*)",
            re.IGNORECASE,
        )
        match = pattern.search(content)

        if match:
            amount_start = match.group(1)
            crypto_start = match.group(2)
            crypto_end = match.group(3)
            amount_end = match.group(4)

            crypto = crypto_start or crypto_end
            amount = amount_start or amount_end

            if crypto:
                result["crypto"] = self.SUPPORTED_CRYPTOS.get(crypto.lower(), {}).get(
                    "symbol"
                )
            if amount:
                result["amount"] = amount

        return result

    def _extract_crypto(self, content: str) -> str | None:
        """Extract crypto from content (always returns USDC if mentioned)."""
        content_lower = content.lower().strip()
        if "usdc" in content_lower:
            return "USDC"
        return None

    def _detect_unsupported_crypto(self, content: str) -> str | None:
        """Detect if user is trying to buy an unsupported crypto."""
        content_lower = content.lower().strip()
        for alias, data in self.UNSUPPORTED_CRYPTOS.items():
            if alias in content_lower:
                return data["symbol"]
        return None

    def _extract_amount(self, content: str) -> str | None:
        """Extract amount from content."""
        match = re.search(r"(\d+\.?\d*)", content)
        return match.group(1) if match else None

    def _show_usdc_only_message(
        self, requested_crypto: str, language: str, is_authenticated: bool
    ) -> dict:
        """Show message when user requests unsupported crypto."""
        translations = {
            "en": {
                "title": f"💡 **USDC Only Available**\n\n",
                "message": f"I see you want to buy **{requested_crypto}**, but currently only **USDC** is available for direct purchase.\n\n",
                "divider": "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n",
                "tip": f"**Here's a tip:** You can buy USDC first, then swap it for {requested_crypto} instantly!\n\n",
                "question": "Would you like to buy USDC instead?\n\n",
                "hint": '💬 Just tell me how much (e.g., "$100" or "500 dollars")',
            },
            "es": {
                "title": f"💡 **Solo USDC Disponible**\n\n",
                "message": f"Veo que quieres comprar **{requested_crypto}**, pero actualmente solo **USDC** está disponible para compra directa.\n\n",
                "divider": "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n",
                "tip": f"**Un consejo:** ¡Puedes comprar USDC primero y luego cambiarlo por {requested_crypto} al instante!\n\n",
                "question": "¿Te gustaría comprar USDC en su lugar?\n\n",
                "hint": '💬 Solo dime cuánto (ej: "$100" o "500 dólares")',
            },
            "pt": {
                "title": f"💡 **Apenas USDC Disponível**\n\n",
                "message": f"Vejo que você quer comprar **{requested_crypto}**, mas atualmente apenas **USDC** está disponível para compra direta.\n\n",
                "divider": "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n",
                "tip": f"**Uma dica:** Você pode comprar USDC primeiro e depois trocar por {requested_crypto} instantaneamente!\n\n",
                "question": "Gostaria de comprar USDC em vez disso?\n\n",
                "hint": '💬 Apenas me diga quanto (ex: "$100" ou "500 dólares")',
            },
            "zh": {
                "title": f"💡 **仅支持 USDC**\n\n",
                "message": f"我看到您想购买 **{requested_crypto}**，但目前只有 **USDC** 可以直接购买。\n\n",
                "divider": "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n",
                "tip": f"**小贴士：** 您可以先购买 USDC，然后立即将其兑换成 {requested_crypto}！\n\n",
                "question": "您想改为购买 USDC 吗？\n\n",
                "hint": '💬 告诉我您想要多少（例如："$100" 或 "500美元"）',
            },
        }
        t = translations.get(language, translations["en"])

        content = f"{t['title']}{t['message']}{t['divider']}{t['tip']}{t['question']}{t['hint']}"

        return {
            "content": content,
            "enrichment": {
                "buy_flow": "usdc_only_redirect",
                "requested_crypto": requested_crypto,
            },
            "requires_registration": not is_authenticated,
            "pending_action": "buy_awaiting_amount",
            "buy_info": {"crypto": "USDC", "requested_crypto": requested_crypto},
        }

    def _ask_for_usdc_amount(self, language: str, is_authenticated: bool) -> dict:
        """Ask user how much USDC to buy."""
        translations = {
            "en": {
                "title": "💵 **Buy USDC**\n\n",
                "question": "How much USDC would you like to buy?\n\n",
                "divider": "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n",
                "benefits": "**USDC** is a stablecoin pegged 1:1 to the US Dollar - perfect for:\n• 🔄 Swapping to other cryptos (ETH, BTC, SOL...)\n• 💰 Earning yield in DeFi\n• 📤 Sending to friends\n\n",
                "hint": '💬 Enter the amount in USD (e.g., "100" or "$500")\n\n',
                "note": "💡 *Minimum: $20 • Maximum: $10,000*",
            },
            "es": {
                "title": "💵 **Comprar USDC**\n\n",
                "question": "¿Cuánto USDC te gustaría comprar?\n\n",
                "divider": "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n",
                "benefits": "**USDC** es una stablecoin con paridad 1:1 al dólar - perfecta para:\n• 🔄 Intercambiar por otras criptos (ETH, BTC, SOL...)\n• 💰 Ganar rendimiento en DeFi\n• 📤 Enviar a amigos\n\n",
                "hint": '💬 Ingresa la cantidad en USD (ej: "100" o "$500")\n\n',
                "note": "💡 *Mínimo: $20 • Máximo: $10,000*",
            },
            "pt": {
                "title": "💵 **Comprar USDC**\n\n",
                "question": "Quanto USDC você gostaria de comprar?\n\n",
                "divider": "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n",
                "benefits": "**USDC** é uma stablecoin com paridade 1:1 ao dólar - perfeita para:\n• 🔄 Trocar por outras criptos (ETH, BTC, SOL...)\n• 💰 Ganhar rendimento em DeFi\n• 📤 Enviar para amigos\n\n",
                "hint": '💬 Digite o valor em USD (ex: "100" ou "$500")\n\n',
                "note": "💡 *Mínimo: $20 • Máximo: $10,000*",
            },
            "zh": {
                "title": "💵 **购买 USDC**\n\n",
                "question": "您想购买多少 USDC？\n\n",
                "divider": "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n",
                "benefits": "**USDC** 是与美元 1:1 挂钩的稳定币 - 非常适合：\n• 🔄 兑换其他加密货币（ETH、BTC、SOL...）\n• 💰 在 DeFi 中赚取收益\n• 📤 发送给朋友\n\n",
                "hint": '💬 输入美元金额（例如："100" 或 "$500"）\n\n',
                "note": "💡 *最低：$20 • 最高：$10,000*",
            },
        }
        t = translations.get(language, translations["en"])

        content = f"{t['title']}{t['question']}{t['divider']}{t['benefits']}{t['hint']}{t['note']}"

        return {
            "content": content,
            "enrichment": {"buy_flow": "step1_amount"},
            "requires_registration": not is_authenticated,
            "pending_action": "buy_awaiting_amount",
            "buy_info": {"crypto": "USDC"},
        }

    def _ask_for_crypto(
        self, language: str, is_authenticated: bool, error: bool = False
    ) -> dict:
        """Ask user which crypto to buy (redirects to USDC amount since only USDC is available)."""
        # Since only USDC is available, skip crypto selection and ask for amount
        return self._ask_for_usdc_amount(language, is_authenticated)

    def _ask_for_amount(
        self, buy_info: dict, language: str, is_authenticated: bool, error: bool = False
    ) -> dict:
        """Ask user how much to buy."""
        crypto = buy_info.get("crypto", "").upper()

        # Crypto emoji mapping
        crypto_emoji = {
            "BTC": "₿",
            "ETH": "Ξ",
            "SOL": "◎",
            "USDC": "💵",
            "USDT": "💵",
            "MATIC": "🔷",
        }
        emoji = crypto_emoji.get(crypto, "💎")

        translations = {
            "en": {
                "error": "❌ That doesn't look like a valid amount. Let's try again!\n\n",
                "title": f"💰 **Buying {emoji} {crypto}**\n\n",
                "question": f"**Step 2 of 3:** How much USD would you like to spend?\n\n",
                "hint": f"💡 *Enter amount in USD:*\n• `50` ($50)\n• `100` ($100)\n• `500` ($500)",
                "note": "\n\n📊 *Minimum: $20 • Maximum: $10,000*",
            },
            "es": {
                "error": "❌ Eso no parece una cantidad válida. ¡Intentemos de nuevo!\n\n",
                "title": f"💰 **Comprando {emoji} {crypto}**\n\n",
                "question": f"**Paso 2 de 3:** ¿Cuánto USD te gustaría gastar?\n\n",
                "hint": f"💡 *Ingresa la cantidad en USD:*\n• `50` ($50)\n• `100` ($100)\n• `500` ($500)",
                "note": "\n\n📊 *Mínimo: $20 • Máximo: $10,000*",
            },
        }
        t = translations.get(language, translations["en"])

        if error:
            content = f"{t['error']}{t['question']}{t['hint']}{t['note']}"
        else:
            content = f"{t['title']}{t['question']}{t['hint']}{t['note']}"

        return {
            "content": content,
            "enrichment": {"buy_flow": "step2_amount", "crypto": crypto},
            "requires_registration": not is_authenticated,
            "pending_action": "buy_awaiting_amount",
            "buy_info": buy_info,
        }

    async def _get_crypto_price(self, symbol: str) -> float:
        """Get real-time crypto price from CoinGecko."""
        coin_id = self._coin_id_map.get(symbol)
        if not coin_id:
            logger.warning(f"No CoinGecko mapping for {symbol}, using fallback price")
            return 100.0

        try:
            price_data = await self._coingecko.get_price(coin_id)
            logger.info(f"Fetched real price for {symbol}: ${price_data.usd:.2f}")
            return price_data.usd
        except Exception as e:
            logger.warning(f"Failed to fetch price for {symbol} from CoinGecko: {e}")
            # Fallback to approximate prices
            fallback_prices = {
                "BTC": 45000,
                "ETH": 1950,
                "SOL": 32.5,
                "USDC": 1.0,
                "USDT": 1.0,
                "MATIC": 0.65,
            }
            return fallback_prices.get(symbol, 100.0)

    async def _show_quote_and_confirm(
        self, buy_info: dict, language: str, is_authenticated: bool
    ) -> dict:
        """Show quote and ask for confirmation (USDC only)."""
        crypto = "USDC"  # Always USDC
        buy_info["crypto"] = crypto
        amount_usd = buy_info.get("amount", "100")

        emoji = "💵"

        # USDC is pegged 1:1 to USD
        price_per_unit = 1.0

        try:
            usd = float(amount_usd)
            crypto_amount = usd / price_per_unit
            processing_fee = usd * 0.0299  # 2.99% MoonPay fee
            total_usd = usd + processing_fee
        except ValueError:
            crypto_amount = 1.0
            processing_fee = 3.0
            total_usd = 103.0

        translations = {
            "en": {
                "title": "💳 **Your Buy Quote**\n\n",
                "divider": "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n",
                "you_pay": f"💵 **You Pay:** ${usd:.2f} USD",
                "you_receive": f"💎 **You Receive:** ~{crypto_amount:.6f} {crypto} {emoji}",
                "fee_label": "⚡ **Processing Fee (2.99%):**",
                "total_label": "💰 **Total Charge:**",
            },
            "es": {
                "title": "💳 **Tu Cotización de Compra**\n\n",
                "divider": "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n",
                "you_pay": f"💵 **Pagas:** ${usd:.2f} USD",
                "you_receive": f"💎 **Recibes:** ~{crypto_amount:.6f} {crypto} {emoji}",
                "fee_label": "⚡ **Tarifa de Procesamiento (2.99%):**",
                "total_label": "💰 **Cargo Total:**",
            },
            "pt": {
                "title": "💳 **Sua Cotação de Compra**\n\n",
                "divider": "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n",
                "you_pay": f"💵 **Você Paga:** ${usd:.2f} USD",
                "you_receive": f"💎 **Você Recebe:** ~{crypto_amount:.6f} {crypto} {emoji}",
                "fee_label": "⚡ **Taxa de Processamento (2.99%):**",
                "total_label": "💰 **Total:**",
            },
            "zh": {
                "title": "💳 **您的购买报价**\n\n",
                "divider": "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n",
                "you_pay": f"💵 **您支付：** ${usd:.2f} USD",
                "you_receive": f"💎 **您收到：** ~{crypto_amount:.6f} {crypto} {emoji}",
                "fee_label": "⚡ **手续费 (2.99%)：**",
                "total_label": "💰 **总计：**",
            },
        }
        t = translations.get(language, translations["en"])

        # Build content - no reply instructions (frontend shows card with execute_data)
        content = f"{t['title']}{t['divider']}"
        content += f"{t['you_pay']}\n"
        content += f"{t['you_receive']}\n\n"
        content += f"{t['fee_label']} ${processing_fee:.2f}\n"
        content += f"{t['total_label']} ${total_usd:.2f}"

        return {
            "content": content,
            "enrichment": {
                "buy_flow": "step3_confirmation",
                "crypto": crypto.lower(),
                "amount_usd": amount_usd,
                "crypto_amount": f"{crypto_amount:.6f}",
                "total_usd": f"{total_usd:.2f}",
                "quote": {
                    "price_per_unit": price_per_unit,
                    "processing_fee": processing_fee,
                },
            },
            "requires_registration": not is_authenticated,
            "pending_action": "buy_awaiting_confirmation",
            "buy_info": buy_info,
        }

    def _execute_buy(
        self, buy_info: dict, language: str, is_authenticated: bool
    ) -> dict:
        """Execute buy (requires authentication)."""
        crypto = buy_info.get("crypto", "").upper()
        amount = buy_info.get("amount", "100")

        translations = {
            "en": {
                "title": "🎉 **Purchase Confirmed!**\n\n",
                "summary": f"You're buying ${amount} USD worth of {crypto}\n\n",
                "divider": "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n",
                "next_step": "**Next: Complete Your Purchase**\n\n",
                "signup": "To execute this purchase securely with MoonPay:\n\n👉 **Sign Up Now** - Takes just 2 minutes!\n\n",
                "saved": "✨ Your quote is saved and ready to go once you're registered.\n\n",
                "secure": "🔒 *Secure Payment • Licensed Provider • Instant Delivery*",
            },
            "es": {
                "title": "🎉 **¡Compra Confirmada!**\n\n",
                "summary": f"Estás comprando ${amount} USD de {crypto}\n\n",
                "divider": "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n",
                "next_step": "**Siguiente: Completa tu Compra**\n\n",
                "signup": "Para ejecutar esta compra de forma segura con MoonPay:\n\n👉 **Regístrate Ahora** - ¡Solo toma 2 minutos!\n\n",
                "saved": "✨ Tu cotización está guardada y lista una vez que te registres.\n\n",
                "secure": "🔒 *Pago Seguro • Proveedor Licenciado • Entrega Instantánea*",
            },
        }
        t = translations.get(language, translations["en"])

        content = f"{t['title']}{t['summary']}{t['divider']}{t['next_step']}"
        if not is_authenticated:
            content += t["signup"]
        content += f"{t['saved']}{t['secure']}"

        return {
            "content": content,
            "enrichment": {
                "buy_flow": "execution",
                "crypto": crypto.lower(),
                "amount_usd": amount,
            },
            "requires_registration": not is_authenticated,
        }

    def _cancel_buy(self, language: str) -> dict:
        """Cancel buy operation."""
        translations = {
            "en": {
                "title": "❌ **Purchase Cancelled**\n\n",
                "message": "No problem! Your purchase has been cancelled.\n\n",
                "restart": '💡 *Want to start over? Just type "buy" anytime!*',
            },
            "es": {
                "title": "❌ **Compra Cancelada**\n\n",
                "message": "¡No hay problema! Tu compra ha sido cancelada.\n\n",
                "restart": '💡 *¿Quieres empezar de nuevo? ¡Solo escribe "buy" en cualquier momento!*',
            },
        }
        t = translations.get(language, translations["en"])

        return {
            "content": f"{t['title']}{t['message']}{t['restart']}",
            "enrichment": {"buy_flow": "cancelled"},
            "requires_registration": False,
        }

    async def _handle_edit(
        self, content: str, buy_info: dict, language: str, is_authenticated: bool
    ) -> dict:
        """Handle edit request."""
        # Extract new amount if mentioned
        if "amount" in content.lower():
            new_amount = self._extract_amount(content)
            if new_amount:
                buy_info["amount"] = new_amount
                return await self._show_quote_and_confirm(
                    buy_info, language, is_authenticated
                )

        # Generic edit response
        return self._ask_for_amount(buy_info, language, is_authenticated)

    def _show_help(self, language: str, is_authenticated: bool) -> dict:
        """Show help/available options (USDC only)."""
        return self._ask_for_usdc_amount(language, is_authenticated)
