---
phase: 02-source-ingestion
plan: 01
subsystem: infra, database, api
tags: [docling, playwright, pytorch-cpu, alembic, pydantic, sse]

# Dependency graph
requires:
  - phase: 01-foundation
    provides: RawSource model, Alembic migration 001, Docker Compose stack, pyproject.toml
provides:
  - Docling + Playwright dependencies installed in backend container
  - PyTorch CPU-only index configuration (avoids 9.7GB CUDA wheels)
  - RawSource extended with page_count, source_type, author, quality_flags columns
  - UNIQUE constraint on content_hash for DB-level dedup
  - Pydantic schemas for full ingestion API contract (SSE events, requests, responses)
  - Ingestion settings in config (upload limit, SSRF protection)
  - Test scaffolds with xfail markers for Plan 02 implementation
  - 2-page sample.pdf test fixture
affects: [02-source-ingestion]

# Tech tracking
tech-stack:
  added: [docling>=2.85.0, playwright>=1.52.0]
  patterns: [pytorch-cpu-index, xfail-test-scaffolds, quality-flags-json-column]

key-files:
  created:
    - backend/app/sources/schemas.py
    - backend/alembic/versions/002_add_source_ingestion_columns.py
    - backend/tests/test_ingestion.py
    - backend/tests/test_searxng.py
    - backend/tests/fixtures/sample.pdf
  modified:
    - backend/pyproject.toml
    - backend/Dockerfile
    - docker-compose.yml
    - backend/app/sources/models.py
    - backend/app/config.py
    - backend/uv.lock

key-decisions:
  - "PyTorch CPU-only index via [tool.uv.sources] saves ~8GB per Docker build"
  - "quality_flags as JSON column (not transient SSE state) per review HIGH concern"
  - "content_hash UNIQUE constraint at DB level prevents race-prone service-only dedup"
  - "xfail markers instead of skip for test scaffolds -- shows expected failures in CI"

patterns-established:
  - "JSON column pattern: sa_column=Column(JSON, nullable=False, server_default='[]') for list fields"
  - "xfail test scaffold pattern: mark stubs with pytest.mark.xfail for Plan 04 zero-xfail assertion"

requirements-completed: [SRCI-01, SRCI-03]

# Metrics
duration: 3min
completed: 2026-04-07
---

# Phase 2 Plan 01: Source Ingestion Infrastructure Summary

**Docling + Playwright deps with PyTorch CPU index, RawSource schema extensions (quality_flags, UNIQUE content_hash), Pydantic API contracts, and xfail test scaffolds**

## Performance

- **Duration:** 3 min
- **Started:** 2026-04-07T21:12:56Z
- **Completed:** 2026-04-07T21:16:20Z
- **Tasks:** 2
- **Files modified:** 12

## Accomplishments
- Backend dependencies updated with docling and playwright, PyTorch configured for CPU-only wheels
- RawSource model extended with page_count, source_type, author, quality_flags (JSON), and UNIQUE content_hash
- Full Pydantic schema contract created for ingestion SSE events, requests, and responses
- 9 xfail test stubs scaffolded across ingestion and SearXNG test files

## Task Commits

Each task was committed atomically:

1. **Task 1: Add docling + playwright dependencies, update Dockerfile and Docker Compose** - `29cb05c` (feat)
2. **Task 2: Extend RawSource model, create schemas, scaffold tests** - `586252c` (feat)

## Files Created/Modified
- `backend/pyproject.toml` - Added docling, playwright deps + PyTorch CPU index config
- `backend/Dockerfile` - Playwright system libs, chromium install, appuser cache dir
- `docker-compose.yml` - docling_models named volume for ML model cache
- `backend/app/sources/models.py` - Added page_count, source_type, author, quality_flags; UNIQUE content_hash
- `backend/app/sources/schemas.py` - Pydantic schemas for ingestion API contract
- `backend/app/config.py` - Ingestion settings (upload limit, SSRF protection)
- `backend/alembic/versions/002_add_source_ingestion_columns.py` - Migration for new columns + UNIQUE constraint
- `backend/tests/test_ingestion.py` - xfail stubs for PDF upload, URL fetch, source list
- `backend/tests/test_searxng.py` - xfail stubs for SearXNG search
- `backend/tests/fixtures/sample.pdf` - 2-page text PDF fixture
- `backend/uv.lock` - Regenerated with new dependency tree

## Decisions Made
- PyTorch CPU-only index via `[tool.uv.sources]` saves ~8GB per Docker build -- docling pulls torch as transitive dep
- quality_flags stored as JSON column (not transient SSE-only state) per review HIGH concern
- content_hash gets DB-level UNIQUE constraint (not just service-layer check) to prevent race conditions
- Used xfail markers instead of skip for test scaffolds so Plan 04 can assert zero xfails remain

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Infrastructure ready for Plan 02 (service layer implementation)
- All xfail tests awaiting service implementation
- Migration 002 applied to development database
- Schemas define the full API contract that Plan 02 endpoints will implement

---
*Phase: 02-source-ingestion*
*Completed: 2026-04-07*

## Self-Check: PASSED

All 8 key files verified present. Both task commits (29cb05c, 586252c) confirmed in git log.
