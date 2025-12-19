# Reporte de Módulos - Anvil Backend

**Fecha**: December 19, 2025
**Audiencia**: CPO (Chief Product Officer)
**Propósito**: Análisis completo de módulos del sistema para toma de decisiones estratégicas

---

## 📊 Resumen Ejecutivo

Este documento proporciona un análisis completo de todos los módulos del sistema Anvil Backend, basado en el análisis del OpenAPI schema del sistema en producción.

**Total de módulos analizados**: 47
**Total de endpoints**: 233
**Total de paths únicos**: 194

---

## 📦 Módulos del Sistema

### Chat con Agentes IA

**URL Base**: `/api/v1/user`
**Tag**: `chat`
**Total Endpoints**: 19
**Complejidad Frontend**: Alta

#### Descripción

Sistema de chat con múltiples agentes IA especializados para asistencia en DeFi y trading. Permite a los usuarios interactuar con agentes especializados mediante conversaciones naturales. Incluye detección de intención, análisis de conversaciones y dashboard de analytics.

#### Beneficios

- Asistencia IA personalizada
- Múltiples agentes especializados
- Análisis conversacional
- Experiencia de usuario mejorada
- Detección de intención

#### Impacto si se Desactiva

Pérdida de la funcionalidad principal de asistencia IA del producto. Los usuarios no podrían interactuar con agentes especializados, eliminando el valor diferencial principal.

#### Detalles Técnicos

- **Métodos HTTP**: GET (12), POST (7)
- **Paths únicos**: 17

---

### Cuenta y Autenticación

**URL Base**: `/api/v1/account`
**Tag**: `Account`
**Total Endpoints**: 13
**Complejidad Frontend**: Media

#### Descripción

Sistema completo de autenticación y gestión de cuentas: registro, login, recuperación de contraseña, verificación de email, gestión de perfil. Incluye soporte para Privy (wallet-based auth) y autenticación tradicional.

#### Beneficios

- Autenticación segura
- Gestión de cuenta
- Recuperación de contraseña
- Seguridad
- Múltiples métodos de auth

#### Impacto si se Desactiva

Sistema de autenticación perdido - CRÍTICO. Sin esto, los usuarios no pueden acceder al sistema. Bloquea completamente el uso del producto.

#### Detalles Técnicos

- **Métodos HTTP**: DELETE (1), GET (1), POST (8), PUT (3)
- **Paths únicos**: 11

---

### Administración de Proyectos

**URL Base**: `/api/v1/admin`
**Tag**: `Admin - Projects`
**Total Endpoints**: 13
**Complejidad Frontend**: Media

#### Descripción

Gestión administrativa de proyectos de usuarios. Permite a administradores crear, modificar y gestionar proyectos del sistema.

#### Beneficios

- Gestión administrativa
- Control de proyectos
- Configuración del sistema

#### Impacto si se Desactiva

Sin capacidad de gestionar proyectos desde el panel de administración. Los administradores perderían control sobre proyectos.

#### Detalles Técnicos

- **Métodos HTTP**: DELETE (1), GET (5), PATCH (2), POST (5)
- **Paths únicos**: 7

---

### Sistema de Distillation

**URL Base**: `/api/v1/admin`
**Tag**: `Admin - Distillation`
**Total Endpoints**: 10
**Complejidad Frontend**: Media

#### Descripción

Sistema de distillation para optimización de requests LLM. Permite a administradores gestionar y monitorear el proceso de distillation.

#### Beneficios

- Optimización de LLM
- Reducción de costos
- Gestión de requests

#### Impacto si se Desactiva

Sin optimización de requests LLM. Costos más altos y menor eficiencia en el uso de modelos.

#### Detalles Técnicos

- **Métodos HTTP**: DELETE (1), GET (5), PATCH (2), POST (2)
- **Paths únicos**: 7

---

### Analytics Dashboard

**URL Base**: `/api/v1/user`
**Tag**: `analytics`
**Total Endpoints**: 8
**Complejidad Frontend**: Baja

#### Descripción

Dashboard de analytics para análisis de conversaciones y uso del sistema. Proporciona métricas y visualizaciones de datos.

#### Beneficios

- Métricas de uso
- Análisis de conversaciones
- Visualizaciones
- Insights

#### Impacto si se Desactiva

