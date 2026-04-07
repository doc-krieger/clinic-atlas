# Project Research Summary

**Project:** Clinic Atlas
**Domain:** Self-hosted chat-first clinical knowledge assistant (single user, local-first)
**Researched:** 2026-04-06
**Confidence:** HIGH

## Executive Summary

Clinic Atlas is a personal clinical knowledge assistant designed around a single core insight: knowledge should compound. Every research session should enrich a personal wiki that makes future queries better-answered. No commercial tool (UpToDate, DynaMed, OpenEvidence, Glass Health) does this — they all start from zero per session. This creates a clear, defensible differentiation that should guide every architectural and feature decision. The recommended implementation is a FastAPI backend with PostgreSQL full-text search, a Next.js frontend, and local Ollama LLM inference — all self-hosted via Docker Compose. This stack is well-matched to a single-user privacy-first tool and avoids unnecessary complexity (no vector DB, no background job queues, no auth system).

The architecture is a dual-storage pattern: markdown files on disk are the authoritative knowledge base (human-readable, git-trackable, portable), with PostgreSQL serving as a derived search index. The core workflow is a 10-step async generator that streams progress to the frontend via Server-Sent Events, pausing at an approval gate where the physician reviews and accepts synthesized notes before they enter the knowledge base. This mandatory approval gate is not just a UX feature — it is the trust mechanism that makes the tool usable in a clinical context. LLM output quality assurance (citation verification, provenance display, scanned PDF detection, context window budget enforcement) must be built in from day one, not retrofitted.

The top risks are all citation-related: LLMs fabricate plausible-sounding citations, scanned PDFs produce garbage text that silently corrupts the knowledge base, and Postgres FTS without medical synonym support returns zero results for common clinical abbreviations. These risks have known mitigations — verbatim quote-first synthesis prompts, word-count-per-page extraction checks, custom thesaurus dictionaries — but each must be designed into the relevant phase rather than added later. A secondary cluster of risks involves infrastructure: litellm silently swallows async Ollama streaming errors, Ollama's default 5-minute model unload causes unacceptable cold-start latency in clinical use, and the dual-storage pattern requires a reindex endpoint to recover from disk-DB drift.

## Key Findings

### Recommended Stack

The stack is built around the FastAPI / SQLModel / PostgreSQL / Next.js family, with Ollama as the default LLM provider abstracted through litellm. The critical version constraint is litellm: versions 1.82.7 and 1.82.8 contained a supply chain attack (March 24 2026) and must be explicitly excluded; pin to `>=1.83.0`. FastAPI 0.135.3 introduced native `EventSourceResponse` — the third-party `sse-starlette` library is now redundant and should not be used. PostgreSQL FTS with GIN indexes replaces a vector database at the 100-400 article scale; the "FTS is sufficient at small scale" argument holds, but only if a medical synonym dictionary is implemented. Web search scoped to trusted domains is best served by a self-hosted SearXNG instance — Google Custom Search was deprecated January 2025, and Brave Search shifted to credit-based billing in February 2026.

**Core technologies:**
- **FastAPI 0.135.3:** Python API backend, native SSE streaming — fastest async Python framework, native SSE since 0.135.0
- **PostgreSQL 17:** Primary database with tsvector FTS and GIN indexes — replaces vector DB at this scale
- **SQLModel 0.0.24:** ORM bridging Pydantic v2 and SQLAlchemy 2.0 — tight FastAPI integration, less boilerplate
- **litellm >=1.83.0:** LLM provider abstraction over Ollama/Anthropic/OpenAI — unified API, never install 1.82.7 or 1.82.8
- **Ollama:** Local LLM runtime — zero cost, fully local, privacy-preserving, default provider
- **Next.js 15 (App Router):** Frontend — required for streaming Route Handlers; compatible with React 19 and shadcn/ui 0.9.x
- **PyMuPDF4LLM:** PDF to LLM-optimized Markdown — use `to_markdown(path, page_chunks=True)` for page-level chunking
- **trafilatura 2.x:** HTML extraction from web pages — industry standard for main-content extraction
- **SearXNG (self-hosted):** Domain-scoped web search — free, no API key, privacy-preserving
- **uv 0.6.x / pnpm 9.x:** Package managers — 10-100x faster than pip/npm respectively

