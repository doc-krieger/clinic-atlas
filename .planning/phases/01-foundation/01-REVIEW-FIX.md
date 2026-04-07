---
phase: 01-foundation
fixed_at: 2026-04-07T18:45:00Z
review_path: .planning/phases/01-foundation/01-REVIEW.md
iteration: 1
findings_in_scope: 6
fixed: 5
skipped: 1
status: partial
---

# Phase 1: Code Review Fix Report

**Fixed at:** 2026-04-07T18:45:00Z
**Source review:** .planning/phases/01-foundation/01-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 6
- Fixed: 5
- Skipped: 1

## Fixed Issues

### CR-01: Double Alembic migration execution on startup

**Files modified:** `backend/app/main.py`
**Commit:** 9de82e7
**Applied fix:** Removed the subprocess-based Alembic migration call from the FastAPI lifespan handler. docker-compose already runs `alembic upgrade head` before starting uvicorn, making the lifespan call redundant. Also removed the now-unused `import subprocess`.

### WR-01: Source registry re-loaded from disk on every request

**Files modified:** `backend/app/sources/router.py`
**Commit:** 2f8c4da
**Applied fix:** Added a `@lru_cache`-decorated `_load_registry()` helper that caches the parsed `SourceRegistry` by file path string. The `get_registry` dependency now delegates to this cached function, avoiding disk re-reads on every request.

### WR-02: Fragile `nested` variable check in reindex error handler

**Files modified:** `backend/app/notes/service.py`
**Commit:** bffaa52
**Applied fix:** Replaced manual `session.begin_nested()` + `nested.commit()` + fragile `if "nested" in locals()` rollback with `with session.begin_nested():` context manager. The context manager handles automatic rollback on exception and commit on success, eliminating the error-prone variable check.

### WR-03: `updated_at` onupdate lambda may not trigger via SQLModel

**Files modified:** `backend/app/notes/models.py`, `backend/app/sources/models.py`
**Commit:** de966cc
**Applied fix:** Added documentation comments to both model files clarifying that `onupdate` only fires for ORM-level updates (SQLAlchemy unit-of-work) and that a database trigger should be added if non-ORM write paths are introduced. Acceptable for Phase 1 where all writes go through SQLModel.

### WR-04: Health endpoint exposes internal paths in response

**Files modified:** `backend/app/health/router.py`
**Commit:** 5959e3c
**Applied fix:** Removed the `"path": path` field from the disk volume health check response, eliminating exposure of internal filesystem paths (e.g., `/data/notes`, `/data/sources`) in the API response.

## Skipped Issues

### WR-05: SearXNG secret_key is hardcoded in committed config

**File:** `config/searxng/settings.yml:4`
**Reason:** File is owned by UID 977 (SearXNG container user) and cannot be modified without sudo. The file permissions prevent editing outside the container context.
**Original issue:** `secret_key: "clinic-atlas-dev-key-change-in-production"` is hardcoded in the repository. Should be overridden via `SEARXNG_SECRET` environment variable in production.

---

_Fixed: 2026-04-07T18:45:00Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
