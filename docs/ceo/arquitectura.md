# Arquitectura del Sistema Anvil Backend

**Documento para CEO**  
**Fecha**: Enero 2026  
**Versión**: 1.0  
**Estado**: Producción ✅

---

## Executive Summary

Anvil Backend es una plataforma de **arquitectura hexagonal** (Clean Architecture) diseñada para escalar y mantener código de alta calidad. El sistema maneja tres flujos principales de chat:

1. **Guest Chat** (`/api/v1/guest/chat`) - Usuarios no autenticados con capacidades limitadas
2. **Conversations** (`/api/v1/conversations/{id}/messages`) - Sistema completo para usuarios autenticados y guests
3. **Execute Actions** (`/api/v1/conversations/{id}/execute`) - Ejecución de transacciones DeFi

**Arquitectura Clave**:
- **18 Agentes Especializados** (AgentSquad) para diferentes tareas DeFi
- **Sistema de Orquestación Inteligente** que enruta automáticamente al agente correcto
- **Arquitectura Hexagonal** que separa lógica de negocio de infraestructura
- **99% de Ahorro en Costos** vs OpenAI mediante Vertex AI + DeepInfra

---

## Arquitectura General del Backend

### Principio: Arquitectura Hexagonal (Clean Architecture)

La arquitectura hexagonal separa el código en **4 capas concéntricas**, donde las capas internas no dependen de las externas:

```
┌─────────────────────────────────────────────────────────────┐
│                    ARQUITECTURA HEXAGONAL                  │
└─────────────────────────────────────────────────────────────┘

    ┌──────────────────────────────────────────┐
    │   PRESENTATION LAYER                      │  ← HTTP Controllers
    │   (FastAPI Routers)                       │     (Interfaz Externa)
    └──────────────┬───────────────────────────┘
                   │
    ┌──────────────▼───────────────────────────┐
    │   APPLICATION LAYER                      │  ← Use Cases
    │   (Commands & Queries)                   │     (Lógica de Aplicación)
    └──────────────┬───────────────────────────┘
                   │
    ┌──────────────▼───────────────────────────┐
    │   DOMAIN LAYER                           │  ← Business Logic
    │   (Entities & Value Objects)             │     (Reglas de Negocio)
    └──────────────┬───────────────────────────┘
                   │
    ┌──────────────▼───────────────────────────┐
    │   INFRASTRUCTURE LAYER                   │  ← Implementaciones
    │   (Database, APIs, External Services)    │     (Detalles Técnicos)
    └──────────────────────────────────────────┘
```

### Capas del Sistema

#### 1. Domain Layer (Capa de Dominio)
**Ubicación**: `src/app/domain/`

**Qué contiene**:
- **Entidades**: Objetos de negocio con identidad (Conversation, Message, User)
- **Value Objects**: Objetos inmutables (AgentType, MessageRole)
- **Ports (Interfaces)**: Contratos que definen qué necesita el negocio
- **Domain Services**: Lógica de negocio que no pertenece a una entidad específica

**Características**:
- ✅ **NO depende** de ninguna otra capa
- ✅ Contiene las **reglas de negocio fundamentales**
- ✅ Es la capa más **estable** del sistema

**Ejemplo**:
```python
# Domain Entity
class Conversation:
    """Conversación entre usuario y agentes"""
    id: UUID
    user_id: UUID
    messages: list[Message]
    
    def add_message(self, message: Message):
        """Regla de negocio: agregar mensaje"""
        self.messages.append(message)
        self.updated_at = datetime.now()
```

---

#### 2. Application Layer (Capa de Aplicación)
**Ubicación**: `src/app/application/`

**Qué contiene**:
- **Commands**: Operaciones de escritura (CreateConversation, SendMessage)
- **Queries**: Operaciones de lectura optimizadas (GetConversation, ListConversations)
- **Services**: Servicios de aplicación (IntentDetector, ConversationMemory)

**Características**:
- ✅ **Depende SOLO** de Domain Layer
- ✅ Orquesta la lógica de negocio y llamadas externas
- ✅ Cada interactor maneja **un caso de uso** específico

**Ejemplo**:
```python
# Application Command
class SendMessage:
    """Caso de uso: Enviar mensaje a conversación"""
    
    async def execute(self, conversation_id, content):
        # 1. Obtener conversación (Domain)
        conversation = await self._repo.get(conversation_id)
        
        # 2. Crear mensaje (Domain)
        message = Message.create(content)
        
        # 3. Detectar intent (Application Service)
        intent = await self._intent_detector.detect(content)
        
        # 4. Route a agente (Infrastructure)
        agent_response = await self._agent_gateway.process(intent)
        
        # 5. Guardar (Infrastructure)
        await self._repo.save(conversation, message)
        
        return agent_response
```

---

#### 3. Infrastructure Layer (Capa de Infraestructura)
**Ubicación**: `src/app/infrastructure/`

**Qué contiene**:
- **Adapters**: Implementaciones de los ports del Domain
- **Persistence**: SQLAlchemy para base de datos
- **External APIs**: Clientes para servicios externos (1inch, DeFiLlama, etc.)
- **Agent Squad**: Implementación de los 18 agentes especializados

**Características**:
- ✅ **Implementa** los ports definidos en Domain
- ✅ Contiene todos los detalles técnicos (base de datos, APIs, etc.)
- ✅ Puede cambiar sin afectar Domain o Application

**Ejemplo**:
```python
# Infrastructure Adapter
class ConversationRepositorySqla(ConversationRepository):
    """Implementa ConversationRepository usando SQLAlchemy"""
    
    async def save(self, conversation: Conversation):
        # Detalles técnicos de SQLAlchemy
        db_conversation = ConversationMapping.from_domain(conversation)
        self._session.add(db_conversation)
        await self._session.commit()
```

---

#### 4. Presentation Layer (Capa de Presentación)
**Ubicación**: `src/app/presentation/http/`

**Qué contiene**:
- **Controllers**: Endpoints HTTP (FastAPI routers)
- **Schemas**: Modelos de request/response (Pydantic)
- **Auth**: Middleware de autenticación

**Características**:
- ✅ **Capa más externa** - recibe requests HTTP
- ✅ **Delgada** - solo valida input y delega a Application Layer
- ✅ **Framework-agnostic** - Domain/Application no saben que es FastAPI

**Ejemplo**:
```python
# Presentation Controller
@router.post("/conversations/{id}/messages")
async def send_message(
    conversation_id: UUID,
    request: SendMessageRequest,
    interactor: SendMessage = Depends(),
):
    """Endpoint HTTP - solo valida y delega"""
    result = await interactor.execute(
        conversation_id=conversation_id,
        content=request.content,
    )
    return MessageResponse.from_domain(result)
```

