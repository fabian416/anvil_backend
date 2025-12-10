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
