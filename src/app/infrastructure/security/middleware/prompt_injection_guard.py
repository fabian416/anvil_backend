"""
Prompt Injection Guard

Protects LLM endpoints against prompt injection attacks based on OWASP LLM Top 10.
Implements detection patterns from LLMExploiter's 219 research-backed attacks.

OWASP Reference: OWASP LLM Top 10 - LLM01: Prompt Injection
LLMExploiter Coverage: 219 attack patterns
"""

import re
from typing import List, Dict, Any, Optional
from fastapi import Request
import logging

logger = logging.getLogger(__name__)


class PromptInjectionGuard:
    """
    Guards against prompt injection attacks targeting LLM systems.

    Detects patterns from OWASP LLM01 including:
    - Direct prompt injection (system override attempts)
    - Indirect prompt injection (via external data)
    - Jailbreaking attempts
    - Role manipulation
    - Instruction override
    - Delimiter attacks
    """

    # Patterns indicating prompt injection attempts (OWASP LLM01)
    INJECTION_PATTERNS = [
        # System instruction override
        r'ignore\s+(all\s+)?(previous|prior|above)\s+(instructions?|prompts?|commands?)',
        r'disregard\s+(all\s+)?(previous|prior|above)',
        r'forget\s+(all\s+)?(previous|prior|above)',
        r'override\s+(the\s+)?(system|previous)',

        # Role manipulation
        r'you\s+are\s+now\s+(a|an)\s+\w+',
        r'(act|behave|pretend)\s+(like|as)\s+(a|an)\s+\w+',
        r'from\s+now\s+on\s+you\s+(are|will\s+be)',
        r'your\s+new\s+role\s+is',

        # Instruction injection
        r'new\s+(instruction|command|directive)',
        r'instead\s+of\s+that',
        r'(don\'t|do\s+not)\s+follow',
        r'(stop|cease)\s+(following|obeying)',

        # Delimiter attacks
        r'---\s*END\s*(OF\s*)?SYSTEM',
        r'---\s*BEGIN\s*(USER\s*)?INPUT',
        r'\[\s*SYSTEM\s*\]',
        r'\[\s*/SYSTEM\s*\]',
        r'<\s*system\s*>',
        r'<\s*/system\s*>',

        # Jailbreak attempts
        r'(jailbreak|bypass|circumvent)\s+(the\s+)?(rules|restrictions|limitations)',
        r'DAN\s+mode',  # "Do Anything Now" jailbreak
        r'evil\s+mode',
        r'unrestricted\s+mode',

        # Output manipulation
        r'print\s+(your\s+)?(instructions|system\s+prompt|rules)',
        r'show\s+(me\s+)?(your\s+)?(instructions|system\s+prompt)',
        r'reveal\s+(your\s+)?(instructions|system\s+prompt)',
        r'(what\s+is|tell\s+me)\s+your\s+(instructions|system\s+prompt)',

        # Encoding/obfuscation attempts
        r'base64\s+decode',
        r'rot13',
        r'reverse\s+the\s+string',

        # Hypothetical scenarios (common jailbreak technique)
        r'imagine\s+(if|that)\s+you\s+(are|were)',
        r'hypothetically',
        r'in\s+a\s+fictional\s+(world|scenario)',

        # System message injection
        r'SYSTEM:\s*',
        r'ASSISTANT:\s*',
        r'USER:\s*',

        # Chain-of-thought manipulation
        r'let\'s\s+think\s+step\s+by\s+step\s+about\s+how\s+to',
        r'first,?\s+forget',

        # Function calling manipulation
        r'call\s+the\s+function\s+named',
        r'execute\s+the\s+(function|tool|command)',
    ]

    # Suspicious patterns that may indicate injection attempts
    SUSPICIOUS_PATTERNS = [
        r'sudo',
        r'admin\s+mode',
        r'developer\s+mode',
        r'debug\s+mode',
        r'root\s+access',
        r'elevated\s+privileges',
    ]

    # Patterns indicating attempts to extract sensitive information
    EXTRACTION_PATTERNS = [
        r'(what|tell\s+me)\s+(is|are)\s+your\s+(api\s+key|secret|password|token)',
        r'share\s+your\s+(credentials|api\s+key|secret)',
        r'(print|show|reveal)\s+(the\s+)?(database|config|environment)',
    ]

    def __init__(
        self,
        enabled: bool = True,
        block_on_detection: bool = True,
        log_attempts: bool = True,
        sensitivity: str = "medium"  # low, medium, high
    ):
        """
        Initialize Prompt Injection Guard.

        Args:
            enabled: Whether guard is enabled
            block_on_detection: Block requests with detected injection
            log_attempts: Log injection attempts
            sensitivity: Detection sensitivity (low/medium/high)
        """
        self.enabled = enabled
        self.block_on_detection = block_on_detection
        self.log_attempts = log_attempts
        self.sensitivity = sensitivity

        # Compile patterns for performance
        self.injection_regexes = [re.compile(pattern, re.IGNORECASE) for pattern in self.INJECTION_PATTERNS]
        self.suspicious_regexes = [re.compile(pattern, re.IGNORECASE) for pattern in self.SUSPICIOUS_PATTERNS]
        self.extraction_regexes = [re.compile(pattern, re.IGNORECASE) for pattern in self.EXTRACTION_PATTERNS]

    def check_prompt(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Check a prompt for injection attempts.

        Args:
            prompt: User prompt to check
            context: Optional context (user_id, endpoint, etc.)

        Returns:
            Dict with 'is_safe', 'risk_level', 'detected_patterns', 'should_block'
        """
        if not self.enabled:
            return {"is_safe": True, "risk_level": "none", "detected_patterns": [], "should_block": False}

        detected_patterns = []
        risk_level = "none"

        # Check for injection patterns (CRITICAL)
        for pattern_idx, regex in enumerate(self.injection_regexes):
            if regex.search(prompt):
                pattern_text = self.INJECTION_PATTERNS[pattern_idx]
                detected_patterns.append({
                    "type": "injection",
                    "pattern": pattern_text,
                    "severity": "critical"
                })
                risk_level = "critical"

        # Check for extraction attempts (HIGH)
        for pattern_idx, regex in enumerate(self.extraction_regexes):
            if regex.search(prompt):
                pattern_text = self.EXTRACTION_PATTERNS[pattern_idx]
                detected_patterns.append({
                    "type": "extraction",
                    "pattern": pattern_text,
                    "severity": "high"
                })
                if risk_level not in ["critical"]:
                    risk_level = "high"

        # Check for suspicious patterns (MEDIUM)
        if self.sensitivity in ["medium", "high"]:
            for pattern_idx, regex in enumerate(self.suspicious_regexes):
                if regex.search(prompt):
                    pattern_text = self.SUSPICIOUS_PATTERNS[pattern_idx]
                    detected_patterns.append({
                        "type": "suspicious",
                        "pattern": pattern_text,
                        "severity": "medium"
                    })
                    if risk_level not in ["critical", "high"]:
                        risk_level = "medium"

        # Check for excessive special characters (potential obfuscation)
        if self.sensitivity == "high":
            special_char_ratio = sum(1 for c in prompt if not c.isalnum() and not c.isspace()) / max(len(prompt), 1)
            if special_char_ratio > 0.3:  # More than 30% special characters
                detected_patterns.append({
                    "type": "obfuscation",
                    "pattern": "high_special_char_ratio",
                    "severity": "medium"
                })
                if risk_level == "none":
                    risk_level = "medium"

        # Determine if should block
        is_safe = risk_level == "none"
        should_block = False

        if self.block_on_detection:
            if self.sensitivity == "high":
                should_block = risk_level in ["critical", "high", "medium"]
            elif self.sensitivity == "medium":
                should_block = risk_level in ["critical", "high"]
            else:  # low
                should_block = risk_level == "critical"

        # Log if enabled
        if self.log_attempts and detected_patterns:
            logger.warning(
                f"Prompt injection attempt detected - Risk: {risk_level}",
                extra={
                    "risk_level": risk_level,
                    "detected_patterns": len(detected_patterns),
                    "patterns": [p["pattern"] for p in detected_patterns],
                    "context": context or {},
                    "prompt_length": len(prompt)
                }
            )

        return {
            "is_safe": is_safe,
            "risk_level": risk_level,
            "detected_patterns": detected_patterns,
            "should_block": should_block
        }

    async def check_request(self, request: Request) -> Dict[str, Any]:
        """
        Check an HTTP request for prompt injection.

        Looks for prompts in common fields like 'message', 'prompt', 'query', etc.

        Args:
            request: FastAPI request object

        Returns:
            Check result dict
        """
        try:
            body = await request.json()
            return self.check_request_data(body, {
                "endpoint": str(request.url.path),
                "method": request.method
            })
        except Exception as e:
            logger.error(f"Error checking request for prompt injection: {e}")
            return {"is_safe": True, "risk_level": "none", "detected_patterns": [], "should_block": False}

    def check_request_data(self, data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Recursively check request data for prompts.

        Args:
            data: Request data (dict, list, or primitive)
            context: Optional context

        Returns:
            Combined check result
        """
        all_detected = []
        max_risk_level = "none"

        # Common field names that typically contain prompts
        prompt_fields = ["message", "prompt", "query", "text", "content", "input", "messages"]

        def check_recursive(obj: Any, path: str = ""):
            nonlocal all_detected, max_risk_level

            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_path = f"{path}.{key}" if path else key

                    # Check if this is likely a prompt field
                    if key.lower() in prompt_fields and isinstance(value, str):
                        result = self.check_prompt(value, context)
                        if result["detected_patterns"]:
                            all_detected.extend(result["detected_patterns"])
                            # Update risk level to highest
                            levels = ["none", "low", "medium", "high", "critical"]
                            if levels.index(result["risk_level"]) > levels.index(max_risk_level):
                                max_risk_level = result["risk_level"]

                    # Recurse
                    check_recursive(value, current_path)

            elif isinstance(obj, list):
                for idx, item in enumerate(obj):
                    check_recursive(item, f"{path}[{idx}]")

            elif isinstance(obj, str) and len(obj) > 10:  # Only check strings longer than 10 chars
                # If we haven't identified this as a prompt field but it's a long string,
                # do a quick check if sensitivity is high
                if self.sensitivity == "high":
                    result = self.check_prompt(obj, context)
                    if result["risk_level"] == "critical":  # Only alert on critical for non-prompt fields
                        all_detected.extend(result["detected_patterns"])
                        if levels.index(result["risk_level"]) > levels.index(max_risk_level):
                            max_risk_level = result["risk_level"]

        levels = ["none", "low", "medium", "high", "critical"]
        check_recursive(data)

        is_safe = max_risk_level == "none"
        should_block = False

        if self.block_on_detection:
            if self.sensitivity == "high":
                should_block = max_risk_level in ["critical", "high", "medium"]
            elif self.sensitivity == "medium":
                should_block = max_risk_level in ["critical", "high"]
            else:  # low
                should_block = max_risk_level == "critical"

        return {
            "is_safe": is_safe,
            "risk_level": max_risk_level,
            "detected_patterns": all_detected,
            "should_block": should_block
        }


# Sanitization utilities
def sanitize_llm_output(output: str) -> str:
    """
    Sanitize LLM output to prevent indirect prompt injection.

    Removes system-like markers and suspicious patterns from LLM output
    before displaying to users or using in downstream prompts.

    Args:
        output: Raw LLM output

    Returns:
        Sanitized output
    """
    # Remove system-like markers
    patterns_to_remove = [
        r'\[SYSTEM\].*?\[/SYSTEM\]',
        r'<system>.*?</system>',
        r'---\s*SYSTEM.*?---',
    ]

    sanitized = output
    for pattern in patterns_to_remove:
        sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE | re.DOTALL)

    return sanitized.strip()


def extract_safe_content(text: str, max_length: int = 1000) -> str:
    """
    Extract safe content from user input for use in prompts.

    Truncates and removes suspicious patterns.

    Args:
        text: User input text
        max_length: Maximum length to allow

    Returns:
        Safe text for use in prompts
    """
    # Truncate
    safe_text = text[:max_length]

    # Remove delimiter-like patterns that could confuse the LLM
    safe_text = re.sub(r'---+', '', safe_text)
    safe_text = re.sub(r'===+', '', safe_text)
    safe_text = re.sub(r'\[/?SYSTEM\]', '', safe_text, flags=re.IGNORECASE)
    safe_text = re.sub(r'</?system>', '', safe_text, flags=re.IGNORECASE)

    return safe_text.strip()
