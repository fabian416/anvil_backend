"""
Transaction History Agent - Transaction history queries for authenticated users.

This agent is ONLY available for authenticated users and provides:
- View recent transactions
- Filter by chain, type, or date
- Transaction volume analytics
- Activity summaries
- Transaction status tracking

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


class TransactionHistoryAgent:
    """
    Transaction History Agent implementation for authenticated users.
    
    Implements: AgentGateway
    
    Purpose: Transaction history queries and analytics
    
    Capabilities:
    - View recent transactions
    - Filter by chain, type, date range
    - Transaction volume analytics (30-day)
    - Most active chain identification
    - Transaction status tracking (pending, success, failed)
    
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
        max_tokens: int = 2000,
    ):
        """
        Initialize transaction history agent.
        
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
        return AgentType.TRANSACTION_HISTORY
    
    async def execute(
        self,
        conversation_id: ConversationId,
        message: MessageContent,
        conversation_context: ConversationContext,
    ) -> AgentResponse:
        """
        Execute transaction history agent - handle transaction queries.
        
        Expects user_context in conversation_context.user_metadata containing:
        - transactions: TransactionSummary with recent_transactions, volume, etc.
        """
        start_time = time.time()
        
        # Extract user context from conversation metadata
        user_context = self._extract_user_context(conversation_context)
        
        if not user_context:
            # User is not authenticated or no transaction data
            return self._create_auth_required_response(start_time)
        
        # Build context string with user's transaction data
        tx_context = self._build_transaction_context(user_context)
        
        # Build enhanced prompt with actual transaction data
        enhanced_message = f"""User Query: {message.value}

**USER'S TRANSACTION DATA (REAL DATA - USE THIS):**
{tx_context}

Respond to the user's query using ONLY the transaction data provided above.
Do NOT make up transaction hashes or amounts.
If the user asks about something not in their data, explain what data is available."""
        
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
        
        # Add database source (transaction data)
        sources.append(create_database_source(
            citation_text="Your transaction history from Anvil",
            fetched_at=fetched_at,
            metadata={"query_type": "transaction_history"},
        ))
        
        # Add LLM source
        model_name = response.get("model", self._model)
        sources.append(create_llm_source(
            model=model_name,
            fetched_at=fetched_at,
        ))
        
        provider_info = response.get("provider", "vertex_ai" if "gemini" in model_name.lower() else "deepinfra")
        
        tx_data = user_context.get("transactions", {})
        
        return AgentResponse(
            content=response["content"],
            agent_type=self.agent_type,
            tools_used=["llm_gateway", "transaction_repository"],
            sources=sources,
            metadata={
                "tokens_used": response.get("tokens_used"),
                "latency_ms": latency_ms,
                "model": model_name,
                "provider": provider_info,
                "transaction_count": tx_data.get("total_count", 0) if isinstance(tx_data, dict) else 0,
            },
        )
    
    async def is_available(self) -> bool:
        """Check if agent is available."""
        return True
    
    def _extract_user_context(self, conversation_context: ConversationContext) -> dict[str, Any] | None:
        """Extract user context from conversation metadata."""
        if not conversation_context.user_metadata:
            return None
        
        # Check for user_context or direct transaction data
        if "user_context" in conversation_context.user_metadata:
            return conversation_context.user_metadata["user_context"]
        
        # Check for direct transaction data
        if "transactions" in conversation_context.user_metadata:
            return conversation_context.user_metadata
        
        # Check for flat structure (user_id, wallet_address, is_authenticated at top level)
        # This is how the supervisor passes user context
        if conversation_context.user_metadata.get("is_authenticated"):
            return {
                "user_id": conversation_context.user_metadata.get("user_id"),
                "wallet_address": conversation_context.user_metadata.get("wallet_address"),
                "transactions": conversation_context.user_metadata.get("transactions"),
                "primary_wallet": {
                    "address": conversation_context.user_metadata.get("wallet_address"),
                    "chain_type": conversation_context.user_metadata.get("wallet_chain"),
                } if conversation_context.user_metadata.get("wallet_address") else None,
            }
        
        return None
    
    def _build_transaction_context(self, user_context: dict[str, Any]) -> str:
        """Build transaction context string from user data."""
        lines = []
        
        tx_data = user_context.get("transactions", {})
        
        if not tx_data:
            return "No transaction history available. Make your first transaction to see it here!"
        
        # Handle TransactionSummary dataclass or dict
        if hasattr(tx_data, "total_count"):
            # Dataclass
            total_count = tx_data.total_count
            recent_txs = tx_data.recent_transactions or []
            volume_30d = tx_data.volume_last_30_days or 0
            most_active = tx_data.most_active_chain
        else:
            # Dict
            total_count = tx_data.get("total_count", 0)
            recent_txs = tx_data.get("recent_transactions", [])
            volume_30d = tx_data.get("volume_last_30_days", 0)
            most_active = tx_data.get("most_active_chain")
        
        lines.append(f"**Transaction Summary:**")
        lines.append(f"- Total Transactions: {total_count}")
        lines.append(f"- 30-Day Volume: ${volume_30d:,.2f}")
        if most_active:
            lines.append(f"- Most Active Chain: {most_active}")
        lines.append("")
        
        if recent_txs:
            lines.append(f"**Recent Transactions ({len(recent_txs)} shown):**\n")
            
            for i, tx in enumerate(recent_txs[:10], 1):
                tx_hash = tx.get("tx_hash", "Unknown")
                tx_type = tx.get("type", "Unknown")
                status = tx.get("status", "Unknown")
                chain = tx.get("chain", "Unknown")
                amount = tx.get("amount", 0)
                created = tx.get("created_at", "Unknown")
                
                # Status emoji
                status_emoji = {
                    "success": "✅",
                    "pending": "⏳",
                    "failed": "❌",
                }.get(status.lower() if status else "", "❓")
                
                lines.append(f"**{i}. {tx_type}** {status_emoji}")
                if tx_hash and tx_hash != "Unknown":
                    lines.append(f"   - Hash: `{tx_hash}`")
                lines.append(f"   - Chain: {chain}")
                if amount:
                    lines.append(f"   - Amount: {amount}")
                lines.append(f"   - Status: {status}")
                if created and created != "Unknown":
                    lines.append(f"   - Date: {created[:19] if len(created) > 19 else created}")
                lines.append("")
        else:
            lines.append("**Recent Transactions:** None available")
        
        return "\n".join(lines)
    
    def _create_auth_required_response(self, start_time: float) -> AgentResponse:
        """Create response for unauthenticated users."""
        latency_ms = int((time.time() - start_time) * 1000)
        
        content = """**Transaction History Requires Authentication**

