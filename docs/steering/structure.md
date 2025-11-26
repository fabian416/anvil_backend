# Project Structure

## Directory Organization

```
project-root/
├── config/                          # Environment-specific configuration
│   ├── local/                       # Local development config
│   ├── dev/                         # Development environment config
│   └── prod/                        # Production environment config
├── src/                             # Source code
│   └── app/
│       ├── domain/                  # Domain layer (business logic)
│       │   ├── entities/            # Domain entities with identity
│       │   ├── value_objects/       # Immutable value objects
│       │   ├── services/            # Domain services
│       │   └── ports/               # Port interfaces (abstractions)
│       ├── application/             # Application layer (use cases)
│       │   ├── commands/            # Write operations (CQRS)
│       │   ├── queries/             # Read operations (CQRS)
│       │   └── common/               # Shared application logic
│       ├── infrastructure/          # Infrastructure layer (adapters)
│       │   ├── adapters/            # Port implementations
│       │   ├── persistence_sqla/    # Database adapters
│       │   ├── celery/              # Background task processing
│       │   └── auth/                 # Authentication adapters
│       ├── presentation/             # Presentation layer (HTTP)
│       │   └── http/
│       │       ├── controllers/      # Route handlers
│       │       ├── schemas/          # Request/response models
│       │       └── errors/           # Error handling
│       ├── setup/                   # Application setup
│       │   ├── ioc/                 # Dependency injection config
│       │   └── config/              # Settings management
│       └── run.py                   # Application entry point
├── tests/                           # Test files
│   ├── unit/                        # Unit tests
│   ├── integration/                 # Integration tests
│   └── fixtures/                    # Test data and fixtures
├── docs/                            # Documentation
│   ├── steering/                    # Steering documents (this directory)
│   ├── architecture/                # Architecture documentation
│   └── api/                         # API documentation
├── scripts/                          # Utility scripts
├── config/                          # Configuration files
├── Makefile                         # Development shortcuts
└── pyproject.toml                   # Project metadata and tooling config
```

### DeFi Multi-Agents Chat Specific Structure

For the DeFi multi-agents chat feature, the following structure will be added:

```
src/app/
├── domain/
│   ├── entities/
│   │   ├── conversation.py          # Conversation entity
│   │   ├── message.py               # Message entity
│   │   ├── agent.py                 # Agent entity
│   │   └── agent_session.py          # Agent session state
│   ├── value_objects/
│   │   ├── agent_type.py             # Agent type enum/value object
│   │   ├── message_role.py           # Message role (user/agent/system)
│   │   └── conversation_context.py   # Conversation context value object
│   ├── services/
│   │   └── agent_orchestrator.py     # Domain service for agent coordination
│   └── ports/
│       ├── agent_gateway.py          # Interface for agent interactions
│       ├── conversation_repository.py # Conversation persistence interface
│       └── defi_data_provider.py     # DeFi data source interface
├── application/
│   ├── commands/
│   │   ├── create_conversation.py    # Start new conversation
│   │   ├── send_message.py           # Send user message
│   │   ├── route_to_agent.py         # Route message to specific agent
│   │   └── update_agent_state.py      # Update agent session state
│   ├── queries/
│   │   ├── get_conversation.py       # Retrieve conversation history
│   │   ├── list_conversations.py     # List user conversations
│   │   ├── get_agent_capabilities.py  # Get available agents and capabilities
│   │   └── search_conversations.py   # Search conversation history
│   └── common/
│       └── ports/
│           ├── conversation_query_gateway.py # Read-optimized conversation access
│           └── conversation_command_gateway.py # Write-optimized conversation access
├── infrastructure/
│   ├── adapters/
│   │   ├── conversation_repository_sqla.py    # SQLAlchemy conversation adapter
│   │   ├── agent_gateway_openai.py            # OpenAI agent implementation
│   │   ├── defi_data_provider_1inch.py        # 1inch DEX data adapter
│   │   ├── defi_data_provider_defillama.py    # DeFiLlama adapter
│   │   └── defi_data_provider_thegraph.py     # The Graph adapter
│   ├── persistence_sqla/
│   │   └── mappings/
│   │       ├── conversation.py        # Conversation table mapping
│   │       ├── message.py            # Message table mapping
│   │       └── agent_session.py      # Agent session table mapping
│   └── celery/
│       └── tasks/
│           ├── process_agent_response.py      # Background agent processing
│           └── update_defi_data_cache.py       # Cache refresh tasks
└── presentation/
    └── http/
        ├── controllers/
        │   └── chat/
        │       ├── router.py         # Chat routes
        │       ├── create_conversation.py
        │       ├── send_message.py
        │       ├── get_conversation.py
        │       └── list_conversations.py
        └── schemas/
            └── chat/
                ├── conversation.py    # Conversation request/response schemas
                ├── message.py        # Message schemas
                └── agent.py          # Agent schemas
```

