"""
Agent Orchestrator domain service - Routes messages to correct agent.
"""

from typing import Protocol
from dataclasses import dataclass

from app.domain.enums.agent_type import AgentType
from app.domain.value_objects.conversation_id import ConversationId
from app.domain.value_objects.message_content import MessageContent


@dataclass
class IntentClassification:
    """
    Intent classification result.
    
    Contains:
    - intent: Classified user intent (e.g., "swap_tokens", "analyze_risk")
    - confidence: Classification confidence (0.0-1.0)
    - agent_type: Recommended agent for this intent
    - reasoning: Why this agent was selected (for transparency)
    """
    intent: str
    confidence: float
    agent_type: AgentType
    reasoning: str
    
    @property
    def is_high_confidence(self) -> bool:
        """Check if confidence is high (>=0.85)."""
        return self.confidence >= 0.85
    
    @property
    def is_low_confidence(self) -> bool:
        """Check if confidence is low (<0.5)."""
        return self.confidence < 0.5


@dataclass
class AgentRoutingResult:
    """
    Agent routing result.
    
    Contains:
    - agent_type: Selected agent
    - intent_classification: Intent classification details
    - fallback_used: Whether fallback agent was used
    """
    agent_type: AgentType
    intent_classification: IntentClassification
    fallback_used: bool


class AgentOrchestrator:
    """
    Agent Orchestrator domain service.
    
    Responsibilities:
    - Route messages to correct agent based on intent
    - Use IntentClassifier for intent detection
    - Handle low-confidence routing (fallback to chat agent)
    - Validate agent availability (feature flags)
    - Log routing decisions for telemetry
    
    Architecture:
    - Domain service (framework-agnostic)
    - Uses ports for external dependencies (IntentClassifier, FeatureFlags)
    - Returns routing decisions (not agent responses)
    """
    
    def __init__(
        self,
        intent_classifier: "IntentClassifierPort",
        feature_flags: "FeatureFlagsPort",
        agent_registry: dict[AgentType, "AgentGateway"] | None = None,
        confidence_threshold: float = 0.85,
        fallback_agent: AgentType = AgentType.CHAT,
    ):
        """
        Initialize agent orchestrator.
        
        Args:
            intent_classifier: Intent classification port
            feature_flags: Feature flags port (agent enable/disable)
            agent_registry: Registry mapping agent types to implementations
            confidence_threshold: Minimum confidence for routing (default 0.85)
            fallback_agent: Fallback agent for low confidence (default CHAT)
        """
        self._intent_classifier = intent_classifier
        self._feature_flags = feature_flags
        self._agent_registry = agent_registry or {}
        self._confidence_threshold = confidence_threshold
        self._fallback_agent = fallback_agent
    
    async def route_message(
        self,
        conversation_id: ConversationId,
        message: MessageContent,
        conversation_context: "ConversationContext",
    ) -> AgentRoutingResult:
        """
        Route message to appropriate agent.
        
        Process:
        1. Classify user intent using IntentClassifier
        2. Check confidence threshold
        3. Validate agent availability (feature flags)
        4. Return routing decision
        
        Args:
            conversation_id: Conversation identifier
            message: User message
            conversation_context: Conversation history & metadata
            
        Returns:
            AgentRoutingResult with selected agent and intent details
        """
        # 1. Classify intent
        intent_classification = await self._intent_classifier.classify(
            message=message,
            conversation_context=conversation_context,
        )
        
        # 2. Check confidence threshold
        if intent_classification.confidence < self._confidence_threshold:
            # Low confidence - use fallback agent
            return AgentRoutingResult(
                agent_type=self._fallback_agent,
                intent_classification=intent_classification,
                fallback_used=True,
            )
        
        # 3. Check if agent is enabled (feature flag)
        agent_type = intent_classification.agent_type
        if not await self._feature_flags.is_agent_enabled(agent_type):
            # Agent disabled - use fallback
            return AgentRoutingResult(
                agent_type=self._fallback_agent,
                intent_classification=intent_classification,
                fallback_used=True,
            )
        
        # 4. Route to recommended agent
        return AgentRoutingResult(
            agent_type=agent_type,
            intent_classification=intent_classification,
            fallback_used=False,
        )
    
    async def select_agents_for_complex_task(
        self,
        message: MessageContent,
        conversation_context: "ConversationContext",
        max_agents: int = 5,
    ) -> list[AgentType]:
        """
        Select multiple agents for complex multi-agent task.
        
        Used by SupervisorCoordinator for complex workflows.
        
        Args:
            message: User message
            conversation_context: Conversation history
            max_agents: Maximum agents to select (default 5)
            
        Returns:
            List of agent types for complex task
        """
        # Use intent classifier to recommend agents
        agents = await self._intent_classifier.recommend_agents_for_complex_task(
            message=message,
            conversation_context=conversation_context,
            max_agents=max_agents,
        )
        
        # Filter by availability (feature flags)
        available_agents = []
        for agent_type in agents:
            if await self._feature_flags.is_agent_enabled(agent_type):
                available_agents.append(agent_type)
        
        return available_agents[:max_agents]
    
    async def execute_agent(
        self,
        agent_type: AgentType,
        message: str,
        conversation_context: "ConversationContext",
    ) -> "AgentResponse":
        """
        Execute specific agent with message and context.
        
        Args:
            agent_type: Agent to execute
            message: User message
            conversation_context: Conversation history
            
        Returns:
            Agent response with content, tools used, metadata
            
        Raises:
            ValueError: If agent not found in registry
        """
        from app.domain.value_objects.conversation_id import ConversationId
        
        # Get agent from registry
        agent = self._agent_registry.get(agent_type)
        if not agent:
            raise ValueError(f"Agent {agent_type.value} not found in registry")
        
        # Execute agent
        response = await agent.execute(
            conversation_id=conversation_context.conversation_id,
            message=message,
            context=conversation_context,
        )
        
        return response


# Ports (interfaces) for dependency injection

class IntentClassifierPort(Protocol):
    """Port for intent classification."""
    
    async def classify(
        self,
        message: MessageContent,
        conversation_context: "ConversationContext",
    ) -> IntentClassification:
        """Classify user intent."""
        ...
    
    async def recommend_agents_for_complex_task(
        self,
        message: MessageContent,
        conversation_context: "ConversationContext",
        max_agents: int,
    ) -> list[AgentType]:
        """Recommend multiple agents for complex task."""
        ...


class FeatureFlagsPort(Protocol):
    """Port for feature flags (agent enable/disable)."""
    
    async def is_agent_enabled(self, agent_type: AgentType) -> bool:
        """Check if agent is enabled via feature flag."""
        ...
