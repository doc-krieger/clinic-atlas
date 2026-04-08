---
phase: 02-source-ingestion
fixed_at: 2026-04-07T19:30:00Z
review_path: .planning/phases/02-source-ingestion/02-REVIEW.md
iteration: 1
findings_in_scope: 6
fixed: 6
skipped: 0
status: all_fixed
---

# Phase 2: Code Review Fix Report

**Fixed at:** 2026-04-07T19:30:00Z
**Source review:** .planning/phases/02-source-ingestion/02-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 6
- Fixed: 6
- Skipped: 0

## Fixed Issues

### CR-01: SSRF TOCTOU Race -- DNS Resolution Checked Before Fetch

**Files modified:** `backend/app/sources/service.py`
**Commit:** ab77dc3
**Applied fix:** Added `SSRFSafeTransport(httpx.AsyncHTTPTransport)` that validates resolved IPs at connection time (including redirects). Extracted shared `_validate_ip_is_public()` helper. Updated `fetch_and_parse_url` to use the safe transport, catching `UnsafeURLError` from the transport layer. Removed the post-redirect `validate_url_safety()` call since the transport now handles all connection-time validation.

### WR-01: Mutable Default Argument in SQLModel Field

**Files modified:** `backend/app/sources/models.py`
**Commit:** de52229
**Applied fix:** Changed `default=[]` to `default_factory=list` on the `quality_flags` field. The `sa_column` with `server_default="[]"` remains unchanged for DB-level defaults.

### WR-02: URL Fetch Warning State Does Not Call onSourceAdded

**Files modified:** `frontend/src/components/sources/url-fetch-tab.tsx`
**Commit:** bf79f68
**Applied fix:** Moved `onSourceAdded()` call to the top of the `onComplete` handler so it fires unconditionally -- the source is stored in the DB regardless of quality warnings. Removed redundant `onSourceAdded()` calls from individual branches and from the "Fetch another" warning button (no longer needed since refresh already happened).

### WR-03: Migration Creates Both UNIQUE Constraint and UNIQUE Index on Same Column

**Files modified:** `backend/alembic/versions/002_add_source_ingestion_columns.py`
**Commit:** 0960ed6
**Applied fix:** Removed the redundant `op.create_index()` call after `op.create_unique_constraint()`. Postgres creates an implicit unique index for the constraint, which is sufficient for both uniqueness enforcement and query performance. Updated downgrade to match (removed `op.drop_index` since only the constraint needs dropping).

### WR-04: Temp File Not Cleaned Up on Read Failure

**Files modified:** `backend/app/sources/router.py`
**Commit:** 8191890
**Applied fix:** Added `os.close(tmp_fd)` and `os.unlink(tmp_path)` in the `except` block before raising HTTPException. This ensures the temp file and fd are cleaned up if `await file.read()` fails.

### WR-05: SearchRequest.limit Has No Upper Bound

**Files modified:** `backend/app/sources/schemas.py`
**Commit:** ba5829f
**Applied fix:** Changed `limit: int = 10` to `limit: int = Field(default=10, ge=1, le=50)` with Pydantic validation. Added `Field` to the pydantic import.

## Skipped Issues

None -- all in-scope findings were fixed.

---

_Fixed: 2026-04-07T19:30:00Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