## Naming Conventions

### Files
- **Components/Modules**: `snake_case.py` (Python standard)
- **Services/Handlers**: `snake_case.py` (e.g., `agent_gateway.py`, `conversation_service.py`)
- **Utilities/Helpers**: `snake_case.py` (e.g., `defi_utils.py`, `message_formatter.py`)
- **Tests**: `test_*.py` or `*_test.py` (e.g., `test_conversation_repository.py`)

### Code
- **Classes/Types**: `PascalCase` (e.g., `Conversation`, `AgentGateway`, `MessageRole`)
- **Functions/Methods**: `snake_case` (e.g., `create_conversation`, `send_message`, `get_agent_response`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_MESSAGE_LENGTH`, `DEFAULT_AGENT_TIMEOUT`)
- **Variables**: `snake_case` (e.g., `conversation_id`, `user_message`, `agent_response`)
- **Private/Internal**: Prefix with single underscore `_` (e.g., `_internal_method`, `_cache_key`)

### Domain-Specific Naming
- **Entities**: Singular noun, PascalCase (e.g., `Conversation`, `Message`, `Agent`)
- **Value Objects**: Descriptive noun phrase, PascalCase (e.g., `AgentType`, `MessageRole`, `ConversationContext`)
- **Repositories**: `{Entity}Repository` (e.g., `ConversationRepository`)
- **Gateways**: `{Purpose}Gateway` (e.g., `AgentGateway`, `DefiDataGateway`)
- **Interactors**: Verb phrase describing action (e.g., `CreateConversation`, `SendMessage`, `RouteToAgent`)
- **Controllers**: Verb phrase or noun describing endpoint (e.g., `create_conversation`, `send_message`)

## Import Patterns

### Import Order
1. Standard library imports
2. Third-party library imports
3. Application imports (from `app.`)
4. Relative imports (within same module)

### Module/Package Organization
- **Absolute imports from project root**: Use `from app.domain.entities.conversation import Conversation`
- **Relative imports within module**: Use `from .message import Message` when in same package
- **Avoid circular dependencies**: Domain layer should never import from outer layers

### Example Import Structure
```python
# Standard library
from datetime import datetime
from typing import Optional
from uuid import UUID

# Third-party
from sqlalchemy import select
from pydantic import BaseModel

# Application (absolute imports)
from app.domain.entities.conversation import Conversation
from app.domain.value_objects.message_role import MessageRole
from app.application.common.ports.conversation_query_gateway import ConversationQueryGateway

# Relative imports (within same package)
from .base import BaseEntity
```

## Code Structure Patterns

### Module/Class Organization
```python
"""
Module docstring describing purpose.
"""
# 1. Imports
from typing import Optional
from app.domain.entities.base import BaseEntity

# 2. Constants
MAX_MESSAGE_LENGTH = 10000

# 3. Type/interface definitions
class Conversation(BaseEntity):
    """Conversation entity docstring."""
    
    # 4. Class attributes
    # 5. __init__ and properties
    # 6. Public methods
    # 7. Private methods
    # 8. Class methods and static methods
```

### Function/Method Organization
```python
def send_message(
    self,
    conversation_id: UUID,
    content: str,
    role: MessageRole,
) -> Message:
    """
    Function docstring.
    
    Args:
        conversation_id: The conversation identifier
        content: Message content
        role: Message role (user/agent/system)
    
    Returns:
        Created message entity
    
    Raises:
        ConversationNotFoundError: If conversation doesn't exist
    """
    # 1. Input validation
    if not content or len(content) > MAX_MESSAGE_LENGTH:
        raise ValueError("Invalid message content")
    
    # 2. Core logic
    conversation = self._get_conversation(conversation_id)
    message = Message.create(conversation_id, content, role)
    
    # 3. Persistence
    self._repository.save(message)
    
    # 4. Return result
    return message
```

### File Organization Principles
- **One class per file**: Each entity, value object, or major class gets its own file
- **Related functionality grouped**: Related utilities or helpers can be in the same file
- **Public API at module level**: Expose main classes/functions via `__init__.py`
- **Implementation details hidden**: Private methods and internal utilities use `_` prefix

## Code Organization Principles

1. **Single Responsibility**: Each file, class, and function should have one clear purpose
2. **Modularity**: Code organized into reusable, independent modules
3. **Testability**: Structure code to be easily testable with clear dependencies
4. **Consistency**: Follow established patterns throughout the codebase
5. **Layer Separation**: Strict adherence to hexagonal architecture layers

## Module Boundaries

### Layer Boundaries
- **Domain Layer**: 
  - Cannot depend on any other layer
  - Defines ports (interfaces) for external dependencies
  - Contains pure business logic
  
- **Application Layer**: 
  - Depends only on Domain layer
  - Implements use cases via interactors
  - Orchestrates domain logic and external calls
  
- **Infrastructure Layer**: 
  - Implements Domain and Application ports
  - Contains all external system integrations
  - Can depend on Domain layer only
  
- **Presentation Layer**: 
  - Depends on Application and Domain layers
  - Handles HTTP requests/responses
  - Validates input, delegates to Application layer

### Feature Boundaries (DeFi Chat)
- **Chat Core**: Conversation and message management
- **Agent System**: Agent orchestration and routing
- **DeFi Integration**: External DeFi data providers
- **User Context**: User preferences and session management

### Dependency Direction Rules
- Inner layers define interfaces (ports)
- Outer layers implement interfaces (adapters)
- Dependencies point inward only
- No circular dependencies between layers

## Code Size Guidelines

### File Size
- **Maximum lines per file**: 500 lines
- **Preferred**: 200-300 lines
- **Action required**: If file exceeds 500 lines, consider splitting into smaller modules

### Function/Method Size
- **Maximum lines per function**: 50 lines
- **Preferred**: 10-20 lines
- **Action required**: If function exceeds 50 lines, extract helper functions or split logic

### Class/Module Complexity
- **Maximum methods per class**: 15 methods
- **Cyclomatic complexity**: Keep below 10 per function
- **Action required**: If complexity is high, refactor into smaller, focused classes

### Nesting Depth
- **Maximum nesting levels**: 3 levels deep
- **Preferred**: 2 levels deep
- **Action required**: If nesting exceeds 3 levels, extract functions or use early returns

## DeFi Chat Specific Structure Guidelines

### Conversation Management
- Conversations are isolated by user
- Each conversation maintains its own context and agent state
- Message history stored chronologically with timestamps

### Agent Architecture
- Agents are pluggable and can be added/removed without core changes
- Each agent has defined capabilities and input/output contracts
- Agent state is maintained per conversation session

### Data Integration
- DeFi data providers abstracted behind ports
- Caching layer for frequently accessed data
- Background tasks for data refresh and agent processing

## Documentation Standards
- **Public APIs**: All public classes, methods, and functions must have docstrings
- **Complex Logic**: Inline comments for non-obvious business logic
- **README files**: Each major module should have a README explaining its purpose
- **Type Hints**: All function signatures must include type hints
- **Docstring Format**: Use Google-style docstrings for consistency
