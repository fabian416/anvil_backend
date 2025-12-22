# Module: Support Center

**Route**: `/support`
**Auth Required**: No (Public FAQ) / Yes (Tickets)
**Package**: `user/support`

## 1. Overview
Help center and ticket management.

## 2. Integration
**Status**: Third-Party Integration Planned (Intercom / Zendesk).
**Current State**:
- Static FAQ links.
- "Contact Us" `mailto` link.

## 3. Implementation Flow
1.  **Mount**: Load Intercom Widget (if configured).
2.  **Fallback**: Show "Email Support" button if Widget fails.
