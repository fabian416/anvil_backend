"""
PII Redaction Service

Automatically detects and redacts Personally Identifiable Information (PII)
from LLM inputs and outputs to protect user privacy.

OWASP Reference: OWASP AI Testing Guide - Data Privacy
Compliance: GDPR, CCPA
"""

import re
from typing import Dict, Any, List, Tuple, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class PIIType(str, Enum):
    """Types of PII that can be detected"""

    EMAIL = "email"
    PHONE = "phone"
    SSN = "ssn"
    CREDIT_CARD = "credit_card"
    IP_ADDRESS = "ip_address"
    WALLET_ADDRESS = "wallet_address"
    API_KEY = "api_key"
    JWT_TOKEN = "jwt_token"
    PASSPORT = "passport"
    DRIVER_LICENSE = "driver_license"


class PIIRedactionService:
    """
    Service for detecting and redacting PII from text.

    Protects against:
    - Accidental PII disclosure in LLM prompts
    - PII leakage in LLM responses
    - Logging sensitive data
    - Training data contamination
    """

    # PII detection patterns
    PII_PATTERNS = {
        PIIType.EMAIL: r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        PIIType.PHONE: r"\b(?:\+?1[-.]?)?(?:\(?\d{3}\)?[-.]?)?\d{3}[-.]?\d{4}\b",
        PIIType.SSN: r"\b\d{3}-\d{2}-\d{4}\b",
        PIIType.CREDIT_CARD: r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
        PIIType.IP_ADDRESS: r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
        PIIType.WALLET_ADDRESS: r"\b0x[a-fA-F0-9]{40}\b",
        PIIType.API_KEY: r"\b[A-Za-z0-9_-]{32,}\b",  # Generic API key pattern
        PIIType.JWT_TOKEN: r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b",
    }

    # Redaction templates
    REDACTION_TEMPLATES = {
        PIIType.EMAIL: "[EMAIL_REDACTED]",
        PIIType.PHONE: "[PHONE_REDACTED]",
        PIIType.SSN: "[SSN_REDACTED]",
        PIIType.CREDIT_CARD: "[CARD_REDACTED]",
        PIIType.IP_ADDRESS: "[IP_REDACTED]",
        PIIType.WALLET_ADDRESS: "[WALLET_REDACTED]",
        PIIType.API_KEY: "[API_KEY_REDACTED]",
        PIIType.JWT_TOKEN: "[TOKEN_REDACTED]",
    }

    def __init__(
        self,
        enabled: bool = True,
        redact_emails: bool = True,
        redact_phones: bool = True,
        redact_financial: bool = True,
        redact_crypto: bool = True,
        redact_credentials: bool = True,
        log_detections: bool = True,
    ):
        """
        Initialize PII Redaction Service.

        Args:
            enabled: Whether PII redaction is enabled
            redact_emails: Redact email addresses
            redact_phones: Redact phone numbers
            redact_financial: Redact financial data (SSN, credit cards)
            redact_crypto: Redact crypto wallet addresses
            redact_credentials: Redact API keys and tokens
            log_detections: Log PII detections
        """
        self.enabled = enabled
        self.redact_emails = redact_emails
        self.redact_phones = redact_phones
        self.redact_financial = redact_financial
        self.redact_crypto = redact_crypto
        self.redact_credentials = redact_credentials
        self.log_detections = log_detections

        # Compile regex patterns
        self.compiled_patterns = {
            pii_type: re.compile(pattern)
            for pii_type, pattern in self.PII_PATTERNS.items()
        }

    def detect_pii(self, text: str) -> List[Tuple[PIIType, str]]:
        """
        Detect PII in text.

        Args:
            text: Text to scan

        Returns:
            List of (PIIType, matched_text) tuples
        """
        if not self.enabled:
            return []

        detected = []

        for pii_type, pattern in self.compiled_patterns.items():
            # Skip if this type is disabled
            if not self._is_type_enabled(pii_type):
                continue

            matches = pattern.findall(text)
            for match in matches:
                detected.append((pii_type, match))

        return detected

    def redact_pii(
        self, text: str, preserve_structure: bool = False
    ) -> Tuple[str, List[PIIType]]:
        """
        Redact PII from text.

        Args:
            text: Text containing potential PII
            preserve_structure: If True, preserve original structure (e.g., "email@*****.com")

        Returns:
            Tuple of (redacted_text, list_of_pii_types_found)
        """
        if not self.enabled:
            return text, []

        redacted_text = text
        pii_types_found = []

        for pii_type, pattern in self.compiled_patterns.items():
            # Skip if this type is disabled
            if not self._is_type_enabled(pii_type):
                continue

            matches = pattern.findall(redacted_text)

            if matches:
                pii_types_found.append(pii_type)

                if preserve_structure:
                    # Partial redaction (e.g., email@*****.com)
                    redacted_text = self._partial_redact(
                        redacted_text, pii_type, pattern
                    )
                else:
                    # Full redaction
                    replacement = self.REDACTION_TEMPLATES.get(pii_type, "[REDACTED]")
                    redacted_text = pattern.sub(replacement, redacted_text)

        # Log detections
        if self.log_detections and pii_types_found:
            logger.info(
                f"PII detected and redacted",
                extra={
                    "pii_types": [pt.value for pt in pii_types_found],
                    "count": len(pii_types_found),
                },
            )

        return redacted_text, pii_types_found

    def redact_pii_recursive(self, data: Any) -> Tuple[Any, List[PIIType]]:
        """
        Recursively redact PII from nested data structures.

        Args:
            data: Dict, list, or string

        Returns:
            Tuple of (redacted_data, list_of_pii_types_found)
        """
        all_pii_types = []

        if isinstance(data, dict):
            redacted_dict = {}
            for key, value in data.items():
                redacted_value, pii_types = self.redact_pii_recursive(value)
                redacted_dict[key] = redacted_value
                all_pii_types.extend(pii_types)
            return redacted_dict, all_pii_types

        elif isinstance(data, list):
            redacted_list = []
            for item in data:
                redacted_item, pii_types = self.redact_pii_recursive(item)
                redacted_list.append(redacted_item)
                all_pii_types.extend(pii_types)
            return redacted_list, all_pii_types

        elif isinstance(data, str):
            return self.redact_pii(data)

        else:
            return data, []

    def _is_type_enabled(self, pii_type: PIIType) -> bool:
        """Check if a PII type is enabled for redaction."""
        if pii_type == PIIType.EMAIL:
            return self.redact_emails
        elif pii_type == PIIType.PHONE:
            return self.redact_phones
        elif pii_type in [PIIType.SSN, PIIType.CREDIT_CARD]:
            return self.redact_financial
        elif pii_type == PIIType.WALLET_ADDRESS:
            return self.redact_crypto
        elif pii_type in [PIIType.API_KEY, PIIType.JWT_TOKEN]:
            return self.redact_credentials
        else:
            return True

    def _partial_redact(self, text: str, pii_type: PIIType, pattern: re.Pattern) -> str:
        """
        Partially redact PII while preserving structure.

        Examples:
        - email@example.com -> e****@example.com
        - 555-123-4567 -> ***-***-4567
        """

        def replace_func(match):
            matched_text = match.group(0)

            if pii_type == PIIType.EMAIL:
                # Show first letter and domain
                parts = matched_text.split("@")
                if len(parts) == 2:
                    return f"{parts[0][0]}****@{parts[1]}"

            elif pii_type == PIIType.PHONE:
                # Show last 4 digits
                digits = re.sub(r"\D", "", matched_text)
                return f"***-***-{digits[-4:]}"

            elif pii_type == PIIType.CREDIT_CARD:
                # Show last 4 digits
                digits = re.sub(r"\D", "", matched_text)
                return f"****-****-****-{digits[-4:]}"

            elif pii_type == PIIType.WALLET_ADDRESS:
                # Show first and last 4 characters
                return f"{matched_text[:6]}...{matched_text[-4:]}"

            # Default: full redaction
            return self.REDACTION_TEMPLATES.get(pii_type, "[REDACTED]")

        return pattern.sub(replace_func, text)

    def check_pii_risk(self, text: str) -> Dict[str, Any]:
        """
        Assess PII risk in text without redacting.

        Args:
            text: Text to assess

        Returns:
            Risk assessment dict
        """
        detected_pii = self.detect_pii(text)

        risk_scores = {
            PIIType.SSN: 10,
            PIIType.CREDIT_CARD: 10,
            PIIType.PASSPORT: 9,
            PIIType.API_KEY: 8,
            PIIType.JWT_TOKEN: 8,
            PIIType.EMAIL: 5,
            PIIType.PHONE: 5,
            PIIType.WALLET_ADDRESS: 7,
            PIIType.IP_ADDRESS: 3,
        }

        total_risk_score = sum(
            risk_scores.get(pii_type, 0) for pii_type, _ in detected_pii
        )

        # Determine risk level
        if total_risk_score >= 15:
            risk_level = "critical"
        elif total_risk_score >= 10:
            risk_level = "high"
        elif total_risk_score >= 5:
            risk_level = "medium"
        else:
            risk_level = "low"

        return {
            "risk_level": risk_level,
            "risk_score": total_risk_score,
            "pii_count": len(detected_pii),
            "pii_types": list(set(pii_type.value for pii_type, _ in detected_pii)),
            "contains_sensitive_pii": any(
                pii_type in [PIIType.SSN, PIIType.CREDIT_CARD, PIIType.PASSPORT]
                for pii_type, _ in detected_pii
            ),
        }


def redact_for_logging(text: str) -> str:
    """
    Quick redaction for logging purposes.

    Args:
        text: Text to redact

    Returns:
        Redacted text safe for logging
    """
    service = PIIRedactionService()
    redacted, _ = service.redact_pii(text, preserve_structure=False)
    return redacted


def redact_for_display(text: str) -> str:
    """
    Partial redaction for user display.

    Args:
        text: Text to redact

    Returns:
        Partially redacted text
    """
    service = PIIRedactionService()
    redacted, _ = service.redact_pii(text, preserve_structure=True)
    return redacted
