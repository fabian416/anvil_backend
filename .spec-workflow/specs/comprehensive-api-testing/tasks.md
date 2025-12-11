# Tasks Document: Comprehensive API Testing Suite

## Phase 1: Test Infrastructure Foundation

- [x] 1. Create test helper module structure
  - File: tests/helpers/__init__.py
  - Create the helpers module directory structure
  - Export all helper classes and functions
  - Purpose: Establish centralized test utilities module
  - _Leverage: tests/conftest.py, tests/fixtures/_
  - _Requirements: All non-functional requirements_
  - _Prompt: Role: Python Test Architect | Task: Create the test helpers module structure with __init__.py that exports auth_helper, api_client, db_manager, error_validator, and llm_verifier modules | Restrictions: Follow existing project structure, use relative imports | Success: Module is importable, all helpers accessible via tests.helpers_

- [x] 1.1 Create authentication test helper
  - File: tests/helpers/auth_helper.py
  - Implement JWT token generation for test users
  - Create test user with specific roles (user, admin, super_admin)
  - Generate valid auth headers
  - Manage test sessions with proper cleanup
  - Purpose: Provide consistent authentication for all tests
  - _Leverage: tests/fixtures/auth_fixtures.py, tests/builders/user_builder.py, app.infrastructure.auth_
  - _Requirements: REQ-001, REQ-005_
  - _Prompt: Role: Security Test Engineer | Task: Create auth_helper.py with functions create_test_user(role), get_auth_headers(token), create_admin_session(), invalidate_session(session_id) following existing auth patterns | Restrictions: Use actual JWT generation, no hardcoded tokens for integration tests | Success: Can create authenticated users, tokens are valid, sessions can be cleaned up_

- [x] 1.2 Create API test client wrapper
  - File: tests/helpers/api_client.py
  - Implement AuthenticatedClient class wrapping FastAPI TestClient
  - Support login/logout, automatic token refresh
  - Provide as_admin() context switching
  - Handle cookie and header-based auth
  - Purpose: Simplify authenticated API testing
  - _Leverage: fastapi.testclient.TestClient, tests/helpers/auth_helper.py_
  - _Requirements: REQ-001, REQ-002_
  - _Prompt: Role: API Test Engineer | Task: Create AuthenticatedClient class with login(), logout(), get(), post(), put(), patch(), delete() methods and as_admin() context manager | Restrictions: Must support both Bearer token and cookie auth | Success: Client maintains session state, can switch roles, handles auth errors gracefully_

- [x] 1.3 Create database test manager
  - File: tests/helpers/db_manager.py
  - Implement async database session management
  - Provide transaction rollback for test isolation
  - Support test data seeding
  - Handle cleanup between tests
  - Purpose: Ensure test database isolation and consistency
  - _Leverage: tests/fixtures/database_fixtures.py, app.infrastructure.persistence_sqla_
  - _Requirements: Non-functional (Reliability)_
  - _Prompt: Role: Database Test Engineer | Task: Create DatabaseTestManager with setup_test_db(), rollback_transaction(), seed_test_data(fixtures), cleanup() methods using SQLAlchemy async sessions | Restrictions: Must use transaction rollback, not DELETE statements | Success: Tests are isolated, no data leaks between tests, cleanup is automatic_

- [x] 1.4 Create error response validator
  - File: tests/helpers/error_validator.py
  - Implement standardized error response validation
  - Verify error codes match expected values
  - Validate i18n keys exist
  - Check HTTP status code alignment
  - Purpose: Ensure consistent error handling across all endpoints
  - _Leverage: app.domain.exceptions.error_codes, app.presentation.http.errors_
  - _Requirements: REQ-015_
  - _Prompt: Role: QA Engineer | Task: Create validate_error_response(response, expected_code), validate_i18n_key(error), validate_http_status_match(error, status) functions following error_codes module | Restrictions: Must validate all error fields, use standardized format | Success: All error responses validated, i18n keys verified, status codes match_

