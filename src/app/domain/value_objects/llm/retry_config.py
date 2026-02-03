"""
Retry Configuration value object.

Defines retry behavior for LLM orchestration.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class RetryConfig:
    """
    Retry configuration for LLM requests.

    Defines how the system should retry failed requests.
    """

    max_retries_per_provider: int = 2
    max_total_retries: int = 6
    initial_delay_ms: int = 100
    max_delay_ms: int = 5000
    backoff_multiplier: float = 2.0
    jitter: bool = True

    def __post_init__(self):
        """Validate configuration."""
        if self.max_retries_per_provider < 0:
            raise ValueError("max_retries_per_provider must be non-negative")

        if self.max_total_retries < 0:
            raise ValueError("max_total_retries must be non-negative")

        if self.initial_delay_ms <= 0:
            raise ValueError("initial_delay_ms must be positive")

        if self.max_delay_ms < self.initial_delay_ms:
            raise ValueError("max_delay_ms must be >= initial_delay_ms")

        if self.backoff_multiplier <= 1:
            raise ValueError("backoff_multiplier must be > 1")

    def calculate_delay(self, attempt: int) -> int:
        """
        Calculate delay for given attempt number.

        Args:
            attempt: Attempt number (0-indexed)

        Returns:
            Delay in milliseconds
        """
        delay = min(
            self.initial_delay_ms * (self.backoff_multiplier**attempt),
            self.max_delay_ms,
        )

        if self.jitter:
            import random

            # Add random jitter: ±25% of calculated delay
            jitter_range = delay * 0.25
            delay = delay + random.uniform(-jitter_range, jitter_range)

        return int(max(delay, self.initial_delay_ms))
