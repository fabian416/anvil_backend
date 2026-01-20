# SupervisorCoordinator Delegation Plan

## Overview

Delegate all routing responsibilities to SupervisorCoordinator:
- ✅ Price queries → Hunter AI agent
- ✅ Anvil knowledge → Chat agent (with knowledge base)
- ✅ General questions → Chat agent
- ✅ Shortcuts → Multi-step workflows via supervisor
- ✅ Multi-step operations → SupervisorCoordinator workflows

## Current State

**Guest Chat (`send_guest_message.py`)** currently has:
1. Price query check (manual pattern matching)
2. Informational query check (manual pattern matching)
3. Shortcut handling (manual pattern matching)
4. Agent Squad Supervisor (already exists but not primary)

## Target State

**All routing through SupervisorCoordinator:**
1. Remove manual price query check
2. Remove manual informational query check
3. Remove manual shortcut handling
4. Make SupervisorCoordinator the PRIMARY handler for ALL queries
5. Enhance IntentClassifier to recognize:
   - Price queries → `market_sentiment` intent → Hunter AI
   - Anvil knowledge → `general_chat` intent → Chat agent
   - General questions → `general_chat` intent → Chat agent
   - Shortcuts → `swap_tokens`, `lending`, etc. → Appropriate agents

## Implementation Steps

### Step 1: Enhance IntentClassifier
- Add price query patterns to intent classification
- Add shortcut recognition to intent classification
- Add Anvil knowledge base context to Chat agent

### Step 2: Remove Manual Routing from Guest Chat
- Remove price query check (lines 203-214)
- Remove informational query check (lines 217-296)
- Remove shortcut handling (lines 1341-1421)
- Keep only SupervisorCoordinator routing

### Step 3: Enhance SupervisorCoordinator
- Ensure it can handle single-agent queries (not just multi-agent)
- Add fallback to Chat agent for general questions
- Add shortcut workflow planning

### Step 4: Update Chat Agent
- Add Anvil knowledge base to Chat agent context
- Include shortcuts documentation in Chat agent knowledge

## Benefits

1. **Single Source of Truth**: All routing through SupervisorCoordinator
2. **LLM-Based**: No manual pattern matching
3. **Context-Aware**: Uses conversation history
4. **Extensible**: Easy to add new intents/agents
5. **Multi-Step**: Handles complex workflows automatically
