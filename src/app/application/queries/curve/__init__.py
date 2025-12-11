"""Curve Finance application queries."""

from app.application.queries.curve.get_gauges import GetGauges, GetGaugesRequest
from app.application.queries.curve.get_pool_apy import GetPoolAPY, GetPoolAPYRequest
from app.application.queries.curve.get_pools import GetPools, GetPoolsRequest
from app.application.queries.curve.get_tvl import GetTVL, GetTVLRequest

__all__ = [
    "GetPools",
    "GetPoolsRequest",
    "GetPoolAPY",
    "GetPoolAPYRequest",
    "GetGauges",
    "GetGaugesRequest",
    "GetTVL",
    "GetTVLRequest",
]
