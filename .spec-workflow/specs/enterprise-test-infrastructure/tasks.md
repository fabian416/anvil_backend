# Tasks Document: Enterprise Test Infrastructure

## Phase 1: Foundation

- [ ] 1. Create test configuration structure
  - Files: `config/test/config.toml`, `config/test/.secrets.toml`, `tests/pytest.ini`
  - Create test-specific TOML configuration with database, Redis, and external API settings
  - Configure pytest with markers, timeouts, and coverage settings
  - Purpose: Establish configuration foundation for isolated test environment
  - _Leverage: `config/local/config.toml`, `tests/conftest.py`_
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_
  - _Prompt: |
      Implement the task for spec enterprise-test-infrastructure, first run spec-workflow-guide to get the workflow guide then implement the task:
      
      Role: DevOps Engineer specializing in Python test infrastructure and configuration management
      
      Task: Create test-specific configuration structure following requirements 5.1-5.5:
      1. Create `config/test/config.toml` with test database settings (port 5433), disabled external APIs, and test-specific parameters
      2. Create `config/test/.secrets.toml.example` with placeholder test secrets
      3. Update `tests/pytest.ini` or `pyproject.toml` [tool.pytest] with markers, coverage config, and timeout settings
      
      Restrictions:
      - Do not modify production configuration files
      - Test database must use different port (5433) than dev (5432)
      - External APIs must be disabled by default in test config
      - Follow existing TOML configuration patterns from `config/local/`
      
      _Leverage: `config/local/config.toml` for structure, `tests/conftest.py` for existing markers
      
      Success:
      - `config/test/config.toml` exists with all required sections
      - pytest can load test configuration via APP_ENV=test
      - All existing test markers are preserved and documented
      
      After completing, mark this task as in-progress in tasks.md by changing [ ] to [-], implement, then log implementation with log-implementation tool, then mark as complete [x]._

- [ ] 2. Create Docker test database setup
  - Files: `tests/docker/docker-compose.test.yml`, `tests/docker/init-test-db.sql`
  - Configure PostgreSQL 15 container for testing on port 5433
  - Create initialization script for test database schema
  - Purpose: Provide isolated, reproducible database for integration tests
  - _Leverage: `config/local/docker-compose.yaml`, `config/local/init-db.sql`_
  - _Requirements: 1.1, 1.2, 1.6_
  - _Prompt: |
      Implement the task for spec enterprise-test-infrastructure, first run spec-workflow-guide to get the workflow guide then implement the task:
      
      Role: DevOps Engineer specializing in Docker and PostgreSQL
      
      Task: Create Docker Compose configuration for test database following requirements 1.1, 1.2, 1.6:
      1. Create `tests/docker/docker-compose.test.yml` with PostgreSQL 15 on port 5433
      2. Configure health checks for container readiness
      3. Create `tests/docker/init-test-db.sql` for initial schema setup
      4. Add volume for data persistence during test session
      
      Restrictions:
      - Must use different port (5433) than development database
      - Container name must be unique (`anvil_test_db`)
      - Do not include production credentials
      - Health check must verify PostgreSQL is accepting connections
      
      _Leverage: `config/local/docker-compose.yaml` for patterns
      
      Success:
      - `docker-compose -f tests/docker/docker-compose.test.yml up -d` starts test database
      - Database accepts connections on localhost:5433
      - Container health check passes within 30 seconds
      
      After completing, mark this task as in-progress in tasks.md, implement, log with log-implementation tool, then mark complete._

