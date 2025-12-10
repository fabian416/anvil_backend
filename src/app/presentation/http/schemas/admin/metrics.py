"""
Admin Metrics Schemas.

Pydantic models for admin analytics/metrics API responses.
"""

from datetime import datetime

from pydantic import BaseModel, Field

# ============================================================
# Time Series Data Points
# ============================================================


class TimeSeriesDataPoint(BaseModel):
    """Single data point in a time series."""

    date: datetime = Field(..., description="Date/timestamp for this data point")
    value: int = Field(..., description="Count or value at this point")


class TimeSeriesWithChain(BaseModel):
    """Time series data point with chain information."""

    date: datetime = Field(..., description="Date/timestamp for this data point")
    chain: str = Field(..., description="Chain identifier")
    value: int = Field(..., description="Count or value at this point")


# ============================================================
# Overview Metrics
# ============================================================


class WalletOverviewMetrics(BaseModel):
    """Wallet-related overview metrics."""

    total_wallets: int = Field(..., description="Total number of wallets")
    active_wallets: int = Field(..., description="Number of active wallets")
    privy_wallets: int = Field(..., description="Wallets from Privy provider")
    imported_wallets: int = Field(..., description="Imported wallets")
    external_wallets: int = Field(..., description="External wallets")


class TransactionOverviewMetrics(BaseModel):
    """Transaction-related overview metrics."""

    total_transactions: int = Field(..., description="Total number of transactions")
    pending_transactions: int = Field(..., description="Pending transactions")
    successful_transactions: int = Field(..., description="Successful transactions")
    failed_transactions: int = Field(..., description="Failed transactions")


class UserOverviewMetrics(BaseModel):
    """User activity overview metrics."""

    total_users: int = Field(..., description="Total registered users in the system")
    total_users_with_transactions: int = Field(
        ..., description="Users who have made at least one transaction"
    )
    active_users_today: int = Field(
        ..., description="Users active today (made a transaction)"
    )
    active_users_7d: int = Field(..., description="Users active in the last 7 days")
    active_users_30d: int = Field(..., description="Users active in the last 30 days")


class AdminMetricsOverview(BaseModel):
    """High-level admin metrics overview."""

    wallets: WalletOverviewMetrics = Field(..., description="Wallet metrics")
    transactions: TransactionOverviewMetrics = Field(
        ..., description="Transaction metrics"
    )
    users: UserOverviewMetrics = Field(..., description="User activity metrics")
    generated_at: datetime = Field(..., description="When these metrics were generated")

    class Config:
        json_schema_extra = {
            "example": {
                "wallets": {
                    "total_wallets": 1500,
                    "active_wallets": 1200,
                    "privy_wallets": 800,
                    "imported_wallets": 500,
                    "external_wallets": 200,
                },
                "transactions": {
                    "total_transactions": 5000,
                    "pending_transactions": 50,
                    "successful_transactions": 4800,
                    "failed_transactions": 150,
                },
                "users": {
                    "total_users": 1000,
                    "total_users_with_transactions": 500,
                    "active_users_today": 50,
                    "active_users_7d": 200,
                    "active_users_30d": 400,
                },
                "generated_at": "2024-01-15T10:30:00Z",
            }
        }


# ============================================================
# Time Series Responses
# ============================================================


class TransactionTimeSeriesResponse(BaseModel):
    """Time series data for transactions."""

    data: list[TimeSeriesDataPoint] = Field(
        ..., description="Time series data points"
    )
    from_date: datetime = Field(..., description="Start of the time range")
    to_date: datetime = Field(..., description="End of the time range")
    group_by: str = Field(
        default="day", description="Grouping interval (day, week, month)"
    )
    chain: str | None = Field(None, description="Chain filter if applied")
    tx_type: str | None = Field(None, description="Transaction type filter if applied")
    total_count: int = Field(..., description="Total count in the range")


class WalletTimeSeriesResponse(BaseModel):
    """Time series data for wallet creation."""

    data: list[TimeSeriesDataPoint] = Field(
        ..., description="Time series data points"
    )
    from_date: datetime = Field(..., description="Start of the time range")
    to_date: datetime = Field(..., description="End of the time range")
    group_by: str = Field(
        default="day", description="Grouping interval (day, week, month)"
    )
    total_count: int = Field(..., description="Total count in the range")


class UserActivityTimeSeriesResponse(BaseModel):
    """Time series data for user activity."""

    data: list[TimeSeriesDataPoint] = Field(
        ..., description="Time series data points (unique users per day)"
    )
    from_date: datetime = Field(..., description="Start of the time range")
    to_date: datetime = Field(..., description="End of the time range")


# ============================================================
# Distribution Responses
# ============================================================


class DistributionItem(BaseModel):
    """Item in a distribution (e.g., chain distribution)."""

    name: str = Field(..., description="Name of the category")
    count: int = Field(..., description="Count in this category")
    percentage: float = Field(..., description="Percentage of total")


class WalletDistributionResponse(BaseModel):
    """Distribution of wallets by provider."""

    by_provider: list[DistributionItem] = Field(
        ..., description="Distribution by provider"
    )
    total: int = Field(..., description="Total wallets")


class TransactionDistributionResponse(BaseModel):
    """Distribution of transactions by various dimensions."""

    by_chain: list[DistributionItem] = Field(
        ..., description="Distribution by chain"
    )
    by_status: list[DistributionItem] = Field(
        ..., description="Distribution by status"
    )
    by_type: list[DistributionItem] = Field(
        ..., description="Distribution by transaction type"
    )
    total: int = Field(..., description="Total transactions")


# ============================================================
# Request Query Parameters
# ============================================================


class TimeRangeQuery(BaseModel):
    """Common time range query parameters."""

    from_date: datetime = Field(..., description="Start date (inclusive)")
    to_date: datetime = Field(..., description="End date (inclusive)")


class TransactionTimeSeriesQuery(TimeRangeQuery):
    """Query parameters for transaction time series."""

    group_by: str = Field(
        default="day",
        description="Grouping interval: day, week, month",
    )
    chain: str | None = Field(None, description="Filter by chain")
    tx_type: str | None = Field(None, description="Filter by transaction type")
