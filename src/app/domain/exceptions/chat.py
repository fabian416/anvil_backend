"""
Chat-specific domain exceptions with standardized error codes.

This module provides all exceptions related to:
- Conversations (CRUD, access control)
- Messages (sending, validation)
- Agents (availability, routing, errors)
- Chat service (rate limits, overload)
"""

from typing import Any
from uuid import UUID

from app.domain.exceptions.base import ApplicationError
from app.domain.exceptions.error_codes import ErrorCode


# =============================================================================
# CONVERSATION ERRORS
# =============================================================================


class ConversationNotFoundError(ApplicationError):
    """Raised when a conversation is not found."""

    def __init__(
        self,
        conversation_id: str | UUID | None = None,
    ) -> None:
        details = {}
        if conversation_id:
            details["conversation_id"] = str(conversation_id)
        super().__init__(ErrorCode.CHAT_CONVERSATION_NOT_FOUND, details=details)


class ConversationAccessDeniedError(ApplicationError):
    """Raised when user doesn't have access to a conversation."""

    def __init__(
        self,
        conversation_id: str | UUID | None = None,
        user_id: str | UUID | None = None,
    ) -> None:
        details = {}
        if conversation_id:
            details["conversation_id"] = str(conversation_id)
        if user_id:
            details["user_id"] = str(user_id)
        super().__init__(ErrorCode.CHAT_ACCESS_DENIED, details=details)


class ConversationClosedError(ApplicationError):
    """Raised when trying to send a message to a closed conversation."""

    def __init__(
        self,
        conversation_id: str | UUID | None = None,
        closed_at: str | None = None,
    ) -> None:
        details = {}
        if conversation_id:
            details["conversation_id"] = str(conversation_id)
        if closed_at:
            details["closed_at"] = closed_at
        super().__init__(ErrorCode.CHAT_CONVERSATION_CLOSED, details=details)


# =============================================================================
# MESSAGE ERRORS
# =============================================================================


class MessageEmptyError(ApplicationError):
    """Raised when a message content is empty."""

    def __init__(self) -> None:
        super().__init__(ErrorCode.CHAT_MESSAGE_EMPTY, field="content")


class MessageTooLongError(ApplicationError):
    """Raised when a message exceeds the maximum length."""

    def __init__(
        self,
        length: int | None = None,
        max_length: int | None = None,
    ) -> None:
        details = {}
        if length is not None:
            details["length"] = length
        if max_length is not None:
            details["max_length"] = max_length
        super().__init__(ErrorCode.CHAT_MESSAGE_TOO_LONG, details=details, field="content")


# =============================================================================
# AGENT ERRORS
# =============================================================================


class AgentUnavailableError(ApplicationError):
    """Raised when the requested agent is unavailable."""

    def __init__(
        self,
        agent_type: str | None = None,
        agent_id: str | UUID | None = None,
        reason: str | None = None,
    ) -> None:
        details = {}
        if agent_type:
            details["agent_type"] = agent_type
        if agent_id:
            details["agent_id"] = str(agent_id)
        if reason:
            details["reason"] = reason
        super().__init__(ErrorCode.CHAT_AGENT_UNAVAILABLE, details=details)


class InvalidAgentTypeError(ApplicationError):
    """Raised when an invalid agent type is specified."""

    def __init__(
        self,
        agent_type: str | None = None,
        valid_types: list[str] | None = None,
    ) -> None:
        details = {}
        if agent_type:
            details["agent_type"] = agent_type
        if valid_types:
            details["valid_types"] = valid_types
        super().__init__(ErrorCode.CHAT_INVALID_AGENT_TYPE, details=details, field="agent_type")


class AgentProcessingError(ApplicationError):
    """Raised when an agent encounters an error processing a request."""

    def __init__(
        self,
        agent_type: str | None = None,
        error_message: str | None = None,
        request_id: str | None = None,
    ) -> None:
        details = {}
        if agent_type:
            details["agent_type"] = agent_type
        if error_message:
            details["error_message"] = error_message
        if request_id:
            details["request_id"] = request_id
        super().__init__(ErrorCode.CHAT_AGENT_ERROR, details=details)


# =============================================================================
# SERVICE ERRORS
# =============================================================================


