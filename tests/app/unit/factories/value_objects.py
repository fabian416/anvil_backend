import uuid
from dataclasses import dataclass
from datetime import datetime

from app.domain.value_objects.base import ValueObject
from app.domain.value_objects.raw_password.raw_password import RawPassword
from app.domain.value_objects.user_id import UserId
from app.domain.value_objects.user_password_hash import UserPasswordHash
from app.domain.value_objects.email import Email
from app.domain.value_objects.first_name import FirstName
from app.domain.value_objects.last_name import LastName
from app.domain.value_objects.language import Language
from app.domain.value_objects.user_active import UserActive
from app.domain.value_objects.user_blocked import UserBlocked
from app.domain.value_objects.user_verified import UserVerified
from app.domain.value_objects.retry_count import RetryCount
from app.domain.value_objects.created_at import CreatedAt
from app.domain.value_objects.updated_at import UpdatedAt


@dataclass(frozen=True, slots=True, repr=False)
class SingleFieldVO(ValueObject):
    value: int


@dataclass(frozen=True, slots=True, repr=False)
class MultiFieldVO(ValueObject):
    value1: int
    value2: str


def create_single_field_vo(value: int = 1) -> SingleFieldVO:
    return SingleFieldVO(value)


def create_multi_field_vo(value1: int = 1, value2: str = "Alice") -> MultiFieldVO:
    return MultiFieldVO(value1, value2)


def create_user_id(value: int | None = None) -> UserId:
    return UserId(value if value else 1)


def create_email(value: str = "alice@example.com") -> Email:
    return Email(value)


def create_first_name(value: str = "Alice") -> FirstName:
    return FirstName(value)


def create_last_name(value: str = "Smith") -> LastName:
    return LastName(value)


def create_language(value: str = "en") -> Language:
    return Language(value)


def create_user_active(value: bool = True) -> UserActive:
    return UserActive(value)


def create_user_blocked(value: bool = False) -> UserBlocked:
    return UserBlocked(value)


def create_user_verified(value: bool = False) -> UserVerified:
    return UserVerified(value)


def create_retry_count(value: int = 0) -> RetryCount:
    return RetryCount(value)


def create_created_at(value: datetime | None = None) -> CreatedAt:
    return CreatedAt(value if value else datetime.now())


def create_updated_at(value: datetime | None = None) -> UpdatedAt:
    return UpdatedAt(value if value else datetime.now())


def create_raw_password(value: str = "Good Password") -> RawPassword:
    return RawPassword(value)


def create_password_hash(value: bytes = b"password_hash") -> UserPasswordHash:
    return UserPasswordHash(value)
