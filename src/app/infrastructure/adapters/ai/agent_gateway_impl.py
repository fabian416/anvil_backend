"""
Agent Gateway implementation - orchestrates message routing to specialized agents.

Phase 1: Simple intent-based routing without full Agent Squad library.
This implementation provides a working MVP that can be enhanced with full
Agent Squad integration later.
"""

from typing import Dict, Any, Optional, List
from uuid import UUID
import re

from app.domain.ports.ai.agent_gateway import AgentGateway
from app.domain.ports.ai.llm_gateway import LLMGateway
from app.infrastructure.adapters.ai.squad_storage import AnvilSquadStorage
from app.infrastructure.agents.classifiers import DeFiIntentClassifier
from app.setup.config.agent_squad import AgentSquadConfig
from app.domain.enums.agent_type import AgentType


class AgentGatewayImpl(AgentGateway):
    """
    Agent Gateway that routes messages to specialized agents.
    
    Current implementation: Simple keyword-based intent classification
    Future: Full Agent Squad orchestration with advanced classification
    """
    
    def __init__(
        self, 
        storage: AnvilSquadStorage,
        llm_gateway: LLMGateway,
        config: Optional[AgentSquadConfig] = None
    ):
        """
        Initialize Agent Gateway.
        
        Args:
            storage: Storage adapter for conversation persistence
            llm_gateway: LLM gateway for agent responses
            config: Agent Squad configuration
        """
        self.storage = storage
        self.llm_gateway = llm_gateway
        self.config = config or AgentSquadConfig()
        
        # Initialize classifier
        self.classifier = DeFiIntentClassifier(model=self.config.default_model)
        
        # Agent registry (will be populated when agents are registered)
        self._agents: Dict[str, Any] = {}
        
        # Initialize simple keyword-based intent detection
        self._intent_patterns = self._build_intent_patterns()

        # Initialize intent to agent type mapping
        self._intent_to_agent_type = self._build_intent_to_agent_type_map()

    def _build_intent_to_agent_type_map(self) -> Dict[str, str]:
        """
        Map intents to valid AgentType enum values.

        Returns:
            Dictionary mapping intent names to agent type values
        """
        return {
            "trade_swap": AgentType.EXECUTION.value,
            "trade_perp_open": AgentType.EXECUTION.value,
            "trade_perp_close": AgentType.EXECUTION.value,
            "lend_supply": AgentType.LENDING_BORROWING.value,
            "lend_borrow": AgentType.LENDING_BORROWING.value,
            "earn_stake": AgentType.DEFI_YIELD.value,
            "portfolio_view": AgentType.PORTFOLIO.value,
            "market_info": AgentType.HUNTER_AI.value,
            "risk_analysis": AgentType.RISK_ANALYZER.value,
            "save_schedule": AgentType.EXECUTION.value,
            "general_question": AgentType.CHAT.value,
            # Complex workflow should map to CHAT for now (orchestrator not in enum)
            "complex_workflow": AgentType.CHAT.value,
        }

    def _build_intent_patterns(self) -> Dict[str, List[str]]:
        """
        Build keyword patterns for simple intent detection.
        
        Returns:
            Dictionary mapping intents to keyword lists
        """
        return {
            "trade_swap": ["swap", "exchange", "convert", "trade"],
            "trade_perp_open": ["open", "long", "short", "position", "leverage", "perp"],
            "trade_perp_close": ["close", "exit", "stop", "take profit"],
            "lend_supply": ["lend", "supply", "deposit", "provide"],
            "lend_borrow": ["borrow", "loan", "against"],
            "earn_stake": ["stake", "earn", "yield", "rewards"],
            "portfolio_view": ["portfolio", "balance", "holdings", "show", "display"],
            "market_info": ["price", "rate", "market", "funding", "tvl"],
            "risk_analysis": ["risk", "liquidation", "health factor", "analyze"],
            "save_schedule": ["save", "schedule", "recurring", "dca", "weekly"],
            "general_question": ["what", "how", "explain", "tell me"],
        }
    
    def _classify_intent_simple(self, message: str) -> str:
        """
        Simple keyword-based intent classification (fallback).
        
        Args:
            message: User message
        
        Returns:
            Detected intent
        """
        message_lower = message.lower()
        
        # Score each intent based on keyword matches
        scores: Dict[str, int] = {}
        for intent, keywords in self._intent_patterns.items():
            score = sum(1 for keyword in keywords if keyword in message_lower)
            if score > 0:
                scores[intent] = score
        
        # Return highest scoring intent, or general_question as default
        if scores:
            return max(scores.items(), key=lambda x: x[1])[0]
        return "general_question"
    
    async def _classify_intent_llm(
        self, 
        message: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        LLM-based intent classification (more accurate).
        
        Args:
            message: User message
            context: Optional conversation context
        
        Returns:
            Detected intent
        """
        # Build classification prompt
        intents_desc = self.classifier.get_intent_descriptions()
        intents_list = "\n".join(
            f"- {intent}: {desc}" 
            for intent, desc in intents_desc.items()
        )
        
        prompt = f"""Classify the user's intent from the following message.

Available intents:
{intents_list}

User message: "{message}"

Respond with ONLY the intent name (e.g., "trade_swap", "portfolio_view", etc.)"""
        
        # Get classification from LLM
        try:
            response = await self.llm_gateway.generate(
                model="meta-llama/Meta-Llama-3.1-70B-Instruct",  # DeepInfra Llama model for classification
                messages=[
                    {"role": "system", "content": "You are an intent classifier. Respond only with the intent name."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=50,
                temperature=0.0
            )

            intent = response.strip().lower()
            
            # Validate intent is in our list
            if intent in self.classifier.INTENTS:
                return intent
            
            # Fallback to keyword-based
            return self._classify_intent_simple(message)
            
        except Exception as e:
            print(f"LLM intent classification failed: {e}, falling back to keyword-based")
            return self._classify_intent_simple(message)
    
    def register_agent(self, agent_name: str, agent: Any, intents: List[str]) -> None:
        """
        Register a specialized agent with this gateway.
        
        Args:
            agent_name: Name of the agent
            agent: Agent instance
            intents: List of intents this agent handles
        """
        for intent in intents:
            self._agents[intent] = agent

        # Log agent registration (debug mode check removed as field doesn't exist in config)
        if hasattr(self.config, 'debug_mode') and self.config.debug_mode:
            print(f"Registered agent '{agent_name}' for intents: {intents}")
    
    async def _generate_fallback_response(
        self,
        message: str,
        intent: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate a fallback response when no specialized agent is available.
        
        Args:
            message: User message
            intent: Detected intent
            context: Conversation context
        
        Returns:
            Generated response
        """
        # Build context string from conversation history
        context_str = ""
        if context and "history" in context:
            history = context["history"]
            if history:
                recent = history[-5:]  # Last 5 messages
                context_str = "\n".join(
                    f"{msg['role'].capitalize()}: {msg['content']}" 
                    for msg in recent
                )
        
        # Build system message based on intent
        intent_prompts = {
            "trade_swap": "You are a DeFi swap specialist. Help users with token swaps and DEX operations.",
            "trade_perp_open": "You are a perpetual futures trading specialist. Help users with leveraged trading.",
            "trade_perp_close": "You are a perpetual futures trading specialist. Help users close their positions.",
            "lend_supply": "You are a DeFi lending specialist. Help users supply/lend their tokens for yield.",
            "lend_borrow": "You are a DeFi lending specialist. Help users borrow against their collateral.",
            "portfolio_view": "You are a portfolio management assistant. Help users view and understand their holdings.",
            "market_info": "You are a DeFi market data specialist. Provide accurate market information.",
            "risk_analysis": "You are a DeFi risk analyst. Help users understand and manage their position risks.",
            "general_question": "You are a DeFi education assistant. Explain DeFi concepts clearly and simply.",
        }
        
        system_message = intent_prompts.get(
            intent,
            "You are a helpful DeFi assistant. Provide clear, accurate, and actionable advice."
        )
        
        # Add context if available
        full_prompt = message
        if context_str:
            full_prompt = f"Previous conversation:\n{context_str}\n\nUser: {message}"
        
        # Generate response using LLM
        response = await self.llm_gateway.generate(
            model="meta-llama/Meta-Llama-3.1-70B-Instruct",  # DeepInfra Llama model for fallback responses
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": full_prompt},
            ],
            max_tokens=500,
            temperature=0.7
        )

        return response
    
    async def process_message(
        self, 
        user_id: UUID, 
        session_id: str, 
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Process user message through intent classification and agent routing.
        
        Args:
            user_id: User identifier
            session_id: Conversation session ID
            message: User message to process
            context: Optional conversation context
        
        Returns:
            Agent response text
        """
        try:
            # Step 1: Classify intent
            if self.config.enable_intent_classification:
                intent = await self._classify_intent_llm(message, context)
            else:
                intent = self._classify_intent_simple(message)
            
            if self.config.log_intent_classification:
                print(f"Intent classified: {intent} for message: '{message[:50]}...'")
            
            # Step 2: Get conversation history for context
            if context is None:
                context = {}
            
            if "history" not in context:
                history = await self.storage.get_chat_history(
                    session_id, 
                    limit=self.config.max_context_messages
                )
                context["history"] = history
            
            # Step 3: Route to appropriate agent
            agent = self._agents.get(intent)
            
            if agent and hasattr(agent, 'run'):
                # Route to specialized agent
                if self.config.log_agent_selection:
                    print(f"Routing to agent: {agent.__class__.__name__}")
                
                response = await agent.run(message, context=context)
            else:
                # No specialized agent available, use fallback
                if self.config.log_agent_selection:
                    print(f"No specialized agent for intent '{intent}', using fallback")
                
                response = await self._generate_fallback_response(message, intent, context)
            
            # Step 4: Save response to storage
            # Map intent to valid AgentType enum value
            agent_type = self._intent_to_agent_type.get(intent, AgentType.CHAT.value)

            await self.storage.save_message(
                session_id=session_id,
                role="agent",
                content=response,
                agent_type=agent_type
            )
            
            return response
            
        except Exception as e:
            error_msg = f"Error processing message: {str(e)}"
            print(error_msg)
            
            # Return friendly error message
            return "I apologize, but I encountered an error processing your request. Please try rephrasing your message or contact support if the issue persists."