class ChatRateLimitError(ApplicationError):
    """Raised when the user exceeds the chat rate limit."""

    def __init__(
        self,
        retry_after_seconds: int | None = None,
        limit: int | None = None,
        window_seconds: int | None = None,
    ) -> None:
        details = {}
        if retry_after_seconds is not None:
            details["retry_after_seconds"] = retry_after_seconds
        if limit is not None:
            details["limit"] = limit
        if window_seconds is not None:
            details["window_seconds"] = window_seconds
        super().__init__(ErrorCode.CHAT_RATE_LIMIT, details=details)


class ChatServiceOverloadedError(ApplicationError):
    """Raised when the chat service is experiencing high load."""

    def __init__(
        self,
        estimated_wait_seconds: int | None = None,
        queue_position: int | None = None,
    ) -> None:
        details = {}
        if estimated_wait_seconds is not None:
            details["estimated_wait_seconds"] = estimated_wait_seconds
        if queue_position is not None:
            details["queue_position"] = queue_position
        super().__init__(ErrorCode.CHAT_SERVICE_OVERLOADED, details=details)


# =============================================================================
# ADDITIONAL CHAT-SPECIFIC ERRORS (extending ErrorCode enum)
# =============================================================================


class MessageNotFoundError(ApplicationError):
    """Raised when a message is not found."""

    def __init__(
        self,
        message_id: str | UUID | None = None,
        conversation_id: str | UUID | None = None,
    ) -> None:
        details = {}
        if message_id:
            details["message_id"] = str(message_id)
        if conversation_id:
            details["conversation_id"] = str(conversation_id)
        # Using CHAT_001 with custom message since there's no specific MESSAGE_NOT_FOUND
        super().__init__(
            ErrorCode.CHAT_CONVERSATION_NOT_FOUND,
            details=details,
            override_message="Message not found",
        )


class ConversationLimitExceededError(ApplicationError):
    """Raised when user has reached maximum number of conversations."""

    def __init__(
        self,
        current_count: int | None = None,
        max_allowed: int | None = None,
    ) -> None:
        details = {}
        if current_count is not None:
            details["current_count"] = current_count
        if max_allowed is not None:
            details["max_allowed"] = max_allowed
        super().__init__(
            ErrorCode.CHAT_RATE_LIMIT,
            details=details,
            override_message="Maximum conversation limit reached",
        )


class CacheError(ApplicationError):
    """Raised when cache operations fail."""

    def __init__(
        self,
        operation: str | None = None,
        cache_key: str | None = None,
        reason: str | None = None,
    ) -> None:
        details = {}
        if operation:
            details["operation"] = operation
        if cache_key:
            details["cache_key"] = cache_key
        if reason:
            details["reason"] = reason
        super().__init__(
            ErrorCode.CHAT_SERVICE_OVERLOADED,
            details=details,
            override_message="Cache operation failed",
        )


class PerformanceBudgetViolation(ApplicationError):
    """Raised when performance budget is violated."""

    def __init__(
        self,
        metric: str | None = None,
        actual_value: float | None = None,
        budget_value: float | None = None,
    ) -> None:
        details = {}
        if metric:
            details["metric"] = metric
        if actual_value is not None:
            details["actual_value"] = actual_value
        if budget_value is not None:
            details["budget_value"] = budget_value
        super().__init__(
            ErrorCode.CHAT_RATE_LIMIT,
            details=details,
            override_message=f"Performance budget violated: {metric}",
        )


class AgentRoutingError(ApplicationError):
    """Raised when the system cannot route to an appropriate agent."""

    def __init__(
        self,
        intent: str | None = None,
        available_agents: list[str] | None = None,
    ) -> None:
        details = {}
        if intent:
            details["detected_intent"] = intent
        if available_agents:
            details["available_agents"] = available_agents
        super().__init__(
            ErrorCode.CHAT_AGENT_UNAVAILABLE,
            details=details,
            override_message="Unable to route request to an appropriate agent",
        )


