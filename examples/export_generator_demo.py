#!/usr/bin/env python3
"""
Demonstration of ExportGeneratorAdapter functionality.

This script demonstrates:
1. Generating exports in multiple formats (JSON, Markdown, HTML, PDF)
2. PII redaction using regex patterns
3. Compliance formatting for SEC, GDPR, FINRA standards
4. Export metadata generation
5. Async file generation

Usage:
    python examples/export_generator_demo.py
"""

import asyncio
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from app.domain.entities.conversation import Conversation
from app.domain.entities.message import Message
from app.domain.value_objects.chat.export import (
    ExportFormat,
    ComplianceStandard,
    PIIRedactionConfig,
)
from app.domain.value_objects.message_role import MessageRole
from app.infrastructure.adapters.chat.export_generator_adapter import (
    ExportGeneratorAdapter,
)


async def create_sample_data():
    """Create sample conversation and messages."""
    conversation = Conversation(
        id=uuid4(),
        user_id=12345,
        title="DeFi Portfolio Strategy Discussion",
        created_at=datetime(2024, 12, 1, 9, 0, 0),
        updated_at=datetime(2024, 12, 1, 10, 30, 0),
    )

    messages = [
        Message(
            id=uuid4(),
            conversation_id=conversation.id,
            role=MessageRole.USER,
            content="I want to optimize my DeFi portfolio. What yield farming strategies do you recommend?",
            created_at=datetime(2024, 12, 1, 9, 0, 0),
        ),
        Message(
            id=uuid4(),
            conversation_id=conversation.id,
            role=MessageRole.AGENT,
            content="Based on current market conditions, I recommend a diversified strategy: 40% Aave v3 (4.2% APY), 30% Curve Finance (5.1% APY), and 30% Uniswap v3 (variable APY). This balances stability with growth potential.",
            agent_type="defi_yield_agent",
            created_at=datetime(2024, 12, 1, 9, 5, 0),
        ),
        Message(
            id=uuid4(),
            conversation_id=conversation.id,
            role=MessageRole.USER,
            content="Can you analyze the risks? My wallet is 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1. Also, contact me at investor@example.com if there are any concerns.",
            created_at=datetime(2024, 12, 1, 9, 10, 0),
        ),
        Message(
            id=uuid4(),
            conversation_id=conversation.id,
            role=MessageRole.AGENT,
            content="Risk analysis complete:\n- Smart Contract Risk: Low (all protocols are audited)\n- Impermanent Loss Risk: Medium (Uniswap v3 concentrated liquidity)\n- Market Risk: Medium (correlated with overall DeFi TVL)\n- Liquidation Risk: Low (no leverage)\n\nRecommendation: Proceed with diversification as suggested.",
            agent_type="risk_analyzer_agent",
            created_at=datetime(2024, 12, 1, 9, 15, 0),
        ),
        Message(
            id=uuid4(),
            conversation_id=conversation.id,
            role=MessageRole.USER,
            content="Perfect! Execute the strategy with $50,000 USDC.",
            created_at=datetime(2024, 12, 1, 9, 20, 0),
        ),
        Message(
            id=uuid4(),
            conversation_id=conversation.id,
            role=MessageRole.AGENT,
            content="Strategy execution initiated:\n- $20,000 USDC → Aave v3 (tx: 0xabc123...)\n- $15,000 USDC → Curve Finance (tx: 0xdef456...)\n- $15,000 USDC → Uniswap v3 (tx: 0xghi789...)\n\nAll transactions confirmed. Portfolio rebalancing complete.",
            agent_type="execution_agent",
            created_at=datetime(2024, 12, 1, 9, 25, 0),
        ),
    ]

    return conversation, messages


async def demo_json_export(adapter, conversation, messages):
    """Demonstrate JSON export generation."""
    print("\n" + "=" * 80)
    print("1. JSON EXPORT (Standard)")
    print("=" * 80)

    file_path, content = await adapter.generate_export(
        conversation=conversation,
        messages=messages,
        format=ExportFormat.JSON,
        include_metadata=True,
        include_timestamps=True,
        include_agent_names=True,
    )

    print(f"✓ Generated: {file_path}")
    print(f"✓ Size: {len(content)} bytes")
    print(f"\nPreview (first 500 chars):")
    print(content.decode()[:500] + "...")


async def demo_markdown_export(adapter, conversation, messages):
    """Demonstrate Markdown export generation."""
    print("\n" + "=" * 80)
    print("2. MARKDOWN EXPORT (Human-Readable)")
    print("=" * 80)

    file_path, content = await adapter.generate_export(
        conversation=conversation,
        messages=messages,
        format=ExportFormat.MARKDOWN,
        include_metadata=True,
        include_timestamps=True,
        include_agent_names=True,
    )

    print(f"✓ Generated: {file_path}")
    print(f"✓ Size: {len(content)} bytes")
    print(f"\nPreview (first 800 chars):")
    print(content.decode()[:800] + "...")


