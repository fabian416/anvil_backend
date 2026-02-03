import logging
from collections.abc import AsyncIterator, Iterable
from contextlib import asynccontextmanager

from dishka import AsyncContainer, Provider, make_async_container
from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from sqlalchemy.ext.asyncio import AsyncEngine

from app.infrastructure.persistence_sqla.mappings.all import map_tables
from app.infrastructure.persistence_sqla.registry import mapping_registry
from app.presentation.http.auth.asgi_middleware import (
    ASGIAuthMiddleware,
)
from app.setup.config.settings import AppSettings


async def init_database(engine: AsyncEngine) -> None:
    """
    Initialize the database by ensuring all tables exist.

    This function:
    - Registers all SQLAlchemy mappings
    - Creates any missing tables (idempotent - does NOT drop existing tables)
    - Does NOT recreate or drop existing tables

    Note: SQLAlchemy's create_all() only creates tables that don't exist.
    For a full reset (drop + recreate), use: make init-db
    """
    logger = logging.getLogger(__name__)

    try:
        # Ensure all table mappings are registered
        map_tables()

        # Import entities to ensure they are registered
        from app.domain.entities.user import User
        from app.domain.atlas.entities.country import Country
        from app.domain.atlas.entities.city import City
        from app.domain.entities.email_verification import EmailVerification
        from app.domain.entities.notification import Notification
        from app.domain.entities.password_reset import PasswordReset
        from app.domain.entities.payment import Payment
        from app.domain.entities.session import Session
        from app.domain.entities.subscription import Subscription
        from app.domain.entities.subscription_user import SubscriptionUser

        # Check existing tables before creating
        from sqlalchemy import text

        async with engine.connect() as conn:
            result = await conn.execute(
                text("""
                    SELECT COUNT(*) 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_type = 'BASE TABLE'
                """)
            )
            existing_count = result.scalar()

        # Create all tables (only creates missing ones - idempotent)
        async with engine.begin() as conn:
            await conn.run_sync(mapping_registry.metadata.create_all)

        # Check tables after creation
        async with engine.connect() as conn:
            result = await conn.execute(
                text("""
                    SELECT COUNT(*) 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_type = 'BASE TABLE'
                """)
            )
            final_count = result.scalar()

        if final_count > existing_count:
            logger.info(
                f"Database initialized: Created {final_count - existing_count} new table(s). "
                f"Total tables: {final_count}"
            )
        else:
            logger.info(
                f"Database verified: All {final_count} tables already exist. "
                "No tables were recreated."
            )
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise


def create_app() -> FastAPI:
    return FastAPI(
        lifespan=lifespan,
        default_response_class=ORJSONResponse,
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Initialize database tables
    try:
        # Get the engine from the container
        container = app.state.dishka_container
        engine = await container.get(AsyncEngine)
        await init_database(engine)
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to initialize database: {str(e)}")
        # You might want to raise here depending on your requirements
        # raise

    yield None
    await app.state.dishka_container.close()
    # https://dishka.readthedocs.io/en/stable/integrations/fastapi.html


def configure_app(
    app: FastAPI,
    root_router: APIRouter,
    environment: str = "local",
) -> None:
    """
    Configure FastAPI application with middleware and routing.

    Args:
        app: FastAPI application instance
        root_router: Root API router
        environment: Environment name (local, dev, prod)
    """
    app.include_router(root_router)
    app.add_middleware(ASGIAuthMiddleware)

    # CORS middleware with environment-specific origins
    from app.presentation.http.middleware.cors_config import get_cors_config

    cors_config = get_cors_config(environment)

    # For local development, allow flexible localhost ports
    allow_origin_regex = None
    if environment == "local":
        allow_origin_regex = r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_config["allow_origins"],
        allow_origin_regex=allow_origin_regex,
        allow_credentials=cors_config["allow_credentials"],
        allow_methods=cors_config["allow_methods"],
        allow_headers=cors_config["allow_headers"],
        expose_headers=cors_config["expose_headers"],
        max_age=cors_config["max_age"],
    )

    # Security headers middleware (OWASP best practices)
    from app.presentation.http.middleware.security_headers import (
        SecurityHeadersMiddleware,
        HTTPSRedirectMiddleware,
    )

    # Add HTTPS redirect for production
    is_production = environment in ("prod", "production")
    if is_production:
        app.add_middleware(HTTPSRedirectMiddleware, enabled=True)

    # Add security headers
    app.add_middleware(
        SecurityHeadersMiddleware,
        enable_hsts=is_production,  # HSTS only in production with HTTPS
        enable_csp=True,  # Content Security Policy in all environments
    )

    # Register global exception handlers for standardized error responses
    from app.presentation.http.errors.handlers import register_exception_handlers

    register_exception_handlers(app)


def create_async_ioc_container(
    providers: Iterable[Provider],
    settings: AppSettings,
) -> AsyncContainer:
    return make_async_container(
        *providers,
        context={AppSettings: settings},
    )
