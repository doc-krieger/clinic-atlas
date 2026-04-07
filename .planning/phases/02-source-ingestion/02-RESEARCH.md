# Phase 2: Source Ingestion - Research

**Researched:** 2026-04-07
**Domain:** Document parsing (PDF + HTML), web search integration, SSE streaming
**Confidence:** HIGH

## Summary

Phase 2 implements three ingestion pathways: PDF upload with scanned-page detection, URL fetch with JS rendering fallback, and SearXNG search with selective ingestion. The user chose docling (D-05) as the unified document parser replacing PyMuPDF4LLM + trafilatura. This is the single most impactful decision -- docling requires PyTorch, which adds ~1.7 GB to the Docker image (CPU-only). The tradeoff is better extraction quality and a single dependency for both PDF and HTML.

The existing codebase provides a solid foundation: `RawSource` model with content hash and tsvector indexing, `SourceRegistry` with domain fields for SearXNG scoping, FastAPI SSE via `EventSourceResponse`, and Docker Compose with SearXNG already configured. The main work is adding the ingestion service layer (`app/sources/service.py`), three new API endpoints, schema migration for `page_count`, and the frontend sources page with three tabs.

**Primary recommendation:** Install docling with CPU-only PyTorch via `uv` explicit index. Use `StandardPdfPipeline` with `do_ocr=False` for PDFs, `convert_string()` for pre-fetched HTML. Use httpx for URL fetching with Playwright async fallback for JS-heavy pages. Stream progress via `ServerSentEvent` with custom event types.

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Scanned/image-only PDF detection via text extraction heuristic -- extract text with docling, flag pages yielding < ~50 chars average as potentially scanned. User sees a visible warning (SRCI-03).
- **D-02:** Duplicate detection by content hash -- reject duplicate uploads with a message pointing to the existing source record. No new row created.
- **D-03:** 50 MB file size limit on PDF uploads. Covers all clinical guidelines and textbook chapters.
- **D-04:** Extract title, page count, and author from PDF document metadata. Title pre-fills the source record. Falls back to filename if no title in metadata.
- **D-05:** Use docling as the unified document parser for both PDF and HTML content, replacing the originally planned PyMuPDF4LLM + trafilatura combination. Better extraction quality, single dependency, built-in OCR capability if needed.
- **D-06:** Docling configured without heavy OCR by default (do_ocr=False). OCR can be enabled per-document or globally via config if scanned PDFs become common.
- **D-07:** Attempt fetch with httpx. If extracted content is very short (< 200 chars), flag as "possibly paywalled" but still store what was retrieved. User sees the warning.
- **D-08:** HTTP fetch with JS rendering fallback -- try httpx first, if content is suspiciously thin, retry with a headless browser (Playwright). Most clinical guideline pages are server-rendered so the fallback rarely triggers.
- **D-09:** Auto-extract title from HTML `<title>` tag via docling. Fall back to URL domain+path if no title found. User can edit the source title after ingest.
- **D-10:** User picks which search results to ingest -- show SearXNG results as a list, user selects which to fetch. No auto-ingestion.
- **D-11:** Domain scoping uses both site: filters in the query (built from source registry domains) AND post-filtering of results.
- **D-12:** Synchronous processing with SSE progress streaming -- keep the connection open, stream progress events.
- **D-13:** On success, return the full RawSource record: id, title, parse_status, page_count, content preview (first 500 chars).
- **D-14:** Separate endpoints for each operation: POST /api/sources/upload (multipart), POST /api/sources/fetch (JSON), POST /api/sources/search (SearXNG query).

### Claude's Discretion
- Exact docling pipeline configuration options (table extraction, formula enrichment)
- httpx timeout values and retry logic
- SSE event format and progress granularity
- Playwright headless browser configuration for JS fallback
- SearXNG query construction details (how many site: filters per query, pagination)
- Content preview truncation strategy for the API response

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope.

