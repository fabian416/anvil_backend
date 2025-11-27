# Celery Tasks Plan

## Overview
Plan for background tasks using Celery to handle asynchronous operations like agent processing and data caching.

## 1. Agent Processing Tasks
Handle long-running AI agent responses without blocking the HTTP request.

### Tasks:
- `process_agent_response`:
    - **Input**: `conversation_id`, `user_message_id`, `agent_type`.
    - **Logic**:
        1.  Retrieve conversation context.
        2.  Call AI service (via `AgentGateway`).
        3.  Store agent response in database.
        4.  (Optional) Push update via WebSocket.
- **Location**: `src/app/infrastructure/celery/tasks/process_agent_response.py`

## 2. Data Caching Tasks
Periodically refresh DeFi data to ensure quick responses.

### Tasks:
- `update_defi_data_cache`:
    - **Schedule**: Every 5-15 minutes (Configurable).
    - **Logic**:
        1.  Fetch data from external providers (1inch, DeFiLlama).
        2.  Update Redis cache.
- **Location**: `src/app/infrastructure/celery/tasks/update_defi_data_cache.py`

## 3. Implementation Steps
1.  **Define Task Wrappers**: Create task functions decorated with `@celery_app.task`.
2.  **Implement Logic**: Write the async runner function that resolves dependencies via Dishka container.
3.  **Register Tasks**: Ensure tasks are imported/registered in `src/app/infrastructure/celery/app.py`.
4.  **Schedule Tasks**: Add periodic tasks to `celery_app.conf.beat_schedule`.

## 4. Integration per Endpoint
- **Send Message Endpoint**:
    - After saving the user message, trigger `process_agent_response.delay(...)`.
    - Return "Message accepted" status immediately.
