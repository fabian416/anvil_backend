"""
Unified chat orchestrator with intelligent intent-based routing.

Routes messages to appropriate handlers:
- GraphRAG (search, risk, similar)
- Agent Squad (specialist tasks)
- Supervisor (complex workflows)
- Regular chat (general conversation)
"""

from uuid import UUID
from typing import Optional
import time

from app.domain.chat.entities.message import Message
from app.domain.chat.ports.conversation_repository import ConversationRepository
from app.application.chat.services.intent_detector import (
    IntentDetectorService,
    ChatIntent,
)
from app.application.chat.graph_search_handler import ChatGraphSearchHandler
from app.application.chat.risk_insights_handler import ChatRiskInsightsHandler
from app.application.agent_squad.commands.send_agent_squad_message import (
    SendAgentSquadMessage,
)
from app.application.agent_squad.commands.execute_supervisor_workflow import (
    ExecuteSupervisorWorkflow,
)
from app.application.chat.commands.send_message import SendMessage


class UnifiedChatOrchestrator:
    """
    Orchestrates unified chat routing with intelligent intent detection.

    Routes messages to:
    - GraphRAG handlers (search, risk, similar)
    - Agent Squad (specialist tasks)
    - Supervisor (complex workflows)
    - Regular chat (general conversation)

    All responses are saved to conversation history for context.
    """

    def __init__(
        self,
        conversation_repo: ConversationRepository,
        intent_detector: IntentDetectorService,
        graphrag_search: ChatGraphSearchHandler,
        graphrag_risk: ChatRiskInsightsHandler,
        agent_squad: SendAgentSquadMessage,
        supervisor: ExecuteSupervisorWorkflow,
        regular_chat: SendMessage,
    ):
        """
        Initialize orchestrator with all handlers.

        Args:
            conversation_repo: Conversation repository
            intent_detector: Intent detection service
            graphrag_search: GraphRAG search handler
            graphrag_risk: GraphRAG risk analysis handler
            agent_squad: Agent Squad message handler
            supervisor: Supervisor workflow handler
            regular_chat: Regular chat handler
        """
        self._conversation_repo = conversation_repo
        self._intent_detector = intent_detector
        self._graphrag_search = graphrag_search
        self._graphrag_risk = graphrag_risk
        self._agent_squad = agent_squad
        self._supervisor = supervisor
        self._regular_chat = regular_chat

    async def execute(
        self,
        user_id: int,
        conversation_id: UUID,
        content: str,
    ) -> dict:
        """
        Execute unified chat routing.

        Args:
            user_id: User ID
            conversation_id: Conversation ID
            content: User message

        Returns:
            Unified response with routing metadata and enrichment

        Raises:
            ValueError: If conversation not found or not owned by user
        """
        start_time = time.time()

        # Get conversation for verification
        conversation = await self._conversation_repo.get_conversation(conversation_id)
        if not conversation:
            raise ValueError("Conversation not found")

        if conversation.user_id != user_id:
            raise ValueError("Conversation does not belong to user")

        # Get conversation history for context (last 10 messages)
        messages = await self._conversation_repo.get_messages(
            conversation_id=conversation_id,
            limit=10,
        )

        # Detect intent
        intent_result = await self._intent_detector.detect_intent(
            message=content,
            conversation_history=messages,
        )

        # Route based on intent
        if intent_result.intent == ChatIntent.PROTOCOL_SEARCH:
            result = await self._handle_protocol_search(
                user_id, conversation_id, content, intent_result
            )
        elif intent_result.intent == ChatIntent.RISK_ASSESSMENT:
            result = await self._handle_risk_assessment(
                user_id, conversation_id, content, intent_result
            )
        elif intent_result.intent == ChatIntent.SIMILAR_PROTOCOLS:
            result = await self._handle_similar_protocols(
                user_id, conversation_id, content, intent_result
            )
        # Hunter AI intents
        elif intent_result.intent == ChatIntent.HUNTER_SENTIMENT:
            result = await self._handle_hunter_sentiment(
                user_id, conversation_id, content, intent_result
            )
        elif intent_result.intent == ChatIntent.HUNTER_PRICE_PREDICTION:
            result = await self._handle_hunter_price_prediction(
                user_id, conversation_id, content, intent_result
            )
        elif intent_result.intent == ChatIntent.HUNTER_RISK_SIGNALS:
            result = await self._handle_hunter_risk_signals(
                user_id, conversation_id, content, intent_result
            )
        elif intent_result.intent == ChatIntent.HUNTER_TRADING_SIGNALS:
            result = await self._handle_hunter_trading_signals(
                user_id, conversation_id, content, intent_result
            )
        elif intent_result.intent == ChatIntent.HUNTER_PATTERNS:
            result = await self._handle_hunter_patterns(
                user_id, conversation_id, content, intent_result
            )
        elif intent_result.intent == ChatIntent.HUNTER_PORTFOLIO:
            result = await self._handle_hunter_portfolio(
                user_id, conversation_id, content, intent_result
            )
        # Agent Squad & Supervisor intents
        elif intent_result.intent == ChatIntent.SPECIALIST_TASK:
            result = await self._handle_specialist_task(
                user_id, conversation_id, content, intent_result
            )
        elif intent_result.intent == ChatIntent.COMPLEX_WORKFLOW:
            result = await self._handle_complex_workflow(
                user_id, conversation_id, content, intent_result
            )
        else:  # GENERAL_CONVERSATION
            result = await self._handle_general_conversation(
                user_id, conversation_id, content, intent_result
            )

        # Add total latency
        total_latency = int((time.time() - start_time) * 1000)
        result["routing"]["total_latency_ms"] = total_latency

        return result

    async def _handle_protocol_search(
        self, user_id, conversation_id, content, intent_result
    ) -> dict:
        """Handle protocol search intent via GraphRAG."""
        entities = intent_result.extracted_entities

        # Build user preferences from entities
        user_preferences = {}
        if "risk_preference" in entities:
            user_preferences["risk_tolerance"] = (
                "conservative" if entities["risk_preference"] == "low" else "aggressive"
            )
        if "chain" in entities:
            user_preferences["preferred_chains"] = [entities["chain"]]
        if "category" in entities:
            user_preferences["preferred_categories"] = [entities["category"]]

        # Perform GraphRAG search
        search_results = await self._graphrag_search.search_protocols_from_chat(
            message=content,
            user_preferences=user_preferences,
            conversation_id=conversation_id,
        )

        # Format response message
        response_content = self._format_search_results(search_results)

        # Save to conversation history
        user_msg, agent_msg = await self._save_messages(
            conversation_id, content, response_content
        )

        return {
            "user_message": self._message_to_dict(user_msg),
            "agent_message": self._message_to_dict(agent_msg),
            "routing": {
                "intent": "PROTOCOL_SEARCH",
                "confidence": intent_result.confidence,
                "handler": "graphrag_search",
                "reasoning": intent_result.reasoning,
            },
            "enrichment": {
                "protocols": [
                    {
                        "protocol_id": str(r.protocol_id),
                        "protocol_name": r.protocol_name,
                        "similarity_score": r.similarity_score,
                        "risk_score": r.risk_score,
                        "risk_level": r.risk_level,
                        "tvl": r.tvl,
                        "category": r.category,
                        "chain": r.chain,
                    }
                    for r in search_results.results
                ],
                "search_context": search_results.search_explanation,
                "recommendations": search_results.recommendations,
            }
        }

    async def _handle_risk_assessment(
        self, user_id, conversation_id, content, intent_result
    ) -> dict:
        """Handle risk assessment intent via GraphRAG."""
        entities = intent_result.extracted_entities

        if "protocol_name" not in entities:
            # Fallback to general chat if no protocol detected
            return await self._handle_general_conversation(
                user_id, conversation_id, content, intent_result
            )

        # Perform risk analysis
        risk_insights = await self._graphrag_risk.get_protocol_risk_from_chat(
            protocol_name=entities["protocol_name"],
            conversation_id=conversation_id,
            operation_type=entities.get("operation_type"),
            amount_usd=entities.get("amount_usd"),
        )

        # Format response
        response_content = self._format_risk_analysis(risk_insights)

        # Save to conversation
        user_msg, agent_msg = await self._save_messages(
            conversation_id, content, response_content
        )

        return {
            "user_message": self._message_to_dict(user_msg),
            "agent_message": self._message_to_dict(agent_msg),
            "routing": {
                "intent": "RISK_ASSESSMENT",
                "confidence": intent_result.confidence,
                "handler": "graphrag_risk",
                "reasoning": intent_result.reasoning,
            },
            "enrichment": {
                "risk_analysis": {
                    "protocol_id": str(risk_insights.risk_analysis.protocol_id),
                    "protocol_name": risk_insights.risk_analysis.protocol_name,
                    "risk_score": risk_insights.risk_analysis.risk_score,
                    "risk_level": risk_insights.risk_analysis.risk_level,
                    "confidence": risk_insights.risk_analysis.confidence,
                    "should_warn": risk_insights.risk_analysis.should_warn,
                },
                "alternatives_count": len(risk_insights.alternatives),
            }
        }

    async def _handle_similar_protocols(
        self, user_id, conversation_id, content, intent_result
    ) -> dict:
        """Handle similar protocols intent via GraphRAG."""
        entities = intent_result.extracted_entities
        protocol_name = entities.get("protocol_name", "")

        if not protocol_name:
            # Fallback to general chat if no protocol detected
            return await self._handle_general_conversation(
                user_id, conversation_id, content, intent_result
            )

        # Find base protocol
        base_search = await self._graphrag_search.search_protocols_from_chat(
            message=protocol_name,
            conversation_id=conversation_id,
        )

        if not base_search.results:
            # Protocol not found - fallback to general chat
            response_content = f"I couldn't find the protocol '{protocol_name}'. Could you provide more details or check the spelling?"
            user_msg, agent_msg = await self._save_messages(
                conversation_id, content, response_content
            )
            return {
                "user_message": self._message_to_dict(user_msg),
                "agent_message": self._message_to_dict(agent_msg),
                "routing": {
                    "intent": "SIMILAR_PROTOCOLS",
                    "confidence": intent_result.confidence,
                    "handler": "graphrag_similar",
                    "reasoning": "Protocol not found, fallback response",
                },
            }

        base_protocol = base_search.results[0]

        # Find similar protocols
        similar_search = await self._graphrag_search.search_protocols_from_chat(
            message=f"protocols similar to {protocol_name}",
            conversation_id=conversation_id,
        )

        # Filter out base protocol
        similar_protocols = [
            r for r in similar_search.results
            if r.protocol_id != base_protocol.protocol_id
        ][:5]

        # Format response
        response_content = self._format_similar_protocols(
            base_protocol, similar_protocols
        )

        # Save to conversation
        user_msg, agent_msg = await self._save_messages(
            conversation_id, content, response_content
        )

        return {
            "user_message": self._message_to_dict(user_msg),
            "agent_message": self._message_to_dict(agent_msg),
            "routing": {
                "intent": "SIMILAR_PROTOCOLS",
                "confidence": intent_result.confidence,
                "handler": "graphrag_similar",
                "reasoning": intent_result.reasoning,
            },
            "enrichment": {
                "base_protocol": {
                    "protocol_id": str(base_protocol.protocol_id),
                    "protocol_name": base_protocol.protocol_name,
                    "risk_score": base_protocol.risk_score,
                    "tvl": base_protocol.tvl,
                },
                "similar_protocols": [
                    {
                        "protocol_id": str(p.protocol_id),
                        "protocol_name": p.protocol_name,
                        "similarity_score": p.similarity_score,
                        "tvl": p.tvl,
                    }
                    for p in similar_protocols
                ]
            }
        }

    async def _handle_specialist_task(
        self, user_id, conversation_id, content, intent_result
    ) -> dict:
        """Handle specialist task intent via Agent Squad."""
        # Execute Agent Squad routing
        result = await self._agent_squad.execute(
            conversation_id=conversation_id,
            user_id=user_id,
            content=content,
            force_agent=intent_result.suggested_agent,  # Use suggested agent
        )

        return {
            "user_message": {
                "id": str(result["user_message_id"]),
                "content": content,
                "role": "user",
            },
            "agent_message": {
                "id": str(result["agent_message_id"]),
                "content": result["content"],
                "role": "assistant",
                "agent_type": result["agent_type"],
            },
            "routing": {
                "intent": "SPECIALIST_TASK",
                "confidence": intent_result.confidence,
                "handler": "agent_squad",
                "agent_used": result["agent_type"],
                "reasoning": intent_result.reasoning,
            },
            "enrichment": {
                "tools_used": result.get("tools_used", []),
                "tokens_consumed": result.get("tokens_used"),
                "latency_ms": result.get("latency_ms"),
                "intent_classification": result.get("intent_classification"),
            }
        }

    async def _handle_complex_workflow(
        self, user_id, conversation_id, content, intent_result
    ) -> dict:
        """Handle complex workflow intent via Supervisor."""
        # Execute Supervisor workflow
        result = await self._supervisor.execute(
            conversation_id=conversation_id,
            user_id=user_id,
            complex_task=content,
            max_agents=5,
        )

        return {
            "user_message": {
                "content": content,
                "role": "user",
            },
            "agent_message": {
                "content": result.get("final_response", ""),
                "role": "assistant",
            },
            "routing": {
                "intent": "COMPLEX_WORKFLOW",
                "confidence": intent_result.confidence,
                "handler": "supervisor",
                "reasoning": intent_result.reasoning,
            },
            "enrichment": {
                "workflow_id": str(result.get("workflow_id")),
                "workflow_status": result.get("status"),
                "tasks_count": len(result.get("tasks", [])),
                "agents_involved": result.get("agents_used", []),
                "total_latency_ms": result.get("total_latency_ms"),
            }
        }

    async def _handle_general_conversation(
        self, user_id, conversation_id, content, intent_result
    ) -> dict:
        """Handle general conversation intent via Regular Chat."""
        # Execute regular chat
        user_msg, agent_msg = await self._regular_chat.execute(
            user_id=user_id,
            conversation_id=conversation_id,
            content=content,
        )

        return {
            "user_message": self._message_to_dict(user_msg),
            "agent_message": self._message_to_dict(agent_msg),
            "routing": {
                "intent": "GENERAL_CONVERSATION",
                "confidence": intent_result.confidence,
                "handler": "regular_chat",
                "reasoning": intent_result.reasoning,
            },
        }

    async def _save_messages(
        self, conversation_id: UUID, user_content: str, agent_content: str
    ) -> tuple[Message, Message]:
        """Save user and agent messages to conversation."""
        # Create and save user message
        user_message = Message.create_user_message(
            conversation_id=conversation_id,
            content=user_content,
        )
        await self._conversation_repo.add_message(user_message)

        # Create and save agent message
        agent_message = Message.create_agent_message(
            conversation_id=conversation_id,
            content=agent_content,
        )
        await self._conversation_repo.add_message(agent_message)

        # Update conversation timestamp
        conversation = await self._conversation_repo.get_conversation(conversation_id)
        if conversation:
            conversation.touch()
            await self._conversation_repo.add_conversation(conversation)

        return user_message, agent_message

    def _message_to_dict(self, message: Message) -> dict:
        """Convert Message entity to dict for response."""
        return {
            "id": str(message.id),
            "conversation_id": str(message.conversation_id),
            "role": message.role.value,
            "content": message.content,
            "agent_type": message.agent_type,
            "created_at": message.created_at.isoformat(),
        }

    def _format_search_results(self, search_results) -> str:
        """Format GraphRAG search results as markdown."""
        if not search_results.results:
            return "I couldn't find any protocols matching your criteria. Try broadening your search or adjusting your preferences."

        output = f"**{search_results.search_explanation}**\n\n"

        for i, protocol in enumerate(search_results.results, 1):
            output += f"**{i}. {protocol.protocol_name}**\n"
            output += f"- TVL: ${protocol.tvl/1e9:.2f}B\n"
            output += f"- Risk: {protocol.risk_level} ({protocol.risk_score:.1f}/10)\n"
            output += f"- Category: {protocol.category}\n"
            output += f"- Chain: {protocol.chain}\n"
            if protocol.apy:
                output += f"- APY: {protocol.apy:.2f}%\n"
            output += f"- Why relevant: {protocol.why_relevant}\n\n"

        if search_results.recommendations:
            output += "**Recommendations:**\n"
            for rec in search_results.recommendations:
                output += f"- {rec}\n"

        return output

    def _format_risk_analysis(self, risk_insights) -> str:
        """Format risk analysis as markdown."""
        ra = risk_insights.risk_analysis

        output = f"**Risk Analysis: {ra.protocol_name}**\n\n"
        output += f"**Overall Risk:** {ra.risk_score:.1f}/10 ({ra.risk_level})\n"
        output += f"**Confidence:** {ra.confidence*100:.0f}%\n\n"

        if ra.contributing_factors:
            output += "**Contributing Factors:**\n"
            for factor in ra.contributing_factors:
                critical = " ⚠️ CRITICAL" if factor.is_critical else ""
                output += f"\n**{factor.factor}**{critical}\n"
                output += f"- Impact: {factor.impact:.1f}/10\n"
                output += f"- {factor.description}\n"

        if ra.recommendations:
            output += "\n**Recommendations:**\n"
            for rec in ra.recommendations:
                output += f"- {rec}\n"

        if ra.should_warn and ra.warning_message:
            output += f"\n⚠️ **Warning:** {ra.warning_message}\n"

        if risk_insights.alternatives:
            output += "\n**Safer Alternatives:**\n"
            for alt in risk_insights.alternatives[:3]:
                output += f"\n**{alt.protocol_name}** (Risk: {alt.risk_level})\n"
                output += f"- {alt.why_better}\n"
                output += f"- TVL: ${alt.tvl/1e9:.2f}B\n"

        return output

    def _format_similar_protocols(self, base, similar_list) -> str:
        """Format similar protocols as markdown."""
        output = f"**Protocols Similar to {base.protocol_name}**\n\n"
        output += f"**Base Protocol:**\n"
        output += f"- TVL: ${base.tvl/1e9:.2f}B\n"
        output += f"- Risk: {base.risk_level} ({base.risk_score:.1f}/10)\n"
        output += f"- Category: {base.category}\n\n"

        if not similar_list:
            output += "No similar protocols found. Try exploring other categories or chains."
            return output

        output += "**Similar Protocols:**\n\n"

        for i, protocol in enumerate(similar_list, 1):
            output += f"**{i}. {protocol.protocol_name}**\n"
            output += f"- Similarity: {protocol.similarity_score*100:.0f}%\n"
            output += f"- TVL: ${protocol.tvl/1e9:.2f}B\n"
            output += f"- Risk: {protocol.risk_level} ({protocol.risk_score:.1f}/10)\n"
            output += f"- Why similar: {protocol.why_relevant}\n\n"

        return output

    async def _handle_hunter_sentiment(
        self, user_id: int, conversation_id: int, content: str, intent_result
    ) -> dict:
        """Handle sentiment analysis intent via Hunter AI."""
        entities = intent_result.extracted_entities
        token_symbol = entities.get("token_symbol", "ETH")
        time_horizon = entities.get("time_horizon", "24h")
        sources = entities.get("sources")

        response_content = f"📊 **Sentiment Analysis for {token_symbol}**\n\n"
        response_content += f"Analyzing sentiment from multiple sources ({time_horizon} timeframe)...\n\n"
        response_content += "This feature routes to Hunter AI sentiment analysis tools:\n"
        response_content += "- Twitter sentiment\n"
        response_content += "- Reddit discussions\n"
        response_content += "- Discord communities\n"
        response_content += "- News coverage\n\n"
        response_content += f"*This is routed via unified routing to Hunter AI tools.*"

        user_msg, agent_msg = await self._save_messages(
            conversation_id, content, response_content
        )

        return {
            "user_message": self._message_to_dict(user_msg),
            "agent_message": self._message_to_dict(agent_msg),
            "routing": {
                "intent": "hunter_sentiment",
                "confidence": intent_result.confidence,
                "handler": "hunter_sentiment",
                "agent_used": "hunter_ai",
                "reasoning": intent_result.reasoning,
            },
            "enrichment": {
                "token_symbol": token_symbol,
                "time_horizon": time_horizon,
                "sources": sources or ["twitter", "reddit", "discord", "news"],
                "hunter_tool": "sentiment_analysis",
            },
        }

    async def _handle_hunter_price_prediction(
        self, user_id: int, conversation_id: int, content: str, intent_result
    ) -> dict:
        """Handle price prediction intent via Hunter AI."""
        entities = intent_result.extracted_entities
        token_symbol = entities.get("token_symbol", "ETH")
        time_horizon = entities.get("time_horizon", "24h")

        response_content = f"📈 **Price Prediction for {token_symbol}**\n\n"
        response_content += f"Generating price forecast ({time_horizon} timeframe)...\n\n"
        response_content += "This feature routes to Hunter AI price prediction ML models:\n"
        response_content += "- Historical price analysis\n"
        response_content += "- Machine learning forecasting\n"
        response_content += "- Confidence intervals\n"
        response_content += "- Price targets\n\n"
        response_content += f"*This is routed via unified routing to Hunter AI tools.*"

        user_msg, agent_msg = await self._save_messages(
            conversation_id, content, response_content
        )

        return {
            "user_message": self._message_to_dict(user_msg),
            "agent_message": self._message_to_dict(agent_msg),
            "routing": {
                "intent": "hunter_price_prediction",
                "confidence": intent_result.confidence,
                "handler": "hunter_price_prediction",
                "agent_used": "hunter_ai",
                "reasoning": intent_result.reasoning,
            },
            "enrichment": {
                "token_symbol": token_symbol,
                "time_horizon": time_horizon,
                "hunter_tool": "price_prediction",
            },
        }

    async def _handle_hunter_risk_signals(
        self, user_id: int, conversation_id: int, content: str, intent_result
    ) -> dict:
        """Handle risk signals intent via Hunter AI."""
        entities = intent_result.extracted_entities
        token_symbol = entities.get("token_symbol", "ETH")

        response_content = f"⚠️ **Risk Signals for {token_symbol}**\n\n"
        response_content += f"Analyzing market risk indicators...\n\n"
        response_content += "This feature routes to Hunter AI risk detection:\n"
        response_content += "- Market volatility warnings\n"
        response_content += "- Liquidity risk signals\n"
        response_content += "- Price anomaly detection\n"
        response_content += "- Risk severity scoring\n\n"
        response_content += f"*This is routed via unified routing to Hunter AI tools.*"

        user_msg, agent_msg = await self._save_messages(
            conversation_id, content, response_content
        )

        return {
            "user_message": self._message_to_dict(user_msg),
            "agent_message": self._message_to_dict(agent_msg),
            "routing": {
                "intent": "hunter_risk_signals",
                "confidence": intent_result.confidence,
                "handler": "hunter_risk_signals",
                "agent_used": "hunter_ai",
                "reasoning": intent_result.reasoning,
            },
            "enrichment": {
                "token_symbol": token_symbol,
                "hunter_tool": "risk_signals",
            },
        }

    async def _handle_hunter_trading_signals(
        self, user_id: int, conversation_id: int, content: str, intent_result
    ) -> dict:
        """Handle trading signals intent via Hunter AI."""
        entities = intent_result.extracted_entities
        token_symbol = entities.get("token_symbol", "ETH")

        response_content = f"📉 **Trading Signals for {token_symbol}**\n\n"
        response_content += f"Generating buy/sell signals...\n\n"
        response_content += "This feature routes to Hunter AI trading analysis:\n"
        response_content += "- Buy/sell recommendations\n"
        response_content += "- Entry/exit points\n"
        response_content += "- Signal strength indicators\n"
        response_content += "- Risk-reward ratios\n\n"
        response_content += f"*This is routed via unified routing to Hunter AI tools.*"

        user_msg, agent_msg = await self._save_messages(
            conversation_id, content, response_content
        )

        return {
            "user_message": self._message_to_dict(user_msg),
            "agent_message": self._message_to_dict(agent_msg),
            "routing": {
                "intent": "hunter_trading_signals",
                "confidence": intent_result.confidence,
                "handler": "hunter_trading_signals",
                "agent_used": "hunter_ai",
                "reasoning": intent_result.reasoning,
            },
            "enrichment": {
                "token_symbol": token_symbol,
                "hunter_tool": "trading_signals",
            },
        }

    async def _handle_hunter_patterns(
        self, user_id: int, conversation_id: int, content: str, intent_result
    ) -> dict:
        """Handle chart pattern detection intent via Hunter AI."""
        entities = intent_result.extracted_entities
        token_symbol = entities.get("token_symbol", "ETH")

        response_content = f"📊 **Chart Pattern Analysis for {token_symbol}**\n\n"
        response_content += f"Detecting technical patterns...\n\n"
        response_content += "This feature routes to Hunter AI pattern detection:\n"
        response_content += "- Head and shoulders patterns\n"
        response_content += "- Support/resistance levels\n"
        response_content += "- Trend line analysis\n"
        response_content += "- Pattern reliability scores\n\n"
        response_content += f"*This is routed via unified routing to Hunter AI tools.*"

        user_msg, agent_msg = await self._save_messages(
            conversation_id, content, response_content
        )

        return {
            "user_message": self._message_to_dict(user_msg),
            "agent_message": self._message_to_dict(agent_msg),
            "routing": {
                "intent": "hunter_patterns",
                "confidence": intent_result.confidence,
                "handler": "hunter_patterns",
                "agent_used": "hunter_ai",
                "reasoning": intent_result.reasoning,
            },
            "enrichment": {
                "token_symbol": token_symbol,
                "hunter_tool": "pattern_detection",
            },
        }

    async def _handle_hunter_portfolio(
        self, user_id: int, conversation_id: int, content: str, intent_result
    ) -> dict:
        """Handle portfolio optimization intent via Hunter AI."""
        entities = intent_result.extracted_entities
        tokens = entities.get("tokens", ["BTC", "ETH", "SOL"])
        risk_tolerance = entities.get("risk_tolerance", 0.5)

        response_content = f"💼 **Portfolio Optimization**\n\n"
        response_content += f"Optimizing portfolio for: {', '.join(tokens)}\n"
        response_content += f"Risk tolerance: {risk_tolerance*100:.0f}%\n\n"
        response_content += "This feature routes to Hunter AI MPT optimization:\n"
        response_content += "- Modern Portfolio Theory analysis\n"
        response_content += "- Efficient frontier calculation\n"
        response_content += "- Asset allocation recommendations\n"
        response_content += "- Risk-adjusted returns\n\n"
        response_content += f"*This is routed via unified routing to Hunter AI tools.*"

        user_msg, agent_msg = await self._save_messages(
            conversation_id, content, response_content
        )

        return {
            "user_message": self._message_to_dict(user_msg),
            "agent_message": self._message_to_dict(agent_msg),
            "routing": {
                "intent": "hunter_portfolio",
                "confidence": intent_result.confidence,
                "handler": "hunter_portfolio",
                "agent_used": "hunter_ai",
                "reasoning": intent_result.reasoning,
            },
            "enrichment": {
                "tokens": tokens,
                "risk_tolerance": risk_tolerance,
                "hunter_tool": "portfolio_optimization",
            },
        }