- [ ] 3. Implement BaseFactory class
  - File: `tests/fixtures/factories/base.py`
  - Create generic factory pattern with `build()`, `create()`, `create_batch()` methods
  - Support both in-memory and database-persisted entity creation
  - Purpose: Provide foundation for all domain-specific factories
  - _Leverage: `tests/builders/conversation_builder.py`, `tests/helpers/db_manager.py`_
  - _Requirements: 2.1, 2.5, 2.6, 2.7_
  - _Prompt: |
      Implement the task for spec enterprise-test-infrastructure, first run spec-workflow-guide to get the workflow guide then implement the task:
      
      Role: Python Developer specializing in testing patterns and factory design
      
      Task: Create BaseFactory class following requirements 2.1, 2.5, 2.6, 2.7:
      1. Create `tests/fixtures/factories/base.py` with generic `BaseFactory[T]` class
      2. Implement `build(**overrides) -> T` for in-memory entity creation
      3. Implement `create(session, **overrides) -> T` for database persistence
      4. Implement `create_batch(session, count, **overrides) -> list[T]` for bulk creation
      5. Implement `build_dict(**overrides) -> dict` for dictionary output
      6. Add `_defaults` class attribute for default values
      
      Restrictions:
      - Must be generic and work with any SQLAlchemy model
      - Do not hardcode any domain-specific logic
      - Must support async database sessions
      - Follow existing builder patterns from `tests/builders/`
      
      _Leverage: `tests/builders/conversation_builder.py` for builder pattern, `tests/helpers/db_manager.py` for session handling
      
      Success:
      - BaseFactory can be subclassed for any entity type
      - `build()` returns entity without database interaction
      - `create()` persists entity and returns it with ID
      - Type hints work correctly with generic type parameter
      
      After completing, update tasks.md, implement, log with log-implementation tool, mark complete._

---

## Phase 2: Domain Factories

- [ ] 4. Implement UserFactory
  - File: `tests/fixtures/factories/user_factory.py`
  - Create user factory with password hashing and role support
  - Add convenience methods for admin/super_admin creation
  - Purpose: Enable rapid test user creation with proper authentication setup
  - _Leverage: `tests/builders/user_builder.py`, `tests/helpers/auth_helper.py`, `tests/fixtures/factories/base.py`_
  - _Requirements: 2.1, 2.2, 3.1, 3.2, 3.3_
  - _Prompt: |
      Implement the task for spec enterprise-test-infrastructure, first run spec-workflow-guide to get the workflow guide then implement the task:
      
      Role: Python Developer specializing in authentication and test data generation
      
      Task: Create UserFactory following requirements 2.1, 2.2, 3.1, 3.2, 3.3:
      1. Create `tests/fixtures/factories/user_factory.py` extending BaseFactory
      2. Generate unique emails with UUID prefix
      3. Hash passwords using bcrypt (like production)
      4. Support role parameter (user, admin, super_admin)
      5. Add `create_with_session(session) -> tuple[User, AuthSession]` for authenticated users
      6. Add `create_admin(session)` and `create_super_admin(session)` shortcuts
      
      Restrictions:
      - Must use same password hashing as production code
      - Email addresses must be unique per factory call
      - Do not store plain text passwords in created users
      - Must integrate with existing AuthHelper for token generation
      
      _Leverage: `tests/builders/user_builder.py`, `tests/helpers/auth_helper.py`
      
      Success:
      - `UserFactory.create(session)` creates valid user in database
      - `UserFactory.create_with_session(session)` returns user + valid JWT
      - Password verification works with created users
      - Admin/super_admin users have correct role attributes
      
      After completing, update tasks.md, implement, log with log-implementation tool, mark complete._

- [ ] 5. Implement ConversationFactory
  - File: `tests/fixtures/factories/conversation_factory.py`
  - Create conversation factory with optional message generation
  - Support agent session creation
  - Purpose: Enable rapid conversation setup for chat tests
  - _Leverage: `tests/builders/conversation_builder.py`, `tests/builders/message_builder.py`, `tests/fixtures/factories/base.py`_
  - _Requirements: 2.2, 2.3_
  - _Prompt: |
      Implement the task for spec enterprise-test-infrastructure, first run spec-workflow-guide to get the workflow guide then implement the task:
      
      Role: Python Developer specializing in domain-driven design and test data
      
      Task: Create ConversationFactory following requirements 2.2, 2.3:
      1. Create `tests/fixtures/factories/conversation_factory.py` extending BaseFactory
      2. Auto-generate conversation titles if not provided
      3. Implement `create_with_messages(session, user_id, message_count, include_agent_responses)`
      4. Implement `create_with_agent_session(session, user_id, agent_type)`
      5. Support custom message content templates
      
      Restrictions:
      - Must create valid foreign key relationships (user_id)
      - Messages must have proper timestamps (chronological order)
      - Agent sessions must reference valid agent types
      - Do not create orphaned messages
      
      _Leverage: `tests/builders/conversation_builder.py`, `tests/builders/message_builder.py`
      
      Success:
      - `ConversationFactory.create_with_messages(session, user_id, 5)` creates conversation with 5 messages
      - Messages alternate between user and agent roles
      - Agent session is properly linked to conversation
      - All foreign keys are valid
      
      After completing, update tasks.md, implement, log with log-implementation tool, mark complete._

