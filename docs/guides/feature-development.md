# Feature Development Guide

**Purpose**: Step-by-step guide for adding new features  
**Audience**: Developers

---

## 🎯 Overview

This guide walks you through adding a new feature following hexagonal architecture and modular organization.

---

## 📋 Step-by-Step Process

### Step 1: Define Domain Layer

#### 1.1 Create Module Structure

```bash
mkdir -p src/app/domain/{feature_name}/{entities,value_objects,ports,services}
```

#### 1.2 Define Entities

```python
# src/app/domain/{feature_name}/entities/{entity}.py
from dataclasses import dataclass
from uuid import UUID

@dataclass
class MyEntity:
    id: UUID
    name: str
    # ... other fields
```

#### 1.3 Define Value Objects

```python
# src/app/domain/{feature_name}/value_objects/{value_object}.py
from dataclasses import dataclass

@dataclass(frozen=True)
class MyValueObject:
    value: str
```

#### 1.4 Define Ports (Interfaces)

```python
# src/app/domain/{feature_name}/ports/{repository}.py
from typing import Protocol
from app.domain.{feature_name}.entities.my_entity import MyEntity

class MyRepository(Protocol):
    async def save(self, entity: MyEntity) -> None: ...
    async def get_by_id(self, id: UUID) -> MyEntity | None: ...
```

#### 1.5 Create __init__.py Files

```python
# src/app/domain/{feature_name}/__init__.py
from app.domain.{feature_name}.entities.my_entity import MyEntity

__all__ = ["MyEntity"]
```

---

### Step 2: Implement Application Layer

#### 2.1 Create Module Structure

```bash
mkdir -p src/app/application/{feature_name}/{commands,queries,services}
```

#### 2.2 Create Command (Write Operation)

```python
# src/app/application/{feature_name}/commands/create_{entity}.py
from uuid import UUID
from app.domain.{feature_name}.entities.my_entity import MyEntity
from app.domain.{feature_name}.ports.my_repository import MyRepository

class CreateMyEntity:
    def __init__(self, repository: MyRepository):
        self._repository = repository
    
    async def execute(self, name: str) -> MyEntity:
        entity = MyEntity.create(name)
        await self._repository.save(entity)
        return entity
```

#### 2.3 Create Query (Read Operation)

```python
# src/app/application/{feature_name}/queries/get_{entity}.py
from uuid import UUID
from app.domain.{feature_name}.ports.my_repository import MyRepository

class GetMyEntity:
    def __init__(self, repository: MyRepository):
        self._repository = repository
    
    async def execute(self, id: UUID) -> MyEntity | None:
        return await self._repository.get_by_id(id)
```

---

### Step 3: Implement Infrastructure Layer

#### 3.1 Implement Repository Adapter

```python
# src/app/infrastructure/adapters/{feature_name}_repository_sqla.py
from app.domain.{feature_name}.entities.my_entity import MyEntity
from app.domain.{feature_name}.ports.my_repository import MyRepository

class MyRepositorySqla(MyRepository):
    def __init__(self, session: AsyncSession):
        self._session = session
    
    async def save(self, entity: MyEntity) -> None:
        # SQLAlchemy implementation
        pass
```

#### 3.2 Create Database Mapping

```python
# src/app/infrastructure/persistence_sqla/mappings/{feature_name}.py
from sqlalchemy import Column, String
from app.infrastructure.persistence_sqla.mappings.base import Base

class MyEntityTable(Base):
    __tablename__ = "my_entities"
    
    id = Column(UUID, primary_key=True)
    name = Column(String, nullable=False)
```

---

### Step 4: Create Presentation Layer

#### 4.1 Create Request/Response Schemas

```python
# src/app/presentation/http/schemas/{feature_name}.py
from pydantic import BaseModel

class CreateMyEntityRequest(BaseModel):
    name: str

class MyEntityResponse(BaseModel):
    id: str
    name: str
```

#### 4.2 Create Controller

```python
# src/app/presentation/http/controllers/{feature_name}/router.py
from fastapi import APIRouter, Depends
from dishka.integrations.fastapi import FromDishka, inject
from app.application.{feature_name}.commands.create_my_entity import CreateMyEntity
from app.presentation.http.schemas.{feature_name} import CreateMyEntityRequest, MyEntityResponse

router = APIRouter(prefix="/user/{feature_name}", tags=["{feature_name}"])

@router.post("/", response_model=MyEntityResponse)
@inject
async def create_entity(
    request: CreateMyEntityRequest,
    interactor: FromDishka[CreateMyEntity],
) -> MyEntityResponse:
    entity = await interactor.execute(request.name)
    return MyEntityResponse.from_domain(entity)
```

---

### Step 5: Register Dependencies

#### 5.1 Register in Infrastructure Provider

```python
# src/app/setup/ioc/infrastructure.py
from app.infrastructure.adapters.{feature_name}_repository_sqla import MyRepositorySqla
from app.domain.{feature_name}.ports.my_repository import MyRepository

class InfrastructureProvider(Provider):
    @provide
    def get_my_repository(
        self, adapter: MyRepositorySqla
    ) -> MyRepository:
        return adapter
```

#### 5.2 Register in Application Provider

```python
# src/app/setup/ioc/application.py
from app.application.{feature_name}.commands.create_my_entity import CreateMyEntity

class ApplicationProvider(Provider):
    @provide
    def get_create_my_entity(
        self, repository: MyRepository
    ) -> CreateMyEntity:
        return CreateMyEntity(repository)
```

---

### Step 6: Register Routes

```python
# src/app/presentation/http/controllers/api_v1_router.py
from app.presentation.http.controllers.{feature_name}.router import router as {feature_name}_router

def create_api_v1_router() -> APIRouter:
    router = APIRouter(prefix="/api/v1")
    router.include_router({feature_name}_router)
    return router
```

---

### Step 7: Create Database Migration

```bash
alembic revision --autogenerate -m "Add {feature_name} tables"
alembic upgrade head
```

---

### Step 8: Write Tests

#### 8.1 Unit Tests

```python
# tests/unit/domain/{feature_name}/test_my_entity.py
def test_create_entity():
    entity = MyEntity.create("Test")
    assert entity.name == "Test"
```

#### 8.2 Integration Tests

```python
# tests/integration/{feature_name}/test_my_entity_api.py
async def test_create_entity_endpoint(client):
    response = await client.post("/api/v1/user/{feature_name}/", json={"name": "Test"})
    assert response.status_code == 201
```

---

## ✅ Checklist

- [ ] Domain layer created (entities, value objects, ports)
- [ ] Application layer created (commands, queries)
- [ ] Infrastructure adapters implemented
- [ ] Presentation layer created (controllers, schemas)
- [ ] Dependencies registered in IoC
- [ ] Routes registered
- [ ] Database migration created
- [ ] Tests written (unit and integration)
- [ ] Documentation updated

---

## 📚 Related Documentation

- **[Architecture Guide](../architecture/README.md)** - Architecture patterns
- **[Code Standards](code-standards.md)** - Coding conventions
- **[Testing Guide](../testing/README.md)** - Testing practices
- **[API Development](../api/README.md)** - API development

---

**Last Updated**: December 19, 2025

