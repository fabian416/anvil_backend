from dataclasses import dataclass
from typing import Optional

from app.domain.value_objects.base import ValueObject

@dataclass(frozen=True, repr=False)
class MessageContent(ValueObject):
    value: str