---

## Sistemas de Orquestación y Procesamiento

### 1. Destilador (Distillation Orchestrator)

#### ¿Qué es el Destilador?

El **Destilador** es un sistema inteligente que **valida y optimiza** las requests de los usuarios **antes** de procesarlas con LLM. Actúa como un "filtro inteligente" que:

1. **Clasifica la intención** del usuario
2. **Evalúa la complejidad** de la pregunta
3. **Extrae entidades** (tokens, protocolos, chains)
4. **Decide la ruta óptima**: Cache → Static Response → LLM Completo
5. **Registra telemetría** para análisis y optimización

#### Arquitectura del Destilador

```
┌─────────────────────────────────────────────────────────────┐
│              DISTILLATION ORCHESTRATOR FLOW                  │
└─────────────────────────────────────────────────────────────┘

Usuario: "¿Cuál es el mejor yield para USDC?"
    │
    ▼
┌─────────────────────────────┐
│   Request Preprocessor      │  ← Preprocesa request
│   - Normaliza texto         │
│   - Detecta idioma          │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│   Intent Classifier          │  ← Clasifica intención
│   - yield_optimization       │
│   - Confidence: 0.92         │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│   Complexity Assessor       │  ← Evalúa complejidad
│   - Complexity: LOW          │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│   Entity Extractor           │  ← Extrae entidades
│   - Token: USDC              │
│   - Chain: (none)            │
└──────────────┬──────────────┘
               │
    ┌──────────┴──────────┐
    │                     │
    ▼                     ▼
┌──────────┐      ┌──────────────┐
│ Check    │      │ Check Static │
│ Cache    │      │ Response     │
│ (Exact)  │      │              │
└─────┬────┘      └──────┬───────┘
      │                   │
      └──────────┬────────┘
                 │
    ┌────────────┴────────────┐
    │                         │
    ▼                         ▼
Cache Hit?              Static Available?
    │                         │
    ▼                         ▼
┌──────────┐          ┌──────────────┐
│ Return   │          │ Return       │
│ Cached   │          │ Static       │
│ Response │          │ Response     │
└──────────┘          └──────────────┘
    │                         │
    └──────────┬──────────────┘
               │
               ▼
      ┌───────────────────────┐
      │ Route Decision        │  ← Decide ruta óptima
      │ - CACHE: Return cached│
      │ - STATIC: Return static│
      │ - FULL_LLM: Process   │
      └───────────┬───────────┘
                  │
                  ▼
      ┌───────────────────────┐
      │ Record Telemetry      │  ← Registra métricas
      │ - Intent              │
      │ - Complexity          │
      │ - Route Type          │
      │ - Latency             │
      └───────────────────────┘
```

#### Proceso de Destilación

**Step 1: Preprocessing**
```python
# Normaliza y prepara el request
request = preprocessor.preprocess(
    user_message="¿Cuál es el mejor yield para USDC?",
    conversation_history=[...],
    user_id="123",
    conversation_id="456",
)
# Output: {
#   "normalized_text": "cual es el mejor yield para usdc",
#   "detected_language": "es",
#   "message_length": 35
# }
```

**Step 2: Intent Classification**
```python
# Clasifica la intención
intent, confidence = intent_classifier.classify("cual es el mejor yield para usdc")
# Output: ("yield_optimization", 0.92)
```

**Step 3: Complexity Assessment**
```python
# Evalúa complejidad
complexity = complexity_assessor.assess(query, intent)
# Output: "LOW" (pregunta simple, directa)
```

**Step 4: Entity Extraction**
```python
# Extrae entidades
entities = entity_extractor.extract("cual es el mejor yield para usdc")
# Output: {
#   "tokens": ["USDC"],
#   "chains": [],
#   "amounts": []
# }
```

**Step 5: Cache Lookup**
```python
# Busca en cache (exact match → semantic similarity)
cache_hit, cache_level = cache_manager.get(
    cache_key="distill:v1:abc123...",
    query="cual es el mejor yield para usdc",
    semantic_threshold=0.85,
)
# Output: (None, CacheLevel.NONE)  # No hay cache hit
```

**Step 6: Static Response Check**
```python
# Verifica si hay respuesta estática disponible
static_available = static_responder.check_available(
    intent="yield_optimization",
    entities={"tokens": ["USDC"]},
)
# Output: False  # No hay respuesta estática
```

**Step 7: Routing Decision**
```python
# Decide la ruta óptima
result = router.route(
    text="cual es el mejor yield para usdc",
    cache_lookup=None,
    static_available=False,
)
# Output: {
#   "should_process": True,
#   "route_type": "FULL_LLM",  # Necesita LLM completo
#   "intent": "yield_optimization",
#   "complexity": "LOW"
# }
```

**Step 8: Telemetry Recording**
```python
# Registra telemetría
await telemetry_repo.record({
    "request_id": "req_123",
    "user_id": "123",
    "query": "cual es el mejor yield para usdc",
    "intent": "yield_optimization",
    "complexity": "LOW",
    "route_type": "FULL_LLM",
    "latency_ms": 45,
    "timestamp": "2026-01-15T10:30:00Z"
})
```

#### Tipos de Routing

**A. CACHE Route** (Respuesta desde Cache)
- **Cuándo**: Query exacto o semánticamente similar ya procesado
- **Ventaja**: Respuesta instantánea, costo $0
- **Ejemplo**: "¿Cuál es el mejor yield para USDC?" (ya preguntado antes)

**B. STATIC Route** (Respuesta Estática)
- **Cuándo**: Pregunta simple con respuesta predefinida
- **Ventaja**: Respuesta instantánea, costo $0
- **Ejemplo**: "¿Qué es Bitcoin?" → Respuesta estática desde knowledge base

**C. FULL_LLM Route** (LLM Completo)
- **Cuándo**: Pregunta compleja que requiere razonamiento
- **Ventaja**: Respuesta personalizada y contextual
- **Costo**: ~$0.0001 por request
- **Ejemplo**: "Crea un portfolio balanceado con yield optimization"

#### Beneficios del Destilador

1. **Reducción de Costos**: 50-70% de requests resueltas sin LLM
2. **Mejor Latencia**: Cache/Static responses en < 100ms vs 2-3s con LLM
3. **Telemetría Completa**: Tracking de todos los requests para optimización
4. **Fail-Safe**: Si destilador falla, permite request (fail-open)

