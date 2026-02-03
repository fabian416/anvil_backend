#!/usr/bin/env python3
"""Script to add expected_output fields to all test cases in test_data.json"""

import json
from typing import Dict, Any


def generate_agent_content(
    test_case: Dict[str, Any], category: str, subcategory: str
) -> str:
    """Generate realistic agent response content based on test case."""
    content = test_case["input"]["content"]
    intent = test_case["expected_routing"].get("intent", "general_conversation")
    enrichment = test_case.get("expected_enrichment", {})

    if category == "graphrag":
        if subcategory == "protocol_search":
            return f"I found several protocols matching your search:\n\n1. **Protocol 1** - Details...\n2. **Protocol 2** - Details...\n3. **Protocol 3** - Details...\n\nThese protocols match your criteria and have been verified for security."
        elif subcategory == "risk_assessment":
            protocol = enrichment.get("protocol_name", "the protocol")
            return f"Here's a comprehensive risk assessment for {protocol}:\n\n**Smart Contract Risk**: Low\n**Economic Risk**: Medium\n**Operational Risk**: Low\n\nOverall, {protocol} has a strong security track record with multiple audits."
        elif subcategory == "similar_protocols":
            ref = enrichment.get("reference_protocol", "the protocol")
            return f"Here are protocols similar to {ref}:\n\n1. **Similar Protocol 1** - Similarity: 0.85\n2. **Similar Protocol 2** - Similarity: 0.78\n3. **Similar Protocol 3** - Similarity: 0.72\n\nThese protocols share similar features and use cases."

    elif category == "hunter_ai":
        token = enrichment.get("token_symbol", "the token")
        if subcategory == "sentiment":
            return f"Sentiment analysis for {token}:\n\n**Overall Score**: 72.5/100 (Bullish)\n**Confidence**: 0.85\n**Signal Strength**: Strong\n\n**Source Breakdown**:\n- Twitter: 75/100 (Bullish)\n- Reddit: 68/100 (Neutral-Bullish)\n\nOverall sentiment is positive with strong consensus across sources."
        elif subcategory == "price_prediction":
            horizon = enrichment.get("time_horizon", "7d")
            return f"Price prediction for {token} over the next {horizon}:\n\n**Current Price**: $X,XXX\n**Predicted Price**: $X,XXX (+X%)\n**Confidence**: 0.82\n\nBased on LSTM model analysis, {token} shows bullish momentum."
        elif subcategory == "trading_signals":
            return f"Trading signals for {token}:\n\n**Recommendation**: BUY\n**Entry Signal**: Strong\n**Exit Target**: $X,XXX\n**Stop Loss**: $X,XXX\n\nMultiple indicators suggest a buying opportunity."
        elif subcategory == "portfolio":
            tokens = enrichment.get("tokens", ["BTC", "ETH"])
            risk = enrichment.get("risk_tolerance", "moderate")
            return f"Optimized portfolio for {risk} risk:\n\n**Allocation**:\n- {tokens[0] if tokens else 'BTC'}: 40%\n- {tokens[1] if len(tokens) > 1 else 'ETH'}: 35%\n- {tokens[2] if len(tokens) > 2 else 'SOL'}: 25%\n\nThis allocation maximizes returns while maintaining your risk tolerance."

    elif category == "ultra":
        if subcategory == "arbitrage":
            capital = enrichment.get("capital", 10000)
            return f"Found {3} arbitrage opportunities with ${capital:,} capital:\n\n1. **ARB-001** - Profit: $95.50 (0.96%)\n   - Type: 2-hop\n   - Confidence: 0.85\n\n2. **ARB-002** - Profit: $78.20 (0.78%)\n   - Type: Triangle\n   - Confidence: 0.82\n\n3. **ARB-003** - Profit: $65.40 (0.65%)\n   - Type: 3-hop\n   - Confidence: 0.79"
        elif subcategory == "flash_loans":
            token = enrichment.get("token_symbol", "USDC")
            amount = enrichment.get("amount", 100000)
            return f"Best flash loan protocol for {amount:,} {token}:\n\n**Recommended**: Balancer\n**Fee**: 0% (gas only)\n**Estimated Total Cost**: $5.00\n\nBalancer offers the lowest fees for this amount."
        elif subcategory == "auto_executor":
            action = enrichment.get("action", "start")
            if action == "start":
                return "Auto-executor started successfully. The bot will now scan for arbitrage opportunities every 10 seconds and execute profitable trades automatically."
            elif action == "stop":
                return "Auto-executor stopped. All active scans and executions have been halted."
            elif action == "status":
                return "**Status**: Running\n**Active Opportunities**: 2\n**Total Profit Today**: $245.50\n**Last Execution**: 2 minutes ago"

    elif category == "agent_squad":
        if subcategory == "specialist_task":
            return "Analysis complete:\n\n**Liquidity Depth**: $12.5M\n**Price Impact**: 0.15%\n**Recommended Action**: Proceed with swap\n\nThe liquidity is sufficient for your trade size."
        elif subcategory == "complex_workflow":
            return "Complete DeFi strategy created:\n\n**Workflow ID**: WF-001\n**Agents Involved**: 3\n**Tasks Completed**: 5\n\nYour strategy includes risk analysis, yield optimization, and execution plan."

    elif category == "chat":
        if "greeting" in content.lower() or "hello" in content.lower():
            return "Hello! I'm Anvil, your DeFi assistant. I can help you with:\n\n- Finding and analyzing DeFi protocols\n- Market sentiment and price predictions\n- Arbitrage opportunities and flash loans\n- Portfolio optimization\n- Risk assessment\n\nWhat would you like to explore today?"
        elif "features" in content.lower() or "help" in content.lower():
            return "Anvil offers comprehensive DeFi intelligence:\n\n**GraphRAG**: Protocol search, risk analysis, similarity matching\n**Hunter AI**: Sentiment, predictions, trading signals, patterns\n**ULTRA**: Arbitrage discovery, flash loans, MEV protection\n**Agent Squad**: Specialized tasks and complex workflows\n\nAsk me anything about DeFi!"

    return f"Response to: {content}"


