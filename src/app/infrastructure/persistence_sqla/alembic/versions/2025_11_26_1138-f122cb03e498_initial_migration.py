"""Initial migration

Revision ID: f122cb03e498
Revises:
Create Date: 2025-11-26 11:38:58.993338

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "f122cb03e498"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create Enums using raw SQL to avoid duplication issues
    connection = op.get_bind()
    connection.execute(sa.text("""DO $$ BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'userrole') THEN
            CREATE TYPE userrole AS ENUM ('admin', 'moderator', 'user', 'guest');
        END IF;
    END $$;"""))
    
    op.create_table(
        "cities",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("city_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("state_id", sa.String(length=20), nullable=True),
        sa.Column("state_code", sa.String(length=10), nullable=True),
        sa.Column("state_name", sa.String(length=100), nullable=True),
        sa.Column("country_id", sa.Integer(), nullable=False),
        sa.Column("country_code", sa.String(length=2), nullable=True),
        sa.Column("country_name", sa.String(length=100), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("wikiDataId", sa.String(length=50), nullable=True),
        sa.CheckConstraint(
            "latitude >= -90 AND latitude <= 90",
            name=op.f("ck_cities_check_city_latitude_range"),
        ),
        sa.CheckConstraint(
            "longitude >= -180 AND longitude <= 180",
            name=op.f("ck_cities_check_city_longitude_range"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cities")),
        sa.UniqueConstraint("city_id", "country_id", name="uq_cities_city_country"),
    )
    op.create_index(op.f("ix_cities_city_id"), "cities", ["city_id"], unique=False)
    op.create_index(
        op.f("ix_cities_country_code"), "cities", ["country_code"], unique=False
    )
    op.create_index(
        op.f("ix_cities_country_id"), "cities", ["country_id"], unique=False
    )
    op.create_index(op.f("ix_cities_id"), "cities", ["id"], unique=False)
    op.create_index(op.f("ix_cities_name"), "cities", ["name"], unique=False)
    op.create_index(
        op.f("ix_cities_state_code"), "cities", ["state_code"], unique=False
    )
    op.create_index(op.f("ix_cities_state_id"), "cities", ["state_id"], unique=False)
    op.create_index(
        op.f("ix_cities_wikiDataId"), "cities", ["wikiDataId"], unique=False
    )
    op.create_table(
        "countries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("country_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("iso3", sa.String(length=3), nullable=False),
        sa.Column("iso2", sa.String(length=2), nullable=True),
        sa.Column("numeric_code", sa.String(length=3), nullable=True),
        sa.Column("phonecode", sa.String(length=20), nullable=True),
        sa.Column("capital", sa.String(length=100), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=True),
        sa.Column("currency_name", sa.String(length=50), nullable=True),
        sa.Column("currency_symbol", sa.String(length=10), nullable=True),
        sa.Column("tld", sa.String(length=10), nullable=True),
        sa.Column("native", sa.String(length=100), nullable=True),
        sa.Column("nationality", sa.String(length=100), nullable=True),
        sa.Column("timezones", sa.JSON(), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("emoji", sa.String(length=10), nullable=True),
        sa.Column("emojiU", sa.String(length=20), nullable=True),
        sa.Column("region", sa.String(length=50), nullable=True),
        sa.Column("subregion", sa.String(length=50), nullable=True),
        sa.CheckConstraint(
            "latitude >= -90 AND latitude <= 90",
            name=op.f("ck_countries_check_latitude_range"),
        ),
        sa.CheckConstraint(
            "longitude >= -180 AND longitude <= 180",
            name=op.f("ck_countries_check_longitude_range"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_countries")),
    )
    op.create_index(
        op.f("ix_countries_country_id"), "countries", ["country_id"], unique=False
    )
    op.create_index(op.f("ix_countries_id"), "countries", ["id"], unique=False)
    op.create_index(op.f("ix_countries_iso2"), "countries", ["iso2"], unique=False)
    op.create_index(op.f("ix_countries_iso3"), "countries", ["iso3"], unique=True)
    op.create_index(op.f("ix_countries_name"), "countries", ["name"], unique=False)
    op.create_index(op.f("ix_countries_region"), "countries", ["region"], unique=False)
    op.create_index(
        op.f("ix_countries_subregion"), "countries", ["subregion"], unique=False
    )
    op.create_table(
        "subscriptions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("subscription_type", sa.String(length=100), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=True),
        sa.Column("duration", sa.Integer(), nullable=False),
        sa.Column("features", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("stripe_price_id", sa.String(length=255), nullable=True),
        sa.Column("stripe_product_id", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_subscriptions")),
    )
    op.create_index(op.f("ix_subscriptions_id"), "subscriptions", ["id"], unique=False)
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("first_name", sa.String(length=100), nullable=False),
        sa.Column("last_name", sa.String(length=100), nullable=False),
        sa.Column(
            "role",
            postgresql.ENUM(
                "admin",
                "moderator",
                "user",
                "guest",
                name="userrole",
                create_type=False,
            ),
            nullable=True,
        ),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("is_blocked", sa.Boolean(), nullable=True),
        sa.Column("is_verified", sa.Boolean(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=True),
        sa.Column("password", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        sa.Column("last_login", sa.DateTime(), nullable=True),
        sa.Column("profile_picture", sa.String(length=255), nullable=True),
        sa.Column("phone_number", sa.String(length=20), nullable=True),
        sa.Column("language", sa.String(length=10), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("postal_code", sa.String(length=20), nullable=True),
        sa.Column("country_id", sa.Integer(), nullable=True),
        sa.Column("city_id", sa.Integer(), nullable=True),
        sa.Column("subscription", sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(
            ["city_id"], ["cities.id"], name=op.f("fk_users_city_id_cities")
        ),
        sa.ForeignKeyConstraint(
            ["country_id"], ["countries.id"], name=op.f("fk_users_country_id_countries")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)
    op.create_table(
        "auth_sessions",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("expiration", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_auth_sessions_user_id_users")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_auth_sessions")),
    )
    op.create_table(
        "email_verifications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_used", sa.Boolean(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_email_verifications_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_email_verifications")),
    )
    op.create_index(
        op.f("ix_email_verifications_id"), "email_verifications", ["id"], unique=False
    )
    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=True),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("data_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_notifications_user_id_users")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_notifications")),
    )
    op.create_index(op.f("ix_notifications_id"), "notifications", ["id"], unique=False)
    op.create_table(
        "password_resets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_used", sa.Boolean(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_password_resets_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_password_resets")),
    )
    op.create_index(
        op.f("ix_password_resets_id"), "password_resets", ["id"], unique=False
    )
    op.create_table(
        "sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("access_token", sa.String(length=500), nullable=False),
        sa.Column("refresh_token", sa.String(length=500), nullable=False),
        sa.Column("token_type", sa.String(length=50), nullable=True),
        sa.Column("ip_address", sa.String(length=50), nullable=True),
        sa.Column("user_agent", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("last_activity", sa.DateTime(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_sessions_user_id_users")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sessions")),
    )
    op.create_index(op.f("ix_sessions_id"), "sessions", ["id"], unique=False)
    op.create_table(
        "subscription_users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("subscription_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("stripe_subscription_id", sa.String(length=255), nullable=True),
        sa.Column("stripe_customer_id", sa.String(length=255), nullable=True),
        sa.Column("client_secret", sa.String(length=255), nullable=True),
        sa.Column("subscription_data", sa.JSON(), nullable=True),
        sa.Column("data_json", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default="now()",
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["subscription_id"],
            ["subscriptions.id"],
            name=op.f("fk_subscription_users_subscription_id_subscriptions"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_subscription_users_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_subscription_users")),
    )
    op.create_index(
        op.f("ix_subscription_users_id"), "subscription_users", ["id"], unique=False
    )
    op.create_table(
        "payments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("subscription_id", sa.Integer(), nullable=True),
        sa.Column("subscription_user_id", sa.Integer(), nullable=True),
        sa.Column("amount", sa.Float(), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("stripe_payment_intent_id", sa.String(length=255), nullable=True),
        sa.Column("stripe_customer_id", sa.String(length=255), nullable=True),
        sa.Column("payment_data", sa.JSON(), nullable=True),
        sa.Column("payment_method", sa.String(length=50), nullable=True),
        sa.Column("payment_type", sa.String(length=50), nullable=True),
        sa.Column("date", sa.DateTime(), nullable=True),
        sa.Column("data_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["subscription_id"],
            ["subscriptions.id"],
            name=op.f("fk_payments_subscription_id_subscriptions"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["subscription_user_id"],
            ["subscription_users.id"],
            name=op.f("fk_payments_subscription_user_id_subscription_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_payments_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_payments")),
    )
    op.create_index(op.f("ix_payments_id"), "payments", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_payments_id"), table_name="payments")
    op.drop_table("payments")
    op.drop_index(op.f("ix_subscription_users_id"), table_name="subscription_users")
    op.drop_table("subscription_users")
    op.drop_index(op.f("ix_sessions_id"), table_name="sessions")
    op.drop_table("sessions")
    op.drop_index(op.f("ix_password_resets_id"), table_name="password_resets")
    op.drop_table("password_resets")
    op.drop_index(op.f("ix_notifications_id"), table_name="notifications")
    op.drop_table("notifications")
    op.drop_index(op.f("ix_email_verifications_id"), table_name="email_verifications")
    op.drop_table("email_verifications")
    op.drop_table("auth_sessions")
    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
    op.drop_index(op.f("ix_subscriptions_id"), table_name="subscriptions")
    op.drop_table("subscriptions")
    op.drop_index(op.f("ix_countries_subregion"), table_name="countries")
    op.drop_index(op.f("ix_countries_region"), table_name="countries")
    op.drop_index(op.f("ix_countries_name"), table_name="countries")
    op.drop_index(op.f("ix_countries_iso3"), table_name="countries")
    op.drop_index(op.f("ix_countries_iso2"), table_name="countries")
    op.drop_index(op.f("ix_countries_id"), table_name="countries")
    op.drop_index(op.f("ix_countries_country_id"), table_name="countries")
    op.drop_table("countries")
    op.drop_index(op.f("ix_cities_wikiDataId"), table_name="cities")
    op.drop_index(op.f("ix_cities_state_id"), table_name="cities")
    op.drop_index(op.f("ix_cities_state_code"), table_name="cities")
    op.drop_index(op.f("ix_cities_name"), table_name="cities")
    op.drop_index(op.f("ix_cities_id"), table_name="cities")
    op.drop_index(op.f("ix_cities_country_id"), table_name="cities")
    op.drop_index(op.f("ix_cities_country_code"), table_name="cities")
    op.drop_index(op.f("ix_cities_city_id"), table_name="cities")
    op.drop_table("cities")
    sa.Enum(name="userrole").drop(op.get_bind())