---

### 2. Telemetría (LLM Telemetry System)

#### ¿Qué es la Telemetría?

El sistema de **Telemetría** rastrea y analiza **todas las interacciones con LLMs** para:
- Monitorear costos y uso
- Detectar problemas de rendimiento
- Optimizar selección de modelos
- Alertar sobre presupuestos

#### Componentes de Telemetría

**A. LLM Telemetry** (Tracking de LLM Calls)
```
┌─────────────────────────────────────────────────────────────┐
│              LLM TELEMETRY FLOW                            │
└─────────────────────────────────────────────────────────────┘

LLM Call Iniciado
    │
    ▼
┌─────────────────────────────┐
│   Start Call Context        │  ← Crea contexto de tracking
│   - call_id: uuid           │
│   - provider: vertex_ai     │
│   - model: gemini-2.0-flash │
│   - start_time: timestamp   │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│   Execute LLM Call          │  ← Ejecuta llamada
│   (Vertex AI API)           │
└──────────────┬──────────────┘
               │
    ┌──────────┴──────────┐
    │                     │
    ▼                     ▼
Success?              Error?
    │                     │
    ▼                     ▼
┌──────────┐      ┌──────────────┐
│ Complete │      │ Record Error │
│ Context  │      │              │
│ - tokens │      │ - error_type │
│ - cost   │      │ - error_msg  │
│ - latency│      │              │
└─────┬────┘      └──────┬───────┘
      │                   │
      └──────────┬────────┘
                 │
                 ▼
      ┌───────────────────────┐
      │ Record Telemetry      │  ← Guarda en base de datos
      │ (PostgreSQL)          │
      └───────────────────────┘
                 │
                 ▼
      ┌───────────────────────┐
      │ Update Metrics        │  ← Actualiza métricas
      │ - Total tokens        │
      │ - Total cost          │
      │ - Success rate        │
      │ - Avg latency         │
      └───────────────────────┘
```

**B. Distillation Telemetry** (Tracking de Destilación)
- Rastrea todas las decisiones del destilador
- Mide latencia de cada paso (classification, routing, etc.)
- Registra cache hits/misses
- Trackea static response usage

**C. Retry Telemetry** (Tracking de Reintentos)
- Rastrea fallos y reintentos de LLM calls
- Mide circuit breaker states
- Registra fallback usage

#### Métricas Rastreadas

**Por Provider/Model**:
- Total requests
- Success rate
- Error rate
- Average latency (P50, P90, P99)
- Total tokens (input + output)
- Total cost (USD)
- Rate limit events

**Por Intent**:
- Intent distribution
- Average confidence
- Route type distribution (CACHE/STATIC/FULL_LLM)
- Average latency per intent

**Por Usuario**:
- Requests per user
- Cost per user
- Most common intents

#### Dashboard de Telemetría

**Endpoints Admin**:
- `GET /api/v1/admin/llm/telemetry` - Métricas generales
- `GET /api/v1/admin/llm/telemetry/providers` - Métricas por provider
- `GET /api/v1/admin/llm/telemetry/models` - Métricas por modelo
- `GET /api/v1/admin/distillation/telemetry` - Métricas de destilación

---

### 3. Orchestrator con Multi-Intent

#### ¿Qué es Multi-Intent?

El sistema de **Multi-Intent** detecta y procesa **múltiples intenciones en un solo mensaje** del usuario.

**Ejemplos**:
- "Show BTC ETH ADA prices" → 3 intents de precio (paralelo)
- "Swap USDC to ETH and show balance" → 2 intents con dependencia (secuencial)
- "Buy Bitcoin if price drops below 90k" → 2 intents con condición (condicional)

#### Arquitectura Multi-Intent

```
┌─────────────────────────────────────────────────────────────┐
│              MULTI-INTENT ORCHESTRATION                    │
└─────────────────────────────────────────────────────────────┘

Usuario: "Show BTC ETH ADA prices"
    │
    ▼
┌─────────────────────────────┐
│   IntentDetectorV2          │  ← Detecta múltiples intents
│   .detect_multi_intent()    │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│   Extract Entities          │  ← Extrae tokens
│   - tokens: [BTC, ETH, ADA] │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│   Expand by Entities        │  ← Crea intent por token
│   - Intent 1: BTC price     │
│   - Intent 2: ETH price      │
│   - Intent 3: ADA price      │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│   Detect Dependencies       │  ← Analiza dependencias
│   - None (independent)      │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│   Determine Strategy        │  ← Decide estrategia
│   - PARALLEL (independent)  │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│   IntentOrchestrator        │  ← Ejecuta intents
│   .execute()                │
└──────────────┬──────────────┘
               │
    ┌──────────┴──────────┐
    │                     │
    ▼                     ▼
PARALLEL            SEQUENTIAL
    │                     │
    ▼                     ▼
┌──────────┐      ┌──────────────┐
│ Execute  │      │ Execute      │
│ All at   │      │ in Order     │
│ Once     │      │ (with deps)  │
│ (async)  │      │              │
└─────┬────┘      └──────┬───────┘
      │                   │
      └──────────┬────────┘
                 │
                 ▼
      ┌───────────────────────┐
      │ Aggregate Results    │  ← Combina resultados
      │ - BTC: $45,000       │
      │ - ETH: $3,200        │
      │ - ADA: $0.50         │
      └───────────────────────┘
                 │
                 ▼
      ┌───────────────────────┐
      │ Format Response      │  ← Formatea respuesta
      │ "BTC: $45,000        │
      │  ETH: $3,200         │
      │  ADA: $0.50"         │
      └───────────────────────┘
```

#### Estrategias de Orquestación

**A. PARALLEL** (Ejecución Paralela)
- **Cuándo**: Intents independientes sin dependencias
- **Ejemplo**: "Show BTC ETH ADA prices"
- **Proceso**: Ejecuta todos los intents simultáneamente usando `asyncio.gather()`
- **Tiempo**: ~2-3s (mismo que un solo intent)

**B. SEQUENTIAL** (Ejecución Secuencial)
- **Cuándo**: Intents con dependencias (uno necesita resultado del otro)
- **Ejemplo**: "Swap USDC to ETH and show balance"
- **Proceso**: Ejecuta en orden, pasando contexto entre intents
- **Tiempo**: ~4-6s (suma de tiempos individuales)

