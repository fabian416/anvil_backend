# 🐳 DOCKER IMPLEMENTATION PLAN - OPCIÓN D

**Documento**: DOCKER_IMPLEMENTATION_PLAN.md  
**Respuesta a**: "¿Solo Dockerfiles o modificar servicios?"  
**Estado**: PLAN EJECUTABLE

---

## ✅ RESPUESTA DIRECTA

**❌ NO necesitas modificar servicios ni backend**

**✅ SOLO crear 14 Dockerfiles (infraestructura pura)**

**Backend changes: 0**

---

## 📋 MAPEO DE EXISTENCIA

### ✅ LO QUE YA EXISTE (cero cambios necesarios):

#### 1️⃣ **11 MCPs - Ubicación: `src/app/infrastructure/mcp/servers/`**

```
✅ oneinch_mcp.py          (puerto 8081)
✅ defillama_mcp.py        (puerto 8082)
✅ thegraph_mcp.py         (puerto 8083)
✅ coingecko_mcp.py        (puerto 8084)
✅ aave_mcp.py             (puerto 8085)
✅ portfolio_mcp.py        (puerto 8086)
✅ perplexity_mcp.py       (puerto 8087)
✅ morpho_mcp.py           (puerto 8088)
✅ curve_mcp.py            (puerto 8089)
✅ hyperliquid_mcp.py      (puerto 8090)
✅ layerzero_mcp.py        (puerto 8091)

Cada uno tiene:
  - __main__ para ejecutarse standalone
  - MCPServer como base class
  - Tools registradas
  - Listo para Docker (solo ejecutar como proceso)
```

**Comando para Docker:**
```bash
python -m app.infrastructure.mcp.servers.oneinch_mcp
```

---

#### 2️⃣ **9 Workers Especializados - Ubicación: `Makefile` (líneas 132+)**

```makefile
✅ celery.worker.maintenance        (lines 134-140)
✅ celery.worker.agents             (lines 142-148)    🔥 Alta prioridad
✅ celery.worker.graph              (lines 150-156)
✅ celery.worker.distillation       (lines 158-164)
✅ celery.worker.projects           (lines 166-172)
✅ celery.worker.llm                (lines 174-180)
✅ celery.worker.transactions       (lines 182-188)    🔥 CRÍTICO
✅ celery.worker.risk               (lines 190+)
✅ celery.worker.email              (lines 196+)

Cada uno ya tiene:
  - Queue específica (-Q nombre)
  - Concurrency configurado (--concurrency=N)
  - Task routing definido en src/app/infrastructure/celery/app.py
  - Max tasks per child setup
```

**Comando para Docker:**
```bash
celery -A app.infrastructure.celery.app.celery_app worker \
  -Q agents \
  -n agents@%h \
  --concurrency=8 \
  --max-tasks-per-child=200
```

---

#### 3️⃣ **FastAPI - Ubicación: `src/app/run.py`**

```python
✅ make_app()  # Factory function
✅ Uvicorn compatible
✅ Health endpoint (/health)
✅ CORS configured
✅ 233 endpoints registradas
```

**Comando para Docker:**
```bash
uvicorn app.run:make_app --factory --host 0.0.0.0 --port 8080
```

---

#### 4️⃣ **Celery Beat - Ubicación: `src/app/infrastructure/celery/`**

```python
✅ Beat schedule configurado
✅ 20+ periodic tasks definidas
✅ Cron expressions setup
```

**Comando para Docker:**
```bash
celery -A app.infrastructure.celery.app.celery_app beat
```

---

#### 5️⃣ **Transaction Confirmation Worker - Ubicación: `src/app/cli/confirm_pending_transactions.py`**

```python
✅ Implementado como CLI
✅ Loop mode disponible (--loop)
✅ Log level configurable (--log-level INFO)
```

**Comando para Docker:**
```bash
python -m app.cli.confirm_pending_transactions --loop --log-level INFO
```

---

#### 6️⃣ **docker-compose.yaml - Ubicación: `config/local/docker-compose.yaml`**

