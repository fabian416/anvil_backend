"""
Reddit API Client.

Provides access to Reddit posts and comments for sentiment analysis.
Uses public JSON API (no authentication required for read-only).

API Docs: https://www.reddit.com/dev/api/
Rate Limit: ~60 requests/minute (be respectful)
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime

import httpx

logger = logging.getLogger(__name__)


@dataclass
class RedditPost:
    """Reddit post/submission data."""

    id: str
    title: str
    selftext: str
    score: int
    upvote_ratio: float
    num_comments: int
    created_utc: datetime
    subreddit: str
    author: str
    url: str
    is_self: bool  # True if text post, False if link
    permalink: str


@dataclass
class RedditComment:
    """Reddit comment data."""

    id: str
    body: str
    score: int
    created_utc: datetime
    author: str
    permalink: str


@dataclass
class SubredditInfo:
    """Subreddit information."""

    name: str
    subscribers: int
    active_users: int
    description: str
    public_description: str


class RedditClient:
    """
    Reddit API client for cryptocurrency sentiment analysis.

    Uses public JSON endpoints (append .json to any Reddit URL).
    No authentication required for read-only access.

    Features:
    - Fetch posts from subreddits
    - Fetch comments on posts
    - Search posts by keyword
    - Get subreddit info
    """

    BASE_URL = "https://www.reddit.com"
    USER_AGENT = "AnvilCrypto/1.0 (Sentiment Analysis Bot)"

    # Crypto-focused subreddits
    CRYPTO_SUBREDDITS = [
        "cryptocurrency",
        "cryptomarkets",
        "ethereum",
        "bitcoin",
        "defi",
        "ethtrader",
        "altcoin",
    ]

    def __init__(self, user_agent: str | None = None):
        """
        Initialize Reddit client.

        Args:
            user_agent: Custom user agent (recommended by Reddit API)
        """
        self._client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            timeout=30.0,
            headers={
                "User-Agent": user_agent or self.USER_AGENT,
            },
            follow_redirects=True,
        )

    async def close(self):
        """Close HTTP client."""
        await self._client.aclose()

    async def get_subreddit_posts(
        self,
        subreddit: str,
        sort: str = "hot",
        limit: int = 25,
        time_filter: str = "day",
    ) -> list[RedditPost]:
        """
        Get posts from a subreddit.

        Args:
            subreddit: Subreddit name (without r/)
            sort: Sort method - "hot", "new", "top", "rising"
            limit: Number of posts (max 100)
            time_filter: Time filter for "top" - "hour", "day", "week", "month", "year", "all"

        Returns:
            List of RedditPost objects

        Example:
            >>> posts = await client.get_subreddit_posts("ethereum", sort="hot", limit=25)
            >>> for post in posts:
            ...     print(f"[{post.score}] {post.title}")
        """
        params = {"limit": min(limit, 100)}
        if sort == "top":
            params["t"] = time_filter

        try:
            response = await self._client.get(
                f"/r/{subreddit}/{sort}.json",
                params=params,
            )
            response.raise_for_status()
            data = response.json()

            posts = []
            for child in data.get("data", {}).get("children", []):
                post_data = child.get("data", {})
                posts.append(self._parse_post(post_data))

            return posts

        except httpx.HTTPStatusError as e:
            logger.warning(f"Reddit API error for r/{subreddit}: {e}")
            return []
        except Exception as e:
            logger.warning(f"Error fetching r/{subreddit}: {e}")
            return []

    async def search_posts(
        self,
        query: str,
        subreddit: str | None = None,
        sort: str = "relevance",
        time_filter: str = "week",
        limit: int = 25,
    ) -> list[RedditPost]:
        """
        Search for posts containing a query.

        Args:
            query: Search query (e.g., "ETH", "Ethereum")
            subreddit: Limit to specific subreddit (optional)
            sort: Sort method - "relevance", "hot", "top", "new", "comments"
            time_filter: Time filter - "hour", "day", "week", "month", "year", "all"
            limit: Number of results (max 100)

        Returns:
            List of matching RedditPost objects

        Example:
            >>> posts = await client.search_posts("ETH price", subreddit="cryptocurrency")
            >>> print(f"Found {len(posts)} posts about ETH")
        """
        params = {
            "q": query,
            "sort": sort,
            "t": time_filter,
            "limit": min(limit, 100),
            "restrict_sr": "true" if subreddit else "false",
        }

        endpoint = f"/r/{subreddit}/search.json" if subreddit else "/search.json"

        try:
            response = await self._client.get(endpoint, params=params)
            response.raise_for_status()
            data = response.json()

            posts = []
            for child in data.get("data", {}).get("children", []):
                post_data = child.get("data", {})
                posts.append(self._parse_post(post_data))

            return posts

        except httpx.HTTPStatusError as e:
            logger.warning(f"Reddit search error: {e}")
            return []
        except Exception as e:
            logger.warning(f"Error searching Reddit: {e}")
            return []

    async def get_post_comments(
        self,
        subreddit: str,
        post_id: str,
        sort: str = "best",
        limit: int = 50,
    ) -> list[RedditComment]:
        """
        Get comments on a post.

        Args:
            subreddit: Subreddit name
            post_id: Post ID (without t3_ prefix)
            sort: Sort method - "best", "top", "new", "controversial", "old"
            limit: Number of comments

        Returns:
            List of RedditComment objects

        Example:
            >>> comments = await client.get_post_comments("ethereum", "abc123")
            >>> for comment in comments[:5]:
            ...     print(f"[{comment.score}] {comment.body[:50]}...")
        """
        params = {"sort": sort, "limit": limit}

        try:
            response = await self._client.get(
                f"/r/{subreddit}/comments/{post_id}.json",
                params=params,
            )
            response.raise_for_status()
            data = response.json()

            comments = []
            # Second element contains comments
            if len(data) > 1:
                for child in data[1].get("data", {}).get("children", []):
                    comment_data = child.get("data", {})
                    if comment_data.get("body"):  # Skip deleted comments
                        comments.append(self._parse_comment(comment_data))

            return comments

        except Exception as e:
            logger.warning(f"Error fetching comments: {e}")
            return []

    async def get_crypto_sentiment_posts(
        self,
        token_symbol: str,
        limit_per_subreddit: int = 10,
    ) -> list[RedditPost]:
        """
        Get posts mentioning a token across crypto subreddits.

        Uses hot/new posts endpoint (works without auth) instead of search.

        Args:
            token_symbol: Token symbol (e.g., "ETH", "BTC")
            limit_per_subreddit: Posts per subreddit

        Returns:
            List of posts mentioning the token

        Example:
            >>> posts = await client.get_crypto_sentiment_posts("ETH")
            >>> print(f"Found {len(posts)} posts about ETH")
        """
        all_posts = []
        token_lower = token_symbol.lower()
        token_upper = token_symbol.upper()

        # Token-specific subreddit mapping
        token_subreddits = {
            "ETH": ["ethereum", "ethtrader", "ethfinance"],
            "BTC": ["bitcoin", "bitcoinmarkets"],
            "SOL": ["solana"],
            "AVAX": ["avalanche"],
            "MATIC": ["maticnetwork", "polygonnetwork"],
        }

        # Get token-specific subreddits + general crypto subreddits
        subreddits_to_check = token_subreddits.get(
            token_upper, []
        ) + ["cryptocurrency", "cryptomarkets", "defi"]

        for subreddit in subreddits_to_check[:5]:  # Limit to 5 subreddits
            # Fetch hot posts (works without auth)
            posts = await self.get_subreddit_posts(
                subreddit=subreddit,
                sort="hot",
                limit=limit_per_subreddit * 2,  # Fetch more, then filter
            )

            # Filter posts that mention the token
            for post in posts:
                title_lower = post.title.lower()
                text_lower = post.selftext.lower()

                if (
                    token_lower in title_lower
                    or token_upper in post.title
                    or f"${token_upper}" in post.title
                    or token_lower in text_lower
                ):
                    all_posts.append(post)

        # Remove duplicates by ID
        seen_ids = set()
        unique_posts = []
        for post in all_posts:
            if post.id not in seen_ids:
                seen_ids.add(post.id)
                unique_posts.append(post)

        # Sort by score and recency
        unique_posts.sort(key=lambda p: (p.score, p.created_utc), reverse=True)

        return unique_posts[:limit_per_subreddit * 3]

    async def get_subreddit_info(self, subreddit: str) -> SubredditInfo | None:
        """
        Get information about a subreddit.

        Args:
            subreddit: Subreddit name

        Returns:
            SubredditInfo or None if not found

        Example:
            >>> info = await client.get_subreddit_info("ethereum")
            >>> print(f"r/{info.name}: {info.subscribers:,} subscribers")
        """
        try:
            response = await self._client.get(f"/r/{subreddit}/about.json")
            response.raise_for_status()
            data = response.json().get("data", {})

            return SubredditInfo(
                name=data.get("display_name", subreddit),
                subscribers=data.get("subscribers", 0),
                active_users=data.get("accounts_active", 0),
                description=data.get("description", ""),
                public_description=data.get("public_description", ""),
            )

        except Exception as e:
            logger.warning(f"Error fetching r/{subreddit} info: {e}")
            return None

    def _parse_post(self, data: dict) -> RedditPost:
        """Parse raw post data into RedditPost object."""
        return RedditPost(
            id=data.get("id", ""),
            title=data.get("title", ""),
            selftext=data.get("selftext", ""),
            score=data.get("score", 0),
            upvote_ratio=data.get("upvote_ratio", 0.5),
            num_comments=data.get("num_comments", 0),
            created_utc=datetime.fromtimestamp(data.get("created_utc", 0)),
            subreddit=data.get("subreddit", ""),
            author=data.get("author", "[deleted]"),
            url=data.get("url", ""),
            is_self=data.get("is_self", True),
            permalink=f"https://reddit.com{data.get('permalink', '')}",
        )

    def _parse_comment(self, data: dict) -> RedditComment:
        """Parse raw comment data into RedditComment object."""
        return RedditComment(
            id=data.get("id", ""),
            body=data.get("body", ""),
            score=data.get("score", 0),
            created_utc=datetime.fromtimestamp(data.get("created_utc", 0)),
            author=data.get("author", "[deleted]"),
            permalink=f"https://reddit.com{data.get('permalink', '')}",
        )
