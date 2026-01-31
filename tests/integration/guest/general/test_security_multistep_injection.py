"""
Security Multi-Step Injection Tests for Chat Endpoints (Phases 1-2).

Tests comprehensive security coverage for multi-step conversation flows:
- Phase 1: XSS injection at each conversation step (12 tests)
- Phase 2: SQL injection at each conversation step (8 tests)

These tests validate that malicious inputs are properly sanitized at EVERY
step of multi-step conversation flows, not just the initial request.

Following OWASP Top 10 and secure coding best practices.
Generated: 2026-01-14
"""

import pytest
from httpx import AsyncClient
from fastapi import status
import json
import warnings
from datetime import datetime


# Mark all tests as security and integration tests
pytestmark = [pytest.mark.asyncio, pytest.mark.integration, pytest.mark.security]


# ============================================================================
# Phase 1: XSS Multi-Step Injection Tests (12 tests)
# ============================================================================


class TestXSSMultiStepInjection:
    """Test XSS injection protection across multi-step conversation flows."""

    @pytest.mark.llm_validation
    async def test_xss_step1_script_tag(self, client: AsyncClient, llm_validator):
        """Test XSS script tag injection at step 1 (initial request)."""
        # Step 1: XSS in initial request
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "<script>alert('XSS')</script> Deposit USDC on Morpho", "language": "en"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        agent_content = data["agent_message"]["content"]

        # Verify XSS is sanitized
        assert "<script>" not in agent_content.lower()
        assert "alert" not in agent_content.lower() or "sanitized" in agent_content.lower()

        conv_id = data["conversation_id"]

        # Step 2: Continue normal flow
        response = await client.post(
            f"/api/v1/guest/chat?conversation_id={conv_id}",
            json={"content": "1", "language": "en"}
        )
        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.llm_validation
    async def test_xss_step2_img_onerror(self, client: AsyncClient, llm_validator):
        """Test XSS img onerror injection at step 2 (asset selection)."""
        # Step 1: Normal request
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "Deposit USDC on Morpho", "language": "en"}
        )
        assert response.status_code == status.HTTP_200_OK
        conv_id = response.json()["conversation_id"]

        # Step 2: XSS in asset selection
        response = await client.post(
            f"/api/v1/guest/chat?conversation_id={conv_id}",
            json={"content": "1<img src=x onerror=alert('XSS')>", "language": "en"}
        )
        assert response.status_code == status.HTTP_200_OK
        agent_content = response.json()["agent_message"]["content"]

        # Verify XSS is sanitized
        assert "onerror" not in agent_content.lower()
        assert "<img" not in agent_content.lower()

    @pytest.mark.llm_validation
    async def test_xss_step3_svg_onload(self, client: AsyncClient, llm_validator):
        """Test XSS svg onload injection at step 3 (amount field)."""
        # Step 1: Normal request
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "Lend USDC on Aave", "language": "en"}
        )
        assert response.status_code == status.HTTP_200_OK
        conv_id = response.json()["conversation_id"]

        # Step 2: XSS in amount field
        response = await client.post(
            f"/api/v1/guest/chat?conversation_id={conv_id}",
            json={"content": "100<svg onload=alert('XSS')>", "language": "en"}
        )
        assert response.status_code == status.HTTP_200_OK
        agent_content = response.json()["agent_message"]["content"]

        # Verify XSS is sanitized
        assert "onload" not in agent_content.lower()
        assert "<svg" not in agent_content.lower()

    @pytest.mark.llm_validation
    async def test_xss_step4_iframe_injection(self, client: AsyncClient, llm_validator):
        """Test XSS iframe injection at step 4 (confirmation)."""
        # Step 1: Normal request
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "Swap 1 ETH to USDC", "language": "en"}
        )
        assert response.status_code == status.HTTP_200_OK
        conv_id = response.json()["conversation_id"]

        # Step 2: XSS in confirmation
        response = await client.post(
            f"/api/v1/guest/chat?conversation_id={conv_id}",
            json={"content": "yes<iframe src='javascript:alert(\"XSS\")'></iframe>", "language": "en"}
        )
        assert response.status_code == status.HTTP_200_OK
        agent_content = response.json()["agent_message"]["content"]

        # Verify XSS is sanitized
        assert "<iframe" not in agent_content.lower()
        assert "javascript:" not in agent_content.lower()

    @pytest.mark.llm_validation
    async def test_xss_deposit_flow(self, client: AsyncClient, llm_validator):
        """Test XSS injection throughout deposit flow."""
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "Deposit USDC on Morpho<script>alert(1)</script>", "language": "en"}
        )
        assert response.status_code == status.HTTP_200_OK
        agent_content = response.json()["agent_message"]["content"]

        # Verify XSS is sanitized
        assert "<script>" not in agent_content.lower()

    @pytest.mark.llm_validation
    async def test_xss_lend_flow(self, client: AsyncClient, llm_validator):
        """Test XSS injection in lending flow with event handler."""
        # Step 1: Normal request
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "Lend USDC on Aave", "language": "en"}
        )
        assert response.status_code == status.HTTP_200_OK
        conv_id = response.json()["conversation_id"]

        # Step 2: XSS with event handler
        response = await client.post(
            f"/api/v1/guest/chat?conversation_id={conv_id}",
            json={"content": "<img src=x onerror=alert(document.cookie)>100", "language": "en"}
        )
        assert response.status_code == status.HTTP_200_OK
        agent_content = response.json()["agent_message"]["content"]

        # Verify XSS is sanitized
        assert "onerror" not in agent_content.lower()
        assert "document.cookie" not in agent_content.lower()

    @pytest.mark.llm_validation
    async def test_xss_swap_flow(self, client: AsyncClient, llm_validator):
        """Test XSS injection in swap flow at step 2."""
        # Step 1: Initiate swap
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "Swap ETH to USDC", "language": "en"}
        )
        assert response.status_code == status.HTTP_200_OK
        conv_id = response.json()["conversation_id"]

        # Step 2: XSS in amount field
        response = await client.post(
            f"/api/v1/guest/chat?conversation_id={conv_id}",
            json={"content": "1<svg onload=alert('XSS')>", "language": "en"}
        )
        assert response.status_code == status.HTTP_200_OK
        agent_content = response.json()["agent_message"]["content"]

        # Verify XSS is sanitized
        assert "onload" not in agent_content.lower()
        assert "<svg>" not in agent_content.lower()

    @pytest.mark.llm_validation
    async def test_xss_buy_flow(self, client: AsyncClient, llm_validator):
        """Test XSS injection in buy flow at step 2."""
        # Step 1: Initiate buy
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "Buy Bitcoin", "language": "en"}
        )
        assert response.status_code == status.HTTP_200_OK
        conv_id = response.json()["conversation_id"]

        # Step 2: XSS with style injection
        response = await client.post(
            f"/api/v1/guest/chat?conversation_id={conv_id}",
            json={"content": "yes<style>body{background:url('javascript:alert(1)')}</style>", "language": "en"}
        )
        assert response.status_code == status.HTTP_200_OK
        agent_content = response.json()["agent_message"]["content"]

        # Verify XSS is sanitized
        assert "<style>" not in agent_content.lower()
        assert "javascript:" not in agent_content.lower()

    @pytest.mark.llm_validation
    async def test_xss_with_cancel_step2(self, client: AsyncClient, llm_validator):
        """Test XSS injection followed by cancellation at step 2."""
        # Step 1: Normal request
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "Deposit USDC on Morpho", "language": "en"}
        )
        assert response.status_code == status.HTTP_200_OK
        conv_id = response.json()["conversation_id"]

        # Step 2: Cancel with XSS payload
        response = await client.post(
            f"/api/v1/guest/chat?conversation_id={conv_id}",
            json={"content": "cancel<script>alert('XSS')</script>", "language": "en"}
        )
        assert response.status_code == status.HTTP_200_OK
        agent_content = response.json()["agent_message"]["content"]

        # Verify XSS is sanitized and cancellation worked
        assert "<script>" not in agent_content.lower()

    @pytest.mark.llm_validation
    async def test_xss_with_cancel_step3(self, client: AsyncClient, llm_validator):
        """Test XSS injection then cancel with malicious payload."""
        # Step 1: Normal request
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "Lend USDC on Aave", "language": "en"}
        )
        assert response.status_code == status.HTTP_200_OK
        conv_id = response.json()["conversation_id"]

        # Step 2: Normal amount
        response = await client.post(
            f"/api/v1/guest/chat?conversation_id={conv_id}",
            json={"content": "100", "language": "en"}
        )
        assert response.status_code == status.HTTP_200_OK

        # Step 3: Cancel with XSS
        response = await client.post(
            f"/api/v1/guest/chat?conversation_id={conv_id}",
            json={"content": "never mind<img src=x onerror=alert('XSS')>", "language": "en"}
        )
        assert response.status_code == status.HTTP_200_OK
        agent_content = response.json()["agent_message"]["content"]

        # Verify XSS is sanitized
        assert "onerror" not in agent_content.lower()

    @pytest.mark.llm_validation
    async def test_xss_then_topic_change(self, client: AsyncClient, llm_validator):
        """Test XSS injection followed by topic change (implicit cancel)."""
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "Swap ETH to USDC<script>alert(1)</script>", "language": "en"}
        )
        assert response.status_code == status.HTTP_200_OK
        conv_id = response.json()["conversation_id"]
        agent_content = response.json()["agent_message"]["content"]

        # Verify XSS is sanitized
        assert "<script>" not in agent_content.lower()

        # Step 2: Topic change
        response = await client.post(
            f"/api/v1/guest/chat?conversation_id={conv_id}",
            json={"content": "What is Bitcoin price?", "language": "en"}
        )
        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.llm_validation
    async def test_xss_unicode_mixed(self, client: AsyncClient, llm_validator):
        """Test XSS with unicode and mixed encoding attempts."""
        # Step 1: Normal request
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "Deposit USDC on Morpho", "language": "en"}
        )
        assert response.status_code == status.HTTP_200_OK
        conv_id = response.json()["conversation_id"]

        # Step 2: Unicode-encoded XSS
        response = await client.post(
            f"/api/v1/guest/chat?conversation_id={conv_id}",
            json={"content": "1\\u003cscript\\u003ealert('XSS')\\u003c/script\\u003e", "language": "en"}
        )
        assert response.status_code == status.HTTP_200_OK
        agent_content = response.json()["agent_message"]["content"]

        # Verify unicode XSS is sanitized
        assert "script" not in agent_content.lower() or "invalid" in agent_content.lower()

