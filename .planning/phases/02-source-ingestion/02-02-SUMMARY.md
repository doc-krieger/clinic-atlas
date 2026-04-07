---
phase: 02-source-ingestion
plan: 02
subsystem: backend, api, ingestion
tags: [docling, ssrf, sse, searxng, playwright, dedup]

# Dependency graph
requires:
  - phase: 02-source-ingestion
    plan: 01
    provides: RawSource model with quality_flags, schemas, docling deps, test fixtures
provides:
  - Ingestion service layer (parse_pdf, fetch_and_parse_url, validate_url_safety)
  - SearXNG client with domain scoping and post-filtering
  - Four API endpoints (GET /api/sources, POST upload/fetch/search)
  - SSE progress streaming for upload and fetch operations
  - SSRF protection with DNS resolution and redirect validation
  - 11 passing tests covering all ingestion paths
affects: [02-source-ingestion]

# Tech tracking
tech-stack:
  added: []
  patterns: [sse-manual-format, ssrf-dns-validation, docling-threadpool, lazy-fitz-import]

key-files:
  created:
    - backend/app/sources/service.py
    - backend/app/sources/searxng.py
  modified:
    - backend/app/sources/router.py
    - backend/tests/test_ingestion.py
    - backend/tests/test_searxng.py

key-decisions:
  - "Use return EventSourceResponse(generator) + format_sse_event for SSE endpoints -- allows pre-stream validation with proper HTTP error codes"
  - "Lazy import fitz (PyMuPDF) for author extraction -- graceful fallback if not installed"
  - "ServerSentEvent.data takes dicts (not JSON strings) -- FastAPI JSON-encodes them automatically"
  - "Dependency override pattern for test settings instead of patching lru_cache functions"

patterns-established:
  - "SSE endpoint pattern: regular async def does validation, returns EventSourceResponse wrapping async generator"
  - "_sse_to_bytes helper: converts ServerSentEvent to wire-format bytes using format_sse_event"
  - "SSRF validation: DNS resolution check + post-redirect revalidation"
  - "Playwright subresource blocking via context.route with hostname matching"

requirements-completed: [SRCI-01, SRCI-02, SRCI-03, SRCI-05]

# Metrics
duration: 15min
completed: 2026-04-07
---

# Phase 2 Plan 02: Source Ingestion Pipeline Summary

**Full backend ingestion pipeline: docling PDF parsing with scanned detection and author extraction, URL fetching with JS fallback and SSRF protection, SearXNG search with domain filtering, SSE progress streaming, and 11 passing tests**

## Performance

- **Duration:** 15 min
- **Started:** 2026-04-07T21:19:32Z
- **Completed:** 2026-04-07T21:34:47Z
- **Tasks:** 3
- **Files modified:** 5

## Accomplishments
- Ingestion service with PDF parsing (scanned detection, dedup, author extraction, quality_flags)
- URL fetching with httpx, Playwright JS fallback, thin content detection, SSRF protection
- SearXNG client with site: query scoping and domain post-filtering
- Four API endpoints: GET /api/sources, POST upload/fetch/search
- SSE streaming via EventSourceResponse with manual format_sse_event encoding
- 11 tests passing, zero xfail markers remaining

## Task Commits

1. **Task 1: Implement ingestion service layer with SSRF protection and SearXNG client** - `c873220` (feat)
2. **Task 2: Create SSE-streaming API endpoints and GET source list** - `0635635` (feat)
3. **Task 3: Implement and unskip ingestion and SearXNG tests** - `703e064` (test)

## Files Created/Modified
- `backend/app/sources/service.py` - Ingestion service: parse_pdf, fetch_and_parse_url, validate_url_safety, get_converter
- `backend/app/sources/searxng.py` - SearXNG client: search_searxng with domain filtering
- `backend/app/sources/router.py` - Added 4 endpoints: GET sources, POST upload/fetch/search
- `backend/tests/test_ingestion.py` - 8 tests: PDF upload, scanned detection, dedup, size limit, URL fetch, thin content, SSRF, source list
- `backend/tests/test_searxng.py` - 3 tests: filtered results, domain post-filtering, timeout handling

## Decisions Made
- SSE endpoints use `return EventSourceResponse(generator)` pattern, not yield-from-path-operation, because validation before streaming requires non-generator code that can raise HTTPException
- `format_sse_event` from `fastapi.routing` converts ServerSentEvent to wire-format bytes for StreamingResponse
- PyMuPDF (fitz) import is lazy with ImportError fallback since it may not be installed as a direct dependency
- Test settings use FastAPI dependency_overrides instead of patching lru_cache functions

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] SSE endpoint pattern incompatible with HTTPException**
- **Found during:** Task 2
- **Issue:** FastAPI's yield-pattern SSE generators cannot raise HTTPException (it creates an ExceptionGroup). Validation errors (413, 400) need proper HTTP responses.
- **Fix:** Changed to `return EventSourceResponse(generate())` pattern with manual SSE encoding via `format_sse_event`. Validation happens before the generator starts.
- **Files modified:** backend/app/sources/router.py

**2. [Rule 3 - Blocking] ServerSentEvent data double-serialization**
- **Found during:** Task 3
- **Issue:** Passing `json.dumps()` to `ServerSentEvent(data=...)` caused double JSON encoding. FastAPI auto-serializes the data field.
- **Fix:** Pass dicts/model.model_dump() to data instead of JSON strings. Created helper functions `_progress_event`, `_error_event`, `_complete_event`.
- **Files modified:** backend/app/sources/service.py

**3. [Rule 3 - Blocking] PyMuPDF (fitz) not installed in container**
- **Found during:** Task 3
- **Issue:** `import fitz` at module level failed because PyMuPDF is not a direct dependency (expected as docling transitive dep but not present).
- **Fix:** Changed to lazy import inside the function body with ImportError fallback.
- **Files modified:** backend/app/sources/service.py

## Issues Encountered
None beyond the auto-fixed deviations above.

## User Setup Required
None.

## Next Phase Readiness
- All backend ingestion endpoints operational
- Tests validate end-to-end flow with mocked docling/httpx
- Ready for Plan 03 (frontend sources page) to consume these endpoints
- Ready for Plan 04 (integration testing) to run full pipeline

---
*Phase: 02-source-ingestion*
*Completed: 2026-04-07*

## Self-Check: PASSED

All 5 key files verified present. All 3 task commits (c873220, 0635635, 703e064) confirmed in git log.
