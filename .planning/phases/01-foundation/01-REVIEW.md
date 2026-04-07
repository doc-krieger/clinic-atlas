---
phase: 01-foundation
reviewed: 2026-04-07T12:00:00Z
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
  warning: 6
  info: 3
  total: 10
status: issues_found
---

# Phase 1: Code Review Report

**Reviewed:** 2026-04-07T12:00:00Z
**Depth:** standard
**Files Reviewed:** 37
**Status:** issues_found

## Summary

The Phase 1 foundation codebase is well-structured overall. The backend follows clear module boundaries (health, notes, search, sources), the Alembic migration correctly sets up FTS with a medical thesaurus, and the frontend shell is minimal and clean. Docker Compose wiring is consistent with the architecture plan.

Key concerns: one hardcoded secret in SearXNG config, deprecated `datetime.utcnow` usage across all models, missing `updated_at` auto-update logic, and a partial-commit risk in the reindex service. The thesaurus file has duplicate abbreviation keys that will cause unpredictable PostgreSQL behavior.

## Critical Issues

### CR-01: Hardcoded SearXNG Secret Key

**File:** `config/searxng/settings.yml:4`
**Issue:** The SearXNG `secret_key` is hardcoded as `"clinic-atlas-dev-key-change-in-production"`. While the comment-in-name suggests changing it, this value is committed to git. If this config is ever used in a non-local context, the secret is exposed. SearXNG uses this key for CSRF protection and session signing.
**Fix:**
```yaml
server:
  secret_key: "${SEARXNG_SECRET_KEY}"
  bind_address: "0.0.0.0"
  port: 8080
```
Then set `SEARXNG_SECRET_KEY` as an environment variable in `docker-compose.yml` under the searxng service, defaulting to a dev value:
```yaml
environment:
  SEARXNG_SECRET_KEY: ${SEARXNG_SECRET_KEY:-$(openssl rand -hex 32)}
```
Alternatively, generate the key at container startup via an entrypoint script. At minimum, add a comment in `.env` reminding to override this for any non-local deployment.

## Warnings

### WR-01: Deprecated `datetime.utcnow` Usage

**File:** `backend/app/notes/models.py:34-35`
**File:** `backend/app/sources/models.py:19-20`
**Issue:** `datetime.utcnow` is deprecated since Python 3.12 (the project requires Python 3.13). It returns a naive datetime without timezone info, which can cause subtle bugs when comparing with timezone-aware datetimes. Python 3.12+ emits a `DeprecationWarning` and it will be removed in a future version.
**Fix:**
```python
from datetime import datetime, timezone

# In Note model:
created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
```
Apply the same change to `RawSource` in `backend/app/sources/models.py:19-20`.

### WR-02: `reindex_from_disk` Commits Partial Results on Error

**File:** `backend/app/notes/service.py:74`
**Issue:** The `session.commit()` at line 74 runs unconditionally after the loop, even if some files raised exceptions. This means partial results are committed to the database alongside error records in the stats dict. If a file parse error corrupts the session state (e.g., an integrity error from a duplicate slug), the commit will fail entirely and no notes get indexed -- but the error is not caught at this level.
**Fix:** Wrap individual upserts in savepoints so one bad file does not block others:
```python
for filename in os.listdir(dir_path):
    if not filename.endswith(".md"):
        continue
    stats["scanned"] += 1
    file_path = os.path.join(dir_path, filename)
    try:
        nested = session.begin_nested()  # SAVEPOINT
        post = frontmatter.load(file_path)
        # ... upsert logic ...
        nested.commit()
        stats["upserted"] += 1
    except Exception as e:
        nested.rollback()
        stats["errors"].append({"file": file_path, "error": str(e)})
        logger.warning("Reindex error for %s: %s", file_path, e)
session.commit()
```

### WR-03: `updated_at` Column Never Auto-Updates

**File:** `backend/alembic/versions/001_initial_schema.py:78-82`
**File:** `backend/app/notes/models.py:35`
**Issue:** The `updated_at` column has `server_default=sa.func.now()` which only applies on INSERT. There is no database trigger and no application-level logic to update this column when a row is modified. The `default_factory=datetime.utcnow` in the SQLModel only applies when creating new Python objects, not on database UPDATE. This means `updated_at` will always equal `created_at`.
**Fix:** Either add a database trigger in the migration:
```sql
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tr_notes_updated_at BEFORE UPDATE ON notes
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER tr_raw_sources_updated_at BEFORE UPDATE ON raw_sources
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```
Or set `updated_at` explicitly in the reindex service and any future update paths:
```python
existing.updated_at = datetime.now(timezone.utc)
```

### WR-04: Duplicate Abbreviation Keys in Medical Thesaurus

