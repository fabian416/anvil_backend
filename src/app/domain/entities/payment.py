"""
Payment entity for the hexagonal architecture.
Based on the BaseAPI Payment model with domain-driven design principles.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any

from app.domain.entities.base import Entity
from app.domain.value_objects.payment_id import PaymentId
from app.domain.value_objects.user_id import UserId
from app.domain.value_objects.subscription_id import SubscriptionId
from app.domain.value_objects.subscription_user_id import SubscriptionUserId
from app.domain.value_objects.amount import Amount
from app.domain.value_objects.currency import Currency
from app.domain.value_objects.payment_status import PaymentStatus
from app.domain.value_objects.stripe_payment_intent_id import StripePaymentIntentId
from app.domain.value_objects.stripe_customer_id import StripeCustomerId
from app.domain.value_objects.payment_data import PaymentData
from app.domain.value_objects.payment_method import PaymentMethod
from app.domain.value_objects.payment_type import PaymentType
from app.domain.value_objects.payment_date import PaymentDate
from app.domain.value_objects.data_json import DataJson
from app.domain.value_objects.created_at import CreatedAt
from app.domain.value_objects.updated_at import UpdatedAt


@dataclass(eq=False, kw_only=True)
class Payment(Entity[PaymentId]):
    """
    Payment entity representing a payment transaction in the system.
    
    This is an anemic model following DDD principles where behavior
    is handled by domain services rather than the entity itself.
    """
    user_id: UserId
    subscription_id: Optional[SubscriptionId]
    subscription_user_id: Optional[SubscriptionUserId]
    amount: Optional[Amount]
    currency: Currency
    status: PaymentStatus
    stripe_payment_intent_id: Optional[StripePaymentIntentId]
    stripe_customer_id: Optional[StripeCustomerId]
    payment_data: Optional[PaymentData]
    payment_method: Optional[PaymentMethod]
    payment_type: Optional[PaymentType]
    created_at: CreatedAt
    updated_at: UpdatedAt
    date: Optional[PaymentDate]
    data_json: Optional[DataJson]
