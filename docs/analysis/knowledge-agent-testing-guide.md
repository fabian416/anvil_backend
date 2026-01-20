# Knowledge Anvil Agent - Testing Guide

## ✅ Implementation Complete

### What Was Created

1. **KnowledgeAgent** - Specialized agent for educational queries
2. **AgentType.KNOWLEDGE** - New agent type added
3. **Configuration** - Added to `config/local/config.toml`
4. **DI Registration** - Registered in dependency injection
5. **Intent Routing** - Updated to route knowledge queries to KnowledgeAgent
6. **Guest Chat Integration** - Fast path routes to KnowledgeAgent

## 🧪 Test Queries

### Test 1: Simple Knowledge Query (Fast Path)
```bash
curl -X POST http://localhost:8080/api/v1/guest/chat \
  -H "Content-Type: application/json" \
  -d '{"content": "What is Anvil?"}'
```

**Expected:**
- Routes to KnowledgeAgent (fast path)
- Response time: < 3 seconds
- Agent type in enrichment: `"knowledge"`
- Uses knowledge base from JSON files

### Test 2: Complex Workflow Query
```bash
curl -X POST http://localhost:8080/api/v1/guest/chat \
  -H "Content-Type: application/json" \
  -d '{"content": "What is Anvil? Can you give me the price of BTC?"}'
```

**Expected:**
- Routes through SupervisorCoordinator
- Creates workflow with multiple agents:
  - KnowledgeAgent (for "What is Anvil?")
  - HunterAIAgent (for BTC price)
- Response time: 5-10 seconds (multi-agent)
- Multiple agents in enrichment

## 📊 Performance Monitoring

### Check Logs for Performance Issues

```bash
# Check for knowledge agent usage
tail -f logs/fastapi.log | grep -i "knowledge\|fast path"

# Check execution times
tail -f logs/fastapi.log | grep -i "execution.*time\|latency"

# Check for errors
tail -f logs/fastapi.log | grep -i "error\|exception\|timeout"
```

### Expected Log Patterns

**Fast Path (Simple Query):**
```
⚡ Fast path: Simple informational query → Knowledge agent (bypassing workflow planning)
```

**Workflow (Complex Query):**
```
Parsing workflow task: agent_type_str=knowledge
Parsing workflow task: agent_type_str=hunter_ai
```

## 🔍 Troubleshooting

### If Server Not Starting

1. **Check Config Syntax:**
   ```bash
   python3 -c "import rtoml; rtoml.load(open('config/local/config.toml'))"
   ```

2. **Check Imports:**
   ```bash
   python3 -c "from app.infrastructure.adapters.agent_squad.agents.knowledge_agent import KnowledgeAgent; print('OK')"
   ```

3. **Check DI Registration:**
   ```bash
   python3 -c "from app.setup.ioc.agent_squad_infrastructure import AgentSquadInfrastructureProvider; print('OK')"
   ```

### If Queries Are Slow

1. **Check KnowledgeInjector:**
   - Verify `anvil_knowledge/features/*.json` files exist
   - Check if KnowledgeInjector is loading correctly

2. **Check LLM Calls:**
   - Verify Vertex AI API key is set
   - Check LLM response times in logs

3. **Check Fast Path Detection:**
   - Verify simple query patterns are matching
   - Check if queries are going through SupervisorCoordinator instead

## 📝 Current Status

- ✅ KnowledgeAgent created
- ✅ AgentType.KNOWLEDGE added
- ✅ Configuration added
- ✅ DI registration complete
- ✅ Intent routing updated
- ✅ Guest chat integration complete
- ⏳ **Server needs to be running for testing**

## 🚀 Next Steps

1. Start server: `make start-dev-full`
2. Wait for startup: ~30 seconds
3. Test simple query: "What is Anvil?"
4. Test complex query: "What is Anvil? Can you give me the price of BTC?"
5. Review logs for performance
6. Optimize if needed