**C. CONDITIONAL** (Ejecución Condicional)
- **Cuándo**: Segundo intent depende de condición del primero
- **Ejemplo**: "Buy Bitcoin if price drops below 90k"
- **Proceso**: Ejecuta primer intent, evalúa condición, ejecuta segundo si condición se cumple
- **Tiempo**: ~3-5s (depende de condición)

#### Ejemplo Completo: Multi-Intent Paralelo

**Input**: "Show BTC ETH ADA prices"

**Step 1: Entity Extraction**
```python
entities = extract_entities("show btc eth ada prices")
# Output: {"tokens": ["btc", "eth", "ada"]}
```

**Step 2: Intent Detection**
```python
# Detecta keyword "price" + múltiples tokens
intents = detect_all_intents("show btc eth ada prices", entities)
# Output: [
#   IntentResult(intent=HUNTER_PRICE_PREDICTION, entities=["BTC"]),
#   IntentResult(intent=HUNTER_PRICE_PREDICTION, entities=["ETH"]),
#   IntentResult(intent=HUNTER_PRICE_PREDICTION, entities=["ADA"]),
# ]
```

**Step 3: Dependency Detection**
```python
dependencies = detect_dependencies(intents)
# Output: []  # No hay dependencias (intents independientes)
```

**Step 4: Strategy Determination**
```python
strategy = determine_strategy(intents, dependencies)
# Output: OrchestrationStrategy.PARALLEL
```

**Step 5: Parallel Execution**
```python
# Ejecuta los 3 intents en paralelo
results = await asyncio.gather(
    execute_intent(intents[0]),  # BTC price
    execute_intent(intents[1]),  # ETH price
    execute_intent(intents[2]),  # ADA price
)
# Output: [
#   {"token": "BTC", "price": 45000},
#   {"token": "ETH", "price": 3200},
#   {"token": "ADA", "price": 0.50},
# ]
```

**Step 6: Response Formatting**
```python
formatted = format_multi_intent_response(results)
# Output: "💰 Precios Actuales:\n\nBTC: $45,000\nETH: $3,200\nADA: $0.50"
```

---

### 4. Knowledge Questions (GraphRAG)

#### ¿Qué son Knowledge Questions?

Las **Knowledge Questions** son preguntas que requieren **conocimiento estructurado** sobre protocolos DeFi, relaciones entre protocolos, y análisis de riesgo. Estas preguntas usan **GraphRAG** (Graph Retrieval-Augmented Generation) en lugar de LLM directo.

#### Intents de Knowledge

**A. PROTOCOL_SEARCH** (Búsqueda de Protocolos)
- **Ejemplo**: "Find low-risk staking protocols on Ethereum"
- **Handler**: GraphRAG handler
- **Proceso**: Busca en knowledge graph de protocolos DeFi
- **Ventaja**: Respuestas precisas basadas en datos estructurados

**B. RISK_ASSESSMENT** (Evaluación de Riesgo)
- **Ejemplo**: "Is Aave safe? What are the risks?"
- **Handler**: GraphRAG handler
- **Proceso**: Analiza riesgo usando knowledge graph de protocolos
- **Ventaja**: Análisis sistémico de riesgos (no solo opinión LLM)

**C. SIMILAR_PROTOCOLS** (Protocolos Similares)
- **Ejemplo**: "What's similar to Uniswap?"
- **Handler**: GraphRAG handler
- **Proceso**: Busca protocolos similares en knowledge graph
- **Ventaja**: Comparaciones basadas en características reales

#### Arquitectura GraphRAG

```
┌─────────────────────────────────────────────────────────────┐
│              KNOWLEDGE QUESTIONS (GraphRAG)                 │
└─────────────────────────────────────────────────────────────┘

Usuario: "Find low-risk staking protocols on Ethereum"
    │
    ▼
┌─────────────────────────────┐
│   Intent Detection          │  ← Detecta PROTOCOL_SEARCH
│   - Intent: PROTOCOL_SEARCH │
│   - Confidence: 0.88         │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│   Extract Query Params      │  ← Extrae parámetros
│   - Risk: low               │
│   - Type: staking           │
│   - Chain: ethereum         │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│   GraphRAG Handler          │  ← Busca en knowledge graph
│   - Query knowledge graph   │
│   - Filter by risk level    │
│   - Filter by chain         │
│   - Filter by type          │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│   Knowledge Graph Query      │  ← Consulta graph database
│   - Nodes: Protocols         │
│   - Edges: Relationships     │
│   - Properties: Risk, Chain │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│   Format Results            │  ← Formatea resultados
│   - Lido: Low risk          │
│   - Rocket Pool: Low risk   │
│   - ...                     │
└─────────────────────────────┘
```

#### Knowledge Base Structure

**Knowledge Files** (`anvil_knowledge/features/`):
- `overview.json` - Overview general de Anvil
- `swap.json` - Información sobre swaps
- `hunter_ai.json` - Información sobre Hunter AI
- `ultra.json` - Información sobre ULTRA
- `shortcuts.json` - Comandos y shortcuts

**Knowledge Injector**:
- Selecciona knowledge relevante basado en intent
- Inyecta knowledge en prompts LLM cuando necesario
- Personaliza knowledge por tipo de usuario (user vs investor)

---

### 5. General Questions (LLM Directo)

#### ¿Qué son General Questions?

Las **General Questions** son preguntas generales sobre DeFi, cripto, o conceptos que no requieren datos estructurados. Estas preguntas usan **LLM directo** (Vertex AI Gemini) sin GraphRAG.

#### Intent: GENERAL_CONVERSATION

**Ejemplos**:
- "¿Qué es Bitcoin?"
- "Explain impermanent loss"
- "What is DeFi?"
- "How does staking work?"

#### Arquitectura General Questions

```
┌─────────────────────────────────────────────────────────────┐
│              GENERAL QUESTIONS FLOW                        │
└─────────────────────────────────────────────────────────────┘

Usuario: "¿Qué es Bitcoin?"
    │
    ▼
┌─────────────────────────────┐
│   Intent Detection          │  ← Detecta GENERAL_CONVERSATION
│   - Intent: GENERAL_CONVERSATION│
│   - Confidence: 0.85         │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│   Check Knowledge Injector  │  ← Inyecta knowledge si aplica
│   - Intent: GENERAL_CONVERSATION│
│   - Knowledge: overview.json│
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│   Build LLM Prompt          │  ← Construye prompt
│   - System: "You are Anvil..."│
│   - User: "¿Qué es Bitcoin?" │
│   - Context: Last 10 msgs    │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│   LLM Gateway               │  ← Llama a Vertex AI
│   - Model: gemini-2.0-flash │
│   - Temperature: 0.7        │
│   - Max tokens: 500         │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│   LLM Response              │  ← Respuesta del LLM
│   "Bitcoin es una cripto..."│
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│   Record Telemetry          │  ← Registra métricas
│   - Tokens: 150              │
│   - Cost: $0.000015         │
│   - Latency: 1.2s           │
└─────────────────────────────┘
```

