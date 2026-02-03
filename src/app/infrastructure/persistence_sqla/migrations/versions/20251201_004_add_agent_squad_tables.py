"""add agent squad tables

Revision ID: 20251201_004
Revises: 20251201_003
Create Date: 2025-12-01 15:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20251201_004"
down_revision: Union[str, None] = "20251201_003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Create Agent Squad tables for multi-agent orchestration system.

    Tables:
    - agent_sessions: Conversation-level agent state tracking
    - agent_telemetry: Performance metrics per agent
    - compliance_screening_logs: AML/KYC screening results (enterprise)
    - multisig_proposals: Multi-sig treasury proposals (enterprise)
    - crisis_events: Crisis detection and response logs (enterprise)
    """

    # ========================================
    # 1. Agent Sessions Table
    # ========================================
    op.create_table(
        "agent_sessions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "conversation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("conversations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "agent_type",
            sa.String(50),
            nullable=False,
            comment="Agent type: chat, hunter_ai, research, execution, etc.",
        ),
        sa.Column(
            "state",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
            comment="Agent-specific state (e.g., compliance checks, portfolio data)",
        ),
        sa.Column(
            "created_at", sa.TIMESTAMP, nullable=False, server_default=sa.text("NOW()")
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP,
            nullable=False,
            server_default=sa.text("NOW()"),
            onupdate=sa.text("NOW()"),
        ),
        comment="Agent sessions: per-conversation agent state tracking for multi-agent orchestration",
    )

    # Indexes for agent_sessions
    op.create_index(
        "idx_agent_sessions_conversation", "agent_sessions", ["conversation_id"]
    )
    op.create_index("idx_agent_sessions_agent_type", "agent_sessions", ["agent_type"])
    op.create_index("idx_agent_sessions_created_at", "agent_sessions", ["created_at"])

    # ========================================
    # 2. Agent Telemetry Table
    # ========================================
    op.create_table(
        "agent_telemetry",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "agent_type",
            sa.String(50),
            nullable=False,
            comment="Agent type (18 total agents)",
        ),
        sa.Column(
            "conversation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("conversations.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "message_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("messages.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "intent_classification",
            sa.String(100),
            nullable=True,
            comment='Classified user intent (e.g., "swap_tokens", "analyze_risk")',
        ),
        sa.Column(
            "intent_confidence",
            sa.Float,
            nullable=True,
            comment="Intent classification confidence (0.0-1.0)",
        ),
        sa.Column(
            "latency_ms",
            sa.Integer,
            nullable=False,
            comment="Agent response latency in milliseconds",
        ),
        sa.Column(
            "tokens_used",
            sa.Integer,
            nullable=True,
            comment="LLM tokens used for this agent call",
        ),
        sa.Column(
            "tools_used",
            postgresql.JSONB,
            nullable=True,
            server_default=sa.text("'[]'::jsonb"),
            comment="List of tools/APIs used by agent",
        ),
        sa.Column(
            "success",
            sa.Boolean,
            nullable=False,
            comment="Whether agent call succeeded",
        ),
        sa.Column(
            "error_message",
            sa.Text,
            nullable=True,
            comment="Error message if success=false",
        ),
        sa.Column(
            "created_at", sa.TIMESTAMP, nullable=False, server_default=sa.text("NOW()")
        ),
        comment="Agent telemetry: performance metrics for all 18 agents",
    )

    # Indexes for agent_telemetry
    op.create_index("idx_agent_telemetry_agent_type", "agent_telemetry", ["agent_type"])
    op.create_index("idx_agent_telemetry_created_at", "agent_telemetry", ["created_at"])
    op.create_index("idx_agent_telemetry_success", "agent_telemetry", ["success"])
    op.create_index(
        "idx_agent_telemetry_conversation", "agent_telemetry", ["conversation_id"]
    )

    # ========================================
    # 3. Compliance Screening Logs (Enterprise)
    # ========================================
    op.create_table(
        "compliance_screening_logs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "wallet_address",
            sa.String(42),
            nullable=False,
            comment="Ethereum wallet address (0x...)",
        ),
        sa.Column(
            "risk_score",
            sa.Integer,
            nullable=False,
            comment="Risk score (0-100, higher = riskier)",
        ),
        sa.Column(
            "ofac_status",
            sa.String(20),
            nullable=False,
            comment="OFAC sanction status: clear, sanctioned",
        ),
        sa.Column(
            "pep_status",
            sa.String(20),
            nullable=False,
            comment="Politically Exposed Person status: clear, detected",
        ),
        sa.Column(
            "mixer_exposure_pct",
            sa.Float,
            nullable=True,
            comment="Percentage of funds from mixers (e.g., Tornado Cash)",
        ),
        sa.Column(
            "high_risk_sources_pct",
            sa.Float,
            nullable=True,
            comment="Percentage from high-risk sources (gambling, unverified exchanges)",
        ),
        sa.Column(
            "screening_result",
            sa.String(20),
            nullable=False,
            comment="Screening decision: approved, blocked, review",
        ),
        sa.Column(
            "screening_data",
            postgresql.JSONB,
            nullable=False,
            comment="Full Chainalysis/TRM Labs API response",
        ),
        sa.Column(
            "created_at", sa.TIMESTAMP, nullable=False, server_default=sa.text("NOW()")
        ),
        comment="Compliance screening logs: AML/KYC screening results for enterprise customers",
    )

    # Indexes for compliance_screening_logs
    op.create_index(
        "idx_compliance_logs_user", "compliance_screening_logs", ["user_id"]
    )
    op.create_index(
        "idx_compliance_logs_wallet", "compliance_screening_logs", ["wallet_address"]
    )
    op.create_index(
        "idx_compliance_logs_created_at", "compliance_screening_logs", ["created_at"]
    )
    op.create_index(
        "idx_compliance_logs_risk_score", "compliance_screening_logs", ["risk_score"]
    )
    op.create_index(
        "idx_compliance_logs_screening_result",
        "compliance_screening_logs",
        ["screening_result"],
    )

    # ========================================
    # 4. Multi-Sig Proposals (Enterprise)
    # ========================================
    op.create_table(
        "multisig_proposals",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "safe_address", sa.String(42), nullable=False, comment="Gnosis Safe address"
        ),
        sa.Column(
            "transaction_hash",
            sa.String(66),
            nullable=True,
            comment="Transaction hash (null until executed)",
        ),
        sa.Column("nonce", sa.Integer, nullable=False, comment="Gnosis Safe nonce"),
        sa.Column(
            "amount_usd",
            sa.Numeric(18, 2),
            nullable=False,
            comment="Transaction amount in USD",
        ),
        sa.Column(
            "destination_address",
            sa.String(42),
            nullable=False,
            comment="Destination wallet address",
        ),
        sa.Column(
            "purpose",
            sa.Text,
            nullable=False,
            comment="Transaction purpose/description",
        ),
        sa.Column(
            "budget_code",
            sa.String(50),
            nullable=True,
            comment="Budget code (e.g., ENG-2025-Q4-001)",
        ),
        sa.Column(
            "policy_check_result",
            sa.String(20),
            nullable=False,
            comment="Policy check: passed, failed",
        ),
        sa.Column(
            "approval_policy",
            sa.String(20),
            nullable=False,
            comment="Required approvals: 2-of-3, 3-of-5, etc.",
        ),
        sa.Column(
            "approvals",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
            comment="List of approvals: [{signer, timestamp, ip, comment}]",
        ),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            comment="Proposal status: pending, approved, executed, cancelled",
        ),
        sa.Column(
            "executed_at", sa.TIMESTAMP, nullable=True, comment="Execution timestamp"
        ),
        sa.Column(
            "created_at", sa.TIMESTAMP, nullable=False, server_default=sa.text("NOW()")
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP,
            nullable=False,
            server_default=sa.text("NOW()"),
            onupdate=sa.text("NOW()"),
        ),
        comment="Multi-sig proposals: treasury management workflow for enterprise customers",
    )

    # Indexes for multisig_proposals
    op.create_index(
        "idx_multisig_proposals_safe", "multisig_proposals", ["safe_address"]
    )
    op.create_index("idx_multisig_proposals_status", "multisig_proposals", ["status"])
    op.create_index(
        "idx_multisig_proposals_created_at", "multisig_proposals", ["created_at"]
    )
    op.create_index(
        "idx_multisig_proposals_tx_hash", "multisig_proposals", ["transaction_hash"]
    )

    # ========================================
    # 5. Crisis Events (Enterprise)
    # ========================================
    op.create_table(
        "crisis_events",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "event_type",
            sa.String(50),
            nullable=False,
            comment="Crisis type: exploit, depeg, flash_crash, liquidation_risk",
        ),
        sa.Column(
            "protocol_name",
            sa.String(100),
            nullable=False,
            comment="Affected protocol (e.g., Aave V2, Compound)",
        ),
        sa.Column(
            "severity",
            sa.String(20),
            nullable=False,
            comment="Severity: critical, high, medium, low",
        ),
        sa.Column(
            "user_exposure_usd",
            sa.Numeric(18, 2),
            nullable=False,
            comment="User exposure in USD",
        ),
        sa.Column(
            "response_time_ms",
            sa.Integer,
            nullable=False,
            comment="Crisis Manager response time (milliseconds)",
        ),
        sa.Column(
            "actions_taken",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
            comment="List of automated actions: [{action, timestamp, result}]",
        ),
        sa.Column(
            "positions_saved",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
            comment="Positions saved: [{protocol, amount_usd, action}]",
        ),
        sa.Column(
            "losses_prevented_usd",
            sa.Numeric(18, 2),
            nullable=False,
            comment="Estimated losses prevented (USD)",
        ),
        sa.Column(
            "crisis_resolved",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("false"),
            comment="Whether crisis was fully resolved",
        ),
        sa.Column(
            "resolved_at",
            sa.TIMESTAMP,
            nullable=True,
            comment="Crisis resolution timestamp",
        ),
        sa.Column(
            "created_at", sa.TIMESTAMP, nullable=False, server_default=sa.text("NOW()")
        ),
        comment="Crisis events: emergency response logs for Crisis Manager agent",
    )

    # Indexes for crisis_events
    op.create_index("idx_crisis_events_user", "crisis_events", ["user_id"])
    op.create_index("idx_crisis_events_created_at", "crisis_events", ["created_at"])
    op.create_index("idx_crisis_events_severity", "crisis_events", ["severity"])
    op.create_index("idx_crisis_events_protocol", "crisis_events", ["protocol_name"])
    op.create_index("idx_crisis_events_resolved", "crisis_events", ["crisis_resolved"])


def downgrade() -> None:
    """Drop Agent Squad tables in reverse order."""

    # Drop tables (reverse order to handle foreign keys)
    op.drop_table("crisis_events")
    op.drop_table("multisig_proposals")
    op.drop_table("compliance_screening_logs")
    op.drop_table("agent_telemetry")
    op.drop_table("agent_sessions")