class AgentTimeoutError(ApplicationError):
    """Raised when an agent takes too long to respond."""

    def __init__(
        self,
        agent_type: str | None = None,
        timeout_seconds: int | None = None,
    ) -> None:
        details = {}
        if agent_type:
            details["agent_type"] = agent_type
        if timeout_seconds is not None:
            details["timeout_seconds"] = timeout_seconds
        super().__init__(
            ErrorCode.CHAT_AGENT_ERROR,
            details=details,
            override_message="Agent response timed out",
        )


class AgentContextLimitError(ApplicationError):
    """Raised when the conversation context exceeds agent's limit."""

    def __init__(
        self,
        current_tokens: int | None = None,
        max_tokens: int | None = None,
        agent_type: str | None = None,
    ) -> None:
        details = {}
        if current_tokens is not None:
            details["current_tokens"] = current_tokens
        if max_tokens is not None:
            details["max_tokens"] = max_tokens
        if agent_type:
            details["agent_type"] = agent_type
        super().__init__(
            ErrorCode.CHAT_MESSAGE_TOO_LONG,
            details=details,
            override_message="Conversation context exceeds agent's token limit",
        )


class InvalidMessageRoleError(ApplicationError):
    """Raised when an invalid message role is provided."""

    def __init__(
        self,
        role: str | None = None,
        valid_roles: list[str] | None = None,
    ) -> None:
        details = {}
        if role:
            details["role"] = role
        if valid_roles:
            details["valid_roles"] = valid_roles
        super().__init__(
            ErrorCode.CHAT_MESSAGE_EMPTY,
            details=details,
            field="role",
            override_message="Invalid message role",
        )


class DuplicateConversationError(ApplicationError):
    """Raised when trying to create a duplicate conversation."""

    def __init__(
        self,
        title: str | None = None,
        existing_id: str | UUID | None = None,
    ) -> None:
        details = {}
        if title:
            details["title"] = title
        if existing_id:
            details["existing_conversation_id"] = str(existing_id)
        super().__init__(
            ErrorCode.CHAT_ACCESS_DENIED,
            details=details,
            override_message="A conversation with this title already exists",
        )


class ConversationUpdateError(ApplicationError):
    """Raised when a conversation update fails."""

    def __init__(
        self,
        conversation_id: str | UUID | None = None,
        reason: str | None = None,
    ) -> None:
        details = {}
        if conversation_id:
            details["conversation_id"] = str(conversation_id)
        if reason:
            details["reason"] = reason
        super().__init__(
            ErrorCode.CHAT_AGENT_ERROR,
            details=details,
            override_message="Failed to update conversation",
        )


class StreamingNotSupportedError(ApplicationError):
    """Raised when streaming is requested but not supported."""

    def __init__(
        self,
        agent_type: str | None = None,
    ) -> None:
        details = {}
        if agent_type:
            details["agent_type"] = agent_type
        super().__init__(
            ErrorCode.CHAT_AGENT_UNAVAILABLE,
            details=details,
            override_message="Streaming is not supported for this agent",
        )


class AttachmentNotAllowedError(ApplicationError):
    """Raised when attachments are not allowed."""

    def __init__(
        self,
        file_type: str | None = None,
        allowed_types: list[str] | None = None,
    ) -> None:
        details = {}
        if file_type:
            details["file_type"] = file_type
        if allowed_types:
            details["allowed_types"] = allowed_types
        super().__init__(
            ErrorCode.CHAT_MESSAGE_EMPTY,
            details=details,
            field="attachment",
            override_message="This file type is not allowed",
        )


class AttachmentTooLargeError(ApplicationError):
    """Raised when an attachment exceeds the size limit."""

    def __init__(
        self,
        size_bytes: int | None = None,
        max_size_bytes: int | None = None,
    ) -> None:
        details = {}
        if size_bytes is not None:
            details["size_bytes"] = size_bytes
        if max_size_bytes is not None:
            details["max_size_bytes"] = max_size_bytes
        super().__init__(
            ErrorCode.CHAT_MESSAGE_TOO_LONG,
            details=details,
            field="attachment",
            override_message="Attachment exceeds maximum size limit",
        )


# =============================================================================
# TEMPLATE ERRORS
# =============================================================================


