"""Tests for SearXNG search client with domain filtering (SRCI-05, D-11)."""

from unittest.mock import AsyncMock, MagicMock, patch

from app.sources.searxng import search_searxng
from app.sources.schemas import SearchResult


FAKE_SEARXNG_RESPONSE = {
    "results": [
        {
            "title": "CPS Neonatal Guidelines",
            "url": "https://cps.ca/en/documents/position/neonatal-jaundice",
            "content": "Guidelines for neonatal jaundice management.",
        },
        {
            "title": "UpToDate Article",
            "url": "https://www.uptodate.com/contents/jaundice",
            "content": "Neonatal hyperbilirubinemia overview.",
        },
        {
            "title": "Random Blog Post",
            "url": "https://randomblog.com/jaundice-tips",
            "content": "Home remedies for jaundice (not trusted).",
        },
        {
            "title": "Alberta Health Services",
            "url": "https://www.albertahealthservices.ca/topics/Page12345.aspx",
            "content": "Provincial health information.",
        },
    ]
}

TRUSTED_DOMAINS = ["cps.ca", "uptodate.com", "albertahealthservices.ca"]


class TestSearxngSearch:
    @patch("app.sources.searxng.httpx.AsyncClient")
    async def test_search_returns_filtered_results(self, mock_httpx_cls):
        """SRCI-05: Search returns results filtered to trusted domains."""
        mock_response = MagicMock()
        mock_response.json.return_value = FAKE_SEARXNG_RESPONSE
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_httpx_cls.return_value = mock_client

        results = await search_searxng(
            query="neonatal jaundice",
            domains=TRUSTED_DOMAINS,
            searxng_url="http://searxng:8080",
            limit=10,
        )

        # Should only include trusted domains -- randomblog.com filtered out
        assert len(results) == 3
        result_domains = [r.domain for r in results]
        assert "randomblog.com" not in result_domains
        assert "cps.ca" in result_domains
        assert "uptodate.com" in result_domains
        assert "albertahealthservices.ca" in result_domains

        # Verify result type
        assert all(isinstance(r, SearchResult) for r in results)

    @patch("app.sources.searxng.httpx.AsyncClient")
    async def test_domain_post_filtering(self, mock_httpx_cls):
        """D-11: Results post-filtered to trusted domains only. site: appears in query."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {
                    "title": "Untrusted Result",
                    "url": "https://sketchy-site.com/article",
                    "content": "Should be filtered out.",
                },
                {
                    "title": "Trusted Result",
                    "url": "https://cps.ca/guidelines",
                    "content": "This should pass.",
                },
            ]
        }
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_httpx_cls.return_value = mock_client

        results = await search_searxng(
            query="test query",
            domains=["cps.ca"],
            searxng_url="http://searxng:8080",
            limit=10,
        )

        # Only cps.ca result should survive post-filtering
        assert len(results) == 1
        assert results[0].domain == "cps.ca"
        assert results[0].title == "Trusted Result"

        # Verify site: appears in the query sent to SearXNG
        call_args = mock_client.get.call_args
        query_params = call_args.kwargs.get("params", {})
        assert "site:cps.ca" in query_params.get("q", "")

    @patch("app.sources.searxng.httpx.AsyncClient")
    async def test_searxng_timeout_returns_empty(self, mock_httpx_cls):
        """SearXNG timeout returns empty list gracefully."""
        import httpx

        mock_client = AsyncMock()
        mock_client.get.side_effect = httpx.TimeoutException("timeout")
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_httpx_cls.return_value = mock_client

        results = await search_searxng(
            query="test",
            domains=["cps.ca"],
            searxng_url="http://searxng:8080",
        )

        assert results == []
