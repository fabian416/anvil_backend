from datetime import datetime
from typing import TypedDict

from app.domain.enums.user_role import UserRole


class UserQueryModel(TypedDict):
    id: int
    email: str
    first_name: str
    last_name: str
    role: UserRole
    is_active: bool
    is_blocked: bool
    is_verified: bool
    retry_count: int
    created_at: datetime
    updated_at: datetime
    last_login: datetime | None
    profile_picture: str | None
    phone_number: str | None
    language: str
    address: str | None
    postal_code: str | None
    country_id: int | None
    city_id: int | None
    subscription: str | None
    # Privy authentication fields
    privy_user_id: str | None
    primary_wallet_address: str | None
    auth_provider: str | None