Sin dashboard de analytics. Pérdida de visibilidad sobre el uso del sistema y comportamiento de usuarios.

#### Detalles Técnicos

- **Métodos HTTP**: GET (8)
- **Paths únicos**: 8

---

### Administración de Usuarios - Listado y Consulta

**URL Base**: `/api/v1/admin/users`
**Tag**: `user`
**Total Endpoints**: 8
**Complejidad Frontend**: Baja

#### Descripción

Módulo administrativo para consulta y listado de usuarios del sistema. Permite a administradores obtener información detallada de usuarios, listar usuarios con filtros, y consultar estados de cuentas. Complementa el módulo de gestión de usuarios proporcionando capacidades de lectura y consulta.

#### Beneficios

- Consulta de información de usuarios
- Listado con filtros avanzados
- Visibilidad del estado de cuentas
- Auditoría y reporting
- Análisis de usuarios

#### Impacto si se Desactiva

Sin capacidad de consultar y listar usuarios desde el panel de administración. Los administradores perderían visibilidad sobre usuarios del sistema, dificultando la auditoría y el análisis.

#### Detalles Técnicos

- **Métodos HTTP**: GET (8)
- **Paths únicos**: 8
- **Tipo**: Administrativo (requiere permisos de admin)
- **Relacionado con**: Módulo "Administración de Usuarios - Gestión" (operaciones de escritura)

---

### ULTRA Auto-Executor

**URL Base**: `/api/v1/user`
**Tag**: `ultra-auto-executor`
**Total Endpoints**: 7
**Complejidad Frontend**: Baja

#### Descripción

Sistema de ejecución automática de trades. Permite ejecutar estrategias de trading de forma automatizada con gestión de riesgo.

#### Beneficios

- Ejecución automática
- Trading automatizado
- Gestión de riesgo
- Alta frecuencia

#### Impacto si se Desactiva

Sin capacidad de ejecución automática. Los usuarios avanzados perderían una herramienta profesional de trading.

#### Detalles Técnicos

- **Métodos HTTP**: GET (1), POST (5), PUT (1)
- **Paths únicos**: 7

---

### Administración - Ranking de LLMs

**URL Base**: `/api/v1/admin/llm/ranking`
**Tag**: `Admin - LLM Ranking`
**Total Endpoints**: 7
**Complejidad Frontend**: Baja

#### Descripción

Módulo administrativo para ranking y gestión de modelos LLM. Permite a administradores gestionar, rankear y optimizar el uso de diferentes modelos LLM en el sistema. Incluye configuración de rankings, gestión de modelos disponibles, y optimización de costos mediante selección inteligente de modelos basada en performance y costo.

#### Beneficios

- Optimización de costos de LLM
- Gestión centralizada de modelos
- Ranking inteligente basado en performance
- Reducción de costos operativos
- Control administrativo sobre uso de LLM
- Configuración de políticas de uso

#### Impacto si se Desactiva

Sin sistema de ranking de LLMs, los administradores perderían capacidad de optimizar costos y performance de modelos LLM. El sistema usaría modelos de forma menos eficiente, resultando en costos más altos y menor control sobre la selección de modelos. Esto impactaría directamente los costos operativos del sistema.

#### Detalles Técnicos

- **Métodos HTTP**: DELETE (1), GET (2), POST (3), PUT (1)
- **Paths únicos**: 6
- **Tipo**: Administrativo (requiere permisos de admin)

---

### Sistema de Alertas

**URL Base**: `/api/v1/user`
**Tag**: `alerts`
**Total Endpoints**: 7
**Complejidad Frontend**: Baja

#### Descripción

Gestiona alertas de riesgo y notificaciones para usuarios sobre cambios en el mercado, posiciones y oportunidades. Sistema proactivo de notificaciones basado en umbrales y condiciones personalizables.

#### Beneficios

- Notificaciones en tiempo real
- Prevención de pérdidas
- Alertas personalizables
- Monitoreo proactivo

#### Impacto si se Desactiva

Los usuarios no recibirían alertas críticas sobre riesgos o oportunidades, aumentando significativamente el riesgo de pérdidas.

#### Detalles Técnicos

- **Métodos HTTP**: DELETE (2), GET (2), POST (1), PUT (2)
- **Paths únicos**: 5

