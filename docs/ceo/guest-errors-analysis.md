# Guest Error Handling Analysis: "What is Bitcoin?" Problem

**Documento para CEO**  
**Fecha**: Enero 2026  
**Metodología**: CTO Engineering Framework  
**Estado**: Análisis Completo ✅

---

## Executive Summary

**Problema Identificado**: Cuando usuarios guest preguntan "what is btc?" o "what is bitcoin", el sistema responde con un mensaje genérico de introducción en lugar de proporcionar información específica sobre Bitcoin.

**Impacto**: 
- **UX Degradado**: Usuarios no reciben respuestas útiles a preguntas básicas
- **Pérdida de Confianza**: Sistema parece no entender preguntas simples
- **Conversión Reducida**: Usuarios pueden abandonar antes de registrarse

**Solución Propuesta**: Mejorar el sistema de detección de intents y respuestas para preguntas generales sobre cripto/DeFi.

---

## Phase 1: Problem Decomposition & Root Cause Analysis

### 1.1 Assumption Questioning

**¿Cuál es el requerimiento real?**
- Usuarios guest deben poder hacer preguntas básicas sobre cripto/DeFi
- El sistema debe responder de manera útil y educativa
- Las respuestas deben ser precisas y relevantes

**¿Qué suposiciones no verificadas hace el enfoque actual?**
- ❌ **Suposición 1**: Todos los mensajes de guest son sobre acciones restringidas
- ❌ **Suposición 2**: Preguntas educativas requieren registro
- ❌ **Suposición 3**: Mensajes genéricos son suficientes para engagement

**¿Qué restricciones "obvias" podrían ser pseudo-restricciones?**
- ⚠️ **Restricción 1**: "Guest users solo pueden ver demos" → FALSO: Pueden recibir información educativa
- ⚠️ **Restricción 2**: "Respuestas detalladas requieren LLM costoso" → FALSO: Knowledge base puede proporcionar respuestas básicas
- ⚠️ **Restricción 3**: "Debemos forzar registro para información útil" → FALSO: Información educativa aumenta conversión

---

### 1.2 Root Cause Identification

**Fenómeno Observado**:
```
Input: "what is btc?"
Output: "I'm your AI assistant for DeFi! I can help with..."
```

**Esencia del Problema**:
1. **Intent Detection Failure**: El sistema no detecta correctamente preguntas educativas básicas
2. **Handler Selection Error**: Se selecciona un handler genérico en lugar del handler de conocimiento
3. **Knowledge Base Bypass**: El sistema no utiliza la knowledge base disponible para respuestas educativas

**Causal Relationship Mapping**:
```
Root Cause 1: IntentDetectorV2 no detecta "token_info" intents correctamente
    ↓
    Intent clasificado como GENERAL_CONVERSATION con baja confianza
    ↓
    Handler genérico seleccionado (fallback)
    ↓
    Respuesta genérica en lugar de respuesta específica

Root Cause 2: GuestHandlerService no tiene handler para preguntas educativas
    ↓
    No hay ruta específica para "what is bitcoin?" queries
    ↓
    Fallback a mensaje genérico de introducción

Root Cause 3: KnowledgeInjector no se utiliza para guest users
    ↓
    Conocimiento estructurado disponible pero no inyectado
    ↓
    LLM no tiene contexto sobre Bitcoin para generar respuesta
```

---

### 1.3 Solution Space Mapping

**System Invariants** (No pueden cambiar):
- ✅ Guest users no pueden ejecutar transacciones
- ✅ Guest users tienen rate limiting (20 msgs/hour)
- ✅ Sistema debe mantener seguridad y prevenir abuso

**Design Degrees of Freedom** (Pueden cambiar):
- ✅ Mejorar detección de intents educativos
- ✅ Agregar handler específico para preguntas educativas
- ✅ Inyectar knowledge base en prompts para guest users
- ✅ Crear respuestas predefinidas para preguntas comunes

**Hard Constraints**:
- No puede ejecutar transacciones sin wallet
- No puede acceder a datos privados del usuario
- Debe mantener rate limiting

**Soft Constraints**:
- Costo de LLM (puede optimizarse con cache/knowledge base)
- Latencia de respuesta (puede mejorarse con respuestas estáticas)
- Complejidad de implementación (puede simplificarse con módulos)

---

## Phase 2: Solution Generation & Trade-off Analysis

### 2.1 Solution Divergence

