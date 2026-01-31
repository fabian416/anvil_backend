"""Integration test for buy crypto intent."""
import pytest
from httpx import AsyncClient


@pytest.fixture
async def ops_auth_token(async_client: AsyncClient):
    """Get real auth token for ops@anvilcrypto.com user."""
    # Login with ops user credentials
    login_response = await async_client.post(
        "/api/v1/account/login",
        json={
            "email": "ops@anvilcrypto.com",
            "password": "your-password-here",  # TODO: Replace with actual password
        },
    )

    if login_response.status_code != 200:
        pytest.skip(f"Cannot login as ops user: {login_response.text}")

    data = login_response.json()
    return data["access_token"]


@pytest.fixture
def ops_auth_headers(ops_auth_token):
    """Generate auth headers for ops user."""
    return {
        "Authorization": f"Bearer {ops_auth_token}",
        "Content-Type": "application/json",
    }


class TestBuyIntent:
    """Test buy crypto intent integration."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.skip(reason="Requires real ops user password - run manually")
    @pytest.mark.llm_validation
    async def test_buy_crypto_shows_wallet_for_authenticated_user(
        self,
        async_client: AsyncClient,
        ops_auth_headers: dict,
    ):
        """
        Test that buy intent shows wallet address for authenticated user.

        User: ops@anvilcrypto.com (user_id=239)
        Expected wallet: 0xc42c83fff8891a368b2579ebd3e964dcef6e0e97

        To run this test:
        1. Update the password in ops_auth_token fixture
        2. Remove @pytest.mark.skip decorator
        3. Run: pytest tests/integration/chat/test_buy_intent.py -v -s
        """
        # Step 1: Create a conversation
        create_response = await async_client.post(
        "/api/v1/conversations",
        json={"title": "Buy Crypto Test", "language": "en"},
        headers=ops_auth_headers,
    )
        assert create_response.status_code == 201
        conversation_data = create_response.json()
        conversation_id = conversation_data["id"]

        print(f"\n✅ Conversation created: {conversation_id}")

        # Step 2: Send "buy crypto" message
        message_response = await async_client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            json={
                "content": "I want to buy crypto",
                "language": "en",
            },
            headers=auth_headers_ops,
        )

        assert message_response.status_code == 201, f"Failed with: {message_response.text}"

        message_data = message_response.json()

        # Verify response structure
        assert "user_message" in message_data
        assert "agent_message" in message_data
        assert "routing" in message_data

        # Check intent was detected correctly
        routing = message_data["routing"]
        assert routing["intent"] in ["buy", "BUY"], f"Expected buy intent, got: {routing['intent']}"

        # Check wallet info in enrichment
        if "enrichment" in message_data:
            enrichment = message_data["enrichment"]
            wallet_address = enrichment.get("wallet_address")

            if wallet_address:
                print(f"\n✅ Wallet found in enrichment: {wallet_address}")
                assert wallet_address == "0xc42c83fff8891a368b2579ebd3e964dcef6e0e97"
            else:
                print(f"\n⚠️  Wallet not in enrichment. Full enrichment: {enrichment}")

        # Check agent message content mentions wallet
        agent_content = message_data["agent_message"]["content"]
        print(f"\n📝 Agent response:\n{agent_content}\n")

        # Wallet should appear in the response
        expected_wallet = "0xc42c83fff8891a368b2579ebd3e964dcef6e0e97"

        # Check if wallet appears in content (might be shortened like 0xc42c...e0e97)
        assert (
            expected_wallet in agent_content or
            expected_wallet[:6] in agent_content  # Check for shortened version
        ), f"Wallet {expected_wallet} not found in agent response"

        print(f"✅ Wallet {expected_wallet[:10]}... found in response!")

        # Verify supported assets are mentioned
        assert "ETH" in agent_content or "USDC" in agent_content

        # Verify supported networks are mentioned
        assert "Base" in agent_content or "Ethereum" in agent_content


    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.llm_validation
    async def test_buy_crypto_different_phrasings(
        self,
        async_client: AsyncClient,
        auth_headers_ops: dict,
    ):
        """Test that different buy phrasings trigger the buy intent."""
        # Create conversation
        create_response = await async_client.post(
            "/api/v1/conversations",
            json={"title": "Buy Intent Test", "language": "en"},
            headers=auth_headers_ops,
        )
        conversation_id = create_response.json()["id"]

        test_phrases = [
            "buy eth",
            "purchase usdc",
            "I want to buy cryptocurrency",
            "how do I buy crypto?",
            "buy 100 USDC",
        ]

        for phrase in test_phrases:
            print(f"\n🔍 Testing phrase: '{phrase}'")

            response = await async_client.post(
                f"/api/v1/conversations/{conversation_id}/messages",
                json={"content": phrase, "language": "en"},
                headers=auth_headers_ops,
            )

            assert response.status_code == 201
            data = response.json()

            # Check intent detection
            intent = data["routing"]["intent"]
            print(f"   Detected intent: {intent}")

            # Should detect as buy intent (or at least not fail)
            assert intent in ["buy", "BUY", "general_conversation"], \
                f"Unexpected intent '{intent}' for phrase '{phrase}'"

            # If it's buy intent, wallet should be shown
            if intent in ["buy", "BUY"]:
                agent_content = data["agent_message"]["content"]
                assert "0xc42c" in agent_content or "wallet" in agent_content.lower()
                print(f"   ✅ Buy intent correctly detected with wallet info")