---

### Preferencias de Usuario

**URL Base**: `/api/v1/user`
**Tag**: `preferences`
**Total Endpoints**: 7
**Complejidad Frontend**: Baja

#### Descripción

Gestión de preferencias de usuario: configuración, personalización y settings. Sistema de personalización del usuario.

#### Beneficios

- Personalización
- Configuración flexible
- Experiencia adaptada

#### Impacto si se Desactiva

Sin personalización de usuario. Experiencia genérica sin adaptación a preferencias individuales.

#### Detalles Técnicos

- **Métodos HTTP**: DELETE (2), GET (1), POST (2), PUT (2)
- **Paths únicos**: 6

---

### Administración de Usuarios - Gestión

**URL Base**: `/api/v1/admin/users`
**Tag**: `AdminUsers`
**Total Endpoints**: 6
**Complejidad Frontend**: Baja

#### Descripción

Módulo administrativo para gestión completa de usuarios del sistema. Permite a administradores realizar operaciones de escritura sobre usuarios: activar/desactivar cuentas, cambiar roles (incluyendo otorgar/revocar permisos de administrador), modificar contraseñas y gestionar permisos de acceso. Esencial para el control administrativo del sistema y la gestión de seguridad.

#### Beneficios

- Control administrativo completo sobre usuarios
- Gestión de roles y permisos
- Activación/desactivación de cuentas
- Seguridad y control de acceso
- Modificación de credenciales

#### Impacto si se Desactiva

Sin capacidad de gestionar usuarios desde el panel de administración. Los administradores perderían control crítico sobre usuarios, incluyendo la capacidad de activar/desactivar cuentas, gestionar roles y permisos. Esto bloquearía funcionalidades administrativas esenciales y comprometería la seguridad del sistema al no poder gestionar accesos.

#### Detalles Técnicos

- **Métodos HTTP**: GET (1), PATCH (5)
- **Paths únicos**: 6
- **Tipo**: Administrativo (requiere permisos de admin)
- **Relacionado con**: Módulo "Administración de Usuarios - Listado y Consulta" (operaciones de lectura)

---

### Suscripciones

**URL Base**: `/api/v1/subscription`
**Tag**: `Subscription`
**Total Endpoints**: 6
**Complejidad Frontend**: Baja

#### Descripción

Gestión de suscripciones y pagos. Sistema de monetización con múltiples planes y gestión de facturación mediante Stripe.

#### Beneficios

- Monetización
- Gestión de suscripciones
- Múltiples planes
- Facturación automática

#### Impacto si se Desactiva

Sin capacidad de monetización. No se pueden generar ingresos recurrentes, bloqueando el modelo de negocio.

#### Detalles Técnicos

- **Métodos HTTP**: GET (3), POST (3)
- **Paths únicos**: 6

---

### Métricas Administrativas

**URL Base**: `/api/v1/admin`
**Tag**: `Admin - Metrics`
**Total Endpoints**: 6
**Complejidad Frontend**: Baja

#### Descripción

Métricas y analytics para administradores. Dashboard de métricas del sistema y análisis de uso.

#### Beneficios

- Visibilidad del sistema
- Métricas administrativas
- Análisis de uso

#### Impacto si se Desactiva

Sin métricas administrativas. Los administradores perderían visibilidad sobre el estado del sistema.

#### Detalles Técnicos

- **Métodos HTTP**: GET (6)
- **Paths únicos**: 6

---

### Búsqueda

**URL Base**: `/api/v1/user`
**Tag**: `search`
**Total Endpoints**: 6
**Complejidad Frontend**: Baja

#### Descripción

Búsqueda global en el sistema con historial y sugerencias. Sistema de búsqueda unificado con capacidades avanzadas.

#### Beneficios

- Búsqueda unificada
- Historial de búsquedas
- Sugerencias inteligentes

#### Impacto si se Desactiva

Sin capacidad de búsqueda global. Los usuarios perderían una funcionalidad esencial de navegación.

#### Detalles Técnicos

- **Métodos HTTP**: DELETE (2), GET (4)
- **Paths únicos**: 5

---

### Atlas

**URL Base**: `/api/v1/user`
**Tag**: `Atlas`
**Total Endpoints**: 5
**Complejidad Frontend**: Baja

#### Descripción

