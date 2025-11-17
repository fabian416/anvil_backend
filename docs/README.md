# 📚 Anvil Platform - Documentation

## Documentation Structure

This directory contains all documentation for the Anvil DeFi Trading Platform, organized by category for easy navigation.

---

## 📁 Folder Organization

### 📋 [user_stories/](./user_stories/)
User stories, user flows, and requirements documentation
- `user_stories_for_devs.md` - Complete user stories for development team
- `anvil_user_flows_client_part1.md` - Client user flows (part 1)
- `anvil_user_flows_client_part2.md` - Client user flows (part 2)
- `anvil_user_flows_admin.md` - Admin user flows
- `anvil_user_flows_auditor.md` - Auditor user flows
- `anvil_user_flows_summary.md` - User flows summary

### 🗄️ [database/](./database/)
Database schemas, SQL files, and database guides
- `anvil_complete_database_implementation.sql` - Complete database schema (27 tables)
- `anvil_database_implementation_guide.md` - Database implementation guide
- `anvil_database_quick_reference.md` - Quick reference guide

### 🏗️ [architecture/](./architecture/)
Technical architecture and system design documents
- `03_technical_architecture.md` - Main technical architecture document
- `technical_architecture.md` - Alternative technical architecture
- `11_mobile_architecture.md` - Mobile app architecture
- `15_admin_portal_architecture.md` - Admin portal architecture

### 🔌 [api/](./api/)
API documentation and endpoint references
- `anvil_api_client_part1.md` - Client API endpoints (part 1)
- `anvil_api_client_part2.md` - Client API endpoints (part 2)
- `anvil_api_admin.md` - Admin API documentation
- `anvil_api_auditor.md` - Auditor API documentation
- `anvil_api_endpoints_client.md` - Client endpoints reference
- `anvil_api_endpoints_admin.md` - Admin endpoints reference
- `anvil_api_documentation_index.md` - API documentation index
- `api_endpoints_for_devs.md` - API endpoints for developers

### 📦 [product/](./product/)
Product requirements and specifications
- `13_product_requirements.md` - Complete Product Requirements Document (PRD)

### 🛠️ [implementation/](./implementation/)
Implementation guides, setup instructions, and development guides
- `implementation_guide.md` - Main implementation guide
- `04_integration_guide.md` - Integration guide
- `09_environment_setup_guide.md` - Environment setup guide
- `14_developer_onboarding.md` - Developer onboarding guide
- `10_code_style_guide.md` - Code style guide

### ⚙️ [operations/](./operations/)
DevOps, deployment, monitoring, and operational documentation
- `06_deployment_devops.md` - Deployment and DevOps guide
- `12_monitoring_observability.md` - Monitoring and observability
- `20_operations_runbook.md` - Operations runbook
- `16_disaster_recovery_plan.md` - Disaster recovery plan
- `18_performance_optimization.md` - Performance optimization guide
- `19_cost_optimization.md` - Cost optimization guide
- `17_rate_limiting_guide.md` - Rate limiting guide
- `22_data_migration_guide.md` - Data migration guide
- `23_faq_troubleshooting.md` - FAQ and troubleshooting

### 🔒 [security/](./security/)
Security and compliance documentation
- `05_security_compliance.md` - Security and compliance guide

### 💻 [development/](./development/)
Code files, models, and development resources
- `01_base_and_users.py` - Base configuration and user models
- `02_wallets_and_chains.py` - Wallet and chain models
- `03_transactions.py` - Transaction models
- `04_earn_and_save.py` - Earn and save models
- `05_perpetuals.py` - Perpetual trading models
- `06_ai_and_agents.py` - AI and agent models
- `07_subscriptions_and_payments.py` - Subscription and payment models
- `08_notifications.py` - Notification models
- `09_settings_and_audit.py` - Settings and audit models
- `07_testing_strategy.md` - Testing strategy document

### 📅 [project_management/](./project_management/)
Project timeline, milestones, and release management
- `08_project_timeline.md` - Project timeline and milestones
- `21_release_management.md` - Release management guide

