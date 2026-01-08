"""
Chat-related request/response schemas.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


# Request schemas
class CreateConversationRequest(BaseModel):
    """Request to create a new conversation."""
    
    title: Optional[str] = Field(None, max_length=200)


class SendMessageRequest(BaseModel):
    """Request to send a message."""
    
    content: str = Field(..., min_length=1, max_length=10000)
    language: Optional[str] = Field(
        default="en",
        description="Response language code: en, es, fr, zh, pt",
        pattern="^(en|es|fr|zh|pt)$",
    )


# Response schemas
class ConversationResponse(BaseModel):
    """Conversation response."""
    
    id: UUID
    user_id: int
    title: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class SourceInfoResponse(BaseModel):
    """Source information response for frontend."""
    
    source_type: str  # api, database, mcp_server, rss_feed, social_media, blockchain, llm, aggregated
    source_name: str
    source_id: Optional[str] = None
    url: Optional[str] = None
    citation_text: Optional[str] = None
    fetched_at: Optional[str] = None  # ISO format
    data_age_seconds: Optional[int] = None
    provider: Optional[str] = None
    endpoint: Optional[str] = None
    query_params: Optional[dict] = None
    relevance_score: Optional[float] = None
    data_points_used: Optional[int] = None
    metadata: Optional[dict] = None


class MessageResponse(BaseModel):
    """Message response with source attribution."""
    
    id: UUID
    conversation_id: UUID
    role: str
    content: str
    agent_type: Optional[str]
    sources: List[SourceInfoResponse] = Field(default_factory=list)  # NEW
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
    
    @classmethod
    def from_domain(cls, message: "Message") -> "MessageResponse":
        """Create response from domain entity."""
        from app.domain.entities.message import Message as DomainMessage
        from app.domain.value_objects.chat.source_info import SourceInfo
        
        # Extract sources from metadata
        sources = []
        if message.metadata and "sources" in message.metadata:
            sources_data = message.metadata["sources"]
            if isinstance(sources_data, list):
                sources = []
                for s in sources_data:
                    if isinstance(s, dict):
                        sources.append(SourceInfoResponse(**s))
                    elif hasattr(s, "to_dict"):
                        sources.append(SourceInfoResponse(**s.to_dict()))
        
        return cls(
            id=message.id,
            conversation_id=message.conversation_id,
            role=message.role.value if hasattr(message.role, "value") else str(message.role),
            content=message.content,
            agent_type=message.agent_type,
            sources=sources,
            created_at=message.created_at,
        )


class SendMessageResponse(BaseModel):
    """Response for send message containing both user and agent messages."""

    user_message: MessageResponse
    agent_message: MessageResponse


# NEW: Unified Routing Schemas

class RoutingMetadata(BaseModel):
    """Routing metadata for unified chat responses."""

    intent: str  # Detected intent type
    confidence: float = Field(..., ge=0.0, le=1.0)  # Classification confidence
    handler: str  # Which handler processed the message
    agent_used: Optional[str] = None  # If Agent Squad, which agent
    reasoning: Optional[str] = None  # Why this route was chosen
    total_latency_ms: Optional[int] = None  # Total processing time
    language: Optional[str] = Field(
        default="en",
        description="Response language code used: en, es, fr, zh, pt",
    )


class EnrichmentData(BaseModel):
    """Optional enrichment data based on handler type."""

    # For GraphRAG Search
    protocols: Optional[List[dict]] = None
    search_context: Optional[str] = None
    recommendations: Optional[List[str]] = None

    # For GraphRAG Risk
    risk_analysis: Optional[dict] = None
    alternatives_count: Optional[int] = None

    # For GraphRAG Similar
    base_protocol: Optional[dict] = None
    similar_protocols: Optional[List[dict]] = None

    # For Agent Squad
    task_type: Optional[str] = None  # analysis, research, general
    has_tools_used: Optional[bool] = None  # Boolean indicating if tools were used
    tools_used: Optional[List[str]] = None
    tokens_consumed: Optional[int] = None
    latency_ms: Optional[int] = None
    intent_classification: Optional[str] = None

    # For Supervisor
    workflow_id: Optional[str] = None
    workflow_status: Optional[str] = None
    tasks_count: Optional[int] = None
    agents_involved: Optional[List[str]] = None
    workflow_type: Optional[str] = None
    total_latency_ms: Optional[int] = None

    # For Hunter AI
    hunter_tool: Optional[str] = None  # sentiment_analysis, price_prediction, risk_signals, trading_signals, pattern_detection, portfolio_optimization
    token_symbol: Optional[str] = None  # Primary token (BTC, ETH, SOL, etc.)
    tokens: Optional[List[str]] = None  # Multiple tokens for portfolio optimization
    time_horizon: Optional[str] = None  # 24h, 7d, 30d
    sources: Optional[List[str]] = None  # twitter, reddit, discord, news (for sentiment)
    risk_tolerance: Optional[float] = None  # 0.0-1.0 (for portfolio optimization)

    # For ULTRA (DeFi Automation & MEV)
    ultra_tool: Optional[str] = None  # arbitrage_discovery, flash_loan_engine, mev_protection, auto_executor
    capital: Optional[float] = None  # Capital amount for arbitrage discovery
    arb_type: Optional[str] = None  # 2hop, 3hop, triangle, all
    amount: Optional[float] = None  # Flash loan amount
    protocol: Optional[str] = None  # Flash loan protocol (aave, balancer, uniswap)
    opportunity_id: Optional[str] = None  # Arbitrage opportunity ID for MEV execution
    action: Optional[str] = None  # Bot action (start, stop, pause, resume, status)


class ExecuteActionData(BaseModel):
    """Execute action data for executable intents (swap, deposit, withdraw, etc.)."""
    
    action_type: str = Field(..., description="Type of action: swap, deposit, withdraw, transfer, approve, bridge")
    chain: str = Field(default="base", description="Blockchain to execute on")
    from_token: Optional[str] = Field(default=None, description="Source token symbol or address")
    to_token: Optional[str] = Field(default=None, description="Destination token symbol (for swap)")
    amount: Optional[str] = Field(default=None, description="Amount to execute (human readable)")
    protocol: Optional[str] = Field(default=None, description="Protocol name (for deposit/withdraw)")
    vault_address: Optional[str] = Field(default=None, description="Vault address (for Morpho deposits)")
    recipient: Optional[str] = Field(default=None, description="Recipient address (for transfer)")
    slippage: Optional[float] = Field(default=1.0, description="Slippage tolerance in percent")
    to_chain: Optional[str] = Field(default=None, description="Destination chain (for cross-chain swap/bridge)")


class UnifiedChatResponse(BaseModel):
    """Unified response for all chat routing handlers with source attribution."""

    user_message: dict  # User message data
    agent_message: dict  # Agent response data with sources
    routing: RoutingMetadata  # Routing information
    enrichment: Optional[EnrichmentData] = None  # Handler-specific data
    sources: List[SourceInfoResponse] = Field(default_factory=list)  # NEW: Aggregated sources
    execute: Optional[ExecuteActionData] = Field(
        default=None,
        description="Execute action data for executable intents (swap, deposit, withdraw, etc.)"
    )


class ConversationListResponse(BaseModel):
    """List of conversations response."""
    
    conversations: List[ConversationResponse]
    total: int


class MessageListResponse(BaseModel):
    """List of messages response."""
    
    messages: List[MessageResponse]
    total: int


# NEW: GraphRAG and ML Integration Schemas

class ChatProtocolSearchRequest(BaseModel):
    """Request to search protocols from chat with GraphRAG."""
    
    conversation_id: UUID
    query: str = Field(..., min_length=1, max_length=500)
    user_preferences: Optional[dict] = None
    limit: Optional[int] = Field(5, ge=1, le=20)


class ProtocolSearchResult(BaseModel):
    """Protocol search result for chat."""
    
    protocol_id: str
    protocol_name: str
    similarity_score: float
    risk_score: float
    risk_level: str
    tvl: float
    apy: Optional[float]
    audit_count: int
    description: str
    category: str
    chain: str
    why_relevant: str


class ChatProtocolSearchResponse(BaseModel):
    """Response for protocol search from chat."""
    
    results: List[ProtocolSearchResult]
    search_context: str
    recommendations: List[str]


class ChatRiskAnalysisRequest(BaseModel):
    """Request to analyze protocol risk from chat."""
    
    conversation_id: UUID
    protocol_name: str = Field(..., min_length=1, max_length=200)
    operation_type: Optional[str] = Field(None, pattern="^(supply|borrow|swap|stake|bridge)$")
    amount_usd: Optional[float] = Field(None, gt=0)


class RiskFactor(BaseModel):
    """Risk factor for chat."""
    
    factor: str
    impact: float
    description: str
    is_critical: bool


class RiskAnalysis(BaseModel):
    """Risk analysis for chat."""
    
    protocol_id: str
    protocol_name: str
    risk_score: float
    risk_level: str
    confidence: float
    contributing_factors: List[RiskFactor]
    recommendations: List[str]
    should_warn: bool
    warning_message: Optional[str]


class AlternativeProtocol(BaseModel):
    """Alternative protocol suggestion."""
    
    protocol_id: str
    protocol_name: str
    similarity_score: float
    risk_score: float
    risk_level: str
    tvl: float
    apy: Optional[float]
    why_better: str


class ChatRiskAnalysisResponse(BaseModel):
    """Response for risk analysis from chat."""
    
    risk_analysis: RiskAnalysis
    alternatives: List[AlternativeProtocol]
    contextual_message: str


class ChatSimilarProtocolsRequest(BaseModel):
    """Request to find similar protocols from chat."""
    
    conversation_id: UUID
    protocol_name: str = Field(..., min_length=1, max_length=200)
    limit: Optional[int] = Field(5, ge=1, le=20)


class BaseProtocolInfo(BaseModel):
    """Base protocol information."""
    
    protocol_id: str
    protocol_name: str
    risk_score: float
    risk_level: str
    tvl: float
    category: str


class SimilarProtocolInfo(BaseModel):
    """Similar protocol information."""
    
    protocol_id: str
    protocol_name: str
    similarity_score: float
    risk_score: float
    risk_level: str
    tvl: float
    why_similar: str


class ChatSimilarProtocolsResponse(BaseModel):
    """Response for similar protocols from chat."""
    
    base_protocol: BaseProtocolInfo
    similar_protocols: List[SimilarProtocolInfo]


# ========================================
# Agent Squad Schemas
# ========================================

class AgentSquadMessageRequest(BaseModel):
    """Request to send message with Agent Squad routing."""
    
    content: str = Field(..., min_length=1, max_length=10000, description="User message")
    force_agent: Optional[str] = Field(None, description="Force specific agent (chat, hunter_ai, etc.)")


class AgentSquadMessageResponse(BaseModel):
    """Response from Agent Squad message."""
    
    user_message_id: UUID
    agent_message_id: UUID
    agent_type: str  # Which agent handled the message
    intent_classification: Optional[str]  # Classified intent
    intent_confidence: Optional[float]  # Intent confidence (0.0-1.0)
    content: str  # Agent response
    tools_used: List[str]  # Tools/APIs used
    latency_ms: int  # Response latency
    tokens_used: Optional[int]  # LLM tokens consumed


class SupervisorWorkflowRequest(BaseModel):
    """Request for supervisor-coordinated multi-agent workflow."""
    
    content: str = Field(..., min_length=1, max_length=10000, description="Complex task description")
    max_agents: int = Field(5, ge=1, le=10, description="Maximum agents to use")
    timeout_seconds: int = Field(120, ge=30, le=300, description="Workflow timeout")


class WorkflowTaskResponse(BaseModel):
    """Single task in workflow."""
    
    agent_type: str
    task_description: str
    status: str  # pending, in_progress, completed, failed
    result: Optional[str]  # Agent response (if completed)


class SupervisorWorkflowResponse(BaseModel):
    """Response from supervisor workflow."""
    
    workflow_id: UUID
    conversation_id: UUID
    status: str  # in_progress, completed, failed
    tasks: List[WorkflowTaskResponse]
    final_response: Optional[str]  # Aggregated response (if completed)
    total_latency_ms: int
    agents_used: List[str]


class AgentCapability(BaseModel):
    """Agent capability information."""
    
    agent_type: str
    name: str
    description: str
    model: str
    temperature: float
    enabled: bool
    is_enterprise: bool


class ListEnabledAgentsResponse(BaseModel):
    """Response with list of enabled agents."""
    
    agents: List[AgentCapability]
    total: int
    core_agents: int  # Number of core agents
    enterprise_agents: int  # Number of enterprise agents


# ========================================
# Intent Detection Schemas
# ========================================

class DetectIntentRequest(BaseModel):
    """Request to detect intent from user message."""
    
    message: str = Field(..., min_length=1, max_length=10000, description="User message to analyze")
    conversation_id: Optional[UUID] = Field(None, description="Optional conversation ID for context")
    include_suggestions: bool = Field(True, description="Whether to include agent suggestions")


class AlternativeIntent(BaseModel):
    """Alternative intent prediction."""
    
    intent_type: str
    confidence: float = Field(..., ge=0.0, le=1.0)


class IntentPredictionResponse(BaseModel):
    """Intent prediction response."""
    
    intent_type: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    confidence_level: str  # low, medium, high
    suggested_agent: Optional[str]
    extracted_entities: dict
    reasoning: Optional[str]
    alternative_intents: List[AlternativeIntent]
    is_high_confidence: bool
    is_ambiguous: bool


class AgentSuggestionResponse(BaseModel):
    """Agent suggestion response."""
    
    agent_name: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: Optional[str]
    agent_description: Optional[str]
    estimated_response_time_seconds: Optional[float]
    is_high_confidence: bool


class DetectIntentResponse(BaseModel):
    """Response for intent detection."""
    
    intent: IntentPredictionResponse
    suggested_agents: List[AgentSuggestionResponse]
    processing_time_ms: int


class AutocompleteRequest(BaseModel):
    """Request for autocomplete suggestions."""
    
    partial_message: str = Field(..., min_length=1, max_length=1000)
    limit: int = Field(10, ge=1, le=50)


class AutocompleteSuggestionResponse(BaseModel):
    """Autocomplete suggestion response."""
    
    completion_text: str
    display_text: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    suggestion_type: str  # protocol, token, action, etc.
    icon: Optional[str]
    metadata: dict


class AutocompleteResponse(BaseModel):
    """Response for autocomplete."""
    
    suggestions: List[AutocompleteSuggestionResponse]
    processing_time_ms: int


class SimilarConversationsRequest(BaseModel):
    """Request to find similar conversations."""
    
    message: str = Field(..., min_length=1, max_length=10000)
    limit: int = Field(5, ge=1, le=20)
    similarity_threshold: float = Field(0.7, ge=0.0, le=1.0)


class ConversationMatchResponse(BaseModel):
    """Similar conversation match response."""
    
    conversation_id: UUID
    title: Optional[str]
    similarity_score: float = Field(..., ge=0.0, le=1.0)
    snippet: str
    created_at: datetime
    message_count: int
    was_helpful: Optional[bool]


class SimilarConversationsResponse(BaseModel):
    """Response for similar conversations."""
    
    matches: List[ConversationMatchResponse]
    processing_time_ms: int