async def demo_html_export(adapter, conversation, messages):
    """Demonstrate HTML export generation."""
    print("\n" + "=" * 80)
    print("3. HTML EXPORT (Web-Viewable)")
    print("=" * 80)

    file_path, content = await adapter.generate_export(
        conversation=conversation,
        messages=messages,
        format=ExportFormat.HTML,
        include_metadata=True,
        include_timestamps=True,
        include_agent_names=True,
    )

    print(f"✓ Generated: {file_path}")
    print(f"✓ Size: {len(content)} bytes")
    print(f"✓ Open in browser: file://{file_path}")


async def demo_pdf_export(adapter, conversation, messages):
    """Demonstrate PDF export generation."""
    print("\n" + "=" * 80)
    print("4. PDF EXPORT (Professional Report)")
    print("=" * 80)

    try:
        file_path, content = await adapter.generate_export(
            conversation=conversation,
            messages=messages,
            format=ExportFormat.PDF,
            include_metadata=True,
            include_timestamps=True,
            include_agent_names=True,
        )

        print(f"✓ Generated: {file_path}")
        print(f"✓ Size: {len(content)} bytes")
        print(f"✓ PDF created successfully")

    except Exception as e:
        print(f"⚠ PDF generation failed: {e}")
        print(f"  Install reportlab: pip install reportlab")


async def demo_pii_redaction(adapter, conversation, messages):
    """Demonstrate PII redaction."""
    print("\n" + "=" * 80)
    print("5. PII REDACTION (Privacy Protection)")
    print("=" * 80)

    pii_config = PIIRedactionConfig(
        redact_wallet_addresses=True,
        redact_emails=True,
        redact_phone_numbers=True,
        replacement_text="[REDACTED]",
    )

    file_path, content = await adapter.generate_export(
        conversation=conversation,
        messages=messages,
        format=ExportFormat.JSON,
        redact_pii=True,
        pii_config=pii_config,
    )

    import json

    data = json.loads(content.decode())

    print(f"✓ Generated: {file_path}")
    print(f"✓ PII redaction applied")
    print(f"\nSample redacted message:")
    for msg in data["messages"]:
        if (
            "wallet" in msg["content"].lower()
            or "example.com" in msg["content"].lower()
        ):
            print(f"  Original contained: wallet address and email")
            print(f"  Redacted: {msg['content']}")
            break


async def demo_sec_compliance(adapter, conversation, messages):
    """Demonstrate SEC compliance export."""
    print("\n" + "=" * 80)
    print("6. SEC COMPLIANCE EXPORT")
    print("=" * 80)

    file_path, content = await adapter.generate_export(
        conversation=conversation,
        messages=messages,
        format=ExportFormat.JSON,
        compliance_standard=ComplianceStandard.SEC,
        include_metadata=True,
    )

    # Generate metadata
    export_id = uuid4()
    metadata = await adapter.get_export_metadata(
        export_id=export_id,
        conversation=conversation,
        messages=messages,
        format=ExportFormat.JSON,
        file_size_bytes=len(content),
        compliance_standard=ComplianceStandard.SEC,
    )

    print(f"✓ Generated: {file_path}")
    print(f"✓ Compliance: SEC")
    print(f"✓ Digitally Signed: {metadata.digitally_signed}")
    print(f"✓ Hash (SHA256): {metadata.hash_value[:16]}...")
    print(f"✓ Retention Period: 7 years")


async def demo_gdpr_compliance(adapter, conversation, messages):
    """Demonstrate GDPR compliance export with PII redaction."""
    print("\n" + "=" * 80)
    print("7. GDPR COMPLIANCE EXPORT (with PII Redaction)")
    print("=" * 80)

    pii_config = PIIRedactionConfig(
        redact_wallet_addresses=True,
        redact_emails=True,
        redact_phone_numbers=True,
    )

    file_path, content = await adapter.generate_export(
        conversation=conversation,
        messages=messages,
        format=ExportFormat.HTML,
        compliance_standard=ComplianceStandard.GDPR,
        redact_pii=True,
        pii_config=pii_config,
        include_metadata=True,
    )

    # Generate metadata
    export_id = uuid4()
    metadata = await adapter.get_export_metadata(
        export_id=export_id,
        conversation=conversation,
        messages=messages,
        format=ExportFormat.HTML,
        file_size_bytes=len(content),
        compliance_standard=ComplianceStandard.GDPR,
        pii_redacted=True,
    )

    print(f"✓ Generated: {file_path}")
    print(f"✓ Compliance: GDPR")
    print(f"✓ PII Redacted: {metadata.pii_redacted}")
    print(f"✓ Retention Period: 2 years (right to erasure)")


