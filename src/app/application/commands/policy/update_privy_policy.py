"""
Update Privy Policy Command

Admin command to update a policy in Privy.
"""

import logging
from dataclasses import dataclass
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
from app.infrastructure.persistence_sqla.repositories.policy_repository import (
    PolicyRepositorySqla,
)
from app.infrastructure.privy.client import (
    PrivyClient,
    PrivyClientError,
    PrivyPolicyNotFoundError,
)

logger = logging.getLogger(__name__)


class PolicyUpdateError(Exception):
    """Error updating a policy in Privy."""


class PolicyNotFoundError(Exception):
    """Policy not found."""


@dataclass(frozen=True, slots=True)
class UpdatePrivyPolicyRequest:
    policy_id: str
    name: str | None = None
    rules: list[dict[str, Any]] | None = None
    authorization_signature: str | None = None
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class UpdatePrivyPolicyResult:
    policy: PrivyPolicyDTO


class UpdatePrivyPolicy:
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

    async def execute(
        self, request: UpdatePrivyPolicyRequest
    ) -> UpdatePrivyPolicyResult:
        current_user = await self._current_user_service.get_current_user()
        authorize(
            CanManageRole(),
            context=RoleManagementContext(
                subject=current_user, target_role=UserRole.USER
            ),
        )

        try:
            data = await self._privy_client.update_policy(
                request.policy_id,
                name=request.name,
                rules=request.rules,
                authorization_signature=request.authorization_signature,
            )
            policy = PrivyPolicyDTO.from_api(data)
            actor_user_id = (
                getattr(current_user, "id_", None).value
                if getattr(current_user, "id_", None)
                else None
            )

            repo = PolicyRepositorySqla(self._session)
            await repo.upsert_from_privy(
                policy=policy,
                privy_raw=data if isinstance(data, dict) else {"raw": data},
                actor_user_id=actor_user_id,
                action="update",
                metadata=request.metadata,
                extra_audit_payload={"source": "privy"},
            )
            logger.info("UpdatePrivyPolicy: updated policy_id=%s", policy.id)
            return UpdatePrivyPolicyResult(policy=policy)
        except PrivyPolicyNotFoundError as e:
            raise PolicyNotFoundError(str(e)) from e
        except PrivyClientError as e:
            raise PolicyUpdateError(str(e)) from e
        except Exception as e:
            if isinstance(
                e, (AuthorizationError, PolicyNotFoundError, PolicyUpdateError)
            ):
                raise
            raise PolicyUpdateError(str(e)) from e
