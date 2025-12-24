"""Persist Privy policies locally (cache + audit + metadata search).

Revision ID: pol_20251222
Revises: expand_addr_btc
Create Date: 2025-12-22
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "pol_20251222"
# NOTE: `expand_addr_btc` revision is not present in this repo; link to the last
# known revision in the chain instead.
down_revision: Union[str, None] = "g8h9i0j1k2l3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "policies",
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("version", sa.String(length=32), nullable=False),
        sa.Column("chain_type", sa.String(length=32), nullable=False),
        sa.Column("owner_id", sa.String(length=255), nullable=True),
        sa.Column(
            "rules",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("privy_raw", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("last_privy_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "is_deleted",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("updated_by_user_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"],
            ["users.id"],
            name=op.f("fk_policies_created_by_user_id_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["updated_by_user_id"],
            ["users.id"],
            name=op.f("fk_policies_updated_by_user_id_users"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_policies")),
    )
    op.create_index("ix_policies_name", "policies", ["name"])
    op.create_index("ix_policies_chain_type", "policies", ["chain_type"])
    op.create_index("ix_policies_owner_id", "policies", ["owner_id"])
    op.create_index("ix_policies_created_at", "policies", ["created_at"])
    op.create_index("ix_policies_updated_at", "policies", ["updated_at"])
    op.create_index("ix_policies_last_privy_sync_at", "policies", ["last_privy_sync_at"])
    op.create_index("ix_policies_is_deleted", "policies", ["is_deleted"])
    op.create_index("ix_policies_created_by_user_id", "policies", ["created_by_user_id"])
    op.create_index("ix_policies_updated_by_user_id", "policies", ["updated_by_user_id"])

    # JSONB indexes for fast metadata/rules queries (advanced search)
    op.create_index(
        "ix_policies_metadata_gin",
        "policies",
        ["metadata"],
        postgresql_using="gin",
    )

    op.create_table(
        "policy_audit_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("policy_id", sa.String(length=255), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["actor_user_id"],
            ["users.id"],
            name=op.f("fk_policy_audit_events_actor_user_id_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["policy_id"],
            ["policies.id"],
            name=op.f("fk_policy_audit_events_policy_id_policies"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_policy_audit_events")),
    )
    op.create_index("ix_policy_audit_events_policy_id", "policy_audit_events", ["policy_id"])
    op.create_index(
        "ix_policy_audit_events_actor_user_id",
        "policy_audit_events",
        ["actor_user_id"],
    )
    op.create_index("ix_policy_audit_events_action", "policy_audit_events", ["action"])
    op.create_index("ix_policy_audit_events_created_at", "policy_audit_events", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_policy_audit_events_created_at", table_name="policy_audit_events")
    op.drop_index("ix_policy_audit_events_action", table_name="policy_audit_events")
    op.drop_index("ix_policy_audit_events_actor_user_id", table_name="policy_audit_events")
    op.drop_index("ix_policy_audit_events_policy_id", table_name="policy_audit_events")
    op.drop_table("policy_audit_events")

    op.drop_index("ix_policies_metadata_gin", table_name="policies")
    op.drop_index("ix_policies_updated_by_user_id", table_name="policies")
    op.drop_index("ix_policies_created_by_user_id", table_name="policies")
    op.drop_index("ix_policies_is_deleted", table_name="policies")
    op.drop_index("ix_policies_last_privy_sync_at", table_name="policies")
    op.drop_index("ix_policies_updated_at", table_name="policies")
    op.drop_index("ix_policies_created_at", table_name="policies")
    op.drop_index("ix_policies_owner_id", table_name="policies")
    op.drop_index("ix_policies_chain_type", table_name="policies")
    op.drop_index("ix_policies_name", table_name="policies")
    op.drop_table("policies")

