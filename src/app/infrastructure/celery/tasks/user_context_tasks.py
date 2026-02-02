"""
User Context Update Celery Tasks.

Background tasks for updating user context data used by context-aware agents.

Task Configuration:
- Runs every 10 minutes
- Processes max 100 users per run
- Skips users updated within the last hour

This ensures user context is reasonably fresh without overloading the system.
"""

import asyncio
import logging
from datetime import datetime, UTC

from app.infrastructure.celery.app import celery_app
from app.setup.ioc.provider_registry import get_providers
from app.setup.app_factory import create_async_ioc_container
from app.setup.config.settings import load_settings

logger = logging.getLogger(__name__)

# Task configuration
MAX_USERS_PER_RUN = 100  # Max users to UPDATE per run
MAX_CREATE_PER_RUN = 30  # Max users to CREATE context for per run
UPDATE_COOLDOWN_HOURS = 1


async def _run_task(coro_factory):
    """Helper to run async tasks with DI container using all registered providers."""
    settings = load_settings()
    container = create_async_ioc_container(
        providers=get_providers(),
        settings=settings,
    )
    try:
        async with container() as request_container:
            await coro_factory(request_container)
    finally:
        await container.close()


@celery_app.task(name="update_user_context")
def update_user_context():
    """
    Update user context for users eligible for processing.
    
    This task performs TWO operations:
    
    1. CREATE MISSING CONTEXTS (max 30 users)
       - Find authenticated users without user_context_aware entry
       - Create with default values
       - Ensures all users eventually get context
    
    2. UPDATE EXISTING CONTEXTS (max 100 users)
       - Fetch users where next_update_eligible_at <= NOW()
       - Aggregate chat stats, wallet data, execution history
       - Recalculate classifications (portfolio_state, activity_level, user_type)
       - Set next_update_eligible_at to NOW() + 1 hour
    
    Configuration:
    - Runs every 10 minutes (beat schedule)
    - Creates max 30 contexts per run (for users missing them)
    - Updates max 100 contexts per run
    - Skips users updated within last hour
    """
    async def runner(container):
        from app.application.chat.services.user_context_service import UserContextService
        from app.domain.chat.ports.user_context_repository import UserContextRepository
        from app.domain.chat.ports.wallet_balance import WalletBalancePort
        from app.domain.ports.chat_repository import (
            ChatUserRepository,
            ChatMessageRepository,
            ChatConversationRepository,
        )
        from app.infrastructure.persistence_sqla.registry import mapping_registry
        from app.infrastructure.adapters.types import MainAsyncSession
        from app.infrastructure.adapters.wallet_balance_db import WalletBalanceDbAdapter
        from app.infrastructure.persistence_sqla.mappings.user_context import map_user_context_aware_table
        from app.infrastructure.persistence_sqla.mappings.chat import map_chat_tables
        from sqlalchemy import select, and_
        
        # Ensure tables are mapped before using them
        map_chat_tables()
        map_user_context_aware_table()
        
        start_time = datetime.now(UTC)
        logger.info(f"🔄 Starting user context task at {start_time.isoformat()}")
        
        created_count = 0
        updated_count = 0
        error_count = 0
        
        try:
            # Get repositories from container
            context_repo = await container.get(UserContextRepository)
            message_repo = await container.get(ChatMessageRepository)
            conversation_repo = await container.get(ChatConversationRepository)
            session = await container.get(MainAsyncSession)
            
            # Create wallet balance adapter for accurate portfolio_state
            wallet_balance_adapter = WalletBalanceDbAdapter(session)
            
            # Try to get PortfolioService for real-time balance fetching
            # This is optional - if not available, falls back to DB balance only
            portfolio_service = None
            try:
                from app.application.portfolio.portfolio_service import PortfolioService
                portfolio_service = await container.get(PortfolioService)
                logger.debug("PortfolioService available for real-time balance fetching")
            except Exception as ps_err:
                logger.debug(f"PortfolioService not available (optional): {ps_err}")
            
            # Create service with wallet balance adapter and portfolio service
            service = UserContextService(
                context_repository=context_repo,
                chat_message_repository=message_repo,
                chat_conversation_repository=conversation_repo,
                wallet_repository=None,  # Deprecated
                wallet_balance_adapter=wallet_balance_adapter,  # For accurate balance
                portfolio_service=portfolio_service,  # For real-time on-chain balance
            )
            
            # ============================================
            # STEP 1: CREATE MISSING CONTEXTS (max 30)
            # ============================================
            logger.info("📝 Step 1: Creating missing user contexts...")
            
            # Use reflected tables to get actual DB schema (mapping may be outdated)
            from sqlalchemy import MetaData, Table
            metadata = MetaData()
            try:
                chat_users_table = Table("chat_users", metadata, autoload_with=session.get_bind())
                context_table = Table("user_context_aware", metadata, autoload_with=session.get_bind())
            except Exception as e:
                logger.warning(f"  Could not reflect tables: {e}")
                chat_users_table = None
                context_table = None
            
            if chat_users_table is not None and context_table is not None:
                # Query authenticated users without context
                # Note: chat_users table structure varies - use only id column
                stmt = (
                    select(
                        chat_users_table.c.id,
                    )
                    .select_from(chat_users_table)
                    .outerjoin(
                        context_table,
                        chat_users_table.c.id == context_table.c.chat_user_id,
                    )
                    .where(
                        and_(
                            chat_users_table.c.user_type == "authenticated",
                            context_table.c.id.is_(None),
                        )
                    )
                    .limit(MAX_CREATE_PER_RUN)
                )
                
                result = await session.execute(stmt)
                missing_users = result.fetchall()
                
                if missing_users:
                    logger.info(f"  Found {len(missing_users)} users without context")
                    
                    for row in missing_users:
                        chat_user_id = row[0]
                        try:
                            await service.create_for_new_user(
                                chat_user_id=chat_user_id,
                                legacy_user_id=None,  # No longer tracked in chat_users
                            )
                            created_count += 1
                            logger.debug(f"  Created context for {chat_user_id}")
                        except Exception as e:
                            error_count += 1
                            logger.error(f"  Failed to create for {chat_user_id}: {e}")
                else:
                    logger.info("  ✓ All users have context entries")
            else:
                logger.warning("  Tables not found, skipping creation step")
            
            # ============================================
            # STEP 2: UPDATE EXISTING CONTEXTS (max 100)
            # ============================================
            logger.info("🔄 Step 2: Updating existing user contexts...")
            
            # Get eligible users
            users = await service.get_users_for_update(
                limit=MAX_USERS_PER_RUN,
                cooldown_hours=UPDATE_COOLDOWN_HOURS,
            )
            
            if not users:
                logger.info("  ✓ No users eligible for update")
            else:
                logger.info(f"  Processing {len(users)} users for update")
                
                for user in users:
                    try:
                        result = await service.update_user_context(
                            chat_user_id=user.chat_user_id,
                            cooldown_hours=UPDATE_COOLDOWN_HOURS,
                        )
                        
                        if result:
                            updated_count += 1
                            logger.debug(
                                f"  Updated {user.chat_user_id}: "
                                f"portfolio={result.portfolio_state}, "
                                f"activity={result.activity_level}, "
                                f"type={result.user_type}"
                            )
                        else:
                            error_count += 1
                            
                    except Exception as e:
                        error_count += 1
                        logger.error(f"  Failed to update {user.chat_user_id}: {e}")
            
            # ============================================
            # SUMMARY
            # ============================================
            duration = (datetime.now(UTC) - start_time).total_seconds()
            logger.info(
                f"✅ User context task complete: "
                f"created={created_count}, updated={updated_count}, "
                f"errors={error_count}, duration={duration:.2f}s"
            )
            
        except Exception as e:
            logger.error(f"❌ User context task failed: {e}")
            raise
    
    asyncio.run(_run_task(runner))


