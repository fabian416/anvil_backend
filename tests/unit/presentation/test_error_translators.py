"""
Unit tests for HTTP error translators.

Tests error translation and response formatting.
"""

import pytest
from unittest.mock import MagicMock


@pytest.mark.unit
class TestServiceUnavailableTranslator:
    """Tests for ServiceUnavailableTranslator."""
    
    def test_translator_exists(self):
        """Test ServiceUnavailableTranslator exists."""
        from app.presentation.http.errors.translators import ServiceUnavailableTranslator
        
        assert ServiceUnavailableTranslator is not None
    
    def test_translator_instantiation(self):
        """Test translator can be instantiated."""
        from app.presentation.http.errors.translators import ServiceUnavailableTranslator
        
        translator = ServiceUnavailableTranslator()
        
        assert translator is not None
    
    def test_error_response_model_cls_property(self):
        """Test error_response_model_cls returns correct class."""
        from app.presentation.http.errors.translators import ServiceUnavailableTranslator
        from fastapi_error_map import SimpleErrorResponseModel
        
        translator = ServiceUnavailableTranslator()
        
        assert translator.error_response_model_cls == SimpleErrorResponseModel
    
    def test_from_error_returns_error_model(self):
        """Test from_error returns SimpleErrorResponseModel."""
        from app.presentation.http.errors.translators import ServiceUnavailableTranslator
        from fastapi_error_map import SimpleErrorResponseModel
        
        translator = ServiceUnavailableTranslator()
        error = Exception("Test error")
        
        result = translator.from_error(error)
        
        assert isinstance(result, SimpleErrorResponseModel)
    
    def test_from_error_contains_message(self):
        """Test from_error contains appropriate message."""
        from app.presentation.http.errors.translators import ServiceUnavailableTranslator
        
        translator = ServiceUnavailableTranslator()
        error = Exception("Database connection failed")
        
        result = translator.from_error(error)
        
        assert result.error == "Service temporarily unavailable. Please try again later."
    
    def test_from_error_ignores_original_message(self):
        """Test from_error uses generic message regardless of original."""
        from app.presentation.http.errors.translators import ServiceUnavailableTranslator
        
        translator = ServiceUnavailableTranslator()
        
        # Different errors should produce same message
        error1 = Exception("Specific error 1")
        error2 = Exception("Specific error 2")
        
        result1 = translator.from_error(error1)
        result2 = translator.from_error(error2)
        
        assert result1.error == result2.error


@pytest.mark.unit
class TestErrorTranslatorEdgeCases:
    """Tests for error translator edge cases."""
    
    def test_translator_with_none_error(self):
        """Test translator with None error (should still work)."""
        from app.presentation.http.errors.translators import ServiceUnavailableTranslator
        
        translator = ServiceUnavailableTranslator()
        
        result = translator.from_error(None)
        
        assert result.error == "Service temporarily unavailable. Please try again later."
    
    def test_translator_with_empty_string_error(self):
        """Test translator with empty string error."""
        from app.presentation.http.errors.translators import ServiceUnavailableTranslator
        
        translator = ServiceUnavailableTranslator()
        error = Exception("")
        
        result = translator.from_error(error)
        
        assert len(result.error) > 0
        assert result.error == "Service temporarily unavailable. Please try again later."
    
    def test_translator_with_unicode_error(self):
        """Test translator with unicode error message."""
        from app.presentation.http.errors.translators import ServiceUnavailableTranslator
        
        translator = ServiceUnavailableTranslator()
        error = Exception("服务不可用")
        
        result = translator.from_error(error)
        
        # Should return standard English message
        assert result.error == "Service temporarily unavailable. Please try again later."
    
    def test_translator_with_very_long_error_message(self):
        """Test translator with very long error message."""
        from app.presentation.http.errors.translators import ServiceUnavailableTranslator
        
        translator = ServiceUnavailableTranslator()
        long_message = "Error: " + "A" * 10000
        error = Exception(long_message)
        
        result = translator.from_error(error)
        
        # Should return standard short message
        assert len(result.error) < 100
    
    def test_translator_with_nested_exception(self):
        """Test translator with nested exception."""
        from app.presentation.http.errors.translators import ServiceUnavailableTranslator
        
        translator = ServiceUnavailableTranslator()
        
        try:
            try:
                raise ValueError("Inner error")
            except ValueError as inner:
                raise Exception("Outer error") from inner
        except Exception as error:
            result = translator.from_error(error)
            assert result.error == "Service temporarily unavailable. Please try again later."
    
    def test_translator_with_custom_exception_class(self):
        """Test translator with custom exception class."""
        from app.presentation.http.errors.translators import ServiceUnavailableTranslator
        
        class CustomDatabaseError(Exception):
            pass
        
        translator = ServiceUnavailableTranslator()
        error = CustomDatabaseError("Database connection timeout")
        
        result = translator.from_error(error)
        
        assert result.error == "Service temporarily unavailable. Please try again later."


