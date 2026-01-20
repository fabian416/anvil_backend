"""
Agent Squad agent implementations.

Core User-Facing Agents (11):
- ChatAgent: General conversation
- GuestAuthAgent: Authentication requirements for restricted features
- HunterAIAgent: Market sentiment & predictions
- ResearchAgentPerplexity: Deep protocol analysis
- ExecutionAgentPrivy: Transaction execution
- RiskAnalyzerAgent: Risk assessment
- PortfolioAgent: Portfolio optimization
- TaxOptimizerAgent: Tax strategies
- DefiYieldAgent: Yield farming
- SecurityAuditorAgentSlither: Contract security
- GasOptimizerAgent: Gas optimization

All implement AgentGateway interface.
"""

from .chat_agent import ChatAgent
from .guest_auth_agent import GuestAuthAgent
from .knowledge_agent import KnowledgeAgent
from .hunter_ai_agent import HunterAIAgent
from .research_agent_perplexity import ResearchAgentPerplexity
from .execution_agent_privy import ExecutionAgentPrivy
from .risk_analyzer_agent import RiskAnalyzerAgent
from .portfolio_agent import PortfolioAgent
from .tax_optimizer_agent import TaxOptimizerAgent
from .defi_yield_agent import DefiYieldAgent
from .security_auditor_agent_slither import SecurityAuditorAgentSlither
from .gas_optimizer_agent import GasOptimizerAgent

__all__ = [
    "ChatAgent",
    "GuestAuthAgent",
    "KnowledgeAgent",
    "HunterAIAgent",
    "ResearchAgentPerplexity",
    "ExecutionAgentPrivy",
    "RiskAnalyzerAgent",
    "PortfolioAgent",
    "TaxOptimizerAgent",
    "DefiYieldAgent",
    "SecurityAuditorAgentSlither",
    "GasOptimizerAgent",
]
