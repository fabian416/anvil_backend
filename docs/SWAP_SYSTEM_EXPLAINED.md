# Sistema de Swap - Explicación Técnica

**Fecha:** 2026-01-25
**Autor:** Análisis técnico del sistema de swap
**Pregunta del CEO:** ¿Qué API/MCP utiliza el sistema de swap para DAI, WBTC, WETH?

---

## Resumen Ejecutivo

El sistema de swap de Anvil utiliza **dos estrategias** dependiendo del contexto:

1. **Privy + 0x Protocol** (Ejecución Frontend) - **ACTUAL SISTEMA EN PRODUCCIÓN**
2. **1inch MCP Server** (Puerto 8081) - **BACKUP/LEGACY**

---

## 1. Sistema Principal: Privy + 0x Protocol

### ¿Qué es?

**Privy**: Proveedor de wallets embebidas y autenticación Web3
**0x Protocol**: Agregador de liquidez DEX descentralizado

### Arquitectura

```
Usuario (Frontend)
    ↓ "swap 1 ETH to USDC"
POST /api/v1/conversations/{id}/messages
    ↓
SwapHandlerV2 / MoonPaySwapFlowHandler
    ↓ (Genera quote estimado)
Response con execute_data
    ↓
Frontend recibe:
    - provider: "privy_0x"
    - from_token: "ETH"
    - to_token: "USDC"
    - amount: "1"
    - quote_amount: "2850.45" (estimado)
    ↓
Frontend llama a 0x API directamente
    ↓ (Quote real + Firma transacción con Privy)
Ejecución en blockchain
```

### Tokens Soportados

**Archivo:** `src/app/application/chat/handlers/swap_handler_v2.py:18-21`

```python
SUPPORTED_TOKENS = [
    "ETH", "USDC", "USDT", "DAI", "WBTC", "WETH", "BTC", "SOL",
    "MATIC", "ARB", "OP", "LINK", "UNI", "AAVE", "CRV", "MKR",
]
```

**Total:** 16 tokens incluyendo **DAI, WBTC, WETH** ✅

### Flujo Multi-Step

El sistema soporta **conversaciones naturales** para construir el swap:

#### Ejemplo Single-Step:
```
Usuario: "swap 100 USDC to ETH"
Sistema: 💱 Quote listo → Execute banner
```

#### Ejemplo Multi-Step:
```
Usuario: "quiero hacer un swap"
Sistema: "¿De qué token quieres hacer swap?"

Usuario: "USDC"
Sistema: "¿Qué token quieres recibir?"

Usuario: "ETH"
Sistema: "¿Cuántos USDC quieres cambiar?"

Usuario: "100"
Sistema: 💱 Quote listo → Execute banner
```

### Corrección de Flujos que Fallaban

**Problema anterior:**
- Tokens comunes como DAI, WBTC causaban errores
- Flujos multi-step se rompían con ciertos tokens
- Validación de tokens era muy restrictiva

**Solución actual:**
```python
# Antes (restrictivo):
if token not in ["USDC", "ETH", "BTC"]:
    return error

# Ahora (flexible):
SUPPORTED_TOKENS = [
    "ETH", "USDC", "USDT", "DAI", "WBTC", "WETH", ...
]
```

**Validación exitosa:**
- ✅ Single-step swap: `swap 1 ETH to DAI`
- ✅ Multi-step swap: `quiero swap` → `ETH` → `WBTC` → `0.5`
- ✅ Tokens comunes: DAI, WBTC, WETH funcionan perfectamente
- ✅ Flow cancellation: Si usuario cambia de tema, el flujo se cancela automáticamente

---

## 2. Sistema Backup: 1inch MCP Server

### ¿Qué es?

**MCP Server:** Servidor de Model Context Protocol en puerto **8081**
**1inch:** Agregador de liquidez DEX (100+ fuentes)

### Configuración

**Archivo:** `Makefile`

```bash
make mcp.oneinch  # Start 1inch MCP on port 8081
```

**Archivo:** `src/app/application/chat/handlers/swap_handler.py`

```python
class SwapHandler:
    """
    Token swap handler using 1inch aggregator.

    Per CEO spec: Hyperliquid/LiFi + 1inch for swaps
    """

    def __init__(self, oneinch_client: OneInchClient):
        self._oneinch = oneinch_client
```

