# Technology Stack

## Project Type
Web application backend API service providing conversational AI interface for DeFi multi-agent interactions. The system serves as the backend for a chat-based interface where users interact with specialized AI agents for decentralized finance operations.

## Core Technologies

### Primary Language(s)
- **Language**: Python 3.12
- **Runtime**: CPython 3.12
- **Language-specific tools**: 
  - `uv` for package management and virtual environment management
  - `ruff` for linting and code formatting
  - `mypy` for static type checking
  - `pytest` for testing framework

### Key Dependencies/Libraries
- **FastAPI 0.116.1**: High-performance async web framework for building REST APIs
- **Dishka 1.6.0**: Framework-agnostic dependency injection container
- **SQLAlchemy 2.0.41**: ORM for database operations with async support
- **Alembic 1.12.1**: Database migration tool
- **Pydantic 2.11.7**: Data validation and settings management
- **Celery 5.3.6**: Distributed task queue for background job processing
- **Redis 5.0.1**: In-memory data store for caching and Celery broker
- **PostgreSQL (via psycopg 3.2.9)**: Primary relational database
- **JWT (PyJWT 2.8.0)**: Authentication and session management
- **orjson 3.11.0**: Fast JSON serialization
- **uvicorn 0.35.0**: ASGI server with uvloop support
- **requests 2.31.0**: HTTP client for external API integrations

### Application Architecture
**Hexagonal Architecture (Clean Architecture)** with strict layered separation:
- **Domain Layer**: Core business entities, value objects, and domain services
- **Application Layer**: Use case orchestration via interactors (CQRS pattern)
- **Infrastructure Layer**: Adapters for external systems (database, APIs, messaging)
- **Presentation Layer**: HTTP controllers and request/response models

The architecture follows dependency inversion principles, with inner layers defining ports (interfaces) and outer layers providing adapters (implementations).

### Data Storage
- **Primary storage**: PostgreSQL 13+ for persistent data (conversations, user preferences, agent configurations, transaction history)
- **Caching**: Redis for session storage, rate limiting, and temporary conversation context
- **Data formats**: 
  - JSON for API responses and configuration
  - PostgreSQL JSONB for flexible schema storage (conversation messages, agent state)
  - Protocol Buffers (future consideration) for inter-service communication

### External Integrations
- **DeFi Data APIs**: 
  - DEX aggregators (1inch, 0x, Paraswap) for price and liquidity data
  - DeFiLlama for protocol analytics and yield data
  - The Graph for on-chain data queries
  - CoinGecko/CoinMarketCap for market data
- **Blockchain RPC Providers**: 
  - Infura, Alchemy, QuickNode for multi-chain data access
  - Web3.py for blockchain interactions
- **AI/LLM Services**:
  - OpenAI GPT-4/GPT-3.5 for agent reasoning and responses
  - Anthropic Claude (future consideration) for specialized agents
  - Vector databases (Pinecone, Weaviate) for agent knowledge retrieval
- **Protocols**: HTTP/REST, WebSocket for real-time updates, GraphQL (The Graph)
- **Authentication**: JWT tokens, OAuth 2.0 for third-party wallet connections (WalletConnect, MetaMask)

### Monitoring & Dashboard Technologies
- **Dashboard Framework**: FastAPI admin endpoints + React-based dashboard (future)
- **Real-time Communication**: WebSocket for live conversation updates, Server-Sent Events for metrics streaming
- **Visualization Libraries**: Chart.js for analytics visualization (future frontend)
- **State Management**: Redis for distributed state, PostgreSQL for persistent state

## Development Environment

### Build & Development Tools
- **Build System**: Makefile for common development tasks
- **Package Management**: `uv` for fast Python package management
- **Development workflow**: 
  - Hot reload via uvicorn `--reload` flag
  - Pre-commit hooks for code quality checks
  - Docker Compose for local development environment

### Code Quality Tools
- **Static Analysis**: 
  - `ruff` for linting and formatting (replaces black, isort, flake8)
  - `mypy` for type checking with strict mode
  - `slotscheck` for ensuring proper use of `__slots__`
- **Formatting**: `ruff format` for consistent code style
- **Testing Framework**: 
  - `pytest` with `pytest-asyncio` for async test support
  - `coverage` for test coverage reporting
- **Documentation**: OpenAPI/Swagger auto-generated from FastAPI route definitions

### Version Control & Collaboration
- **VCS**: Git
- **Branching Strategy**: Git Flow or GitHub Flow (to be determined by team)
- **Code Review Process**: Pull request reviews required before merging to main branch

### Dashboard Development (if applicable)
- **Live Reload**: FastAPI auto-reload for backend, Vite HMR for frontend (future)
- **Port Management**: Configurable via TOML configuration files
- **Multi-Instance Support**: Docker Compose supports multiple service instances

## Deployment & Distribution
- **Target Platform(s)**: Cloud platforms (AWS, GCP, Azure) with container orchestration (Kubernetes, ECS)
- **Distribution Method**: Docker containers deployed via CI/CD pipeline
- **Installation Requirements**: 
  - Docker and Docker Compose for local development
  - PostgreSQL 13+ and Redis 6.0+ for production
  - Python 3.12 runtime environment