Datos geográficos: países y ciudades para análisis geográfico. Soporte para análisis basado en ubicación.

#### Beneficios

- Datos geográficos
- Análisis por región
- Localización

#### Impacto si se Desactiva

Sin capacidades de análisis geográfico. Funcionalidad de nicho pero útil para análisis regional.

#### Detalles Técnicos

- **Métodos HTTP**: GET (3), POST (2)
- **Paths únicos**: 5

---

### Métricas de Usuario

**URL Base**: `/api/v1/metrics`
**Tag**: `Metrics`
**Total Endpoints**: 5
**Complejidad Frontend**: Baja

#### Descripción

Sistema de métricas y tracking de eventos para usuarios. Permite rastrear uso y comportamiento.

#### Beneficios

- Tracking de eventos
- Métricas de uso
- Análisis de comportamiento

#### Impacto si se Desactiva

Sin tracking de métricas. Pérdida de datos valiosos para análisis y mejora del producto.

#### Detalles Técnicos

- **Métodos HTTP**: GET (4), POST (1)
- **Paths únicos**: 5

---

### Wallets

**URL Base**: `/api/v1/user/wallet`
**Tag**: `wallet`
**Total Endpoints**: 5
**Complejidad Frontend**: Baja

#### Descripción

Gestión de wallets de usuarios. Permite a usuarios autenticados conectar, gestionar y exportar sus wallets blockchain. Incluye integración con múltiples proveedores de wallets, gestión de direcciones y operaciones de wallet para usuarios.

#### Beneficios

- Gestión de wallets para usuarios
- Integración blockchain
- Seguridad y control de wallets
- Exportación de wallets
- Soporte múltiples proveedores

#### Impacto si se Desactiva

Sin gestión de wallets, los usuarios no pueden conectar ni gestionar sus wallets blockchain. Esto bloquearía funcionalidades esenciales del producto que dependen de la conexión de wallets, como operaciones DeFi, transacciones y gestión de activos.

#### Detalles Técnicos

- **Métodos HTTP**: GET (2), POST (3)
- **Paths únicos**: 3
- **Tipo**: Usuario (requiere autenticación)

---

### Hunter AI - Análisis de Riesgo

**URL Base**: `/api/v1/user`
**Tag**: `hunter-risk`
**Total Endpoints**: 5
**Complejidad Frontend**: Baja

#### Descripción

Análisis avanzado de riesgo para posiciones y estrategias. Proporciona scoring de riesgo y recomendaciones.

#### Beneficios

- Análisis de riesgo
- Scoring de riesgo
- Recomendaciones
- Prevención de pérdidas

#### Impacto si se Desactiva

Sin análisis de riesgo avanzado. Los usuarios perderían herramientas profesionales de evaluación de riesgo.

#### Detalles Técnicos

- **Métodos HTTP**: GET (5)
- **Paths únicos**: 5

---

### ULTRA Flash Loans

**URL Base**: `/api/v1/user`
**Tag**: `ultra-flash-loans`
**Total Endpoints**: 5
**Complejidad Frontend**: Baja

#### Descripción

Sistema de flash loans para operaciones DeFi avanzadas. Permite ejecutar operaciones complejas sin capital inicial.

#### Beneficios

- Flash loans
- Operaciones avanzadas
- Sin capital inicial
- Arbitraje

#### Impacto si se Desactiva

Sin soporte para flash loans. Los usuarios avanzados perderían capacidad de operaciones DeFi complejas.

#### Detalles Técnicos

- **Métodos HTTP**: GET (4), POST (1)
- **Paths únicos**: 5

---

### Validación de Distillation

**URL Base**: `/api/v1/admin`
**Tag**: `Admin - Distillation Validation`
**Total Endpoints**: 5
**Complejidad Frontend**: Baja

#### Descripción

Sistema de validación de requests para el proceso de distillation. Asegura calidad y eficiencia.

#### Beneficios

- Validación de requests
- Control de calidad
- Optimización

#### Impacto si se Desactiva

Sin validación de distillation. Menor calidad y eficiencia en el proceso de optimización.

#### Detalles Técnicos

- **Métodos HTTP**: GET (4), PATCH (1)
- **Paths únicos**: 4

---

### Proyectos de Usuario

