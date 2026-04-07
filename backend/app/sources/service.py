"""Source ingestion service: PDF parsing, URL fetching, content hashing, SSRF protection."""

import asyncio
import hashlib
import ipaddress
import logging
import os
import socket
from collections.abc import AsyncGenerator
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse

import httpx
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from fastapi import HTTPException
from fastapi.sse import ServerSentEvent
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.config import Settings
from app.sources.models import RawSource
from app.sources.schemas import IngestionComplete, IngestionProgress

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Docling converter singleton (Pitfall 1: CPU-bound, reuse instance)
# ---------------------------------------------------------------------------


@lru_cache
def get_converter() -> DocumentConverter:
    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = False  # D-06: OCR disabled by default
    pipeline_options.do_table_structure = False  # Avoid model downloads at runtime
    pipeline_options.do_code_enrichment = False
    pipeline_options.do_formula_enrichment = False
    pipeline_options.document_timeout = 300.0  # 5 min for large PDFs

    return DocumentConverter(
        allowed_formats=[InputFormat.PDF, InputFormat.HTML],
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options),
        },
    )


# ---------------------------------------------------------------------------
# SSRF protection (T-02-03)
# ---------------------------------------------------------------------------


class UnsafeURLError(Exception):
    """Raised when a URL resolves to a non-public IP or uses a disallowed scheme."""

    pass


def validate_url_safety(url: str) -> None:
    """Validate URL is safe to fetch. Raises UnsafeURLError on failure.

    Checks:
    - Scheme allowlist (http/https only)
    - DNS resolution to non-private IP
    - Blocks loopback, link-local, and reserved addresses
    """
    parsed = urlparse(url)

    # Scheme allowlist
    if parsed.scheme not in ("http", "https"):
        raise UnsafeURLError(f"URL scheme must be http or https, got: {parsed.scheme}")

    # Resolve hostname to IP
    hostname = parsed.hostname
    if not hostname:
        raise UnsafeURLError("URL has no hostname")

    try:
        ip = ipaddress.ip_address(socket.gethostbyname(hostname))
    except (socket.gaierror, ValueError) as e:
        raise UnsafeURLError(f"Cannot resolve hostname: {hostname}") from e

    # Block private/loopback/link-local/reserved IPs
    if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
        raise UnsafeURLError(f"URL resolves to non-public IP: {ip}")


# ---------------------------------------------------------------------------
# Upload size validation (D-03)
# ---------------------------------------------------------------------------


def validate_upload_size(content_length: int, max_mb: int) -> None:
    """Raise 413 if content exceeds the upload limit."""
    if content_length > max_mb * 1024 * 1024:
        raise HTTPException(
            status_code=413, detail=f"This file exceeds the {max_mb} MB limit."
        )


# ---------------------------------------------------------------------------
# SSE helpers -- pass dicts to ServerSentEvent.data (FastAPI JSON-encodes them)
# ---------------------------------------------------------------------------


def _progress_event(status: str, message: str, **kwargs) -> ServerSentEvent:
    """Create a progress SSE event."""
    return ServerSentEvent(
        data=IngestionProgress(status=status, message=message, **kwargs).model_dump(),
        event="progress",
    )


def _error_event(**fields) -> ServerSentEvent:
    """Create an error SSE event."""
    return ServerSentEvent(data=fields, event="error")


def _complete_event(
    source: RawSource, markdown: str, quality_flags: list[str]
) -> ServerSentEvent:
    """Create a complete SSE event (D-13)."""
    return ServerSentEvent(
        data=IngestionComplete(
            id=source.id,
            title=source.title,
            author=source.author,
            parse_status=source.parse_status,
            page_count=source.page_count,
            content_preview=markdown[:500],
            source_type=source.source_type,
            quality_flags=quality_flags,
        ).model_dump(),
        event="complete",
    )


# ---------------------------------------------------------------------------
# PDF ingestion (SRCI-01, SRCI-03, D-01, D-02, D-04)
# ---------------------------------------------------------------------------


