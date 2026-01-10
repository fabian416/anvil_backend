import ssl
import time
import aiohttp
import orjson
from typing import List, Dict, Any, Tuple
from app.infrastructure.adapters.ai.llm.strategy import LLMStrategy

class DeepInfraStrategy(LLMStrategy):
    """
    Adapter for DeepInfra API.
    """
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.deepinfra.com/v1/openai"

    async def generate(
        self, 
        model_name: str, 
        messages: List[Dict[str, str]], 
        **kwargs
    ) -> Tuple[str, Dict[str, Any]]:
        
        start_time = time.time()
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model_name,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 1024),
            "stream": False
        }

        # Configure timeout and SSL
        timeout = aiohttp.ClientTimeout(total=60)  # 60 second timeout for LLM calls
        # Create SSL context that doesn't verify certificates (for development)
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        
        async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
            async with session.post(
                f"{self.base_url}/chat/completions", 
                headers=headers, 
                json=payload
            ) as response:
                if response.status != 200:
                    text = await response.text()
                    raise Exception(f"DeepInfra Error {response.status}: {text}")
                
                data = await response.json()
                
        end_time = time.time()
        latency_ms = int((end_time - start_time) * 1000)
        
        response_text = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        
        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)
        
        # Approximate cost calculation (DeepInfra prices vary, simplified here)
        # Typical Llama3 70B: $0.59/1M in, $0.79/1M out
        cost = (input_tokens * 0.59 + output_tokens * 0.79) / 1_000_000
        
        metadata = {
            "provider": "deepinfra",
            "model": model_name,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "latency_ms": latency_ms,
            "cost_usd": cost
        }
        
        return response_text, metadata
