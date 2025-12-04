# Anvil Backend Documentation

Welcome to the Anvil Backend documentation! This comprehensive documentation covers all aspects of the backend system.

## 📚 Quick Navigation

### Main Systems

| System | Status | Documentation |
|--------|--------|---------------|
| **Enterprise Retry System** | ✅ Production | [→ Index](RETRY_SYSTEM_INDEX.md) |
| **LLM Orchestration** | ✅ Production | [→ Features](features/llm-orchestration-docs/) |
| **GraphRAG Integration** | ✅ Production | [→ Specs](specs/) |
| **MCP Servers** | ✅ Production | [→ Infrastructure](infrastructure/) |
| **Agno Agents** | ✅ Production | [→ Features](features/) |

---

## 🚀 Enterprise Retry System

**Status**: ✅ Production Ready (100% Complete)

The enterprise-grade retry system with circuit breakers, telemetry, and admin dashboard.

### Quick Start
- **Overview**: [RETRY_SYSTEM.md](RETRY_SYSTEM.md)
- **Complete Index**: [RETRY_SYSTEM_INDEX.md](RETRY_SYSTEM_INDEX.md)
- **Migration**: [RETRY_SYSTEM_MIGRATION_GUIDE.md](RETRY_SYSTEM_MIGRATION_GUIDE.md)
- **Operations**: [ops/RETRY_SYSTEM_RUNBOOK.md](ops/RETRY_SYSTEM_RUNBOOK.md)

### What It Does
- **Protects 6 MCP Servers**: DeFiLlama, 1inch, The Graph, CoinGecko, Aave, Portfolio
- **Protects 4 Agno Agents**: All agents via DeFiAgentBase
- **Improves Success Rate**: 85% → 98% (+13%)
- **Full Observability**: 4 PostgreSQL tables, 7 admin API endpoints

### Key Features
- ✅ Intelligent retry with exponential backoff
- ✅ Circuit breaker (3-state, Redis-backed)
- ✅ Comprehensive telemetry (PostgreSQL)
- ✅ Admin dashboard (7 API endpoints)
- ✅ Manual intervention (enable/disable services)
- ✅ MCP exception hierarchy
- ✅ 75 integration tests
- ✅ Complete documentation

---

## 📖 Documentation Structure

```
docs/
├── README.md                           # This file
├── RETRY_SYSTEM_INDEX.md              # Retry system documentation index
├── RETRY_SYSTEM.md                    # Main retry system docs
├── RETRY_SYSTEM_ANALYSIS.md           # Original analysis
├── RETRY_SYSTEM_FINAL_SUMMARY.md      # Executive summary
├── RETRY_SYSTEM_MIGRATION_GUIDE.md    # Deployment guide
├── RETRY_IMPLEMENTATION_GUIDE_PHASES_4-7.md
│
├── specs/                             # Technical specifications
│   ├── ENTERPRISE_RETRY_TELEMETRY_SPEC.md
│   └── ...
│
├── features/                          # Feature documentation
│   ├── llm-orchestration-docs/
│   └── ...
│
├── frontend/                          # Frontend integration docs
│   ├── RETRY_ADMIN_DASHBOARD.md
│   └── ...
│
├── ops/                               # Operations documentation
│   ├── RETRY_SYSTEM_RUNBOOK.md
│   └── ...
│
└── infrastructure/                    # Infrastructure docs
    └── ...
```

---

## 🎯 Documentation by Role

### For Developers

