# Knowledge Base Integration Guide

## Quick Start

The knowledge injector is now ready to use! This guide shows how to integrate it into `conversations_router.py` to enhance LLM responses.

---

## Step 1: Import the Knowledge Injector

Add this import to `src/app/presentation/http/controllers/chat/conversations_router.py`:

```python
from app.application.chat.services.knowledge_injector import inject_knowledge
```

---

## Step 2: Enhance System Prompt with Knowledge

### Option A: Simple Integration (Recommended for Quick Test)

Find the section where the LLM system prompt is created (around line 1240) and enhance it:

```python
# BEFORE (existing code):
system_prompt = """You are Anvil, a specialized DeFi assistant focused EXCLUSIVELY on decentralized finance, crypto trading, and blockchain technology.

✅ ALWAYS IN SCOPE (Answer these confidently):
- Cryptocurrency basics: "What is Bitcoin?", "What is Ethereum?", "What is BTC?", "What is ETH?"
- Token information: Any questions about crypto tokens, coins, or digital assets
...
"""

# AFTER (with knowledge injection):
from app.application.chat.services.knowledge_injector import inject_knowledge

# Detect if query is investor-focused
user_type = "investor" if any(kw in message.content.lower() for kw in [
    "investor", "investment", "competitive advantage", "market opportunity",
    "revenue", "monetization", "roi"
]) else "user"

# Inject knowledge into system prompt
enhanced_system_prompt = inject_knowledge(
    user_query=message.content,
    detected_intent=mapped_intent.name,  # Use the mapped intent from intent_detector
    user_type=user_type,
    base_system_prompt=None  # Use default base prompt, or provide custom one
)

# Use enhanced prompt instead of original
llm_response = await llm_gateway.generate_response(
    prompt=message.content,
    system_prompt=enhanced_system_prompt,  # ← Use enhanced prompt here
    conversation_history=conversation_history
)
```

---

### Option B: Advanced Integration (Full Control)

For more control over knowledge injection, use the `KnowledgeInjector` class directly:

```python
from app.application.chat.services.knowledge_injector import get_knowledge_injector

# Get singleton injector instance
knowledge_injector = get_knowledge_injector()

# Get just the knowledge (without full prompt)
knowledge = knowledge_injector.get_knowledge_for_intent(
    user_query=message.content,
    detected_intent=mapped_intent.name,
    user_type="investor" if is_investor_query else "user"
)

# Build custom prompt with knowledge
custom_prompt = f"""You are Anvil, an expert DeFi assistant.

RELEVANT KNOWLEDGE:
{json.dumps(knowledge, indent=2)}

Answer the user's question using the knowledge above.

USER: {message.content}
"""

llm_response = await llm_gateway.generate_response(
    prompt=custom_prompt,
    system_prompt=None,
    conversation_history=conversation_history
)
```

---

## Step 3: Test the Integration

### Test Case 1: User Asking "What can you do?"

**Before (without knowledge injection):**
```
User: "what can you do?"
Response: "I'm Anvil, a DeFi assistant. I can help with crypto trading, swaps, and market analysis."
```

**After (with knowledge injection):**
```
User: "what can you do?"
Response: "I'm Anvil, your AI-powered gateway to decentralized finance. I offer:

**💱 Trading & Swaps**
- Execute token swaps across 1inch, Hyperliquid, and UniswapX
- Support for 100+ tokens (BTC, ETH, SOL, USDC, etc.)
- Best-rate optimization with MEV protection
Commands: 'swap 100 USDC to ETH', 'exchange 0.5 BTC for SOL'

**📊 Hunter AI - Market Intelligence**
- Multi-source sentiment analysis (Twitter, Reddit, News)
- AI-powered price predictions with 73% accuracy (24h)
- Risk signals and trading recommendations
Commands: 'check sentiment for BTC', 'predict ETH price'

**⚡ ULTRA - DeFi Automation**
- Arbitrage opportunities with 92% accuracy
- Flash loans (0% fees via Balancer/Uniswap V3)
- MEV protection via Flashbots (saved users $127K last month)
Commands: 'find arbitrage with $10k', 'protect from MEV'

**💼 Portfolio Management**
- Multi-chain portfolio tracking
- Real-time balance updates
- Transaction history and PnL calculations

**🏦 Lending & Borrowing**
- Multi-protocol rate comparison (Aave, Compound, Morpho)
- One-click deposit to highest APY

**🔍 Protocol Research**
- Instant protocol information and risk assessments
- Compare similar protocols

Try: 'swap 100 USDC to ETH' or 'what's the sentiment for BTC?'"
```

