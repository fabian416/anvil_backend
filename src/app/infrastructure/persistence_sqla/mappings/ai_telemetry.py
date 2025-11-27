"""
SQLAlchemy mapping for AI Telemetry tables metadata.
"""

from sqlalchemy import Integer, String, DateTime, Enum, ForeignKey, Numeric, Text, Boolean, BigInteger, UniqueConstraint
from sqlalchemy.orm import mapped_column
from sqlalchemy.dialects.postgresql import JSON, JSONB
import sqlalchemy as sa

from app.domain.enums.ai.llm_provider import LLMProvider
from app.domain.enums.ai.llm_status import LLMStatus
from app.domain.enums.ai.agent_execution_status import AgentExecutionStatus
from app.domain.enums.ai.agent_task_status import AgentTaskStatus
from app.domain.enums.ai.agent_tool_status import AgentToolStatus
from app.domain.enums.ai.rate_limit_event_type import RateLimitEventType
from app.domain.enums.ai.cost_alert_type import CostAlertType
from app.domain.enums.ai.feedback_type import FeedbackType
from app.domain.enums.ai.model_status import ModelStatus
from app.infrastructure.persistence_sqla.registry import mapping_registry

def map_ai_telemetry_tables() -> None:
    """Map AI Telemetry entities to database tables (idempotent)."""
    
    # --- Models ---
    if "models" not in mapping_registry.metadata.tables:
        @mapping_registry.mapped
        class ModelsTable:
            __tablename__ = "models"
            __table_args__ = (
                UniqueConstraint('provider', 'model_name', name='unique_provider_model'),
                {"extend_existing": True}
            )
            
            id = mapped_column(BigInteger, primary_key=True, autoincrement=True)
            provider = mapped_column(Enum(LLMProvider, values_callable=lambda x: [e.value for e in x]), nullable=False, index=True)
            model_name = mapped_column(String(100), nullable=False, index=True)
            label = mapped_column(String(255), nullable=False)
            is_default = mapped_column(Boolean, default=False, index=True)
            is_available = mapped_column(Boolean, default=True, index=True)
            
            cost_per_1k_input_tokens = mapped_column(Numeric(10, 8), nullable=False)
            cost_per_1k_output_tokens = mapped_column(Numeric(10, 8), nullable=False)
            max_tokens = mapped_column(Integer, nullable=True)
            
            status = mapped_column(Enum(ModelStatus, values_callable=lambda x: [e.value for e in x]), default=ModelStatus.ACTIVE, nullable=False, index=True)
            request_count = mapped_column(BigInteger, default=0)
            total_cost_usd = mapped_column(Numeric(12, 2), default=0)
            
            created_at = mapped_column(DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'))
            updated_at = mapped_column(DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), onupdate=sa.text('CURRENT_TIMESTAMP'))

    # --- LLM Conversations ---
    if "llm_conversations" not in mapping_registry.metadata.tables:
        @mapping_registry.mapped
        class LLMConversationsTable:
            __tablename__ = "llm_conversations"
            __table_args__ = {"extend_existing": True}
            
            id = mapped_column(BigInteger, primary_key=True, autoincrement=True)
            user_id = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
            session_id = mapped_column(String(100), nullable=False, index=True)
            model_id = mapped_column(BigInteger, ForeignKey("models.id", ondelete="SET NULL"), nullable=True, index=True)
            
            provider = mapped_column(Enum(LLMProvider, values_callable=lambda x: [e.value for e in x]), nullable=False, index=True)
            model_name = mapped_column(String(100), nullable=False)
            prompt_text = mapped_column(Text, nullable=False)
            response_text = mapped_column(Text, nullable=True)
            
            input_tokens = mapped_column(Integer, nullable=True)
            output_tokens = mapped_column(Integer, nullable=True)
            total_tokens = mapped_column(Integer, nullable=True)
            cost_usd = mapped_column(Numeric(10, 6), nullable=True)
            latency_ms = mapped_column(Integer, nullable=True)
            
            status = mapped_column(Enum(LLMStatus, values_callable=lambda x: [e.value for e in x]), default=LLMStatus.SUCCESS, index=True)
            error_message = mapped_column(Text, nullable=True)
            ip_address = mapped_column(String(45), nullable=True)
            user_agent = mapped_column(Text, nullable=True)
            
            created_at = mapped_column(DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), index=True)

    # --- Agent Executions ---
    if "agent_executions" not in mapping_registry.metadata.tables:
        @mapping_registry.mapped
        class AgentExecutionsTable:
            __tablename__ = "agent_executions"
            __table_args__ = {"extend_existing": True}
            
            id = mapped_column(BigInteger, primary_key=True, autoincrement=True)
            user_id = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
            conversation_id = mapped_column(BigInteger, ForeignKey("llm_conversations.id", ondelete="SET NULL"), nullable=True, index=True)
            
            agent_type = mapped_column(String(50), nullable=False, index=True)
            workflow_type = mapped_column(String(50), nullable=False, index=True)
            status = mapped_column(Enum(AgentExecutionStatus, values_callable=lambda x: [e.value for e in x]), default=AgentExecutionStatus.PENDING, index=True)
            
            input_params = mapped_column(JSON, nullable=True)
            output_result = mapped_column(JSON, nullable=True)
            
            total_tasks = mapped_column(Integer, default=0)
            completed_tasks = mapped_column(Integer, default=0)
            failed_tasks = mapped_column(Integer, default=0)
            total_cost_usd = mapped_column(Numeric(10, 6), default=0)
            execution_time_ms = mapped_column(Integer, nullable=True)
            error_message = mapped_column(Text, nullable=True)
            
            started_at = mapped_column(DateTime(timezone=True), nullable=True)
            completed_at = mapped_column(DateTime(timezone=True), nullable=True)
            created_at = mapped_column(DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), index=True)

    # --- Agent Tasks ---
    if "agent_tasks" not in mapping_registry.metadata.tables:
        @mapping_registry.mapped
        class AgentTasksTable:
            __tablename__ = "agent_tasks"
            __table_args__ = {"extend_existing": True}
            
            id = mapped_column(BigInteger, primary_key=True, autoincrement=True)
            execution_id = mapped_column(BigInteger, ForeignKey("agent_executions.id", ondelete="CASCADE"), nullable=False, index=True)
            
            task_name = mapped_column(String(100), nullable=False)
            task_type = mapped_column(String(50), nullable=False, index=True)
            status = mapped_column(Enum(AgentTaskStatus, values_callable=lambda x: [e.value for e in x]), default=AgentTaskStatus.PENDING, index=True)
            
            input_data = mapped_column(JSON, nullable=True)
            output_data = mapped_column(JSON, nullable=True)
            error_message = mapped_column(Text, nullable=True)
            
            execution_time_ms = mapped_column(Integer, nullable=True)
            retry_count = mapped_column(Integer, default=0)
            
            started_at = mapped_column(DateTime(timezone=True), nullable=True)
            completed_at = mapped_column(DateTime(timezone=True), nullable=True)
            created_at = mapped_column(DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), index=True)

    # --- Agent Tools Usage ---
    if "agent_tools_usage" not in mapping_registry.metadata.tables:
        @mapping_registry.mapped
        class AgentToolsUsageTable:
            __tablename__ = "agent_tools_usage"
            __table_args__ = {"extend_existing": True}
            
            id = mapped_column(BigInteger, primary_key=True, autoincrement=True)
            execution_id = mapped_column(BigInteger, ForeignKey("agent_executions.id", ondelete="CASCADE"), nullable=False, index=True)
            task_id = mapped_column(BigInteger, ForeignKey("agent_tasks.id", ondelete="SET NULL"), nullable=True, index=True)
            
            tool_name = mapped_column(String(100), nullable=False, index=True)
            input_params = mapped_column(JSON, nullable=True)
            output_result = mapped_column(JSON, nullable=True)
            
            status = mapped_column(Enum(AgentToolStatus, values_callable=lambda x: [e.value for e in x]), default=AgentToolStatus.SUCCESS, index=True)
            execution_time_ms = mapped_column(Integer, nullable=True)
            error_message = mapped_column(Text, nullable=True)
            
            created_at = mapped_column(DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), index=True)

    # --- LLM Rate Limit Events ---
    if "llm_rate_limit_events" not in mapping_registry.metadata.tables:
        @mapping_registry.mapped
        class LLMRateLimitEventsTable:
            __tablename__ = "llm_rate_limit_events"
            __table_args__ = {"extend_existing": True}
            
            id = mapped_column(BigInteger, primary_key=True, autoincrement=True)
            provider = mapped_column(Enum(LLMProvider, values_callable=lambda x: [e.value for e in x]), nullable=False, index=True)
            model_name = mapped_column(String(100), nullable=False, index=True)
            event_type = mapped_column(Enum(RateLimitEventType, values_callable=lambda x: [e.value for e in x]), nullable=False, index=True)
            
            user_id = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
            error_code = mapped_column(String(50), nullable=True)
            error_message = mapped_column(Text, nullable=True)
            retry_after_seconds = mapped_column(Integer, nullable=True)
            
            fallback_used = mapped_column(Boolean, default=False)
            fallback_provider = mapped_column(String(20), nullable=True)
            
            created_at = mapped_column(DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), index=True)

    # --- LLM Cost Alerts ---
    if "llm_cost_alerts" not in mapping_registry.metadata.tables:
        @mapping_registry.mapped
        class LLMCostAlertsTable:
            __tablename__ = "llm_cost_alerts"
            __table_args__ = {"extend_existing": True}
            
            id = mapped_column(BigInteger, primary_key=True, autoincrement=True)
            alert_type = mapped_column(Enum(CostAlertType, values_callable=lambda x: [e.value for e in x]), nullable=False, index=True)
            threshold_usd = mapped_column(Numeric(10, 2), nullable=False)
            actual_cost_usd = mapped_column(Numeric(10, 2), nullable=False)
            
            time_period_start = mapped_column(DateTime(timezone=True), nullable=False, index=True)
            time_period_end = mapped_column(DateTime(timezone=True), nullable=False, index=True)
            
            user_id = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
            provider = mapped_column(String(20), nullable=True)
            
            alert_sent = mapped_column(Boolean, default=False, index=True)
            alert_sent_at = mapped_column(DateTime(timezone=True), nullable=True)
            
            created_at = mapped_column(DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), index=True)

    # --- Vertex API Metrics ---
    if "vertex_api_metrics" not in mapping_registry.metadata.tables:
        @mapping_registry.mapped
        class VertexApiMetricsTable:
            __tablename__ = "vertex_api_metrics"
            __table_args__ = (
                UniqueConstraint('model_id', 'region', 'time_window_start', name='unique_vertex_metric'),
                {"extend_existing": True}
            )
            
            id = mapped_column(BigInteger, primary_key=True, autoincrement=True)
            model_id = mapped_column(BigInteger, ForeignKey("models.id", ondelete="CASCADE"), nullable=True, index=True)
            region = mapped_column(String(50), nullable=False, index=True)
            
            requests_count = mapped_column(Integer, default=0)
            tokens_consumed = mapped_column(BigInteger, default=0)
            cost_usd = mapped_column(Numeric(10, 6), default=0)
            
            quota_exceeded_count = mapped_column(Integer, default=0)
            rate_limit_count = mapped_column(Integer, default=0)
            
            avg_latency_ms = mapped_column(Integer, nullable=True)
            p95_latency_ms = mapped_column(Integer, nullable=True)
            p99_latency_ms = mapped_column(Integer, nullable=True)
            
            error_count = mapped_column(Integer, default=0)
            success_rate = mapped_column(Numeric(5, 2), nullable=True)
            failover_to_bedrock_count = mapped_column(Integer, default=0)
            
            time_window_start = mapped_column(DateTime(timezone=True), nullable=False, index=True)
            time_window_end = mapped_column(DateTime(timezone=True), nullable=False)
            created_at = mapped_column(DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'))

    # --- Bedrock API Metrics ---
    if "bedrock_api_metrics" not in mapping_registry.metadata.tables:
        @mapping_registry.mapped
        class BedrockApiMetricsTable:
            __tablename__ = "bedrock_api_metrics"
            __table_args__ = (
                UniqueConstraint('model_id', 'region', 'time_window_start', name='unique_bedrock_metric'),
                {"extend_existing": True}
            )
            
            id = mapped_column(BigInteger, primary_key=True, autoincrement=True)
            model_id = mapped_column(BigInteger, ForeignKey("models.id", ondelete="CASCADE"), nullable=True, index=True)
            region = mapped_column(String(50), nullable=False, index=True)
            
            requests_count = mapped_column(Integer, default=0)
            tokens_consumed = mapped_column(BigInteger, default=0)
            cost_usd = mapped_column(Numeric(10, 6), default=0)
            
            throttle_count = mapped_column(Integer, default=0)
            model_not_ready_count = mapped_column(Integer, default=0)
            
            avg_latency_ms = mapped_column(Integer, nullable=True)
            p95_latency_ms = mapped_column(Integer, nullable=True)
            p99_latency_ms = mapped_column(Integer, nullable=True)
            
            error_count = mapped_column(Integer, default=0)
            success_rate = mapped_column(Numeric(5, 2), nullable=True)
            failover_from_vertex_count = mapped_column(Integer, default=0)
            
            time_window_start = mapped_column(DateTime(timezone=True), nullable=False, index=True)
            time_window_end = mapped_column(DateTime(timezone=True), nullable=False)
            created_at = mapped_column(DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'))

    # --- Conversation Feedback ---
    if "conversation_feedback" not in mapping_registry.metadata.tables:
        @mapping_registry.mapped
        class ConversationFeedbackTable:
            __tablename__ = "conversation_feedback"
            __table_args__ = {"extend_existing": True}
            
            id = mapped_column(BigInteger, primary_key=True, autoincrement=True)
            conversation_id = mapped_column(BigInteger, ForeignKey("llm_conversations.id", ondelete="CASCADE"), nullable=False, index=True)
            user_id = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
            
            rating = mapped_column(Integer, nullable=True, index=True)
            feedback_type = mapped_column(Enum(FeedbackType, values_callable=lambda x: [e.value for e in x]), nullable=False, index=True)
            feedback_text = mapped_column(Text, nullable=True)
            
            created_at = mapped_column(DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), index=True)
