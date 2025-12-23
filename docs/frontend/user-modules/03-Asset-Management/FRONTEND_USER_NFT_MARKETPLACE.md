# FRONTEND_USER_NFT_MARKETPLACE

> **Enterprise Grade Specification**
> Version: 2.0.0
> Status: **Live**
> Source Validation: `src/app/presentation/http/controllers/nft/opensea_router.py` & `opensea_schemas.py`

## 1. Module Overview
The **NFT Marketplace** module integrates with **OpenSea** to provide portfolio tracking, floor price valuation, and collection analytics.

**Base URL**: `/api/v1/opensea`

---

## 2. Endpoints

### 2.1 Get NFT Portfolio
**GET** `/api/v1/opensea/portfolio/{address}`

Retrieves user's NFTs with total valuation.

*   **Query Params**: `chain` (default `ethereum`), `include_valuation` (bool).

**Response (200 OK):**
```json
{
  "address": "0x...",
  "chain": "ethereum",
  "total_value_eth": "12.5",
  "total_value_usd": "31250.00",
  "total_count": 5,
  "nfts": [
    {
      "identifier": "123",
      "display_name": "Bored Ape #123",
      "collection_slug": "boredapeyachtclub",
      "image_url": "https://...",
      "last_sale_price": "85.0"
    }
  ]
}
```

### 2.2 Get Collection Stats
**GET** `/api/v1/opensea/collections/{slug}/stats`

Market data for a specific collection.

**Response (200 OK):**
```json
{
  "stats": {
    "floor_price": "12.5",
    "floor_price_usd": "31250.00",
    "one_day_volume": "450.0",
    "num_owners": 6400,
    "is_trending": true
  },
  "market_sentiment": "BULLISH",
  "floor_change_alert": "SIGNIFICANT_RISE"
}
```

### 2.3 Get Listings
**GET** `/api/v1/opensea/collections/{slug}/listings`

Active listings for a collection.

**Response (200 OK):**
```json
{
  "listings": [
    {
      "token_id": "456",
      "price": "12.6",
      "price_usd": "31500.00",
      "expiration_date": "2024-02-01T00:00:00Z"
    }
  ],
  "count": 50
}
```

---

## 3. Error Handling

| Status | Code | Meaning |
| :--- | :--- | :--- |
| 404 | `COLLECTION_NOT_FOUND` | Slug validation failed. |
| 429 | `RATE_LIMIT_EXCEEDED` | OpenSea API quota hit. |
