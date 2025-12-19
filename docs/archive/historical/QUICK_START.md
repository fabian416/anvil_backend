# ⚡ LLM Orchestration - Quick Start Guide

## 🚀 Get Started in 5 Minutes

### **Step 1: Configure API Keys**

Edit `config/local/.secrets.toml`:

```toml
[llm.vertex_ai]
project_id = "your-gcp-project-id"
location = "us-central1"

[llm.deepinfra]
api_key = "your-deepinfra-api-key"

[llm.bedrock]
region = "us-east-1"
aws_access_key_id = "your-aws-key"
aws_secret_access_key = "your-aws-secret"
```

### **Step 2: Run Migration**

```bash
# Start database
make up.db

# Apply migrations
alembic upgrade head
```

### **Step 3: Start Services**

```bash
# Terminal 1: API Server
make start

# Terminal 2: Celery Worker
make celery.worker

# Terminal 3: Celery Beat
make celery.beat
```

### **Step 4: Verify**

```bash
# Check health
curl http://localhost:8000/admin/llm/dashboard/health

# View dashboard data
curl http://localhost:8000/admin/llm/dashboard?period=24h | jq

# View providers
curl http://localhost:8000/admin/llm/providers | jq
```

### **Step 5: Use in Code**

```python
from app.infrastructure.llm.orchestrator_integration import create_orchestrator_integration
from app.domain.value_objects.llm import LLMRequest, LLMMessage

# Create orchestrator (or inject via Dishka)
orchestrator = create_orchestrator_integration(
    vertex_project_id="your-project",
    deepinfra_api_key="your-key",
    bedrock_region="us-east-1",
)

# Execute request
response = await orchestrator.execute_agent_request(
    agent_type="swap_agent",
    messages=["Swap 100 USDC to ETH on Uniswap"],
    user_id=user_id,
)

print(response)  # AI-generated swap strategy
```

---

## 🎯 What You Get Out of the Box

### **Automatic Features:**

✅ **Best Model Selection**
- Chooses optimal model based on past performance
- Agent-specific optimization (accuracy vs speed vs cost)
- Updates rankings hourly

✅ **Automatic Failover**
- Provider down? Switches to next provider instantly
- Model overloaded? Tries next model in carousel
- 3-tier fallback: Vertex AI → DeepInfra → Bedrock

✅ **Cost Optimization**
- Routes to cheaper models when appropriate
- Tracks every penny spent
- Budget alerts before overspending

✅ **Circuit Breaker Protection**
- Bad provider? Circuit opens, traffic redirected
- Automatic recovery testing after 60s
- Zero manual intervention

✅ **Complete Telemetry**
- Every request tracked (latency, cost, tokens)
- Hourly aggregations for fast queries
- Export to CSV/PDF

---

## 📊 Dashboard Preview

### **Access Dashboard:**

```bash
# Via API
curl http://localhost:8000/admin/llm/dashboard

# Via WebSocket (real-time)
wscat -c ws://localhost:8000/admin/llm/dashboard/ws
```

### **Dashboard Shows:**

**System Health:**
- Provider status: 🟢 Vertex AI, 🟢 DeepInfra, 🟢 Bedrock
- Circuit breakers: 0 open, 12 closed
- Uptime: 99.97%

**Today's Metrics:**
- Requests: 25,000 (98% success rate)
- Avg latency: 1.2s
- Total cost: $76.50
- Budget used: 23% of $10,000 monthly

**Top Models:**
1. Gemini 1.5 Pro (score: 0.8945)
2. Gemini 1.5 Flash (score: 0.8720)
3. Claude 3.5 Sonnet (score: 0.8650)

---

## 🛠️ Common Operations

### **Check Provider Health**

```bash
curl http://localhost:8000/admin/llm/providers
```

### **View Rankings**

```bash
curl http://localhost:8000/admin/llm/rankings?agent_type=swap_agent
```

### **Check Costs**

