"""Tests for health, reindex, search, and sources registry endpoints."""

from fastapi.testclient import TestClient


def test_health_returns_200_with_status(client: TestClient):
    """GET /api/health returns 200 with status field."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("ok", "degraded", "error")


def test_health_has_postgres_check(client: TestClient):
    """GET /api/health includes postgres status ok."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["checks"]["postgres"]["status"] == "ok"


def test_health_has_all_check_keys(client: TestClient):
    """GET /api/health includes checks for all services."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    checks = data["checks"]
    for key in ["postgres", "ollama", "searxng", "disk_notes", "disk_sources"]:
        assert key in checks, f"Missing health check key: {key}"


def test_reindex_returns_200_with_stats(client: TestClient):
    """POST /api/reindex returns 200 with stats object."""
    response = client.post("/api/reindex")
    assert response.status_code == 200
    data = response.json()
    assert "stats" in data
    stats = data["stats"]
    assert "scanned" in stats
    assert "upserted" in stats
    assert "errors" in stats


def test_search_returns_200_with_notes_and_sources(client: TestClient):
    """GET /api/search?q=test returns 200 with notes and sources arrays."""
    response = client.get("/api/search", params={"q": "test"})
    assert response.status_code == 200
    data = response.json()
    assert "notes" in data
    assert "sources" in data
    assert isinstance(data["notes"], list)
    assert isinstance(data["sources"], list)


def test_sources_registry_returns_200(client: TestClient):
    """GET /api/sources/registry returns 200 with sources list and count."""
    response = client.get("/api/sources/registry")
    assert response.status_code == 200
    data = response.json()
    assert "sources" in data
    assert "count" in data
    assert isinstance(data["sources"], list)
    assert isinstance(data["count"], int)
    assert data["count"] > 0