</user_constraints>

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| SRCI-01 | User can upload PDF files which are parsed and stored as raw sources | Docling `DocumentConverter` with `StandardPdfPipeline`, `do_ocr=False`. POST /api/sources/upload multipart endpoint. SSE progress streaming. |
| SRCI-02 | User can submit a URL which is fetched, extracted, and stored as a raw source | httpx async fetch + docling `convert_string()` for HTML. Playwright fallback for JS pages. POST /api/sources/fetch endpoint. |
| SRCI-03 | Scanned/image-only PDFs are detected and flagged (not silently indexed) | Post-parse heuristic: check avg chars per page from docling output. Flag if < 50 chars/page average. Set `parse_status="warning"`. |
| SRCI-05 | System can search trusted source domains via SearXNG and ingest results | SearXNG JSON API at `settings.searxng_url`. Build query with site: filters from `SourceRegistry.all_sources`. POST /api/sources/search endpoint. User selects results, then fetches each via URL fetch pipeline. |

</phase_requirements>

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| docling | >=2.85.0 | Unified PDF + HTML parsing to markdown | User decision D-05. Replaces PyMuPDF4LLM + trafilatura. Single dependency for both formats. IBM-backed, MIT licensed. [VERIFIED: PyPI registry -- 2.85.0 latest as of 2026-04-07] |
| torch (CPU) | >=2.6.0 | ML inference for docling layout analysis | Required by docling's StandardPdfPipeline. CPU-only build via PyTorch index keeps Docker image at ~1.7 GB vs ~9.7 GB with CUDA. [VERIFIED: PyTorch docs] |
| httpx | >=0.28.0 | Async HTTP client for URL fetching | Already in pyproject.toml. Async, HTTP/2, connection pooling. [VERIFIED: existing dependency] |
| playwright | >=1.52.0 | JS rendering fallback for SPA pages | D-08 requires headless browser fallback. Async API integrates with FastAPI. [VERIFIED: pip3 show -- 1.52.0 installed on host] |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| python-multipart | (bundled) | Multipart file upload parsing | Required by FastAPI for `UploadFile`. Already included with `fastapi[standard]`. [VERIFIED: FastAPI docs] |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| docling | PyMuPDF4LLM + trafilatura | Overridden by user decision D-05. PyMuPDF4LLM is lighter (no PyTorch) but two dependencies, and user explicitly chose docling for quality. |
| Playwright | Selenium | Playwright has better async support, auto-wait, smaller footprint. Selenium would work but is heavier. |

### Installation

**Backend dependencies (add to pyproject.toml):**
```toml
# In [project] dependencies:
"docling>=2.85.0",
"playwright>=1.52.0",

# In pyproject.toml at the end:
[tool.uv.sources]
torch = [{ index = "pytorch-cpu" }]
torchvision = [{ index = "pytorch-cpu" }]

[[tool.uv.index]]
name = "pytorch-cpu"
url = "https://download.pytorch.org/whl/cpu"
explicit = true
```

**Playwright browser install (in Dockerfile):**
```bash
RUN playwright install chromium --with-deps
```

**Frontend (shadcn components for UI-SPEC):**
```bash
pnpm dlx shadcn@latest add tabs badge progress alert dialog checkbox skeleton
```

## Architecture Patterns

### Recommended Project Structure
```
backend/app/sources/
  __init__.py
  models.py          # RawSource model (exists, needs page_count migration)
  router.py          # Add upload/fetch/search endpoints
  service.py          # NEW: ingestion logic (parse, hash, store)
  schemas.py          # NEW: Pydantic request/response schemas
  registry.py         # Exists: SourceEntry, SourceRegistry
  searxng.py          # NEW: SearXNG client wrapper

frontend/src/
  app/sources/
    page.tsx           # Sources page with SourceTabs
  components/sources/
    source-tabs.tsx
    pdf-upload-tab.tsx
    url-fetch-tab.tsx
    search-tab.tsx
    search-result-item.tsx
    ingestion-progress.tsx
    quality-warning.tsx
    source-list.tsx
    source-list-item.tsx
```

