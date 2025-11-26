"""
SQLAlchemy adapter for the auth gateway.
"""

import os
from typing import Optional

from sqlalchemy import Select, select, update
from sqlalchemy.exc import SQLAlchemyError

from app.domain.entities.auth import AuthContext
from app.domain.entities.user import User
from app.domain.enums.user_role import UserRole
from app.domain.ports.auth_gateway import AuthGateway
from app.domain.value_objects.address import Address
from app.domain.value_objects.city_id import CityId
from app.domain.value_objects.country_id import CountryId
from app.domain.value_objects.created_at import CreatedAt
from app.domain.value_objects.email import Email
from app.domain.value_objects.first_name import FirstName
from app.domain.value_objects.language import Language
from app.domain.value_objects.last_login import LastLogin
from app.domain.value_objects.last_name import LastName
from app.domain.value_objects.phone_number import PhoneNumber
from app.domain.value_objects.postal_code import PostalCode
from app.domain.value_objects.profile_picture import ProfilePicture
from app.domain.value_objects.retry_count import RetryCount
from app.domain.value_objects.subscription import Subscription
from app.domain.value_objects.updated_at import UpdatedAt
from app.domain.value_objects.user_id import UserId
from app.domain.value_objects.user_password_hash import UserPasswordHash
from app.domain.value_objects.user_status import UserActive, UserBlocked, UserVerified
from app.infrastructure.adapters.constants import DB_QUERY_FAILED
from app.infrastructure.adapters.types import MainAsyncSession
from app.infrastructure.auth.handlers.jwt_handler import JwtHandler
from app.infrastructure.exceptions.gateway import DataMapperError
from app.infrastructure.persistence_sqla.mappings.user import map_users_table
from app.infrastructure.persistence_sqla.registry import mapping_registry


class AuthGatewaySqla(AuthGateway):
    """
    SQLAlchemy implementation of the auth gateway.
    """

    def __init__(
        self,
        session: MainAsyncSession,
        jwt_handler: JwtHandler,
    ):
        map_users_table()
        self._session = session
        self._jwt_handler = jwt_handler
        # Support both formats: ADMIN_USER_ADMIN (from TOML export) or USER_ADMIN (legacy)
        self._super_admin_email = os.getenv("ADMIN_USER_ADMIN") or os.getenv("USER_ADMIN")

    async def validate_token(self, access_token: str) -> Optional[AuthContext]:
        """
        Validate an access token and return the auth context.
        """
        try:
            payload = self._jwt_handler.decode_token(access_token)
            user_id = payload.get("sub")
            email = payload.get("email")
            role = payload.get("role")

            if not all([user_id, email, role]):
                return None

            return AuthContext(
                access_token=access_token,
                user_email=Email(email),
                user_role=UserRole(role),
                user_id=user_id,
            )
        except Exception:
            return None

    async def get_user_by_email(self, email: Email) -> Optional[User]:
        """
        Get a user by email address.
        """
        try:
            users_table = mapping_registry.metadata.tables["users"]
            stmt: Select = select(users_table).where(users_table.c.email == email.value)
            row = (await self._session.execute(stmt)).mappings().first()
            return self._row_to_user(row) if row else None
        except SQLAlchemyError as error:
            raise DataMapperError(DB_QUERY_FAILED) from error

    async def update_user_role(self, user_id: int, new_role: UserRole) -> Optional[User]:
        """
        Update a user's role.
        """
        try:
            users_table = mapping_registry.metadata.tables["users"]
            stmt = (
                update(users_table)
                .where(users_table.c.id == user_id)
                .values(role=new_role.value)
            )
            await self._session.execute(stmt)
            await self._session.commit()

            # Fetch updated user
            select_stmt: Select = select(users_table).where(users_table.c.id == user_id)
            row = (await self._session.execute(select_stmt)).mappings().first()
            return self._row_to_user(row) if row else None
        except SQLAlchemyError as error:
            raise DataMapperError(DB_QUERY_FAILED) from error

    async def is_super_admin(self, email: Email) -> bool:
        """
        Check if a user is a super admin.
        """
        return bool(self._super_admin_email and email.value == self._super_admin_email)

    @staticmethod
    def _row_to_user(row: dict | None) -> User | None:
        """Convert a database row to a User entity."""
        if not row:
            return None
        return User(
            id_=UserId(int(row["id"])),
            email=Email(str(row["email"])),
            first_name=FirstName(str(row["first_name"])),
            last_name=LastName(str(row["last_name"])),
            role=UserRole(str(row["role"])),
            is_active=UserActive(bool(row["is_active"])),
            is_blocked=UserBlocked(bool(row["is_blocked"])),
            is_verified=UserVerified(bool(row["is_verified"])),
            retry_count=RetryCount(int(row["retry_count"] or 0)),
            password=UserPasswordHash(str(row["password"]).encode("utf-8")),
            created_at=CreatedAt(row["created_at"]),
            updated_at=UpdatedAt(row["updated_at"]),
            last_login=LastLogin(row["last_login"]) if row.get("last_login") else None,
            profile_picture=ProfilePicture(row["profile_picture"]) if row.get("profile_picture") else None,
            phone_number=PhoneNumber(row["phone_number"]) if row.get("phone_number") else None,
            language=Language(str(row["language"])) if row.get("language") else Language("en"),
            address=Address(row["address"]) if row.get("address") else None,
            postal_code=PostalCode(row["postal_code"]) if row.get("postal_code") else None,
            country_id=CountryId(int(row["country_id"])) if row.get("country_id") is not None else None,
            city_id=CityId(int(row["city_id"])) if row.get("city_id") is not None else None,
            subscription=Subscription(row["subscription"]) if row.get("subscription") else None,
        )
