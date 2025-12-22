"""
WebSocket connection state enumeration.

Defines the possible states of a WebSocket session.
"""

from enum import Enum


class ConnectionState(Enum):
    """
    WebSocket connection states.

    Values:
        CONNECTED: Active connection established
        DISCONNECTED: Connection closed or terminated
        IDLE: Connection active but no recent activity
        RECONNECTING: Attempting to restore connection
    """

    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    IDLE = "idle"
    RECONNECTING = "reconnecting"
