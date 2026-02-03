"""Base Agno Agent with MCP Tool Integration.

Provides foundation for all specialized DeFi agents, integrating Agno's
powerful agent runtime with our MCP (Model Context Protocol) tool servers.

Architecture:
    - Agno Agent as the runtime engine
    - MCP servers for tool discovery and execution
    - Async tool loading from MCP manager
    - Session management and memory
    - Streaming support

Key Features:
    - Automatic MCP tool discovery
    - Type-safe tool registration
    - Session-based conversations
    - Streaming responses
    - Error handling and recovery
"""

from typing import Dict, List, Any, Optional, AsyncIterator
from dataclasses import dataclass
import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

# Agno imports (from PyPI package)
from agno.agent import Agent, Message, RunEvent, RunOutput
from agno.tools import Toolkit
from agno.tools.function import Function
from agno.models.openai import OpenAIChat

from app.setup.config.agno import AgnoConfig


@dataclass
class MCPToolDefinition:
    """Definition of an MCP tool loaded from server."""

    server: str
    name: str
    qualified_name: str  # server_name
    description: str
    parameters: Dict[str, Any]  # JSON Schema
    server_url: str


class DeFiAgentBase:
    """
    Base class for all DeFi Agno agents.

    Provides:
    - MCP tool integration
    - Session management
    - Streaming support
    - Error handling

    Usage:
        class TradingAgent(DeFiAgentBase):
            def __init__(self, config: AgnoConfig):
                super().__init__(
                    name="Trading Agent",
                    role="DeFi trading specialist",
                    config=config,
                    mcp_servers=["1inch"],
                )
    """

    def __init__(
        self,
        name: str,
        role: str,
        config: AgnoConfig,
        mcp_servers: Optional[List[str]] = None,
        mcp_manager_url: str = "http://localhost:8080",
        instructions: Optional[List[str]] = None,
        add_datetime_to_instructions: bool = True,
        markdown: bool = True,
        debug_mode: bool = False,
    ):
        """
        Initialize DeFi agent.

        Args:
            name: Agent name (e.g., "Trading Agent")
            role: Agent role description
            config: Agno configuration
            mcp_servers: List of MCP servers to load tools from (e.g., ["1inch", "aave"])
            mcp_manager_url: URL of MCP manager API
            instructions: Custom instructions for agent
            add_datetime_to_instructions: Add timestamp to instructions
            markdown: Use markdown in responses
            debug_mode: Enable debug logging
        """
        self.name = name
        self.role = role
        self.config = config
        self.mcp_servers = mcp_servers or []
        self.mcp_manager_url = mcp_manager_url
        self.debug_mode = debug_mode

        # Build instructions
        self.instructions = self._build_instructions(instructions)

        # MCP tools (loaded async)
        self.mcp_tools: List[MCPToolDefinition] = []
        self.agno_functions: List[Function] = []

        # Create retry decorator for MCP tool calls
        self._mcp_retry = retry(
            stop=stop_after_attempt(
                config.retry_max_attempts
                if hasattr(config, "retry_max_attempts")
                else 2
            ),
            wait=wait_exponential(multiplier=1, min=1, max=5),
            retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
            reraise=True,
        )

        # Create Agno agent (tools loaded separately)
        self.agent = Agent(
            name=name,
            model=OpenAIChat(
                id=config.model_id,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
            ),
            instructions=self.instructions,
            markdown=markdown,
            # Tools added via add_tool() after MCP discovery
        )

        if self.debug_mode:
            print(f"[{self.name}] Initialized (model: {config.model_id})")

    def _build_instructions(
        self,
        custom_instructions: Optional[List[str]] = None,
    ) -> List[str]:
        """Build agent instructions."""
        base_instructions = [
            f"You are {self.name}, a {self.role}.",
            "You help users with DeFi operations through natural conversation.",
            "You have access to specialized tools for DeFi protocols.",
            "Always explain what you're doing and ask for confirmation before executing transactions.",
            "Provide clear, accurate information about risks and costs.",
            "If you're unsure, ask clarifying questions.",
            "Be concise but thorough in your responses.",
        ]

        if custom_instructions:
            base_instructions.extend(custom_instructions)

        return base_instructions

    async def load_mcp_tools(self):
        """
        Load tools from MCP servers.

        Discovers available tools from MCP manager and registers them
        with the Agno agent.
        """
        if self.debug_mode:
            print(f"[{self.name}] Loading MCP tools...")

        try:
            async with httpx.AsyncClient() as client:
                # Get all tools from manager
                response = await client.get(f"{self.mcp_manager_url}/tools")
                response.raise_for_status()
                data = response.json()

                all_tools = data.get("tools", [])

                # Filter by requested servers
                if self.mcp_servers:
                    filtered_tools = [
                        tool for tool in all_tools if tool["server"] in self.mcp_servers
                    ]
                else:
                    filtered_tools = all_tools

                # Convert to MCPToolDefinition
                for tool in filtered_tools:
                    tool_def = MCPToolDefinition(
                        server=tool["server"],
                        name=tool["tool_name"],
                        qualified_name=tool["qualified_name"],
                        description=tool["description"],
                        parameters=tool["parameters"],
                        server_url=tool["server_url"],
                    )
                    self.mcp_tools.append(tool_def)

                    # Create Agno Function for this tool
                    agno_func = self._create_agno_function(tool_def)
                    self.agno_functions.append(agno_func)

                    # Add to agent
                    self.agent.add_tool(agno_func)

                if self.debug_mode:
                    print(f"[{self.name}] Loaded {len(self.mcp_tools)} tools")
                    for tool in self.mcp_tools:
                        print(f"          • {tool.qualified_name} ({tool.server})")

        except Exception as e:
            print(f"[{self.name}] Error loading MCP tools: {e}")
            raise

    def _create_agno_function(self, tool_def: MCPToolDefinition) -> Function:
        """
        Create an Agno Function from an MCP tool definition.

        Args:
            tool_def: MCP tool definition

        Returns:
            Agno Function that calls the MCP tool with retry logic
        """

        # Create async handler that calls MCP tool with retry
        async def mcp_tool_handler(**kwargs) -> Dict[str, Any]:
            """Handler that calls MCP tool via HTTP with automatic retry."""

            @self._mcp_retry
            async def _execute_mcp_call():
                """Inner function with retry logic."""
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{self.mcp_manager_url}/tools/{tool_def.name}",
                        json={"parameters": kwargs},
                        timeout=30.0,
                    )
                    response.raise_for_status()
                    return response.json()

            try:
                result = await _execute_mcp_call()

                if result.get("success"):
                    return result.get("result", {})
                else:
                    return {
                        "error": result.get("error", "Tool execution failed"),
                        "server": tool_def.server,
                        "tool": tool_def.name,
                    }

            except Exception as e:
                return {
                    "error": str(e),
                    "server": tool_def.server,
                    "tool": tool_def.name,
                }

        # Create Function with JSON Schema parameters
        return Function(
            name=tool_def.qualified_name,
            description=tool_def.description,
            parameters=tool_def.parameters,
            entrypoint=mcp_tool_handler,
        )

    async def run(
        self,
        message: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        stream: bool = False,
    ) -> RunOutput:
        """
        Run agent with a message.

        Args:
            message: User message
            user_id: User identifier
            session_id: Session identifier (for continuing conversation)
            stream: Whether to stream response

        Returns:
            RunOutput with agent response
        """
        if self.debug_mode:
            print(f"[{self.name}] Running with message: {message[:100]}...")

        # Create or continue session
        if session_id:
            # Continue existing session
            result = await self.agent.arun(
                message,
                session_id=session_id,
                stream=stream,
            )
        else:
            # New session
            result = await self.agent.arun(
                message,
                user_id=user_id,
                stream=stream,
            )

        return result

    async def run_stream(
        self,
        message: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> AsyncIterator[RunEvent]:
        """
        Run agent with streaming response.

        Args:
            message: User message
            user_id: User identifier
            session_id: Session identifier

        Yields:
            RunEvent objects for streaming
        """
        if self.debug_mode:
            print(f"[{self.name}] Streaming with message: {message[:100]}...")

        # Stream response
        if session_id:
            async for event in self.agent.arun_stream(
                message,
                session_id=session_id,
            ):
                yield event
        else:
            async for event in self.agent.arun_stream(
                message,
                user_id=user_id,
            ):
                yield event

    async def print_response(self, message: str, **kwargs):
        """
        Run agent and print response (for CLI testing).

        Args:
            message: User message
            **kwargs: Additional arguments for run()
        """
        result = await self.run(message, **kwargs)

        print("\n" + "=" * 60)
        print(f"Agent: {self.name}")
        print("=" * 60)
        print(result.content)
        print("=" * 60 + "\n")

    def get_available_tools(self) -> List[Dict[str, str]]:
        """
        Get list of available MCP tools.

        Returns:
            List of tool info dictionaries
        """
        return [
            {
                "server": tool.server,
                "name": tool.name,
                "qualified_name": tool.qualified_name,
                "description": tool.description,
            }
            for tool in self.mcp_tools
        ]


# Example usage (for testing)
if __name__ == "__main__":
    import asyncio

    # Create config
    config = AgnoConfig(
        model_id="gpt-4-turbo",
        temperature=0.7,
        max_tokens=2000,
        show_tool_calls=True,
    )

    async def test_base_agent():
        """Test base agent with MCP tools."""
        # Create agent
        agent = DeFiAgentBase(
            name="Test Agent",
            role="DeFi operations assistant",
            config=config,
            mcp_servers=["portfolio", "1inch"],
            debug_mode=True,
        )

        # Load MCP tools
        await agent.load_mcp_tools()

        # Print available tools
        print("\nAvailable Tools:")
        for tool in agent.get_available_tools():
            print(f"  • {tool['qualified_name']}: {tool['description'][:60]}...")

        # Run a test message
        await agent.print_response("What tools do you have available?")

    # Run test
    print("""
╔══════════════════════════════════════════════════════════╗
║        Base Agno Agent - MCP Integration Test            ║
╚══════════════════════════════════════════════════════════╝
    """)

    asyncio.run(test_base_agent())
