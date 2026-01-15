"""
Metrics Exporter for Prometheus/OpenMetrics.

Exports API telemetry metrics in Prometheus format for:
- Grafana dashboards
- Alertmanager integration
- Long-term metrics storage

Metrics exported:
- api_requests_total (counter)
- api_request_duration_seconds (histogram)
- api_errors_total (counter)
- api_rate_limits_total (counter)
- api_cache_hits_total (counter)
- api_estimated_cost_usd (gauge)
"""

import logging
from datetime import datetime, UTC
from typing import Optional

logger = logging.getLogger(__name__)


class PrometheusMetrics:
    """
    Prometheus-compatible metrics storage.
    
    Usage:
        metrics = PrometheusMetrics()
        metrics.inc_counter("api_requests_total", labels={"api": "coingecko"})
        metrics.observe_histogram("api_request_duration_seconds", 0.5, labels={"api": "coingecko"})
        
        # Export in Prometheus format
        output = metrics.export()
    """
    
    def __init__(self, prefix: str = "anvil"):
        """
        Initialize Prometheus metrics.
        
        Args:
            prefix: Metric name prefix
        """
        self._prefix = prefix
        
        # Counters
        self._counters: dict[str, dict[tuple, float]] = {}
        
        # Gauges
        self._gauges: dict[str, dict[tuple, float]] = {}
        
        # Histograms (simplified - just count and sum)
        self._histograms: dict[str, dict[tuple, dict]] = {}
        
        # Metric metadata
        self._metadata: dict[str, dict] = {}
        
        # Initialize default metrics
        self._init_default_metrics()
    
    def _init_default_metrics(self):
        """Initialize default API metrics."""
        self.register_counter(
            "api_requests_total",
            "Total number of API requests",
            ["api", "operation", "status"],
        )
        self.register_counter(
            "api_errors_total",
            "Total number of API errors",
            ["api", "operation", "error_type"],
        )
        self.register_counter(
            "api_rate_limits_total",
            "Total number of rate limit events",
            ["api"],
        )
        self.register_counter(
            "api_cache_hits_total",
            "Total number of cache hits",
            ["api", "operation"],
        )
        self.register_gauge(
            "api_estimated_cost_usd",
            "Estimated API cost in USD",
            ["api"],
        )
        self.register_histogram(
            "api_request_duration_seconds",
            "API request duration in seconds",
            ["api", "operation"],
            buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
        )
    
    def register_counter(
        self,
        name: str,
        help_text: str,
        labels: list[str],
    ):
        """Register a counter metric."""
        full_name = f"{self._prefix}_{name}"
        self._counters[full_name] = {}
        self._metadata[full_name] = {
            "type": "counter",
            "help": help_text,
            "labels": labels,
        }
    
    def register_gauge(
        self,
        name: str,
        help_text: str,
        labels: list[str],
    ):
        """Register a gauge metric."""
        full_name = f"{self._prefix}_{name}"
        self._gauges[full_name] = {}
        self._metadata[full_name] = {
            "type": "gauge",
            "help": help_text,
            "labels": labels,
        }
    
    def register_histogram(
        self,
        name: str,
        help_text: str,
        labels: list[str],
        buckets: list[float],
    ):
        """Register a histogram metric."""
        full_name = f"{self._prefix}_{name}"
        self._histograms[full_name] = {}
        self._metadata[full_name] = {
            "type": "histogram",
            "help": help_text,
            "labels": labels,
            "buckets": buckets,
        }
    
    def _labels_to_key(self, labels: dict) -> tuple:
        """Convert labels dict to hashable key."""
        return tuple(sorted(labels.items()))
    
    def inc_counter(self, name: str, value: float = 1.0, labels: Optional[dict] = None):
        """Increment a counter."""
        full_name = f"{self._prefix}_{name}"
        if full_name not in self._counters:
            return
        
        key = self._labels_to_key(labels or {})
        self._counters[full_name][key] = self._counters[full_name].get(key, 0) + value
    
    def set_gauge(self, name: str, value: float, labels: Optional[dict] = None):
        """Set a gauge value."""
        full_name = f"{self._prefix}_{name}"
        if full_name not in self._gauges:
            return
        
        key = self._labels_to_key(labels or {})
        self._gauges[full_name][key] = value
    
    def observe_histogram(self, name: str, value: float, labels: Optional[dict] = None):
        """Observe a histogram value."""
        full_name = f"{self._prefix}_{name}"
        if full_name not in self._histograms:
            return
        
        key = self._labels_to_key(labels or {})
        if key not in self._histograms[full_name]:
            self._histograms[full_name][key] = {
                "count": 0,
                "sum": 0.0,
                "buckets": {b: 0 for b in self._metadata[full_name]["buckets"]},
            }
        
        data = self._histograms[full_name][key]
        data["count"] += 1
        data["sum"] += value
        
        for bucket in self._metadata[full_name]["buckets"]:
            if value <= bucket:
                data["buckets"][bucket] += 1
    
    def _format_labels(self, labels: tuple) -> str:
        """Format labels for Prometheus output."""
        if not labels:
            return ""
        
        parts = [f'{k}="{v}"' for k, v in labels]
        return "{" + ",".join(parts) + "}"
    
    def export(self) -> str:
        """
        Export metrics in Prometheus text format.
        
        Returns:
            Prometheus-compatible metrics text
        """
        lines = []
        timestamp = int(datetime.now(UTC).timestamp() * 1000)
        
        # Export counters
        for name, values in self._counters.items():
            meta = self._metadata[name]
            lines.append(f"# HELP {name} {meta['help']}")
            lines.append(f"# TYPE {name} counter")
            for labels, value in values.items():
                label_str = self._format_labels(labels)
                lines.append(f"{name}{label_str} {value}")
        
        # Export gauges
        for name, values in self._gauges.items():
            meta = self._metadata[name]
            lines.append(f"# HELP {name} {meta['help']}")
            lines.append(f"# TYPE {name} gauge")
            for labels, value in values.items():
                label_str = self._format_labels(labels)
                lines.append(f"{name}{label_str} {value}")
        
        # Export histograms
        for name, values in self._histograms.items():
            meta = self._metadata[name]
            lines.append(f"# HELP {name} {meta['help']}")
            lines.append(f"# TYPE {name} histogram")
            
            for labels, data in values.items():
                label_str = self._format_labels(labels)
                
                # Bucket values (cumulative)
                cumulative = 0
                for bucket, count in sorted(data["buckets"].items()):
                    cumulative += count
                    if label_str:
                        bucket_labels = label_str[:-1] + f',le="{bucket}"' + "}"
                    else:
                        bucket_labels = f'{{le="{bucket}"}}'
                    lines.append(f"{name}_bucket{bucket_labels} {cumulative}")
                
                # +Inf bucket
                if label_str:
                    inf_labels = label_str[:-1] + ',le="+Inf"}'
                else:
                    inf_labels = '{le="+Inf"}'
                lines.append(f"{name}_bucket{inf_labels} {data['count']}")
                
                # Sum and count
                lines.append(f"{name}_sum{label_str} {data['sum']}")
                lines.append(f"{name}_count{label_str} {data['count']}")
        
        return "\n".join(lines)
    
    def reset(self):
        """Reset all metrics."""
        for counter in self._counters.values():
            counter.clear()
        for gauge in self._gauges.values():
            gauge.clear()
        for histogram in self._histograms.values():
            histogram.clear()


