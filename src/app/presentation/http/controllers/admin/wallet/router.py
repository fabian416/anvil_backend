"""
Admin Wallet Router

FastAPI router for admin wallet management endpoints.

Endpoints:
- GET /admin/wallets/{privy_wallet_id} - Get wallet details
- PATCH /admin/wallets/{privy_wallet_id} - Update wallet configuration
"""

from fastapi import APIRouter

from app.presentation.http.controllers.admin.wallet.get_wallet_details import (
    create_get_wallet_details_router,
)
from app.presentation.http.controllers.admin.wallet.update_wallet import (
    create_update_wallet_router,
)


def create_admin_wallet_router() -> APIRouter:
    """Create and configure the admin wallet router."""
    router = APIRouter(
        prefix="/admin/wallets",
        tags=["AdminWallets"],
    )

    sub_routers = (
        create_get_wallet_details_router(),
        create_update_wallet_router(),
    )

    for sub_router in sub_routers:
        router.include_router(sub_router)

    return router