**File:** `config/medical_thesaurus.ths`
**Issue:** Several abbreviations appear multiple times with different expansions. PostgreSQL thesaurus dictionaries use the last definition when duplicates exist, so earlier definitions are silently overridden. Affected keys include:
- `tb` (line 82 "tuberculosis", line 239 "tuberculosis") -- same expansion, harmless but redundant
- `sbp` (line 22 "systolic blood pressure", line 182 "spontaneous bacterial peritonitis") -- only one will apply
- `pe` (line 15 "pulmonary embolism", line 669 "pulmonary embolism physical examination") -- different expansions
- `gcs` (line 123, line 342) -- duplicate
- `sz` (line 125 "seizure", line 477 "schizophrenia") -- only one will apply
- `bpd` (line 100, line 440) -- "bronchopulmonary dysplasia" vs same
- `dvt` (line 14, line 511) -- duplicate
- `ngt` (line 165, line 515) -- duplicate
- `ct` (line 141, line 517 "chest tube", line 584 "computed tomography") -- conflicting meanings
- `cbc`, `crp`, `esr` (duplicated between Infectious Disease and Labs sections)

**Fix:** Consolidate duplicate entries. For genuinely ambiguous abbreviations, use a single entry with all expansions (like the "Ambiguous Abbreviations" section already does for `ms`, `as`, etc.):
```
sbp : systolic blood pressure spontaneous bacterial peritonitis
sz : seizure schizophrenia
ct : computed tomography chest tube
```

### WR-05: Source Registry Re-Loaded From Disk on Every Request

**File:** `backend/app/sources/router.py:10-12`
**Issue:** `GET /api/sources/registry` calls `load_source_registry()` on every request, which reads and parses the YAML file from disk each time. The registry is also loaded at startup in `main.py:50` but that result is discarded (not stored anywhere accessible). This creates unnecessary I/O and means the startup validation is wasted.
**Fix:** Cache the registry at startup and serve from memory:
```python
# In main.py lifespan:
app.state.source_registry = load_source_registry(settings.clinic_atlas_sources_file)

# In sources/router.py:
from fastapi import Request

@router.get("/registry")
def get_registry(request: Request):
    registry = request.app.state.source_registry
    return {
        "sources": [s.model_dump() for s in registry.all_sources],
        "count": len(registry.all_sources),
    }
```

### WR-06: Health Endpoint Overall Status Logic Has Incorrect Check

**File:** `backend/app/health/router.py:76-78`
**Issue:** The condition `checks[k].get("status") in ("ok", None)` on line 77-78 checks whether any non-postgres check status is `None`, but the status is always set to a string value ("ok", "degraded", "error", "unavailable") in every code path above. The `None` case is dead logic that obscures the intent. More importantly, "unavailable" is not in the set `("ok", None)`, so any unavailable optional service (ollama, searxng) correctly triggers "degraded". However, a missing `disk_notes` or `disk_sources` directory (status="error") also only triggers "degraded" -- disk errors should arguably be "error" since notes storage is critical to the application.
**Fix:** Remove the dead `None` check and separate critical vs optional services:
```python
postgres_ok = checks.get("postgres", {}).get("status") == "ok"
disk_ok = all(
    checks[k].get("status") == "ok"
    for k in checks if k.startswith("disk_")
)
if not postgres_ok or not disk_ok:
    overall = "error"
elif all(checks[k].get("status") == "ok" for k in checks):
    overall = "ok"
else:
    overall = "degraded"
```

## Info

### IN-01: Dark Mode CSS Mixes oklch and hsl Color Formats

**File:** `frontend/src/app/globals.css:87-121`
**Issue:** The `:root` (light mode) block uses `oklch()` color values, but the `.dark` block uses raw `hsl` component numbers (e.g., `240 10% 4%`). While this works because Tailwind/shadcn interprets these as hsl components, it creates inconsistency with the light mode block and the chart variables within dark mode which still use `oklch()`. This makes maintenance harder and could cause confusion.
**Fix:** Use a consistent color format across both light and dark mode blocks. Either convert all to oklch or all to hsl component format.

### IN-02: Settings Object Instantiated Multiple Times

**File:** `backend/app/health/router.py:21`
**File:** `backend/app/sources/router.py:11`
**File:** `backend/app/main.py:16`
**File:** `backend/app/database.py:5`
**Issue:** `Settings()` is instantiated in four different locations. While pydantic-settings caches environment reads, each call creates a new object and re-parses `.env`. This is not a bug but creates unnecessary work and makes it harder to override settings in tests.
**Fix:** Use a single `get_settings` dependency or a module-level singleton pattern. FastAPI's dependency injection with `lru_cache` is the standard approach:
```python
from functools import lru_cache

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

### IN-03: Test Source Registry Test Uses Hardcoded Relative Path

**File:** `backend/tests/test_source_registry.py:11`
**Issue:** `load_source_registry("config/sources.yml")` uses a relative path, which assumes tests are always run from the project root. This will break if tests are run from the `backend/` directory.
**Fix:** Use a path relative to the test file or a fixture that resolves the correct path:
```python
import os
SOURCES_YML = os.path.join(os.path.dirname(__file__), "..", "..", "config", "sources.yml")
```

---

_Reviewed: 2026-04-07T12:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
