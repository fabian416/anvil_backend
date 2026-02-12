"""
Hyperliquid Spot Token Catalog — Celery tasks for seeding + sentiment enrichment.

Two independent tasks:

1. **seed_hl_spot_tokens** (every 24h):
   - Calls Hyperliquid spotMeta API (FREE, no key)
   - Inserts new tokens with status='pending'
   - Updates existing tokens' metadata (decimals, etc.)

2. **enrich_hl_spot_token_sentiment** (every 1 min):
   - Picks 1 token with oldest sentiment_updated_at (>1h) or status='pending'
   - Runs AssetSentimentService.get_sentiment() (news-based, ~5s)
   - Updates sentiment fields in hl_spot_tokens
   - Rotation ensures all tokens get enriched without API exhaustion
   - ~60 tokens / 60 min = full rotation every hour
"""

import asyncio
import logging
from datetime import datetime, UTC, timedelta
from typing import Any

from app.infrastructure.celery.app import celery_app

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════
# Task 1: Seed tokens from Hyperliquid spotMeta (every 24h)
# ═══════════════════════════════════════════════════════════════════════


@celery_app.task(
    name="hl_spot_tokens.seed",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
    acks_late=True,
)
def seed_hl_spot_tokens(self) -> dict[str, Any]:
    """
    Fetch ALL spot tokens from Hyperliquid and upsert into hl_spot_tokens.

    New tokens get status='pending' so the enrich task picks them up.
    Existing tokens get their metadata updated but sentiment is preserved.
    """

    async def runner(container):
        from sqlalchemy import text as sa_text
        from sqlalchemy.ext.asyncio import AsyncSession

        from app.infrastructure.adapters.types import MainAsyncSession
        from app.infrastructure.adapters.external.hyperliquid_client import (
            HyperliquidClient,
        )

        session: AsyncSession = await container.get(MainAsyncSession)
        now = datetime.now(UTC)
        stats = {"inserted": 0, "updated": 0, "total_api": 0, "errors": 0}

        hl_client = HyperliquidClient(testnet=False)
        try:
            tokens = await hl_client.get_spot_tokens()
            stats["total_api"] = len(tokens)
            logger.info(
                "[HlSpotTokens] Fetched %d tokens from spotMeta", len(tokens)
            )

            # Build set of base-token names that have an active Core spot
            # market (present in spotMeta.universe).  EVM-only tokens are
            # excluded — they cannot be traded via the API.
            spot_meta = await hl_client.get_spot_meta()
            tradeable_names: set[str] = {
                m.base_token.upper() for m in spot_meta
            }
            logger.info(
                "[HlSpotTokens] %d tokens have active spot markets",
                len(tradeable_names),
            )

            for token in tokens:
                try:
                    # Check if token already exists
                    existing = await session.execute(
                        sa_text(
                            "SELECT id, status FROM hl_spot_tokens WHERE name = :name"
                        ),
                        {"name": token.name},
                    )
                    row = existing.first()

                    has_market = token.name.upper() in tradeable_names

                    if row is None:
                        # New token → insert with status='pending'
                        await session.execute(
                            sa_text("""
                                INSERT INTO hl_spot_tokens
                                    (name, token_id, token_index, sz_decimals,
                                     wei_decimals, is_canonical, has_spot_market,
                                     status, created_at, updated_at)
                                VALUES
                                    (:name, :token_id, :idx, :sz_dec,
                                     :wei_dec, :is_canon, :has_market,
                                     'pending', :now, :now)
                            """),
                            {
                                "name": token.name,
                                "token_id": token.token_id,
                                "idx": token.index,
                                "sz_dec": token.sz_decimals,
                                "wei_dec": token.wei_decimals,
                                "is_canon": token.is_canonical,
                                "has_market": has_market,
                                "now": now,
                            },
                        )
                        stats["inserted"] += 1
                    else:
                        # Existing token → update metadata only (preserve sentiment)
                        await session.execute(
                            sa_text("""
                                UPDATE hl_spot_tokens
                                SET token_id = :token_id,
                                    token_index = :idx,
                                    sz_decimals = :sz_dec,
                                    wei_decimals = :wei_dec,
                                    is_canonical = :is_canon,
                                    has_spot_market = :has_market,
                                    updated_at = :now
                                WHERE name = :name
                            """),
                            {
                                "name": token.name,
                                "token_id": token.token_id,
                                "idx": token.index,
                                "sz_dec": token.sz_decimals,
                                "wei_dec": token.wei_decimals,
                                "is_canon": token.is_canonical,
                                "has_market": has_market,
                                "now": now,
                            },
                        )
                        stats["updated"] += 1

                except Exception as e:
                    logger.warning(
                        "[HlSpotTokens] Error upserting %s: %s", token.name, e
                    )
                    stats["errors"] += 1
                    await session.rollback()

            await session.commit()

        finally:
            await hl_client.close()

        logger.info(
            "[HlSpotTokens] Seed done: %d from API, %d inserted, %d updated, %d errors",
            stats["total_api"],
            stats["inserted"],
            stats["updated"],
            stats["errors"],
        )
        return stats

    return asyncio.run(_run_with_container(runner))


# ═══════════════════════════════════════════════════════════════════════
# Task 2: Enrich ONE token with sentiment (every 1 min, rotating)
# ═══════════════════════════════════════════════════════════════════════

