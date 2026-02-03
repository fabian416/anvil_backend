"""
Multi-step Send Flow Handler.

Implements conversational send flow with:
- Step-by-step parameter collection
- Security confirmation before execution
- Address validation
- State preservation across messages
"""

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


class SendMultiStepHandler:
    """Handles multi-step conversational flow for sending tokens."""

    SUPPORTED_TOKENS = {
        "btc": {"symbol": "BTC", "name": "Bitcoin", "emoji": "₿"},
        "bitcoin": {"symbol": "BTC", "name": "Bitcoin", "emoji": "₿"},
        "eth": {"symbol": "ETH", "name": "Ethereum", "emoji": "Ξ"},
        "ethereum": {"symbol": "ETH", "name": "Ethereum", "emoji": "Ξ"},
        "ether": {"symbol": "ETH", "name": "Ethereum", "emoji": "Ξ"},
        "sol": {"symbol": "SOL", "name": "Solana", "emoji": "◎"},
        "solana": {"symbol": "SOL", "name": "Solana", "emoji": "◎"},
        "usdc": {"symbol": "USDC", "name": "USD Coin", "emoji": "💵"},
    }

    def __init__(self, send_handler=None):
        """Initialize with send handler."""
        self._send_handler = send_handler

    async def handle_flow(
        self,
        content: str,
        language: str,
        is_authenticated: bool,
        continuation_step: str | None = None,
        previous_send_info: dict | None = None,
    ) -> dict[str, Any]:
        """
        Handle multi-step send flow.

        Flow:
        1. User: "send" → Ask for token
        2. User: "ETH" → Ask for amount
        3. User: "0.5" → Ask for destination address
        4. User: "0x123..." → Show review, ask confirmation
        5. User: "confirm" → Execute (requires auth)
        """
        content_lower = content.lower().strip()

        # Initialize or load send info
        send_info = previous_send_info or {}

        # Handle continuation steps
        if continuation_step:
            return await self._handle_continuation(
                content,
                content_lower,
                language,
                is_authenticated,
                continuation_step,
                send_info,
            )

        # Parse complete send request (e.g., "send 1 ETH to 0x123...")
        parsed = self._parse_send_request(content)
        if parsed["token"] and parsed["amount"] and parsed["address"]:
            # Complete info provided
            send_info.update(parsed)
            return await self._show_review_and_confirm(
                send_info, language, is_authenticated
            )
        elif parsed["token"] and parsed["amount"]:
            # Has token and amount, need address
            send_info.update(parsed)
            return self._ask_for_address(send_info, language, is_authenticated)
        elif parsed["token"]:
            # Has token only, need amount
            send_info.update(parsed)
            return self._ask_for_amount(send_info, language, is_authenticated)

        # Initial "send" command - start flow
        if any(
            kw in content_lower
            for kw in ["send", "transfer", "enviar", "envoyer", "发送"]
        ):
            return self._ask_for_token(language, is_authenticated)

        # Fallback
        return self._show_help(language, is_authenticated)

    async def _handle_continuation(
        self,
        content: str,
        content_lower: str,
        language: str,
        is_authenticated: bool,
        step: str,
        send_info: dict,
    ) -> dict[str, Any]:
        """Handle continuation from previous step."""

        # Handle confirmation
        if step == "send_awaiting_confirmation":
            if any(
                kw in content_lower
                for kw in [
                    "confirm",
                    "yes",
                    "ok",
                    "proceed",
                    "go",
                    "sí",
                    "sim",
                    "oui",
                    "是",
                ]
            ):
                return self._execute_send(send_info, language, is_authenticated)
            elif any(
                kw in content_lower
                for kw in ["cancel", "no", "stop", "cancelar", "non", "否"]
            ):
                return self._cancel_send(language)
            elif (
                "change" in content_lower
                or "edit" in content_lower
                or "modify" in content_lower
            ):
                # Allow editing any parameter
                return await self._handle_edit(
                    content, send_info, language, is_authenticated
                )

        # Handle address input
        if step == "send_awaiting_address":
            address = self._extract_address(content)
            if address:
                send_info["address"] = address
                send_info["network"] = self._detect_network(send_info["token"], address)
                return await self._show_review_and_confirm(
                    send_info, language, is_authenticated
                )
            else:
                return self._ask_for_address(
                    send_info, language, is_authenticated, error=True
                )

        # Handle amount input
        if step == "send_awaiting_amount":
            amount = self._extract_amount(content)
            if amount:
                send_info["amount"] = amount
                return self._ask_for_address(send_info, language, is_authenticated)
            else:
                return self._ask_for_amount(
                    send_info, language, is_authenticated, error=True
                )

        # Handle token input
        if step == "send_awaiting_token":
            token = self._extract_token(content)
            if token:
                send_info["token"] = token
                return self._ask_for_amount(send_info, language, is_authenticated)
            else:
                return self._ask_for_token(language, is_authenticated, error=True)

        # Unknown step
        return self._show_help(language, is_authenticated)

    def _parse_send_request(self, content: str) -> dict:
        """Parse send request to extract token, amount, and address."""
        result = {"token": None, "amount": None, "address": None}

        # Pattern: "send 1 ETH to 0x123..."
        pattern = re.compile(
            r"(?:send|transfer)?\s*(?:(\\d+\\.?\\d*)\\s+)?(\\w+)\\s+(?:to)?\\s*(0x[a-fA-F0-9]{40}|[a-zA-Z0-9]{32,44})?",
            re.IGNORECASE,
        )
        match = pattern.search(content)

        if match:
            amount = match.group(1)
            token = match.group(2).lower() if match.group(2) else None
            address = match.group(3)

            if token and token in self.SUPPORTED_TOKENS:
                result["token"] = self.SUPPORTED_TOKENS[token]["symbol"]
            if amount:
                result["amount"] = amount
            if address:
                result["address"] = address

        return result

    def _extract_token(self, content: str) -> str | None:
        """Extract token from content."""
        content_lower = content.lower().strip()
        for alias, token_info in self.SUPPORTED_TOKENS.items():
            if alias in content_lower:
                return token_info["symbol"]
        return None

    def _extract_amount(self, content: str) -> str | None:
        """Extract amount from content."""
        match = re.search(r"(\\d+\\.?\\d*)", content)
        return match.group(1) if match else None

    def _extract_address(self, content: str) -> str | None:
        """Extract wallet address from content."""
        # Ethereum address (0x + 40 hex chars)
        eth_match = re.search(r"(0x[a-fA-F0-9]{40})", content)
        if eth_match:
            return eth_match.group(1)

        # Bitcoin/Solana address (alphanumeric, 32-44 chars)
        other_match = re.search(
            r"\\b([13][a-km-zA-HJ-NP-Z1-9]{25,34}|bc1[a-z0-9]{39,59}|[1-9A-HJ-NP-Za-km-z]{32,44})\\b",
            content,
        )
        if other_match:
            return other_match.group(1)

        return None

    def _detect_network(self, token: str, address: str) -> str:
        """Detect blockchain network from token and address."""
        if address.startswith("0x"):
            return "Ethereum"
        elif token == "BTC":
            return "Bitcoin"
        elif token == "SOL":
            return "Solana"
        else:
            return "Ethereum"  # Default

    # Response builders
    def _ask_for_token(
        self, language: str, is_authenticated: bool, error: bool = False
    ) -> dict:
        """Ask user which token to send."""
        translations = {
            "en": {
                "error": "❌ Hmm, I didn't recognize that token. Let's try again!\\n\\n",
                "title": "📤 **Send Crypto Safely**\\n\\n",
                "intro": "Great! Let's send some crypto. I'll guide you through it step by step.\\n\\n",
                "question": "**Step 1 of 4:** Which crypto do you want to send?\\n\\n",
                "options": '💎 Available tokens:\\n• **BTC** ₿ Bitcoin\\n• **ETH** Ξ Ethereum\\n• **SOL** ◎ Solana\\n• **USDC** 💵 USD Coin\\n\\n💡 *Just type the token symbol, like \\"ETH\\"*',
            },
            "es": {
                "error": "❌ Hmm, no reconocí ese token. ¡Intentemos de nuevo!\\n\\n",
                "title": "📤 **Enviar Cripto de Forma Segura**\\n\\n",
                "intro": "¡Genial! Enviemos cripto. Te guiaré paso a paso.\\n\\n",
                "question": "**Paso 1 de 4:** ¿Qué cripto quieres enviar?\\n\\n",
                "options": '💎 Tokens disponibles:\\n• **BTC** ₿ Bitcoin\\n• **ETH** Ξ Ethereum\\n• **SOL** ◎ Solana\\n• **USDC** 💵 USD Coin\\n\\n💡 *Solo escribe el símbolo, como \\"ETH\\"*',
            },
        }
        t = translations.get(language, translations["en"])

        if error:
            content = f"{t['error']}{t['question']}{t['options']}"
        else:
            content = f"{t['title']}{t['intro']}{t['question']}{t['options']}"

        return {
            "content": content,
            "enrichment": {"send_flow": "step1_token"},
            "requires_registration": not is_authenticated,
            "pending_action": "send_awaiting_token",
            "send_info": {},
        }

    def _ask_for_amount(
        self,
        send_info: dict,
        language: str,
        is_authenticated: bool,
        error: bool = False,
    ) -> dict:
        """Ask user how much to send."""
        token = send_info.get("token", "")
        token_info = next(
            (t for t in self.SUPPORTED_TOKENS.values() if t["symbol"] == token), None
        )
        emoji = token_info["emoji"] if token_info else "💎"

        translations = {
            "en": {
                "error": "❌ Please enter a valid amount (number only).\\n\\n",
                "title": f"📤 **Sending {emoji} {token}**\\n\\n",
                "question": f"**Step 2 of 4:** How much {token} do you want to send?\\n\\n",
                "hint": f"💡 *Enter the amount:*\\n• Example: `0.5` (half a {token})\\n• Example: `1` (one {token})\\n• Example: `100` (one hundred {token})\\n\\n⚠️ **Important:** Make sure you have enough balance!",
            },
            "es": {
                "error": "❌ Por favor ingresa una cantidad válida (solo número).\\n\\n",
                "title": f"📤 **Enviando {emoji} {token}**\\n\\n",
                "question": f"**Paso 2 de 4:** ¿Cuánto {token} quieres enviar?\\n\\n",
                "hint": f"💡 *Ingresa la cantidad:*\\n• Ejemplo: `0.5` (medio {token})\\n• Ejemplo: `1` (un {token})\\n• Ejemplo: `100` (cien {token})\\n\\n⚠️ **Importante:** ¡Asegúrate de tener suficiente saldo!",
            },
        }
        t = translations.get(language, translations["en"])

        content = f"{t['error'] if error else ''}{t['title']}{t['question']}{t['hint']}"

        return {
            "content": content,
            "enrichment": {"send_flow": "step2_amount", "token": token},
            "requires_registration": not is_authenticated,
            "pending_action": "send_awaiting_amount",
            "send_info": send_info,
        }

    def _ask_for_address(
        self,
        send_info: dict,
        language: str,
        is_authenticated: bool,
        error: bool = False,
    ) -> dict:
        """Ask user for destination address."""
        token = send_info.get("token", "")
        amount = send_info.get("amount", "")
        token_info = next(
            (t for t in self.SUPPORTED_TOKENS.values() if t["symbol"] == token), None
        )
        emoji = token_info["emoji"] if token_info else "💎"

        translations = {
            "en": {
                "error": "❌ That doesn't look like a valid address. Please check and try again.\\n\\n",
                "title": f"📤 **Sending {amount} {emoji} {token}**\\n\\n",
                "question": f"**Step 3 of 4:** Where should I send this {token}?\\n\\n",
                "hint": f"💡 *Paste the destination wallet address:*\\n\\n⚠️ **CRITICAL WARNING:**\\n• Double-check the address carefully\\n• Sending to wrong address = permanent loss\\n• Copy-paste recommended (avoid typing)\\n• Make sure it's a {token} address\\n\\n*Waiting for address...*",
            },
            "es": {
                "error": "❌ Esa no parece una dirección válida. Por favor verifica e intenta de nuevo.\\n\\n",
                "title": f"📤 **Enviando {amount} {emoji} {token}**\\n\\n",
                "question": f"**Paso 3 de 4:** ¿A dónde debo enviar este {token}?\\n\\n",
                "hint": f"💡 *Pega la dirección de la billetera destino:*\\n\\n⚠️ **ADVERTENCIA CRÍTICA:**\\n• Verifica la dirección cuidadosamente\\n• Enviar a dirección incorrecta = pérdida permanente\\n• Se recomienda copiar-pegar (evita escribir)\\n• Asegúrate que sea una dirección {token}\\n\\n*Esperando dirección...*",
            },
        }
        t = translations.get(language, translations["en"])

        content = f"{t['error'] if error else ''}{t['title']}{t['question']}{t['hint']}"

        return {
            "content": content,
            "enrichment": {
                "send_flow": "step3_address",
                "token": token,
                "amount": amount,
            },
            "requires_registration": not is_authenticated,
            "pending_action": "send_awaiting_address",
            "send_info": send_info,
        }

    async def _show_review_and_confirm(
        self, send_info: dict, language: str, is_authenticated: bool
    ) -> dict:
        """Show transaction review and ask for confirmation."""
        token = send_info.get("token", "")
        amount = send_info.get("amount", "")
        address = send_info.get("address", "")
        network = send_info.get("network", "Unknown")

        token_info = next(
            (t for t in self.SUPPORTED_TOKENS.values() if t["symbol"] == token), None
        )
        emoji = token_info["emoji"] if token_info else "💎"

        # Truncate address for display
        display_address = (
            f"{address[:6]}...{address[-4:]}" if len(address) > 10 else address
        )

        translations = {
            "en": {
                "title": "🔍 **Review Your Transaction**\\n\\n",
                "divider": "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\\n\\n",
                "you_send": f"📤 **You're Sending:** {amount} {token} {emoji}",
                "destination": f"📍 **Destination:** `{display_address}`",
                "network": f"🌐 **Network:** {network}",
                "fee_estimate": "⚡ **Est. Network Fee:** ~$2.50 (varies)",
                "warning": "\\n⚠️ **WARNING:**\\n• Once confirmed, this transaction CANNOT be reversed\\n• Double-check the destination address\\n• Make sure you trust the recipient",
            },
            "es": {
                "title": "🔍 **Revisa Tu Transacción**\\n\\n",
                "divider": "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\\n\\n",
                "you_send": f"📤 **Vas a Enviar:** {amount} {token} {emoji}",
                "destination": f"📍 **Destino:** `{display_address}`",
                "network": f"🌐 **Red:** {network}",
                "fee_estimate": "⚡ **Tarifa Est. de Red:** ~$2.50 (varía)",
                "warning": "\\n⚠️ **ADVERTENCIA:**\\n• Una vez confirmado, esta transacción NO SE PUEDE REVERTIR\\n• Verifica la dirección de destino\\n• Asegúrate de confiar en el destinatario",
            },
            "pt": {
                "title": "🔍 **Revise Sua Transação**\\n\\n",
                "divider": "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\\n\\n",
                "you_send": f"📤 **Você Enviará:** {amount} {token} {emoji}",
                "destination": f"📍 **Destino:** `{display_address}`",
                "network": f"🌐 **Rede:** {network}",
                "fee_estimate": "⚡ **Taxa de Rede Est.:** ~$2.50 (varia)",
                "warning": "\\n⚠️ **AVISO:**\\n• Uma vez confirmado, esta transação NÃO PODE ser revertida\\n• Verifique o endereço de destino\\n• Certifique-se de confiar no destinatário",
            },
            "zh": {
                "title": "🔍 **审核您的交易**\\n\\n",
                "divider": "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\\n\\n",
                "you_send": f"📤 **您将发送：** {amount} {token} {emoji}",
                "destination": f"📍 **目标地址：** `{display_address}`",
                "network": f"🌐 **网络：** {network}",
                "fee_estimate": "⚡ **预计网络费用：** ~$2.50（变化）",
                "warning": "\\n⚠️ **警告：**\\n• 一旦确认，此交易无法撤销\\n• 仔细核对目标地址\\n• 确保您信任收款人",
            },
        }
        t = translations.get(language, translations["en"])

        # Build content - no reply instructions (frontend shows card with execute_data)
        content = f"{t['title']}{t['divider']}"
        content += f"{t['you_send']}\\n"
        content += f"{t['destination']}\\n"
        content += f"{t['network']}\\n"
        content += f"{t['fee_estimate']}"
        content += f"{t['warning']}"

        return {
            "content": content,
            "enrichment": {
                "send_flow": "step4_confirmation",
                "token": token,
                "amount": amount,
                "address": address,
                "network": network,
            },
            "requires_registration": not is_authenticated,
            "pending_action": "send_awaiting_confirmation",
            "send_info": send_info,
        }

    def _execute_send(
        self, send_info: dict, language: str, is_authenticated: bool
    ) -> dict:
        """Execute send transaction (requires authentication)."""
        token = send_info.get("token", "")
        amount = send_info.get("amount", "")
        address = send_info.get("address", "")

        token_info = next(
            (t for t in self.SUPPORTED_TOKENS.values() if t["symbol"] == token), None
        )
        emoji = token_info["emoji"] if token_info else "💎"

        display_address = (
            f"{address[:6]}...{address[-4:]}" if len(address) > 10 else address
        )

        translations = {
            "en": (
                "🎉 **Transaction Confirmed!**\\n\\n"
                f"You're sending **{amount} {token}** {emoji} to `{display_address}`\\n\\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\\n\\n"
                "**Next Step: Create Your Account**\\n\\n"
                "To complete this transaction securely, you'll need to sign up:\\n\\n"
                "👉 **Sign Up Now** - Takes just 2 minutes!\\n\\n"
                "✨ Your transaction details are saved and ready to execute once you're registered.\\n\\n"
                "🔒 *Secure • Fast • Easy*"
            ),
            "es": (
                "🎉 **¡Transacción Confirmada!**\\n\\n"
                f"Vas a enviar **{amount} {token}** {emoji} a `{display_address}`\\n\\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\\n\\n"
                "**Siguiente Paso: Crea Tu Cuenta**\\n\\n"
                "Para completar esta transacción de forma segura, necesitas registrarte:\\n\\n"
                "👉 **Regístrate Ahora** - ¡Solo toma 2 minutos!\\n\\n"
                "✨ Los detalles de tu transacción están guardados y listos para ejecutar una vez que te registres.\\n\\n"
                "🔒 *Seguro • Rápido • Fácil*"
            ),
        }

        return {
            "content": translations.get(language, translations["en"]),
            "enrichment": {"send_flow": "execution", "action": "send_transaction"},
            "requires_registration": True,
        }

    def _cancel_send(self, language: str) -> dict:
        """Cancel send transaction."""
        translations = {
            "en": "❌ Transaction cancelled. Your crypto is safe! Start a new send anytime.",
            "es": "❌ Transacción cancelada. ¡Tu cripto está seguro! Inicia un nuevo envío cuando quieras.",
        }

        return {
            "content": translations.get(language, translations["en"]),
            "enrichment": {},
            "requires_registration": False,
        }

    async def _handle_edit(
        self, content: str, send_info: dict, language: str, is_authenticated: bool
    ) -> dict:
        """Handle edit request."""
        # Extract new amount if mentioned
        if "amount" in content.lower():
            new_amount = self._extract_amount(content)
            if new_amount:
                send_info["amount"] = new_amount
                return await self._show_review_and_confirm(
                    send_info, language, is_authenticated
                )

        # Generic edit response - restart from amount
        return self._ask_for_amount(send_info, language, is_authenticated)

    def _show_help(self, language: str, is_authenticated: bool) -> dict:
        """Show help for send feature."""
        translations = {
            "en": (
                "📤 **Send Crypto to Another Wallet**\\n\\n"
                "Send Bitcoin, Ethereum, Solana, or USDC securely.\\n\\n"
                "**To start:**\\n"
                "• Just say `send` or `send ETH`\\n"
                "• I'll guide you through it step by step\\n\\n"
                "**Example:**\\n"
                "`send 0.5 ETH to 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb`"
            ),
            "es": (
                "📤 **Enviar Cripto a Otra Billetera**\\n\\n"
                "Envía Bitcoin, Ethereum, Solana o USDC de forma segura.\\n\\n"
                "**Para comenzar:**\\n"
                "• Solo di `enviar` o `enviar ETH`\\n"
                "• Te guiaré paso a paso\\n\\n"
                "**Ejemplo:**\\n"
                "`enviar 0.5 ETH a 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb`"
            ),
        }

        return {
            "content": translations.get(language, translations["en"]),
            "enrichment": {"send_flow": "help"},
            "requires_registration": not is_authenticated,
        }
