# Arquitectura de Workers Celery - Especialización por Colas

**Fecha**: December 19, 2025  
**Propósito**: Documentación de la arquitectura de workers especializados para evitar latencia y mejorar performance

---

## 📊 Resumen Ejecutivo

El sistema utiliza **9 colas especializadas** con **workers dedicados** para cada tipo de tarea. Esto evita que tareas críticas (como procesamiento de agentes IA) sean bloqueadas por tareas de mantenimiento (como limpieza de sesiones).

**Beneficios**:
- ✅ **Sin latencia**: Tareas críticas procesadas inmediatamente
- ✅ **Escalabilidad**: Workers independientes por tipo de carga
- ✅ **Performance**: Concurrencia optimizada por tipo de tarea
- ✅ **Monitoreo**: Fácil identificar bottlenecks por cola

---

## 🎯 Colas Configuradas

### 1. `maintenance` - Tareas de Limpieza y Mantenimiento
**Prioridad**: Baja  
**Concurrencia**: 2 workers  
**Uso**: Tareas que pueden esperar sin impacto en UX

**Tareas**:
- `cleanup_expired_sessions` - Limpieza diaria de sesiones expiradas
- `cleanup_expired_password_resets` - Limpieza horaria de resets expirados
- `invalidate_all_sessions` - Invalidación masiva de sesiones

**Worker**:
```bash
make celery.worker.maintenance
```

---

### 2. `agents` - Procesamiento de Agentes IA
**Prioridad**: Alta (Tiempo Real)  
**Concurrencia**: 8 workers  
**Uso**: Procesamiento de mensajes de chat y respuestas de agentes

**Tareas**:
- `process_agent_response` - Procesar respuestas de agentes
- `update_agent_stats` - Actualizar estadísticas de agentes (cada 5 min)

**Worker**:
```bash
make celery.worker.agents
```

---

### 3. `graph` - Mantenimiento de Grafo y Embeddings
**Prioridad**: Media (Procesamiento Pesado)  
**Concurrencia**: 2 workers  
**Uso**: Operaciones costosas de grafo y generación de embeddings

**Tareas**:
- `populate_graph_protocols` - Poblar grafo con protocolos (diario 2 AM)
- `update_graph_metadata` - Actualizar metadata (cada 6 horas)
- `validate_graph_integrity` - Validar integridad (semanal)
- `generate_protocol_embeddings` - Generar embeddings (diario 3 AM)

**Worker**:
```bash
make celery.worker.graph
```

---

### 4. `distillation` - Procesamiento LLM y Caché
**Prioridad**: Media  
**Concurrencia**: 4 workers  
**Uso**: Agregación de telemetría y gestión de caché LLM

**Tareas**:
- `aggregate_distillation_telemetry` - Agregar telemetría (cada hora :05)
- `cleanup_expired_cache` - Limpiar caché expirado (diario 3 AM)
- `cache_llm_response` - Cachear respuestas LLM

**Worker**:
```bash
make celery.worker.distillation
```

---

### 5. `projects` - Knowledge Base y Proyectos
**Prioridad**: Media  
**Concurrencia**: 3 workers  
**Uso**: Procesamiento de knowledge base y proyectos

**Tareas**:
- `reindex_knowledge_base` - Reindexar knowledge base
- `evaluate_auto_assignment_rules` - Evaluar reglas de asignación
- `aggregate_project_analytics` - Agregar analytics (diario 4 AM)
- `check_knowledge_base_health` - Verificar salud KB (semanal domingo 5 AM)

**Worker**:
```bash
make celery.worker.projects
```

---

### 6. `llm` - Ranking y Orchestration de LLM
**Prioridad**: Media-Alta  
**Concurrencia**: 4 workers  
**Uso**: Ranking de modelos LLM y orchestration

**Tareas**:
- `recalculate_all_rankings` - Recalcular rankings generales
- `recalculate_agent_rankings` - Recalcular rankings de agentes
- `recalculate_llm_rankings` - Recalcular rankings LLM (cada hora)
- `aggregate_llm_telemetry` - Agregar telemetría LLM (cada hora :10)
- `llm_provider_health_checks` - Health checks de proveedores (cada 5 min)
- `reset_daily_budgets` - Resetear presupuestos diarios (medianoche)
- `cleanup_old_llm_data` - Limpiar datos antiguos (semanal domingo 4 AM)

**Worker**:
```bash
make celery.worker.llm
```

---

### 7. `transactions` - Confirmación de Transacciones Blockchain
**Prioridad**: Crítica (Alta)  
**Concurrencia**: 6 workers  
**Uso**: Confirmación de transacciones blockchain en tiempo real

**Tareas**:
- `confirm_pending_transactions` - Confirmar transacciones pendientes
- `confirm_pending_transactions_mainnet` - Confirmar en mainnet
- `confirm_pending_transactions_testnet` - Confirmar en testnet

**Worker**:
```bash
make celery.worker.transactions
```

---

### 8. `risk` - Monitoreo de Riesgo
**Prioridad**: Media-Alta  
**Concurrencia**: 3 workers  
**Uso**: Monitoreo continuo de alertas de riesgo

