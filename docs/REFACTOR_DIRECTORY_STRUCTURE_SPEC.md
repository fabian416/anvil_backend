# Especificación: Refactor de Estructura de Directorios por Módulos

**Fecha:** 19 de Diciembre, 2025  
**Estado:** 📋 **ESPECIFICACIÓN**  
**Alcance:** Domain y Application layers (excluyendo Infrastructure)

## Objetivo

Reorganizar la estructura de directorios de las capas Domain y Application para seguir un patrón modular consistente, donde cada módulo de negocio tenga su propia carpeta con todas sus entidades, value objects, ports, servicios, commands y queries agrupados.

## Principios de Diseño

1. **Modularidad**: Cada módulo de negocio tiene su propia carpeta
2. **Consistencia**: Misma estructura para todos los módulos
3. **Separación de Capas**: Mantener Domain y Application separados
4. **CQRS**: Mantener commands y queries separados en Application layer
5. **Escalabilidad**: Fácil agregar nuevos módulos siguiendo el patrón

## Módulos a Refactorizar

Los siguientes módulos fueron actualizados en los endpoints y necesitan refactorización:

1. **Graph** (GraphRAG)
2. **ML** (Machine Learning)
3. **Alerts** (Risk Alerts)
4. **Dashboard**
5. **Comparison** (Protocol Comparison)
6. **Markets**
7. **Transactions**
8. **Bitcoin**
9. **Portfolio**
10. **Hunter AI** (6 sub-módulos)
11. **ULTRA** (4 sub-módulos)
12. **Projects**
13. **Search**
14. **Preferences**
15. **Chat** (ya parcialmente organizado)
16. **Atlas**

## Estructura Actual vs Propuesta

### Estructura Actual

```
src/app/
├── domain/
│   ├── entities/              # Entidades dispersas
│   │   ├── risk_alert.py
│   │   ├── user_portfolio.py
│   │   ├── user_preferences.py
│   │   └── ...
│   ├── value_objects/         # Value objects dispersos
│   │   └── ...
│   ├── ports/                 # Ports dispersos
│   │   ├── analytics_repository.py
│   │   ├── portfolio/
│   │   └── ...
│   └── services/             # Servicios parcialmente organizados
│       ├── graph/
│       ├── ml/
│       └── ...
│
├── application/
│   ├── commands/             # Commands parcialmente organizados
│   │   ├── chat/
│   │   └── ...
│   ├── queries/              # Queries parcialmente organizados
│   │   ├── admin/
│   │   └── ...
│   ├── graph/                # ✅ Ya organizado
│   ├── ml/                   # ✅ Ya organizado
│   ├── alerts/               # ✅ Ya organizado
│   ├── dashboard/            # ✅ Ya organizado
│   ├── comparison/          # ✅ Ya organizado
│   ├── markets/             # ✅ Ya organizado
│   ├── portfolio/           # ✅ Ya organizado
│   ├── hunter/              # ✅ Ya organizado
│   ├── ultra/               # ✅ Ya organizado
│   ├── projects/            # ✅ Ya organizado
│   ├── search/              # ✅ Ya organizado
│   ├── preferences/         # ✅ Ya organizado
│   ├── chat/                # ✅ Ya organizado
│   └── atlas/               # ✅ Ya organizado
```

### Estructura Propuesta

