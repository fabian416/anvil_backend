"""Reddit sentiment analysis service.

Analyzes Reddit posts and comments for cryptocurrency sentiment.
Based on Hunter AI Bot's Reddit integration.
"""

import re
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

from app.domain.value_objects.sentiment import (
    SentimentReading,
    SentimentSource,
)


@dataclass
class RedditConfig:
    """Configuration for Reddit sentiment analysis."""

    # Feature flags
    enabled: bool = True

    # API limits
    rate_limit: int = 60  # requests/minute (Reddit limit)
    max_posts_per_query: int = 100

    # Subreddits to monitor
    target_subreddits: List[str] = None

    # Analysis thresholds
    min_karma: int = 100  # Min post/comment karma
    min_upvote_ratio: float = 0.6  # Min upvote ratio
    high_confidence_threshold: float = 0.75

    # Cache settings
    cache_ttl_minutes: int = 15

    # Quality filters
    min_account_karma: int = 500
    min_account_age_days: int = 30

    def __post_init__(self):
        """Initialize default subreddits if not provided."""
        if self.target_subreddits is None:
            self.target_subreddits = [
                "cryptocurrency",
                "cryptomarkets",
                "defi",
                "ethereum",
                "bitcoin",
                "ethtrader",
                "satoshistreetbets",
            ]