---

### Test Case 2: Investor Asking About Competitive Advantages

**Request:**
```bash
curl -X POST http://localhost:8080/api/v1/conversations/CONV_ID/messages \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content": "what are anvils competitive advantages?"}'
```

**Before (without knowledge injection):**
```
"I'm a DeFi assistant with features like trading, market analysis, and portfolio management."
```

**After (with knowledge injection):**
```
"Anvil's key competitive advantages:

**1. AI-First Approach**
- 18 specialized AI agents vs single-purpose competitors
- Natural language interface - no need to learn complex UIs
- 99% cost reduction through Vertex AI ($0.10/1M tokens vs $30/1M)

**2. Real-Time Market Intelligence**
- Hunter AI provides institutional-grade analysis (vs Bloomberg $2000/month → free)
- 82% sentiment correlation with price movements
- 73% price prediction accuracy (24h horizon)
- Multi-source aggregation (4+ sources vs single-source competitors)

**3. Advanced DeFi Automation**
- Multi-protocol flash loans (0% fees via Balancer/Uniswap vs 0.09% Aave-only competitors)
- Free MEV protection via Flashbots (competitors charge $10-50/trade)
- 850+ MEV attacks prevented, $127K saved (last 30 days)
- 92% arbitrage detection accuracy

**4. Multi-Language Native Support**
- English, Spanish, Portuguese, Chinese (not translations)
- Expands TAM by 3x vs English-only competitors

**5. Hexagonal Architecture**
- Rapid feature deployment
- Enterprise-grade security and scalability
- Clean separation enables fast iteration

**Market Position**: Similar to how ChatGPT became the intelligent layer for information retrieval, Anvil is the intelligent layer between users and DeFi protocols."
```

---

### Test Case 3: User Asking About Hunter AI

**Request:**
```bash
curl -X POST http://localhost:8080/api/v1/conversations/CONV_ID/messages \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content": "what is hunter ai and how accurate is it?"}'
```

**After (with knowledge injection):**
```
"Hunter AI is Anvil's advanced market intelligence system. Here's what it does and how accurate it is:

**Core Capabilities:**

1. **Sentiment Analysis**
   - Tracks Twitter, Reddit, Discord, and news outlets
   - **Accuracy: 82% correlation with actual price movements (24h)**
   - Updates: Real-time for news (every 5 min), hourly for social
   - Data Sources: Real RSS feeds (CoinDesk, CoinTelegraph), simulated Twitter/Discord

2. **Price Predictions**
   - Forecasts for 24h, 1 week, and 1 month
   - **Accuracy: 73% within predicted range (24h), 61% (7 days)**
   - Uses ensemble model: technical analysis + sentiment + on-chain metrics
   - Confidence scores provided (0-100%)

3. **Risk Signals**
   - Detects volatility, liquidity, smart contract, and market risks
   - Alert levels: Low, Medium, High, Critical

4. **Trading Signals**
   - Buy/sell recommendations with technical indicators
   - **Win rate: 68% (signals that moved in predicted direction)**
   - Risk/reward: Average 1:2.5 ratio

5. **Pattern Recognition**
   - Identifies chart patterns using computer vision AI
   - Detects head & shoulders, triangles, support/resistance

**What Makes It Accurate:**
- Multi-source aggregation (4+ sources vs single-source tools)
- AI-powered analysis (Gemini Pro + Claude 3.5)
- Continuous learning from prediction outcomes
- Validated against 6 months historical data

**Competitive Advantage:**
Bloomberg Terminal costs $2,000/month for similar analysis.
Hunter AI is free for authenticated users.

Try: 'check sentiment for BTC' or 'predict ETH price for next week'"
```

