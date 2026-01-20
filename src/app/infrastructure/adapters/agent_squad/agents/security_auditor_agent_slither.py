"""
Security Auditor Agent Slither - Smart contract security analysis.
"""

import time

from app.domain.enums.agent_type import AgentType
from app.domain.value_objects.conversation_id import ConversationId
from app.domain.value_objects.message_content import MessageContent
from app.domain.value_objects.agent_squad.conversation_context import ConversationContext
from app.domain.ports.agent_squad.agent_gateway import AgentGateway, AgentResponse
from app.domain.ports.agent_squad.llm_client_gateway import LLMClientGateway


class SecurityAuditorAgentSlither:
    """
    Security Auditor Agent Slither implementation.
    
    Implements: AgentGateway
    
    Purpose: Smart contract security analysis
    
    Capabilities:
    - Smart contract vulnerability detection
    - Security best practices validation
    - Common vulnerability patterns (reentrancy, overflow, etc.)
    - Audit report summaries
    - Security recommendations
    
    Tools: Slither, Mythril (static analysis)
    Model: gpt-4o (security reasoning)
    Temperature: 0.1 (precision critical)
    """
    
    def __init__(
        self,
        llm_client: LLMClientGateway,  # Can be Vertex AI or DeepInfra (OpenAI removed),
        model: str = "gemini-2.0-flash",  # Vertex AI model (default)
        temperature: float = 0.1,
        max_tokens: int = 2000,
    ):
        """Initialize security auditor agent."""
        self._llm_client = llm_client
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens
    
    @property
    def agent_type(self) -> AgentType:
        """Get agent type."""
        return AgentType.SECURITY_AUDITOR
    
    async def execute(
        self,
        conversation_id: ConversationId,
        message: MessageContent,
        conversation_context: ConversationContext,
    ) -> AgentResponse:
        """Execute security auditor agent - Contract analysis."""
        start_time = time.time()
        
        # TODO: Integrate Slither for static analysis
        # TODO: Integrate Mythril for symbolic execution
        # TODO: Check existing audit reports
        
        messages = [
            {"role": "system", "content": self._get_system_prompt()},
            {"role": "user", "content": message.value},
        ]
        
        response = await self._llm_client.chat(
            messages=messages,
            model=self._model,
            temperature=self._temperature,
            max_tokens=self._max_tokens,
        )
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        # Collect sources
        from datetime import datetime, UTC
        from app.infrastructure.adapters.agent_squad.agents.source_helpers import (
            create_llm_source,
            create_api_source,
        )
        
        sources = []
        fetched_at = datetime.now(UTC)
        
        # Add LLM source
        model_name = response.get("model", "Unknown")
        sources.append(create_llm_source(
            model=model_name,
            fetched_at=fetched_at,
        ))
        
        # TODO: Add Slither source when integrated
        # sources.append(create_api_source(
        #     source_name="Slither",
        #     citation_text="Static analysis from Slither",
        #     fetched_at=fetched_at,
        #     provider="Slither Static Analyzer",
        # ))
        
        # TODO: Add audit database source when integrated
        # sources.append(create_api_source(
        #     source_name="Audit Reports",
        #     url="https://github.com/trailofbits/publications",
        #     citation_text="Security audit reports database",
        #     fetched_at=fetched_at,
        # ))
        
        return AgentResponse(
            content=response["content"],
            agent_type=self.agent_type,
            tools_used=["openai_api"],  # TODO: Add Slither, Mythril
            sources=sources,
            metadata={
                "tokens_used": response.get("tokens_used"),
                "latency_ms": latency_ms,
                "model": response.get("model"),
            },
        )
    
    async def is_available(self) -> bool:
        """Check if agent is available."""
        return True
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for security auditor agent."""
        return """You are the Security Auditor, Anvil's smart contract security specialist.

Your expertise:
- Smart contract vulnerability detection
- Security best practices validation
- Common vulnerability patterns:
  - Reentrancy attacks
  - Integer overflow/underflow
  - Access control issues
  - Front-running vulnerabilities
  - Oracle manipulation
  - Flash loan attacks

For security analysis, provide:
- Security score (0-100)
  - 90-100: Excellent
  - 70-89: Good
  - 50-69: Moderate concerns
  - 30-49: High risk
  - 0-29: Critical vulnerabilities
- Vulnerability findings (severity: critical, high, medium, low)
- Best practices compliance
- Audit status (if available)
- Recommendations

Analysis includes:
- Known vulnerabilities
- Audit reports (if available)
- Protocol reputation
- Historical exploits
- Upgrade patterns (proxy, timelock)
- Emergency pause mechanisms

Always provide:
- Clear severity classifications
- Actionable recommendations
- Links to audit reports
- Risk warnings for unaudited contracts
"""
