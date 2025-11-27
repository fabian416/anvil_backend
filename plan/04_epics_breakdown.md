# Epic Stories Breakdown

## Overview
Breakdown of the implementation into manageable Epic stories.

## Epic 1: Core Data Layer & Models
**Goal**: Establish the database schema and persistence layer for the Chat feature.

### Stories:
1.  **Define Domain Entities**: Create `Conversation`, `Message`, `Agent`, `AgentSession` in Domain layer.
2.  **Implement SQLA Mappings**: Create SQLAlchemy mappings in Infrastructure layer.
3.  **Database Migration**: Generate and run Alembic migrations.
4.  **Seed Dummy Data**: Create script to populate DB with test users and conversations.

## Epic 2: User Chat Interface (API)
**Goal**: Allow users to interact with the system via API.

### Stories:
1.  **Conversation Management**: Implement `create_conversation`, `list_conversations`, `get_conversation` endpoints (Dummy -> Real).
2.  **Messaging**: Implement `send_message` endpoint (Dummy -> Real).
3.  **Profile Access**: Ensure user profile endpoints are functional.

## Epic 3: Agent Integration & Background Processing
**Goal**: Connect the chat interface to the AI agents via background tasks.

### Stories:
1.  **Celery Setup for Agents**: Create `process_agent_response` task skeleton.
2.  **Agent Gateway Mock**: Create a mock implementation of `AgentGateway` for testing.
3.  **Connect API to Task**: Trigger Celery task on `send_message`.
4.  **Real Agent Integration**: Replace mock gateway with actual OpenAI/LLM integration.

## Epic 4: Admin Dashboard & Analytics
**Goal**: Provide administrative visibility.

### Stories:
1.  **Admin Stats Endpoint**: Implement `GET /stats` with dummy data.
2.  **Agent Management**: Implement `GET /agents` to list available agents.
3.  **Real Analytics**: Connect stats endpoint to real database queries.

## Epic 5: DeFi Data Integration
**Goal**: Enable agents to access real-time DeFi data.

### Stories:
1.  **Data Provider Ports**: Define interfaces for data providers.
2.  **Caching Tasks**: Implement `update_defi_data_cache` Celery task.
3.  **Provider Adapters**: Implement adapters for 1inch, DeFiLlama.
