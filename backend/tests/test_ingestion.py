"""Tests for source ingestion endpoints and service layer.

Replaces xfail stubs from Plan 01 with real implementations.
All docling/network calls are mocked -- only DB interactions use real Postgres.
"""

import hashlib
import json
import sys
from io import BytesIO
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.config import Settings
from app.main import app
from app.sources.models import RawSource
from app.sources.router import get_settings

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def parse_sse_events(response_text: str) -> list[dict]:
    """Parse SSE response body into list of {event, data} dicts.

    FastAPI's ServerSentEvent JSON-encodes the data field, so each data: line
    is valid JSON. We parse it back into a Python object.
    """
    events = []
    current_event = None
    current_data = None

    for line in response_text.strip().split("\n"):
        line = line.strip()
        if line.startswith("event:"):
            current_event = line[len("event:") :].strip()
        elif line.startswith("data:"):
            current_data = line[len("data:") :].strip()
        elif line == "" and current_data is not None:
            try:
                data = json.loads(current_data)
            except json.JSONDecodeError:
                data = current_data
            events.append({"event": current_event, "data": data})
            current_event = None
            current_data = None

    # Handle last event if no trailing blank line
    if current_data is not None:
        try:
            data = json.loads(current_data)
        except json.JSONDecodeError:
            data = current_data
        events.append({"event": current_event, "data": data})

    return events


def _make_mock_docling_result(markdown: str, page_count: int = 2, name: str = "test"):
    """Create a mock docling ConversionResult."""
    mock_result = MagicMock()
    mock_result.document.export_to_markdown.return_value = markdown
    mock_result.document.pages = {i: MagicMock() for i in range(page_count)}
    mock_result.document.name = name
    return mock_result


def _mock_fitz_module(author: str | None = None):
    """Create a mock fitz module for PDF metadata extraction."""
    mock_fitz = MagicMock()
    mock_doc = MagicMock()
    mock_doc.metadata = {"author": author}
    mock_fitz.open.return_value = mock_doc
    return mock_fitz


@pytest.fixture
def override_settings(tmp_path):
    """Override get_settings dependency with a temp sources dir."""
    sources_dir = str(tmp_path / "sources")

    def _override() -> Settings:
        s = Settings()
        # Override only the sources dir for test isolation
        s.clinic_atlas_sources_dir = sources_dir
        return s

    app.dependency_overrides[get_settings] = _override
    yield sources_dir
    app.dependency_overrides.pop(get_settings, None)