#### System Prompt para General Questions

```python
system_prompt = """You are Anvil, a specialized DeFi assistant focused EXCLUSIVELY on decentralized finance, crypto trading, and blockchain technology.

✅ ALWAYS IN SCOPE (Answer these confidently):
- Cryptocurrency basics: "What is Bitcoin?", "What is Ethereum?"
- Token information: Any questions about crypto tokens
- DeFi protocols: Aave, Compound, Uniswap, Curve, etc.
- Blockchain technology: How blockchains work
- Trading & Markets: Price analysis, trading strategies
- Portfolio management: Asset allocation, risk management

⚠️ OUT OF SCOPE (Decline politely):
- General knowledge: weather, cooking, jokes, sports
- Personal advice: relationships, health, legal
- If clearly NOT crypto/blockchain related, respond: "I'm Anvil, a specialized DeFi assistant. I can only help with crypto and DeFi topics."

Response Guidelines:
- Be concise, accurate, and friendly
- Respond in the same language the user uses
- Use conversation history for context ONLY for DeFi-related exchanges"""
```

#### Características

1. **Multi-language Support**: Responde en el mismo idioma del usuario
2. **Context Awareness**: Usa últimos 10 mensajes para contexto
3. **Scope Limitation**: Solo responde sobre DeFi/crypto
4. **Cost Optimization**: Usa modelo pequeño (gemini-2.0-flash) para preguntas simples

---

## Arquitectura de Agentes (AgentSquad)

### Visión General

AgentSquad es un **sistema de orquestación multi-agente** que coordina 18 agentes especializados en diferentes aspectos de DeFi.

### Componentes Principales

#### 1. Intent Classifier (Clasificador de Intenciones)

**Qué hace**: Analiza la pregunta del usuario y determina qué agente necesita.

**Cómo funciona**:
```
Usuario: "¿Cuál es el mejor yield para USDC?"
         │
         ▼
┌─────────────────────────────┐
│   Intent Classifier         │
│   (LLM: Vertex AI Gemini)   │
└────────────┬────────────────┘
             │
             ▼
    ┌────────────────┐
    │  Intent:       │
    │  yield_opt     │
    │  Confidence:   │
    │  0.92 (92%)    │
    │  Agent:        │
    │  defi_yield    │
    └────────────────┘
```

**Proceso**:
1. Usuario envía mensaje
2. LLM analiza el mensaje y contexto
3. Calcula confidence score (0-100%)
4. Si confidence ≥ 85% → Route al agente recomendado
5. Si confidence < 85% → Fallback al Chat Agent

**Costo**: ~$0.00001 por clasificación  
**Tiempo**: ~500ms

---

#### 2. Agent Orchestrator (Orquestador de Agentes)

**Qué hace**: Coordina qué agente ejecuta qué tarea.

**Tipos de Routing**:

**A. Single Agent Routing** (Consulta Simple)
```
Usuario: "Swap 1 ETH por USDC"
         │
         ▼
Intent Classifier → confidence: 0.95
         │
         ▼
Execution Agent → Obtiene quote → Retorna respuesta
```

**B. Multi-Agent Workflow** (Tarea Compleja)
```
Usuario: "Crea un portfolio balanceado con yield optimization"
         │
         ▼
Supervisor Coordinator detecta tarea compleja
         │
         ▼
┌─────────────────────────────────────┐
│   Workflow Plan:                     │
│   1. Portfolio Agent → Analiza       │
│   2. Risk Analyzer → Evalúa riesgo   │
│   3. DeFi Yield → Encuentra yields   │
│   4. Tax Optimizer → Considera tax   │
│   5. Chat Agent → Sintetiza          │
└─────────────────────────────────────┘
         │
         ▼
Ejecución coordinada (45-60 segundos)
         │
         ▼
Respuesta final sintetizada
```

**C. Fallback Chain** (Resiliencia)
```
Intento 1: Risk Analyzer (timeout)
    ↓
Intento 2: Yield Optimizer (low confidence)
    ↓
Intento 3: Chat Agent (success)
```

---

#### 3. Los 18 Agentes Especializados

**Core Agents (10)**:
1. Chat - Conversación general
2. Hunter AI - Sentimiento de mercado
3. Research - Análisis profundo de protocolos
4. Execution - Ejecución de transacciones
5. Risk Analyzer - Análisis de riesgo
6. Portfolio - Optimización de portfolio
7. Tax Optimizer - Optimización fiscal
8. DeFi Yield - Yield farming
9. Security Auditor - Auditoría de seguridad
10. Gas Optimizer - Optimización de gas

**Enterprise Agents (4)**:
11. Compliance Monitor - Cumplimiento regulatorio
12. MultiSig Coordinator - Gestión multi-firma
13. Alert Monitoring - Alertas en tiempo real
14. Crisis Manager - Respuesta de emergencia

**Advanced Agents (4)**:
15. Bridge Crosschain - Operaciones cross-chain
16. Lending Borrowing - Estrategias de leverage
17. NFT Asset Manager - Gestión de NFTs
18. DAO Governance - Gobernanza de DAOs

**Más detalles**: Ver `docs/ceo/questions.md`

---

## Flujo: Guest Chat (`/api/v1/guest/chat`)

### Propósito

Permite a usuarios **no autenticados** interactuar con el sistema de chat con capacidades limitadas (demo mode).

### Arquitectura del Flujo

