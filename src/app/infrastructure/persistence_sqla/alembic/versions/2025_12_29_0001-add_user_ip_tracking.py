"""Add IP tracking fields to users table.

Adds last_ip and registration_ip columns for:
- Security auditing (login attempts, suspicious activity)
- Fraud detection (multiple accounts from same IP)
- Compliance (geo-location requirements)

Revision ID: add_user_ip_tracking
Revises: add_policy_persistence
Create Date: 2025-12-29

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ip_tracking_20251229'
down_revision = 'conv_analytics_20251224'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add IP tracking columns to users table."""
    # Add last_ip column - updated on every login
    op.add_column(
        'users',
        sa.Column('last_ip', sa.String(45), nullable=True),
    )
    
    # Add registration_ip column - set once on account creation
    op.add_column(
        'users',
        sa.Column('registration_ip', sa.String(45), nullable=True),
    )
    
    # Add index on last_ip for fraud detection queries
    op.create_index(
        'ix_users_last_ip',
        'users',
        ['last_ip'],
        unique=False,
    )


def downgrade() -> None:
    """Remove IP tracking columns from users table."""
    op.drop_index('ix_users_last_ip', table_name='users')
    op.drop_column('users', 'registration_ip')
    op.drop_column('users', 'last_ip')
