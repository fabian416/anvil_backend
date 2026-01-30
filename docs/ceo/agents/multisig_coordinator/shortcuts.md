# Multi-Sig Coordinator Agent Shortcuts

**Version**: 1.0
**Date**: 2026-01-29
**Status**: Complete

---

## Overview

This document defines the query patterns, treasury operations, and example responses for the **MULTISIG_COORDINATOR** agent.

---

## Query Patterns

### Create Proposals

| Query | Intent | Description |
|-------|--------|-------------|
| "Send 10000 USDC to 0x... for marketing" | manage_multisig | Create proposal |
| "Create treasury proposal for 50000 USDC" | treasury_management | Large proposal |
| "Transfer 5 ETH to 0x... for contractor" | manage_multisig | ETH transfer |
| "Pay 25000 USDC to 0x... for engineering" | manage_multisig | Budget-coded |

### Check Status

| Query | Intent | Description |
|-------|--------|-------------|
| "Check pending approvals" | manage_multisig | List pending |
| "Show my proposals" | manage_multisig | User's proposals |
| "What's the status of proposal XYZ?" | manage_multisig | Specific proposal |
| "List recent treasury transactions" | treasury_management | History |

### Treasury Management

| Query | Intent | Description |
|-------|--------|-------------|
| "Show treasury balance" | treasury_management | Safe balance |
| "What's our marketing budget?" | treasury_management | Budget status |
| "Monthly spending report" | treasury_management | Analytics |
| "Who needs to approve?" | manage_multisig | Pending approvers |

---

## Budget Codes

### Available Categories

| Code | Category | Monthly Limit | Description |
|------|----------|---------------|-------------|
| `marketing` | Marketing & PR | $100,000 | Ads, sponsorships, events |
| `engineering` | Development | $200,000 | Contractors, tools, licenses |
| `operations` | Operations | $150,000 | Office, utilities, salaries |
| `legal` | Legal & Compliance | $50,000 | Attorneys, audits, filings |
| `general` | Uncategorized | $25,000 | Miscellaneous expenses |

### Budget-Coded Queries

```
• "Send 5000 USDC to 0x... for marketing campaign"
• "Transfer 10000 USDC to 0x... budget: engineering"
• "Pay contractor 3000 USDC from operations budget"
```

---

## Example Conversations

### Create Proposal

```
User: "Send 10000 USDC to 0x742d35Cc6634C0532925a3b844Bc454e4438f44e for marketing campaign"

Agent:
🏦 **MULTI-SIG PROPOSAL CREATED**

**Proposal ID**: `a1b2c3d4-e5f6-7890-abcd-1234567890ab`
**Safe Address**: `0x1234...5678`

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**TRANSACTION DETAILS**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Amount**: 10000 USDC ($10,000.00 USD)
**Destination**: `0x742d35Cc6634C0532925a3b844Bc454e4438f44e`
**Purpose**: Marketing campaign
**Budget Code**: marketing

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**APPROVAL WORKFLOW**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Status**: ⏳ **PENDING APPROVAL**
**Required Approvals**: 2
**Current Approvals**: 0/2

**Approvers Notified**:
  ⏳ CFO - Pending
  ⏳ CEO - Pending

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**NEXT STEPS**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Approvers have been notified via email and Slack
2. Each approver must review and approve/reject
3. Transaction executes automatically after final approval
4. Estimated execution time: 2-24 hours (based on approver response)

**Policy**: This transaction requires explicit approval from all
listed approvers. No automatic execution without full approval.

**Audit Trail**: All actions are logged immutably on-chain and in
compliance database for regulatory reporting.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Treasury Management**: Gnosis Safe
**Compliance**: SOC 2 Type II
**Insurance**: $10M coverage (Nexus Mutual)
```

### Large Transaction (Board Approval)

```
User: "Transfer 75000 USDC to 0xABC... for acquisition"

Agent:
🏦 **MULTI-SIG PROPOSAL CREATED**

**Proposal ID**: `xyz-1234-5678-abcd`
**Safe Address**: `0x1234...5678`

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**TRANSACTION DETAILS**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Amount**: 75000 USDC ($75,000.00 USD)
**Destination**: `0xABC...`
**Purpose**: Acquisition
**Budget Code**: N/A

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**APPROVAL WORKFLOW**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Status**: ⏳ **PENDING APPROVAL**
**Required Approvals**: 4 (Board approval required)
**Current Approvals**: 0/4

**Approvers Notified**:
  ⏳ CFO - Pending
  ⏳ CEO - Pending
  ⏳ COO - Pending
  ⏳ Board Member 1 - Pending

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ **LARGE TRANSACTION NOTICE**

This transaction exceeds $50,000 and requires Board approval.
Please allow additional time for the approval process.

**Estimated Resolution**: 24-72 hours
```

### Check Pending Approvals

