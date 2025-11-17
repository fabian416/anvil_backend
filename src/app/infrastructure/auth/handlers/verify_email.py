from dataclasses import dataclass
from datetime import datetime

from app.application.common.exceptions.authorization import AuthorizationError
from app.application.common.ports.email_verification_repository import (
    EmailVerificationRepository,
)
from app.application.common.ports.transaction_manager import TransactionManager
from app.application.common.ports.user_command_gateway import UserCommandGateway
from app.application.common.services.current_user import CurrentUserService
from app.domain.value_objects.updated_at import UpdatedAt
from app.domain.value_objects.user_status import UserVerified


@dataclass(frozen=True, slots=True)
class VerifyEmailRequest:
    token: str


class VerifyEmailHandler:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        user_command_gateway: UserCommandGateway,
        transaction_manager: TransactionManager,
        email_verification_repo: EmailVerificationRepository,
    ) -> None:
        self._current_user_service = current_user_service
        self._user_command_gateway = user_command_gateway
        self._tx = transaction_manager
        self._repo = email_verification_repo

    async def execute(self, request_data: VerifyEmailRequest) -> None:
        user = await self._current_user_service.get_current_user()
        row = await self._repo.read_by_user_and_token(user_id=user.id_.value, token=request_data.token)
        if not row:
            raise AuthorizationError("Invalid or expired verification token")

        # Mark user verified
        user.is_verified = UserVerified(True)
        user.updated_at = UpdatedAt(datetime.utcnow())
        await self._user_command_gateway.update(user)

        # Mark token used and delete
        await self._repo.mark_used(id_=row["id"])  # type: ignore[index]
        await self._repo.delete_by_id(id_=row["id"])  # type: ignore[index]

        await self._tx.commit()


