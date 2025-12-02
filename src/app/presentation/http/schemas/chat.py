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
