from dataclasses import dataclass
from uuid import UUID

from app.domain.value_objects.base import ValueObject


@dataclass(frozen=True, repr=False)
class ConversationId(ValueObject):
    value: UUID
