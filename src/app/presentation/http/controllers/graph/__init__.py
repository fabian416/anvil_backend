"""Graph controllers"""

from .search import router as search_router
from .analytics import router as analytics_router
from .monitoring import router as monitoring_router

__all__ = ["search_router", "analytics_router", "monitoring_router"]
