"""
Guest Auth Agent - Handles authentication requirements for restricted features.

Enhanced with knowledge agent integration to provide context-aware registration messages.
"""

import time
import logging

from app.domain.enums.agent_type import AgentType
from app.domain.value_objects.conversation_id import ConversationId
from app.domain.value_objects.message_content import MessageContent
from app.domain.value_objects.agent_squad.conversation_context import ConversationContext
from app.domain.ports.agent_squad.agent_gateway import AgentGateway, AgentResponse
from app.domain.ports.agent_squad.llm_client_gateway import LLMClientGateway

logger = logging.getLogger(__name__)


class GuestAuthAgent:
    """
    Guest Auth Agent implementation.
    
    Implements: AgentGateway
    
    Purpose: Handle authentication requirements for restricted features
    
    Capabilities:
    - Detect which restricted feature user is asking about
    - Use knowledge base to understand user's intent
    - Generate context-aware registration messages using LLM
    - Return appropriate custom registration message
    - Support multiple languages
    - Provide clear sign-in instructions
    
    Model: gemini-2.0-flash (fast, cost-effective)
    Temperature: 0.3 (consistent responses)
    """
    
    def __init__(
        self,
        llm_client: LLMClientGateway,
        model: str = "gemini-2.0-flash",
        temperature: float = 0.3,
        max_tokens: int = 500,
    ):
        """Initialize guest auth agent."""
        self._llm_client = llm_client
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._knowledge_injector = None  # Lazy load
    
    @property
    def agent_type(self) -> AgentType:
        """Get agent type."""
        return AgentType.GUEST_AUTH
    
    async def execute(
        self,
        conversation_id: ConversationId,
        message: MessageContent,
        conversation_context: ConversationContext,
    ) -> AgentResponse:
        """Execute guest auth agent - Return context-aware registration message."""
        start_time = time.time()
        
        # Get language from context
        language = conversation_context.user_metadata.get("language", "en") if conversation_context.user_metadata else "en"
        
        # Try to generate context-aware message using knowledge + LLM
        custom_message = None
        knowledge_used = False
        tokens_used = 0
        
        try:
            # Load knowledge injector lazily
            if self._knowledge_injector is None:
                try:
                    from app.application.chat.services.knowledge_injector import KnowledgeInjector
                    self._knowledge_injector = KnowledgeInjector()
                except Exception as e:
                    logger.warning(f"Could not load KnowledgeInjector: {e}")
                    self._knowledge_injector = None
            
            # Detect intent for knowledge retrieval
            detected_intent = self._detect_knowledge_intent(message.value)
            
            # Get relevant knowledge from knowledge base
            knowledge_context = ""
            if self._knowledge_injector:
                try:
                    user_type = "guest"
                    if conversation_context.user_metadata:
                        user_type = conversation_context.user_metadata.get("user_type", "guest")
                    
                    knowledge_dict = self._knowledge_injector.get_knowledge_for_intent(
                        user_query=message.value,
                        detected_intent=detected_intent,
                        user_type=user_type,
                    )
                    
                    if knowledge_dict:
                        knowledge_context = self._format_knowledge_context(knowledge_dict)
                        knowledge_used = True
                except Exception as e:
                    logger.warning(f"Error loading knowledge: {e}")
            
            # Generate context-aware message using LLM
            if knowledge_context:
                custom_message = await self._generate_contextual_message(
                    message.value,
                    knowledge_context,
                    language,
                    conversation_context,
                )
                tokens_used = 100  # Estimate for LLM call
        except Exception as e:
            logger.warning(f"Error generating contextual message: {e}, falling back to simple message")
        
        # Fallback to simple message if LLM generation failed
        if not custom_message:
            restricted_feature = self._detect_restricted_feature(message.value)
            custom_message = self._get_custom_message(restricted_feature, conversation_context)
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        # Collect sources
        from datetime import datetime, UTC
        from app.domain.value_objects.chat.source_info import SourceInfo, SourceType
        
        sources = []
        fetched_at = datetime.now(UTC)
        
        # Add LLM source
        sources.append(SourceInfo(
            source_type=SourceType.LLM,
            source_name=self._model,
            citation_text=f"Generated by {self._model}" + (" with knowledge base" if knowledge_used else ""),
            fetched_at=fetched_at,
            provider="Vertex AI" if "gemini" in self._model.lower() else "DeepInfra",
            metadata={
                "model": self._model,
                "knowledge_used": knowledge_used,
                "contextual": knowledge_used,
            },
        ))
        
        return AgentResponse(
            content=custom_message,
            agent_type=self.agent_type,
            tools_used=["auth_detection", "knowledge_base"] if knowledge_used else ["auth_detection"],
            sources=sources,
            metadata={
                "tokens_used": tokens_used,
                "latency_ms": latency_ms,
                "model": self._model,
                "knowledge_used": knowledge_used,
                "provider": "vertex_ai" if "gemini" in self._model.lower() else "deepinfra",
            },
        )
    
    def _detect_knowledge_intent(self, query: str) -> str:
        """Detect knowledge intent from query (similar to KnowledgeAgent)."""
        query_lower = query.lower()
        
        # Lending queries (Morpho) - highest priority for "Supply X to Morpho"
        if any(kw in query_lower for kw in ["lending", "lend", "morpho", "vault", "supply", "deposit assets", "earn yield", "deposit"]):
            return "LENDING_MORPHO"
        
        # Swap queries
        if any(kw in query_lower for kw in ["swap", "exchange", "trade tokens"]):
            return "SWAP"
        
        # Buy queries
        if any(kw in query_lower for kw in ["buy crypto", "purchase", "buy with card", "on-ramp"]):
            return "BUY"
        
        # Send queries
        if any(kw in query_lower for kw in ["send crypto", "transfer tokens", "send to"]):
            return "SEND"
        
        # Portfolio queries
        if any(kw in query_lower for kw in ["portfolio", "balance", "holdings", "my assets"]):
            return "PORTFOLIO"
        
        # Wallet queries
        if any(kw in query_lower for kw in ["wallet", "address", "receive"]):
            return "WALLET"
        
        # Activity queries
        if any(kw in query_lower for kw in ["transactions", "activity", "history"]):
            return "ACTIVITY"
        
        # Default
        return "execute_action"
    
    def _format_knowledge_context(self, knowledge_dict: dict) -> str:
        """Format knowledge dictionary as context string."""
        context_parts = []
        
        if "feature_name" in knowledge_dict:
            context_parts.append(f"Feature: {knowledge_dict['feature_name']}")
        
        if "tagline" in knowledge_dict:
            context_parts.append(f"Tagline: {knowledge_dict['tagline']}")
        
        if "description" in knowledge_dict:
            context_parts.append(f"Description: {knowledge_dict['description']}")
        
        if "capability" in knowledge_dict:
            if isinstance(knowledge_dict["capability"], dict):
                cap = knowledge_dict["capability"]
                context_parts.append(f"Capability: {cap.get('name', '')} - {cap.get('description', '')}")
        
        # Format features if available
        if "features" in knowledge_dict:
            features = knowledge_dict["features"]
            if isinstance(features, list):
                context_parts.append(f"Features: {', '.join(features[:5])}")  # First 5 features
        
        # Format competitive advantages if available
        if "competitive_advantages" in knowledge_dict:
            advantages = knowledge_dict["competitive_advantages"]
            if isinstance(advantages, list):
                context_parts.append(f"Advantages: {', '.join(advantages[:3])}")  # First 3
        
        return "\n".join(context_parts) if context_parts else ""
    
    async def _generate_contextual_message(
        self,
        user_query: str,
        knowledge_context: str,
        language: str,
        conversation_context: ConversationContext,
    ) -> str:
        """Generate context-aware registration message using LLM."""
        # Get CTA message
        from app.application.guest.i18n.translations import get_cta_message
        cta = get_cta_message(language)
        
        # Build prompt for LLM
        system_prompt = f"""You are a helpful assistant that explains why users need to sign up for Anvil to use specific features.

Based on the user's query and the feature information provided, create a brief, friendly registration message that:
1. Acknowledges what the user wants to do
2. Explains why they need an account (briefly)
3. Ends with the CTA: "👉 {cta}"

Keep it concise (2-3 sentences max). Be specific about what they'll be able to do.
Respond in {language.upper()} language.

Example for "Supply 1000 USDC to Morpho":
"To supply USDC to Morpho vaults and start earning yield, you'll need to create an account. This allows you to securely connect your wallet and execute DeFi transactions.

👉 {cta}"

Example for "Buy crypto":
"To buy crypto with a card or bank transfer, you'll need to create an account. This gives you access to multiple on-ramp providers and the best rates.

👉 {cta}"
"""
        
        user_prompt = f"""User query: "{user_query}"

Feature information:
{knowledge_context}

Generate a registration message:"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        
        try:
            response = await self._llm_client.chat(
                messages=messages,
                model=self._model,
                temperature=self._temperature,
                max_tokens=self._max_tokens,
            )
            
            if response and response.strip():
                return response.strip()
        except Exception as e:
            logger.warning(f"Error generating contextual message: {e}")
        
        return None  # Fallback to simple message
    
    def _detect_restricted_feature(self, message: str) -> str:
        """Detect which restricted feature user is asking about."""
        message_lower = message.lower()
        
        # Priority order (most specific first)
        if any(kw in message_lower for kw in ["my balance", "what's my balance", "check my balance", "how much do i have", "wallet balance"]):
            return "balance"
        elif any(kw in message_lower for kw in ["my transactions", "transaction history", "show my activity", "recent activity", "my activity", "my trades"]):
            return "activity"
        elif any(kw in message_lower for kw in ["my address", "wallet address", "receive crypto", "deposit address", "QR code", "receive address", "i want to receive"]):
            return "receive"
        elif any(kw in message_lower for kw in ["buy crypto", "purchase bitcoin", "buy with card", "how to buy ETH", "i want to buy", "buy with fiat"]):
            return "buy"
        elif any(kw in message_lower for kw in ["send crypto", "transfer tokens", "send to wallet", "send to friend", "i want to send", "transfer crypto"]):
            return "send"
        elif any(kw in message_lower for kw in ["my portfolio", "my holdings", "list my tokens", "what tokens do i have", "show my holdings", "what tokens do i own"]):
            return "portfolio"
        elif any(kw in message_lower for kw in ["lending", "lend", "morpho", "vault", "supply", "deposit assets", "earn yield"]):
            return "lending"
        else:
            return "general"  # Fallback
    
    def _get_custom_message(self, feature: str, context: ConversationContext) -> str:
        """Get custom registration message for restricted feature."""
        # Get language from context
        language = context.user_metadata.get("language", "en") if context.user_metadata else "en"
        
        # Import translation function
        from app.application.guest.i18n.translations import get_registration_message
        
        # Map feature to reason
        feature_to_reason = {
            "balance": "wallet_access",
            "activity": "transaction_history",
            "receive": "wallet_address",
            "buy": "buy_crypto",
            "send": "send_crypto",
            "portfolio": "portfolio_access",
            "lending": "execute_deposit",
            "general": "execute_action",  # Fallback
        }
        
        reason = feature_to_reason.get(feature, "execute_action")
        messages = get_registration_message(reason, language)
        message = messages.get(language, messages.get("en", ""))
        
        # Add CTA
        from app.application.guest.i18n.translations import get_cta_message
        cta = get_cta_message(language)
        
        return f"{message}\n\n👉 {cta}"
    
    async def is_available(self) -> bool:
        """Check if agent is available."""
        return True