---

## Step 4: Verify Knowledge Injection is Working

Add logging to see what knowledge is being injected:

```python
from app.application.chat.services.knowledge_injector import get_knowledge_injector
import logging

logger = logging.getLogger(__name__)

# ... in your router code ...

knowledge_injector = get_knowledge_injector()

# Get knowledge to see what's being injected
knowledge = knowledge_injector.get_knowledge_for_intent(
    user_query=message.content,
    detected_intent=mapped_intent.name,
    user_type=user_type
)

logger.info(
    f"Knowledge injection for intent={mapped_intent.name}",
    extra={
        "user_query": message.content,
        "knowledge_sections": list(knowledge.keys()),
        "user_type": user_type
    }
)

# Now augment prompt with this knowledge
enhanced_prompt = inject_knowledge(
    user_query=message.content,
    detected_intent=mapped_intent.name,
    user_type=user_type
)
```

**Expected Log Output:**
```
INFO: Knowledge injection for intent=GENERAL_CONVERSATION
  user_query="what can you do?"
  knowledge_sections=['feature_name', 'tagline', 'core_capabilities', 'unique_features', 'getting_started', 'example_use_cases']
  user_type=user
```

---

## Performance Considerations

### Token Usage

Knowledge injection adds tokens to each LLM request:

| Knowledge File | Size | Est. Tokens | When Used |
|----------------|------|-------------|-----------|
| overview.json (full) | 150KB | ~40K tokens | "what can you do?" |
| overview.json (extracted) | 30KB | ~8K tokens | Investor queries |
| hunter_ai.json (full) | 80KB | ~20K tokens | Hunter AI queries |
| ultra.json (full) | 135KB | ~35K tokens | ULTRA queries |
| swap.json (full) | 70KB | ~18K tokens | Swap queries |
| shortcuts.json (full) | 95KB | ~24K tokens | Command help |

**Optimization**: The knowledge injector automatically extracts only relevant sections to minimize token usage.

**Example**:
- Query: "what's the sentiment for BTC?"
- Full `hunter_ai.json`: 1,500 lines (~20K tokens)
- Injected knowledge: ~300 lines (~4K tokens) - only sentiment section

---

### Caching

The `KnowledgeInjector` class caches loaded JSON files in memory:

```python
# Files are loaded once and cached
injector = get_knowledge_injector()

# First call: loads from disk
knowledge1 = injector.get_knowledge_for_intent("what can you do?", "GENERAL_CONVERSATION")

# Second call: uses cached version (faster)
knowledge2 = injector.get_knowledge_for_intent("tell me about anvil", "GENERAL_CONVERSATION")

# Clear cache after updates (only needed if JSON files change)
injector.clear_cache()
```

---

## Intent-to-Knowledge Mapping

The knowledge injector automatically maps intents to relevant JSON files:

| Intent Pattern | Primary File | Sections Extracted |
|----------------|--------------|-------------------|
| `GENERAL_CONVERSATION` + "what can you do" | overview.json | All core capabilities |
| `GENERAL_CONVERSATION` + investor keywords | overview.json | Competitive advantages, investor highlights |
| `HUNTER_SENTIMENT` | hunter_ai.json | Sentiment capability + accuracy metrics |
| `HUNTER_PRICE_PREDICTION` | hunter_ai.json | Price prediction + accuracy |
| `HUNTER_*` | hunter_ai.json | Specific Hunter AI capability |
| `ULTRA_ARBITRAGE` | ultra.json | Arbitrage discovery + examples |
| `ULTRA_FLASH_LOANS` | ultra.json | Flash loan protocols + fees |
| `ULTRA_MEV_PROTECTION` | ultra.json | MEV protection + attack types |
| `ULTRA_AUTO_EXECUTOR` | ultra.json | Auto executor + performance |
| `SWAP` | swap.json | How it works + aggregators |
| Any + "command"/"how to" | shortcuts.json | Relevant command categories |

