"""SQLAlchemy repository for persisted Privy policies."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.dialects.postgresql import insert

from app.application.commands.policy.policy_dto import PrivyPolicyDTO
from app.infrastructure.adapters.types import MainAsyncSession
from app.infrastructure.persistence_sqla.mappings.policy import map_policy_tables
from app.infrastructure.persistence_sqla.registry import mapping_registry


class PolicyRepositorySqla:
    def __init__(self, session: MainAsyncSession) -> None:
        self._session = session

    def _tables(self):
        map_policy_tables()
        policies = mapping_registry.metadata.tables["policies"]
        events = mapping_registry.metadata.tables["policy_audit_events"]
        return policies, events

    async def get_policy(self, policy_id: str) -> dict[str, Any] | None:
        policies, _ = self._tables()
        stmt = select(policies).where(
            and_(
                policies.c.id == policy_id,  # type: ignore[attr-defined]
                policies.c.is_deleted.is_(False),  # type: ignore[attr-defined]
            )
        )
        result = await self._session.execute(stmt)
        row = result.mappings().one_or_none()
        return dict(row) if row else None

    async def list_policies(
        self,
        *,
        offset: int,
        limit: int,
        chain_type: str | None = None,
        meta_key: str | None = None,
        meta_value: str | None = None,
        include_deleted: bool = False,
    ) -> list[dict[str, Any]]:
        policies, _ = self._tables()
        stmt = select(policies)

        if not include_deleted:
            stmt = stmt.where(policies.c.is_deleted.is_(False))  # type: ignore[attr-defined]

        if chain_type:
            stmt = stmt.where(policies.c.chain_type == chain_type)  # type: ignore[attr-defined]

        if meta_key:
            # JSONB existence / equality checks
            if meta_value is None:
                stmt = stmt.where(policies.c.metadata.has_key(meta_key))  # type: ignore[attr-defined]  # noqa: E711
            else:
                stmt = stmt.where(policies.c.metadata[meta_key].astext == meta_value)  # type: ignore[attr-defined]

        stmt = (
            stmt.order_by(policies.c.created_at.desc())  # type: ignore[attr-defined]
            .offset(offset)
            .limit(limit)
        )

        result = await self._session.execute(stmt)
        rows = result.mappings().all()
        return [dict(r) for r in rows]

    async def upsert_from_privy(
        self,
        *,
        policy: PrivyPolicyDTO,
        privy_raw: dict[str, Any],
        actor_user_id: int | None,
        action: str,
        metadata: dict[str, Any] | None = None,
        extra_audit_payload: dict[str, Any] | None = None,
    ) -> None:
        policies, events = self._tables()

        now = datetime.now(timezone.utc)

        insert_values: dict[str, Any] = {
            "id": policy.id,
            "name": policy.name,
            "version": policy.version,
            "chain_type": policy.chain_type,
            "owner_id": policy.owner_id,
            "rules": policy.rules,
            "privy_raw": privy_raw,
            "is_deleted": False,
            "last_privy_sync_at": now,
            "created_by_user_id": actor_user_id,
            "updated_by_user_id": actor_user_id,
            "updated_at": now,
        }
        if metadata is not None:
            insert_values["metadata"] = metadata

        # Preserve metadata/created_by/created_at on conflict unless explicitly provided.
        set_values: dict[str, Any] = {
            "name": insert_values["name"],
            "version": insert_values["version"],
            "chain_type": insert_values["chain_type"],
            "owner_id": insert_values["owner_id"],
            "rules": insert_values["rules"],
            "privy_raw": insert_values["privy_raw"],
            "is_deleted": False,
            "last_privy_sync_at": insert_values["last_privy_sync_at"],
            "updated_by_user_id": actor_user_id,
            "updated_at": insert_values["updated_at"],
        }
        if metadata is not None:
            set_values["metadata"] = metadata

        stmt = insert(policies).values(**insert_values)
        stmt = stmt.on_conflict_do_update(index_elements=["id"], set_=set_values)
        await self._session.execute(stmt)

        audit_payload: dict[str, Any] = {
            "policy": asdict(policy),
            "privy_raw": privy_raw,
        }
        if metadata is not None:
            audit_payload["metadata"] = metadata
        if extra_audit_payload:
            audit_payload.update(extra_audit_payload)

        await self._session.execute(
            insert(events).values(
                policy_id=policy.id,
                actor_user_id=actor_user_id,
                action=action,
                payload=audit_payload,
                created_at=func.current_timestamp(),
            )
        )

        await self._session.commit()