class TestPdfUpload:
    @patch("app.sources.service.get_converter")
    def test_pdf_upload_returns_sse_events(
        self, mock_get_converter, client: TestClient, override_settings
    ):
        """SRCI-01: Upload PDF, receive SSE progress events, source stored."""
        markdown = (
            "# Test Document\n\nThis is a test document with enough content "
            "to pass the scanned check. "
        ) * 10
        mock_converter = MagicMock()
        mock_converter.convert.return_value = _make_mock_docling_result(markdown)
        mock_get_converter.return_value = mock_converter

        mock_fitz = _mock_fitz_module(author="Dr. Test Author")

        sample_pdf = FIXTURES_DIR / "sample.pdf"
        with patch.dict(sys.modules, {"fitz": mock_fitz}):
            with open(sample_pdf, "rb") as f:
                response = client.post(
                    "/api/sources/upload",
                    files={"file": ("sample.pdf", f, "application/pdf")},
                )

        assert response.status_code == 200
        events = parse_sse_events(response.text)
        event_types = [e["event"] for e in events]

        assert "progress" in event_types
        assert "complete" in event_types

        complete = next(e for e in events if e["event"] == "complete")
        assert "id" in complete["data"]
        assert "title" in complete["data"]
        assert complete["data"]["source_type"] == "pdf"
        assert complete["data"]["parse_status"] == "parsed"
        assert "quality_flags" in complete["data"]
        assert complete["data"]["author"] == "Dr. Test Author"

    @patch("app.sources.service.get_converter")
    def test_scanned_pdf_detection(
        self, mock_get_converter, client: TestClient, session: Session, override_settings
    ):
        """SRCI-03: Scanned/image PDF flagged with warning status and persisted quality_flags."""
        short_markdown = "x" * 20  # 20 chars across 5 pages = 4 chars/page (< 50)
        mock_converter = MagicMock()
        mock_converter.convert.return_value = _make_mock_docling_result(
            short_markdown, page_count=5
        )
        mock_get_converter.return_value = mock_converter

        mock_fitz = _mock_fitz_module(author=None)

        sample_pdf = FIXTURES_DIR / "sample.pdf"
        with patch.dict(sys.modules, {"fitz": mock_fitz}):
            with open(sample_pdf, "rb") as f:
                response = client.post(
                    "/api/sources/upload",
                    files={"file": ("scanned.pdf", f, "application/pdf")},
                )

        assert response.status_code == 200
        events = parse_sse_events(response.text)
        complete = next(e for e in events if e["event"] == "complete")

        assert complete["data"]["parse_status"] == "warning"
        assert "scanned_pdf" in complete["data"]["quality_flags"]

        # Verify quality_flags are PERSISTED in DB (not just transient SSE state)
        source = session.exec(
            select(RawSource).where(RawSource.id == complete["data"]["id"])
        ).first()
        assert source is not None
        assert "scanned_pdf" in source.quality_flags

    @patch("app.sources.service.get_converter")
    def test_duplicate_pdf_rejection(
        self, mock_get_converter, client: TestClient, session: Session, override_settings
    ):
        """D-02: Duplicate content hash rejected with existing source ID."""
        markdown = "# Duplicate Test\n\nSame content for dedup testing. " * 10
        mock_converter = MagicMock()
        mock_converter.convert.return_value = _make_mock_docling_result(markdown)
        mock_get_converter.return_value = mock_converter

        mock_fitz = _mock_fitz_module(author=None)
        sample_pdf = FIXTURES_DIR / "sample.pdf"

        with patch.dict(sys.modules, {"fitz": mock_fitz}):
            # First upload: should succeed
            with open(sample_pdf, "rb") as f:
                resp1 = client.post(
                    "/api/sources/upload",
                    files={"file": ("test.pdf", f, "application/pdf")},
                )
            events1 = parse_sse_events(resp1.text)
            complete1 = next(e for e in events1 if e["event"] == "complete")
            first_id = complete1["data"]["id"]

            # Second upload: should be rejected as duplicate
            with open(sample_pdf, "rb") as f:
                resp2 = client.post(
                    "/api/sources/upload",
                    files={"file": ("test.pdf", f, "application/pdf")},
                )

        events2 = parse_sse_events(resp2.text)
        error = next(e for e in events2 if e["event"] == "error")

        assert "already been ingested" in error["data"]["error"]
        assert error["data"]["existing_source_id"] == first_id

        # Verify only one RawSource row exists (UNIQUE constraint)
        content_hash = hashlib.sha256(markdown.encode()).hexdigest()
        sources = session.exec(
            select(RawSource).where(RawSource.content_hash == content_hash)
        ).all()
        assert len(sources) == 1

    def test_file_size_limit(self, client: TestClient, override_settings):
        """D-03: Files over 50 MB rejected with 413."""
        large_content = b"%PDF-1.4 " + b"x" * 100

        # Override settings to set 0 MB limit
        def _zero_limit():
            s = Settings()
            s.max_upload_size_mb = 0
            s.clinic_atlas_sources_dir = override_settings
            return s

        app.dependency_overrides[get_settings] = _zero_limit
        try:
            response = client.post(
                "/api/sources/upload",
                files={"file": ("big.pdf", BytesIO(large_content), "application/pdf")},
            )
            assert response.status_code == 413
        finally:
            # Restore the normal override (from fixture)
            app.dependency_overrides.pop(get_settings, None)


