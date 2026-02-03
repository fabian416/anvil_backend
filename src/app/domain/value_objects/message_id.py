from dataclasses import dataclass
from uuid import UUID

from app.domain.value_objects.base import ValueObject


@dataclass(frozen=True, repr=False)
class MessageId(ValueObject):
    value: UUID
