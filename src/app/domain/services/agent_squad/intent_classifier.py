"""
Intent Classifier domain service - Classifies user intent for routing.
"""

from typing import Protocol
from dataclasses import dataclass

from app.domain.enums.agent_type import AgentType
from app.domain.value_objects.message_content import MessageContent


@dataclass
class ConversationContext:
    """
    Conversation context for intent classification.
    
    Contains:
    - conversation_history: Recent messages (for context)
    - user_metadata: User preferences, portfolio, etc.
    - session_metadata: Current session info
    """
    conversation_history: list[dict]  # Recent messages
    user_metadata: dict  # User profile, preferences, portfolio
    session_metadata: dict  # Session info
    
    @property
    def last_n_messages(self, n: int = 5) -> list[dict]:
        """Get last N messages for context."""
        return self.conversation_history[-n:] if self.conversation_history else []
    
    @property
    def has_history(self) -> bool:
        """Check if conversation has history."""
        return len(self.conversation_history) > 0

    @property
    def last_agent_type(self) -> AgentType | None:
        """Get the agent type of the last agent message."""
        for message in reversed(self.conversation_history):
            if message.get("role") == "agent" and message.get("agent_type"):
                # Handle both string and AgentType values
                agent_type_value = message["agent_type"]
                if isinstance(agent_type_value, AgentType):
                    return agent_type_value
                return AgentType(agent_type_value)
        return None


