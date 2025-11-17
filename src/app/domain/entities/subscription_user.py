"""
SubscriptionUser entity for the hexagonal architecture.
Based on the BaseAPI SubscriptionUser model with domain-driven design principles.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any

from app.domain.entities.base import Entity
from app.domain.value_objects.subscription_user_id import SubscriptionUserId
from app.domain.value_objects.user_id import UserId
from app.domain.value_objects.subscription_id import SubscriptionId
from app.domain.value_objects.subscription_status import SubscriptionStatus
from app.domain.value_objects.start_date import StartDate
from app.domain.value_objects.end_date import EndDate
from app.domain.value_objects.stripe_subscription_id import StripeSubscriptionId
from app.domain.value_objects.stripe_customer_id import StripeCustomerId
from app.domain.value_objects.client_secret import ClientSecret
from app.domain.value_objects.subscription_data import SubscriptionData
from app.domain.value_objects.data_json import DataJson
from app.domain.value_objects.created_at import CreatedAt
from app.domain.value_objects.updated_at import UpdatedAt


@dataclass(eq=False, kw_only=True)
class SubscriptionUser(Entity[SubscriptionUserId]):
    """
    SubscriptionUser entity representing a user's subscription in the system.
    
    This is an anemic model following DDD principles where behavior
    is handled by domain services rather than the entity itself.
    """
    user_id: UserId
    subscription_id: SubscriptionId
    status: SubscriptionStatus
    start_date: Optional[StartDate]
    end_date: Optional[EndDate]
    stripe_subscription_id: Optional[StripeSubscriptionId]
    stripe_customer_id: Optional[StripeCustomerId]
    client_secret: Optional[ClientSecret]
    subscription_data: Optional[SubscriptionData]
    data_json: Optional[DataJson]
    created_at: CreatedAt
    updated_at: UpdatedAt
