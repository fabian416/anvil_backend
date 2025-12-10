"""DeFi HTTP controllers."""

from app.presentation.http.controllers.defi.aave_router import create_aave_router
from app.presentation.http.controllers.defi.axelar_router import create_axelar_router
from app.presentation.http.controllers.defi.curve_router import create_curve_router
from app.presentation.http.controllers.defi.hyperliquid_router import create_hyperliquid_router
from app.presentation.http.controllers.defi.layerzero_router import create_layerzero_router
from app.presentation.http.controllers.defi.morpho_router import create_morpho_router

__all__ = [
    "create_aave_router",
    "create_axelar_router",
    "create_curve_router",
    "create_hyperliquid_router",
    "create_layerzero_router",
    "create_morpho_router",
]
