"""
Pytest fixtures for Agno integration tests.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def mock_mcp_manager_http(mocker):
    """
    Mock HTTP calls to MCP manager.

    This fixture mocks httpx.AsyncClient to simulate MCP manager responses
    without requiring an actual MCP manager server running.
    """
    # Create mock response for /tools endpoint
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "tools": [
            {
                "server": "defillama",
                "tool_name": "get_protocol_tvl",
                "qualified_name": "defillama__get_protocol_tvl",
                "description": "Get TVL for a DeFi protocol",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "protocol": {"type": "string", "description": "Protocol name"}
                    },
                    "required": ["protocol"],
                },
                "server_url": "http://localhost:8000",
            },
            {
                "server": "coingecko",
                "tool_name": "get_token_price",
                "qualified_name": "coingecko__get_token_price",
                "description": "Get current token price",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "token_id": {"type": "string", "description": "Token ID"}
                    },
                    "required": ["token_id"],
                },
                "server_url": "http://localhost:8000",
            },
            {
                "server": "oneinch",
                "tool_name": "get_swap_quote",
                "qualified_name": "oneinch__get_swap_quote",
                "description": "Get swap quote",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "from_token": {"type": "string"},
                        "to_token": {"type": "string"},
                        "amount": {"type": "string"},
                    },
                    "required": ["from_token", "to_token", "amount"],
                },
                "server_url": "http://localhost:8000",
            },
            {
                "server": "thegraph",
                "tool_name": "query_subgraph",
                "qualified_name": "thegraph__query_subgraph",
                "description": "Query subgraph data",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "GraphQL query"}
                    },
                    "required": ["query"],
                },
                "server_url": "http://localhost:8000",
            },
        ]
    }
    mock_response.raise_for_status = MagicMock()

    # Create mock AsyncClient context manager
    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response

    # Create mock context manager
    mock_context = AsyncMock()
    mock_context.__aenter__.return_value = mock_client
    mock_context.__aexit__.return_value = None

    # Patch httpx.AsyncClient to return our mock context manager
    mocker.patch("httpx.AsyncClient", return_value=mock_context)

    return mock_client


@pytest.fixture
def mock_mcp_manager_unavailable(mocker):
    """
    Mock MCP manager as unavailable (connection error).

    Use this fixture to test fallback behavior when MCP manager is down.
    """
    import httpx

    # Create mock that raises connection error
    mock_context = AsyncMock()
    mock_client = AsyncMock()
    mock_client.get.side_effect = httpx.ConnectError("Connection refused")
    mock_context.__aenter__.return_value = mock_client
    mock_context.__aexit__.return_value = None

    mocker.patch("httpx.AsyncClient", return_value=mock_context)

    return mock_client