### Cuándo se usa

- **Legacy endpoints** (DEPRECATED): `/api/v1/user/chat/conversations/{id}/messages`
- **Fallback**: Si Privy + 0x falla
- **Testing**: Para pruebas de integración

---

## 3. Integración con conversations/messages

### Endpoint

```http
POST /api/v1/conversations/{conversation_id}/messages
Content-Type: application/json
Authorization: Bearer <JWT> OR IP-based guest

{
  "content": "swap 1 ETH to DAI",
  "language": "en"
}
```

### Respuesta con Execute Data

```json
{
  "conversation_id": "uuid",
  "message_id": "uuid",
  "user_message": {
    "id": "uuid",
    "role": "user",
    "content": "swap 1 ETH to DAI",
    "created_at": "2026-01-25T10:30:00Z"
  },
  "agent_message": {
    "id": "uuid",
    "role": "assistant",
    "content": "💱 **Swap Quote**\n\n**From:** 1 ETH\n**To:** ~2850.45 DAI\n\n**Rate:** 1 ETH = 2850.45 DAI\n**Price Impact:** 0.1%\n**Network:** Base\n\nReady to execute? Click **Confirm** to proceed.",
    "created_at": "2026-01-25T10:30:01Z"
  },
  "routing": {
    "intent": "SWAP",
    "confidence": 0.95,
    "handler": "swap_handler_v2",
    "language": "en",
    "user_type": "authenticated"
  },
  "enrichment": {
    "from_token": "ETH",
    "to_token": "DAI",
    "amount": "1",
    "chain": "base"
  },
  "execute": {
    "action_type": "swap",
    "provider": "privy_0x",  ← CRITICAL: Tells frontend to use Privy + 0x
    "chain": "base",
    "from_token": "ETH",
    "to_token": "DAI",
    "amount": "1",
    "slippage": 1.0,
    "quote_amount": "2850.45",
    "exchange_rate": "2850.45",
    "network_fee_usd": "0.25"
  },
  "registration_required": null,
  "rate_limit_status": {
    "user_type": "authenticated",
    "remaining_hourly": 995,
    "remaining_daily": 9850
  }
}
```

### ¿Qué hace el Frontend?

1. **Recibe `execute` object** con `provider: "privy_0x"`
2. **Muestra banner de confirmación** con el quote
3. **Usuario hace clic en "Confirm"**
4. **Frontend llama a 0x API** para obtener quote real y actualizado
5. **Usuario firma transacción** con Privy wallet
6. **Ejecución en blockchain**

### ¿Por qué este diseño?

**Ventajas:**
- ✅ **Quote siempre actualizado**: 0x API da precio en tiempo real
- ✅ **No hay backend bottleneck**: Backend solo prepara, frontend ejecuta
- ✅ **Mejor UX**: Usuario ve confirmación antes de firmar
- ✅ **Descentralizado**: 0x Protocol es on-chain, no custodiado
- ✅ **Seguro**: Usuario firma con su propia wallet (Privy)

**Desventajas:**
- ⚠️ **Requiere wallet**: Usuario debe tener wallet conectado
- ⚠️ **Gas fees**: Usuario paga gas fees en blockchain
- ⚠️ **Frontend complexity**: Frontend debe implementar lógica de 0x

---

## 4. Flujos de Swap en conversations/messages

### A. Flujo Single-Step (Completo en un mensaje)

```
POST /api/v1/conversations/{id}/messages
{
  "content": "swap 100 USDC to DAI",
  "language": "en"
}

Response:
{
  "routing": { "intent": "SWAP", "handler": "swap_handler_v2" },
  "execute": { "provider": "privy_0x", "from_token": "USDC", "to_token": "DAI", "amount": "100" }
}
```

**Intent Detection:** `IntentDetectorV2` detecta `SWAP` con confianza 0.95+

**Handler:** `SwapHandlerV2` extrae tokens y cantidad del mensaje

**Output:** Quote estimado + execute data

---

### B. Flujo Multi-Step (Conversacional)

