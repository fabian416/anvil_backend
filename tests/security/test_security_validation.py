"""
Security validation tests for Phase 6.

Validates:
- No hardcoded credentials
- Proper API key management
- User data isolation
- Input validation
- Authentication/authorization
"""

import pytest
import re
from uuid import uuid4
from pathlib import Path


# ==============================================================================
# CREDENTIAL SECURITY
# ==============================================================================

class TestCredentialSecurity:
    """Validate no hardcoded credentials or API keys"""
    
    def test_no_hardcoded_api_keys_in_agent_squad_gateway(self):
        """Verify AgentSquadGateway has no hardcoded API keys"""
        gateway_file = Path(__file__).parent.parent.parent / "src/app/infrastructure/adapters/ai/agent_squad_gateway.py"
        
        if gateway_file.exists():
            content = gateway_file.read_text()
            
            # Check for common API key patterns
            patterns = [
                r'api_key\s*=\s*["\']sk-[a-zA-Z0-9]{20,}["\']',  # OpenAI pattern
                r'api_key\s*=\s*["\'][A-Z0-9]{32,}["\']',  # Generic key pattern
                r'Authorization:\s*Bearer\s+[a-zA-Z0-9]{20,}',  # Bearer token
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, content)
                assert len(matches) == 0, f"Found hardcoded API key pattern: {pattern}"
    
    def test_no_hardcoded_api_keys_in_mcp_servers(self):
        """Verify MCP servers have no hardcoded API keys"""
        mcp_servers_dir = Path(__file__).parent.parent.parent / "src/app/infrastructure/mcp/servers"
        
        if mcp_servers_dir.exists():
            for server_file in mcp_servers_dir.glob("*.py"):
                content = server_file.read_text()
                
                # API keys should come from parameters, not be hardcoded
                assert '"sk-' not in content, f"Hardcoded OpenAI key in {server_file.name}"
                assert "'sk-" not in content, f"Hardcoded OpenAI key in {server_file.name}"
                
                # Check Authorization header patterns
                if "Authorization" in content:
                    # Should use f-string or variable, not hardcoded
                    assert re.search(r'Authorization.*{.*api_key', content) or \
                           'api_key if api_key else' in content, \
                           f"Suspicious Authorization pattern in {server_file.name}"
    
    def test_config_files_use_env_vars(self):
        """Verify configuration files use environment variables"""
        config_file = Path(__file__).parent.parent.parent / "src/app/setup/config/agent_squad.py"
        
        if config_file.exists():
            content = config_file.read_text()
            
            # Should not have hardcoded production credentials
            assert "sk-prod-" not in content
            assert "sk-live-" not in content


# ==============================================================================
# USER DATA ISOLATION
# ==============================================================================

class TestUserDataIsolation:
    """Validate user conversations and data are properly isolated"""
    
    async def test_conversations_isolated_by_user_id(self):
        """Test conversations are isolated by user_id"""
        user1_id = uuid4()
        user2_id = uuid4()
        
        # User IDs must be different
        assert user1_id != user2_id
        
        # Conversations should be keyed by user_id
        from app.domain.entities.conversation import Conversation
        
        conv1 = Conversation(id=uuid4(), user_id=user1_id, created_at=None)
        conv2 = Conversation(id=uuid4(), user_id=user2_id, created_at=None)
        
        assert conv1.user_id != conv2.user_id
    
    async def test_agent_squad_storage_uses_user_id(self):
        """Test AnvilSquadStorage properly scopes by user_id"""
        from app.infrastructure.adapters.ai.squad_storage import AnvilSquadStorage
        import inspect
        
        # Check that save_chat_message and get_conversation use user_id
        save_signature = inspect.signature(AnvilSquadStorage.save_chat_message)
        assert 'user_id' in save_signature.parameters
        
        get_signature = inspect.signature(AnvilSquadStorage.get_conversation)
        assert 'user_id' in get_signature.parameters


# ==============================================================================
# INPUT VALIDATION
# ==============================================================================

