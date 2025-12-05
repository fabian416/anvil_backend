"""
Agent Squad agent implementations.

Core User-Facing Agents (10):
- ChatAgentOpenAI: General conversation
- HunterAIAgentOpenAI: Market sentiment & predictions
- ResearchAgentPerplexity: Deep protocol analysis
- ExecutionAgentPrivy: Transaction execution
- RiskAnalyzerAgentOpenAI: Risk assessment
- PortfolioAgentOpenAI: Portfolio optimization
- TaxOptimizerAgentOpenAI: Tax strategies
- DefiYieldAgentOpenAI: Yield farming
- SecurityAuditorAgentSlither: Contract security
- GasOptimizerAgentOpenAI: Gas optimization

All implement AgentGateway interface.
"""

from .chat_agent_openai import ChatAgentOpenAI
from .hunter_ai_agent_openai import HunterAIAgentOpenAI
from .research_agent_perplexity import ResearchAgentPerplexity
from .execution_agent_privy import ExecutionAgentPrivy
from .risk_analyzer_agent_openai import RiskAnalyzerAgentOpenAI
from .portfolio_agent_openai import PortfolioAgentOpenAI
from .tax_optimizer_agent_openai import TaxOptimizerAgentOpenAI
from .defi_yield_agent_openai import DefiYieldAgentOpenAI
from .security_auditor_agent_slither import SecurityAuditorAgentSlither
from .gas_optimizer_agent_openai import GasOptimizerAgentOpenAI

__all__ = [
    "ChatAgentOpenAI",
    "HunterAIAgentOpenAI",
    "ResearchAgentPerplexity",
    "ExecutionAgentPrivy",
    "RiskAnalyzerAgentOpenAI",
    "PortfolioAgentOpenAI",
    "TaxOptimizerAgentOpenAI",
    "DefiYieldAgentOpenAI",
    "SecurityAuditorAgentSlither",
    "GasOptimizerAgentOpenAI",
]