```
┌─────────────────────────────────────────────────────────────┐
│              GUEST CHAT FLOW                                │
└─────────────────────────────────────────────────────────────┘

Usuario (IP: 192.168.1.1)
    │
    ▼
POST /api/v1/guest/chat
    │
    ▼
┌─────────────────────────────┐
│   Guest Router              │  ← Presentation Layer
│   (FastAPI Controller)      │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│   SendGuestMessage          │  ← Application Layer
│   (Command Interactor)      │
└──────────────┬──────────────┘
               │
    ┌──────────┴──────────┐
    │                     │
    ▼                     ▼
┌──────────┐      ┌──────────────┐
│ Get/Create│      │ Rate Limit   │
│ Guest User│      │ Check        │
│ (by IP)   │      │ (20/hr)      │
└─────┬─────┘      └──────┬───────┘
      │                   │
      └──────────┬────────┘
                 │
                 ▼
┌─────────────────────────────┐
│   Intent Detection          │  ← Application Service
│   (IntentDetectorService)    │
└──────────────┬──────────────┘
               │
    ┌──────────┴──────────┐
    │                     │
    ▼                     ▼
Restricted?          Not Restricted?
    │                     │
    ▼                     ▼
┌──────────┐      ┌──────────────┐
│ Show     │      │ Route to      │
│ Signup   │      │ Handler       │
│ CTA      │      │ (Real Data)   │
└──────────┘      └──────┬────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │ GuestHandlerService  │  ← Application Service
              │ - Swap Handler       │
              │ - Lending Handler    │
              │ - Hunter AI          │
              │ - ULTRA              │
              │ - Agent Squad        │
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │ Save Messages        │  ← Infrastructure
              │ (GuestRepository)    │
              └──────────────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │ Return Response      │
              │ (Demo Mode)          │
              └──────────────────────┘
```

### Características Clave

1. **Auto-Creación de Usuario**: Crea automáticamente un `GuestUser` basado en IP
2. **Rate Limiting**: 20 mensajes/hora, 50 mensajes/día
3. **Demo Mode**: Muestra datos de ejemplo para acciones restringidas
4. **Real Data para Algunos Intents**: Hunter AI, ULTRA, Protocol Search usan datos reales
5. **Registration Prompts**: Muestra CTAs de registro para acciones que requieren autenticación

### Ejemplo de Flujo

**Request**:
```http
POST /api/v1/guest/chat
Content-Type: application/json

{
  "message": "¿Cuál es el mejor yield para USDC?",
  "language": "es"
}
```

**Proceso**:
1. Sistema identifica usuario por IP: `192.168.1.1`
2. Crea/obtiene `GuestUser` para esa IP
3. Verifica rate limit (20/hr)
4. Detecta intent: `PROTOCOL_SEARCH` (confidence: 0.88)
5. Route a: `GuestHandlerService.handle_intent(PROTOCOL_SEARCH)`
6. Handler consulta DeFiLlama API (datos reales)
7. Retorna: Top 3 yields para USDC con datos reales

**Response**:
```json
{
  "user_message": {...},
  "agent_message": {
    "content": "🌾 Mejores Yields USDC:\n- Aave V3: 12.5% APY\n- Compound: 11.8% APY\n- Morpho: 13.2% APY"
  },
  "routing": {
    "intent": "PROTOCOL_SEARCH",
    "confidence": 0.88,
    "handler": "protocol_search_handler"
  },
  "enrichment": {
    "protocols": [...]
  }
}
```

---

## Flujo: Conversations Messages (`/api/v1/conversations/{id}/messages`)

### Propósito

Sistema completo de conversaciones que soporta tanto usuarios **autenticados** como **guests**, con capacidades completas.

### Arquitectura del Flujo

```
┌─────────────────────────────────────────────────────────────┐
│         CONVERSATIONS MESSAGES FLOW                        │
└─────────────────────────────────────────────────────────────┘

Usuario (Authenticated o Guest)
    │
    ▼
POST /api/v1/conversations/{conversation_id}/messages
    │
    ▼
┌─────────────────────────────┐
│   Conversations Router      │  ← Presentation Layer
│   (FastAPI Controller)      │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│   Resolve Chat User         │  ← User Resolution
│   - JWT Bearer Token?       │
│   - Privy Token?            │
│   - IP Address? (Guest)     │
└──────────────┬──────────────┘
               │
    ┌──────────┴──────────┐
    │                     │
Authenticated?        Guest?
    │                     │
    ▼                     ▼
┌──────────┐      ┌──────────────┐
│ App User │      │ Guest User   │
│ (UUID)   │      │ (IP-based)   │
└─────┬────┘      └──────┬───────┘
      │                   │
      └──────────┬────────┘
                 │
                 ▼
┌─────────────────────────────┐
│   Rate Limit Check          │  ← Application Service
│   - Guest: 800/hr           │
│   - Auth: 1000/hr           │
│   - Premium: 10,000/hr     │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│   Get Conversation          │  ← Application Service
│   (Verify Ownership)        │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│   Get Conversation Context  │  ← Application Service
│   (Last 10 messages)        │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│   Intent Detection V2       │  ← Application Service
│   (With Context)             │
└──────────────┬──────────────┘
               │
    ┌──────────┴──────────┐
    │                     │
    ▼                     ▼
Pending Flow?        New Intent?
    │                     │
    ▼                     ▼
┌──────────┐      ┌──────────────┐
│ Flow     │      │ Route to     │
│ Cancellation│   │ Handler      │
│ Detection│      │              │
└─────┬────┘      └──────┬───────┘
      │                   │
      └──────────┬────────┘
                 │
    ┌────────────┴────────────┐
    │                         │
    ▼                         ▼
┌──────────┐          ┌──────────────┐
│ SWAP     │          │ Other        │
│ Handler  │          │ Handlers     │
│ V2       │          │              │
└─────┬────┘          └──────┬───────┘
      │                       │
      └───────────┬───────────┘
                  │
                  ▼
      ┌───────────────────────┐
      │ Handler Execution     │  ← Application/Infrastructure
      │ - SwapHandlerV2       │
      │ - MoonPaySwapHandler  │
      │ - GuestHandlerService │
      │ - LLMGateway          │
      └───────────┬───────────┘
                  │
                  ▼
      ┌───────────────────────┐
      │ Save Messages         │  ← Infrastructure
      │ (ChatMessageRepository)│
      └───────────────────────┘
                  │
                  ▼
      ┌───────────────────────┐
      │ Return Response       │
      │ (ChatResponse)        │
      └───────────────────────┘
```

### Características Clave

1. **User Resolution Inteligente**:
   - Prioridad 1: JWT Bearer Token (Backend auth)
   - Prioridad 2: Privy Token (Frontend auth)
   - Prioridad 3: IP Address (Guest)

2. **Conversational Memory**: Mantiene contexto de últimos 10 mensajes

3. **Multi-Step Flow Support**: Soporta flujos multi-paso (swap, lending, buy)

4. **Flow Cancellation**: Detecta automáticamente cuando usuario cambia de tema

5. **Intent Detection V2**: Clasificación avanzada con contexto

6. **Routing Directo**: No usa orquestador, routing manual basado en intent

### Ejemplo de Flujo Completo

