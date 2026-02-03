"""
Multi-step MoonPay Swap Flow Handler.

Implements conversational swap flow with:
- Step-by-step parameter collection
- Confirmation before execution
- Edit capabilities
- State preservation across messages
"""

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


class MoonPaySwapMultiStepHandler:
    """Handles multi-step conversational flow for MoonPay swaps."""

    MOONPAY_TOKENS = {
        "btc": "btc",
        "bitcoin": "btc",
        "eth": "eth",
        "ethereum": "eth",
        "ether": "eth",
        "sol": "sol",
        "solana": "sol",
        "usdc": "usdc",
    }

    def __init__(self, moonpay_swap_handler):
        """Initialize with MoonPay swap handler."""
        self._moonpay_handler = moonpay_swap_handler

    async def handle_flow(
        self,
        content: str,
        language: str,
        is_authenticated: bool,
        continuation_step: str | None = None,
        previous_swap_info: dict | None = None,
    ) -> dict[str, Any]:
        """
        Handle multi-step swap flow.

        Flow:
        1. User: "swap" → Ask for FROM token
        2. User: "BTC" → Ask for TO token
        3. User: "ETH" → Ask for amount
        4. User: "1" → Show quote, ask confirmation
        5. User: "confirm" → Execute (requires auth)
        6. User: "change amount to 0.5" → Re-quote
        """
        content_lower = content.lower().strip()

        # Initialize or load swap info
        swap_info = previous_swap_info or {}

        # Handle continuation steps
        if continuation_step:
            return await self._handle_continuation(
                content, content_lower, language, is_authenticated, continuation_step, swap_info
            )

        # Parse complete swap request (e.g., "swap 1 BTC to ETH")
        parsed = self._parse_swap_request(content)
        if parsed["from_token"] and parsed["to_token"]:
            # Complete info provided
            swap_info.update(parsed)
            if not parsed.get("amount"):
                # Has tokens but no amount
                return self._ask_for_amount(swap_info, language, is_authenticated)
            else:
                # Has everything, show quote and ask confirmation
                return await self._show_quote_and_confirm(swap_info, language, is_authenticated)

        # Initial "swap" command - start flow
        if any(kw in content_lower for kw in ["swap", "exchange", "convert", "trade"]):
            return self._ask_for_from_token(language, is_authenticated)

        # Fallback: show available pairs
        return await self._show_available_pairs(language, is_authenticated)

    async def _handle_continuation(
        self,
        content: str,
        content_lower: str,
        language: str,
        is_authenticated: bool,
        step: str,
        swap_info: dict,
    ) -> dict[str, Any]:
        """Handle continuation from previous step."""

        # Handle confirmation
        if step == "swap_awaiting_confirmation":
            if any(kw in content_lower for kw in ["confirm", "yes", "ok", "proceed", "go", "sí", "sim"]):
                return self._execute_swap(swap_info, language, is_authenticated)
            elif any(kw in content_lower for kw in ["cancel", "no", "stop", "cancelar"]):
                return self._cancel_swap(language)
            elif "change" in content_lower or "edit" in content_lower or "modify" in content_lower:
                # Parse what to change
                return await self._handle_edit(content, swap_info, language, is_authenticated)

        # Handle amount input
        if step == "swap_awaiting_amount":
            amount = self._extract_amount(content)
            if amount:
                swap_info["amount"] = amount
                return await self._show_quote_and_confirm(swap_info, language, is_authenticated)
            else:
                return self._ask_for_amount(swap_info, language, is_authenticated, error=True)

        # Handle TO token input
        if step == "swap_awaiting_to_token":
            to_token = self._extract_token(content)
            if to_token:
                swap_info["to_token"] = to_token
                return self._ask_for_amount(swap_info, language, is_authenticated)
            else:
                return self._ask_for_to_token(swap_info, language, is_authenticated, error=True)

        # Handle FROM token input
        if step == "swap_awaiting_from_token":
            from_token = self._extract_token(content)
            if from_token:
                swap_info["from_token"] = from_token
                return self._ask_for_to_token(swap_info, language, is_authenticated)
            else:
                return self._ask_for_from_token(language, is_authenticated, error=True)

        # Unknown step
        return await self._show_available_pairs(language, is_authenticated)

    def _parse_swap_request(self, content: str) -> dict:
        """Parse swap request to extract tokens and amount."""
        result = {"from_token": None, "to_token": None, "amount": None}

        # Pattern: "swap 1 BTC to ETH" or "BTC to ETH 1"
        pattern = re.compile(
            r'(?:swap|exchange|convert|trade)?\s*(?:(\d+\.?\d*)\s+)?(\w+)\s+(?:to|for|into)\s+(\w+)(?:\s+(\d+\.?\d*))?',
            re.IGNORECASE
        )
        match = pattern.search(content)

        if match:
            amount_start = match.group(1)
            token1 = match.group(2).lower()
            token2 = match.group(3).lower()
            amount_end = match.group(4)

            result["from_token"] = self.MOONPAY_TOKENS.get(token1)
            result["to_token"] = self.MOONPAY_TOKENS.get(token2)
            result["amount"] = amount_start or amount_end

        return result

    def _extract_token(self, content: str) -> str | None:
        """Extract token from content."""
        content_lower = content.lower().strip()
        for alias, symbol in self.MOONPAY_TOKENS.items():
            if alias in content_lower:
                return symbol
        return None

    def _extract_amount(self, content: str) -> str | None:
        """Extract amount from content."""
        match = re.search(r'(\d+\.?\d*)', content)
        return match.group(1) if match else None

    # Response builders
    def _ask_for_from_token(self, language: str, is_authenticated: bool, error: bool = False) -> dict:
        """Ask user which token to swap FROM."""
        translations = {
            "en": {
                "error": "❌ Hmm, I didn't recognize that token. Let's try again!\n\n",
                "title": "🔄 **Let's Start Your Swap!**\n\n",
                "intro": "Great choice! Swapping crypto is easy with MoonPay.\n\n",
                "question": "**Step 1 of 4:** Which crypto do you want to swap FROM?\n\n",
                "options": "💎 Available tokens:\n• **BTC** (Bitcoin)\n• **ETH** (Ethereum)\n• **SOL** (Solana)\n• **USDC** (USD Coin)\n\n💡 *Just type the token symbol, like \"BTC\"*",
            },
            "es": {
                "error": "❌ Hmm, no reconocí ese token. ¡Intentemos de nuevo!\n\n",
                "title": "🔄 **¡Comencemos tu Swap!**\n\n",
                "intro": "¡Excelente elección! Intercambiar cripto es fácil con MoonPay.\n\n",
                "question": "**Paso 1 de 4:** ¿Qué cripto quieres intercambiar?\n\n",
                "options": "💎 Tokens disponibles:\n• **BTC** (Bitcoin)\n• **ETH** (Ethereum)\n• **SOL** (Solana)\n• **USDC** (USD Coin)\n\n💡 *Solo escribe el símbolo, como \"BTC\"*",
            },
        }
        t = translations.get(language, translations["en"])

        if error:
            content = f"{t['error']}{t['question']}{t['options']}"
        else:
            content = f"{t['title']}{t['intro']}{t['question']}{t['options']}"

        return {
            "content": content,
            "enrichment": {"swap_flow": "step1_from_token"},
            "requires_registration": not is_authenticated,
            "pending_action": "swap_awaiting_from_token",
            "swap_info": {},
        }

    def _ask_for_to_token(self, swap_info: dict, language: str, is_authenticated: bool, error: bool = False) -> dict:
        """Ask user which token to swap TO."""
        from_token = swap_info.get("from_token", "").upper()

        # Token emoji mapping
        token_emoji = {"BTC": "₿", "ETH": "Ξ", "SOL": "◎", "USDC": "💵"}
        from_emoji = token_emoji.get(from_token, "💎")

        translations = {
            "en": {
                "error": "❌ Oops! I didn't catch that token. Let's try again.\n\n",
                "title": f"✨ **Perfect! You're swapping {from_emoji} {from_token}**\n\n",
                "question": f"**Step 2 of 4:** What crypto would you like to receive?\n\n",
                "options": "💎 Available tokens:\n• **BTC** ₿ Bitcoin\n• **ETH** Ξ Ethereum\n• **SOL** ◎ Solana\n• **USDC** 💵 USD Coin\n\n💡 *Type the token you want to get, like \"ETH\"*",
            },
            "es": {
                "error": "❌ ¡Ups! No reconocí ese token. Intentemos de nuevo.\n\n",
                "title": f"✨ **¡Perfecto! Vas a intercambiar {from_emoji} {from_token}**\n\n",
                "question": f"**Paso 2 de 4:** ¿Qué cripto te gustaría recibir?\n\n",
                "options": "💎 Tokens disponibles:\n• **BTC** ₿ Bitcoin\n• **ETH** Ξ Ethereum\n• **SOL** ◎ Solana\n• **USDC** 💵 USD Coin\n\n💡 *Escribe el token que quieres recibir, como \"ETH\"*",
            },
        }
        t = translations.get(language, translations["en"])

        if error:
            content = f"{t['error']}{t['question']}{t['options']}"
        else:
            content = f"{t['title']}{t['question']}{t['options']}"

        return {
            "content": content,
            "enrichment": {"swap_flow": "step2_to_token", "from_token": from_token},
            "requires_registration": not is_authenticated,
            "pending_action": "swap_awaiting_to_token",
            "swap_info": swap_info,
        }

    def _ask_for_amount(self, swap_info: dict, language: str, is_authenticated: bool, error: bool = False) -> dict:
        """Ask user how much to swap."""
        from_token = swap_info.get("from_token", "").upper()
        to_token = swap_info.get("to_token", "").upper()

        # Token emoji mapping
        token_emoji = {"BTC": "₿", "ETH": "Ξ", "SOL": "◎", "USDC": "💵"}
        from_emoji = token_emoji.get(from_token, "💎")
        to_emoji = token_emoji.get(to_token, "💎")

        translations = {
            "en": {
                "error": "❌ Hmm, that doesn't look like a valid amount. Let's try again!\n\n",
                "title": f"🎯 **Almost There!**\n\n",
                "swap_direction": f"Swapping {from_emoji} **{from_token}** → {to_emoji} **{to_token}**\n\n",
                "question": f"**Step 3 of 4:** How much {from_token} would you like to swap?\n\n",
                "hint": f"💡 *Just enter a number, like:*\n• `1` (one {from_token})\n• `0.5` (half a {from_token})\n• `100` (one hundred {from_token})",
            },
            "es": {
                "error": "❌ Hmm, eso no parece una cantidad válida. ¡Intentemos de nuevo!\n\n",
                "title": f"🎯 **¡Casi Listo!**\n\n",
                "swap_direction": f"Intercambiando {from_emoji} **{from_token}** → {to_emoji} **{to_token}**\n\n",
                "question": f"**Paso 3 de 4:** ¿Cuánto {from_token} te gustaría intercambiar?\n\n",
                "hint": f"💡 *Solo ingresa un número, como:*\n• `1` (un {from_token})\n• `0.5` (medio {from_token})\n• `100` (cien {from_token})",
            },
        }
        t = translations.get(language, translations["en"])

        if error:
            content = f"{t['error']}{t['swap_direction']}{t['question']}{t['hint']}"
        else:
            content = f"{t['title']}{t['swap_direction']}{t['question']}{t['hint']}"

        return {
            "content": content,
            "enrichment": {"swap_flow": "step3_amount", "from_token": from_token, "to_token": to_token},
            "requires_registration": not is_authenticated,
            "pending_action": "swap_awaiting_amount",
            "swap_info": swap_info,
        }

    async def _show_quote_and_confirm(self, swap_info: dict, language: str, is_authenticated: bool) -> dict:
        """Show quote and ask for confirmation."""
        from_token = swap_info.get("from_token")
        to_token = swap_info.get("to_token")
        amount = swap_info.get("amount", "1")

        try:
            # Get quote from MoonPay
            result = await self._moonpay_handler.get_swap_quote(
                from_currency=from_token,
                to_currency=to_token,
                amount=amount,
                language=language
            )

            # Extract quote info
            quote = result.quote if hasattr(result, "quote") else {}
            quote_amount = quote.get("quoteCurrencyAmount", "N/A")
            exchange_rate = quote.get("exchangeRate", "N/A")
            network_fee = quote.get("networkFee", "N/A")

            # Token emoji mapping
            token_emoji = {"btc": "₿", "eth": "Ξ", "sol": "◎", "usdc": "💵"}
            from_emoji = token_emoji.get(from_token, "💎")
            to_emoji = token_emoji.get(to_token, "💎")

            translations = {
                "en": {
                    "title": "🌙 **Your MoonPay Swap Quote**\n\n",
                    "divider": "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n",
                    "you_send": f"📤 **You Send:** {amount} {from_token.upper()} {from_emoji}",
                    "you_receive": f"📥 **You Receive:** ~{quote_amount} {to_token.upper()} {to_emoji}",
                    "rate_label": "💱 **Exchange Rate:**",
                    "fee_label": "⚡ **Network Fee:**",
                },
                "es": {
                    "title": "🌙 **Tu Cotización MoonPay**\n\n",
                    "divider": "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n",
                    "you_send": f"📤 **Envías:** {amount} {from_token.upper()} {from_emoji}",
                    "you_receive": f"📥 **Recibes:** ~{quote_amount} {to_token.upper()} {to_emoji}",
                    "rate_label": "💱 **Tasa de Cambio:**",
                    "fee_label": "⚡ **Tarifa de Red:**",
                },
                "pt": {
                    "title": "🌙 **Sua Cotação MoonPay**\n\n",
                    "divider": "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n",
                    "you_send": f"📤 **Você Envia:** {amount} {from_token.upper()} {from_emoji}",
                    "you_receive": f"📥 **Você Recebe:** ~{quote_amount} {to_token.upper()} {to_emoji}",
                    "rate_label": "💱 **Taxa de Câmbio:**",
                    "fee_label": "⚡ **Taxa de Rede:**",
                },
                "zh": {
                    "title": "🌙 **您的 MoonPay 交换报价**\n\n",
                    "divider": "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n",
                    "you_send": f"📤 **您发送：** {amount} {from_token.upper()} {from_emoji}",
                    "you_receive": f"📥 **您收到：** ~{quote_amount} {to_token.upper()} {to_emoji}",
                    "rate_label": "💱 **汇率：**",
                    "fee_label": "⚡ **网络费用：**",
                },
            }
            t = translations.get(language, translations["en"])

            # Build content - no reply instructions (frontend shows card with execute_data)
            content = f"{t['title']}{t['divider']}"
            content += f"{t['you_send']}\n"
            content += f"{t['you_receive']}\n\n"
            content += f"{t['rate_label']} {exchange_rate}\n"
            content += f"{t['fee_label']} ${network_fee}"

            return {
                "content": content,
                "enrichment": {
                    "swap_flow": "step4_confirmation",
                    "from_token": from_token,
                    "to_token": to_token,
                    "amount": amount,
                    "quote": quote,
                },
                "requires_registration": not is_authenticated,
                "pending_action": "swap_awaiting_confirmation",
                "swap_info": swap_info,
            }

        except Exception as e:
            logger.error(f"Error getting quote: {e}")
            return {
                "content": f"⚠️ Unable to get quote for {from_token.upper()} → {to_token.upper()}. Please try again.",
                "enrichment": {},
                "requires_registration": not is_authenticated,
            }

    def _execute_swap(self, swap_info: dict, language: str, is_authenticated: bool) -> dict:
        """Execute swap (requires authentication)."""
        from_token = swap_info.get("from_token", "").upper()
        to_token = swap_info.get("to_token", "").upper()
        amount = swap_info.get("amount", "")

        # Token emoji mapping
        token_emoji = {"BTC": "₿", "ETH": "Ξ", "SOL": "◎", "USDC": "💵"}
        from_emoji = token_emoji.get(from_token, "💎")
        to_emoji = token_emoji.get(to_token, "💎")

        translations = {
            "en": (
                "🎉 **Awesome! Swap Confirmed!**\n\n"
                f"You're all set to swap **{amount} {from_token}** {from_emoji} → {to_emoji} **{to_token}**\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "**Next Step: Create Your Account**\n\n"
                "To complete this swap securely with MoonPay, you'll need to sign up:\n\n"
                "👉 **Sign Up Now** - Takes just 2 minutes!\n\n"
                "✨ Your swap quote is saved and ready to go once you're registered.\n\n"
                "🔒 *Secure • Fast • Easy*"
            ),
            "es": (
                "🎉 **¡Genial! ¡Swap Confirmado!**\n\n"
                f"Estás listo para intercambiar **{amount} {from_token}** {from_emoji} → {to_emoji} **{to_token}**\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "**Siguiente Paso: Crea Tu Cuenta**\n\n"
                "Para completar este swap de forma segura con MoonPay, necesitas registrarte:\n\n"
                "👉 **Regístrate Ahora** - ¡Solo toma 2 minutos!\n\n"
                "✨ Tu cotización está guardada y lista una vez que te registres.\n\n"
                "🔒 *Seguro • Rápido • Fácil*"
            ),
        }

        return {
            "content": translations.get(language, translations["en"]),
            "enrichment": {"swap_flow": "execution", "action": "open_swap_modal"},
            "requires_registration": True,
        }

    def _cancel_swap(self, language: str) -> dict:
        """Cancel swap."""
        translations = {
            "en": "❌ Swap cancelled. Start a new swap anytime!",
            "es": "❌ Swap cancelado. ¡Inicia un nuevo swap cuando quieras!",
        }

        return {
            "content": translations.get(language, translations["en"]),
            "enrichment": {},
            "requires_registration": False,
        }

    async def _handle_edit(self, content: str, swap_info: dict, language: str, is_authenticated: bool) -> dict:
        """Handle edit request."""
        # Extract new amount if mentioned
        if "amount" in content.lower():
            new_amount = self._extract_amount(content)
            if new_amount:
                swap_info["amount"] = new_amount
                # Re-show quote
                return await self._show_quote_and_confirm(swap_info, language, is_authenticated)

        # Generic edit response
        return self._ask_for_amount(swap_info, language, is_authenticated)

    async def _show_available_pairs(self, language: str, is_authenticated: bool) -> dict:
        """Show available swap pairs."""
        result = await self._moonpay_handler.get_available_pairs(language=language)
        return {
            "content": result.content,
            "enrichment": result.__dict__ if hasattr(result, "__dict__") else {},
            "requires_registration": not is_authenticated,
        }
