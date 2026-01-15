"""Hunter AI sentiment analysis endpoints.

REST API endpoints for cryptocurrency sentiment analysis.
"""

from typing import Annotated, Optional
from fastapi import APIRouter, Query, HTTPException, status
from pydantic import BaseModel, Field
from datetime import datetime, UTC

from app.application.hunter.twitter_sentiment import (
    TwitterSentimentAnalyzer,
    TwitterConfig,
)
from app.application.hunter.reddit_sentiment import (
    RedditSentimentAnalyzer,
    RedditConfig,
)
from app.application.hunter.discord_sentiment import (
    DiscordSentimentAnalyzer,
    DiscordConfig,
)
from app.application.hunter.news_sentiment import (
    NewsSentimentAnalyzer,
    NewsConfig,
)
from app.application.hunter.sentiment_aggregator import SentimentAggregator
from app.domain.value_objects.sentiment import SentimentSource


class SentimentResponse(BaseModel):
    """Response model for sentiment analysis."""

    token_symbol: str = Field(..., description="Token symbol (e.g., ETH)")
    overall_score: float = Field(..., ge=0, le=100, description="Overall sentiment score (0-100)")
    classification: str = Field(..., description="Sentiment classification")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score (0-1)")
    signal_strength: str = Field(..., description="Signal strength (strong/moderate/weak)")
    timestamp: datetime = Field(..., description="Analysis timestamp")
    
    # Source breakdown
    sources: dict = Field(..., description="Per-source sentiment breakdown")
    source_count: int = Field(..., description="Number of sources analyzed")
    
    # Divergence analysis
    has_divergence: bool = Field(..., description="Whether sources have divergent signals")
    consensus: float = Field(..., ge=0, le=1, description="Consensus level (0-1)")


class TrendingTokenResponse(BaseModel):
    """Response model for trending tokens."""

    symbol: str = Field(..., description="Token symbol")
    mentions: int = Field(..., description="Number of mentions")
    sentiment: float = Field(..., ge=0, le=100, description="Average sentiment score")


class SentimentHistoryResponse(BaseModel):
    """Response model for sentiment history."""

    token_symbol: str
    period_hours: int
    current_score: float
    previous_score: float
    change_percent: float
    direction: str
    momentum: str


