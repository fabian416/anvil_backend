"""
Lending Multi-Step Handler for Guest Chat.

Provides multi-step conversational flow for lending/deposit:
1. Ask for asset (USDC, ETH, DAI, etc.)
2. Ask for amount to deposit
3. Show vault options with APY quotes
4. Confirm deposit → requires signup

Guest experience with demo Morpho vault data.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class LendingMultiStepHandler:
    """Handles multi-step conversational flow for lending/deposits."""

    SUPPORTED_ASSETS = {
        "usdc": {"symbol": "USDC", "name": "USD Coin", "emoji": "💵"},
        "usdt": {"symbol": "USDT", "name": "Tether", "emoji": "💵"},
        "dai": {"symbol": "DAI", "name": "Dai", "emoji": "💰"},
        "eth": {"symbol": "ETH", "name": "Ethereum", "emoji": "Ξ"},
        "wbtc": {"symbol": "WBTC", "name": "Wrapped Bitcoin", "emoji": "₿"},
    }

    # Demo APY rates for different assets
    DEMO_APYS = {
        "USDC": 8.5,
        "USDT": 7.8,
        "DAI": 9.2,
        "ETH": 5.4,
        "WBTC": 4.2,
    }

    async def handle_flow(
        self,
        content: str,
        language: str,
        is_authenticated: bool,
        continuation_step: str | None = None,
        previous_lending_info: dict | None = None,
    ) -> dict[str, Any]:
        """
        Handle multi-step lending flow.

        Flow:
        1. User: "lending" → Ask for asset
        2. User: "USDC" → Ask for amount
        3. User: "1000" → Show vault quote, ask confirmation
        4. User: "confirm" → Execute (requires auth)
        """
        # Step 1: Ask for asset (initial request)
        if not continuation_step and not previous_lending_info:
            return await self._ask_for_asset(language)

        # Step 2: Process asset selection
        if continuation_step == "lending_awaiting_asset" or (
            previous_lending_info and not previous_lending_info.get("asset")
        ):
            asset = self._parse_asset(content)
            if not asset:
                # Invalid asset, re-ask
                return await self._ask_for_asset(language, error=True)
            return await self._ask_for_amount(asset, language)

        # Step 3: Process amount selection
        if continuation_step == "lending_awaiting_amount" or (
            previous_lending_info
            and previous_lending_info.get("asset")
            and not previous_lending_info.get("amount")
        ):
            asset = previous_lending_info.get("asset", "USDC")
            amount = self._parse_amount(content)
            if not amount:
                # Invalid amount, re-ask
                return await self._ask_for_amount(asset, language, error=True)
            return await self._show_vault_quote(asset, amount, language)

        # Step 4: Process confirmation
        if continuation_step == "lending_awaiting_confirmation":
            asset = previous_lending_info.get("asset", "USDC")
            amount = previous_lending_info.get("amount", "0")
            confirmation = self._parse_confirmation(content)

            if confirmation:
                return await self._execute_deposit(asset, amount, language, is_authenticated)
            elif confirmation is False:  # Explicit cancellation
                return await self._cancel_deposit(language)
            else:
                # Unclear response, re-ask
                return await self._show_vault_quote(asset, amount, language, error=True)

        # Fallback: restart flow
        return await self._ask_for_asset(language)

    async def _ask_for_asset(self, language: str, error: bool = False) -> dict[str, Any]:
        """Step 1: Ask user which asset to deposit."""
        messages = {
            "en": {
                "title": "💰 Earn Yield on Your Crypto",
                "error": "❌ Invalid asset. Please select from the list below.",
                "description": "Deposit into Morpho vaults to earn passive income. Which asset would you like to deposit?",
                "cta": "Select an asset to continue:",
            },
            "es": {
                "title": "💰 Gana Rendimiento con tus Cripto",
                "error": "❌ Activo inválido. Por favor selecciona de la lista.",
                "description": "Deposita en vaults de Morpho para ganar ingresos pasivos. ¿Qué activo te gustaría depositar?",
                "cta": "Selecciona un activo para continuar:",
            },
            "pt": {
                "title": "💰 Ganhe Rendimento com suas Cripto",
                "error": "❌ Ativo inválido. Por favor selecione da lista.",
                "description": "Deposite em vaults Morpho para ganhar renda passiva. Qual ativo você gostaria de depositar?",
                "cta": "Selecione um ativo para continuar:",
            },
            "zh": {
                "title": "💰 赚取加密货币收益",
                "error": "❌ 无效资产。请从列表中选择。",
                "description": "存入 Morpho 金库以赚取被动收入。您想存入哪种资产？",
                "cta": "选择资产以继续:",
            },
        }

        msg = messages.get(language, messages["en"])
        error_text = f"\n\n{msg['error']}\n" if error else ""

        content = f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{msg['title']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{error_text}
{msg['description']}

**{msg['cta']}**

1. 💵 **USDC** (USD Coin) - ~8.5% APY
2. 💵 **USDT** (Tether) - ~7.8% APY
3. 💰 **DAI** (Dai) - ~9.2% APY
4. Ξ **ETH** (Ethereum) - ~5.4% APY
5. ₿ **WBTC** (Wrapped Bitcoin) - ~4.2% APY

💬 Reply with the number (1-5) or type the asset name (e.g., "USDC")
"""

        return {
            "content": content,
            "pending_action": "lending_awaiting_asset",
            "lending_info": {},
            "enrichment": {
                "lending_flow": "step1_asset",
            },
            "requires_registration": True,
        }

    async def _ask_for_amount(
        self, asset: str, language: str, error: bool = False
    ) -> dict[str, Any]:
        """Step 2: Ask user how much to deposit."""
        asset_info = next(
            (v for v in self.SUPPORTED_ASSETS.values() if v["symbol"] == asset), None
        )
        emoji = asset_info["emoji"] if asset_info else "💰"
        asset_name = asset_info["name"] if asset_info else asset

        messages = {
            "en": {
                "title": f"{emoji} Deposit {asset}",
                "error": "❌ Invalid amount. Please enter a positive number.",
                "description": f"You're depositing **{asset}** ({asset_name}) into a Morpho vault.",
                "cta": "How much would you like to deposit?",
                "examples": f"Examples: 100, 1000, 5000 {asset}",
            },
            "es": {
                "title": f"{emoji} Depositar {asset}",
                "error": "❌ Cantidad inválida. Por favor ingresa un número positivo.",
                "description": f"Vas a depositar **{asset}** ({asset_name}) en un vault de Morpho.",
                "cta": "¿Cuánto te gustaría depositar?",
                "examples": f"Ejemplos: 100, 1000, 5000 {asset}",
            },
            "pt": {
                "title": f"{emoji} Depositar {asset}",
                "error": "❌ Quantia inválida. Por favor insira um número positivo.",
                "description": f"Você está depositando **{asset}** ({asset_name}) em um vault Morpho.",
                "cta": "Quanto você gostaria de depositar?",
                "examples": f"Exemplos: 100, 1000, 5000 {asset}",
            },
            "zh": {
                "title": f"{emoji} 存入 {asset}",
                "error": "❌ 无效数量。请输入正数。",
                "description": f"您将存入 **{asset}** ({asset_name}) 到 Morpho 金库。",
                "cta": "您想存入多少?",
                "examples": f"示例: 100, 1000, 5000 {asset}",
            },
        }

        msg = messages.get(language, messages["en"])
        error_text = f"\n\n{msg['error']}\n" if error else ""

        content = f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{msg['title']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{error_text}
{msg['description']}

**{msg['cta']}**

{msg['examples']}

💬 Enter the amount to continue
"""

        return {
            "content": content,
            "pending_action": "lending_awaiting_amount",
            "lending_info": {"asset": asset},
            "enrichment": {
                "lending_flow": "step2_amount",
                "asset": asset,
            },
            "requires_registration": True,
        }

    async def _show_vault_quote(
        self, asset: str, amount: str, language: str, error: bool = False
    ) -> dict[str, Any]:
        """Step 3: Show vault options and quote."""
        try:
            amount_float = float(amount.replace(",", ""))
        except ValueError:
            amount_float = 0

        # Demo APY calculation
        apy = self.DEMO_APYS.get(asset, 5.0)
        yearly_earnings = amount_float * (apy / 100)
        monthly_earnings = yearly_earnings / 12

        asset_info = next(
            (v for v in self.SUPPORTED_ASSETS.values() if v["symbol"] == asset), None
        )
        emoji = asset_info["emoji"] if asset_info else "💰"

        messages = {
            "en": {
                "title": f"{emoji} Morpho Vault Quote",
                "error": "❌ Unclear response. Please confirm or cancel.",
                "vault_title": "Best Vault (Demo Mode)",
                "deposit": "Deposit Amount",
                "estimated_apy": "Estimated APY",
                "monthly": "Monthly Earnings",
                "yearly": "Yearly Earnings",
                "note_title": "📝 Note",
                "note": "Demo pricing shown. Actual APY varies based on market conditions.",
                "confirm_title": "Ready to deposit?",
                "confirm_actions": 'Reply "confirm" or "yes" to proceed\nReply "cancel" to abort',
                "signup_required": "⚠️ You'll need to sign up to complete the deposit",
            },
            "es": {
                "title": f"{emoji} Cotización de Vault Morpho",
                "error": "❌ Respuesta poco clara. Por favor confirma o cancela.",
                "vault_title": "Mejor Vault (Modo Demo)",
                "deposit": "Cantidad a Depositar",
                "estimated_apy": "APY Estimado",
                "monthly": "Ganancias Mensuales",
                "yearly": "Ganancias Anuales",
                "note_title": "📝 Nota",
                "note": "Se muestra precio demo. El APY real varía según las condiciones del mercado.",
                "confirm_title": "¿Listo para depositar?",
                "confirm_actions": 'Responde "confirmar" o "sí" para proceder\nResponde "cancelar" para abortar',
                "signup_required": "⚠️ Necesitarás registrarte para completar el depósito",
            },
            "pt": {
                "title": f"{emoji} Cotação do Vault Morpho",
                "error": "❌ Resposta pouco clara. Por favor confirme ou cancele.",
                "vault_title": "Melhor Vault (Modo Demo)",
                "deposit": "Valor do Depósito",
                "estimated_apy": "APY Estimado",
                "monthly": "Ganhos Mensais",
                "yearly": "Ganhos Anuais",
                "note_title": "📝 Nota",
                "note": "Preço demo mostrado. O APY real varia de acordo com as condições do mercado.",
                "confirm_title": "Pronto para depositar?",
                "confirm_actions": 'Responda "confirmar" ou "sim" para prosseguir\nResponda "cancelar" para abortar',
                "signup_required": "⚠️ Você precisará se cadastrar para completar o depósito",
            },
            "zh": {
                "title": f"{emoji} Morpho 金库报价",
                "error": "❌ 回复不清楚。请确认或取消。",
                "vault_title": "最佳金库（演示模式）",
                "deposit": "存款金额",
                "estimated_apy": "预估 APY",
                "monthly": "月收益",
                "yearly": "年收益",
                "note_title": "📝 说明",
                "note": "显示的是演示定价。实际 APY 根据市场情况而变化。",
                "confirm_title": "准备存款了吗?",
                "confirm_actions": '回复"确认"或"是"继续\n回复"取消"中止',
                "signup_required": "⚠️ 您需要注册才能完成存款",
            },
        }

        msg = messages.get(language, messages["en"])
        error_text = f"\n{msg['error']}\n\n" if error else ""

        content = f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{msg['title']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{error_text}
**{msg['vault_title']}**

📊 **{msg['deposit']}**: {amount} {asset}
📈 **{msg['estimated_apy']}**: {apy:.2f}%
💰 **{msg['monthly']}**: ~{monthly_earnings:.2f} {asset}/month
💵 **{msg['yearly']}**: ~{yearly_earnings:.2f} {asset}/year

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{msg['note_title']}
{msg['note']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**{msg['confirm_title']}**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{msg['confirm_actions']}

{msg['signup_required']}
"""

        return {
            "content": content,
            "pending_action": "lending_awaiting_confirmation",
            "lending_info": {"asset": asset, "amount": amount},
            "enrichment": {
                "lending_flow": "step3_confirmation",
                "asset": asset,
                "amount": amount,
                "apy": apy,
                "monthly_earnings": monthly_earnings,
                "yearly_earnings": yearly_earnings,
            },
            "requires_registration": True,
        }

    async def _execute_deposit(
        self, asset: str, amount: str, language: str, is_authenticated: bool
    ) -> dict[str, Any]:
        """Step 4: Execute deposit (requires authentication)."""
        asset_info = next(
            (v for v in self.SUPPORTED_ASSETS.values() if v["symbol"] == asset), None
        )
        emoji = asset_info["emoji"] if asset_info else "💰"

        messages = {
            "en": {
                "title": f"✅ Deposit Confirmed!",
                "summary": f"You're depositing **{amount} {asset}** into a Morpho vault.",
                "next_steps": "Next Steps",
                "step1": "Sign up to connect your wallet",
                "step2": "Approve the vault contract",
                "step3": "Complete the deposit transaction",
                "cta": "Sign up now to start earning!",
            },
            "es": {
                "title": f"✅ ¡Depósito Confirmado!",
                "summary": f"Vas a depositar **{amount} {asset}** en un vault de Morpho.",
                "next_steps": "Próximos Pasos",
                "step1": "Regístrate para conectar tu billetera",
                "step2": "Aprueba el contrato del vault",
                "step3": "Completa la transacción de depósito",
                "cta": "¡Regístrate ahora para comenzar a ganar!",
            },
            "pt": {
                "title": f"✅ Depósito Confirmado!",
                "summary": f"Você está depositando **{amount} {asset}** em um vault Morpho.",
                "next_steps": "Próximos Passos",
                "step1": "Cadastre-se para conectar sua carteira",
                "step2": "Aprove o contrato do vault",
                "step3": "Complete a transação de depósito",
                "cta": "Cadastre-se agora para começar a ganhar!",
            },
            "zh": {
                "title": f"✅ 存款已确认!",
                "summary": f"您将存入 **{amount} {asset}** 到 Morpho 金库。",
                "next_steps": "下一步",
                "step1": "注册以连接您的钱包",
                "step2": "批准金库合约",
                "step3": "完成存款交易",
                "cta": "立即注册开始赚取收益!",
            },
        }

        msg = messages.get(language, messages["en"])

        content = f"""🎉 {msg['title']}

{msg['summary']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**{msg['next_steps']}**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. {emoji} {msg['step1']}
2. ✅ {msg['step2']}
3. 💰 {msg['step3']}

👉 **{msg['cta']}**
/signup
"""

        return {
            "content": content,
            "pending_action": None,
            "lending_info": None,
            "enrichment": {
                "lending_flow": "execution",
                "asset": asset,
                "amount": amount,
            },
            "requires_registration": True,
        }

    async def _cancel_deposit(self, language: str) -> dict[str, Any]:
        """Cancel the deposit flow."""
        messages = {
            "en": "❌ Deposit cancelled. Feel free to start over whenever you're ready!",
            "es": "❌ Depósito cancelado. ¡Puedes comenzar de nuevo cuando estés listo!",
            "pt": "❌ Depósito cancelado. Sinta-se à vontade para começar de novo quando estiver pronto!",
            "zh": "❌ 已取消存款。随时可以重新开始!",
        }

        content = messages.get(language, messages["en"])

        return {
            "content": content,
            "pending_action": None,
            "lending_info": None,
            "enrichment": {
                "lending_flow": "cancelled",
            },
            "requires_registration": False,
        }

    def _parse_asset(self, content: str) -> str | None:
        """Parse asset from user input."""
        content_lower = content.lower().strip()

        # Check for number selection (1-5)
        if content_lower in ["1", "one"]:
            return "USDC"
        elif content_lower in ["2", "two"]:
            return "USDT"
        elif content_lower in ["3", "three"]:
            return "DAI"
        elif content_lower in ["4", "four"]:
            return "ETH"
        elif content_lower in ["5", "five"]:
            return "WBTC"

        # Check for asset symbol/name
        for key, info in self.SUPPORTED_ASSETS.items():
            if key in content_lower or info["symbol"].lower() in content_lower:
                return info["symbol"]

        return None

    def _parse_amount(self, content: str) -> str | None:
        """Parse amount from user input."""
        import re

        # Remove non-numeric characters except decimal point
        cleaned = re.sub(r"[^\d.]", "", content)

        try:
            amount = float(cleaned)
            if amount > 0:
                return str(amount)
        except ValueError:
            pass

        return None

    def _parse_confirmation(self, content: str) -> bool | None:
        """
        Parse confirmation from user input.

        Returns:
            True if confirmed, False if cancelled, None if unclear
        """
        content_lower = content.lower().strip()

        # Confirmation keywords
        confirm_keywords = [
            "confirm",
            "yes",
            "y",
            "ok",
            "proceed",
            "continue",
            "confirmar",
            "sí",
            "si",
            "vale",
            "continuar",
        ]

        # Cancellation keywords
        cancel_keywords = [
            "cancel",
            "no",
            "n",
            "abort",
            "stop",
            "cancelar",
            "abortar",
            "parar",
        ]

        if any(keyword in content_lower for keyword in confirm_keywords):
            return True

        if any(keyword in content_lower for keyword in cancel_keywords):
            return False

        return None
