from app.application.common.exceptions.authorization import AuthorizationError
from app.application.common.services.authorization.base import (
    Permission,
    PermissionContext,
)
from app.application.common.services.constants import AUTHZ_NOT_AUTHORIZED


def authorize(
    permission: Permission,
    *,
    context: PermissionContext,
) -> None:
    """
    :raises AuthorizationError:
    """
    if not permission.is_satisfied_by(context):
        raise AuthorizationError(AUTHZ_NOT_AUTHORIZED)
