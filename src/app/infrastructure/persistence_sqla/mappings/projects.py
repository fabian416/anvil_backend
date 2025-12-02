"""SQLAlchemy mappings for projects."""
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Column, Integer, Numeric, String, Table, Text, TIMESTAMP, Date
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID as PGUUID
from sqlalchemy.orm import registry

mapper_registry = registry()

# Projects table
projects = Table(
    "projects",
    mapper_registry.metadata,
    Column("id", PGUUID(as_uuid=True), primary_key=True, default=uuid4),
    Column("slug", String(50), nullable=False, unique=True),
    Column("name", String(100), nullable=False),
    Column("description", Text),
    
    # Branding
    Column("icon", String(50)),
    Column("color", String(7)),
    Column("banner_url", Text),
    
    # Status
    Column("status", String(20), nullable=False, default="draft"),
    Column("visibility", String(20), nullable=False, default="public"),
    
    # System Prompt
    Column("system_prompt", Text, nullable=False),
    Column("welcome_message", Text),
    
    # DeFi Configuration
    Column("enabled_protocols", ARRAY(Text), default=[]),
    Column("enabled_chains", ARRAY(Text), default=[]),
    Column("enabled_tools", ARRAY(Text), default=[]),
    
    # Risk Configuration
    Column("risk_config", JSONB, default={}),
    
    # User limits
    Column("max_users", Integer),
    
    # Display order
    Column("display_order", Integer, default=0),
    Column("is_featured", Boolean, default=False),
    
    # Audit
    Column("created_by", PGUUID(as_uuid=True), nullable=False),
    Column("created_at", TIMESTAMP(timezone=True), default=datetime.utcnow),
    Column("updated_at", TIMESTAMP(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow),
)

# Project knowledge bases
project_knowledge_bases = Table(
    "project_knowledge_bases",
    mapper_registry.metadata,
    Column("id", PGUUID(as_uuid=True), primary_key=True, default=uuid4),
    Column("project_id", PGUUID(as_uuid=True), nullable=False),
    
    # Configuration
    Column("name", String(100), nullable=False),
    Column("description", Text),
    
    # Embedding settings
    Column("embedding_model", String(100), default="text-embedding-3-small"),
    Column("chunk_size", Integer, default=500),
    Column("chunk_overlap", Integer, default=50),
    
    # Statistics
    Column("total_documents", Integer, default=0),
    Column("total_chunks", Integer, default=0),
    
    # Status
    Column("status", String(20), default="active"),
    Column("last_indexed_at", TIMESTAMP(timezone=True)),
    
    Column("created_at", TIMESTAMP(timezone=True), default=datetime.utcnow),
    Column("updated_at", TIMESTAMP(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow),
)

# Project knowledge documents
project_knowledge_documents = Table(
    "project_knowledge_documents",
    mapper_registry.metadata,
    Column("id", PGUUID(as_uuid=True), primary_key=True, default=uuid4),
    Column("knowledge_base_id", PGUUID(as_uuid=True), nullable=False),
    
    # Content
    Column("title", String(255), nullable=False),
    Column("content", Text, nullable=False),
    Column("doc_type", String(50), nullable=False),
    
    # Source
    Column("source_url", Text),
    Column("source_type", String(50), default="manual"),
    
    # Metadata
    Column("tags", ARRAY(Text), default=[]),
    Column("priority", Integer, default=1),
    
    # Processing status
    Column("is_processed", Boolean, default=False),
    Column("chunk_count", Integer, default=0),
    Column("processing_error", Text),
    
    Column("created_at", TIMESTAMP(timezone=True), default=datetime.utcnow),
    Column("updated_at", TIMESTAMP(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow),
)

# Project knowledge chunks
project_knowledge_chunks = Table(
    "project_knowledge_chunks",
    mapper_registry.metadata,
    Column("id", PGUUID(as_uuid=True), primary_key=True, default=uuid4),
    Column("document_id", PGUUID(as_uuid=True), nullable=False),
    Column("knowledge_base_id", PGUUID(as_uuid=True), nullable=False),
    
    # Content
    Column("chunk_text", Text, nullable=False),
    Column("chunk_index", Integer, nullable=False),
    
    # Embedding (will be vector in DB)
    Column("embedding", ARRAY(Numeric)),
    
    # Metadata
    Column("metadata", JSONB, default={}),
    
    Column("created_at", TIMESTAMP(timezone=True), default=datetime.utcnow),
)

# Project tool configs
project_tool_configs = Table(
    "project_tool_configs",
    mapper_registry.metadata,
    Column("id", PGUUID(as_uuid=True), primary_key=True, default=uuid4),
    Column("project_id", PGUUID(as_uuid=True), nullable=False),
    Column("tool_id", String(50), nullable=False),
    
    # Enablement
    Column("is_enabled", Boolean, default=True),
    
    # Restrictions
    Column("max_calls_per_session", Integer),
    Column("max_amount_per_call", Numeric(20, 8)),
    Column("requires_confirmation", Boolean, default=True),
    
    # Custom parameters
    Column("default_params", JSONB, default={}),
    Column("locked_params", JSONB, default={}),
    
    Column("created_at", TIMESTAMP(timezone=True), default=datetime.utcnow),
    Column("updated_at", TIMESTAMP(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow),
)

# User project assignments
user_project_assignments = Table(
    "user_project_assignments",
    mapper_registry.metadata,
    Column("id", PGUUID(as_uuid=True), primary_key=True, default=uuid4),
    Column("user_id", PGUUID(as_uuid=True), nullable=False),
    Column("project_id", PGUUID(as_uuid=True), nullable=False),
    
    # Assignment type
    Column("assignment_type", String(20), nullable=False),
    Column("assigned_by", PGUUID(as_uuid=True)),
    Column("assignment_reason", Text),
    
    # Status
    Column("is_active", Boolean, default=True),
    
    # Timestamps
    Column("assigned_at", TIMESTAMP(timezone=True), default=datetime.utcnow),
    Column("last_active_at", TIMESTAMP(timezone=True)),
    Column("removed_at", TIMESTAMP(timezone=True)),
)

# User active projects
user_active_projects = Table(
    "user_active_projects",
    mapper_registry.metadata,
    Column("user_id", PGUUID(as_uuid=True), primary_key=True),
    Column("project_id", PGUUID(as_uuid=True), nullable=False),
    
    Column("activated_at", TIMESTAMP(timezone=True), default=datetime.utcnow),
    Column("session_count", Integer, default=0),
    
    Column("updated_at", TIMESTAMP(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow),
)

# Project auto assign rules
project_auto_assign_rules = Table(
    "project_auto_assign_rules",
    mapper_registry.metadata,
    Column("id", PGUUID(as_uuid=True), primary_key=True, default=uuid4),
    Column("project_id", PGUUID(as_uuid=True), nullable=False),
    
    # Rule definition
    Column("rule_name", String(100), nullable=False),
    Column("condition_type", String(50), nullable=False),
    Column("condition_params", JSONB, nullable=False),
    
    # Behavior
    Column("priority", Integer, default=1),
    Column("auto_switch", Boolean, default=False),
    
    # Status
    Column("is_active", Boolean, default=True),
    
    Column("created_at", TIMESTAMP(timezone=True), default=datetime.utcnow),
    Column("updated_at", TIMESTAMP(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow),
)

# Project invitations
project_invitations = Table(
    "project_invitations",
    mapper_registry.metadata,
    Column("id", PGUUID(as_uuid=True), primary_key=True, default=uuid4),
    Column("project_id", PGUUID(as_uuid=True), nullable=False),
    
    # Invitation details
    Column("email", String(255)),
    Column("invitation_code", String(50), unique=True),
    
    # Status
    Column("status", String(20), default="pending"),
    
    # Timestamps
    Column("invited_by", PGUUID(as_uuid=True), nullable=False),
    Column("invited_at", TIMESTAMP(timezone=True), default=datetime.utcnow),
    Column("expires_at", TIMESTAMP(timezone=True)),
    Column("accepted_at", TIMESTAMP(timezone=True)),
    Column("accepted_by", PGUUID(as_uuid=True)),
)

# Project chat sessions
project_chat_sessions = Table(
    "project_chat_sessions",
    mapper_registry.metadata,
    Column("id", PGUUID(as_uuid=True), primary_key=True, default=uuid4),
    Column("session_id", PGUUID(as_uuid=True), nullable=False, unique=True),
    Column("project_id", PGUUID(as_uuid=True), nullable=False),
    Column("user_id", PGUUID(as_uuid=True), nullable=False),
    
    # Context used
    Column("system_prompt_version", Integer, default=1),
    Column("knowledge_chunks_used", Integer, default=0),
    Column("tools_used", ARRAY(Text), default=[]),
    
    # Metrics
    Column("messages_count", Integer, default=0),
    Column("tokens_used", Integer, default=0),
    
    Column("created_at", TIMESTAMP(timezone=True), default=datetime.utcnow),
    Column("ended_at", TIMESTAMP(timezone=True)),
)

# Project analytics daily
project_analytics_daily = Table(
    "project_analytics_daily",
    mapper_registry.metadata,
    Column("id", PGUUID(as_uuid=True), primary_key=True, default=uuid4),
    Column("project_id", PGUUID(as_uuid=True), nullable=False),
    Column("date", Date, nullable=False),
    
    # User metrics
    Column("total_users", Integer, default=0),
    Column("active_users", Integer, default=0),
    Column("new_users", Integer, default=0),
    Column("returning_users", Integer, default=0),
    
    # Session metrics
    Column("total_sessions", Integer, default=0),
    Column("total_messages", Integer, default=0),
    Column("avg_session_duration_seconds", Integer),
    Column("avg_messages_per_session", Numeric(6, 2)),
    
    # Engagement
    Column("satisfaction_score_avg", Numeric(3, 2)),
    Column("helpful_rate", Numeric(5, 4)),
    
    # Knowledge usage
    Column("knowledge_queries", Integer, default=0),
    Column("knowledge_hit_rate", Numeric(5, 4)),
    Column("top_queries", JSONB, default=[]),
    
    # Transactions
    Column("total_transactions", Integer, default=0),
    Column("total_volume_usd", Numeric(20, 2), default=0),
    Column("transaction_success_rate", Numeric(5, 4)),
    
    # Tools
    Column("tool_usage", JSONB, default={}),
    
    Column("created_at", TIMESTAMP(timezone=True), default=datetime.utcnow),
)
