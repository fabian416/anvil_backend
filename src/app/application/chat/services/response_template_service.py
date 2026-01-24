"""
Response Template Service for Context-Aware Agents.

This service loads and serves pre-defined response templates based on
user classification (portfolio state, activity level, user type).

Templates reduce LLM calls for common scenarios and ensure
consistent, localized messaging.

Usage:
    service = ResponseTemplateService()
    
    # Get template for empty portfolio
    result = service.get_response(
        portfolio_state="empty",
        message_key="portfolio_query",
        language="en",
    )
    
    # Check if workflow is blocked
    blocked, reason = service.check_workflow_blocked(
        portfolio_state="empty",
        workflow="swap",
        language="en",
    )
"""

import json
import logging
from pathlib import Path
from typing import Any

from app.domain.chat.entities.response_template import (
    ResponseTemplate,
    TemplateMessage,
    TemplateContext,
    TemplateResult,
)

logger = logging.getLogger(__name__)

# Default templates directory
TEMPLATES_DIR = Path(__file__).parent.parent.parent.parent / "infrastructure" / "templates" / "responses"


class ResponseTemplateService:
    """
    Service for loading and serving response templates.
    
    Templates are loaded from JSON files in the infrastructure layer
    and cached in memory for fast access.
    
    Attributes:
        _portfolio_templates: Templates by portfolio state
        _activity_templates: Templates by activity level
        _user_type_templates: Templates by user type
        _workflow_templates: Templates for workflow scenarios
    """
    
    def __init__(self, templates_dir: Path | str | None = None):
        """
        Initialize service and load templates.
        
        Args:
            templates_dir: Path to templates directory (optional)
        """
        self._templates_dir = Path(templates_dir) if templates_dir else TEMPLATES_DIR
        
        # Template caches
        self._portfolio_templates: dict[str, dict] = {}
        self._activity_templates: dict[str, dict] = {}
        self._user_type_templates: dict[str, dict] = {}
        self._workflow_templates: dict[str, dict] = {}
        
        # Load templates on initialization
        self._load_templates()
    
    def _load_templates(self) -> None:
        """Load all template files from disk."""
        try:
            # Load portfolio state templates
            portfolio_file = self._templates_dir / "portfolio_states.json"
            if portfolio_file.exists():
                with open(portfolio_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for state in ["empty", "starter", "active", "whale"]:
                        if state in data:
                            self._portfolio_templates[state] = data[state]
                logger.info(f"Loaded {len(self._portfolio_templates)} portfolio templates")
            
            # Load activity level templates
            activity_file = self._templates_dir / "activity_levels.json"
            if activity_file.exists():
                with open(activity_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for level in ["new", "very_active", "active", "weekly_active", 
                                  "monthly_active", "inactive", "reactivated"]:
                        if level in data:
                            self._activity_templates[level] = data[level]
                logger.info(f"Loaded {len(self._activity_templates)} activity templates")
            
            # Load user type templates
            user_type_file = self._templates_dir / "user_types.json"
            if user_type_file.exists():
                with open(user_type_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for user_type in ["new_user", "casual", "trader", 
                                      "yield_farmer", "power_user"]:
                        if user_type in data:
                            self._user_type_templates[user_type] = data[user_type]
                logger.info(f"Loaded {len(self._user_type_templates)} user type templates")
            
            # Load workflow templates
            workflow_file = self._templates_dir / "workflows.json"
            if workflow_file.exists():
                with open(workflow_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for workflow in ["swap", "buy", "lending", "transfer", "errors"]:
                        if workflow in data:
                            self._workflow_templates[workflow] = data[workflow]
                logger.info(f"Loaded {len(self._workflow_templates)} workflow templates")
                
        except Exception as e:
            logger.error(f"Failed to load templates: {e}")
    
    # ═══════════════════════════════════════════════════════════════
    # TEMPLATE RETRIEVAL
    # ═══════════════════════════════════════════════════════════════
    
    def get_portfolio_response(
        self,
        portfolio_state: str,
        message_key: str,
        language: str = "en",
        **variables: Any,
    ) -> TemplateResult:
        """
        Get response template for a portfolio state.
        
        Args:
            portfolio_state: User's portfolio state (empty, starter, active, whale)
            message_key: Specific message to retrieve (e.g., "portfolio_query")
            language: Target language code
            **variables: Variables to substitute in template
            
        Returns:
            TemplateResult with rendered message
        """
        template_data = self._portfolio_templates.get(portfolio_state.lower(), {})
        messages = template_data.get("messages", {})
        
        if message_key not in messages:
            return TemplateResult(
                message="",
                template_key="",
                language=language,
            )
        
        message_data = messages[message_key]
        message_text = message_data.get(language) or message_data.get("en", "")
        
        # Render variables
        rendered = self._render_template(message_text, **variables)
        
        return TemplateResult(
            message=rendered,
            template_key=f"portfolio:{portfolio_state}:{message_key}",
            language=language,
            suggested_actions=template_data.get("suggested_actions", []),
            is_blocked=False,
        )
    
    def get_activity_response(
        self,
        activity_level: str,
        message_key: str,
        language: str = "en",
        **variables: Any,
    ) -> TemplateResult:
        """
        Get response template for an activity level.
        
        Args:
            activity_level: User's activity level (new, active, inactive, etc.)
            message_key: Specific message to retrieve
            language: Target language code
            **variables: Variables to substitute
            
        Returns:
            TemplateResult with rendered message
        """
        template_data = self._activity_templates.get(activity_level.lower(), {})
        messages = template_data.get("messages", {})
        
        if message_key not in messages:
            return TemplateResult(
                message="",
                template_key="",
                language=language,
            )
        
        message_data = messages[message_key]
        message_text = message_data.get(language) or message_data.get("en", "")
        
        rendered = self._render_template(message_text, **variables)
        
        return TemplateResult(
            message=rendered,
            template_key=f"activity:{activity_level}:{message_key}",
            language=language,
            suggested_actions=template_data.get("suggested_actions", []),
        )
    
    def get_user_type_response(
        self,
        user_type: str,
        message_key: str,
        language: str = "en",
        **variables: Any,
    ) -> TemplateResult:
        """
        Get response template for a user type.
        
        Args:
            user_type: User's behavioral type (trader, yield_farmer, etc.)
            message_key: Specific message to retrieve
            language: Target language code
            **variables: Variables to substitute
            
        Returns:
            TemplateResult with rendered message
        """
        template_data = self._user_type_templates.get(user_type.lower(), {})
        messages = template_data.get("messages", {})
        
        if message_key not in messages:
            return TemplateResult(
                message="",
                template_key="",
                language=language,
            )
        
        message_data = messages[message_key]
        message_text = message_data.get(language) or message_data.get("en", "")
        
        rendered = self._render_template(message_text, **variables)
        
        return TemplateResult(
            message=rendered,
            template_key=f"user_type:{user_type}:{message_key}",
            language=language,
            suggested_actions=template_data.get("suggested_actions", []),
            response_style=template_data.get("response_style", "default"),
        )
    
    def get_workflow_response(
        self,
        workflow: str,
        message_key: str,
        language: str = "en",
        **variables: Any,
    ) -> TemplateResult:
        """
        Get response template for a workflow scenario.
        
        Args:
            workflow: Workflow type (swap, buy, lending, transfer, errors)
            message_key: Specific message (initiation, success, insufficient_balance)
            language: Target language code
            **variables: Variables to substitute
            
        Returns:
            TemplateResult with rendered message
        """
        template_data = self._workflow_templates.get(workflow.lower(), {})
        
        if message_key not in template_data:
            return TemplateResult(
                message="",
                template_key="",
                language=language,
            )
        
        message_data = template_data[message_key]
        message_text = message_data.get(language) or message_data.get("en", "")
        
        rendered = self._render_template(message_text, **variables)
        
        return TemplateResult(
            message=rendered,
            template_key=f"workflow:{workflow}:{message_key}",
            language=language,
        )
    
    # ═══════════════════════════════════════════════════════════════
    # WORKFLOW BLOCKING
    # ═══════════════════════════════════════════════════════════════
    
    def check_workflow_blocked(
        self,
        portfolio_state: str,
        workflow: str,
        language: str = "en",
        **variables: Any,
    ) -> tuple[bool, str | None]:
        """
        Check if a workflow is blocked for a portfolio state.
        
        Args:
            portfolio_state: User's portfolio state
            workflow: Workflow to check (swap, lending, transfer, etc.)
            language: Target language for blocked message
            **variables: Variables for blocked message
            
        Returns:
            Tuple of (is_blocked, blocked_message)
        """
        template_data = self._portfolio_templates.get(portfolio_state.lower(), {})
        blocked_workflows = template_data.get("blocked_workflows", [])
        
        if workflow.lower() not in [w.lower() for w in blocked_workflows]:
            return False, None
        
        # Get blocked message
        message_key = f"{workflow.lower()}_blocked"
        result = self.get_portfolio_response(
            portfolio_state=portfolio_state,
            message_key=message_key,
            language=language,
            **variables,
        )
        
        if result.message:
            return True, result.message
        
        # Generic fallback
        return True, f"You need crypto to {workflow}. Try buying some first!"
    
    def should_show_gas_warning(
        self,
        portfolio_state: str,
        amount_usd: float,
    ) -> bool:
        """
        Check if gas warning should be shown for a trade.
        
        Args:
            portfolio_state: User's portfolio state
            amount_usd: Trade amount in USD
            
        Returns:
            True if gas warning should be shown
        """
        template_data = self._portfolio_templates.get(portfolio_state.lower(), {})
        threshold = template_data.get("gas_warning_threshold", 0)
        
        return threshold > 0 and amount_usd < threshold
    
    def get_gas_warning(
        self,
        portfolio_state: str,
        language: str = "en",
        **variables: Any,
    ) -> str | None:
        """
        Get gas warning message for portfolio state.
        
        Args:
            portfolio_state: User's portfolio state
            language: Target language
            **variables: Variables to substitute
            
        Returns:
            Gas warning message or None
        """
        result = self.get_portfolio_response(
            portfolio_state=portfolio_state,
            message_key="swap_warning",
            language=language,
            **variables,
        )
        
        return result.message if result.message else None
    
    # ═══════════════════════════════════════════════════════════════
    # CONTEXTUAL TEMPLATE SELECTION
    # ═══════════════════════════════════════════════════════════════
    
    def get_contextual_response(
        self,
        context: TemplateContext,
        message_key: str,
        priority: str = "portfolio",  # "portfolio", "activity", "user_type"
    ) -> TemplateResult:
        """
        Get the most appropriate response based on full context.
        
        Args:
            context: Full user context with classification data
            message_key: Message to retrieve
            priority: Which classification to prioritize
            
        Returns:
            TemplateResult from the best matching template
        """
        render_kwargs = context.to_render_kwargs()
        
        # Try in priority order
        if priority == "portfolio":
            result = self.get_portfolio_response(
                portfolio_state=context.portfolio_state,
                message_key=message_key,
                language=context.language,
                **render_kwargs,
            )
            if result.message:
                return result
        
        if priority == "activity" or not result.message:
            result = self.get_activity_response(
                activity_level=context.activity_level,
                message_key=message_key,
                language=context.language,
                **render_kwargs,
            )
            if result.message:
                return result
        
        if priority == "user_type" or not result.message:
            result = self.get_user_type_response(
                user_type=context.user_type,
                message_key=message_key,
                language=context.language,
                **render_kwargs,
            )
        
        return result
    
    def should_use_template(
        self,
        context: TemplateContext,
        query_type: str,
    ) -> bool:
        """
        Determine if a template should be used instead of LLM.
        
        Templates are preferred for:
        - Empty portfolio queries (consistent onboarding)
        - Blocked workflow explanations
        - Simple informational responses
        
        LLM is preferred for:
        - Complex analysis requests
        - Multi-step reasoning
        - Personalized advice
        
        Args:
            context: User context
            query_type: Type of query (portfolio, swap, analysis, etc.)
            
        Returns:
            True if template should be used
        """
        # Always use templates for blocked workflows
        if context.workflow_type:
            is_blocked, _ = self.check_workflow_blocked(
                portfolio_state=context.portfolio_state,
                workflow=context.workflow_type,
                language=context.language,
            )
            if is_blocked:
                return True
        
        # Use templates for empty portfolio common queries
        if context.portfolio_state == "empty" and query_type in [
            "portfolio", "balance", "swap", "lending", "transfer"
        ]:
            return True
        
        # Use templates for simple greetings/welcome
        if query_type in ["welcome", "greeting", "help"]:
            return True
        
        # Don't use templates for complex queries
        if query_type in ["analysis", "research", "compare", "strategy"]:
            return False
        
        return False
    
    # ═══════════════════════════════════════════════════════════════
    # HELPER METHODS
    # ═══════════════════════════════════════════════════════════════
    
    def _render_template(self, template: str, **variables: Any) -> str:
        """
        Render a template string with variable substitution.
        
        Handles both {var} and ${var} syntax.
        """
        result = template
        
        for key, value in variables.items():
            # Handle ${var} style (for currency)
            result = result.replace(f"${{{key}}}", str(value))
            # Handle {var} style
            result = result.replace(f"{{{key}}}", str(value))
        
        return result
    
    def get_suggested_actions(
        self,
        portfolio_state: str,
        activity_level: str | None = None,
        user_type: str | None = None,
    ) -> list[str]:
        """
        Get combined suggested actions for user context.
        
        Args:
            portfolio_state: User's portfolio state
            activity_level: User's activity level (optional)
            user_type: User's behavioral type (optional)
            
        Returns:
            List of suggested action keywords
        """
        actions = set()
        
        # Portfolio-based suggestions (highest priority)
        portfolio_data = self._portfolio_templates.get(portfolio_state.lower(), {})
        actions.update(portfolio_data.get("suggested_actions", []))
        
        # Activity-based suggestions
        if activity_level:
            activity_data = self._activity_templates.get(activity_level.lower(), {})
            actions.update(activity_data.get("suggested_actions", []))
        
        # User type suggestions
        if user_type:
            type_data = self._user_type_templates.get(user_type.lower(), {})
            actions.update(type_data.get("suggested_actions", []))
        
        return list(actions)
    
    def get_response_style(self, user_type: str) -> str:
        """
        Get preferred response style for user type.
        
        Args:
            user_type: User's behavioral type
            
        Returns:
            Response style (educational, concise, expert, etc.)
        """
        type_data = self._user_type_templates.get(user_type.lower(), {})
        return type_data.get("response_style", "default")
    
    def should_include_explanations(self, user_type: str) -> bool:
        """
        Check if explanations should be included for user type.
        
        Args:
            user_type: User's behavioral type
            
        Returns:
            True if explanations should be included
        """
        type_data = self._user_type_templates.get(user_type.lower(), {})
        return type_data.get("include_explanations", True)
    
    def reload_templates(self) -> None:
        """Reload templates from disk (useful for hot-reloading in dev)."""
        self._portfolio_templates.clear()
        self._activity_templates.clear()
        self._user_type_templates.clear()
        self._workflow_templates.clear()
        self._load_templates()
        logger.info("Templates reloaded")
