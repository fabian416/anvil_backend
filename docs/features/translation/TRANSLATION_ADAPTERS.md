# Translation Adapters Documentation

Enterprise-grade multi-language support using DeepL and Google Cloud Translation APIs.

## Overview

The translation system provides high-quality neural machine translation with support for 30+ languages (DeepL) and 100+ languages (Google Cloud Translation). Both adapters implement the `TranslationAdapter` port, following hexagonal architecture principles.

## Architecture

```
Domain Layer:
├── ports/translation_adapter.py          # Port interface
├── value_objects/chat/translation.py     # TranslationResult, SupportedLanguage
└── exceptions/translation.py             # Translation-specific exceptions

Infrastructure Layer:
├── adapters/external/deepl_translation_adapter.py       # DeepL implementation
└── adapters/external/google_translate_adapter.py        # Google implementation

Application Layer:
└── [Use TranslationAdapter port in interactors]

Configuration:
├── setup/config/translation.py           # Translation settings
└── setup/ioc/translation.py              # Dependency injection
```

## Features

### DeepL Translation Adapter

**Strengths:**
- High-quality translations (often considered best-in-class)
- 30+ supported languages
- Formality control (formal/informal) for 10+ languages
- Context-aware translation
- Glossary support for consistent terminology
- Fast response times

**Configuration:**
```toml
[translation]
enabled = true
default_provider = "deepl"
deepl_api_key = "your-deepl-api-key"
deepl_formality = "default"  # Options: default, more, less, prefer_more, prefer_less
```

**Supported Languages:**
- English (EN-US)
- Spanish (ES)
- French (FR)
- German (DE)
- Italian (IT)
- Portuguese (PT-PT)
- Japanese (JA)
- Korean (KO)
- Chinese Simplified (ZH)
- Russian (RU)

**Formality Support:** German, French, Italian, Spanish, Dutch, Polish, Portuguese, Russian, Japanese

**Cost Structure (2025):**
- Free tier: 500,000 characters/month
- Pro: $25/month for 1M characters
- Additional: $5 per 250K characters

### Google Cloud Translation Adapter

**Strengths:**
- Comprehensive language coverage (100+ languages)
- All languages from our `SupportedLanguage` enum
- HTML translation support (preserves markup)
- Auto language detection with confidence scores
- Enterprise-grade reliability
- Advanced Neural Machine Translation (NMT)

**Configuration:**
```toml
[translation]
enabled = true
default_provider = "google"
google_project_id = "your-gcp-project-id"
google_location = "global"
google_credentials_path = "/path/to/credentials.json"  # Optional
google_enable_html = true
```

**Supported Languages:**
All languages in `SupportedLanguage` enum:
- English, Spanish, French, German, Italian, Portuguese
- Japanese, Korean, Chinese (Simplified & Traditional)
- Russian, Arabic
- Plus 90+ additional languages via Google

**Cost Structure (2025):**
- Translation (NMT): $20 per 1M characters
- Language detection: $20 per 1M characters
- With glossary: Additional $80 per 1M characters

## Usage

### Basic Translation

```python
from app.domain.ports.translation_adapter import TranslationAdapter
from app.domain.value_objects.chat.translation import SupportedLanguage

# Injected via Dishka
async def translate_message(
    translation_adapter: TranslationAdapter,
    message: str,
    target_lang: SupportedLanguage,
):
    result = await translation_adapter.translate_text(
        text=message,
        target_language=target_lang,
        source_language=None,  # Auto-detect
    )

    print(f"Original: {result.original_text}")
    print(f"Translated: {result.translated_text}")
    print(f"Confidence: {result.confidence_score:.2f}")
    print(f"Detected: {result.detected_language}")
```

### Batch Translation

```python
messages = [
    "Check the TVL for Aave",
    "What's the current ETH price?",
    "Show me my portfolio performance",
]

results = await translation_adapter.translate_batch(
    texts=messages,
    target_language=SupportedLanguage.SPANISH,
)

for result in results:
    print(f"{result.original_text} -> {result.translated_text}")
```

### Preserving Technical Terms

```python
from app.domain.value_objects.chat.translation import PreservedTermsConfig

# Default config preserves DeFi protocols, tokens, technical terms
preserve_config = PreservedTermsConfig()

result = await translation_adapter.translate_text(
    text="Deposit 100 USDC into Aave to earn 4.5% APY",
    target_language=SupportedLanguage.JAPANESE,
    preserve_terms=preserve_config,
)

# Output: "100 USDC を Aave に預けて 4.5% APY を獲得"
# USDC, Aave, and APY are preserved
```

