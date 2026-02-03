"""
MCP Client for calling MCP servers via HTTP.

Provides a simple interface to call tools on MCP servers running on different ports.
"""

import logging
from typing import Any, Dict

import httpx

logger = logging.getLogger(__name__)


class MCPClient:
    """
    HTTP client for calling MCP server tools.

    MCP servers expose tools via HTTP endpoints:
    - GET /tools - List available tools
    - POST /tools/{tool_name} - Call a tool

    Example:
        client = MCPClient()
        result = await client.call_tool(
            server_url="http://localhost:8085",
            tool_name="get_user_positions",
            arguments={"wallet_address": "0x..."}
        )
    """

    def __init__(self, timeout: float = 30.0):
        """
        Initialize MCP client.

        Args:
            timeout: HTTP request timeout in seconds
        """
        self._timeout = timeout
        self._client = httpx.AsyncClient(timeout=timeout)

    async def call_tool(
        self,
        server_url: str,
        tool_name: str,
        arguments: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Call a tool on an MCP server.

        Args:
            server_url: Base URL of the MCP server (e.g., "http://localhost:8085")
            tool_name: Name of the tool to call
            arguments: Tool arguments/parameters

        Returns:
            Tool execution result

        Raises:
            httpx.HTTPError: If HTTP request fails
            ValueError: If tool call fails or returns error
        """
        url = f"{server_url.rstrip('/')}/tools/{tool_name}"

        logger.debug(
            f"Calling MCP tool: {tool_name} on {server_url} with args: {arguments}"
        )

        try:
            response = await self._client.post(
                url,
                json={"parameters": arguments},
            )
            response.raise_for_status()

            result = response.json()

            # Check if tool execution was successful
            if isinstance(result, dict):
                if result.get("success") is False:
                    error_msg = result.get("error", "Unknown error")
                    raise ValueError(f"MCP tool '{tool_name}' failed: {error_msg}")

                # Return the result field if present, otherwise return the whole response
                if "result" in result:
                    return result["result"]

            return result

        except httpx.HTTPStatusError as e:
            logger.error(
                f"MCP tool '{tool_name}' HTTP error: {e.response.status_code} - {e.response.text}"
            )
            raise ValueError(
                f"MCP tool '{tool_name}' HTTP error: {e.response.status_code}"
            ) from e
        except httpx.RequestError as e:
            logger.error(f"MCP tool '{tool_name}' request error: {e}")
            raise ValueError(f"MCP tool '{tool_name}' request failed: {str(e)}") from e

    async def list_tools(self, server_url: str) -> list[Dict[str, Any]]:
        """
        List available tools on an MCP server.

        Args:
            server_url: Base URL of the MCP server

        Returns:
            List of tool descriptions
        """
        url = f"{server_url.rstrip('/')}/tools"

        try:
            response = await self._client.get(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to list tools from {server_url}: {e}")
            raise ValueError(f"Failed to list tools: {str(e)}") from e

    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