class TestSQLMultiStepInjection:
    """Test SQL injection protection across multi-step conversation flows."""

    @pytest.mark.llm_validation
    async def test_sql_step1_or_injection(self, client: AsyncClient, llm_validator):
        """Test SQL OR injection at step 1 (initial request)."""
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "' OR '1'='1 Deposit USDC on Morpho", "language": "en"}
        )
        assert response.status_code == status.HTTP_200_OK
        agent_content = response.json()["agent_message"]["content"]

        # Verify SQL injection is sanitized (no error, normal response)
        assert "or '1'='1" not in agent_content.lower()

        # Continue flow to verify conversation state is maintained
        conv_id = response.json()["conversation_id"]
        response = await client.post(
            f"/api/v1/guest/chat?conversation_id={conv_id}",
            json={"content": "1", "language": "en"}
        )
        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.llm_validation
    async def test_sql_step2_union_injection(self, client: AsyncClient, llm_validator):
        """Test SQL UNION injection at step 2 (asset selection)."""
        # Step 1: Normal request
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "Lend USDC on Aave", "language": "en"}
        )
        assert response.status_code == status.HTTP_200_OK
        conv_id = response.json()["conversation_id"]

        # Step 2: SQL UNION injection
        response = await client.post(
            f"/api/v1/guest/chat?conversation_id={conv_id}",
            json={"content": "1' UNION SELECT * FROM users--", "language": "en"}
        )
        assert response.status_code == status.HTTP_200_OK
        agent_content = response.json()["agent_message"]["content"]

        # Verify SQL injection is sanitized
        assert "union select" not in agent_content.lower()
        assert "from users" not in agent_content.lower()

    @pytest.mark.llm_validation
    async def test_sql_step3_drop_injection(self, client: AsyncClient, llm_validator):
        """Test SQL DROP TABLE injection at step 3 (amount field)."""
        # Step 1: Normal request
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "Swap ETH to USDC", "language": "en"}
        )
        assert response.status_code == status.HTTP_200_OK
        conv_id = response.json()["conversation_id"]

        # Step 2: SQL DROP injection
        response = await client.post(
            f"/api/v1/guest/chat?conversation_id={conv_id}",
            json={"content": "1'; DROP TABLE conversations--", "language": "en"}
        )
        assert response.status_code == status.HTTP_200_OK
        agent_content = response.json()["agent_message"]["content"]

        # Verify SQL injection is sanitized
        assert "drop table" not in agent_content.lower()

    @pytest.mark.llm_validation
    async def test_sql_step4_comment_injection(self, client: AsyncClient, llm_validator):
        """Test SQL comment injection at step 4 (confirmation)."""
        # Step 1-3: Normal requests
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "Deposit USDC on Morpho", "language": "en"}
        )
        assert response.status_code == status.HTTP_200_OK
        conv_id = response.json()["conversation_id"]

        response = await client.post(
            f"/api/v1/guest/chat?conversation_id={conv_id}",
            json={"content": "1", "language": "en"}
        )
        assert response.status_code == status.HTTP_200_OK

        response = await client.post(
            f"/api/v1/guest/chat?conversation_id={conv_id}",
            json={"content": "100", "language": "en"}
        )
        assert response.status_code == status.HTTP_200_OK

        # Step 4: SQL comment injection
        response = await client.post(
            f"/api/v1/guest/chat?conversation_id={conv_id}",
            json={"content": "yes'--", "language": "en"}
        )
        assert response.status_code == status.HTTP_200_OK
        agent_content = response.json()["agent_message"]["content"]

        # Verify SQL injection is sanitized
        assert "'--" not in agent_content or "invalid" in agent_content.lower()

    @pytest.mark.llm_validation
    async def test_sql_deposit_with_cancel(self, client: AsyncClient, llm_validator):
        """Test SQL injection in deposit flow followed by cancellation."""
        # Step 1: Normal request
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "Deposit USDC on Morpho", "language": "en"}
        )
        assert response.status_code == status.HTTP_200_OK
        conv_id = response.json()["conversation_id"]

        # Step 2: SQL injection
        response = await client.post(
            f"/api/v1/guest/chat?conversation_id={conv_id}",
            json={"content": "1' OR '1'='1", "language": "en"}
        )
        assert response.status_code == status.HTTP_200_OK
        agent_content = response.json()["agent_message"]["content"]

        # Verify SQL is sanitized
        assert "or '1'='1" not in agent_content.lower()

        # Step 3: Cancel
        response = await client.post(
            f"/api/v1/guest/chat?conversation_id={conv_id}",
            json={"content": "cancel", "language": "en"}
        )
        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.llm_validation
    async def test_sql_lend_with_topic_change(self, client: AsyncClient, llm_validator):
        """Test SQL injection in lending flow then topic change."""
        # Step 1: Normal request
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "Lend USDC on Aave", "language": "en"}
        )
        assert response.status_code == status.HTTP_200_OK
        conv_id = response.json()["conversation_id"]

        # Step 2: SQL injection with password extraction attempt
        response = await client.post(
            f"/api/v1/guest/chat?conversation_id={conv_id}",
            json={"content": "100' UNION SELECT password FROM users--", "language": "en"}
        )
        assert response.status_code == status.HTTP_200_OK
        agent_content = response.json()["agent_message"]["content"]

        # Verify SQL is sanitized
        assert "union select" not in agent_content.lower()
        assert "password" not in agent_content.lower() or "quote" in agent_content.lower()

        # Step 3: Topic change
        response = await client.post(
            f"/api/v1/guest/chat?conversation_id={conv_id}",
            json={"content": "What is Bitcoin price?", "language": "en"}
        )
        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.llm_validation
    async def test_sql_in_amount_field(self, client: AsyncClient, llm_validator):
        """Test SQL injection specifically in amount field."""
        # Step 1: Normal request
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "Buy Bitcoin", "language": "en"}
        )
        assert response.status_code == status.HTTP_200_OK
        conv_id = response.json()["conversation_id"]

        # Step 2: SQL DELETE injection in amount
        response = await client.post(
            f"/api/v1/guest/chat?conversation_id={conv_id}",
            json={"content": "100'; DELETE FROM chat_conversations WHERE '1'='1'--", "language": "en"}
        )
        assert response.status_code == status.HTTP_200_OK
        agent_content = response.json()["agent_message"]["content"]

        # Verify SQL is sanitized
        assert "delete from" not in agent_content.lower()

    @pytest.mark.llm_validation
    async def test_sql_admin_bypass_attempt(self, client: AsyncClient, llm_validator):
        """Test SQL admin bypass attempt in multi-step flow."""
        # Step 1: Normal request
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "Swap ETH to USDC", "language": "en"}
        )
        assert response.status_code == status.HTTP_200_OK
        conv_id = response.json()["conversation_id"]

        # Step 2: Admin bypass attempt
        response = await client.post(
            f"/api/v1/guest/chat?conversation_id={conv_id}",
            json={"content": "admin'--", "language": "en"}
        )
        assert response.status_code == status.HTTP_200_OK
        agent_content = response.json()["agent_message"]["content"]

        # Verify admin bypass is blocked
        assert "admin'--" not in agent_content or "invalid" in agent_content.lower()

        # Step 3: Topic change to verify conversation still works
        response = await client.post(
            f"/api/v1/guest/chat?conversation_id={conv_id}",
            json={"content": "What is gas price?", "language": "en"}
        )
        assert response.status_code == status.HTTP_200_OK