- [x] 1.5 Create LLM response verifier
  - File: tests/helpers/llm_verifier.py
  - Implement response structure validation
  - Check content relevance to queries
  - Verify risk disclaimers for financial advice
  - Validate DeFi data formatting
  - Purpose: Ensure LLM responses meet quality standards
  - _Leverage: app.domain.entities.message, app.domain.value_objects.agent_type_
  - _Requirements: REQ-004_
  - _Prompt: Role: AI/ML Test Engineer | Task: Create verify_response_structure(response), verify_content_relevance(query, response), verify_risk_disclaimers(response), verify_defi_data_format(data) functions | Restrictions: Must be deterministic, use pattern matching for relevance | Success: LLM responses validated for structure, content quality, safety_

## Phase 2: Test Data Builders Enhancement

- [x] 2. Enhance conversation builder
  - File: tests/builders/conversation_builder.py
  - Add support for conversation with messages
  - Support different agent types
  - Add build_entity() method for domain objects
  - Purpose: Streamline conversation test data creation
  - _Leverage: tests/builders/user_builder.py patterns_
  - _Requirements: REQ-003_
  - _Prompt: Role: Test Data Engineer | Task: Enhance ConversationBuilder with with_messages(count), with_agent_type(type), with_user(user_id), build_dict(), build_entity() methods | Restrictions: Follow existing builder patterns | Success: Can create conversations with messages, supports all agent types_

- [x] 2.1 Enhance message builder
  - File: tests/builders/message_builder.py
  - Add support for different message roles
  - Support agent responses with metadata
  - Add LLM content templates
  - Purpose: Create realistic message test data
  - _Leverage: tests/builders/conversation_builder.py_
  - _Requirements: REQ-003, REQ-004_
  - _Prompt: Role: Test Data Engineer | Task: Enhance MessageBuilder with with_role(role), with_agent_type(type), with_content(content), with_llm_response(), build_dict(), build_entity() methods | Restrictions: Support all MessageRole values | Success: Can create messages for all roles, LLM responses are realistic_

- [x] 2.2 Create subscription builder
  - File: tests/builders/subscription_builder.py
  - Build subscription plan test data
  - Support different plan tiers
  - Add payment status scenarios
  - Purpose: Simplify subscription testing
  - _Leverage: tests/builders/user_builder.py patterns_
  - _Requirements: REQ-007_
  - _Prompt: Role: Test Data Engineer | Task: Create SubscriptionBuilder with with_plan(tier), with_status(status), with_payment_method(), for_user(user_id), build_dict() methods | Restrictions: Follow existing builder patterns | Success: Can create subscriptions for all plan types and payment states_

- [x] 2.3 Create error test case builder
  - File: tests/builders/error_test_case_builder.py
  - Build error scenario test cases
  - Support parametrized error testing
  - Include expected error codes and messages
  - Purpose: Standardize error scenario testing
  - _Leverage: app.domain.exceptions.error_codes_
  - _Requirements: REQ-015_
  - _Prompt: Role: Test Data Engineer | Task: Create ErrorTestCaseBuilder with for_endpoint(path), with_method(method), with_request_data(data), expecting_error(code), expecting_status(status), build() methods | Restrictions: Must support all error codes | Success: Can generate comprehensive error test cases_

## Phase 3: Authentication Tests

- [x] 3. Create auth unit tests
  - File: tests/unit/presentation/account/test_auth_controllers.py
  - Test signup, login, logout controllers in isolation
  - Mock all dependencies
  - Test request validation
  - Purpose: Verify auth controller logic
  - _Leverage: tests/helpers/auth_helper.py, tests/builders/user_builder.py_
  - _Requirements: REQ-001_
  - _Prompt: Role: Unit Test Engineer | Task: Create unit tests for SignUpController, LogInController, LogOutController with mocked interactors, testing valid/invalid inputs | Restrictions: No database access, mock all dependencies | Success: All controllers tested, validation logic verified_