### Pattern 1: SSE Progress Streaming for Ingestion
**What:** Stream progress events during PDF parsing / URL fetching using FastAPI native SSE.
**When to use:** All three ingestion endpoints (upload, fetch, search-ingest).
**Example:**
```python
# Source: FastAPI SSE docs (https://fastapi.tiangolo.com/tutorial/server-sent-events/)
from fastapi.sse import EventSourceResponse, ServerSentEvent

@router.post("/upload", response_class=EventSourceResponse)
async def upload_pdf(file: UploadFile) -> AsyncIterable[ServerSentEvent]:
    async def generate():
        yield ServerSentEvent(data={"status": "uploading"}, event="progress")
        # ... parse with docling ...
        yield ServerSentEvent(data={"status": "parsing", "page": 3, "total": 50}, event="progress")
        # ... on complete ...
        yield ServerSentEvent(data={"source": source_dict}, event="complete")
    return EventSourceResponse(generate())
```
[VERIFIED: Context7 /fastapi/fastapi -- EventSourceResponse + ServerSentEvent from fastapi.sse]

### Pattern 2: Docling PDF Conversion with Scanned Detection
**What:** Parse PDF with docling, check text density per page, flag scanned pages.
**When to use:** PDF upload endpoint (SRCI-01, SRCI-03).
**Example:**
```python
# Source: Context7 /docling-project/docling
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions

pipeline_options = PdfPipelineOptions()
pipeline_options.do_ocr = False           # D-06
pipeline_options.do_table_structure = True  # Keep table extraction
pipeline_options.do_code_enrichment = False
pipeline_options.do_formula_enrichment = False

converter = DocumentConverter(
    allowed_formats=[InputFormat.PDF, InputFormat.HTML],
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options),
    },
)

result = converter.convert(pdf_path)
markdown = result.document.export_to_markdown()
page_count = len(result.document.pages)

# D-01: Scanned page detection heuristic
avg_chars = len(markdown) / max(page_count, 1)
is_likely_scanned = avg_chars < 50
```
[VERIFIED: Context7 /docling-project/docling -- PdfPipelineOptions, export_to_markdown, pages dict]

### Pattern 3: HTML Fetch with JS Fallback
**What:** Fetch URL with httpx, check content length, retry with Playwright if thin.
**When to use:** URL fetch endpoint (SRCI-02, D-07, D-08).
**Example:**
```python
import httpx
from playwright.async_api import async_playwright

async def fetch_url_content(url: str) -> tuple[str, bool]:
    """Returns (html_content, used_js_fallback)."""
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        html = resp.text

    # Check if content is suspiciously thin
    from docling.document_converter import DocumentConverter
    from docling.datamodel.base_models import InputFormat
    converter = DocumentConverter()
    result = converter.convert_string(content=html, format=InputFormat.HTML, name="page")
    text = result.document.export_to_markdown(strict_text=True)

    if len(text) < 200:
        # D-08: JS rendering fallback
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, wait_until="networkidle", timeout=30000)
            html = await page.content()
            await browser.close()
        result = converter.convert_string(content=html, format=InputFormat.HTML, name="page")
        text = result.document.export_to_markdown(strict_text=True)
        return text, True

    return text, False
```
[VERIFIED: Context7 /microsoft/playwright-python -- async_playwright, chromium.launch, page.goto]
[VERIFIED: Context7 /docling-project/docling -- convert_string with InputFormat.HTML]

### Pattern 4: Content Hash Deduplication
**What:** SHA-256 hash of extracted content to detect duplicate uploads.
**When to use:** Before inserting any RawSource record (D-02).
**Example:**
```python
import hashlib

content_hash = hashlib.sha256(markdown_content.encode()).hexdigest()
existing = session.exec(
    select(RawSource).where(RawSource.content_hash == content_hash)
).first()
if existing:
    raise DuplicateSourceError(existing_id=existing.id)
```
[ASSUMED -- standard Python hashlib pattern]

