"""
Anvil Platform - SQLAlchemy Models
Section 6: AI and Agent Models

These models track LLM conversations (Gemini/Claude) and agent executions
for research, analysis, and automated workflows.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column,
    Integer,
    String,
    Numeric,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Text,
    Enum as SQLEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from decimal import Decimal
import enum

from .base_and_users import Base


# ============================================================================
# Enums
# ============================================================================

class LLMProvider(str, enum.Enum):
    """LLM provider"""
    VERTEX = "vertex"     # Google Vertex AI
    BEDROCK = "bedrock"   # AWS Bedrock


class ConversationStatus(str, enum.Enum):
    """Conversation status"""
    SUCCESS = "success"
    ERROR = "error"
    RATE_LIMITED = "rate_limited"


class AgentType(str, enum.Enum):
    """Agent type"""
    RESEARCH = "research"
    ANALYSIS = "analysis"
    TRADING = "trading"
    PORTFOLIO = "portfolio"


class AgentStatus(str, enum.Enum):
    """Agent execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# ============================================================================
# LLM Models
# ============================================================================

class LLMConversation(Base):
    """
    LLM conversation logs
    
    Tracks all AI chat interactions including prompts, responses,
    token usage, and costs.
    """
    
    __tablename__ = "llm_conversations"
    
    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign Key
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Session Tracking
    session_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="Session UUID for conversation continuity"
    )
    
    # Provider Information
    provider: Mapped[str] = mapped_column(
        SQLEnum(LLMProvider),
        nullable=False,
        index=True,
        comment="LLM provider (vertex, bedrock)"
    )
    model_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Model name (e.g., 'gemini-1.5-flash', 'claude-sonnet-4')"
    )
    
    # Conversation Content
    prompt_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="User's input message"
    )
    response_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="AI's response"
    )
    
    # Token Usage
    input_tokens: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of input tokens"
    )
    output_tokens: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of output tokens"
    )
    total_tokens: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Total tokens used"
    )
    
    # Cost Tracking
    cost_usd: Mapped[Decimal] = mapped_column(
        Numeric(10, 6),
        nullable=False,
        default=Decimal("0"),
        comment="Cost in USD"
    )
    
    # Performance Metrics
    latency_ms: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Response latency in milliseconds"
    )
    
    # Status
    status: Mapped[str] = mapped_column(
        SQLEnum(ConversationStatus),
        nullable=False,
        default=ConversationStatus.SUCCESS,
        index=True
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    
    # Context
    context_metadata: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="JSON: Additional context (portfolio data, market data, etc.)"
    )
    
    # Recommendations
    recommendations_json: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="JSON: AI-generated recommendations"
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        index=True
    )
    
    # Relationships
    user = relationship("User", back_populates="llm_conversations")
    agent_executions = relationship("AgentExecution", back_populates="conversation", lazy="select")
    
    # Indexes
    __table_args__ = (
        Index("idx_llm_user_created", "user_id", "created_at"),
        Index("idx_llm_session", "session_id"),
        Index("idx_llm_provider_model", "provider", "model_name"),
        Index("idx_llm_status", "status"),
        Index("idx_llm_created_date", "created_at"),
    )
    
    def __repr__(self) -> str:
        return f"<LLMConversation(id={self.id}, user_id={self.user_id}, model='{self.model_name}', tokens={self.total_tokens})>"
    
    @property
    def is_success(self) -> bool:
        """Check if conversation succeeded"""
        return self.status == ConversationStatus.SUCCESS
    
    @property
    def cost_per_token(self) -> Decimal:
        """Calculate cost per token"""
        if self.total_tokens == 0:
            return Decimal("0")
        return self.cost_usd / Decimal(str(self.total_tokens))


# ============================================================================
# Agent Models
# ============================================================================