### Language Detection

```python
detected_lang = await translation_adapter.detect_language(
    "Bonjour, comment allez-vous?"
)

print(detected_lang)  # SupportedLanguage.FRENCH
```

### HTML Translation (Google only)

```python
html_content = """
<h1>Welcome to DeFi</h1>
<p>Earn <strong>high APY</strong> on your crypto assets.</p>
<p>Protocols: <span>Aave</span>, <span>Compound</span>, <span>Curve</span></p>
"""

result = await google_adapter.translate_text(
    text=html_content,
    target_language=SupportedLanguage.SPANISH,
)

# HTML structure is preserved, only text is translated
```

## Configuration

### Full Configuration Example

```toml
[translation]
# Master switch
enabled = true

# Provider selection
default_provider = "deepl"  # Options: deepl, google, fallback

# DeepL configuration
deepl_api_key = "abc123..."
deepl_formality = "default"

# Google Cloud Translation
google_project_id = "my-gcp-project"
google_location = "global"
google_credentials_path = "/opt/gcp/credentials.json"
google_enable_html = true

# Performance
cache_ttl = 300  # 5 minutes

# Cost management
enable_cost_tracking = true
cost_limit_usd = 100.0  # Monthly limit

# Quality
min_confidence_score = 0.7

# Features
auto_detect_language = true
preserve_technical_terms = true
```

### Environment Variables

Alternatively, configure via environment variables:

```bash
# DeepL
DEEPL_API_KEY=abc123...

# Google Cloud
GOOGLE_PROJECT_ID=my-gcp-project
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
```

## Technical Implementation

### Term Preservation

Both adapters protect technical terms from translation using different strategies:

**DeepL (Placeholder Strategy):**
```python
# Original: "Stake 100 ETH in Lido for 4.5% APY"
# Protected: "Stake 100 __TERM_0__ in __TERM_1__ for 4.5% __TERM_2__"
# Translated: "Stake 100 __TERM_0__ en __TERM_1__ por 4.5% __TERM_2__"
# Restored: "Stake 100 ETH en Lido por 4.5% APY"
```

**Google (HTML Span Strategy):**
```python
# Protected: 'Stake 100 <span translate="no">ETH</span> in <span translate="no">Lido</span>'
# Google respects translate="no" attribute
# Result: "Stake 100 ETH en Lido por 4.5% APY"
```

### Caching Strategy

Translations are cached in Redis with 15-minute TTL by default:

```python
# Cache key format: api_cache:deepl:translate:<hash>
# Hash includes: text, target_language, source_language

# Automatic cache hit
result1 = await adapter.translate_text("Hello", SupportedLanguage.SPANISH)
result2 = await adapter.translate_text("Hello", SupportedLanguage.SPANISH)
# result2 is returned from cache instantly
```

### Cost Tracking

Both adapters track usage and costs:

```python
# Get usage statistics
stats = adapter.get_usage_stats()
print(f"Characters translated: {stats['total_characters']}")
print(f"Estimated cost: ${stats['estimated_cost_usd']:.2f}")

# DeepL: Get actual API usage
api_usage = await deepl_adapter.get_usage_from_api()
print(f"API quota: {api_usage['character_usage_percent']:.1f}%")
```

## Error Handling

### Exception Hierarchy

```python
from app.domain.exceptions.translation import (
    TranslationError,              # Base translation error
    TranslationAPIError,            # API communication error
    TranslationQuotaExceededError,  # Quota/rate limit exceeded
    UnsupportedLanguageError,       # Language not supported
    TextTooLongForTranslationError, # Text exceeds limits
    EmptyTextError,                 # Empty text provided
    LanguageDetectionError,         # Detection failed
    BatchTranslationError,          # Batch operation failed
)
```

### Error Handling Example

```python
try:
    result = await translation_adapter.translate_text(
        text=user_message,
        target_language=SupportedLanguage.JAPANESE,
    )
except TranslationQuotaExceededError as e:
    # Handle quota exceeded (retry later, use different provider)
    logger.error(f"Translation quota exceeded: {e.details}")
    return "Translation temporarily unavailable"

except UnsupportedLanguageError as e:
    # Handle unsupported language
    return f"Language {e.details['language']} is not supported"

except TranslationError as e:
    # Generic error handling
    logger.error(f"Translation failed: {e}")
    return "Translation error occurred"
```

## Performance Characteristics

### DeepL Performance
- **Latency:** 200-500ms for short texts
- **Max text length:** 50,000 characters
- **Batch size:** 50 texts, 130,000 total characters
- **Cache hit rate:** ~60-70% (typical)