**URL Base**: `/api/v1/user`
**Tag**: `User - Projects`
**Total Endpoints**: 5
**Complejidad Frontend**: Baja

#### Descripción

Gestión de proyectos por parte de usuarios. Permite crear y gestionar proyectos personalizados.

#### Beneficios

- Gestión de proyectos
- Personalización
- Organización

#### Impacto si se Desactiva

Sin capacidad de gestionar proyectos. Los usuarios perderían funcionalidad de organización y personalización.

#### Detalles Técnicos

- **Métodos HTTP**: GET (3), POST (2)
- **Paths únicos**: 5

---

### Graph Visualization

**URL Base**: `/api/v1/user`
**Tag**: `graph-visualization`
**Total Endpoints**: 4
**Complejidad Frontend**: Baja

#### Descripción

Visualización de grafos de protocolos DeFi. Permite visualizar relaciones y conexiones entre protocolos.

#### Beneficios

- Visualización de datos
- Análisis visual
- Relaciones complejas

#### Impacto si se Desactiva

Sin visualización de grafos. Los usuarios perderían capacidad de análisis visual de relaciones.

#### Detalles Técnicos

- **Métodos HTTP**: GET (4)
- **Paths únicos**: 4

---

### Hunter AI - Análisis de Sentimiento

**URL Base**: `/api/v1/user`
**Tag**: `hunter-sentiment`
**Total Endpoints**: 4
**Complejidad Frontend**: Baja

#### Descripción

Análisis de sentimiento del mercado basado en datos sociales y noticias. Proporciona insights sobre sentimiento del mercado.

#### Beneficios

- Análisis de sentimiento
- Insights de mercado
- Datos sociales

#### Impacto si se Desactiva

Sin análisis de sentimiento. Los usuarios perderían insights valiosos sobre sentimiento del mercado.

#### Detalles Técnicos

- **Métodos HTTP**: GET (4)
- **Paths únicos**: 4

---

### Hunter AI - Predicciones

**URL Base**: `/api/v1/user`
**Tag**: `hunter-predictions`
**Total Endpoints**: 4
**Complejidad Frontend**: Baja

#### Descripción

Predicciones de precio y tendencias de mercado basadas en modelos de ML. Proporciona forecast de precios.

#### Beneficios

- Predicciones de precio
- Forecast
- Modelos de ML
- Tendencias

#### Impacto si se Desactiva

Sin predicciones de precio. Los usuarios perderían herramientas de forecast y análisis predictivo.

#### Detalles Técnicos

- **Métodos HTTP**: GET (3), POST (1)
- **Paths únicos**: 4

---

### Hunter AI - Señales de Trading

**URL Base**: `/api/v1/user`
**Tag**: `hunter-signals`
**Total Endpoints**: 4
**Complejidad Frontend**: Baja

#### Descripción

Generación de señales de trading basadas en análisis técnico y ML. Proporciona señales de compra/venta.

#### Beneficios

- Señales de trading
- Análisis técnico
- Recomendaciones
- Trading asistido

#### Impacto si se Desactiva

Sin señales de trading. Los usuarios perderían asistencia en decisiones de trading.

#### Detalles Técnicos

- **Métodos HTTP**: GET (4)
- **Paths únicos**: 4

---

### Gestión de Portafolio

**URL Base**: `/api/v1/user`
**Tag**: `portfolio`
**Total Endpoints**: 4
**Complejidad Frontend**: Baja

#### Descripción

Gestión y análisis completo de portafolios de usuarios. Permite rastrear activos, analizar rendimiento, calcular riesgos y optimizar asignaciones.

#### Beneficios

- Gestión centralizada
- Análisis de rendimiento
- Optimización
- Seguimiento

#### Impacto si se Desactiva

Funcionalidad core del producto perdida. Los usuarios no podrían gestionar ni analizar sus portafolios.

#### Detalles Técnicos

- **Métodos HTTP**: GET (3), POST (1)
- **Paths únicos**: 4

---

### Hunter AI - Detección de Patrones

**URL Base**: `/api/v1/user`
**Tag**: `hunter-patterns`
**Total Endpoints**: 4
**Complejidad Frontend**: Baja

#### Descripción

Detección de patrones en datos de mercado y blockchain. Identifica patrones técnicos y oportunidades.

#### Beneficios

