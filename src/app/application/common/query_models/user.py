from typing import TypedDict, Optional
from datetime import datetime

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
    last_login: Optional[datetime]
    profile_picture: Optional[str]
    phone_number: Optional[str]
    language: str
    address: Optional[str]
    postal_code: Optional[str]
    country_id: Optional[int]
    city_id: Optional[int]
    subscription: Optional[str]
