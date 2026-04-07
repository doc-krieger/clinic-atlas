import pytest
from fastapi.testclient import TestClient


class TestPdfUpload:
    @pytest.mark.xfail(reason="Awaiting service implementation (Plan 02)")
    def test_pdf_upload_returns_sse_events(self, client: TestClient):
        """SRCI-01: Upload PDF, receive SSE progress events, source stored."""
        assert False, "Not yet implemented"

    @pytest.mark.xfail(reason="Awaiting service implementation (Plan 02)")
    def test_scanned_pdf_detection(self, client: TestClient):
        """SRCI-03: Scanned/image PDF flagged with warning status and persisted quality_flags."""
        assert False, "Not yet implemented"

    @pytest.mark.xfail(reason="Awaiting service implementation (Plan 02)")
    def test_duplicate_pdf_rejection(self, client: TestClient):
        """D-02: Duplicate content hash rejected with existing source ID."""
        assert False, "Not yet implemented"

    @pytest.mark.xfail(reason="Awaiting service implementation (Plan 02)")
    def test_file_size_limit(self, client: TestClient):
        """D-03: Files over 50 MB rejected with 413."""
        assert False, "Not yet implemented"


class TestUrlFetch:
    @pytest.mark.xfail(reason="Awaiting service implementation (Plan 02)")
    def test_url_fetch_returns_sse_events(self, client: TestClient):
        """SRCI-02: URL fetched, extracted, stored as raw source."""
        assert False, "Not yet implemented"

    @pytest.mark.xfail(reason="Awaiting service implementation (Plan 02)")
    def test_thin_content_warning(self, client: TestClient):
        """D-07: Thin content flagged as possibly paywalled with quality_flags persisted."""
        assert False, "Not yet implemented"


class TestSourceList:
    @pytest.mark.xfail(reason="Awaiting endpoint implementation (Plan 02)")
    def test_list_sources_returns_indexed_sources(self, client: TestClient):
        """GET /api/sources returns list of ingested sources."""
        assert False, "Not yet implemented"