@pytest.mark.unit
class TestErrorTranslatorInheritance:
    """Tests for error translator inheritance."""
    
    @pytest.mark.skip(reason="ErrorTranslator is a Protocol without @runtime_checkable")
    def test_translator_is_error_translator(self):
        """Test ServiceUnavailableTranslator inherits from ErrorTranslator."""
        from app.presentation.http.errors.translators import ServiceUnavailableTranslator
        from fastapi_error_map import ErrorTranslator
        
        translator = ServiceUnavailableTranslator()
        
        # Cannot use isinstance/issubclass with non-runtime-checkable protocols
        assert issubclass(ServiceUnavailableTranslator, ErrorTranslator)
    
    def test_translator_implements_required_methods(self):
        """Test translator implements all required methods."""
        from app.presentation.http.errors.translators import ServiceUnavailableTranslator
        
        translator = ServiceUnavailableTranslator()
        
        assert hasattr(translator, 'error_response_model_cls')
        assert hasattr(translator, 'from_error')
        assert callable(translator.from_error)


@pytest.mark.unit
class TestErrorResponseModel:
    """Tests for error response model."""
    
    def test_simple_error_response_model_structure(self):
        """Test SimpleErrorResponseModel has correct structure."""
        from fastapi_error_map import SimpleErrorResponseModel
        
        model = SimpleErrorResponseModel(error="Test error")
        
        assert hasattr(model, 'error')
        assert model.error == "Test error"
    
    def test_error_response_model_serialization(self):
        """Test error response model can be serialized."""
        from fastapi_error_map import SimpleErrorResponseModel
        
        model = SimpleErrorResponseModel(error="Serialization test")
        
        # Should have dict method for serialization
        if hasattr(model, 'dict'):
            data = model.dict()
            assert 'error' in data
            assert data['error'] == "Serialization test"
        elif hasattr(model, 'model_dump'):
            data = model.model_dump()
            assert 'error' in data
            assert data['error'] == "Serialization test"


@pytest.mark.unit
class TestMultipleTranslatorInstances:
    """Tests for multiple translator instances."""
    
    def test_multiple_translator_instances_independent(self):
        """Test multiple translator instances are independent."""
        from app.presentation.http.errors.translators import ServiceUnavailableTranslator
        
        translator1 = ServiceUnavailableTranslator()
        translator2 = ServiceUnavailableTranslator()
        
        assert translator1 is not translator2
        assert translator1.error_response_model_cls == translator2.error_response_model_cls
    
    def test_translator_stateless(self):
        """Test translator is stateless."""
        from app.presentation.http.errors.translators import ServiceUnavailableTranslator
        
        translator = ServiceUnavailableTranslator()
        
        error1 = Exception("Error 1")
        error2 = Exception("Error 2")
        
        result1 = translator.from_error(error1)
        result2 = translator.from_error(error2)
        
        # Both should produce same result (stateless)
        assert result1.error == result2.error
