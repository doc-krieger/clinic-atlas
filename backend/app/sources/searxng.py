"""SearXNG search client with domain scoping and post-filtering (SRCI-05, D-11)."""

import logging
from urllib.parse import urlparse

import httpx

from app.sources.schemas import SearchResult

logger = logging.getLogger(__name__)


async def search_searxng(
    query: str,
    domains: list[str],
    searxng_url: str,
    limit: int = 10,
) -> list[SearchResult]:
    """Query SearXNG with domain-scoped search, post-filter to trusted domains only.

    D-11 belt-and-suspenders approach:
    1. Build query with site: filters from trusted domains (pre-filter)
    2. Post-filter results to only include trusted domains
    """
    # Build site:-scoped query (limit to first 5 domains to keep query reasonable)
    if domains:
        site_filters = " OR ".join(f"site:{d}" for d in domains[:5])
        scoped_query = f"({site_filters}) {query}"
    else:
        scoped_query = query

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"{searxng_url}/search",
                params={"q": scoped_query, "format": "json", "pageno": 1},
            )
            resp.raise_for_status()
            data = resp.json()
    except (httpx.TimeoutException, httpx.ConnectError) as e:
        logger.warning("SearXNG request failed: %s", e)
        return []
    except httpx.HTTPStatusError as e:
        logger.warning("SearXNG returned error status: %s", e)
        return []

    # D-11: Post-filter to trusted domains only
    trusted = {d.removeprefix("www.") for d in domains}
    results: list[SearchResult] = []

    for r in data.get("results", []):
        url = r.get("url", "")
        domain = urlparse(url).netloc.removeprefix("www.")
        if domain in trusted:
            results.append(
                SearchResult(
                    title=r.get("title", ""),
                    url=url,
                    snippet=r.get("content", ""),
                    domain=domain,
                )
            )
        if len(results) >= limit:
            break

    return results
