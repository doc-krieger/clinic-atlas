# Phase 2: Source Ingestion - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-07
**Phase:** 02-source-ingestion
**Areas discussed:** PDF upload flow, URL fetch behavior, SearXNG integration, Ingestion API design

---

## PDF Upload Flow

### Scanned PDF Detection
| Option | Description | Selected |
|--------|-------------|----------|
| Text extraction heuristic | Extract text with PyMuPDF — if pages yield < ~50 chars each, flag as scanned. Simple, no extra deps. | |
| PyMuPDF font analysis | Check if pages contain embedded fonts/text objects. More accurate but complex. | |
| OCR attempt with fallback | Try pytesseract on flagged pages. Adds heavy dependency. | |

**User's choice:** Text heuristic approach, but raised docling as a potential alternative parser.
**Notes:** User has experience with docling and finds it produces better extraction than PyMuPDF4LLM even on non-scanned PDFs. After research, decided to use docling as unified parser for both PDF and HTML.

### Duplicate Handling
| Option | Description | Selected |
|--------|-------------|----------|
| Reject with message | Return existing source record. No new row created. | ✓ |
| Allow re-upload | Create new row each time. | |
| Upsert — update existing | Overwrite existing content and re-index. | |

**User's choice:** Reject with message (Recommended)

### File Size Limit
| Option | Description | Selected |
|--------|-------------|----------|
| 50 MB limit | Covers clinical guidelines and textbook chapters. | ✓ |
| No limit | Trust the user. | |
| Configurable via env var | Default 50 MB, overridable. | |

**User's choice:** 50 MB limit (Recommended)

### PDF Metadata
| Option | Description | Selected |
|--------|-------------|----------|
| Title + page count + author | Extract from PDF document info dict. | ✓ |
| Title + page count only | Minimal extraction. | |
| Full document info | Title, author, subject, keywords, creation date, page count. | |

**User's choice:** Title + page count + author (Recommended)

### Parser Choice (follow-up)
| Option | Description | Selected |
|--------|-------------|----------|
| PyMuPDF4LLM | Lightweight, fast, already in stack spec. | |
| Docling | Full pipeline with OCR, layout analysis, table extraction. | |
| PyMuPDF4LLM now, docling later | Start light, swap later if needed. | |

**User's choice:** Docling — user finds it produces better output even on regular text PDFs and HTML.
**Notes:** Replaces both PyMuPDF4LLM and trafilatura with a single unified parser. Heavier Docker image but acceptable for self-hosted tool.

---

## URL Fetch Behavior

### Paywalled/Auth Pages
| Option | Description | Selected |
|--------|-------------|----------|
| Fetch and flag if thin | Attempt fetch, flag if < 200 chars extracted. | ✓ |
| Check registry first | Cross-reference requires_auth before fetching. | |
| Always attempt, never warn | Just try, user judges quality. | |

**User's choice:** Fetch and flag if thin (Recommended)

### JS Rendering
| Option | Description | Selected |
|--------|-------------|----------|
| HTTP only, follow redirects | httpx follows redirects. No JS. Simple. | |
| Add Playwright for JS pages | Handle JS SPAs. Heavy dependency. | |
| HTTP with JS fallback | Try httpx first, retry with headless browser if thin. | ✓ |

**User's choice:** HTTP with JS fallback
**Notes:** Some clinical knowledge bases (UpToDate, DynaMed) are JavaScript SPAs.

### URL Title Extraction
| Option | Description | Selected |
|--------|-------------|----------|
| Extract from HTML title tag | Docling or raw parse gives page title. | |
| Let user provide title | Prompt for name on submission. | |
| Auto-extract, user can edit later | Extract automatically, allow editing. | ✓ |

**User's choice:** Auto-extract, user can edit later

---

## SearXNG Integration

### Auto-ingest vs User Selection
| Option | Description | Selected |
|--------|-------------|----------|
| User picks from results | Show results as list, user selects which to ingest. | ✓ |
| Auto-ingest top N | Automatically fetch top 3-5 results. | |
| Auto-ingest with approval gate | Fetch automatically, hold in pending status. | |

**User's choice:** User picks from results (Recommended)

### Domain Scoping
| Option | Description | Selected |
|--------|-------------|----------|
| Append site: filters from registry | Build query with site: operators. | |
| Post-filter results by domain | Search broadly, filter to registered domains. | |
| Both — site filter + post-filter | Use site: in query AND post-filter results. | ✓ |

**User's choice:** Both — site filter + post-filter

---

## Ingestion API Design

### Processing Model
| Option | Description | Selected |
|--------|-------------|----------|
| Synchronous | Parse inline during request. Most PDFs < 5s. | |
| Async with polling | Return job ID, client polls. | |
| Sync with SSE progress | Keep connection open, stream progress events. | ✓ |

**User's choice:** Sync with SSE progress

### Response Format
| Option | Description | Selected |
|--------|-------------|----------|
| Full RawSource record | Return created record with id, title, status, page count, content preview. | ✓ |
| Minimal — id + status only | Just ID and parse_status. | |
| Full record + FTS snippet | Record plus search result sample. | |

**User's choice:** Full RawSource record (Recommended)

### Endpoint Structure
| Option | Description | Selected |
|--------|-------------|----------|
| Separate endpoints | POST /upload, POST /fetch, POST /search. Different input shapes. | ✓ |
| Unified endpoint | POST /ingest with file or URL. | |
| Separate + search endpoint | Three distinct endpoints for three operations. | |

**User's choice:** Separate endpoints (Recommended)

---

## Claude's Discretion

- Exact docling pipeline configuration options
- httpx timeout values and retry logic
- SSE event format and progress granularity
- Playwright headless browser configuration
- SearXNG query construction details
- Content preview truncation strategy

## Deferred Ideas

None — discussion stayed within phase scope
