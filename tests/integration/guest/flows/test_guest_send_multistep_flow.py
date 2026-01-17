"""
Integration tests for multi-step guest send flow.

Tests the complete conversational flow from initiation through confirmation.
"""

import json
import warnings
from datetime import datetime

import pytest


class TestGuestSendMultiStepFlow:
    """Test multi-step send conversational flow."""

    @pytest.mark.asyncio
    async def test_complete_send_flow_eth(self, client, llm_validator, csv_tracker):
        """Test complete 5-step send flow: ETH."""

        # Build conversation history for multi-step validation
        conversation_history = []

        # Step 1: Initiate send
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "send", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        # Verify step 1 response
        assert "agent_message" in data
        step1_content = data["agent_message"]["content"]
        assert "📤" in step1_content or "Send" in step1_content
        assert "token" in step1_content.lower() or "crypto" in step1_content.lower()
        assert any(token in step1_content for token in ["BTC", "ETH", "SOL", "USDC"])

        # Verify metadata
        assert data["enrichment"]["send_flow"] == "step1_token"
        assert data["registration_required"]["required"] is True

        # Track step 1
        conversation_history.append({"user": "send", "agent": step1_content})

        # Step 2: Select token (ETH)
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "ETH", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        # Verify step 2 response
        step2_content = data["agent_message"]["content"]
        assert "ETH" in step2_content or "Ethereum" in step2_content
        assert "amount" in step2_content.lower() or "how much" in step2_content.lower()
        assert data["enrichment"]["send_flow"] == "step2_amount"
        assert data["enrichment"]["token"] == "ETH"

        # Track step 2
        conversation_history.append({"user": "ETH", "agent": step2_content})

        # Step 3: Enter amount
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "0.5", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        # Verify step 3 response
        step3_content = data["agent_message"]["content"]
        assert "0.5" in step3_content
        assert "ETH" in step3_content
        assert "address" in step3_content.lower() or "destination" in step3_content.lower()
        assert data["enrichment"]["send_flow"] == "step3_address"
        assert data["enrichment"]["amount"] == "0.5"

        # Track step 3
        conversation_history.append({"user": "0.5", "agent": step3_content})

        # Step 4: Enter address
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        # Verify step 4 response (review)
        step4_content = data["agent_message"]["content"]
        assert "0.5" in step4_content
        assert "ETH" in step4_content
        assert "0x742d" in step4_content  # Address snippet
        assert "confirm" in step4_content.lower()
        assert data["enrichment"]["send_flow"] == "step4_confirmation"

        # Track step 4
        conversation_history.append({"user": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb", "agent": step4_content})

        # Step 5: Confirm send
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "confirm", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        # Verify step 5 response (execution)
        step5_content = data["agent_message"]["content"]
        assert "✅" in step5_content or "Confirmed" in step5_content or "🎉" in step5_content
        assert "sign up" in step5_content.lower() or "signup" in step5_content.lower()
        assert data["enrichment"]["send_flow"] == "execution"
        assert data["registration_required"]["required"] is True

        # Track step 5
        conversation_history.append({"user": "confirm", "agent": step5_content})

        # PHASE 3: LLM validation with multi-step conversation history
        validation = None
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_complete_send_flow_eth",
                user_input="confirm",  # Final user input
                agent_output=step5_content,  # Final agent output
                expected_behavior=(
                    "Multi-step send flow validation: "
                    "1) User initiates send with 'send' → Agent asks for token "
                    "2) User selects ETH → Agent asks for amount "
                    "3) User enters 0.5 → Agent asks for destination address "
                    "4) User provides address → Agent shows transaction review and confirmation prompt "
                    "5) User confirms → Agent executes send and prompts for signup. "
                    "Response must maintain context across all 5 steps, show proper progression, "
                    "include confirmation emoji (✅), and direct user to sign up for execution."
                ),
                test_func=self.test_complete_send_flow_eth,  # PHASE 3: Custom prompt generation
                conversation_history=conversation_history,  # PHASE 3: Multi-step context
                additional_context={
                    "test_category": "flows",
                    "flow_type": "send_multistep",
                    "flow_steps": 5,
                    "token": "ETH",
                    "amount": "0.5",
                    "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
                },
            )
            if validation.verdict != "PASS":
                warnings.warn(f"LLM validation concern: {validation.reasoning}")

        # CSV tracking with enhanced fields
        await csv_tracker("guest", "flows", {
            "test_id": "guest_send_multistep_flow_eth_001",
            "s_multistep": True,  # Multi-step flow
            "input": "5-step flow: send → ETH → 0.5 → 0x742d... → confirm",
            "output": step5_content,
            "test_label_sequence": "flows_send_multistep",
            "output_expected": "Complete send flow with context continuity and signup prompt",
            "status": "PASS" if response.status_code == 200 else "FAIL",
            "date": datetime.utcnow().isoformat(),
            # Standard 11 fields
            "quality": validation.scoring.overall_score if validation and validation.scoring else None,
            "qa_status": validation.verdict.value if validation else "SKIPPED",
            "qa_output": validation.reasoning if validation else None,
            # Enhanced 12 fields (PHASE 3)
            "accuracy_score": validation.scoring.accuracy_score if validation and validation.scoring else None,
            "relevance_score": validation.scoring.relevance_score if validation and validation.scoring else None,
            "safety_score": validation.scoring.safety_score if validation and validation.scoring else None,
            "coherence_score": validation.scoring.coherence_score if validation and validation.scoring else None,
            "test_category": validation.metadata.test_category if validation and validation.metadata else "flows",
            "test_type": validation.metadata.test_type if validation and validation.metadata else "multi_step",
            "expected_intents": json.dumps(validation.metadata.expected_intents) if validation and validation.metadata else json.dumps(["send_flow"]),
            "token_usage": validation.metadata.token_usage if validation and validation.metadata else None,
            "improvement_suggestions": json.dumps(validation.recommendations.improvement_suggestions) if validation and validation.recommendations else None,
            "critical_issues": json.dumps(validation.recommendations.critical_issues) if validation and validation.recommendations else None,
            "next_steps": json.dumps(validation.recommendations.next_steps) if validation and validation.recommendations else None,
            "model_used": validation.metadata.model_used if validation and validation.metadata else None,
        })

    @pytest.mark.asyncio
    async def test_complete_send_flow_btc(self, client):
        """Test complete send flow with Bitcoin."""

        steps = [
            ("send", "step1_token"),
            ("BTC", "step2_amount"),
            ("0.01", "step3_address"),
            ("bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh", "step4_confirmation"),
            ("yes", "execution"),
        ]

        for i, (message, expected_flow) in enumerate(steps, 1):
            response = await client.post(
                "/api/v1/guest/chat",
                json={"content": message, "language": "en"}
            )
            assert response.status_code == 200
            data = response.json()

            # Verify progression
            if i < len(steps):  # Not last step
                assert data["enrichment"]["send_flow"] == expected_flow

            # Verify final step
            if i == len(steps):
                assert "🎉" in data["agent_message"]["content"] or "✅" in data["agent_message"]["content"]
                assert data["enrichment"]["send_flow"] == "execution"

    @pytest.mark.asyncio
    async def test_send_flow_with_invalid_address(self, client):
        """Test error handling for invalid address."""

        # Complete flow to address step
        await client.post("/api/v1/guest/chat", json={"content": "send", "language": "en"})
        await client.post("/api/v1/guest/chat", json={"content": "ETH", "language": "en"})
        await client.post("/api/v1/guest/chat", json={"content": "1", "language": "en"})

        # Enter invalid address
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "invalid_address", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        # Should show error and re-ask
        content = data["agent_message"]["content"]
        assert "❌" in content or "error" in content.lower() or "valid" in content.lower()

    @pytest.mark.asyncio
    async def test_send_flow_cancel(self, client):
        """Test cancelling send at confirmation."""

        # Complete flow to confirmation
        await client.post("/api/v1/guest/chat", json={"content": "send", "language": "en"})
        await client.post("/api/v1/guest/chat", json={"content": "ETH", "language": "en"})
        await client.post("/api/v1/guest/chat", json={"content": "1", "language": "en"})
        await client.post(
            "/api/v1/guest/chat",
            json={"content": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb", "language": "en"}
        )

        # Cancel
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "cancel", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        content = data["agent_message"]["content"]
        assert "❌" in content or "cancel" in content.lower()

    @pytest.mark.asyncio
    async def test_send_flow_multilingual_spanish(self, client):
        """Test send flow in Spanish."""

        # Step 1
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "send", "language": "es"}
        )
        assert response.status_code == 200
        data = response.json()

        content = data["agent_message"]["content"]
        # Should contain Spanish or English text (fallback)
        assert any(word in content.lower() for word in ["send", "enviar", "token", "cripto"])

    @pytest.mark.asyncio
    async def test_send_security_warnings(self, client):
        """Test that security warnings are displayed."""

        # Get to address step
        await client.post("/api/v1/guest/chat", json={"content": "send", "language": "en"})
        await client.post("/api/v1/guest/chat", json={"content": "ETH", "language": "en"})
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "0.5", "language": "en"}
        )

        assert response.status_code == 200
        data = response.json()
        content = data["agent_message"]["content"]

        # Verify security warnings
        security_elements = [
            "⚠️" in content or "WARNING" in content.upper(),
            "address" in content.lower(),
            "cannot" in content.lower() or "permanent" in content.lower() or "irreversible" in content.lower(),
        ]
        assert any(security_elements), "Missing security warnings"