async def parse_pdf(
    file_path: Path,
    filename: str,
    session: Session,
    settings: Settings,
) -> AsyncGenerator[ServerSentEvent, None]:
    """Parse a PDF with docling, detect scanned pages, extract metadata, store as RawSource.

    Yields ServerSentEvent objects with event types: progress, complete, error.
    """
    try:
        yield _progress_event("parsing", "Parsing document...")

        # Run docling in threadpool (Pitfall 1: CPU-bound, must not block event loop)
        converter = get_converter()
        result = await asyncio.to_thread(converter.convert, str(file_path))

        markdown = result.document.export_to_markdown()
        page_count = len(result.document.pages)

        # D-01: Scanned page detection heuristic
        avg_chars = len(markdown) / max(page_count, 1)
        parse_status = "warning" if avg_chars < 50 else "parsed"
        quality_flags: list[str] = []
        if avg_chars < 50:
            quality_flags.append("scanned_pdf")

        # D-02: Duplicate check by content hash
        content_hash = hashlib.sha256(markdown.encode()).hexdigest()
        existing = session.exec(
            select(RawSource).where(RawSource.content_hash == content_hash)
        ).first()
        if existing:
            yield _error_event(
                error="This document has already been ingested.",
                existing_source_id=existing.id,
            )
            return

        # D-04: Extract author from PDF metadata via PyMuPDF (reliable metadata access)
        author = None
        try:
            import fitz

            doc = fitz.open(str(file_path))
            author = doc.metadata.get("author") or None
            doc.close()
        except ImportError:
            logger.info(
                "PyMuPDF (fitz) not available; skipping PDF metadata extraction"
            )
        except Exception:
            logger.warning("Could not extract PDF metadata from %s", filename)

        # D-04: Extract title -- prefer original filename stem (docling name is the temp path)
        title = Path(filename).stem

        # Save raw PDF to disk (T-02-01: hash-based filename prevents path traversal)
        # Atomic write: write to .tmp suffix, then os.replace()
        sources_dir = Path(settings.clinic_atlas_sources_dir)
        sources_dir.mkdir(parents=True, exist_ok=True)
        disk_path = str(sources_dir / f"{content_hash}.pdf")
        tmp_disk_path = f"{disk_path}.tmp"
        with open(file_path, "rb") as src, open(tmp_disk_path, "wb") as dst:
            while chunk := src.read(8192):
                dst.write(chunk)
        os.replace(tmp_disk_path, disk_path)

        # Create RawSource record
        source = RawSource(
            content=markdown,
            content_hash=content_hash,
            file_path=disk_path,
            title=title,
            author=author,
            mime_type="application/pdf",
            parse_status=parse_status,
            page_count=page_count,
            source_type="pdf",
            quality_flags=quality_flags,
        )

        try:
            session.add(source)
            session.commit()
            session.refresh(source)
        except IntegrityError:
            # Race condition: another request inserted the same content_hash
            session.rollback()
            existing = session.exec(
                select(RawSource).where(RawSource.content_hash == content_hash)
            ).first()
            yield _error_event(
                error="This document has already been ingested.",
                existing_source_id=existing.id if existing else None,
            )
            return

        yield _progress_event("indexing", "Indexing...")
        yield _complete_event(source, markdown, quality_flags)

    except Exception as e:
        logger.exception("Error parsing PDF %s", filename)
        yield _error_event(error=str(e))


# ---------------------------------------------------------------------------
# URL ingestion (SRCI-02, D-07, D-08, D-09, T-02-03)
# ---------------------------------------------------------------------------