class IntentClassifier:
    """
    Intent Classifier domain service.
    
    Responsibilities:
    - Classify user intent from message content
    - Recommend appropriate agent for intent
    - Support multi-turn conversation context
    - Provide confidence scores
    
    Architecture:
    - Domain service (framework-agnostic)
    - Uses LLM port for classification
    - Returns intent classification (not agent responses)
    
    Intent Categories (Examples):
    - swap_tokens: Execute token swap (EXECUTION agent)
    - analyze_risk: Risk assessment (RISK_ANALYZER agent)
    - research_protocol: Deep protocol analysis (RESEARCH agent)
    - optimize_portfolio: Portfolio optimization (PORTFOLIO agent)
    - check_compliance: AML/KYC screening (COMPLIANCE_MONITOR agent)
    - manage_multisig: Treasury operations (MULTISIG_COORDINATOR agent)
    - alert_setup: Risk alerts (ALERT_MONITORING agent)
    - crisis_response: Emergency response (CRISIS_MANAGER agent)
    """
    
    # Intent to Agent mapping
    INTENT_AGENT_MAP = {
        # Core user intents
        "general_chat": AgentType.CHAT,
        "anvil_knowledge": AgentType.CHAT,  # Anvil knowledge → Chat agent
        "general_question": AgentType.CHAT,  # General questions → Chat agent
        "price_query": AgentType.HUNTER_AI,  # Price queries → Hunter AI
        "market_sentiment": AgentType.HUNTER_AI,
        "research_protocol": AgentType.RESEARCH,
        "swap_tokens": AgentType.EXECUTION,
        "execute_transaction": AgentType.EXECUTION,
        "analyze_risk": AgentType.RISK_ANALYZER,
        "risk_assessment": AgentType.RISK_ANALYZER,
        "optimize_portfolio": AgentType.PORTFOLIO,
        "rebalance_portfolio": AgentType.PORTFOLIO,
        "tax_optimization": AgentType.TAX_OPTIMIZER,
        "tax_loss_harvesting": AgentType.TAX_OPTIMIZER,
        "find_yield": AgentType.DEFI_YIELD,
        "yield_farming": AgentType.DEFI_YIELD,
        "audit_contract": AgentType.SECURITY_AUDITOR,
        "security_audit": AgentType.SECURITY_AUDITOR,
        "optimize_gas": AgentType.GAS_OPTIMIZER,
        "gas_estimation": AgentType.GAS_OPTIMIZER,
        
        # Enterprise intents
        "check_compliance": AgentType.COMPLIANCE_MONITOR,
        "screen_wallet": AgentType.COMPLIANCE_MONITOR,
        "manage_multisig": AgentType.MULTISIG_COORDINATOR,
        "treasury_management": AgentType.MULTISIG_COORDINATOR,
        "setup_alerts": AgentType.ALERT_MONITORING,
        "monitor_portfolio": AgentType.ALERT_MONITORING,
        "crisis_response": AgentType.CRISIS_MANAGER,
        "emergency_withdrawal": AgentType.CRISIS_MANAGER,
        "bridge_tokens": AgentType.BRIDGE_CROSSCHAIN,
        "cross_chain": AgentType.BRIDGE_CROSSCHAIN,
        "borrow_assets": AgentType.LENDING_BORROWING,
        "leverage_position": AgentType.LENDING_BORROWING,
        "manage_nfts": AgentType.NFT_ASSET_MANAGER,
        "nft_valuation": AgentType.NFT_ASSET_MANAGER,
        "dao_voting": AgentType.DAO_GOVERNANCE,
        "governance_proposal": AgentType.DAO_GOVERNANCE,
    }
    
    def __init__(
        self,
        llm_client: "LLMClientPort",
        classification_model: str = "meta-llama/Meta-Llama-3.1-8B-Instruct",  # DeepInfra-compatible model
    ):
        """
        Initialize intent classifier.
        
        Args:
            llm_client: LLM client port for classification
            classification_model: Model to use (default gpt-4o-mini for speed)
        """
        self._llm_client = llm_client
        self._classification_model = classification_model
    
    async def classify(
        self,
        message: MessageContent,
        conversation_context: ConversationContext,
    ) -> "IntentClassification":
        """
        Classify user intent from message.
        
        Uses LLM to classify intent and recommend agent.
        
        Args:
            message: User message
            conversation_context: Conversation history & metadata
            
        Returns:
            IntentClassification with intent, confidence, and agent
        """
        # Build classification prompt
        prompt = self._build_classification_prompt(message, conversation_context)
        
        # Call LLM for classification
        response = await self._llm_client.classify_intent(
            prompt=prompt,
            model=self._classification_model,
        )
        
        # Parse response
        intent = response.get("intent", "general_chat")
        confidence = response.get("confidence", 0.5)
        reasoning = response.get("reasoning", "")
        
        # Map intent to agent
        agent_type = self.INTENT_AGENT_MAP.get(intent, AgentType.CHAT)
        
        # Import IntentClassification from agent_orchestrator to avoid circular import
        from .agent_orchestrator import IntentClassification
        
        return IntentClassification(
            intent=intent,
            confidence=confidence,
            agent_type=agent_type,
            reasoning=reasoning,
        )
    
    async def recommend_agents_for_complex_task(
        self,
        message: MessageContent,
        conversation_context: ConversationContext,
        max_agents: int = 5,
    ) -> list[AgentType]:
        """
        Recommend multiple agents for complex task.
        
        Used for supervisor-coordinated workflows.
        
        Args:
            message: User message
            conversation_context: Conversation history
            max_agents: Maximum agents to recommend
            
        Returns:
            List of agent types for complex task
        """
        # Build complex task prompt
        prompt = self._build_complex_task_prompt(message, conversation_context, max_agents)
        
        # Call LLM for agent recommendation
        response = await self._llm_client.recommend_agents(
            prompt=prompt,
            model=self._classification_model,
        )
        
        # Parse agent list
        agent_names = response.get("agents", ["chat"])
        
        # Map to AgentType
        agents = []
        for agent_name in agent_names[:max_agents]:
            try:
                agent_type = AgentType[agent_name.upper()]
                agents.append(agent_type)
            except KeyError:
                # Invalid agent name, skip
                continue
        
        # Fallback to CHAT if no valid agents
        if not agents:
            agents = [AgentType.CHAT]
        
        return agents
    
    def _build_classification_prompt(
        self,
        message: MessageContent,
        conversation_context: ConversationContext,
    ) -> str:
        """
        Build intent classification prompt for LLM.
        
        Enhanced to recognize:
        - Price queries → price_query intent → Hunter AI
        - Anvil knowledge → anvil_knowledge intent → Chat agent
        - General questions → general_question intent → Chat agent
        - Shortcuts → appropriate intents (swap_tokens, lending, etc.)
        """
        context_str = ""
        if conversation_context.has_history:
            recent_messages = conversation_context.last_n_messages(3)
            context_str = "\n".join([
                f"- {msg.get('role', 'user')}: {msg.get('content', '')}"
                for msg in recent_messages
            ])
        
        available_intents = ", ".join(self.INTENT_AGENT_MAP.keys())
        
        return f"""
Classify the user's intent from the following message.

User Message:
{message.value}

Recent Conversation Context:
{context_str if context_str else "(No previous context)"}

Available Intents:
{available_intents}

Respond with JSON:
{{
    "intent": "intent_name",
    "confidence": 0.0-1.0,
    "reasoning": "why this intent was selected"
}}

Guidelines:
- **Informational queries** (e.g., "what is btc?", "what is eth?", "explain DeFi", "tell me about Anvil") → Use "general_question" intent (FAST PATH - single agent)
- **Price queries** (e.g., "what is the price of btc?", "how much is ETH?", "current price of bitcoin") → Use "price_query" intent
- **Anvil knowledge** (e.g., "what is Anvil?", "how does Anvil work?", "Anvil features") → Use "anvil_knowledge" intent
- **General questions** (e.g., "what is DeFi?", "explain yield farming", "what are NFTs?") → Use "general_question" intent
- **Shortcuts** (e.g., "swap BTC to ETH", "show my portfolio", "lend USDC") → Use appropriate intent:
  * "swap BTC to ETH" → "swap_tokens"
  * "show my portfolio" → "optimize_portfolio"
  * "lend USDC" → "find_yield"
  * "what's my balance?" → "optimize_portfolio"
- **Multi-step operations** → Use "general_chat" and let SupervisorCoordinator create workflow
- Use "general_chat" for casual conversation or unclear intent
- Use specific intent if message clearly matches (confidence >= 0.85)
- Consider conversation context for multi-turn conversations
- Enterprise intents (compliance, multisig, crisis) require explicit keywords
- **IMPORTANT**: "what is X" or "explain X" queries should use "general_question" intent for fast single-agent response
"""
    
    def _build_complex_task_prompt(
        self,
        message: MessageContent,
        conversation_context: ConversationContext,
        max_agents: int,
    ) -> str:
        """Build complex task agent recommendation prompt."""
        available_agents = [agent.value for agent in AgentType.get_all_agents()]
        
        return f"""
The user is requesting a complex task that requires multiple specialist agents.

User Message:
{message.value}

Available Agents:
{", ".join(available_agents)}

Agent Capabilities:
- chat: General conversation
- hunter_ai: Market sentiment & predictions
- research: Deep protocol analysis
- execution: Transaction execution
- risk_analyzer: Risk assessment
- portfolio: Portfolio optimization
- tax_optimizer: Tax strategies
- defi_yield: Yield farming
- security_auditor: Smart contract security
- gas_optimizer: Gas optimization
- compliance_monitor: AML/KYC (enterprise)
- multisig_coordinator: Treasury management (enterprise)
- alert_monitoring: Real-time alerts (enterprise)
- crisis_manager: Emergency response (enterprise)
- bridge_crosschain: Layer 2 operations
- lending_borrowing: Leverage optimization
- nft_asset_manager: NFT portfolio
- dao_governance: DAO voting

Select up to {max_agents} agents for this task.

Respond with JSON:
{{
    "agents": ["agent1", "agent2", ...],
    "reasoning": "why these agents were selected"
}}
"""


# Port (interface) for dependency injection

class LLMClientPort(Protocol):
    """Port for LLM client (intent classification)."""
    
    async def classify_intent(
        self,
        prompt: str,
        model: str,
    ) -> dict:
        """Classify intent using LLM."""
        ...
    
    async def recommend_agents(
        self,
        prompt: str,
        model: str,
    ) -> dict:
        """Recommend agents for complex task."""
        ...