**Request**:
```http
POST /api/v1/conversations/550e8400-e29b-41d4-a716-446655440000/messages
Authorization: Bearer anvil_access_token
Content-Type: application/json

{
  "content": "Swap 1 ETH por USDC",
  "language": "es"
}
```

**Proceso**:
1. **User Resolution**: JWT token → Usuario autenticado (UUID: `123e4567-...`)
2. **Rate Limit**: Verifica 1000 mensajes/hora (✅ OK)
3. **Conversation**: Obtiene conversación y verifica ownership
4. **Context**: Obtiene últimos 10 mensajes para contexto
5. **Intent Detection**: 
   - Input: "Swap 1 ETH por USDC"
   - Output: `intent = SWAP`, `confidence = 0.95`
6. **Flow Cancellation Check**: No hay flow pendiente → Continúa
7. **Routing**: Route a `SwapHandlerV2`
8. **Handler Execution**:
   - SwapHandlerV2 detecta que es inicio de flow
   - Pregunta: "¿En qué chain quieres hacer el swap?"
   - Guarda estado: `pending_swap_info = {...}`
9. **Save Messages**: Guarda mensaje usuario y respuesta agente
10. **Response**: Retorna con `pending_action = "swap_chain_selection"`

**Response**:
```json
{
  "conversation_id": "550e8400-...",
  "message_id": "660e8400-...",
  "user_message": {
    "content": "Swap 1 ETH por USDC",
    "role": "user"
  },
  "agent_message": {
    "content": "💱 Swap 1 ETH → USDC\n\n¿En qué blockchain quieres hacer el swap?\n- Base\n- Ethereum\n- Arbitrum",
    "role": "assistant"
  },
  "routing": {
    "intent": "SWAP",
    "confidence": 0.95,
    "handler": "swap_handler_v2"
  },
  "enrichment": {
    "from_token": "ETH",
    "to_token": "USDC",
    "amount": "1"
  }
}
```

**Siguiente Mensaje** (Continuación del Flow):
```http
POST /api/v1/conversations/550e8400-.../messages

{
  "content": "Base"
}
```

**Proceso**:
1. **Context**: Detecta `pending_swap_info` en contexto
2. **Intent Detection**: Detecta `SWAP_CONTINUE` con metadata `{step: "chain", value: "Base"}`
3. **Handler**: SwapHandlerV2 continúa flow con chain seleccionada
4. **Next Step**: Pregunta por amount o confirma quote

---

## Flujo: Execute Action (`/api/v1/conversations/{id}/execute`)

### Propósito

Ejecuta transacciones DeFi recomendadas por el chat (swaps, deposits, withdrawals, etc.).

### Arquitectura del Flujo

```
┌─────────────────────────────────────────────────────────────┐
│              EXECUTE ACTION FLOW                            │
└─────────────────────────────────────────────────────────────┘

Usuario (Authenticated)
    │
    ▼
POST /api/v1/conversations/{conversation_id}/execute
    │
    ▼
┌─────────────────────────────┐
│   Execute Action Router     │  ← Presentation Layer
│   (FastAPI Controller)     │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│   ExecuteActionCommand      │  ← Application Layer
│   (Command Interactor)      │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│   Verify Conversation       │  ← Validation
│   (Ownership Check)         │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│   Get User Wallet            │  ← Infrastructure
│   (Privy Wallet Repository) │
└──────────────┬──────────────┘
               │
    ┌──────────┴──────────┐
    │                     │
    ▼                     ▼
Confirmed?           Not Confirmed?
    │                     │
    ▼                     ▼
┌──────────┐      ┌──────────────┐
│ Execute  │      │ Simulate     │
│ Transaction│    │ Transaction  │
└─────┬────┘      └──────┬───────┘
      │                   │
      └──────────┬────────┘
                 │
    ┌────────────┴────────────┐
    │                         │
    ▼                         ▼
┌──────────┐          ┌──────────────┐
│ Swap     │          │ Deposit/     │
│ (1inch)  │          │ Withdraw     │
│          │          │ (Morpho/Aave) │
└─────┬────┘          └──────┬───────┘
      │                       │
      └───────────┬───────────┘
                  │
                  ▼
      ┌───────────────────────┐
      │ Transaction Execution │  ← Infrastructure
      │ - Get Quote           │
      │ - Build Transaction   │
      │ - Sign (Privy)        │
      │ - Broadcast           │
      └───────────┬───────────┘
                  │
                  ▼
      ┌───────────────────────┐
      │ Save Transaction      │  ← Infrastructure
      │ (Transaction Repo)    │
      └───────────────────────┘
                  │
                  ▼
      ┌───────────────────────┐
      │ Return Result         │
      │ (Transaction Hash)    │
      └───────────────────────┘
```

### Características Clave

1. **Two-Step Confirmation**:
   - **Step 1**: `confirmed: false` → Simula transacción, retorna quote
   - **Step 2**: `confirmed: true` → Ejecuta transacción real

2. **Security Features**:
   - Transaction simulation (pre-flight)
   - Slippage protection
   - Transaction limits (max $50k swap, $100k deposit)
   - User confirmation required

3. **Supported Actions**:
   - Token swaps (1inch, LiFi, MoonPay)
   - Deposits (Morpho, Aave, Compound)
   - Withdrawals (Morpho, Aave, Compound)
   - Token transfers
   - Token approvals
   - Cross-chain bridges

### Ejemplo de Flujo Completo

**Step 1: Simulation** (Usuario ve quote y decide)
```http
POST /api/v1/conversations/550e8400-.../execute
Authorization: Bearer anvil_access_token
Content-Type: application/json

{
  "action_type": "swap",
  "chain": "base",
  "from_token": "ETH",
  "to_token": "USDC",
  "amount": "1",
  "slippage": 1.0,
  "confirmed": false
}
```

**Proceso**:
1. Verifica ownership de conversación
2. Obtiene wallet del usuario (Privy)
3. Obtiene quote de 1inch API
4. Simula transacción (pre-flight check)
5. Calcula gas fees
6. Retorna quote sin ejecutar

**Response**:
```json
{
  "action_id": "770e8400-...",
  "action_type": "swap",
  "status": "pending_confirmation",
  "requires_confirmation": true,
  "confirmation_message": "Swap 1 ETH → 3,250 USDC\nGas: ~$2.50\nSlippage: 1%",
  "simulation": {
    "from_amount": "1 ETH",
    "to_amount": "3,250 USDC",
    "exchange_rate": "1 ETH = 3,250 USDC",
    "gas_estimate": "0.001 ETH",
    "gas_cost_usd": "2.50",
    "slippage": "1%"
  },
  "transaction": null,
  "summary": "Ready to execute swap"
}
```