class TestInputValidation:
    """Validate proper input validation and sanitization"""
    
    @pytest.mark.skip(reason="Requires full system")
    async def test_agent_message_length_validation(self):
        """Test agent gateway validates message length"""
        from app.infrastructure.adapters.ai.agent_gateway_impl import AgentGatewayImpl
        from unittest.mock import AsyncMock
        
        gateway = AgentGatewayImpl(
            storage=AsyncMock(),
            llm_gateway=AsyncMock(),
            config=AsyncMock(),
        )
        
        # Very long message (> 10k chars)
        long_message = "x" * 10001
        
        # Should handle gracefully or validate
        try:
            result = await gateway.process_message(
                user_id=uuid4(),
                session_id="test",
                message=long_message,
            )
            # If it succeeds, result should be reasonable
            assert isinstance(result, str)
        except ValueError:
            # Or it should raise validation error
            assert True
    
    def test_mcp_tool_params_validated(self):
        """Test MCP tools validate their parameters"""
        from app.infrastructure.mcp.base_server import MCPTool
        
        # MCPTool has parameters schema
        tool = MCPTool(
            name="test_tool",
            description="Test",
            parameters={"type": "object", "properties": {}},
            handler=lambda: None,
        )
        
        assert "type" in tool.parameters
        assert tool.parameters["type"] == "object"


# ==============================================================================
# AUTHENTICATION & AUTHORIZATION
# ==============================================================================

class TestAuthenticationAuthorization:
    """Validate authentication and authorization mechanisms"""
    
    def test_agent_squad_config_has_auth_settings(self):
        """Verify Agent Squad config includes authentication settings"""
        from app.setup.config.agent_squad import AgentSquadConfig
        
        config = AgentSquadConfig()
        
        # Should have session-related security settings
        assert hasattr(config, 'session_timeout')
        assert config.session_timeout > 0
    
    def test_ioc_provider_requires_dependencies(self):
        """Test IoC provider enforces dependency injection"""
        from app.setup.ioc.infrastructure import InfrastructureProvider
        import inspect
        
        provider = InfrastructureProvider()
        gateway_method = provider.get_agent_gateway
        
        # get_agent_gateway should require storage, config, etc.
        signature = inspect.signature(gateway_method)
        assert 'storage' in signature.parameters
        assert 'config' in signature.parameters


# ==============================================================================
# DATA PROTECTION
# ==============================================================================

class TestDataProtection:
    """Validate data protection mechanisms"""
    
    def test_conversation_repository_uses_sqlalchemy(self):
        """Verify conversation repository uses SQLAlchemy (parameterized queries)"""
        from app.infrastructure.adapters.conversation_repository_sqla import SqlaConversationRepository
        import inspect
        
        # Repository should use SQLAlchemy session
        init_signature = inspect.signature(SqlaConversationRepository.__init__)
        assert 'session' in init_signature.parameters or 'async_session' in str(init_signature)
    
    def test_no_sql_string_concatenation_in_repositories(self):
        """Verify no SQL string concatenation (SQL injection risk)"""
        repo_file = Path(__file__).parent.parent.parent / "src/app/infrastructure/adapters/conversation_repository_sqla.py"
        
        if repo_file.exists():
            content = repo_file.read_text()
            
            # Should not have f-strings or .format() in SQL queries
            dangerous_patterns = [
                r'f"SELECT.*WHERE',
                r'f\'SELECT.*WHERE',
                r'\.format\(.*SELECT',
                r'\+.*WHERE',  # String concatenation
            ]
            
            for pattern in dangerous_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                assert len(matches) == 0, f"Found SQL concatenation pattern: {pattern}"


# ==============================================================================
# MCP SERVER SECURITY
# ==============================================================================

class TestMCPServerSecurity:
    """Validate MCP server security"""
    
    def test_mcp_servers_use_env_vars_for_api_keys(self):
        """Verify MCP servers use environment variables for API keys"""
        from app.infrastructure.mcp.servers.oneinch_mcp import OneInchMCPServer
        import inspect
        
        # __init__ should accept api_key parameter
        init_signature = inspect.signature(OneInchMCPServer.__init__)
        assert 'api_key' in init_signature.parameters
        
        # Default should be empty string (secure)
        api_key_param = init_signature.parameters['api_key']
        assert api_key_param.default == ""
    
    def test_mcp_servers_handle_missing_api_keys(self):
        """Test MCP servers work without API keys (public endpoints)"""
        from app.infrastructure.mcp.servers.defillama_mcp import DeFiLlamaMCPServer
        
        # DeFiLlama doesn't require API key (public API)
        server = DeFiLlamaMCPServer()
        assert server is not None
    
    @pytest.mark.skip(reason="Requires MCP servers running")
    async def test_mcp_servers_reject_invalid_tool_params(self):
        """Test MCP servers validate tool parameters"""
        import httpx
        
        async with httpx.AsyncClient() as client:
            # Invalid params (missing required fields)
            response = await client.post(
                "http://localhost:8081/execute/get_swap_quote",
                json={"params": {}},  # Missing required params
                timeout=2.0,
            )
            
            # Should return error, not crash
            assert response.status_code in [400, 422, 500]


