import logging
from dataclasses import dataclass
from datetime import datetime, timedelta

from app.application.common.exceptions.authorization import AuthorizationError
from app.application.common.ports.email_verification_repository import (
    EmailVerificationRepository,
)
from app.application.common.ports.transaction_manager import TransactionManager
from app.application.common.services.current_user import CurrentUserService
from app.infrastructure.celery.app import celery_app


log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class SendEmailVerificationRequest:
    pass


class SendEmailVerificationHandler:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        transaction_manager: TransactionManager,
        email_verification_repo: EmailVerificationRepository,
    ) -> None:
        self._current_user_service = current_user_service
        self._tx = transaction_manager
        self._repo = email_verification_repo

    async def execute(self, _request_data: SendEmailVerificationRequest | None = None) -> None:
        user = await self._current_user_service.get_current_user()

        if user.is_verified.value:
            raise AuthorizationError("Email already verified")

        # Create verification token
        from secrets import token_urlsafe

        token = token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=24)

        await self._repo.add(user_id=user.id_.value, token=token, expires_at=expires_at)
        await self._tx.commit()

        # Best-effort: enqueue email send
        try:
            celery_app.send_task(
                "tasks.email_tasks.send_verification_email",
                kwargs={
                    "to_email": user.email.value,
                    "verification_url": token,
                },
            )
        except Exception as e:  # noqa: BLE001
            log.warning("Failed to enqueue verification email: %s", e)


