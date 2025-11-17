"""
SQLAlchemy adapter for the auth gateway.
"""

import os
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from app.domain.entities.auth import AuthContext
from app.domain.entities.user import User
from app.domain.enums.user_role import UserRole
from app.domain.ports.auth_gateway import AuthGateway
from app.domain.value_objects.email import Email
from app.infrastructure.persistence_sqla.mappings.user import UserMapping
from app.infrastructure.auth.handlers.jwt_handler import JwtHandler


class AuthGatewaySqla(AuthGateway):
    """
    SQLAlchemy implementation of the auth gateway.
    """

    def __init__(
        self,
        session: AsyncSession,
        jwt_handler: JwtHandler,
    ):
        self._session = session
        self._jwt_handler = jwt_handler
        self._super_admin_email = os.getenv("USER_ADMIN")

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
        stmt = select(UserMapping).where(UserMapping.email == email.value)
        result = await self._session.execute(stmt)
        user_mapping = result.scalar_one_or_none()

        if user_mapping is None:
            return None

        return user_mapping.to_domain()

    async def update_user_role(self, user_id: str, new_role: UserRole) -> Optional[User]:
        """
        Update a user's role.
        """
        stmt = (
            update(UserMapping)
            .where(UserMapping.id == user_id)
            .values(role=new_role.value)
            .returning(UserMapping)
        )
        
        result = await self._session.execute(stmt)
        user_mapping = result.scalar_one_or_none()

        if user_mapping is None:
            return None

        await self._session.commit()
        return user_mapping.to_domain()

    async def is_super_admin(self, email: Email) -> bool:
        """
        Check if a user is a super admin.
        """
        return self._super_admin_email and email.value == self._super_admin_email
