"""
Admin Policies Router

FastAPI router for admin Privy policy management endpoints.
"""

from fastapi import APIRouter

from app.presentation.http.controllers.admin.policies.create_policy import (
    create_create_policy_router,
)
from app.presentation.http.controllers.admin.policies.get_policy import (
    create_get_policy_router,
)
from app.presentation.http.controllers.admin.policies.list_policies import (
    create_list_policies_router,
)
from app.presentation.http.controllers.admin.policies.policy_rules import (
    create_policy_rules_router,
)
from app.presentation.http.controllers.admin.policies.update_policy import (
    create_update_policy_router,
)


def create_admin_policies_router() -> APIRouter:
    router = APIRouter(prefix="/admin/policies", tags=["AdminPolicies"])

    sub_routers = (
        create_list_policies_router(),
        create_create_policy_router(),
        create_get_policy_router(),
        create_update_policy_router(),
        create_policy_rules_router(),
    )

    for sub_router in sub_routers:
        router.include_router(sub_router)

    return router

