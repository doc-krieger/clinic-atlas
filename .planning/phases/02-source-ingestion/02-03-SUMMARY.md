---
phase: 02-source-ingestion
plan: 03
subsystem: frontend
tags: [sources-ui, sse-client, shadcn, drag-drop, search, batch-ingestion]

# Dependency graph
requires:
  - phase: 02-source-ingestion
    plan: 01
    provides: RawSource schema with quality_flags, Pydantic API contract
provides:
  - /sources page route with three-tab ingestion interface
  - SSE client utility with POST support, AbortSignal cancellation, frame parsing
  - PDF upload with drag-and-drop, file picker, size validation
  - URL fetch with input validation, SSE progress, quality warnings
  - SearXNG search with multi-select and serial batch ingestion
  - Source list fetched from GET /api/sources with status badges
  - Sidebar navigation with active state highlighting
affects: [02-source-ingestion]

# Tech tracking
tech-stack:
  added: [shadcn-tabs, shadcn-badge, shadcn-progress, shadcn-alert, shadcn-dialog, shadcn-checkbox, shadcn-skeleton]
  patterns: [post-sse-via-fetch-readablestream, abort-controller-cancellation, refresh-key-pattern]

key-files:
  created:
    - frontend/src/lib/sse.ts
    - frontend/src/app/sources/page.tsx
    - frontend/src/components/sources/source-tabs.tsx
    - frontend/src/components/sources/pdf-upload-tab.tsx
    - frontend/src/components/sources/url-fetch-tab.tsx
    - frontend/src/components/sources/search-tab.tsx
    - frontend/src/components/sources/search-result-item.tsx
    - frontend/src/components/sources/ingestion-progress.tsx
    - frontend/src/components/sources/quality-warning.tsx
    - frontend/src/components/sources/source-list.tsx
    - frontend/src/components/sources/source-list-item.tsx
    - frontend/src/components/ui/tabs.tsx
    - frontend/src/components/ui/badge.tsx
    - frontend/src/components/ui/progress.tsx
    - frontend/src/components/ui/alert.tsx
    - frontend/src/components/ui/dialog.tsx
    - frontend/src/components/ui/checkbox.tsx
    - frontend/src/components/ui/skeleton.tsx
  modified:
    - frontend/src/components/layout/sidebar.tsx

key-decisions:
  - "Manual fetch+ReadableStream SSE client instead of @microsoft/fetch-event-source -- zero deps, ~100 lines"
  - "refreshKey counter pattern for SourceList refetch after ingestion -- simple, no external state management"
  - "Serial batch ingestion via sequential await postSSE per URL -- avoids multiple concurrent SSE streams"

requirements-completed: [SRCI-01, SRCI-02, SRCI-03, SRCI-05]

# Metrics
duration: 4min
completed: 2026-04-07
---

# Phase 2 Plan 03: Frontend Sources Page Summary

**Complete source ingestion UI with POST SSE client, three-tab interface (Upload PDF / Fetch URL / Search Sources), quality gate warnings, and serial batch ingestion**

## Performance

- **Duration:** 4 min
- **Started:** 2026-04-07T21:18:57Z
- **Completed:** 2026-04-07T21:22:57Z
- **Tasks:** 3
- **Files created:** 19

## Accomplishments

- SSE client utility using fetch + ReadableStream with AbortSignal cancellation, double-newline frame splitting, and reader cleanup
- Sidebar updated with Chat and Sources navigation links with active state highlighting via usePathname
- Sources page at /sources with three-tab layout (Upload PDF, Fetch URL, Search Sources) and source list below
- PDF upload tab with drag-and-drop zone, file picker, 50 MB client-side validation, SSE progress, scanned PDF warning, duplicate detection
- URL fetch tab with URL validation on blur, SSE progress streaming, thin content and fetch failure warnings
- Search tab querying SearXNG via POST /api/sources/search with multi-select checkboxes and serial batch ingestion
- Ingestion progress component mapping status to percentage with status text per UI-SPEC Copywriting Contract
- Quality warning component for scanned PDFs and thin content using shadcn Alert
- Source list fetched from GET /api/sources with loading skeletons, empty state, type badges, status badges, and relative timestamps
- 7 new shadcn UI components installed: tabs, badge, progress, alert, dialog, checkbox, skeleton

## Task Commits

1. **Task 1: Install shadcn components, create SSE utility, update sidebar** - `9522666` (feat)
2. **Task 2: Build sources page, PDF upload, URL fetch, and shared components** - `d37d549` (feat)
3. **Task 3: Build search tab with result selection and serial batch ingestion** - `1d6cf84` (feat)

## Decisions Made

- Used manual fetch+ReadableStream for POST SSE instead of @microsoft/fetch-event-source -- avoids dependency, ~100 lines of code
- refreshKey counter pattern triggers SourceList refetch after any successful ingestion -- simpler than react-query for this use case
- Serial batch ingestion processes each selected search result URL sequentially via await postSSE -- prevents concurrent SSE stream issues per review MEDIUM concern

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - frontend-only changes, no external service configuration.

## Next Phase Readiness

- All frontend components ready for integration with backend API endpoints (Plan 02)
- SSE client utility ready for real-time progress streaming
- Source list connected to GET /api/sources endpoint
- Plan 04 verification can test full-stack integration

---
*Phase: 02-source-ingestion*
*Completed: 2026-04-07*

## Self-Check: PASSED

All 17 key files verified present. All 3 task commits (9522666, d37d549, 1d6cf84) confirmed in git log.
