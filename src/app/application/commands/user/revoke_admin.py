import logging
from dataclasses import dataclass

from app.application.common.exceptions.authorization import AuthorizationError
from app.application.common.ports.transaction_manager import (
    TransactionManager,
)
from app.application.common.ports.user_command_gateway import UserCommandGateway
from app.application.common.services.authorization.authorize import authorize
from app.application.common.services.authorization.permissions import (
    CanManageRole,
    RoleManagementContext,
)
from app.application.common.services.current_user import CurrentUserService
from app.domain.entities.user import User
from app.domain.enums.user_role import UserRole
from app.domain.exceptions.user import UserNotFoundByEmailError
from app.domain.services.user import UserService
from app.domain.services.auth import AuthService
from app.domain.value_objects.email import Email

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class RevokeAdminRequest:
    email: str


class RevokeAdminInteractor:
    """
    - Open to admins.
    - Revokes admin rights from a specified user.
    - Admin rights can be managed by other admins.
    """

    def __init__(
        self,
        current_user_service: CurrentUserService,
        user_command_gateway: UserCommandGateway,
        user_service: UserService,
        transaction_manager: TransactionManager,
        auth_service: AuthService,
    ):
        self._current_user_service = current_user_service
        self._user_command_gateway = user_command_gateway
        self._user_service = user_service
        self._transaction_manager = transaction_manager
        self._auth_service = auth_service

    async def execute(self, request_data: RevokeAdminRequest) -> None:
        """
        :raises AuthenticationError:
        :raises DataMapperError:
        :raises AuthorizationError:
        :raises DomainFieldError:
        :raises UserNotFoundByEmailError:
        :raises RoleChangeNotPermittedError:
        """
        log.info(
            "Revoke admin: started. Email: '%s'.",
            request_data.email,
        )

        current_user = await self._current_user_service.get_current_user()

        # Enterprise: only the configured "super admin" can revoke admin rights.
        if not self._auth_service.is_super_admin(current_user.email):
            raise AuthorizationError("Super admin privileges required.")

        authorize(
            CanManageRole(),
            context=RoleManagementContext(
                subject=current_user,
                target_role=UserRole.ADMIN,
            ),
        )

        email = Email(request_data.email)
        user: User | None = await self._user_command_gateway.read_by_email(
            email,
            for_update=True,
        )
        if user is None:
            raise UserNotFoundByEmailError(email)

        # Protect the configured super admin account from role changes.
        if self._auth_service.is_super_admin(user.email):
            raise AuthorizationError("Cannot modify super admin role.")

        self._user_service.toggle_user_admin_role(user, is_admin=False)
        await self._user_command_gateway.update(user)
        await self._transaction_manager.commit()

        log.info(
            "Revoke admin: done. Email: '%s'.",
            user.email.value,
        )
