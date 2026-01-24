# Análisis: Docker & Build - Environment Management

## 📊 Estado Actual

### Dockerfiles
- ✅ Multi-stage builds optimizados
- ✅ Layer caching eficiente  
- ✅ Non-root user (appuser)
- ❌ Hardcoded `APP_ENV=local` en todos los Dockerfiles
- ❌ No soportan variables de ambiente en build time

### GitHub Actions Workflow
- ✅ Matrix paralela para 23 servicios
- ✅ Auto-tags por rama (production/staging/development)
- ❌ No pasa ENV variables al Docker build
- ❌ No diferencia configuraciones por ambiente

### Estructura de Configuración
```
config/
├── dev/           ← Desarrollo
├── local/         ← Local
├── prod/          ← Producción
└── toml_config_manager.py
```

✅ Infraestructura para ambientes existente pero no usada en Docker

---

## 🔍 Análisis Profundo

### PROBLEMA 1: Hardcoded APP_ENV en Dockerfile

**Dockerfile.fastapi (línea 54)**
```dockerfile
ENV APP_ENV=local  # ❌ SIEMPRE "local"
```

**Impacto:**
- Production images dicen `local`
- No hay diferencia entre ambientes
- Configs incorrectas se cargan
- Logs/errores no funcionan bien

---

### PROBLEMA 2: No hay Build Args

**Dockerfiles actuales:**
```dockerfile
# NO ACEPTAN build args
ENV APP_ENV=local
```

**Debería ser:**
```dockerfile
# Con ARG podemos pasar en build time
ARG APP_ENV=local
ENV APP_ENV=${APP_ENV}
```

---

### PROBLEMA 3: Workflow no pasa ENV variables

**build.yml actual:**
```yaml
build-args: |
  ${{ matrix.build_args }}  # Solo para MCPs
```

**Debería enviar:**
```yaml
build-args: |
  APP_ENV=${{ env.IMAGE_VERSION }}
```

---

## ✅ SOLUCIÓN RECOMENDADA

### 1️⃣ Actualizar Dockerfiles (Simple)

**Cambio en TODOS los Dockerfiles:**

```dockerfile
# ANTES:
ENV APP_ENV=local

# DESPUÉS:
ARG APP_ENV=local
ENV APP_ENV=${APP_ENV}
```

**Archivos a actualizar (14 total):**
- Dockerfile.fastapi
- Dockerfile.celery
- Dockerfile.celery-beat
- Dockerfile.celery-workers.* (9 files)
- Dockerfile.mcp
- Dockerfile.tx-confirmation

---

### 2️⃣ Actualizar Workflow GitHub Actions

**En `.github/workflows/build.yml`:**

```yaml
# Cambiar build-args en TODOS los servicios:

DE:
  build-args: |
    ${{ matrix.build_args }}

A:
  build-args: |
    APP_ENV=${{ env.IMAGE_VERSION }}
    ${{ matrix.build_args }}
```

**Resultado:**
```
master → APP_ENV=production
staging → APP_ENV=staging
infra → APP_ENV=development
```

---

### 3️⃣ Docker Compose (Ya está bien)

**docker-compose.yaml - YA TIENE:**
```yaml
environment:
  - APP_ENV=local  # ✅ Correcto para local
```

---

## 📋 IMPLEMENTACIÓN

### Paso 1: Actualizar Dockerfiles

Cambiar esta línea en los 14 Dockerfiles:

```dockerfile
# ANTES (Línea ~54 en fastapi, ~42 en otros)
ENV APP_ENV=local

# DESPUÉS
ARG APP_ENV=local
ENV APP_ENV=${APP_ENV}
```

### Paso 2: Actualizar Workflow

Cambiar el step "Build and Push" en `build.yml`:

```yaml
- name: Build and Push - ${{ matrix.service }}
  uses: docker/build-push-action@v5
  with:
    context: .
    file: ${{ matrix.dockerfile }}
    push: ${{ github.event_name == 'push' }}
    tags: ${{ steps.meta.outputs.tags }}
    labels: ${{ steps.meta.outputs.labels }}
    cache-from: type=gha
    cache-to: type=gha,mode=max
    build-args: |
      APP_ENV=${{ env.IMAGE_VERSION }}
      ${{ matrix.build_args }}
```

