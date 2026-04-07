---
phase: 1
slug: foundation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-07
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x (backend), vitest (frontend - if needed) |
| **Config file** | `backend/pyproject.toml` (pytest section) |
| **Quick run command** | `docker compose exec backend uv run pytest -x -q` |
| **Full suite command** | `docker compose exec backend uv run pytest --tb=short` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `docker compose exec backend uv run pytest -x -q`
- **After every plan wave:** Run `docker compose exec backend uv run pytest --tb=short`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 1-01-01 | 01 | 1 | KBSE-01 | — | N/A | integration | `docker compose up -d && docker compose ps` | ❌ W0 | ⬜ pending |
| 1-01-02 | 01 | 1 | KBSE-02 | — | N/A | integration | `docker compose exec backend uv run pytest tests/test_schema.py` | ❌ W0 | ⬜ pending |
| 1-01-03 | 01 | 1 | KBSE-02 | — | N/A | integration | `docker compose exec backend uv run pytest tests/test_fts.py` | ❌ W0 | ⬜ pending |
| 1-01-04 | 01 | 1 | SRCI-04 | — | N/A | unit | `docker compose exec backend uv run pytest tests/test_source_registry.py` | ❌ W0 | ⬜ pending |
| 1-01-05 | 01 | 1 | KBSE-01 | — | N/A | integration | `curl -sX POST http://localhost:8000/api/reindex \| jq .status` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/conftest.py` — shared fixtures (test DB session, cleanup)
- [ ] `backend/tests/test_schema.py` — stubs for KBSE-01, KBSE-02
- [ ] `backend/tests/test_fts.py` — stubs for FTS search with medical synonyms
- [ ] `backend/tests/test_source_registry.py` — stubs for SRCI-04
- [ ] pytest installed via `uv add --dev pytest pytest-asyncio httpx`

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| SearXNG returns search results | SRCI-04 | Requires running SearXNG container with network access | `curl 'http://localhost:8888/search?q=test&format=json'` and verify JSON response |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
