from fastapi import APIRouter

from app.presentation.http.controllers.account.email_verification import create_email_verification_router
from app.presentation.http.controllers.account.password_reset import create_password_reset_router
from app.presentation.http.controllers.account.change_password import create_change_own_password_router
from fastapi import APIRouter

from app.presentation.http.controllers.account.log_in import create_log_in_router
from app.presentation.http.controllers.account.log_out import (
    create_log_out_router,
)
from app.presentation.http.controllers.account.sign_up import (
    create_sign_up_router,
)
from app.presentation.http.controllers.account.refresh_token import (
    create_refresh_token_router,
)
from app.presentation.http.controllers.account.email_verification import (
    create_email_verification_router,
)
from app.presentation.http.controllers.account.me import create_me_router


def create_account_router() -> APIRouter:
    router = APIRouter(
        prefix="/account",
        tags=["Account"],
    )

    sub_routers = (
        create_sign_up_router(),
        create_log_in_router(),
        create_log_out_router(),
        create_refresh_token_router(),
        create_email_verification_router(),
        create_me_router(),
        create_password_reset_router(),
        create_change_own_password_router(),
    )

    for sub_router in sub_routers:
        router.include_router(sub_router)

    return router