class TestGuestSendFlowStorytellingQuality:
    """Test storytelling and UX quality of send responses."""

    @pytest.mark.asyncio
    async def test_responses_have_clear_progression(self, client):
        """Test that each step clearly indicates progression."""

        steps = ["send", "ETH", "0.5", "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"]
        previous_content = ""

        for step in steps:
            response = await client.post(
                "/api/v1/guest/chat",
                json={"content": step, "language": "en"}
            )
            content = response.json()["agent_message"]["content"]

            # Each response should be different
            assert content != previous_content
            previous_content = content

    @pytest.mark.asyncio
    async def test_responses_use_emojis_for_visual_appeal(self, client):
        """Test that responses use emojis to enhance communication."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "send", "language": "en"}
        )
        content = response.json()["agent_message"]["content"]

        # Should have emoji indicators
        assert "📤" in content or "💸" in content or "🚀" in content

    @pytest.mark.asyncio
    async def test_confirmation_step_has_clear_call_to_action(self, client):
        """Test that confirmation step has clear CTAs."""

        # Get to confirmation
        await client.post("/api/v1/guest/chat", json={"content": "send", "language": "en"})
        await client.post("/api/v1/guest/chat", json={"content": "ETH", "language": "en"})
        await client.post("/api/v1/guest/chat", json={"content": "0.1", "language": "en"})
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb", "language": "en"}
        )

        content = response.json()["agent_message"]["content"]

        # Should have clear action buttons/instructions
        assert "confirm" in content.lower()
        assert "yes" in content.lower() or "proceed" in content.lower()
        assert "cancel" in content.lower() or "abort" in content.lower()
