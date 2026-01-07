"""Expand agenttype enum with all 18 agent types

Revision ID: expand_agenttype_enum
Revises: chat_unified_v2
Create Date: 2026-01-06 16:00:00.000000

This migration adds the missing agent types to the PostgreSQL enum.
The original enum only had 5 values but the Python AgentType enum has 18 agents:

Core User-Facing Agents (10):
- chat, hunter_ai, research, execution, risk_analyzer
- portfolio, tax_optimizer, defi_yield, security_auditor, gas_optimizer

Enterprise Agents (8):
- compliance_monitor, multisig_coordinator, alert_monitoring, crisis_manager
- bridge_crosschain, lending_borrowing, nft_asset_manager, dao_governance
"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "expand_agenttype_enum"
down_revision: Union[str, None] = "chat_unified_v2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# New values to add to the agenttype enum
# Original values: trading, yield_farming, risk_analysis, research, portfolio
# Note: Some original values are aliases in Python (trading->execution, yield_farming->defi_yield, risk_analysis->risk_analyzer)
NEW_AGENT_TYPE_VALUES = [
    # Core agents (not in original enum)
    "chat",
    "hunter_ai",
    "execution",
    "risk_analyzer",
    "tax_optimizer",
    "defi_yield",
    "security_auditor",
    "gas_optimizer",
    # Enterprise agents
    "compliance_monitor",
    "multisig_coordinator",
    "alert_monitoring",
    "crisis_manager",
    "bridge_crosschain",
    "lending_borrowing",
    "nft_asset_manager",
    "dao_governance",
]


def upgrade() -> None:
    """Add new values to the agenttype enum."""
    # PostgreSQL allows adding new values to an enum type using ALTER TYPE
    # Each value must be added individually
    for value in NEW_AGENT_TYPE_VALUES:
        op.execute(f"ALTER TYPE agenttype ADD VALUE IF NOT EXISTS '{value}'")


def downgrade() -> None:
    """
    Note: PostgreSQL does not support removing values from an enum type.
    To truly downgrade, you would need to:
    1. Create a new enum type without the removed values
    2. Update all columns using the enum to use the new type
    3. Drop the old enum type
    4. Rename the new enum type to the old name
    
    This is a complex and potentially dangerous operation, so we leave 
    the enum values in place during downgrade.
    """
    # Cannot remove enum values in PostgreSQL - this is intentional
    pass

