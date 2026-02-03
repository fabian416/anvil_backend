"""
Upgrade to admin command interactor for the hexagonal architecture.
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
)
from app.domain.exceptions.user import UserNotFoundByEmailError
from app.domain.ports.auth_gateway import AuthGateway
from app.domain.services.auth import AuthService
from app.domain.value_objects.email import Email

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class UpgradeToAdminRequest:
    """Request to upgrade a user to admin role."""

    authorization: str


class UpgradeToAdminInteractor:
    """
    Upgrade a user to admin role. Only accessible by users with USER_ADMIN role.
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

    async def execute(self, request_data: UpgradeToAdminRequest) -> User:
        """
        :raises InvalidAuthorizationHeaderError:
        :raises InsufficientPermissionsError:
        :raises UserNotFoundByEmailError:
        """
        log.info("Upgrade to admin: started.")

        # Validate authorization header
        access_token = self._auth_service.validate_authorization_header(
            request_data.authorization
        )

        # Get current user
        current_user = await self._current_user_service.get_current_user()

        # Check if current user has USER_ADMIN role
        self._auth_service.check_super_admin_permission(current_user.email)

        # Update user role to admin
        updated_user = await self._auth_gateway.update_user_role(
            current_user.id_.value, UserRole.ADMIN
        )

        if not updated_user:
            raise UserNotFoundByEmailError(current_user.email)

        await self._transaction_manager.commit()

        log.info("Upgrade to admin: done. User: '%s'.", current_user.email.value)
        return updated_user
