from abc import abstractmethod
from typing import Protocol
from datetime import datetime


class SubscriptionRepository(Protocol):
    @abstractmethod
    async def read_by_name(self, name: str) -> dict | None: ...

    @abstractmethod
    async def read_all(self) -> list[dict]: ...

    @abstractmethod
    async def read_by_id(self, id_: int) -> dict | None: ...

    @abstractmethod
    async def add(
        self,
        *,
        name: str,
        price: float,
        subscription_type: str,
        currency: str,
        duration: int,
        features: dict | None,
        is_active: bool,
        stripe_price_id: str | None,
        stripe_product_id: str | None,
        created_at: datetime,
        updated_at: datetime,
    ) -> int: ...

    @abstractmethod
    async def update_stripe_ids(self, *, id_: int, stripe_price_id: str, stripe_product_id: str) -> None: ...


class SubscriptionUserRepository(Protocol):
    @abstractmethod
    async def add(
        self,
        *,
        user_id: int,
        subscription_id: int,
        status: str,
        data_json: dict | None,
    ) -> int: ...

    @abstractmethod
    async def read_for_user_by_id(self, *, id_: int, user_id: int) -> dict | None: ...

    @abstractmethod
    async def update_status(self, *, id_: int, status: str) -> None: ...

    @abstractmethod
    async def update_stripe_subscription_id(self, *, id_: int, stripe_subscription_id: str) -> None: ...

    @abstractmethod
    async def read_by_checkout_session_id(self, *, session_id: str) -> dict | None: ...

    @abstractmethod
    async def update_data_json(self, *, id_: int, data_json: dict) -> None: ...

    @abstractmethod
    async def read_active_for_user_and_subscription(
        self, *, user_id: int, subscription_id: int
    ) -> dict | None: ...


class PaymentRepository(Protocol):
    @abstractmethod
    async def add(
        self,
        *,
        user_id: int,
        subscription_id: int | None,
        subscription_user_id: int | None,
        amount: float | None,
        currency: str,
        status: str,
        stripe_payment_intent_id: str | None,
        data_json: dict | None,
    ) -> int: ...

    @abstractmethod
    async def find_pending_for_subscription_user(self, *, subscription_user_id: int) -> dict | None: ...

    @abstractmethod
    async def update_status(self, *, id_: int, status: str) -> None: ...

    @abstractmethod
    async def list_by_subscription_user(self, *, subscription_user_id: int) -> list[dict]: ...

    @abstractmethod
    async def update_data_json(self, *, id_: int, data_json: dict) -> None: ...

    @abstractmethod
    async def read_by_user_paginated(self, *, user_id: int, offset: int, limit: int) -> list[dict]: ...

    @abstractmethod
    async def find_or_create_transaction(
        self,
        *,
        user_id: int,
        amount: float,
        currency: str,
        description: str,
    ) -> dict: ...


