import stripe
from dataclasses import dataclass

from app.application.subscription.ports import (
    PaymentRepository,
    SubscriptionUserRepository,
)
from app.application.common.ports.transaction_manager import TransactionManager


@dataclass(frozen=True, slots=True)
class SubscriptionSuccessRequest:
    session_id: str


class SubscriptionSuccessHandler:
    def __init__(
        self,
        subscription_user_repo: SubscriptionUserRepository,
        payment_repo: PaymentRepository,
        transaction_manager: TransactionManager,
    ) -> None:
        self._subs_user = subscription_user_repo
        self._payments = payment_repo
        self._tx = transaction_manager

    async def execute(self, request: SubscriptionSuccessRequest) -> dict:
        from app.setup.config.settings import load_settings

        settings = load_settings()
        stripe_cfg = getattr(settings, "stripe", None)
        api_key = getattr(stripe_cfg, "STRIPE_API_KEY", None) if stripe_cfg else None
        if not api_key:
            raise ValueError("Stripe is not configured")
        stripe.api_key = api_key

        session = stripe.checkout.Session.retrieve(request.session_id)
        subs_user = await self._subs_user.read_by_checkout_session_id(session_id=request.session_id)
        if not subs_user:
            raise ValueError("Subscription not found")

        await self._subs_user.update_status(id_=int(subs_user["id"]), status="active")
        await self._subs_user.update_stripe_subscription_id(id_=int(subs_user["id"]), stripe_subscription_id=session["subscription"])  # type: ignore[index]

        pending_payment = await self._payments.find_pending_for_subscription_user(subscription_user_id=int(subs_user["id"]))
        if pending_payment:
            await self._payments.update_status(id_=int(pending_payment["id"]), status="completed")
            await self._payments.update_data_json(
                id_=int(pending_payment["id"]),
                data_json={
                    **(pending_payment.get("data_json") or {}),
                    "subscription_id": session["subscription"],  # type: ignore[index]
                    "payment_intent": session["payment_intent"],  # type: ignore[index]
                },
            )
        await self._tx.commit()
        return {"status": "success", "message": "Subscription activated successfully", "subscription_id": int(subs_user["id"])}


