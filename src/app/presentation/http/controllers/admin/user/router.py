from fastapi import APIRouter

from app.presentation.http.controllers.admin.user.activate_user import (
    create_activate_user_router,
)
from app.presentation.http.controllers.admin.user.change_password import (
    create_change_password_router,
)
from app.presentation.http.controllers.admin.user.deactivate_user import (
    create_deactivate_user_router,
)
from app.presentation.http.controllers.admin.user.grant_admin import (
    create_grant_admin_router,
)
from app.presentation.http.controllers.admin.user.list_users import create_list_users_router
from app.presentation.http.controllers.admin.user.revoke_admin import (
    create_revoke_admin_router,
)


def create_users_router() -> APIRouter:
    router = APIRouter(
        prefix="/admin/users",
        tags=["AdminUsers"],
    )

    sub_routers = (
        create_list_users_router(),
        create_change_password_router(),
        create_grant_admin_router(),
        create_revoke_admin_router(),
        create_activate_user_router(),
        create_deactivate_user_router(),
    )

    for sub_router in sub_routers:
        router.include_router(sub_router)

    return router


