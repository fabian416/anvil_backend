"""Graph controllers"""

from .search import router as search_router
from .analytics import router as analytics_router

__all__ = ["search_router", "analytics_router"]
