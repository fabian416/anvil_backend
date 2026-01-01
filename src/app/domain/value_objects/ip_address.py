"""
IP Address value object.

Represents a user's IP address (IPv4 or IPv6).
"""

import re
from dataclasses import dataclass
from typing import Optional


# IPv4 pattern
IPV4_PATTERN = re.compile(
    r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}'
    r'(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
)

# Simplified IPv6 pattern (allows :: compression)
IPV6_PATTERN = re.compile(
    r'^(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$|'
    r'^(?:[0-9a-fA-F]{1,4}:){1,7}:$|'
    r'^(?:[0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}$|'
    r'^(?:[0-9a-fA-F]{1,4}:){1,5}(?::[0-9a-fA-F]{1,4}){1,2}$|'
    r'^(?:[0-9a-fA-F]{1,4}:){1,4}(?::[0-9a-fA-F]{1,4}){1,3}$|'
    r'^(?:[0-9a-fA-F]{1,4}:){1,3}(?::[0-9a-fA-F]{1,4}){1,4}$|'
    r'^(?:[0-9a-fA-F]{1,4}:){1,2}(?::[0-9a-fA-F]{1,4}){1,5}$|'
    r'^[0-9a-fA-F]{1,4}:(?::[0-9a-fA-F]{1,4}){1,6}$|'
    r'^:(?::[0-9a-fA-F]{1,4}){1,7}$|'
    r'^::$'
)


@dataclass(frozen=True, slots=True)
class IpAddress:
    """
    Value object representing an IP address.
    
    Supports both IPv4 and IPv6 addresses.
    Maximum length: 45 characters (full IPv6 with zone ID).
    
    Examples:
        - IPv4: "192.168.1.1"
        - IPv6: "2001:0db8:85a3:0000:0000:8a2e:0370:7334"
        - IPv6 compressed: "::1"
    """
    
    value: str
    
    def __post_init__(self) -> None:
        """Validate the IP address format."""
        if not self.value:
            raise ValueError("IP address cannot be empty")
        
        # Normalize: strip whitespace
        normalized = self.value.strip()
        
        # Length check (max IPv6 with zone ID)
        if len(normalized) > 45:
            raise ValueError(f"IP address too long: {len(normalized)} chars (max 45)")
        
        # Allow localhost variants
        if normalized in ("localhost", "127.0.0.1", "::1"):
            object.__setattr__(self, "value", normalized)
            return
        
        # Validate format
        if not self._is_valid_ip(normalized):
            raise ValueError(f"Invalid IP address format: {normalized}")
        
        object.__setattr__(self, "value", normalized)
    
    @staticmethod
    def _is_valid_ip(ip: str) -> bool:
        """Check if string is a valid IPv4 or IPv6 address."""
        # Check IPv4
        if IPV4_PATTERN.match(ip):
            return True
        
        # Check IPv6
        if IPV6_PATTERN.match(ip):
            return True
        
        # Check IPv6 with zone ID (e.g., fe80::1%eth0)
        if "%" in ip:
            base_ip = ip.split("%")[0]
            return IPV6_PATTERN.match(base_ip) is not None
        
        return False
    
    @classmethod
    def from_optional(cls, value: Optional[str]) -> Optional["IpAddress"]:
        """Create IpAddress from optional string, returning None if empty."""
        if not value or not value.strip():
            return None
        try:
            return cls(value)
        except ValueError:
            # Log invalid IP but don't fail
            return None
    
    def __str__(self) -> str:
        return self.value
    
    def __repr__(self) -> str:
        return f"IpAddress({self.value!r})"
    
    @property
    def is_ipv4(self) -> bool:
        """Check if this is an IPv4 address."""
        return bool(IPV4_PATTERN.match(self.value))
    
    @property
    def is_ipv6(self) -> bool:
        """Check if this is an IPv6 address."""
        return not self.is_ipv4
    
    @property
    def is_localhost(self) -> bool:
        """Check if this is a localhost address."""
        return self.value in ("localhost", "127.0.0.1", "::1")