```
User: "Check pending approvals"

Agent:
📋 **PENDING APPROVALS**

You have **3** proposals awaiting approval:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**1. Proposal #a1b2c3**
| Field | Value |
|-------|-------|
| Amount | 10,000 USDC |
| Purpose | Marketing campaign |
| Status | 1/2 approvals |
| Created | 2h ago |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**2. Proposal #xyz789**
| Field | Value |
|-------|-------|
| Amount | 5,000 USDC |
| Purpose | Contractor payment |
| Status | 0/2 approvals |
| Created | 4h ago |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**3. Proposal #def456**
| Field | Value |
|-------|-------|
| Amount | 75,000 USDC |
| Purpose | Acquisition |
| Status | 2/4 approvals |
| Created | 1d ago |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Actions**:
- Say "Approve proposal #a1b2c3" to approve
- Say "Reject proposal #xyz789" to reject
- Say "Details of proposal #def456" for more info

**Your Role**: CFO (Approver)
```

### Treasury Balance

```
User: "Show treasury balance"

Agent:
🏦 **TREASURY BALANCE**

**Safe Address**: `0x1234...5678`
**Network**: Ethereum Mainnet

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**CURRENT HOLDINGS**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| Token | Balance | USD Value |
|-------|---------|-----------|
| ETH | 125.5 | $313,750 |
| USDC | 500,000 | $500,000 |
| USDT | 250,000 | $250,000 |
| LINK | 10,000 | $75,000 |

**Total Balance**: **$1,138,750 USD**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**MONTHLY ACTIVITY**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| Metric | Value |
|--------|-------|
| Inflows | +$150,000 |
| Outflows | -$85,000 |
| Net Change | +$65,000 |
| Pending | $90,000 |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**BUDGET STATUS**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| Budget | Spent | Limit | Remaining |
|--------|-------|-------|-----------|
| Marketing | $45,000 | $100,000 | $55,000 |
| Engineering | $120,000 | $200,000 | $80,000 |
| Operations | $75,000 | $150,000 | $75,000 |

**Budget Period**: January 2026

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Insurance**: $10M coverage (Nexus Mutual)
**Last Audit**: 2026-01-15 (All clear)
**Signers**: 7 authorized (3-of-7 required)
```

### Invalid Request

```
User: "Send money"

Agent:
Invalid transaction request. Please specify amount, destination, and purpose.

**Required Information**:
- **Amount**: How much to send (e.g., "10000 USDC")
- **Destination**: Wallet address (e.g., "0x...")
- **Purpose**: Transaction purpose (e.g., "for marketing")

**Example Queries**:
- "Send 10000 USDC to 0x1234... for marketing campaign"
- "Transfer 5 ETH to 0xABC... for contractor payment"
- "Pay 25000 USDC to 0xDEF... budget: engineering"

**Optional**: Specify budget code (marketing, engineering, operations, legal, general)
```

---

## API Response Examples

### Proposal Creation

```json
{
  "agent_message": {
    "content": "🏦 **MULTI-SIG PROPOSAL CREATED**\n\n**Proposal ID**: `a1b2c3...`...",
    "role": "assistant",
    "agent_type": "multisig_coordinator"
  },
  "enrichment": {
    "agent_timings": [
      {"agent_type": "supervisor", "duration_ms": 50},
      {"agent_type": "multisig_coordinator", "duration_ms": 600}
    ],
    "sources": [
      {
        "source_type": "api",
        "source_name": "Gnosis Safe",
        "url": "https://app.safe.global/",
        "citation_text": "Multi-sig wallet coordination via Gnosis Safe",
        "provider": "Gnosis Safe API",
        "relevance_score": 1.0
      },
      {
        "source_type": "llm",
        "source_name": "gemini-2.0-flash",
        "citation_text": "Generated by gemini-2.0-flash",
        "relevance_score": 1.0
      }
    ]
  },
  "metadata": {
    "proposal_id": "a1b2c3d4-e5f6-7890-abcd-1234567890ab",
    "amount_usd": 10000.0,
    "status": "PENDING_APPROVAL",
    "approvals_required": 2
  }
}
```

---

## Approval Thresholds Reference

### Amount-Based Policy

| Amount Range | Policy | Required Approvers |
|--------------|--------|-------------------|
| < $10,000 | 2-of-3 | CFO, CEO |
| $10,000 - $50,000 | 3-of-5 | CFO, CEO, COO |
| > $50,000 | 4-of-7 | CFO, CEO, COO, Board |

### Role Definitions

| Role | Permissions | Example Users |
|------|-------------|---------------|
| **Viewer** | Read-only | Analysts |
| **Proposer** | Create proposals | Department heads |
| **Approver** | Approve/reject | CFO, CEO, COO |
| **Admin** | Manage roles | Treasury lead |
| **Super Admin** | Emergency override | CEO only |

---

## Proposal Statuses

| Status | Icon | Description | Next Step |
|--------|------|-------------|-----------|
| `PENDING_APPROVAL` | ⏳ | Awaiting signatures | Approvers review |
| `PARTIALLY_APPROVED` | 🔄 | Some signatures | More approvals needed |
| `APPROVED` | ✅ | All signatures | Auto-execute |
| `REJECTED` | ❌ | Declined | Proposal cancelled |
| `EXECUTED` | 🎉 | Complete | Archived |
| `CANCELLED` | 🚫 | Withdrawn | No further action |

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-29 | Initial specification |

---

**End of Multi-Sig Coordinator Agent Shortcuts**
