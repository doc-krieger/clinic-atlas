---
phase: 01-foundation
plan: 02
subsystem: api
tags: [fastapi, fts, tsvector, pydantic, yaml, pytest, medical-thesaurus]

requires:
  - phase: 01-foundation-plan-01
    provides: "Database schema with notes, raw_sources, note_sources tables; tsvector columns; GIN indexes; medical thesaurus config; Alembic migrations"
provides:
  - "Source registry loader with Pydantic validation from config/sources.yml"
  - "FTS search endpoint using medical thesaurus configuration (plainto_tsquery)"
  - "Health endpoint with per-service 3s timeouts and degraded status"
  - "Reindex endpoint to rebuild notes table from disk markdown files"
  - "23-test backend test suite covering schema, FTS, source registry, and endpoints"
  - "Pre-populated Canadian clinical source registry (17 sources)"
affects: [02-source-ingestion, 03-research-agent, 04-knowledge-pipeline]

tech-stack:
  added: [python-frontmatter, pyyaml, httpx]
  patterns: [yaml-source-registry, medical-fts-query, health-probe-timeout, reindex-from-disk]

key-files:
  created:
    - backend/app/sources/registry.py
    - backend/app/sources/router.py
    - backend/app/search/service.py
    - backend/app/search/router.py
    - backend/app/notes/service.py
    - backend/app/health/router.py
    - config/sources.yml
    - backend/tests/conftest.py
    - backend/tests/test_schema.py
    - backend/tests/test_fts.py
    - backend/tests/test_source_registry.py
    - backend/tests/test_health.py
  modified:
    - backend/app/main.py

key-decisions:
  - "Reindex rebuilds notes table only from disk .md files; raw_sources populated by ingestion pipeline in Phase 2"
  - "Health endpoint uses 3s timeouts for Ollama/SearXNG probes, reports unavailable instead of error for optional services"
  - "Source registry uses warn-and-skip pattern for invalid entries (D-29)"
  - "Tests use real Postgres with transaction rollback for isolation"

patterns-established:
  - "FTS query pattern: plainto_tsquery('medical', :q) with ts_rank for ranking"
  - "Source registry: YAML -> Pydantic validation with category-based organization"
  - "Health probes: per-service timeouts with ok/degraded/unavailable/error status model"
  - "Test isolation: real Postgres connection with transaction rollback per test"

requirements-completed: [SRCI-04, KBSE-01, KBSE-02]

duration: 3min
completed: 2026-04-07
---

# Phase 1 Plan 2: API Endpoints and Test Suite Summary

**Source registry, FTS search with medical thesaurus (HTN->hypertension), health/reindex endpoints, and 23-test backend suite against real Postgres**

## Performance

- **Duration:** 3 min
- **Started:** 2026-04-07T07:48:23Z
- **Completed:** 2026-04-07T07:51:21Z
- **Tasks:** 2
- **Files modified:** 16

## Accomplishments
- Source registry loads 17 Canadian clinical sources from config/sources.yml with Pydantic validation and warn-on-error behavior
- FTS search endpoint uses medical thesaurus configuration for synonym expansion (HTN->hypertension, anaemia->anemia)
- Health endpoint checks Postgres, Ollama, SearXNG, and disk volumes with 3s probe timeouts
- Reindex endpoint rebuilds notes table from disk markdown files (raw_sources handled separately)
- 23 pytest tests covering schema integrity, FTS thesaurus, source registry, and all API endpoints

## Task Commits

Each task was committed atomically:

1. **Task 1: Source registry, search service, health and reindex endpoints** - `cb0d403` (feat)
2. **Task 2: Backend test suite** - `43b3f6c` (test)

## Files Created/Modified
- `backend/app/sources/registry.py` - YAML source registry loader with Pydantic validation and ReliabilityTier enum
- `backend/app/sources/router.py` - GET /api/sources/registry endpoint
- `backend/app/search/service.py` - FTS query logic using medical thesaurus config with plainto_tsquery
- `backend/app/search/router.py` - GET /api/search endpoint with query validation
- `backend/app/notes/service.py` - Reindex logic mapping disk markdown files to notes table
- `backend/app/health/router.py` - Health endpoint with per-service probes and reindex endpoint
- `backend/app/health/__init__.py` - Package init
- `backend/app/search/__init__.py` - Package init
- `backend/app/main.py` - Added router includes and source registry startup loading
- `config/sources.yml` - 17 Canadian clinical sources across 4 categories
- `backend/tests/conftest.py` - Test fixtures with real Postgres and transaction rollback
- `backend/tests/test_schema.py` - 6 schema integrity tests
- `backend/tests/test_fts.py` - 6 FTS tests including HTN smoke test
- `backend/tests/test_source_registry.py` - 5 source registry validation tests
- `backend/tests/test_health.py` - 6 endpoint tests (health, reindex, search, sources)
- `backend/tests/__init__.py` - Package init

## Decisions Made
- Reindex rebuilds notes table only from disk .md files; raw_sources populated by ingestion pipeline in Phase 2
- Health endpoint uses 3s timeouts for Ollama/SearXNG probes, reports "unavailable" instead of "error" for optional services
- Source registry uses warn-and-skip pattern for invalid entries (D-29)
- Tests use real Postgres with transaction rollback for isolation (no SQLite substitution per D-47)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- All API endpoints ready for frontend integration
- Source registry ready for web search agent (Phase 3)
- FTS search with medical thesaurus verified working
- Test infrastructure established for future test additions

## Self-Check: PASSED

All 16 files verified present. Both task commits (cb0d403, 43b3f6c) verified in git log.

---
*Phase: 01-foundation*
*Completed: 2026-04-07*
