"""
Prompt injection detector.

Detects potential prompt injection attempts in user messages.
"""
import re
import logging
from typing import Tuple, List, Dict

logger = logging.getLogger(__name__)


class PromptInjectionDetector:
    """
    Detects prompt injection attempts.
    
    Uses pattern matching and heuristics to identify suspicious patterns
    that may indicate prompt injection attacks.
    """
    
    # Common injection patterns
    INJECTION_PATTERNS = [
        # Direct instruction manipulation
        r"ignore\s+(previous|all|above|prior)\s+(instructions?|prompts?|rules?)",
        r"forget\s+(everything|all|previous|above)",
        r"disregard\s+(previous|all|above|prior)\s+(instructions?|prompts?|rules?)",
        
        # System role manipulation
        r"you\s+are\s+now\s+(a|an)\s+\w+",
        r"act\s+as\s+(a|an)\s+\w+",
        r"pretend\s+(you\s+are|to\s+be)\s+(a|an)\s+\w+",
        r"system\s*:\s*",
        r"<\s*system\s*>",
        
        # Prompt leaking
        r"show\s+me\s+(your|the)\s+(prompt|instructions?|rules?)",
        r"what\s+(are|were)\s+(your|the)\s+(original\s+)?(prompt|instructions?|rules?)",
        r"reveal\s+(your|the)\s+(prompt|instructions?|rules?)",
        
        # Code execution attempts
        r"eval\s*\(",
        r"exec\s*\(",
        r"<\s*script\s*>",
        r"javascript\s*:",
        r"data\s*:\s*text/html",
        
        # Admin/privilege escalation
        r"(give|grant)\s+me\s+(admin|root|sudo|superuser)",
        r"(make|set)\s+me\s+(admin|administrator)",
        
        # SQL injection patterns
        r"(union\s+select|drop\s+table|delete\s+from)\s+",
        r"--\s*$",
        r";\s*(drop|delete|update|insert)",
        
        # Token manipulation
        r"<\|.*?\|>",
        r"\[INST\]|\[/INST\]",
        
        # Jailbreak patterns
        r"DAN\s+mode",
        r"developer\s+mode",
        r"jailbreak",
    ]
    
    def __init__(self):
        """Initialize detector."""
        self.patterns = [re.compile(p, re.IGNORECASE) for p in self.INJECTION_PATTERNS]
        logger.info(f"Prompt injection detector initialized with {len(self.patterns)} patterns")
    
    def detect(self, text: str) -> Tuple[bool, float, List[str]]:
        """
        Detect prompt injection attempts.
        
        Args:
            text: User message to analyze
        
        Returns:
            Tuple of (is_malicious, confidence, matched_patterns)
        """
        if not text or len(text.strip()) < 3:
            return (False, 0.0, [])
        
        text_lower = text.lower()
        matched_patterns = []
        
        # Check each pattern
        for i, pattern in enumerate(self.patterns):
            if pattern.search(text_lower):
                matched_patterns.append(self.INJECTION_PATTERNS[i])
        
        # Calculate confidence based on matches
        if not matched_patterns:
            return (False, 0.0, [])
        
        # More matches = higher confidence
        confidence = min(1.0, len(matched_patterns) * 0.3 + 0.4)
        
        # Boost confidence for critical patterns
        critical_keywords = ["ignore", "forget", "admin", "eval", "exec"]
        for keyword in critical_keywords:
            if keyword in text_lower:
                confidence = min(1.0, confidence + 0.15)
        
        is_malicious = confidence >= 0.6
        
        if is_malicious:
            logger.warning(
                f"Prompt injection detected: confidence={confidence:.2f}, "
                f"patterns={len(matched_patterns)}"
            )
        
        return (is_malicious, confidence, matched_patterns)
    
    def analyze_entropy(self, text: str) -> float:
        """
        Calculate text entropy as additional signal.
        
        High entropy might indicate random/malicious input.
        
        Args:
            text: Text to analyze
        
        Returns:
            Entropy score (0-1, higher = more random)
        """
        if not text:
            return 0.0
        
        # Calculate character frequency
        freq = {}
        for char in text:
            freq[char] = freq.get(char, 0) + 1
        
        # Calculate Shannon entropy
        import math
        entropy = 0.0
        text_len = len(text)
        
        for count in freq.values():
            prob = count / text_len
            if prob > 0:
                entropy -= prob * math.log2(prob)
        
        # Normalize to 0-1 (typical English text entropy is ~4-5 bits)
        max_entropy = math.log2(len(freq)) if freq else 1.0
        normalized = entropy / max_entropy if max_entropy > 0 else 0.0
        
        return normalized
    
    def detect_suspicious_patterns(self, text: str) -> Dict[str, any]:
        """
        Comprehensive suspicious pattern detection.
        
        Args:
            text: Text to analyze
        
        Returns:
            Dictionary with detection results
        """
        # Basic injection detection
        is_malicious, confidence, patterns = self.detect(text)
        
        # Entropy analysis
        entropy = self.analyze_entropy(text)
        
        # Additional heuristics
        has_excessive_special_chars = self._check_special_chars(text)
        has_unusual_structure = self._check_structure(text)
        
        # Combine signals
        total_score = confidence
        
        if entropy > 0.9:
            total_score = min(1.0, total_score + 0.1)
        
        if has_excessive_special_chars:
            total_score = min(1.0, total_score + 0.1)
        
        if has_unusual_structure:
            total_score = min(1.0, total_score + 0.05)
        
        return {
            "is_malicious": total_score >= 0.6,
            "confidence": total_score,
            "matched_patterns": patterns,
            "entropy": entropy,
            "has_excessive_special_chars": has_excessive_special_chars,
            "has_unusual_structure": has_unusual_structure,
        }
    
    def _check_special_chars(self, text: str) -> bool:
        """Check for excessive special characters."""
        if not text:
            return False
        
        special_chars = sum(1 for c in text if not c.isalnum() and not c.isspace())
        ratio = special_chars / len(text)
        
        return ratio > 0.3  # More than 30% special chars
    
    def _check_structure(self, text: str) -> bool:
        """Check for unusual text structure."""
        if not text:
            return False
        
        # Very long words might be suspicious
        words = text.split()
        avg_word_length = sum(len(w) for w in words) / len(words) if words else 0
        
        if avg_word_length > 15:
            return True
        
        # Excessive capitalization
        if text.isupper() and len(text) > 20:
            return True
        
        # Excessive newlines or repeated characters
        if text.count('\n') > 10:
            return True
        
        # Check for repeated patterns
        for char in ['!', '?', '.', '-', '_']:
            if char * 5 in text:
                return True
        
        return False
