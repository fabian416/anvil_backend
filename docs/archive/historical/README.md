# Anvil Backend - Enterprise Documentation

**Version:** 2.0.0  
**Last Updated:** December 19, 2025  
**Status:** ✅ Production Ready

---

## 📚 Documentation Index

Welcome to the Anvil Backend enterprise documentation. This documentation is organized by audience and purpose to help you quickly find what you need.

### 🎯 Quick Navigation by Role

| Role | Start Here | Key Documents |
|------|------------|---------------|
| **New Developer** | [Getting Started Guide](getting-started/README.md) | [Architecture Overview](architecture/README.md), [Development Setup](getting-started/setup.md) |
| **Backend Developer** | [Developer Guide](developer/README.md) | [API Reference](api/README.md), [Code Standards](guides/code-standards.md) |
| **DevOps/SRE** | [Operations Guide](operations/README.md) | [Deployment Guide](deployment/README.md), [Monitoring](operations/monitoring.md) |
| **Product Manager** | [Product Documentation](product/README.md) | [Features Overview](features/README.md), [Roadmap](product/roadmap.md) |
| **Architect** | [Architecture Documentation](architecture/README.md) | [System Design](architecture/system-design.md), [Integration Patterns](architecture/integration-patterns.md) |

---

## 📖 Documentation Structure

```
docs/
├── README.md                    # This file - Main documentation index
│
├── getting-started/             # Onboarding and setup guides
│   ├── README.md               # Getting started overview
│   ├── setup.md                # Development environment setup
│   ├── quick-start.md          # Quick start guide
│   └── architecture-overview.md # High-level architecture
│
├── architecture/                # System architecture documentation
│   ├── README.md               # Architecture index
│   ├── system-design.md        # Overall system design
│   ├── hexagonal-architecture.md # Clean architecture patterns
│   ├── data-flow.md            # Data flow diagrams
│   └── integration-patterns.md # Integration patterns
│
├── api/                         # API documentation
│   ├── README.md               # API index
│   ├── reference/              # Complete API reference
│   ├── endpoints/              # Endpoint documentation
│   └── examples/               # API usage examples
│
├── guides/                      # Development guides
│   ├── README.md               # Guides index
│   ├── code-standards.md       # Coding standards and conventions
│   ├── testing.md              # Testing guidelines
│   ├── database.md             # Database guide
│   └── deployment.md           # Deployment procedures
│
├── features/                    # Feature documentation
│   ├── README.md               # Features index
│   ├── chat/                   # Chat feature docs
│   ├── graphrag/               # GraphRAG documentation
│   ├── agents/                 # Agent system docs
│   └── retry-system/           # Enterprise retry system
│
├── operations/                  # Operations and runbooks
│   ├── README.md               # Operations index
│   ├── deployment.md           # Deployment procedures
│   ├── monitoring.md           # Monitoring and observability
│   ├── troubleshooting.md      # Troubleshooting guide
│   └── runbooks/               # Operational runbooks
│
├── specifications/              # Technical specifications
│   ├── README.md               # Specifications index
│   ├── api-specs/              # API specifications
│   ├── integration-specs/       # Integration specifications
│   └── feature-specs/          # Feature specifications
│
├── reference/                   # Quick reference guides
│   ├── README.md               # Reference index
│   ├── commands.md             # Common commands
│   ├── configuration.md        # Configuration reference
│   └── troubleshooting.md      # Quick troubleshooting
│
├── security/                    # Security documentation
│   ├── README.md               # Security index
│   ├── guidelines.md           # Security guidelines
│   └── audit.md                # Security audit procedures
│
├── testing/                     # Testing documentation
│   ├── README.md               # Testing index
│   ├── guidelines.md           # Testing guidelines
│   └── coverage.md             # Test coverage reports
│
└── archive/                     # Historical documentation
    ├── historical/             # Historical documents
    └── obsolete/               # Obsolete/deprecated docs
```

---

## 🚀 Getting Started

### For New Team Members

1. **Start Here**: [Getting Started Guide](getting-started/README.md)
2. **Setup Environment**: [Development Setup](getting-started/setup.md)
3. **Understand Architecture**: [Architecture Overview](architecture/README.md)
4. **Read Code Standards**: [Code Standards Guide](guides/code-standards.md)

