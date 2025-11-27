from abc import abstractmethod
from typing import Protocol

from app.domain.entities.user import User
from app.domain.value_objects.email import Email
from app.domain.value_objects.privy_user_id import PrivyUserId
from app.domain.value_objects.user_id import UserId
from app.domain.value_objects.wallet_address import WalletAddress


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

    @abstractmethod
    async def read_by_privy_user_id(
        self,
        privy_user_id: PrivyUserId,
        for_update: bool = False,
    ) -> User | None:
        """
        Find user by Privy user ID.
        
        :raises DataMapperError:
        """

    @abstractmethod
    async def read_by_wallet_address(
        self,
        wallet_address: WalletAddress,
        for_update: bool = False,
    ) -> User | None:
        """
        Find user by primary wallet address.
        
        :raises DataMapperError:
        """
