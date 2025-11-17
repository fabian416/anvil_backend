from app.domain.entities.user import User
from app.domain.enums.user_role import UserRole
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
from tests.app.unit.factories.value_objects import (
    create_password_hash,
    create_user_id,
    create_email,
    create_first_name,
    create_last_name,
    create_language,
    create_user_active,
    create_user_blocked,
    create_user_verified,
    create_retry_count,
    create_created_at,
    create_updated_at,
)


def create_user(
    user_id: UserId | None = None,
    email: Email | None = None,
    first_name: FirstName | None = None,
    last_name: LastName | None = None,
    password_hash: UserPasswordHash | None = None,
    role: UserRole = UserRole.USER,
    is_active: UserActive | None = None,
    is_blocked: UserBlocked | None = None,
    is_verified: UserVerified | None = None,
    retry_count: RetryCount | None = None,
    language: Language | None = None,
    created_at: CreatedAt | None = None,
    updated_at: UpdatedAt | None = None,
) -> User:
    return User(
        id=user_id or create_user_id(),
        email=email or create_email(),
        first_name=first_name or create_first_name(),
        last_name=last_name or create_last_name(),
        password=password_hash or create_password_hash(),
        role=role,
        is_active=is_active or create_user_active(),
        is_blocked=is_blocked or create_user_blocked(),
        is_verified=is_verified or create_user_verified(),
        retry_count=retry_count or create_retry_count(),
        language=language or create_language(),
        created_at=created_at or create_created_at(),
        updated_at=updated_at or create_updated_at(),
        last_login=None,
        profile_picture=None,
        phone_number=None,
        address=None,
        postal_code=None,
        country_id=None,
        city_id=None,
        subscription=None,
    )
