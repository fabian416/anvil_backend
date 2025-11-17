from dataclasses import dataclass

from app.application.subscription.ports import SubscriptionRepository


@dataclass(frozen=True, slots=True)
class SubscriptionItem:
    id: int
    name: str
    price: float
    currency: str
    duration: int
    features: dict | None
    is_active: bool
    stripe_product_id: str | None
    stripe_price_id: str | None


class GetSubscriptionsHandler:
    def __init__(self, subscription_repo: SubscriptionRepository) -> None:
        self._repo = subscription_repo

    async def execute(self) -> list[SubscriptionItem]:
        rows = await self._repo.read_all()
        return [
            SubscriptionItem(
                id=int(r["id"]),
                name=str(r["name"]),
                price=float(r["price"]),
                currency=str(r["currency"]),
                duration=int(r["duration"]),
                features=r.get("features"),
                is_active=bool(r["is_active"]),
                stripe_product_id=r.get("stripe_product_id"),
                stripe_price_id=r.get("stripe_price_id"),
            )
            for r in rows
        ]


