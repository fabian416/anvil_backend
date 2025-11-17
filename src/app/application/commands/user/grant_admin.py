import logging
from dataclasses import dataclass

from app.application.common.ports.transaction_manager import (
    TransactionManager,
)
from app.application.common.ports.user_command_gateway import UserCommandGateway
from app.application.common.services.authorization.authorize import (
    authorize,
)
from app.application.common.services.authorization.permissions import (
    CanManageRole,
    RoleManagementContext,
)
from app.application.common.services.current_user import CurrentUserService
from app.domain.entities.user import User
from app.domain.enums.user_role import UserRole
from app.domain.exceptions.user import UserNotFoundByEmailError
from app.domain.services.user import UserService
from app.domain.value_objects.email import Email

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class GrantAdminRequest:
    email: str


class GrantAdminInteractor:
    """
    - Open to admins.
    - Grants admin rights to a specified user.
    - Admin rights can be managed by other admins.
    """

    def __init__(
        self,
        current_user_service: CurrentUserService,
        user_command_gateway: UserCommandGateway,
        user_service: UserService,
        transaction_manager: TransactionManager,
    ):
        self._current_user_service = current_user_service
        self._user_command_gateway = user_command_gateway
        self._user_service = user_service
        self._transaction_manager = transaction_manager

    async def execute(self, request_data: GrantAdminRequest) -> None:
        """
        :raises AuthenticationError:
        :raises DataMapperError:
        :raises AuthorizationError:
        :raises DomainFieldError:
        :raises UserNotFoundByEmailError:
        :raises RoleChangeNotPermittedError:
        """
        log.info(
            "Grant admin: started. Email: '%s'.",
            request_data.email,
        )

        current_user = await self._current_user_service.get_current_user()

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

        self._user_service.toggle_user_admin_role(user, is_admin=True)
        await self._transaction_manager.commit()

        log.info("Grant admin: done. Email: '%s'.", user.email.value)
