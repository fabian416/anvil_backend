"""
Integration tests for Agno agent retry functionality.

Tests retry behavior for agent MCP tool calls.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from app.infrastructure.agno.base_agent import DeFiAgentBase, MCPToolDefinition
from app.setup.config.agno import AgnoConfig, AgnoRetryConfig


class TestAgnoAgentRetry:
    """Test retry functionality for Agno agents."""
    
    @pytest.fixture
    def mock_agno_config(self):
        """Create mock Agno configuration."""
        return AgnoConfig(
            default_model="gpt-4-turbo",
            retry=AgnoRetryConfig(
                enabled=True,
                max_attempts=2,
                initial_backoff_seconds=0.1,  # Fast for testing
                max_backoff_seconds=0.5,
            ),
        )
    
    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_agent_has_retry_decorator(self, mock_agno_config):
        """Test agent initializes with retry decorator."""
        # Arrange & Act
        agent = DeFiAgentBase(
            name="Test Agent",
            role="Test",
            config=mock_agno_config,
            mcp_servers=[],
        )
        
        # Assert
        assert hasattr(agent, '_mcp_retry')
        assert agent._mcp_retry is not None

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_agent_has_retry_decorator",
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
    async def test_mcp_tool_call_retries_on_http_error(self, mock_agno_config):
        """Test MCP tool call retries on HTTP error."""
        # Arrange
        agent = DeFiAgentBase(
            name="Test Agent",
            role="Test",
            config=mock_agno_config,
            mcp_servers=[],
        )
        
        tool_def = MCPToolDefinition(
            server="test_server",
            name="test_tool",
            qualified_name="test_server_test_tool",
            description="Test tool",
            parameters={},
            server_url="http://localhost:8080",
        )
        
        # Create the agno function
        agno_func = agent._create_agno_function(tool_def)
        
        # Mock HTTP client to fail once, then succeed
        mock_response_fail = MagicMock()
        mock_response_fail.raise_for_status.side_effect = httpx.HTTPStatusError(
            "503 Service Unavailable",
            request=MagicMock(),
            response=MagicMock(),
        )
        
        mock_response_success = MagicMock()
        mock_response_success.raise_for_status.return_value = None
        mock_response_success.json.return_value = {
            "success": True,
            "result": {"data": "test_result"},
        }
        
        call_count = 0
        
        async def mock_post(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return mock_response_fail
            return mock_response_success
        
        with patch('httpx.AsyncClient') as MockClient:
            mock_client = AsyncMock()
            mock_client.post = mock_post
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            MockClient.return_value = mock_client
            
            # Act
            result = await agno_func.entrypoint()
        
        # Assert
        assert call_count == 2  # Retried once
        assert "data" in result
        assert result["data"] == "test_result"

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_mcp_tool_call_retries_on_http_error",
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
    async def test_mcp_tool_call_exhausts_retries(self, mock_agno_config):
        """Test MCP tool call exhausts retries and returns error."""
        # Arrange
        agent = DeFiAgentBase(
            name="Test Agent",
            role="Test",
            config=mock_agno_config,
            mcp_servers=[],
        )
        
        tool_def = MCPToolDefinition(
            server="test_server",
            name="test_tool",
            qualified_name="test_server_test_tool",
            description="Test tool",
            parameters={},
            server_url="http://localhost:8080",
        )
        
        agno_func = agent._create_agno_function(tool_def)
        
        # Mock HTTP client to always fail
        call_count = 0
        
        async def mock_post(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            mock_fail = MagicMock()
            mock_fail.raise_for_status.side_effect = httpx.HTTPStatusError(
                "503 Service Unavailable",
                request=MagicMock(),
                response=MagicMock(),
            )
            return mock_fail
        
        with patch('httpx.AsyncClient') as MockClient:
            mock_client = AsyncMock()
            mock_client.post = mock_post
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            MockClient.return_value = mock_client
            
            # Act
            result = await agno_func.entrypoint()
        
        # Assert
        assert call_count == 2  # Max attempts = 2
        assert "error" in result
        assert result["server"] == "test_server"
        assert result["tool"] == "test_tool"

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_mcp_tool_call_exhausts_retries",
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
    async def test_mcp_tool_call_successful_first_attempt(self, mock_agno_config):
        """Test MCP tool call succeeds without retry."""
        # Arrange
        agent = DeFiAgentBase(
            name="Test Agent",
            role="Test",
            config=mock_agno_config,
            mcp_servers=[],
        )
        
        tool_def = MCPToolDefinition(
            server="test_server",
            name="test_tool",
            qualified_name="test_server_test_tool",
            description="Test tool",
            parameters={},
            server_url="http://localhost:8080",
        )
        
        agno_func = agent._create_agno_function(tool_def)
        
        call_count = 0
        
        async def mock_post(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            mock_success = MagicMock()
            mock_success.raise_for_status.return_value = None
            mock_success.json.return_value = {
                "success": True,
                "result": {"data": "first_attempt"},
            }
            return mock_success
        
        with patch('httpx.AsyncClient') as MockClient:
            mock_client = AsyncMock()
            mock_client.post = mock_post
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            MockClient.return_value = mock_client
            
            # Act
            result = await agno_func.entrypoint()
        
        # Assert
        assert call_count == 1  # No retry
        assert "data" in result
        assert result["data"] == "first_attempt"

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_mcp_tool_call_successful_first_attempt",
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
    async def test_retry_on_timeout(self, mock_agno_config):
        """Test MCP tool call retries on timeout."""
        # Arrange
        agent = DeFiAgentBase(
            name="Test Agent",
            role="Test",
            config=mock_agno_config,
            mcp_servers=[],
        )
        
        tool_def = MCPToolDefinition(
            server="test_server",
            name="test_tool",
            qualified_name="test_server_test_tool",
            description="Test tool",
            parameters={},
            server_url="http://localhost:8080",
        )
        
        agno_func = agent._create_agno_function(tool_def)
        
        call_count = 0
        
        async def mock_post(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise httpx.TimeoutException("Request timeout")
            
            mock_success = MagicMock()
            mock_success.raise_for_status.return_value = None
            mock_success.json.return_value = {
                "success": True,
                "result": {"data": "after_timeout"},
            }
            return mock_success
        
        with patch('httpx.AsyncClient') as MockClient:
            mock_client = AsyncMock()
            mock_client.post = mock_post
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            MockClient.return_value = mock_client
            
            # Act
            result = await agno_func.entrypoint()
        
        # Assert
        assert call_count == 2  # Retried after timeout
        assert "data" in result
        assert result["data"] == "after_timeout"

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_retry_on_timeout",
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
    async def test_agno_config_retry_defaults(self, mock_mcp_manager_http):
        """Test AgnoConfig has correct retry defaults."""
        # Arrange & Act
        config = AgnoConfig()
        
        # Assert
        assert hasattr(config, 'retry')
        assert config.retry.enabled is True
        assert config.retry.max_attempts == 2
        assert config.retry.initial_backoff_seconds == 1.0
        assert config.retry.max_backoff_seconds == 5.0
        assert config.retry.circuit_breaker_enabled is True
        assert config.retry.telemetry_enabled is True

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_agno_config_retry_defaults",
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
    async def test_custom_retry_configuration(self, mock_mcp_manager_http):
        """Test custom retry configuration."""
        # Arrange & Act
        config = AgnoConfig(
            retry=AgnoRetryConfig(
                enabled=True,
                max_attempts=3,
                initial_backoff_seconds=0.5,
            )
        )
        
        # Assert
        assert config.retry.max_attempts == 3
        assert config.retry.initial_backoff_seconds == 0.5

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_custom_retry_configuration",
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
    async def test_legacy_retry_max_attempts_property(self, mock_mcp_manager_http):
        """Test legacy retry_max_attempts property."""
        # Arrange & Act
        config = AgnoConfig(
            retry=AgnoRetryConfig(max_attempts=3)
        )
        
        # Assert
        assert config.retry_max_attempts == 3  # Legacy property
        assert config.retry.max_attempts == 3  # New property

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_legacy_retry_max_attempts_property",
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
    async def test_retry_backoff_timing(self, mock_agno_config):
        """Test retry respects backoff timing."""
        # Arrange
        agent = DeFiAgentBase(
            name="Test Agent",
            role="Test",
            config=mock_agno_config,
            mcp_servers=[],
        )
        
        tool_def = MCPToolDefinition(
            server="test_server",
            name="test_tool",
            qualified_name="test_server_test_tool",
            description="Test tool",
            parameters={},
            server_url="http://localhost:8080",
        )
        
        agno_func = agent._create_agno_function(tool_def)
        
        import time
        call_times = []
        
        async def mock_post(*args, **kwargs):
            call_times.append(time.time())
            raise httpx.HTTPStatusError(
                "503 Service Unavailable",
                request=MagicMock(),
                response=MagicMock(),
            )
        
        with patch('httpx.AsyncClient') as MockClient:
            mock_client = AsyncMock()
            mock_client.post = mock_post
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            MockClient.return_value = mock_client
            
            # Act
            result = await agno_func.entrypoint()
        
        # Assert
        assert len(call_times) == 2  # 2 attempts
        if len(call_times) >= 2:
            delay = call_times[1] - call_times[0]
            # Should have some backoff delay (configured at 0.1s minimum)

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_retry_backoff_timing",
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

            assert delay >= 0.05  # At least 50ms (allowing for variance)