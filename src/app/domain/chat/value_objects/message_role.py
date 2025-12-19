"""
Message role value object.
"""

from enum import Enum


class MessageRole(str, Enum):
    """
    Message role enumeration.
    
    Defines who sent a message in a conversation.
    """
    
    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"
