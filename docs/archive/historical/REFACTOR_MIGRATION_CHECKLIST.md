# Checklist de Migración - Refactor de Directorios

**Fecha:** 19 de Diciembre, 2025  
**Referencia:** [REFACTOR_DIRECTORY_STRUCTURE_SPEC.md](./REFACTOR_DIRECTORY_STRUCTURE_SPEC.md)

## Resumen Ejecutivo

Este documento proporciona un checklist práctico para ejecutar el refactor de estructura de directorios módulo por módulo.

## Orden de Ejecución

### Fase 1: Módulos Simples (Sin Entidades Propias)

#### ✅ 1. Alerts
- [ ] Crear `domain/alerts/` estructura
- [ ] Mover `domain/entities/risk_alert.py` → `domain/alerts/entities/risk_alert.py`
- [ ] Actualizar imports en `application/alerts/risk_alert_service.py`
- [ ] Actualizar imports en `presentation/http/controllers/alerts/router.py`
- [ ] Verificar tests
- [ ] Commit: `refactor(domain): reorganize alerts module`

#### ✅ 2. Dashboard
- [ ] Crear `domain/dashboard/` estructura (vacía, usa UserPortfolio)
- [ ] Commit: `refactor(domain): add dashboard module structure`

#### ✅ 3. Comparison
- [ ] Crear `domain/comparison/` estructura
- [ ] Commit: `refactor(domain): add comparison module structure`

#### ✅ 4. Markets
- [ ] Crear `domain/markets/` estructura
- [ ] Commit: `refactor(domain): add markets module structure`

#### ✅ 5. Search
- [ ] Crear `domain/search/` estructura
- [ ] Commit: `refactor(domain): add search module structure`

### Fase 2: Módulos con Entidades

#### ✅ 6. Transactions
- [ ] Crear `domain/transactions/` estructura
- [ ] Mover `domain/entities/transaction.py` → `domain/transactions/entities/transaction.py`
- [ ] Mover `domain/ports/transaction/` → `domain/transactions/ports/`
- [ ] Actualizar imports (51 archivos encontrados)
- [ ] Mover `application/transaction/` → `application/transactions/`
- [ ] Verificar tests
- [ ] Commit: `refactor(domain): reorganize transactions module`

#### ✅ 7. Portfolio
- [ ] Crear `domain/portfolio/` estructura
- [ ] Mover `domain/entities/user_portfolio.py` → `domain/portfolio/entities/user_portfolio.py`
- [ ] Mover `domain/entities/portfolio_snapshot.py` → `domain/portfolio/entities/portfolio_snapshot.py`
- [ ] Mover `domain/ports/portfolio/` → `domain/portfolio/ports/`
- [ ] Actualizar imports en `application/portfolio/`
- [ ] Actualizar imports en `presentation/http/controllers/portfolio/`
- [ ] Verificar tests
- [ ] Commit: `refactor(domain): reorganize portfolio module`

#### ✅ 8. Preferences
- [ ] Crear `domain/preferences/` estructura
- [ ] Mover `domain/entities/user_preferences.py` → `domain/preferences/entities/user_preferences.py`
- [ ] Mover `domain/ports/user_preferences_repository.py` → `domain/preferences/ports/user_preferences_repository.py`
- [ ] Actualizar imports en `application/preferences/`
- [ ] Actualizar imports en `presentation/http/controllers/preferences/`
- [ ] Verificar tests
- [ ] Commit: `refactor(domain): reorganize preferences module`

#### ✅ 9. Projects
- [ ] Crear `domain/projects/` estructura
- [ ] Mover `domain/entities/project.py` → `domain/projects/entities/project.py`
- [ ] Mover `domain/ports/project_repository.py` → `domain/projects/ports/project_repository.py`
- [ ] Actualizar imports (15+ archivos)
- [ ] Verificar tests
- [ ] Commit: `refactor(domain): reorganize projects module`

### Fase 3: Módulos Complejos

#### ✅ 10. Chat (Consolidación Completa)
- [ ] Crear `domain/chat/` estructura completa
- [ ] Mover entidades:
  - `conversation.py` → `domain/chat/entities/conversation.py`
  - `message.py` → `domain/chat/entities/message.py`
  - `conversation_context.py` → `domain/chat/entities/conversation_context.py`
  - `chat/*` → `domain/chat/entities/chat/*`
- [ ] Mover ports:
  - `conversation_repository.py` → `domain/chat/ports/conversation_repository.py`
  - `message_repository.py` → `domain/chat/ports/message_repository.py`
  - `conversation_context_repository.py` → `domain/chat/ports/conversation_context_repository.py`
  - `template_repository.py` → `domain/chat/ports/template_repository.py`
  - `template_execution_repository.py` → `domain/chat/ports/template_execution_repository.py`
  - `export_repository.py` → `domain/chat/ports/export_repository.py`
  - `analytics_repository.py` → `domain/chat/ports/analytics_repository.py`
- [ ] Mover value objects:
  - `message_role.py` → `domain/chat/value_objects/message_role.py`
- [ ] Actualizar imports (39+ archivos)
- [ ] Verificar tests
- [ ] Commit: `refactor(domain): reorganize chat module`

