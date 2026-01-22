"""
Lending Workflow Agent - Multi-Step Deposit/Yield Operations.

Handles the complete lending workflow for authenticated users:
1. Parse request: Extract asset and amount from user message
2. Fetch vaults: Get best yield options from Morpho and Aave
3. Confirm: Show quote and wait for user confirmation
4. Execute: Generate execute_data for frontend execution

Integration:
- Primary: Morpho MetaMorpho vaults (Base chain)
- Fallback: Aave V3 markets
- Execution: Frontend uses Privy SDK with execute_data

Example Conversation:
    User: "deposit 1000 USDC"
    Agent: "📊 Best Vault: Steakhouse USDC (12.5% APY). Monthly: ~$10.42. Confirm?"
    User: "yes"
    Agent: "✅ Ready to deposit!" + execute_data for frontend modal
"""

import logging
import re
from decimal import Decimal
from typing import Any, TYPE_CHECKING

from app.domain.enums.agent_type import AgentType
from app.domain.value_objects.message_content import MessageContent
from app.domain.ports.agent_squad.agent_gateway import AgentResponse

from .base_workflow_agent import (
    BaseWorkflowAgent,
    WorkflowState,
    WorkflowStep,
    UserContext,
)

if TYPE_CHECKING:
    from app.domain.ports.morpho_gateway import MorphoGateway
    from app.domain.ports.aave_gateway import AaveGateway
    from app.domain.ports.agent_squad.llm_client_gateway import LLMClientGateway

logger = logging.getLogger(__name__)


# Supported assets for lending
SUPPORTED_ASSETS = {
    "usdc": {"symbol": "USDC", "name": "USD Coin", "emoji": "💵", "decimals": 6},
    "usdt": {"symbol": "USDT", "name": "Tether", "emoji": "💵", "decimals": 6},
    "dai": {"symbol": "DAI", "name": "Dai", "emoji": "💰", "decimals": 18},
    "eth": {"symbol": "ETH", "name": "Ethereum", "emoji": "Ξ", "decimals": 18},
    "weth": {"symbol": "WETH", "name": "Wrapped Ethereum", "emoji": "Ξ", "decimals": 18},
    "wbtc": {"symbol": "WBTC", "name": "Wrapped Bitcoin", "emoji": "₿", "decimals": 8},
}

# Vaults with known issues (exclude from selection)
EXCLUDED_VAULTS = {
    "0x8773447e6369472D9B72f064Ea62e405216E9084",  # MEV Frontier USDC
    "0x1D3b1Cd0a0f242d598834b3F2d126dC6bd774657",  # Clearstar USDC Reactor
    "0xB7890CEE6CF4792cdCC13489D36D9d42726ab863",  # Universal USDC (UUSDC)
    "0x23479229e52Ab6aaD312D0B03DF9F33B46753B5e",  # Extrafi XLend USDC
}

# Aave V3 pool addresses by chain
AAVE_POOL_ADDRESSES = {
    "ethereum": "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2",
    "polygon": "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
    "arbitrum": "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
    "optimism": "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
    "avalanche": "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
    "base": "0xA238Dd80C259a72e81d7e4664a9801593F98d1c5",
}