### Expected Features

**Must have (table stakes):**
- Conversational chat interface with streaming SSE responses — the standard UX paradigm for 2025 clinical AI
- Cited answers with source provenance — every clinical AI tool shows citations; without them a clinical tool is untrustworthy
- PDF ingestion — the primary source format for clinical literature (guidelines, CPG PDFs)
- Full-text search over the knowledge base — core to any knowledge tool
- Topic browser for navigating accumulated knowledge — without it the KB is write-only
- Session/query history — physicians revisit past research
- Trusted source scoping via domain registry — physicians do not want hallucinated or unreliable web results

**Should have (competitive differentiators):**
- Compounding knowledge base — the core value proposition; no commercial tool does this
- Mandatory approval gate before saving notes — the physician controls what enters their KB; prevents garbage-in
- Three note types (source, topic, research log) — structured capture: raw sources, synthesized topics, reasoning chain
- On-demand topic refresh with diff view — re-research with visual change tracking; no commercial tool offers this
- Local-first / self-hosted with Ollama — eliminates data residency concerns for Canadian/Alberta privacy requirements
- LLM provider flexibility — Ollama for privacy, cloud APIs for higher capability, one config change via litellm
- Web search scoped to trusted domains — automation without sacrificing trust

**Defer (v2+):**
- Multi-user support — requires auth, permissions, sync complexity; clone-your-own-instance is sufficient
- Scheduled source monitoring / alerts — background job infrastructure not justified for single-user v1
- CME/CPD credit logging — requires external system integration
- Differential diagnosis / patient-case mode — different product, different regulatory and liability posture
- Backlinks / graph view — only valuable at ~500+ notes; adds infrastructure overhead before that threshold

### Architecture Approach

The architecture is a three-tier system: a Next.js frontend that proxies SSE and REST calls, a FastAPI backend with a service layer (orchestrator, LLM, FTS, ingestion) built on async generators, and a dual storage layer (markdown files on disk as source of truth, PostgreSQL as derived search index). The research orchestrator is the core component — a Python async generator that runs a 10-step workflow (search local KB, evaluate coverage, plan fetch, fetch sources, parse content, synthesize notes, emit approval gate event, save on approval, log session). The workflow streams typed SSE events at each step so the frontend can show real-time progress. The approval gate splits the workflow at step 7: the generator exits cleanly with draft notes stored in server-side state, the frontend renders the approval widget, and approval/discard arrives as a separate POST to a continuation endpoint.

**Major components:**
1. **Research Orchestrator** (`services/orchestrator.py`) — async generator driving the 10-step workflow; all business logic lives here
2. **LLM Service** (`services/llm.py`) — litellm wrapper; provider-agnostic, handles streaming, implements heartbeat/error wrapping
3. **Ingestion Service** (`services/ingestion.py`) — PDF parsing via PyMuPDF4LLM, HTML extraction via trafilatura; wraps blocking calls in `asyncio.to_thread()`
4. **FTS Service** (`services/search.py`) — tsvector queries via raw SQL (SQLModel does not natively support tsvector); includes medical synonym expansion
5. **Storage Layer** (`storage/disk.py` + Postgres) — write file first, upsert Postgres row second; reindex endpoint for recovery
6. **FastAPI SSE Endpoint** (`api/chat.py`) — wires orchestrator to HTTP; handles `approval_pending` session state
7. **Next.js SSE Proxy** (`app/api/chat/stream/route.ts`) — pipes `upstream.body` ReadableStream without awaiting; sets `X-Accel-Buffering: no` to prevent nginx buffering
8. **Chat UI + Approval Gate** (`components/chat/`) — EventSource hook, StepProgress display, ApprovalGate widget