### Pattern 5: SearXNG JSON API Query
**What:** Query SearXNG with domain-scoped search, return structured results.
**When to use:** Search endpoint (SRCI-05, D-10, D-11).
**Example:**
```python
async def search_searxng(query: str, domains: list[str], limit: int = 10) -> list[dict]:
    # D-11: Build site:-scoped query
    site_filters = " OR ".join(f"site:{d}" for d in domains[:5])
    scoped_query = f"({site_filters}) {query}"

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{settings.searxng_url}/search",
            params={"q": scoped_query, "format": "json", "pageno": 1},
            timeout=15.0,
        )
        resp.raise_for_status()
        data = resp.json()

    # D-11: Post-filter to trusted domains only
    trusted = {d for d in domains}
    results = []
    for r in data.get("results", []):
        from urllib.parse import urlparse
        domain = urlparse(r["url"]).netloc.lstrip("www.")
        if domain in trusted:
            results.append({
                "title": r.get("title", ""),
                "url": r["url"],
                "snippet": r.get("content", ""),
                "domain": domain,
            })
    return results[:limit]
```
[CITED: SearXNG search API docs -- https://docs.searxng.org/dev/search_api.html]

### Anti-Patterns to Avoid
- **Running docling in an async handler without threadpool:** Docling's `convert()` is CPU-bound and synchronous. Wrap in `asyncio.to_thread()` or use `run_in_executor()` to avoid blocking the event loop.
- **Storing raw PDF bytes in the database:** Store file on disk at `data/sources/<hash>.pdf`, store only the path in `RawSource.file_path`. Database stores extracted markdown in `content`.
- **Proxying SSE through Next.js:** Per CLAUDE.md, connect browser `EventSource` directly to FastAPI. Next.js buffers SSE responses.
- **Using `convert()` with a URL for HTML:** Docling's URL fetching uses `requests` (sync). Use httpx to fetch HTML async, then `convert_string()` with `InputFormat.HTML`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| PDF text extraction | Custom fitz/pypdf reader | docling `DocumentConverter` | Layout analysis, table structure, metadata extraction -- hundreds of edge cases |
| HTML content extraction | regex/BeautifulSoup scraper | docling `convert_string(format=HTML)` | Boilerplate removal, structure preservation handled by docling |
| SSE protocol | Manual `text/event-stream` formatting | `fastapi.sse.EventSourceResponse` + `ServerSentEvent` | Keep-alive pings, proper encoding, cache headers |
| File upload parsing | Manual multipart parsing | FastAPI `UploadFile` | Handles temp files, content type, streaming |
| Content hashing | Custom hash function | `hashlib.sha256` | Standard, fast, collision-resistant |
| JS rendering | Custom puppeteer wrapper | Playwright async API | Auto-wait, proper cleanup, well-maintained |

## Common Pitfalls

### Pitfall 1: Docling Blocks the Event Loop
**What goes wrong:** `converter.convert()` is CPU-bound (layout analysis, table detection). Calling it in an async handler blocks all other requests.
**Why it happens:** Docling uses PyTorch inference which is inherently synchronous.
**How to avoid:** Wrap docling calls in `asyncio.to_thread(converter.convert, path)`. This offloads to a thread pool.
**Warning signs:** Slow API responses during PDF parsing, SSE events stop flowing.

### Pitfall 2: Docker Image Size Explosion
**What goes wrong:** Default PyTorch install pulls CUDA libraries, image grows to ~9-10 GB.
**Why it happens:** PyPI torch wheel includes CUDA by default.
**How to avoid:** Use `uv` explicit index pointing to `https://download.pytorch.org/whl/cpu`. Pin torch source in `[tool.uv.sources]`.
**Warning signs:** `docker build` takes 20+ minutes, image is > 3 GB.

### Pitfall 3: Docling Model Download on First Run
**What goes wrong:** Docling downloads ML models (~500 MB) from HuggingFace on first `convert()` call. In Docker, this happens every container restart.
**Why it happens:** Models are cached in `~/.cache/docling/` by default.
**How to avoid:** Add a Docker volume for `~/.cache/docling` or pre-download models in Dockerfile build step. Alternatively, mount a named volume: `docling_cache:/home/appuser/.cache/docling`.
**Warning signs:** First PDF conversion takes 2-5 minutes, subsequent ones are fast.

### Pitfall 4: Playwright Browser Not Installed in Docker
**What goes wrong:** `playwright install chromium` downloads browser binaries. Without `--with-deps`, system libraries are missing.
**Why it happens:** Slim base images lack required shared libraries (libglib, libx11, etc.).
**How to avoid:** Run `playwright install chromium --with-deps` in Dockerfile. This installs both the browser and system dependencies.
**Warning signs:** `BrowserType.launch: Executable doesn't exist` error.

### Pitfall 5: SSE Connection Drops on Large PDFs
**What goes wrong:** Processing a 50 MB PDF can take minutes. Load balancers or proxies may time out the SSE connection.
**Why it happens:** Nginx/reverse proxy default timeout is often 60s.
**How to avoid:** Send periodic keep-alive SSE comments (FastAPI does this automatically every 15s). For dev, no reverse proxy is involved. Document the requirement for production.
**Warning signs:** Client receives error event mid-processing.

### Pitfall 6: SearXNG Rate Limiting
**What goes wrong:** SearXNG may rate-limit or block requests if queried too rapidly.
**Why it happens:** Upstream search engines (Google, Bing) have rate limits that SearXNG respects.
**How to avoid:** Single-user app, unlikely to hit limits. But add a reasonable delay (1s) between ingesting multiple search results.
**Warning signs:** SearXNG returns empty results or HTTP 429.

## Code Examples

### Docling Converter Initialization (Singleton)
```python
# Source: Context7 /docling-project/docling
from functools import lru_cache
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions

@lru_cache
def get_converter() -> DocumentConverter:
    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = False
    pipeline_options.do_table_structure = True
    pipeline_options.do_code_enrichment = False
    pipeline_options.do_formula_enrichment = False
    pipeline_options.document_timeout = 300.0  # 5 min for large PDFs

    return DocumentConverter(
        allowed_formats=[InputFormat.PDF, InputFormat.HTML],
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options),
        },
    )
```
[VERIFIED: Context7 /docling-project/docling]

### RawSource Schema Extension
```python
# Migration needed: add page_count, source_type, author to raw_sources
class RawSource(SQLModel, table=True):
    __tablename__ = "raw_sources"
    # ... existing fields ...
    page_count: Optional[int] = None       # D-04: PDF page count
    source_type: str = Field(default="pdf") # "pdf" | "url" | "search"
    author: Optional[str] = None           # D-04: extracted from PDF metadata
```
[ASSUMED -- based on D-04 and D-13 requirements]

### SSE Event Schema
```python
from pydantic import BaseModel
from typing import Optional

class IngestionProgress(BaseModel):
    status: str           # "uploading" | "parsing" | "fetching" | "extracting" | "indexing" | "complete" | "error"
    page: Optional[int] = None
    total: Optional[int] = None
    message: Optional[str] = None

class IngestionComplete(BaseModel):
    id: int
    title: Optional[str]
    author: Optional[str]  # D-04: extracted from PDF metadata
    parse_status: str
    page_count: Optional[int]
    content_preview: str   # First 500 chars (D-13)
    source_type: str
```
[ASSUMED -- designed from D-04, D-12, D-13 requirements]

### Frontend SSE Consumer
```typescript
// Source: MDN EventSource API
const eventSource = new EventSource(
  `${process.env.NEXT_PUBLIC_API_URL}/api/sources/upload`,
  // Note: EventSource only supports GET. For POST uploads,
  // use fetch() with ReadableStream or a library like @microsoft/fetch-event-source
);
```
**Important:** Native `EventSource` only supports GET requests. For POST endpoints (file upload, URL fetch), use `@microsoft/fetch-event-source` or a manual `fetch()` + `ReadableStream` approach. This is a critical implementation detail.
[VERIFIED: MDN EventSource spec -- GET only]

### fetch-event-source Pattern for POST SSE
```typescript
import { fetchEventSource } from "@microsoft/fetch-event-source";

await fetchEventSource(`${API_URL}/api/sources/upload`, {
  method: "POST",
  body: formData,
  onmessage(ev) {
    if (ev.event === "progress") {
      const data = JSON.parse(ev.data);
      setProgress(data);
    } else if (ev.event === "complete") {
      const source = JSON.parse(ev.data);
      addSource(source);
    }
  },
  onerror(err) {
    // Handle error
  },
});
```
[ASSUMED -- standard pattern for @microsoft/fetch-event-source]

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| PyMuPDF4LLM + trafilatura (separate) | docling unified parser | User decision D-05 | Single dependency, better quality, but adds PyTorch |
| `sse-starlette` (third-party) | `fastapi.sse.EventSourceResponse` | FastAPI 0.135.0 (2025) | No third-party SSE library needed |
| Native `EventSource` for POST | `@microsoft/fetch-event-source` | N/A | EventSource API is GET-only; POST needs fetch wrapper |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Content hash uses SHA-256 of extracted markdown text | Architecture Pattern 4 | LOW -- any hash works, SHA-256 is standard |
| A2 | RawSource needs `page_count`, `source_type`, and `author` columns added via migration | Code Examples | MEDIUM -- if schema differs, migration needs adjustment |
| A3 | `@microsoft/fetch-event-source` is the right library for POST SSE on frontend | Code Examples | MEDIUM -- alternative is manual fetch+ReadableStream, but this library is widely used |
| A4 | Docling model cache is at `~/.cache/docling/` | Pitfall 3 | LOW -- may be at `~/.cache/huggingface/` instead, volume mount path may need adjustment |
| A5 | Docling `result.document.pages` dict gives page count | Architecture Pattern 2 | LOW -- verified from Context7 docs showing `for page_no, page in result.document.pages.items()` |

## Open Questions (RESOLVED)

1. **Docling model pre-download strategy** -- RESOLVED
   - What we know: Docling downloads ~500 MB of models on first use. Docker volume can cache them.
   - What's unclear: Whether to pre-download in Dockerfile (larger image, faster cold start) or use a volume mount (smaller image, slow first run).
   - Resolution: Use a Docker named volume `docling_models:/home/appuser/.cache`. First run is slow, subsequent runs are fast. Avoids bloating the image further. Implemented in Plan 01 Task 1.

2. **`@microsoft/fetch-event-source` vs manual fetch** -- RESOLVED
   - What we know: Native EventSource is GET-only. POST SSE needs a wrapper.
   - What's unclear: Whether `@microsoft/fetch-event-source` is still maintained and compatible with React 19.
   - Resolution: Use manual `fetch()` + `ReadableStream` implementation (~40 lines in `frontend/src/lib/sse.ts`). Avoids dependency risk. Implemented in Plan 03 Task 1.

3. **Docling thread safety** -- RESOLVED
   - What we know: `DocumentConverter` is called via `asyncio.to_thread()`. Single-user app.
   - What's unclear: Whether `DocumentConverter` instance is safe to share across threads.
   - Resolution: Use a singleton converter via `@lru_cache` (it's stateless after init). If issues arise, create a new instance per request. Implemented in Plan 02 Task 1.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| PostgreSQL | Data layer | Yes (Docker) | 17 | -- |
| SearXNG | SRCI-05 search | Yes (Docker) | latest | -- |
| Playwright | D-08 JS fallback | Yes (host) | 1.52.0 | Need browser install in Docker |
| Docker Compose | Dev environment | Yes | v2 | -- |
| Ollama | Not needed this phase | Yes (Docker) | latest | -- |

**Missing dependencies with no fallback:**
- None -- all dependencies are available or installable.

**Missing dependencies with fallback:**
- Playwright browsers need to be installed inside the Docker container (`playwright install chromium --with-deps`). Not blocking -- standard Dockerfile step.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework (backend) | pytest 9.x + pytest-asyncio 0.25.x |
| Framework (frontend) | vitest (jsdom) |
| Config file (backend) | `backend/pyproject.toml` [tool.pytest.ini_options] |
| Config file (frontend) | `frontend/vitest.config.ts` |
| Quick run command (backend) | `docker compose exec backend uv run pytest tests/test_sources_service.py -x` |
| Full suite command | `make test` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SRCI-01 | PDF upload parses and stores RawSource | integration | `docker compose exec backend uv run pytest tests/test_ingestion.py::test_pdf_upload -x` | No -- Wave 0 |
| SRCI-02 | URL fetch extracts and stores RawSource | integration | `docker compose exec backend uv run pytest tests/test_ingestion.py::test_url_fetch -x` | No -- Wave 0 |
| SRCI-03 | Scanned PDF flagged with warning | unit | `docker compose exec backend uv run pytest tests/test_ingestion.py::test_scanned_pdf_detection -x` | No -- Wave 0 |
| SRCI-05 | SearXNG search returns filtered results | unit (mocked) | `docker compose exec backend uv run pytest tests/test_searxng.py -x` | No -- Wave 0 |
| D-02 | Duplicate content hash rejection | unit | `docker compose exec backend uv run pytest tests/test_ingestion.py::test_duplicate_rejection -x` | No -- Wave 0 |

### Sampling Rate
- **Per task commit:** `docker compose exec backend uv run pytest tests/test_ingestion.py -x`
- **Per wave merge:** `make test`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `backend/tests/test_ingestion.py` -- covers SRCI-01, SRCI-02, SRCI-03, D-02
- [ ] `backend/tests/test_searxng.py` -- covers SRCI-05
- [ ] Small test PDF fixture at `backend/tests/fixtures/sample.pdf` (a 2-page text PDF)
- [ ] SearXNG mock fixture for search result tests

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | Single-user, no auth |
| V3 Session Management | No | Stateless API |
| V4 Access Control | No | Single-user |
| V5 Input Validation | Yes | Pydantic schemas for request validation, file type + size validation |
| V6 Cryptography | No | No encryption needed (local-first) |

### Known Threat Patterns for This Phase

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Malicious PDF upload | Tampering | Validate MIME type, enforce 50 MB limit, docling sandboxes parsing |
| Path traversal via filename | Tampering | Generate deterministic filename from content hash, never use user-provided filename for disk path |
| SSRF via URL fetch | Spoofing | Validate URL scheme (https only), don't follow redirects to internal IPs. httpx `follow_redirects=True` but verify final URL is not private. |
| XSS via stored markdown | Tampering | react-markdown sanitizes by default (no `dangerouslySetInnerHTML`). Docling output is markdown text, not raw HTML. |

## Sources

### Primary (HIGH confidence)
- Context7 `/docling-project/docling` -- DocumentConverter API, PdfPipelineOptions, convert_string, export_to_markdown
- Context7 `/fastapi/fastapi` -- EventSourceResponse, ServerSentEvent from fastapi.sse
- Context7 `/microsoft/playwright-python` -- async_playwright, chromium.launch, page.goto
- Context7 `/websites/astral_sh_uv` -- explicit index for PyTorch CPU, tool.uv.sources
- [PyPI docling](https://pypi.org/project/docling/) -- version 2.85.0 current
- [SearXNG search API docs](https://docs.searxng.org/dev/search_api.html) -- JSON format, query params

### Secondary (MEDIUM confidence)
- [Reducing Docling Docker image size](https://shekhargulati.com/2025/02/05/reducing-size-of-docling-pytorch-docker-image/) -- 9.7 GB to 1.7 GB with CPU-only torch
- [Docling installation docs](https://docling-project.github.io/docling/getting_started/installation/) -- PyTorch dependency confirmed

### Tertiary (LOW confidence)
- Docling model cache location (`~/.cache/docling/`) -- inferred from HuggingFace patterns, needs verification at runtime

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- docling verified on PyPI, API verified via Context7, PyTorch CPU index verified via uv docs
- Architecture: HIGH -- patterns verified against official docs, existing codebase well understood
- Pitfalls: HIGH -- Docker size issue verified with real numbers, SSE GET-only limitation is spec-level

**Research date:** 2026-04-07
**Valid until:** 2026-05-07 (docling is fast-moving, check for API changes)