class LendingWorkflowAgent(BaseWorkflowAgent):
    """
    AGNO-based multi-step lending/deposit workflow agent.
    
    Steps:
    1. parse_request: Extract asset, amount, and optional protocol preference
    2. fetch_data: Get vault options from Morpho, fallback to Aave
    3. confirm: Show best vault with APY, wait for user confirmation
    4. execute: Generate execute_data for frontend
    
    Features:
    - Natural language parameter extraction
    - Morpho vault selection with APY optimization
    - Aave V3 fallback for unsupported assets
    - User modification support ("change to 500 USDC")
    - Multi-language support
    """
    
    def __init__(
        self,
        llm_client: "LLMClientGateway | None" = None,
        morpho_gateway: "MorphoGateway | None" = None,
        aave_gateway: "AaveGateway | None" = None,
    ):
        """
        Initialize lending workflow agent.
        
        Args:
            llm_client: LLM client for parameter extraction
            morpho_gateway: Morpho gateway for vault data
            aave_gateway: Aave gateway for fallback markets
        """
        super().__init__(llm_client=llm_client)
        self._morpho = morpho_gateway
        self._aave = aave_gateway
    
    @property
    def agent_type(self) -> AgentType:
        return AgentType.LENDING_WORKFLOW
    
    @property
    def workflow_name(self) -> str:
        return "LendingWorkflow"
    
    async def process_step(
        self,
        message: MessageContent,
        state: WorkflowState,
        user_context: UserContext,
    ) -> tuple[str, WorkflowState]:
        """Process lending workflow step."""
        
        step = state.step
        language = user_context.language
        
        logger.info(f"[LendingWorkflow] Processing step={step}, message={message.value[:50]}...")
        
        # Step 1: Parse request
        if step == WorkflowStep.PARSE_REQUEST.value:
            return await self._handle_parse_request(message, state, user_context)
        
        # Step 2: Fetch vault data
        if step == WorkflowStep.FETCH_DATA.value:
            return await self._handle_fetch_data(message, state, user_context)
        
        # Step 3: Confirm
        if step == WorkflowStep.CONFIRM.value:
            return await self._handle_confirm(message, state, user_context)
        
        # Step 4: Execute
        if step == WorkflowStep.EXECUTE.value:
            return await self._handle_execute(message, state, user_context)
        
        # Unknown step - reset
        logger.warning(f"[LendingWorkflow] Unknown step: {step}")
        state.step = WorkflowStep.PARSE_REQUEST.value
        return await self._handle_parse_request(message, state, user_context)
    
    # ========================================
    # Step Handlers
    # ========================================
    
    async def _handle_parse_request(
        self,
        message: MessageContent,
        state: WorkflowState,
        user_context: UserContext,
    ) -> tuple[str, WorkflowState]:
        """Parse deposit request from user message."""
        
        language = user_context.language
        text = message.value.lower()
        
        # Try to extract parameters from message
        params = await self._extract_lending_params(text)
        
        asset = params.get("asset")
        amount = params.get("amount")
        
        # If we have both asset and amount, proceed to fetch data
        if asset and amount:
            state.data["asset"] = asset.upper()
            state.data["amount"] = amount
            state.data["chain"] = params.get("chain", "base")
            state.step = WorkflowStep.FETCH_DATA.value
            return await self._handle_fetch_data(message, state, user_context)
        
        # If we have asset but no amount, ask for amount
        if asset and not amount:
            state.data["asset"] = asset.upper()
            state.step = WorkflowStep.PARSE_REQUEST.value
            return self._ask_for_amount(asset.upper(), language), state
        
        # No asset detected - ask user to select
        return self._ask_for_asset(language), state
    
    async def _handle_fetch_data(
        self,
        message: MessageContent,
        state: WorkflowState,
        user_context: UserContext,
    ) -> tuple[str, WorkflowState]:
        """Fetch vault data from Morpho/Aave."""
        
        language = user_context.language
        asset = state.data.get("asset", "USDC")
        amount = state.data.get("amount", "0")
        chain = state.data.get("chain", "base")
        wallet_address = user_context.wallet_address
        
        logger.info(f"[LendingWorkflow] Fetching vaults for {asset} on {chain}")
        
        # Try Morpho first
        vault_data = await self._fetch_morpho_vault(asset, chain)
        
        # Fallback to Aave if no Morpho vault
        if not vault_data and self._aave:
            vault_data = await self._fetch_aave_market(asset, chain)
        
        if not vault_data:
            # No vault available
            response = self._format_no_vault_available(asset, chain, language)
            state.step = WorkflowStep.CANCELLED.value
            state.cancelled = True
            return response, state
        
        # Store vault data
        state.data["vault"] = vault_data
        state.step = WorkflowStep.CONFIRM.value
        
        # Build execute_data for frontend
        state.execute_data = self._build_deposit_execute_data(
            vault_data=vault_data,
            amount=amount,
            chain=chain,
        )
        
        # Format quote response
        response = self._format_vault_quote(
            vault_data=vault_data,
            asset=asset,
            amount=amount,
            language=language,
        )
        
        return response, state
    
    async def _handle_confirm(
        self,
        message: MessageContent,
        state: WorkflowState,
        user_context: UserContext,
    ) -> tuple[str, WorkflowState]:
        """Handle user confirmation or modification."""
        
        language = user_context.language
        text = message.value.lower().strip()
        
        # Check for confirmation
        if self._is_confirmation(text):
            state.confirmed = True
            state.step = WorkflowStep.EXECUTE.value
            return self._format_ready_to_execute(state.data, language), state
        
        # Check for cancellation
        if self._is_cancellation(text):
            state.cancelled = True
            state.step = WorkflowStep.CANCELLED.value
            return self._format_cancelled(language), state
        
        # Check for modification (e.g., "change to 500 USDC")
        modification = await self._parse_modification(text)
        if modification:
            if modification.get("amount"):
                state.data["amount"] = modification["amount"]
            if modification.get("asset"):
                state.data["asset"] = modification["asset"].upper()
            
            # Re-fetch with new parameters
            state.step = WorkflowStep.FETCH_DATA.value
            return await self._handle_fetch_data(message, state, user_context)
        
        # Unclear response - ask again
        return self._ask_for_confirmation(language), state
    
    async def _handle_execute(
        self,
        message: MessageContent,
        state: WorkflowState,
        user_context: UserContext,
    ) -> tuple[str, WorkflowState]:
        """Handle execute step - transaction is done by frontend."""
        
        language = user_context.language
        
        # The actual transaction is handled by the frontend using execute_data
        # This step just confirms the workflow is ready
        state.step = WorkflowStep.COMPLETED.value
        
        return self._format_execution_pending(state.data, language), state
    
    # ========================================
    # Data Fetching
    # ========================================
    
    async def _fetch_morpho_vault(
        self,
        asset: str,
        chain: str,
    ) -> dict[str, Any] | None:
        """Fetch best Morpho vault for asset."""
        
        if not self._morpho:
            logger.warning("[LendingWorkflow] Morpho gateway not available")
            return None
        
        try:
            vaults = await self._morpho.get_vaults(asset=asset, chain=chain)
            
            if not vaults:
                logger.info(f"[LendingWorkflow] No Morpho vaults for {asset} on {chain}")
                return None
            
            # Filter whitelisted vaults and exclude problematic ones
            valid_vaults = [
                v for v in vaults
                if v.whitelisted and v.address not in EXCLUDED_VAULTS
            ]
            
            if not valid_vaults:
                logger.info(f"[LendingWorkflow] No valid whitelisted vaults for {asset}")
                return None
            
            # Sort by APY (highest first)
            sorted_vaults = sorted(valid_vaults, key=lambda v: float(v.apy), reverse=True)
            best_vault = sorted_vaults[0]
            
            logger.info(f"[LendingWorkflow] Best vault: {best_vault.name} ({best_vault.apy}% APY)")
            
            return {
                "protocol": "morpho",
                "provider": "morpho",
                "name": best_vault.name,
                "address": best_vault.address,
                "asset_address": best_vault.asset_address,
                "asset_symbol": best_vault.asset,
                "apy": float(best_vault.apy),
                "tvl": float(best_vault.total_assets),
                "chain": chain,
            }
            
        except Exception as e:
            logger.error(f"[LendingWorkflow] Error fetching Morpho vaults: {e}")
            return None
    
    async def _fetch_aave_market(
        self,
        asset: str,
        chain: str,
    ) -> dict[str, Any] | None:
        """Fetch Aave V3 market for asset."""
        
        if not self._aave:
            logger.warning("[LendingWorkflow] Aave gateway not available")
            return None
        
        try:
            market = await self._aave.get_market_details(asset=asset, chain=chain)
            
            if not market or not market.is_suppliable:
                logger.info(f"[LendingWorkflow] No active Aave market for {asset} on {chain}")
                return None
            
            pool_address = AAVE_POOL_ADDRESSES.get(chain)
            if not pool_address:
                logger.warning(f"[LendingWorkflow] No Aave pool address for {chain}")
                return None
            
            logger.info(f"[LendingWorkflow] Aave market: {market.symbol} ({market.supply_apy}% APY)")
            
            return {
                "protocol": "aave_v3",
                "provider": "aave",
                "name": f"Aave V3 {market.symbol}",
                "address": pool_address,
                "asset_address": market.asset_address,
                "asset_symbol": market.symbol,
                "apy": float(market.supply_apy),
                "tvl": float(market.total_supplied_usd),
                "chain": chain,
                "available_liquidity_usd": float(market.available_liquidity_usd),
            }
            
        except Exception as e:
            logger.error(f"[LendingWorkflow] Error fetching Aave market: {e}")
            return None
    
    # ========================================
    # Parameter Extraction
    # ========================================
    
    async def _extract_lending_params(self, text: str) -> dict[str, Any]:
        """Extract lending parameters from text."""
        
        params: dict[str, Any] = {}
        
        # Try LLM extraction first
        if self._llm_client:
            try:
                llm_params = await self._llm_extract_params(
                    text,
                    param_schema={
                        "asset": "Token symbol to deposit (USDC, ETH, DAI, etc.)",
                        "amount": "Amount to deposit (numeric value)",
                        "chain": "Blockchain network (base, ethereum, etc.)",
                    },
                )
                if llm_params:
                    params.update(llm_params)
            except Exception as e:
                logger.warning(f"[LendingWorkflow] LLM extraction failed: {e}")
        
        # Regex fallback for amount
        if not params.get("amount"):
            amount_match = re.search(r"(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:usdc|usdt|dai|eth|wbtc)?", text, re.I)
            if amount_match:
                params["amount"] = amount_match.group(1).replace(",", "")
        
        # Regex fallback for asset
        if not params.get("asset"):
            for key, info in SUPPORTED_ASSETS.items():
                if key in text or info["symbol"].lower() in text:
                    params["asset"] = info["symbol"]
                    break
        
        # Default chain
        if not params.get("chain"):
            params["chain"] = "base"
        
        return params
    
    async def _parse_modification(self, text: str) -> dict[str, Any] | None:
        """Parse modification request from user."""
        
        modification: dict[str, Any] = {}
        
        # Check for amount modification
        amount_match = re.search(r"(?:change|update|make it|use)\s+(?:to\s+)?(\d+(?:,\d{3})*(?:\.\d+)?)", text, re.I)
        if amount_match:
            modification["amount"] = amount_match.group(1).replace(",", "")
        
        # Check for asset change
        for key, info in SUPPORTED_ASSETS.items():
            if key in text or info["symbol"].lower() in text:
                modification["asset"] = info["symbol"]
                break
        
        return modification if modification else None
    
    # ========================================
    # Response Formatting
    # ========================================
    
    def _ask_for_asset(self, language: str) -> str:
        """Ask user which asset to deposit."""
        
        msgs = {
            "en": """💰 **Earn Yield on Your Crypto**

Deposit into DeFi vaults to earn passive income. Which asset would you like to deposit?

**Available Assets:**
1. 💵 **USDC** (USD Coin)
2. 💵 **USDT** (Tether)
3. 💰 **DAI** (Dai)
4. Ξ **ETH** (Ethereum)
5. ₿ **WBTC** (Wrapped Bitcoin)

💬 Reply with the asset name (e.g., "USDC" or "1000 USDC")""",
            
            "es": """💰 **Gana Rendimiento con tus Cripto**

Deposita en vaults DeFi para ganar ingresos pasivos. ¿Qué activo te gustaría depositar?

**Activos Disponibles:**
1. 💵 **USDC** (USD Coin)
2. 💵 **USDT** (Tether)
3. 💰 **DAI** (Dai)
4. Ξ **ETH** (Ethereum)
5. ₿ **WBTC** (Wrapped Bitcoin)

💬 Responde con el nombre del activo (ej: "USDC" o "1000 USDC")""",
            
            "pt": """💰 **Ganhe Rendimento com suas Cripto**

Deposite em vaults DeFi para ganhar renda passiva. Qual ativo você gostaria de depositar?

**Ativos Disponíveis:**
1. 💵 **USDC** (USD Coin)
2. 💵 **USDT** (Tether)
3. 💰 **DAI** (Dai)
4. Ξ **ETH** (Ethereum)
5. ₿ **WBTC** (Wrapped Bitcoin)

💬 Responda com o nome do ativo (ex: "USDC" ou "1000 USDC")""",
            
            "zh": """💰 **赚取加密货币收益**

存入 DeFi 金库以赚取被动收入。您想存入哪种资产？

**可用资产：**
1. 💵 **USDC** (USD Coin)
2. 💵 **USDT** (Tether)
3. 💰 **DAI** (Dai)
4. Ξ **ETH** (以太坊)
5. ₿ **WBTC** (封装比特币)

💬 回复资产名称（例如："USDC" 或 "1000 USDC"）""",
        }
        
        return msgs.get(language, msgs["en"])
    
    def _ask_for_amount(self, asset: str, language: str) -> str:
        """Ask user for deposit amount."""
        
        asset_info = SUPPORTED_ASSETS.get(asset.lower(), {"emoji": "💰", "name": asset})
        emoji = asset_info["emoji"]
        
        msgs = {
            "en": f"""{emoji} **Deposit {asset}**

How much **{asset}** would you like to deposit?

💡 *Examples:*
• `100` (one hundred {asset})
• `1000` (one thousand {asset})
• `0.5` (half a {asset})

💬 Enter the amount to continue""",
            
            "es": f"""{emoji} **Depositar {asset}**

¿Cuánto **{asset}** te gustaría depositar?

💡 *Ejemplos:*
• `100` (cien {asset})
• `1000` (mil {asset})
• `0.5` (medio {asset})

💬 Ingresa la cantidad para continuar""",
            
            "pt": f"""{emoji} **Depositar {asset}**

Quanto **{asset}** você gostaria de depositar?

💡 *Exemplos:*
• `100` (cem {asset})
• `1000` (mil {asset})
• `0.5` (meio {asset})

💬 Digite a quantia para continuar""",
            
            "zh": f"""{emoji} **存入 {asset}**

您想存入多少 **{asset}**？

💡 *示例：*
• `100` (一百 {asset})
• `1000` (一千 {asset})
• `0.5` (半个 {asset})

💬 输入金额以继续""",
        }
        
        return msgs.get(language, msgs["en"])
    
    def _format_vault_quote(
        self,
        vault_data: dict[str, Any],
        asset: str,
        amount: str,
        language: str,
    ) -> str:
        """Format vault quote for display."""
        
        try:
            amount_float = float(amount.replace(",", ""))
        except ValueError:
            amount_float = 0
        
        apy = vault_data.get("apy", 0)
        yearly_earnings = amount_float * (apy / 100)
        monthly_earnings = yearly_earnings / 12
        
        protocol = vault_data.get("protocol", "morpho")
        protocol_name = "Morpho" if protocol == "morpho" else "Aave V3"
        vault_name = vault_data.get("name", f"{protocol_name} Vault")
        
        msgs = {
            "en": f"""📊 **Deposit Quote**

**{vault_name}**

💰 **Deposit Amount:** {amount} {asset}
📈 **Current APY:** {apy:.2f}%
💵 **Monthly Earnings:** ~{monthly_earnings:.2f} {asset}
📆 **Yearly Earnings:** ~{yearly_earnings:.2f} {asset}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Ready to deposit?**
Reply "yes" to confirm or "cancel" to abort.
You can also modify: "change to 500 {asset}" """,
            
            "es": f"""📊 **Cotización de Depósito**

**{vault_name}**

💰 **Cantidad a Depositar:** {amount} {asset}
📈 **APY Actual:** {apy:.2f}%
💵 **Ganancias Mensuales:** ~{monthly_earnings:.2f} {asset}
📆 **Ganancias Anuales:** ~{yearly_earnings:.2f} {asset}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**¿Listo para depositar?**
Responde "sí" para confirmar o "cancelar" para abortar.
También puedes modificar: "cambiar a 500 {asset}" """,
            
            "pt": f"""📊 **Cotação de Depósito**

**{vault_name}**

💰 **Valor do Depósito:** {amount} {asset}
📈 **APY Atual:** {apy:.2f}%
💵 **Ganhos Mensais:** ~{monthly_earnings:.2f} {asset}
📆 **Ganhos Anuais:** ~{yearly_earnings:.2f} {asset}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Pronto para depositar?**
Responda "sim" para confirmar ou "cancelar" para abortar.
Você também pode modificar: "alterar para 500 {asset}" """,
            
            "zh": f"""📊 **存款报价**

**{vault_name}**

💰 **存款金额：** {amount} {asset}
📈 **当前 APY：** {apy:.2f}%
💵 **月收益：** ~{monthly_earnings:.2f} {asset}
📆 **年收益：** ~{yearly_earnings:.2f} {asset}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**准备存款了吗？**
回复'是'确认或'取消'中止。
您也可以修改："改为 500 {asset}" """,
        }
        
        return msgs.get(language, msgs["en"])
    
    def _format_no_vault_available(
        self,
        asset: str,
        chain: str,
        language: str,
    ) -> str:
        """Format message when no vault is available."""
        
        msgs = {
            "en": f"""❌ **No Vault Available**

Unfortunately, there are no active vaults for **{asset}** on {chain.title()} network.

**Available assets:** USDC, USDT, DAI

Would you like to deposit one of these instead?""",
            
            "es": f"""❌ **Vault No Disponible**

Desafortunadamente, no hay vaults activos para **{asset}** en la red {chain.title()}.

**Activos disponibles:** USDC, USDT, DAI

¿Te gustaría depositar alguno de estos en su lugar?""",
            
            "pt": f"""❌ **Vault Não Disponível**

Infelizmente, não há vaults ativos para **{asset}** na rede {chain.title()}.

**Ativos disponíveis:** USDC, USDT, DAI

Gostaria de depositar algum destes em seu lugar?""",
            
            "zh": f"""❌ **金库不可用**

抱歉，{chain.title()} 网络上没有 **{asset}** 的活跃金库。

**可用资产：** USDC, USDT, DAI

您想存入其中一种吗？""",
        }
        
        return msgs.get(language, msgs["en"])
    
    def _ask_for_confirmation(self, language: str) -> str:
        """Ask user to confirm."""
        
        msgs = {
            "en": """Would you like to confirm this deposit? Reply "yes" or "cancel".""",
            "es": """¿Te gustaría confirmar este depósito? Responde "sí" o "cancelar".""",
            "pt": """Gostaria de confirmar este depósito? Responda "sim" ou "cancelar".""",
            "zh": """您想确认此存款吗？回复"是"或"取消"。""",
        }
        
        return msgs.get(language, msgs["en"])
    
    def _format_ready_to_execute(
        self,
        data: dict[str, Any],
        language: str,
    ) -> str:
        """Format ready-to-execute message."""
        
        asset = data.get("asset", "USDC")
        amount = data.get("amount", "0")
        vault = data.get("vault", {})
        protocol = vault.get("protocol", "morpho")
        protocol_name = "Morpho" if protocol == "morpho" else "Aave V3"
        
        msgs = {
            "en": f"""✅ **Deposit Ready to Execute**

🔄 **Depositing:** {amount} {asset}
🏦 **Protocol:** {protocol_name}
⛓️ **Network:** Base

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Click **Confirm** to execute the deposit.""",
            
            "es": f"""✅ **Depósito Listo para Ejecutar**

🔄 **Depositando:** {amount} {asset}
🏦 **Protocolo:** {protocol_name}
⛓️ **Red:** Base

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Haz clic en **Confirmar** para ejecutar el depósito.""",
            
            "pt": f"""✅ **Depósito Pronto para Executar**

🔄 **Depositando:** {amount} {asset}
🏦 **Protocolo:** {protocol_name}
⛓️ **Rede:** Base

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Clique em **Confirmar** para executar o depósito.""",
            
            "zh": f"""✅ **存款准备执行**

🔄 **存入：** {amount} {asset}
🏦 **协议：** {protocol_name}
⛓️ **网络：** Base

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

点击 **确认** 执行存款。""",
        }
        
        return msgs.get(language, msgs["en"])
    
    def _format_cancelled(self, language: str) -> str:
        """Format cancellation message."""
        
        msgs = {
            "en": "❌ Deposit cancelled. Let me know if you'd like to try again!",
            "es": "❌ Depósito cancelado. ¡Avísame si quieres intentarlo de nuevo!",
            "pt": "❌ Depósito cancelado. Me avise se quiser tentar novamente!",
            "zh": "❌ 存款已取消。如果您想再试一次，请告诉我！",
        }
        
        return msgs.get(language, msgs["en"])
    
    def _format_execution_pending(
        self,
        data: dict[str, Any],
        language: str,
    ) -> str:
        """Format message while execution is pending."""
        
        asset = data.get("asset", "USDC")
        amount = data.get("amount", "0")
        
        msgs = {
            "en": f"""⏳ **Processing Deposit**

Depositing **{amount} {asset}**...

Please confirm the transaction in your wallet.""",
            
            "es": f"""⏳ **Procesando Depósito**

Depositando **{amount} {asset}**...

Por favor confirma la transacción en tu wallet.""",
            
            "pt": f"""⏳ **Processando Depósito**

Depositando **{amount} {asset}**...

Por favor confirme a transação na sua carteira.""",
            
            "zh": f"""⏳ **处理存款中**

正在存入 **{amount} {asset}**...

请在您的钱包中确认交易。""",
        }
        
        return msgs.get(language, msgs["en"])
    
    # ========================================
    # Execute Data Builder
    # ========================================
    
    def _build_deposit_execute_data(
        self,
        vault_data: dict[str, Any],
        amount: str,
        chain: str,
    ) -> dict[str, Any]:
        """Build execute_data for deposit action."""
        
        protocol = vault_data.get("protocol", "morpho")
        
        execute_data = {
            "action_type": "deposit",
            "provider": vault_data.get("provider", "morpho"),
            "protocol": protocol,
            "chain": chain,
            "amount": amount,
            "slippage": 0.5,
        }
        
        if protocol == "morpho":
            execute_data.update({
                "vault_address": vault_data.get("address"),
                "asset_address": vault_data.get("asset_address"),
                "asset_symbol": vault_data.get("asset_symbol"),
                "vault_name": vault_data.get("name"),
                "supply_apy": vault_data.get("apy"),
            })
        else:
            # Aave V3
            execute_data.update({
                "pool_address": vault_data.get("address"),
                "asset_address": vault_data.get("asset_address"),
                "asset_symbol": vault_data.get("asset_symbol"),
                "supply_apy": vault_data.get("apy"),
                "available_liquidity_usd": vault_data.get("available_liquidity_usd"),
                "referral_code": 0,
            })
        
        return execute_data
    
    # ========================================
    # Helpers
    # ========================================
    
    def _is_confirmation(self, text: str) -> bool:
        """Check if text is a confirmation."""
        confirm_words = [
            "yes", "y", "confirm", "ok", "proceed", "continue", "do it", "execute",
            "sí", "si", "confirmar", "vale", "continuar",
            "sim", "confirmar", "prosseguir",
            "是", "确认", "好", "继续",
        ]
        return any(word in text for word in confirm_words)
    
    def _is_cancellation(self, text: str) -> bool:
        """Check if text is a cancellation."""
        cancel_words = [
            "no", "n", "cancel", "abort", "stop", "nevermind", "forget it",
            "cancelar", "abortar", "parar",
            "取消", "不", "停止",
        ]
        return any(word in text for word in cancel_words)