- [x] 3.1 Create auth integration tests - registration flow
  - File: tests/integration/auth/test_registration_flow.py
  - Test complete registration flow with database
  - Verify email verification process
  - Test duplicate email handling
  - Test password strength validation
  - Purpose: Verify registration works end-to-end
  - _Leverage: tests/helpers/api_client.py, tests/helpers/db_manager.py_
  - _Requirements: REQ-001 (AC 1, 7, 8)_
  - _Prompt: Role: Integration Test Engineer | Task: Create tests for POST /signup flow including email verification, testing success and all failure scenarios | Restrictions: Use real database with transaction rollback | Success: Registration flow tested, email verification works, errors handled_

- [x] 3.2 Create auth integration tests - login flow
  - File: tests/integration/auth/test_login_flow.py
  - Test valid credentials return tokens
  - Test invalid credentials return AUTH_001
  - Test inactive account handling
  - Test blocked account handling
  - Purpose: Verify login works correctly
  - _Leverage: tests/helpers/api_client.py, tests/helpers/error_validator.py_
  - _Requirements: REQ-001 (AC 2, 3, 6)_
  - _Prompt: Role: Integration Test Engineer | Task: Create tests for POST /login flow testing valid credentials, invalid password, invalid email, inactive user, blocked user | Restrictions: Use seeded test users | Success: All login scenarios covered, correct error codes returned_

- [x] 3.3 Create auth integration tests - token refresh
  - File: tests/integration/auth/test_token_refresh_flow.py
  - Test valid refresh token returns new access token
  - Test expired refresh token handling
  - Test invalid refresh token handling
  - Test session invalidation after refresh
  - Purpose: Verify token refresh mechanism
  - _Leverage: tests/helpers/auth_helper.py_
  - _Requirements: REQ-001 (AC 4)_
  - _Prompt: Role: Integration Test Engineer | Task: Create tests for POST /refresh-token flow testing valid refresh, expired refresh, invalid refresh, session management | Restrictions: Test actual token expiry | Success: Refresh flow works, expired tokens rejected, sessions managed correctly_

- [x] 3.4 Create auth integration tests - password reset
  - File: tests/integration/auth/test_password_reset_flow.py
  - Test password reset request
  - Test password reset confirmation
  - Test invalid/expired reset tokens
  - Purpose: Verify password reset works
  - _Leverage: tests/helpers/api_client.py_
  - _Requirements: REQ-001 (AC 7)_
  - _Prompt: Role: Integration Test Engineer | Task: Create tests for POST /password-reset/request and /confirm flows testing valid requests, invalid tokens, expired tokens | Restrictions: Mock email sending | Success: Password reset flow complete, all error scenarios handled_

- [x] 3.5 Create auth integration tests - logout
  - File: tests/integration/auth/test_logout_flow.py
  - Test logout invalidates session
  - Test token cannot be used after logout
  - Test multiple device logout handling
  - Purpose: Verify logout security
  - _Leverage: tests/helpers/auth_helper.py, tests/helpers/api_client.py_
  - _Requirements: REQ-001 (AC 5)_
  - _Prompt: Role: Integration Test Engineer | Task: Create tests for DELETE /logout flow testing session invalidation, token reuse prevention, multi-device scenarios | Restrictions: Verify session storage state | Success: Logout invalidates all sessions, tokens rejected after logout_

## Phase 4: User Profile Tests

- [x] 4. Create user profile unit tests
  - File: tests/unit/presentation/account/test_user_profile_controllers.py
  - Test GET /me controller
  - Test PUT /me controller
  - Test PUT /password controller
  - Purpose: Verify user profile controller logic
  - _Leverage: tests/helpers/auth_helper.py_
  - _Requirements: REQ-002_
  - _Prompt: Role: Unit Test Engineer | Task: Create unit tests for MeController, ChangePasswordController with mocked dependencies | Restrictions: No database access | Success: Controllers tested in isolation_