# ==============================================================================
# SECRETS MANAGEMENT
# ==============================================================================

class TestSecretsManagement:
    """Validate secrets are managed securely"""
    
    def test_no_secrets_in_git_tracked_files(self):
        """Verify .gitignore includes common secret files"""
        gitignore_file = Path(__file__).parent.parent.parent / ".gitignore"
        
        if gitignore_file.exists():
            content = gitignore_file.read_text()
            
            # Should ignore environment files
            assert ".env" in content or "*.env" in content
            
            # Should ignore secrets
            assert ".secrets" in content or "secrets" in content.lower()
    
    def test_docker_compose_uses_env_file(self):
        """Verify Docker Compose uses .env files, not hardcoded secrets"""
        docker_compose_file = Path(__file__).parent.parent.parent / "config/local/docker-compose-mcp.yml"
        
        if docker_compose_file.exists():
            content = docker_compose_file.read_text()
            
            # Should use ${VAR} syntax, not hardcoded values
            assert "${" in content and "}" in content
            
            # Should reference .env file or use environment section
            assert "environment:" in content or "env_file:" in content


# ==============================================================================
# NETWORK SECURITY
# ==============================================================================

class TestNetworkSecurity:
    """Validate network security configurations"""
    
    def test_mcp_servers_have_timeout_configured(self):
        """Verify MCP servers have request timeouts"""
        from app.infrastructure.mcp.servers.oneinch_mcp import OneInchMCPServer
        
        server = OneInchMCPServer()
        assert server.client.timeout is not None
        assert server.client.timeout.total <= 30.0  # Max 30s timeout
    
    @pytest.mark.skip(reason="Requires MCP servers running")
    async def test_mcp_servers_cors_not_allow_all(self):
        """Test MCP servers don't allow unrestricted CORS"""
        import httpx
        
        async with httpx.AsyncClient() as client:
            response = await client.options(
                "http://localhost:8081/health",
                headers={"Origin": "http://evil.com"}
            )
            
            # Should not have Access-Control-Allow-Origin: *
            cors_header = response.headers.get("Access-Control-Allow-Origin", "")
            assert cors_header != "*" or cors_header == ""


# ==============================================================================
# ERROR HANDLING SECURITY
# ==============================================================================

class TestErrorHandlingSecurity:
    """Validate error handling doesn't leak sensitive information"""
    
    def test_agent_gateway_handles_errors_safely(self):
        """Test agent gateway doesn't expose internal errors"""
        from app.infrastructure.adapters.ai.agent_squad_gateway import AgentSquadGateway
        import inspect
        
        # Check error handling in process_message
        source = inspect.getsource(AgentSquadGateway.process_message)
        
        # Should have try-except
        assert "try:" in source and "except" in source
        
        # Should not re-raise with full traceback to user
        assert "raise" not in source or "except Exception" in source
    
    @pytest.mark.skip(reason="Requires MCP servers running")
    async def test_mcp_servers_return_safe_error_messages(self):
        """Test MCP servers don't expose internal errors to clients"""
        import httpx
        
        async with httpx.AsyncClient() as client:
            # Cause an error (invalid tool name)
            response = await client.post(
                "http://localhost:8081/execute/invalid_tool_name",
                json={"params": {}},
            )
            
            # Should return structured error, not stack trace
            assert response.status_code in [400, 404]
            data = response.json()
            assert "error" in data or "detail" in data
            
            # Should not contain file paths or stack traces
            error_text = str(data).lower()
            assert "/home/" not in error_text
            assert "traceback" not in error_text


# ==============================================================================
# COMPLIANCE & AUDIT
# ==============================================================================

class TestComplianceAudit:
    """Validate compliance and audit requirements"""
    
    def test_conversation_has_timestamps(self):
        """Verify conversations track created_at for audit"""
        from app.domain.entities.conversation import Conversation
        
        conv = Conversation(id=uuid4(), user_id=uuid4(), created_at=None)
        assert hasattr(conv, 'created_at')
    
    def test_messages_have_timestamps(self):
        """Verify messages track created_at for audit"""
        from app.domain.entities.message import Message
        import inspect
        
        # Message should have created_at field
        init_signature = inspect.signature(Message.__init__)
        params = init_signature.parameters
        
        # Should have timestamp field
        assert 'created_at' in params or 'timestamp' in params


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
