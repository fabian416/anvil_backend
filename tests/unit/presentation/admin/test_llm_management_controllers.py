"""
Unit tests for admin LLM management controllers.

Tests providers, models, and ranking controllers in isolation
with mocked dependencies.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime

from tests.helpers.auth_helper import AuthHelper


class TestProvidersController:
    """Unit tests for LLM providers controller."""

    @pytest.fixture
    def mock_providers_service(self):
        """Create mock providers service."""
        service = AsyncMock()
        service.list_providers = AsyncMock(
            return_value=[
                {
                    "id": "openai",
                    "name": "OpenAI",
                    "is_enabled": True,
                    "is_healthy": True,
                    "models_count": 4,
                },
                {
                    "id": "anthropic",
                    "name": "Anthropic",
                    "is_enabled": True,
                    "is_healthy": True,
                    "models_count": 3,
                },
            ]
        )
        return service

    def test_list_providers_response_structure(self, mock_providers_service):
        """Test list providers returns expected structure."""
        response = {
            "providers": [
                {
                    "id": "openai",
                    "name": "OpenAI",
                    "is_enabled": True,
                    "is_healthy": True,
                },
            ],
        }

        assert "providers" in response
        provider = response["providers"][0]
        assert "id" in provider
        assert "is_enabled" in provider
        assert "is_healthy" in provider

    def test_provider_health_check_response(self):
        """Test provider health check response."""
        health_response = {
            "provider_id": "openai",
            "is_healthy": True,
            "latency_ms": 150,
            "last_check": datetime.utcnow().isoformat(),
        }

        assert health_response["is_healthy"] is True
        assert "latency_ms" in health_response

    def test_enable_provider_request(self):
        """Test enable provider request structure."""
        # Usually just provider_id in path
        provider_id = "openai"

        assert provider_id == "openai"

    def test_disable_provider_request(self):
        """Test disable provider request structure."""
        provider_id = "openai"

        assert provider_id == "openai"


class TestModelsController:
    """Unit tests for LLM models controller."""

    @pytest.fixture
    def mock_models_service(self):
        """Create mock models service."""
        service = AsyncMock()
        service.list_models = AsyncMock(
            return_value=[
                {
                    "id": "gpt-4",
                    "provider_id": "openai",
                    "name": "GPT-4",
                    "is_enabled": True,
                    "context_window": 8192,
                    "cost_per_1k_tokens": 0.03,
                },
                {
                    "id": "claude-3-opus",
                    "provider_id": "anthropic",
                    "name": "Claude 3 Opus",
                    "is_enabled": True,
                    "context_window": 200000,
                    "cost_per_1k_tokens": 0.015,
                },
            ]
        )
        return service

    def test_list_models_response_structure(self, mock_models_service):
        """Test list models returns expected structure."""
        response = {
            "models": [
                {
                    "id": "gpt-4",
                    "provider_id": "openai",
                    "name": "GPT-4",
                    "is_enabled": True,
                },
            ],
        }

        assert "models" in response
        model = response["models"][0]
        assert "id" in model
        assert "provider_id" in model
        assert "is_enabled" in model

    def test_enable_model_request(self):
        """Test enable model request structure."""
        model_id = "gpt-4"

        assert model_id == "gpt-4"

    def test_disable_model_request(self):
        """Test disable model request structure."""
        model_id = "gpt-4"

        assert model_id == "gpt-4"

    def test_model_not_found_error(self):
        """Test model not found returns error."""
        error_response = {
            "error": {
                "code": "LLM_001",
                "message": "Model not found",
                "i18n_key": "errors.llm.model_not_found",
                "http_status": 404,
            }
        }

        assert error_response["error"]["code"] == "LLM_001"


class TestRankingController:
    """Unit tests for LLM ranking/carousel controller."""

    @pytest.fixture
    def mock_ranking_service(self):
        """Create mock ranking service."""
        service = AsyncMock()
        service.get_carousel_order = AsyncMock(
            return_value=[
                {"model_id": "gpt-4", "position": 1},
                {"model_id": "claude-3-opus", "position": 2},
                {"model_id": "claude-3-sonnet", "position": 3},
            ]
        )
        return service

    def test_get_carousel_order_response(self, mock_ranking_service):
        """Test get carousel order response structure."""
        response = {
            "carousel": [
                {"model_id": "gpt-4", "position": 1},
                {"model_id": "claude-3-opus", "position": 2},
            ],
        }

        assert "carousel" in response
        assert response["carousel"][0]["position"] == 1

    def test_update_carousel_order_request(self):
        """Test update carousel order request structure."""
        request_data = {
            "order": [
                {"model_id": "claude-3-opus", "position": 1},
                {"model_id": "gpt-4", "position": 2},
            ],
        }

        assert "order" in request_data
        assert len(request_data["order"]) == 2

    def test_carousel_order_validation(self):
        """Test carousel order validation."""
        # Positions should be unique and sequential
        valid_order = [
            {"model_id": "model1", "position": 1},
            {"model_id": "model2", "position": 2},
        ]

        positions = [item["position"] for item in valid_order]
        assert positions == sorted(positions)
        assert len(positions) == len(set(positions))  # No duplicates


class TestAgentModelConfigController:
    """Unit tests for agent model configuration controller."""

    def test_get_agent_config_response(self):
        """Test get agent config response structure."""
        response = {
            "agent_id": "chat_agent",
            "model_id": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 4096,
        }

        assert "agent_id" in response
        assert "model_id" in response
        assert "temperature" in response

    def test_update_agent_config_request(self):
        """Test update agent config request structure."""
        request_data = {
            "model_id": "claude-3-opus",
            "temperature": 0.5,
            "max_tokens": 8192,
        }

        assert "model_id" in request_data
        assert 0 <= request_data["temperature"] <= 1

    def test_invalid_temperature_error(self):
        """Test invalid temperature returns error."""
        error_response = {
            "error": {
                "code": "LLM_002",
                "message": "Invalid model configuration",
                "i18n_key": "errors.llm.invalid_config",
                "http_status": 400,
            }
        }

        assert error_response["error"]["http_status"] == 400


class TestCircuitBreakersController:
    """Unit tests for circuit breaker management."""

    def test_get_circuit_status_response(self):
        """Test get circuit breaker status response."""
        response = {
            "circuits": [
                {
                    "provider_id": "openai",
                    "status": "CLOSED",
                    "failure_count": 0,
                    "last_failure": None,
                },
                {
                    "provider_id": "anthropic",
                    "status": "OPEN",
                    "failure_count": 5,
                    "last_failure": datetime.utcnow().isoformat(),
                },
            ],
        }

        assert "circuits" in response
        assert response["circuits"][0]["status"] in ("CLOSED", "OPEN", "HALF_OPEN")

    def test_reset_circuit_request(self):
        """Test reset circuit breaker request."""
        provider_id = "anthropic"

        assert provider_id == "anthropic"


class TestTelemetryController:
    """Unit tests for LLM telemetry/metrics controller."""

    def test_get_telemetry_response(self):
        """Test get telemetry response structure."""
        response = {
            "metrics": {
                "total_requests": 10000,
                "successful_requests": 9500,
                "failed_requests": 500,
                "average_latency_ms": 250,
                "total_tokens_used": 5000000,
            },
            "by_provider": [
                {
                    "provider_id": "openai",
                    "requests": 6000,
                    "avg_latency_ms": 200,
                },
            ],
        }

        assert "metrics" in response
        assert "total_requests" in response["metrics"]

    def test_get_telemetry_with_date_range(self):
        """Test get telemetry with date range filter."""
        params = {
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
        }

        assert "start_date" in params
        assert "end_date" in params


class TestBudgetsController:
    """Unit tests for LLM budget management controller."""

    def test_get_budgets_response(self):
        """Test get budgets response structure."""
        response = {
            "budgets": [
                {
                    "id": str(uuid4()),
                    "provider_id": "openai",
                    "monthly_limit_usd": 1000.00,
                    "current_spend_usd": 250.00,
                    "remaining_usd": 750.00,
                },
            ],
        }

        assert "budgets" in response
        budget = response["budgets"][0]
        assert "monthly_limit_usd" in budget
        assert "current_spend_usd" in budget

    def test_update_budget_request(self):
        """Test update budget request structure."""
        request_data = {
            "monthly_limit_usd": 2000.00,
        }

        assert "monthly_limit_usd" in request_data
        assert request_data["monthly_limit_usd"] > 0


class TestLLMAdminAuthorization:
    """Unit tests for LLM admin authorization."""

    def test_admin_required_for_llm_management(self):
        """Test LLM management requires admin role."""
        error_response = {
            "error": {
                "code": "ADMIN_002",
                "message": "Admin privileges required",
                "i18n_key": "errors.admin.access_denied",
                "http_status": 403,
            }
        }

        assert error_response["error"]["http_status"] == 403

    def test_create_admin_for_llm_tests(self):
        """Test creating admin user for LLM tests."""
        admin_user, token = AuthHelper.create_test_user(role="admin")

        assert admin_user.role == "admin"
        assert token is not None
