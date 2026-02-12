from datetime import datetime, timedelta, UTC
from inspect import getdoc
from typing import Any, Optional

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Header, Security, status
from fastapi_error_map import ErrorAwareRouter, rule
from sqlalchemy import insert

from app.application.common.services.current_user import CurrentUserService
from app.domain.transactions.ports.transaction.transaction_repository import (
    TransactionRepository,
)
from app.domain.value_objects.user_id import UserId
from app.domain.enums.transaction_type import TransactionType
from app.infrastructure.adapters.types import MainAsyncSession
from app.infrastructure.auth.handlers.account_me import (
    GetMeHandler,
    MeResponse,
    UpdateMeHandler,
    UpdateMeRequest,
)
from app.infrastructure.auth.exceptions import AuthenticationError
from app.infrastructure.exceptions.gateway import DataMapperError
from app.presentation.http.auth.fastapi_openapi_markers import bearer_scheme
from app.presentation.http.errors.callbacks import log_error, log_info
from app.presentation.http.errors.translators import ServiceUnavailableTranslator


def create_me_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.get(
        "/me",
        description="Get current authenticated user's profile",
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            DataMapperError: rule(
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
                translator=ServiceUnavailableTranslator(),
                on_error=log_error,
            ),
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
        dependencies=[Security(bearer_scheme)],
    )
    @inject
    async def get_me(handler: FromDishka[GetMeHandler]) -> MeResponse:
        return await handler.execute()

    @router.put(
        "/me",
        description="Update current authenticated user's profile",
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            DataMapperError: rule(
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
                translator=ServiceUnavailableTranslator(),
                on_error=log_error,
            ),
            ValueError: status.HTTP_400_BAD_REQUEST,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
        dependencies=[Security(bearer_scheme)],
    )
    @inject
    async def update_me(
        req: UpdateMeRequest,
        handler: FromDishka[UpdateMeHandler],
    ) -> MeResponse:
        return await handler.execute(req)

    @router.get(
        "/me/sync-status",
        description="Sync status for current user (Celery swap-intent watcher & recent-user sync)",
        status_code=status.HTTP_200_OK,
        dependencies=[Security(bearer_scheme)],
    )
    @inject
    async def get_sync_status(
        current_user: FromDishka[CurrentUserService],
        session: FromDishka[MainAsyncSession],
        tx_repo: FromDishka[TransactionRepository],
    ) -> dict[str, Any]:
        """Return Celery-related sync data for the authenticated user (for debugging 'my swaps')."""
        from sqlalchemy import select, func
        from app.infrastructure.persistence_sqla.registry import mapping_registry
        from app.infrastructure.persistence_sqla.mappings.swap_intent_mapping import (
            map_swap_intents_table,
        )
        from app.infrastructure.persistence_sqla.mappings.user_sync_schedule_mapping import (
            map_user_sync_schedule_table,
        )

        user = await current_user.get_current_user()
        user_id = user.id_.value

        map_swap_intents_table()
        map_user_sync_schedule_table()
        swap_intents_table = mapping_registry.metadata.tables.get("swap_intents")
        schedule_table = mapping_registry.metadata.tables.get("user_sync_schedule")

        user_sync_schedule: dict[str, Any] | None = None
        swap_intents_pending = 0
        swap_intents_completed = 0

        if schedule_table:
            row = await session.execute(
                select(schedule_table).where(schedule_table.c.user_id == user_id)
            )
            r = row.first()
            if r:
                user_sync_schedule = {
                    "next_sync_at": r.next_sync_at.isoformat() if r.next_sync_at else None,
                    "interval_index": r.interval_index,
                    "last_synced_at": r.last_synced_at.isoformat() if r.last_synced_at else None,
                }

        if swap_intents_table:
            cnt_p = await session.execute(
                select(func.count()).select_from(swap_intents_table).where(
                    swap_intents_table.c.user_id == user_id,
                    swap_intents_table.c.status == "pending",
                )
            )
            swap_intents_pending = cnt_p.scalar() or 0
            cnt_c = await session.execute(
                select(func.count()).select_from(swap_intents_table).where(
                    swap_intents_table.c.user_id == user_id,
                    swap_intents_table.c.status == "completed",
                )
            )
            swap_intents_completed = cnt_c.scalar() or 0

        swap_count = await tx_repo.count_by_user_id(
            UserId(user_id),
            tx_type=TransactionType.SWAP,
        )

        return {
            "user_id": user_id,
            "user_sync_schedule": user_sync_schedule,
            "swap_intents_pending": swap_intents_pending,
            "swap_intents_completed": swap_intents_completed,
            "transactions_swap_count": swap_count,
            "note": "Celery tasks: swap_intent.check_pending (every 2 min), recent_user_sync.incremental (every 1 min). 'My swaps' shows data from transactions table (type=SWAP).",
        }

    @router.post(
        "/me/sync-now",
        description="Trigger sync now for current user (Celery) and ensure they are in the incremental schedule",
        status_code=status.HTTP_200_OK,
        dependencies=[Security(bearer_scheme)],
    )
    @inject
    async def post_sync_now(
        current_user: FromDishka[CurrentUserService],
        session: FromDishka[MainAsyncSession],
    ) -> dict[str, Any]:
        """Upsert user_sync_schedule so user is in the rotation, then enqueue recent_user_sync.sync_user to run without waiting."""
        from app.infrastructure.celery.tasks.recent_user_sync_tasks import sync_single_user
        from app.infrastructure.persistence_sqla.mappings.user_sync_schedule_mapping import (
            map_user_sync_schedule_table,
        )
        from app.infrastructure.persistence_sqla.registry import mapping_registry

        user = await current_user.get_current_user()
        user_id = user.id_.value

        map_user_sync_schedule_table()
        schedule_table = mapping_registry.metadata.tables.get("user_sync_schedule")
        if schedule_table is None:
            return {
                "message": "Schedule table not available",
                "user_id": user_id,
                "task_triggered": False,
            }

        now_utc = datetime.now(UTC)
        next_sync_at = now_utc + timedelta(minutes=1)
        await session.execute(
            insert(schedule_table)
            .values(
                user_id=user_id,
                next_sync_at=next_sync_at,
                interval_index=0,
                last_synced_at=None,
                created_at=now_utc,
                updated_at=now_utc,
            )
            .on_conflict_do_update(
                index_elements=["user_id"],
                set_={
                    "next_sync_at": next_sync_at,
                    "interval_index": 0,
                    "updated_at": now_utc,
                },
            )
        )
        await session.commit()

        sync_single_user.delay(user_id)

        return {
            "message": "Sync triggered",
            "user_id": user_id,
            "task_triggered": True,
            "note": "recent_user_sync.sync_user runs in Celery; you remain in the incremental schedule.",
        }

    return router
