"""
Web Search Tool — DuckDuckGo search + page scraping + content extraction.
"""

import asyncio
import logging
from typing import Optional
from urllib.parse import quote_plus

import httpx
from bs4 import BeautifulSoup

from backend.core.config import settings

logger = logging.getLogger(__name__)


class WebSearchTool:
    """DuckDuckGo web search with page content extraction."""

    DDGS_URL = "https://html.duckduckgo.com/html/"
    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
        )
    }

    async def search(self, query: str, max_results: int = 5) -> str:
        """Search DuckDuckGo and return formatted results."""
        logger.info(f"Web search: {query!r}")
        try:
            async with httpx.AsyncClient(timeout=settings.SEARCH_TIMEOUT, follow_redirects=True) as client:
                resp = await client.post(
                    self.DDGS_URL,
                    data={"q": query, "b": ""},
                    headers=self.HEADERS,
                )
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "html.parser")

                results = []
                for i, result in enumerate(soup.select(".result")):
                    if i >= max_results:
                        break
                    title_el = result.select_one(".result__title")
                    url_el = result.select_one(".result__url")
                    snippet_el = result.select_one(".result__snippet")

                    title = title_el.get_text(strip=True) if title_el else "No title"
                    url = url_el.get_text(strip=True) if url_el else ""
                    snippet = snippet_el.get_text(strip=True) if snippet_el else ""

                    results.append(f"[{i+1}] {title}\nURL: {url}\n{snippet}")

                if not results:
                    return f"No results found for: {query}"

                return "\n\n".join(results)

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return f"Search error: {e}"

    async def fetch_page(self, url: str, max_chars: int = 8000) -> str:
        """Fetch and extract readable text from a web page."""
        logger.info(f"Fetching page: {url}")
        try:
            async with httpx.AsyncClient(
                timeout=settings.SEARCH_TIMEOUT,
                follow_redirects=True,
            ) as client:
                resp = await client.get(url, headers=self.HEADERS)
                resp.raise_for_status()

                soup = BeautifulSoup(resp.text, "html.parser")

                # Remove noise elements
                for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
                    tag.decompose()

                # Try to find main content
                main = (
                    soup.find("main")
                    or soup.find("article")
                    or soup.find(class_=["content", "main-content", "post-content"])
                    or soup.find("body")
                )

                text = main.get_text(separator="\n", strip=True) if main else soup.get_text("\n", strip=True)

                # Collapse excessive whitespace
                lines = [line.strip() for line in text.splitlines() if line.strip()]
                text = "\n".join(lines)

                if len(text) > max_chars:
                    text = text[:max_chars] + f"\n\n[truncated — {len(text)} chars total]"

                return text

        except Exception as e:
            logger.error(f"Page fetch failed for {url}: {e}")
            return f"Failed to fetch {url}: {e}"

    async def search_and_fetch(self, query: str, top_n: int = 2) -> str:
        """Search and fetch top N result pages for deep research."""
        search_results = await self.search(query, max_results=top_n + 2)
        # Extract URLs from results (simple heuristic)
        lines = search_results.splitlines()
        urls = [line.replace("URL: ", "").strip() for line in lines if line.startswith("URL:")][:top_n]

        content_parts = [f"Search Results:\n{search_results}\n"]
        for url in urls:
            if url:
                page_content = await self.fetch_page(url)
                content_parts.append(f"\n--- Content from {url} ---\n{page_content}")

        return "\n".join(content_parts)
