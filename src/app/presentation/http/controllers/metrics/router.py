"""
Router for metrics endpoints.
"""

from fastapi_error_map import ErrorAwareRouter

router = ErrorAwareRouter(prefix="/metrics", tags=["Metrics"])

# Import controllers to register routes
from app.presentation.http.controllers.metrics import track_event  # noqa: F401, E402
from app.presentation.http.controllers.metrics import get_metrics  # noqa: F401, E402
