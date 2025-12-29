"""Auto-Executor API endpoints.

REST API for automated arbitrage execution.
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from typing import Dict, Optional

from app.application.ultra.auto_executor import AutoExecutor


class ConfigUpdateRequest(BaseModel):
    """Request model for config update."""

    min_profit_usd: Optional[float] = Field(None, description="Minimum profit USD")
    scan_interval_seconds: Optional[int] = Field(None, description="Scan interval seconds")
    max_gas_price_gwei: Optional[int] = Field(None, description="Max gas price gwei")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "min_profit_usd": 75.0,
            "scan_interval_seconds": 10,
            "max_gas_price_gwei": 120,
        }
    })


def create_auto_executor_router() -> APIRouter:
    """Create auto-executor router.

    Returns:
        Configured FastAPI router
    """
    router = APIRouter(prefix="/user/ultra/auto-executor", tags=["ultra-auto-executor"])

    # Global auto-executor instance
    _auto_executor = AutoExecutor()

    @router.post("/start", response_model=Dict, summary="Start auto-executor")
    async def start_executor() -> Dict:
        """Start automated arbitrage execution."""
        return await _auto_executor.start()

    @router.post("/stop", response_model=Dict, summary="Stop auto-executor")
    async def stop_executor() -> Dict:
        """Stop automated arbitrage execution."""
        return await _auto_executor.stop()

    @router.post("/pause", response_model=Dict, summary="Pause auto-executor")
    async def pause_executor() -> Dict:
        """Pause automated execution."""
        return await _auto_executor.pause()

    @router.post("/resume", response_model=Dict, summary="Resume auto-executor")
    async def resume_executor() -> Dict:
        """Resume automated execution."""
        return await _auto_executor.resume()

    @router.get("/status", response_model=Dict, summary="Get status")
    async def get_status() -> Dict:
        """Get auto-executor status."""
        return _auto_executor.get_status()

    @router.put("/config", response_model=Dict, summary="Update configuration")
    async def update_config(request: ConfigUpdateRequest) -> Dict:
        """Update auto-executor configuration."""
        return _auto_executor.update_config(**request.dict(exclude_none=True))

    @router.post("/scan", response_model=Dict, summary="Manual scan")
    async def manual_scan() -> Dict:
        """Manually trigger opportunity scan and execution."""
        return await _auto_executor.scan_and_execute()

    return router