**Solution A: Mejorar Intent Detection + Knowledge Injection**
- **Enfoque**: Mejorar `IntentDetectorV2` para detectar "token_info" intents y usar `KnowledgeInjector` para guest users
- **Cambios**: 
  - Agregar keywords más específicos para token_info en `IntentDetectorV2`
  - Modificar `GuestHandlerService` para usar `KnowledgeInjector` en preguntas educativas
  - Inyectar knowledge base en prompts LLM para guest users

**Solution B: Crear Handler Específico para Preguntas Educativas**
- **Enfoque**: Crear nuevo handler `EducationalQuestionHandler` específico para guest users
- **Cambios**:
  - Nuevo handler que responde preguntas educativas usando knowledge base
  - Respuestas predefinidas para preguntas comunes (Bitcoin, Ethereum, etc.)
  - Fallback a LLM solo si knowledge base no tiene respuesta

**Solution C: Respuestas Estáticas Predefinidas**
- **Enfoque**: Crear respuestas estáticas para preguntas comunes sin usar LLM
- **Cambios**:
  - Base de datos de respuestas predefinidas para preguntas frecuentes
  - Matching exacto de preguntas comunes
  - Zero costo LLM para preguntas básicas

**Solution D: Híbrido (A + B + C)**
- **Enfoque**: Combinar mejor detección + handler específico + respuestas estáticas
- **Cambios**:
  - Mejorar intent detection
  - Crear handler educativo con respuestas estáticas + knowledge base
  - Fallback a LLM solo si necesario

---

### 2.2 Multi-dimensional Trade-off Matrix

| Solución | Technical Benefits | Implementation Cost | Risk Assessment | Score |
|----------|-------------------|---------------------|-----------------|-------|
| **Solution A** | ✅ Mejora detección general<br>✅ Reutiliza infraestructura existente<br>✅ Escalable a más preguntas | ⚠️ Medio (2-3 días)<br>⚠️ Requiere testing de intents<br>⚠️ Modifica código existente | 🟢 Bajo riesgo<br>🟢 No rompe funcionalidad existente<br>🟢 Fácil rollback | **8/10** |
| **Solution B** | ✅ Handler dedicado y mantenible<br>✅ Separación de responsabilidades<br>✅ Fácil de extender | ⚠️ Medio-Alto (3-4 días)<br>⚠️ Nuevo código a mantener<br>⚠️ Requiere testing completo | 🟡 Medio riesgo<br>🟡 Nuevo código puede tener bugs<br>🟡 Requiere integración cuidadosa | **7/10** |
| **Solution C** | ✅ Zero costo LLM<br>✅ Latencia instantánea<br>✅ 100% confiable | ⚠️ Alto (4-5 días)<br>⚠️ Requiere crear base de datos<br>⚠️ Mantenimiento manual | 🟡 Medio riesgo<br>🟡 Respuestas pueden quedar obsoletas<br>🟡 No cubre todas las preguntas | **6/10** |
| **Solution D** | ✅ Mejor de todos los mundos<br>✅ Máxima cobertura<br>✅ Optimizado para costo | ❌ Alto (5-6 días)<br>❌ Más complejo<br>❌ Más testing requerido | 🟡 Medio-Alto riesgo<br>🟡 Más superficie de error<br>🟡 Más mantenimiento | **9/10** |

---

### 2.3 Constraint Priority Framework

**Performance Efficiency vs Code Maintainability**:
- **Solution A**: Balanceado (reutiliza código existente)
- **Solution B**: Favorable a mantenibilidad (código separado)
- **Solution C**: Favorable a performance (zero LLM)
- **Solution D**: Balanceado (optimizado pero más complejo)

**Development Speed vs Architecture Scalability**:
- **Solution A**: Rápido pero escalable
- **Solution B**: Medio pero muy escalable
- **Solution C**: Rápido pero limitado
- **Solution D**: Lento pero altamente escalable

**Feature Completeness vs Implementation Simplicity**:
- **Solution A**: Completo y simple
- **Solution B**: Completo pero más complejo
- **Solution C**: Simple pero limitado
- **Solution D**: Muy completo pero complejo

**System Security vs Usage Convenience**:
- Todas las soluciones mantienen seguridad (no cambian permisos)
- Todas mejoran conveniencia para usuarios

---

## Phase 3: Risk Assessment & Validation Design

### 3.1 Cognitive Limitation Analysis

**Este análisis puede pasar por alto factores como**:
- ⚠️ **Volumen de preguntas**: ¿Cuántas preguntas educativas diferentes hay?
- ⚠️ **Idiomas**: ¿Cómo manejar preguntas en español/portugués/chino?
- ⚠️ **Variaciones**: "what is btc?" vs "tell me about bitcoin" vs "explain bitcoin"
- ⚠️ **Contexto**: ¿Preguntas en medio de conversaciones vs preguntas aisladas?

