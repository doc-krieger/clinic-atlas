---
status: complete
phase: 02-source-ingestion
source: [02-01-SUMMARY.md, 02-02-SUMMARY.md, 02-03-SUMMARY.md, 02-04-SUMMARY.md]
started: 2026-04-07T22:00:00Z
updated: 2026-04-07T23:17:30Z
---

## Current Test

[testing complete]

## Tests

### 1. Cold Start Smoke Test
expected: Kill any running containers. Run `make up`. All services start without errors. Backend responds to requests. Frontend loads in browser.
result: pass

### 2. Navigate to Sources Page
expected: Click "Sources" in the sidebar. Page loads at /sources with three tabs visible: "Upload PDF", "Fetch URL", "Search Sources". Sources link shows active state in sidebar.
result: pass

### 3. Upload a PDF
expected: On the Upload PDF tab, drag a PDF file onto the drop zone (or click to pick a file). SSE progress appears showing stages (uploading, parsing, indexing). On completion, the source appears in the source list below with a PDF type badge and "complete" status.
result: issue
reported: "PDF upload completes successfully (progress bar shows 'Source indexed', scanned PDF warning displayed correctly), but the source list does not refresh to show the new source. List only refreshes after clicking 'Upload another' which resets the upload form. The refreshKey pattern triggers on form reset, not on ingestion completion."
severity: minor

### 4. Duplicate PDF Detection
expected: Upload the same PDF again. An error is shown indicating the source already exists (duplicate detected via content hash).
result: pass

### 5. Fetch a URL
expected: Switch to the "Fetch URL" tab. Enter a valid URL (e.g. a Wikipedia article). SSE progress streams showing fetch/extract/index stages. On completion, source appears in the list with appropriate type badge.
result: pass

### 6. SSRF Protection
expected: In the Fetch URL tab, enter a localhost URL (e.g. http://localhost:8000 or http://127.0.0.1). An error is shown rejecting the URL as non-public IP. The fetch does not proceed.
result: pass

### 7. Search Sources via SearXNG
expected: Switch to the "Search Sources" tab. Enter a search query (e.g. "neonatal jaundice guidelines"). Results appear from SearXNG with titles, URLs, and selection checkboxes.
result: pass

### 8. Batch Ingest from Search Results
expected: Select one or more search results using checkboxes. Click ingest. Each selected URL is fetched sequentially with SSE progress shown. Ingested sources appear in the source list.
result: pass

### 9. Source List Display
expected: After ingesting at least one source, the source list below the tabs shows all ingested sources. Each source displays: title, type badge (PDF/URL), status badge, and relative timestamp (e.g. "just now").
result: pass

## Summary

total: 9
passed: 8
issues: 1
pending: 0
skipped: 0
blocked: 0

## Gaps

- truth: "After PDF upload completes, the source list refreshes to show the newly ingested source"
  status: failed
  reason: "Source list does not refresh after PDF upload completion. Only refreshes after clicking 'Upload another' which resets the form. The refreshKey increment likely happens on form reset, not on SSE complete event."
  severity: minor
  test: 3
  root_cause: ""
  artifacts: []
  missing: []
  debug_session: ""