- Detección de patrones
- Análisis técnico
- Oportunidades
- Insights

#### Impacto si se Desactiva

Sin detección de patrones. Los usuarios perderían capacidad de identificar oportunidades basadas en patrones.

#### Detalles Técnicos

- **Métodos HTTP**: GET (4)
- **Paths únicos**: 4

---

### ULTRA Arbitraje

**URL Base**: `/api/v1/user`
**Tag**: `ultra-arbitrage`
**Total Endpoints**: 4
**Complejidad Frontend**: Baja

#### Descripción

Sistema de detección y ejecución de oportunidades de arbitraje. Identifica y ejecuta arbitraje entre DEXs.

#### Beneficios

- Arbitraje automatizado
- Oportunidades
- Ejecución rápida
- Profitabilidad

#### Impacto si se Desactiva

Sin capacidad de arbitraje. Los usuarios avanzados perderían oportunidad de generar ganancias por arbitraje.

#### Detalles Técnicos

- **Métodos HTTP**: GET (3), POST (1)
- **Paths únicos**: 4

---

### ULTRA MEV Protection

**URL Base**: `/api/v1/user`
**Tag**: `ultra-mev`
**Total Endpoints**: 4
**Complejidad Frontend**: Baja

#### Descripción

Protección contra MEV (Maximal Extractable Value). Protege a usuarios de front-running y sandwich attacks.

#### Beneficios

- Protección MEV
- Seguridad
- Protección de trades
- Front-running protection

#### Impacto si se Desactiva

Sin protección MEV. Los usuarios estarían expuestos a front-running y otros ataques MEV.

#### Detalles Técnicos

- **Métodos HTTP**: GET (3), POST (1)
- **Paths únicos**: 4

---

### Machine Learning - Predicciones

**URL Base**: `/api/v1/user`
**Tag**: `ML Prediction`
**Total Endpoints**: 4
**Complejidad Frontend**: Baja

#### Descripción

Predicciones de riesgo y mercado basadas en modelos de ML. Proporciona análisis predictivo avanzado.

#### Beneficios

- Predicciones ML
- Análisis predictivo
- Modelos avanzados
- Insights

#### Impacto si se Desactiva

Sin predicciones ML. Los usuarios perderían análisis predictivo avanzado y insights valiosos.

#### Detalles Técnicos

- **Métodos HTTP**: GET (3), POST (1)
- **Paths únicos**: 4

---

### Machine Learning - Análisis de Red

**URL Base**: `/api/v1/user`
**Tag**: `Network Analysis`
**Total Endpoints**: 4
**Complejidad Frontend**: Baja

#### Descripción

Análisis de redes y relaciones usando modelos de ML. Proporciona análisis de grafos y relaciones complejas.

#### Beneficios

- Análisis de redes
- Relaciones complejas
- Modelos ML
- Insights

#### Impacto si se Desactiva

Sin análisis de redes. Los usuarios perderían capacidad de análisis de relaciones complejas.

#### Detalles Técnicos

- **Métodos HTTP**: GET (4)
- **Paths únicos**: 4

---

### Mercados

**URL Base**: `/api/v1/user`
**Tag**: `markets`
**Total Endpoints**: 4
**Complejidad Frontend**: Baja

#### Descripción

Información de mercados, precios y datos de mercado en tiempo real. Proporciona datos agregados de múltiples fuentes.

#### Beneficios

- Datos en tiempo real
- Precios agregados
- Análisis de mercado
- Datos históricos

#### Impacto si se Desactiva

Sin información de mercado. Los usuarios no tendrían acceso a datos de mercado esenciales.

#### Detalles Técnicos

- **Métodos HTTP**: GET (4)
- **Paths únicos**: 4

---

### General

**URL Base**: ``
**Tag**: `General`
**Total Endpoints**: 3
**Complejidad Frontend**: Baja

#### Descripción

Endpoints generales del sistema: health checks y utilidades.

#### Beneficios

- Health checks
- Utilidades
- Monitoreo

#### Impacto si se Desactiva

Sin health checks. Dificultad para monitorear el estado del sistema.

#### Detalles Técnicos

- **Métodos HTTP**: GET (3)
- **Paths únicos**: 3

---

### Detección de Intención