# Tokens older than this get re-enriched
SENTIMENT_STALE_HOURS = 1


@celery_app.task(
    name="hl_spot_tokens.enrich_sentiment",
    bind=True,
    max_retries=1,
    default_retry_delay=30,
    acks_late=True,
)
def enrich_hl_spot_token_sentiment(self) -> dict[str, Any]:
    """
    Pick ONE token that needs sentiment enrichment and run analysis.

    Selection priority:
    1. status='pending' (never enriched) — oldest first
    2. sentiment_updated_at < NOW() - 1 hour (stale) — oldest first

    This ensures:
    - New tokens get enriched within minutes of being seeded
    - All tokens rotate through enrichment every ~1 hour
    - Only 1 API call per minute → no rate limit exhaustion
    """

    async def runner(container):
        from sqlalchemy import text as sa_text
        from sqlalchemy.ext.asyncio import AsyncSession

        from app.infrastructure.adapters.types import MainAsyncSession
        from app.application.hunter.asset_sentiment_service import (
            AssetSentimentService,
        )

        session: AsyncSession = await container.get(MainAsyncSession)
        now = datetime.now(UTC)
        stale_cutoff = now - timedelta(hours=SENTIMENT_STALE_HOURS)
        stats: dict[str, Any] = {
            "token": None,
            "status": "no_token",
            "sentiment": None,
        }

        # ── Pick the next token to enrich ──
        # Only enrich tokens with an active Core spot market (tradeable).
        # EVM-only tokens are skipped to avoid wasting API calls.
        # Priority: pending first (NULLS FIRST), then oldest sentiment_updated_at
        result = await session.execute(
            sa_text("""
                SELECT id, name, status
                FROM hl_spot_tokens
                WHERE has_spot_market = true
                AND status IN ('pending', 'enriched', 'error')
                AND (
                    status = 'pending'
                    OR sentiment_updated_at IS NULL
                    OR sentiment_updated_at < :stale_cutoff
                )
                ORDER BY
                    CASE WHEN status = 'pending' THEN 0 ELSE 1 END,
                    sentiment_updated_at ASC NULLS FIRST
                LIMIT 1
            """),
            {"stale_cutoff": stale_cutoff},
        )
        row = result.first()

        if row is None:
            logger.debug("[HlSpotTokens] No tokens need enrichment right now")
            stats["status"] = "all_fresh"
            return stats

        token_id_db = row[0]
        token_name = row[1]
        stats["token"] = token_name

        logger.info("[HlSpotTokens] Enriching sentiment for: %s", token_name)

        # ── Run sentiment analysis ──
        sentiment_service = AssetSentimentService(timeout_seconds=10.0)
        try:
            sentiment = await sentiment_service.get_sentiment(token_name)
        except Exception as e:
            logger.warning(
                "[HlSpotTokens] Sentiment failed for %s: %s", token_name, e
            )
            # Mark as error so it gets retried later
            await session.execute(
                sa_text("""
                    UPDATE hl_spot_tokens
                    SET status = 'error',
                        sentiment_updated_at = :now,
                        updated_at = :now
                    WHERE id = :tid
                """),
                {"tid": token_id_db, "now": now},
            )
            await session.commit()
            stats["status"] = "error"
            return stats

        if sentiment is None:
            # No sentiment available (timeout, no news, etc.)
            logger.debug(
                "[HlSpotTokens] No sentiment data for %s", token_name
            )
            await session.execute(
                sa_text("""
                    UPDATE hl_spot_tokens
                    SET status = 'enriched',
                        sentiment_score = NULL,
                        sentiment_classification = 'neutral',
                        sentiment_interpretation = 'no data available',
                        sentiment_confidence = NULL,
                        sentiment_source = 'none',
                        sentiment_time_horizon = '24h',
                        sentiment_updated_at = :now,
                        updated_at = :now
                    WHERE id = :tid
                """),
                {"tid": token_id_db, "now": now},
            )
            await session.commit()
            stats["status"] = "enriched_no_data"
            return stats

        # ── Update sentiment fields ──
        await session.execute(
            sa_text("""
                UPDATE hl_spot_tokens
                SET status = 'enriched',
                    sentiment_score = :score,
                    sentiment_classification = :classification,
                    sentiment_interpretation = :interpretation,
                    sentiment_confidence = :confidence,
                    sentiment_source = :source,
                    sentiment_time_horizon = :time_horizon,
                    sentiment_updated_at = :now,
                    updated_at = :now
                WHERE id = :tid
            """),
            {
                "tid": token_id_db,
                "score": sentiment.get("score"),
                "classification": sentiment.get("classification", "neutral"),
                "interpretation": sentiment.get("interpretation", ""),
                "confidence": sentiment.get("confidence"),
                "source": sentiment.get("source", "news"),
                "time_horizon": sentiment.get("time_horizon", "24h"),
                "now": now,
            },
        )
        await session.commit()

        stats["status"] = "enriched"
        stats["sentiment"] = sentiment
        logger.info(
            "[HlSpotTokens] Enriched %s: score=%.1f, %s",
            token_name,
            sentiment.get("score", 0),
            sentiment.get("classification", "?"),
        )
        return stats

    return asyncio.run(_run_with_container(runner))


async def _run_with_container(coro_factory):
    """Run async task with Dishka IOC container."""
    from app.infrastructure.celery.helpers import _run_task

    return await _run_task(coro_factory)
