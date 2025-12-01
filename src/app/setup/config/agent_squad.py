"""
Agent Squad configuration.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class AgentSquadConfig:
    """Configuration for Agent Squad orchestrator"""
    
    # Model configuration
    default_model: str = "gpt-4-turbo"
    fallback_model: str = "gpt-3.5-turbo"
    
    # Intent classification
    intent_threshold: float = 0.75  # Confidence threshold for intent classification
    
    # Session management
    session_timeout: int = 3600  # 1 hour in seconds
    max_context_messages: int = 20  # Max messages to keep in context
    
    # Performance settings
    max_retries: int = 3
    timeout_seconds: int = 30
    
    # Feature flags
    enable_intent_classification: bool = True
    enable_context_memory: bool = True
    enable_multi_agent_routing: bool = True
    
    # Debug settings
    debug_mode: bool = False
    log_intent_classification: bool = True
    log_agent_selection: bool = True


def load_agent_squad_config(
    default_model: Optional[str] = None,
    fallback_model: Optional[str] = None,
    intent_threshold: Optional[float] = None,
    session_timeout: Optional[int] = None,
    debug_mode: Optional[bool] = None
) -> AgentSquadConfig:
    """
    Load Agent Squad configuration with optional overrides.
    
    Args:
        default_model: Override default model
        fallback_model: Override fallback model
        intent_threshold: Override intent threshold
        session_timeout: Override session timeout
        debug_mode: Override debug mode
    
    Returns:
        AgentSquadConfig instance
    """
    config = AgentSquadConfig()
    
    if default_model is not None:
        config.default_model = default_model
    if fallback_model is not None:
        config.fallback_model = fallback_model
    if intent_threshold is not None:
        config.intent_threshold = intent_threshold
    if session_timeout is not None:
        config.session_timeout = session_timeout
    if debug_mode is not None:
        config.debug_mode = debug_mode
    
    return config
