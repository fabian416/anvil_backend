"""
Prometheus Metrics for Security Middleware

Exports metrics for monitoring security defense middleware performance and detections.
"""

from prometheus_client import Counter, Histogram, Gauge, Info
import time
from functools import wraps
from typing import Callable


# XSS Guard Metrics
xss_attacks_detected = Counter(
    'anvil_xss_attacks_detected_total',
    'Total number of XSS attacks detected',
    ['endpoint', 'severity', 'pattern_type']
)

xss_attacks_blocked = Counter(
    'anvil_xss_attacks_blocked_total',
    'Total number of XSS attacks blocked',
    ['endpoint']
)

xss_middleware_latency = Histogram(
    'anvil_xss_middleware_seconds',
    'XSS middleware processing time in seconds',
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0]
)

# Prompt Injection Metrics
prompt_injection_detected = Counter(
    'anvil_prompt_injection_detected_total',
    'Total number of prompt injection attempts detected',
    ['risk_level', 'pattern_type']
)

prompt_injection_blocked = Counter(
    'anvil_prompt_injection_blocked_total',
    'Total number of prompt injection attempts blocked',
    ['risk_level']
)

prompt_guard_latency = Histogram(
    'anvil_prompt_guard_seconds',
    'Prompt injection guard processing time',
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1]
)

# Transaction Approval Metrics
transaction_approvals_requested = Counter(
    'anvil_transaction_approvals_requested_total',
    'Total transaction approvals requested',
    ['transaction_type', 'risk_level']
)

transaction_approvals_granted = Counter(
    'anvil_transaction_approvals_granted_total',
    'Total transaction approvals granted',
    ['transaction_type']
)

transaction_approvals_denied = Counter(
    'anvil_transaction_approvals_denied_total',
    'Total transaction approvals denied',
    ['transaction_type']
)

transaction_approvals_expired = Counter(
    'anvil_transaction_approvals_expired_total',
    'Total transaction approvals that expired',
    ['transaction_type']
)

pending_approvals = Gauge(
    'anvil_pending_approvals',
    'Number of pending transaction approvals'
)

# PII Redaction Metrics
pii_detected = Counter(
    'anvil_pii_detected_total',
    'Total PII instances detected',
    ['pii_type']
)

pii_redacted = Counter(
    'anvil_pii_redacted_total',
    'Total PII instances redacted',
    ['pii_type']
)

pii_risk_score = Histogram(
    'anvil_pii_risk_score',
    'PII risk scores for scanned text',
    buckets=[0, 1, 3, 5, 8, 10, 15, 20]
)

# Agent Isolation Metrics
agent_permission_checks = Counter(
    'anvil_agent_permission_checks_total',
    'Total agent permission checks',
    ['agent_role', 'resource_type', 'action']
)

agent_permission_denied = Counter(
    'anvil_agent_permission_denied_total',
    'Total agent permissions denied',
    ['agent_role', 'resource_type', 'action', 'risk_level']
)

agent_isolation_violations = Counter(
    'anvil_agent_isolation_violations_total',
    'Total agent isolation violations',
    ['agent_id', 'violation_type']
)

active_agents = Gauge(
    'anvil_active_agents',
    'Number of active registered agents',
    ['role']
)

# Security Scan Metrics
security_scan_duration = Histogram(
    'anvil_security_scan_duration_seconds',
    'Duration of security scans',
    ['tool', 'scan_type'],
    buckets=[10, 30, 60, 120, 300, 600, 1800, 3600]
)

vulnerabilities_found = Gauge(
    'anvil_vulnerabilities_found',
    'Current number of vulnerabilities found',
    ['severity', 'tool']
)

security_scan_failures = Counter(
    'anvil_security_scan_failures_total',
    'Total security scan failures',
    ['tool', 'error_type']
)

# Overall Security Posture
security_posture = Gauge(
    'anvil_security_posture_score',
    'Overall security posture score (0-100)',
    ['category']
)

security_middleware_info = Info(
    'anvil_security_middleware',
    'Security middleware version and configuration'
)


# Decorator for timing middleware operations
def track_latency(histogram: Histogram):
    """Decorator to track operation latency."""
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                histogram.observe(duration)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                histogram.observe(duration)
        
        # Return appropriate wrapper based on whether function is async
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# Initialize security middleware info
security_middleware_info.info({
    'version': '1.0.0',
    'owasp_tools': '5',
    'defense_components': '5',
    'attack_patterns': '500+'
})
