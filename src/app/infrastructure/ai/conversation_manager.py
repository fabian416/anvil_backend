"""
Multi-turn conversation manager.
"""

import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from uuid import UUID

logger = logging.getLogger(__name__)


@dataclass
class ConversationTurn:
    """Single turn in conversation."""
    user_message: str
    agent_response: str
    intent: str
    entities: Dict[str, Any]
    requires_followup: bool = False
    followup_question: Optional[str] = None


class ConversationManager:
    """
    Manages multi-turn conversations with state tracking.
    
    Handles:
    - Incomplete requests (missing info)
    - Follow-up questions
    - Context continuation
    - Clarifications
    """
    
    # Required parameters for each intent
    REQUIRED_PARAMS = {
        "trade_swap": ["src_token", "dst_token", "amount"],
        "trade_perp_open": ["symbol", "leverage", "collateral", "is_long"],
        "trade_perp_close": ["position_id"],
        "portfolio_view": [],  # No required params
    }
    
    def __init__(self):
        """Initialize conversation manager."""
        # Store pending requests: session_id -> pending_intent
        self._pending: Dict[str, Dict[str, Any]] = {}
    
    def check_completeness(
        self,
        intent: str,
        entities: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> tuple[bool, Optional[str]]:
        """
        Check if request has all required information.
        
        Args:
            intent: Classified intent
            entities: Extracted entities
            context: Conversation context
        
        Returns:
            (is_complete, followup_question)
        """
        required = self.REQUIRED_PARAMS.get(intent, [])
        
        if not required:
            return True, None
        
        # Check what's missing
        missing = []
        for param in required:
            if param not in entities:
                # Try to get from context preferences
                if context and self._can_infer_from_context(param, context):
                    continue
                missing.append(param)
        
        if not missing:
            return True, None
        
        # Generate follow-up question
        question = self._generate_followup_question(intent, missing[0])
        
        return False, question
    
    def handle_followup_response(
        self,
        session_id: str,
        message: str,
        extracted_entities: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """
        Handle response to follow-up question.
        
        Args:
            session_id: Session identifier
            message: User's response
            extracted_entities: Entities from response
        
        Returns:
            Complete request data or None
        """
        if session_id not in self._pending:
            return None
        
        pending = self._pending[session_id]
        
        # Merge new entities
        pending["entities"].update(extracted_entities)
        
        # Check if now complete
        is_complete, _ = self.check_completeness(
            pending["intent"],
            pending["entities"],
        )
        
        if is_complete:
            # Clear pending and return complete request
            result = self._pending.pop(session_id)
            return result
        
        return None
    
    def store_pending(
        self,
        session_id: str,
        intent: str,
        entities: Dict[str, Any],
        original_message: str,
    ) -> None:
        """
        Store incomplete request as pending.
        
        Args:
            session_id: Session identifier
            intent: Classified intent
            entities: Extracted entities so far
            original_message: Original user message
        """
        self._pending[session_id] = {
            "intent": intent,
            "entities": entities,
            "original_message": original_message,
        }
    
    def has_pending(self, session_id: str) -> bool:
        """
        Check if session has pending request.
        
        Args:
            session_id: Session identifier
        
        Returns:
            True if has pending
        """
        return session_id in self._pending
    
    def clear_pending(self, session_id: str) -> None:
        """
        Clear pending request.
        
        Args:
            session_id: Session identifier
        """
        if session_id in self._pending:
            del self._pending[session_id]
    
    def _can_infer_from_context(
        self,
        param: str,
        context: Dict[str, Any],
    ) -> bool:
        """
        Check if parameter can be inferred from context.
        
        Args:
            param: Parameter name
            context: Conversation context
        
        Returns:
            True if can infer
        """
        preferences = context.get("user_preferences", {})
        
        # Map parameters to context fields
        param_map = {
            "slippage": "slippage",
            "leverage": "leverage",
        }
        
        context_key = param_map.get(param)
        if context_key and preferences.get(context_key) is not None:
            return True
        
        return False
    
    def _generate_followup_question(
        self,
        intent: str,
        missing_param: str,
    ) -> str:
        """
        Generate follow-up question for missing parameter.
        
        Args:
            intent: Intent type
            missing_param: Missing parameter name
        
        Returns:
            Follow-up question
        """
        # Parameter-specific questions
        questions = {
            "src_token": "Which token do you want to swap from?",
            "dst_token": "Which token do you want to swap to?",
            "amount": "How much do you want to swap?",
            "symbol": "Which asset do you want to trade? (e.g., BTC, ETH)",
            "leverage": "What leverage would you like? (e.g., 5x, 10x)",
            "collateral": "How much collateral in USD?",
            "is_long": "Do you want to go long or short?",
            "position_id": "Which position do you want to close?",
        }
        
        return questions.get(
            missing_param,
            f"Please provide the {missing_param}."
        )


# Global conversation manager
_manager: Optional[ConversationManager] = None


def get_conversation_manager() -> ConversationManager:
    """Get global conversation manager."""
    global _manager
    if _manager is None:
        _manager = ConversationManager()
    return _manager
