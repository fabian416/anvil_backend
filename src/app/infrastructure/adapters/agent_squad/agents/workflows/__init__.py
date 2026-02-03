"""
AGNO-based Multi-Step Workflow Agents.

This module provides workflow agents for authenticated users that handle
multi-step DeFi operations with stateful conversation memory.

Workflow Agents:
- SwapWorkflowAgent: Token swaps via 1inch/LiFi
- LendingWorkflowAgent: Deposits via Morpho/Aave (planned)
- BuyWorkflowAgent: Fiat on-ramp (planned)
- TransferWorkflowAgent: Token transfers (planned)
- MoneyMarketWorkflowAgent: Compare & select protocols (planned)

Architecture:
- Each workflow agent extends BaseWorkflowAgent
- Workflow state is maintained in conversation context
- execute_data is generated for frontend execution modal
- Integrates with AuthenticatedSupervisorCoordinator
"""

from .base_workflow_agent import (
    BaseWorkflowAgent,
    WorkflowState,
    WorkflowStep,
    UserContext,
)
from .swap_workflow_agent import SwapWorkflowAgent
from .lending_workflow_agent import LendingWorkflowAgent
from .transfer_workflow_agent import TransferWorkflowAgent
from .buy_workflow_agent import BuyWorkflowAgent
from .money_market_workflow_agent import MoneyMarketWorkflowAgent

__all__ = [
    "BaseWorkflowAgent",
    "WorkflowState",
    "WorkflowStep",
    "UserContext",
    "SwapWorkflowAgent",
    "LendingWorkflowAgent",
    "TransferWorkflowAgent",
    "BuyWorkflowAgent",
    "MoneyMarketWorkflowAgent",
]