```bash
curl http://localhost:8000/admin/llm/telemetry/cost?period=7d
```

### **Set Budget**

```bash
curl -X POST http://localhost:8000/admin/llm/budgets \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Monthly Budget",
    "budget_type": "monthly",
    "budget_amount_usd": 10000,
    "warning_threshold_percent": 80,
    "is_hard_limit": true,
    "notify_emails": ["team@example.com"]
  }'
```

### **Reset Circuit Breaker**

```bash
curl -X POST http://localhost:8000/admin/llm/circuit-breakers/{id}/reset
```

---

## 🎓 Key Concepts

### **Ranking Score Formula:**

```
Score = (w1 × Success Rate) + (w2 × Latency Score) + (w3 × Cost Score) + (w4 × Recency)

Example (swap_agent):
Score = (0.60 × 0.989) + (0.25 × 0.85) + (0.10 × 0.90) + (0.05 × 0.50)
      = 0.5934 + 0.2125 + 0.09 + 0.025
      = 0.9209 (Higher is better)
```

### **Circuit Breaker States:**

- **CLOSED**: Normal operation, all requests go through
- **OPEN**: Too many failures, blocking all requests
- **HALF_OPEN**: Testing recovery with limited requests

### **Provider Priority:**

1. **Vertex AI** (Priority 1) - Tried first
2. **DeepInfra** (Priority 2) - Fallback if Vertex fails
3. **Bedrock** (Priority 3) - Final fallback

---

## 📈 Expected Results

### **Week 1:**
- 98% success rate
- ~1.5s average latency
- ~$150/day cost (baseline)

### **Week 2-4:**
- Rankings stabilize
- Cost drops to ~$100/day (33% reduction)
- Latency improves to ~1.2s (faster models ranked higher)

### **Month 2+:**
- Full 61% cost reduction achieved
- 99.95% uptime maintained
- Rankings fully optimized

---

## 🚨 Troubleshooting

### **Problem: "No providers configured"**

**Solution:**
```bash
# Check configuration
cat config/local/.secrets.toml

# Verify environment
echo $APP_ENV

# Regenerate .env
make dotenv
```

### **Problem: "All circuit breakers open"**

**Solution:**
```bash
# Check circuit breaker states
curl http://localhost:8000/admin/llm/circuit-breakers

# Reset all
for id in $(curl http://localhost:8000/admin/llm/circuit-breakers | jq -r '.data.circuit_breakers[].id'); do
  curl -X POST http://localhost:8000/admin/llm/circuit-breakers/$id/reset
done
```

### **Problem: High costs**

**Solution:**
```bash
# Check cost breakdown
curl http://localhost:8000/admin/llm/telemetry/cost?period=24h | jq

# Adjust ranking to favor cheaper models
curl -X PUT http://localhost:8000/admin/llm/rankings/weights \
  -d '{
    "agent_type": "swap_agent",
    "weights": {
      "success_weight": 0.40,
      "latency_weight": 0.20,
      "cost_weight": 0.30,
      "recency_weight": 0.10
    }
  }'
```

---

## 📞 Support

**Documentation:**
- [README](./README.md) - Complete guide
- [Operations Guide](./OPERATIONS_GUIDE.md) - Detailed operations
- [Implementation Plan](./IMPLEMENTATION_PLAN.md) - Original plan

**Help:**
- Slack: #llm-orchestration
- Email: engineering@anvil.com

---

## ✅ Checklist for Production

**Before deploying to production:**

- [ ] All API keys configured
- [ ] Database migrated (`alembic upgrade head`)
- [ ] Budgets configured
- [ ] Alert channels configured (email, Slack)
- [ ] Monitoring setup (Prometheus, Grafana)
- [ ] Load tested (500 req/s)
- [ ] Disaster recovery tested
- [ ] Team trained on admin API
- [ ] Runbook documented
- [ ] On-call rotation established

---

**🎉 You're Ready! Start using the orchestration system now!**