**Tareas**:
- `check_user_risk_alerts` - Verificar alertas de riesgo (cada 15 min)

**Worker**:
```bash
make celery.worker.risk
```

---

### 9. `email` - Envío de Emails
**Prioridad**: Media  
**Concurrencia**: 2 workers  
**Uso**: Envío asíncrono de emails

**Tareas**:
- `send_email` - Enviar email genérico
- `tasks.email_tasks.*` - Todas las tareas de email

**Worker**:
```bash
make celery.worker.email
```

---

## 🚀 Uso en Desarrollo

### Iniciar Workers Especializados

Para desarrollo local, puedes iniciar múltiples workers en terminales separadas:

```bash
# Terminal 1: Agents (crítico para chat)
make celery.worker.agents

# Terminal 2: Transactions (crítico para blockchain)
make celery.worker.transactions

# Terminal 3: Maintenance (baja prioridad)
make celery.worker.maintenance

# Terminal 4: Otros workers según necesidad
make celery.worker.graph
make celery.worker.distillation
make celery.worker.projects
make celery.worker.llm
make celery.worker.risk
make celery.worker.email
```

### Iniciar Celery Beat

```bash
make celery.flower
```

### Monitorear con Flower

```bash
make celery.flower
# Abre http://localhost:5555
```

---

## 🏭 Uso en Producción

### Recomendación de Workers por Ambiente

**Desarrollo Local**:
- `agents` (1 worker)
- `transactions` (1 worker)
- `maintenance` (1 worker)
- Opcional: otros según necesidad

**Producción**:
- `agents`: 2-4 workers (alta carga de chat)
- `transactions`: 2-3 workers (crítico)
- `llm`: 2 workers (ranking y telemetría)
- `distillation`: 2 workers (caché LLM)
- `graph`: 1 worker (procesamiento pesado)
- `projects`: 1-2 workers
- `risk`: 1 worker
- `email`: 1 worker
- `maintenance`: 1 worker

### Usando Supervisor o Systemd

Ejemplo de configuración para supervisor:

```ini
[program:celery-agents]
command=/path/to/env/bin/celery -A app.infrastructure.celery.app.celery_app worker -Q agents -n agents@%%h --loglevel=INFO --concurrency=8
directory=/path/to/project
user=www-data
autostart=true
autorestart=true

[program:celery-transactions]
command=/path/to/env/bin/celery -A app.infrastructure.celery.app.celery_app worker -Q transactions -n transactions@%%h --loglevel=INFO --concurrency=6
directory=/path/to/project
user=www-data
autostart=true
autorestart=true
```

---

## 📈 Configuración de Concurrencia

La concurrencia está optimizada por tipo de tarea:

| Cola | Concurrencia | Razón |
|------|--------------|-------|
| `agents` | 8 | Alta demanda, tiempo real |
| `transactions` | 6 | Crítico, múltiples cadenas |
| `distillation` | 4 | Procesamiento LLM paralelo |
| `llm` | 4 | Ranking y telemetría |
| `projects` | 3 | Knowledge base processing |
| `risk` | 3 | Monitoreo continuo |
| `graph` | 2 | Procesamiento pesado, CPU-bound |
| `maintenance` | 2 | Baja prioridad |
| `email` | 2 | I/O bound, bajo costo |

---

## 🔧 Configuración Técnica

### Routing de Tareas

El routing está configurado en `src/app/infrastructure/celery/app.py`:

```python
app.conf.task_routes = {
    "process_agent_response": {"queue": "agents"},
    "confirm_pending_transactions": {"queue": "transactions"},
    # ... más rutas
}
```

### Beat Schedule

Las tareas periódicas están configuradas en `src/app/infrastructure/celery/main_tasks.py` con colas específicas:

```python
"update-agent-stats": {
    "task": "update_agent_stats",
    "schedule": crontab(minute="*/5"),
    "options": {"queue": "agents"},
}
```

---

## 🐛 Troubleshooting

### Warning: DuplicateNodenameWarning

**Problema**: Múltiples workers con el mismo nombre

**Solución**: Cada worker tiene un nombre único con `-n`:
- `-n agents@%h` (agents@hostname)
- `-n transactions@%h` (transactions@hostname)
- etc.

### Tareas no se procesan

**Verificar**:
1. Worker está corriendo: `ps aux | grep celery`
2. Worker está escuchando la cola correcta: `-Q agents`
3. Tarea está siendo enrutada a la cola correcta
4. Redis está corriendo: `redis-cli ping`

### Latencia en tareas críticas

**Solución**: Asegúrate de que workers críticos estén corriendo:
- `agents` para chat
- `transactions` para blockchain

---

## 📚 Referencias

- Configuración Celery: `src/app/infrastructure/celery/app.py`
- Tareas principales: `src/app/infrastructure/celery/main_tasks.py`
- Makefile: `Makefile` (comandos `celery.worker.*`)
- Flower UI: `http://localhost:5555` (cuando `make celery.flower` está corriendo)

---

**Última actualización**: December 19, 2025

