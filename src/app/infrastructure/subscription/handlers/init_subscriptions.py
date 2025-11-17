import logging
from dataclasses import dataclass
from datetime import datetime
import stripe

from app.application.subscription.ports import SubscriptionRepository
from app.application.common.ports.transaction_manager import TransactionManager


log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class InitSubscriptionsRequest:
    pass


class InitSubscriptionsHandler:
    def __init__(
        self,
        subscription_repo: SubscriptionRepository,
        transaction_manager: TransactionManager,
    ) -> None:
        self._repo = subscription_repo
        self._tx = transaction_manager

    async def execute(self, _request: InitSubscriptionsRequest | None = None) -> list[dict]:
        definitions = [
            {
                "name": "PRO",
                "price": 9.99,
                "subscription_type": "month",
                "currency": "USD",
                "duration": 30,
                "features": {"users": 1, "storage_gb": 10},
                "is_active": True,
                "stripe_price_id": None,
                "stripe_product_id": None,
            },
            {
                "name": "CORPORATE",
                "price": 49.99,
                "subscription_type": "month",
                "currency": "USD",
                "duration": 30,
                "features": {"users": 10, "storage_gb": 100},
                "is_active": True,
                "stripe_price_id": None,
                "stripe_product_id": None,
            },
        ]

        results: list[dict] = []
        now = datetime.utcnow()
        # First ensure rows exist
        for d in definitions:
            existing = await self._repo.read_by_name(d["name"])
            if existing:
                results.append({
                    "id": int(existing["id"]),
                    "name": d["name"],
                    "price": d["price"],
                    "currency": d["currency"],
                    "stripe_product_id": existing.get("stripe_product_id"),
                    "stripe_price_id": existing.get("stripe_price_id"),
                    "created": False,
                })
                continue
            new_id = await self._repo.add(
                name=d["name"],
                price=d["price"],
                subscription_type=d["subscription_type"],
                currency=d["currency"],
                duration=d["duration"],
                features=d["features"],
                is_active=d["is_active"],
                stripe_price_id=d["stripe_price_id"],
                stripe_product_id=d["stripe_product_id"],
                created_at=now,
                updated_at=now,
            )
            results.append({
                "id": new_id,
                "name": d["name"],
                "price": d["price"],
                "currency": d["currency"],
                "stripe_product_id": None,
                "stripe_price_id": None,
                "created": True,
            })

        # Optionally create Stripe products/prices if API key is configured
        try:
            from app.setup.config.settings import load_settings

            settings = load_settings()
            stripe_cfg = getattr(settings, "stripe", None)
            api_key = getattr(stripe_cfg, "STRIPE_API_KEY", None) if stripe_cfg else None
            if api_key:
                stripe.api_key = api_key
                for item in results:
                    if item.get("stripe_product_id") and item.get("stripe_price_id"):
                        continue
                    name = item["name"]
                    price = float(item["price"])
                    currency = str(item["currency"]).lower()
                    # Create product & price
                    product = stripe.Product.create(name=f"{name} Plan")
                    unit_amount = int(round(price * 100))
                    price_obj = stripe.Price.create(
                        unit_amount=unit_amount,
                        currency=currency,
                        recurring={"interval": "month"},
                        product=product["id"],
                    )
                    await self._repo.update_stripe_ids(
                        id_=int(item["id"]),
                        stripe_price_id=price_obj["id"],
                        stripe_product_id=product["id"],
                    )
                    item["stripe_product_id"] = product["id"]
                    item["stripe_price_id"] = price_obj["id"]
        except Exception as e:  # noqa: BLE001
            log.warning("Stripe integration skipped or failed: %s", e)

        await self._tx.commit()

        # Build response from DB to ensure latest Stripe IDs are included
        final_results: list[dict] = []
        for d in definitions:
            row = await self._repo.read_by_name(d["name"])
            if not row:
                continue
            final_results.append(
                {
                    "id": int(row["id"]),
                    "name": d["name"],
                    "price": float(row.get("price", d["price"]) or d["price"]),
                    "currency": row.get("currency", d["currency"]) or d["currency"],
                    "stripe_product_id": row.get("stripe_product_id"),
                    "stripe_price_id": row.get("stripe_price_id"),
                    "created": any(r["name"] == d["name"] and r.get("created") for r in results),
                }
            )

        return final_results


