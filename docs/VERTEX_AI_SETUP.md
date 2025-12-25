# Vertex AI / Gemini API Setup Guide

## Overview

This guide helps you configure Google Cloud Vertex AI and Gemini API for the distillation system.

## Current Configuration

**Project Details:**
- Project ID: `atlantean-field-480121-i2`
- Project Number: `369224500418`
- API Key: Stored in `config/local/.secrets.toml`
- Location: `us-central1`
- Model: `gemini-1.5-flash`

## Required APIs

Before using Vertex AI, you must enable the following APIs in your Google Cloud project:

### 1. Generative Language API (Gemini)

**Enable at:** https://console.developers.google.com/apis/api/generativelanguage.googleapis.com/overview?project=369224500418

This API is required for the Gemini models (faster, simpler authentication with API key).

### 2. Vertex AI API

**Enable at:** https://console.cloud.google.com/apis/library/aiplatform.googleapis.com?project=atlantean-field-480121-i2

This API is required for advanced Vertex AI features.

## Setup Steps

### Option 1: API Key (Recommended for Development)

1. **Enable the Generative Language API:**
   - Visit: https://console.developers.google.com/apis/api/generativelanguage.googleapis.com/overview?project=369224500418
   - Click "Enable API"
   - Wait 2-5 minutes for propagation

2. **API Key is already configured:**
   - Location: `config/local/.secrets.toml`
   - Section: `[vertex_ai]`
   - Key: `API_KEY = "AIzaSyBcFG0fFOr9T0LLn7STcOy0qQ_vEQxg4sU"`

3. **Test the configuration:**
   ```bash
   make test-vertex-ai
   ```

### Option 2: Service Account (Recommended for Production)

1. **Create a service account:**
   - Go to: https://console.cloud.google.com/iam-admin/serviceaccounts?project=atlantean-field-480121-i2
   - Click "Create Service Account"
   - Name: `vertex-ai-distillation`
   - Grant role: "Vertex AI User"

2. **Download JSON credentials:**
   - Click on the service account
   - Go to "Keys" tab
   - Click "Add Key" → "Create New Key" → "JSON"
   - Save to: `config/local/vertex-ai-credentials.json`

3. **Update configuration:**
   Edit `config/local/config.toml`:
   ```toml
   [distillation.vertex_ai]
   credentials_path = "config/local/vertex-ai-credentials.json"
   ```

4. **Test the configuration:**
   ```bash
   make test-vertex-ai
   ```

## Verifying Setup

### Quick Test

```bash
make test-vertex-ai
```

This runs a comprehensive test suite that checks:
1. Google Generative AI SDK (direct API key usage)
2. Vertex AI SDK (service account or default credentials)
3. Distillation system integration

### Expected Output (Success)

```
============================================================
TEST SUMMARY
============================================================
✅ PASSED: Google Generative AI SDK
✅ PASSED: Vertex AI SDK
✅ PASSED: Distillation Integration

Total: 3/3 tests passed

🎉 All tests passed! Vertex AI is configured correctly.
```

### Common Errors

#### 1. API Not Enabled

**Error:**
```
403 Generative Language API has not been used in project 369224500418 before or it is disabled.
```

**Solution:**
- Enable the API: https://console.developers.google.com/apis/api/generativelanguage.googleapis.com/overview?project=369224500418
- Wait 2-5 minutes for changes to propagate

#### 2. Invalid API Key

**Error:**
```
google.api_core.exceptions.InvalidArgument: 400 API key not valid
```

**Solution:**
- Verify the API key in `.secrets.toml`
- Generate a new API key at: https://console.cloud.google.com/apis/credentials?project=atlantean-field-480121-i2

#### 3. Missing Credentials

**Error:**
```
DefaultCredentialsError: Your default credentials were not found
```

**Solution:**
- Use API key authentication (Option 1)
- OR set up service account credentials (Option 2)

## Usage in Application

### Distillation System

The distillation system is already configured to use Vertex AI:

```toml
# config/local/config.toml
[distillation]
enabled = true
provider = "vertex_ai"  # Primary provider
fallback_provider = "deepinfra"  # Fallback if Vertex AI fails
```

### Making API Calls

The application automatically uses Vertex AI when the distillation provider is set to `vertex_ai`. The system will:

1. Try API key authentication first (if configured)
2. Fall back to service account credentials
3. Fall back to default application credentials
4. Use fallback provider if all fail (if `fail_open = true`)

## Cost Monitoring

### Gemini 1.5 Flash Pricing

- **Input:** $0.075 per 1M tokens
- **Output:** $0.30 per 1M tokens

### Typical Request Cost

For distillation (input: ~200 tokens, output: ~50 tokens):
- Cost per request: ~$0.000015 (< 2 cents per 1000 requests)

### Monitoring Usage

Check usage in Google Cloud Console:
https://console.cloud.google.com/apis/api/generativelanguage.googleapis.com/quotas?project=369224500418

## Configuration Files

### Main Configuration
**File:** `config/local/config.toml`
```toml
[distillation.vertex_ai]
project_id = "atlantean-field-480121-i2"
project_number = "369224500418"
location = "us-central1"
credentials_path = ""  # Optional service account path
api_key = ""  # Loaded from secrets
model = "gemini-1.5-flash"
```

### Secrets
**File:** `config/local/.secrets.toml`
```toml
[vertex_ai]
API_KEY = "AIzaSyBcFG0fFOr9T0LLn7STcOy0qQ_vEQxg4sU"
PROJECT_ID = "atlantean-field-480121-i2"
PROJECT_NUMBER = "369224500418"
```

## Next Steps

1. ✅ Enable Generative Language API (see link above)
2. ✅ Run test: `make test-vertex-ai`
3. ✅ Monitor costs in Google Cloud Console
4. ✅ Set up billing alerts (recommended)

## Support

For issues or questions:
- Google Cloud Support: https://cloud.google.com/support
- Vertex AI Documentation: https://cloud.google.com/vertex-ai/docs
- Gemini API Documentation: https://ai.google.dev/docs
