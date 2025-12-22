# Translation Services - Quick Start Guide

Get translation services up and running in 5 minutes.

## Step 1: Install Dependencies

```bash
# Install translation libraries
uv pip install deepl>=1.18.0 google-cloud-translate>=3.15.0

# Verify installation
python -c "import deepl; import google.cloud.translate_v3; print('✓ Translation libraries installed')"
```

## Step 2: Get API Keys

### Option A: DeepL (Recommended for Quality)

1. Sign up at https://www.deepl.com/pro-api
2. Choose plan:
   - **Free:** 500,000 chars/month (good for testing)
   - **Pro:** $25/month for 1M chars (recommended for production)
3. Copy your API key

### Option B: Google Cloud Translation (Recommended for Coverage)

1. Create/select GCP project at https://console.cloud.google.com
2. Enable Translation API:
   ```bash
   gcloud services enable translate.googleapis.com
   ```
3. Create service account:
   ```bash
   gcloud iam service-accounts create translation-sa \
       --display-name="Translation Service Account"
   ```
4. Grant permissions:
   ```bash
   gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
       --member="serviceAccount:translation-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
       --role="roles/cloudtranslate.user"
   ```
5. Create and download key:
   ```bash
   gcloud iam service-accounts keys create ~/translation-key.json \
       --iam-account=translation-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com
   ```

## Step 3: Configure

### Update `config/local/config.toml`

```toml
[translation]
# Enable translation features
enabled = true

# Choose provider: "deepl" or "google"
default_provider = "deepl"

# DeepL configuration
deepl_api_key = "YOUR_DEEPL_API_KEY"
deepl_formality = "default"

# Google Cloud Translation (if using)
google_project_id = "YOUR_GCP_PROJECT_ID"
google_location = "global"
google_credentials_path = "/path/to/translation-key.json"

# Optional: Cost limit (USD per month)
cost_limit_usd = 100.0
```

### Or use environment variables

```bash
# DeepL
export DEEPL_API_KEY="your-key-here"

# Google Cloud
export GOOGLE_PROJECT_ID="your-project-id"
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/key.json"
```

## Step 4: Verify Setup

Create a test script `test_translation.py`:

```python
import asyncio
from app.setup.config.settings import load_settings
from app.setup.ioc.translation import TranslationAdapterProvider
from app.infrastructure.cache.external_api_cache import ExternalAPICache, CacheConfig
from app.domain.value_objects.chat.translation import SupportedLanguage
import redis.asyncio as aioredis


async def test_translation():
    # Load settings
    settings = load_settings()

    # Create Redis cache
    redis_client = aioredis.from_url("redis://localhost:6379")
    cache = ExternalAPICache(redis_client, CacheConfig())

    # Create adapter
    provider = TranslationAdapterProvider()
    adapter = provider.provide_translation_adapter(cache, settings)

    # Test translation
    result = await adapter.translate_text(
        text="Welcome to the future of DeFi!",
        target_language=SupportedLanguage.SPANISH,
    )

    print(f"✓ Translation successful!")
    print(f"  Original: {result.original_text}")
    print(f"  Translated: {result.translated_text}")
    print(f"  Confidence: {result.confidence_score:.2%}")

    # Test batch
    results = await adapter.translate_batch(
        texts=["Hello", "Goodbye", "Thank you"],
        target_language=SupportedLanguage.FRENCH,
    )

    print(f"\n✓ Batch translation successful!")
    for r in results:
        print(f"  {r.original_text} → {r.translated_text}")

    # Get usage stats
    stats = adapter.get_usage_stats()
    print(f"\n✓ Usage stats:")
    print(f"  Provider: {stats['provider']}")
    print(f"  Characters: {stats['total_characters']}")
    print(f"  Cost: ${stats['estimated_cost_usd']:.4f}")

    await redis_client.close()


if __name__ == "__main__":
    asyncio.run(test_translation())
```

Run the test:

```bash
python test_translation.py
```

Expected output:
```
✓ Translation successful!
  Original: Welcome to the future of DeFi!
  Translated: ¡Bienvenido al futuro de DeFi!
  Confidence: 89.00%

✓ Batch translation successful!
  Hello → Bonjour
  Goodbye → Au revoir
  Thank you → Merci

✓ Usage stats:
  Provider: DeepL
  Characters: 67
  Cost: $0.0017
```

## Step 5: Use in Your Code

### In an Interactor

```python
from dishka import FromDishka
from app.domain.ports.translation_adapter import TranslationAdapter
from app.domain.value_objects.chat.translation import (
    SupportedLanguage,
    PreservedTermsConfig,
)


class TranslateChatMessageInteractor:
    def __init__(
        self,
        translation_adapter: FromDishka[TranslationAdapter],
    ):
        self._translator = translation_adapter

    async def execute(
        self,
        message: str,
        target_language: SupportedLanguage,
    ) -> str:
        # Preserve DeFi terms
        preserve_config = PreservedTermsConfig()

        result = await self._translator.translate_text(
            text=message,
            target_language=target_language,
            preserve_terms=preserve_config,
        )

        return result.translated_text
```