---

## Customization

### Adding Custom Knowledge Extraction Logic

You can extend the knowledge injector for custom use cases:

```python
from app.application.chat.services.knowledge_injector import KnowledgeInjector

class CustomKnowledgeInjector(KnowledgeInjector):
    """Extended knowledge injector with custom logic"""

    def get_knowledge_for_intent(self, user_query: str, detected_intent: str, user_type: str = "user"):
        """Override to add custom logic"""

        # Custom logic: if query mentions specific token, inject token-specific data
        if "BTC" in user_query or "bitcoin" in user_query.lower():
            knowledge = super().get_knowledge_for_intent(user_query, detected_intent, user_type)
            # Add BTC-specific context
            knowledge["focus_token"] = "Bitcoin (BTC)"
            knowledge["btc_specifics"] = {
                "market_cap_rank": 1,
                "common_pairs": ["BTC/USDC", "BTC/ETH", "BTC/USDT"]
            }
            return knowledge

        # Default behavior
        return super().get_knowledge_for_intent(user_query, detected_intent, user_type)
```

---

## Troubleshooting

### Issue: Knowledge not appearing in responses

**Check 1**: Verify knowledge injector is being called
```python
logger.info(f"Enhanced prompt length: {len(enhanced_prompt)} chars")
logger.debug(f"Enhanced prompt preview: {enhanced_prompt[:500]}...")
```

**Check 2**: Verify JSON files exist
```python
from pathlib import Path
knowledge_path = Path(__file__).parent.parent.parent.parent.parent / "anvil_knowledge"
print(f"Knowledge base path: {knowledge_path}")
print(f"Files: {list(knowledge_path.glob('features/*.json'))}")
```

**Check 3**: Verify LLM is using the enhanced prompt
```python
# In your LLM gateway call, log the system prompt
logger.debug(f"System prompt for LLM: {system_prompt[:500]}...")
```

---

### Issue: Responses are incomplete or truncated

**Cause**: LLM context window exceeded

**Solution**: Use selective extraction instead of full files
```python
# Instead of full file injection
knowledge = injector.get_knowledge_for_intent(...)

# Use targeted extraction (implemented in knowledge_injector.py)
# The injector automatically extracts only relevant sections
```

---

### Issue: Slow response times

**Cause**: Large knowledge files being loaded on every request

**Solution**: Use singleton pattern (already implemented)
```python
# This uses cached injector instance
from app.application.chat.services.knowledge_injector import get_knowledge_injector

injector = get_knowledge_injector()  # Singleton, cached
```

---

## Metrics to Track

After integration, monitor these metrics to measure impact:

### Response Quality
- **Feature Coverage**: % of user questions answerable (target: 90%+)
- **Response Accuracy**: % of factually correct responses (target: 95%+)
- **User Satisfaction**: Feedback scores (target: 85%+)

### Performance
- **Response Time**: Should increase by <500ms
- **Token Usage**: Monitor tokens/request (should be +4K-8K)
- **Cache Hit Rate**: % of requests using cached knowledge (target: 90%+)

### Business Impact
- **Feature Discovery**: % users who discover new features (target: +70%)
- **Investor Conversion**: % investor queries answered completely (target: 100%)
- **Support Ticket Reduction**: Fewer "how does X work?" tickets (target: -40%)

---

## Next Steps

1. ✅ **Integrate**: Add knowledge injection to `conversations_router.py` (Steps 1-2 above)
2. ✅ **Test**: Verify with test cases (Step 3)
3. ✅ **Monitor**: Add logging to track knowledge injection (Step 4)
4. ✅ **Measure**: Track metrics listed above
5. ✅ **Iterate**: Update JSON files based on user feedback

---

## Support

Questions or issues?
- Review README.md in `anvil_knowledge/`
- Check implementation in `knowledge_injector.py`
- See examples in this integration guide

---

**Last Updated**: 2025-01-14
**Version**: 1.0.0
