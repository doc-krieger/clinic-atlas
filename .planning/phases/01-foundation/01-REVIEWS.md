---
phase: 1
reviewers: [codex]
reviewed_at: 2026-04-07T00:00:00Z
plans_reviewed: [01-01-PLAN.md, 01-02-PLAN.md, 01-03-PLAN.md]
---

# Cross-AI Plan Review — Phase 1

> Adversarial review of Phase 1 (Foundation) plans by external AI systems.
> Use with `/gsd-plan-phase 1 --reviews` to incorporate feedback.

---

## Codex Review

**Model:** gpt-5.4 via OpenAI Codex CLI v0.118.0

### Overall Summary

The plans are broadly aligned with Phase 1 and cover the main deliverables, but the highest risk is operational: `docker compose up` must not merely start containers, it must leave Postgres migrated, the custom `medical` FTS configuration available, disk directories created, and the API able to use them. The backend/database plans need tighter init and migration sequencing before I'd call this low-risk.

### Plan 01-01: Docker Compose + Postgres FTS + Alembic

**Strengths**
- Covers the core stack and schema work required for Phase 1.
- Uses Alembic from day one, which is the right call for schema evolution.
- Weighted `tsvector` for notes is appropriate for title/content ranking.
- Real Postgres FTS with GIN indexes fits the "no vector DB" constraint.
- Explicit thesaurus config directly targets the `HTN` → `hypertension` success criterion.

**Concerns**
- **HIGH:** `docker-entrypoint-initdb.d` only runs on first Postgres volume initialization. If the thesaurus or text search config changes later, existing dev volumes may not update.
- **HIGH:** If the custom `medical` text search configuration is only in `init-postgres.sql`, tests, fresh non-Docker databases, and future deployments can drift from Alembic migrations.
- **HIGH:** The plan does not explicitly say how migrations run during `docker compose up`. Without an app entrypoint or one-shot migration service, the schema may not exist after startup.
- **MEDIUM:** A 500+ entry thesaurus in Phase 1 is high-risk content work. Bad expansions or ambiguous abbreviations can reduce precision significantly.
- **MEDIUM:** Generated `tsvector` columns using a custom dictionary need an integration test proving insert/update/search behavior works with the exact Postgres image.
- **MEDIUM:** Python 3.13 may increase dependency compatibility risk unless versions are pinned and locked.

**Suggestions**
- Put text search dictionary/config creation in Alembic as well as any Docker bootstrap needed for the `.ths` file.
- Add a deterministic migration path: app startup runs `alembic upgrade head`, or Compose includes a migration service that the API depends on.
- Add a smoke test that starts a clean Postgres volume, applies migrations, inserts "hypertension", and verifies `plainto_tsquery('medical', 'HTN')` matches.
- Start with a tested core thesaurus subset if needed, then expand to 500+ entries once the FTS mechanism is proven.
- Document how to refresh existing dev volumes when thesaurus files change.

**Risk Assessment:** MEDIUM-HIGH

---

### Plan 01-02: Source Registry + Search/Health/Reindex + Tests

**Strengths**
- Directly maps to success criteria for source registry loading, search, health, and reindex.
- Pydantic validation with "warn and keep valid entries" is pragmatic for YAML registry data.
- Real Postgres tests are the right choice for FTS behavior.
- Separating source registry, search, notes, and health modules keeps the backend maintainable.
- Health checks for Postgres, Ollama, SearXNG, and disk volumes are appropriate for local self-hosting.

**Concerns**
- **HIGH:** Search depends on the `medical` FTS config from Plan 01-01; if that config is not migration-owned, this plan can pass in one environment and fail in another.
- **HIGH:** The plan says reindex reads `topics/`, `sources/`, and `logs/` and upserts by slug, but it is unclear how compiled notes versus raw sources map into `notes` and `raw_sources`.
- **MEDIUM:** `POST /api/reindex` is a mutating endpoint. Even for single-user local use, it should not be accidentally exposed on a LAN without some boundary.
- **MEDIUM:** Health probes need short timeouts and degraded status responses, otherwise Ollama or SearXNG startup lag can make the API appear broken.
- **MEDIUM:** The test count sounds light for the critical path. It should include at least one full migration/search/reindex integration test.
- **LOW:** The source registry includes commercial/proprietary sources like UpToDate and DynaMed; registry metadata is fine, but crawler/fetch behavior should not imply unrestricted access.

