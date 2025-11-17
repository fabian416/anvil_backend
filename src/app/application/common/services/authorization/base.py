from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, TypeVar


@dataclass(frozen=True)
class PermissionContext:
    pass


ContextT = TypeVar("ContextT", bound=PermissionContext)


class Permission(ABC, Generic[ContextT]):
    @abstractmethod
    def is_satisfied_by(self, context: ContextT) -> bool: ...
