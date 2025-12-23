# 01 - Onboarding & Auth

> **User Journey Stage**: The Entry
> **Goal**: Guide the user from "Stranger" to "Verified User".

## 📖 Overview
This directory contains the documentation for the initial user experience. This is the **critical first impression**. The focus is on friction reduction while ensuring security and compliance.

## 🧩 Modules
1.  **Authentication (`FRONTEND_USER_AUTH_LOGIN.md`)**:
    - Privy-based login (Email, Wallet, Social).
    - JWT Session management.
2.  **KYC (`FRONTEND_USER_ONBOARDING_KYC.md`)**:
    - Identity verification flow (Sumsub/Persona).
    - Risk scoring.
3.  **Welcome & Setup (`FRONTEND_USER_ONBOARDING_WELCOME.md`)**:
    - Initial profile creation.
    - Default preference selection.

## 🎨 UX Guidelines
- **Progressive Profiling**: Don't ask for everything at once.
- **Fail Gracefully**: If KYC hangs, allow "Guest Mode" if possible.
- **Immediate Value**: Show the Dashboard teaser during loading states.
