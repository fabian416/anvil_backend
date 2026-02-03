"""
List Privy Policies Query

Admin query to list policies from Privy.
"""

import logging
from dataclasses import dataclass, field
from typing import Any

from app.application.commands.policy.policy_dto import PrivyPolicyDTO
from app.application.common.exceptions.authorization import AuthorizationError
from app.application.common.services.authorization.authorize import authorize
from app.application.common.services.authorization.permissions import (
    CanManageRole,
    RoleManagementContext,
)
from app.application.common.services.current_user import CurrentUserService
from app.domain.enums.user_role import UserRole
from app.infrastructure.adapters.types import MainAsyncSession
from app.infrastructure.persistence_sqla.mappings.wallet import map_wallet_tables
from app.infrastructure.persistence_sqla.repositories.policy_repository import (
    PolicyRepositorySqla,
)
from app.infrastructure.persistence_sqla.registry import mapping_registry
from app.infrastructure.privy.client import (
    PrivyClient,
    PrivyClientError,
    PrivyMethodNotAllowedError,
)
from sqlalchemy import select

logger = logging.getLogger(__name__)


class PolicyListError(Exception):
    """Error listing policies from Privy."""


@dataclass(frozen=True, slots=True)
class ListPrivyPoliciesRequest:
    cursor: str | None = None
    limit: int | None = None
    chain_type: str | None = None
    refresh: bool = False
    meta_key: str | None = None
    meta_value: str | None = None


@dataclass(frozen=True, slots=True)
class ListPrivyPoliciesResult:
    policies: list[PrivyPolicyDTO] = field(default_factory=list)
    next_cursor: str | None = None
    total_count: int | None = None
    raw: Any = None


