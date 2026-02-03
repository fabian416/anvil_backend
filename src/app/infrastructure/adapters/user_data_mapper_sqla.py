from sqlalchemy import Select, select
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from app.application.common.ports.user_command_gateway import UserCommandGateway
from app.domain.entities.user import User
from app.domain.value_objects.user_id import UserId
from app.domain.value_objects.email import Email
from app.domain.value_objects.first_name import FirstName
from app.domain.value_objects.last_name import LastName
from app.domain.value_objects.user_status import UserActive, UserBlocked, UserVerified
from app.domain.value_objects.retry_count import RetryCount
from app.domain.value_objects.user_password_hash import UserPasswordHash
from app.domain.value_objects.created_at import CreatedAt
from app.domain.value_objects.updated_at import UpdatedAt
from app.domain.value_objects.last_login import LastLogin
from app.domain.value_objects.profile_picture import ProfilePicture
from app.domain.value_objects.phone_number import PhoneNumber
from app.domain.value_objects.language import Language
from app.domain.value_objects.address import Address
from app.domain.value_objects.postal_code import PostalCode
from app.domain.value_objects.country_id import CountryId
from app.domain.value_objects.city_id import CityId
from app.domain.value_objects.subscription import Subscription
from app.domain.value_objects.privy_user_id import PrivyUserId
from app.domain.value_objects.wallet_address import WalletAddress
from app.domain.value_objects.auth_provider import AuthProvider
from app.domain.value_objects.ip_address import IpAddress
from app.domain.enums.user_role import UserRole
from app.infrastructure.adapters.constants import (
    DB_QUERY_FAILED,
    DB_CONSTRAINT_VIOLATION,
)
from app.infrastructure.adapters.types import MainAsyncSession
from app.infrastructure.exceptions.gateway import DataMapperError
from app.infrastructure.persistence_sqla.mappings.user import map_users_table
from app.infrastructure.persistence_sqla.registry import mapping_registry
from app.domain.exceptions.user import EmailAlreadyExistsError


