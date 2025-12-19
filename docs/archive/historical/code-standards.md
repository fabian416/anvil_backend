# Code Standards and Conventions

**Purpose**: Coding standards, naming conventions, and best practices  
**Audience**: All developers

---

## 📋 Table of Contents

1. [Naming Conventions](#naming-conventions)
2. [Code Organization](#code-organization)
3. [Import Patterns](#import-patterns)
4. [Type Hints](#type-hints)
5. [Docstrings](#docstrings)
6. [Code Formatting](#code-formatting)

---

## 🏷️ Naming Conventions

### Files

- **Python files**: `snake_case.py`
- **Test files**: `test_*.py` or `*_test.py`
- **Module directories**: `snake_case/`

### Code

- **Classes/Types**: `PascalCase`
- **Functions/Methods**: `snake_case`
- **Constants**: `UPPER_SNAKE_CASE`
- **Variables**: `snake_case`
- **Private/Internal**: Prefix with `_`

### Domain-Specific

- **Entities**: Singular noun, `PascalCase` (e.g., `Conversation`)
- **Value Objects**: Descriptive noun phrase, `PascalCase` (e.g., `MessageRole`)
- **Repositories**: `{Entity}Repository` (e.g., `ConversationRepository`)
- **Gateways**: `{Purpose}Gateway` (e.g., `AgentGateway`)
- **Interactors**: Verb phrase (e.g., `CreateConversation`)
- **Controllers**: Verb phrase or noun (e.g., `create_conversation`)

---

## 📁 Code Organization

### File Structure

```python
"""
Module docstring.
"""
# 1. Imports
# 2. Constants
# 3. Type/interface definitions
# 4. Class attributes
# 5. __init__ and properties
# 6. Public methods
# 7. Private methods
# 8. Class methods and static methods
```

### Function Structure

```python
def function_name(param: Type) -> ReturnType:
    """
    Function docstring.
    """
    # 1. Input validation
    # 2. Core logic
    # 3. Error handling
    # 4. Return result
```

---

## 📦 Import Patterns

### Import Order

1. Standard library imports
2. Third-party library imports
3. Application imports (from `app.`)
4. Relative imports (within same module)

### Example

```python
# Standard library
from datetime import datetime
from typing import Optional
from uuid import UUID

# Third-party
from sqlalchemy import select
from pydantic import BaseModel

# Application (absolute imports - modular structure)
from app.domain.chat.entities.conversation import Conversation
from app.domain.chat.entities.message import Message
from app.domain.chat.value_objects.message_role import MessageRole
from app.domain.chat.ports.conversation_repository import ConversationRepository

# Relative imports (within same package)
from .base import BaseEntity
```

### Modular Import Pattern

**✅ DO**: Use modular imports
```python
from app.domain.chat.entities.conversation import Conversation
from app.domain.transactions.entities.transaction import Transaction
from app.domain.portfolio.entities.user_portfolio import UserPortfolio
```

**❌ DON'T**: Use old flat structure
```python
from app.domain.entities.conversation import Conversation  # ❌
from app.domain.entities.transaction import Transaction    # ❌
```

---

## 🔤 Type Hints

### Required

All function signatures must include type hints:

```python
def process_message(
    conversation_id: UUID,
    content: str,
    role: MessageRole,
) -> Message:
    pass
```

### Optional Types

```python
from typing import Optional

def get_conversation(id: UUID) -> Optional[Conversation]:
    pass
```

### Union Types

```python
from typing import Union

def process(value: Union[str, int]) -> str:
    pass
```

---

## 📝 Docstrings

### Format

Google-style docstrings:

```python
def create_conversation(user_id: UUID) -> Conversation:
    """
    Create a new conversation for a user.
    
    Args:
        user_id: The user identifier
        
    Returns:
        Created conversation entity
        
    Raises:
        UserNotFoundError: If user doesn't exist
    """
    pass
```

### Required For

- All public classes, methods, and functions
- Complex business logic (inline comments)
- Module-level docstrings for major modules

---

## 🎨 Code Formatting

### Tool

**ruff** (replaces black, isort, flake8)

```bash
make code.format  # Format code
make code.lint    # Check formatting and lint
```

### Line Length

- **Maximum**: 88 characters (ruff default)
- **Preferred**: 80 characters

### Type Checking

**mypy** with strict mode

```bash
make code.lint  # Runs mypy
```

---

## 📏 Code Size Guidelines

### File Size

- **Maximum**: 500 lines
- **Preferred**: 200-300 lines
- **Action**: Split if exceeds 500 lines

### Function Size

- **Maximum**: 50 lines
- **Preferred**: 10-20 lines
- **Action**: Extract helper functions if exceeds 50 lines

### Complexity

- **Cyclomatic Complexity**: Keep below 10 per function
- **Nesting Depth**: Maximum 3 levels (prefer 2)

---

## ✅ Best Practices

### DO

- ✅ Use type hints for all functions
- ✅ Write docstrings for public APIs
- ✅ Follow naming conventions
- ✅ Keep functions small and focused
- ✅ Use meaningful variable names
- ✅ Handle errors explicitly

### DON'T

- ❌ Use `any` type (use `Any` from typing if needed)
- ❌ Skip type hints
- ❌ Write functions longer than 50 lines
- ❌ Use magic numbers (use constants)
- ❌ Ignore linting errors
- ❌ Mix concerns in single function

---

## 🔗 Related Documentation

- **[Project Structure](../steering/structure.md)** - Code organization
- **[Hexagonal Architecture](../architecture/hexagonal-architecture.md)** - Architecture patterns
- **[Testing Guide](../testing/README.md)** - Testing standards

---

**Last Updated**: December 19, 2025

