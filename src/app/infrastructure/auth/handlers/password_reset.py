import logging
from dataclasses import dataclass
from datetime import datetime, timedelta

from app.application.common.ports.password_reset_repository import PasswordResetRepository
from app.application.common.ports.transaction_manager import TransactionManager
from app.application.common.ports.user_command_gateway import UserCommandGateway
from app.domain.value_objects.raw_password.raw_password import RawPassword
from app.application.common.services.current_user import CurrentUserService
from app.domain.value_objects.updated_at import UpdatedAt
from app.domain.value_objects.user_password_hash import UserPasswordHash
from app.domain.services.user import UserService
from app.domain.ports.password_hasher import PasswordHasher
from app.domain.value_objects.email import Email
from app.domain.value_objects.user_id import UserId
from app.application.common.ports.user_command_gateway import UserCommandGateway
from app.domain.exceptions.user import UserNotFoundByEmailError

from app.infrastructure.celery.app import celery_app

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ForgotPasswordRequest:
    email: str


@dataclass(frozen=True, slots=True)
class ResetPasswordRequest:
    token: str
    new_password: str


class ForgotPasswordHandler:
    def __init__(
        self,
        user_command_gateway: UserCommandGateway,
        password_reset_repo: PasswordResetRepository,
        transaction_manager: TransactionManager,
    ) -> None:
        self._user_gateway = user_command_gateway
        self._repo = password_reset_repo
        self._tx = transaction_manager

    async def execute(self, request: ForgotPasswordRequest) -> None:
        user = await self._user_gateway.read_by_email(Email(request.email))
        if user is None:
            raise UserNotFoundByEmailError(Email(request.email))

        # Invalidate existing tokens and create a new one
        await self._repo.invalidate_all_for_user(user_id=user.id_.value)
        from secrets import token_urlsafe

        token = token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=24)
        await self._repo.add(user_id=user.id_.value, token=token, expires_at=expires_at)
        await self._tx.commit()

        try:
            subject = "Password reset request"
            body = (
                "Use the code below to reset your password\n"
                f"{token}\n\n"
                "If you did not request this, you can ignore this email."
            )
            celery_app.send_task(
                "tasks.email_tasks.send_email",
                kwargs={
                    "to_email": user.email.value,
                    "subject": subject,
                    "body": body,
                },
            )
        except Exception as e:  # noqa: BLE001
            log.warning("Failed to enqueue password reset email: %s", e)


class ResetPasswordHandler:
    def __init__(
        self,
        user_command_gateway: UserCommandGateway,
        password_reset_repo: PasswordResetRepository,
        transaction_manager: TransactionManager,
        password_hasher: PasswordHasher,
    ) -> None:
        self._user_gateway = user_command_gateway
        self._repo = password_reset_repo
        self._tx = transaction_manager
        self._password_hasher = password_hasher

    async def execute(self, request: ResetPasswordRequest) -> None:
        row = await self._repo.read_by_token(token=request.token)
        if not row:
            # Silently ignore to avoid token probing; could raise specific error
            return

        user = await self._user_gateway.read_by_id(UserId(int(row["user_id"])))  # type: ignore[index]
        if user is None:
            return

        # Update password
        new_hash = UserPasswordHash(self._password_hasher.hash(RawPassword(request.new_password)))
        user.password = new_hash
        user.updated_at = UpdatedAt(datetime.utcnow())
        await self._user_gateway.update(user)

        # Mark token used and delete
        await self._repo.mark_used(id_=row["id"])  # type: ignore[index]
        await self._repo.delete_by_id(id_=row["id"])  # type: ignore[index]

        await self._tx.commit()


