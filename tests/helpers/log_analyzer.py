"""
Log Analyzer - Automated error analysis from application logs.

Analyzes logs from FastAPI, Celery, and MCP servers to identify root causes of test failures.
Uses LLM-powered analysis to understand error patterns and provide actionable insights.

Only runs on localhost to ensure log access security.
"""

import json
import logging
import os
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from app.infrastructure.adapters.agent_squad.llm_client_deepinfra import (
    LLMClientDeepInfra,
)

logger = logging.getLogger(__name__)


class ErrorType(str, Enum):
    """Type of error identified in logs."""

    API_ERROR = "API_ERROR"
    CELERY_ERROR = "CELERY_ERROR"
    MCP_ERROR = "MCP_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    RATE_LIMIT_ERROR = "RATE_LIMIT_ERROR"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


@dataclass
class LogEntry:
    """A single log entry."""

    timestamp: datetime
    level: str
    source: str  # "fastapi", "celery", "mcp"
    message: str
    raw_line: str


@dataclass
class ErrorAnalysis:
    """Result from log analysis."""

    root_cause: str
    error_type: ErrorType
    relevant_logs: list[LogEntry]
    suggested_fix: str
    confidence: float  # 0.0 - 1.0
    analysis_time_ms: int
    timestamp: datetime