- **Update Mechanism**: 
  - Automated deployments via GitHub Actions/GitLab CI
  - Blue-green deployments for zero-downtime updates
  - Database migrations via Alembic with rollback capability

## Technical Requirements & Constraints

### Performance Requirements
- **API Response Time**: < 200ms for standard endpoints, < 2s for agent responses
- **Throughput**: Support 1000+ concurrent users, 10,000+ requests per minute
- **Memory Usage**: < 2GB per application instance under normal load
- **Startup Time**: Application should start within 10 seconds
- **Database Query Performance**: < 100ms for 95th percentile queries

### Compatibility Requirements  
- **Platform Support**: 
  - Linux (Ubuntu 20.04+, Debian 11+) for production
  - macOS and Linux for development
- **Dependency Versions**: 
  - Python: Strictly 3.12.* (as specified in pyproject.toml)
  - PostgreSQL: 13+ (tested with 13, 14, 15)
  - Redis: 6.0+ (tested with 6.0, 7.0)
- **Standards Compliance**: 
  - OpenAPI 3.0 for API documentation
  - JWT (RFC 7519) for authentication
  - RESTful API design principles

### Security & Compliance
- **Security Requirements**: 
  - JWT-based authentication with secure session management
  - Input validation and sanitization at all layers
  - Rate limiting to prevent abuse
  - CORS configuration for frontend access
  - SQL injection prevention via SQLAlchemy ORM
  - XSS prevention in API responses
  - Secure handling of wallet connections (read-only access preferred)
- **Compliance Standards**: 
  - GDPR compliance for user data handling
  - SOC 2 Type II (future consideration)
- **Threat Model**: 
  - API abuse and rate limiting attacks
  - Unauthorized access to user conversations and data
  - Injection attacks via user input
  - Man-in-the-middle attacks on external API calls

### Scalability & Reliability
- **Expected Load**: 
  - Initial: 100-500 concurrent users
  - Growth: 5,000+ concurrent users within 6 months
  - Peak: 10,000+ concurrent users during market volatility
- **Availability Requirements**: 
  - 99.9% uptime SLA (target)
  - Automated failover for database and Redis
  - Health check endpoints for load balancer integration
- **Growth Projections**: 
  - Horizontal scaling via container orchestration
  - Database read replicas for query distribution
  - Redis cluster for distributed caching
  - CDN for static assets (future frontend)

## Technical Decisions & Rationale

### Decision Log

1. **FastAPI over Django/Flask**: 
   - **Rationale**: FastAPI provides excellent async support, automatic OpenAPI documentation, and high performance. Better suited for API-first architecture than Django's full-stack approach.
   - **Alternatives Considered**: Django REST Framework, Flask with async extensions
   - **Trade-offs**: Less mature ecosystem than Django, but sufficient for our needs

2. **Dishka over FastAPI Depends**: 
   - **Rationale**: Maintains framework independence, allows easy migration to other frameworks if needed. Prevents coupling business logic to FastAPI-specific features.
   - **Alternatives Considered**: FastAPI's built-in Depends, dependency-injector
   - **Trade-offs**: Slightly more complex setup, but provides better architectural separation

3. **Hexagonal Architecture**: 
   - **Rationale**: Ensures business logic remains independent of infrastructure, making the system testable, maintainable, and adaptable to changing requirements.
   - **Alternatives Considered**: Traditional MVC, microservices architecture
   - **Trade-offs**: More initial complexity, but pays off in long-term maintainability

4. **CQRS Pattern**: 
   - **Rationale**: Separates read and write operations, allowing optimization of each path independently. Critical for performance as the system scales.
   - **Alternatives Considered**: Traditional CRUD pattern
   - **Trade-offs**: More code to maintain, but enables better performance and scalability

5. **PostgreSQL over NoSQL**: 
   - **Rationale**: ACID compliance critical for financial data, excellent JSONB support for flexible schema needs, mature ecosystem, and strong consistency guarantees.
   - **Alternatives Considered**: MongoDB, DynamoDB
   - **Trade-offs**: Less flexible schema, but better for transactional data and complex queries

6. **Celery + Redis for Background Tasks**: 
   - **Rationale**: Proven Python solution for async task processing. Redis provides both message broker and caching capabilities.
   - **Alternatives Considered**: RQ, Dramatiq, AWS SQS + Lambda
   - **Trade-offs**: Requires Redis infrastructure, but provides excellent Python integration and flexibility

## Known Limitations

- **Python GIL**: CPU-intensive agent processing may benefit from multiprocessing or external worker processes
  - **Impact**: May limit concurrent agent processing on single instance
  - **Future Solution**: Consider async multiprocessing or dedicated agent processing services

- **Database Connection Pooling**: Current implementation may need tuning for high concurrency
  - **Impact**: Potential connection exhaustion under heavy load
  - **Future Solution**: Implement connection pool monitoring and dynamic scaling

- **External API Rate Limits**: DeFi data providers may have rate limits affecting real-time data freshness
  - **Impact**: Some data may be slightly stale during high-traffic periods
  - **Future Solution**: Implement intelligent caching and multiple provider fallbacks

- **Agent Response Latency**: LLM API calls can be slow, affecting user experience
  - **Impact**: Users may experience 2-5 second delays for complex agent responses
  - **Future Solution**: Implement streaming responses, response caching, and local model deployment for common queries
