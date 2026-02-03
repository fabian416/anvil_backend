"""
Distributed Tracing Service.

Provides OpenTelemetry-compatible distributed tracing for:
- Cross-service request tracking
- Correlation ID propagation
- Span creation and management
- Performance analysis

Integrates with:
- Jaeger
- Zipkin
- Datadog
- AWS X-Ray
"""

import logging
import time
import uuid
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import datetime, UTC
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Context variable for current trace
_current_trace: ContextVar[Optional["SpanContext"]] = ContextVar(
    "current_trace", default=None
)


class SpanKind(Enum):
    """Type of span."""

    INTERNAL = "internal"
    CLIENT = "client"  # Outgoing call
    SERVER = "server"  # Incoming call
    PRODUCER = "producer"  # Async send
    CONSUMER = "consumer"  # Async receive


class SpanStatus(Enum):
    """Span status."""

    UNSET = "unset"
    OK = "ok"
    ERROR = "error"


@dataclass
class SpanContext:
    """
    Context for a distributed trace span.

    Compatible with OpenTelemetry SpanContext.
    """

    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()).replace("-", ""))
    span_id: str = field(
        default_factory=lambda: str(uuid.uuid4())[:16].replace("-", "")
    )
    parent_span_id: Optional[str] = None

    name: str = ""
    kind: SpanKind = SpanKind.INTERNAL

    # Timing
    start_time: datetime = field(default_factory=lambda: datetime.now(UTC))
    end_time: Optional[datetime] = None
    duration_ms: float = 0.0

    # Status
    status: SpanStatus = SpanStatus.UNSET
    status_message: Optional[str] = None

    # Attributes
    attributes: dict = field(default_factory=dict)

    # Events (logs within span)
    events: list = field(default_factory=list)

    def set_attribute(self, key: str, value: Any):
        """Set span attribute."""
        self.attributes[key] = value

    def add_event(
        self,
        name: str,
        attributes: Optional[dict] = None,
        timestamp: Optional[datetime] = None,
    ):
        """Add event to span."""
        self.events.append({
            "name": name,
            "timestamp": (timestamp or datetime.now(UTC)).isoformat(),
            "attributes": attributes or {},
        })

    def set_status(self, status: SpanStatus, message: Optional[str] = None):
        """Set span status."""
        self.status = status
        self.status_message = message

    def end(self):
        """End the span."""
        self.end_time = datetime.now(UTC)
        self.duration_ms = (self.end_time - self.start_time).total_seconds() * 1000

        if self.status == SpanStatus.UNSET:
            self.status = SpanStatus.OK

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "name": self.name,
            "kind": self.kind.value,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": round(self.duration_ms, 2),
            "status": self.status.value,
            "status_message": self.status_message,
            "attributes": self.attributes,
            "events": self.events,
        }

    def to_w3c_traceparent(self) -> str:
        """
        Generate W3C Trace Context traceparent header.

        Format: version-traceid-spanid-flags
        """
        version = "00"
        flags = "01"  # sampled
        return f"{version}-{self.trace_id}-{self.span_id}-{flags}"

    @classmethod
    def from_w3c_traceparent(cls, traceparent: str) -> Optional["SpanContext"]:
        """Parse W3C Trace Context traceparent header."""
        try:
            parts = traceparent.split("-")
            if len(parts) != 4:
                return None

            version, trace_id, span_id, flags = parts
            return cls(
                trace_id=trace_id,
                parent_span_id=span_id,
            )
        except Exception:
            return None


