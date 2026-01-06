"""
Agent LLM Gateway - Bridges LLMGateway to Agent Squad interface.

This adapter allows agents to use the unified LLMGateway while maintaining
the dict-based response format they expect from LLMClientGateway.

Migration Path:
1. Agents currently use: LLMClientGateway.chat() → dict
2. Unified interface: LLMGateway.generate() → str
3. This adapter: LLMGateway → dict format expected by agents
"""

import time
from typing import Optional

from app.domain.ports.ai.llm_gateway import LLMGateway


class AgentLLMGateway:
    """
    Wrapper that adapts LLMGateway for use by Agent Squad agents.
    
    Provides the same interface as LLMClientGateway but uses the
    unified LLMGateway implementation under the hood.
    """

    def __init__(self, llm_gateway: LLMGateway):
        """
        Initialize with unified LLM gateway.
        
        Args:
            llm_gateway: The unified LLM gateway to delegate to
        """
        self._llm = llm_gateway

    async def chat(
        self,
        messages: list[dict],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> dict:
        """
        Chat completion with dict response format.
        
        Wraps LLMGateway.generate_with_metadata() to provide the response
        format expected by agents: {"content": str, "tokens_used": int, ...}
        
        Args:
            messages: Conversation messages
            model: Model to use
            temperature: Sampling temperature
            max_tokens: Maximum response tokens
            
        Returns:
            dict with content, tokens_used, model, finish_reason
        """
        start_time = time.time()
        
        try:
            # Use generate_with_metadata for full response info
            content, metadata = await self._llm.generate_with_metadata(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            return {
                "content": content,
                "role": "assistant",
                "tokens_used": metadata.get("tokens_used", len(content.split()) * 2),
                "model": metadata.get("model", model),
                "finish_reason": metadata.get("finish_reason", "stop"),
                "latency_ms": latency_ms,
            }
            
        except Exception:
            # Fallback to simple generate if metadata not available
            content = await self._llm.generate(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            return {
                "content": content,
                "role": "assistant",
                "tokens_used": len(content.split()) * 2,  # Rough estimate
                "model": model,
                "finish_reason": "stop",
                "latency_ms": latency_ms,
            }

    async def generate(
        self,
        model: str,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> str:
        """
        Generate text completion (direct passthrough).
        
        Args:
            model: Model to use
            messages: Conversation messages
            temperature: Sampling temperature
            max_tokens: Maximum response tokens
            
        Returns:
            Generated text response
        """
        return await self._llm.generate(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    async def classify_intent(
        self,
        prompt: str,
        model: str,
    ) -> dict:
        """
        Classify intent using LLM.
        
        Translates to generate() call with classification prompt.
        """
        import json
        import re
        
        messages = [
            {
                "role": "system",
                "content": """You are an intent classifier. Analyze the prompt and classify the intent.
Return JSON: {"intent": "...", "confidence": 0.0-1.0, "reasoning": "..."}""",
            },
            {"role": "user", "content": prompt},
        ]

        response = await self._llm.generate(
            model=model,
            messages=messages,
            temperature=0.1,
            max_tokens=300,
        )

        return self._parse_json_response(response, {
            "intent": "unknown",
            "confidence": 0.5,
            "reasoning": response,
        })

    async def recommend_agents(
        self,
        prompt: str,
        model: str,
    ) -> dict:
        """
        Recommend agents for complex task.
        """
        import json
        import re
        
        messages = [
            {
                "role": "system",
                "content": """You are an agent recommender. Analyze the task and recommend the best agents.
Return JSON: {"agents": ["agent1", "agent2"], "reasoning": "..."}""",
            },
            {"role": "user", "content": prompt},
        ]

        response = await self._llm.generate(
            model=model,
            messages=messages,
            temperature=0.3,
            max_tokens=500,
        )

        return self._parse_json_response(response, {
            "agents": [],
            "reasoning": response,
        })

    async def plan_workflow(
        self,
        prompt: str,
        max_agents: int,
    ) -> dict:
        """
        Plan multi-agent workflow.
        """
        import json
        import re
        
        messages = [
            {
                "role": "system",
                "content": f"""You are a workflow planner. Create a plan with up to {max_agents} agents.
Return JSON: {{"tasks": [{{"agent": "...", "task": "...", "order": 1}}]}}""",
            },
            {"role": "user", "content": prompt},
        ]

        response = await self._llm.generate(
            model="gemini-2.0-flash-exp",
            messages=messages,
            temperature=0.3,
            max_tokens=800,
        )

        return self._parse_json_response(response, {"tasks": []})

    def _parse_json_response(self, response: str, default: dict) -> dict:
        """Parse JSON from LLM response with fallback."""
        import json
        import re
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(0))
                except json.JSONDecodeError:
                    pass
            return default