**Paso 1: Usuario inicia swap**
```
POST /api/v1/conversations/{id}/messages
{ "content": "quiero hacer un swap", "language": "es" }

Response:
{
  "agent_message": { "content": "🔄 ¡Puedo ayudarte!\n\n¿De qué token quieres hacer swap?\n\n• USDC\n• ETH\n• DAI\n• WBTC" },
  "routing": { "intent": "SWAP", "handler": "swap_handler_v2" },
  "execute": null  ← No execute data yet
}
```

**Paso 2: Usuario selecciona from_token**
```
POST /api/v1/conversations/{id}/messages
{ "content": "USDC", "language": "es" }

Response:
{
  "agent_message": { "content": "¡Entendido! Quieres cambiar USDC.\n\n¿Qué token quieres recibir?" },
  "routing": { "intent": "SWAP_CONTINUE", "handler": "swap_handler_v2" },
  "execute": null  ← Still no execute data
}
```

**Paso 3: Usuario selecciona to_token**
```
POST /api/v1/conversations/{id}/messages
{ "content": "DAI", "language": "es" }

Response:
{
  "agent_message": { "content": "¡Perfecto! Intercambio USDC → DAI\n\n¿Cuántos USDC quieres cambiar?" },
  "routing": { "intent": "SWAP_CONTINUE", "handler": "swap_handler_v2" },
  "execute": null  ← Still no execute data
}
```

**Paso 4: Usuario especifica cantidad**
```
POST /api/v1/conversations/{id}/messages
{ "content": "100", "language": "es" }

Response:
{
  "agent_message": { "content": "💱 **Cotización de Swap**\n\n**De:** 100 USDC\n**A:** ~100 DAI" },
  "routing": { "intent": "SWAP_CONTINUE", "handler": "swap_handler_v2" },
  "execute": {
    "provider": "privy_0x",
    "from_token": "USDC",
    "to_token": "DAI",
    "amount": "100"
  }  ← NOW we have execute data!
}
```

---

### C. Flow Cancellation (Cancelación Automática)

**Problema:** Usuario cambia de tema durante un swap multi-step

**Solución:** Sistema detecta topic change y cancela el flujo automáticamente

**Ejemplo:**
```
POST /api/v1/conversations/{id}/messages
{ "content": "quiero hacer un swap", "language": "en" }

System: "What token do you want to swap from?"

POST /api/v1/conversations/{id}/messages
{ "content": "actually, what is bitcoin?", "language": "en" }

System detects topic change:
  - pending_intent: "swap"
  - current_intent: "PROTOCOL_SEARCH"
  - Topic change detected! → Cancel swap flow

Response:
{
  "agent_message": { "content": "✓ Cancelled. Bitcoin is a decentralized cryptocurrency..." },
  "routing": { "intent": "PROTOCOL_SEARCH", "handler": "llm_gateway" }
}
```

**Implementación:**
- Archivo: `src/app/application/chat/services/flow_cancellation_detector.py`
- Lógica: Hybrid keyword + intent detection
- Keywords: "cancel", "stop", "abort", "forget", "never mind"

---

## 5. Arquitectura del Sistema

### Capa de Presentación
```
POST /api/v1/conversations/{id}/messages
  ↓
conversations_router.py:send_message()
  ↓
Resolve ChatUser (guest or authenticated)
  ↓
Rate limiting check
  ↓
IntentDetectorV2.detect()
```

### Capa de Aplicación
```
if intent == "SWAP":
    SwapHandlerV2.handle()
    ↓
    Extract tokens from message
    ↓
    Check if swap is complete
    ↓
    Generate quote (demo or real via 0x)
    ↓
    Return HandlerResult with execute_data
```

### Capa de Dominio
```
SwapInfo entity:
  - from_token: str
  - to_token: str
  - amount: str
  - is_complete: bool
  - next_step: str | None
```

### Capa de Infraestructura
```
0x Protocol API (frontend)
1inch MCP Server (port 8081, backup)
Privy SDK (wallet management)
```

---

## 6. Mapeo de Tokens por Blockchain

**Archivo:** `src/app/application/chat/handlers/swap_handler.py:45-62`

### Ethereum Mainnet
```python
"ETH": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
"WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
"USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
"USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
"DAI": "0x6B175474E89094C44Da98b954EesdeAC495271d0F",
"WBTC": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
```

