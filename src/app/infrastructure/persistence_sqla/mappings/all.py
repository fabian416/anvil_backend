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
# REMOVED: Legacy session mapping (use auth_session instead)
# from app.infrastructure.persistence_sqla.mappings.session import map_sessions_table
from app.infrastructure.persistence_sqla.mappings.subscription import map_subscriptions_table
from app.infrastructure.persistence_sqla.mappings.subscription_user import map_subscription_users_table
from app.infrastructure.persistence_sqla.mappings.user import map_users_table
# REMOVED: Legacy conversation/message mappings (use chat_unified instead)
# from app.infrastructure.persistence_sqla.mappings.conversation import map_conversation_table
# from app.infrastructure.persistence_sqla.mappings.message import map_message_table
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
# Guest Chat - Still in active use by /guest/ router
from app.infrastructure.persistence_sqla.mappings.guest import map_guest_tables
from app.infrastructure.persistence_sqla.mappings.chat_unified import map_unified_chat_tables
from app.infrastructure.persistence_sqla.mappings.moonpay import map_moonpay_customer_tokens_table
from app.infrastructure.persistence_sqla.mappings.user_context import map_user_context_aware_table
from app.infrastructure.persistence_sqla.mappings.lending_position_mapping import map_lending_positions_table
from app.infrastructure.persistence_sqla.mappings.lending_supply_mapping import map_lending_supplies_table
from app.infrastructure.persistence_sqla.mappings.lending_borrow_mapping import map_lending_borrows_table
from app.infrastructure.persistence_sqla.mappings.lending_transaction_mapping import map_lending_transactions_table
from app.infrastructure.persistence_sqla.mappings.user_lending_preferences_mapping import map_user_lending_preferences_table
from app.infrastructure.persistence_sqla.mappings.lending_health_check_mapping import map_lending_health_checks_table
from app.infrastructure.persistence_sqla.mappings.leverage_loop_execution_mapping import map_leverage_loop_executions_table
from app.infrastructure.persistence_sqla.mappings.lending_alert_mapping import map_lending_alerts_table


def map_tables() -> None:
    map_users_table()
    map_auth_sessions_table()
    map_countries_table()
    map_cities_table()
    map_email_verifications_table()
    map_notifications_table()
    map_password_resets_table()
    map_payments_table()
    # REMOVED: map_sessions_table() - Legacy session (use auth_sessions)
    map_subscriptions_table()
    map_subscription_users_table()
    # REMOVED: Legacy DeFi Chat mappings (use unified chat)
    # map_conversation_table()
    # map_message_table()
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
    # Guest Chat - Still in active use by /guest/ router
    map_guest_tables()
    # Unified Chat (guest + authenticated) - Primary chat system
    map_unified_chat_tables()
    # MoonPay Customer Tokens
    map_moonpay_customer_tokens_table()
    # User Context Aware (context-aware agent responses)
    map_user_context_aware_table()
    # Lending Tables (Aave & Morpho)
    map_lending_positions_table()
    map_lending_supplies_table()
    map_lending_borrows_table()
    map_lending_transactions_table()
    map_user_lending_preferences_table()
    map_lending_health_checks_table()
    map_leverage_loop_executions_table()
    map_lending_alerts_table()
