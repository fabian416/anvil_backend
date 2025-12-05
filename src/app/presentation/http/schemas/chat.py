"""
Chat-related request/response schemas.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field


# Request schemas
class CreateConversationRequest(BaseModel):
    """Request to create a new conversation."""
    
    title: Optional[str] = Field(None, max_length=200)


class SendMessageRequest(BaseModel):
    """Request to send a message."""
    
    content: str = Field(..., min_length=1, max_length=10000)


# Response schemas
class ConversationResponse(BaseModel):
    """Conversation response."""
    
    id: UUID
    user_id: int
    title: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    """Message response."""
    
    id: UUID
    conversation_id: UUID
    role: str
    content: str
    agent_type: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class SendMessageResponse(BaseModel):
    """Response for send message containing both user and agent messages."""
    
    user_message: MessageResponse
    agent_message: MessageResponse


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