```
src/app/
├── domain/
│   ├── graph/                    # Módulo GraphRAG
│   │   ├── entities/
│   │   │   └── __init__.py
│   │   ├── value_objects/
│   │   │   └── __init__.py
│   │   ├── ports/
│   │   │   ├── graph_repository.py
│   │   │   ├── vector_repository.py
│   │   │   └── __init__.py
│   │   ├── services/
│   │   │   ├── graph_service.py
│   │   │   ├── pagerank.py
│   │   │   ├── risk_analysis_service.py
│   │   │   └── __init__.py
│   │   └── __init__.py
│   │
│   ├── ml/                       # Módulo Machine Learning
│   │   ├── entities/
│   │   │   └── __init__.py
│   │   ├── value_objects/
│   │   │   └── __init__.py
│   │   ├── ports/
│   │   │   └── __init__.py
│   │   ├── services/
│   │   │   ├── network_analysis_service.py
│   │   │   ├── risk_prediction_service.py
│   │   │   └── __init__.py
│   │   └── __init__.py
│   │
│   ├── alerts/                   # Módulo Risk Alerts
│   │   ├── entities/
│   │   │   └── risk_alert.py
│   │   ├── value_objects/
│   │   │   └── __init__.py
│   │   ├── ports/
│   │   │   └── __init__.py
│   │   ├── services/
│   │   │   └── __init__.py
│   │   └── __init__.py
│   │
│   ├── dashboard/                # Módulo Dashboard
│   │   ├── entities/
│   │   │   └── __init__.py
│   │   ├── value_objects/
│   │   │   └── __init__.py
│   │   ├── ports/
│   │   │   └── __init__.py
│   │   ├── services/
│   │   │   └── __init__.py
│   │   └── __init__.py
│   │
│   ├── comparison/               # Módulo Protocol Comparison
│   │   ├── entities/
│   │   │   └── __init__.py
│   │   ├── value_objects/
│   │   │   └── __init__.py
│   │   ├── ports/
│   │   │   └── __init__.py
│   │   ├── services/
│   │   │   └── __init__.py
│   │   └── __init__.py
│   │
│   ├── markets/                  # Módulo Markets
│   │   ├── entities/
│   │   │   └── __init__.py
│   │   ├── value_objects/
│   │   │   └── __init__.py
│   │   ├── ports/
│   │   │   └── __init__.py
│   │   ├── services/
│   │   │   └── __init__.py
│   │   └── __init__.py
│   │
│   ├── transactions/             # Módulo Transactions
│   │   ├── entities/
│   │   │   └── transaction.py
│   │   ├── value_objects/
│   │   │   └── __init__.py
│   │   ├── ports/
│   │   │   └── transaction/
│   │   │       ├── transaction_repository.py
│   │   │       └── __init__.py
│   │   ├── services/
│   │   │   └── __init__.py
│   │   └── __init__.py
│   │
│   ├── bitcoin/                  # Módulo Bitcoin
│   │   ├── entities/
│   │   │   └── __init__.py
│   │   ├── value_objects/
│   │   │   └── __init__.py
│   │   ├── ports/
│   │   │   └── __init__.py
│   │   ├── services/
│   │   │   └── __init__.py
│   │   └── __init__.py
│   │
│   ├── portfolio/                # Módulo Portfolio
│   │   ├── entities/
│   │   │   ├── user_portfolio.py
│   │   │   └── portfolio_snapshot.py
│   │   ├── value_objects/
│   │   │   └── __init__.py
│   │   ├── ports/
│   │   │   └── portfolio/
│   │   │       ├── portfolio_repository.py
│   │   │       └── __init__.py
│   │   ├── services/
│   │   │   └── __init__.py
│   │   └── __init__.py
│   │
│   ├── hunter/                   # Módulo Hunter AI
│   │   ├── entities/
│   │   │   └── __init__.py
│   │   ├── value_objects/
│   │   │   └── sentiment.py
│   │   ├── ports/
│   │   │   └── __init__.py
│   │   ├── services/
│   │   │   └── __init__.py
│   │   └── __init__.py
│   │
│   ├── ultra/                    # Módulo ULTRA
│   │   ├── entities/
│   │   │   └── __init__.py
│   │   ├── value_objects/
│   │   │   └── __init__.py
│   │   ├── ports/
│   │   │   └── __init__.py
│   │   ├── services/
│   │   │   └── __init__.py
│   │   └── __init__.py
│   │
│   ├── projects/                 # Módulo Projects
│   │   ├── entities/
│   │   │   └── project.py
│   │   ├── value_objects/
│   │   │   └── __init__.py
│   │   ├── ports/
│   │   │   └── project_repository.py
│   │   ├── services/
│   │   │   └── __init__.py
│   │   └── __init__.py
│   │
│   ├── search/                   # Módulo Search
│   │   ├── entities/
│   │   │   └── __init__.py
│   │   ├── value_objects/
│   │   │   └── __init__.py
│   │   ├── ports/
│   │   │   └── __init__.py
│   │   ├── services/
│   │   │   └── __init__.py
│   │   └── __init__.py
│   │
│   ├── preferences/              # Módulo Preferences
│   │   ├── entities/
│   │   │   └── user_preferences.py
│   │   ├── value_objects/
│   │   │   └── __init__.py
│   │   ├── ports/
│   │   │   └── user_preferences_repository.py
│   │   ├── services/
│   │   │   └── __init__.py
│   │   └── __init__.py
│   │
│   ├── chat/                     # Módulo Chat (ya parcialmente organizado)
│   │   ├── entities/
│   │   │   ├── conversation.py
│   │   │   ├── message.py
│   │   │   └── chat/
│   │   │       ├── conversation_analytics.py
│   │   │       ├── conversation_export.py
│   │   │       ├── conversation_template.py
│   │   │       ├── template_execution.py
│   │   │       └── user_chat_preferences.py
│   │   ├── value_objects/
│   │   │   └── message_role.py
│   │   ├── ports/
│   │   │   ├── conversation_repository.py
│   │   │   ├── message_repository.py
│   │   │   ├── conversation_context_repository.py
│   │   │   ├── template_repository.py
│   │   │   ├── template_execution_repository.py
│   │   │   ├── export_repository.py
│   │   │   └── analytics_repository.py
│   │   ├── services/
│   │   │   └── __init__.py
│   │   └── __init__.py
│   │
│   └── atlas/                    # Módulo Atlas
│       ├── entities/
│       │   ├── country.py
│       │   └── city.py
│       ├── value_objects/
│       │   └── __init__.py
│       ├── ports/
│       │   └── __init__.py
│       ├── services/
│       │   └── __init__.py
│       └── __init__.py
│
└── application/
    ├── graph/                    # ✅ Ya organizado - mantener estructura
    │   ├── commands/
    │   │   └── __init__.py
    │   ├── queries/
    │   │   └── __init__.py
    │   ├── services/
    │   │   └── __init__.py
    │   └── __init__.py
    │
    ├── ml/                       # ✅ Ya organizado - mantener estructura
    │   ├── commands/
    │   │   └── __init__.py
    │   ├── queries/
    │   │   └── __init__.py
    │   ├── services/
    │   │   └── __init__.py
    │   └── __init__.py
    │
    ├── alerts/                   # ✅ Ya organizado - mantener estructura
    │   ├── commands/
    │   │   └── __init__.py
    │   ├── queries/
    │   │   └── __init__.py
    │   ├── services/
    │   │   └── risk_alert_service.py
    │   └── __init__.py
    │
    ├── dashboard/                # ✅ Ya organizado - mantener estructura
    │   ├── commands/
    │   │   └── __init__.py
    │   ├── queries/
    │   │   └── __init__.py
    │   ├── services/
    │   │   └── dashboard_aggregation_service.py
    │   └── __init__.py
    │
    ├── comparison/               # ✅ Ya organizado - mantener estructura
    │   ├── commands/
    │   │   └── __init__.py
    │   ├── queries/
    │   │   └── __init__.py
    │   ├── services/
    │   │   └── protocol_comparison_service.py
    │   └── __init__.py
    │
    ├── markets/                  # ✅ Ya organizado - mantener estructura
    │   ├── commands/
    │   │   └── __init__.py
    │   ├── queries/
    │   │   └── __init__.py
    │   ├── services/
    │   │   └── advanced_markets_service.py
    │   └── __init__.py
    │
    ├── transactions/             # ⚠️ Refactorizar
    │   ├── commands/
    │   │   └── __init__.py
    │   ├── queries/
    │   │   └── __init__.py
    │   ├── services/
    │   │   ├── confirmation_service.py
    │   │   └── factory.py
    │   └── __init__.py
    │
    ├── bitcoin/                  # ⚠️ Crear estructura
    │   ├── commands/
    │   │   └── __init__.py
    │   ├── queries/
    │   │   └── __init__.py
    │   ├── services/
    │   │   └── __init__.py
    │   └── __init__.py
    │
    ├── portfolio/                # ✅ Ya organizado - mantener estructura
    │   ├── commands/
    │   │   └── __init__.py
    │   ├── queries/
    │   │   └── __init__.py
    │   ├── services/
    │   │   ├── portfolio_risk_analysis.py
    │   │   └── portfolio_service.py
    │   └── __init__.py
    │
    ├── hunter/                   # ✅ Ya organizado - mantener estructura
    │   ├── commands/
    │   │   └── __init__.py
    │   ├── queries/
    │   │   └── __init__.py
    │   ├── services/
    │   │   ├── pattern_recognition.py
    │   │   ├── portfolio_optimizer.py
    │   │   ├── lstm_price_predictor.py
    │   │   ├── price_data_service.py
    │   │   ├── sentiment_aggregator.py
    │   │   ├── twitter_sentiment.py
    │   │   ├── reddit_sentiment.py
    │   │   ├── discord_sentiment.py
    │   │   ├── news_sentiment.py
    │   │   ├── risk_analyzer.py
    │   │   └── trading_signal_generator.py
    │   └── __init__.py
    │
    ├── ultra/                    # ✅ Ya organizado - mantener estructura
    │   ├── commands/
    │   │   └── __init__.py
    │   ├── queries/
    │   │   └── __init__.py
    │   ├── services/
    │   │   ├── arbitrage_discovery.py
    │   │   ├── arbitrage_executor.py
    │   │   ├── auto_executor.py
    │   │   ├── flash_loan_engine.py
    │   │   ├── mev_protection.py
    │   │   └── risk_manager.py
    │   └── __init__.py
    │
    ├── projects/                 # ✅ Ya organizado - mantener estructura
    │   ├── commands/
    │   │   └── ...
    │   ├── queries/
    │   │   └── ...
    │   ├── services/
    │   │   └── ...
    │   └── __init__.py
    │
    ├── search/                   # ✅ Ya organizado - mantener estructura
    │   ├── commands/
    │   │   └── __init__.py
    │   ├── queries/
    │   │   └── __init__.py
    │   ├── services/
    │   │   └── search_history_service.py
    │   └── __init__.py
    │
    ├── preferences/              # ✅ Ya organizado - mantener estructura
    │   ├── commands/
    │   │   └── __init__.py
    │   ├── queries/
    │   │   └── __init__.py
    │   ├── services/
    │   │   └── user_preferences_service.py
    │   └── __init__.py
    │
    ├── chat/                     # ✅ Ya organizado - mantener estructura
    │   ├── commands/
    │   │   ├── create_conversation.py
    │   │   └── send_message.py
    │   ├── queries/
    │   │   ├── get_conversation.py
    │   │   ├── get_messages.py
    │   │   └── list_conversations.py
    │   ├── services/
    │   │   └── ...
    │   └── __init__.py
    │
    └── atlas/                    # ✅ Ya organizado - mantener estructura
        ├── commands/
        │   └── __init__.py
        ├── queries/
        │   └── queries.py
        ├── services/
        │   └── __init__.py
        └── __init__.py
```

