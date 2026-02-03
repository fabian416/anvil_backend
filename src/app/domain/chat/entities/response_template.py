"""
Response Template entity for context-aware agent responses.

This entity represents a pre-defined response template that can be
rendered with user context variables for personalized messaging.
"""

from dataclasses import dataclass, field
from typing import Any
import re


@dataclass(frozen=True)
class TemplateMessage:
    """
    A localized message template with variable placeholders.

    Placeholders use the format: {variable_name}
    Examples: ${total_usd}, {token}, {rate}
    """

    en: str
    es: str = ""
    pt: str = ""
    zh: str = ""

    def get(self, language: str = "en") -> str:
        """Get message for specified language, falling back to English."""
        lang_map = {
            "en": self.en,
            "es": self.es or self.en,
            "pt": self.pt or self.en,
            "zh": self.zh or self.en,
        }
        return lang_map.get(language, self.en)

    def render(self, language: str = "en", **variables: Any) -> str:
        """
        Render template with variables substituted.

        Args:
            language: Target language code
            **variables: Key-value pairs to substitute

        Returns:
            Rendered message string
        """
        template = self.get(language)

        # Replace {variable} and ${variable} placeholders
        for key, value in variables.items():
            # Handle ${var} style (for currency)
            template = template.replace(f"${{{key}}}", str(value))
            # Handle {var} style
            template = template.replace(f"{{{key}}}", str(value))

        return template


@dataclass
class ResponseTemplate:
    """
    A complete response template with metadata.

    Templates are organized by:
    - state_type: "portfolio", "activity", "user_type", "workflow"
    - state_value: The specific state (e.g., "empty", "trader", "swap")
    - message_key: The specific message within that state (e.g., "portfolio_query")
    """

    state_type: str  # "portfolio", "activity", "user_type", "workflow"
    state_value: str  # e.g., "empty", "active", "trader", "swap"
    message_key: str  # e.g., "portfolio_query", "greeting", "initiation"
    message: TemplateMessage

    # Optional metadata
    suggested_actions: list[str] = field(default_factory=list)
    blocked_workflows: list[str] = field(default_factory=list)
    show_tutorials: bool = False
    response_style: str = "default"  # "educational", "concise", "expert"
    include_explanations: bool = True

    def render(
        self,
        language: str = "en",
        **context: Any,
    ) -> str:
        """
        Render the template with context variables.

        Args:
            language: Target language code
            **context: Variables to substitute in template

        Returns:
            Rendered message string
        """
        return self.message.render(language, **context)

    def is_workflow_blocked(self, workflow: str) -> bool:
        """Check if a workflow is blocked for this state."""
        return workflow.lower() in [w.lower() for w in self.blocked_workflows]

    @property
    def key(self) -> str:
        """Unique key for this template."""
        return f"{self.state_type}:{self.state_value}:{self.message_key}"


@dataclass
class TemplateContext:
    """
    Context for template rendering combining user classification data.

    This is passed to the template service to select and render
    the appropriate template for a user.
    """

    # User classification
    portfolio_state: str = "empty"
    activity_level: str = "new"
    user_type: str = "new_user"

    # User data
    total_balance_usd: float = 0.0
    wallet_address: str | None = None
    language: str = "en"

    # Workflow context (if applicable)
    workflow_type: str | None = None  # "swap", "buy", "lending", etc.
    workflow_step: str | None = None  # "initiation", "confirmation", "success"

    # Dynamic variables for rendering
    variables: dict[str, Any] = field(default_factory=dict)

    def to_render_kwargs(self) -> dict[str, Any]:
        """Convert context to kwargs for template rendering."""
        kwargs = {
            "total_usd": f"{self.total_balance_usd:,.2f}",
            "portfolio_state": self.portfolio_state,
            "activity_level": self.activity_level,
            "user_type": self.user_type,
        }
        kwargs.update(self.variables)
        return kwargs


@dataclass
class TemplateResult:
    """
    Result of template lookup and rendering.

    Contains the rendered message and metadata about
    what template was used.
    """

    message: str
    template_key: str
    language: str
    suggested_actions: list[str] = field(default_factory=list)
    is_blocked: bool = False
    blocked_reason: str | None = None
    response_style: str = "default"

    @property
    def has_template(self) -> bool:
        """Check if a template was found."""
        return bool(self.template_key)