@celery_app.task(name="create_missing_user_contexts")
def create_missing_user_contexts():
    """
    Create context entries for users who don't have one.
    
    This is a one-time migration task that can also be run
    periodically to catch any users who slipped through.
    
    Processes max 100 users per run.
    """
    async def runner(container):
        from app.application.chat.services.user_context_service import UserContextService
        from app.domain.chat.ports.user_context_repository import UserContextRepository
        from app.domain.ports.chat_repository import (
            ChatUserRepository,
            ChatMessageRepository,
            ChatConversationRepository,
        )
        from sqlalchemy import select, and_, not_
        from sqlalchemy.dialects.postgresql import UUID
        
        start_time = datetime.now(UTC)
        logger.info(f"🔄 Starting missing user context creation at {start_time.isoformat()}")
        
        try:
            # Get repositories
            context_repo = await container.get(UserContextRepository)
            chat_user_repo = await container.get(ChatUserRepository)
            message_repo = await container.get(ChatMessageRepository)
            conversation_repo = await container.get(ChatConversationRepository)
            
            # Create service
            service = UserContextService(
                context_repository=context_repo,
                chat_message_repository=message_repo,
                chat_conversation_repository=conversation_repo,
            )
            
            # Find authenticated users without context
            # Note: This is a simplified query - in production you'd
            # do a proper LEFT JOIN to find missing entries
            from app.infrastructure.persistence_sqla.registry import mapping_registry
            from app.infrastructure.adapters.types import MainAsyncSession
            
            session = await container.get(MainAsyncSession)
            
            chat_users_table = mapping_registry.metadata.tables.get("chat_users")
            context_table = mapping_registry.metadata.tables.get("user_context_aware")
            
            if not chat_users_table or not context_table:
                logger.warning("Tables not found, skipping")
                return
            
            # Query for authenticated users without context
            # (user_type = 'authenticated' means they logged in via Privy)
            stmt = (
                select(chat_users_table.c.id)
                .select_from(chat_users_table)
                .outerjoin(
                    context_table,
                    chat_users_table.c.id == context_table.c.chat_user_id,
                )
                .where(
                    and_(
                        chat_users_table.c.user_type == "authenticated",
                        context_table.c.id.is_(None),
                    )
                )
                .limit(MAX_USERS_PER_RUN)
            )
            
            result = await session.execute(stmt)
            missing_user_ids = [row[0] for row in result.fetchall()]
            
            if not missing_user_ids:
                logger.info("✅ No users missing context entries")
                return
            
            logger.info(f"📊 Creating context for {len(missing_user_ids)} users")
            
            # Create context for each
            created_count = 0
            for user_id in missing_user_ids:
                try:
                    await service.create_for_new_user(
                        chat_user_id=user_id,
                        legacy_user_id=None,
                    )
                    created_count += 1
                except Exception as e:
                    logger.error(f"Failed to create context for {user_id}: {e}")
            
            duration = (datetime.now(UTC) - start_time).total_seconds()
            logger.info(
                f"✅ Missing context creation complete: "
                f"{created_count}/{len(missing_user_ids)} created, "
                f"{duration:.2f}s duration"
            )
            
        except Exception as e:
            logger.error(f"❌ Missing context creation failed: {e}")
            raise
    
    asyncio.run(_run_task(runner))