## Plan de Migración

### Fase 1: Domain Layer - Módulos Simples

#### 1.1 Alerts Module
**Archivos a mover:**
- `domain/entities/risk_alert.py` → `domain/alerts/entities/risk_alert.py`

**Archivos a crear:**
- `domain/alerts/__init__.py`
- `domain/alerts/entities/__init__.py`
- `domain/alerts/value_objects/__init__.py`
- `domain/alerts/ports/__init__.py`
- `domain/alerts/services/__init__.py`

**Dependencias a actualizar:**
- `application/alerts/risk_alert_service.py`
- `presentation/http/controllers/alerts/router.py`

#### 1.2 Dashboard Module
**Archivos a crear:**
- `domain/dashboard/__init__.py`
- `domain/dashboard/entities/__init__.py`
- `domain/dashboard/value_objects/__init__.py`
- `domain/dashboard/ports/__init__.py`
- `domain/dashboard/services/__init__.py`

**Nota:** Dashboard no tiene entidades propias, usa `UserPortfolio` del módulo portfolio.

#### 1.3 Comparison Module
**Archivos a crear:**
- `domain/comparison/__init__.py`
- `domain/comparison/entities/__init__.py`
- `domain/comparison/value_objects/__init__.py`
- `domain/comparison/ports/__init__.py`
- `domain/comparison/services/__init__.py`

