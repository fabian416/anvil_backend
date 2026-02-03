"""User-project assignment service."""

from typing import Dict, List, Optional, Any
from uuid import UUID

from app.domain.entities.assignment_rule import AssignmentRule, UserProjectAssignment
from app.domain.services.assignment.rule_evaluator import RuleEvaluator


class AssignmentService:
    """
    Service for managing user-project assignments.

    Handles auto-assignment, manual assignment, and active project switching.
    """

    def __init__(
        self,
        rule_evaluator: RuleEvaluator,
    ):
        """
        Initialize assignment service.

        Args:
            rule_evaluator: Rule evaluation service
        """
        self.rule_evaluator = rule_evaluator

    async def auto_assign_user(
        self,
        user_id: UUID,
        user_context: Dict[str, Any],
        rules: List[AssignmentRule],
        existing_assignments: List[UUID],
    ) -> List[UserProjectAssignment]:
        """
        Auto-assign user to matching projects.

        Args:
            user_id: User to assign
            user_context: User context data
            rules: Active assignment rules (sorted by priority)
            existing_assignments: Already assigned project IDs

        Returns:
            List of new assignments created
        """
        # Find matching projects
        matching_projects = await self.rule_evaluator.find_matching_projects(
            rules=rules,
            user_context=user_context,
        )

        # Filter out already assigned
        new_projects = [p for p in matching_projects if p not in existing_assignments]

        # Create assignments
        assignments = []
        for project_id in new_projects:
            # Find the rule that matched
            matching_rule = next(
                (r for r in rules if r.project_id == project_id),
                None,
            )

            reason = (
                f"Auto-assigned via rule: {matching_rule.rule_name}"
                if matching_rule
                else "Auto-assigned"
            )

            assignment = UserProjectAssignment.create_auto(
                user_id=user_id,
                project_id=project_id,
                reason=reason,
            )
            assignments.append(assignment)

        return assignments

    async def recommend_project(
        self,
        user_id: UUID,
        user_context: Dict[str, Any],
        rules: List[AssignmentRule],
    ) -> Optional[UUID]:
        """
        Recommend best project for user.

        Args:
            user_id: User to recommend for
            user_context: User context data
            rules: Active assignment rules (sorted by priority DESC)

        Returns:
            Recommended project ID or None
        """
        return await self.rule_evaluator.find_best_project(
            rules=rules,
            user_context=user_context,
        )

    def should_auto_switch(
        self,
        rule: AssignmentRule,
        user_context: Dict[str, Any],
    ) -> bool:
        """
        Determine if user should be auto-switched to project.

        Args:
            rule: Assignment rule
            user_context: User context data

        Returns:
            True if should auto-switch
        """
        # Only auto-switch if rule has auto_switch enabled
        if not rule.auto_switch:
            return False

        # Don't auto-switch if user is actively using another project
        if user_context.get("has_active_session", False):
            return False

        return True