### In a FastAPI Controller

```python
from fastapi import APIRouter, Depends
from dishka.integrations.fastapi import FromDishka
from pydantic import BaseModel

from app.domain.ports.translation_adapter import TranslationAdapter
from app.domain.value_objects.chat.translation import SupportedLanguage


router = APIRouter(prefix="/api/v1/translation", tags=["translation"])


class TranslateRequest(BaseModel):
    text: str
    target_language: str


class TranslateResponse(BaseModel):
    original_text: str
    translated_text: str
    confidence_score: float
    detected_language: str | None


@router.post("/translate", response_model=TranslateResponse)
async def translate_text(
    request: TranslateRequest,
    translator: FromDishka[TranslationAdapter],
):
    """Translate text to target language."""
    target_lang = SupportedLanguage(request.target_language)

    result = await translator.translate_text(
        text=request.text,
        target_language=target_lang,
    )

    return TranslateResponse(
        original_text=result.original_text,
        translated_text=result.translated_text,
        confidence_score=result.confidence_score,
        detected_language=result.detected_language.value if result.detected_language else None,
    )
```

## Common Use Cases

### 1. Translate Chat Messages

```python
async def translate_for_user(
    message: str,
    user_language: SupportedLanguage,
    translator: TranslationAdapter,
) -> str:
    """Translate message to user's preferred language."""
    if user_language == SupportedLanguage.ENGLISH:
        return message  # No translation needed

    result = await translator.translate_text(
        text=message,
        target_language=user_language,
        preserve_terms=PreservedTermsConfig(),
    )

    return result.translated_text
```

### 2. Multi-Language Support for Notifications

```python
async def send_notification_multilang(
    user_ids: list[str],
    message_en: str,
    translator: TranslationAdapter,
):
    """Send notification in each user's language."""
    for user_id in user_ids:
        user_lang = await get_user_language(user_id)

        if user_lang != SupportedLanguage.ENGLISH:
            translated = await translator.translate_text(
                message_en,
                user_lang,
            )
            message = translated.translated_text
        else:
            message = message_en

        await send_notification(user_id, message)
```

### 3. Translate Documentation

```python
async def translate_docs(
    html_content: str,
    target_langs: list[SupportedLanguage],
    translator: TranslationAdapter,  # Use Google for HTML support
) -> dict[str, str]:
    """Translate HTML documentation to multiple languages."""
    results = {}

    for lang in target_langs:
        result = await translator.translate_text(
            text=html_content,
            target_language=lang,
        )
        results[lang.value] = result.translated_text

    return results
```

## Troubleshooting

### Issue: "Translation features are disabled"

**Solution:** Enable in config
```toml
[translation]
enabled = true
```

### Issue: "DeepL API key is required"

**Solution:** Add API key
```toml
deepl_api_key = "your-key-here"
```

Or environment variable:
```bash
export DEEPL_API_KEY="your-key-here"
```

### Issue: "Permission denied" (Google)

**Solution:** Check service account permissions
```bash
gcloud projects get-iam-policy YOUR_PROJECT_ID \
    --filter="bindings.members:translation-sa@*" \
    --flatten="bindings[].members"
```

### Issue: Redis connection error

**Solution:** Start Redis
```bash
docker run -d -p 6379:6379 redis:latest
```

## Next Steps

1. **Review full documentation:** See `TRANSLATION_ADAPTERS.md`
2. **Set up monitoring:** Track usage and costs
3. **Implement user preferences:** Store language preferences in database
4. **Add to chat system:** Integrate with conversation handling
5. **Create glossaries:** Define custom terminology for your domain

## Production Checklist

- [ ] API keys configured in secure secret storage
- [ ] Cost limits set (`cost_limit_usd` in config)
- [ ] Redis caching enabled and configured
- [ ] Error handling implemented
- [ ] Monitoring and alerting set up
- [ ] Rate limiting configured
- [ ] Fallback provider configured (optional)
- [ ] Load testing completed
- [ ] Documentation updated for team

## Support

- **Documentation:** `docs/features/translation/`
- **Examples:** `examples/translation/`
- **Issues:** Create ticket in project management system
- **Slack:** #translation-support

## Cost Estimates

### DeepL Pricing
- **Small app** (10K msgs/day, 500 chars avg): ~$7.50/month
- **Medium app** (100K msgs/day): ~$75/month
- **Large app** (1M msgs/day): ~$750/month

### Google Cloud Translation
- **Small app** (10K msgs/day, 500 chars avg): ~$6/month
- **Medium app** (100K msgs/day): ~$60/month
- **Large app** (1M msgs/day): ~$600/month

*Assumes 50% cache hit rate. Actual costs may vary.*
