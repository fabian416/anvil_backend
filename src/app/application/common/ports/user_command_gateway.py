from abc import abstractmethod
from typing import Protocol

from app.domain.entities.user import User
from app.domain.value_objects.user_id import UserId
from app.domain.value_objects.email import Email


class UserCommandGateway(Protocol):
    @abstractmethod
    async def add(self, user: User) -> None:
        """
        :raises DataMapperError:
        """

    @abstractmethod
    async def update(self, user: User) -> None:
        """
        :raises DataMapperError:
        """

    @abstractmethod
    async def read_by_id(self, user_id: UserId) -> User | None:
        """
        :raises DataMapperError:
        """

    @abstractmethod
    async def read_by_email(
        self,
        email: Email,
        for_update: bool = False,
    ) -> User | None:
        """
        :raises DataMapperError:
        """
