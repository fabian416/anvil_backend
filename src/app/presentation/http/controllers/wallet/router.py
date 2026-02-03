"""
Wallet Router
FastAPI router for wallet endpoints.

Endpoints:
- GET /wallet/me - Get all wallets for the current user
- POST /wallet/sync - Sync wallets from frontend
- POST /wallet/export - Export wallet private key (HPKE encrypted)
- POST /wallet/swaps/complete - Save completed swap transaction
"""

from fastapi import APIRouter


def create_wallet_router() -> APIRouter:
    """Create and configure the wallet router."""
    # Import here to avoid circular imports
    from app.presentation.http.controllers.wallet.complete_swap import (
        router as complete_swap_router,
    )

    # from app.presentation.http.controllers.wallet.execute_swap import router as execute_swap_router
    from app.presentation.http.controllers.wallet.export_wallet import (
        router as export_router,
    )
    from app.presentation.http.controllers.wallet.my_wallets import (
        create_my_wallets_router,
    )

    main_router = APIRouter(prefix="/wallet", tags=["wallet"])

    # Include the my_wallets router (GET /me, POST /sync)
    main_router.include_router(create_my_wallets_router())

    # Include the export router (POST /export)
    main_router.include_router(export_router)

    # Include the execute swap router (POST /swaps/quote)
    # NOTE: Temporarily disabled - swap quotes are handled via chat flow
    # main_router.include_router(execute_swap_router)

    # Include the complete swap router (POST /swaps/complete)
    main_router.include_router(complete_swap_router)

    return main_router


# Keep a simple router for the endpoint file to use
router = APIRouter(tags=["wallet"])
