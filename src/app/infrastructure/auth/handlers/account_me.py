from dataclasses import dataclass
from datetime import datetime
from typing import TypedDict

from sqlalchemy import Select, select
from sqlalchemy.exc import SQLAlchemyError

from app.application.common.ports.country_query_gateway import CountryQueryGateway
from app.application.common.ports.city_query_gateway import CityQueryGateway
from app.application.common.ports.flusher import Flusher
from app.application.common.ports.transaction_manager import TransactionManager
from app.application.common.ports.user_command_gateway import UserCommandGateway
from app.application.common.services.current_user import CurrentUserService
from app.domain.value_objects.first_name import FirstName
from app.domain.value_objects.last_name import LastName
from app.domain.value_objects.phone_number import PhoneNumber
from app.domain.value_objects.profile_picture import ProfilePicture
from app.domain.value_objects.language import Language
from app.domain.value_objects.address import Address
from app.domain.value_objects.postal_code import PostalCode
from app.domain.value_objects.country_id import CountryId
from app.domain.value_objects.city_id import CityId
from app.domain.value_objects.updated_at import UpdatedAt
from app.infrastructure.adapters.types import MainAsyncSession
from app.infrastructure.exceptions.gateway import DataMapperError
from app.infrastructure.adapters.constants import DB_QUERY_FAILED
from app.infrastructure.persistence_sqla.mappings.country import map_countries_table
from app.infrastructure.persistence_sqla.mappings.city import map_cities_table
from app.infrastructure.persistence_sqla.registry import mapping_registry


class MeResponse(TypedDict, total=False):
    id: int
    email: str
    first_name: str
    last_name: str
    role: str
    is_active: bool
    is_blocked: bool
    is_verified: bool
    retry_count: int
    profile_picture: str | None
    phone_number: str | None
    last_login: str | None
    country_id: int | None
    country_name: str | None
    country_code: str | None
    city_id: int | None
    city_name: str | None
    language: str
    subscription: str | None


class GetMeHandler:
    def __init__(self, current_user_service: CurrentUserService, session: MainAsyncSession):
        self._current_user_service = current_user_service
        self._session = session

    async def execute(self) -> MeResponse:
        user = await self._current_user_service.get_current_user()

        # Enrich with country/city names
        map_countries_table()
        map_cities_table()
        country_name: str | None = None
        country_code: str | None = None
        city_name: str | None = None
        try:
            Countries = mapping_registry.metadata.tables["countries"]  # type: ignore
            Cities = mapping_registry.metadata.tables["cities"]  # type: ignore
            if user.country_id is not None:
                stmt_c: Select = select(Countries.c.name, Countries.c.iso2).where(
                    Countries.c.id == user.country_id.value
                )
                c_row = (await self._session.execute(stmt_c)).first()
                if c_row:
                    country_name = c_row[0]
                    country_code = c_row[1]
            if user.city_id is not None:
                stmt_city: Select = select(Cities.c.name).where(
                    Cities.c.id == user.city_id.value
                )
                ct_row = (await self._session.execute(stmt_city)).first()
                if ct_row:
                    city_name = ct_row[0]
        except SQLAlchemyError as error:
            raise DataMapperError(DB_QUERY_FAILED) from error

        return MeResponse(
            id=user.id_.value,
            email=user.email.value,
            first_name=user.first_name.value,
            last_name=user.last_name.value,
            role=user.role.value,
            is_active=user.is_active.value,
            is_blocked=user.is_blocked.value,
            is_verified=user.is_verified.value,
            retry_count=user.retry_count.value,
            profile_picture=user.profile_picture.value if user.profile_picture else None,
            phone_number=user.phone_number.value if user.phone_number else None,
            last_login=user.last_login.value.isoformat() if user.last_login else None,
            country_id=user.country_id.value if user.country_id else None,
            country_name=country_name,
            country_code=country_code,
            city_id=user.city_id.value if user.city_id else None,
            city_name=city_name,
            language=user.language.value,
            subscription=user.subscription.value if user.subscription else None,
        )


@dataclass(frozen=True, slots=True)
class UpdateMeRequest:
    first_name: str | None = None
    last_name: str | None = None
    phone_number: str | None = None
    profile_picture: str | None = None
    language: str | None = None
    address: str | None = None
    postal_code: str | None = None
    country_id: int | None = None
    city_id: int | None = None


class UpdateMeHandler:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        user_command_gateway: UserCommandGateway,
        flusher: Flusher,
        transaction_manager: TransactionManager,
        country_query_gateway: CountryQueryGateway,
        city_query_gateway: CityQueryGateway,
        session: MainAsyncSession,
    ) -> None:
        self._current_user_service = current_user_service
        self._user_command_gateway = user_command_gateway
        self._flusher = flusher
        self._tx = transaction_manager
        self._country_q = country_query_gateway
        self._city_q = city_query_gateway
        self._session = session

    async def execute(self, request: UpdateMeRequest) -> MeResponse:
        user = await self._current_user_service.get_current_user()

        # Optional updates
        if request.first_name is not None:
            user.first_name = FirstName(request.first_name)
        if request.last_name is not None:
            user.last_name = LastName(request.last_name)
        if request.phone_number is not None:
            user.phone_number = PhoneNumber(request.phone_number)
        if request.profile_picture is not None:
            user.profile_picture = ProfilePicture(request.profile_picture)
        if request.language is not None:
            user.language = Language(request.language)
        if request.address is not None:
            user.address = Address(request.address)
        if request.postal_code is not None:
            user.postal_code = PostalCode(request.postal_code)

        # Country/City validation
        if request.country_id is not None:
            exists = await self._country_q.exists(request.country_id)
            if not exists:
                # Surface as 400 in controller via DomainFieldError or explicit exceptions if defined
                raise ValueError("Invalid country ID")
            user.country_id = CountryId(request.country_id)
            # Reset city if mismatch
            if user.city_id is not None:
                # verify belongs
                if not await self._city_q.exists_in_country(user.city_id.value, user.country_id.value):
                    user.city_id = None
        if request.city_id is not None and (user.country_id is not None):
            exists_city = await self._city_q.exists_in_country(request.city_id, user.country_id.value)
            if not exists_city:
                raise ValueError("City does not belong to selected country")
            user.city_id = CityId(request.city_id)

        user.updated_at = UpdatedAt(datetime.utcnow())

        # Persist
        await self._user_command_gateway.update(user)
        await self._tx.commit()

        # Return enriched response
        return await GetMeHandler(self._current_user_service, self._session).execute()


