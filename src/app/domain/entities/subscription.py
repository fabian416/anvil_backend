"""
Subscription entity for the hexagonal architecture.
Based on the BaseAPI Subscription model with domain-driven design principles.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any

from app.domain.entities.base import Entity
from app.domain.value_objects.subscription_id import SubscriptionId
from app.domain.value_objects.subscription_name import SubscriptionName
from app.domain.value_objects.price import Price
from app.domain.value_objects.subscription_type import SubscriptionType
from app.domain.value_objects.currency import Currency
from app.domain.value_objects.duration import Duration
from app.domain.value_objects.features import Features
from app.domain.value_objects.subscription_status import SubscriptionStatus
from app.domain.value_objects.stripe_price_id import StripePriceId
from app.domain.value_objects.stripe_product_id import StripeProductId
from app.domain.value_objects.created_at import CreatedAt
from app.domain.value_objects.updated_at import UpdatedAt


@dataclass(eq=False, kw_only=True)
class Subscription(Entity[SubscriptionId]):
    """
    Subscription entity representing a subscription plan in the system.
    
    This is an anemic model following DDD principles where behavior
    is handled by domain services rather than the entity itself.
    """
    name: SubscriptionName
    price: Price
    subscription_type: SubscriptionType
    currency: Currency
    duration: Duration
    features: Optional[Features]
    is_active: SubscriptionStatus
    stripe_price_id: Optional[StripePriceId]
    stripe_product_id: Optional[StripeProductId]
    created_at: CreatedAt
    updated_at: UpdatedAt
