# Admin Module: Project Configuration

> **Technical Specification**: `FRONTEND_ADMIN_CONFIG_PROJECTS`
> **Base URL**: `/api/admin/config/projects`

## 📖 Overview
**Project Configuration** manages global defaults and tenant-specific settings. This is where global feature flags and system-wide constants are defined.

### Key Capabilities
1.  **Feature Flags**: Toggle features (e.g., "Maintenance Mode", "Beta Features") on/off.
2.  **Global Variables**: Set system constants (e.g., "Default Max Token Limit").

---

## 🔌 API Endpoints

### 1. Get Configuration
**GET** `/api/admin/config/projects/global`
Retrieve the current global configuration.

**Response**:
```json
{
  "maintenance_mode": false,
  "beta_features_enabled": true,
  "default_language": "en-US",
  "support_email": "help@anvil.com"
}
```

### 2. Update Configuration
**PATCH** `/api/admin/config/projects/global`
Update specific settings.

**Request**:
```json
{
  "maintenance_mode": true
}
```

---

## 🎨 UI/UX Guidelines

- **Dangerous Actions**: Toggling "Maintenance Mode" should trigger a distinct warning (e.g., "This will disconnect all active users").
- **Audit Trail**: Every change here should ideally be logged to the Audit Log.
