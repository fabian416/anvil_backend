"""
Timezone-aware datetime utilities.

This module provides timezone-aware datetime functions to replace deprecated
datetime.now(UTC) usage throughout the codebase.

Python 3.12+ deprecates datetime.now(UTC) in favor of timezone-aware alternatives.
See: https://docs.python.org/3.12/library/datetime.html#datetime.datetime.utcnow

Usage:
    from app.domain.common.datetime_utils import utc_now
    
    # Instead of datetime.now(UTC)
    current_time = utc_now()
"""

from datetime import datetime, timezone


def utc_now() -> datetime:
    """
    Return the current UTC datetime as a timezone-aware object.
    
    This is the recommended replacement for datetime.now(UTC) which is
    deprecated as of Python 3.12 and will be removed in a future version.
    
    Returns:
        A timezone-aware datetime object representing the current time in UTC.
    
    Example:
        >>> now = utc_now()
        >>> now.tzinfo
        datetime.timezone.utc
    """
    return datetime.now(timezone.utc)


def utc_now_naive() -> datetime:
    """
    Return the current UTC datetime as a naive (timezone-unaware) object.
    
    Use this only when you need to maintain compatibility with existing
    code that expects naive datetime objects. Prefer utc_now() for new code.
    
    Returns:
        A naive datetime object representing the current time in UTC.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)


__all__ = ["utc_now", "utc_now_naive"]
