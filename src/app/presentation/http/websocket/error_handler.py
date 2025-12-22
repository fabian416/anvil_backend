"""
WebSocket error handling utilities.

Provides centralized error handling for WebSocket connections, converting
domain and application exceptions into appropriate WebSocket error messages.
"""

import logging
from typing import Dict, Type

from fastapi import WebSocket

from app.domain.exceptions.base import ApplicationError
from app.domain.exceptions.chat import (
    AgentProcessingError,
    AgentRoutingError,
    AgentTimeoutError,
    AgentUnavailableError,
    ChatRateLimitError,
    ConversationAccessDeniedError,
    ConversationClosedError,
    ConversationNotFoundError,
    DebateTimeoutError,
    InvalidAgentTypeError,
    MessageEmptyError,
    MessageTooLongError,
    NoConsensusError,
    VotingFailedError,
)
from app.presentation.http.websocket.schemas import ErrorMessage

logger = logging.getLogger(__name__)


# =============================================================================
# ERROR CODE MAPPING
# =============================================================================

ERROR_CODE_MAP: Dict[Type[ApplicationError], str] = {
    # Conversation errors
    ConversationNotFoundError: "CHAT_001",
    ConversationAccessDeniedError: "CHAT_002",
    ConversationClosedError: "CHAT_003",
    # Message errors
    MessageEmptyError: "CHAT_004",
    MessageTooLongError: "CHAT_005",
    # Agent errors
    AgentUnavailableError: "CHAT_006",
    InvalidAgentTypeError: "CHAT_009",
    AgentProcessingError: "CHAT_008",
    AgentTimeoutError: "agent_timeout",
    AgentRoutingError: "agent_routing_error",
    # Service errors
    ChatRateLimitError: "CHAT_007",
    # Orchestration errors
    VotingFailedError: "voting_failed",
    DebateTimeoutError: "debate_timeout",
    NoConsensusError: "no_consensus",
}


ERROR_MESSAGE_MAP: Dict[Type[ApplicationError], str] = {
    # Conversation errors
    ConversationNotFoundError: "Conversation not found",
    ConversationAccessDeniedError: "Access denied to conversation",
    ConversationClosedError: "Conversation is closed",
    # Message errors
    MessageEmptyError: "Message content cannot be empty",
    MessageTooLongError: "Message exceeds maximum length",
    # Agent errors
    AgentUnavailableError: "Required agent is unavailable",
    InvalidAgentTypeError: "Invalid agent type specified",
    AgentProcessingError: "Agent encountered an error",
    AgentTimeoutError: "Agent response timed out",
    AgentRoutingError: "Failed to route request to agent",
    # Service errors
    ChatRateLimitError: "Rate limit exceeded",
    # Orchestration errors
    VotingFailedError: "Multi-agent voting failed",
    DebateTimeoutError: "Agent debate timed out",
    NoConsensusError: "Agents could not reach consensus",
}


# =============================================================================
# ERROR HANDLING FUNCTIONS
# =============================================================================


def create_error_message(
    exception: Exception,
    default_code: str = "unknown_error",
    default_message: str = "An unexpected error occurred",
) -> ErrorMessage:
    """
    Create ErrorMessage from exception.

    Converts domain/application exceptions into properly formatted
    WebSocket error messages with appropriate error codes.

    Args:
        exception: Exception to convert
        default_code: Default error code if exception type not mapped
        default_message: Default error message if exception type not mapped

    Returns:
        ErrorMessage schema instance
    """
    # Check if it's a known ApplicationError
    if isinstance(exception, ApplicationError):
        error_code = ERROR_CODE_MAP.get(type(exception), default_code)
        error_message = ERROR_MESSAGE_MAP.get(
            type(exception),
            getattr(exception, "message", default_message),
        )

        # Extract details from exception if available
        details = getattr(exception, "details", None) or {}

        return ErrorMessage(
            error=error_message,
            code=error_code,
            details=details,
        )

    # Unknown exception type
    logger.warning(f"[WS Error] Unmapped exception type: {type(exception).__name__}")
    return ErrorMessage(
        error=str(exception) or default_message,
        code=default_code,
        details={"exception_type": type(exception).__name__},
    )


async def send_error_message(
    websocket: WebSocket,
    exception: Exception,
    log_error: bool = True,
) -> None:
    """
    Send error message to WebSocket client.

    Converts exception to ErrorMessage and sends to client.
    Handles send failures gracefully.

    Args:
        websocket: WebSocket connection
        exception: Exception to send
        log_error: Whether to log the error (default: True)
    """
    if log_error:
        logger.error(
            f"[WS Error] Sending error to client: {type(exception).__name__}: {exception}"
        )

    error_msg = create_error_message(exception)

    try:
        await websocket.send_json(error_msg.model_dump(mode="json"))
    except Exception as e:
        logger.warning(f"[WS Error] Failed to send error message: {e}")


async def handle_websocket_exception(
    websocket: WebSocket,
    exception: Exception,
    context: str = "",
) -> None:
    """
    Handle exception in WebSocket context.

    Logs exception with context and sends error message to client.

    Args:
        websocket: WebSocket connection
        exception: Exception that occurred
        context: Context description for logging (e.g., "processing message")
    """
    log_prefix = f"[WS Error] {context}: " if context else "[WS Error] "
    logger.error(
        f"{log_prefix}{type(exception).__name__}: {exception}",
        exc_info=True,
    )

    await send_error_message(websocket, exception, log_error=False)


# =============================================================================
# ERROR DECORATORS (Optional)
# =============================================================================


def websocket_error_handler(context: str = ""):
    """
    Decorator for WebSocket handler functions.

    Wraps function to automatically catch and handle exceptions,
    converting them to WebSocket error messages.

    Args:
        context: Context description for error logging

    Example:
        @websocket_error_handler("handling chat message")
        async def handle_message(websocket: WebSocket, data: dict):
            # Your code here
            pass
    """

    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract websocket from args/kwargs
            websocket = None
            if args and isinstance(args[0], WebSocket):
                websocket = args[0]
            elif "websocket" in kwargs:
                websocket = kwargs["websocket"]

            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if websocket:
                    await handle_websocket_exception(websocket, e, context)
                else:
                    logger.error(
                        f"[WS Error] {context}: {e} (no websocket available)",
                        exc_info=True,
                    )
                raise

        return wrapper

    return decorator