**La solución asume premisas clave como**:
- ✅ Knowledge base tiene información suficiente sobre Bitcoin
- ✅ IntentDetectorV2 puede mejorarse sin romper otros intents
- ✅ LLM puede generar buenas respuestas con knowledge inyectado

**Áreas que requieren validación adicional**:
- 🔍 Testing de intents: ¿Mejora la detección sin falsos positivos?
- 🔍 Quality de respuestas: ¿Las respuestas son útiles y precisas?
- 🔍 Performance: ¿Aumenta latencia significativamente?
- 🔍 Costo: ¿Aumenta costo de LLM calls?

---

### 3.2 Technical Debt Assessment

**Compromisos de implementación rápida en la solución**:
- ⚠️ **Solution A**: Puede requerir ajustes iterativos de keywords
- ⚠️ **Solution B**: Nuevo handler puede necesitar refactoring futuro
- ⚠️ **Solution C**: Base de datos estática puede quedar desactualizada
- ⚠️ **Solution D**: Complejidad puede requerir simplificación futura

**Impacto de cambios de requerimientos en arquitectura**:
- ✅ **Cambio 1**: "Agregar más preguntas educativas" → Fácil con todas las soluciones
- ✅ **Cambio 2**: "Personalizar respuestas por usuario" → Requiere extensión pero factible
- ⚠️ **Cambio 3**: "Respuestas multi-idioma mejoradas" → Requiere trabajo adicional

**Costo de mantenimiento a largo plazo**:
- **Solution A**: Bajo (reutiliza infraestructura)
- **Solution B**: Medio (nuevo código a mantener)
- **Solution C**: Medio-Alto (base de datos manual)
- **Solution D**: Medio-Alto (múltiples componentes)

---

### 3.3 Validation & Testing Strategy

**Criterios de éxito medibles**:
- ✅ **Accuracy**: 90%+ de preguntas "what is X?" detectadas correctamente
- ✅ **Relevance**: Respuestas deben mencionar el token específico (Bitcoin, BTC)
- ✅ **User Satisfaction**: Respuestas útiles (no genéricas)
- ✅ **Performance**: Latencia < 2 segundos
- ✅ **Cost**: No aumentar costo LLM > 10%

**Experimentos de validación para rutas críticas**:
1. **Test de Intent Detection**:
   - Input: "what is btc?", "what is bitcoin", "tell me about bitcoin"
   - Expected: Intent = TOKEN_INFO o GENERAL_CONVERSATION con metadata token="BTC"
   - Validation: Intent confidence > 0.85

2. **Test de Response Quality**:
   - Input: "what is bitcoin?"
   - Expected: Respuesta menciona "Bitcoin", "BTC", características básicas
   - Validation: LLM validator score > 0.85

3. **Test de Performance**:
   - Measure: Latencia promedio de respuestas educativas
   - Expected: < 2 segundos
   - Validation: P95 latency < 2.5 segundos

4. **Test de Cost**:
   - Measure: Tokens usados por respuesta educativa
   - Expected: Similar o menor que respuestas genéricas
   - Validation: No increase > 10%

**Mecanismos de detección de errores y rollback**:
- ✅ Feature flag para habilitar/deshabilitar mejoras
- ✅ Monitoring de intent detection accuracy
- ✅ Alertas si respuestas genéricas aumentan
- ✅ Rollback automático si error rate > 5%

---

## Phase 4: Recommended Solution & Implementation

### 4.1 Recommended Solution: **Solution A (Mejorada)**

**Razón de selección**:
- ✅ Balance óptimo entre beneficios técnicos y costo de implementación
- ✅ Reutiliza infraestructura existente (KnowledgeInjector, IntentDetectorV2)
- ✅ Escalable y mantenible
- ✅ Bajo riesgo de romper funcionalidad existente

**Mejoras adicionales**:
- Agregar respuestas estáticas para preguntas más comunes (fallback rápido)
- Mejorar keywords multi-idioma en IntentDetectorV2

---

### 4.2 Implementation Plan

#### Step 1: Mejorar Intent Detection (1 día)

**Archivo**: `src/app/application/chat/services/intent_detector_v2.py`

