# Persistence SQLAlchemy Implementation Plan

## Overview
This plan covers the implementation of SQLAlchemy models and mappings in the `src/app/infrastructure/persistence_sqla` directory.

## 1. Model Modifications
Modify existing models or create new ones to support the required features (DeFi Chat, User/Admin features).

### Files to Modify/Create:
- `src/app/infrastructure/persistence_sqla/mappings/user.py`: Ensure user model supports roles (admin/user) and necessary profile fields.
- `src/app/infrastructure/persistence_sqla/mappings/conversation.py`: Create mapping for Conversation entity.
- `src/app/infrastructure/persistence_sqla/mappings/message.py`: Create mapping for Message entity.
- `src/app/infrastructure/persistence_sqla/mappings/agent_session.py`: Create mapping for Agent Session entity.

### Steps:
1.  **Review Existing Mappings**: Check `mappings/user.py` and others.
2.  **Define New Mappings**: Implement mappings for `Conversation`, `Message`, and `AgentSession` based on the domain entities defined in `docs/steering/structure.md`.
3.  **Update Registry**: Ensure new mappings are registered in `src/app/infrastructure/persistence_sqla/registry.py`.

## 2. Implementation of Models
Implement the actual table structures and relationships.

### Key Relationships:
- **User <-> Conversation**: One-to-Many (One user has many conversations).
- **Conversation <-> Message**: One-to-Many (One conversation has many messages).
- **Conversation <-> AgentSession**: One-to-Many (One conversation can have multiple agent sessions/states).

### Steps:
1.  **Create/Update Mapping Files**: Write the SQLAlchemy `Table` definitions and `mapper_registry.map_imperatively` calls.
2.  **Database Migrations**: Generate Alembic migrations for the new tables.
    - Command: `alembic revision --autogenerate -m "Add chat feature tables"`
    - Review and apply: `alembic upgrade head`

## 3. Dummy Data Generation
Create scripts or fixtures to populate the database with dummy data for testing.

### Data to Generate:
- **Users**: Admin users, Regular users.
- **Conversations**: Sample conversations for testing history.
- **Messages**: Sample messages between users and agents.

### Implementation:
- Create a script in `scripts/seed_data.py` or similar to insert this data using the application's repositories or direct SQLA session.
