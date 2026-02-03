"""
Base DeFi agent template for specialized agents.
"""

from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod
from uuid import UUID

try:
    from agno.agent import Agent
    from agno.models.openai import OpenAIChat

    AGNO_AVAILABLE = True
except ImportError:
    # Agno not available - use mock for testing
    AGNO_AVAILABLE = False
    Agent = None  # type: ignore
    OpenAIChat = None  # type: ignore


class BaseDeFiAgent(ABC):
    """
    Base class for all DeFi specialized agents.

    Provides common functionality:
    - Agent initialization
    - Message processing
    - Context management
    - Error handling
    """

    def __init__(
        self,
        name: str,
        description: str,
        instructions: List[str],
        model: str = "gpt-4-turbo",
        tools: Optional[List[Any]] = None,
    ):
        """
        Initialize DeFi agent.

        Args:
            name: Agent name
            description: Agent description
            instructions: List of instruction strings
            model: LLM model to use
            tools: Optional list of tools for the agent
        """
        self.name = name
        self.description = description
        self.model_name = model
        self._instructions = instructions
        self._tools = tools or []

        # Create Agno agent if available
        if AGNO_AVAILABLE and Agent is not None:
            self.agent = Agent(
                name=name,
                model=OpenAIChat(id=model),
                description=description,
                instructions=instructions,
                tools=tools or [],
                add_history_to_context=True,
                add_datetime_to_context=True,
                markdown=False,  # We'll format responses ourselves
            )
        else:
            # Mock agent for testing
            self.agent = None

    async def run(self, message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Process a user message and return agent response.

        Args:
            message: User message
            context: Optional conversation context

        Returns:
            Agent response string
        """
        try:
            # Add context to message if provided
            if context:
                message = self._prepare_message_with_context(message, context)

            # Run agent
            if self.agent is not None:
                response = await self.agent.arun(message)
                # Extract response content
                return self._extract_response(response)
            else:
                # Fallback for testing without Agno
                return f"[{self.name}] Processing: {message[:50]}..."

        except Exception as e:
            return self._handle_error(e)

    def _prepare_message_with_context(
        self, message: str, context: Dict[str, Any]
    ) -> str:
        """
        Prepare message with conversation context.

        Args:
            message: User message
            context: Conversation context

        Returns:
            Enhanced message with context
        """
        # Extract relevant context
        user_id = context.get("user_id")
        recent_action = context.get("recent_action")

        # Build context string
        context_parts = []

        if user_id:
            context_parts.append(f"User ID: {user_id}")

        if recent_action:
            context_parts.append(f"Recent action: {recent_action}")

        # Add context to message
        if context_parts:
            context_str = " | ".join(context_parts)
            return f"[Context: {context_str}]\n\n{message}"

        return message

    def _extract_response(self, response: Any) -> str:
        """
        Extract response content from agent response.

        Args:
            response: Agent response object

        Returns:
            Response string
        """
        # Agno agent returns response with content
        if hasattr(response, "content"):
            return response.content

        # If it's already a string
        if isinstance(response, str):
            return response

        # Convert to string as fallback
        return str(response)

    def _handle_error(self, error: Exception) -> str:
        """
        Handle errors during agent execution.

        Args:
            error: Exception that occurred

        Returns:
            Error message for user
        """
        error_msg = str(error)
        print(f"[{self.name}] Error: {error_msg}")

        return (
            f"I apologize, but I encountered an error while processing your request. "
            f"Please try again or rephrase your question."
        )

    @abstractmethod
    def get_intent_types(self) -> List[str]:
        """
        Get the intent types this agent handles.

        Returns:
            List of intent type strings
        """
        pass

    @abstractmethod
    def get_tools(self) -> List[Any]:
        """
        Get the tools this agent uses.

        Returns:
            List of tool instances
        """
        pass


def create_defi_agent(
    name: str,
    description: str,
    instructions: List[str],
    intents: List[str],
    tools: Optional[List[Any]] = None,
    model: str = "gpt-4-turbo",
) -> BaseDeFiAgent:
    """
    Factory function to create a DeFi agent.

    Args:
        name: Agent name
        description: Agent description
        instructions: List of instructions
        intents: Intent types this agent handles
        tools: Optional tools
        model: LLM model

    Returns:
        DeFi agent instance
    """

    class CustomDeFiAgent(BaseDeFiAgent):
        def __init__(self):
            super().__init__(name, description, instructions, model, tools)
            self._intents = intents

        def get_intent_types(self) -> List[str]:
            return self._intents

        def get_tools(self) -> List[Any]:
            return tools or []

    return CustomDeFiAgent()