- [x] 4.1 Create user profile integration tests
  - File: tests/integration/user/test_profile_management.py
  - Test get current user profile
  - Test update profile with valid data
  - Test update profile with invalid data
  - Test password change success
  - Test password change with wrong current password
  - Test password change with same password (USER_014)
  - Purpose: Verify profile management works
  - _Leverage: tests/helpers/api_client.py, tests/helpers/error_validator.py_
  - _Requirements: REQ-002 (AC 1-5)_
  - _Prompt: Role: Integration Test Engineer | Task: Create integration tests for /me GET, PUT and /password PUT endpoints covering all acceptance criteria | Restrictions: Use authenticated client | Success: All profile operations tested, correct error codes for failures_

## Phase 5: Chat Conversation Tests

- [x] 5. Create chat unit tests
  - File: tests/unit/presentation/chat/test_chat_controllers.py
  - Test conversation creation controller
  - Test message sending controller
  - Test conversation listing controller
  - Purpose: Verify chat controller logic
  - _Leverage: tests/builders/conversation_builder.py, tests/builders/message_builder.py_
  - _Requirements: REQ-003_
  - _Prompt: Role: Unit Test Engineer | Task: Create unit tests for chat controllers with mocked interactors testing request validation and response formatting | Restrictions: No database or LLM access | Success: Controllers handle all request variations_

- [x] 5.1 Create chat integration tests - conversation lifecycle
  - File: tests/integration/chat/test_conversation_lifecycle.py
  - Test create conversation returns ID
  - Test list conversations with pagination
  - Test get conversation by ID
  - Test conversation not found (CHAT_001)
  - Purpose: Verify conversation CRUD operations
  - _Leverage: tests/helpers/api_client.py, tests/helpers/db_manager.py_
  - _Requirements: REQ-003 (AC 1, 4, 6)_
  - _Prompt: Role: Integration Test Engineer | Task: Create tests for POST /conversations, GET /conversations, GET /conversations/{id} with pagination and error scenarios | Restrictions: Test real database operations | Success: Conversation lifecycle complete, pagination works, errors handled_

- [x] 5.2 Create chat integration tests - message handling
  - File: tests/integration/chat/test_message_handling.py
  - Test send message routes to agent
  - Test empty message returns CHAT_003
  - Test message history in order
  - Test agent response structure
  - Purpose: Verify message handling works
  - _Leverage: tests/helpers/api_client.py, tests/helpers/llm_verifier.py_
  - _Requirements: REQ-003 (AC 2, 3, 5, 7)_
  - _Prompt: Role: Integration Test Engineer | Task: Create tests for POST /conversations/{id}/messages testing agent routing, message validation, history ordering | Restrictions: Mock LLM provider | Success: Messages processed correctly, agent routing works, errors validated_

- [x] 5.3 Create LLM response verification tests
  - File: tests/integration/chat/test_llm_response_verification.py
  - Test response structure validation
  - Test content relevance to queries
  - Test DeFi data formatting
  - Test risk disclaimer presence
  - Test provider unavailable (LLM_003)
  - Test token limit truncation
  - Purpose: Verify LLM responses meet quality standards
  - _Leverage: tests/helpers/llm_verifier.py, tests/fixtures/mock_services.py_
  - _Requirements: REQ-004 (AC 1-5)_
  - _Prompt: Role: AI/ML Test Engineer | Task: Create tests for LLM response quality including structure, relevance, formatting, disclaimers, error handling | Restrictions: Use mock LLM with controlled responses | Success: All response quality criteria verified_

## Phase 6: Admin User Management Tests

- [x] 6. Create admin user unit tests
  - File: tests/unit/presentation/admin/test_user_management_controllers.py
  - Test list users controller
  - Test grant/revoke admin controllers
  - Test activate/deactivate controllers
  - Test change password controller
  - Purpose: Verify admin controller logic
  - _Leverage: tests/builders/user_builder.py_
  - _Requirements: REQ-005_
  - _Prompt: Role: Unit Test Engineer | Task: Create unit tests for admin user controllers with mocked interactors | Restrictions: No database access | Success: All admin controllers tested_

