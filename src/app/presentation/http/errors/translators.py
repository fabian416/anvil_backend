from typing import Any

from fastapi_error_map import ErrorTranslator, SimpleErrorResponseModel


class BadRequestTranslator(ErrorTranslator[SimpleErrorResponseModel]):
    """Translator for bad request errors (400)."""

    @property
    def error_response_model_cls(self) -> type[SimpleErrorResponseModel]:
        return SimpleErrorResponseModel

    def from_error(self, err: Exception) -> SimpleErrorResponseModel:
        return SimpleErrorResponseModel(error=str(err))


class NotFoundTranslator(ErrorTranslator[SimpleErrorResponseModel]):
    """Translator for not found errors (404)."""

    @property
    def error_response_model_cls(self) -> type[SimpleErrorResponseModel]:
        return SimpleErrorResponseModel

    def from_error(self, err: Exception) -> SimpleErrorResponseModel:
        return SimpleErrorResponseModel(error=str(err))


class ServiceUnavailableTranslator(ErrorTranslator[SimpleErrorResponseModel]):
    """Translator for service unavailable errors (503)."""

    @property
    def error_response_model_cls(self) -> type[SimpleErrorResponseModel]:
        return SimpleErrorResponseModel

    def from_error(self, _err: Exception) -> SimpleErrorResponseModel:
        return SimpleErrorResponseModel(
            error="Service temporarily unavailable. Please try again later."
        )


class NotFoundErrorTranslator(ErrorTranslator[SimpleErrorResponseModel]):
    """Translator for not found errors with resource type context."""

    def __init__(self, resource_type: str = "resource"):
        """Initialize with resource type for context."""
        self._resource_type = resource_type

    @property
    def error_response_model_cls(self) -> type[SimpleErrorResponseModel]:
        return SimpleErrorResponseModel

    def from_error(self, err: Exception) -> SimpleErrorResponseModel:
        return SimpleErrorResponseModel(error=str(err))


class ValidationErrorTranslator(ErrorTranslator[SimpleErrorResponseModel]):
    """Translator for validation errors (400)."""

    @property
    def error_response_model_cls(self) -> type[SimpleErrorResponseModel]:
        return SimpleErrorResponseModel

    def from_error(self, err: Exception) -> SimpleErrorResponseModel:
        return SimpleErrorResponseModel(error=str(err))


class StandardizedErrorTranslator(ErrorTranslator[SimpleErrorResponseModel]):
    """Translator for standardized error responses."""

    @property
    def error_response_model_cls(self) -> type[SimpleErrorResponseModel]:
        return SimpleErrorResponseModel

    def from_error(self, err: Exception) -> SimpleErrorResponseModel:
        # Check if error has error_code attribute
        error_code = getattr(err, "error_code", None)
        message = str(err)
        if error_code:
            return SimpleErrorResponseModel(error=f"[{error_code}] {message}")
        return SimpleErrorResponseModel(error=message)


class ConflictTranslator(ErrorTranslator[SimpleErrorResponseModel]):
    """Translator for conflict errors (409)."""

    @property
    def error_response_model_cls(self) -> type[SimpleErrorResponseModel]:
        return SimpleErrorResponseModel

    def from_error(self, err: Exception) -> SimpleErrorResponseModel:
        return SimpleErrorResponseModel(error=str(err))


class UnauthorizedTranslator(ErrorTranslator[SimpleErrorResponseModel]):
    """Translator for unauthorized errors (401)."""

    @property
    def error_response_model_cls(self) -> type[SimpleErrorResponseModel]:
        return SimpleErrorResponseModel

    def from_error(self, err: Exception) -> SimpleErrorResponseModel:
        return SimpleErrorResponseModel(error=str(err))


class ForbiddenTranslator(ErrorTranslator[SimpleErrorResponseModel]):
    """Translator for forbidden errors (403)."""

    @property
    def error_response_model_cls(self) -> type[SimpleErrorResponseModel]:
        return SimpleErrorResponseModel

    def from_error(self, err: Exception) -> SimpleErrorResponseModel:
        return SimpleErrorResponseModel(error=str(err))
