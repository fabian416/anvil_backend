import stripe
from dataclasses import dataclass
from datetime import datetime

from app.application.subscription.ports import (
    PaymentRepository,
    SubscriptionUserRepository,
)
from app.application.common.ports.transaction_manager import TransactionManager
from app.application.common.services.current_user import CurrentUserService


@dataclass(frozen=True, slots=True)
class CancelSubscriptionRequest:
    subscription_id: int


class CancelSubscriptionHandler:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        subscription_user_repo: SubscriptionUserRepository,
        payment_repo: PaymentRepository,
        transaction_manager: TransactionManager,
    ) -> None:
        self._current_user_service = current_user_service
        self._subs_user = subscription_user_repo
        self._payments = payment_repo
        self._tx = transaction_manager

    async def execute(self, request: CancelSubscriptionRequest) -> dict:
        user = await self._current_user_service.get_current_user()
        subs_user = await self._subs_user.read_active_for_user_and_subscription(
            user_id=user.id_.value, subscription_id=request.subscription_id
        )
        if not subs_user:
            raise ValueError("Subscription not found")

        # Cancel in Stripe if id exists
        from app.setup.config.settings import load_settings

        settings = load_settings()
        stripe_cfg = getattr(settings, "stripe", None)
        api_key = getattr(stripe_cfg, "STRIPE_API_KEY", None) if stripe_cfg else None
        if api_key and subs_user.get("stripe_subscription_id"):
            try:
                stripe.api_key = api_key
                stripe.Subscription.delete(subs_user["stripe_subscription_id"])  # type: ignore[index]
            except Exception:
                pass

        # Update statuses
        await self._subs_user.update_status(id_=int(subs_user["id"]), status="cancelled")
        payments = await self._payments.list_by_subscription_user(subscription_user_id=int(subs_user["id"]))
        for p in payments:
            await self._payments.update_status(id_=int(p["id"]), status="cancelled")
        await self._tx.commit()

        return {
            "status": "success",
            "message": "Subscription and all associated payments cancelled",
            "subscription_id": int(subs_user["id"]),
            "cancelled_payments": len(payments),
        }


