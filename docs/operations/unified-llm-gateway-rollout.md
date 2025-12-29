# Unified LLM Gateway Rollout Guide

## Overview

This document describes how to enable and test the unified LLM gateway for Agent Squad.

## Feature Flag

The unified gateway can be enabled via configuration:

```toml
# config/local/config.toml (or config/dev/, config/prod/)
[llm_provider]
use_unified_gateway = true  # Enable unified gateway
```

## Rollout Phases

### Phase 1: Local Development Testing ✅
- Set `use_unified_gateway = true` in local config
- Run integration tests
- Verify agent responses are correct

### Phase 2: Staging A/B Testing
1. Deploy with flag enabled to staging
2. Monitor metrics:
   - Response latency (should be similar)
   - Error rates (should decrease or stay same)
   - Token usage (should be comparable)
3. Compare against baseline (flag disabled)

### Phase 3: Production Canary
1. Enable for 1% of requests (requires traffic splitting)
2. Monitor for 24-48 hours
3. Gradually increase to 10%, 50%, 100%

### Phase 4: Full Rollout
1. Set `use_unified_gateway = true` in production
2. Monitor for 1 week
3. Remove legacy code path

## Monitoring Checklist

### Metrics to Watch

| Metric | Expected | Alert Threshold |
|--------|----------|-----------------|
| P50 Latency | < 500ms | > 1000ms |
| P99 Latency | < 2000ms | > 5000ms |
| Error Rate | < 1% | > 5% |
| Token Usage | Similar to baseline | +20% variance |

### Logs to Review

```bash
# Check for unified gateway activation
grep "using unified AgentLLMGateway" logs/*.log

# Check for errors
grep "AgentLLMGateway.*error" logs/*.log
```

## Rollback Procedure

If issues are detected:

1. Set `use_unified_gateway = false` in config
2. Restart application
3. Verify legacy path is active:
   ```bash
   grep "LLM client configured: primary=" logs/*.log
   ```

## Architecture Comparison

### Legacy Path (use_unified_gateway = false)
```
Agent → LLMClientGateway → LLMClientWithFallback → VertexAI/DeepInfra/OpenAI
```

### Unified Path (use_unified_gateway = true)
```
Agent → AgentLLMGateway → LLMGateway → Unified Providers
```

## Benefits of Unified Gateway

1. **Single implementation**: One LLM abstraction for entire codebase
2. **Consistent instrumentation**: Same logging, metrics, tracing
3. **Simplified maintenance**: Changes in one place
4. **Unified fallback**: Same fallback logic everywhere

## Technical Details

### AgentLLMGateway Methods

| Method | Purpose | Notes |
|--------|---------|-------|
| `chat()` | Agent conversations | Returns dict with content, tokens |
| `generate()` | Simple text generation | Direct passthrough |
| `classify_intent()` | Intent classification | JSON response parsing |
| `recommend_agents()` | Agent recommendation | JSON response parsing |
| `plan_workflow()` | Workflow planning | JSON response parsing |

### Response Format

```python
{
    "content": "Generated response...",
    "role": "assistant",
    "tokens_used": 150,
    "model": "gpt-4o-mini",
    "finish_reason": "stop",
    "latency_ms": 342
}
```

## FAQ

**Q: Will this affect existing agents?**
A: No, agents use the same interface. Only the implementation changes.

**Q: What if the unified gateway fails?**
A: The LLMGateway has its own fallback mechanism. Additionally, you can rollback via feature flag.

**Q: How do I test locally?**
A: Set `use_unified_gateway = true` in `config/local/config.toml` and run tests.