def generate_enrichment_data(
    test_case: Dict[str, Any], category: str, subcategory: str
) -> Dict[str, Any]:
    """Generate enrichment data based on test case."""
    base_enrichment = test_case.get("expected_enrichment", {}).copy()

    # Add category-specific enrichment
    if category == "graphrag" and subcategory == "protocol_search":
        if "protocols" not in base_enrichment:
            base_enrichment["protocols"] = [
                {
                    "protocol_id": "aave_v3",
                    "protocol_name": "Aave V3",
                    "similarity_score": 0.95,
                    "risk_score": 0.15,
                    "risk_level": "low",
                    "tvl": 12500000000,
                    "apy": 6.5,
                    "audit_count": 5,
                    "description": "Decentralized lending protocol",
                    "category": "lending",
                    "chain": "ethereum",
                    "why_relevant": "Matches your criteria",
                }
            ]
        if "search_context" not in base_enrichment:
            base_enrichment["search_context"] = (
                "Found protocols matching your search criteria"
            )
        if "recommendations" not in base_enrichment:
            base_enrichment["recommendations"] = [
                "Consider diversifying across protocols"
            ]

    elif category == "hunter_ai" and subcategory == "sentiment":
        if "token_symbol" in base_enrichment:
            base_enrichment["sources"] = {
                "twitter": {"score": 75, "confidence": 0.88},
                "reddit": {"score": 68, "confidence": 0.82},
            }

    elif category == "ultra" and subcategory == "arbitrage":
        if "opportunities" not in base_enrichment:
            base_enrichment["opportunities"] = [
                {
                    "opportunity_id": "ARB-001",
                    "type": "2hop",
                    "expected_profit_usd": "95.50",
                    "confidence_score": 0.85,
                }
            ]

    return base_enrichment


def add_outputs_to_test_cases(data: Dict[str, Any]) -> None:
    """Recursively add expected_output to all test cases."""
    test_cases = data.get("test_cases", {})

    for category, category_data in test_cases.items():
        if not isinstance(category_data, dict):
            continue

        for subcategory, subcategory_data in category_data.items():
            if not isinstance(subcategory_data, list):
                continue

            for test_case in subcategory_data:
                if "expected_output" in test_case:
                    continue  # Skip if already has output

                # Generate output
                agent_content = generate_agent_content(test_case, category, subcategory)
                enrichment = generate_enrichment_data(test_case, category, subcategory)

                routing = test_case.get("expected_routing", {})
                handler = routing.get("handler", "general_chat")
                confidence = routing.get("confidence_min", 0.85) + 0.05
                if confidence > 1.0:
                    confidence = 0.95

                test_case["expected_output"] = {
                    "user_message": {
                        "id": f"msg_user_{test_case['id']}",
                        "conversation_id": "conv_abc123",
                        "role": "user",
                        "content": test_case["input"]["content"],
                        "agent_type": None,
                        "created_at": "2025-12-26T10:00:00Z",
                    },
                    "agent_message": {
                        "id": f"msg_agent_{test_case['id']}",
                        "conversation_id": "conv_abc123",
                        "role": "assistant",
                        "content": agent_content,
                        "agent_type": handler if handler != "general_chat" else None,
                        "created_at": "2025-12-26T10:00:01Z",
                    },
                    "routing": {
                        "intent": routing.get("intent", "general_conversation"),
                        "confidence": round(confidence, 2),
                        "handler": handler,
                        "agent_used": None,
                        "reasoning": f"Detected intent: {routing.get('intent', 'general_conversation')} with {round(confidence * 100)}% confidence",
                        "total_latency_ms": 1000,
                    },
                    "enrichment": enrichment,
                }


def main():
    """Main function."""
    file_path = "docs/api/examples/test_data.json"

    # Read file
    with open(file_path, "r") as f:
        data = json.load(f)

    # Add outputs
    add_outputs_to_test_cases(data)

    # Write back
    with open(file_path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"✅ Added expected_output to all test cases in {file_path}")


if __name__ == "__main__":
    main()