- [ ] 6. Implement SubscriptionFactory
  - File: `tests/fixtures/factories/subscription_factory.py`
  - Create subscription factory for all plan tiers
  - Support various subscription states (active, canceled, past_due)
  - Purpose: Enable payment/subscription flow testing
  - _Leverage: `tests/builders/subscription_builder.py`, `tests/fixtures/factories/base.py`_
  - _Requirements: 2.2, 2.4_
  - _Prompt: |
      Implement the task for spec enterprise-test-infrastructure, first run spec-workflow-guide to get the workflow guide then implement the task:
      
      Role: Python Developer specializing in payment systems and test data
      
      Task: Create SubscriptionFactory following requirements 2.2, 2.4:
      1. Create `tests/fixtures/factories/subscription_factory.py` extending BaseFactory
      2. Support all plan tiers (free, basic, premium, enterprise)
      3. Support all subscription states (active, canceled, past_due, trialing)
      4. Generate realistic Stripe-like IDs (sub_xxx, cus_xxx)
      5. Add `create_active(session, user_id, plan)` shortcut
      6. Add `create_canceled(session, user_id)` shortcut
      
      Restrictions:
      - Subscription IDs must follow Stripe format
      - Period dates must be realistic (start < end)
      - User must exist before creating subscription
      - Do not use real Stripe API
      
      _Leverage: `tests/builders/subscription_builder.py`
      
      Success:
      - `SubscriptionFactory.create_active(session, user_id, "premium")` creates active premium subscription
      - Subscription has valid period dates
      - Stripe-like IDs are properly formatted
      - All subscription states can be created
      
      After completing, update tasks.md, implement, log with log-implementation tool, mark complete._

---

## Phase 3: Mock Services

- [ ] 7. Implement MockStripeClient
  - File: `tests/fixtures/mocks/stripe_mock.py`
  - Create Stripe API mock with call recording
  - Support configurable responses and error injection
  - Purpose: Enable payment testing without real Stripe API
  - _Leverage: `src/app/infrastructure/subscription/handlers/`_
  - _Requirements: 4.1, 4.5, 4.6_
  - _Prompt: |
      Implement the task for spec enterprise-test-infrastructure, first run spec-workflow-guide to get the workflow guide then implement the task:
      
      Role: Python Developer specializing in payment integrations and mocking
      
      Task: Create MockStripeClient following requirements 4.1, 4.5, 4.6:
      1. Create `tests/fixtures/mocks/stripe_mock.py` with MockStripeClient class
      2. Implement `create_customer(**kwargs) -> MockCustomer`
      3. Implement `create_subscription(**kwargs) -> MockSubscription`
      4. Implement `cancel_subscription(subscription_id) -> MockSubscription`
      5. Record all calls in `self.calls: list[MockCall]`
      6. Add `set_response(method, response)` for custom responses
      7. Add `set_error(method, error)` for error injection
      8. Add `assert_called(method, times)` for verification
      
      Restrictions:
      - Must match Stripe API interface signatures
      - Mock responses must have same structure as real Stripe responses
      - Call recording must capture args and kwargs
      - Error injection must raise proper Stripe error types
      
      _Leverage: `src/app/infrastructure/subscription/handlers/` for API patterns
      
      Success:
      - MockStripeClient can replace real Stripe client in tests
      - `mock.create_customer(email="test@example.com")` returns MockCustomer
      - `mock.assert_called("create_customer", times=1)` passes
      - Error injection causes proper exception handling
      
      After completing, update tasks.md, implement, log with log-implementation tool, mark complete._