class TemplateNotFoundError(ApplicationError):
    """Raised when a conversation template is not found."""

    def __init__(
        self,
        template_id: str | UUID | None = None,
        template_name: str | None = None,
    ) -> None:
        details = {}
        if template_id:
            details["template_id"] = str(template_id)
        if template_name:
            details["template_name"] = template_name
        super().__init__(
            ErrorCode.CHAT_CONVERSATION_NOT_FOUND,
            details=details,
            override_message="Conversation template not found",
        )


class TemplateValidationError(ApplicationError):
    """Raised when template validation fails."""

    def __init__(
        self,
        template_id: str | UUID | None = None,
        validation_errors: list[str] | None = None,
    ) -> None:
        details = {}
        if template_id:
            details["template_id"] = str(template_id)
        if validation_errors:
            details["validation_errors"] = validation_errors
        super().__init__(
            ErrorCode.CHAT_MESSAGE_EMPTY,
            details=details,
            override_message="Template validation failed",
        )


class TemplateExecutionError(ApplicationError):
    """Raised when template execution fails."""

    def __init__(
        self,
        template_id: str | UUID | None = None,
        step_index: int | None = None,
        error_message: str | None = None,
    ) -> None:
        details = {}
        if template_id:
            details["template_id"] = str(template_id)
        if step_index is not None:
            details["failed_step"] = step_index
        if error_message:
            details["error_message"] = error_message
        super().__init__(
            ErrorCode.CHAT_AGENT_ERROR,
            details=details,
            override_message="Template execution failed",
        )


# =============================================================================
# PREFERENCE ERRORS
# =============================================================================


class PreferencesNotFoundError(ApplicationError):
    """Raised when user preferences are not found."""

    def __init__(
        self,
        user_id: str | UUID | None = None,
    ) -> None:
        details = {}
        if user_id:
            details["user_id"] = str(user_id)
        super().__init__(
            ErrorCode.CHAT_CONVERSATION_NOT_FOUND,
            details=details,
            override_message="User chat preferences not found",
        )


class InvalidPreferenceError(ApplicationError):
    """Raised when an invalid preference value is provided."""

    def __init__(
        self,
        preference_name: str | None = None,
        invalid_value: Any | None = None,
        valid_values: list[Any] | None = None,
    ) -> None:
        details = {}
        if preference_name:
            details["preference_name"] = preference_name
        if invalid_value is not None:
            details["invalid_value"] = str(invalid_value)
        if valid_values:
            details["valid_values"] = [str(v) for v in valid_values]
        super().__init__(
            ErrorCode.CHAT_MESSAGE_EMPTY,
            details=details,
            field=preference_name,
            override_message="Invalid preference value",
        )


# =============================================================================
# INTENT DETECTION ERRORS
# =============================================================================


class IntentDetectionError(ApplicationError):
    """Raised when intent detection fails."""

    def __init__(
        self,
        message: str | None = None,
        reason: str | None = None,
    ) -> None:
        details = {}
        if message:
            details["message"] = message[:100]  # Truncate for privacy
        if reason:
            details["reason"] = reason
        super().__init__(
            ErrorCode.CHAT_AGENT_ERROR,
            details=details,
            override_message="Failed to detect user intent",
        )


# =============================================================================
# ORCHESTRATION ERRORS
# =============================================================================


class VotingFailedError(ApplicationError):
    """Raised when multi-agent voting fails."""

    def __init__(
        self,
        agent_count: int | None = None,
        reason: str | None = None,
    ) -> None:
        details = {}
        if agent_count is not None:
            details["agent_count"] = agent_count
        if reason:
            details["reason"] = reason
        super().__init__(
            ErrorCode.CHAT_AGENT_ERROR,
            details=details,
            override_message="Multi-agent voting failed",
        )


class DebateTimeoutError(ApplicationError):
    """Raised when agent debate exceeds time limit."""

    def __init__(
        self,
        max_rounds: int | None = None,
        current_round: int | None = None,
    ) -> None:
        details = {}
        if max_rounds is not None:
            details["max_rounds"] = max_rounds
        if current_round is not None:
            details["current_round"] = current_round
        super().__init__(
            ErrorCode.CHAT_AGENT_ERROR,
            details=details,
            override_message="Agent debate timed out",
        )