### Google Translation Performance
- **Latency:** 300-700ms for short texts
- **Max text length:** 30,000 characters
- **Batch size:** 1,000 texts, 100,000 total characters
- **Cache hit rate:** ~60-70% (typical)

## Best Practices

### 1. Choose the Right Provider

**Use DeepL when:**
- Quality is paramount (business communications)
- Target audience is European (German, French, Spanish)
- You need formality control
- Budget allows ($25/month minimum)

**Use Google when:**
- You need maximum language coverage
- Translating HTML content
- Cost is a concern (pay-per-use)
- Need rare languages (100+ options)

### 2. Optimize Costs

```python
# ✅ Good: Cache-friendly patterns
await adapter.translate_text("Common phrase", SupportedLanguage.SPANISH)

# ✅ Good: Batch translations
await adapter.translate_batch(many_texts, target_lang)

# ❌ Bad: Translating unique, dynamic content frequently
await adapter.translate_text(f"Balance: {random_balance}", target_lang)
```

### 3. Handle Failures Gracefully

```python
# Implement fallback
try:
    result = await deepl_adapter.translate_text(text, target_lang)
except TranslationError:
    result = await google_adapter.translate_text(text, target_lang)
```

### 4. Preserve Context

```python
# Include context in translation
full_text = f"Context: DeFi protocol analysis\n\n{user_query}"
result = await adapter.translate_text(full_text, target_lang)
```

## Monitoring and Observability

### Metrics to Track

1. **Usage metrics:**
   - Characters translated per day/month
   - Cache hit rate
   - API error rate

2. **Cost metrics:**
   - Daily/monthly spend
   - Cost per translation
   - Quota utilization

3. **Quality metrics:**
   - Average confidence scores
   - User feedback on translations
   - Retry rates

### Logging

```python
# Adapters log important events
logger.info(f"DeepL translated {len(text)} chars from {src} to {tgt} in {ms}ms")
logger.warning(f"Cache miss for translation: {cache_key}")
logger.error(f"Translation API error: {error_details}")
```

## Testing

### Unit Tests

```python
import pytest
from app.domain.value_objects.chat.translation import SupportedLanguage

@pytest.mark.asyncio
async def test_translate_with_term_preservation(translation_adapter):
    result = await translation_adapter.translate_text(
        text="Deposit 100 USDC into Aave",
        target_language=SupportedLanguage.SPANISH,
        preserve_terms=PreservedTermsConfig(),
    )

    assert "USDC" in result.translated_text
    assert "Aave" in result.translated_text
    assert result.confidence_score >= 0.7
```

### Integration Tests

```python
@pytest.mark.integration
async def test_deepl_api_integration(deepl_adapter):
    result = await deepl_adapter.translate_text(
        "Hello world",
        SupportedLanguage.FRENCH,
    )
    assert result.translated_text == "Bonjour le monde"
```

## Migration Guide

### From Manual Translation

**Before:**
```python
# Manual translation dictionary
TRANSLATIONS = {
    "en": {"greeting": "Hello"},
    "es": {"greeting": "Hola"},
    "fr": {"greeting": "Bonjour"},
}

greeting = TRANSLATIONS[user_lang]["greeting"]
```

**After:**
```python
# Dynamic translation
result = await translation_adapter.translate_text(
    "Hello",
    target_language=user_preferences.language,
)
greeting = result.translated_text
```

## Troubleshooting

### Common Issues

**Issue: "DeepL quota exceeded"**
```toml
# Solution: Switch to Google or increase DeepL plan
[translation]
default_provider = "google"
```

**Issue: "Translation quality is poor"**
```toml
# Solution: Increase confidence threshold, use DeepL
[translation]
default_provider = "deepl"
min_confidence_score = 0.85
```

**Issue: "Technical terms are being translated"**
```python
# Solution: Ensure preserve_terms is configured
preserve_config = PreservedTermsConfig(
    protocols=["Aave", "Compound", "CustomProtocol"],
    tokens=["MYTOKEN"],
)
```

## Resources

### API Documentation
- [DeepL API Docs](https://www.deepl.com/docs-api)
- [Google Cloud Translation Docs](https://cloud.google.com/translate/docs)

### Getting Started
1. **DeepL:** Sign up at https://www.deepl.com/pro-api
2. **Google:** Enable Translation API in GCP Console

### Support
- Internal: Check `#translation-support` Slack channel
- DeepL: support@deepl.com
- Google: GCP Support Console
