# Phase 02 -- Source Ingestion: Security Audit

**ASVS Level:** 1
**Audit Date:** 2026-04-07
**Auditor:** GSD Security Auditor
**Threats Closed:** 10/10
**Status:** SECURED

## Threat Verification

| Threat ID | Category | Disposition | Evidence |
|-----------|----------|-------------|----------|
| T-02-01 | Tampering | mitigate | `router.py:108` extension check (.pdf), `router.py:112` MIME check (application/pdf), `router.py:118+135` 50 MB size limit (double-checked after read), `service.py:233` hash-based filename (`{content_hash}.pdf`), `service.py:234-238` atomic write (`.tmp` + `os.replace()`) |
| T-02-02 | Tampering | accept | Single-user app. react-markdown sanitizes output. Docling produces markdown, not raw HTML. |
| T-02-03 | Spoofing (SSRF) | mitigate | `service.py:83` scheme allowlist (http/https), `service.py:92+96` DNS resolution to non-private IP via `_validate_ip_is_public()`, `service.py:99-114` `SSRFSafeTransport` validates IPs at connection time including redirects (prevents DNS rebinding), `service.py:308` `max_redirects=settings.max_redirects` (default 5), `service.py:318` response size check (`max_response_size_mb` default 20) |
| T-02-04 | DoS | mitigate | `config.py:29` `max_upload_size_mb: int = 50`, `router.py:118+135` enforced at endpoint (pre-read + post-read), `service.py:42` `document_timeout = 300.0` |
| T-02-05 | Info Disclosure | accept | Single-user app. User controls which URLs they submit. No multi-tenant data leak vector. |
| T-02-06 | Tampering | accept | Source content rendered via react-markdown (sanitizes by default). No `dangerouslySetInnerHTML`. Single-user app. |
| T-02-07 | Info Disclosure | accept | `API_URL` is `localhost:8000` by design for local-first architecture. No secrets in frontend code. |
| T-02-08 | DoS | mitigate | `models.py:18-20` `sa_column=Column(String, unique=True, index=True, nullable=True)` UNIQUE constraint on `content_hash`. `service.py:258` and `service.py:459` catch `IntegrityError` for race condition on concurrent inserts. |
| T-02-09 | Spoofing | mitigate | `service.py:377-383` Playwright route handler compares `urlparse(route.request.url).hostname` against `target_host`, calls `route.abort()` for non-matching hosts. |
| T-02-10 | DoS | mitigate | `config.py:33` `max_response_size_mb: int = 20`, enforced at `service.py:318`. `config.py:32` `playwright_timeout: int = 30000`, enforced at `service.py:389`. |

## Accepted Risks Log

| Threat ID | Category | Risk Description | Justification |
|-----------|----------|------------------|---------------|
| T-02-02 | Tampering | Stored markdown could contain malicious content | react-markdown sanitizes by default. Docling output is markdown text, not raw HTML. Single-user app with no cross-user exposure. |
| T-02-05 | Info Disclosure | User-submitted URLs could leak information via server-side requests | Single-user app where the user controls all URL submissions. No multi-tenant data isolation needed. |
| T-02-06 | Tampering | Markdown display could render malicious content | react-markdown sanitizes output by default. No dangerouslySetInnerHTML used. Single-user local-first app. |
| T-02-07 | Info Disclosure | API_URL exposed in client-side JavaScript | By design: local-first architecture exposes localhost:8000. No secrets or credentials in frontend code. |

## Unregistered Flags

None. No `## Threat Flags` sections found in any SUMMARY.md files.

## Test Coverage

Threat mitigations are covered by automated tests in `backend/tests/test_ingestion.py`:

- `test_file_size_limit` -- T-02-04 (413 on oversized upload)
- `test_ssrf_private_ip_rejected` -- T-02-03 (private IP blocked)
- `test_duplicate_pdf_rejection` -- T-02-08 (UNIQUE constraint dedup)
- `test_scanned_pdf_detection` -- quality_flags persistence verification
- `test_pdf_upload_returns_sse_events` -- end-to-end upload flow
- `test_url_fetch_returns_sse_events` -- end-to-end fetch flow
- `test_thin_content_warning` -- quality_flags for thin content
