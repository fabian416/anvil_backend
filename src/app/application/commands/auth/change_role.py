"""
Change role command interactor for the hexagonal architecture.
"""

import logging
from dataclasses import dataclass

from app.application.common.ports.transaction_manager import TransactionManager
from app.application.common.services.current_user import CurrentUserService
from app.domain.entities.user import User
from app.domain.enums.user_role import UserRole
from app.domain.exceptions.auth import (
    InvalidAuthorizationHeaderError,
    InsufficientPermissionsError,
    RoleChangeNotAllowedError,
)
from app.domain.exceptions.user import UserNotFoundByEmailError
from app.domain.ports.auth_gateway import AuthGateway
from app.domain.services.auth import AuthService
from app.domain.value_objects.email import Email

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ChangeRoleRequest:
    """Request to change a user's role."""

    authorization: str
    target_email: str
    new_role: str


class ChangeRoleInteractor:
    """
    Change a user's role. Only accessible by admin users.
    """

    def __init__(
        self,
        current_user_service: CurrentUserService,
        auth_gateway: AuthGateway,
        auth_service: AuthService,
        transaction_manager: TransactionManager,
    ):
        self._current_user_service = current_user_service
        self._auth_gateway = auth_gateway
        self._auth_service = auth_service
        self._transaction_manager = transaction_manager

    async def execute(self, request_data: ChangeRoleRequest) -> User:
        """
        :raises InvalidAuthorizationHeaderError:
        :raises InsufficientPermissionsError:
        :raises RoleChangeNotAllowedError:
        :raises UserNotFoundByEmailError:
        """
        log.info(
            "Change role: started. Target email: '%s', new role: '%s'.",
            request_data.target_email,
            request_data.new_role,
        )

        # Validate authorization header
        access_token = self._auth_service.validate_authorization_header(
            request_data.authorization
        )

        # Get current user and verify admin role
        current_user = await self._current_user_service.get_current_user()
        self._auth_service.check_admin_permission(current_user.role)

        # Validate new role
        try:
            new_role = UserRole(request_data.new_role)
        except ValueError:
            raise RoleChangeNotAllowedError(
                f"Invalid role. Must be one of: {[r.value for r in UserRole]}"
            )

        # Find user by email
        target_email = Email(request_data.target_email)
        target_user = await self._auth_gateway.get_user_by_email(target_email)

        if not target_user:
            raise UserNotFoundByEmailError(target_email)

        # Validate role change
        self._auth_service.validate_role_change(target_user.role, new_role)

        # Update user role
        updated_user = await self._auth_gateway.update_user_role(
            target_user.id, new_role
        )

        if not updated_user:
            raise UserNotFoundByEmailError(target_email)

        await self._transaction_manager.commit()

        log.info(
            "Change role: done. User: '%s', new role: '%s'.",
            target_user.email.value,
            new_role.value,
        )
        return updated_user
