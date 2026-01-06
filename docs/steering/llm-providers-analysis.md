# Análisis de Proveedores LLM Configurados

**Fecha**: 6 de Enero, 2026  
**Estado**: Análisis de configuración actual

---

## Resumen Ejecutivo

El sistema Anvil Backend está configurado con **2 proveedores LLM principales**:

1. **Vertex AI (Google Gemini 2.0)** - Proveedor primario
2. **DeepInfra (Meta Llama)** - Proveedor de fallback

**OpenAI (GPT-4) ha sido eliminado** debido a costos 50-187x más altos.

---

## 1. Vertex AI (Google Gemini 2.0 Flash)

### Configuración
- **Proveedor**: Google Cloud Vertex AI
- **Modelo**: `gemini-2.0-flash-exp`
- **Rol**: Proveedor primario
- **Archivo de configuración**: `config/local/.secrets.toml` → `[vertex_ai]`

### Costos por Millón de Tokens
- **Input**: $0.10/1M tokens
- **Output**: $0.40/1M tokens
- **Promedio** (50/50 input/output): ~$0.25/1M tokens

### Modelos Mapeados
```python
{
    "gpt-4o": "gemini-2.0-flash-exp",
    "gpt-4o-mini": "gemini-2.0-flash-exp",
    "gpt-4": "gemini-1.5-pro",  # Para tareas complejas
    "gpt-3.5-turbo": "gemini-2.0-flash-exp"
}
```

### Uso
- **Primary Provider** en `config/local/config.toml`
- Usado por todos los agentes del Agent Squad (18 agentes)
- Usado por Hunter AI para análisis de mercado
- Usado por Chat para conversación general

### Archivos de Implementación
- `src/app/infrastructure/adapters/agent_squad/llm_client_vertex_ai.py`
- `src/app/setup/config/llm_orchestration.py` → `VertexAIConfig`

---

## 2. DeepInfra (Meta Llama)

### Configuración
- **Proveedor**: DeepInfra API
- **Modelos**: Meta Llama 3.2 3B, Llama 3.1 70B, Llama 3.1 405B
- **Rol**: Proveedor de fallback (más económico)
- **Archivo de configuración**: `config/local/.secrets.toml` → `[deepinfra]`

### Costos por Millón de Tokens
- **Unificado**: $0.08/1M tokens (input + output)
- **68% más barato** que Vertex AI

### Modelos Mapeados
```python
{
    "gpt-4o": "meta-llama/Meta-Llama-3.1-70B-Instruct",
    "gpt-4o-mini": "meta-llama/Llama-3.2-3B-Instruct",
    "gpt-4": "meta-llama/Meta-Llama-3.1-405B-Instruct",
    "gpt-3.5-turbo": "meta-llama/Llama-3.2-3B-Instruct"
}
```

### Uso
- **Fallback Provider** en `config/local/config.toml`
- Se activa automáticamente cuando Vertex AI falla
- Más económico que Vertex AI (ahorro del 68%)

### Archivos de Implementación
- `src/app/infrastructure/adapters/agent_squad/llm_client_deepinfra.py`
- `src/app/setup/config/llm_orchestration.py` → `DeepInfraConfig`

---

## 3. OpenAI (GPT-4) - **REMOVED**

### Estado
- **❌ ELIMINADO**: OpenAI provider ha sido removido del código
- **Razón**: Costos 50-187x más altos que Vertex AI/DeepInfra
- **Fecha de eliminación**: Enero 2026

### Costos (Histórico - Ya no se usa)
- **GPT-4o**: $5.00-15.00/1M tokens
- **GPT-4o-mini**: $0.15-0.60/1M tokens
- **50-187x más caro** que Vertex AI/DeepInfra

### Nota
El paquete `openai` sigue en `pyproject.toml` porque:
- DeepInfra usa la API compatible con OpenAI (requiere el paquete `openai`)
- Agno requiere `openai` para modelos OpenAI (si se usa Agno)

Pero la implementación de `LLMClientOpenAI` (que llama directamente a la API de OpenAI) ha sido eliminada.

---

## Comparación de Costos

| Proveedor | Modelo | Costo/1M tokens | Relación de Costo |
|-----------|--------|-----------------|-------------------|
| **DeepInfra** | Llama 3.2 3B / 70B | **$0.08** | 1x (más barato) |
| **Vertex AI** | Gemini 2.0 Flash | **$0.10-0.40** | 1.25-5x |
| ~~**OpenAI**~~ | ~~GPT-4o~~ | ~~$5.00-15.00~~ | ~~62.5-187.5x~~ **REMOVED** |