- [ ] 8. Implement MockMailgunClient
  - File: `tests/fixtures/mocks/mailgun_mock.py`
  - Create email mock that captures sent emails
  - Support assertion methods for email verification
  - Purpose: Enable email testing without sending real emails
  - _Leverage: `src/app/infrastructure/adapters/`_
  - _Requirements: 4.2, 4.5_
  - _Prompt: |
      Implement the task for spec enterprise-test-infrastructure, first run spec-workflow-guide to get the workflow guide then implement the task:
      
      Role: Python Developer specializing in email systems and testing
      
      Task: Create MockMailgunClient following requirements 4.2, 4.5:
      1. Create `tests/fixtures/mocks/mailgun_mock.py` with MockMailgunClient class
      2. Implement `send(to, subject, body, html=None) -> MockEmailResponse`
      3. Store all sent emails in `self.sent_emails: list[MockEmail]`
      4. Implement `get_emails_to(recipient) -> list[MockEmail]`
      5. Implement `get_emails_with_subject(contains) -> list[MockEmail]`
      6. Implement `assert_email_sent(to, subject_contains=None) -> MockEmail`
      7. Implement `clear()` to reset captured emails
      
      Restrictions:
      - Must not make any real HTTP requests
      - Email structure must match real Mailgun responses
      - Assertion methods must provide clear error messages
      - Support both single recipient and list of recipients
      
      _Leverage: Existing email sending patterns in infrastructure
      
      Success:
      - `mock.send("user@example.com", "Welcome", "Hello!")` captures email
      - `mock.assert_email_sent("user@example.com", subject_contains="Welcome")` passes
      - `mock.get_emails_to("user@example.com")` returns list of emails
      - No real emails are sent during tests
      
      After completing, update tasks.md, implement, log with log-implementation tool, mark complete._

- [ ] 9. Implement MockDeFiDataProvider
  - File: `tests/fixtures/mocks/defi_mock.py`
  - Create DeFi data mock for TVL, prices, and yield data
  - Support configurable data fixtures
  - Purpose: Enable DeFi agent testing without external API calls
  - _Leverage: `src/app/infrastructure/adapters/external/`, `tests/conftest.py` (mock fixtures)_
  - _Requirements: 4.3, 4.5, 4.6_
  - _Prompt: |
      Implement the task for spec enterprise-test-infrastructure, first run spec-workflow-guide to get the workflow guide then implement the task:
      
      Role: Python Developer specializing in DeFi integrations and testing
      
      Task: Create MockDeFiDataProvider following requirements 4.3, 4.5, 4.6:
      1. Create `tests/fixtures/mocks/defi_mock.py` with MockDeFiDataProvider class
      2. Implement configurable TVL data: `set_protocol_tvl(protocol, tvl)`
      3. Implement configurable price data: `set_token_price(token, price)`
      4. Implement configurable yield data: `set_yield_pools(protocol, pools)`
      5. Implement async getters: `get_protocol_tvl()`, `get_token_price()`, `get_yield_pools()`
      6. Add default fixture data for common protocols (Aave, Uniswap, Compound)
      7. Support error injection for specific protocols
      
      Restrictions:
      - Must be async-compatible
      - Default data must be realistic (real TVL ranges, prices)
      - Error injection must simulate real API failures
      - Must not make any external HTTP requests
      
      _Leverage: `src/app/infrastructure/adapters/external/`, existing mock fixtures in `tests/conftest.py`
      
      Success:
      - `mock.get_protocol_tvl("aave")` returns configured or default TVL
      - `mock.set_token_price("ETH", 2500.0)` overrides default price
      - Default fixtures include realistic DeFi data
      - Tests can run completely offline
      
      After completing, update tasks.md, implement, log with log-implementation tool, mark complete._

