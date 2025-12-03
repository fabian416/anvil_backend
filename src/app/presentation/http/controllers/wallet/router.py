"""
Wallet Router
FastAPI router for wallet endpoints.
"""

from fastapi import APIRouter


def create_wallet_router() -> APIRouter:
    """Create and configure the wallet router."""
    # Import here to avoid circular imports
    from app.presentation.http.controllers.wallet.export_wallet import router as export_router
    
    main_router = APIRouter(prefix="/wallet", tags=["wallet"])
    main_router.include_router(export_router)
    
    return main_router


# Keep a simple router for the endpoint file to use
router = APIRouter(tags=["wallet"])