async def demo_finra_compliance(adapter, conversation, messages):
    """Demonstrate FINRA compliance export."""
    print("\n" + "=" * 80)
    print("8. FINRA COMPLIANCE EXPORT (Financial Industry)")
    print("=" * 80)

    file_path, content = await adapter.generate_export(
        conversation=conversation,
        messages=messages,
        format=ExportFormat.PDF,
        compliance_standard=ComplianceStandard.FINRA,
        include_metadata=True,
        include_timestamps=True,
        include_agent_names=True,
    )

    # Generate metadata
    export_id = uuid4()
    metadata = await adapter.get_export_metadata(
        export_id=export_id,
        conversation=conversation,
        messages=messages,
        format=ExportFormat.PDF,
        file_size_bytes=len(content),
        compliance_standard=ComplianceStandard.FINRA,
    )

    print(f"✓ Generated: {file_path}")
    print(f"✓ Compliance: FINRA")
    print(f"✓ Digitally Signed: {metadata.digitally_signed}")
    print(f"✓ Retention Period: 6 years")


async def demo_compliance_validation(adapter):
    """Demonstrate compliance validation."""
    print("\n" + "=" * 80)
    print("9. COMPLIANCE VALIDATION")
    print("=" * 80)

    # Valid combinations
    print("\n✓ Valid combinations:")
    valid_combos = [
        (ExportFormat.JSON, ComplianceStandard.SEC),
        (ExportFormat.PDF, ComplianceStandard.FINRA),
        (ExportFormat.HTML, ComplianceStandard.GDPR),
    ]

    for format, standard in valid_combos:
        try:
            adapter.validate_compliance(format, standard)
            print(f"  - {format.value.upper()} + {standard.value.upper()}: ✓")
        except Exception as e:
            print(f"  - {format.value.upper()} + {standard.value.upper()}: ✗ ({e})")

    # Invalid combinations
    print("\n✗ Invalid combinations:")
    invalid_combos = [
        (ExportFormat.CSV, ComplianceStandard.SEC),
        (ExportFormat.MARKDOWN, ComplianceStandard.FINRA),
    ]

    for format, standard in invalid_combos:
        try:
            adapter.validate_compliance(format, standard)
            print(
                f"  - {format.value.upper()} + {standard.value.upper()}: Should have failed!"
            )
        except Exception as e:
            print(
                f"  - {format.value.upper()} + {standard.value.upper()}: ✓ Correctly rejected"
            )


async def main():
    """Run all demonstrations."""
    print("\n" + "=" * 80)
    print("EXPORT GENERATOR ADAPTER DEMONSTRATION")
    print("=" * 80)

    # Create sample data
    conversation, messages = await create_sample_data()

    # Initialize adapter with temporary storage
    storage_path = "/tmp/conversation_exports_demo"
    adapter = ExportGeneratorAdapter(storage_path=storage_path)

    print(f"\nStorage path: {storage_path}")
    print(f"Conversation: {conversation.title}")
    print(f"Messages: {len(messages)}")

    # Run demonstrations
    await demo_json_export(adapter, conversation, messages)
    await demo_markdown_export(adapter, conversation, messages)
    await demo_html_export(adapter, conversation, messages)
    await demo_pdf_export(adapter, conversation, messages)
    await demo_pii_redaction(adapter, conversation, messages)
    await demo_sec_compliance(adapter, conversation, messages)
    await demo_gdpr_compliance(adapter, conversation, messages)
    await demo_finra_compliance(adapter, conversation, messages)
    await demo_compliance_validation(adapter)

    # Summary
    print("\n" + "=" * 80)
    print("DEMONSTRATION COMPLETE")
    print("=" * 80)
    print(f"\nAll exports saved to: {storage_path}")
    print(f"Total files generated: {len(list(Path(storage_path).glob('*')))}")
    print("\nKey Features Demonstrated:")
    print("  ✓ Multiple export formats (JSON, Markdown, HTML, PDF)")
    print("  ✓ PII redaction (emails, wallets, phone numbers)")
    print("  ✓ Compliance formatting (SEC, GDPR, FINRA)")
    print("  ✓ Metadata generation with digital signatures")
    print("  ✓ Async file generation")
    print("  ✓ Compliance validation")


if __name__ == "__main__":
    asyncio.run(main())