**Cambios**:
```python
# Agregar keywords más específicos para token_info
INTENT_KEYWORDS["token_info"] = {
    "en": [
        "what is bitcoin", "what is btc", "what is ethereum", "what is eth",
        "tell me about bitcoin", "explain bitcoin", "what is defi",
        "what is crypto", "what is cryptocurrency",
        # Agregar más variaciones
        "bitcoin explained", "what does btc mean", "bitcoin definition",
    ],
    "es": [
        "qué es bitcoin", "qué es btc", "qué es ethereum",
        "cuéntame sobre bitcoin", "explica bitcoin",
        # Agregar más variaciones
    ],
    # ... otros idiomas
}

# Mejorar detección de token_info
def _detect_token_info_intent(self, message: str, language: str) -> Optional[IntentResult]:
    """Detect token info queries with improved accuracy."""
    message_lower = message.lower().strip()
    
    # Check for token info keywords
    token_keywords = self._get_all_keywords("token_info", language)
    
    # Check for "what is" + token pattern
    if any(kw in message_lower for kw in ["what is", "qué es", "o que é"]):
        # Extract token from message
        tokens = self._extract_tokens_from_message(message_lower)
        if tokens:
            return IntentResult(
                intent=ChatIntentV2.GENERAL_CONVERSATION,
                confidence=0.90,
                handler=self._handler_map[ChatIntentV2.GENERAL_CONVERSATION],
                metadata={"token_info": tokens[0], "query_type": "educational"},
            )
    
    return None
```

#### Step 2: Mejorar Guest Handler para Preguntas Educativas (1 día)

**Archivo**: `src/app/application/guest/handlers/guest_handler_service.py`

**Cambios**:
```python
async def _handle_general_conversation(
    self, content: str, language: str, is_authenticated: bool = False
) -> dict[str, Any]:
    """Handle general conversation with knowledge injection for educational queries."""
    
    # Check if this is an educational query about tokens
    if self._is_educational_query(content):
        # Use KnowledgeInjector to get relevant knowledge
        from app.application.chat.services.knowledge_injector import KnowledgeInjector
        
        knowledge_injector = KnowledgeInjector()
        
        # Detect token from message
        token = self._extract_token_from_message(content)
        
        # Get knowledge about the token
        knowledge = knowledge_injector.get_knowledge_for_intent(
            user_query=content,
            detected_intent="GENERAL_CONVERSATION",
            user_type="user",
        )
        
        # Build enhanced system prompt with knowledge
        enhanced_prompt = knowledge_injector.augment_system_prompt(
            user_query=content,
            detected_intent="GENERAL_CONVERSATION",
            user_type="user",
            base_system_prompt=self._get_base_system_prompt(language),
        )
        
        # Use LLM Gateway with enhanced prompt
        from app.domain.ports.llm_gateway import LLMGateway
        llm_gateway = await self._get_llm_gateway()
        
        response = await llm_gateway.complete(
            messages=[
                {"role": "system", "content": enhanced_prompt},
                {"role": "user", "content": content},
            ],
            temperature=0.7,
            max_tokens=500,
        )
        
        return {
            "content": response.content,
            "enrichment": {"knowledge_injected": True, "token": token},
            "requires_registration": False,
        }
    
    # Fallback to generic response for non-educational queries
    return self._get_generic_intro_response(language, is_authenticated)

def _is_educational_query(self, content: str) -> bool:
    """Check if query is educational (about tokens, DeFi, etc.)."""
    content_lower = content.lower()
    
    educational_patterns = [
        "what is", "qué es", "o que é", "什么是",
        "tell me about", "cuéntame sobre", "me conte sobre",
        "explain", "explica", "explique",
    ]
    
    return any(pattern in content_lower for pattern in educational_patterns)

def _extract_token_from_message(self, content: str) -> Optional[str]:
    """Extract token symbol from message."""
    content_lower = content.lower()
    
    # Common token mappings
    token_map = {
        "bitcoin": "BTC",
        "btc": "BTC",
        "ethereum": "ETH",
        "eth": "ETH",
        "usdc": "USDC",
        "usdt": "USDT",
        # ... más tokens
    }
    
    for keyword, token in token_map.items():
        if keyword in content_lower:
            return token
    
    return None
```

#### Step 3: Agregar Respuestas Estáticas para Preguntas Comunes (0.5 días)

**Archivo**: `src/app/application/guest/handlers/static_responses.py` (nuevo)