@celery_app.task(name="user_context_analytics")
def user_context_analytics():
    """
    Generate analytics report and persist snapshot to database.
    
    This task:
    1. Aggregates user distribution stats from user_context_aware
    2. Persists a daily snapshot to analytics_snapshots table
    3. Logs summary statistics for monitoring
    
    Runs daily at 6 AM (configured in beat schedule).
    """
    async def runner(container):
        from datetime import date
        from decimal import Decimal
        from uuid import uuid4
        from app.application.chat.services.user_context_service import UserContextService
        from app.domain.chat.ports.user_context_repository import UserContextRepository
        from app.domain.chat.ports.analytics_repository import AnalyticsRepository
        from app.domain.chat.entities.analytics_snapshot import (
            AnalyticsSnapshot,
            PortfolioDistribution,
            ActivityDistribution,
            UserTypeDistribution,
            ExecutionMetrics,
        )
        from app.domain.ports.chat_repository import (
            ChatMessageRepository,
            ChatConversationRepository,
        )
        from app.infrastructure.adapters.types import MainAsyncSession
        from app.infrastructure.adapters.analytics_repository_sqla import AnalyticsRepositorySqla
        
        logger.info("📊 Generating user context analytics and snapshot")
        
        try:
            # Get repositories
            context_repo = await container.get(UserContextRepository)
            message_repo = await container.get(ChatMessageRepository)
            conversation_repo = await container.get(ChatConversationRepository)
            session = await container.get(MainAsyncSession)
            
            # Create analytics repository
            analytics_repo = AnalyticsRepositorySqla(session)
            
            # Create service
            service = UserContextService(
                context_repository=context_repo,
                chat_message_repository=message_repo,
                chat_conversation_repository=conversation_repo,
            )
            
            # Get distribution stats
            stats = await service.get_distribution_stats()
            
            # Extract portfolio state stats
            portfolio_stats = stats.get("portfolio_state", {})
            total_users = sum(portfolio_stats.values())
            
            # Extract activity level stats
            activity_stats = stats.get("activity_level", {})
            
            # Extract user type stats
            type_stats = stats.get("user_type", {})
            
            # Get execution stats from context repo
            # (Aggregate from user_context_aware table)
            exec_stats = await context_repo.get_execution_stats() if hasattr(context_repo, 'get_execution_stats') else {}
            
            # Get total balance from context repo
            total_balance = await context_repo.get_total_balance() if hasattr(context_repo, 'get_total_balance') else Decimal("0")
            
            # Build snapshot entity
            snapshot = AnalyticsSnapshot(
                id=uuid4(),
                snapshot_date=date.today(),
                snapshot_type="daily",
                portfolio=PortfolioDistribution(
                    empty=portfolio_stats.get("empty", 0),
                    starter=portfolio_stats.get("starter", 0),
                    active=portfolio_stats.get("active", 0),
                    whale=portfolio_stats.get("whale", 0),
                ),
                activity=ActivityDistribution(
                    new=activity_stats.get("new", 0),
                    very_active=activity_stats.get("very_active", 0),
                    active=activity_stats.get("active", 0),
                    weekly_active=activity_stats.get("weekly_active", 0),
                    monthly_active=activity_stats.get("monthly_active", 0),
                    inactive=activity_stats.get("inactive", 0),
                    reactivated=activity_stats.get("reactivated", 0),
                ),
                user_types=UserTypeDistribution(
                    new_user=type_stats.get("new_user", 0),
                    casual=type_stats.get("casual", 0),
                    trader=type_stats.get("trader", 0),
                    yield_farmer=type_stats.get("yield_farmer", 0),
                    power_user=type_stats.get("power_user", 0),
                ),
                executions=ExecutionMetrics(
                    total=exec_stats.get("total", 0),
                    swap=exec_stats.get("swap", 0),
                    buy=exec_stats.get("buy", 0),
                    lending=exec_stats.get("lending", 0),
                    transfer=exec_stats.get("transfer", 0),
                    cashout=exec_stats.get("cashout", 0),
                ),
                total_users=total_users,
                total_balance_usd=total_balance if isinstance(total_balance, Decimal) else Decimal(str(total_balance)),
            )
            
            # Save snapshot to database
            await analytics_repo.save(snapshot)
            logger.info(f"💾 Saved analytics snapshot for {snapshot.snapshot_date}")
            
            # Log distribution for monitoring
            logger.info(f"📈 User Context Analytics (Total: {total_users})")
            logger.info("Portfolio State Distribution:")
            for state, count in portfolio_stats.items():
                pct = (count / total_users * 100) if total_users > 0 else 0
                logger.info(f"  - {state}: {count} ({pct:.1f}%)")
            
            logger.info("Activity Level Distribution:")
            for level, count in activity_stats.items():
                pct = (count / total_users * 100) if total_users > 0 else 0
                logger.info(f"  - {level}: {count} ({pct:.1f}%)")
            
            logger.info("User Type Distribution:")
            for user_type, count in type_stats.items():
                pct = (count / total_users * 100) if total_users > 0 else 0
                logger.info(f"  - {user_type}: {count} ({pct:.1f}%)")
            
            logger.info("✅ Analytics snapshot saved and logged")
            
        except Exception as e:
            logger.error(f"❌ Analytics generation failed: {e}")
            raise
    
    asyncio.run(_run_task(runner))
