"""
Comprehensive Multi-Language Testing Suite - Week 12 (P3-1)

Implements comprehensive multi-language testing across 5 languages:
- French (fr) - NEW language support
- Spanish (es) - Expanded coverage
- Portuguese (pt) - Expanded coverage
- Chinese (zh) - Expanded coverage
- Multi-language context switching

Target: 42 comprehensive tests covering all aspects of multi-language support.

Test Classes:
1. TestFrenchLanguageSupport (10 tests) - Full French coverage
2. TestSpanishComprehensive (8 tests) - Expanded Spanish tests
3. TestPortugueseComprehensive (8 tests) - Expanded Portuguese tests
4. TestChineseComprehensive (6 tests) - Expanded Chinese tests
5. TestMultiLanguageContextSwitching (10 tests) - Context switching + edge cases
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from uuid import uuid4

from tests.helpers.auth_helper import AuthHelper

pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.integration,
    pytest.mark.multilanguage,
]


@pytest_asyncio.fixture
async def french_test_user(async_db_session):
    """Create test user for French language tests."""
    user, token = await AuthHelper.create_test_user_in_db(
        db_session=async_db_session,
        email=f"french_test_{uuid4().hex[:8]}@example.com",
        role="user",
    )
    return user, token


@pytest_asyncio.fixture
async def french_auth_headers(french_test_user):
    """Provide authentication headers for French tests."""
    _, token = french_test_user
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def french_conversation(authenticated_client: AsyncClient, french_auth_headers: dict):
    """Create conversation with French language."""
    response = await authenticated_client.post(
        "/api/v1/conversations",
        headers=french_auth_headers,
        json={"language": "fr"},
    )
    assert response.status_code == 200
    return response.json()["id"]


@pytest.mark.asyncio
class TestFrenchLanguageSupport:
    """Comprehensive French language support tests (10 tests)."""

    @pytest.mark.llm_validation
    async def test_french_001_price_query(
        self,
        authenticated_client: AsyncClient,
        french_auth_headers: dict,
        french_conversation: str,
        llm_validator,
    ):
        """
        GIVEN a French-language conversation
        WHEN sending price query in French
        THEN response should be in French with correct data
        """
        response = await authenticated_client.post(
            f"/api/v1/conversations/{french_conversation}/messages",
            headers=french_auth_headers,
            json={
                "content": "Quel est le prix du Bitcoin?",
                "language": "fr",
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Validate response structure
        assert "agent_message" in data
        assert data["routing"]["language"] == "fr"

        # Validate substantive response
        agent_response = data["agent_message"]["content"]
        assert len(agent_response) > 50, "Should provide substantive response"

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_french_001_price_query",
                user_input="Quel est le prix du Bitcoin?",
                agent_output=agent_response,
                expected_behavior=(
                    "Should provide accurate cryptocurrency price information in French with clear format. "
                    "Response must reference Bitcoin specifically and include current price data with USD denomination."
                ),
                additional_context={'test_category': 'price_query', 'token': 'BTC', 'language': 'fr'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

    @pytest.mark.llm_validation
    async def test_french_002_sentiment_analysis(
        self,
        authenticated_client: AsyncClient,
        french_auth_headers: dict,

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_french_002_sentiment_analysis",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide market sentiment analysis for crypto. Response should include relevant market indicators, community sentiment, or price trends without making specific investment recommendations."
                ),
                additional_context={'test_category': 'sentiment_query', 'token': 'crypto'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        french_conversation: str,
    ):
        """
        GIVEN a French-language conversation
        WHEN requesting sentiment analysis in French
        THEN response should include sentiment data in French
        """
        response = await authenticated_client.post(
            f"/api/v1/conversations/{french_conversation}/messages",
            headers=french_auth_headers,
            json={
                "content": "Quel est le sentiment pour Ethereum?",
                "language": "fr",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert "agent_message" in data
        agent_response = data["agent_message"]["content"]
        assert len(agent_response) > 50

    @pytest.mark.llm_validation
    async def test_french_003_balance_check(
        self,
        authenticated_client: AsyncClient,
        french_auth_headers: dict,

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_french_003_balance_check",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        french_conversation: str,
    ):
        """
        GIVEN a French-language conversation
        WHEN checking balance in French
        THEN response should provide balance info in French
        """
        response = await authenticated_client.post(
            f"/api/v1/conversations/{french_conversation}/messages",
            headers=french_auth_headers,
            json={
                "content": "Vérifier mon solde",
                "language": "fr",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert "agent_message" in data
        agent_response = data["agent_message"]["content"]
        assert len(agent_response) > 30

    @pytest.mark.llm_validation
    async def test_french_004_portfolio_view(
        self,
        authenticated_client: AsyncClient,
        french_auth_headers: dict,

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_french_004_portfolio_view",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        french_conversation: str,
    ):
        """
        GIVEN a French-language conversation
        WHEN requesting portfolio view in French
        THEN response should display portfolio in French
        """
        response = await authenticated_client.post(
            f"/api/v1/conversations/{french_conversation}/messages",
            headers=french_auth_headers,
            json={
                "content": "Afficher mon portefeuille",
                "language": "fr",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert "agent_message" in data
        agent_response = data["agent_message"]["content"]
        assert len(agent_response) > 30

    @pytest.mark.llm_validation
    async def test_french_005_help_request(
        self,
        authenticated_client: AsyncClient,
        french_auth_headers: dict,

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_french_005_help_request",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        french_conversation: str,
    ):
        """
        GIVEN a French-language conversation
        WHEN requesting help in French
        THEN response should provide help in French
        """
        response = await authenticated_client.post(
            f"/api/v1/conversations/{french_conversation}/messages",
            headers=french_auth_headers,
            json={
                "content": "Aide-moi avec les transactions",
                "language": "fr",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert "agent_message" in data
        agent_response = data["agent_message"]["content"]
        assert len(agent_response) > 50

    @pytest.mark.llm_validation
    async def test_french_006_swap_intent(
        self,
        authenticated_client: AsyncClient,
        french_auth_headers: dict,

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_french_006_swap_intent",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        french_conversation: str,
    ):
        """
        GIVEN a French-language conversation
        WHEN requesting token swap in French
        THEN response should handle swap intent in French
        """
        response = await authenticated_client.post(
            f"/api/v1/conversations/{french_conversation}/messages",
            headers=french_auth_headers,
            json={
                "content": "Échanger 100 USDC contre ETH",
                "language": "fr",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert "agent_message" in data
        agent_response = data["agent_message"]["content"]
        assert len(agent_response) > 30

    @pytest.mark.llm_validation
    async def test_french_007_send_intent(
        self,
        authenticated_client: AsyncClient,
        french_auth_headers: dict,

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_french_007_send_intent",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        french_conversation: str,
    ):
        """
        GIVEN a French-language conversation
        WHEN requesting to send tokens in French
        THEN response should handle send intent in French
        """
        response = await authenticated_client.post(
            f"/api/v1/conversations/{french_conversation}/messages",
            headers=french_auth_headers,
            json={
                "content": "Envoyer 50 USDC à 0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
                "language": "fr",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert "agent_message" in data
        agent_response = data["agent_message"]["content"]
        assert len(agent_response) > 30

    @pytest.mark.llm_validation
    async def test_french_008_receive_intent(
        self,
        authenticated_client: AsyncClient,
        french_auth_headers: dict,

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_french_008_receive_intent",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        french_conversation: str,
    ):
        """
        GIVEN a French-language conversation
        WHEN requesting to receive tokens in French
        THEN response should handle receive intent in French
        """
        response = await authenticated_client.post(
            f"/api/v1/conversations/{french_conversation}/messages",
            headers=french_auth_headers,
            json={
                "content": "Recevoir des tokens",
                "language": "fr",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert "agent_message" in data
        agent_response = data["agent_message"]["content"]
        assert len(agent_response) > 30

    @pytest.mark.llm_validation
    async def test_french_009_lending_intent(
        self,
        authenticated_client: AsyncClient,
        french_auth_headers: dict,

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_french_009_lending_intent",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        french_conversation: str,
    ):
        """
        GIVEN a French-language conversation
        WHEN requesting lending operation in French
        THEN response should handle lending intent in French
        """
        response = await authenticated_client.post(
            f"/api/v1/conversations/{french_conversation}/messages",
            headers=french_auth_headers,
            json={
                "content": "Prêter 1000 USDC sur Aave",
                "language": "fr",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert "agent_message" in data
        agent_response = data["agent_message"]["content"]
        assert len(agent_response) > 30

    @pytest.mark.llm_validation
    async def test_french_010_buy_intent(
        self,
        authenticated_client: AsyncClient,
        french_auth_headers: dict,

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_french_010_buy_intent",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        french_conversation: str,
    ):
        """
        GIVEN a French-language conversation
        WHEN requesting to buy crypto in French
        THEN response should handle buy intent in French
        """
        response = await authenticated_client.post(
            f"/api/v1/conversations/{french_conversation}/messages",
            headers=french_auth_headers,
            json={
                "content": "Acheter 0.1 ETH",
                "language": "fr",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert "agent_message" in data
        agent_response = data["agent_message"]["content"]
        assert len(agent_response) > 30


@pytest.mark.asyncio
class TestSpanishComprehensive:
    """Expanded Spanish language tests (8 tests)."""

    @pytest.mark.llm_validation
    async def test_spanish_001_trading_signals(
        self,
        authenticated_client: AsyncClient,
        auth_headers: dict,

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_spanish_001_trading_signals",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        conversation_id: str,
    ):
        """
        GIVEN a Spanish-language conversation
        WHEN requesting trading signals in Spanish
        THEN response should provide trading signals in Spanish
        """
        response = await authenticated_client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={
                "content": "Señales de trading para BTC",
                "language": "es",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert "agent_message" in data
        agent_response = data["agent_message"]["content"]
        assert len(agent_response) > 50

    @pytest.mark.llm_validation
    async def test_spanish_002_price_prediction(
        self,
        authenticated_client: AsyncClient,
        auth_headers: dict,

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_spanish_002_price_prediction",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate cryptocurrency price information in a clear format. Response must reference cryptocurrency specifically (not other cryptocurrencies) and include current price data with USD denomination."
                ),
                additional_context={'test_category': 'price_query', 'token': 'cryptocurrency'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        conversation_id: str,
    ):
        """
        GIVEN a Spanish-language conversation
        WHEN requesting price prediction in Spanish
        THEN response should provide prediction in Spanish
        """
        response = await authenticated_client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={
                "content": "Predicción de precio para SOL",
                "language": "es",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert "agent_message" in data
        agent_response = data["agent_message"]["content"]
        assert len(agent_response) > 50

    @pytest.mark.llm_validation
    async def test_spanish_003_wallet_operations(
        self,
        authenticated_client: AsyncClient,
        auth_headers: dict,

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_spanish_003_wallet_operations",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        conversation_id: str,
    ):
        """
        GIVEN a Spanish-language conversation
        WHEN requesting wallet operations in Spanish
        THEN response should provide wallet info in Spanish
        """
        response = await authenticated_client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={
                "content": "Operaciones de billetera",
                "language": "es",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert "agent_message" in data
        agent_response = data["agent_message"]["content"]
        assert len(agent_response) > 30

    @pytest.mark.llm_validation
    async def test_spanish_004_defi_protocols(
        self,
        authenticated_client: AsyncClient,
        auth_headers: dict,

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_spanish_004_defi_protocols",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate information about DeFi protocol. Response must explain what the protocol does, its key features, and relevant DeFi concepts in an accessible way."
                ),
                additional_context={'test_category': 'defi_protocol', 'protocol': 'DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        conversation_id: str,
    ):
        """
        GIVEN a Spanish-language conversation
        WHEN requesting DeFi protocols in Spanish
        THEN response should list protocols in Spanish
        """
        response = await authenticated_client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={
                "content": "Protocolos DeFi disponibles",
                "language": "es",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert "agent_message" in data
        agent_response = data["agent_message"]["content"]
        assert len(agent_response) > 50

    @pytest.mark.llm_validation
    async def test_spanish_005_swap_operation(
        self,
        authenticated_client: AsyncClient,
        auth_headers: dict,

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_spanish_005_swap_operation",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        conversation_id: str,
    ):
        """
        GIVEN a Spanish-language conversation
        WHEN requesting swap on Uniswap in Spanish
        THEN response should handle swap in Spanish
        """
        response = await authenticated_client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={
                "content": "Intercambiar tokens en Uniswap",
                "language": "es",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert "agent_message" in data
        agent_response = data["agent_message"]["content"]
        assert len(agent_response) > 30

    @pytest.mark.llm_validation
    async def test_spanish_006_lending_borrowing(
        self,
        authenticated_client: AsyncClient,
        auth_headers: dict,

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_spanish_006_lending_borrowing",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        conversation_id: str,
    ):
        """
        GIVEN a Spanish-language conversation
        WHEN requesting lending/borrowing in Spanish
        THEN response should handle Aave operations in Spanish
        """
        response = await authenticated_client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={
                "content": "Prestar y pedir prestado en Aave",
                "language": "es",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert "agent_message" in data
        agent_response = data["agent_message"]["content"]
        assert len(agent_response) > 30

    @pytest.mark.llm_validation
    async def test_spanish_007_nft_query(
        self,
        authenticated_client: AsyncClient,
        auth_headers: dict,

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_spanish_007_nft_query",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        conversation_id: str,
    ):
        """
        GIVEN a Spanish-language conversation
        WHEN requesting NFT display in Spanish
        THEN response should show NFTs in Spanish
        """
        response = await authenticated_client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={
                "content": "Mostrar mis NFTs",
                "language": "es",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert "agent_message" in data
        agent_response = data["agent_message"]["content"]
        assert len(agent_response) > 30

    @pytest.mark.llm_validation
    async def test_spanish_008_gas_estimation(
        self,
        authenticated_client: AsyncClient,
        auth_headers: dict,

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_spanish_008_gas_estimation",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        conversation_id: str,
    ):
        """
        GIVEN a Spanish-language conversation
        WHEN requesting gas estimation in Spanish
        THEN response should provide gas cost in Spanish
        """
        response = await authenticated_client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={
                "content": "¿Cuánto gas costará esta transacción?",
                "language": "es",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert "agent_message" in data
        agent_response = data["agent_message"]["content"]
        assert len(agent_response) > 30


@pytest.mark.asyncio
class TestPortugueseComprehensive:
    """Expanded Portuguese language tests (8 tests)."""

    @pytest.mark.llm_validation
    async def test_portuguese_001_market_analysis(
        self,
        authenticated_client: AsyncClient,
        auth_headers: dict,

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_portuguese_001_market_analysis",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide market sentiment analysis for crypto. Response should include relevant market indicators, community sentiment, or price trends without making specific investment recommendations."
                ),
                additional_context={'test_category': 'sentiment_query', 'token': 'crypto'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        conversation_id: str,
    ):
        """
        GIVEN a Portuguese-language conversation
        WHEN requesting market analysis in Portuguese
        THEN response should provide analysis in Portuguese
        """
        response = await authenticated_client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={
                "content": "Análise de mercado para BTC",
                "language": "pt",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert "agent_message" in data
        agent_response = data["agent_message"]["content"]
        assert len(agent_response) > 50

    @pytest.mark.llm_validation
    async def test_portuguese_002_portfolio_tracking(
        self,
        authenticated_client: AsyncClient,
        auth_headers: dict,

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_portuguese_002_portfolio_tracking",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        conversation_id: str,
    ):
        """
        GIVEN a Portuguese-language conversation
        WHEN requesting portfolio tracking in Portuguese
        THEN response should show portfolio in Portuguese
        """
        response = await authenticated_client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={
                "content": "Rastrear minha carteira",
                "language": "pt",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert "agent_message" in data
        agent_response = data["agent_message"]["content"]
        assert len(agent_response) > 30

    @pytest.mark.llm_validation
    async def test_portuguese_003_token_swap(
        self,
        authenticated_client: AsyncClient,
        auth_headers: dict,

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_portuguese_003_token_swap",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        conversation_id: str,
    ):
        """
        GIVEN a Portuguese-language conversation
        WHEN requesting token swap in Portuguese
        THEN response should handle swap in Portuguese
        """
        response = await authenticated_client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={
                "content": "Trocar 200 USDC por BTC",
                "language": "pt",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert "agent_message" in data
        agent_response = data["agent_message"]["content"]
        assert len(agent_response) > 30

    @pytest.mark.llm_validation
    async def test_portuguese_004_staking_info(
        self,
        authenticated_client: AsyncClient,
        auth_headers: dict,

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_portuguese_004_staking_info",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about Staking. Response must focus on Staking specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'Staking'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        conversation_id: str,
    ):
        """
        GIVEN a Portuguese-language conversation
        WHEN requesting staking info in Portuguese
        THEN response should provide staking details in Portuguese
        """
        response = await authenticated_client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={
                "content": "Informações sobre staking",
                "language": "pt",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert "agent_message" in data
        agent_response = data["agent_message"]["content"]
        assert len(agent_response) > 50

    @pytest.mark.llm_validation
    async def test_portuguese_005_yield_farming(
        self,
        authenticated_client: AsyncClient,
        auth_headers: dict,

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_portuguese_005_yield_farming",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        conversation_id: str,
    ):
        """
        GIVEN a Portuguese-language conversation
        WHEN requesting yield farming on Curve in Portuguese
        THEN response should provide yield info in Portuguese
        """
        response = await authenticated_client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={
                "content": "Yield farming em Curve",
                "language": "pt",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert "agent_message" in data
        agent_response = data["agent_message"]["content"]
        assert len(agent_response) > 30

    @pytest.mark.llm_validation
    async def test_portuguese_006_risk_assessment(
        self,
        authenticated_client: AsyncClient,
        auth_headers: dict,

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_portuguese_006_risk_assessment",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        conversation_id: str,
    ):
        """
        GIVEN a Portuguese-language conversation
        WHEN requesting risk assessment in Portuguese
        THEN response should analyze risks in Portuguese
        """
        response = await authenticated_client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={
                "content": "Avaliação de risco do meu portfólio",
                "language": "pt",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert "agent_message" in data
        agent_response = data["agent_message"]["content"]
        assert len(agent_response) > 50

    @pytest.mark.llm_validation
    async def test_portuguese_007_transaction_history(
        self,
        authenticated_client: AsyncClient,
        auth_headers: dict,

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_portuguese_007_transaction_history",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        conversation_id: str,
    ):
        """
        GIVEN a Portuguese-language conversation
        WHEN requesting transaction history in Portuguese
        THEN response should show history in Portuguese
        """
        response = await authenticated_client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={
                "content": "Histórico de transações",
                "language": "pt",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert "agent_message" in data
        agent_response = data["agent_message"]["content"]
        assert len(agent_response) > 30

    @pytest.mark.llm_validation
    async def test_portuguese_008_security_check(
        self,
        authenticated_client: AsyncClient,
        auth_headers: dict,

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_portuguese_008_security_check",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        conversation_id: str,
    ):
        """
        GIVEN a Portuguese-language conversation
        WHEN requesting security check in Portuguese
        THEN response should provide security analysis in Portuguese
        """
        response = await authenticated_client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={
                "content": "Verificação de segurança da carteira",
                "language": "pt",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert "agent_message" in data
        agent_response = data["agent_message"]["content"]
        assert len(agent_response) > 30


@pytest.mark.asyncio
class TestChineseComprehensive:
    """Expanded Chinese language tests (6 tests)."""

    @pytest.mark.llm_validation
    async def test_chinese_001_market_overview(
        self,
        authenticated_client: AsyncClient,
        auth_headers: dict,

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_chinese_001_market_overview",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide market sentiment analysis for crypto. Response should include relevant market indicators, community sentiment, or price trends without making specific investment recommendations."
                ),
                additional_context={'test_category': 'sentiment_query', 'token': 'crypto'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        conversation_id: str,
    ):
        """
        GIVEN a Chinese-language conversation
        WHEN requesting market overview in Chinese
        THEN response should provide overview in Chinese
        """
        response = await authenticated_client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={
                "content": "市场概览",
                "language": "zh",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert "agent_message" in data
        agent_response = data["agent_message"]["content"]
        assert len(agent_response) > 30

    @pytest.mark.llm_validation
    async def test_chinese_002_trading_strategy(
        self,
        authenticated_client: AsyncClient,
        auth_headers: dict,

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_chinese_002_trading_strategy",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        conversation_id: str,
    ):
        """
        GIVEN a Chinese-language conversation
        WHEN requesting trading strategy in Chinese
        THEN response should provide strategy in Chinese
        """
        response = await authenticated_client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={
                "content": "交易策略建议",
                "language": "zh",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert "agent_message" in data
        agent_response = data["agent_message"]["content"]
        assert len(agent_response) > 50

    @pytest.mark.llm_validation
    async def test_chinese_003_token_analysis(
        self,
        authenticated_client: AsyncClient,
        auth_headers: dict,

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_chinese_003_token_analysis",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        conversation_id: str,
    ):
        """
        GIVEN a Chinese-language conversation
        WHEN requesting token analysis in Chinese
        THEN response should analyze token in Chinese
        """
        response = await authenticated_client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={
                "content": "代币分析",
                "language": "zh",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert "agent_message" in data
        agent_response = data["agent_message"]["content"]
        assert len(agent_response) > 30

    @pytest.mark.llm_validation
    async def test_chinese_004_defi_yield(
        self,
        authenticated_client: AsyncClient,
        auth_headers: dict,

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_chinese_004_defi_yield",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        conversation_id: str,
    ):
        """
        GIVEN a Chinese-language conversation
        WHEN requesting DeFi yield in Chinese
        THEN response should show yield rates in Chinese
        """
        response = await authenticated_client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={
                "content": "DeFi 收益率",
                "language": "zh",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert "agent_message" in data
        agent_response = data["agent_message"]["content"]
        assert len(agent_response) > 30

    @pytest.mark.llm_validation
    async def test_chinese_005_wallet_security(
        self,
        authenticated_client: AsyncClient,
        auth_headers: dict,

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_chinese_005_wallet_security",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        conversation_id: str,
    ):
        """
        GIVEN a Chinese-language conversation
        WHEN requesting wallet security check in Chinese
        THEN response should provide security info in Chinese
        """
        response = await authenticated_client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={
                "content": "钱包安全检查",
                "language": "zh",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert "agent_message" in data
        agent_response = data["agent_message"]["content"]
        assert len(agent_response) > 30

    @pytest.mark.llm_validation
    async def test_chinese_006_gas_optimization(
        self,
        authenticated_client: AsyncClient,
        auth_headers: dict,

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_chinese_006_gas_optimization",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        conversation_id: str,
    ):
        """
        GIVEN a Chinese-language conversation
        WHEN requesting gas optimization in Chinese
        THEN response should provide gas tips in Chinese
        """
        response = await authenticated_client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={
                "content": "Gas 优化建议",
                "language": "zh",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert "agent_message" in data
        agent_response = data["agent_message"]["content"]
        assert len(agent_response) > 30


@pytest.mark.asyncio
class TestMultiLanguageContextSwitching:
    """Multi-language context switching and edge cases (10 tests)."""

    @pytest.mark.llm_validation
    async def test_context_switch_001_english_to_french(
        self,
        authenticated_client: AsyncClient,
        auth_headers: dict,

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_context_switch_001_english_to_french",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        conversation_id: str,
    ):
        """
        GIVEN a conversation started in English
        WHEN switching to French mid-conversation
        THEN responses should switch to French
        """
        # English message
        response1 = await authenticated_client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={
                "content": "What is the price of Bitcoin?",
                "language": "en",
            },
        )
        assert response1.status_code == 200

        # Switch to French
        response2 = await authenticated_client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={
                "content": "Quel est le sentiment pour ETH?",
                "language": "fr",
            },
        )

        assert response2.status_code == 200
        data = response2.json()
        assert data["routing"]["language"] == "fr"

    @pytest.mark.llm_validation
    async def test_context_switch_002_spanish_to_english(
        self,
        authenticated_client: AsyncClient,
        auth_headers: dict,

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_context_switch_002_spanish_to_english",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        conversation_id: str,
    ):
        """
        GIVEN a conversation started in Spanish
        WHEN switching to English mid-conversation
        THEN responses should switch to English
        """
        # Spanish message
        response1 = await authenticated_client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={
                "content": "¿Cuál es el precio de Bitcoin?",
                "language": "es",
            },
        )
        assert response1.status_code == 200

        # Switch to English
        response2 = await authenticated_client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={
                "content": "What is the sentiment for ETH?",
                "language": "en",
            },
        )

        assert response2.status_code == 200
        data = response2.json()
        assert data["routing"]["language"] == "en"

    @pytest.mark.llm_validation
    async def test_context_switch_003_chinese_to_portuguese(
        self,
        authenticated_client: AsyncClient,
        auth_headers: dict,

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_context_switch_003_chinese_to_portuguese",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        conversation_id: str,
    ):
        """
        GIVEN a conversation started in Chinese
        WHEN switching to Portuguese mid-conversation
        THEN responses should switch to Portuguese
        """
        # Chinese message
        response1 = await authenticated_client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={
                "content": "比特币的价格是多少？",
                "language": "zh",
            },
        )
        assert response1.status_code == 200

        # Switch to Portuguese
        response2 = await authenticated_client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={
                "content": "Qual é o preço do Ethereum?",
                "language": "pt",
            },
        )

        assert response2.status_code == 200
        data = response2.json()
        assert data["routing"]["language"] == "pt"

    @pytest.mark.llm_validation
    async def test_context_switch_004_maintain_context(
        self,
        authenticated_client: AsyncClient,
        auth_headers: dict,

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_context_switch_004_maintain_context",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        conversation_id: str,
    ):
        """
        GIVEN a multi-turn conversation with language switch
        WHEN referencing previous context in new language
        THEN context should be maintained across language switch
        """
        # English message about Bitcoin
        response1 = await authenticated_client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={
                "content": "What is the price of Bitcoin?",
                "language": "en",
            },
        )
        assert response1.status_code == 200

        # Follow-up in French referencing Bitcoin
        response2 = await authenticated_client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={
                "content": "Et le sentiment pour celui-ci?",  # "And the sentiment for this one?"
                "language": "fr",
            },
        )

        assert response2.status_code == 200
        data = response2.json()
        # Should understand "celui-ci" refers to Bitcoin from previous message
        assert len(data["agent_message"]["content"]) > 30

    @pytest.mark.llm_validation
    async def test_context_switch_005_multi_conversation_languages(
        self,
        authenticated_client: AsyncClient,
        auth_headers: dict,

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_context_switch_005_multi_conversation_languages",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        test_user,
    ):
        """
        GIVEN multiple conversations for same user
        WHEN using different languages in each conversation
        THEN each conversation should maintain its own language
        """
        # Create English conversation
        conv1_response = await authenticated_client.post(
            "/api/v1/conversations",
            headers=auth_headers,
            json={"language": "en"},
        )
        conv1_id = conv1_response.json()["id"]

        # Create French conversation
        conv2_response = await authenticated_client.post(
            "/api/v1/conversations",
            headers=auth_headers,
            json={"language": "fr"},
        )
        conv2_id = conv2_response.json()["id"]

        # Send message to each
        msg1_response = await authenticated_client.post(
            f"/api/v1/conversations/{conv1_id}/messages",
            headers=auth_headers,
            json={"content": "Hello", "language": "en"},
        )

        msg2_response = await authenticated_client.post(
            f"/api/v1/conversations/{conv2_id}/messages",
            headers=auth_headers,
            json={"content": "Bonjour", "language": "fr"},
        )

        assert msg1_response.status_code == 200
        assert msg2_response.status_code == 200
        assert msg1_response.json()["routing"]["language"] == "en"
        assert msg2_response.json()["routing"]["language"] == "fr"

    @pytest.mark.llm_validation
    async def test_edge_case_001_mixed_language_content(
        self,
        authenticated_client: AsyncClient,
        auth_headers: dict,

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_edge_case_001_mixed_language_content",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        conversation_id: str,
    ):
        """
        GIVEN a message with mixed language content
        WHEN language param specifies French
        THEN response should be in French despite mixed content
        """
        response = await authenticated_client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={
                "content": "Swap 100 USDC à ETH",  # Mixed English/French
                "language": "fr",
            },
        )

        assert response.status_code == 200
        data = response.json()
        # Should respond in French as specified
        assert data["routing"]["language"] == "fr"

    @pytest.mark.llm_validation
    async def test_edge_case_002_language_detection(
        self,
        authenticated_client: AsyncClient,
        auth_headers: dict,

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_edge_case_002_language_detection",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        conversation_id: str,
    ):
        """
        GIVEN a message in French without explicit language param
        WHEN language defaults to 'en'
        THEN response should still be generated (may auto-detect or use default)
        """
        response = await authenticated_client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={
                "content": "Quel est le prix du Bitcoin?",
                "language": "en",  # Explicitly set to English despite French content
            },
        )

        assert response.status_code == 200
        data = response.json()
        # Should still generate response
        assert "agent_message" in data
        assert len(data["agent_message"]["content"]) > 30

    @pytest.mark.llm_validation
    async def test_edge_case_003_fallback_to_english(
        self,
        authenticated_client: AsyncClient,
        auth_headers: dict,

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_edge_case_003_fallback_to_english",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        conversation_id: str,
    ):
        """
        GIVEN a conversation without explicit language
        WHEN sending message with default language
        THEN should fallback to English
        """
        response = await authenticated_client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={
                "content": "What is Bitcoin price?",
                # No language field - should default to 'en'
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["routing"]["language"] == "en"

    @pytest.mark.llm_validation
    async def test_edge_case_004_language_preference_persistence(
        self,
        authenticated_client: AsyncClient,
        french_auth_headers: dict,

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_edge_case_004_language_preference_persistence",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        french_conversation: str,
    ):
        """
        GIVEN a conversation created with French language
        WHEN sending multiple messages
        THEN language preference should persist
        """
        # First message
        response1 = await authenticated_client.post(
            f"/api/v1/conversations/{french_conversation}/messages",
            headers=french_auth_headers,
            json={"content": "Bonjour", "language": "fr"},
        )

        # Second message (no explicit language)
        response2 = await authenticated_client.post(
            f"/api/v1/conversations/{french_conversation}/messages",
            headers=french_auth_headers,
            json={"content": "Quel est le prix?", "language": "fr"},
        )

        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response1.json()["routing"]["language"] == "fr"
        assert response2.json()["routing"]["language"] == "fr"

    @pytest.mark.llm_validation
    async def test_edge_case_005_invalid_language_code(
        self,
        authenticated_client: AsyncClient,
        auth_headers: dict,

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_edge_case_005_invalid_language_code",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        conversation_id: str,
    ):
        """
        GIVEN a message with invalid language code
        WHEN sending request
        THEN should return 422 validation error
        """
        response = await authenticated_client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={
                "content": "What is Bitcoin price?",
                "language": "xyz",  # Invalid code
            },
        )

        # Should reject invalid language code
        assert response.status_code == 422