class NoConsensusError(ApplicationError):
    """Raised when agents cannot reach consensus."""

    def __init__(
        self,
        participating_agents: list[str] | None = None,
        reason: str | None = None,
    ) -> None:
        details = {}
        if participating_agents:
            details["participating_agents"] = participating_agents
        if reason:
            details["reason"] = reason
        super().__init__(
            ErrorCode.CHAT_AGENT_ERROR,
            details=details,
            override_message="Agents could not reach consensus",
        )


class AllAgentsUnavailableError(ApplicationError):
    """Raised when all fallback agents are unavailable."""

    def __init__(
        self,
        attempted_agents: list[str] | None = None,
        fallback_reasons: list[str] | None = None,
    ) -> None:
        details = {}
        if attempted_agents:
            details["attempted_agents"] = attempted_agents
        if fallback_reasons:
            details["fallback_reasons"] = fallback_reasons
        super().__init__(
            ErrorCode.CHAT_AGENT_UNAVAILABLE,
            details=details,
            override_message="All fallback agents unavailable",
        )


class CustomAgentValidationError(ApplicationError):
    """Raised when custom agent configuration is invalid."""

    def __init__(
        self,
        validation_errors: list[str] | None = None,
        agent_name: str | None = None,
    ) -> None:
        details = {}
        if validation_errors:
            details["validation_errors"] = validation_errors
        if agent_name:
            details["agent_name"] = agent_name
        super().__init__(
            ErrorCode.CHAT_MESSAGE_EMPTY,
            details=details,
            override_message="Custom agent configuration is invalid",
        )


class CustomAgentNotFoundError(ApplicationError):
    """Raised when custom agent is not found."""

    def __init__(
        self,
        config_id: str | None = None,
        agent_name: str | None = None,
    ) -> None:
        details = {}
        if config_id:
            details["config_id"] = config_id
        if agent_name:
            details["agent_name"] = agent_name
        super().__init__(
            ErrorCode.CHAT_CONVERSATION_NOT_FOUND,
            details=details,
            override_message="Custom agent not found",
        )


# =============================================================================
# EXPORT ERRORS
# =============================================================================


class ExportGenerationError(ApplicationError):
    """Raised when export generation fails."""

    def __init__(
        self,
        reason: str | None = None,
        export_format: str | None = None,
        conversation_id: str | UUID | None = None,
    ) -> None:
        details = {}
        if reason:
            details["reason"] = reason
        if export_format:
            details["export_format"] = export_format
        if conversation_id:
            details["conversation_id"] = str(conversation_id)
        super().__init__(
            ErrorCode.CHAT_AGENT_ERROR,
            details=details,
            override_message=f"Export generation failed: {reason}" if reason else "Export generation failed",
        )


class ComplianceViolationError(ApplicationError):
    """Raised when export violates compliance requirements."""

    def __init__(
        self,
        compliance_standard: str | None = None,
        violation_reason: str | None = None,
        export_format: str | None = None,
    ) -> None:
        details = {}
        if compliance_standard:
            details["compliance_standard"] = compliance_standard
        if violation_reason:
            details["violation_reason"] = violation_reason
        if export_format:
            details["export_format"] = export_format
        super().__init__(
            ErrorCode.CHAT_ACCESS_DENIED,
            details=details,
            override_message=f"Compliance violation: {violation_reason}" if violation_reason else "Compliance requirements violated",
        )


class ExportNotFoundError(ApplicationError):
    """Raised when an export is not found."""

    def __init__(
        self,
        export_id: str | UUID | None = None,
    ) -> None:
        details = {}
        if export_id:
            details["export_id"] = str(export_id)
        super().__init__(
            ErrorCode.CHAT_CONVERSATION_NOT_FOUND,
            details=details,
            override_message="Export not found",
        )


class ExportExpiredError(ApplicationError):
    """Raised when an export has expired."""

    def __init__(
        self,
        export_id: str | UUID | None = None,
        expired_at: str | None = None,
    ) -> None:
        details = {}
        if export_id:
            details["export_id"] = str(export_id)
        if expired_at:
            details["expired_at"] = expired_at
        super().__init__(
            ErrorCode.CHAT_ACCESS_DENIED,
            details=details,
            override_message="Export has expired",
        )
