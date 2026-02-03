"""
Unit tests for response validator.

Tests JSON parsing, schema validation, and fallback responses.
"""

import pytest

from app.infrastructure.distillation.response_validator import ResponseValidator


class TestResponseValidator:
    """Test response validator."""

    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        return ResponseValidator()

    def test_validate_valid_response(self, validator):
        """Test validation of valid response."""
        response = {
            "success": True,
            "message": "Request is valid",
            "reason": "validation_passed",
            "confidence": 0.95,
        }

        is_valid, error = validator.validate(response)

        assert is_valid is True
        assert error is None

    def test_validate_missing_field(self, validator):
        """Test validation fails with missing field."""
        response = {
            "success": True,
            "message": "Request is valid",
            # Missing 'reason' and 'confidence'
        }

        is_valid, error = validator.validate(response)

        assert is_valid is False
        assert "validation failed" in error.lower()

    def test_validate_invalid_confidence(self, validator):
        """Test validation fails with invalid confidence."""
        response = {
            "success": True,
            "message": "Request is valid",
            "reason": "validation_passed",
            "confidence": 1.5,  # Out of range
        }

        is_valid, error = validator.validate(response)

        assert is_valid is False

    def test_parse_json_clean(self, validator):
        """Test parsing clean JSON."""
        text = '{"success": true, "message": "OK", "reason": "validation_passed", "confidence": 0.9}'

        data, error = validator.parse_json_safe(text)

        assert error is None
        assert data["success"] is True
        assert data["confidence"] == 0.9

    def test_parse_json_with_markdown(self, validator):
        """Test parsing JSON with markdown code blocks."""
        text = """```json
{
  "success": false,
  "message": "Out of scope",
  "reason": "out_of_scope",
  "confidence": 0.85
}
```"""

        data, error = validator.parse_json_safe(text)

        assert error is None
        assert data["success"] is False
        assert data["reason"] == "out_of_scope"

    def test_parse_json_with_extra_text(self, validator):
        """Test parsing JSON with surrounding text."""
        text = """Here is the response:
{
  "success": true,
  "message": "Valid request",
  "reason": "validation_passed",
  "confidence": 0.92
}
Some extra text here."""

        data, error = validator.parse_json_safe(text)

        assert error is None
        assert data["success"] is True

    def test_parse_json_invalid(self, validator):
        """Test parsing invalid JSON."""
        text = "This is not JSON at all"

        data, error = validator.parse_json_safe(text)

        assert data is None
        assert error is not None

    def test_parse_json_empty(self, validator):
        """Test parsing empty string."""
        text = ""

        data, error = validator.parse_json_safe(text)

        assert data is None
        assert "Empty response" in error

    def test_create_fallback_response_english(self, validator):
        """Test fallback response in English."""
        response = validator.create_fallback_response("Some error", "en")

        assert response["success"] is False
        assert response["reason"] == "system_error"
        assert "try again" in response["message"].lower()

    def test_create_fallback_response_spanish(self, validator):
        """Test fallback response in Spanish."""
        response = validator.create_fallback_response("Algún error", "es")

        assert response["success"] is False
        assert "inténtalo" in response["message"].lower()

    def test_create_fallback_response_unknown_language(self, validator):
        """Test fallback response with unknown language defaults to English."""
        response = validator.create_fallback_response("Error", "xx")

        assert response["success"] is False
        assert "try again" in response["message"].lower()