class LogAnalyzer:
    """
    Analyze FastAPI/Celery/MCP logs to identify root causes.

    Provides automated error analysis:
    - Extracts relevant log entries around error time
    - Identifies error patterns and types
    - Uses LLM to understand root cause
    - Suggests fixes based on error context

    Environment Variables:
        ENABLE_LOG_ANALYSIS: "true" to enable (default: "false")
        DEEPINFRA_API_KEY: DeepInfra API key (required if enabled)
        LOGS_DIR: Path to logs directory (default: "./logs")

    Usage:
        analyzer = LogAnalyzer()
        analysis = analyzer.analyze_error(
            test_name="test_guest_chat_bitcoin_query",
            error_message="HTTP 500 Internal Server Error",
            timestamp=datetime.utcnow()
        )
        print(f"Root cause: {analysis.root_cause}")
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        logs_dir: Optional[str] = None,
        enabled: Optional[bool] = None,
    ):
        """
        Initialize log analyzer.

        Args:
            api_key: DeepInfra API key (defaults to DEEPINFRA_API_KEY env var)
            logs_dir: Path to logs directory
            enabled: Whether to enable analysis (defaults to ENABLE_LOG_ANALYSIS env var)
        """
        # Check if log analysis is enabled
        self._enabled = enabled if enabled is not None else os.getenv("ENABLE_LOG_ANALYSIS", "false").lower() == "true"

        # Only enable on localhost for security
        if self._enabled and not self._is_localhost():
            logger.warning("Log analysis is only available on localhost - disabling")
            self._enabled = False

        if not self._enabled:
            logger.info("Log analysis is DISABLED (set ENABLE_LOG_ANALYSIS=true to enable)")
            self._client = None
            return

        # Get API key
        api_key = api_key or os.getenv("DEEPINFRA_API_KEY")
        if not api_key:
            logger.warning(
                "DEEPINFRA_API_KEY not set - log analysis will be skipped. "
                "Set DEEPINFRA_API_KEY environment variable to enable."
            )
            self._enabled = False
            self._client = None
            return

        # Initialize DeepInfra client
        self._client = LLMClientDeepInfra(api_key=api_key)
        self._model = "meta-llama/Meta-Llama-3.1-70B-Instruct"

        # Set logs directory
        self._logs_dir = Path(logs_dir) if logs_dir else Path("./logs")
        if not self._logs_dir.exists():
            logger.warning(f"Logs directory not found: {self._logs_dir} - log analysis will be limited")

        logger.info(f"Log analyzer initialized with logs_dir={self._logs_dir}")

    @property
    def enabled(self) -> bool:
        """Check if log analysis is enabled."""
        return self._enabled

    def analyze_error(
        self,
        test_name: str,
        error_message: str,
        timestamp: Optional[datetime] = None,
        time_window_seconds: int = 60,
    ) -> ErrorAnalysis:
        """
        Analyze logs to find root cause of test failure.

        Args:
            test_name: Name of the test that failed
            error_message: Error message from the test
            timestamp: Timestamp of the error (defaults to now)
            time_window_seconds: Time window to search logs (default: 60s)

        Returns:
            ErrorAnalysis with root cause, relevant logs, and suggested fix
        """
        if not self._enabled:
            return ErrorAnalysis(
                root_cause="Log analysis is disabled",
                error_type=ErrorType.UNKNOWN_ERROR,
                relevant_logs=[],
                suggested_fix="Enable log analysis with ENABLE_LOG_ANALYSIS=true",
                confidence=0.0,
                analysis_time_ms=0,
                timestamp=datetime.utcnow(),
            )

        start_time = datetime.utcnow()
        timestamp = timestamp or datetime.utcnow()

        # Extract relevant logs from all sources
        relevant_logs = self._extract_logs_in_window(
            timestamp=timestamp,
            time_window_seconds=time_window_seconds,
        )

        if not relevant_logs:
            return ErrorAnalysis(
                root_cause="No relevant logs found",
                error_type=ErrorType.UNKNOWN_ERROR,
                relevant_logs=[],
                suggested_fix="Check if application logs are being written correctly",
                confidence=0.0,
                analysis_time_ms=int((datetime.utcnow() - start_time).total_seconds() * 1000),
                timestamp=datetime.utcnow(),
            )

        # Identify error type from error message
        error_type = self._identify_error_type(error_message)

        # Use LLM to analyze logs and determine root cause
        try:
            analysis_prompt = self._build_log_analysis_prompt(
                test_name=test_name,
                error_message=error_message,
                relevant_logs=relevant_logs,
                error_type=error_type,
            )

            response = self._client.chat(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a log analysis assistant. Analyze application logs to identify root causes of test failures. "
                        "Provide actionable insights and suggested fixes. Respond in JSON format.",
                    },
                    {"role": "user", "content": analysis_prompt},
                ],
                model=self._model,
                temperature=0.2,  # Slightly higher for more creative analysis
                max_tokens=1000,
            )

            # Parse analysis result
            analysis_data = self._parse_analysis_response(response["content"])

            end_time = datetime.utcnow()
            analysis_time_ms = int((end_time - start_time).total_seconds() * 1000)

            return ErrorAnalysis(
                root_cause=analysis_data.get("root_cause", "Unknown"),
                error_type=ErrorType(analysis_data.get("error_type", error_type.value)),
                relevant_logs=relevant_logs,
                suggested_fix=analysis_data.get("suggested_fix", ""),
                confidence=analysis_data.get("confidence", 0.0),
                analysis_time_ms=analysis_time_ms,
                timestamp=datetime.utcnow(),
            )

        except Exception as e:
            logger.error(f"Log analysis failed for {test_name}: {e}")
            end_time = datetime.utcnow()
            analysis_time_ms = int((end_time - start_time).total_seconds() * 1000)

            return ErrorAnalysis(
                root_cause=f"Log analysis error: {str(e)}",
                error_type=error_type,
                relevant_logs=relevant_logs,
                suggested_fix="Check logs manually for more details",
                confidence=0.0,
                analysis_time_ms=analysis_time_ms,
                timestamp=datetime.utcnow(),
            )

    def _is_localhost(self) -> bool:
        """Check if running on localhost."""
        # Check common indicators of localhost
        hostname = os.getenv("HOSTNAME", "").lower()
        is_local = any(
            [
                hostname == "localhost",
                hostname.startswith("ubuntu"),  # Common dev hostname
                os.path.exists("/.dockerenv") is False,  # Not in Docker
                os.getenv("APP_ENV", "").lower() in ["local", "dev", "development"],
            ]
        )
        return is_local

    def _extract_logs_in_window(
        self,
        timestamp: datetime,
        time_window_seconds: int,
    ) -> list[LogEntry]:
        """Extract logs within time window around error."""
        logs = []

        # Calculate time window
        start_time = timestamp - timedelta(seconds=time_window_seconds // 2)
        end_time = timestamp + timedelta(seconds=time_window_seconds // 2)

        # Extract FastAPI logs
        fastapi_logs = self._extract_from_file(
            file_path=self._logs_dir / "fastapi.log",
            source="fastapi",
            start_time=start_time,
            end_time=end_time,
        )
        logs.extend(fastapi_logs)

        # Extract Celery logs
        celery_dir = self._logs_dir / "celery"
        if celery_dir.exists():
            for log_file in celery_dir.glob("*.log"):
                celery_logs = self._extract_from_file(
                    file_path=log_file,
                    source="celery",
                    start_time=start_time,
                    end_time=end_time,
                )
                logs.extend(celery_logs)

        # Extract MCP logs
        mcp_dir = self._logs_dir / "mcp"
        if mcp_dir.exists():
            for log_file in mcp_dir.glob("*.log"):
                mcp_logs = self._extract_from_file(
                    file_path=log_file,
                    source="mcp",
                    start_time=start_time,
                    end_time=end_time,
                )
                logs.extend(mcp_logs)

        # Sort by timestamp
        logs.sort(key=lambda x: x.timestamp)

        # Limit to most relevant logs (max 50)
        return logs[:50]

    def _extract_from_file(
        self,
        file_path: Path,
        source: str,
        start_time: datetime,
        end_time: datetime,
    ) -> list[LogEntry]:
        """Extract log entries from a single file."""
        if not file_path.exists():
            return []

        logs = []

        try:
            # Read last 1000 lines for performance
            with file_path.open("r") as f:
                lines = f.readlines()[-1000:]

            for line in lines:
                log_entry = self._parse_log_line(line, source)
                if log_entry and start_time <= log_entry.timestamp <= end_time:
                    logs.append(log_entry)

        except Exception as e:
            logger.warning(f"Failed to read log file {file_path}: {e}")

        return logs

    def _parse_log_line(self, line: str, source: str) -> Optional[LogEntry]:
        """Parse a single log line."""
        # Common log patterns
        patterns = [
            # ISO format: 2026-01-14T17:24:31.123456
            r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?)\s+(\w+)\s+(.+)",
            # Uvicorn format: INFO:     2026-01-14 17:24:31 - message
            r"(\w+):\s+(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s+-\s+(.+)",
            # Simple format: [2026-01-14 17:24:31] INFO: message
            r"\[(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\]\s+(\w+):\s+(.+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, line)
            if match:
                try:
                    groups = match.groups()
                    if len(groups) == 3:
                        timestamp_str, level, message = groups
                        # Try to parse timestamp
                        for fmt in [
                            "%Y-%m-%dT%H:%M:%S.%f",
                            "%Y-%m-%dT%H:%M:%S",
                            "%Y-%m-%d %H:%M:%S",
                        ]:
                            try:
                                timestamp = datetime.strptime(timestamp_str, fmt)
                                return LogEntry(
                                    timestamp=timestamp,
                                    level=level.upper(),
                                    source=source,
                                    message=message.strip(),
                                    raw_line=line.strip(),
                                )
                            except ValueError:
                                continue
                except Exception:
                    continue

        # If no pattern matches, return None
        return None

    def _identify_error_type(self, error_message: str) -> ErrorType:
        """Identify error type from error message."""
        error_lower = error_message.lower()

        if "500" in error_lower or "internal server error" in error_lower:
            return ErrorType.API_ERROR
        elif "celery" in error_lower or "task" in error_lower:
            return ErrorType.CELERY_ERROR
        elif "mcp" in error_lower:
            return ErrorType.MCP_ERROR
        elif "database" in error_lower or "sql" in error_lower:
            return ErrorType.DATABASE_ERROR
        elif "validation" in error_lower or "invalid" in error_lower:
            return ErrorType.VALIDATION_ERROR
        elif "auth" in error_lower or "unauthorized" in error_lower or "forbidden" in error_lower:
            return ErrorType.AUTHENTICATION_ERROR
        elif "rate limit" in error_lower or "too many requests" in error_lower:
            return ErrorType.RATE_LIMIT_ERROR
        else:
            return ErrorType.UNKNOWN_ERROR

    def _build_log_analysis_prompt(
        self,
        test_name: str,
        error_message: str,
        relevant_logs: list[LogEntry],
        error_type: ErrorType,
    ) -> str:
        """Build prompt for LLM log analysis."""
        # Format logs for prompt
        logs_str = "\n".join([f"[{log.timestamp.isoformat()}] {log.source.upper()} {log.level}: {log.message}" for log in relevant_logs[-20:]])  # Last 20 logs

        return f"""Analyze these application logs to identify the root cause of a test failure:

Test Name: {test_name}
Error Message: {error_message}
Suspected Error Type: {error_type.value}

Recent Application Logs:
{logs_str}

Analyze the logs and determine:
1. What is the root cause of this test failure?
2. Which log entries are most relevant?
3. What is the error type (API_ERROR, CELERY_ERROR, MCP_ERROR, DATABASE_ERROR, etc.)?
4. What fix would resolve this issue?

Respond with JSON containing:
{{
  "root_cause": "Clear explanation of what went wrong",
  "error_type": "ERROR_TYPE_ENUM",
  "suggested_fix": "Actionable fix to resolve the issue",
  "confidence": 0.0-1.0,
  "key_log_patterns": ["pattern1", "pattern2"]
}}"""

    def _parse_analysis_response(self, content: str) -> dict[str, Any]:
        """Parse LLM analysis response from JSON."""
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
                return json.loads(content)
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
                return json.loads(content)
            else:
                # Last resort: return minimal result
                logger.warning(f"Failed to parse log analysis response: {content}")
                return {
                    "root_cause": f"Parse error: {content[:100]}",
                    "error_type": "UNKNOWN_ERROR",
                    "suggested_fix": "Check logs manually",
                    "confidence": 0.0,
                    "key_log_patterns": [],
                }
