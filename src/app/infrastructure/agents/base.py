from typing import List, Optional
# from agno.agent import Agent
# from agno.models.openai import OpenAIChat

class AnvilAgent:
    """
    Base wrapper for Agno Agents to integrate with our Anvil Infrastructure.
    """
    def __init__(self, name: str, model_id: str, tools: List[Any] = None):
        self.name = name
        # self.agent = Agent(
        #     name=name,
        #     model=OpenAIChat(id=model_id),
        #     tools=tools or [],
        #     markdown=True
        # )
        
    async def run(self, prompt: str) -> str:
        # return self.agent.run(prompt)
        return f"[{self.name}] Mock Response: {prompt}"