### Ahorro vs OpenAI (Histórico)
- **Vertex AI**: 91.6% de ahorro vs OpenAI GPT-4o
- **DeepInfra**: 97.7% de ahorro vs OpenAI GPT-4o
- **OpenAI eliminado** para evitar costos excesivos

---

## Estrategia de Fallback

### Orden de Prioridad
1. **Vertex AI** (Gemini 2.0) - Primario
2. **DeepInfra** (Meta Llama) - Fallback automático
3. ~~**OpenAI** (GPT-4)~~ - **REMOVED** (no disponible)

### Triggers de Fallback
- Error de API de Vertex AI
- Rate limit excedido
- Timeout (>30 segundos)
- Respuesta inválida

### Impacto de Costo del Fallback
- **Positivo**: DeepInfra es más barato que Vertex AI (68% ahorro)
- **Neutral**: El fallback automático asegura confiabilidad
- **Sin impacto negativo**: El fallback reduce costos

---

## Configuración Actual

### Archivo: `config/local/config.toml`

```toml
[llm_provider]
# Primary provider for agent squad (vertex_ai, deepinfra, openai)
primary_provider = "vertex_ai"

# Fallback provider (used when primary fails)
fallback_provider = "deepinfra"

# Enable automatic fallback
enable_fallback = true

[llm_provider.vertex_ai]
# Model mapping (OpenAI model names -> Gemini models)
model_mapping = {
    "gpt-4o" = "gemini-2.0-flash-exp",
    "gpt-4o-mini" = "gemini-2.0-flash-exp",
    "gpt-4" = "gemini-1.5-pro"
}

[llm_provider.deepinfra]
# Model mapping (OpenAI model names -> Llama models)
model_mapping = {
    "gpt-4o" = "meta-llama/Meta-Llama-3.1-70B-Instruct",
    "gpt-4o-mini" = "meta-llama/Llama-3.2-3B-Instruct",
    "gpt-4" = "meta-llama/Meta-Llama-3.1-405B-Instruct"
}
```

### Archivo: `config/local/.secrets.toml`

```toml
# Vertex AI (Google Gemini) - Primary Provider
[vertex_ai]
API_KEY = "your-vertex-ai-api-key"
# Get from: Google Cloud Console

# DeepInfra (Meta Llama) - Fallback Provider
[deepinfra]
API_KEY = "your-deepinfra-api-key"
BASE_URL = "https://api.deepinfra.com/v1/openai"
# Get from: https://deepinfra.com/dash/api_keys

# OpenAI REMOVED - Not supported anymore
# [openai]
# API_KEY = ""
# OpenAI provider has been removed. Use vertex_ai or deepinfra instead.
```

---

## Nota sobre "Vercel"

**Aclaración**: El usuario mencionó "Gemini 2.0 (Vercel)", pero en el código:
- **No hay configuración de Vercel** para LLMs
- **Vertex AI** es el proveedor de Google Gemini (no Vercel)
- **Vercel** es una plataforma de deployment (Next.js, frontend), no un proveedor LLM

**Posible confusión**: 
- Vertex AI (Google Cloud) → Gemini 2.0
- Vercel (plataforma de hosting) → No relacionado con LLMs

---

## Recomendaciones

### Configuración Actual (Recomendada)
✅ **Vertex AI como primario** - Excelente balance costo/calidad  
✅ **DeepInfra como fallback** - Más económico y confiable  
✅ **OpenAI opcional** - Solo para casos especiales

### Optimización de Costos
1. **Usar DeepInfra como primario para Chat** - Ahorro del 68%
2. **Mantener Vertex AI para análisis complejos** - Mejor calidad
3. **Evitar OpenAI en producción** - 50-187x más caro

### Monitoreo
- Costos por proveedor: `GET /api/v1/admin/llm/telemetry/costs`
- Tokens usados por modelo
- Tasa de fallback (Vertex AI → DeepInfra)

---

## Referencias

- Documentación completa: [llm-models-cost-analysis.md](./llm-models-cost-analysis.md)
- Configuración: `config/local/config.toml`
- Secrets: `config/local/.secrets.toml`
- Implementación: `src/app/infrastructure/adapters/agent_squad/llm_client_*.py`
