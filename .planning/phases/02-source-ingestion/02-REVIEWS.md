---
phase: 2
reviewers: [codex]
reviewed_at: 2026-04-07T00:00:00Z
plans_reviewed: [02-01-PLAN.md, 02-02-PLAN.md, 02-03-PLAN.md, 02-04-PLAN.md]
review_round: 2
---

# Cross-AI Plan Review — Phase 2 (Round 2)

> Post-execution review of implemented plans. Round 1 review drove improvements to SSRF handling, quality_flags persistence, content_hash UNIQUE constraint, GET /api/sources endpoint, xfail→real tests, and serial batch ingestion. This round validates the executed plans.

## Codex Review

### Overall Summary
The plans are directionally strong and map well to Phase 2's success criteria. The main risks are concentrated in Plan 02: dependency weight, SSE implementation details, SSRF hardening with Playwright, and long-running synchronous ingestion semantics. I would approve the approach with targeted refinements before execution.

### Plan 01: Backend Infrastructure
**Summary:** Good foundation plan. It sequences schema, dependencies, Docker, and test scaffolds before service work, which reduces downstream churn.

**Strengths**
- Captures required metadata fields and persists `quality_flags`, which supports visible warnings and later auditability.
- Adds DB-level `UNIQUE` on `content_hash`, correctly backing duplicate detection with a durable constraint.
- Uses xfail scaffolds to define expected behavior before service implementation.

**Concerns**
- `MEDIUM`: Docling plus PyTorch can create build-time and runtime instability; the plan should pin versions and verify image size/startup time early.
- `MEDIUM`: `UNIQUE(content_hash)` needs explicit handling for empty extraction, null hashes, and duplicate error translation into user-facing API responses.
- `LOW`: xfail scaffolds are useful, but they can mask drift unless Plan 04 enforces their removal.

**Suggestions**
- Add indexes for common source-list filters such as `source_type`, creation date, and possibly status/quality flags if queryable.
- Define JSON column defaults and migration downgrade behavior explicitly.
- Add a dependency smoke test in Docker that imports docling and verifies the model cache path.

**Risk Assessment:** `MEDIUM` due to heavyweight dependencies and schema semantics, but the plan is otherwise well-contained.

### Plan 02: Backend Service Layer
**Summary:** This is the highest-value and highest-risk plan. It addresses the phase goals directly and has strong security intent, but the operational and edge-case details need tightening.

**Strengths**
- Uses `asyncio.to_thread()` for Docling parsing, avoiding event loop blockage.
- Treats SSRF seriously: scheme allowlist, DNS checks, redirect checks, size limits, and Playwright subresource blocking are the right categories.
- Persists quality flags rather than making them transient progress-only state.
- Domain scoping with both `site:` filters and post-filtering is the correct defense against search provider looseness.

**Concerns**
- `HIGH`: Verify the SSE implementation choice. `fastapi.sse.EventSourceResponse` is a suspicious import path; the plan should either use `StreamingResponse` directly or explicitly add/verify a supported SSE dependency.
- `HIGH`: Playwright SSRF protection is hard. DNS validation before fetch is not enough if redirects, browser subrequests, DNS rebinding, or browser-level navigation bypasses are not handled.
- `MEDIUM`: Long synchronous processing over SSE needs clear timeout, cancellation, cleanup, and client disconnect behavior.
- `MEDIUM`: URL extraction needs separate handling for thin content, paywalls, binary URLs, wrong content types, compressed response size, and parser failures.
- `MEDIUM`: Search-result ingestion needs partial failure semantics, duplicate handling, and deterministic result filtering.

**Suggestions**
- Define a stable SSE event contract: `progress`, `warning`, `error`, `complete`, with full `RawSource` only on completion.
- Add explicit tests for encrypted PDFs, malformed PDFs, image-only PDFs, very large PDFs, empty extracted markdown, duplicate content, redirect-to-private-IP, DNS rebinding-style host changes, and oversized compressed responses.
- Enforce Playwright request interception for all non-document subresources and revalidate every navigation URL.
- Translate DB uniqueness errors into a clear duplicate response rather than a generic 500.

**Risk Assessment:** `HIGH` because this plan carries the security boundary and the core ingestion behavior.

### Plan 03: Frontend
**Summary:** The frontend plan supports the user-facing success criteria well, especially visible quality warnings and source listing. Its main risk is custom SSE parsing and state management for long-running operations.

