# Quick Reference Guide

**Purpose**: Quick reference for common tasks and information  
**Audience**: All team members

---

## 📚 Reference Index

### Commands

- **[Common Commands](commands.md)** - Frequently used commands
- **[Makefile Commands](makefile.md)** - Makefile shortcuts
- **[Database Commands](database.md)** - Database operations

### Configuration

- **[Configuration Reference](configuration.md)** - Configuration options
- **[Environment Variables](environment-variables.md)** - Environment setup
- **[API Keys](api-keys.md)** - API key configuration

### Troubleshooting

- **[Troubleshooting Guide](troubleshooting.md)** - Common issues
- **[Error Codes](error-codes.md)** - Error code reference
- **[Debugging Tips](debugging.md)** - Debugging techniques

### Code Reference

- **[Import Patterns](import-patterns.md)** - Import examples
- **[Type Hints](type-hints.md)** - Type hint reference
- **[Decorators](decorators.md)** - Common decorators

---

## 🚀 Quick Commands

### Development

```bash
make start              # Start development server
make code.format        # Format code
make code.lint          # Lint code
make code.test          # Run tests
```

### Database

```bash
make up.db              # Start database
make init-db            # Initialize database
alembic upgrade head    # Apply migrations
```

### Services

```bash
make celery.worker      # Start Celery worker
make celery.beat        # Start scheduler
make celery.flower      # Start monitoring
```

---

## 📖 Detailed References

See individual reference guides for complete information:

- **[Commands Reference](commands.md)** - All commands
- **[Configuration Reference](configuration.md)** - All config options
- **[Troubleshooting Guide](troubleshooting.md)** - Common issues

---

**Last Updated**: December 19, 2025

