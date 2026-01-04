# Steering Documents

**Purpose**: High-level project steering documentation for product, technology, and structure decisions  
**Audience**: CPO, CEO, CTO, Engineering Leadership  
**Last Updated**: January 2, 2026

---

## 📚 Documents

### [Product Vision](./product.md)

Product strategy, target users, and roadmap priorities.

- Vision statement and product pillars
- Target user segments
- Product tiers and pricing strategy
- Key differentiators
- Success metrics
- Roadmap priorities

### [Technical Stack](./tech.md)

Technology choices, architecture patterns, and implementation details.

- Core technology stack
- Architecture patterns (Hexagonal, CQRS)
- LLM provider configuration
- MCP server architecture
- Database schema overview
- Security configuration
- Development workflow

### [Project Structure](./structure.md)

Codebase organization and conventions.

- Directory overview
- Domain module structure
- Application layer patterns
- Infrastructure adapters
- Presentation controllers
- Dependency injection setup
- Testing structure
- File naming conventions

### [Authentication & Authorization](./authentication.md)

Complete authentication system documentation.

- Privy integration (Web3-native auth)
- Traditional authentication (email/password)
- JWT token system
- Session management
- Role-Based Access Control (RBAC)
- Admin system and Super Admin
- Security features

---

## 🔗 Related Documents

- [API Architecture Spec (CPO/CEO)](../API_ARCHITECTURE_SPEC_CPO_CEO.md) - Complete API architecture overview
- [Modules Report (CPO)](../MODULES_REPORT_CPO.md) - Detailed module analysis
- [Main Documentation Index](../README.md) - Complete documentation index

---

## 📊 Quick Reference

| Aspect | Choice |
|--------|--------|
| **Architecture** | Hexagonal (Clean Architecture) |
| **Framework** | FastAPI + Dishka |
| **Database** | PostgreSQL 16+ |
| **Cache** | Redis 7+ |
| **Primary LLM** | Vertex AI (Gemini 2.0) |
| **Fallback LLM** | DeepInfra (Llama 3.1) |
| **Background Jobs** | Celery |
| **Payments** | Stripe |

---

**Last Updated**: January 2, 2026
