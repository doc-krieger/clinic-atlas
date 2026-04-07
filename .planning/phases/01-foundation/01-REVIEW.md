---
phase: 01-foundation
reviewed: 2026-04-07T18:30:00Z
depth: standard
files_reviewed: 37
files_reviewed_list:
  - backend/alembic/env.py
  - backend/alembic.ini
  - backend/alembic/versions/001_initial_schema.py
  - backend/app/config.py
  - backend/app/database.py
  - backend/app/health/router.py
  - backend/app/main.py
  - backend/app/notes/models.py
  - backend/app/notes/service.py
  - backend/app/search/router.py
  - backend/app/search/service.py
  - backend/app/sources/models.py
  - backend/app/sources/registry.py
  - backend/app/sources/router.py
  - backend/Dockerfile
  - backend/pyproject.toml
  - backend/tests/conftest.py
  - backend/tests/test_fts.py
  - backend/tests/test_health.py
  - backend/tests/test_schema.py
  - backend/tests/test_source_registry.py
  - config/medical_thesaurus.ths
  - config/searxng/limiter.toml
  - config/searxng/settings.yml
  - config/sources.yml
  - docker-compose.yml
  - .env
  - frontend/Dockerfile
  - frontend/src/app/chat/page.tsx
  - frontend/src/app/globals.css
  - frontend/src/app/layout.tsx
  - frontend/src/app/page.tsx
  - frontend/src/components/chat/message-input.tsx
  - frontend/src/components/chat/message-list.tsx
  - frontend/src/components/layout/sidebar.tsx
  - frontend/src/components/theme-provider.tsx
  - frontend/src/lib/api.ts
  - frontend/vitest.config.ts
  - scripts/init-postgres.sql
findings:
  critical: 1
  warning: 5
  info: 3
  total: 9
status: issues_found
---

# Phase 1: Code Review Report

**Reviewed:** 2026-04-07T18:30:00Z
**Depth:** standard
**Files Reviewed:** 37
**Status:** issues_found

## Summary

Phase 1 foundation is solid overall. The database schema, FTS pipeline with medical thesaurus, source registry, health checks, and frontend shell are all well-structured. One critical issue exists with double Alembic migration execution. Several warnings relate to error handling edge cases in the reindex service and the sources router re-parsing YAML on every request. Frontend code is clean and appropriately minimal for a scaffold phase.

## Critical Issues

### CR-01: Double Alembic migration execution on startup

**File:** `backend/app/main.py:24-34` and `docker-compose.yml:38`
**Issue:** The `docker-compose.yml` command runs `uv run alembic upgrade head` before starting uvicorn, and then the FastAPI lifespan handler in `main.py` also runs `alembic upgrade head` via `subprocess.run`. This means migrations execute twice on every container start. While Alembic is idempotent for already-applied migrations, the subprocess call spawns a separate Python process that creates its own database connection and Settings instance, which adds latency and unnecessary load. More importantly, if the subprocess migration fails (e.g., transient DB error), the application raises `RuntimeError` and refuses to start -- even though the docker-compose command already succeeded. This creates a confusing failure mode.
**Fix:** Remove one of the two migration invocations. Since docker-compose already runs migrations before `exec uvicorn`, remove the subprocess call from the lifespan:
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Migrations are run by docker-compose command before uvicorn starts.
    # For non-Docker environments, run `alembic upgrade head` manually.

    # D-21: Auto-create directories on startup
    for dir_path in [
        os.path.join(settings.clinic_atlas_notes_dir, "topics"),
        # ...
    ]:
        os.makedirs(dir_path, exist_ok=True)
    # ...
    yield
```
Alternatively, keep only the lifespan migration and simplify the docker-compose command to just `exec uv run uvicorn ...`.

## Warnings

### WR-01: Source registry re-loaded from disk on every request

**File:** `backend/app/sources/router.py:16-17`
**Issue:** `get_registry` is a plain function (not cached), so every `GET /api/sources/registry` request re-reads and re-parses `sources.yml` from disk. While harmless at low traffic, this is wasteful and inconsistent with the lifespan preload in `main.py:50-54` which loads the registry but discards the result.
**Fix:** Cache the registry using `lru_cache` or store it in `app.state` during lifespan:
```python
@lru_cache
def get_registry(sources_file: str = "") -> SourceRegistry:
    if not sources_file:
        sources_file = get_settings().clinic_atlas_sources_file
    return load_source_registry(sources_file)
