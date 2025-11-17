import stripe
from dataclasses import dataclass
from datetime import datetime

from app.application.subscription.ports import (
    PaymentRepository,
    SubscriptionRepository,
    SubscriptionUserRepository,
)
from app.application.common.ports.transaction_manager import TransactionManager
from app.application.common.services.current_user import CurrentUserService
from app.application.notification.ports import NotificationRepository


@dataclass(frozen=True, slots=True)
class CreateSubscriptionRequest:
    subscription_id: int
    callback_base_url: str | None = None


class CreateSubscriptionHandler:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        subscription_repo: SubscriptionRepository,
        subscription_user_repo: SubscriptionUserRepository,
        payment_repo: PaymentRepository,
        notification_repo: NotificationRepository,
        transaction_manager: TransactionManager,
    ) -> None:
        self._current_user_service = current_user_service
        self._subs = subscription_repo
        self._subs_user = subscription_user_repo
        self._payments = payment_repo
        self._notifications = notification_repo
        self._tx = transaction_manager

    async def execute(self, request: CreateSubscriptionRequest) -> dict:
        user = await self._current_user_service.get_current_user()
        plan = await self._subs.read_by_id(request.subscription_id)
        if not plan:
            raise ValueError("Subscription not found")

        # Create SubscriptionUser row
        subs_user_id = await self._subs_user.add(
            user_id=user.id_.value,
            subscription_id=int(plan["id"]),
            status="pending",
            data_json={},
        )

        # Create a Payment row (pending)
        payment_id = await self._payments.add(
            user_id=user.id_.value,
            subscription_id=int(plan["id"]),
            subscription_user_id=subs_user_id,
            amount=float(plan.get("price") or 0.0),
            currency=str(plan.get("currency") or "USD"),
            status="pending",
            stripe_payment_intent_id=None,
            data_json={},
        )

        # Create Stripe Checkout Session if keys exist
        from app.setup.config.settings import load_settings

        settings = load_settings()
        stripe_cfg = getattr(settings, "stripe", None)
        api_key = getattr(stripe_cfg, "STRIPE_API_KEY", None) if stripe_cfg else None
        checkout_session_id: str | None = None
        if api_key and plan.get("stripe_price_id"):
            stripe.api_key = api_key
            base = request.callback_base_url or "http://127.0.0.1:9999"
            if base.endswith("/"):
                base = base[:-1]
            success_url = f"{base}/api/v1/subscription/success?session_id={{CHECKOUT_SESSION_ID}}"
            cancel_url = f"{base}/api/v1/subscription/cancel?session_id={{CHECKOUT_SESSION_ID}}"
            try:
                session = stripe.checkout.Session.create(
                    mode="subscription",
                    line_items=[{"price": plan["stripe_price_id"], "quantity": 1}],
                    success_url=success_url,
                    cancel_url=cancel_url,
                )
                checkout_session_id = session["id"]
            except Exception as e:  # noqa: BLE001
                raise ValueError(str(e))
            # persist on subscription_user and payment
            await self._subs_user.update_data_json(
                id_=subs_user_id,
                data_json={"checkout_session_id": checkout_session_id},
            )
            await self._payments.update_data_json(
                id_=payment_id,
                data_json={"checkout_session_id": checkout_session_id},
            )

        # Persist checkout session id on subscription user and payment
        await self._tx.commit()

        return {
            "status": "success",
            "subscription_user_id": subs_user_id,
            "payment_id": payment_id,
            "checkout_session_id": checkout_session_id,
        }