class RedditSentimentAnalyzer:
    """Analyzes Reddit sentiment for cryptocurrency tokens.

    Uses Reddit API to analyze posts and comments from crypto subreddits:
    - Post titles and content
    - Comment sentiment
    - Upvote/downvote ratios
    - User karma weighting
    """

    def __init__(self, config: RedditConfig = None):
        """Initialize Reddit sentiment analyzer.

        Args:
            config: Configuration for Reddit analysis
        """
        self.config = config or RedditConfig()
        self._bullish_keywords = self._load_bullish_keywords()
        self._bearish_keywords = self._load_bearish_keywords()
        self._bullish_phrases = self._load_bullish_phrases()
        self._bearish_phrases = self._load_bearish_phrases()

    def _load_bullish_keywords(self) -> set:
        """Load bullish keywords for sentiment analysis."""
        return {
            "buy",
            "buying",
            "bullish",
            "long",
            "accumulate",
            "accumulating",
            "hodl",
            "holding",
            "undervalued",
            "gem",
            "moonshot",
            "potential",
            "promising",
            "bullrun",
            "rally",
            "breakout",
            "support",
            "bounce",
            "recovery",
            "upgrade",
            "adoption",
            "partnership",
            "launch",
        }

    def _load_bearish_keywords(self) -> set:
        """Load bearish keywords for sentiment analysis."""
        return {
            "sell",
            "selling",
            "bearish",
            "short",
            "overvalued",
            "dump",
            "dumping",
            "crash",
            "falling",
            "drop",
            "scam",
            "rug",
            "rugpull",
            "avoid",
            "warning",
            "concern",
            "worried",
            "risk",
            "danger",
            "resistance",
            "breakdown",
            "liquidation",
        }

    def _load_bullish_phrases(self) -> set:
        """Load bullish multi-word phrases."""
        return {
            "to the moon",
            "diamond hands",
            "strong buy",
            "great project",
            "solid fundamentals",
            "long term hold",
            "accumulation zone",
            "buying opportunity",
            "strong support",
        }

    def _load_bearish_phrases(self) -> set:
        """Load bearish multi-word phrases."""
        return {
            "paper hands",
            "stay away",
            "red flag",
            "sell signal",
            "weak fundamentals",
            "exit liquidity",
            "dead project",
            "losing interest",
            "breaking support",
        }

    async def analyze_token_sentiment(
        self, token_symbol: str, hours: int = 24
    ) -> SentimentReading:
        """Analyze Reddit sentiment for a token.

        Args:
            token_symbol: Token symbol (e.g., "ETH")
            hours: Hours of historical data to analyze

        Returns:
            SentimentReading with Reddit sentiment analysis

        Example:
            >>> analyzer = RedditSentimentAnalyzer()
            >>> sentiment = await analyzer.analyze_token_sentiment("ETH", hours=24)
            >>> print(f"ETH Reddit sentiment: {sentiment.score}/100")
        """
        # In production, this would call Reddit API
        # For now, simulate with mock data
        posts = await self._fetch_posts(token_symbol, hours)

        if not posts:
            return self._create_neutral_reading(token_symbol)

        # Analyze posts and comments
        scores = [self._analyze_post(post) for post in posts]

        # Calculate weighted average based on karma
        weighted_score = self._calculate_weighted_sentiment(posts, scores)

        # Calculate confidence based on sample size and consistency
        confidence = self._calculate_confidence(posts, scores)

        return SentimentReading(
            source=SentimentSource.REDDIT,
            score=weighted_score,
            confidence=confidence,
            timestamp=datetime.utcnow(),
            token_symbol=token_symbol,
            metadata={
                "post_count": len(posts),
                "time_period_hours": hours,
                "subreddits": len(set(p.get("subreddit") for p in posts)),
                "total_karma": sum(p.get("karma", 0) for p in posts),
                "avg_upvote_ratio": sum(p.get("upvote_ratio", 0) for p in posts)
                / len(posts)
                if posts
                else 0,
            },
        )

    async def _fetch_posts(
        self, token_symbol: str, hours: int
    ) -> List[Dict]:
        """Fetch Reddit posts mentioning token.

        In production, this would call Reddit API.
        For now, returns simulated data.

        Args:
            token_symbol: Token symbol
            hours: Hours of history

        Returns:
            List of post dictionaries
        """
        # Simulate Reddit API response
        # In production: use PRAW (Python Reddit API Wrapper)
        # reddit = praw.Reddit(...)
        # subreddit = reddit.subreddit("cryptocurrency+ethtrader")
        # posts = subreddit.search(token_symbol, time_filter="day")

        # Simulated posts for testing
        simulated_posts = [
            {
                "title": f"Why ${token_symbol} is undervalued - long term hold",
                "text": f"Great fundamentals, solid team. ${token_symbol} is a gem. Accumulating more.",
                "karma": 450,
                "upvote_ratio": 0.85,
                "comments": 67,
                "subreddit": "cryptocurrency",
                "timestamp": datetime.utcnow() - timedelta(hours=2),
            },
            {
                "title": f"${token_symbol} breaking support - bearish",
                "text": f"Not looking good for ${token_symbol}. Might be time to sell.",
                "karma": 120,
                "upvote_ratio": 0.65,
                "comments": 34,
                "subreddit": "cryptomarkets",
                "timestamp": datetime.utcnow() - timedelta(hours=5),
            },
            {
                "title": f"${token_symbol} analysis - strong buy signal",
                "text": f"Technical analysis shows ${token_symbol} is in accumulation zone. Bullish!",
                "karma": 780,
                "upvote_ratio": 0.92,
                "comments": 123,
                "subreddit": "ethtrader",
                "timestamp": datetime.utcnow() - timedelta(hours=8),
            },
            {
                "title": f"Discussion: ${token_symbol} future prospects",
                "text": f"What do you think about ${token_symbol}? Holding long term.",
                "karma": 340,
                "upvote_ratio": 0.78,
                "comments": 89,
                "subreddit": "defi",
                "timestamp": datetime.utcnow() - timedelta(hours=12),
            },
            {
                "title": f"${token_symbol} partnership announcement!",
                "text": f"Major partnership for ${token_symbol}. This is huge! Diamond hands!",
                "karma": 920,
                "upvote_ratio": 0.95,
                "comments": 201,
                "subreddit": "cryptocurrency",
                "timestamp": datetime.utcnow() - timedelta(hours=18),
            },
        ]

        # Filter by karma and upvote ratio
        filtered = [
            p
            for p in simulated_posts
            if p["karma"] >= self.config.min_karma
            and p["upvote_ratio"] >= self.config.min_upvote_ratio
        ]

        return filtered

    def _analyze_post(self, post: Dict) -> float:
        """Analyze individual Reddit post sentiment.

        Args:
            post: Post dictionary

        Returns:
            Sentiment score (0-100)
        """
        title = post["title"].lower()
        text = post.get("text", "").lower()
        combined_text = f"{title} {text}"

        score = 50.0  # Neutral baseline

        # Keyword analysis
        bullish_count = sum(1 for kw in self._bullish_keywords if kw in combined_text)
        bearish_count = sum(1 for kw in self._bearish_keywords if kw in combined_text)

        # Adjust score based on keywords (5 points per keyword)
        score += bullish_count * 5
        score -= bearish_count * 5

        # Phrase analysis (stronger signal than individual keywords)
        bullish_phrase_count = sum(
            1 for phrase in self._bullish_phrases if phrase in combined_text
        )
        bearish_phrase_count = sum(
            1 for phrase in self._bearish_phrases if phrase in combined_text
        )

        score += bullish_phrase_count * 8
        score -= bearish_phrase_count * 8

        # Upvote ratio indicates community agreement
        upvote_ratio = post.get("upvote_ratio", 0.5)
        if upvote_ratio > 0.8:
            # High upvote ratio boosts sentiment
            score *= 1.1
        elif upvote_ratio < 0.6:
            # Low upvote ratio dampens sentiment
            score *= 0.9

        # Question marks indicate uncertainty
        if "?" in combined_text:
            score *= 0.95

        # Exclamation marks indicate strong sentiment
        exclamations = combined_text.count("!")
        if score > 50:
            score += exclamations * 2
        else:
            score -= exclamations * 2

        # Clamp to 0-100
        return max(0, min(100, score))

    def _calculate_weighted_sentiment(
        self, posts: List[Dict], scores: List[float]
    ) -> float:
        """Calculate weighted sentiment based on karma.

        Args:
            posts: List of posts
            scores: Corresponding sentiment scores

        Returns:
            Weighted average sentiment score
        """
        if not posts:
            return 50.0

        total_weight = 0.0
        weighted_sum = 0.0

        for post, score in zip(posts, scores):
            # Calculate weight based on karma and upvote ratio
            karma = post["karma"]
            upvote_ratio = post.get("upvote_ratio", 0.5)
            comments = post.get("comments", 0)

            # Weight = karma * upvote_ratio + comment_bonus
            weight = karma * upvote_ratio + (comments * 0.5)

            total_weight += weight
            weighted_sum += score * weight

        return weighted_sum / total_weight if total_weight > 0 else 50.0

    def _calculate_confidence(
        self, posts: List[Dict], scores: List[float]
    ) -> float:
        """Calculate confidence in sentiment analysis.

        Args:
            posts: List of posts
            scores: Corresponding sentiment scores

        Returns:
            Confidence score (0-1)
        """
        if not posts:
            return 0.0

        # Base confidence from sample size
        sample_confidence = min(len(posts) / 50, 1.0)  # Max at 50 posts

        # Consistency: how similar are the scores?
        if len(scores) > 1:
            mean_score = sum(scores) / len(scores)
            variance = sum((s - mean_score) ** 2 for s in scores) / len(scores)
            std_dev = variance**0.5
            consistency = 1.0 - (std_dev / 50)
        else:
            consistency = 0.5

        # High karma posts increase confidence
        avg_karma = sum(p["karma"] for p in posts) / len(posts)
        karma_boost = min(avg_karma / 1000, 0.2)  # Max 0.2 boost

        # High upvote ratio increases confidence
        avg_upvote_ratio = sum(p.get("upvote_ratio", 0.5) for p in posts) / len(posts)
        upvote_boost = (avg_upvote_ratio - 0.5) * 0.2  # Max 0.1 boost

        # Combine factors
        confidence = (
            (sample_confidence * 0.5)
            + (consistency * 0.3)
            + karma_boost
            + upvote_boost
        )

        return max(0.0, min(1.0, confidence))

    def _create_neutral_reading(self, token_symbol: str) -> SentimentReading:
        """Create neutral sentiment reading when no data available."""
        return SentimentReading(
            source=SentimentSource.REDDIT,
            score=50.0,
            confidence=0.0,
            timestamp=datetime.utcnow(),
            token_symbol=token_symbol,
            metadata={
                "post_count": 0,
                "reason": "no_data",
            },
        )

    async def get_trending_discussions(
        self, limit: int = 10
    ) -> List[Dict]:
        """Get trending cryptocurrency discussions on Reddit.

        Args:
            limit: Maximum number of discussions to return

        Returns:
            List of trending discussions

        Example:
            >>> analyzer = RedditSentimentAnalyzer()
            >>> trending = await analyzer.get_trending_discussions(limit=5)
        """
        # In production: analyze hot posts across crypto subreddits
        # For now, return simulated data
        trending = [
            {
                "token": "ETH",
                "posts": 145,
                "sentiment": 72.3,
                "top_subreddit": "ethereum",
            },
            {
                "token": "BTC",
                "posts": 203,
                "sentiment": 68.5,
                "top_subreddit": "bitcoin",
            },
            {
                "token": "SOL",
                "posts": 87,
                "sentiment": 65.8,
                "top_subreddit": "solana",
            },
        ]

        return trending[:limit]
