"""
Portfolio-specific domain exceptions with standardized error codes.

This module provides all exceptions related to:
- Portfolio management and access
- Asset allocations and positions
- Risk management and rebalancing
"""

from typing import Any
from uuid import UUID

from app.domain.exceptions.base import ApplicationError
from app.domain.exceptions.error_codes import ErrorCode


class PortfolioNotFoundError(ApplicationError):
    """Raised when a portfolio is not found."""

    def __init__(
        self,
        portfolio_id: str | UUID | None = None,
        user_id: str | UUID | None = None,
    ) -> None:
        details = {}
        if portfolio_id:
            details["portfolio_id"] = str(portfolio_id)
        if user_id:
            details["user_id"] = str(user_id)
        super().__init__(ErrorCode.PORT_NOT_FOUND, details=details)


class PortfolioAccessDeniedError(ApplicationError):
    """Raised when user doesn't have access to a portfolio."""

    def __init__(
        self,
        portfolio_id: str | UUID | None = None,
        user_id: str | UUID | None = None,
    ) -> None:
        details = {}
        if portfolio_id:
            details["portfolio_id"] = str(portfolio_id)
        if user_id:
            details["user_id"] = str(user_id)
        super().__init__(ErrorCode.PORT_ACCESS_DENIED, details=details)


class InvalidAllocationError(ApplicationError):
    """Raised when allocation percentages are invalid."""

    def __init__(
        self,
        total_percentage: float | None = None,
        allocations: dict[str, float] | None = None,
    ) -> None:
        details = {}
        if total_percentage is not None:
            details["total_percentage"] = total_percentage
        if allocations:
            details["allocations"] = allocations
        super().__init__(ErrorCode.PORT_INVALID_ALLOCATION, details=details)


class RiskLimitExceededError(ApplicationError):
    """Raised when allocation exceeds risk tolerance."""

    def __init__(
        self,
        risk_score: float | None = None,
        max_risk_score: float | None = None,
        asset: str | None = None,
    ) -> None:
        details = {}
        if risk_score is not None:
            details["risk_score"] = risk_score
        if max_risk_score is not None:
            details["max_risk_score"] = max_risk_score
        if asset:
            details["asset"] = asset
        super().__init__(ErrorCode.PORT_RISK_LIMIT_EXCEEDED, details=details)


class InvalidTimeframeError(ApplicationError):
    """Raised when an invalid time frame is specified."""

    def __init__(
        self,
        timeframe: str | None = None,
        valid_timeframes: list[str] | None = None,
    ) -> None:
        details = {}
        if timeframe:
            details["timeframe"] = timeframe
        if valid_timeframes:
            details["valid_timeframes"] = valid_timeframes
        super().__init__(
            ErrorCode.PORT_INVALID_TIMEFRAME, details=details, field="timeframe"
        )


class RebalanceFailedError(ApplicationError):
    """Raised when portfolio rebalancing fails."""

    def __init__(
        self,
        portfolio_id: str | UUID | None = None,
        reason: str | None = None,
        failed_trades: list[str] | None = None,
    ) -> None:
        details = {}
        if portfolio_id:
            details["portfolio_id"] = str(portfolio_id)
        if reason:
            details["reason"] = reason
        if failed_trades:
            details["failed_trades"] = failed_trades
        super().__init__(ErrorCode.PORT_REBALANCE_FAILED, details=details)


class InvalidPositionError(ApplicationError):
    """Raised when an invalid position is specified."""

    def __init__(
        self,
        position_id: str | UUID | None = None,
        asset: str | None = None,
        reason: str | None = None,
    ) -> None:
        details = {}
        if position_id:
            details["position_id"] = str(position_id)
        if asset:
            details["asset"] = asset
        if reason:
            details["reason"] = reason
        super().__init__(ErrorCode.PORT_INVALID_POSITION, details=details)


# Additional portfolio-specific exceptions


class PortfolioLimitExceededError(ApplicationError):
    """Raised when user has reached maximum portfolios."""

    def __init__(
        self,
        current_count: int | None = None,
        max_allowed: int | None = None,
    ) -> None:
        details = {}
        if current_count is not None:
            details["current_count"] = current_count
        if max_allowed is not None:
            details["max_allowed"] = max_allowed
        super().__init__(
            ErrorCode.PORT_ACCESS_DENIED,
            details=details,
            override_message="Maximum portfolio limit reached",
        )


class PositionNotFoundError(ApplicationError):
    """Raised when a position is not found."""

    def __init__(
        self,
        position_id: str | UUID | None = None,
        portfolio_id: str | UUID | None = None,
        asset: str | None = None,
    ) -> None:
        details = {}
        if position_id:
            details["position_id"] = str(position_id)
        if portfolio_id:
            details["portfolio_id"] = str(portfolio_id)
        if asset:
            details["asset"] = asset
        super().__init__(
            ErrorCode.PORT_NOT_FOUND,
            details=details,
            override_message="Position not found",
        )


class InsufficientPositionError(ApplicationError):
    """Raised when position size is insufficient for operation."""

    def __init__(
        self,
        asset: str | None = None,
        required: float | None = None,
        available: float | None = None,
    ) -> None:
        details = {}
        if asset:
            details["asset"] = asset
        if required is not None:
            details["required"] = required
        if available is not None:
            details["available"] = available
        super().__init__(
            ErrorCode.PORT_INVALID_POSITION,
            details=details,
            override_message="Insufficient position size",
        )


class PortfolioLockedError(ApplicationError):
    """Raised when portfolio is locked for modifications."""

    def __init__(
        self,
        portfolio_id: str | UUID | None = None,
        reason: str | None = None,
        locked_until: str | None = None,
    ) -> None:
        details = {}
        if portfolio_id:
            details["portfolio_id"] = str(portfolio_id)
        if reason:
            details["reason"] = reason
        if locked_until:
            details["locked_until"] = locked_until
        super().__init__(
            ErrorCode.PORT_ACCESS_DENIED,
            details=details,
            override_message="Portfolio is locked for modifications",
        )


class DuplicateAssetError(ApplicationError):
    """Raised when trying to add duplicate asset to portfolio."""

    def __init__(
        self,
        asset: str | None = None,
        portfolio_id: str | UUID | None = None,
    ) -> None:
        details = {}
        if asset:
            details["asset"] = asset
        if portfolio_id:
            details["portfolio_id"] = str(portfolio_id)
        super().__init__(
            ErrorCode.PORT_INVALID_ALLOCATION,
            details=details,
            override_message="Asset already exists in portfolio",
        )


class PerformanceDataUnavailableError(ApplicationError):
    """Raised when performance data is not available."""

    def __init__(
        self,
        portfolio_id: str | UUID | None = None,
        timeframe: str | None = None,
    ) -> None:
        details = {}
        if portfolio_id:
            details["portfolio_id"] = str(portfolio_id)
        if timeframe:
            details["timeframe"] = timeframe
        super().__init__(
            ErrorCode.PORT_INVALID_TIMEFRAME,
            details=details,
            override_message="Performance data not available for requested period",
        )
