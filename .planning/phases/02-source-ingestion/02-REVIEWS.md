---
phase: 2
reviewers: [codex]
reviewed_at: 2026-04-07T00:00:00Z
plans_reviewed: [02-01-PLAN.md, 02-02-PLAN.md, 02-03-PLAN.md, 02-04-PLAN.md]
---

# Cross-AI Plan Review — Phase 2

## Codex Review

**Overall Assessment**
The plans are directionally solid and likely achieve Phase 2, but several contracts need tightening before execution. The biggest risks are arbitrary URL fetching with Playwright fallback, persistence of ingestion quality flags, SSE lifecycle/error handling, and ensuring skipped scaffold tests do not create false confidence.

### Plan 01: Backend Infrastructure
**Summary**
Good foundation for dependencies, schema, config, and test fixtures, but it should explicitly add the persistent fields and constraints required by later plans.

**Strengths**
- Captures heavy dependency concerns early: docling, Playwright, CPU-only PyTorch, model cache volume.
- Adds schema/config scaffolding before backend and frontend implementation.
- Introduces fixtures and requirement-linked test placeholders.

**Concerns**
- `HIGH`: Migration does not mention persistent `quality_flags`/`ingestion_status` fields for scanned or thin-content warnings, so warnings may become transient SSE-only state.
- `HIGH`: Duplicate detection needs a DB-level unique constraint on `content_hash`; service-only checks are race-prone.
- `MEDIUM`: `pytest.skip` scaffolds can make the phase look green unless Plan 04 explicitly fails on remaining skips.
- `MEDIUM`: Heavy dependency installation needs pinned versions and lockfile validation to avoid CUDA wheels or browser install drift.

**Suggestions**
- Add or confirm fields for `content_hash`, `quality_flags`, `ingestion_status`, `parse_error`, `source_type`, `page_count`, `author`, and storage path/source URL as applicable.
- Use `xfail` or TODO markers that Plan 04 checks, rather than permanent skips.
- Specify migration nullability/backfill behavior for existing `RawSource` rows.

**Risk Assessment**
`MEDIUM`: The direction is sound, but missing persistence/constraint details could undermine later plans.

### Plan 02: Backend Service Layer
**Summary**
This is the core of the phase and covers the required workflows, but it carries the highest implementation and security risk.

**Strengths**
- Separates ingestion service, SearXNG client, and router responsibilities.
- Correctly treats docling conversion as CPU-bound and plans thread offloading.
- Includes deduplication, metadata extraction, scanned/thin-content checks, and mocked tests.

**Concerns**
- `HIGH`: SSRF mitigation is under-specified for redirects, DNS rebinding, non-HTTP schemes, ports, proxy env vars, and Playwright subresource requests.
- `HIGH`: Synchronous SSE processing needs concurrency limits, cancellation handling, timeouts, and cleanup on client disconnect.
- `MEDIUM`: `IngestSelectedRequest` and frontend batch ingest do not clearly map to D-14's three endpoints unless selected results call `/fetch` one-by-one.
- `MEDIUM`: Malformed/encrypted PDFs, zero-page outputs, docling failures, and partial URL fetches need explicit error events and persisted failure states.
- `MEDIUM`: File write and DB insert order must be atomic enough to avoid orphan files and duplicate races.

**Suggestions**
- Add a dedicated URL safety layer: scheme allowlist, DNS/IP validation per redirect, redirect cap, max response size, content-type checks, timeout, and proxy disabling.
- For Playwright, block navigation/subrequests outside the validated host or trusted allowlist.
- Define SSE event names and payloads up front: `progress`, `warning`, `duplicate`, `complete`, `error`.
- Add a bounded semaphore around docling/Playwright work to avoid CPU and memory exhaustion.

**Risk Assessment**
`HIGH`: The plan can achieve the phase goals, but arbitrary URL fetching plus Playwright makes security and resource control non-optional.

### Plan 03: Frontend Sources Page
**Summary**
The UI plan matches the intended user workflows, but it depends on backend contracts that are not yet precise enough.

**Strengths**
- Aligns the UI with the three user actions: upload, fetch URL, and search sources.
- Correctly accounts for POST-based SSE using `fetch` plus `ReadableStream`.
- Includes visible quality warnings for scanned PDFs and thin URL content.