async def fetch_and_parse_url(
    url: str,
    session: Session,
    settings: Settings,
) -> AsyncGenerator[ServerSentEvent, None]:
    """Fetch URL, extract content with docling, JS fallback for thin pages.

    Yields ServerSentEvent objects with event types: progress, complete, error.
    """
    try:
        # Validate URL safety (SSRF protection)
        try:
            validate_url_safety(url)
        except UnsafeURLError as e:
            yield _error_event(error=str(e))
            return

        yield _progress_event("fetching", "Fetching...")

        # Fetch with httpx
        async with httpx.AsyncClient(
            timeout=settings.httpx_timeout,
            follow_redirects=True,
            max_redirects=settings.max_redirects,
        ) as client:
            resp = await client.get(url, headers={"User-Agent": "ClinicAtlas/1.0"})
            resp.raise_for_status()

        # Post-redirect SSRF check (T-02-03: catches DNS rebinding)
        try:
            validate_url_safety(str(resp.url))
        except UnsafeURLError as e:
            yield _error_event(error=f"Redirect destination unsafe: {e}")
            return

        # Enforce max response size (T-02-10)
        if len(resp.content) > settings.max_response_size_mb * 1024 * 1024:
            yield _error_event(
                error=f"Response exceeds {settings.max_response_size_mb} MB limit."
            )
            return

        yield _progress_event("extracting", "Extracting content...")

        # Detect content type — PDFs fetched by URL should use the PDF pipeline
        content_type = resp.headers.get("content-type", "")
        is_pdf = "application/pdf" in content_type or url.lower().endswith(".pdf")

        converter = get_converter()

        if is_pdf:
            # Save to temp file and parse as PDF
            import tempfile

            tmp_fd, tmp_path = tempfile.mkstemp(suffix=".pdf")
            os.write(tmp_fd, resp.content)
            os.close(tmp_fd)
            try:
                result = await asyncio.to_thread(converter.convert, tmp_path)
            finally:
                os.unlink(tmp_path)
        else:
            # Parse HTML with docling in threadpool
            result = await asyncio.to_thread(
                lambda: converter.convert_string(
                    content=resp.text, format=InputFormat.HTML, name="page"
                )
            )
        markdown = result.document.export_to_markdown()

        quality_flags: list[str] = []

        if is_pdf:
            # PDF-specific: check for scanned content
            page_count = len(result.document.pages)
            avg_chars = len(markdown) / max(page_count, 1)
            if avg_chars < 50:
                quality_flags.append("scanned_pdf")

        # D-07: Thin content check (applies to HTML; skip for PDFs)
        if not is_pdf and len(markdown) < 200:
            quality_flags.append("thin_content")

            # D-08: JS fallback -- retry with Playwright
            yield _progress_event("extracting", "Retrying with browser rendering...")

            try:
                from playwright.async_api import async_playwright

                target_host = urlparse(url).hostname
                async with async_playwright() as p:
                    browser = await p.chromium.launch(headless=True)
                    context = await browser.new_context()

                    # T-02-09: Block subresource requests to non-target hosts
                    async def _route_handler(route):
                        req_host = urlparse(route.request.url).hostname
                        if req_host == target_host:
                            await route.continue_()
                        else:
                            await route.abort()

                    await context.route("**/*", _route_handler)
                    page = await context.new_page()
                    await page.goto(
                        url,
                        wait_until="networkidle",
                        timeout=settings.playwright_timeout,
                    )
                    html = await page.content()
                    await browser.close()

                # Re-parse with docling
                result = await asyncio.to_thread(
                    lambda: converter.convert_string(
                        content=html, format=InputFormat.HTML, name="page"
                    )
                )
                new_markdown = result.document.export_to_markdown()

                if len(new_markdown) >= 200:
                    markdown = new_markdown
                    quality_flags.remove("thin_content")
                    quality_flags.append("js_fallback_used")
                else:
                    # Still thin -- keep thin_content flag, use longer version if available
                    markdown = (
                        new_markdown if len(new_markdown) > len(markdown) else markdown
                    )

            except Exception as pw_err:
                logger.warning("Playwright fallback failed for %s: %s", url, pw_err)
                # Keep original thin content, proceed with what we have

        # D-09: Extract title (temp filenames from PDF conversion are not useful)
        title = getattr(result.document, "name", None)
        if not title or title == "page" or title.startswith("tmp"):
            parsed_url = urlparse(url)
            # Use the filename from the URL path if it looks meaningful
            path_stem = Path(parsed_url.path).stem
            if path_stem and len(path_stem) > 3 and not path_stem.startswith("tmp"):
                title = path_stem.replace("-", " ").replace("_", " ").strip()
            else:
                title = f"{parsed_url.netloc}{parsed_url.path}".rstrip("/")

        # D-02: Duplicate check by content hash
        content_hash = hashlib.sha256(markdown.encode()).hexdigest()
        existing = session.exec(
            select(RawSource).where(RawSource.content_hash == content_hash)
        ).first()
        if existing:
            yield _error_event(
                error="This content has already been ingested.",
                existing_source_id=existing.id,
            )
            return

        parse_status = "warning" if quality_flags else "parsed"

        # Create RawSource record
        source = RawSource(
            content=markdown,
            content_hash=content_hash,
            url=url,
            title=title,
            author=None,
            mime_type="application/pdf" if is_pdf else "text/html",
            parse_status=parse_status,
            page_count=len(result.document.pages) if is_pdf else None,
            source_type="url",
            quality_flags=quality_flags,
        )

        try:
            session.add(source)
            session.commit()
            session.refresh(source)
        except IntegrityError:
            session.rollback()
            existing = session.exec(
                select(RawSource).where(RawSource.content_hash == content_hash)
            ).first()
            yield _error_event(
                error="This content has already been ingested.",
                existing_source_id=existing.id if existing else None,
            )
            return

        yield _progress_event("indexing", "Indexing...")
        yield _complete_event(source, markdown, quality_flags)

    except Exception as e:
        logger.exception("Error fetching URL %s", url)
        yield _error_event(error=str(e))
