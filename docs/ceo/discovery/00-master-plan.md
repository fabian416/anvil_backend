# Discovery Module — Implementation Plan (Master)

## Overview
The Discovery Module is Anvil's content aggregation layer — personalized news feed + DeFi vault opportunities. This plan breaks the full implementation spec into 7 discrete, implementation-ready documents.

## Deliverable Sequence — ALL COMPLETE ✅

| # | Document | Memory ID | Status |
|---|----------|-----------|--------|
| 1 | Architecture Spec | #1729 | ✅ Complete |
| 2 | C4 Diagrams (Mermaid) | #1730 | ✅ Complete |
| 3 | Database Schema | #1733 | ✅ Complete |
| 4 | Services Layer | #1736 | ✅ Complete |
| 5 | API Spec — User Endpoints | #1739 | ✅ Complete |
| 6 | API Spec — Admin Endpoints | #1742 | ✅ Complete |
| 7 | Celery Pipeline | #1745 | ✅ Complete |

## Tech Stack
- Backend: FastAPI + SQLAlchemy + Pydantic v2
- Database: PostgreSQL + TimescaleDB + Apache AGE (graph)
- Cache: Redis (TTL-based)
- Workers: Celery + Beat (gevent pool)
- Primary News: Perplexity Sonar API ($1/M tokens)
- Fallback News: NewsAPI, CryptoPanic, RSS feeds
- Vaults: DeFiLlama + Vaults.fyi
- GraphRAG: Gemini 2.0 Flash extraction → Apache AGE storage
- Architecture: Hexagonal (Clean Architecture)

## Cost Budget
- Perplexity Sonar: ~$609/mo
- GraphRAG extraction: ~$5/mo
- Infrastructure: Existing PostgreSQL + Redis (no extra services)
