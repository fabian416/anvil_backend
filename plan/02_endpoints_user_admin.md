# User and Admin Endpoints Implementation Plan

## Overview
This plan covers the implementation of HTTP endpoints for Users and Admins, including dummy data integration for development.

## 1. User Endpoints (`/api/v1/user`)
Endpoints for regular user operations, primarily focusing on the chat feature and profile management.

### Endpoints to Implement:
- `GET /api/v1/user/profile`: Get current user profile.
- `PUT /api/v1/user/profile`: Update user profile.
- `POST /api/v1/chat/conversations`: Start a new conversation.
- `GET /api/v1/chat/conversations`: List user conversations.
- `GET /api/v1/chat/conversations/{conversation_id}`: Get conversation details.
- `POST /api/v1/chat/conversations/{conversation_id}/messages`: Send a message.

### Structure:
- **Controller**: `src/app/presentation/http/controllers/chat/`
- **Schemas**: `src/app/presentation/http/schemas/chat/`

### Dummy Data:
- For initial development, endpoints will return dummy data if the backend logic isn't fully ready.
- Example: `List Conversations` returns a static list of mock conversations.

## 2. Admin Endpoints (`/api/v1/admin`)
Endpoints for administrative tasks.

### Endpoints to Implement:
- `GET /api/v1/admin/users`: List all users (already likely exists, check `src/app/presentation/http/controllers/admin/user`).
- `GET /api/v1/admin/stats`: Get system statistics (active conversations, agent usage).
- `GET /api/v1/admin/agents`: Manage/View agent configurations.

### Structure:
- **Controller**: `src/app/presentation/http/controllers/admin/`
- **Schemas**: `src/app/presentation/http/schemas/admin/`

### Dummy Data:
- `GET /api/v1/admin/stats` will return hardcoded statistics for UI testing.

## 3. Implementation Steps
1.  **Define Schemas**: Create Pydantic models for Requests and Responses in `src/app/presentation/http/schemas/`.
2.  **Create Routers**: Define `APIRouter` in `src/app/presentation/http/controllers/`.
3.  **Implement Controllers**: Write async functions for each endpoint.
    - **Phase 1 (Dummy)**: Return static JSON objects matching the response schema.
    - **Phase 2 (Real)**: Inject Application Interactors (`Depends(FromDishka[Interactor])`) and call business logic.
4.  **Register Routers**: Add new routers to the main API router in `src/app/presentation/http/api_v1_router.py` or similar.