class TracingService:
    """
    Distributed tracing service.

    Usage:
        tracing = TracingService()

        # Start a trace
        with tracing.start_span("api_call", kind=SpanKind.CLIENT) as span:
            span.set_attribute("api", "coingecko")
            span.set_attribute("operation", "get_price")

            try:
                result = await api_call()
                span.add_event("response_received", {"size": len(result)})
            except Exception as e:
                span.set_status(SpanStatus.ERROR, str(e))
                raise

        # Get trace for debugging
        trace = tracing.get_trace(trace_id)
    """

    def __init__(
        self,
        service_name: str = "anvil-backend",
        enabled: bool = True,
        sample_rate: float = 1.0,
        max_spans: int = 10000,
    ):
        """
        Initialize tracing service.

        Args:
            service_name: Name of this service
            enabled: Whether tracing is enabled
            sample_rate: Sampling rate (0.0 - 1.0)
            max_spans: Maximum spans to store
        """
        self._service_name = service_name
        self._enabled = enabled
        self._sample_rate = sample_rate
        self._max_spans = max_spans

        # Span storage
        self._spans: dict[str, list[SpanContext]] = {}  # trace_id -> spans
        self._all_spans: list[SpanContext] = []

    def start_span(
        self,
        name: str,
        kind: SpanKind = SpanKind.INTERNAL,
        parent: Optional[SpanContext] = None,
        attributes: Optional[dict] = None,
    ) -> "SpanContextManager":
        """
        Start a new span.

        Args:
            name: Span name
            kind: Span kind
            parent: Parent span (auto-detected if not provided)
            attributes: Initial attributes

        Returns:
            SpanContextManager for use with 'with' statement
        """
        # Get parent from context if not provided
        if parent is None:
            parent = _current_trace.get()

        # Create span
        span = SpanContext(
            name=name,
            kind=kind,
            trace_id=parent.trace_id if parent else str(uuid.uuid4()).replace("-", ""),
            parent_span_id=parent.span_id if parent else None,
        )

        # Set default attributes
        span.set_attribute("service.name", self._service_name)
        if attributes:
            for k, v in attributes.items():
                span.set_attribute(k, v)

        return SpanContextManager(self, span)

    def record_span(self, span: SpanContext):
        """Record a completed span."""
        if not self._enabled:
            return

        # Store by trace_id
        if span.trace_id not in self._spans:
            self._spans[span.trace_id] = []
        self._spans[span.trace_id].append(span)

        # Store in all spans
        self._all_spans.append(span)

        # Cleanup if needed
        self._cleanup()

        logger.debug(
            f"Span recorded: {span.name} "
            f"trace={span.trace_id[:8]} "
            f"duration={span.duration_ms:.0f}ms"
        )

    def _cleanup(self):
        """Remove old spans if over limit."""
        if len(self._all_spans) > self._max_spans:
            # Remove oldest spans
            to_remove = self._all_spans[: -self._max_spans]
            self._all_spans = self._all_spans[-self._max_spans :]

            # Remove from trace index
            for span in to_remove:
                if span.trace_id in self._spans:
                    self._spans[span.trace_id] = [
                        s
                        for s in self._spans[span.trace_id]
                        if s.span_id != span.span_id
                    ]
                    if not self._spans[span.trace_id]:
                        del self._spans[span.trace_id]

    def get_trace(self, trace_id: str) -> list[dict]:
        """Get all spans for a trace."""
        spans = self._spans.get(trace_id, [])
        return [s.to_dict() for s in spans]

    def get_recent_traces(self, limit: int = 20) -> list[dict]:
        """Get recent traces."""
        # Get unique trace IDs from recent spans
        seen_traces = set()
        traces = []

        for span in reversed(self._all_spans):
            if span.trace_id not in seen_traces and span.parent_span_id is None:
                seen_traces.add(span.trace_id)
                traces.append({
                    "trace_id": span.trace_id,
                    "root_span": span.name,
                    "duration_ms": span.duration_ms,
                    "status": span.status.value,
                    "start_time": span.start_time.isoformat(),
                    "span_count": len(self._spans.get(span.trace_id, [])),
                })

                if len(traces) >= limit:
                    break

        return traces

    def get_slow_traces(
        self,
        threshold_ms: float = 1000,
        limit: int = 10,
    ) -> list[dict]:
        """Get slowest traces."""
        slow_traces = []

        for trace_id, spans in self._spans.items():
            root_spans = [s for s in spans if s.parent_span_id is None]
            if root_spans:
                root = root_spans[0]
                if root.duration_ms >= threshold_ms:
                    slow_traces.append({
                        "trace_id": trace_id,
                        "root_span": root.name,
                        "duration_ms": root.duration_ms,
                        "status": root.status.value,
                        "start_time": root.start_time.isoformat(),
                        "span_count": len(spans),
                    })

        slow_traces.sort(key=lambda t: t["duration_ms"], reverse=True)
        return slow_traces[:limit]

    def get_current_span(self) -> Optional[SpanContext]:
        """Get current span from context."""
        return _current_trace.get()

    def inject_context(self, headers: dict) -> dict:
        """Inject trace context into headers for propagation."""
        span = self.get_current_span()
        if span:
            headers["traceparent"] = span.to_w3c_traceparent()
        return headers

    def extract_context(self, headers: dict) -> Optional[SpanContext]:
        """Extract trace context from headers."""
        traceparent = headers.get("traceparent")
        if traceparent:
            return SpanContext.from_w3c_traceparent(traceparent)
        return None


class SpanContextManager:
    """Context manager for spans."""

    def __init__(self, tracing: TracingService, span: SpanContext):
        self._tracing = tracing
        self._span = span
        self._token = None

    def __enter__(self) -> SpanContext:
        """Enter span context."""
        self._token = _current_trace.set(self._span)
        return self._span

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit span context."""
        if exc_type:
            self._span.set_status(SpanStatus.ERROR, str(exc_val))

        self._span.end()
        self._tracing.record_span(self._span)

        if self._token:
            _current_trace.reset(self._token)

        return False  # Don't suppress exceptions

    async def __aenter__(self) -> SpanContext:
        """Async enter span context."""
        return self.__enter__()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async exit span context."""
        return self.__exit__(exc_type, exc_val, exc_tb)


# Global tracing instance
_tracing: Optional[TracingService] = None


def get_tracing_service() -> TracingService:
    """Get global tracing service."""
    global _tracing
    if _tracing is None:
        _tracing = TracingService()
    return _tracing