- [ ] 10. Implement MockLLMGateway
  - File: `tests/fixtures/mocks/llm_mock.py`
  - Create LLM mock with configurable responses
  - Support streaming and non-streaming modes
  - Purpose: Enable agent testing without OpenAI API calls
  - _Leverage: `src/app/infrastructure/adapters/ai/`_
  - _Requirements: 4.4, 4.5, 4.6_
  - _Prompt: |
      Implement the task for spec enterprise-test-infrastructure, first run spec-workflow-guide to get the workflow guide then implement the task:
      
      Role: Python Developer specializing in LLM integrations and testing
      
      Task: Create MockLLMGateway following requirements 4.4, 4.5, 4.6:
      1. Create `tests/fixtures/mocks/llm_mock.py` with MockLLMGateway class
      2. Implement `complete(prompt, **kwargs) -> str` for non-streaming
      3. Implement `stream(prompt, **kwargs) -> AsyncIterator[str]` for streaming
      4. Add `set_response(prompt_contains, response)` for conditional responses
      5. Add `set_default_response(response)` for fallback
      6. Record all prompts in `self.prompts: list[str]`
      7. Support latency simulation via `set_latency(seconds)`
      
      Restrictions:
      - Must match LLM gateway interface from domain
      - Streaming must yield chunks like real OpenAI API
      - Must not make any external API calls
      - Support both sync and async interfaces
      
      _Leverage: `src/app/infrastructure/adapters/ai/` for interface patterns
      
      Success:
      - `mock.complete("What is DeFi?")` returns configured response
      - `async for chunk in mock.stream("Explain yield farming"):` yields response chunks
      - `mock.prompts` contains all prompts sent during test
      - Tests run without OpenAI API key
      
      After completing, update tasks.md, implement, log with log-implementation tool, mark complete._

---

## Phase 4: Enhanced Fixtures

- [ ] 11. Enhance conftest.py with factory fixtures
  - File: `tests/conftest.py`
  - Add session-scoped database engine fixture
  - Add function-scoped session with rollback
  - Register all factories as fixtures
  - Purpose: Provide convenient access to factories in all tests
  - _Leverage: `tests/conftest.py`, `tests/fixtures/factories/`_
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_
  - _Prompt: |
      Implement the task for spec enterprise-test-infrastructure, first run spec-workflow-guide to get the workflow guide then implement the task:
      
      Role: Python Developer specializing in pytest fixtures and test architecture
      
      Task: Enhance conftest.py following requirements 6.1-6.5:
      1. Add `@pytest.fixture(scope="session")` for database engine
      2. Add `@pytest.fixture(scope="function")` for session with savepoint rollback
      3. Add factory fixtures: `user_factory`, `conversation_factory`, `subscription_factory`
      4. Add mock fixtures: `mock_stripe`, `mock_mailgun`, `mock_defi`, `mock_llm`
      5. Add `authenticated_user` fixture returning (user, token, headers)
      6. Add `admin_user` and `super_admin_user` fixtures
      7. Ensure proper cleanup in fixture teardown
      
      Restrictions:
      - Session-scoped fixtures must not leak state between tests
      - Function-scoped fixtures must rollback all changes
      - Factory fixtures must receive session fixture as dependency
      - Mock fixtures must be reset between tests
      
      _Leverage: Existing `tests/conftest.py`, new factory classes
      
      Success:
      - `def test_example(user_factory, db_session):` works
      - `def test_auth(authenticated_user):` provides ready-to-use auth
      - Each test runs in isolation with automatic rollback
      - All existing tests continue to pass
      
      After completing, update tasks.md, implement, log with log-implementation tool, mark complete._

- [ ] 12. Implement TestDatabaseManager with migrations
  - File: `tests/helpers/db_manager.py`
  - Enhance with PostgreSQL support and Alembic migration runner
  - Add connection pooling and health checks
  - Purpose: Provide production-like database for integration tests
  - _Leverage: `tests/helpers/db_manager.py`, `src/app/infrastructure/persistence_sqla/`_
  - _Requirements: 1.2, 1.3, 1.4, 1.5_
  - _Prompt: |
      Implement the task for spec enterprise-test-infrastructure, first run spec-workflow-guide to get the workflow guide then implement the task:
      
      Role: Python Developer specializing in database management and SQLAlchemy
      
      Task: Enhance TestDatabaseManager following requirements 1.2, 1.3, 1.4, 1.5:
      1. Add PostgreSQL connection support with asyncpg
      2. Implement `run_migrations()` using Alembic programmatically
      3. Add connection pooling configuration (pool_size=5, max_overflow=10)
      4. Implement `health_check()` to verify database connectivity
      5. Add `create_test_database()` for creating isolated test DB
      6. Add `drop_test_database()` for cleanup
      7. Support both URL-based and config-based connection
      
      Restrictions:
      - Must work with both SQLite (fast tests) and PostgreSQL (integration)
      - Migrations must run in correct order
      - Connection pool must be properly closed on teardown
      - Must not affect non-test databases
      
      _Leverage: `tests/helpers/db_manager.py`, Alembic configuration
      
      Success:
      - `await manager.setup()` creates engine and runs migrations
      - `manager.health_check()` returns True when database is ready
      - Tests can run against PostgreSQL with full schema
      - Cleanup properly disposes all connections
      
      After completing, update tasks.md, implement, log with log-implementation tool, mark complete._

