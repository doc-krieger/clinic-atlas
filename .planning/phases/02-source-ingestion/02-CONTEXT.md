# Phase 2: Source Ingestion - Context

**Gathered:** 2026-04-07
**Status:** Ready for planning

<domain>
## Phase Boundary

The physician can add clinical source material to the knowledge base via PDF upload or URL fetch, with quality guarantees before indexing. SearXNG can be queried for trusted source domains and returns results for user selection. Scanned/image-only PDFs are detected and flagged. This phase delivers the ingestion pipeline that feeds all downstream research and synthesis phases.

</domain>

<decisions>
## Implementation Decisions

### PDF Upload Flow
- **D-01:** Scanned/image-only PDF detection via text extraction heuristic — extract text with docling, flag pages yielding < ~50 chars average as potentially scanned. User sees a visible warning (SRCI-03).
- **D-02:** Duplicate detection by content hash — reject duplicate uploads with a message pointing to the existing source record. No new row created.
- **D-03:** 50 MB file size limit on PDF uploads. Covers all clinical guidelines and textbook chapters.
- **D-04:** Extract title, page count, and author from PDF document metadata. Title pre-fills the source record. Falls back to filename if no title in metadata.

### Document Parsing
- **D-05:** Use docling as the unified document parser for both PDF and HTML content, replacing the originally planned PyMuPDF4LLM + trafilatura combination. Better extraction quality, single dependency, built-in OCR capability if needed.
- **D-06:** Docling configured without heavy OCR by default (do_ocr=False). OCR can be enabled per-document or globally via config if scanned PDFs become common.

### URL Fetch Behavior
- **D-07:** Attempt fetch with httpx. If extracted content is very short (< 200 chars), flag as "possibly paywalled" but still store what was retrieved. User sees the warning.
- **D-08:** HTTP fetch with JS rendering fallback — try httpx first, if content is suspiciously thin, retry with a headless browser (Playwright). Most clinical guideline pages are server-rendered so the fallback rarely triggers.
- **D-09:** Auto-extract title from HTML `<title>` tag via docling. Fall back to URL domain+path if no title found. User can edit the source title after ingest.

### SearXNG Integration
- **D-10:** User picks which search results to ingest — show SearXNG results as a list, user selects which to fetch. No auto-ingestion. Prevents garbage from entering the KB.
- **D-11:** Domain scoping uses both site: filters in the query (built from source registry domains) AND post-filtering of results. Belt and suspenders — ensures no untrusted results leak through.

### Ingestion API Design
- **D-12:** Synchronous processing with SSE progress streaming — keep the connection open, stream progress events (e.g., "parsing page 3/50"). Single user, no contention. Good UX for large PDFs.
- **D-13:** On success, return the full RawSource record: id, title, parse_status, page_count, content preview (first 500 chars). Client has everything it needs.
- **D-14:** Separate endpoints for each operation: POST /api/sources/upload (multipart file for PDFs), POST /api/sources/fetch (JSON body with URL), POST /api/sources/search (SearXNG query). Clean separation, different input shapes.

### Claude's Discretion
- Exact docling pipeline configuration options (table extraction, formula enrichment)
- httpx timeout values and retry logic
- SSE event format and progress granularity
- Playwright headless browser configuration for JS fallback
- SearXNG query construction details (how many site: filters per query, pagination)
- Content preview truncation strategy for the API response

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements
- `.planning/REQUIREMENTS.md` — SRCI-01 (PDF upload), SRCI-02 (URL fetch), SRCI-03 (scanned PDF detection), SRCI-05 (SearXNG search)

### Project constraints
- `CLAUDE.md` — Tech stack specification, version constraints, stack patterns, what NOT to use

### Phase 1 foundation
- `.planning/phases/01-foundation/01-CONTEXT.md` — Database schema (RawSource model), disk layout, source registry, Docker Compose, FastAPI project structure

### Source registry
- `config/sources.yml` — Trusted source domains used for SearXNG query scoping and post-filtering

### Existing models
- `backend/app/sources/models.py` — RawSource model (content, content_hash, parse_status, mime_type)
- `backend/app/sources/registry.py` — SourceEntry with domain, requires_auth, reliability_tier
- `backend/app/sources/router.py` — Existing /api/sources/registry endpoint to extend

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `RawSource` model (backend/app/sources/models.py) — already has content, content_hash, parse_status, mime_type columns. Ready for ingestion pipeline to populate.
- `SourceRegistry` + `SourceEntry` (backend/app/sources/registry.py) — domain field available for SearXNG query scoping. `requires_auth` field for paywall warnings.
- `/api/sources/registry` endpoint (backend/app/sources/router.py) — returns all registered sources. Frontend can use this for domain display.
- `Settings.searxng_url` (backend/app/config.py) — SearXNG connection already configured.
- Health probe for SearXNG (backend/app/health/router.py) — already checks SearXNG availability.

### Established Patterns
- Feature-based module layout: app/sources/ has models.py, router.py, registry.py — add service.py for ingestion logic
- Pydantic BaseSettings for configuration — add upload size limit, docling config options here
- `GENERATED ALWAYS AS` tsvector pattern on raw_sources — new content auto-indexes on insert/update
- Atomic disk writes (write .tmp → fsync → rename) from D-22 — apply to source file storage

### Integration Points
- raw_sources table — ingestion pipeline writes here, search reads from here, research workflow reads from here
- data/sources/ directory — raw PDF/HTML files stored on disk, path recorded in raw_sources.file_path
- SearXNG at settings.searxng_url — JSON API for search, results filtered by source registry domains
- FastAPI SSE (EventSourceResponse) — use for progress streaming during ingest (same pattern Phase 3 uses for chat)

</code_context>

<specifics>
## Specific Ideas

- User prefers docling over PyMuPDF4LLM for extraction quality — even on non-scanned text PDFs and HTML pages, docling produces better structured output
- JS rendering fallback needed because some clinical knowledge bases (UpToDate, DynaMed) are JavaScript SPAs
- Source title should be auto-populated but always editable — reduces friction while preserving user control

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 02-source-ingestion*
*Context gathered: 2026-04-07*