**Strengths**
- Three-tab structure maps cleanly to the three ingestion paths.
- Manual `fetch` plus `ReadableStream` is appropriate for POST upload/fetch flows where native `EventSource` is insufficient.
- AbortSignal cancellation and serial batch ingestion reduce backend load.
- Quality warnings for scanned PDFs and thin content directly satisfy key user-facing requirements.

**Concerns**
- `HIGH`: A custom SSE parser must correctly handle chunk boundaries, multi-line `data:`, event names, error payloads, and stream termination.
- `MEDIUM`: Serial search ingestion may feel slow; partial success/failure UX must be explicit.
- `MEDIUM`: Upload UX needs validation for file type, 50 MB limit, aborts, duplicate responses, and backend parse failures.
- `LOW`: Drag-and-drop needs keyboard-accessible fallback and clear status messaging.

**Suggestions**
- Add unit tests for the SSE stream utility with fragmented chunks and multi-event payloads.
- Refresh the source list after successful ingestion and preserve warnings in the list view.
- Show per-result status for search ingestion: pending, ingesting, success, duplicate, failed.
- Disable repeated submissions while an operation is active and expose cancel behavior consistently.

**Risk Assessment:** `MEDIUM` because UI scope is reasonable, but custom streaming UX has enough edge cases to warrant tests.

### Plan 04: Integration Verification
**Summary:** Strong verification plan, especially because it ties back to acceptance criteria and removes xfail/skips. It should be refined so the gate is strict on phase-critical tests without blocking on unrelated or environment-conditional skips.

**Strengths**
- Verifies all success criteria end-to-end.
- Includes negative API cases, especially SSRF, which is essential for this phase.
- Checks database schema, not just API behavior.
- User acceptance testing is appropriate because visible warning behavior matters.

**Concerns**
- `MEDIUM`: "Zero skips" can be too rigid if some tests are environment-conditional, such as Playwright or SearXNG availability.
- `MEDIUM`: SearXNG verification may be flaky unless backed by a controlled test service or fixture.
- `LOW`: Integration tests should validate the persisted `quality_flags`, not only streamed warnings.

**Suggestions**
- Replace "zero skips" with "zero unexpected skips/xfails"; allow explicitly marked environment-gated tests only if documented.
- Use local fixtures or mocks for SearXNG and URL targets, plus one optional smoke test against the real service.
- Add an end-to-end happy path for PDF upload, URL fetch, duplicate rejection, scanned-PDF flagging, and source listing.
- Include Docker Compose verification because dependency/cache behavior is a major project risk.

**Risk Assessment:** `MEDIUM`; the plan is strong, but test environment determinism needs attention.

---

## Consensus Summary

*Single reviewer (Codex) — consensus analysis requires 2+ reviewers.*

### Agreed Strengths
- Plans are well-structured with clear wave dependencies and requirement tracing
- Heavy dependency management (docling, PyTorch, Playwright) addressed early in Wave 1
- CPU-bound work correctly identified for threadpool offloading
- Security threat model included with STRIDE analysis
- quality_flags persisted to DB (not transient) — addresses Round 1 HIGH
- DB-level UNIQUE constraint on content_hash — addresses Round 1 HIGH
- GET /api/sources endpoint defined — addresses Round 1 HIGH
- Serial batch ingestion policy explicit — addresses Round 1 MEDIUM

### Top Concerns (Round 2)

1. **HIGH — SSE import path verification**: `fastapi.sse.EventSourceResponse` needs build-time verification (it exists in FastAPI 0.135.0+ per project constraints)
2. **HIGH — Playwright SSRF hardening**: DNS rebinding and browser-level navigation bypasses need explicit attention beyond current route blocking
3. **HIGH — Custom SSE parser robustness**: Frontend's manual fetch+ReadableStream parser must handle chunk boundaries, multi-line data fields, stream termination
4. **MEDIUM — Docling/PyTorch version pinning**: Build-time instability risk without pinned versions
5. **MEDIUM — Null/empty content_hash edge case**: UNIQUE constraint behavior with NULL values needs explicit handling
6. **MEDIUM — Environment-conditional test skips**: "Zero skips" gate may be too rigid for Playwright/SearXNG availability

### Divergent Views
*Single reviewer — no divergent views to report.*

### Actionable Items for Planning
- Verify `fastapi.sse` import at Docker build time (smoke test)
- Pin docling and PyTorch versions in pyproject.toml
- Add unit tests for SSE stream utility (fragmented chunks, multi-event payloads)
- Handle NULL content_hash in UNIQUE constraint (allow multiple NULLs)
- Add edge case tests: encrypted PDFs, malformed PDFs, DNS rebinding
- Allow documented environment-gated skips in Plan 04