#### 1.4 Markets Module
**Archivos a crear:**
- `domain/markets/__init__.py`
- `domain/markets/entities/__init__.py`
- `domain/markets/value_objects/__init__.py`
- `domain/markets/ports/__init__.py`
- `domain/markets/services/__init__.py`

#### 1.5 Search Module
**Archivos a crear:**
- `domain/search/__init__.py`
- `domain/search/entities/__init__.py`
- `domain/search/value_objects/__init__.py`
- `domain/search/ports/__init__.py`
- `domain/search/services/__init__.py`

### Fase 2: Domain Layer - Módulos con Entidades

#### 2.1 Transactions Module
**Archivos a mover:**
- `domain/entities/transaction.py` → `domain/transactions/entities/transaction.py`
- `domain/ports/transaction/transaction_repository.py` → `domain/transactions/ports/transaction_repository.py`

**Archivos a crear:**
- `domain/transactions/__init__.py`
- `domain/transactions/entities/__init__.py`
- `domain/transactions/value_objects/__init__.py`
- `domain/transactions/ports/__init__.py`
- `domain/transactions/services/__init__.py`

**Dependencias a actualizar:**
- `application/transaction/confirmation_service.py`
- `application/transaction/factory.py`
- `infrastructure/adapters/transaction/` (no tocar según especificación)
- `presentation/http/controllers/transaction/router.py`