---

## Phase 5: CI/CD Integration

- [ ] 13. Create GitHub Actions test workflow
  - File: `.github/workflows/test.yml`
  - Configure parallel test execution with PostgreSQL service
  - Add coverage reporting and artifact upload
  - Purpose: Automate test execution on every PR
  - _Leverage: `.github/workflows/` existing workflows_
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_
  - _Prompt: |
      Implement the task for spec enterprise-test-infrastructure, first run spec-workflow-guide to get the workflow guide then implement the task:
      
      Role: DevOps Engineer specializing in GitHub Actions and CI/CD
      
      Task: Create GitHub Actions workflow following requirements 8.1-8.5:
      1. Create `.github/workflows/test.yml` with test job
      2. Configure PostgreSQL service container (postgres:15-alpine)
      3. Set up Python 3.12 with uv package manager
      4. Run migrations before tests
      5. Execute tests with `pytest -n 4` for parallel execution
      6. Generate coverage report and upload to Codecov
      7. Cache dependencies between runs
      8. Add retry logic for flaky tests (max 2 retries)
      
      Restrictions:
      - Must use same Python version as production (3.12)
      - Database service must be healthy before tests run
      - Coverage must be uploaded even if some tests fail
      - Workflow must complete within 15 minutes
      
      _Leverage: Existing workflows in `.github/workflows/`
      
      Success:
      - Workflow triggers on push and pull_request
      - Tests run in parallel across 4 workers
      - Coverage report is uploaded to Codecov
      - Failed tests are retried before marking as failed
      
      After completing, update tasks.md, implement, log with log-implementation tool, mark complete._

- [ ] 14. Add Makefile test commands
  - File: `Makefile`
  - Add convenient test commands for local development
  - Support running specific test categories
  - Purpose: Simplify test execution for developers
  - _Leverage: `Makefile` existing commands_
  - _Requirements: 8.1_
  - _Prompt: |
      Implement the task for spec enterprise-test-infrastructure, first run spec-workflow-guide to get the workflow guide then implement the task:
      
      Role: DevOps Engineer specializing in build automation
      
      Task: Add Makefile test commands following requirement 8.1:
      1. Add `test.all` - Run all tests
      2. Add `test.unit` - Run unit tests only (`-m unit`)
      3. Add `test.integration` - Run integration tests (`-m integration`)
      4. Add `test.security` - Run security tests (`-m security`)
      5. Add `test.e2e` - Run end-to-end tests (`-m e2e`)
      6. Add `test.cov` - Run with coverage report
      7. Add `test.cov.html` - Generate HTML coverage report
      8. Add `test.db.up` - Start test database container
      9. Add `test.db.down` - Stop test database container
      10. Add `test.parallel` - Run tests with 4 workers
      
      Restrictions:
      - Commands must use virtual environment Python
      - Must not conflict with existing Makefile targets
      - Coverage commands must output to `htmlcov/` directory
      - Database commands must use test docker-compose file
      
      _Leverage: Existing Makefile patterns
      
      Success:
      - `make test.unit` runs only unit tests
      - `make test.cov.html` generates browsable coverage report
      - `make test.db.up` starts PostgreSQL on port 5433
      - All commands work from project root
      
      After completing, update tasks.md, implement, log with log-implementation tool, mark complete._

---

## Phase 6: Documentation & Validation