**URL Base**: `/api/v1/user`
**Tag**: `chat-intent`
**Total Endpoints**: 3
**Complejidad Frontend**: Baja

#### Descripción

Sistema de detección de intención en conversaciones. Identifica la intención del usuario para routing inteligente.

#### Beneficios

- Detección de intención
- Routing inteligente
- Mejor UX
- Personalización

#### Impacto si se Desactiva

Sin detección de intención. Menor precisión en routing y experiencia de usuario degradada.

#### Detalles Técnicos

- **Métodos HTTP**: POST (3)
- **Paths únicos**: 3

---

### GraphRAG - Búsqueda

**URL Base**: `/api/v1/user`
**Tag**: `Graph Search`
**Total Endpoints**: 3
**Complejidad Frontend**: Baja

#### Descripción

Búsqueda semántica en grafos de conocimiento DeFi. Utiliza GraphRAG para búsqueda avanzada de protocolos.

#### Beneficios

- Búsqueda semántica
- GraphRAG
- Búsqueda avanzada
- Descubrimiento

#### Impacto si se Desactiva

Sin búsqueda GraphRAG. Los usuarios perderían capacidad de búsqueda semántica avanzada.

#### Detalles Técnicos

- **Métodos HTTP**: POST (3)
- **Paths únicos**: 3

---

### GraphRAG - Analytics

**URL Base**: `/api/v1/user`
**Tag**: `Graph Analytics`
**Total Endpoints**: 3
**Complejidad Frontend**: Baja

#### Descripción

Analytics y análisis de grafos de protocolos DeFi. Proporciona insights sobre relaciones y conexiones.

#### Beneficios

- Analytics de grafos
- Análisis de relaciones
- Insights
- Visualización

#### Impacto si se Desactiva

Sin analytics de grafos. Pérdida de capacidad de análisis de relaciones complejas entre protocolos.

#### Detalles Técnicos

- **Métodos HTTP**: GET (1), POST (2)
- **Paths únicos**: 3

---

### Recuperación de Contraseña

**URL Base**: `/api/v1/account`
**Tag**: `Account - Password Reset`
**Total Endpoints**: 2
**Complejidad Frontend**: Baja

#### Descripción

Sistema de recuperación de contraseña para usuarios. Permite resetear contraseñas de forma segura.

#### Beneficios

- Recuperación segura
- UX mejorada
- Seguridad

#### Impacto si se Desactiva

Sin recuperación de contraseña. Los usuarios no podrían recuperar acceso a sus cuentas.

#### Detalles Técnicos

- **Métodos HTTP**: POST (2)
- **Paths únicos**: 2

---

### Pagos

**URL Base**: `/api/v1/payments`
**Tag**: `payments`
**Total Endpoints**: 2
**Complejidad Frontend**: Baja

#### Descripción

Procesamiento de pagos mediante Stripe. Integración completa con pasarela de pagos.

#### Beneficios

- Procesamiento de pagos
- Integración Stripe
- Múltiples métodos

#### Impacto si se Desactiva

Sin capacidad de procesar pagos. Bloquea monetización directa y suscripciones.

#### Detalles Técnicos

- **Métodos HTTP**: GET (1), POST (1)
- **Paths únicos**: 2

---

### Autenticación

**URL Base**: `/api/v1/auth`
**Tag**: `auth`
**Total Endpoints**: 2
**Complejidad Frontend**: Baja

#### Descripción

Sistema de autenticación y autorización. Gestión de roles y permisos.

#### Beneficios

- Autenticación
- Autorización
- Roles y permisos

#### Impacto si se Desactiva

Sin sistema de autenticación. Bloquea completamente el acceso al sistema.

#### Detalles Técnicos

- **Métodos HTTP**: POST (2)
- **Paths únicos**: 2

---

### Administración General

**URL Base**: `/api/v1/admin`
**Tag**: `admin`
**Total Endpoints**: 2
**Complejidad Frontend**: Baja

#### Descripción

Funcionalidades administrativas generales del sistema.

#### Beneficios

- Gestión administrativa
- Control del sistema

#### Impacto si se Desactiva

Sin capacidades administrativas generales. Pérdida de control administrativo.

#### Detalles Técnicos

- **Métodos HTTP**: GET (2)
- **Paths únicos**: 2

---

### Administración de Wallets