class ListPrivyPolicies:
    __slots__ = ("_current_user_service", "_privy_client", "_session")

    def __init__(
        self,
        current_user_service: CurrentUserService,
        privy_client: PrivyClient,
        session: MainAsyncSession,
    ) -> None:
        self._current_user_service = current_user_service
        self._privy_client = privy_client
        self._session = session

    async def _list_policy_ids_from_db(self) -> list[str]:
        """
        Fallback: list policy IDs observed on locally persisted wallets.

        We store `policy_ids` on the wallets table, so we can build a best-effort list
        of policies even if Privy doesn't support `GET /v1/policies` (list).
        """
        map_wallet_tables()
        wallets_table = mapping_registry.metadata.tables["wallets"]

        stmt = select(wallets_table.c.policy_ids).where(
            wallets_table.c.policy_ids.is_not(None)
        )  # type: ignore[attr-defined]
        result = await self._session.execute(stmt)
        rows = result.scalars().all()

        seen: set[str] = set()
        ordered: list[str] = []
        for policy_ids in rows:
            if not isinstance(policy_ids, list):
                continue
            for policy_id in policy_ids:
                if not isinstance(policy_id, str) or not policy_id:
                    continue
                if policy_id in seen:
                    continue
                seen.add(policy_id)
                ordered.append(policy_id)

        return ordered

    async def execute(
        self, request: ListPrivyPoliciesRequest
    ) -> ListPrivyPoliciesResult:
        current_user = await self._current_user_service.get_current_user()
        authorize(
            CanManageRole(),
            context=RoleManagementContext(
                subject=current_user, target_role=UserRole.USER
            ),
        )

        actor_user_id = (
            getattr(current_user, "id_", None).value
            if getattr(current_user, "id_", None)
            else None
        )
        repo = PolicyRepositorySqla(self._session)

        # Our API already uses a string cursor; for DB we interpret it as an offset.
        start = 0
        if request.cursor:
            try:
                start = max(0, int(request.cursor))
            except ValueError:
                start = 0

        page_size = request.limit or 50

        if not request.refresh:
            cached_rows = await repo.list_policies(
                offset=start,
                limit=page_size,
                chain_type=request.chain_type,
                meta_key=request.meta_key,
                meta_value=request.meta_value,
            )
            if cached_rows:
                policies = [
                    PrivyPolicyDTO(
                        id=str(r.get("id", "")),
                        name=str(r.get("name", "")),
                        version=str(r.get("version", "")),
                        chain_type=str(r.get("chain_type", "")),
                        rules=list(r.get("rules", []) or []),
                        owner_id=r.get("owner_id"),
                    )
                    for r in cached_rows
                ]
                next_cursor = (
                    str(start + page_size) if len(cached_rows) == page_size else None
                )
                return ListPrivyPoliciesResult(
                    policies=policies,
                    next_cursor=next_cursor,
                    total_count=None,
                    raw={"source": "db"},
                )

        try:
            data = await self._privy_client.list_policies(
                cursor=request.cursor,
                limit=request.limit,
                chain_type=request.chain_type,
            )

            # Normalize: Privy may return {"data": [...], "next_cursor": "..."} or a raw list
            policies: list[PrivyPolicyDTO]
            raw_list: list[dict[str, Any]] = []
            next_cursor: str | None = None
            total_count: int | None = None

            if isinstance(data, list):
                policies = [
                    PrivyPolicyDTO.from_api(p) for p in data if isinstance(p, dict)
                ]
                raw_list = [p for p in data if isinstance(p, dict)]
            elif isinstance(data, dict):
                policies_raw = data.get("data")
                if isinstance(policies_raw, list):
                    policies = [
                        PrivyPolicyDTO.from_api(p)
                        for p in policies_raw
                        if isinstance(p, dict)
                    ]
                    raw_list = [p for p in policies_raw if isinstance(p, dict)]
                else:
                    policies = []
                next_cursor = data.get("next_cursor")
                total_count = data.get("total_count")
            else:
                policies = []

            # Persist for cache/audit (best effort).
            for p_raw in raw_list:
                dto = PrivyPolicyDTO.from_api(p_raw)
                try:
                    await repo.upsert_from_privy(
                        policy=dto,
                        privy_raw=p_raw,
                        actor_user_id=actor_user_id,
                        action="sync_list",
                        extra_audit_payload={"source": "privy"},
                    )
                except Exception:
                    # Don't fail the list call if persistence fails.
                    logger.exception(
                        "ListPrivyPolicies: failed to upsert policy_id=%s", dto.id
                    )

            result = ListPrivyPoliciesResult(
                policies=policies,
                next_cursor=next_cursor,
                total_count=total_count,
                raw=data,
            )
            logger.info("ListPrivyPolicies: returned %s policies", len(result.policies))
            return result
        except PrivyMethodNotAllowedError:
            # Privy sometimes does not expose a "list policies" endpoint for an app.
            # Fallback: use locally observed `policy_ids` from wallets, then fetch each policy.
            policy_ids = await self._list_policy_ids_from_db()

            page_policy_ids = policy_ids[start : start + page_size]
            next_cursor = (
                str(start + page_size)
                if (start + page_size) < len(policy_ids)
                else None
            )

            policies: list[PrivyPolicyDTO] = []
            raw: dict[str, Any] = {
                "source": "db_wallet_policy_ids",
                "policy_ids": page_policy_ids,
            }
            for policy_id in page_policy_ids:
                try:
                    policy_raw = await self._privy_client.get_policy(policy_id)
                    dto = PrivyPolicyDTO.from_api(policy_raw)
                    policies.append(dto)
                    try:
                        await repo.upsert_from_privy(
                            policy=dto,
                            privy_raw=policy_raw
                            if isinstance(policy_raw, dict)
                            else {"raw": policy_raw},
                            actor_user_id=actor_user_id,
                            action="sync_get",
                            extra_audit_payload={
                                "source": "privy",
                                "fallback": "db_wallet_policy_ids",
                            },
                        )
                    except Exception:
                        logger.exception(
                            "ListPrivyPolicies fallback: failed to upsert %s",
                            policy_id,
                        )
                except PrivyClientError as e:
                    # Best effort: skip policies we can't fetch (deleted, auth mismatch, etc.).
                    logger.warning(
                        "ListPrivyPolicies fallback: failed to fetch %s: %s",
                        policy_id,
                        e,
                    )

            return ListPrivyPoliciesResult(
                policies=policies,
                next_cursor=next_cursor,
                total_count=len(policy_ids),
                raw=raw,
            )
        except PrivyClientError as e:
            raise PolicyListError(str(e)) from e
        except Exception as e:
            if isinstance(e, (AuthorizationError, PolicyListError)):
                raise
            raise PolicyListError(str(e)) from e