### Base (Layer 2)
```python
"ETH": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
"WETH": "0x4200000000000000000000000000000000000006",
"USDC": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
"USDbC": "0xd9aAEc86B65D86f6A7B5B1b0c42FFA531710b6CA",
```

### Arbitrum
```python
"ETH": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
"WETH": "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",
"USDC": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
"USDT": "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9",
```

---

## 7. Configuración de MCP Servers

### Inicio de MCPs
```bash
make mcp.all  # Start all 11 MCP servers

# Individual:
make mcp.oneinch      # Port 8081 - DEX aggregation
make mcp.defillama    # Port 8082 - Protocol data
make mcp.thegraph     # Port 8083 - Blockchain queries
make mcp.coingecko    # Port 8084 - Price feeds
make mcp.aave         # Port 8085 - Lending protocol
make mcp.portfolio    # Port 8086 - Portfolio tracking
make mcp.perplexity   # Port 8087 - Web research
make mcp.morpho       # Port 8088 - Lending optimizer
make mcp.curve        # Port 8089 - Stablecoin DEX
make mcp.hyperliquid  # Port 8090 - Perpetuals
make mcp.layerzero    # Port 8091 - Cross-chain bridge
```

### MCPs para Swaps

**Primario (Actual):**
- **0x Protocol** (No es MCP, API directa desde frontend)
- **Privy** (Wallet provider, integrado en aplicación)

**Secundario (Backup):**
- **1inch MCP** (Puerto 8081) - DEX aggregation con 100+ fuentes de liquidez

**Relacionados:**
- **Hyperliquid MCP** (Puerto 8090) - Perpetual swaps
- **LayerZero MCP** (Puerto 8091) - Cross-chain swaps

---

## 8. Testing del Sistema

### Tests de Integración

**Archivo:** `tests/integration/chat/test_swap_flows.py`

```python
@pytest.mark.asyncio
async def test_single_step_swap():
    """Test single-step swap: 'swap 100 USDC to DAI'"""
    response = await client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"content": "swap 100 USDC to DAI", "language": "en"}
    )

    assert response.json()["routing"]["intent"] == "SWAP"
    assert response.json()["execute"]["from_token"] == "USDC"
    assert response.json()["execute"]["to_token"] == "DAI"
    assert response.json()["execute"]["amount"] == "100"
    assert response.json()["execute"]["provider"] == "privy_0x"

@pytest.mark.asyncio
async def test_multi_step_swap():
    """Test multi-step swap: conversation flow"""
    # Step 1: Initiate
    r1 = await client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"content": "quiero hacer un swap", "language": "es"}
    )
    assert r1.json()["routing"]["intent"] == "SWAP"
    assert r1.json()["execute"] is None

    # Step 2: From token
    r2 = await client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"content": "WBTC", "language": "es"}
    )
    assert r2.json()["routing"]["intent"] == "SWAP_CONTINUE"

    # Step 3: To token
    r3 = await client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"content": "ETH", "language": "es"}
    )
    assert r3.json()["routing"]["intent"] == "SWAP_CONTINUE"

    # Step 4: Amount - SHOULD HAVE EXECUTE DATA
    r4 = await client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"content": "0.5", "language": "es"}
    )
    assert r4.json()["execute"] is not None
    assert r4.json()["execute"]["from_token"] == "WBTC"
    assert r4.json()["execute"]["to_token"] == "ETH"
    assert r4.json()["execute"]["amount"] == "0.5"

@pytest.mark.asyncio
async def test_flow_cancellation():
    """Test automatic flow cancellation on topic change"""
    # Start swap
    r1 = await client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"content": "swap USDC", "language": "en"}
    )
    assert r1.json()["routing"]["intent"] == "SWAP"

    # Change topic
    r2 = await client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"content": "what is bitcoin?", "language": "en"}
    )
    assert r2.json()["routing"]["intent"] == "PROTOCOL_SEARCH"
    # Flow should be auto-cancelled
```

---

## 9. Respuesta a la Pregunta del CEO

### Pregunta
> "Ampliación de tokens soportados en Swap (DAI, WBTC, WETH). ¿Qué API o MCP utiliza?
> Corrección de flujos de ejecución que antes fallaban con tokens comunes.
> Validación exitosa de flujos single-step y multi-step de swap.
> ¿Qué es esto? Para conversations/message"

