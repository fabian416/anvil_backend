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
) -> None:
    app.include_router(root_router)
    app.add_middleware(ASGIAuthMiddleware)

    # CORS middleware for frontend (Vite dev server on 5173)
    origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    # https://github.com/encode/starlette/discussions/2451

    # Good place to register global exception handlers


def create_async_ioc_container(
    providers: Iterable[Provider],
    settings: AppSettings,
) -> AsyncContainer:
    return make_async_container(
        *providers,
        context={AppSettings: settings},
    )