### Critical Pitfalls

1. **Citation fabrication** — LLMs confabulate plausible citations even when sources are in context; studies show 50-90% of LLM-generated citations are not fully supported. Avoid by: designing synthesis prompts to require verbatim quoted evidence before each claim, separating retrieval / quote extraction / synthesis into distinct steps, displaying source chunks alongside generated claims.

2. **Scanned PDF silent garbage extraction** — PyMuPDF has no OCR; scanned PDFs return near-empty text that gets indexed and passed to the LLM as source material. Avoid by: checking word-count-per-page ratio after extraction; flagging PDFs yielding fewer than 100 words per page before indexing; integrating Tesseract as an OCR fallback.

3. **Postgres FTS medical synonym gap** — A search for "HTN" finds nothing when articles use "hypertension"; "T2DM" misses "type 2 diabetes mellitus." The default English Snowball stemmer has no medical knowledge. Avoid by: building a custom Postgres thesaurus dictionary covering abbreviations, brand/generic drug pairs, and query expansion in the search service layer. Must be designed at schema creation time.

4. **litellm async streaming errors silently swallowed** — Confirmed GitHub bug #8868: async streaming errors from Ollama are swallowed; stream truncates mid-sentence with no error. Avoid by: wrapping the litellm async iterator in try/except and yielding an explicit `error` SSE event; implementing a heartbeat timeout independent of litellm.

