"""
Integration tests for Perplexity MCP Server.

Tests retry functionality and API integration.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from app.infrastructure.mcp.servers.perplexity_mcp import PerplexityMCPServer
from app.setup.config.mcp import MCPSettings, MCPRetrySettings


class TestPerplexityMCP:
    """Test Perplexity MCP server."""
    
    @pytest.fixture
    def mock_settings(self):
        """Mock MCP settings."""
        return MCPSettings(
            enabled=True,
            retry=MCPRetrySettings(
                enabled=True,
                max_retries=3,
                initial_backoff_seconds=0.1,
                max_backoff_seconds=0.5,
            ),
        )
    
    @pytest.fixture
    def server(self, mock_settings):
        """Create test server."""
        return PerplexityMCPServer(
            api_key="test_key",
            settings=mock_settings,
        )
    
    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_retry_decorator_exists(self, server):
        """Test that retry decorator is initialized."""
        assert hasattr(server, "_retry")
        assert server._retry is not None

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_retry_decorator_exists",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

    
    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_search_success(self, server):
        """Test successful search."""
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "Ethereum is a blockchain platform."
                    }
                }
            ],
            "citations": ["https://ethereum.org"],
            "usage": {"total_tokens": 50},
        }
        
        with patch.object(
            server.client, "post", new_callable=AsyncMock
        ) as mock_post:
            mock_post.return_value = mock_response
            
            result = await server._search("What is Ethereum?")
            
            assert "answer" in result
            assert "Ethereum" in result["answer"]
            assert "citations" in result
            assert len(result["citations"]) > 0

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_search_success",
                user_input="Ethereum is a blockchain platform.",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

    
    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_search_retries_on_http_error(self, server):
        """Test that search retries on HTTP error."""
        mock_response_fail = MagicMock()
        mock_response_fail.raise_for_status.side_effect = httpx.HTTPStatusError(
            "503 Service Unavailable",
            request=MagicMock(),
            response=MagicMock(),
        )
        
        mock_response_success = MagicMock()
        mock_response_success.raise_for_status.return_value = None
        mock_response_success.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "Bitcoin is a cryptocurrency."
                    }
                }
            ],
            "citations": [],
            "usage": {},
        }
        
        call_count = 0
        
        async def mock_post(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                return mock_response_fail
            return mock_response_success
        
        with patch.object(
            server.client, "post", side_effect=mock_post
        ):
            result = await server._search("What is Bitcoin?")
            
            assert "answer" in result
            assert "Bitcoin" in result["answer"]
            assert call_count == 3  # Failed twice, succeeded third time

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_search_retries_on_http_error",
                user_input="Bitcoin is a cryptocurrency.",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

    
    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_search_handles_timeout(self, server):
        """Test search handles timeout error."""
        with patch.object(
            server.client, "post", new_callable=AsyncMock
        ) as mock_post:
            mock_post.side_effect = httpx.TimeoutException("Request timeout")
            
            result = await server._search("What is DeFi?")
            
            assert "error" in result
            assert "timeout" in result["error"].lower()

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_search_handles_timeout",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

    
    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_chat_success(self, server):
        """Test successful chat."""
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "DeFi stands for Decentralized Finance.",
                    }
                }
            ],
            "citations": ["https://defipulse.com"],
            "usage": {"total_tokens": 45},
        }
        
        with patch.object(
            server.client, "post", new_callable=AsyncMock
        ) as mock_post:
            mock_post.return_value = mock_response
            
            messages = [
                {"role": "user", "content": "What is DeFi?"}
            ]
            result = await server._chat(messages)
            
            assert "message" in result
            assert "content" in result["message"]
            assert "DeFi" in result["message"]["content"]

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_chat_success",
                user_input="DeFi stands for Decentralized Finance.",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

    
    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_call_tool_search(self, server):
        """Test calling search tool."""
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test answer"}}],
            "citations": [],
            "usage": {},
        }
        
        with patch.object(
            server.client, "post", new_callable=AsyncMock
        ) as mock_post:
            mock_post.return_value = mock_response
            
            result = await server.call_tool(
                "search",
                {"query": "test query"}
            )
            
            assert "answer" in result or "error" not in result

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_call_tool_search",
                user_input="Test answer",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

    
    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_call_tool_unknown(self, server):
        """Test calling unknown tool."""
        result = await server.call_tool(
            "unknown_tool",
            {}
        )
        
        assert "error" in result
        assert "Unknown tool" in result["error"]

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_call_tool_unknown",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

    
    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_tools_registered(self, server):
        """Test that tools are registered."""
        assert "search" in server.tools
        assert "chat" in server.tools
        
        search_tool = server.tools["search"]
        assert "name" in search_tool
        assert "description" in search_tool
        assert "parameters" in search_tool
        assert "handler" in search_tool

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_tools_registered",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

    
    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_retry_configuration(self, mock_settings):
        """Test retry configuration from settings."""
        server = PerplexityMCPServer(
            api_key="test_key",
            settings=mock_settings,
        )
        
        assert server._retry is not None
        # Retry decorator should be callable (it's a decorator function)

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_retry_configuration",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        assert callable(server._retry)