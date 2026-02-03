"""Assignment rule evaluation service."""

from typing import Dict, List, Optional, Any
from uuid import UUID

from app.domain.entities.assignment_rule import AssignmentRule


class RuleEvaluator:
    """
    Service for evaluating auto-assignment rules.

    Evaluates conditions and determines which projects to assign users to.
    """

    def __init__(self):
        """Initialize rule evaluator."""
        pass

    async def evaluate_rule(
        self,
        rule: AssignmentRule,
        user_context: Dict[str, Any],
    ) -> bool:
        """
        Evaluate if a rule matches for a user.

        Args:
            rule: Assignment rule to evaluate
            user_context: User context data

        Returns:
            True if rule matches
        """
        if not rule.is_active:
            return False

        # Route to appropriate evaluator based on condition type
        if rule.condition_type == "PORTFOLIO":
            return self._evaluate_portfolio(rule.condition_params, user_context)
        elif rule.condition_type == "ACTIVITY":
            return self._evaluate_activity(rule.condition_params, user_context)
        elif rule.condition_type == "PREFERENCE":
            return self._evaluate_preference(rule.condition_params, user_context)
        elif rule.condition_type == "ONBOARDING":
            return self._evaluate_onboarding(rule.condition_params, user_context)
        else:
            return False

    def _evaluate_portfolio(
        self,
        params: Dict[str, Any],
        context: Dict[str, Any],
    ) -> bool:
        """
        Evaluate portfolio-based condition.

        Example params:
        {
            "min_balance_usd": 1000,
            "required_tokens": ["ETH", "USDC"],
            "min_token_count": 2
        }
        """
        portfolio = context.get("portfolio", {})

        # Check minimum balance
        if "min_balance_usd" in params:
            total_balance = portfolio.get("total_balance_usd", 0)
            if total_balance < params["min_balance_usd"]:
                return False

        # Check required tokens
        if "required_tokens" in params:
            holdings = portfolio.get("holdings", [])
            held_tokens = {h.get("token") for h in holdings}
            required = set(params["required_tokens"])
            if not required.issubset(held_tokens):
                return False

        # Check minimum token count
        if "min_token_count" in params:
            holdings = portfolio.get("holdings", [])
            if len(holdings) < params["min_token_count"]:
                return False

        # Check specific token balance
        if "token_balances" in params:
            holdings = portfolio.get("holdings", [])
            holdings_map = {h.get("token"): h.get("balance", 0) for h in holdings}

            for token, min_balance in params["token_balances"].items():
                if holdings_map.get(token, 0) < min_balance:
                    return False

        return True

    def _evaluate_activity(
        self,
        params: Dict[str, Any],
        context: Dict[str, Any],
    ) -> bool:
        """
        Evaluate activity-based condition.

        Example params:
        {
            "min_transactions": 5,
            "required_protocols": ["uniswap", "aave"],
            "timeframe_days": 30
        }
        """
        activity = context.get("activity", {})

        # Check minimum transactions
        if "min_transactions" in params:
            tx_count = activity.get("transaction_count", 0)
            if tx_count < params["min_transactions"]:
                return False

        # Check required protocols
        if "required_protocols" in params:
            used_protocols = set(activity.get("protocols_used", []))
            required = set(params["required_protocols"])
            if not required.issubset(used_protocols):
                return False

        # Check transaction volume
        if "min_volume_usd" in params:
            volume = activity.get("total_volume_usd", 0)
            if volume < params["min_volume_usd"]:
                return False

        return True

    def _evaluate_preference(
        self,
        params: Dict[str, Any],
        context: Dict[str, Any],
    ) -> bool:
        """
        Evaluate preference-based condition.

        Example params:
        {
            "interests": ["yield-farming", "lending"],
            "risk_tolerance": "medium"
        }
        """
        preferences = context.get("preferences", {})

        # Check interests
        if "interests" in params:
            user_interests = set(preferences.get("interests", []))
            required_interests = set(params["interests"])

            # Match if any interest overlaps
            if not user_interests.intersection(required_interests):
                return False

        # Check risk tolerance
        if "risk_tolerance" in params:
            user_risk = preferences.get("risk_tolerance", "medium")
            if user_risk != params["risk_tolerance"]:
                return False

        # Check experience level
        if "experience_level" in params:
            user_exp = preferences.get("experience_level", "beginner")
            if user_exp != params["experience_level"]:
                return False

        return True

    def _evaluate_onboarding(
        self,
        params: Dict[str, Any],
        context: Dict[str, Any],
    ) -> bool:
        """
        Evaluate onboarding-based condition.

        Example params:
        {
            "is_new_user": true,
            "max_days_since_signup": 7
        }
        """
        user = context.get("user", {})

        # Check if new user
        if "is_new_user" in params:
            is_new = user.get("is_new_user", False)
            if is_new != params["is_new_user"]:
                return False

        # Check days since signup
        if "max_days_since_signup" in params:
            days_since_signup = user.get("days_since_signup", 999)
            if days_since_signup > params["max_days_since_signup"]:
                return False

        # Check if completed onboarding
        if "completed_onboarding" in params:
            completed = user.get("completed_onboarding", False)
            if completed != params["completed_onboarding"]:
                return False

        return True

    async def find_matching_projects(
        self,
        rules: List[AssignmentRule],
        user_context: Dict[str, Any],
    ) -> List[UUID]:
        """
        Find all projects that match rules for a user.

        Args:
            rules: List of assignment rules (should be sorted by priority)
            user_context: User context data

        Returns:
            List of matching project IDs (ordered by rule priority)
        """
        matching_projects = []

        for rule in rules:
            if await self.evaluate_rule(rule, user_context):
                matching_projects.append(rule.project_id)

        return matching_projects

    async def find_best_project(
        self,
        rules: List[AssignmentRule],
        user_context: Dict[str, Any],
    ) -> Optional[UUID]:
        """
        Find the best matching project for a user.

        Args:
            rules: List of assignment rules (sorted by priority DESC)
            user_context: User context data

        Returns:
            Best matching project ID or None
        """
        matching = await self.find_matching_projects(rules, user_context)

        if matching:
            return matching[0]  # Return highest priority match

        return None
