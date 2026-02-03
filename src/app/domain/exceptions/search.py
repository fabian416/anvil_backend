"""
Search-specific domain exceptions with standardized error codes.

This module provides all exceptions related to:
- Search queries and validation
- Search filters and sorting
- Search service availability
"""

from typing import Any

from app.domain.exceptions.base import ApplicationError
from app.domain.exceptions.error_codes import ErrorCode


class SearchQueryEmptyError(ApplicationError):
    """Raised when a search query is empty."""

    def __init__(self) -> None:
        super().__init__(ErrorCode.SRCH_QUERY_EMPTY, field="query")


class SearchQueryTooShortError(ApplicationError):
    """Raised when a search query is too short."""

    def __init__(
        self,
        length: int | None = None,
        min_length: int | None = None,
    ) -> None:
        details = {}
        if length is not None:
            details["length"] = length
        if min_length is not None:
            details["min_length"] = min_length
        super().__init__(ErrorCode.SRCH_QUERY_TOO_SHORT, details=details, field="query")


class SearchQueryTooLongError(ApplicationError):
    """Raised when a search query exceeds maximum length."""

    def __init__(
        self,
        length: int | None = None,
        max_length: int | None = None,
    ) -> None:
        details = {}
        if length is not None:
            details["length"] = length
        if max_length is not None:
            details["max_length"] = max_length
        super().__init__(ErrorCode.SRCH_QUERY_TOO_LONG, details=details, field="query")


class InvalidSearchFiltersError(ApplicationError):
    """Raised when search filters are invalid."""

    def __init__(
        self,
        invalid_filters: list[str] | None = None,
        valid_filters: list[str] | None = None,
        reason: str | None = None,
    ) -> None:
        details = {}
        if invalid_filters:
            details["invalid_filters"] = invalid_filters
        if valid_filters:
            details["valid_filters"] = valid_filters
        if reason:
            details["reason"] = reason
        super().__init__(
            ErrorCode.SRCH_INVALID_FILTERS, details=details, field="filters"
        )


class SearchServiceUnavailableError(ApplicationError):
    """Raised when search service is temporarily unavailable."""

    def __init__(
        self,
        retry_after_seconds: int | None = None,
        reason: str | None = None,
    ) -> None:
        details = {}
        if retry_after_seconds is not None:
            details["retry_after_seconds"] = retry_after_seconds
        if reason:
            details["reason"] = reason
        super().__init__(ErrorCode.SRCH_SERVICE_UNAVAILABLE, details=details)


class SearchNoResultsError(ApplicationError):
    """Raised when search returns no results."""

    def __init__(
        self,
        query: str | None = None,
        filters: dict[str, Any] | None = None,
        suggestions: list[str] | None = None,
    ) -> None:
        details = {}
        if query:
            details["query"] = query
        if filters:
            details["filters"] = filters
        if suggestions:
            details["suggestions"] = suggestions
        super().__init__(ErrorCode.SRCH_NO_RESULTS, details=details)


# Additional search-specific exceptions


class InvalidSortFieldError(ApplicationError):
    """Raised when an invalid sort field is specified."""

    def __init__(
        self,
        field: str | None = None,
        valid_fields: list[str] | None = None,
    ) -> None:
        details = {}
        if field:
            details["sort_field"] = field
        if valid_fields:
            details["valid_fields"] = valid_fields
        super().__init__(
            ErrorCode.SRCH_INVALID_FILTERS,
            details=details,
            field="sort_by",
            override_message="Invalid sort field",
        )


class InvalidSortOrderError(ApplicationError):
    """Raised when an invalid sort order is specified."""

    def __init__(
        self,
        order: str | None = None,
    ) -> None:
        details = {}
        if order:
            details["sort_order"] = order
            details["valid_orders"] = ["asc", "desc"]
        super().__init__(
            ErrorCode.SRCH_INVALID_FILTERS,
            details=details,
            field="sort_order",
            override_message="Invalid sort order (use 'asc' or 'desc')",
        )


class InvalidPaginationError(ApplicationError):
    """Raised when pagination parameters are invalid."""

    def __init__(
        self,
        page: int | None = None,
        page_size: int | None = None,
        max_page_size: int | None = None,
    ) -> None:
        details = {}
        if page is not None:
            details["page"] = page
        if page_size is not None:
            details["page_size"] = page_size
        if max_page_size is not None:
            details["max_page_size"] = max_page_size
        super().__init__(
            ErrorCode.SRCH_INVALID_FILTERS,
            details=details,
            override_message="Invalid pagination parameters",
        )


class SearchIndexError(ApplicationError):
    """Raised when search index is unavailable or corrupted."""

    def __init__(
        self,
        index_name: str | None = None,
        reason: str | None = None,
    ) -> None:
        details = {}
        if index_name:
            details["index_name"] = index_name
        if reason:
            details["reason"] = reason
        super().__init__(
            ErrorCode.SRCH_SERVICE_UNAVAILABLE,
            details=details,
            override_message="Search index unavailable",
        )


class SearchTimeoutError(ApplicationError):
    """Raised when search operation times out."""

    def __init__(
        self,
        query: str | None = None,
        timeout_seconds: int | None = None,
    ) -> None:
        details = {}
        if query:
            details["query"] = query
        if timeout_seconds is not None:
            details["timeout_seconds"] = timeout_seconds
        super().__init__(
            ErrorCode.SRCH_SERVICE_UNAVAILABLE,
            details=details,
            override_message="Search operation timed out",
        )


class InvalidDateRangeError(ApplicationError):
    """Raised when date range filter is invalid."""

    def __init__(
        self,
        start_date: str | None = None,
        end_date: str | None = None,
        reason: str | None = None,
    ) -> None:
        details = {}
        if start_date:
            details["start_date"] = start_date
        if end_date:
            details["end_date"] = end_date
        if reason:
            details["reason"] = reason
        super().__init__(
            ErrorCode.SRCH_INVALID_FILTERS,
            details=details,
            override_message="Invalid date range",
        )