**Concerns**
- `HIGH`: `SourceList` requires an API to list indexed raw sources; if Phase 1 already has it, the plan should reference it explicitly.
- `MEDIUM`: The SSE utility must handle partial frames, stream errors, final error events, cancellation, and UTF-8 chunk boundaries.
- `MEDIUM`: Batch ingest from selected search results needs a defined serial/parallel policy and a clear mapping to backend endpoints.
- `LOW`: shadcn component installation and nav polish are reasonable, but should not block the core ingestion workflow.

**Suggestions**
- Create or share typed event contracts for progress, complete, warning, duplicate, and error payloads.
- Display durable states for duplicate source, scanned PDF, thin URL, JS fallback used, parse failure, cancel, and retry.
- Limit concurrent selected-result ingests to avoid opening too many SSE streams.

**Risk Assessment**
`MEDIUM`: Mostly execution risk from unclear contracts and batch-ingest behavior.

### Plan 04: Integration Verification
**Summary**
The verification gate is necessary, but it should be more explicit and failure-oriented to prevent superficial completion.

**Strengths**
- Includes full test/lint runs, API curl checks, manual E2E, and a user acceptance checkpoint.
- Correctly waits until backend and frontend implementation are complete.
- Maps to the four main ingestion pathways.

**Concerns**
- `HIGH`: It must fail if scaffolded skipped tests remain; otherwise requirements can appear covered without real tests.
- `MEDIUM`: Needs Docker Compose verification for Postgres migrations, SearXNG, Playwright browser dependencies, and docling cache cold/warm behavior.
- `MEDIUM`: Manual E2E should include negative cases: scanned PDF, duplicate upload, thin/paywalled URL, SSRF denial, and parse failure.
- `LOW`: Curl SSE checks should verify streaming events and final `complete`/`error`, not just HTTP 200.

**Suggestions**
- Add an acceptance checklist mapped directly to SRCI-01, SRCI-02, SRCI-03, and SRCI-05.
- Run migrations on both a clean DB and an existing Phase 1 DB.
- Capture exact UAT fixtures: text PDF, scanned/image PDF, known trusted-domain query, and controlled URL fallback case.

**Risk Assessment**
`MEDIUM`: The verification concept is good, but it needs sharper pass/fail criteria to catch integration gaps.

---

## Consensus Summary

*Single reviewer (Codex) — consensus requires 2+ reviewers.*

### Key Strengths
- Plans are well-structured with clear wave dependencies and requirement tracing
- Heavy dependency management (docling, PyTorch, Playwright) addressed early in Wave 1
- CPU-bound work correctly identified for threadpool offloading
- Security threat model included with STRIDE analysis

### Top Concerns (by severity)

1. **HIGH — SSRF mitigation under-specified**: URL fetch with Playwright fallback needs stronger safety controls: DNS rebinding defense, redirect cap, max response size, Playwright subresource blocking
2. **HIGH — Quality flags not persisted**: Scanned PDF and thin content warnings may be transient SSE-only state; need DB columns to persist these
3. **HIGH — No unique constraint on content_hash**: Service-level dedup check without DB constraint is race-prone
4. **HIGH — Missing source list API**: Frontend SourceList component needs a GET endpoint to list indexed sources — not defined in any plan
5. **MEDIUM — SSE lifecycle gaps**: No cancellation handling, no cleanup on client disconnect, no concurrency limits on docling/Playwright work
6. **MEDIUM — Batch ingest undefined**: How selected search results map to backend endpoints needs explicit definition

### Actionable Items for Replanning
- Add `UNIQUE` constraint on `content_hash` in the migration (Plan 01)
- Persist quality flags (warnings array or dedicated column) in RawSource (Plan 01)
- Add or reference a `GET /api/sources` endpoint for listing indexed sources (Plan 02)
- Strengthen SSRF controls with redirect cap, DNS validation, max response size (Plan 02)
- Add SSE cancellation/cleanup handling in both service and frontend (Plans 02, 03)
- Replace `pytest.skip` with `pytest.mark.xfail` or add a Plan 04 check that no skips remain (Plans 01, 04)
- Define batch ingest policy: serial via `/fetch` per selected URL (Plan 03)
- Add negative test cases to E2E verification (Plan 04)