### For Developers

1. **Developer Guide**: [Developer Documentation](developer/README.md)
2. **API Reference**: [API Documentation](api/README.md)
3. **Testing Guide**: [Testing Guidelines](testing/README.md)
4. **Database Guide**: [Database Documentation](database/README.md)

### For DevOps

1. **Operations Guide**: [Operations Documentation](operations/README.md)
2. **Deployment Guide**: [Deployment Procedures](deployment/README.md)
3. **Monitoring**: [Monitoring Setup](operations/monitoring.md)

---

## 📋 Core Documentation

### Architecture & Design

- **[System Architecture](architecture/README.md)** - Overall system design
- **[Hexagonal Architecture](architecture/hexagonal-architecture.md)** - Clean architecture patterns
- **[Project Structure](steering/structure.md)** - Code organization
- **[Integration Patterns](architecture/integration-patterns.md)** - How components integrate

### Development

- **[Developer Guide](developer/README.md)** - Complete developer documentation
- **[Code Standards](guides/code-standards.md)** - Coding conventions and best practices
- **[Testing Guidelines](testing/README.md)** - Testing standards and practices
- **[API Reference](api/README.md)** - Complete API documentation

### Operations

- **[Deployment Guide](deployment/README.md)** - Production deployment procedures
- **[Operations Runbook](operations/README.md)** - Day-to-day operations
- **[Monitoring Guide](operations/monitoring.md)** - Monitoring and observability
- **[Troubleshooting](operations/troubleshooting.md)** - Common issues and solutions

### Features

- **[Enterprise Retry System](features/retry-system/README.md)** - Retry system documentation
- **[Chat System](features/chat/README.md)** - Chat feature documentation
- **[GraphRAG](features/graphrag/README.md)** - GraphRAG integration
- **[Agent System](features/agents/README.md)** - Multi-agent orchestration

---

## 🔍 Search & Navigation

### By Topic

- **Authentication & Authorization**: [Auth Documentation](features/auth/README.md)
- **Database**: [Database Guide](database/README.md)
- **API Integration**: [API Documentation](api/README.md)
- **Background Tasks**: [Celery Documentation](operations/celery.md)
- **Caching**: [Cache Documentation](features/api-caching/README.md)

### By Status

- **✅ Production Ready**: [Production Features](features/README.md#production-ready)
- **🚧 In Development**: [Development Features](features/README.md#in-development)
- **📋 Planned**: [Roadmap](product/roadmap.md)

---

## 📊 Documentation Statistics

- **Total Documents**: 453+ markdown files
- **Main Categories**: 15+ organized sections
- **API Endpoints**: 100+ documented endpoints
- **Features**: 20+ major features documented
- **Last Updated**: December 19, 2025

---

## 🔄 Recent Updates

### December 2025

- ✅ **Refactor Complete**: Directory structure refactored to modular organization
- ✅ **Documentation Updated**: All docs and tests updated to reflect new structure
- ✅ **API Reorganization**: Endpoints reorganized by user type (user/admin/guest)
- ✅ **Enterprise Structure**: Documentation reorganized to enterprise-grade structure

### Key Changes

- **Modular Architecture**: Domain and Application layers now organized by feature modules
- **API Paths**: All endpoints now follow `/api/v1/{user-type}/...` pattern
- **Documentation**: Complete reorganization with clear navigation and indexes

---

## 📞 Support & Contribution

### Getting Help

- **Technical Questions**: See [Developer Guide](developer/README.md)
- **Operations Issues**: See [Operations Guide](operations/README.md)
- **API Questions**: See [API Reference](api/README.md)

### Contributing

- **Code Standards**: [Code Standards Guide](guides/code-standards.md)
- **Documentation Standards**: [Documentation Guide](guides/documentation.md)
- **Pull Request Process**: See project contribution guidelines

---

## 📝 Documentation Maintenance

This documentation is actively maintained. If you find:

- **Outdated Information**: Please update or flag for review
- **Missing Documentation**: Please create or request documentation
- **Broken Links**: Please report or fix broken references
- **Clarifications Needed**: Please suggest improvements

---

**Last Updated**: December 19, 2025  
**Maintained By**: Anvil Backend Team  
**Version**: 2.0.0
