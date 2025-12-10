"""
Wallet Router
FastAPI router for wallet endpoints.

Endpoints:
- GET /wallet/me - Get all wallets for the current user
- POST /wallet/sync - Sync wallets from frontend
- POST /wallet/export - Export wallet private key (HPKE encrypted)
"""

from fastapi import APIRouter


def create_wallet_router() -> APIRouter:
    """Create and configure the wallet router."""
    # Import here to avoid circular imports
    from app.presentation.http.controllers.wallet.export_wallet import router as export_router
    from app.presentation.http.controllers.wallet.my_wallets import create_my_wallets_router
    
    main_router = APIRouter(prefix="/wallet", tags=["wallet"])
    
    # Include the my_wallets router (GET /me, POST /sync)
    main_router.include_router(create_my_wallets_router())
    
    # Include the export router (POST /export)
    main_router.include_router(export_router)
    
    return main_router


# Keep a simple router for the endpoint file to use
router = APIRouter(tags=["wallet"])