#### 2.2 Portfolio Module
**Archivos a mover:**
- `domain/entities/user_portfolio.py` → `domain/portfolio/entities/user_portfolio.py`
- `domain/entities/portfolio_snapshot.py` → `domain/portfolio/entities/portfolio_snapshot.py`
- `domain/ports/portfolio/portfolio_repository.py` → `domain/portfolio/ports/portfolio_repository.py`

**Archivos a crear:**
- `domain/portfolio/__init__.py`
- `domain/portfolio/entities/__init__.py`
- `domain/portfolio/value_objects/__init__.py`
- `domain/portfolio/ports/__init__.py`
- `domain/portfolio/services/__init__.py`

**Dependencias a actualizar:**
- `application/portfolio/portfolio_risk_analysis.py`
- `application/portfolio/portfolio_service.py`
- `presentation/http/controllers/portfolio/router.py`

#### 2.3 Preferences Module
**Archivos a mover:**
- `domain/entities/user_preferences.py` → `domain/preferences/entities/user_preferences.py`
- `domain/ports/user_preferences_repository.py` → `domain/preferences/ports/user_preferences_repository.py`

**Archivos a crear:**
- `domain/preferences/__init__.py`
- `domain/preferences/entities/__init__.py`
- `domain/preferences/value_objects/__init__.py`
- `domain/preferences/ports/__init__.py`
- `domain/preferences/services/__init__.py`

**Dependencias a actualizar:**
- `application/preferences/user_preferences_service.py`
- `presentation/http/controllers/preferences/router.py`

#### 2.4 Projects Module
**Archivos a mover:**
- `domain/entities/project.py` → `domain/projects/entities/project.py`
- `domain/ports/project_repository.py` → `domain/projects/ports/project_repository.py`

**Archivos a crear:**
- `domain/projects/__init__.py`
- `domain/projects/entities/__init__.py`
- `domain/projects/value_objects/__init__.py`
- `domain/projects/ports/__init__.py`
- `domain/projects/services/__init__.py`

**Dependencias a actualizar:**
- `application/projects/commands/`
- `application/projects/queries/`
- `presentation/http/controllers/user/projects_router.py`
- `presentation/http/controllers/admin/projects_router.py`

