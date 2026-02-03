"""
Standardized error codes for the Anvil DeFi platform.

This module defines all error codes used across the API, providing:
- Consistent error code format (CATEGORY_NNN)
- i18n translation keys for multilingual support
- HTTP status code mappings
- Default English messages

Usage:
    from app.domain.exceptions.error_codes import ErrorCode

    # In exception classes:
    class InvalidCredentialsError(ApplicationError):
        def __init__(self):
            super().__init__(ErrorCode.AUTH_INVALID_CREDENTIALS)

    # The error will automatically include:
    # - code: "AUTH_001"
    # - i18n_key: "errors.auth.invalid_credentials"
    # - message: "Invalid email or password"
    # - http_status: 401
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any


@dataclass(frozen=True)
class ErrorDefinition:
    """
    Definition of an error code with all associated metadata.

    Attributes:
        code: Unique error code (e.g., "AUTH_001")
        i18n_key: Translation key for frontend i18n (e.g., "errors.auth.invalid_credentials")
        default_message: Default English message
        http_status: HTTP status code to return
    """

    code: str
    i18n_key: str
    default_message: str
    http_status: int

    def to_dict(
        self, details: dict[str, Any] | None = None, field: str | None = None
    ) -> dict[str, Any]:
        """Convert to API response format."""
        result: dict[str, Any] = {
            "code": self.code,
            "message": self.default_message,
            "i18n_key": self.i18n_key,
            "http_status": self.http_status,
        }
        if details:
            result["details"] = details
        if field:
            result["field"] = field
        return result


class ErrorCode(Enum):
    """
    All error codes in the system, organized by category.

    Categories:
        AUTH (001-099): Authentication & Authorization
        USER (001-099): User Management
        CHAT (001-099): Chat & Conversations
        WALLET (001-099): Wallet Operations
        PORT (001-099): Portfolio Management
        MKT (001-099): Market Data
        SRCH (001-099): Search & Discovery
        ALRT (001-099): Alerts & Notifications
        SUB (001-099): Subscriptions & Payments
        ADM (001-099): Admin Operations
        LLM (001-099): LLM Operations
        TEL (001-099): Telemetry & Monitoring
        VAL (001-099): Field Validation
        SYS (001-099): System Errors
    """

    # =========================================================================
    # AUTHENTICATION & AUTHORIZATION (AUTH_001 - AUTH_099)
    # =========================================================================

    AUTH_INVALID_CREDENTIALS = ErrorDefinition(
        code="AUTH_001",
        i18n_key="errors.auth.invalid_credentials",
        default_message="Invalid email or password",
        http_status=401,
    )

    AUTH_TOKEN_EXPIRED = ErrorDefinition(
        code="AUTH_002",
        i18n_key="errors.auth.token_expired",
        default_message="Session has expired, please login again",
        http_status=401,
    )

    AUTH_TOKEN_INVALID = ErrorDefinition(
        code="AUTH_003",
        i18n_key="errors.auth.token_invalid",
        default_message="Invalid authentication token",
        http_status=401,
    )

    AUTH_TOKEN_MISSING = ErrorDefinition(
        code="AUTH_004",
        i18n_key="errors.auth.token_missing",
        default_message="Authentication required",
        http_status=401,
    )

    AUTH_INSUFFICIENT_PERMISSIONS = ErrorDefinition(
        code="AUTH_005",
        i18n_key="errors.auth.insufficient_permissions",
        default_message="You don't have permission to perform this action",
        http_status=403,
    )

    AUTH_ACCOUNT_DISABLED = ErrorDefinition(
        code="AUTH_006",
        i18n_key="errors.auth.account_disabled",
        default_message="Your account has been disabled",
        http_status=403,
    )

    AUTH_ACCOUNT_NOT_VERIFIED = ErrorDefinition(
        code="AUTH_007",
        i18n_key="errors.auth.account_not_verified",
        default_message="Please verify your email address",
        http_status=403,
    )

    AUTH_ADMIN_REQUIRED = ErrorDefinition(
        code="AUTH_008",
        i18n_key="errors.auth.admin_required",
        default_message="Administrator access required",
        http_status=403,
    )

    AUTH_TOO_MANY_ATTEMPTS = ErrorDefinition(
        code="AUTH_009",
        i18n_key="errors.auth.too_many_attempts",
        default_message="Too many login attempts, please try again later",
        http_status=429,
    )

    AUTH_REFRESH_TOKEN_INVALID = ErrorDefinition(
        code="AUTH_010",
        i18n_key="errors.auth.refresh_token_invalid",
        default_message="Session refresh failed, please login again",
        http_status=401,
    )

    AUTH_ALREADY_AUTHENTICATED = ErrorDefinition(
        code="AUTH_011",
        i18n_key="errors.auth.already_authenticated",
        default_message="You are already logged in",
        http_status=403,
    )

    AUTH_ROLE_CHANGE_NOT_ALLOWED = ErrorDefinition(
        code="AUTH_012",
        i18n_key="errors.auth.role_change_not_allowed",
        default_message="This role change is not allowed",
        http_status=403,
    )

    AUTH_EMAIL_ALREADY_VERIFIED = ErrorDefinition(
        code="AUTH_013",
        i18n_key="errors.auth.email_already_verified",
        default_message="Email is already verified",
        http_status=409,
    )

    AUTH_SESSION_INVALID = ErrorDefinition(
        code="AUTH_014",
        i18n_key="errors.auth.session_invalid",
        default_message="Session is invalid or has been terminated",
        http_status=401,
    )

    # =========================================================================
    # USER MANAGEMENT (USER_001 - USER_099)
    # =========================================================================

    USER_NOT_FOUND = ErrorDefinition(
        code="USER_001",
        i18n_key="errors.user.not_found",
        default_message="User not found",
        http_status=404,
    )

    USER_EMAIL_EXISTS = ErrorDefinition(
        code="USER_002",
        i18n_key="errors.user.email_exists",
        default_message="An account with this email already exists",
        http_status=409,
    )

    USER_INVALID_EMAIL = ErrorDefinition(
        code="USER_003",
        i18n_key="errors.user.invalid_email",
        default_message="Please enter a valid email address",
        http_status=400,
    )

    USER_PASSWORD_TOO_WEAK = ErrorDefinition(
        code="USER_004",
        i18n_key="errors.user.password_too_weak",
        default_message="Password must be at least 8 characters with uppercase, lowercase, and number",
        http_status=400,
    )

    USER_PASSWORD_MISMATCH = ErrorDefinition(
        code="USER_005",
        i18n_key="errors.user.password_mismatch",
        default_message="Passwords do not match",
        http_status=400,
    )

    USER_INVALID_CURRENT_PASSWORD = ErrorDefinition(
        code="USER_006",
        i18n_key="errors.user.invalid_current_password",
        default_message="Current password is incorrect",
        http_status=400,
    )

    USER_PASSWORD_SAME_AS_CURRENT = ErrorDefinition(
        code="USER_014",
        i18n_key="errors.user.password_same_as_current",
        default_message="New password must be different from current password",
        http_status=400,
    )

    USER_NAME_REQUIRED = ErrorDefinition(
        code="USER_007",
        i18n_key="errors.user.name_required",
        default_message="First name and last name are required",
        http_status=400,
    )

    USER_INVALID_PHONE = ErrorDefinition(
        code="USER_008",
        i18n_key="errors.user.invalid_phone",
        default_message="Please enter a valid phone number",
        http_status=400,
    )

    USER_PROFILE_INCOMPLETE = ErrorDefinition(
        code="USER_009",
        i18n_key="errors.user.profile_incomplete",
        default_message="Please complete your profile",
        http_status=422,
    )

    USER_VERIFICATION_RATE_LIMIT = ErrorDefinition(
        code="USER_010",
        i18n_key="errors.user.verification_rate_limit",
        default_message="Please wait before requesting another verification email",
        http_status=429,
    )

    USER_ACTIVATION_NOT_PERMITTED = ErrorDefinition(
        code="USER_011",
        i18n_key="errors.user.activation_not_permitted",
        default_message="Activation change is not permitted for this user",
        http_status=403,
    )

    USER_ROLE_ASSIGNMENT_NOT_PERMITTED = ErrorDefinition(
        code="USER_012",
        i18n_key="errors.user.role_assignment_not_permitted",
        default_message="This role assignment is not permitted",
        http_status=403,
    )

    USER_ROLE_CHANGE_NOT_PERMITTED = ErrorDefinition(
        code="USER_013",
        i18n_key="errors.user.role_change_not_permitted",
        default_message="Role change is not permitted for this user",
        http_status=403,
    )

    # =========================================================================
    # CHAT & CONVERSATIONS (CHAT_001 - CHAT_099)
    # =========================================================================

    CHAT_CONVERSATION_NOT_FOUND = ErrorDefinition(
        code="CHAT_001",
        i18n_key="errors.chat.conversation_not_found",
        default_message="Conversation not found",
        http_status=404,
    )

    CHAT_ACCESS_DENIED = ErrorDefinition(
        code="CHAT_002",
        i18n_key="errors.chat.conversation_access_denied",
        default_message="You don't have access to this conversation",
        http_status=403,
    )

    CHAT_MESSAGE_EMPTY = ErrorDefinition(
        code="CHAT_003",
        i18n_key="errors.chat.message_empty",
        default_message="Message cannot be empty",
        http_status=400,
    )

    CHAT_MESSAGE_TOO_LONG = ErrorDefinition(
        code="CHAT_004",
        i18n_key="errors.chat.message_too_long",
        default_message="Message exceeds maximum length",
        http_status=400,
    )

    CHAT_AGENT_UNAVAILABLE = ErrorDefinition(
        code="CHAT_005",
        i18n_key="errors.chat.agent_unavailable",
        default_message="The requested agent is currently unavailable",
        http_status=422,
    )

    CHAT_CONVERSATION_CLOSED = ErrorDefinition(
        code="CHAT_006",
        i18n_key="errors.chat.conversation_closed",
        default_message="This conversation has been closed",
        http_status=422,
    )

    CHAT_RATE_LIMIT = ErrorDefinition(
        code="CHAT_007",
        i18n_key="errors.chat.rate_limit",
        default_message="You're sending messages too quickly",
        http_status=429,
    )

    CHAT_AGENT_ERROR = ErrorDefinition(
        code="CHAT_008",
        i18n_key="errors.chat.agent_error",
        default_message="Agent encountered an error processing your request",
        http_status=500,
    )

    CHAT_SERVICE_OVERLOADED = ErrorDefinition(
        code="CHAT_009",
        i18n_key="errors.chat.service_overloaded",
        default_message="Chat service is experiencing high load",
        http_status=503,
    )

    CHAT_INVALID_AGENT_TYPE = ErrorDefinition(
        code="CHAT_010",
        i18n_key="errors.chat.invalid_agent_type",
        default_message="Invalid agent type specified",
        http_status=400,
    )

    # =========================================================================
    # WALLET OPERATIONS (WALLET_001 - WALLET_099)
    # =========================================================================

    WALLET_NOT_FOUND = ErrorDefinition(
        code="WALLET_001",
        i18n_key="errors.wallet.not_found",
        default_message="Wallet not found",
        http_status=404,
    )

    WALLET_NOT_CONNECTED = ErrorDefinition(
        code="WALLET_002",
        i18n_key="errors.wallet.not_connected",
        default_message="Please connect your wallet",
        http_status=403,
    )

    WALLET_INVALID_ADDRESS = ErrorDefinition(
        code="WALLET_003",
        i18n_key="errors.wallet.invalid_address",
        default_message="Invalid wallet address",
        http_status=400,
    )

    WALLET_INSUFFICIENT_BALANCE = ErrorDefinition(
        code="WALLET_004",
        i18n_key="errors.wallet.insufficient_balance",
        default_message="Insufficient balance",
        http_status=422,
    )

    WALLET_TRANSACTION_FAILED = ErrorDefinition(
        code="WALLET_005",
        i18n_key="errors.wallet.transaction_failed",
        default_message="Transaction failed",
        http_status=422,
    )

    WALLET_INVALID_CHAIN = ErrorDefinition(
        code="WALLET_006",
        i18n_key="errors.wallet.invalid_chain",
        default_message="Unsupported blockchain network",
        http_status=400,
    )

    WALLET_INVALID_AMOUNT = ErrorDefinition(
        code="WALLET_007",
        i18n_key="errors.wallet.invalid_amount",
        default_message="Invalid amount specified",
        http_status=400,
    )

    WALLET_RATE_LIMIT = ErrorDefinition(
        code="WALLET_008",
        i18n_key="errors.wallet.rate_limit",
        default_message="Too many wallet operations",
        http_status=429,
    )

    WALLET_NETWORK_CONGESTED = ErrorDefinition(
        code="WALLET_009",
        i18n_key="errors.wallet.network_congested",
        default_message="Network is congested, please try again",
        http_status=503,
    )

    WALLET_SIGNATURE_INVALID = ErrorDefinition(
        code="WALLET_010",
        i18n_key="errors.wallet.signature_invalid",
        default_message="Invalid signature",
        http_status=400,
    )

    # =========================================================================
    # PORTFOLIO MANAGEMENT (PORT_001 - PORT_099)
    # =========================================================================

    PORT_NOT_FOUND = ErrorDefinition(
        code="PORT_001",
        i18n_key="errors.portfolio.not_found",
        default_message="Portfolio not found",
        http_status=404,
    )

    PORT_ACCESS_DENIED = ErrorDefinition(
        code="PORT_002",
        i18n_key="errors.portfolio.access_denied",
        default_message="You don't have access to this portfolio",
        http_status=403,
    )

    PORT_INVALID_ALLOCATION = ErrorDefinition(
        code="PORT_003",
        i18n_key="errors.portfolio.invalid_allocation",
        default_message="Allocation percentages must sum to 100%",
        http_status=400,
    )

    PORT_RISK_LIMIT_EXCEEDED = ErrorDefinition(
        code="PORT_004",
        i18n_key="errors.portfolio.risk_limit_exceeded",
        default_message="This allocation exceeds your risk tolerance",
        http_status=422,
    )

    PORT_INVALID_TIMEFRAME = ErrorDefinition(
        code="PORT_005",
        i18n_key="errors.portfolio.invalid_timeframe",
        default_message="Invalid time frame specified",
        http_status=400,
    )

    PORT_REBALANCE_FAILED = ErrorDefinition(
        code="PORT_006",
        i18n_key="errors.portfolio.rebalance_failed",
        default_message="Portfolio rebalancing failed",
        http_status=422,
    )

    PORT_INVALID_POSITION = ErrorDefinition(
        code="PORT_007",
        i18n_key="errors.portfolio.invalid_position",
        default_message="Invalid position specified",
        http_status=400,
    )

    # =========================================================================
    # MARKET DATA (MKT_001 - MKT_099)
    # =========================================================================

    MKT_PROTOCOL_NOT_FOUND = ErrorDefinition(
        code="MKT_001",
        i18n_key="errors.market.protocol_not_found",
        default_message="Protocol not found",
        http_status=404,
    )

    MKT_TOKEN_NOT_FOUND = ErrorDefinition(
        code="MKT_002",
        i18n_key="errors.market.token_not_found",
        default_message="Token not found",
        http_status=404,
    )

    MKT_DATA_UNAVAILABLE = ErrorDefinition(
        code="MKT_003",
        i18n_key="errors.market.data_unavailable",
        default_message="Market data temporarily unavailable",
        http_status=503,
    )

    MKT_INVALID_SYMBOL = ErrorDefinition(
        code="MKT_004",
        i18n_key="errors.market.invalid_symbol",
        default_message="Invalid token symbol",
        http_status=400,
    )

    MKT_INVALID_CHAIN = ErrorDefinition(
        code="MKT_005",
        i18n_key="errors.market.invalid_chain",
        default_message="Unsupported blockchain",
        http_status=400,
    )

    MKT_RATE_LIMIT = ErrorDefinition(
        code="MKT_006",
        i18n_key="errors.market.rate_limit",
        default_message="Market data rate limit exceeded",
        http_status=429,
    )

    # =========================================================================
    # SEARCH & DISCOVERY (SRCH_001 - SRCH_099)
    # =========================================================================

    SRCH_QUERY_EMPTY = ErrorDefinition(
        code="SRCH_001",
        i18n_key="errors.search.query_empty",
        default_message="Search query cannot be empty",
        http_status=400,
    )

    SRCH_QUERY_TOO_SHORT = ErrorDefinition(
        code="SRCH_002",
        i18n_key="errors.search.query_too_short",
        default_message="Search query must be at least 2 characters",
        http_status=400,
    )

    SRCH_QUERY_TOO_LONG = ErrorDefinition(
        code="SRCH_003",
        i18n_key="errors.search.query_too_long",
        default_message="Search query exceeds maximum length",
        http_status=400,
    )

    SRCH_INVALID_FILTERS = ErrorDefinition(
        code="SRCH_004",
        i18n_key="errors.search.invalid_filters",
        default_message="Invalid search filters",
        http_status=400,
    )

    SRCH_SERVICE_UNAVAILABLE = ErrorDefinition(
        code="SRCH_005",
        i18n_key="errors.search.service_unavailable",
        default_message="Search service temporarily unavailable",
        http_status=503,
    )

    SRCH_NO_RESULTS = ErrorDefinition(
        code="SRCH_006",
        i18n_key="errors.search.no_results",
        default_message="No results found",
        http_status=404,
    )

    # =========================================================================
    # ALERTS & NOTIFICATIONS (ALRT_001 - ALRT_099)
    # =========================================================================

    ALRT_NOT_FOUND = ErrorDefinition(
        code="ALRT_001",
        i18n_key="errors.alert.not_found",
        default_message="Alert not found",
        http_status=404,
    )

    ALRT_ALREADY_EXISTS = ErrorDefinition(
        code="ALRT_002",
        i18n_key="errors.alert.already_exists",
        default_message="Alert already exists for this condition",
        http_status=409,
    )

    ALRT_INVALID_THRESHOLD = ErrorDefinition(
        code="ALRT_003",
        i18n_key="errors.alert.invalid_threshold",
        default_message="Invalid threshold value",
        http_status=400,
    )

    ALRT_INVALID_CONDITION = ErrorDefinition(
        code="ALRT_004",
        i18n_key="errors.alert.invalid_condition",
        default_message="Invalid alert condition",
        http_status=400,
    )

    ALRT_LIMIT_EXCEEDED = ErrorDefinition(
        code="ALRT_005",
        i18n_key="errors.alert.limit_exceeded",
        default_message="Maximum alert limit reached",
        http_status=422,
    )

    # =========================================================================
    # SUBSCRIPTIONS & PAYMENTS (SUB_001 - SUB_099)
    # =========================================================================

    SUB_NOT_FOUND = ErrorDefinition(
        code="SUB_001",
        i18n_key="errors.subscription.not_found",
        default_message="Subscription not found",
        http_status=404,
    )

    SUB_ALREADY_ACTIVE = ErrorDefinition(
        code="SUB_002",
        i18n_key="errors.subscription.already_active",
        default_message="You already have an active subscription",
        http_status=409,
    )

    SUB_PAYMENT_FAILED = ErrorDefinition(
        code="SUB_003",
        i18n_key="errors.subscription.payment_failed",
        default_message="Payment processing failed",
        http_status=422,
    )

    SUB_INVALID_PLAN = ErrorDefinition(
        code="SUB_004",
        i18n_key="errors.subscription.invalid_plan",
        default_message="Invalid subscription plan",
        http_status=400,
    )

    SUB_CANCEL_FAILED = ErrorDefinition(
        code="SUB_005",
        i18n_key="errors.subscription.cancel_failed",
        default_message="Unable to cancel subscription",
        http_status=422,
    )

    SUB_FEATURE_UNAVAILABLE = ErrorDefinition(
        code="SUB_006",
        i18n_key="errors.subscription.feature_unavailable",
        default_message="This feature requires a premium subscription",
        http_status=403,
    )

    SUB_INVALID_CARD = ErrorDefinition(
        code="SUB_007",
        i18n_key="errors.subscription.invalid_card",
        default_message="Invalid payment card",
        http_status=400,
    )

    # =========================================================================
    # ADMIN OPERATIONS (ADM_001 - ADM_099)
    # =========================================================================

    ADM_ACCESS_DENIED = ErrorDefinition(
        code="ADM_001",
        i18n_key="errors.admin.access_denied",
        default_message="Administrator access required",
        http_status=403,
    )

    ADM_RESOURCE_NOT_FOUND = ErrorDefinition(
        code="ADM_002",
        i18n_key="errors.admin.resource_not_found",
        default_message="Resource not found",
        http_status=404,
    )

    ADM_RESOURCE_CONFLICT = ErrorDefinition(
        code="ADM_003",
        i18n_key="errors.admin.resource_conflict",
        default_message="Resource already exists",
        http_status=409,
    )

    ADM_OPERATION_FAILED = ErrorDefinition(
        code="ADM_004",
        i18n_key="errors.admin.operation_failed",
        default_message="Admin operation failed",
        http_status=422,
    )

    ADM_INVALID_CONFIG = ErrorDefinition(
        code="ADM_005",
        i18n_key="errors.admin.invalid_config",
        default_message="Invalid configuration",
        http_status=400,
    )

    ADM_SERVICE_UNAVAILABLE = ErrorDefinition(
        code="ADM_006",
        i18n_key="errors.admin.service_unavailable",
        default_message="Admin service temporarily unavailable",
        http_status=503,
    )

    # =========================================================================
    # LLM OPERATIONS (LLM_001 - LLM_099)
    # =========================================================================

    LLM_PROVIDER_UNAVAILABLE = ErrorDefinition(
        code="LLM_001",
        i18n_key="errors.llm.provider_unavailable",
        default_message="AI service temporarily unavailable",
        http_status=503,
    )

    LLM_RATE_LIMIT = ErrorDefinition(
        code="LLM_002",
        i18n_key="errors.llm.rate_limit",
        default_message="AI request rate limit exceeded",
        http_status=429,
    )

    LLM_BUDGET_EXCEEDED = ErrorDefinition(
        code="LLM_003",
        i18n_key="errors.llm.budget_exceeded",
        default_message="AI budget limit reached",
        http_status=422,
    )

    LLM_GENERATION_FAILED = ErrorDefinition(
        code="LLM_004",
        i18n_key="errors.llm.generation_failed",
        default_message="AI response generation failed",
        http_status=500,
    )

    LLM_INVALID_PROMPT = ErrorDefinition(
        code="LLM_005",
        i18n_key="errors.llm.invalid_prompt",
        default_message="Invalid prompt",
        http_status=400,
    )

    LLM_ALL_PROVIDERS_FAILED = ErrorDefinition(
        code="LLM_006",
        i18n_key="errors.llm.all_providers_failed",
        default_message="All AI providers are currently unavailable",
        http_status=503,
    )

    # =========================================================================
    # TELEMETRY & MONITORING (TEL_001 - TEL_099)
    # =========================================================================

    TEL_ACCESS_DENIED = ErrorDefinition(
        code="TEL_001",
        i18n_key="errors.telemetry.access_denied",
        default_message="Telemetry access requires admin privileges",
        http_status=403,
    )

    TEL_INVALID_TIMERANGE = ErrorDefinition(
        code="TEL_002",
        i18n_key="errors.telemetry.invalid_timerange",
        default_message="Invalid time range specified",
        http_status=400,
    )

    TEL_SERVICE_UNAVAILABLE = ErrorDefinition(
        code="TEL_003",
        i18n_key="errors.telemetry.service_unavailable",
        default_message="Telemetry service unavailable",
        http_status=503,
    )

    TEL_INVALID_METRIC = ErrorDefinition(
        code="TEL_004",
        i18n_key="errors.telemetry.invalid_metric",
        default_message="Invalid metric name",
        http_status=400,
    )

    # =========================================================================
    # FIELD VALIDATION (VAL_001 - VAL_099)
    # =========================================================================

    VAL_REQUIRED = ErrorDefinition(
        code="VAL_001",
        i18n_key="errors.validation.required",
        default_message="This field is required",
        http_status=400,
    )

    VAL_MIN_LENGTH = ErrorDefinition(
        code="VAL_002",
        i18n_key="errors.validation.min_length",
        default_message="Must be at least {min} characters",
        http_status=400,
    )

    VAL_MAX_LENGTH = ErrorDefinition(
        code="VAL_003",
        i18n_key="errors.validation.max_length",
        default_message="Must be no more than {max} characters",
        http_status=400,
    )

    VAL_INVALID_FORMAT = ErrorDefinition(
        code="VAL_004",
        i18n_key="errors.validation.invalid_format",
        default_message="Invalid format",
        http_status=400,
    )

    VAL_INVALID_EMAIL = ErrorDefinition(
        code="VAL_005",
        i18n_key="errors.validation.invalid_email",
        default_message="Invalid email format",
        http_status=400,
    )

    VAL_INVALID_UUID = ErrorDefinition(
        code="VAL_006",
        i18n_key="errors.validation.invalid_uuid",
        default_message="Invalid ID format",
        http_status=400,
    )

    VAL_INVALID_DATE = ErrorDefinition(
        code="VAL_007",
        i18n_key="errors.validation.invalid_date",
        default_message="Invalid date format",
        http_status=400,
    )

    VAL_OUT_OF_RANGE = ErrorDefinition(
        code="VAL_008",
        i18n_key="errors.validation.out_of_range",
        default_message="Value must be between {min} and {max}",
        http_status=400,
    )

    VAL_INVALID_ENUM = ErrorDefinition(
        code="VAL_009",
        i18n_key="errors.validation.invalid_enum",
        default_message="Invalid option selected",
        http_status=400,
    )

    VAL_ARRAY_TOO_LONG = ErrorDefinition(
        code="VAL_010",
        i18n_key="errors.validation.array_too_long",
        default_message="Too many items (maximum {max})",
        http_status=400,
    )

    # =========================================================================
    # SYSTEM ERRORS (SYS_001 - SYS_099)
    # =========================================================================

    SYS_INTERNAL_ERROR = ErrorDefinition(
        code="SYS_001",
        i18n_key="errors.system.internal",
        default_message="An unexpected error occurred",
        http_status=500,
    )

    SYS_EXTERNAL_SERVICE = ErrorDefinition(
        code="SYS_002",
        i18n_key="errors.system.external_service",
        default_message="External service error",
        http_status=502,
    )

    SYS_MAINTENANCE = ErrorDefinition(
        code="SYS_003",
        i18n_key="errors.system.maintenance",
        default_message="System is under maintenance",
        http_status=503,
    )

    SYS_OVERLOADED = ErrorDefinition(
        code="SYS_004",
        i18n_key="errors.system.overloaded",
        default_message="System is currently overloaded",
        http_status=503,
    )

    SYS_TIMEOUT = ErrorDefinition(
        code="SYS_005",
        i18n_key="errors.system.timeout",
        default_message="Request timed out",
        http_status=504,
    )

    SYS_DATABASE_ERROR = ErrorDefinition(
        code="SYS_006",
        i18n_key="errors.system.database",
        default_message="Database error",
        http_status=500,
    )

    SYS_CACHE_ERROR = ErrorDefinition(
        code="SYS_007",
        i18n_key="errors.system.cache",
        default_message="Cache error",
        http_status=500,
    )

    # =========================================================================
    # LOCATION ERRORS (LOC_001 - LOC_099)
    # =========================================================================

    LOC_COUNTRY_NOT_FOUND = ErrorDefinition(
        code="LOC_001",
        i18n_key="errors.location.country_not_found",
        default_message="Country not found",
        http_status=404,
    )

    LOC_CITY_NOT_FOUND = ErrorDefinition(
        code="LOC_002",
        i18n_key="errors.location.city_not_found",
        default_message="City not found",
        http_status=404,
    )


# Helper function to get error code by string
def get_error_code(code: str) -> ErrorCode | None:
    """Get ErrorCode enum by code string (e.g., 'AUTH_001')."""
    for error in ErrorCode:
        if error.value.code == code:
            return error
    return None
