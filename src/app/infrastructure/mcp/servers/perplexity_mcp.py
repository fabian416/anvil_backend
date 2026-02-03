"""
Perplexity MCP Server.

Provides access to Perplexity AI's search and research capabilities.
"""

from typing import Dict, Any, Optional, List
import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from app.infrastructure.mcp.base import MCPServer
from app.setup.config.mcp import MCPSettings


class PerplexityMCPServer(MCPServer):
    """
    MCP server for Perplexity AI API.

    Provides intelligent search and research capabilities with retry support.
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.perplexity.ai",
        timeout_ms: int = 600000,  # 10 minutes default
        settings: Optional[MCPSettings] = None,
    ):
        """
        Initialize Perplexity MCP server.

        Args:
            api_key: Perplexity API key
            base_url: Base URL for Perplexity API
            timeout_ms: Request timeout in milliseconds
            settings: MCP settings for retry configuration
        """
        super().__init__(
            "perplexity",
            version="1.0.0",
            description="Perplexity AI research MCP server",
        )
        self.api_key = api_key
        self.base_url = base_url
        self.timeout_seconds = timeout_ms / 1000.0

        self.client = httpx.AsyncClient(
            base_url=base_url,
            timeout=self.timeout_seconds,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )

        # Initialize retry decorator
        retry_config = settings.retry if settings else None
        max_retries = (
            retry_config.max_retries if retry_config and retry_config.enabled else 3
        )
        initial_backoff = retry_config.initial_backoff_seconds if retry_config else 2.0
        max_backoff = retry_config.max_backoff_seconds if retry_config else 10.0

        self._retry = retry(
            stop=stop_after_attempt(max_retries),
            wait=wait_exponential(multiplier=1, min=initial_backoff, max=max_backoff),
            retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
            reraise=True,
        )

        self._register_tools()

    def setup_tools(self):
        """Implement abstract method - tools are registered in _register_tools."""
        pass

    def _register_tools(self):
        """Register Perplexity MCP tools."""
        # Register search tool
        self.register_tool(
            name="search",
            description="Search the web using Perplexity AI for current information",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query",
                    },
                    "model": {
                        "type": "string",
                        "description": "Model to use (sonar-small-online, sonar-medium-online, sonar-large-online)",
                        "default": "sonar-small-online",
                    },
                    "max_tokens": {
                        "type": "integer",
                        "description": "Maximum tokens in response",
                        "default": 1024,
                    },
                },
                "required": ["query"],
            },
            handler=self._search,
        )

        # Register chat tool
        self.register_tool(
            name="chat",
            description="Have a conversation with Perplexity AI with web search capabilities",
            parameters={
                "type": "object",
                "properties": {
                    "messages": {
                        "type": "array",
                        "description": "Conversation messages",
                        "items": {
                            "type": "object",
                            "properties": {
                                "role": {"type": "string"},
                                "content": {"type": "string"},
                            },
                        },
                    },
                    "model": {
                        "type": "string",
                        "description": "Model to use",
                        "default": "sonar-small-online",
                    },
                },
                "required": ["messages"],
            },
            handler=self._chat,
        )

    async def _search(
        self,
        query: str,
        model: str = "sonar-small-online",
        max_tokens: int = 1024,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Search using Perplexity AI.

        Args:
            query: Search query
            model: Model to use
            max_tokens: Maximum tokens in response

        Returns:
            Search results
        """

        @self._retry
        async def _fetch():
            response = await self.client.post(
                "/chat/completions",
                json={
                    "model": model,
                    "messages": [
                        {
                            "role": "user",
                            "content": query,
                        }
                    ],
                    "max_tokens": max_tokens,
                },
            )
            response.raise_for_status()
            return response.json()

        try:
            data = await _fetch()

            # Extract the response
            if "choices" in data and len(data["choices"]) > 0:
                content = data["choices"][0].get("message", {}).get("content", "")
                citations = data.get("citations", [])

                return {
                    "query": query,
                    "answer": content,
                    "citations": citations,
                    "model": model,
                    "usage": data.get("usage", {}),
                }
            else:
                return {
                    "error": "No results found",
                    "query": query,
                }

        except httpx.HTTPError as e:
            return {
                "error": f"Perplexity API error: {str(e)}",
                "query": query,
            }
        except Exception as e:
            return {
                "error": f"Error searching with Perplexity: {str(e)}",
                "query": query,
            }

    async def _chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "sonar-small-online",
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Chat with Perplexity AI.

        Args:
            messages: List of conversation messages
            model: Model to use

        Returns:
            Chat response
        """

        @self._retry
        async def _fetch():
            response = await self.client.post(
                "/chat/completions",
                json={
                    "model": model,
                    "messages": messages,
                },
            )
            response.raise_for_status()
            return response.json()

        try:
            data = await _fetch()

            # Extract the response
            if "choices" in data and len(data["choices"]) > 0:
                message = data["choices"][0].get("message", {})

                return {
                    "message": message,
                    "citations": data.get("citations", []),
                    "model": model,
                    "usage": data.get("usage", {}),
                }
            else:
                return {
                    "error": "No response from Perplexity",
                }

        except httpx.HTTPError as e:
            return {
                "error": f"Perplexity API error: {str(e)}",
            }
        except Exception as e:
            return {
                "error": f"Error chatting with Perplexity: {str(e)}",
            }

    async def call_tool(
        self, tool_name: str, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Call a Perplexity tool.

        Args:
            tool_name: Name of the tool
            parameters: Tool parameters

        Returns:
            Tool response
        """
        if tool_name not in self.tools:
            return {
                "error": f"Unknown tool: {tool_name}",
                "available_tools": list(self.tools.keys()),
            }

        tool = self.tools[tool_name]
        handler = tool.handler

        try:
            return await handler(**parameters)
        except Exception as e:
            return {
                "error": f"Tool execution error: {str(e)}",
                "tool": tool_name,
            }

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


# Main entry point for running server standalone
if __name__ == "__main__":
    import os
    import uvicorn

    print("""
╔══════════════════════════════════════════════════════════╗
║       Perplexity MCP Server Starting...                 ║
╚══════════════════════════════════════════════════════════╝

Port: 8087

Tools Available:
  • research: AI-powered research with citations
  • chat: Conversational AI with Perplexity

Endpoints:
  GET  /           - Server info
  GET  /tools      - List all tools
  POST /tools/{name} - Call a tool
  GET  /health     - Health check

Starting server...
    """)

    # Get API key from environment
    api_key = os.getenv("PERPLEXITY_API_KEY", "")

    # Create server
    server = PerplexityMCPServer(api_key=api_key)

    uvicorn.run(server.app, host="0.0.0.0", port=8087, log_level="info")