**Suggestions**
- Add explicit tests for `HTN` matching content containing "hypertension", including the generated `tsvector` column path.
- Make reindex behavior type-aware: compiled notes go to `notes`, raw source documents go to `raw_sources`, and citations populate `note_sources` only when metadata exists.
- Ensure disk directories are created on backend startup and covered by a test.
- Add request timeouts and structured per-service health results instead of a single all-or-nothing health response.
- Restrict CORS and bind defaults to localhost for dev; consider a simple local admin token for reindex if the API may bind to `0.0.0.0`.

**Risk Assessment:** MEDIUM

---

### Plan 01-03: Next.js 15 Frontend Skeleton

**Strengths**
- Scope is appropriately limited to skeleton UI and infrastructure.
- Direct FastAPI connection matches the stated architecture and avoids unnecessary proxy complexity.
- Chat layout, dark default, health indicator, and disabled input are good Phase 1 UX targets.
- Accessibility details like semantic layout, focus indicators, and reduced-motion support are valuable early.
- Vitest setup prepares the frontend for later validation without overbuilding features.

**Concerns**
- **MEDIUM:** Health polling depends on an endpoint from Plan 01-02, while this plan is Wave 1. It should handle 404/network failure cleanly until backend endpoints exist.
- **MEDIUM:** Direct browser-to-FastAPI calls require backend CORS configuration, which is not explicitly assigned to any plan.
- **MEDIUM:** `NEXT_PUBLIC_API_URL` must use the browser-reachable host URL, not the Docker service name. This often breaks in Compose setups.
- **LOW:** `next/font/google` for Inter can introduce build-time network dependency. That may conflict with local-first expectations if offline startup matters.
- **LOW:** shadcn/ui plus Tailwind v4 setup should be pinned and scripted to avoid CLI drift.

**Suggestions**
- Define `NEXT_PUBLIC_API_URL=http://localhost:8000` for browser access and separately use internal service URLs only for server-to-server calls.
- Add backend CORS settings in Plan 01-02 or Plan 01-01, restricted to the frontend origin.
- Make the health indicator tolerate missing endpoints and display "backend unavailable" without throwing.
- Consider a system font stack or checked-in local font if offline Docker builds are a goal.
- Add one minimal render test for `/chat` and one API-client error-handling test.

**Risk Assessment:** LOW-MEDIUM

---

## Consensus Summary

> Single reviewer (Codex/gpt-5.4). Consensus analysis requires 2+ reviewers.

### Key Concerns (Priority Order)

1. **Migration sequencing** (HIGH) — No explicit mechanism for running Alembic migrations during `docker compose up`. The plan creates migration files but doesn't wire them into the startup flow.
2. **FTS config ownership** (HIGH) — The `medical` text search configuration lives only in `docker-entrypoint-initdb.d`, which only runs on first volume init. Should also be in Alembic for reproducibility.
3. **Reindex semantics** (HIGH) — Reindex reads disk files into the `notes` table but the mapping between disk directories and database tables (notes vs raw_sources) is ambiguous.
4. **CORS not assigned** (MEDIUM) — Direct browser-to-FastAPI requires CORS, but no plan explicitly owns this configuration.
5. **Thesaurus volume refresh** (MEDIUM) — No documented way to update the thesaurus on existing dev volumes.
6. **Test coverage** (MEDIUM) — 11 tests is light for the critical path; needs at least one full migration → insert → FTS search integration test.

### Strengths Confirmed

- Architecture is sound for the constraints (single user, local-first, FTS over vector DB)
- Alembic from day one is the right call
- Real Postgres tests (no SQLite/mocks) catches FTS issues early
- Frontend scope is appropriately limited to skeleton
- Source registry with validate-and-warn is pragmatic

### Priority Fixes Before Execution

1. Add `alembic upgrade head` to backend startup (entrypoint or lifespan)
2. Put FTS config creation in Alembic migration (not just Docker init SQL)
3. Clarify reindex: disk notes → `notes` table only; raw sources handled separately
4. Add CORS middleware to FastAPI (Plan 01-01 or 01-02)
5. Add HTN → hypertension smoke test as explicit test case
