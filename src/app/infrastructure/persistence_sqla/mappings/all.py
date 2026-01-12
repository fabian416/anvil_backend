"""
Ensures imperative SQLAlchemy mappings are initialized at application startup.

### Purpose:
In Clean Architecture, domain entities remain agnostic of database
mappings. To integrate with SQLAlchemy, mappings must be explicitly
triggered to link ORM attributes to domain classes. Without this setup,
attempts to interact with unmapped entities in database operations
will lead to runtime errors.

### Solution:
This module provides a single entry point to initialize the mapping
of domain entities to database tables. By calling the `map_tables` function,
ORM attributes are linked to domain classes without altering domain code
or introducing infrastructure concerns.

### Usage:
Call the `map_tables` function in the application factory to initialize
mappings at startup. Additionally, it is necessary to call this function
in `env.py` for Alembic migrations to ensure all models are available
during database migrations.
"""

from app.infrastructure.persistence_sqla.mappings.auth_session import (
    map_auth_sessions_table,
)
from app.infrastructure.persistence_sqla.mappings.city import map_cities_table
from app.infrastructure.persistence_sqla.mappings.country import map_countries_table
from app.infrastructure.persistence_sqla.mappings.email_verification import map_email_verifications_table
from app.infrastructure.persistence_sqla.mappings.notification import map_notifications_table
from app.infrastructure.persistence_sqla.mappings.password_reset import map_password_resets_table
from app.infrastructure.persistence_sqla.mappings.payment import map_payments_table
from app.infrastructure.persistence_sqla.mappings.session import map_sessions_table
from app.infrastructure.persistence_sqla.mappings.subscription import map_subscriptions_table
from app.infrastructure.persistence_sqla.mappings.subscription_user import map_subscription_users_table
from app.infrastructure.persistence_sqla.mappings.user import map_users_table
from app.infrastructure.persistence_sqla.mappings.conversation import map_conversation_table
from app.infrastructure.persistence_sqla.mappings.message import map_message_table
from app.infrastructure.persistence_sqla.mappings.agent_session import map_agent_session_table
from app.infrastructure.persistence_sqla.mappings.conversation_analytics import (
    map_conversation_analytics_table,
)
from app.infrastructure.persistence_sqla.mappings.wallet import map_wallet_tables
from app.infrastructure.persistence_sqla.mappings.transaction import map_transaction_table
from app.infrastructure.persistence_sqla.mappings.defi_operations import map_defi_operations_tables
from app.infrastructure.persistence_sqla.mappings.ai_telemetry import map_ai_telemetry_tables
from app.infrastructure.persistence_sqla.mappings.system_config import map_system_config_tables
from app.infrastructure.persistence_sqla.mappings.portfolio_snapshot import map_portfolio_snapshot_tables
from app.infrastructure.persistence_sqla.mappings.policy import map_policy_tables
from app.infrastructure.persistence_sqla.mappings.guest import map_guest_tables
from app.infrastructure.persistence_sqla.mappings.chat_unified import map_unified_chat_tables


def map_tables() -> None:
    map_users_table()
    map_auth_sessions_table()
    map_countries_table()
    map_cities_table()
    map_email_verifications_table()
    map_notifications_table()
    map_password_resets_table()
    map_payments_table()
    map_sessions_table()
    map_subscriptions_table()
    map_subscription_users_table()
    # DeFi Chat mappings
    map_conversation_table()
    map_message_table()
    map_agent_session_table()
    map_conversation_analytics_table()
    # Wallet & Transactions
    map_wallet_tables()
    map_transaction_table()
    # Policies (Privy cache + audit)
    map_policy_tables()
    # DeFi Operations
    map_defi_operations_tables()
    # AI Telemetry
    map_ai_telemetry_tables()
    # System Config
    map_system_config_tables()
    # Portfolio Snapshots
    map_portfolio_snapshot_tables()
    # Guest Chat
    map_guest_tables()
    # Unified Chat (guest + authenticated)
    map_unified_chat_tables()