- [x] 6.1 Create admin user integration tests - user listing
  - File: tests/integration/admin/test_user_listing.py
  - Test list users with pagination
  - Test list users with filters
  - Test non-admin access denied (403)
  - Purpose: Verify user listing for admins
  - _Leverage: tests/helpers/api_client.py_
  - _Requirements: REQ-005 (AC 1, 6)_
  - _Prompt: Role: Integration Test Engineer | Task: Create tests for GET /admin/users with pagination, filtering, and authorization checks | Restrictions: Test with admin and non-admin users | Success: Listing works for admins, denied for non-admins_

- [x] 6.2 Create admin user integration tests - role management
  - File: tests/integration/admin/test_role_management.py
  - Test grant admin role
  - Test revoke admin role
  - Test cannot revoke super admin
  - Test non-admin cannot grant roles
  - Purpose: Verify role management works
  - _Leverage: tests/helpers/api_client.py, tests/helpers/error_validator.py_
  - _Requirements: REQ-005 (AC 2, 3, 6)_
  - _Prompt: Role: Integration Test Engineer | Task: Create tests for PATCH /admin/users/{email}/grant-admin and /revoke-admin with authorization scenarios | Restrictions: Test role boundaries | Success: Roles managed correctly, super admin protected_

- [x] 6.3 Create admin user integration tests - user status
  - File: tests/integration/admin/test_user_status.py
  - Test activate user
  - Test deactivate user
  - Test admin password change
  - Purpose: Verify user status management
  - _Leverage: tests/helpers/api_client.py_
  - _Requirements: REQ-005 (AC 4, 5, 7)_
  - _Prompt: Role: Integration Test Engineer | Task: Create tests for PATCH /admin/users/{email}/activate, /deactivate, and /password endpoints | Restrictions: Verify status changes persist | Success: User status management complete_

## Phase 7: Admin LLM Management Tests

- [x] 7. Create admin LLM unit tests
  - File: tests/unit/presentation/admin/test_llm_management_controllers.py
  - Test providers controller
  - Test models controller
  - Test ranking controller
  - Purpose: Verify LLM admin controller logic
  - _Leverage: tests/fixtures/mock_services.py_
  - _Requirements: REQ-006_
  - _Prompt: Role: Unit Test Engineer | Task: Create unit tests for LLM admin controllers with mocked LLM services | Restrictions: No external API calls | Success: All LLM controllers tested_

- [x] 7.1 Create admin LLM integration tests
  - File: tests/integration/admin/test_llm_configuration.py
  - Test list providers
  - Test provider health check
  - Test list models
  - Test enable/disable model
  - Test update carousel order
  - Purpose: Verify LLM configuration management
  - _Leverage: tests/helpers/api_client.py_
  - _Requirements: REQ-006 (AC 1-6)_
  - _Prompt: Role: Integration Test Engineer | Task: Create tests for /admin/llm/providers, /models, /ranking endpoints with admin authorization | Restrictions: Mock external LLM providers | Success: LLM configuration fully tested_

## Phase 8: Subscription Tests

- [x] 8. Create subscription unit tests
  - File: tests/unit/presentation/subscription/test_subscription_controllers.py
  - Test list subscriptions controller
  - Test create subscription controller
  - Test cancel subscription controller
  - Purpose: Verify subscription controller logic
  - _Leverage: tests/builders/subscription_builder.py_
  - _Requirements: REQ-007_
  - _Prompt: Role: Unit Test Engineer | Task: Create unit tests for subscription controllers with mocked Stripe interactions | Restrictions: No external API calls | Success: Subscription controllers tested_

- [x] 8.1 Create subscription integration tests
  - File: tests/integration/subscription/test_subscription_lifecycle.py
  - Test list available plans
  - Test create subscription initiates payment
  - Test subscription success callback
  - Test cancel subscription
  - Test payment failure (SUB_002)
  - Test subscription not found (SUB_001)
  - Purpose: Verify subscription lifecycle
  - _Leverage: tests/helpers/api_client.py, tests/helpers/error_validator.py_
  - _Requirements: REQ-007 (AC 1-6)_
  - _Prompt: Role: Integration Test Engineer | Task: Create tests for /subscription endpoints covering full payment lifecycle with mocked Stripe | Restrictions: Mock Stripe API | Success: Full subscription lifecycle tested_

