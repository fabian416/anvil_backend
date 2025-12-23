# FRONTEND_USER_SUPPORT_MAIN

> **Enterprise Grade Specification**
> Version: 2.0.0
> Status: **Live**
> Source Validation: *No API Backend - Static/External*

## 1. Module Overview
The **Support** module in the current MVP is primarily frontend-driven, linking to external resources or static content.

---

## 2. Features

### 2.1 Help Center
*   **Implementation**: Static Markdown rendered in-app or link to Gitbook/Notion.
*   **API**: None (Client-side routing).

### 2.2 Submit Ticket
*   **Implementation**: `mailto:support@anvil.com` or integration with Intercom/Zendesk widget.
*   **API**: None (Third-party SDK).

### 2.3 FAQs
*   **Implementation**: Hardcoded JSON in frontend codebase.
*   **API**: None.

---

## 3. Future Roadmap
*   **Ticket API**: `POST /api/v1/support/tickets` (Planned V2).
*   **Chatbot**: Integration with Anvil Chat Agent (Planned V2).
