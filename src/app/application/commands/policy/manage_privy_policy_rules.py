"""
Manage Privy Policy Rules

Admin commands to create/update/delete individual policy rules in Privy.
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


class PolicyRuleOperationError(Exception):
    """Error during a policy rule operation."""


class PolicyNotFoundError(Exception):
    """Policy or rule not found."""


@dataclass(frozen=True, slots=True)
class CreatePrivyPolicyRuleRequest:
    policy_id: str
    rule: dict[str, Any]
    authorization_signature: str | None = None


@dataclass(frozen=True, slots=True)
class UpdatePrivyPolicyRuleRequest:
    policy_id: str
    rule_id: str
    rule: dict[str, Any]
    authorization_signature: str | None = None


@dataclass(frozen=True, slots=True)
class DeletePrivyPolicyRuleRequest:
    policy_id: str
    rule_id: str
    authorization_signature: str | None = None


class CreatePrivyPolicyRule:
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

    async def execute(self, request: CreatePrivyPolicyRuleRequest) -> dict[str, Any]:
        current_user = await self._current_user_service.get_current_user()
        authorize(
            CanManageRole(),
            context=RoleManagementContext(
                subject=current_user, target_role=UserRole.USER
            ),
        )
        try:
            result = await self._privy_client.create_policy_rule(
                request.policy_id,
                rule=request.rule,
                authorization_signature=request.authorization_signature,
            )
            # Refresh cached policy snapshot (best effort).
            try:
                policy_raw = await self._privy_client.get_policy(request.policy_id)
                dto = PrivyPolicyDTO.from_api(policy_raw)
                actor_user_id = (
                    getattr(current_user, "id_", None).value
                    if getattr(current_user, "id_", None)
                    else None
                )
                repo = PolicyRepositorySqla(self._session)
                await repo.upsert_from_privy(
                    policy=dto,
                    privy_raw=policy_raw
                    if isinstance(policy_raw, dict)
                    else {"raw": policy_raw},
                    actor_user_id=actor_user_id,
                    action="rule_create",
                    extra_audit_payload={"rule_result": result},
                )
            except Exception:
                logger.exception(
                    "CreatePrivyPolicyRule: failed to refresh cached policy_id=%s",
                    request.policy_id,
                )
            logger.info(
                "CreatePrivyPolicyRule: policy_id=%s rule_id=%s",
                request.policy_id,
                result.get("id"),
            )
            return result
        except PrivyPolicyNotFoundError as e:
            raise PolicyNotFoundError(str(e)) from e
        except PrivyClientError as e:
            raise PolicyRuleOperationError(str(e)) from e
        except Exception as e:
            if isinstance(
                e, (AuthorizationError, PolicyNotFoundError, PolicyRuleOperationError)
            ):
                raise
            raise PolicyRuleOperationError(str(e)) from e


class UpdatePrivyPolicyRule:
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

    async def execute(self, request: UpdatePrivyPolicyRuleRequest) -> dict[str, Any]:
        current_user = await self._current_user_service.get_current_user()
        authorize(
            CanManageRole(),
            context=RoleManagementContext(
                subject=current_user, target_role=UserRole.USER
            ),
        )
        try:
            result = await self._privy_client.update_policy_rule(
                request.policy_id,
                request.rule_id,
                rule=request.rule,
                authorization_signature=request.authorization_signature,
            )
            # Refresh cached policy snapshot (best effort).
            try:
                policy_raw = await self._privy_client.get_policy(request.policy_id)
                dto = PrivyPolicyDTO.from_api(policy_raw)
                actor_user_id = (
                    getattr(current_user, "id_", None).value
                    if getattr(current_user, "id_", None)
                    else None
                )
                repo = PolicyRepositorySqla(self._session)
                await repo.upsert_from_privy(
                    policy=dto,
                    privy_raw=policy_raw
                    if isinstance(policy_raw, dict)
                    else {"raw": policy_raw},
                    actor_user_id=actor_user_id,
                    action="rule_update",
                    extra_audit_payload={
                        "rule_result": result,
                        "rule_id": request.rule_id,
                    },
                )
            except Exception:
                logger.exception(
                    "UpdatePrivyPolicyRule: failed to refresh cached policy_id=%s",
                    request.policy_id,
                )
            logger.info(
                "UpdatePrivyPolicyRule: policy_id=%s rule_id=%s",
                request.policy_id,
                request.rule_id,
            )
            return result
        except PrivyPolicyNotFoundError as e:
            raise PolicyNotFoundError(str(e)) from e
        except PrivyClientError as e:
            raise PolicyRuleOperationError(str(e)) from e
        except Exception as e:
            if isinstance(
                e, (AuthorizationError, PolicyNotFoundError, PolicyRuleOperationError)
            ):
                raise
            raise PolicyRuleOperationError(str(e)) from e


class DeletePrivyPolicyRule:
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

    async def execute(self, request: DeletePrivyPolicyRuleRequest) -> dict[str, Any]:
        current_user = await self._current_user_service.get_current_user()
        authorize(
            CanManageRole(),
            context=RoleManagementContext(
                subject=current_user, target_role=UserRole.USER
            ),
        )
        try:
            result = await self._privy_client.delete_policy_rule(
                request.policy_id,
                request.rule_id,
                authorization_signature=request.authorization_signature,
            )
            # Refresh cached policy snapshot (best effort).
            try:
                policy_raw = await self._privy_client.get_policy(request.policy_id)
                dto = PrivyPolicyDTO.from_api(policy_raw)
                actor_user_id = (
                    getattr(current_user, "id_", None).value
                    if getattr(current_user, "id_", None)
                    else None
                )
                repo = PolicyRepositorySqla(self._session)
                await repo.upsert_from_privy(
                    policy=dto,
                    privy_raw=policy_raw
                    if isinstance(policy_raw, dict)
                    else {"raw": policy_raw},
                    actor_user_id=actor_user_id,
                    action="rule_delete",
                    extra_audit_payload={
                        "rule_result": result,
                        "rule_id": request.rule_id,
                    },
                )
            except Exception:
                logger.exception(
                    "DeletePrivyPolicyRule: failed to refresh cached policy_id=%s",
                    request.policy_id,
                )
            logger.info(
                "DeletePrivyPolicyRule: policy_id=%s rule_id=%s",
                request.policy_id,
                request.rule_id,
            )
            return result
        except PrivyPolicyNotFoundError as e:
            raise PolicyNotFoundError(str(e)) from e
        except PrivyClientError as e:
            raise PolicyRuleOperationError(str(e)) from e
        except Exception as e:
            if isinstance(
                e, (AuthorizationError, PolicyNotFoundError, PolicyRuleOperationError)
            ):
                raise
            raise PolicyRuleOperationError(str(e)) from e