**Contenido**:
```python
"""Static responses for common educational questions."""

STATIC_RESPONSES = {
    "en": {
        "what is bitcoin": """**Bitcoin (BTC)** is the first and largest cryptocurrency by market capitalization.

**Key Features:**
- **Decentralized**: No central authority controls Bitcoin
- **Limited Supply**: Only 21 million Bitcoin will ever exist
- **Blockchain**: Transactions recorded on a public ledger
- **Digital Gold**: Often called "digital gold" due to store of value properties

**Use Cases:**
- Store of value (like gold)
- Peer-to-peer payments
- Remittances (sending money across borders)
- Investment/portfolio diversification

**Current Status**: Bitcoin is the most widely adopted cryptocurrency with millions of users worldwide.

Want to learn more about Bitcoin trading or DeFi? Sign up for full access!""",
        
        "what is btc": """**BTC** is the ticker symbol for **Bitcoin**, the first cryptocurrency.

Bitcoin was created in 2009 by an anonymous person (or group) using the name Satoshi Nakamoto. It's a decentralized digital currency that operates without a central bank or single administrator.

**Quick Facts:**
- Symbol: BTC
- Max Supply: 21 million
- Consensus: Proof of Work (PoW)
- Block Time: ~10 minutes

Want to trade Bitcoin or explore DeFi opportunities? Sign up to get started!""",
        
        # ... más respuestas estáticas
    },
    "es": {
        "qué es bitcoin": """**Bitcoin (BTC)** es la primera y mayor criptomoneda por capitalización de mercado.

**Características Clave:**
- **Descentralizado**: Ninguna autoridad central controla Bitcoin
- **Suministro Limitado**: Solo existirán 21 millones de Bitcoin
- **Blockchain**: Transacciones registradas en un libro público
- **Oro Digital**: A menudo llamado "oro digital" por sus propiedades de reserva de valor

¿Quieres aprender más sobre trading de Bitcoin o DeFi? ¡Regístrate para acceso completo!""",
        # ... más respuestas en español
    },
    # ... otros idiomas
}

def get_static_response(query: str, language: str = "en") -> Optional[str]:
    """Get static response for common query if available."""
    query_lower = query.lower().strip()
    
    # Try exact match first
    if query_lower in STATIC_RESPONSES.get(language, {}):
        return STATIC_RESPONSES[language][query_lower]
    
    # Try fuzzy matching for variations
    for key, response in STATIC_RESPONSES.get(language, {}).items():
        if key in query_lower or query_lower in key:
            return response
    
    return None
```

**Integración en GuestHandlerService**:
```python
# En _handle_general_conversation, antes de LLM call:
from app.application.guest.handlers.static_responses import get_static_response

static_response = get_static_response(content, language)
if static_response:
    return {
        "content": static_response,
        "enrichment": {"source": "static_response"},
        "requires_registration": False,
    }
```

#### Step 4: Testing & Validation (1 día)

**Tests a crear**:
1. `test_guest_educational_queries_bitcoin` - Verificar respuesta específica sobre Bitcoin
2. `test_guest_educational_queries_multilanguage` - Verificar respuestas en múltiples idiomas
3. `test_guest_intent_detection_token_info` - Verificar detección de intents educativos
4. `test_guest_static_response_fallback` - Verificar uso de respuestas estáticas

**Validación**:
- Ejecutar tests existentes para asegurar no regresiones
- Validar respuestas con LLM validator
- Medir latencia y costo

---

## Implementation Timeline

**Total**: 3.5 días

- **Día 1**: Mejorar Intent Detection
- **Día 2**: Mejorar Guest Handler + Knowledge Injection
- **Día 3 (mañana)**: Agregar respuestas estáticas
- **Día 3 (tarde)**: Testing & Validation
- **Día 4 (mañana)**: Deploy & Monitoring

---

## Success Metrics

**KPIs a monitorear**:
- ✅ **Intent Detection Accuracy**: > 90% para preguntas educativas
- ✅ **Response Relevance**: LLM validator score > 0.85
- ✅ **User Satisfaction**: Menos abandonos en primera interacción
- ✅ **Performance**: Latencia P95 < 2.5 segundos
- ✅ **Cost**: No aumento > 10% en costo LLM

**Rollback Criteria**:
- ❌ Intent detection accuracy < 80%
- ❌ Error rate > 5%
- ❌ Latencia P95 > 3 segundos
- ❌ Costo LLM aumenta > 15%

---

## Conclusion

**Problema**: Sistema responde genéricamente a preguntas educativas básicas.

**Solución Recomendada**: Mejorar Intent Detection + Knowledge Injection + Respuestas Estáticas (Solution A mejorada).

**Beneficios Esperados**:
- ✅ Mejor UX para usuarios guest
- ✅ Mayor engagement y conversión
- ✅ Respuestas útiles y educativas
- ✅ Bajo costo de implementación (3.5 días)
- ✅ Bajo riesgo técnico

**Próximos Pasos**:
1. Aprobar solución recomendada
2. Asignar desarrollador (3.5 días)
3. Implementar cambios
4. Testing & validación
5. Deploy con feature flag
6. Monitorear métricas

---

*Análisis completo siguiendo CTO Engineering Framework - Fases 1-4*
