---
phase: 02-source-ingestion
reviewed: 2026-04-07T19:00:00Z
depth: standard
files_reviewed: 31
files_reviewed_list:
  - backend/alembic/versions/002_add_source_ingestion_columns.py
  - backend/app/config.py
  - backend/app/sources/models.py
  - backend/app/sources/router.py
  - backend/app/sources/schemas.py
  - backend/app/sources/searxng.py
  - backend/app/sources/service.py
  - backend/Dockerfile
  - backend/pyproject.toml
  - backend/tests/conftest.py
  - backend/tests/test_ingestion.py
  - backend/tests/test_searxng.py
  - docker-compose.yml
  - frontend/src/app/sources/page.tsx
  - frontend/src/components/layout/sidebar.tsx
  - frontend/src/components/sources/ingestion-progress.tsx
  - frontend/src/components/sources/pdf-upload-tab.tsx
  - frontend/src/components/sources/quality-warning.tsx
  - frontend/src/components/sources/search-result-item.tsx
  - frontend/src/components/sources/search-tab.tsx
  - frontend/src/components/sources/source-list-item.tsx
  - frontend/src/components/sources/source-list.tsx
  - frontend/src/components/sources/source-tabs.tsx
  - frontend/src/components/sources/url-fetch-tab.tsx
  - frontend/src/components/ui/alert.tsx
  - frontend/src/components/ui/badge.tsx
  - frontend/src/components/ui/checkbox.tsx
  - frontend/src/components/ui/dialog.tsx
  - frontend/src/components/ui/progress.tsx
  - frontend/src/components/ui/skeleton.tsx
  - frontend/src/components/ui/tabs.tsx
  - frontend/src/lib/sse.ts
findings:
  critical: 1
  warning: 5
  info: 3
  total: 9
status: issues_found
---

# Phase 2: Code Review Report

**Reviewed:** 2026-04-07T19:00:00Z
**Depth:** standard
**Files Reviewed:** 31
**Status:** issues_found

## Summary

Phase 2 implements source ingestion (PDF upload, URL fetch, SearXNG search) with SSE progress streaming, duplicate detection, SSRF protection, and a frontend source management UI. The code is well-structured overall with good security practices (SSRF validation, content hashing for dedup, size limits). The main concerns are a TOCTOU race in SSRF validation, a mutable default argument in the model layer, missing `onSourceAdded` call in the URL fetch warning path, and redundant DB constraint setup in the migration.

UI components (shadcn/ui primitives) are standard generated code and have no issues.

## Critical Issues

### CR-01: SSRF TOCTOU Race -- DNS Resolution Checked Before Fetch

**File:** `backend/app/sources/service.py:268-291`
**Issue:** The `validate_url_safety()` call at line 270 resolves DNS and checks the IP is public, but `httpx.AsyncClient.get()` at line 283 resolves DNS again independently. Between the two resolutions, a DNS rebinding attack can switch the A record from a public IP to a private one (e.g., 169.254.169.254 for cloud metadata). The post-redirect check at line 288 validates `resp.url` (the final URL string after redirects) but not the actual IP the connection was made to -- it re-resolves DNS which is subject to the same race.

**Fix:** Use a custom `httpx` transport that resolves DNS once and validates the resolved IP before connecting. Alternatively, configure httpx with a custom `AsyncResolver` that rejects private IPs at connection time:

```python
import httpx

class SSRFSafeTransport(httpx.AsyncHTTPTransport):
    async def handle_async_request(self, request):
        # Resolve and validate before connecting
        hostname = request.url.host
        ip = ipaddress.ip_address(socket.gethostbyname(hostname))
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            raise UnsafeURLError(f"URL resolves to non-public IP: {ip}")
        return await super().handle_async_request(request)

async with httpx.AsyncClient(
    transport=SSRFSafeTransport(),
    timeout=settings.httpx_timeout,
    follow_redirects=True,
    max_redirects=settings.max_redirects,
) as client:
    resp = await client.get(url, headers={"User-Agent": "ClinicAtlas/1.0"})
```

This ensures every connection attempt (including redirects) validates the resolved IP.

## Warnings

### WR-01: Mutable Default Argument in SQLModel Field

