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
