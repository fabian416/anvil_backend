import pytest

from app.application.chat.handlers.money_market_handler import MoneyMarketHandler
from app.application.chat.services.intent_detector import ChatIntent
from app.application.guest.handlers.guest_handler_service import GuestHandlerService


@pytest.mark.asyncio
async def test_guest_money_market_returns_comparison_not_static_prompt() -> None:
    service = GuestHandlerService(money_market_handler=MoneyMarketHandler())

    result = await service.handle_intent(
        ChatIntent.MONEY_MARKET,
        "compare Aave vs Compound",
        language="es",
    )

    assert "¡Puedo comparar tasas del mercado monetario!" not in result["content"]
    assert "Comparación" in result["content"]
    assert result["enrichment"] is not None
    assert isinstance(result["enrichment"].get("rates"), list)
    assert result["requires_registration"] is True