## Phase 9: Wallet Tests

- [x] 9. Create wallet unit tests
  - File: tests/unit/presentation/wallet/test_wallet_controllers.py
  - Test export wallet controller
  - Test wallet balance controller
  - Purpose: Verify wallet controller logic
  - _Leverage: tests/fixtures/mock_services.py_
  - _Requirements: REQ-008_
  - _Prompt: Role: Unit Test Engineer | Task: Create unit tests for wallet controllers with mocked wallet services | Restrictions: No external calls | Success: Wallet controllers tested_

- [x] 9.1 Create wallet integration tests
  - File: tests/integration/wallet/test_wallet_operations.py
  - Test wallet export returns encrypted key
  - Test wallet not found (WALLET_001)
  - Test wallet balance retrieval
  - Test insufficient balance (WALLET_002)
  - Purpose: Verify wallet operations
  - _Leverage: tests/helpers/api_client.py, tests/helpers/error_validator.py_
  - _Requirements: REQ-008 (AC 1-4)_
  - _Prompt: Role: Integration Test Engineer | Task: Create tests for /wallet endpoints covering export and balance operations | Restrictions: Mock blockchain interactions | Success: Wallet operations fully tested_

## Phase 10: GraphRAG Search Tests

- [x] 10. Create GraphRAG unit tests
  - File: tests/unit/presentation/graph/test_search_controllers.py
  - Test hybrid search controller
  - Test similar protocols controller
  - Test contextual search controller
  - Purpose: Verify search controller logic
  - _Leverage: tests/fixtures/graphrag_fixtures.py_
  - _Requirements: REQ-011_
  - _Prompt: Role: Unit Test Engineer | Task: Create unit tests for GraphRAG search controllers with mocked search services | Restrictions: No database access | Success: Search controllers tested_

- [x] 10.1 Create GraphRAG integration tests
  - File: tests/integration/graph/test_search_operations.py
  - Test hybrid search returns results
  - Test similar protocols listing
  - Test contextual search with filters
  - Test empty query (SEARCH_001)
  - Purpose: Verify search functionality
  - _Leverage: tests/helpers/api_client.py, tests/fixtures/graphrag_fixtures.py_
  - _Requirements: REQ-011 (AC 1-4)_
  - _Prompt: Role: Integration Test Engineer | Task: Create tests for /graph/search endpoints covering all search types and error scenarios | Restrictions: Use seeded test data | Success: All search operations tested_

## Phase 11: ML Prediction Tests

- [x] 11. Create ML unit tests
  - File: tests/unit/presentation/ml/test_prediction_controllers.py
  - Test risk prediction controller
  - Test batch prediction controller
  - Test anomaly detection controller
  - Test risk forecast controller
  - Purpose: Verify ML controller logic
  - _Leverage: tests/fixtures/ml_fixtures.py_
  - _Requirements: REQ-012_
  - _Prompt: Role: Unit Test Engineer | Task: Create unit tests for ML prediction controllers with mocked ML services | Restrictions: No ML model inference | Success: All ML controllers tested_

- [x] 11.1 Create ML integration tests
  - File: tests/integration/ml/test_prediction_operations.py
  - Test risk prediction returns result
  - Test batch predictions
  - Test anomaly detection
  - Test risk forecast generation
  - Test protocol not found (SEARCH_002)
  - Purpose: Verify ML predictions work
  - _Leverage: tests/helpers/api_client.py, tests/fixtures/ml_fixtures.py_
  - _Requirements: REQ-012 (AC 1-5)_
  - _Prompt: Role: Integration Test Engineer | Task: Create tests for /ml/prediction endpoints covering all prediction types | Restrictions: Use mock ML models | Success: All ML predictions tested_

## Phase 12: WebSocket Tests

