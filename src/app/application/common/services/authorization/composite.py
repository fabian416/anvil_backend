from app.application.common.services.authorization.base import (
    Permission,
    PermissionContext,
)


class AnyOf(Permission):
    def __init__(self, *permissions: Permission) -> None:
        self._permissions = permissions

    def is_satisfied_by(self, context: PermissionContext) -> bool:
        return any(p.is_satisfied_by(context) for p in self._permissions)
