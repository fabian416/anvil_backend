from datetime import datetime
from typing import Optional

from app.domain.entities.user import User
from app.domain.enums.user_role import UserRole
from app.domain.exceptions.user import (
    ActivationChangeNotPermittedError,
    RoleAssignmentNotPermittedError,
    RoleChangeNotPermittedError,
)
from app.domain.ports.password_hasher import PasswordHasher
from app.domain.ports.user_id_generator import UserIdGenerator
from app.domain.value_objects.raw_password.raw_password import RawPassword
from app.domain.value_objects.user_id import UserId
from app.domain.value_objects.email import Email
from app.domain.value_objects.first_name import FirstName
from app.domain.value_objects.last_name import LastName
from app.domain.value_objects.user_password_hash import UserPasswordHash
from app.domain.value_objects.user_status import UserActive, UserBlocked, UserVerified
from app.domain.value_objects.retry_count import RetryCount
from app.domain.value_objects.phone_number import PhoneNumber
from app.domain.value_objects.language import Language
from app.domain.value_objects.address import Address
from app.domain.value_objects.postal_code import PostalCode
from app.domain.value_objects.country_id import CountryId
from app.domain.value_objects.city_id import CityId
from app.domain.value_objects.subscription import Subscription
from app.domain.value_objects.created_at import CreatedAt
from app.domain.value_objects.updated_at import UpdatedAt
from app.domain.value_objects.last_login import LastLogin


class UserService:
    def __init__(
        self,
        user_id_generator: UserIdGenerator,
        password_hasher: PasswordHasher,
    ) -> None:
        self._user_id_generator = user_id_generator
        self._password_hasher = password_hasher

    def create_user(
        self,
        email: Email,
        first_name: FirstName,
        last_name: LastName,
        password: RawPassword,
        role: UserRole = UserRole.USER,
        phone_number: Optional[PhoneNumber] = None,
        language: Language = Language("en"),
        address: Optional[Address] = None,
        postal_code: Optional[PostalCode] = None,
        country_id: Optional[CountryId] = None,
        city_id: Optional[CityId] = None,
        subscription: Optional[Subscription] = None,
    ) -> User:
        """
        :raises RoleAssignmentNotPermittedError:
        :raises DomainFieldError:
        """
        if not role.is_assignable:
            raise RoleAssignmentNotPermittedError(role)

        user_id = UserId(self._user_id_generator())
        password_hash = UserPasswordHash(self._password_hasher.hash(password))
        now = datetime.utcnow()
        
        return User(
            id_=user_id,
            email=email,
            first_name=first_name,
            last_name=last_name,
            role=role,
            is_active=UserActive(True),
            is_blocked=UserBlocked(False),
            is_verified=UserVerified(False),
            retry_count=RetryCount(0),
            password=password_hash,
            created_at=CreatedAt(now),
            updated_at=UpdatedAt(now),
            last_login=None,
            profile_picture=None,
            phone_number=phone_number,
            language=language,
            address=address,
            postal_code=postal_code,
            country_id=country_id,
            city_id=city_id,
            subscription=subscription,
        )

    def is_password_valid(self, user: User, raw_password: RawPassword) -> bool:
        return self._password_hasher.verify(
            raw_password=raw_password,
            hashed_password=user.password.value,
        )

    def change_password(self, user: User, raw_password: RawPassword) -> None:
        hashed_password = UserPasswordHash(self._password_hasher.hash(raw_password))
        user.password = hashed_password
        user.updated_at = UpdatedAt(datetime.utcnow())

    def toggle_user_activation(self, user: User, *, is_active: bool) -> None:
        """
        :raises ActivationChangeNotPermittedError:
        """
        if not user.role.is_changeable:
            raise ActivationChangeNotPermittedError(user.email, user.role)
        user.is_active = UserActive(is_active)
        user.updated_at = UpdatedAt(datetime.utcnow())

    def toggle_user_admin_role(self, user: User, *, is_admin: bool) -> None:
        """
        :raises RoleChangeNotPermittedError:
        """
        if not user.role.is_changeable:
            raise RoleChangeNotPermittedError(user.email, user.role)
        user.role = UserRole.ADMIN if is_admin else UserRole.USER
        user.updated_at = UpdatedAt(datetime.utcnow())

    def increment_login_retry_count(self, user: User) -> None:
        """
        Increments the user's failed login retry count and updates timestamp.
        """
        user.retry_count = RetryCount(user.retry_count.value + 1)
        user.updated_at = UpdatedAt(datetime.utcnow())

    def record_successful_login(self, user: User) -> None:
        """
        Resets retry count and sets last login timestamp.
        """
        user.retry_count = RetryCount(0)
        user.last_login = LastLogin(datetime.utcnow())
        user.updated_at = UpdatedAt(datetime.utcnow())
