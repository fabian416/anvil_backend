from enum import Enum

class RateLimitEventType(Enum):
    RATE_LIMIT = "rate_limit"
    QUOTA_EXCEEDED = "quota_exceeded"
    THROTTLE = "throttle"
    TIMEOUT = "timeout"