- [ ] 15. Create testing documentation
  - File: `docs/testing/TESTING_GUIDE.md`
  - Document all fixtures, factories, and mocks
  - Include examples and best practices
  - Purpose: Enable developers to write effective tests
  - _Leverage: `docs/` existing documentation_
  - _Requirements: All_
  - _Prompt: |
      Implement the task for spec enterprise-test-infrastructure, first run spec-workflow-guide to get the workflow guide then implement the task:
      
      Role: Technical Writer specializing in developer documentation
      
      Task: Create comprehensive testing documentation:
      1. Create `docs/testing/TESTING_GUIDE.md` with:
         - Quick start guide for running tests
         - Factory usage examples (UserFactory, ConversationFactory, etc.)
         - Mock configuration examples
         - Fixture dependency diagram
         - Best practices for test isolation
         - Troubleshooting common issues
      2. Document all pytest markers and their purposes
      3. Include CI/CD integration details
      4. Add coverage requirements and how to check them
      
      Restrictions:
      - Examples must be runnable code
      - Must follow existing documentation style
      - Include both simple and advanced usage patterns
      - Keep examples up to date with implementation
      
      _Leverage: Existing documentation in `docs/`
      
      Success:
      - New developer can run tests within 5 minutes of reading guide
      - All fixtures and factories are documented with examples
      - Troubleshooting section covers common issues
      - Documentation renders correctly in GitHub
      
      After completing, update tasks.md, implement, log with log-implementation tool, mark complete._

- [ ] 16. Fix remaining test failures
  - Files: Various test files
  - Update tests to use new factories and mocks
  - Ensure all 167 failing tests pass
  - Purpose: Achieve 99%+ test pass rate
  - _Leverage: All new test infrastructure, `tests/logs/errors.md`_
  - _Requirements: All_
  - _Prompt: |
      Implement the task for spec enterprise-test-infrastructure, first run spec-workflow-guide to get the workflow guide then implement the task:
      
      Role: QA Engineer specializing in test maintenance and debugging
      
      Task: Fix remaining test failures to achieve 99%+ pass rate:
      1. Review `tests/logs/errors.md` for failure categories
      2. Update integration tests to use new database fixtures
      3. Update authentication tests to use UserFactory
      4. Update subscription tests to use MockStripeClient
      5. Update email tests to use MockMailgunClient
      6. Update agent tests to use MockLLMGateway and MockDeFiDataProvider
      7. Remove or update tests that require external infrastructure
      8. Add appropriate skip markers for tests needing special setup
      
      Restrictions:
      - Do not delete tests without understanding why they fail
      - Prefer fixing tests over skipping them
      - Maintain test coverage while fixing
      - Document any tests that cannot be fixed without infrastructure
      
      _Leverage: All new factories and mocks, error logs
      
      Success:
      - Test pass rate increases from 92.9% to 99%+
      - Failed tests reduced from 167 to <10
      - Errors reduced from 15 to 0
      - All fixes documented in implementation log
      
      After completing, update tasks.md, implement, log with log-implementation tool, mark complete._

- [ ] 17. Run final validation and generate report
  - Files: `tests/logs/final_report.md`
  - Run full test suite with coverage
  - Generate final metrics report
  - Purpose: Validate infrastructure meets all requirements
  - _Leverage: All test infrastructure_
  - _Requirements: All_
  - _Prompt: |
      Implement the task for spec enterprise-test-infrastructure, first run spec-workflow-guide to get the workflow guide then implement the task:
      
      Role: QA Lead specializing in test validation and reporting
      
      Task: Run final validation and generate comprehensive report:
      1. Start test database: `make test.db.up`
      2. Run full test suite: `make test.cov`
      3. Generate HTML coverage report: `make test.cov.html`
      4. Create `tests/logs/final_report.md` with:
         - Total tests: passed/failed/skipped/errors
         - Pass rate percentage
         - Coverage percentage by module
         - Execution time
         - Comparison with initial metrics (before infrastructure)
         - List of any remaining failures with reasons
         - Recommendations for future improvements
      5. Verify all requirements are met
      
      Restrictions:
      - Report must include actual numbers, not estimates
      - Coverage must be measured, not guessed
      - All metrics must be reproducible
      - Report must be committed to repository
      
      _Leverage: All test infrastructure, coverage tools
      
      Success:
      - Pass rate: 99%+ (target met)
      - Coverage: 80%+ (target met)
      - Execution time: <5 minutes with parallelization
      - Report is comprehensive and accurate
      - All requirements validated as complete
      
      After completing, update tasks.md, implement, log with log-implementation tool, mark complete._
