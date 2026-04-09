"""
Enterprise AI Presentation Architect — Search Engine
Real-time web search integration using DuckDuckGo for current, factual content.
"""

import time
import logging
from typing import List, Dict, Optional

logger = logging.getLogger("PresentationArchitect")

# ─── Search Result Model ────────────────────────────────────────────────────────

class SearchResult:
    """Represents a single search result."""
    def __init__(self, title: str = "", snippet: str = "", url: str = "", source: str = ""):
        self.title = title
        self.snippet = snippet
        self.url = url
        self.source = source

    def to_context_string(self) -> str:
        """Format as context string for LLM prompt injection."""
        return f"- {self.title}: {self.snippet} (Source: {self.url})"

    def to_dict(self) -> Dict:
        return {
            "title": self.title,
            "snippet": self.snippet,
            "url": self.url,
            "source": self.source
        }


# ─── DuckDuckGo Search Engine ───────────────────────────────────────────────────

class WebSearchEngine:
    """
    Real-time web search engine using DuckDuckGo.
    Provides current information for LLM prompt enrichment.
    """

    def __init__(self, max_results: int = 8, timeout: int = 15):
        self.max_results = max_results
        self.timeout = timeout
        self._last_search_time = 0
        self._rate_limit_delay = 1.5  # seconds between searches

    def _rate_limit(self):
        """Enforce rate limiting between searches."""
        elapsed = time.time() - self._last_search_time
        if elapsed < self._rate_limit_delay:
            time.sleep(self._rate_limit_delay - elapsed)
        self._last_search_time = time.time()

    def search(self, query: str, max_results: Optional[int] = None) -> List[SearchResult]:
        """
        Perform a web search and return structured results.

        Args:
            query: Search query string
            max_results: Override default max results

        Returns:
            List of SearchResult objects
        """
        if not query or not query.strip():
            logger.warning("Empty search query provided")
            return []

        results_limit = max_results or self.max_results

        try:
            self._rate_limit()
            return self._search_duckduckgo(query, results_limit)
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    def _search_duckduckgo(self, query: str, max_results: int) -> List[SearchResult]:
        """Execute search using DuckDuckGo."""
        try:
            from duckduckgo_search import DDGS
            import itertools

            results = []
            with DDGS() as ddgs:
                # Modern DDGS text call using iterator
                search_results = ddgs.text(
                    query,
                    region="wt-wt",
                    safesearch="moderate"
                )

                if search_results:
                    # Collect and slice results from the generator
                    for r in itertools.islice(search_results, max_results):
                        results.append(SearchResult(
                            title=r.get("title", ""),
                            snippet=r.get("body", r.get("snippet", "")),
                            url=r.get("href", r.get("link", "")),
                            source="DuckDuckGo"
                        ))

            logger.info(f"DuckDuckGo search returned {len(results)} results for: {query[:50]}")
            return results

        except ImportError:
            logger.error("duckduckgo-search library not installed")
            return []
        except Exception as e:
            logger.warning(f"DuckDuckGo search error: {e}")
            return []

    def search_for_topic(self, topic: str, context: str = "") -> str:
        """
        Search for a topic and return formatted context string for LLM.

        Args:
            topic: Main topic to search for
            context: Additional context to refine search

        Returns:
            Formatted string with search results for prompt injection
        """
        # Build enriched query
        search_queries = self._build_search_queries(topic, context)
        all_results = []

        for query in search_queries[:3]:  # Max 3 sub-queries
            results = self.search(query, max_results=5)
            all_results.extend(results)

        if not all_results:
            logger.info(f"No search results found for topic: {topic}")
            return ""

        # Deduplicate by URL
        seen_urls = set()
        unique_results = []
        for r in all_results:
            if r.url not in seen_urls:
                seen_urls.add(r.url)
                unique_results.append(r)

        # Format for LLM context
        context_parts = [
            "\n=== REAL-TIME WEB RESEARCH ===",
            f"Topic: {topic}",
            f"Search Date: {time.strftime('%Y-%m-%d')}",
            "Relevant findings:",
        ]

        for i, result in enumerate(unique_results[:10], 1):
            context_parts.append(f"\n{i}. {result.to_context_string()}")

        context_parts.append("\n=== END OF WEB RESEARCH ===\n")

        return "\n".join(context_parts)

    def _build_search_queries(self, topic: str, context: str = "") -> List[str]:
        """Build multiple search queries for comprehensive coverage."""
        queries = [topic]

        # Add targeted queries
        topic_lower = topic.lower()

        if any(kw in topic_lower for kw in ["market", "industry", "business", "revenue"]):
            queries.append(f"{topic} latest statistics data 2024 2025")

        if any(kw in topic_lower for kw in ["technology", "ai", "software", "digital"]):
            queries.append(f"{topic} trends innovations latest")

        if any(kw in topic_lower for kw in ["strategy", "plan", "roadmap"]):
            queries.append(f"{topic} best practices case studies")

        if context:
            queries.append(f"{topic} {context}")

        # Always add a current-data query
        if len(queries) < 3:
            queries.append(f"{topic} latest developments key facts")

        return queries[:3]

    def get_quick_facts(self, topic: str) -> List[str]:
        """
        Get quick bullet-point facts about a topic.

        Args:
            topic: Topic to research

        Returns:
            List of fact strings
        """
        results = self.search(f"{topic} key facts statistics", max_results=5)
        facts = []
        for r in results:
            if r.snippet and len(r.snippet) > 20:
                facts.append(r.snippet)
        return facts[:5]