**Getting Started**:
1. [Architecture Overview](RETRY_SYSTEM.md#architecture)
2. [Integration Guide](RETRY_SYSTEM.md#integration-with-mcp-servers)
3. [Configuration](RETRY_SYSTEM.md#configuration)
4. [Testing](RETRY_SYSTEM.md#testing)

**Key Documents**:
- [RETRY_SYSTEM.md](RETRY_SYSTEM.md) - Complete developer guide
- [ENTERPRISE_RETRY_TELEMETRY_SPEC.md](specs/ENTERPRISE_RETRY_TELEMETRY_SPEC.md) - Technical spec
- [LLM Orchestration](features/llm-orchestration-docs/) - LLM system docs

### For DevOps/SRE

**Getting Started**:
1. [Migration Guide](RETRY_SYSTEM_MIGRATION_GUIDE.md)
2. [Operations Runbook](ops/RETRY_SYSTEM_RUNBOOK.md)
3. [Monitoring Setup](ops/RETRY_SYSTEM_RUNBOOK.md#monitoring)
4. [Configuration Examples](../config/local/example_retry_config.toml)

**Key Documents**:
- [RETRY_SYSTEM_MIGRATION_GUIDE.md](RETRY_SYSTEM_MIGRATION_GUIDE.md) - Deployment
- [ops/RETRY_SYSTEM_RUNBOOK.md](ops/RETRY_SYSTEM_RUNBOOK.md) - Operations
- [Configuration Guide](RETRY_SYSTEM.md#configuration)

### For Frontend Developers

**Getting Started**:
1. [Admin Dashboard API](frontend/RETRY_ADMIN_DASHBOARD.md)
2. [API Reference](frontend/RETRY_ADMIN_DASHBOARD.md#api-endpoints)
3. [UI Components](frontend/RETRY_ADMIN_DASHBOARD.md#ui-components)
4. [State Management](frontend/RETRY_ADMIN_DASHBOARD.md#state-management)

**Key Documents**:
- [RETRY_ADMIN_DASHBOARD.md](frontend/RETRY_ADMIN_DASHBOARD.md) - Complete API docs
- [Frontend Integration](frontend/) - All frontend docs

### For Management/Stakeholders

**Getting Started**:
1. [Executive Summary](RETRY_SYSTEM_FINAL_SUMMARY.md)
2. [Business Impact](RETRY_SYSTEM_FINAL_SUMMARY.md#business-impact)
3. [Project Status](RETRY_SYSTEM_INDEX.md#implementation-status)

**Key Documents**:
- [RETRY_SYSTEM_FINAL_SUMMARY.md](RETRY_SYSTEM_FINAL_SUMMARY.md) - Executive summary
- [RETRY_SYSTEM_INDEX.md](RETRY_SYSTEM_INDEX.md) - Complete index

---

## 🔍 Find What You Need

### Common Tasks

**I want to...**

- **Deploy the retry system** → [Migration Guide](RETRY_SYSTEM_MIGRATION_GUIDE.md)
- **Monitor services** → [Operations Runbook](ops/RETRY_SYSTEM_RUNBOOK.md)
- **Integrate with retry system** → [Developer Guide](RETRY_SYSTEM.md)
- **Build admin dashboard UI** → [Admin Dashboard API](frontend/RETRY_ADMIN_DASHBOARD.md)
- **Troubleshoot issues** → [Runbook - Common Issues](ops/RETRY_SYSTEM_RUNBOOK.md#common-issues)
- **Understand architecture** → [Architecture](RETRY_SYSTEM.md#architecture)
- **Run tests** → [Testing Guide](RETRY_SYSTEM.md#testing)
- **Configure settings** → [Configuration](RETRY_SYSTEM.md#configuration)

### Search by Topic

**Retry System**:
- [Main Docs](RETRY_SYSTEM.md)
- [Complete Index](RETRY_SYSTEM_INDEX.md)
- [Specification](specs/ENTERPRISE_RETRY_TELEMETRY_SPEC.md)

**Circuit Breaker**:
- [Circuit Breaker Component](RETRY_SYSTEM.md#circuit-breaker)
- [Operations](ops/RETRY_SYSTEM_RUNBOOK.md#issue-2-circuit-breaker-stuck-open)

**Telemetry**:
- [Telemetry System](RETRY_SYSTEM.md#telemetry-infrastructure)
- [Database Schema](RETRY_SYSTEM.md#database-schema)

**Admin Dashboard**:
- [API Reference](frontend/RETRY_ADMIN_DASHBOARD.md)
- [Endpoints](frontend/RETRY_ADMIN_DASHBOARD.md#api-endpoints)

**MCP Servers**:
- [MCP Integration](RETRY_SYSTEM.md#integration-with-mcp-servers)
- [MCP Exceptions](RETRY_SYSTEM.md#error-standardization-phase-6)

**Configuration**:
- [Configuration Guide](RETRY_SYSTEM.md#configuration)
- [Examples](../config/local/example_retry_config.toml)

---

## 📊 Project Statistics

### Enterprise Retry System

**Completion**: 100% (31/31 tasks)

**Code Delivered**:
- New Files: 35
- Modified Files: 12
- Lines of Code: 7,200+
- Integration Tests: 75
- Documentation Files: 9
- Commits: 27

**Business Impact**:
- Success Rate: +13% (85% → 98%)
- Protected Services: 6 MCP servers, 4 agents
- Test Coverage: 75 integration tests
- Production Ready: ✅ Yes

---

## 🛠️ Development

### Running Tests

```bash
# All retry tests
pytest tests/integration/retry/ -v
pytest tests/integration/mcp/ -v
pytest tests/integration/agno/ -v
pytest tests/integration/admin/ -v

# With coverage
pytest tests/integration/retry/ --cov=app.domain.services.retry

# Specific test file
pytest tests/integration/retry/test_retry_engine.py -v
```

### Local Development

```bash
# Setup
export APP_ENV=local
make dotenv
make venv
uv pip install -e '.[dev,test]'

# Database
make up.db
alembic upgrade head

# Run
make start
```

### Configuration

See [Configuration Examples](../config/local/example_retry_config.toml) and [Configuration Guide](RETRY_SYSTEM.md#configuration).

---

## 📞 Support

**Technical Questions**: #backend-team Slack channel  
**Documentation Issues**: Create GitHub issue  
**On-Call Support**: PagerDuty `retry-system-oncall`  
**Code Review**: Backend team leads

---

## 📝 Contributing

When adding new documentation:

1. Follow the existing structure
2. Update the appropriate index files
3. Add links to this README
4. Keep examples up-to-date
5. Include diagrams where helpful

---

## 🔗 External Resources

- **GitHub Repository**: https://github.com/Anvil-com/anvil_backend
- **API Documentation**: https://api.anvil.com/docs
- **Admin Dashboard**: https://admin.anvil.com
- **Status Page**: https://status.anvil.com

---

**Last Updated**: December 1, 2025  
**Maintained By**: Backend Team  
**Contact**: #backend-team
