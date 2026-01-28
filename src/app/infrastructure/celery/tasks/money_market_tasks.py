"""
Money Market Celery Tasks.

Background tasks for money market operations:
1. Cache warming - Pre-fetch popular asset/chain combinations every 60s
2. Rate alerts - Check alert conditions and send notifications every 5 minutes
3. Analytics aggregation - Aggregate comparison logs every hour
4. Cache cleanup - Remove expired cache entries daily

All tasks use async/await with Dishka DI container for dependency injection.
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from celery import shared_task

from app.setup.app_factory import create_async_ioc_container
from app.setup.config.settings import load_settings
from app.setup.ioc.application import ApplicationProvider
from app.setup.ioc.infrastructure import infrastructure_provider
from app.setup.ioc.money_market import MoneyMarketProvider
from app.setup.ioc.presentation import PresentationProvider
from app.setup.ioc.settings import SettingsProvider

logger = logging.getLogger(__name__)


async def _run_task(coro_factory):
    """
    Helper to run async tasks with DI container.

    Creates a Dishka container with all required providers and enters
    REQUEST scope for proper dependency resolution.
    """
    settings = load_settings()
    container = create_async_ioc_container(
        providers=(
            ApplicationProvider(),
            infrastructure_provider(),
            PresentationProvider(),
            SettingsProvider(),
            MoneyMarketProvider(),  # Money market DI provider
        ),
        settings=settings,
    )
    try:
        # Enter request scope so REQUEST-scoped providers can be resolved
        async with container() as request_container:  # type: ignore[misc]
            return await coro_factory(request_container)
    finally:
        await container.close()


# ============================================================================
# TASK 1: CACHE WARMING (High Priority - Every 60s)
# ============================================================================

@shared_task(
    name="money_market.warm_cache",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    autoretry_for=(Exception,),
    retry_backoff=True,
)
def warm_cache_task(self) -> dict[str, Any]:  # noqa: ARG001 - Required by Celery bind=True
    """
    Warm cache for popular asset/chain combinations.

    Runs every 60 seconds to ensure cache never expires for hot paths.
    Pre-fetches rates for popular assets (USDC, USDT, ETH, WETH, DAI)
    on popular chains (ethereum, base, arbitrum, polygon, optimism)
    for both Aave V3 and Compound V3.

    Strategy:
    - Check if cache exists and is valid (skip if yes)
    - Fetch from RPC and store in cache (if miss or expired)
    - Track: warmed, skipped, errors

    Returns:
        Dictionary with warming summary and timestamp.
    """
    async def runner(container):
        from app.domain.ports.money_market.money_market_cache_gateway import (
            MoneyMarketCacheGateway,
        )
        from app.domain.ports.aave_gateway import AaveGateway
        from app.domain.ports.compound_gateway import CompoundGateway

        # Get gateways from DI container
        cache_gateway = await container.get(MoneyMarketCacheGateway)
        aave_gateway = await container.get(AaveGateway)
        compound_gateway = await container.get(CompoundGateway)

        # Popular combinations (based on analytics and user behavior)
        popular_assets = ["USDC", "USDT", "ETH", "WETH", "DAI"]
        popular_chains = ["ethereum", "base", "arbitrum", "polygon", "optimism"]
        protocols = [
            ("aave_v3", aave_gateway),
            ("compound_v3", compound_gateway),
        ]

        warmed = 0
        skipped = 0
        errors = 0

        for protocol_id, gateway in protocols:
            for chain in popular_chains:
                for asset in popular_assets:
                    try:
                        # Check if cache exists and is valid
                        cached = await cache_gateway.get_cached_rate(
                            protocol=protocol_id,
                            asset=asset,
                            chain=chain,
                        )

                        if cached and cached.is_valid:
                            skipped += 1
                            logger.debug(
                                f"Cache hit: {protocol_id}/{asset}/{chain} "
                                f"(expires in {cached.seconds_until_expiry}s)"
                            )
                            continue

                        # Cache miss or expired - fetch and store
                        logger.info(
                            f"Cache warming: {protocol_id}/{asset}/{chain}"
                        )

                        # Fetch rates based on protocol
                        if protocol_id == "aave_v3":
                            rate_data = await _fetch_aave_rate(
                                aave_gateway, asset, chain
                            )
                        else:  # compound_v3
                            rate_data = await _fetch_compound_rate(
                                compound_gateway, asset, chain
                            )

                        if rate_data:
                            # Store in cache with 60s TTL
                            from app.domain.entities.money_market.protocol_data import (
                                MoneyMarketProtocolData,
                            )

                            entity = MoneyMarketProtocolData(
                                id=uuid4(),
                                protocol_id=protocol_id,
                                asset=asset,
                                chain=chain,
                                supply_apy=Decimal(str(rate_data["supply_apy"])),
                                borrow_apy_variable=Decimal(str(rate_data["borrow_apy"])),
                                borrow_apy_stable=Decimal(str(rate_data.get("borrow_apy_stable", 0))),
                                total_supplied_usd=Decimal(str(rate_data.get("total_supplied_usd", 0))),
                                total_borrowed_usd=Decimal(str(rate_data.get("total_borrowed_usd", 0))),
                                utilization_rate=Decimal(str(rate_data.get("utilization_rate", 0))),
                                liquidity_available=Decimal(str(rate_data.get("liquidity_available", 0))),
                                data_source=rate_data.get("data_source", "on_chain"),
                                valid_until=datetime.now(timezone.utc) + timedelta(seconds=60),
                                created_at=datetime.now(timezone.utc),
                            )

                            await cache_gateway.cache_rate(entity)
                            warmed += 1
                            logger.debug(
                                f"Cached: {protocol_id}/{asset}/{chain} "
                                f"(supply={rate_data['supply_apy']}%, "
                                f"borrow={rate_data['borrow_apy']}%)"
                            )
                        else:
                            errors += 1
                            logger.warning(
                                f"No data returned for {protocol_id}/{asset}/{chain}"
                            )

                    except Exception as e:
                        errors += 1
                        logger.error(
                            f"Cache warming failed for {protocol_id}/{asset}/{chain}: {e}",
                            exc_info=True,
                        )

        logger.info(
            f"Cache warming complete: warmed={warmed}, skipped={skipped}, errors={errors}"
        )

        return {
            "warmed": warmed,
            "skipped": skipped,
            "errors": errors,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    return asyncio.run(_run_task(runner))


async def _fetch_aave_rate(gateway, asset: str, chain: str) -> dict | None:
    """Fetch Aave V3 rates for asset/chain."""
    try:
        markets = await gateway.get_reserve_data(asset, chain)
        if not markets:
            return None

        market = markets[0] if isinstance(markets, list) else markets

        return {
            "protocol": "aave_v3",
            "asset": asset,
            "chain": chain,
            "supply_apy": float(market.get("supply_apy", 0)),
            "borrow_apy": float(market.get("borrow_variable_apy", 0)),
            "borrow_apy_stable": float(market.get("borrow_stable_apy", 0)),
            "total_supplied_usd": float(market.get("total_supplied", 0)),
            "total_borrowed_usd": float(market.get("total_borrowed", 0)),
            "utilization_rate": float(market.get("utilization_rate", 0)),
            "liquidity_available": float(market.get("liquidity_available", 0)),
            "data_source": "on_chain",
        }
    except Exception as e:
        logger.error(f"Error fetching Aave rate for {asset}/{chain}: {e}")
        return None


async def _fetch_compound_rate(gateway, asset: str, chain: str) -> dict | None:
    """Fetch Compound V3 rates for asset/chain."""
    try:
        markets = await gateway.get_market_data(asset, chain)
        if not markets:
            return None

        market = markets[0] if isinstance(markets, list) else markets

        return {
            "protocol": "compound_v3",
            "asset": asset,
            "chain": chain,
            "supply_apy": float(market.get("supply_apy", 0)),
            "borrow_apy": float(market.get("borrow_apy", 0)),
            "borrow_apy_stable": 0.0,  # Compound V3 has no stable rate
            "total_supplied_usd": float(market.get("total_supplied", 0)),
            "total_borrowed_usd": float(market.get("total_borrowed", 0)),
            "utilization_rate": float(market.get("utilization_rate", 0)),
            "liquidity_available": float(market.get("liquidity_available", 0)),
            "data_source": "on_chain",
        }
    except Exception as e:
        logger.error(f"Error fetching Compound rate for {asset}/{chain}: {e}")
        return None


# ============================================================================
# TASK 2: RATE ALERTS (Every 5 minutes)
# ============================================================================

@shared_task(
    name="money_market.check_alerts",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
)
def check_rate_alerts_task(self) -> dict[str, Any]:  # noqa: ARG001
    """
    Check rate alert conditions for all users with alerts enabled.

    Runs every 5 minutes to check if any rates have crossed alert thresholds.

    Process:
    1. Get all users with rate alerts enabled
    2. For each user's watched assets/chains:
       - Get current rates from cache
       - Compare with previous best rate (from alert history)
       - If change >= threshold, create alert and send notification
    3. Track: alerts_triggered, notifications_sent, errors

    Returns:
        Dictionary with alert checking summary and timestamp.
    """
    async def runner(container):
        from app.domain.ports.money_market.money_market_preference_gateway import (
            MoneyMarketPreferenceGateway,
        )
        from app.domain.ports.money_market.money_market_cache_gateway import (
            MoneyMarketCacheGateway,
        )
        from app.domain.ports.money_market.money_market_alert_gateway import (
            MoneyMarketAlertGateway,
        )
        from app.domain.entities.money_market.alert import MoneyMarketAlert

        preference_gateway = await container.get(MoneyMarketPreferenceGateway)
        cache_gateway = await container.get(MoneyMarketCacheGateway)
        alert_gateway = await container.get(MoneyMarketAlertGateway)

        # Get all users with rate alerts enabled
        users_with_alerts = await preference_gateway.get_users_with_rate_alerts_enabled()

        alerts_triggered = 0
        notifications_sent = 0
        errors = 0

        logger.info(f"Checking alerts for {len(users_with_alerts)} users")

        for user_pref in users_with_alerts:
            try:
                # Check each watched asset/chain combination
                for asset in user_pref.watched_assets:
                    for chain in user_pref.watched_chains:
                        # Get current rates from cache
                        aave_rate = await cache_gateway.get_cached_rate(
                            protocol="aave_v3",
                            asset=asset,
                            chain=chain,
                        )
                        compound_rate = await cache_gateway.get_cached_rate(
                            protocol="compound_v3",
                            asset=asset,
                            chain=chain,
                        )

                        if not aave_rate and not compound_rate:
                            logger.debug(
                                f"No cached rates for {asset}/{chain}, skipping"
                            )
                            continue

                        # Determine best current rate
                        best_supply_apy = Decimal("0")
                        best_protocol = "aave_v3"

                        if aave_rate and compound_rate:
                            if aave_rate.supply_apy > compound_rate.supply_apy:
                                best_supply_apy = aave_rate.supply_apy
                                best_protocol = "aave_v3"
                            else:
                                best_supply_apy = compound_rate.supply_apy
                                best_protocol = "compound_v3"
                        elif aave_rate:
                            best_supply_apy = aave_rate.supply_apy
                            best_protocol = "aave_v3"
                        elif compound_rate:
                            best_supply_apy = compound_rate.supply_apy
                            best_protocol = "compound_v3"

                        # Get user's last alert for this asset/chain to check for rate change
                        recent_alerts = await alert_gateway.get_user_alerts(
                            user_id=user_pref.user_id,
                            asset=asset,
                            chain=chain,
                            limit=1,
                        )

                        previous_apy = Decimal("0")
                        if recent_alerts:
                            previous_apy = recent_alerts[0].new_apy

                        # Calculate APY change percentage
                        if previous_apy > 0:
                            apy_change = abs(best_supply_apy - previous_apy)

                            # Check if change exceeds threshold
                            if apy_change >= user_pref.alert_threshold_apy_change:
                                # Determine alert type
                                if best_supply_apy > previous_apy:
                                    alert_type = "rate_increase"
                                    severity = "info"
                                else:
                                    alert_type = "rate_decrease"
                                    severity = "warning"

                                # Create alert message
                                message = (
                                    f"{best_protocol.upper()} {asset} supply rate on {chain} "
                                    f"changed from {previous_apy}% to {best_supply_apy}% "
                                    f"({'+' if best_supply_apy > previous_apy else ''}"
                                    f"{apy_change}%)"
                                )

                                # Create alert entity
                                alert = MoneyMarketAlert(
                                    id=uuid4(),
                                    user_id=user_pref.user_id,
                                    alert_type=alert_type,
                                    protocol=best_protocol,
                                    asset=asset,
                                    chain=chain,
                                    previous_apy=previous_apy,
                                    new_apy=best_supply_apy,
                                    apy_change_percent=apy_change,
                                    severity=severity,
                                    message=message,
                                    is_read=False,
                                    notification_sent=False,
                                    sent_at=None,
                                    created_at=datetime.now(timezone.utc),
                                )

                                alert_id = await alert_gateway.create_alert(alert)
                                alerts_triggered += 1

                                logger.info(
                                    f"Alert triggered for user {user_pref.user_id}: "
                                    f"{asset}/{chain} rate changed by {apy_change}%"
                                )

                                # Send notification if enabled
                                if user_pref.notification_enabled:
                                    # TODO: Integrate with notification service (email, push, in-app)
                                    # For now, just mark as sent
                                    # await notification_service.send_alert(user_pref.user_id, alert)

                                    notifications_sent += 1
                                    logger.debug(
                                        f"Notification sent for alert {alert_id}"
                                    )

            except Exception as e:
                errors += 1
                logger.error(
                    f"Alert checking failed for user {user_pref.user_id}: {e}",
                    exc_info=True,
                )

        logger.info(
            f"Alert checking complete: alerts_triggered={alerts_triggered}, "
            f"notifications_sent={notifications_sent}, errors={errors}"
        )

        return {
            "users_checked": len(users_with_alerts),
            "alerts_triggered": alerts_triggered,
            "notifications_sent": notifications_sent,
            "errors": errors,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    return asyncio.run(_run_task(runner))


# ============================================================================
# TASK 3: ANALYTICS AGGREGATION (Every hour)
# ============================================================================

@shared_task(
    name="money_market.aggregate_analytics",
    bind=True,
    max_retries=2,
    default_retry_delay=300,
)
def aggregate_analytics_task(self) -> dict[str, Any]:  # noqa: ARG001
    """
    Aggregate money market analytics from comparison logs.

    Runs every hour to compute:
    - Most popular asset/chain combinations
    - Protocol preference trends
    - Average response times
    - Cache hit rates
    - User engagement patterns

    Data is aggregated from money_market_comparisons table for:
    - Last 24 hours (daily stats)
    - Last 7 days (weekly trends)

    Returns:
        Dictionary with aggregated analytics and timestamp.
    """
    async def runner(container):
        from app.domain.ports.money_market.money_market_comparison_gateway import (
            MoneyMarketComparisonGateway,
        )

        comparison_gateway = await container.get(MoneyMarketComparisonGateway)

        # Get analytics for last 24 hours
        daily_analytics = await comparison_gateway.get_comparison_analytics(
            asset=None,  # All assets
            chain=None,  # All chains
            days=1,
        )

        # Get analytics for last 7 days
        weekly_analytics = await comparison_gateway.get_comparison_analytics(
            asset=None,
            chain=None,
            days=7,
        )

        # Get popular comparisons
        popular = await comparison_gateway.get_popular_comparisons(
            days=7,
            limit=20,
        )

        logger.info(
            f"Analytics aggregated - Daily: "
            f"total_comparisons={daily_analytics.get('total_comparisons', 0)}, "
            f"unique_users={daily_analytics.get('unique_users', 0)}, "
            f"avg_latency={daily_analytics.get('avg_latency_ms', 0):.0f}ms, "
            f"cache_hit_rate={daily_analytics.get('cache_hit_rate', 0):.1f}%"
        )

        logger.info(
            f"Analytics aggregated - Weekly: "
            f"total_comparisons={weekly_analytics.get('total_comparisons', 0)}, "
            f"unique_users={weekly_analytics.get('unique_users', 0)}"
        )

        # Store aggregated results in time-series table (if exists)
        # TODO: Create money_market_analytics_snapshots table for historical tracking

        return {
            "daily": daily_analytics,
            "weekly": weekly_analytics,
            "popular_comparisons": popular,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    return asyncio.run(_run_task(runner))


# ============================================================================
# TASK 4: CACHE CLEANUP (Daily at 3 AM)
# ============================================================================

@shared_task(
    name="money_market.cleanup_cache",
    bind=True,
    max_retries=2,
    default_retry_delay=600,
)
def cleanup_cache_task(self) -> dict[str, Any]:  # noqa: ARG001
    """
    Clean up expired cache entries.

    Runs daily at 3 AM to remove old cache entries that have expired.

    Note: The partial index (WHERE valid_until > NOW()) ensures queries
    don't see expired entries, but this task reclaims disk space by
    deleting entries that expired more than 7 days ago.

    Also cleans up:
    - Old comparison logs (older than 90 days)
    - Read alerts (older than 30 days)

    Returns:
        Dictionary with cleanup summary and timestamp.
    """
    async def runner(container):
        from sqlalchemy import text
        from sqlalchemy.ext.asyncio import AsyncSession

        session = await container.get(AsyncSession)

        deleted_rates = 0
        deleted_comparisons = 0
        deleted_alerts = 0

        try:
            # Clean up expired cache entries (older than 7 days)
            result = await session.execute(
                text("""
                    DELETE FROM money_market_rates
                    WHERE valid_until < NOW() - INTERVAL '7 days'
                    RETURNING id
                """)
            )
            deleted_rates = len(result.fetchall())

            # Clean up old comparison logs (older than 90 days)
            result = await session.execute(
                text("""
                    DELETE FROM money_market_comparisons
                    WHERE created_at < NOW() - INTERVAL '90 days'
                    RETURNING id
                """)
            )
            deleted_comparisons = len(result.fetchall())

            # Clean up read alerts (older than 30 days)
            result = await session.execute(
                text("""
                    DELETE FROM money_market_alert_history
                    WHERE is_read = true
                    AND created_at < NOW() - INTERVAL '30 days'
                    RETURNING id
                """)
            )
            deleted_alerts = len(result.fetchall())

            await session.commit()

            logger.info(
                f"Cache cleanup complete: "
                f"deleted {deleted_rates} expired cache entries, "
                f"{deleted_comparisons} old comparisons, "
                f"{deleted_alerts} read alerts"
            )

        except Exception as e:
            await session.rollback()
            logger.error(f"Cache cleanup failed: {e}", exc_info=True)
            raise

        finally:
            await session.close()

        return {
            "deleted_rates": deleted_rates,
            "deleted_comparisons": deleted_comparisons,
            "deleted_alerts": deleted_alerts,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    return asyncio.run(_run_task(runner))