#### ✅ 11. Atlas
- [ ] Crear `domain/atlas/` estructura
- [ ] Mover `domain/entities/country.py` → `domain/atlas/entities/country.py`
- [ ] Mover `domain/entities/city.py` → `domain/atlas/entities/city.py`
- [ ] Actualizar imports en `application/atlas/`
- [ ] Actualizar imports en `presentation/http/controllers/atlas/`
- [ ] Actualizar imports en `setup/app_factory.py`
- [ ] Verificar tests
- [ ] Commit: `refactor(domain): reorganize atlas module`

### Fase 4: Módulos con Servicios

#### ✅ 12. Graph (Reorganizar)
- [ ] Mover `domain/services/graph/*` → `domain/graph/services/`
- [ ] Mover `domain/ports/graph/*` → `domain/graph/ports/`
- [ ] Crear `domain/graph/entities/` y `domain/graph/value_objects/`
- [ ] Actualizar imports en `application/graph/`
- [ ] Actualizar imports en `presentation/http/controllers/graph/`
- [ ] Verificar tests
- [ ] Commit: `refactor(domain): reorganize graph module`

#### ✅ 13. ML (Reorganizar)
- [ ] Mover `domain/services/ml/*` → `domain/ml/services/`
- [ ] Crear `domain/ml/entities/`, `domain/ml/value_objects/`, `domain/ml/ports/`
- [ ] Actualizar imports en `application/ml/`
- [ ] Actualizar imports en `presentation/http/controllers/ml/`
- [ ] Verificar tests
- [ ] Commit: `refactor(domain): reorganize ml module`

#### ✅ 14. Hunter
- [ ] Crear `domain/hunter/` estructura
- [ ] Mover `domain/value_objects/sentiment.py` → `domain/hunter/value_objects/sentiment.py` (si existe)
- [ ] Actualizar imports en `application/hunter/`
- [ ] Actualizar imports en `presentation/http/controllers/hunter/`
- [ ] Verificar tests
- [ ] Commit: `refactor(domain): reorganize hunter module`

#### ✅ 15. ULTRA
- [ ] Crear `domain/ultra/` estructura
- [ ] Actualizar imports en `application/ultra/`
- [ ] Actualizar imports en `presentation/http/controllers/ultra/`
- [ ] Verificar tests
- [ ] Commit: `refactor(domain): reorganize ultra module`

#### ✅ 16. Bitcoin
- [ ] Crear `domain/bitcoin/` estructura
- [ ] Crear `application/bitcoin/` estructura
- [ ] Analizar si necesita entidades propias
- [ ] Verificar tests
- [ ] Commit: `refactor(domain): add bitcoin module structure`

## Script de Búsqueda y Reemplazo

Para cada módulo, usar estos comandos para encontrar todos los imports:

```bash
# Buscar imports de entidades
grep -r "from app.domain.entities.risk_alert" src/

# Buscar imports de ports
grep -r "from app.domain.ports.analytics_repository" src/

# Buscar imports de application
grep -r "from app.application.alerts" src/
```

## Comandos Útiles

```bash
# Verificar que la app inicia
make start

# Ejecutar tests de un módulo específico
pytest tests/integration/alerts/ -v

# Verificar imports rotos
python -m py_compile src/app/domain/alerts/entities/risk_alert.py

# Buscar todos los imports de un módulo
grep -r "from app.domain.entities.risk_alert" src/ tests/
```

## Validación Post-Migración

Después de cada módulo:

1. ✅ Aplicación inicia: `make start`
2. ✅ Tests pasan: `pytest tests/ -v`
3. ✅ No hay imports rotos: `python -c "import app.domain.alerts.entities.risk_alert"`
4. ✅ Estructura correcta: Verificar que todos los `__init__.py` existen
5. ✅ Documentación actualizada: Revisar referencias en docs/

## Notas Importantes

- **No tocar Infrastructure**: Según especificación, infrastructure layer no se modifica
- **Commits incrementales**: Hacer commit después de cada módulo
- **Tests primero**: Ejecutar tests antes y después de cada cambio
- **Backup**: Considerar crear branch antes de empezar: `git checkout -b refactor/directory-structure`

## Archivos Críticos a Actualizar

### Setup/IOC
- `src/app/setup/ioc/infrastructure.py`
- `src/app/setup/ioc/application.py`
- `src/app/setup/ioc/chat_phase2.py`
- `src/app/setup/ioc/agent_squad_application.py`

### App Factory
- `src/app/setup/app_factory.py` (imports de Country, City)

### Infrastructure Adapters (Solo actualizar imports)
- `src/app/infrastructure/adapters/transaction_repository_sqla.py`
- `src/app/infrastructure/adapters/message_repository_sqla.py`
- `src/app/infrastructure/adapters/conversation_repository_sqla.py`
- `src/app/infrastructure/adapters/chat/analytics_repository_adapter.py`
- `src/app/infrastructure/adapters/chat/preferences_repository_adapter.py`
- `src/app/infrastructure/persistence_sqla/repositories/project_repository.py`

## Estadísticas de Impacto

- **Total módulos a refactorizar**: 16
- **Archivos a mover**: ~50+
- **Imports a actualizar**: ~200+
- **Tests a verificar**: Todos los tests de integración

---

**Estado:** 📋 **CHECKLIST LISTO**  
**Uso:** Marcar cada item conforme se completa