To view your transaction history, you need to sign in to your Anvil account.

**Once signed in, you can:**
- View all your past transactions
- Filter by chain (Ethereum, Polygon, Arbitrum, etc.)
- Filter by type (Swap, Transfer, Approve, etc.)
- See transaction status (Success, Pending, Failed)
- View 30-day volume analytics
- Track gas costs and fees

**How to Sign In:**
1. Click "Sign In" or "Connect Wallet"
2. Choose your preferred method
3. Return here to view your history

Would you like me to help you with something else?"""
        
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
        """Get system prompt for transaction history agent."""
        return """You are the Transaction History Agent, Anvil's transaction analytics specialist for authenticated users.

**YOUR ROLE:**
You help authenticated users understand their transaction history and activity.

**IMPORTANT RULES:**
1. ONLY use the transaction data provided in the user's context
2. NEVER make up transaction hashes, amounts, or dates
3. If data is missing, explain what data IS available
4. Be accurate - transactions involve real money

**CAPABILITIES:**
- Show recent transactions with details
- Summarize transaction activity
- Identify patterns (most active chain, volume trends)
- Explain transaction statuses
- Help users find specific transactions

**TRANSACTION TYPES:**
- **SWAP**: Token exchange via DEX
- **TRANSFER**: Send tokens to another address
- **APPROVE**: Authorize contract to spend tokens
- **WRAP/UNWRAP**: ETH <-> WETH conversion
- **STAKE/UNSTAKE**: Staking operations
- **DEPOSIT/WITHDRAW**: DeFi protocol operations

**TRANSACTION STATUS:**
- **Success** ✅: Confirmed on blockchain
- **Pending** ⏳: Awaiting confirmation
- **Failed** ❌: Transaction reverted

**RESPONSE FORMAT:**
- Use markdown formatting
- Show transaction hashes (truncated for readability)
- Include relevant chain and timing info
- Provide actionable insights when possible

**ANALYTICS INSIGHTS:**
When asked for analysis:
- Compare 30-day volume to patterns
- Identify most-used chains
- Highlight any unusual activity
- Suggest optimizations (gas timing, chain selection)"""
