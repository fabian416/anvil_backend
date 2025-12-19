# Getting Started with Anvil Backend

**Audience**: New developers, team members, and contributors  
**Time to Complete**: 30-60 minutes  
**Prerequisites**: Basic Python knowledge, Git familiarity

---

## 🎯 Quick Start (5 minutes)

### 1. Clone and Setup

```bash
git clone <repository-url>
cd anvil_backend
make venv              # Create virtual environment
make dotenv            # Generate .env files
make clean-install     # Install dependencies
```

### 2. Start Services

```bash
make up.db             # Start PostgreSQL and Redis
make init-db           # Initialize database
make start             # Start FastAPI server (port 8000)
```

### 3. Verify Installation

```bash
curl http://localhost:8000/docs  # OpenAPI documentation
```

---

## 📚 Learning Path

### Step 1: Understand the Architecture (15 min)

1. **[Architecture Overview](../architecture/README.md)** - High-level system design
2. **[Hexagonal Architecture](../architecture/hexagonal-architecture.md)** - Clean architecture patterns
3. **[Project Structure](../steering/structure.md)** - Code organization

### Step 2: Setup Development Environment (20 min)

1. **[Development Setup](setup.md)** - Complete environment setup
2. **[Configuration Guide](../setup/README.md)** - Configuration management
3. **[Database Setup](../database/README.md)** - Database configuration

### Step 3: Explore the Codebase (30 min)

1. **[Developer Guide](../developer/README.md)** - Developer documentation
2. **[Code Standards](../guides/code-standards.md)** - Coding conventions
3. **[Testing Guide](../testing/README.md)** - Testing practices

### Step 4: Build Your First Feature (60 min)

1. **[Feature Development Guide](../guides/feature-development.md)** - How to add features
2. **[API Development](../api/README.md)** - API development guide
3. **[Testing Your Code](../testing/README.md)** - Writing tests

---

## 🛠️ Development Setup

### Prerequisites

- **Python**: 3.12.* (strictly enforced)
- **PostgreSQL**: 13+ (via Docker)
- **Redis**: 6.0+ (via Docker)
- **Git**: Latest version
- **Docker & Docker Compose**: For local services

### Environment Setup

See **[Complete Setup Guide](setup.md)** for detailed instructions.

**Quick Setup**:
```bash
# 1. Set environment
export APP_ENV=local

# 2. Generate configuration
make dotenv

# 3. Create virtual environment
make venv

# 4. Install dependencies
make clean-install

# 5. Start services
make up.db

# 6. Initialize database
make init-db

# 7. Start application
make start
```

---

## 📖 Essential Reading

### Must Read (First Day)

1. **[Architecture Overview](../architecture/README.md)** - Understand the system
2. **[Project Structure](../steering/structure.md)** - Navigate the codebase
3. **[Code Standards](../guides/code-standards.md)** - Follow conventions
4. **[API Reference](../api/README.md)** - Understand the API

### Should Read (First Week)

1. **[Developer Guide](../developer/README.md)** - Complete developer docs
2. **[Testing Guidelines](../testing/README.md)** - Testing practices
3. **[Database Guide](../database/README.md)** - Database operations
4. **[Deployment Guide](../deployment/README.md)** - Deployment process

### Reference (As Needed)

1. **[API Reference](../api/README.md)** - API documentation
2. **[Configuration Reference](../reference/configuration.md)** - Config options
3. **[Troubleshooting Guide](../reference/troubleshooting.md)** - Common issues

---

## 🎓 Learning Resources

### Architecture

- **[Hexagonal Architecture](../architecture/hexagonal-architecture.md)** - Clean architecture patterns
- **[CQRS Pattern](../architecture/cqrs.md)** - Command Query Responsibility Segregation
- **[Dependency Injection](../architecture/dependency-injection.md)** - DI patterns

### Development

- **[Feature Development](../guides/feature-development.md)** - Adding new features
- **[Testing Guide](../testing/README.md)** - Writing tests
- **[Code Review Guide](../guides/code-review.md)** - Code review process

### Operations

- **[Deployment Guide](../deployment/README.md)** - Production deployment
- **[Monitoring Guide](../operations/monitoring.md)** - Monitoring setup
- **[Troubleshooting](../operations/troubleshooting.md)** - Common issues

---

## 🚀 Next Steps

After completing the getting started guide:

1. **Explore Features**: [Features Documentation](../features/README.md)
2. **Read API Docs**: [API Reference](../api/README.md)
3. **Join Development**: [Contributing Guide](../guides/contributing.md)
4. **Ask Questions**: See [Support](../README.md#support--contribution)

---

## ❓ Common Questions

### Q: How do I add a new feature?

**A**: See [Feature Development Guide](../guides/feature-development.md)

### Q: How do I run tests?

**A**: See [Testing Guide](../testing/README.md)

### Q: How do I deploy to production?

**A**: See [Deployment Guide](../deployment/README.md)

### Q: Where do I find API documentation?

**A**: See [API Reference](../api/README.md) or visit `http://localhost:8000/docs`

---

**Need Help?** See [Support & Contribution](../README.md#support--contribution)

