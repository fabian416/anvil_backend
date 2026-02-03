from enum import Enum


class LLMStatus(Enum):
    SUCCESS = "success"
    FAILED = "failed"
    RATE_LIMITED = "rate_limited"
    FALLBACK = "fallback"