```yaml
✅ Ya existe
✅ Ya tiene: redis, postgres, web_app, celery_worker, celery_beat, flower
```

---

### 📝 LO QUE FALTA (solo infraestructura):

#### **14 Dockerfiles - CREAR:**

```
1. Dockerfile.fastapi                    ← API HTTP (250MB)
2. Dockerfile.celery                     ← Worker general (200MB)
3. Dockerfile.celery-beat                ← Scheduler (180MB)
4. Dockerfile.celery-workers.agents      ← Agentes IA (180MB)
5. Dockerfile.celery-workers.transactions← Blockchain (180MB)
6. Dockerfile.celery-workers.graph       ← Embeddings (180MB)
7. Dockerfile.celery-workers.distillation← LLM (180MB)
8. Dockerfile.celery-workers.projects    ← Knowledge base (180MB)
9. Dockerfile.celery-workers.llm         ← Ranking (180MB)
10. Dockerfile.celery-workers.maintenance← Limpieza (180MB)
11. Dockerfile.celery-workers.risk       ← Monitoreo (180MB)
12. Dockerfile.celery-workers.email      ← Emails (180MB)
13. Dockerfile.mcp                       ← MCPs genérico (180MB)
14. Dockerfile.tx-confirmation           ← TX (180MB)
```

---

#### **docker-compose.yaml - MEJORAR:**

```yaml
Agregar:
  - 9 servicios de celery-worker-*
  - 11 servicios de mcp-*
  - 1 servicio de tx-confirmation

NO cambiar: Lógica de backend
```

---

## 📊 TABLA COMPARATIVA

| Componente | Existe | Ubicación | Backend | Docker |
|-----------|--------|-----------|---------|---------|
| 11 MCPs | ✅ | src/app/infrastructure/mcp/servers/ | ✅ No tocar | 📝 1 Dockerfile.mcp |
| FastAPI | ✅ | src/app/run.py | ✅ No tocar | 📝 Dockerfile.fastapi |
| Celery Worker | ✅ | Makefile | ✅ No tocar | 📝 Dockerfile.celery |
| Celery Beat | ✅ | src/app/infrastructure/celery/ | ✅ No tocar | 📝 Dockerfile.celery-beat |
| 9 Workers | ✅ | Makefile (líneas 132+) | ✅ No tocar | 📝 9 Dockerfiles |
| TX Confirmation | ✅ | src/app/cli/ | ✅ No tocar | 📝 Dockerfile.tx-confirmation |
| docker-compose | ✅ | config/local/ | ✅ No tocar | 📝 Mejorar |

---

## 🎯 PLAN DE TRABAJO EJECUTABLE

### PASO 1: Crear Base Template (10 min)

```dockerfile
# Dockerfile.base (template para todos)
FROM python:3.12-slim AS builder

WORKDIR /build
COPY pyproject.toml .
RUN pip install uv && uv pip install .

# =====================================
FROM python:3.12-slim

WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local

# Copy app code
COPY src/ src/
COPY config/ config/
COPY alembic.ini ./

# Environment
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app/src

# User
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1 || true

# CMD se especifica por servicio
CMD ["uvicorn", "app.run:make_app", "--factory", "--host", "0.0.0.0", "--port", "8080"]
```

---

### PASO 2: Crear 14 Dockerfiles (2-3 horas)

#### **2.1 Dockerfile.fastapi**
```dockerfile
# Copy base template, only change CMD
CMD ["uvicorn", "app.run:make_app", "--factory", "--host", "0.0.0.0", "--port", "8080"]
```

#### **2.2 Dockerfile.celery**
```dockerfile
CMD ["celery", "-A", "app.infrastructure.celery.app.celery_app", "worker", "-l", "INFO"]
```

#### **2.3 Dockerfile.celery-beat**
```dockerfile
CMD ["celery", "-A", "app.infrastructure.celery.app.celery_app", "beat", "-l", "INFO"]
```