class TestUrlFetch:
    @patch("app.sources.service.get_converter")
    @patch("app.sources.service.httpx.AsyncClient")
    @patch("app.sources.service.validate_url_safety")
    def test_url_fetch_returns_sse_events(
        self,
        mock_validate,
        mock_httpx_cls,
        mock_get_converter,
        client: TestClient,
        session: Session,
    ):
        """SRCI-02: URL fetched, extracted, stored as raw source."""
        markdown = "# Clinical Guide\n\nImportant medical content here. " * 10

        mock_converter = MagicMock()
        mock_converter.convert_string.return_value = _make_mock_docling_result(
            markdown, page_count=1, name="Clinical Guide"
        )
        mock_get_converter.return_value = mock_converter

        mock_response = MagicMock()
        mock_response.text = "<html><body><h1>Guide</h1><p>Content</p></body></html>"
        mock_response.content = mock_response.text.encode()
        mock_response.url = "https://example.com/guide"
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_httpx_cls.return_value = mock_client

        mock_validate.return_value = None

        response = client.post(
            "/api/sources/fetch",
            json={"url": "https://example.com/guide"},
        )

        assert response.status_code == 200
        events = parse_sse_events(response.text)
        event_types = [e["event"] for e in events]

        assert "progress" in event_types
        assert "complete" in event_types

        complete = next(e for e in events if e["event"] == "complete")
        assert complete["data"]["source_type"] == "url"
        assert "quality_flags" in complete["data"]

        # Verify stored in DB with quality_flags persisted
        source = session.exec(
            select(RawSource).where(RawSource.id == complete["data"]["id"])
        ).first()
        assert source is not None
        assert source.source_type == "url"
        assert isinstance(source.quality_flags, list)

    @patch("app.sources.service.get_converter")
    @patch("app.sources.service.httpx.AsyncClient")
    @patch("app.sources.service.validate_url_safety")
    def test_thin_content_warning(
        self,
        mock_validate,
        mock_httpx_cls,
        mock_get_converter,
        client: TestClient,
        session: Session,
    ):
        """D-07: Thin content flagged as possibly paywalled with quality_flags persisted."""
        thin_markdown = "Login required"  # < 200 chars

        mock_converter = MagicMock()
        mock_converter.convert_string.return_value = _make_mock_docling_result(
            thin_markdown, page_count=1, name="page"
        )
        mock_get_converter.return_value = mock_converter

        mock_response = MagicMock()
        mock_response.text = "<html><body>Login required</body></html>"
        mock_response.content = mock_response.text.encode()
        mock_response.url = "https://paywalled.com/article"
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_httpx_cls.return_value = mock_client

        mock_validate.return_value = None

        # Mock playwright -- imported lazily. Make it raise so fallback is caught gracefully.
        mock_pw_module = MagicMock()
        mock_pw_module.async_playwright.side_effect = Exception("browser not available")

        with patch.dict(sys.modules, {"playwright.async_api": mock_pw_module}):
            response = client.post(
                "/api/sources/fetch",
                json={"url": "https://paywalled.com/article"},
            )

        assert response.status_code == 200
        events = parse_sse_events(response.text)
        complete = next((e for e in events if e["event"] == "complete"), None)

        assert complete is not None
        assert "thin_content" in complete["data"]["quality_flags"]

        # Verify quality_flags persisted in DB
        source = session.exec(
            select(RawSource).where(RawSource.id == complete["data"]["id"])
        ).first()
        assert source is not None
        assert "thin_content" in source.quality_flags

    @patch("app.sources.service.socket.gethostbyname")
    def test_ssrf_private_ip_rejected(self, mock_gethostbyname, client: TestClient):
        """SSRF protection: URLs resolving to private IPs are rejected."""
        mock_gethostbyname.return_value = "127.0.0.1"

        response = client.post(
            "/api/sources/fetch",
            json={"url": "https://evil.example.com/steal"},
        )

        assert response.status_code == 200
        events = parse_sse_events(response.text)
        error = next((e for e in events if e["event"] == "error"), None)

        assert error is not None
        assert "non-public IP" in error["data"]["error"]


class TestSourceList:
    def test_list_sources_returns_indexed_sources(
        self, client: TestClient, session: Session
    ):
        """GET /api/sources returns list of ingested sources."""
        source = RawSource(
            title="Test Clinical Guide",
            content="# Test content",
            content_hash="abc123unique",
            source_type="pdf",
            parse_status="parsed",
            quality_flags=["test_flag"],
            page_count=5,
            mime_type="application/pdf",
        )
        session.add(source)
        session.commit()
        session.refresh(source)

        response = client.get("/api/sources")
        assert response.status_code == 200

        data = response.json()
        assert "sources" in data
        assert "count" in data
        assert data["count"] >= 1

        # SourceListItem doesn't expose content_hash, find by title
        found = next(
            (s for s in data["sources"] if s["title"] == "Test Clinical Guide"), None
        )

        assert found is not None
        assert found["title"] == "Test Clinical Guide"
        assert found["source_type"] == "pdf"
        assert found["parse_status"] == "parsed"
        assert "test_flag" in found["quality_flags"]
        assert found["page_count"] == 5