### Paso 3: Testing

```bash
# Test local build con APP_ENV=production
docker build --build-arg APP_ENV=production -f docker/Dockerfile.fastapi -t test:prod .

# Verificar variable
docker run --rm test:prod env | grep APP_ENV
# Output: APP_ENV=production ✅
```

---

## 🎯 Cómo Funcionaría

### Flujo Actual (❌ PROBLEMA)
```
Push a master
    ↓
Workflow: IMAGE_VERSION=production ✅
    ↓
Docker build con APP_ENV=local ❌
    ↓
Image tiene app.env=local (INCORRECTO para production)
    ↓
Config cargada: dev/config.toml (no prod/config.toml) ❌
```

### Flujo Propuesto (✅ CORRECTO)
```
Push a master
    ↓
Workflow: IMAGE_VERSION=production ✅
    ↓
Docker build ARG APP_ENV=production ✅
    ↓
Image tiene APP_ENV=production ✅
    ↓
Config cargada: prod/config.toml ✅
    ↓
Settings correctos: DB production, timeouts production, etc ✅
```

---

## 📊 Comparativa de Ambientes

### Desarrollo (infra branch)
```
APP_ENV=development
Config: config/dev/
Logging: DEBUG
Cache: 1 hour
DB Timeout: 30s
Workers: Low concurrency
```

### Staging (staging branch)
```
APP_ENV=staging
Config: config/dev/ (same as dev but on staging infrastructure)
Logging: INFO
Cache: 24 hours
DB Timeout: 60s
Workers: Medium concurrency
```

### Producción (master branch)
```
APP_ENV=production
Config: config/prod/
Logging: ERROR only
Cache: 7 days
DB Timeout: 300s
Workers: Full concurrency
Resources: Maximum
```

---

## 🔒 Seguridad

Con esta implementación:
- ✅ Production images no cargan dev configs
- ✅ Dev images no usan production secrets
- ✅ Environment diferenciación es clara
- ✅ Menos riesgo de misconfiguration

---

## ⚡ Performance Impact

**Build time:** +0 segundos (no hay diferencia)
**Image size:** +0 MB (ARG no se incluye en imagen)
**Runtime:** Mejor (configs optimizadas por ambiente)

---

## 🚀 Beneficios

✅ Imágenes correctamente configuradas por ambiente  
✅ Configs automáticamente se cargan según APP_ENV  
✅ Seguridad mejorada (producción ≠ desarrollo)  
✅ Manejo consistente de variables  
✅ Escalable a más ambientes (QA, UAT, etc.)  
✅ Debugging más fácil (logs incluyen APP_ENV)  

---

## 💡 Alternativas (No Recomendadas)

### ❌ Altrnativa 1: Environment-specific Dockerfiles
- 14 Dockerfiles → 42 Dockerfiles (3x cada uno)
- Duplicación de código
- Hard de mantener
- Versioning complicado

### ❌ Alternativa 2: Entrepoint script dinámico
- Complejidad innecesaria
- Runtime overhead
- Debugging más difícil

### ✅ Alternativa 3: Nuestro enfoque (RECOMENDADO)
- Build-time variable (mejor práctica)
- Simple de implementar
- Sin overhead runtime
- Standard Docker pattern

---

## 📝 Resumen de Cambios

| Componente | Cambio | Lineas | Complejidad |
|-----------|--------|--------|------------|
| Dockerfiles | ARG APP_ENV | ~1 línea c/u | Trivial |
| Workflow | build-args | ~1 línea | Trivial |
| Config | Ya existe | 0 | N/A |
| Docker-compose | Nada | 0 | N/A |

**Total:** 14 Dockerfiles + 1 workflow = 15 cambios simples

---

## ✨ Siguiente Pasos

1. ✅ Entender por qué es necesario (este documento)
2. ⏳ Aplicar cambios a Dockerfiles (1 línea c/u)
3. ⏳ Actualizar workflow GitHub Actions
4. ⏳ Test en cada rama (dev/staging/prod)
5. ⏳ Commit y push

¿Quieres que proceda con los cambios?

---

**Decisión:**

- [ ] Aplicar cambios ahora
- [ ] Más preguntas primero