```
Note: `lru_cache` requires hashable arguments, so pass the path as a string rather than the Settings object.

### WR-02: Fragile `nested` variable check in reindex error handler

**File:** `backend/app/notes/service.py:75-76`
**Issue:** The except block checks `if "nested" in locals()` to decide whether to rollback the savepoint. This is fragile -- if the variable name changes during refactoring, or if the exception occurs after `nested.commit()` (line 72), attempting rollback on an already-committed savepoint will raise a new exception. Additionally, if `session.begin_nested()` itself throws (line 44), `nested` is never assigned, and the `locals()` check correctly skips rollback, but this pattern is error-prone.
**Fix:** Use a try/except inside the loop with explicit savepoint management:
```python
for filename in os.listdir(dir_path):
    if not filename.endswith(".md"):
        continue
    stats["scanned"] += 1
    file_path = os.path.join(dir_path, filename)
    try:
        with session.begin_nested():
            post = frontmatter.load(file_path)
            slug = post.metadata.get("slug", filename[:-3])
            existing = session.exec(
                select(Note).where(Note.slug == slug)
            ).first()
            if existing:
                existing.title = post.metadata.get("title", slug)
                # ... update fields ...
                session.add(existing)
            else:
                note = Note(slug=slug, ...)
                session.add(note)
            session.flush()
        stats["upserted"] += 1
    except Exception as e:
        stats["errors"].append({"file": file_path, "error": str(e)})
        logger.warning("Reindex error for %s: %s", file_path, e)
```
Using `with session.begin_nested()` as a context manager ensures automatic rollback on exception.

### WR-03: `updated_at` onupdate lambda may not trigger via SQLModel

**File:** `backend/app/notes/models.py:36-38` and `backend/app/sources/models.py:22-24`
**Issue:** The `sa_column_kwargs={"onupdate": ...}` is passed alongside `default_factory`, but SQLModel's `Field` with `sa_column_kwargs` can have surprising interactions. More importantly, `onupdate` on the Column only fires for ORM-level `UPDATE` statements that go through SQLAlchemy's unit-of-work. If updates happen via raw SQL (e.g., bulk operations or future search service queries), `updated_at` will not be updated. The migration also does not set a database-level trigger for `updated_at`.
**Fix:** Consider adding a database trigger in the migration for `updated_at`, or document that `updated_at` only updates through ORM operations. For now, this is acceptable for Phase 1 where all writes go through SQLModel, but should be addressed before Phase 2 adds more write paths.

### WR-04: Health endpoint exposes internal paths in response

**File:** `backend/app/health/router.py:74-77`
**Issue:** The disk volume checks include `"path": path` in the JSON response, exposing internal filesystem paths (e.g., `/data/notes`, `/data/sources`) to any caller. While this is a single-user self-hosted app, it is a security hygiene issue that would matter if the app is ever exposed beyond localhost.
**Fix:** Remove the `path` field from the health response, or gate it behind a debug/admin flag:
```python
checks[f"disk_{name}"] = {
    "status": "ok" if os.path.isdir(path) else "error",
}
```

### WR-05: SearXNG secret_key is hardcoded in committed config

**File:** `config/searxng/settings.yml:4`
**Issue:** `secret_key: "clinic-atlas-dev-key-change-in-production"` is hardcoded in the repository. While the comment says "change in production" and this is a dev-only self-hosted tool, the key is still committed to version control. If this repo is open-sourced (stated intent), anyone using it without changing the key gets the same SearXNG secret.
**Fix:** Move the secret key to an environment variable:
```yaml
server:
  secret_key: "${SEARXNG_SECRET_KEY}"
```
Or generate it dynamically in docker-compose. At minimum, document in a setup guide that this must be changed.

## Info

### IN-01: Unused import in main.py

**File:** `backend/app/main.py:4`
**Issue:** `subprocess` is imported and used for the Alembic migration call. If CR-01 is resolved by removing the subprocess migration, this import becomes dead code.
**Fix:** Remove `import subprocess` if the subprocess migration call is removed.

### IN-02: Test file uses hardcoded config path

**File:** `backend/tests/test_source_registry.py:8-9`
**Issue:** `_SOURCES_PATH = _settings.clinic_atlas_sources_file` resolves to `/config/sources.yml` (the Docker path). Tests that run outside Docker (e.g., local `pytest`) will fail if this path does not exist. The test suite depends on the Docker environment being available.
**Fix:** This is acceptable for the stated test strategy (D-47: tests run against real Postgres in Docker), but consider documenting this dependency or providing a fallback for CI environments.

### IN-03: `pyproject.toml` specifies `sqlmodel>=0.0.38` but CLAUDE.md references `0.0.24`

**File:** `backend/pyproject.toml:8`
**Issue:** The pinned version `>=0.0.38` is newer than the `0.0.24` documented in CLAUDE.md. This is not a bug (newer is fine), but the documentation is outdated.
**Fix:** Update CLAUDE.md to reflect the actual pinned version, or note that the constraint allows newer releases.

---

_Reviewed: 2026-04-07T18:30:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
