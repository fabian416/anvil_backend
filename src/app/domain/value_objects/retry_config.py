"""
Retry Configuration value object for Enterprise Retry System.

Defines retry behavior with circuit breaker and telemetry configuration.
"""

from dataclasses import dataclass
import random


@dataclass(frozen=True)
class RetryConfig:
    """
    Enterprise retry configuration.
    
    Defines how the system should retry failed requests with
    circuit breaker and telemetry support.
    """
    
    # Retry behavior
    max_retries: int = 3
    initial_backoff_seconds: float = 2.0
    max_backoff_seconds: float = 10.0
    exponential_base: float = 2.0
    jitter: bool = True
    
    # Circuit breaker
    circuit_breaker_enabled: bool = True
    circuit_failure_threshold: int = 5
    circuit_success_threshold: int = 2
    circuit_timeout_seconds: int = 60
    
    # Telemetry
    telemetry_enabled: bool = True
    
    # Manual override
    allow_manual_override: bool = True
    
    def __post_init__(self):
        """Validate configuration."""
        if self.max_retries < 0:
            raise ValueError("max_retries must be non-negative")
        
        if self.initial_backoff_seconds <= 0:
            raise ValueError("initial_backoff_seconds must be positive")
        
        if self.max_backoff_seconds < self.initial_backoff_seconds:
            raise ValueError("max_backoff_seconds must be >= initial_backoff_seconds")
        
        if self.exponential_base <= 1:
            raise ValueError("exponential_base must be > 1")
        
        if self.circuit_failure_threshold <= 0:
            raise ValueError("circuit_failure_threshold must be positive")
        
        if self.circuit_success_threshold <= 0:
            raise ValueError("circuit_success_threshold must be positive")
        
        if self.circuit_timeout_seconds <= 0:
            raise ValueError("circuit_timeout_seconds must be positive")
    
    def calculate_delay(self, attempt: int) -> int:
        """
        Calculate delay for given attempt number with exponential backoff.
        
        Formula: min(initial * (base ^ attempt), max)
        With optional jitter to prevent thundering herd.
        
        Args:
            attempt: Attempt number (0-indexed)
        
        Returns:
            Delay in milliseconds
        
        Example:
            config = RetryConfig(initial_backoff_seconds=2, exponential_base=2, jitter=True)
            config.calculate_delay(0)  # ~2000ms (2s)
            config.calculate_delay(1)  # ~4000ms (4s)
            config.calculate_delay(2)  # ~8000ms (8s)
            config.calculate_delay(3)  # 10000ms (capped at max)
        """
        # Calculate base delay
        delay_seconds = self.initial_backoff_seconds * (self.exponential_base ** attempt)
        
        # Cap at max
        delay_seconds = min(delay_seconds, self.max_backoff_seconds)
        
        # Apply jitter if enabled (0.5x to 1.5x)
        if self.jitter:
            jitter_factor = 0.5 + random.random()  # Random between 0.5 and 1.5
            delay_seconds *= jitter_factor
        
        # Convert to milliseconds
        return int(delay_seconds * 1000)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "max_retries": self.max_retries,
            "initial_backoff_seconds": self.initial_backoff_seconds,
            "max_backoff_seconds": self.max_backoff_seconds,
            "exponential_base": self.exponential_base,
            "jitter": self.jitter,
            "circuit_breaker_enabled": self.circuit_breaker_enabled,
            "circuit_failure_threshold": self.circuit_failure_threshold,
            "circuit_success_threshold": self.circuit_success_threshold,
            "circuit_timeout_seconds": self.circuit_timeout_seconds,
            "telemetry_enabled": self.telemetry_enabled,
            "allow_manual_override": self.allow_manual_override,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "RetryConfig":
        """Create from dictionary."""
        return cls(**data)
    
    @classmethod
    def for_mcp_servers(cls) -> "RetryConfig":
        """
        Create configuration optimized for MCP servers.
        
        MCP servers typically have:
        - External API calls (DeFiLlama, 1inch, etc.)
        - Rate limits
        - Network variability
        
        Returns:
            Optimized RetryConfig
        """
        return cls(
            max_retries=3,
            initial_backoff_seconds=2.0,
            max_backoff_seconds=10.0,
            exponential_base=2.0,
            jitter=True,
            circuit_breaker_enabled=True,
            circuit_failure_threshold=5,
            circuit_success_threshold=2,
            circuit_timeout_seconds=60,
            telemetry_enabled=True,
            allow_manual_override=True,
        )
    
    @classmethod
    def for_agno_agents(cls) -> "RetryConfig":
        """
        Create configuration optimized for Agno agents.
        
        Agno agents typically have:
        - LLM calls (already have retry)
        - MCP tool calls (need retry)
        - Lower tolerance for latency
        
        Returns:
            Optimized RetryConfig
        """
        return cls(
            max_retries=2,
            initial_backoff_seconds=1.0,
            max_backoff_seconds=5.0,
            exponential_base=2.0,
            jitter=True,
            circuit_breaker_enabled=True,
            circuit_failure_threshold=3,
            circuit_success_threshold=2,
            circuit_timeout_seconds=30,
            telemetry_enabled=True,
            allow_manual_override=True,
        )
    
    @classmethod
    def for_testing(cls) -> "RetryConfig":
        """
        Create configuration optimized for testing.
        
        Fast retries with minimal backoff for test speed.
        
        Returns:
            Test-optimized RetryConfig
        """
        return cls(
            max_retries=2,
            initial_backoff_seconds=0.1,
            max_backoff_seconds=0.5,
            exponential_base=2.0,
            jitter=False,  # Deterministic for testing
            circuit_breaker_enabled=True,
            circuit_failure_threshold=2,
            circuit_success_threshold=1,
            circuit_timeout_seconds=5,
            telemetry_enabled=False,  # Disable for test speed
            allow_manual_override=True,
        )