### 📑 [indexes/](./indexes/)
Index files and master documentation indexes
- `00_START_HERE.md` - Start here guide
- `00_MASTER_INDEX.md` - Master index
- `00_FINAL_MASTER_INDEX.md` - Final master index
- `00_COMPLETE_PACKAGE_INDEX.md` - Complete package index
- `00_ABSOLUTE_FINAL_INDEX.md` - Absolute final index
- `INDEX.md` - General index

---

## 🚀 Quick Start

### For New Developers
1. Start with `indexes/00_START_HERE.md`
2. Read `product/13_product_requirements.md` to understand the product
3. Review `architecture/03_technical_architecture.md` for system design
4. Check `implementation/14_developer_onboarding.md` for setup instructions

### For Backend Developers
1. Review `database/anvil_database_implementation_guide.md`
2. Check `api/api_endpoints_for_devs.md` for API structure
3. Review `development/` folder for SQLAlchemy models
4. Read `implementation/09_environment_setup_guide.md` for setup

### For Frontend Developers
1. Review `user_stories/user_stories_for_devs.md` for requirements
2. Check `api/anvil_api_client_part1.md` and `anvil_api_client_part2.md` for API endpoints
3. Review `architecture/11_mobile_architecture.md` for mobile architecture

### For DevOps/Operations
1. Start with `operations/06_deployment_devops.md`
2. Review `operations/20_operations_runbook.md`
3. Check `operations/12_monitoring_observability.md`
4. Review `operations/16_disaster_recovery_plan.md`

---

## 📊 Documentation Statistics

- **Total Documents**: 60+ files
- **User Stories**: 6 files
- **Database**: 3 files
- **Architecture**: 4 files
- **API Documentation**: 8 files
- **Implementation Guides**: 5 files
- **Operations**: 9 files
- **Development**: 10 files
- **Project Management**: 2 files

---

## 🔍 Finding Documents

### By Topic

**Authentication & Users**
- `user_stories/user_stories_for_devs.md` (US-C01, US-C02)
- `database/anvil_database_implementation_guide.md` (Section 1)
- `development/01_base_and_users.py`

**Trading & Swaps**
- `user_stories/user_stories_for_devs.md` (US-C05, US-C06)
- `api/anvil_api_client_part1.md` (Section 3)

**Yield Farming (Earn)**
- `user_stories/user_stories_for_devs.md` (US-C07, US-C08, US-C09)
- `development/04_earn_and_save.py`

**Perpetual Trading**
- `user_stories/user_stories_for_devs.md` (US-C12, US-C13, US-C14)
- `development/05_perpetuals.py`

**AI Assistant**
- `user_stories/user_stories_for_devs.md` (US-C15, US-C16)
- `development/06_ai_and_agents.py`

**Database Schema**
- `database/anvil_complete_database_implementation.sql`
- `database/anvil_database_implementation_guide.md`

**API Endpoints**
- `api/anvil_api_client_part1.md`
- `api/anvil_api_client_part2.md`
- `api/anvil_api_admin.md`
- `api/anvil_api_auditor.md`

---

## 📝 Document Status

All documentation is organized and categorized. If you need to find a specific document:

1. Check the appropriate folder based on the document type
2. Use the indexes in `indexes/` folder
3. Search by filename pattern (e.g., `anvil_*` for Anvil-specific docs)

---

## 🔄 Maintenance

When adding new documentation:

1. **User Stories** → `user_stories/`
2. **Database** → `database/`
3. **Architecture** → `architecture/`
4. **API Docs** → `api/`
5. **Product Specs** → `product/`
6. **Implementation** → `implementation/`
7. **Operations** → `operations/`
8. **Security** → `security/`
9. **Code/Models** → `development/`
10. **Project Management** → `project_management/`
11. **Indexes** → `indexes/`

---

**Last Updated**: November 2025  
**Organization Status**: ✅ Complete
