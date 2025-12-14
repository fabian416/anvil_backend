"""
Pydantic schemas for Security Dashboard API endpoints.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class VulnerabilitySummarySchema(BaseModel):
    """Summary of vulnerabilities by severity"""
    critical: int = Field(ge=0, description="Number of critical vulnerabilities")
    high: int = Field(ge=0, description="Number of high severity vulnerabilities")
    medium: int = Field(ge=0, description="Number of medium severity vulnerabilities")
    low: int = Field(ge=0, description="Number of low severity vulnerabilities")
    info: int = Field(ge=0, description="Number of informational findings")
    total: int = Field(ge=0, description="Total number of vulnerabilities")


class SecurityScanResultSchema(BaseModel):
    """Results from a security scan"""
    scan_id: str = Field(description="Unique scan identifier")
    scan_date: datetime = Field(description="Date and time of the scan")
    status: str = Field(description="Overall scan status (pass/fail/warning/error)")
    tools_executed: List[str] = Field(description="List of security tools executed")
    vulnerabilities: VulnerabilitySummarySchema = Field(description="Vulnerability counts by severity")
    reports_path: str = Field(description="Path to detailed scan reports")
    duration_seconds: Optional[float] = Field(None, description="Scan duration in seconds")
    errors: List[str] = Field(default_factory=list, description="Any errors encountered during scan")

    class Config:
        json_schema_extra = {
            "example": {
                "scan_id": "20241213_120000",
                "scan_date": "2024-12-13T12:00:00",
                "status": "pass",
                "tools_executed": ["Bandit", "Safety", "Helios", "LLMExploiter", "Nettacker"],
                "vulnerabilities": {
                    "critical": 0,
                    "high": 2,
                    "medium": 5,
                    "low": 10,
                    "info": 3,
                    "total": 20
                },
                "reports_path": "/security/reports/20241213_120000",
                "duration_seconds": 145.3,
                "errors": []
            }
        }


class ToolScanResultSchema(BaseModel):
    """Results from a single security tool"""
    tool_name: str = Field(description="Name of the security tool")
    scan_date: datetime = Field(description="Date and time of the tool execution")
    status: str = Field(description="Tool execution status")
    vulnerabilities_found: int = Field(ge=0, description="Number of vulnerabilities found by this tool")
    report_path: str = Field(description="Path to the tool's detailed report")
    details: Dict[str, Any] = Field(description="Additional tool-specific details")

    class Config:
        json_schema_extra = {
            "example": {
                "tool_name": "Bandit",
                "scan_date": "2024-12-13T12:00:00",
                "status": "completed",
                "vulnerabilities_found": 5,
                "report_path": "/security/reports/20241213_120000/bandit-report.json",
                "details": {
                    "critical": 0,
                    "high": 1,
                    "medium": 3,
                    "low": 1
                }
            }
        }


class ScanHistorySchema(BaseModel):
    """Historical scan results"""
    scans: List[SecurityScanResultSchema] = Field(description="List of historical scans")
    total_scans: int = Field(ge=0, description="Total number of scans available")

    class Config:
        json_schema_extra = {
            "example": {
                "scans": [
                    {
                        "scan_id": "20241213_120000",
                        "scan_date": "2024-12-13T12:00:00",
                        "status": "pass",
                        "tools_executed": ["Bandit", "Safety"],
                        "vulnerabilities": {
                            "critical": 0,
                            "high": 0,
                            "medium": 2,
                            "low": 5,
                            "info": 1,
                            "total": 8
                        },
                        "reports_path": "/security/reports/20241213_120000",
                        "duration_seconds": 120.0,
                        "errors": []
                    }
                ],
                "total_scans": 10
            }
        }


class VulnerabilityTrendsSchema(BaseModel):
    """Vulnerability trends over time"""
    dates: List[str] = Field(description="List of scan dates")
    critical: List[int] = Field(description="Critical vulnerability counts")
    high: List[int] = Field(description="High severity vulnerability counts")
    medium: List[int] = Field(description="Medium severity vulnerability counts")
    low: List[int] = Field(description="Low severity vulnerability counts")

    class Config:
        json_schema_extra = {
            "example": {
                "dates": ["2024-12-01", "2024-12-08", "2024-12-13"],
                "critical": [0, 0, 0],
                "high": [3, 2, 1],
                "medium": [5, 4, 3],
                "low": [10, 8, 5]
            }
        }


class SecurityDashboardSummarySchema(BaseModel):
    """Overall security dashboard summary"""
    latest_scan: Optional[SecurityScanResultSchema] = Field(None, description="Most recent scan results")
    total_scans: int = Field(ge=0, description="Total number of scans performed")
    active_tools: List[str] = Field(description="List of active security tools")
    overall_status: str = Field(description="Overall security posture (healthy/warning/critical)")

    class Config:
        json_schema_extra = {
            "example": {
                "latest_scan": {
                    "scan_id": "20241213_120000",
                    "scan_date": "2024-12-13T12:00:00",
                    "status": "pass",
                    "tools_executed": ["Bandit", "Safety", "Helios"],
                    "vulnerabilities": {
                        "critical": 0,
                        "high": 0,
                        "medium": 2,
                        "low": 5,
                        "info": 1,
                        "total": 8
                    },
                    "reports_path": "/security/reports/20241213_120000",
                    "errors": []
                },
                "total_scans": 45,
                "active_tools": ["Bandit", "Safety", "Helios", "LLMExploiter", "Nettacker"],
                "overall_status": "healthy"
            }
        }


class ScanToolsSchema(BaseModel):
    """List of individual tool results for a scan"""
    scan_id: str = Field(description="Scan identifier")
    tools: List[ToolScanResultSchema] = Field(description="Results from each tool")

    class Config:
        json_schema_extra = {
            "example": {
                "scan_id": "20241213_120000",
                "tools": [
                    {
                        "tool_name": "Bandit",
                        "scan_date": "2024-12-13T12:00:00",
                        "status": "completed",
                        "vulnerabilities_found": 5,
                        "report_path": "/security/reports/20241213_120000/bandit-report.json",
                        "details": {"critical": 0, "high": 1, "medium": 3, "low": 1}
                    },
                    {
                        "tool_name": "Safety",
                        "scan_date": "2024-12-13T12:05:00",
                        "status": "completed",
                        "vulnerabilities_found": 2,
                        "report_path": "/security/reports/20241213_120000/safety-report.json",
                        "details": {"critical": 0, "high": 0, "medium": 1, "low": 1}
                    }
                ]
            }
        }


class ErrorResponse(BaseModel):
    """Error response schema"""
    error: str = Field(description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")

    class Config:
        json_schema_extra = {
            "example": {
                "error": "Scan not found",
                "detail": "No scan results found for scan_id: 20241213_120000"
            }
        }