#### 2.5 Chat Module (Consolidación)
**Archivos a mover:**
- `domain/entities/conversation.py` → `domain/chat/entities/conversation.py`
- `domain/entities/message.py` → `domain/chat/entities/message.py`
- `domain/entities/conversation_context.py` → `domain/chat/entities/conversation_context.py`
- `domain/entities/chat/*` → `domain/chat/entities/chat/*` (mantener subdirectorio)
- `domain/ports/conversation_repository.py` → `domain/chat/ports/conversation_repository.py`
- `domain/ports/message_repository.py` → `domain/chat/ports/message_repository.py`
- `domain/ports/conversation_context_repository.py` → `domain/chat/ports/conversation_context_repository.py`
- `domain/ports/template_repository.py` → `domain/chat/ports/template_repository.py`
- `domain/ports/template_execution_repository.py` → `domain/chat/ports/template_execution_repository.py`
- `domain/ports/export_repository.py` → `domain/chat/ports/export_repository.py`
- `domain/ports/analytics_repository.py` → `domain/chat/ports/analytics_repository.py`
- `domain/value_objects/message_role.py` → `domain/chat/value_objects/message_role.py`

**Archivos a crear:**
- `domain/chat/__init__.py`
- `domain/chat/entities/__init__.py`
- `domain/chat/value_objects/__init__.py`
- `domain/chat/ports/__init__.py`
- `domain/chat/services/__init__.py`

**Dependencias a actualizar:**
- `application/chat/commands/`
- `application/chat/queries/`
- `application/chat/services/`
- `presentation/http/controllers/chat/`

#### 2.6 Atlas Module
**Archivos a mover:**
- `domain/entities/country.py` → `domain/atlas/entities/country.py`
- `domain/entities/city.py` → `domain/atlas/entities/city.py`

**Archivos a crear:**
- `domain/atlas/__init__.py`
- `domain/atlas/entities/__init__.py`
- `domain/atlas/value_objects/__init__.py`
- `domain/atlas/ports/__init__.py`
- `domain/atlas/services/__init__.py`

**Dependencias a actualizar:**
- `application/atlas/queries.py`
- `presentation/http/controllers/atlas/`

#### 2.7 Bitcoin Module
**Archivos a crear:**
- `domain/bitcoin/__init__.py`
- `domain/bitcoin/entities/__init__.py`
- `domain/bitcoin/value_objects/__init__.py`
- `domain/bitcoin/ports/__init__.py`
- `domain/bitcoin/services/__init__.py`

**Nota:** Bitcoin actualmente no tiene entidades propias en domain, solo handlers en infrastructure.

### Fase 3: Domain Layer - Módulos con Servicios

#### 3.1 Graph Module (Reorganizar)
**Archivos a mover:**
- `domain/services/graph/*` → `domain/graph/services/*`
- `domain/ports/graph/*` → `domain/graph/ports/*`

**Archivos a crear:**
- `domain/graph/entities/__init__.py`
- `domain/graph/value_objects/__init__.py`

**Dependencias a actualizar:**
- `application/graph/*`
- `presentation/http/controllers/graph/*`

#### 3.2 ML Module (Reorganizar)
**Archivos a mover:**
- `domain/services/ml/*` → `domain/ml/services/*`

**Archivos a crear:**
- `domain/ml/entities/__init__.py`
- `domain/ml/value_objects/__init__.py`
- `domain/ml/ports/__init__.py`

**Dependencias a actualizar:**
- `application/ml/*`
- `presentation/http/controllers/ml/*`

#### 3.3 Hunter Module
**Archivos a mover:**
- `domain/value_objects/sentiment.py` → `domain/hunter/value_objects/sentiment.py` (si existe)

**Archivos a crear:**
- `domain/hunter/__init__.py`
- `domain/hunter/entities/__init__.py`
- `domain/hunter/value_objects/__init__.py`
- `domain/hunter/ports/__init__.py`
- `domain/hunter/services/__init__.py`

**Dependencias a actualizar:**
- `application/hunter/*`
- `presentation/http/controllers/hunter/*`

#### 3.4 ULTRA Module
**Archivos a crear:**
- `domain/ultra/__init__.py`
- `domain/ultra/entities/__init__.py`
- `domain/ultra/value_objects/__init__.py`
- `domain/ultra/ports/__init__.py`
- `domain/ultra/services/__init__.py`