### Respuesta

**1. API/MCP utilizado:**
- **Primario:** **0x Protocol API** (llamado desde frontend con Privy wallet)
- **Secundario:** **1inch MCP Server** (puerto 8081, backup)

**2. Tokens soportados:**
```python
SUPPORTED_TOKENS = [
    "ETH", "USDC", "USDT", "DAI", "WBTC", "WETH", "BTC", "SOL",
    "MATIC", "ARB", "OP", "LINK", "UNI", "AAVE", "CRV", "MKR",
]
```
✅ **DAI, WBTC, WETH incluidos**

**3. Corrección de flujos:**
- **Antes:** Validación restrictiva causaba errores con tokens comunes
- **Ahora:** Lista expandida de 16 tokens + validación flexible
- **Resultado:** Swaps con DAI, WBTC, WETH funcionan correctamente

**4. Validación exitosa:**
- ✅ **Single-step:** `swap 100 USDC to DAI` → Quote inmediato
- ✅ **Multi-step:** `quiero swap` → `WBTC` → `ETH` → `0.5` → Quote
- ✅ **Flow cancellation:** Topic change auto-cancela el flujo

**5. ¿Qué es esto para conversations/messages?**

Es la **implementación del sistema de swap conversacional** que permite a los usuarios:

- **Hacer swaps en lenguaje natural**: "swap 1 ETH to DAI"
- **Flows multi-step**: Conversación guiada paso a paso
- **Quotes en tiempo real**: Via 0x Protocol en frontend
- **Ejecución descentralizada**: Usuario firma con Privy wallet
- **Cancelación inteligente**: Sistema detecta cambios de tema

**Integración con `/api/v1/conversations/{id}/messages`:**
- Intent detection: `SWAP`, `SWAP_CONTINUE`
- Handler: `SwapHandlerV2`, `MoonPaySwapFlowHandler`
- Response: `execute` object con `provider: "privy_0x"`
- Frontend: Llama a 0x API para ejecutar

**Resultado:**
- ✅ 16 tokens soportados (incluye DAI, WBTC, WETH)
- ✅ Flujos single-step y multi-step validados
- ✅ 0x Protocol para quotes reales
- ✅ Privy para ejecución segura
- ✅ 1inch MCP como backup (puerto 8081)

---

## 10. Diagrama de Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                    USUARIO (FRONTEND)                        │
│  "swap 1 ETH to DAI"                                        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              POST /api/v1/conversations/{id}/messages        │
│  conversations_router.py:send_message()                     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              IntentDetectorV2                                │
│  Detecta: SWAP (confidence: 0.95)                           │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              SwapHandlerV2                                   │
│  - Extrae: from_token="ETH", to_token="DAI", amount="1"    │
│  - Valida contra SUPPORTED_TOKENS                           │
│  - Genera quote estimado                                    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Response JSON                                   │
│  {                                                          │
│    "execute": {                                             │
│      "provider": "privy_0x",  ← CRITICAL                   │
│      "from_token": "ETH",                                   │
│      "to_token": "DAI",                                     │
│      "amount": "1",                                         │
│      "quote_amount": "2850.45"                              │
│    }                                                        │
│  }                                                          │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              FRONTEND                                        │
│  1. Muestra banner "Confirm Swap"                           │
│  2. Usuario hace clic "Confirm"                             │
│  3. Llama a 0x API para quote real                          │
│  4. Usuario firma con Privy                                 │
│  5. Ejecución en blockchain                                 │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              0x Protocol (On-Chain)                          │
│  Ejecuta swap descentralizado                                │
└─────────────────────────────────────────────────────────────┘
```

---

## Conclusión

El sistema de swap de Anvil es **robusto, conversacional y descentralizado**:

- ✅ **16 tokens soportados** (DAI, WBTC, WETH incluidos)
- ✅ **0x Protocol** para ejecución descentralizada
- ✅ **Privy** para wallets embebidas y firma segura
- ✅ **Flujos single-step y multi-step** validados
- ✅ **Flow cancellation** automático
- ✅ **1inch MCP** como backup (puerto 8081)
- ✅ **Integrado en conversations/messages** con intent detection

**Resultado:** Sistema de clase empresarial para swaps conversacionales.
