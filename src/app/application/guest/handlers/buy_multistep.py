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
    """Handles multi-step conversational flow for buying crypto."""

    SUPPORTED_CRYPTOS = {
        "btc": {"symbol": "BTC", "name": "Bitcoin", "emoji": "₿"},
        "bitcoin": {"symbol": "BTC", "name": "Bitcoin", "emoji": "₿"},
        "eth": {"symbol": "ETH", "name": "Ethereum", "emoji": "Ξ"},
        "ethereum": {"symbol": "ETH", "name": "Ethereum", "emoji": "Ξ"},
        "ether": {"symbol": "ETH", "name": "Ethereum", "emoji": "Ξ"},
        "sol": {"symbol": "SOL", "name": "Solana", "emoji": "◎"},
        "solana": {"symbol": "SOL", "name": "Solana", "emoji": "◎"},
        "usdc": {"symbol": "USDC", "name": "USD Coin", "emoji": "💵"},
        "usdt": {"symbol": "USDT", "name": "Tether", "emoji": "💵"},
        "matic": {"symbol": "MATIC", "name": "Polygon", "emoji": "🔷"},
        "polygon": {"symbol": "MATIC", "name": "Polygon", "emoji": "🔷"},
    }

    def __init__(self):
        """Initialize buy multi-step handler."""
        self._coingecko = CoinGeckoClient()
        # CoinGecko coin ID mapping
        self._coin_id_map = {
            "BTC": "bitcoin",
            "ETH": "ethereum",
            "SOL": "solana",
            "USDC": "usd-coin",
            "USDT": "tether",
            "MATIC": "matic-network",
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
        Handle multi-step buy flow.

        Flow:
        1. User: "buy" → Ask for crypto
        2. User: "ETH" → Ask for amount
        3. User: "100" → Show quote, ask confirmation
        4. User: "confirm" → Execute (requires auth)
        """
        content_lower = content.lower().strip()

        # Initialize or load buy info
        buy_info = previous_buy_info or {}

        # Handle continuation steps
        if continuation_step:
            return await self._handle_continuation(
                content, content_lower, language, is_authenticated, continuation_step, buy_info
            )

        # Parse complete buy request (e.g., "buy 100 USD of ETH")
        parsed = self._parse_buy_request(content)
        if parsed["crypto"] and parsed["amount"]:
            # Complete info provided
            buy_info.update(parsed)
            return await self._show_quote_and_confirm(buy_info, language, is_authenticated)
        elif parsed["crypto"]:
            # Has crypto but no amount
            buy_info.update(parsed)
            return self._ask_for_amount(buy_info, language, is_authenticated)

        # Initial "buy" command - start flow
        if any(kw in content_lower for kw in ["buy", "purchase", "on-ramp", "onramp"]):
            return self._ask_for_crypto(language, is_authenticated)

        # Fallback: show available options
        return self._show_help(language, is_authenticated)

    async def _handle_continuation(
        self,
        content: str,
        content_lower: str,
        language: str,
        is_authenticated: bool,
        step: str,
        buy_info: dict,
    ) -> dict[str, Any]:
        """Handle continuation from previous step."""

        # Handle confirmation
        if step == "buy_awaiting_confirmation":
            if any(kw in content_lower for kw in ["confirm", "yes", "ok", "proceed", "go", "buy", "sí", "sim"]):
                return self._execute_buy(buy_info, language, is_authenticated)
            elif any(kw in content_lower for kw in ["cancel", "no", "stop", "cancelar"]):
                return self._cancel_buy(language)
            elif "change" in content_lower or "edit" in content_lower:
                return await self._handle_edit(content, buy_info, language, is_authenticated)

        # Handle amount input
        if step == "buy_awaiting_amount":
            amount = self._extract_amount(content)
            if amount:
                buy_info["amount"] = amount
                return await self._show_quote_and_confirm(buy_info, language, is_authenticated)
            else:
                return self._ask_for_amount(buy_info, language, is_authenticated, error=True)

        # Handle crypto input
        if step == "buy_awaiting_crypto":
            crypto = self._extract_crypto(content)
            if crypto:
                buy_info["crypto"] = crypto
                return self._ask_for_amount(buy_info, language, is_authenticated)
            else:
                return self._ask_for_crypto(language, is_authenticated, error=True)

        # Unknown step
        return self._show_help(language, is_authenticated)

    def _parse_buy_request(self, content: str) -> dict:
        """Parse buy request to extract crypto and amount."""
        result = {"crypto": None, "amount": None}

        # Pattern: "buy 100 USD of ETH" or "buy ETH 100"
        pattern = re.compile(
            r'(?:buy|purchase)\s+(?:(\d+\.?\d*)\s+)?(?:usd|dollars?\s+)?(?:of\s+)?(\w+)|(\w+)\s+(?:for\s+)?(\d+\.?\d*)',
            re.IGNORECASE
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
                result["crypto"] = self.SUPPORTED_CRYPTOS.get(crypto.lower(), {}).get("symbol")
            if amount:
                result["amount"] = amount

        return result

    def _extract_crypto(self, content: str) -> str | None:
        """Extract crypto from content."""
        content_lower = content.lower().strip()
        for alias, data in self.SUPPORTED_CRYPTOS.items():
            if alias in content_lower:
                return data["symbol"]
        return None

    def _extract_amount(self, content: str) -> str | None:
        """Extract amount from content."""
        match = re.search(r'(\d+\.?\d*)', content)
        return match.group(1) if match else None

    def _ask_for_crypto(self, language: str, is_authenticated: bool, error: bool = False) -> dict:
        """Ask user which crypto to buy."""
        translations = {
            "en": {
                "error": "❌ Hmm, I don't recognize that crypto. Let's try again!\n\n",
                "title": "💳 **Buy Crypto with Fiat**\n\n",
                "greeting": "Let's get you some crypto! 🚀\n\n",
                "question": "**Step 1 of 3:** Which crypto would you like to buy?\n\n",
                "options": "💎 Available options:\n• **BTC** ₿ Bitcoin\n• **ETH** Ξ Ethereum\n• **SOL** ◎ Solana\n• **USDC** 💵 USD Coin\n• **USDT** 💵 Tether\n• **MATIC** 🔷 Polygon\n\n💡 *Type the crypto symbol, like \"ETH\"*",
            },
            "es": {
                "error": "❌ Hmm, no reconozco esa cripto. ¡Intentemos de nuevo!\n\n",
                "title": "💳 **Comprar Cripto con Fiat**\n\n",
                "greeting": "¡Consigamos algo de cripto! 🚀\n\n",
                "question": "**Paso 1 de 3:** ¿Qué cripto te gustaría comprar?\n\n",
                "options": "💎 Opciones disponibles:\n• **BTC** ₿ Bitcoin\n• **ETH** Ξ Ethereum\n• **SOL** ◎ Solana\n• **USDC** 💵 USD Coin\n• **USDT** 💵 Tether\n• **MATIC** 🔷 Polygon\n\n💡 *Escribe el símbolo de cripto, como \"ETH\"*",
            },
        }
        t = translations.get(language, translations["en"])

        if error:
            content = f"{t['error']}{t['question']}{t['options']}"
        else:
            content = f"{t['title']}{t['greeting']}{t['question']}{t['options']}"

        return {
            "content": content,
            "enrichment": {"buy_flow": "step1_crypto"},
            "requires_registration": not is_authenticated,
            "pending_action": "buy_awaiting_crypto",
            "buy_info": {},
        }

    def _ask_for_amount(self, buy_info: dict, language: str, is_authenticated: bool, error: bool = False) -> dict:
        """Ask user how much to buy."""
        crypto = buy_info.get("crypto", "").upper()

        # Crypto emoji mapping
        crypto_emoji = {
            "BTC": "₿", "ETH": "Ξ", "SOL": "◎",
            "USDC": "💵", "USDT": "💵", "MATIC": "🔷"
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
                "BTC": 45000, "ETH": 1950, "SOL": 32.5,
                "USDC": 1.0, "USDT": 1.0, "MATIC": 0.65
            }
            return fallback_prices.get(symbol, 100.0)

    async def _show_quote_and_confirm(self, buy_info: dict, language: str, is_authenticated: bool) -> dict:
        """Show quote and ask for confirmation."""
        crypto = buy_info.get("crypto", "").upper()
        amount_usd = buy_info.get("amount", "100")

        # Crypto emoji mapping
        crypto_emoji = {
            "BTC": "₿", "ETH": "Ξ", "SOL": "◎",
            "USDC": "💵", "USDT": "💵", "MATIC": "🔷"
        }
        emoji = crypto_emoji.get(crypto, "💎")

        # Get real-time price from CoinGecko
        price_per_unit = await self._get_crypto_price(crypto)

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
                "step": "**Step 3 of 3:** Review and confirm\n\n",
                "divider": "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n",
                "you_pay": f"💵 **You Pay:** ${usd:.2f} USD",
                "you_receive": f"💎 **You Receive:** ~{crypto_amount:.6f} {crypto} {emoji}",
                "price_label": "📊 **Price per {crypto}:**",
                "fee_label": "⚡ **Processing Fee (2.99%):**",
                "total_label": "💰 **Total Charge:**",
                "confirm_title": "\n**Ready to buy?**",
                "confirm_options": "\n✅ Reply `confirm` or `yes` to proceed\n📝 Reply `change amount to X` to adjust\n❌ Reply `cancel` to abort",
            },
            "es": {
                "title": "💳 **Tu Cotización de Compra**\n\n",
                "step": "**Paso 3 de 3:** Revisar y confirmar\n\n",
                "divider": "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n",
                "you_pay": f"💵 **Pagas:** ${usd:.2f} USD",
                "you_receive": f"💎 **Recibes:** ~{crypto_amount:.6f} {crypto} {emoji}",
                "price_label": "📊 **Precio por {crypto}:**",
                "fee_label": "⚡ **Tarifa de Procesamiento (2.99%):**",
                "total_label": "💰 **Cargo Total:**",
                "confirm_title": "\n**¿Listo para comprar?**",
                "confirm_options": "\n✅ Responde `confirmar` o `sí` para proceder\n📝 Responde `cambiar cantidad a X` para ajustar\n❌ Responde `cancelar` para abortar",
            },
        }
        t = translations.get(language, translations["en"])

        # Build content
        content = f"{t['title']}{t['step']}{t['divider']}"
        content += f"{t['you_pay']}\n"
        content += f"{t['you_receive']}\n\n"
        content += f"{t['price_label'].replace('{crypto}', crypto)} ${price_per_unit:.2f}\n"
        content += f"{t['fee_label']} ${processing_fee:.2f}\n"
        content += f"{t['total_label']} ${total_usd:.2f}\n"
        content += f"\n{t['divider']}"
        content += f"{t['confirm_title']}\n"
        content += t["confirm_options"]

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
                }
            },
            "requires_registration": not is_authenticated,
            "pending_action": "buy_awaiting_confirmation",
            "buy_info": buy_info,
        }

    def _execute_buy(self, buy_info: dict, language: str, is_authenticated: bool) -> dict:
        """Execute buy (requires authentication)."""
        crypto = buy_info.get("crypto", "").upper()
        amount = buy_info.get("amount", "100")

        translations = {
            "en": {
                "title": "🎉 **Purchase Confirmed!**\n\n",
                "summary": f"You're buying ${amount} USD worth of {crypto}\n\n",
                "divider": "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n",
                "next_step": "**Next: Complete Your Purchase**\n\n",
                "signup": "To execute this purchase securely with MoonPay:\n\n👉 **[Sign Up Now](/signup)** - Takes just 2 minutes!\n\n",
                "saved": "✨ Your quote is saved and ready to go once you're registered.\n\n",
                "secure": "🔒 *Secure Payment • Licensed Provider • Instant Delivery*",
            },
            "es": {
                "title": "🎉 **¡Compra Confirmada!**\n\n",
                "summary": f"Estás comprando ${amount} USD de {crypto}\n\n",
                "divider": "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n",
                "next_step": "**Siguiente: Completa tu Compra**\n\n",
                "signup": "Para ejecutar esta compra de forma segura con MoonPay:\n\n👉 **[Regístrate Ahora](/signup)** - ¡Solo toma 2 minutos!\n\n",
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
                "restart": "💡 *Want to start over? Just type \"buy\" anytime!*",
            },
            "es": {
                "title": "❌ **Compra Cancelada**\n\n",
                "message": "¡No hay problema! Tu compra ha sido cancelada.\n\n",
                "restart": "💡 *¿Quieres empezar de nuevo? ¡Solo escribe \"buy\" en cualquier momento!*",
            },
        }
        t = translations.get(language, translations["en"])

        return {
            "content": f"{t['title']}{t['message']}{t['restart']}",
            "enrichment": {"buy_flow": "cancelled"},
            "requires_registration": False,
        }

    async def _handle_edit(self, content: str, buy_info: dict, language: str, is_authenticated: bool) -> dict:
        """Handle edit request."""
        # Extract new amount if mentioned
        if "amount" in content.lower():
            new_amount = self._extract_amount(content)
            if new_amount:
                buy_info["amount"] = new_amount
                return await self._show_quote_and_confirm(buy_info, language, is_authenticated)

        # Generic edit response
        return self._ask_for_amount(buy_info, language, is_authenticated)

    def _show_help(self, language: str, is_authenticated: bool) -> dict:
        """Show help/available options."""
        return self._ask_for_crypto(language, is_authenticated)