class SqlaUserDataMapper(UserCommandGateway):
    def __init__(self, session: MainAsyncSession):
        self._session = session

    async def add(self, user: User) -> None:
        """
        :raises DataMapperError:
        """
        try:
            # Insert explicitly into users table and set generated id on domain entity
            map_users_table()
            UsersTable = mapping_registry.metadata.tables["users"]  # type: ignore
            # Handle password - it can be None for Privy-only users
            password_value = None
            if user.password and user.password.value:
                password_value = user.password.value.decode("utf-8", errors="ignore")

            values = {
                "email": user.email.value,
                "first_name": user.first_name.value,
                "last_name": user.last_name.value,
                "role": user.role.value,
                "is_active": user.is_active.value,
                "is_blocked": user.is_blocked.value,
                "is_verified": user.is_verified.value,
                "retry_count": user.retry_count.value,
                "password": password_value,
                "profile_picture": user.profile_picture.value
                if user.profile_picture
                else None,
                "phone_number": user.phone_number.value if user.phone_number else None,
                "language": user.language.value,
                "address": user.address.value if user.address else None,
                "postal_code": user.postal_code.value if user.postal_code else None,
                "country_id": user.country_id.value if user.country_id else None,
                "city_id": user.city_id.value if user.city_id else None,
                "subscription": user.subscription.value if user.subscription else None,
                # Privy fields
                "privy_user_id": user.privy_user_id.value
                if user.privy_user_id
                else None,
                "primary_wallet_address": user.primary_wallet_address.value
                if user.primary_wallet_address
                else None,
                "auth_provider": user.auth_provider.value
                if user.auth_provider
                else "email",
                # IP tracking fields
                "last_ip": user.last_ip.value if user.last_ip else None,
                "registration_ip": user.registration_ip.value
                if user.registration_ip
                else None,
            }
            insert_stmt = (
                UsersTable.insert().values(**values).returning(UsersTable.c.id)
            )
            result = await self._session.execute(insert_stmt)
            new_id = result.scalar_one()
            # Assign generated id back to domain entity if placeholder
            if getattr(user.id_, "value", None) in (None, 0):
                user.id_ = UserId(new_id)

        except IntegrityError as error:
            if "email" in str(error).lower():
                raise EmailAlreadyExistsError(user.email.value) from error
            raise DataMapperError(DB_CONSTRAINT_VIOLATION) from error
        except SQLAlchemyError as error:
            raise DataMapperError(DB_QUERY_FAILED) from error

    async def update(self, user: User) -> None:
        try:
            map_users_table()
            UsersTable = mapping_registry.metadata.tables["users"]  # type: ignore

            update_values = {
                "first_name": user.first_name.value,
                "last_name": user.last_name.value,
                "role": user.role.value,
                "is_active": user.is_active.value,
                "is_blocked": user.is_blocked.value,
                "is_verified": user.is_verified.value,
                "retry_count": user.retry_count.value,
                "profile_picture": user.profile_picture.value
                if user.profile_picture
                else None,
                "phone_number": user.phone_number.value if user.phone_number else None,
                "language": user.language.value,
                "address": user.address.value if user.address else None,
                "postal_code": user.postal_code.value if user.postal_code else None,
                "country_id": user.country_id.value if user.country_id else None,
                "city_id": user.city_id.value if user.city_id else None,
                "last_login": user.last_login.value if user.last_login else None,
                "updated_at": user.updated_at.value,
                # Privy fields
                "privy_user_id": user.privy_user_id.value
                if user.privy_user_id
                else None,
                "primary_wallet_address": user.primary_wallet_address.value
                if user.primary_wallet_address
                else None,
                "auth_provider": user.auth_provider.value
                if user.auth_provider
                else None,
                # IP tracking - only update last_ip (registration_ip is immutable)
                "last_ip": user.last_ip.value if user.last_ip else None,
            }

            # Only update password if it's a valid bcrypt hash (starts with $2)
            # This prevents overwriting valid passwords with empty ones from Privy users
            if user.password and user.password.value:
                password_str = user.password.value.decode("utf-8", errors="ignore")
                if password_str.startswith("$2"):  # Valid bcrypt hash
                    update_values["password"] = password_str

            await self._session.execute(
                UsersTable.update()
                .where(UsersTable.c.id == user.id_.value)
                .values(**update_values)
            )
        except SQLAlchemyError as error:
            raise DataMapperError(DB_QUERY_FAILED) from error

    async def read_by_id(self, user_id: UserId) -> User | None:
        """
        :raises DataMapperError:
        """
        try:
            UsersTable = mapping_registry.metadata.tables["users"]  # type: ignore
            select_stmt: Select = select(UsersTable).where(
                UsersTable.c.id == user_id.value
            )
            row = (await self._session.execute(select_stmt)).mappings().first()
            return self._row_to_user(row) if row else None
        except SQLAlchemyError as error:
            raise DataMapperError(DB_QUERY_FAILED) from error

    async def read_by_email(
        self,
        email: Email,
        for_update: bool = False,
    ) -> User | None:
        """
        :raises DataMapperError:
        """
        try:
            UsersTable = mapping_registry.metadata.tables["users"]  # type: ignore
            select_stmt: Select = select(UsersTable).where(
                UsersTable.c.email == email.value
            )
            if for_update:
                select_stmt = select_stmt.with_for_update()
            row = (await self._session.execute(select_stmt)).mappings().first()
            return self._row_to_user(row) if row else None
        except SQLAlchemyError as error:
            raise DataMapperError(DB_QUERY_FAILED) from error

    async def read_by_privy_user_id(
        self,
        privy_user_id: PrivyUserId,
        for_update: bool = False,
    ) -> User | None:
        """
        Find user by Privy user ID.

        :raises DataMapperError:
        """
        try:
            UsersTable = mapping_registry.metadata.tables["users"]  # type: ignore
            select_stmt: Select = select(UsersTable).where(
                UsersTable.c.privy_user_id == privy_user_id.value
            )
            if for_update:
                select_stmt = select_stmt.with_for_update()
            row = (await self._session.execute(select_stmt)).mappings().first()
            return self._row_to_user(row) if row else None
        except SQLAlchemyError as error:
            raise DataMapperError(DB_QUERY_FAILED) from error

    async def read_by_wallet_address(
        self,
        wallet_address: WalletAddress,
        for_update: bool = False,
    ) -> User | None:
        """
        Find user by primary wallet address.

        :raises DataMapperError:
        """
        try:
            UsersTable = mapping_registry.metadata.tables["users"]  # type: ignore
            select_stmt: Select = select(UsersTable).where(
                UsersTable.c.primary_wallet_address == wallet_address.value
            )
            if for_update:
                select_stmt = select_stmt.with_for_update()
            row = (await self._session.execute(select_stmt)).mappings().first()
            return self._row_to_user(row) if row else None
        except SQLAlchemyError as error:
            raise DataMapperError(DB_QUERY_FAILED) from error

    @staticmethod
    def _row_to_user(row: dict | None) -> User | None:
        if not row:
            return None

        # Handle password - it can be None for Privy-only users
        password_value = b""
        if row.get("password"):
            password_value = str(row["password"]).encode("utf-8")

        # row is a Mapping with keys matching users table columns
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
            password=UserPasswordHash(password_value),
            created_at=CreatedAt(row["created_at"]),
            updated_at=UpdatedAt(row["updated_at"]),
            last_login=LastLogin(row["last_login"]) if row.get("last_login") else None,
            profile_picture=ProfilePicture(row["profile_picture"])
            if row.get("profile_picture")
            else None,
            phone_number=PhoneNumber(row["phone_number"])
            if row.get("phone_number")
            else None,
            language=Language(str(row["language"]))
            if row.get("language")
            else Language("en"),
            address=Address(row["address"]) if row.get("address") else None,
            postal_code=PostalCode(row["postal_code"])
            if row.get("postal_code")
            else None,
            country_id=CountryId(int(row["country_id"]))
            if row.get("country_id") is not None
            else None,
            city_id=CityId(int(row["city_id"]))
            if row.get("city_id") is not None
            else None,
            subscription=Subscription(row["subscription"])
            if row.get("subscription")
            else None,
            # Privy fields
            privy_user_id=PrivyUserId(row["privy_user_id"])
            if row.get("privy_user_id")
            else None,
            primary_wallet_address=WalletAddress(row["primary_wallet_address"])
            if row.get("primary_wallet_address")
            else None,
            auth_provider=AuthProvider(row["auth_provider"])
            if row.get("auth_provider")
            else None,
            # IP tracking fields
            last_ip=IpAddress.from_optional(row.get("last_ip")),
            registration_ip=IpAddress.from_optional(row.get("registration_ip")),
        )