**URL Base**: `/api/v1/admin`
**Tag**: `AdminWallets`
**Total Endpoints**: 2
**Complejidad Frontend**: Baja

#### Descripción

Gestión administrativa de wallets de usuarios. Permite a administradores gestionar wallets.

#### Beneficios

- Gestión administrativa
- Control de wallets

#### Impacto si se Desactiva

Sin capacidad de gestionar wallets desde administración.

#### Detalles Técnicos

- **Métodos HTTP**: GET (1), PATCH (1)
- **Paths únicos**: 1

---

### GraphRAG - Monitoreo

**URL Base**: `/api/v1/user`
**Tag**: `Graph Monitoring`
**Total Endpoints**: 2
**Complejidad Frontend**: Baja

#### Descripción

Monitoreo del sistema GraphRAG. Proporciona métricas y estado del sistema de grafos.

#### Beneficios

- Monitoreo
- Métricas
- Estado del sistema

#### Impacto si se Desactiva

Sin monitoreo de GraphRAG. Pérdida de visibilidad sobre el estado del sistema de grafos.

#### Detalles Técnicos

- **Métodos HTTP**: GET (1), POST (1)
- **Paths únicos**: 2

---

### Dashboard

**URL Base**: `/api/v1/user`
**Tag**: `dashboard`
**Total Endpoints**: 2
**Complejidad Frontend**: Baja

#### Descripción

Panel de control principal con métricas, resúmenes y visualizaciones. Vista centralizada del estado del sistema.

#### Beneficios

- Vista general
- Métricas clave
- Resumen ejecutivo
- Visualización

#### Impacto si se Desactiva

Sin vista centralizada. Los usuarios perderían el dashboard principal, experiencia degradada.

#### Detalles Técnicos

- **Métodos HTTP**: GET (2)
- **Paths únicos**: 2

---

### Transacciones

**URL Base**: `/api/v1/user`
**Tag**: `transactions`
**Total Endpoints**: 2
**Complejidad Frontend**: Baja

#### Descripción

Registro y gestión de transacciones, historial y confirmaciones. Sistema completo de tracking de transacciones blockchain.

#### Beneficios

- Historial completo
- Confirmaciones
- Registro detallado
- Tracking

#### Impacto si se Desactiva

Sin capacidad de rastrear transacciones. Los usuarios perderían visibilidad de su actividad.

#### Detalles Técnicos

- **Métodos HTTP**: GET (1), POST (1)
- **Paths únicos**: 1

---

### Cambio de Contraseña

**URL Base**: `/api/v1/account`
**Tag**: `Account - Change Password`
**Total Endpoints**: 1
**Complejidad Frontend**: Baja

#### Descripción

Sistema de cambio de contraseña para usuarios autenticados.

#### Beneficios

- Cambio de contraseña
- Seguridad
- Gestión de cuenta

#### Impacto si se Desactiva

Sin capacidad de cambiar contraseña. Los usuarios no podrían actualizar sus credenciales.

#### Detalles Técnicos

- **Métodos HTTP**: PUT (1)
- **Paths únicos**: 1

---

### Notificaciones

**URL Base**: `/api/v1/notifications`
**Tag**: `notifications`
**Total Endpoints**: 1
**Complejidad Frontend**: Baja

#### Descripción

Sistema de notificaciones para usuarios. Notificaciones push, email y en-app.

#### Beneficios

- Notificaciones multi-canal
- Engagement
- Comunicación

#### Impacto si se Desactiva

Sin sistema de notificaciones. Los usuarios no recibirían actualizaciones importantes.

#### Detalles Técnicos

- **Métodos HTTP**: GET (1)
- **Paths únicos**: 1

---

### Comparación

**URL Base**: `/api/v1/user`
**Tag**: `comparison`
**Total Endpoints**: 1
**Complejidad Frontend**: Baja

#### Descripción

Herramientas para comparar activos, protocolos y estrategias. Permite análisis comparativo side-by-side.

#### Beneficios

- Comparación de activos
- Análisis comparativo
- Toma de decisiones

#### Impacto si se Desactiva

Sin capacidad de comparar opciones. Los usuarios perderían herramienta valiosa para decisiones.

#### Detalles Técnicos

- **Métodos HTTP**: POST (1)
- **Paths únicos**: 1

---