- [x] 12. Create WebSocket unit tests
  - File: tests/unit/presentation/websocket/test_websocket_handlers.py
  - Test connection handler
  - Test message handler
  - Test disconnection cleanup
  - Purpose: Verify WebSocket handler logic
  - _Leverage: tests/fixtures/mock_services.py_
  - _Requirements: REQ-014_
  - _Prompt: Role: Unit Test Engineer | Task: Create unit tests for WebSocket handlers with mocked connections | Restrictions: No actual WebSocket connections | Success: Handlers tested in isolation_

- [x] 12.1 Create WebSocket integration tests
  - File: tests/integration/websocket/test_websocket_realtime.py
  - Test WebSocket connection establishment
  - Test real-time message delivery
  - Test reconnection after disconnect
  - Test unauthorized connection rejection
  - Purpose: Verify WebSocket real-time functionality
  - _Leverage: tests/helpers/auth_helper.py_
  - _Requirements: REQ-014 (AC 1-4)_
  - _Prompt: Role: Integration Test Engineer | Task: Create tests for WebSocket /ws/chat endpoint covering connection lifecycle and real-time messaging | Restrictions: Use websocket test client | Success: WebSocket fully functional_

## Phase 13: Error Handling Verification

- [x] 13. Create error handling unit tests
  - File: tests/unit/presentation/errors/test_error_translators.py
  - Test all error translators
  - Verify error code mapping
  - Verify i18n key generation
  - Purpose: Verify error translation logic
  - _Leverage: app.presentation.http.errors.translators_
  - _Requirements: REQ-015_
  - _Prompt: Role: Unit Test Engineer | Task: Create unit tests for all error translators verifying code mapping and i18n keys | Restrictions: Test all error codes | Success: All translators produce correct output_

- [x] 13.1 Create error handling integration tests
  - File: tests/integration/errors/test_error_responses.py
  - Test all error responses follow format
  - Test i18n keys are valid
  - Test HTTP status codes match
  - Test validation errors include fields
  - Purpose: Verify error handling consistency
  - _Leverage: tests/helpers/error_validator.py, tests/builders/error_test_case_builder.py_
  - _Requirements: REQ-015 (AC 1-4)_
  - _Prompt: Role: Integration Test Engineer | Task: Create integration tests triggering all error scenarios and validating response format | Restrictions: Cover all error codes | Success: All errors follow standardized format_

## Phase 14: End-to-End Tests

- [x] 14. Create E2E new user journey test
  - File: tests/e2e/user/test_new_user_journey.py
  - Test complete signup → verify → login → chat → response flow
  - Test with real database and minimal mocking
  - Verify all steps complete successfully
  - Purpose: Verify complete user onboarding
  - _Leverage: tests/helpers/api_client.py, tests/helpers/db_manager.py_
  - _Requirements: REQ-001, REQ-003_
  - _Prompt: Role: E2E Test Engineer | Task: Create end-to-end test for new user journey from signup through first chat interaction | Restrictions: Minimal mocking, real flows | Success: New user can complete entire journey_

- [x] 14.1 Create E2E admin workflow test
  - File: tests/e2e/admin/test_admin_workflow.py
  - Test admin login → list users → manage roles → configure LLM
  - Test with real database
  - Purpose: Verify admin capabilities
  - _Leverage: tests/helpers/api_client.py_
  - _Requirements: REQ-005, REQ-006_
  - _Prompt: Role: E2E Test Engineer | Task: Create end-to-end test for admin workflow including user management and LLM configuration | Restrictions: Minimal mocking | Success: Admin can complete all management tasks_

- [x] 14.2 Create E2E subscription workflow test
  - File: tests/e2e/subscription/test_subscription_workflow.py
  - Test login → view plans → subscribe → access premium → cancel
  - Mock only Stripe API
  - Purpose: Verify subscription journey
  - _Leverage: tests/helpers/api_client.py_
  - _Requirements: REQ-007_
  - _Prompt: Role: E2E Test Engineer | Task: Create end-to-end test for subscription workflow from plan selection through cancellation | Restrictions: Mock Stripe only | Success: Subscription lifecycle complete_

## Phase 15: Security Tests