**Dependencias a actualizar:**
- `application/ultra/*`
- `presentation/http/controllers/ultra/*`

### Fase 4: Application Layer - Reorganización

#### 4.1 Transactions Module
**Archivos a mover:**
- `application/transaction/confirmation_service.py` → `application/transactions/services/confirmation_service.py`
- `application/transaction/factory.py` → `application/transactions/services/factory.py`

**Archivos a crear:**
- `application/transactions/__init__.py`
- `application/transactions/commands/__init__.py`
- `application/transactions/queries/__init__.py`
- `application/transactions/services/__init__.py`

**Dependencias a actualizar:**
- `presentation/http/controllers/transaction/router.py`

#### 4.2 Bitcoin Module
**Archivos a crear:**
- `application/bitcoin/__init__.py`
- `application/bitcoin/commands/__init__.py`
- `application/bitcoin/queries/__init__.py`
- `application/bitcoin/services/__init__.py`

**Nota:** Bitcoin actualmente solo tiene handlers en infrastructure/auth/handlers/.

## Estructura de Archivos __init__.py

Cada módulo debe tener `__init__.py` que exporte los elementos públicos:

```python
# domain/graph/__init__.py
"""GraphRAG domain module."""

from app.domain.graph.entities import *
from app.domain.graph.value_objects import *
from app.domain.graph.ports import *
from app.domain.graph.services import *

__all__ = [
    # Entities
    # Value Objects
    # Ports
    # Services
]
```

## Actualización de Imports

### Patrón de Import Antes
```python
from app.domain.entities.risk_alert import RiskAlert
from app.domain.ports.analytics_repository import AnalyticsRepository
from app.application.alerts import RiskAlertService
```

### Patrón de Import Después
```python
from app.domain.alerts.entities.risk_alert import RiskAlert
from app.domain.chat.ports.analytics_repository import AnalyticsRepository
from app.application.alerts.services.risk_alert_service import RiskAlertService
```

## Checklist de Migración por Módulo

Para cada módulo:

- [ ] Crear estructura de directorios
- [ ] Mover entidades
- [ ] Mover value objects
- [ ] Mover ports
- [ ] Mover services (domain)
- [ ] Actualizar imports en domain
- [ ] Actualizar imports en application
- [ ] Actualizar imports en presentation
- [ ] Actualizar imports en tests
- [ ] Crear `__init__.py` con exports
- [ ] Verificar que la aplicación inicia
- [ ] Ejecutar tests del módulo
- [ ] Actualizar documentación

## Orden de Ejecución Recomendado

1. **Módulos simples primero** (alerts, dashboard, comparison, markets, search)
2. **Módulos con entidades** (transactions, portfolio, preferences, projects)
3. **Módulos complejos** (chat, atlas)
4. **Módulos con servicios** (graph, ml, hunter, ultra)
5. **Bitcoin** (último, requiere análisis adicional)

## Consideraciones Especiales

### Chat Module
- Tiene múltiples sub-entidades en `chat/`
- Tiene múltiples ports relacionados
- Requiere consolidación cuidadosa

### Graph Module
- Ya tiene servicios organizados
- Solo necesita mover ports y crear estructura completa

### ML Module
- Ya tiene servicios organizados
- Solo necesita crear estructura completa

### Hunter y ULTRA
- Son módulos grandes con múltiples servicios
- Ya están organizados en application
- Solo necesitan estructura en domain

## Validación

Después de cada módulo:
1. ✅ Aplicación inicia sin errores
2. ✅ Tests pasan
3. ✅ No hay imports rotos
4. ✅ Estructura sigue el patrón establecido

## Documentación

Actualizar:
- `docs/steering/structure.md` - Estructura del proyecto
- README.md - Referencias a estructura
- `.cursor/rules/project-structure.mdc` - Reglas de estructura

---

**Estado:** 📋 **ESPECIFICACIÓN COMPLETA**  
**Próximo Paso:** Implementación fase por fase