def create_sentiment_router() -> APIRouter:
    """Create sentiment analysis router."""
    router = APIRouter(prefix="/user/hunter/sentiment", tags=["hunter-sentiment"])

    @router.get(
        "/analyze/{token_symbol}",
        response_model=SentimentResponse,
        summary="Analyze token sentiment",
        description="Analyze cryptocurrency sentiment from multiple sources (Twitter, Reddit, Discord, News)",
    )
    async def analyze_token_sentiment(
        token_symbol: str,
        hours: int = Query(24, ge=1, le=168, description="Hours of historical data"),
        sources: Optional[str] = Query(
            None,
            description="Comma-separated sources to analyze (twitter,reddit,discord,news). All if not specified.",
        ),
    ) -> SentimentResponse:
        """Analyze sentiment for a cryptocurrency token.

        Aggregates sentiment from multiple sources:
        - Twitter: Social media sentiment
        - Reddit: Community discussions
        - Discord: Real-time chat sentiment
        - News: Media coverage

        Args:
            token_symbol: Token symbol (e.g., "ETH")
            hours: Hours of historical data to analyze
            sources: Specific sources to analyze (optional)

        Returns:
            SentimentResponse with aggregated sentiment analysis

        Example:
            GET /api/v1/hunter/sentiment/analyze/ETH?hours=24

            Response:
            {
                "token_symbol": "ETH",
                "overall_score": 72.5,
                "classification": "bullish",
                "confidence": 0.85,
                "signal_strength": "strong",
                "sources": {
                    "twitter": {"score": 75, "confidence": 0.88, "weight": 0.35},
                    "reddit": {"score": 68, "confidence": 0.82, "weight": 0.25}
                },
                "has_divergence": false,
                "consensus": 0.92
            }
        """
        try:
            # Parse sources if specified
            source_list = None
            if sources:
                source_names = [s.strip().lower() for s in sources.split(",")]
                source_list = [
                    SentimentSource(name)
                    for name in source_names
                    if name in [s.value for s in SentimentSource]
                ]

            # Initialize analyzers
            twitter_analyzer = TwitterSentimentAnalyzer(TwitterConfig(enabled=True))
            reddit_analyzer = RedditSentimentAnalyzer(RedditConfig(enabled=True))
            discord_analyzer = DiscordSentimentAnalyzer(DiscordConfig(enabled=True))
            news_analyzer = NewsSentimentAnalyzer(NewsConfig(enabled=True))
            aggregator = SentimentAggregator()

            # Collect sentiment readings
            readings = []

            # Twitter sentiment
            if not source_list or SentimentSource.TWITTER in source_list:
                twitter_reading = await twitter_analyzer.analyze_token_sentiment(
                    token_symbol, hours
                )
                readings.append(twitter_reading)

            # Reddit sentiment
            if not source_list or SentimentSource.REDDIT in source_list:
                reddit_reading = await reddit_analyzer.analyze_token_sentiment(
                    token_symbol, hours
                )
                readings.append(reddit_reading)

            # Discord sentiment
            if not source_list or SentimentSource.DISCORD in source_list:
                discord_reading = await discord_analyzer.analyze_token_sentiment(
                    token_symbol, hours
                )
                readings.append(discord_reading)

            # News sentiment (NEW - Day 3)
            if not source_list or SentimentSource.NEWS in source_list:
                news_reading = await news_analyzer.analyze_token_sentiment(
                    token_symbol, hours
                )
                readings.append(news_reading)

            if not readings:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No valid sources specified or no data available",
                )

            # Aggregate sentiment
            aggregated = aggregator.aggregate(readings, token_symbol)

            # Get source breakdown
            source_breakdown = aggregator.get_source_breakdown(aggregated)

            # Identify divergence
            divergence = aggregator.identify_divergence(aggregated)

            return SentimentResponse(
                token_symbol=token_symbol,
                overall_score=aggregated.overall_score,
                classification=aggregated.classification.value,
                confidence=aggregated.overall_confidence,
                signal_strength=aggregated.signal_strength,
                timestamp=aggregated.timestamp,
                sources=source_breakdown,
                source_count=aggregated.source_count,
                has_divergence=divergence["has_divergence"],
                consensus=divergence["consensus"],
            )

        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Sentiment analysis failed: {str(e)}",
            )

    @router.get(
        "/trending",
        response_model=list[TrendingTokenResponse],
        summary="Get trending tokens",
        description="Get cryptocurrency tokens trending on social media",
    )
    async def get_trending_tokens(
        limit: int = Query(10, ge=1, le=50, description="Maximum number of tokens"),
        source: SentimentSource = Query(
            SentimentSource.TWITTER,
            description="Source to check for trending tokens",
        ),
    ) -> list[TrendingTokenResponse]:
        """Get trending cryptocurrency tokens.

        Args:
            limit: Maximum number of tokens to return
            source: Source to analyze (currently only Twitter supported)

        Returns:
            List of trending tokens with mention counts and sentiment

        Example:
            GET /api/v1/hunter/sentiment/trending?limit=5

            Response:
            [
                {
                    "symbol": "BTC",
                    "mentions": 12450,
                    "sentiment": 68.5
                },
                {
                    "symbol": "ETH",
                    "mentions": 8920,
                    "sentiment": 72.3
                }
            ]
        """
        try:
            if source == SentimentSource.TWITTER:
                twitter_analyzer = TwitterSentimentAnalyzer()
                trending = await twitter_analyzer.get_trending_tokens(limit)
                return [
                    TrendingTokenResponse(
                        symbol=t["symbol"],
                        mentions=t["mentions"],
                        sentiment=t["sentiment"],
                    )
                    for t in trending
                ]
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Source {source.value} not yet supported for trending",
                )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get trending tokens: {str(e)}",
            )

    @router.get(
        "/compare",
        response_model=dict,
        summary="Compare sentiment across tokens",
        description="Compare sentiment analysis for multiple tokens",
    )
    async def compare_token_sentiment(
        tokens: str = Query(..., description="Comma-separated token symbols (e.g., ETH,BTC,SOL)"),
        hours: int = Query(24, ge=1, le=168, description="Hours of historical data"),
    ) -> dict:
        """Compare sentiment across multiple tokens.

        Args:
            tokens: Comma-separated token symbols
            hours: Hours of historical data

        Returns:
            Dictionary with sentiment comparison

        Example:
            GET /api/v1/hunter/sentiment/compare?tokens=ETH,BTC,SOL&hours=24

            Response:
            {
                "comparison": [
                    {"token": "ETH", "score": 72.5, "classification": "bullish"},
                    {"token": "BTC", "score": 68.3, "classification": "bullish"},
                    {"token": "SOL", "score": 65.8, "classification": "bullish"}
                ],
                "highest_sentiment": "ETH",
                "lowest_sentiment": "SOL",
                "average_sentiment": 68.87
            }
        """
        try:
            token_list = [t.strip().upper() for t in tokens.split(",")]

            if len(token_list) > 10:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Maximum 10 tokens can be compared at once",
                )

            # Analyze each token
            twitter_analyzer = TwitterSentimentAnalyzer()
            results = []

            for token in token_list:
                reading = await twitter_analyzer.analyze_token_sentiment(token, hours)
                results.append({
                    "token": token,
                    "score": reading.score,
                    "classification": reading.classification.value,
                    "confidence": reading.confidence,
                })

            # Calculate comparison metrics
            scores = [r["score"] for r in results]
            avg_sentiment = sum(scores) / len(scores)
            highest = max(results, key=lambda x: x["score"])
            lowest = min(results, key=lambda x: x["score"])

            return {
                "comparison": results,
                "highest_sentiment": highest["token"],
                "lowest_sentiment": lowest["token"],
                "average_sentiment": round(avg_sentiment, 2),
                "timestamp": datetime.now(UTC).isoformat(),
            }

        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Comparison failed: {str(e)}",
            )

    @router.get(
        "/news/headlines",
        response_model=list[dict],
        summary="Get top crypto news headlines",
        description="Get top cryptocurrency news headlines with sentiment scores",
    )
    async def get_top_headlines(
        limit: int = Query(10, ge=1, le=50, description="Maximum number of headlines"),
    ) -> list[dict]:
        """Get top cryptocurrency news headlines.

        Args:
            limit: Maximum number of headlines to return

        Returns:
            List of top headlines with sentiment

        Example:
            GET /api/v1/hunter/sentiment/news/headlines?limit=5

            Response:
            [
                {
                    "title": "Bitcoin Reaches New All-Time High",
                    "source": "coindesk.com",
                    "sentiment": 85.0,
                    "published": "2025-12-03T10:30:00Z"
                }
            ]
        """
        try:
            news_analyzer = NewsSentimentAnalyzer()
            headlines = await news_analyzer.get_top_headlines(limit)
            return headlines

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get headlines: {str(e)}",
            )

    return router
