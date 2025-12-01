"""
Agent factory for creating and registering specialized DeFi agents.
"""

from typing import Dict, List
import logging

from app.infrastructure.agents.base_defi_agent import BaseDeFiAgent
from app.infrastructure.agents.swap_agent import create_swap_agent
from app.infrastructure.agents.trading_agent import create_trading_agent
from app.infrastructure.agents.portfolio_agent import create_portfolio_agent


logger = logging.getLogger(__name__)


class AgentFactory:
    """
    Factory for creating and managing DeFi agents.
    
    Responsibilities:
    - Create specialized agent instances
    - Register agents with Agent Gateway
    - Maintain agent registry
    - Provide agent lookup by intent
    """
    
    def __init__(self, model: str = "gpt-4-turbo"):
        """
        Initialize agent factory.
        
        Args:
            model: Default LLM model for agents
        """
        self.model = model
        self._agents: Dict[str, BaseDeFiAgent] = {}
        self._intent_to_agent: Dict[str, str] = {}
    
    def create_all_agents(self) -> Dict[str, BaseDeFiAgent]:
        """
        Create all available specialized agents.
        
        Returns:
            Dictionary mapping agent names to agent instances
        """
        logger.info("Creating all specialized DeFi agents...")
        
        # Create agents
        agents = {
            "SwapAgent": create_swap_agent(self.model),
            "TradingAgent": create_trading_agent(self.model),
            "PortfolioAgent": create_portfolio_agent(self.model),
        }
        
        # Store in registry
        self._agents = agents
        
        # Build intent mapping
        for agent_name, agent in agents.items():
            for intent in agent.get_intent_types():
                self._intent_to_agent[intent] = agent_name
                logger.info(f"Mapped intent '{intent}' -> {agent_name}")
        
        logger.info(f"Created {len(agents)} specialized agents")
        
        return agents
    
    def get_agent(self, agent_name: str) -> BaseDeFiAgent:
        """
        Get agent by name.
        
        Args:
            agent_name: Name of agent to retrieve
        
        Returns:
            Agent instance
        
        Raises:
            KeyError: If agent not found
        """
        if agent_name not in self._agents:
            raise KeyError(f"Agent '{agent_name}' not found")
        
        return self._agents[agent_name]
    
    def get_agent_for_intent(self, intent: str) -> BaseDeFiAgent:
        """
        Get agent that handles a specific intent.
        
        Args:
            intent: Intent type
        
        Returns:
            Agent instance
        
        Raises:
            KeyError: If no agent handles the intent
        """
        if intent not in self._intent_to_agent:
            raise KeyError(f"No agent registered for intent '{intent}'")
        
        agent_name = self._intent_to_agent[intent]
        return self.get_agent(agent_name)
    
    def get_all_agents(self) -> Dict[str, BaseDeFiAgent]:
        """
        Get all registered agents.
        
        Returns:
            Dictionary of all agents
        """
        return self._agents.copy()
    
    def get_intent_mapping(self) -> Dict[str, str]:
        """
        Get intent to agent name mapping.
        
        Returns:
            Dictionary mapping intents to agent names
        """
        return self._intent_to_agent.copy()
    
    def register_with_gateway(self, gateway) -> None:
        """
        Register all agents with the Agent Gateway.
        
        Args:
            gateway: AgentGatewayImpl instance
        """
        logger.info("Registering agents with Agent Gateway...")
        
        for agent_name, agent in self._agents.items():
            intents = agent.get_intent_types()
            gateway.register_agent(agent_name, agent, intents)
            logger.info(f"Registered {agent_name} for intents: {intents}")
        
        logger.info(f"Successfully registered {len(self._agents)} agents with gateway")


def create_agent_factory(model: str = "gpt-4-turbo") -> AgentFactory:
    """
    Create and initialize agent factory with all agents.
    
    Args:
        model: Default LLM model for agents
    
    Returns:
        AgentFactory instance with all agents created
    """
    factory = AgentFactory(model=model)
    factory.create_all_agents()
    return factory
