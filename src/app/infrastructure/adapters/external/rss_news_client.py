"""
RSS News Client.

Fetches cryptocurrency news from RSS feeds for sentiment analysis.
No authentication required - all public feeds.

Supported Sources:
- CoinDesk
- CoinTelegraph
- Decrypt
- The Block
- CryptoSlate
"""

import logging
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from email.utils import parsedate_to_datetime

import httpx

logger = logging.getLogger(__name__)


@dataclass
class NewsArticle:
    """News article from RSS feed."""

    title: str
    description: str
    link: str
    published: datetime
    source: str
    categories: list[str]


class RSSNewsClient:
    """
    RSS News client for cryptocurrency sentiment analysis.

    Fetches news from major crypto news sources via RSS feeds.
    No API key required.

    Features:
    - Fetch latest news from multiple sources
    - Filter by keyword
    - Combine feeds for aggregated view
    """

    # Crypto news RSS feeds (all public, no auth required)
    DEFAULT_FEEDS = {
        "coindesk": "https://www.coindesk.com/arc/outboundfeeds/rss/",
        "cointelegraph": "https://cointelegraph.com/rss",
        "decrypt": "https://decrypt.co/feed",
        "theblock": "https://www.theblock.co/rss.xml",
        "cryptoslate": "https://cryptoslate.com/feed/",
        "bitcoinmagazine": "https://bitcoinmagazine.com/feed",
    }

    def __init__(self, feeds: dict[str, str] | None = None):
        """
        Initialize RSS news client.

        Args:
            feeds: Custom feed URLs (optional, defaults to crypto news feeds)
        """
        self._feeds = feeds or self.DEFAULT_FEEDS
        self._client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "User-Agent": "AnvilCrypto/1.0 (News Aggregator)",
            },
            follow_redirects=True,
        )

    async def close(self):
        """Close HTTP client."""
        await self._client.aclose()

    async def fetch_feed(self, source: str, url: str) -> list[NewsArticle]:
        """
        Fetch articles from a single RSS feed.

        Args:
            source: Source name (e.g., "coindesk")
            url: RSS feed URL

        Returns:
            List of NewsArticle objects

        Example:
            >>> articles = await client.fetch_feed("coindesk", "https://...")
            >>> for article in articles[:3]:
            ...     print(f"[{article.source}] {article.title}")
        """
        try:
            response = await self._client.get(url)
            response.raise_for_status()

            # Parse XML
            root = ET.fromstring(response.text)

            articles = []

            # Handle both RSS 2.0 and Atom feeds
            if root.tag == "rss":
                # RSS 2.0 format
                for item in root.findall(".//item"):
                    article = self._parse_rss_item(item, source)
                    if article:
                        articles.append(article)
            elif root.tag.endswith("feed"):
                # Atom format
                for entry in root.findall(".//{http://www.w3.org/2005/Atom}entry"):
                    article = self._parse_atom_entry(entry, source)
                    if article:
                        articles.append(article)
            else:
                # Try to find items anyway
                for item in root.findall(".//item"):
                    article = self._parse_rss_item(item, source)
                    if article:
                        articles.append(article)

            return articles

        except httpx.HTTPStatusError as e:
            logger.warning(f"HTTP error fetching {source} RSS: {e}")
            return []
        except ET.ParseError as e:
            logger.warning(f"XML parse error for {source}: {e}")
            return []
        except Exception as e:
            logger.warning(f"Error fetching {source} RSS: {e}")
            return []

    async def fetch_all_feeds(self) -> list[NewsArticle]:
        """
        Fetch articles from all configured feeds.

        Returns:
            List of all articles, sorted by publication date

        Example:
            >>> all_news = await client.fetch_all_feeds()
            >>> print(f"Fetched {len(all_news)} articles from {len(client._feeds)} sources")
        """
        all_articles = []

        for source, url in self._feeds.items():
            articles = await self.fetch_feed(source, url)
            all_articles.extend(articles)

        # Sort by publication date (newest first)
        all_articles.sort(key=lambda a: a.published, reverse=True)

        return all_articles

    async def search_news(
        self,
        keyword: str,
        limit: int = 20,
    ) -> list[NewsArticle]:
        """
        Search news articles containing a keyword.

        Args:
            keyword: Search keyword (e.g., "ETH", "Ethereum")
            limit: Maximum number of results

        Returns:
            List of matching articles

        Example:
            >>> eth_news = await client.search_news("Ethereum", limit=10)
            >>> for article in eth_news:
            ...     print(f"{article.published.date()}: {article.title}")
        """
        all_articles = await self.fetch_all_feeds()

        # Filter by keyword (case-insensitive)
        keyword_lower = keyword.lower()
        matching = [
            article
            for article in all_articles
            if keyword_lower in article.title.lower()
            or keyword_lower in article.description.lower()
        ]

        return matching[:limit]

    async def get_token_news(
        self,
        token_symbol: str,
        token_name: str | None = None,
        limit: int = 15,
    ) -> list[NewsArticle]:
        """
        Get news about a specific token.

        Args:
            token_symbol: Token symbol (e.g., "ETH")
            token_name: Full token name (e.g., "Ethereum") - optional
            limit: Maximum number of results

        Returns:
            List of articles about the token

        Example:
            >>> eth_news = await client.get_token_news("ETH", "Ethereum")
            >>> print(f"Found {len(eth_news)} articles about Ethereum")
        """
        all_articles = await self.fetch_all_feeds()

        # Create search patterns
        symbol_lower = token_symbol.lower()
        name_lower = token_name.lower() if token_name else None

        matching = []
        for article in all_articles:
            title_lower = article.title.lower()
            desc_lower = article.description.lower()

            # Check for symbol or name
            if symbol_lower in title_lower or symbol_lower in desc_lower:
                matching.append(article)
            elif name_lower and (name_lower in title_lower or name_lower in desc_lower):
                matching.append(article)

        return matching[:limit]

    def _parse_rss_item(self, item: ET.Element, source: str) -> NewsArticle | None:
        """Parse RSS 2.0 item element."""
        try:
            title = self._get_text(item, "title") or ""
            description = self._get_text(item, "description") or ""
            link = self._get_text(item, "link") or ""
            pub_date_str = self._get_text(item, "pubDate") or ""

            # Parse publication date
            try:
                published = parsedate_to_datetime(pub_date_str)
            except Exception:
                published = datetime.now()

            # Get categories
            categories = [cat.text for cat in item.findall("category") if cat.text]

            # Clean description (remove HTML tags)
            description = self._clean_html(description)

            return NewsArticle(
                title=title,
                description=description[:500],  # Limit description length
                link=link,
                published=published,
                source=source,
                categories=categories,
            )

        except Exception as e:
            logger.warning(f"Error parsing RSS item from {source}: {e}")
            return None

    def _parse_atom_entry(self, entry: ET.Element, source: str) -> NewsArticle | None:
        """Parse Atom entry element."""
        ns = {"atom": "http://www.w3.org/2005/Atom"}

        try:
            title = self._get_text(entry, "atom:title", ns) or ""
            summary = self._get_text(entry, "atom:summary", ns) or ""
            content = self._get_text(entry, "atom:content", ns) or summary

            # Get link
            link_elem = entry.find("atom:link[@rel='alternate']", ns)
            if link_elem is None:
                link_elem = entry.find("atom:link", ns)
            link = link_elem.get("href", "") if link_elem is not None else ""

            # Get published date
            pub_date_str = self._get_text(entry, "atom:published", ns) or ""
            if not pub_date_str:
                pub_date_str = self._get_text(entry, "atom:updated", ns) or ""

            try:
                published = datetime.fromisoformat(pub_date_str.replace("Z", "+00:00"))
            except Exception:
                published = datetime.now()

            # Get categories
            categories = [
                cat.get("term", "")
                for cat in entry.findall("atom:category", ns)
                if cat.get("term")
            ]

            # Clean description
            description = self._clean_html(content or summary)

            return NewsArticle(
                title=title,
                description=description[:500],
                link=link,
                published=published,
                source=source,
                categories=categories,
            )

        except Exception as e:
            logger.warning(f"Error parsing Atom entry from {source}: {e}")
            return None

    def _get_text(
        self, element: ET.Element, path: str, namespaces: dict | None = None
    ) -> str | None:
        """Get text content of an element by path."""
        found = element.find(path, namespaces)
        return found.text if found is not None else None

    def _clean_html(self, text: str) -> str:
        """Remove HTML tags from text."""
        # Remove HTML tags
        clean = re.sub(r"<[^>]+>", "", text)
        # Remove extra whitespace
        clean = re.sub(r"\s+", " ", clean).strip()
        # Decode common HTML entities
        clean = clean.replace("&amp;", "&")
        clean = clean.replace("&lt;", "<")
        clean = clean.replace("&gt;", ">")
        clean = clean.replace("&quot;", '"')
        clean = clean.replace("&#39;", "'")
        clean = clean.replace("&nbsp;", " ")
        return clean