class AgentExecution(Base):
    """
    AI agent execution logs
    
    Tracks automated agent workflows such as research, analysis,
    trading suggestions, and portfolio optimization.
    """
    
    __tablename__ = "agent_executions"
    
    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign Keys
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    conversation_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("llm_conversations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Related LLM conversation if triggered by chat"
    )
    
    # Agent Configuration
    agent_type: Mapped[str] = mapped_column(
        SQLEnum(AgentType),
        nullable=False,
        index=True,
        comment="Type of agent executed"
    )
    workflow_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Specific workflow (e.g., 'portfolio_analysis', 'market_research')"
    )
    
    # Execution Details
    status: Mapped[str] = mapped_column(
        SQLEnum(AgentStatus),
        nullable=False,
        default=AgentStatus.PENDING,
        index=True
    )
    
    # Input/Output
    input_params: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="JSON: Input parameters for agent"
    )
    output_result: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="JSON: Agent execution results"
    )
    
    # Performance
    execution_time_ms: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Total execution time in milliseconds"
    )
    llm_calls_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of LLM API calls made"
    )
    total_tokens_used: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Total tokens across all LLM calls"
    )
    total_cost_usd: Mapped[Decimal] = mapped_column(
        Numeric(10, 6),
        nullable=False,
        default=Decimal("0"),
        comment="Total cost of execution"
    )
    
    # Error Handling
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    retry_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of retry attempts"
    )
    
    # Metadata
    metadata_json: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="JSON: Additional execution metadata"
    )
    
    # Timestamps
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )
    
    # Relationships
    user = relationship("User", back_populates="agent_executions")
    conversation = relationship("LLMConversation", back_populates="agent_executions")
    
    # Indexes
    __table_args__ = (
        Index("idx_agent_user_status", "user_id", "status"),
        Index("idx_agent_type", "agent_type"),
        Index("idx_agent_workflow", "workflow_type"),
        Index("idx_agent_created", "created_at"),
        Index("idx_agent_completed", "completed_at"),
    )
    
    def __repr__(self) -> str:
        return f"<AgentExecution(id={self.id}, type='{self.agent_type}', workflow='{self.workflow_type}', status='{self.status}')>"
    
    @property
    def is_running(self) -> bool:
        """Check if agent is currently running"""
        return self.status == AgentStatus.RUNNING
    
    @property
    def is_completed(self) -> bool:
        """Check if agent completed successfully"""
        return self.status == AgentStatus.COMPLETED
    
    @property
    def is_failed(self) -> bool:
        """Check if agent failed"""
        return self.status == AgentStatus.FAILED
    
    @property
    def execution_duration_seconds(self) -> Optional[int]:
        """Calculate execution duration in seconds"""
        if not self.started_at or not self.completed_at:
            return None
        delta = self.completed_at - self.started_at
        return int(delta.total_seconds())


class AIModel(Base):
    """
    AI model configurations
    
    Tracks available AI models, their costs, quotas, and usage statistics.
    """
    
    __tablename__ = "ai_models"
    
    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Model Information
    provider: Mapped[str] = mapped_column(
        SQLEnum(LLMProvider),
        nullable=False,
        index=True
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
        comment="Model identifier (e.g., 'gemini-1.5-flash')"
    )
    display_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Human-readable name"
    )
    
    # Pricing
    cost_per_1k_input: Mapped[Decimal] = mapped_column(
        Numeric(10, 8),
        nullable=False,
        default=Decimal("0"),
        comment="Cost per 1000 input tokens (USD)"
    )
    cost_per_1k_output: Mapped[Decimal] = mapped_column(
        Numeric(10, 8),
        nullable=False,
        default=Decimal("0"),
        comment="Cost per 1000 output tokens (USD)"
    )
    
    # Capabilities
    max_tokens: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=8192,
        comment="Maximum context window"
    )
    supports_streaming: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False
    )
    supports_function_calling: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False
    )
    
    # Status
    is_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True
    )
    is_default: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Is this the default model?"
    )
    
    # Quota Management
    quota_limit_daily: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Daily request quota (null = unlimited)"
    )
    quota_used_today: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Requests used today"
    )
    quota_reset_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="When daily quota resets"
    )
    
    # Usage Statistics
    total_requests: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Total requests all-time"
    )
    total_tokens_used: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Total tokens all-time"
    )
    total_cost_usd: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0"),
        comment="Total cost all-time"
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_ai_model_provider", "provider", "is_enabled"),
        Index("idx_ai_model_default", "is_default"),
    )
    
    def __repr__(self) -> str:
        return f"<AIModel(id={self.id}, name='{self.name}', provider='{self.provider}')>"
    
    @property
    def quota_remaining(self) -> Optional[int]:
        """Calculate remaining daily quota"""
        if self.quota_limit_daily is None:
            return None
        return max(0, self.quota_limit_daily - self.quota_used_today)
    
    @property
    def quota_percent_used(self) -> Optional[Decimal]:
        """Calculate percentage of quota used"""
        if self.quota_limit_daily is None or self.quota_limit_daily == 0:
            return None
        return (Decimal(str(self.quota_used_today)) / Decimal(str(self.quota_limit_daily))) * Decimal("100")


# ============================================================================
# Usage Example
# ============================================================================

if __name__ == "__main__":
    from sqlalchemy import create_engine
    from .base_and_users import Base
    
    DATABASE_URL = "mysql+pymysql://user:password@localhost:3306/anvil"
    engine = create_engine(DATABASE_URL)
    
    # Create all tables
    Base.metadata.create_all(engine)
    
    print("✅ AI and Agent tables created successfully!")
    print("\nTables created:")
    print("- llm_conversations")
    print("- agent_executions")
    print("- ai_models")
