"""
Wallet Agent - Wallet management & balances for authenticated users.

This agent is ONLY available for authenticated users and provides:
- List connected wallets
- Show wallet balances (multi-chain)
- Wallet status and provider information
- Primary wallet identification

Requires: UserDataContext injection from AuthenticatedSupervisorCoordinator
"""

import time
import logging
from typing import Any, TYPE_CHECKING

from app.domain.enums.agent_type import AgentType
from app.domain.value_objects.conversation_id import ConversationId
from app.domain.value_objects.message_content import MessageContent
from app.domain.value_objects.agent_squad.conversation_context import ConversationContext
from app.domain.ports.agent_squad.agent_gateway import AgentGateway, AgentResponse
from app.domain.ports.agent_squad.llm_client_gateway import LLMClientGateway

if TYPE_CHECKING:
    from app.application.chat.services.user_data_service import UserDataContext

logger = logging.getLogger(__name__)


class WalletAgent:
    """
    Wallet Agent implementation for authenticated users.
    
    Implements: AgentGateway
    
    Purpose: Wallet management and balance queries
    
    Capabilities:
    - List user's connected wallets
    - Show balances for each wallet
    - Multi-chain wallet support
    - Primary wallet identification
    - Wallet provider information (Privy, External, Imported)
    
    IMPORTANT: This agent requires user authentication.
    Guest users should be redirected to GuestAuthAgent.
    
    Model: gemini-2.0-flash (Vertex AI)
    Temperature: 0.3 (balanced)
    """
    
    def __init__(
        self,
        llm_client: LLMClientGateway,
        model: str = "gemini-2.0-flash",
        temperature: float = 0.3,
        max_tokens: int = 1500,
    ):
        """
        Initialize wallet agent.
        
        Args:
            llm_client: LLM client gateway (Vertex AI or DeepInfra)
            model: Model to use (default: gemini-2.0-flash)
            temperature: Sampling temperature
            max_tokens: Maximum response tokens
        """
        self._llm_client = llm_client
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens
    
    @property
    def agent_type(self) -> AgentType:
        """Get agent type."""
        return AgentType.WALLET
    
    async def execute(
        self,
        conversation_id: ConversationId,
        message: MessageContent,
        conversation_context: ConversationContext,
    ) -> AgentResponse:
        """
        Execute wallet agent - handle wallet queries.
        
        Expects user_context in conversation_context.user_metadata containing:
        - wallets: List of WalletSummary
        - primary_wallet: WalletSummary or None
        """
        start_time = time.time()
        
        # Extract user context from conversation metadata
        user_context = self._extract_user_context(conversation_context)
        
        if not user_context:
            # User is not authenticated or no wallet data
            return self._create_auth_required_response(start_time)
        
        # Build context string with user's wallet data
        wallet_context = self._build_wallet_context(user_context)
        
        # Get portfolio balance for context-aware suggestions
        # Try multiple sources for balance data
        total_balance = 0.0
        
        # First try direct total_balance_usd (set by authenticated supervisor)
        if user_context.get("total_balance_usd") is not None:
            total_balance = float(user_context.get("total_balance_usd", 0) or 0)
        
        # Fallback to portfolio_summary
        if total_balance == 0:
            portfolio_summary = user_context.get("portfolio_summary", {})
            total_balance = float(portfolio_summary.get("total_value_usd", 0) or 0)
        
        # Build suggestions based on balance - ALWAYS show balance
        if total_balance < 1:
            suggestions = f"""
**💰 Balance:** ${total_balance:.2f}

**🚀 Get Started:**
Your wallet is ready! Add funds to start using Anvil:
• 💳 Say **"buy crypto"** to purchase USDC with card/Apple Pay
• 📥 Transfer crypto from another wallet to the address above"""
        else:
            suggestions = f"""
**💰 Balance:** ${total_balance:,.2f}

**💡 What you can do:**
• 🔄 **Swap** - Trade between different cryptocurrencies
• 💰 **Earn yield** - Deposit to DeFi protocols
• 📊 **Portfolio** - Say "my portfolio" for detailed holdings"""
        
        # Build enhanced prompt with actual wallet data
        enhanced_message = f"""User Query: {message.value}

**USER'S WALLET DATA (REAL DATA - USE THIS):**
{wallet_context}

**BALANCE & SUGGESTIONS (include in response):**
{suggestions}

Respond to the user's query using ONLY the wallet data provided above.
CRITICAL: Show the FULL wallet address - never truncate it!
Include the balance and suggestions at the end."""
        
        messages = [
            {"role": "system", "content": self._get_system_prompt()},
            {"role": "user", "content": enhanced_message},
        ]
        
        response = await self._llm_client.chat(
            messages=messages,
            model=self._model,
            temperature=self._temperature,
            max_tokens=self._max_tokens,
        )
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        # Build sources
        from datetime import datetime, UTC
        from app.infrastructure.adapters.agent_squad.agents.source_helpers import (
            create_llm_source,
            create_database_source,
        )
        
        sources = []
        fetched_at = datetime.now(UTC)
        
        # Add database source (wallet data)
        sources.append(create_database_source(
            citation_text="Your wallet data from Anvil",
            fetched_at=fetched_at,
            metadata={"query_type": "wallet_info"},
        ))
        
        # Add LLM source
        model_name = response.get("model", self._model)
        sources.append(create_llm_source(
            model=model_name,
            fetched_at=fetched_at,
        ))
        
        provider_info = response.get("provider", "vertex_ai" if "gemini" in model_name.lower() else "deepinfra")
        
        return AgentResponse(
            content=response["content"],
            agent_type=self.agent_type,
            tools_used=["llm_gateway", "wallet_repository"],
            sources=sources,
            metadata={
                "tokens_used": response.get("tokens_used"),
                "latency_ms": latency_ms,
                "model": model_name,
                "provider": provider_info,
                "wallet_count": len(user_context.get("wallets", [])) if user_context else 0,
            },
        )
    
    async def is_available(self) -> bool:
        """Check if agent is available."""
        return True
    
    def _extract_user_context(self, conversation_context: ConversationContext) -> dict[str, Any] | None:
        """Extract user context from conversation metadata."""
        if not conversation_context.user_metadata:
            return None
        
        # Check for user_context or direct wallet data
        if "user_context" in conversation_context.user_metadata:
            return conversation_context.user_metadata["user_context"]
        
        # Check for direct wallet data
        if "wallets" in conversation_context.user_metadata:
            return conversation_context.user_metadata
        
        # Check for flat structure (user_id, wallet_address, is_authenticated at top level)
        # This is how the supervisor passes user context
        if conversation_context.user_metadata.get("is_authenticated"):
            wallet_address = conversation_context.user_metadata.get("wallet_address")
            return {
                "user_id": conversation_context.user_metadata.get("user_id"),
                "wallet_address": wallet_address,
                "wallets": [{
                    "address": wallet_address,
                    "chain_type": conversation_context.user_metadata.get("wallet_chain"),
                    "is_primary": True,
                }] if wallet_address else [],
                "primary_wallet": {
                    "address": wallet_address,
                    "chain_type": conversation_context.user_metadata.get("wallet_chain"),
                } if wallet_address else None,
            }
        
        return None
    
    def _build_wallet_context(self, user_context: dict[str, Any]) -> str:
        """Build wallet context string from user data."""
        lines = []
        
        wallets = user_context.get("wallets", [])
        primary_wallet = user_context.get("primary_wallet")
        
        if not wallets:
            return """**Your Wallet is Being Set Up! 🔐**

Your Anvil wallet is being configured. This usually takes just a moment.

**What you can do:**
• **Refresh the page** if this persists
• **Check your account settings** to verify wallet status
• **Contact support** if you need help

Once your wallet is ready, you'll be able to:
• View your balances across all chains
• Swap, buy, and trade tokens
• Track your portfolio automatically"""
        
        lines.append(f"**Connected Wallets: {len(wallets)}**\n")
        
        for i, wallet in enumerate(wallets, 1):
            is_primary = (primary_wallet and 
                         wallet.get("address") == primary_wallet.get("address"))
            
            address = wallet.get("address", "Unknown")
            
            primary_marker = " (PRIMARY)" if is_primary else ""
            provider = wallet.get("provider")
            chain = wallet.get("chain_type")
            
            lines.append(f"**Wallet {i}{primary_marker}:**")
            # ALWAYS show the FULL address - users need the complete address
            lines.append(f"  - Address: `{address}`")
            # Only show provider and chain if they have valid values
            if provider and provider.lower() not in ("unknown", "none", ""):
                lines.append(f"  - Provider: {provider}")
            if chain and chain.lower() not in ("unknown", "none", ""):
                lines.append(f"  - Chain: {chain}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _create_auth_required_response(self, start_time: float) -> AgentResponse:
        """Create response for unauthenticated users."""
        latency_ms = int((time.time() - start_time) * 1000)
        
        content = """**Wallet Access Requires Authentication**

To view your wallet information, balances, and connected addresses, you need to sign in to your Anvil account.

**How to Connect:**
1. Click "Sign In" or "Connect Wallet" in the app
2. Choose your preferred method (email, social, or wallet)
3. Once connected, I can show you:
   - All your connected wallets
   - Balances across chains
   - Transaction history
   - Portfolio overview

Would you like me to help you with something else, or are you ready to sign in?"""
        
        from datetime import datetime, UTC
        from app.infrastructure.adapters.agent_squad.agents.source_helpers import create_llm_source
        
        return AgentResponse(
            content=content,
            agent_type=self.agent_type,
            tools_used=[],
            sources=[create_llm_source(model=self._model, fetched_at=datetime.now(UTC))],
            metadata={
                "latency_ms": latency_ms,
                "auth_required": True,
            },
        )
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for wallet agent."""
        return """You are the Wallet Agent, Anvil's wallet management specialist.

**YOUR ROLE:**
Show the user's connected wallet address AND their current balance. Keep it simple and concise.

**CRITICAL - SHOW FULL ADDRESS:**
ALWAYS show the COMPLETE wallet address (e.g., `0x742d35Cc6634C0532925a3b844Bc454e4438f44e`)
NEVER truncate or shorten addresses (do NOT use `0x742d...f44e` format)
Users NEED the full address to receive funds!

**IMPORTANT RULES:**
1. ONLY show wallet addresses from the provided context
2. Show the FULL address - never truncate!
3. ALWAYS show the balance if provided in the context
4. DO NOT suggest using external tools like Etherscan
5. Keep responses SHORT (5-7 lines max)
6. Include the suggestions provided in the context

**RESPONSE FORMAT:**
Show wallet info in this format:
- **Your Wallet:** `0xFULL_ADDRESS_HERE`
- **Balance:** $X.XX (if provided)
- Include any suggestions from context

**DO NOT:**
- Truncate wallet addresses
- Suggest external block explorers
- Give long explanations"""
