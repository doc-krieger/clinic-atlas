---
phase: 2
slug: source-ingestion
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-07
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | backend/pyproject.toml |
| **Quick run command** | `make test-backend` |
| **Full suite command** | `make test` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `make test-backend`
- **After every plan wave:** Run `make test`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 2-01-01 | 01 | 1 | SRCI-01 | — | N/A | unit | `make test-backend` | ❌ W0 | ⬜ pending |
| 2-01-02 | 01 | 1 | SRCI-02 | — | N/A | unit | `make test-backend` | ❌ W0 | ⬜ pending |
| 2-01-03 | 01 | 1 | SRCI-03 | — | N/A | unit | `make test-backend` | ❌ W0 | ⬜ pending |
| 2-01-04 | 01 | 1 | SRCI-05 | — | N/A | integration | `make test-backend` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/test_ingestion.py` — stubs for SRCI-01, SRCI-02, SRCI-03
- [ ] `backend/tests/test_searxng.py` — stubs for SRCI-05
- [ ] `backend/tests/conftest.py` — shared fixtures (if not existing)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Scanned PDF quality flag visible in UI | SRCI-03 | Requires visual confirmation of UI flag | Upload scanned PDF, verify warning badge appears |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