5. **Ollama cold-start latency** — Default 5-minute model unload causes 20-60 second cold starts, unusable during patient encounters. litellm adds an additional ~20 seconds on reconnection (confirmed bug #17954). Avoid by: setting `OLLAMA_KEEP_ALIVE=-1` in Docker Compose environment; implementing a model warm-up ping on application startup.

6. **Context window overrun degrades synthesis without obvious failure** — Passing 5-8 source documents to a local model with a 4K-8K context window causes silent truncation; the model synthesizes from partial information. Avoid by: counting tokens before building the synthesis prompt, enforcing a hard budget (60% sources / 20% system prompt / 20% output headroom), and notifying the user of omitted sources.

## Implications for Roadmap

Based on combined research, the architecture's dependency layers and pitfall prevention requirements suggest the following phase structure. Build bottom-up: storage before services, services before orchestration, orchestration before UI.

### Phase 1: Foundation — Storage and Infrastructure

**Rationale:** Nothing else works without this. Postgres schema, disk layout, FTS indexes with medical synonym dictionary, and Docker Compose configuration must be established first. The synonym dictionary must be designed at schema creation time (Pitfall 5). Docker Compose `OLLAMA_KEEP_ALIVE=-1` must be set before first end-to-end test or cold-start latency will be misattributed to app code (Pitfall 4).

**Delivers:** Running Docker Compose stack (Postgres 17 + FastAPI shell + Next.js shell + Ollama + SearXNG), SQLModel schema with tsvector columns and GIN indexes, disk layout (`knowledge/sources/`, `knowledge/topics/`, `knowledge/logs/`), Alembic migrations, custom medical thesaurus dictionary installed in Postgres, reindex endpoint skeleton.

**Addresses:** Full-text search table stake, local-first/privacy differentiator.

**Avoids:** Postgres FTS medical synonym gap (Pitfall 5), Ollama cold-start latency (Pitfall 4), file-DB sync divergence (Pitfall 6 — reindex endpoint from day one).

### Phase 2: Source Ingestion Pipeline

**Rationale:** The knowledge base must be populated before the chat workflow can be tested meaningfully. Ingestion service must include quality checks at this phase — scanned PDF detection and gated content detection cannot be retrofitted after content is already indexed (Pitfalls 2 and 8).

**Delivers:** PDF upload endpoint with PyMuPDF4LLM extraction, URL fetch endpoint with trafilatura extraction, word-count-per-page check flagging scanned PDFs, content quality check detecting gated content, source notes written to disk with YAML frontmatter, source notes indexed in Postgres, `fetch_mode` field in source registry YAML.

**Uses:** PyMuPDF4LLM, trafilatura, httpx async, python-frontmatter, `asyncio.to_thread()` for blocking extraction calls.

**Avoids:** Scanned PDF silent garbage (Pitfall 2), web fetch gating blindness (Pitfall 8), sync blocking in async handlers (Pitfall 7).

### Phase 3: LLM Service and Chat Infrastructure

**Rationale:** The LLM service and SSE infrastructure are prerequisites for the research orchestrator. The SSE error contract (heartbeat, explicit error events, litellm async error wrapping) must be designed here, not after the chat UI exists.

**Delivers:** litellm wrapper with Ollama default and cloud fallback configuration, async streaming with heartbeat and explicit error SSE events, FastAPI SSE endpoint with `EventSourceResponse`, Next.js SSE proxy with no-buffer headers, basic chat UI (message list, step progress display), EventSource hook with reconnect logic and error state handling.

**Uses:** FastAPI 0.135.3 native SSE, litellm >=1.83.0, zustand for chat state, shadcn/ui components.

**Avoids:** litellm async streaming errors silently swallowed (Pitfall 3), SSE buffering in Next.js (Architecture Anti-Pattern 1), sync blocking calls (Pitfall 7).

### Phase 4: Research Orchestrator and Note Generation

**Rationale:** The orchestrator is the integration point for all lower-level services. Citation quality and context window budget management must be built into the synthesis step here — they cannot be retrofitted without changing the prompt architecture (Pitfalls 1 and 9).

**Delivers:** 10-step async generator research workflow, FTS local search step with synonym-expanded queries, web search step via SearXNG scoped to trusted source registry, verbatim quote-extraction prompt stage before synthesis, token budget enforcement with relevance-ranked source truncation and user notification, source note generation, topic note generation with inline citations and provenance display, research log generation, SSE step-progress events for all 10 steps.

**Uses:** All services from Phases 1-3, SearXNG JSON API via httpx.

**Avoids:** Citation fabrication (Pitfall 1), context window overrun (Pitfall 9), event loop blocking (Pitfall 7).

### Phase 5: Approval Gate and Knowledge Base Persistence

**Rationale:** The approval gate requires a working orchestrator (Phase 4) and is the mechanism that makes knowledge accumulation trustworthy. Session state design (in-memory dict keyed by session ID) and the split-workflow pattern must be implemented correctly — the generator-resume anti-pattern is a common mistake here (Architecture Anti-Pattern 3).

**Delivers:** `approval_pending` SSE event with draft notes payload, server-side session state for pending approvals, ApprovalGate frontend widget (save / edit inline / discard), POST `/approve/{session_id}` continuation endpoint, atomic file write (write to temp then rename) before Postgres upsert, soft-delete pattern for note deletion.

**Avoids:** Generator resume anti-pattern (Architecture Anti-Pattern 3), content in Postgres instead of disk (Architecture Anti-Pattern 2), file-DB sync divergence on delete (Pitfall 6).

### Phase 6: Topic Browser and Session History

**Rationale:** Read-only views over the Postgres index. No blocking dependencies except accumulated content from Phase 5. Straightforward once notes exist.

**Delivers:** Topic browser with FTS search (ranked results, "did you mean" synonym expansion), topic detail view with source chain display, session history list with chat replay, XSS sanitization on note rendering (DOMPurify / bleach — notes are LLM-generated).

**Uses:** Postgres FTS with ts_rank, @tanstack/react-query for server state, react-markdown + remark-gfm for note rendering.

**Avoids:** XSS from unsanitized LLM output, file path traversal in API responses.

### Phase 7: Topic Refresh and Diff View

**Rationale:** On-demand topic refresh builds on all prior layers and is the feature that most demonstrates the "knowledge compounds" thesis. This is a v1.x feature — deliver it once there are topics worth refreshing.

**Delivers:** "Re-research this topic" action on topic detail page, diff view showing old note vs new draft before approval gate, topic refresh workflow reusing the Phase 4 orchestrator with the existing topic slug, updated YAML frontmatter (`updated` timestamp) on save.

**Uses:** All prior phases, a diff library for frontend diff rendering.

**Avoids:** No new pitfalls — all mitigations already in place from prior phases.

### Phase Ordering Rationale

- Storage must precede ingestion: FTS schema and synonym dictionary must exist before any content is indexed; wrong lexemes cannot be fixed without re-indexing.
- Ingestion must precede orchestration: the orchestrator's local search step is meaningless without KB content; extraction quality checks cannot be retrofitted after garbage is indexed.
- LLM service and SSE infrastructure must precede orchestration: the orchestrator relies on both; the SSE error contract must be defined before the frontend chat UI is built on top of it.
- The approval gate requires a working orchestrator to produce draft notes.
- The topic browser has no blocking dependencies except content — it could be built alongside Phase 5, but depends on Phase 4 for meaningful data.
- Topic refresh extends the orchestrator and approval gate — it belongs last.

### Research Flags

Phases likely needing deeper research during planning:

- **Phase 4 (Research Orchestrator):** The multi-step synthesis prompt architecture (verbatim quote extraction → synthesis → citation verification) is the most novel and domain-specific engineering in the project. Prompt design for medical synthesis has sparse documentation. Recommend a research-phase sprint focused on optimal prompt patterns for clinical note generation with local models.
- **Phase 1 (Postgres medical thesaurus):** Custom Postgres thesaurus dictionary installation is well-documented but the medical synonym set (abbreviations, brand names, Canadian clinical variants) requires domain-specific compilation. This is a content research task, not a technical unknown.

Phases with standard patterns (research-phase not needed):

- **Phase 2 (Source Ingestion):** PyMuPDF4LLM and trafilatura are well-documented. Implementation patterns are clear from STACK.md.
- **Phase 3 (LLM + SSE):** FastAPI SSE, litellm Ollama integration, and Next.js proxy patterns are thoroughly documented in STACK.md and ARCHITECTURE.md.
- **Phase 5 (Approval Gate):** The split-workflow pattern is clearly specified in ARCHITECTURE.md with worked examples.
- **Phase 6 (Topic Browser):** Standard CRUD + search views over an existing Postgres index.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All major technologies verified against official docs via Context7 and direct source checks. Critical version constraints (litellm supply chain, FastAPI 0.135.0 native SSE) confirmed with high-confidence sources. |
| Features | MEDIUM-HIGH | Commercial tool features verified via official sources and comparative research. Physician PKM patterns from forum data carry lower confidence but are directionally consistent with the product brief. |
| Architecture | HIGH | Patterns verified against official FastAPI SSE docs, confirmed GitHub discussions on Next.js SSE buffering, and reference implementations. Anti-patterns documented with confirmed GitHub issues. |
| Pitfalls | HIGH | Most pitfalls verified against official docs, confirmed GitHub issues (litellm #8868, #17954), and peer-reviewed literature on LLM citation accuracy in medicine. |

**Overall confidence:** HIGH

### Gaps to Address

- **Medical synonym dictionary content:** The technical mechanism (Postgres thesaurus dictionary) is clear, but the actual set of abbreviations and brand/generic pairs relevant to a general-practice Alberta physician needs to be compiled. Start with a short list (HTN, T2DM, MI, PE, DVT, URTI) and expand based on actual search failures observed during use.

- **Optimal local model for synthesis:** The right Ollama model size vs. quality tradeoff for clinical synthesis tasks is not established. Research assumes >=7B is necessary for acceptable citation quality; >=13B preferred. The practical choice (llama3.2:3b vs llama3.1:8b vs mistral:7b) should be validated empirically during Phase 4 rather than assumed from research.

- **SearXNG trusted domain configuration:** The source registry YAML structure is specified, but the initial list of trusted domains (CPS, SOGC, ACOG, CFPC, etc.) and their `fetch_mode` classifications (auto vs. manual) require domain knowledge about which sources are open-access vs. gated. Should be populated during Phase 2 based on actual testing.

- **Token counting for Ollama models:** tiktoken is calibrated for OpenAI models. Token count accuracy for Ollama models (which use different tokenizers) may require using the model's own tokenizer via the Ollama API. Should be tested during Phase 4 token budget implementation.

## Sources

### Primary (HIGH confidence)
- Context7 `/fastapi/fastapi` — SSE EventSourceResponse pattern, version 0.135.x
- Context7 `/berriai/litellm` — streaming, Ollama integration, provider config
- Context7 `/websites/sqlmodel_tiangolo` — index patterns, raw SQL for FTS
- Context7 `/remarkjs/react-markdown` — custom components, syntax highlighting
- Context7 `/pymupdf/pymupdf4llm` — `to_markdown()` API, page_chunks parameter
- Context7 `/adbar/trafilatura` — `fetch_url()`, `extract_metadata()` API
- Context7 `/websites/astral_sh_uv` — Docker integration patterns
- [FastAPI SSE official docs](https://fastapi.tiangolo.com/tutorial/server-sent-events/) — confirmed 0.135.0 requirement
- [LiteLLM supply chain security update](https://docs.litellm.ai/blog/security-update-march-2026) — 1.82.7/1.82.8 compromised
- [litellm GitHub Issue #8868](https://github.com/BerriAI/litellm/issues/8868) — async streaming errors swallowed
- [litellm GitHub Issue #17954](https://github.com/BerriAI/litellm/issues/17954) — high latency after idle with Ollama
- [shadcn/ui React 19 docs](https://ui.shadcn.com/docs/react-19) — 0.9.x, Next.js 14-15, Tailwind v4 compatible
- [SearXNG search API docs](https://docs.searxng.org/dev/search_api.html) — JSON output, query parameters
- [Postgres FTS Documentation thesaurus](https://www.postgresql.org/docs/current/textsearch-dictionaries.html)
- [Nature Communications — LLM citation accuracy in medicine](https://www.nature.com/articles/s41467-025-58551-6)
- [medRxiv — Medical Hallucination in Foundation Models](https://www.medrxiv.org/content/10.1101/2025.02.28.25323115v2.full)
- [PyMuPDF4LLM ReadTheDocs](https://pymupdf.readthedocs.io/en/latest/pymupdf4llm/)

### Secondary (MEDIUM confidence)
- WebSearch: Next.js SSE buffering issues — `compress: false`, `X-Accel-Buffering: no` workarounds
- WebSearch: SQLModel + tsvector requiring raw SQL — confirmed by multiple SQLAlchemy/SQLModel issues
- [iatroX: Best AI Clinical Decision Support Tools 2026](https://www.iatrox.com/blog/best-ai-clinical-decision-support-tools-2026-uptodate-ai-dynamed-iatrox) — competitor feature analysis
- [Obsidian Forum: Knowledge management as a medical doctor](https://forum.obsidian.md/t/how-to-manage-knowledge-as-a-medical-doctor/85846) — physician PKM patterns
- Karpathy LLM Wiki architecture — FTS + context window vs. RAG at small scale
- [Google Custom Search Site Restricted API deprecation](https://developers.google.com/custom-search/v1/site_restricted_api) — deprecated Jan 2025

---
*Research completed: 2026-04-06*
*Ready for roadmap: yes*