- [x] 15. Create authentication security tests
  - File: tests/security/auth/test_auth_security.py
  - Test authentication bypass attempts
  - Test token manipulation
  - Test session hijacking prevention
  - Test brute force protection
  - Purpose: Verify authentication security
  - _Leverage: tests/helpers/auth_helper.py_
  - _Requirements: REQ-001 security aspects_
  - _Prompt: Role: Security Test Engineer | Task: Create security tests for authentication including bypass attempts, token tampering, session security | Restrictions: Follow OWASP guidelines | Success: All auth attacks prevented_

- [x] 15.1 Create authorization boundary tests
  - File: tests/security/admin/test_authorization_boundaries.py
  - Test user cannot access admin endpoints
  - Test admin cannot access super admin endpoints
  - Test horizontal privilege escalation prevention
  - Purpose: Verify authorization boundaries
  - _Leverage: tests/helpers/api_client.py_
  - _Requirements: REQ-005 (AC 6)_
  - _Prompt: Role: Security Test Engineer | Task: Create tests for authorization boundaries between user roles and privilege escalation attempts | Restrictions: Test all role combinations | Success: Authorization boundaries enforced_

- [x] 15.2 Create input validation security tests
  - File: tests/security/validation/test_input_security.py
  - Test SQL injection prevention
  - Test XSS prevention
  - Test path traversal prevention
  - Test command injection prevention
  - Purpose: Verify input validation security
  - _Leverage: tests/helpers/api_client.py_
  - _Requirements: Non-functional (Security)_
  - _Prompt: Role: Security Test Engineer | Task: Create tests for input validation security including SQL injection, XSS, path traversal, command injection | Restrictions: Follow OWASP testing guide | Success: All injection attacks prevented_

## Phase 16: Load Tests

- [x] 16. Create load test scenarios
  - File: tests/load/test_api_load.py
  - Test concurrent user authentication
  - Test chat message throughput
  - Test admin operations under load
  - Purpose: Verify system handles load
  - _Leverage: tests/performance/locustfile.py patterns_
  - _Requirements: Non-functional (Performance)_
  - _Prompt: Role: Performance Test Engineer | Task: Create load tests for critical endpoints using locust or pytest-benchmark | Restrictions: Use realistic scenarios | Success: System handles expected concurrent users_

## Phase 17: Test Configuration and CI Integration

- [x] 17. Update pytest configuration
  - File: tests/conftest.py
  - Add new markers for test categories
  - Configure async test fixtures
  - Set up test database configuration
  - Purpose: Complete test configuration
  - _Leverage: existing tests/conftest.py_
  - _Requirements: All_
  - _Prompt: Role: Test Infrastructure Engineer | Task: Update conftest.py with markers (auth, chat, admin, subscription, graphrag, ml, websocket, security, load), async fixtures, database config | Restrictions: Maintain backward compatibility | Success: All tests can be filtered and run by category_

- [x] 17.1 Create test CI configuration
  - File: .github/workflows/test.yml
  - Configure parallel test execution
  - Set up test coverage reporting
  - Add test result artifacts
  - Purpose: Enable CI/CD testing
  - _Leverage: existing .github/workflows/_
  - _Requirements: Non-functional (Usability)_
  - _Prompt: Role: DevOps Engineer | Task: Create GitHub Actions workflow for running tests with parallel execution, coverage reporting, and artifact collection | Restrictions: Use existing CI patterns | Success: Tests run on all PRs, coverage reported_

- [x] 17.2 Create test documentation
  - File: docs/testing/TESTING_GUIDE.md
  - Document test categories and markers
  - Explain running tests locally
  - Document CI/CD integration
  - Document test data management
  - Purpose: Enable team test contribution
  - _Leverage: existing docs/ structure_
  - _Requirements: Non-functional (Usability)_
  - _Prompt: Role: Technical Writer | Task: Create comprehensive testing guide documenting test structure, markers, local execution, CI integration, and data management | Restrictions: Follow existing doc style | Success: New developers can run and write tests_
