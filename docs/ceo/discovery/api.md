Discovery Module APIs - Complete Provider List (2026)
📰 News APIs (Crypto/DeFi/Politics/Tech Coverage)
Tier 1 - Production Ready
Provider	Free Tier	Paid Plans	Keywords/Filter	Crypto/DeFi Coverage
CryptoPanic	100 req/day	$99/mo (100k/day)	categories=defi,nft,regulation	✅ Best (300+ sources)
CoinGecko News	50 calls/min	$129/mo (500/min)	search=DeFi, categories=news	✅ Excellent + market data
NewsAPI.org	100 req/day	$449/mo (1M/mo)	q=DeFi OR Aave OR Morpho	✅ Good general + crypto filter
CryptoCompare	250k calls/mo	$79/mo (1M/mo)	categories=cryptocurrency	✅ Specialized crypto
Tier 2 - Specialized
Provider	Free Tier	Features	Best For
TheNewsAPI	200 req/day	Sentiment analysis, 3k+ topics	DeFi, Politics filtering
NewsData.io	200 req/day	Multilingual, crypto-specific	Latin America, Argentina
LunarCrush	Limited	Social sentiment + news	Tech startups, Big Tech
💰 DeFi Vaults APIs (Morpho/Aave TVL/APY)
Tier 1 - Production Ready
Provider	Free Tier	Data Coverage	Endpoints
vaults.fyi API	✅ Free	Morpho, Aave, 75+ protocols	/v2/vaults, /v2/vaults/{id}
DeFiLlama API	✅ Free	TVL, APY, all chains	/protocols, /yields
Morpho Blue API	✅ Free	Morpho-specific	/markets, /vaults
TokenTerminal	Limited	Protocol metrics	/protocols/morpho
Tier 2 - Protocol Direct
bash
# Morpho Direct
https://api.morpho.org/blue/markets?chain_id=8453  # Base

# Aave V3
https://api.aave.com/v3/pools/base  # Base pool data

# Yearn Finance
https://api.yearn.finance/v1/chains/8453/vaults
🏗️ Recommended Production Stack
Primary News (80% coverage)
python
PROVIDERS = {
    "cryptopanic": {
        "url": "https://cryptopanic.com/api/v1/posts/",
        "params": {
            "auth_token": env.CRYPTO_PANIC_KEY,
            "categories": "defi,trading,regulation",
            "currencies": "USD,ETH,BTC"
        },
        "rate_limit": 100  # req/day free
    },
    "coingecko": {
        "url": "https://api.coingecko.com/api/v3/news",
        "rate_limit": 50   # calls/min free
    },
    "newsapi": {
        "url": "https://newsapi.org/v2/everything",
        "params": {"q": "DeFi OR Aave OR Morpho", "apiKey": env.NEWSAPI_KEY},
        "rate_limit": 100  # req/day free
    }
}
Primary Vaults (100% coverage)
python
VAULT_PROVIDERS = {
    "vaults_fyi": {
        "url": "https://api.vaults.fyi/v2/vaults",
        "free": True,
        "protocols": ["morpho", "aave", "euler"]
    },
    "defillama": {
        "url": "https://yields.llama.fi/pools",
        "free": True
    }
}
📊 Celery Collection Implementation
python
@app.task(rate_limit="10/m")
def collect_news(section: str, subsection: str):
    """Collect per subsection with keyword mapping."""
    keywords = INTEREST_KEYWORDS[subsection]  # "trump", "AI", "biotech"
    
    articles = []
    for provider, config in NEWS_PROVIDERS.items():
        try:
            response = requests.get(config["url"], params={**config["params"], "q": keywords})
            articles.extend(response.json()["articles"][:10])
        except:
            continue
    
    # Dedupe + classify + store
    unique_articles = dedupe_articles(articles)
    store_news(unique_articles, [section, subsection])
    return len(unique_articles)

KEYWORD_MAP = {
    "us_politics": ["trump", "biden", "election", "congress"],
    "ai": ["artificial intelligence", "machine learning", "deep learning"],
    "biotech": ["biotechnology", "CRISPR", "mRNA", "gene editing"],
    "morpho": ["morpho", "defi lending", "peer-to-peer lending"]
}
🚀 Immediate Implementation Priority
Phase 1 (Today)
text
✅ 1. CryptoPanic API (best crypto/DeFi coverage)
✅ 2. vaults.fyi API (Morpho/Aave TVL/APY) 
✅ 3. DeFiLlama yields (backup)
Phase 2 (Week 1)
text
NewsAPI.org (politics/tech general)
CoinGecko News (crypto-specific)
Free Tier Limits
text
CryptoPanic: 100 req/day → 3k articles/mo → 50 users daily feeds
vaults.fyi: Unlimited → Real-time TVL/APY
DeFiLlama: Unlimited → Complete vault coverage
🔧 API Key Setup
bash
# Sign up (all free tiers available)
1. https://cryptopanic.com/developers/api/ → $0 starter
2. https://api.vaults.fyi → Free registration  
3. https://newsapi.org → 100 req/day free
Start with CryptoPanic + vaults.fyi—covers 90% of your discovery needs immediately. Deploy Celery collectors on x2gd Spot workers. Perfect match for Anvil news + vaults module.