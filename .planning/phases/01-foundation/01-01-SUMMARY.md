---
phase: 01-foundation
plan: 01
subsystem: infra
tags: [docker-compose, postgres, fts, thesaurus, alembic, sqlmodel, fastapi, searxng, ollama]

# Dependency graph
requires: []
provides:
  - "5-service Docker Compose stack (Postgres 17, FastAPI, Next.js, Ollama, SearXNG)"
  - "Postgres schema with FTS-enabled notes, raw_sources, note_sources, research_sessions tables"
  - "Medical thesaurus dictionary with 500+ clinical abbreviations for Postgres FTS"
  - "Alembic migration infrastructure with auto-migrate on startup"
  - "FastAPI skeleton with CORS, health endpoint, directory auto-creation"
  - "SQLModel models for all domain entities"
affects: [01-02, 01-03, 02-knowledge-base, 03-search, 04-research-agent]

# Tech tracking
tech-stack:
  added: [fastapi, sqlmodel, alembic, pydantic-settings, litellm, psycopg2-binary, httpx, python-frontmatter, pyyaml, ruff, pytest]
  patterns: [idempotent-fts-creation, generated-always-as-tsvector, gin-index, alembic-auto-migrate-on-startup, pydantic-settings-env-config]

key-files:
  created:
    - docker-compose.yml
    - .env
    - config/medical_thesaurus.ths
    - config/searxng/settings.yml
    - config/searxng/limiter.toml
    - scripts/init-postgres.sql
    - backend/Dockerfile
    - frontend/Dockerfile
    - backend/pyproject.toml
    - backend/alembic.ini
    - backend/alembic/env.py
    - backend/alembic/versions/001_initial_schema.py
    - backend/app/main.py
    - backend/app/config.py
    - backend/app/database.py
    - backend/app/notes/models.py
    - backend/app/sources/models.py
  modified: []

key-decisions:
  - "Idempotent FTS config in both Docker init SQL and Alembic migration for dual-environment support"
  - "search_vector as GENERATED ALWAYS AS column, not modeled in SQLModel (raw SQL in migration)"
  - "CORS allow_origins restricted to localhost:3000 only"
  - "NEXT_PUBLIC_API_URL uses browser-reachable localhost:8000, not Docker service name"

patterns-established:
  - "Idempotent FTS creation: DO $$ IF NOT EXISTS pattern for text search dictionaries and configurations"
  - "tsvector via raw SQL in Alembic: GENERATED ALWAYS AS columns added via op.execute(), not modeled in SQLModel"
  - "Auto-migration on startup: subprocess.run alembic upgrade head in FastAPI lifespan"
  - "Pydantic Settings for all config: env vars with sensible defaults, .env file support"

requirements-completed: [KBSE-01, KBSE-02]

# Metrics
duration: 4min
completed: 2026-04-07
---

# Phase 1 Plan 01: Docker Compose Stack and Postgres Schema Summary

**5-service Docker Compose stack with Postgres 17, medical thesaurus FTS (500+ abbreviations), Alembic-managed schema with tsvector GENERATED ALWAYS AS columns, and FastAPI skeleton with auto-migration**

## Performance

- **Duration:** 4 min
- **Started:** 2026-04-07T07:40:57Z
- **Completed:** 2026-04-07T07:44:46Z
- **Tasks:** 2
- **Files modified:** 23

## Accomplishments
- Docker Compose orchestrating 5 services with healthchecks and dependency ordering
- Postgres schema with 4 tables (notes, raw_sources, note_sources, research_sessions) with weighted tsvector FTS and GIN indexes using custom medical thesaurus dictionary
- Medical thesaurus with 500+ clinical abbreviation entries covering cardiovascular, respiratory, neuro, GI, endocrine, infectious disease, hematology, pharmacology, OB/GYN, pediatrics, psychiatry, surgery, labs, imaging, and Canadian/British spelling variants
- FastAPI app with CORS middleware, automatic Alembic migration on startup, directory auto-creation, and health endpoint

## Task Commits

Each task was committed atomically:

1. **Task 1: Docker Compose stack with Postgres thesaurus and SearXNG** - `a3fe416` (feat)
2. **Task 2: Backend scaffolding with Alembic migration, auto-migrate on startup, and SQLModel models** - `a8e929a` (feat)

## Files Created/Modified
- `docker-compose.yml` - 5-service orchestration with healthchecks and depends_on
- `.env` - Default environment variables for local development
- `config/medical_thesaurus.ths` - 500+ medical abbreviation thesaurus for Postgres FTS
- `config/searxng/settings.yml` - SearXNG with JSON API enabled
- `config/searxng/limiter.toml` - Rate limiter disabled for local dev
- `scripts/init-postgres.sql` - Idempotent FTS dictionary and configuration creation
- `backend/Dockerfile` - Python 3.13-slim with uv package manager
- `frontend/Dockerfile` - Node 22-slim with pnpm
- `backend/pyproject.toml` - Dependencies with litellm>=1.83.0, sqlmodel>=0.0.38
- `backend/alembic.ini` - Alembic configuration
- `backend/alembic/env.py` - Alembic env with SQLModel metadata and Settings integration
- `backend/alembic/script.py.mako` - Alembic migration template
- `backend/alembic/versions/001_initial_schema.py` - Initial schema with FTS, tsvector, GIN indexes
- `backend/app/main.py` - FastAPI app with CORS, auto-migration, directory creation, health endpoint
- `backend/app/config.py` - Pydantic Settings with env var configuration
- `backend/app/database.py` - SQLModel engine and session factory
- `backend/app/notes/models.py` - Note, NoteSource SQLModel models
- `backend/app/sources/models.py` - RawSource SQLModel model

## Decisions Made
- Idempotent FTS config creation in both Docker init SQL and Alembic migration ensures the medical thesaurus works in both Docker and non-Docker environments (e.g., test environments)
- search_vector columns are GENERATED ALWAYS AS via raw SQL in the Alembic migration, not modeled as SQLModel Fields (per Pitfall 3 from research)
- CORS restricted to localhost:3000 only (not wildcard)
- Backend healthcheck start_period set to 30s to allow Alembic migration time

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Known Stubs
None - all data models and infrastructure are fully wired.

## Next Phase Readiness
- Docker Compose stack ready for `docker compose up`
- Postgres schema and FTS infrastructure complete for Plans 02 and 03
- FastAPI skeleton ready for API endpoint development
- Frontend Dockerfile ready for Next.js scaffolding in Plan 03

## Self-Check: PASSED

All 17 created files verified present. Both task commits (a3fe416, a8e929a) verified in git log.

---
*Phase: 01-foundation*
*Completed: 2026-04-07*
