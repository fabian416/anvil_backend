"""
User entity for the hexagonal architecture.
Based on the BaseAPI User model with domain-driven design principles.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.domain.entities.base import Entity
from app.domain.enums.user_role import UserRole
from app.domain.value_objects.user_id import UserId
from app.domain.value_objects.email import Email
from app.domain.value_objects.first_name import FirstName
from app.domain.value_objects.last_name import LastName
from app.domain.value_objects.user_password_hash import UserPasswordHash
from app.domain.value_objects.user_status import UserActive, UserBlocked, UserVerified
from app.domain.value_objects.retry_count import RetryCount
from app.domain.value_objects.last_login import LastLogin
from app.domain.value_objects.profile_picture import ProfilePicture
from app.domain.value_objects.phone_number import PhoneNumber
from app.domain.value_objects.language import Language
from app.domain.value_objects.address import Address
from app.domain.value_objects.postal_code import PostalCode
from app.domain.value_objects.country_id import CountryId
from app.domain.value_objects.city_id import CityId
from app.domain.value_objects.subscription import Subscription
from app.domain.value_objects.created_at import CreatedAt
from app.domain.value_objects.updated_at import UpdatedAt


@dataclass(eq=False, kw_only=True)
class User(Entity[UserId]):
    """
    User entity representing a user in the system.
    
    This is an anemic model following DDD principles where behavior
    is handled by domain services rather than the entity itself.
    """
    email: Email
    first_name: FirstName
    last_name: LastName
    role: UserRole
    is_active: UserActive
    is_blocked: UserBlocked
    is_verified: UserVerified
    retry_count: RetryCount
    password: UserPasswordHash
    created_at: CreatedAt
    updated_at: UpdatedAt
    last_login: Optional[LastLogin]
    profile_picture: Optional[ProfilePicture]
    phone_number: Optional[PhoneNumber]
    language: Language
    address: Optional[Address]
    postal_code: Optional[PostalCode]
    country_id: Optional[CountryId]
    city_id: Optional[CityId]
    subscription: Optional[Subscription]