#### **2.4-2.12 Dockerfile.celery-workers.{agents,transactions,...}**
```dockerfile
# Example: Dockerfile.celery-workers.agents
CMD ["celery", "-A", "app.infrastructure.celery.app.celery_app", "worker", \
     "-Q", "agents", \
     "-n", "agents@%h", \
     "--concurrency", "8", \
     "--max-tasks-per-child", "200", \
     "-l", "INFO"]
```

#### **2.13 Dockerfile.mcp**
```dockerfile
ARG MCP_SERVER=oneinch_mcp
ENV MCP_SERVER=$MCP_SERVER

CMD ["python", "-m", "app.infrastructure.mcp.servers.${MCP_SERVER}"]
```

#### **2.14 Dockerfile.tx-confirmation**
```dockerfile
CMD ["python", "-m", "app.cli.confirm_pending_transactions", "--loop", "--log-level", "INFO"]
```

---

### PASO 3: Mejorar docker-compose.yaml (1-2 horas)

```yaml
version: '3.8'

services:
  # ===== INFRAESTRUCTURA (sin cambios) =====
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  postgres:
    image: postgres:16-alpine
    # ... sin cambios ...

  # ===== FASTAPI =====
  fastapi:
    build:
      context: .
      dockerfile: Dockerfile.fastapi
    ports:
      - "8080:8080"
    environment:
      - DATABASE_URL=postgresql://...
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis
      - postgres
    restart: always

  # ===== CELERY =====
  celery-worker:
    build: Dockerfile.celery
    environment:
      - DATABASE_URL=postgresql://...
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis
      - postgres
    restart: always

  celery-beat:
    build: Dockerfile.celery-beat
    depends_on:
      - redis
    restart: always

  # ===== WORKERS ESPECIALIZADOS (9) =====
  celery-worker-agents:
    build:
      dockerfile: Dockerfile.celery-workers.agents
    depends_on:
      - redis
      - postgres
    restart: always

  celery-worker-transactions:
    build:
      dockerfile: Dockerfile.celery-workers.transactions
    depends_on:
      - redis
      - postgres
    restart: always

  # ... 7 más (graph, distillation, projects, llm, maintenance, risk, email) ...

  # ===== MCPs (11) =====
  mcp-1inch:
    build:
      dockerfile: Dockerfile.mcp
      args:
        MCP_SERVER: oneinch_mcp
    ports:
      - "8081:8081"
    restart: always

  mcp-defillama:
    build:
      dockerfile: Dockerfile.mcp
      args:
        MCP_SERVER: defillama_mcp
    ports:
      - "8082:8082"
    restart: always

  # ... 9 más (8083-8091) ...

  # ===== MONITORING =====
  flower:
    image: mher/flower:1.2.0
    ports:
      - "5555:5555"
    depends_on:
      - redis
    restart: always

  # ===== OTROS =====
  tx-confirmation:
    build: Dockerfile.tx-confirmation
    depends_on:
      - redis
      - postgres
    restart: always
```

---

### PASO 4: Verificar (30 min)

```bash
# Build all images
docker-compose build

# Start all services
docker-compose up

# Check logs
docker-compose logs -f fastapi
docker-compose logs -f celery-worker-agents
docker-compose logs -f mcp-1inch

# Scale a service
docker-compose up -d --scale celery-worker-agents=3
```

---

## ⏱️ TIEMPO ESTIMADO

| Paso | Tarea | Tiempo |
|------|-------|--------|
| 1 | Crear base template | 10 min |
| 2 | Crear 14 Dockerfiles | 2-3 horas |
| 3 | Mejorar docker-compose | 1-2 horas |
| 4 | Testing & Verification | 30 min |
| **TOTAL** | | **4-5 horas** |

---

## ✅ CONCLUSIÓN

**Tu pregunta:** ¿Dockerfiles solo o modificar servicios?

**Respuesta:**
- ✅ SOLO DOCKERFILES
- ✅ NO modificar backend
- ✅ NO modificar servicios
- ✅ Todos ya existen
- ✅ Solo "envolverlos" en Docker

**Cambios de backend:** 0 ✅

---

## 🚀 ¿EMPEZAMOS?

¿Creo los 14 Dockerfiles ahora?

