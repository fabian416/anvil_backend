"""ML Controllers"""

from app.presentation.http.controllers.ml.prediction import router as prediction_router
from app.presentation.http.controllers.ml.network import router as network_router

__all__ = [
    "prediction_router",
    "network_router",
]