class MetricsExporter:
    """
    Exports API telemetry to Prometheus metrics.
    
    Usage:
        from app.infrastructure.telemetry import APITelemetry
        
        telemetry = APITelemetry()
        exporter = MetricsExporter(telemetry)
        
        # Update Prometheus metrics from telemetry
        exporter.update()
        
        # Get Prometheus-format output
        output = exporter.export()
    """
    
    def __init__(self, telemetry: Optional["APITelemetry"] = None):
        """
        Initialize metrics exporter.
        
        Args:
            telemetry: API telemetry instance
        """
        from app.infrastructure.telemetry.api_telemetry import get_api_telemetry
        
        self._telemetry = telemetry or get_api_telemetry()
        self._prometheus = PrometheusMetrics()
    
    def update(self):
        """Update Prometheus metrics from telemetry."""
        metrics = self._telemetry.get_all_metrics()
        
        for api, api_metrics in metrics.get("by_api", {}).items():
            # Update counters
            self._prometheus.inc_counter(
                "api_requests_total",
                value=api_metrics["successful_requests"],
                labels={"api": api, "operation": "all", "status": "success"},
            )
            self._prometheus.inc_counter(
                "api_requests_total",
                value=api_metrics["failed_requests"],
                labels={"api": api, "operation": "all", "status": "error"},
            )
            self._prometheus.inc_counter(
                "api_rate_limits_total",
                value=api_metrics["rate_limited_requests"],
                labels={"api": api},
            )
            self._prometheus.inc_counter(
                "api_cache_hits_total",
                value=api_metrics["cached_requests"],
                labels={"api": api, "operation": "all"},
            )
            
            # Update gauges
            self._prometheus.set_gauge(
                "api_estimated_cost_usd",
                value=api_metrics["estimated_cost_usd"],
                labels={"api": api},
            )
    
    def export(self) -> str:
        """Export Prometheus-format metrics."""
        self.update()
        return self._prometheus.export()
    
    def get_prometheus_metrics(self) -> PrometheusMetrics:
        """Get Prometheus metrics object."""
        return self._prometheus


# Global exporter instance
_exporter: Optional[MetricsExporter] = None


def get_metrics_exporter() -> MetricsExporter:
    """Get global metrics exporter."""
    global _exporter
    if _exporter is None:
        _exporter = MetricsExporter()
    return _exporter