**Step 2: Execution** (Usuario confirma)
```http
POST /api/v1/conversations/550e8400-.../execute

{
  "action_type": "swap",
  "chain": "base",
  "from_token": "ETH",
  "to_token": "USDC",
  "amount": "1",
  "slippage": 1.0,
  "confirmed": true,
  "quote_id": "quote_12345"
}
```

**Proceso**:
1. Valida quote aún válido (no expirado)
2. Construye transacción usando 1inch API
3. Firma transacción con Privy (usuario confirma en frontend)
4. Broadcast transacción a blockchain
5. Espera confirmación (3-5 bloques)
6. Guarda transacción en base de datos
7. Retorna transaction hash

**Response**:
```json
{
  "action_id": "770e8400-...",
  "action_type": "swap",
  "status": "executed",
  "requires_confirmation": false,
  "transaction": {
    "hash": "0x1234567890abcdef...",
    "chain": "base",
    "from_token": "ETH",
    "to_token": "USDC",
    "from_amount": "1",
    "to_amount": "3,250",
    "gas_used": "150000",
    "gas_cost_usd": "2.50",
    "block_number": 12345678,
    "timestamp": "2026-01-15T10:30:00Z"
  },
  "summary": "Swap executed successfully"
}
```

---

## Comparación de Flujos

| Característica | Guest Chat | Conversations Messages | Execute Action |
|----------------|------------|------------------------|----------------|
| **Autenticación** | No requerida (IP-based) | Opcional (JWT/Privy/IP) | Requerida (JWT) |
| **Rate Limit** | 20/hr, 50/day | 800/hr (guest), 1000/hr (auth) | N/A |
| **Capacidades** | Demo mode, datos limitados | Completo, datos reales | Solo ejecución |
| **Multi-Step Flows** | ❌ No | ✅ Sí | N/A |
| **Agent Squad** | ✅ Sí (limitado) | ✅ Sí (completo) | N/A |
| **Real Transactions** | ❌ No | ❌ No | ✅ Sí |
| **Use Case** | Onboarding, demos | Chat completo | Ejecutar acciones |

---

## Stack Tecnológico

### Backend Framework
- **FastAPI**: Framework web moderno y rápido
- **Python 3.12**: Última versión de Python
- **Uvicorn**: Servidor ASGI de alto rendimiento

### Base de Datos
- **PostgreSQL**: Base de datos relacional principal
- **SQLAlchemy**: ORM para Python
- **Alembic**: Migraciones de base de datos

### Caché y Colas
- **Redis**: Caché y message broker
- **Celery**: Procesamiento de tareas en background

### AI/LLM
- **Vertex AI (Gemini)**: Proveedor principal ($0.10/1M tokens)
- **DeepInfra (Llama)**: Fallback ($0.08/1M tokens)
- **Perplexity AI**: Research agent

### Integraciones DeFi
- **1inch**: DEX aggregator para swaps
- **DeFiLlama**: Datos de protocolos y yields
- **Morpho**: Lending protocol
- **Aave**: Lending protocol
- **Privy**: Wallet management

### Arquitectura
- **Hexagonal Architecture**: Separación de capas
- **Dishka**: Dependency injection
- **CQRS**: Separación de commands y queries

---

## Métricas de Rendimiento

### Tiempos de Respuesta

| Operación | Tiempo Promedio | Tiempo Máximo |
|-----------|----------------|---------------|
| Intent Classification | 500ms | 1s |
| Single Agent Response | 2-3s | 5s |
| Multi-Agent Workflow | 45-60s | 120s |
| Transaction Simulation | 1-2s | 3s |
| Transaction Execution | 10-30s | 60s |

### Capacidad

- **Concurrent Users**: 2,000+ (puede escalar a 10,000 con optimizaciones)
- **Requests/Second**: ~500 RPS
- **Database Connections**: Pool de 20 conexiones
- **Redis Connections**: Pool de 10 conexiones

### Disponibilidad

- **Uptime Target**: 99.9%
- **Error Rate**: < 0.1%
- **Fallback Success Rate**: 95% (cuando primario falla)

---

## Seguridad

### Autenticación y Autorización

1. **JWT Tokens**: Tokens firmados para autenticación backend
2. **Privy Integration**: Wallet management seguro
3. **Rate Limiting**: Protección contra abuso
4. **Input Validation**: Validación estricta de todos los inputs

### Transacciones

1. **Transaction Simulation**: Pre-flight checks antes de ejecutar
2. **Slippage Protection**: Protección contra slippage excesivo
3. **Transaction Limits**: Límites máximos por tipo de transacción
4. **User Confirmation**: Requiere confirmación explícita del usuario

### Datos

1. **Encryption at Rest**: Datos sensibles encriptados
2. **Encryption in Transit**: HTTPS/TLS para todas las comunicaciones
3. **No Private Keys**: Nunca almacenamos private keys
4. **Wallet Isolation**: Cada usuario tiene su propio wallet

---

## Escalabilidad

### Horizontal Scaling

- **Stateless Design**: Servidores pueden escalar horizontalmente
- **Database Connection Pooling**: Manejo eficiente de conexiones
- **Redis for Caching**: Reduce carga en base de datos
- **Celery Workers**: Procesamiento asíncrono de tareas pesadas

### Optimizaciones Futuras

- **CDN**: Para assets estáticos
- **Database Read Replicas**: Para queries de solo lectura
- **Redis Cluster**: Para alta disponibilidad
- **Load Balancer**: Distribución de carga

---

## Conclusión

Anvil Backend es una plataforma robusta y escalable construida con:

1. **Arquitectura Hexagonal**: Separación clara de responsabilidades
2. **18 Agentes Especializados**: Sistema de orquestación inteligente
3. **Tres Flujos Principales**: Guest, Conversations, Execute
4. **99% de Ahorro en Costos**: Vertex AI + DeepInfra vs OpenAI
5. **Alta Disponibilidad**: 99.9% uptime con fallback automático

**Ventajas Competitivas**:
- ✅ Experiencia de usuario superior con routing automático
- ✅ Costos operativos bajos (99% vs competencia)
- ✅ Escalabilidad horizontal sin límites
- ✅ Arquitectura mantenible y extensible

---

**Documento Generado**: Enero 2026  
**Autor**: Sistema de Documentación Automática  
**Metodología**: CTO Engineering Framework  
**Fuentes**: 
- Código fuente: `src/app/`
- Documentación técnica: `docs/steering/`
- README: `README.md`
