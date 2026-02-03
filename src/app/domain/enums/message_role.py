from enum import Enum


class MessageRole(Enum):
    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"