**File:** `backend/app/sources/models.py:28`
**Issue:** `quality_flags: list[str] = Field(default=[])` uses a mutable default `[]`. While SQLModel/Pydantic v2 copies defaults per-instance (so instances don't share the list), this pattern is fragile -- if anyone accesses `RawSource.__fields__['quality_flags'].default` and mutates it, all future instances would be affected. The `sa_column` with `server_default="[]"` handles the DB side correctly.

**Fix:**
```python
quality_flags: list[str] = Field(
    default_factory=list,
    sa_column=Column(JSON, nullable=False, server_default="[]"),
)
```

### WR-02: URL Fetch Warning State Does Not Call onSourceAdded

**File:** `frontend/src/components/sources/url-fetch-tab.tsx:65-69`
**Issue:** When URL fetch completes with `thin_content` quality flag, the state is set to `"warning"` but `onSourceAdded()` is NOT called. The source was still ingested and stored in the DB, but the source list will not refresh until the user clicks "Fetch another" (which calls `onSourceAdded()` then `handleReset()`). This means the user sees the warning but the source list is stale.

Compare with `pdf-upload-tab.tsx:54` where `onSourceAdded()` is called in `onComplete` before checking quality flags -- that is the correct pattern.

**Fix:**
```typescript
onComplete: (data) => {
  onSourceAdded()  // Always refresh -- source was stored regardless of warnings
  if (data.quality_flags.includes("thin_content")) {
    setState("warning")
    setWarningMessage(
      "Content appears limited -- the page may require authentication."
    )
  } else if (data.quality_flags.includes("js_fallback_used")) {
    setState("complete")
  } else {
    setState("complete")
  }
},
```

### WR-03: Migration Creates Both UNIQUE Constraint and UNIQUE Index on Same Column

**File:** `backend/alembic/versions/002_add_source_ingestion_columns.py:46-56`
**Issue:** The migration drops the existing index, creates a UNIQUE constraint (which implicitly creates an index in Postgres), then creates another explicit UNIQUE index on the same column. This results in two indexes on `content_hash` -- the implicit one from the constraint and the explicit one. This wastes disk space and slows writes.

**Fix:** Either use only the UNIQUE constraint (Postgres creates an implicit index that supports queries) or use only the UNIQUE index (which enforces uniqueness). Pick one:

```python
# Option A: constraint only (implicit index handles queries)
op.drop_index("ix_raw_sources_content_hash", table_name="raw_sources")
op.create_unique_constraint(
    "uq_raw_sources_content_hash", "raw_sources", ["content_hash"]
)
# Do NOT re-create the index -- the constraint's implicit index is sufficient
```

### WR-04: Temp File Not Cleaned Up on Read Failure

**File:** `backend/app/sources/router.py:125-130`
**Issue:** At line 125, `tempfile.mkstemp()` creates the file and returns the fd. If `await file.read()` at line 128 raises an exception, the code raises `HTTPException` at line 130 but the temp file at `tmp_path` is never cleaned up (the fd is also leaked). The `finally` block in the `generate()` function won't run because `generate()` is never called.

**Fix:**
```python
tmp_fd, tmp_path = tempfile.mkstemp(suffix=".pdf")
try:
    content = await file.read()
except Exception:
    os.close(tmp_fd)
    os.unlink(tmp_path)
    raise HTTPException(status_code=400, detail="Failed to read uploaded file.")
```

### WR-05: SearchRequest.limit Has No Upper Bound

**File:** `backend/app/sources/schemas.py:33`
**Issue:** `limit: int = 10` has no validation constraint. A client can send `limit=999999` which would be passed to the SearXNG post-filter loop. While SearXNG itself limits results per page, the lack of a server-side cap is a code smell that could cause issues if the filtering logic changes.

**Fix:**
```python
from pydantic import Field as PydanticField

class SearchRequest(BaseModel):
    query: str
    limit: int = PydanticField(default=10, ge=1, le=50)
```

## Info

### IN-01: Hardcoded 50 MB Limit in Frontend

**File:** `frontend/src/components/sources/pdf-upload-tab.tsx:29`
**Issue:** The client-side size check `file.size > 50 * 1024 * 1024` hardcodes 50 MB. The backend limit is configurable via `settings.max_upload_size_mb`. If the backend limit changes, the frontend will be out of sync.

**Fix:** Consider exposing the limit via an API endpoint or environment variable (`NEXT_PUBLIC_MAX_UPLOAD_MB`), or accept the hardcoded value with a comment noting the coupling.

### IN-02: Playwright Browser Installed as Root, Run as Non-Root

**File:** `backend/Dockerfile:23-29`
**Issue:** `uv run playwright install chromium` runs before the non-root user is created. Playwright downloads browser binaries to a cache directory (typically `~/.cache/ms-playwright`). When the app runs as `appuser`, Playwright may not find the browser at the expected location because it was installed under root's home. The `chown` at line 30 covers `/home/appuser` but the Playwright cache was installed to `/root/.cache` during build.

**Fix:** Either install Playwright after switching to appuser, or set `PLAYWRIGHT_BROWSERS_PATH` to a shared location:

```dockerfile
ENV PLAYWRIGHT_BROWSERS_PATH=/opt/playwright-browsers
RUN uv run playwright install chromium
# ... then chown /opt/playwright-browsers to appuser
```

### IN-03: `response.headers` Missing Content-Type Check Guard

**File:** `backend/app/sources/service.py:293-294`
**Issue:** `resp.headers.get("content-type", "")` could be `None` in edge cases where httpx returns a non-string value. While httpx should always return strings, using `or ""` as a fallback is more defensive. Minor -- httpx is well-behaved here.

**Fix:** No action required. Noted for completeness.

---

_Reviewed: 2026-04-07T19:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
