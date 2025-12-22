"""
Get Privy Policy Query

Admin query to retrieve a policy from Privy.
"""

import logging

from dataclasses import dataclass

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
from app.infrastructure.persistence_sqla.repositories.policy_repository import (
    PolicyRepositorySqla,
)
from app.infrastructure.privy.client import (
    PrivyClient,
    PrivyClientError,
    PrivyPolicyNotFoundError,
)

logger = logging.getLogger(__name__)


class PolicyNotFoundError(Exception):
    """Policy not found."""


class PolicyQueryError(Exception):
    """Error fetching a policy from Privy."""


@dataclass(frozen=True, slots=True)
class GetPrivyPolicyRequest:
    policy_id: str


class GetPrivyPolicy:
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

    async def execute(self, request: GetPrivyPolicyRequest) -> PrivyPolicyDTO:
        current_user = await self._current_user_service.get_current_user()
        authorize(
            CanManageRole(),
            context=RoleManagementContext(subject=current_user, target_role=UserRole.USER),
        )

        repo = PolicyRepositorySqla(self._session)
        cached = await repo.get_policy(request.policy_id)
        if cached:
            policy = PrivyPolicyDTO(
                id=str(cached.get("id", "")),
                name=str(cached.get("name", "")),
                version=str(cached.get("version", "")),
                chain_type=str(cached.get("chain_type", "")),
                rules=list(cached.get("rules", []) or []),
                owner_id=cached.get("owner_id"),
            )
            logger.info("GetPrivyPolicy: cache hit policy_id=%s", policy.id)
            return policy

        try:
            data = await self._privy_client.get_policy(request.policy_id)
            policy = PrivyPolicyDTO.from_api(data)
            actor_user_id = getattr(current_user, "id_", None).value if getattr(current_user, "id_", None) else None
            await repo.upsert_from_privy(
                policy=policy,
                privy_raw=data if isinstance(data, dict) else {"raw": data},
                actor_user_id=actor_user_id,
                action="sync_get",
                extra_audit_payload={"source": "privy", "cache": "miss"},
            )
            logger.info("GetPrivyPolicy: fetched+cached policy_id=%s", policy.id)
            return policy
        except PrivyPolicyNotFoundError as e:
            raise PolicyNotFoundError(str(e)) from e
        except PrivyClientError as e:
            raise PolicyQueryError(str(e)) from e
        except Exception as e:
            if isinstance(e, (AuthorizationError, PolicyNotFoundError, PolicyQueryError)):
                raise
            raise PolicyQueryError(str(e)) from e

