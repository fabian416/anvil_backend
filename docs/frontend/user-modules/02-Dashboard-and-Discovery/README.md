# 02 - Dashboard & Discovery

> **User Journey Stage**: The Hub
> **Goal**: Provide an "At a Glance" overview and efficient discovery paths.

## 📖 Overview
The Dashboard is the landing pad (`/home`). It must synthesize complex data (Portfolio, Markets, Notifications) into actionable insights. It serves as the jumping-off point for all other actions.

## 🧩 Modules
1.  **Dashboard (`FRONTEND_USER_HOME_DASHBOARD.md`)**:
    - High-level portfolio summary.
    - Active agent status.
    - Quick actions.
2.  **Markets (`FRONTEND_USER_HOME_MARKETS.md`)**:
    - Token discovery and price feeds.
    - Trending assets.
3.  **Notifications (`FRONTEND_USER_NOTIFICATIONS_MAIN.md`)**:
    - System alerts, price triggers, and social pings.
    - **Alerts** (`FRONTEND_USER_ALERTS_PRICE.md`).

## 🎨 UX Guidelines
- **Information Hierarchy**: Critical alerts > Portfolio Value > Market Trends.
- **Performance**: This page MUST load in <1.5s. Use skeleton loaders.
- **Scannability**: Use clean data visualization (sparklines) over raw tables.
