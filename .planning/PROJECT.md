# Clinic Atlas

## What This Is

A self-hosted, chat-first clinical knowledge assistant that researches trusted sources, synthesizes source-grounded answers, and maintains a living markdown knowledge base. Every research session compounds into the wiki — the system gets smarter with use. Built for a physician (Canada/Alberta) as a personal clinical reference tool, with open-source intent.

## Core Value

Every query compounds the knowledge base. Unlike ChatGPT where each session starts from zero, Clinic Atlas builds a growing, cited, searchable wiki that makes every future question faster and richer to answer.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Chat interface with streaming LLM responses (SSE)
- [ ] Source ingestion via PDF upload and URL fetch
- [ ] PDF parsing (PyMuPDF) and HTML/webpage extraction (trafilatura)
- [ ] Curated trusted source registry (YAML config)
- [ ] Web search scoped to trusted source domains for source discovery
- [ ] Postgres full-text search over knowledge base (tsvector, no vector DB)
- [ ] Research workflow: local search → evaluate existing knowledge → plan retrieval → fetch → parse → synthesize → approval → save
- [ ] Source note generation (one per raw source, with provenance)
- [ ] Topic note generation (synthesis across multiple sources, with inline citations)
- [ ] Research log generation (one per research session)
- [ ] Markdown knowledge storage on disk with YAML frontmatter
- [ ] Approval gate before saving notes (save / edit / discard)
- [ ] Topic browser with search
- [ ] On-demand refresh of existing topics (show diff, re-approve)
- [ ] Session history (past research sessions and chat logs)
- [ ] LLM provider flexibility via litellm (Ollama local default, Anthropic/OpenAI cloud option)

### Out of Scope

- Multi-user / authentication — single user, self-hosted
- DOCX support — PDF and HTML cover the primary source formats
- Vector DB / RAG pipeline — at small scale (~100-400 articles), FTS + LLM context window is sufficient
- Task queue / Celery — single user, inline processing + SSE
- Concept notes, index notes, update/diff notes — unnecessary until scale demands it
- Mermaid/figure generation, slide/handout generation — not core to knowledge compounding
- Scheduled/recurring refresh — on-demand only for v1
- Source registry UI editor — YAML file is sufficient for v1
- Image/figure extraction from PDFs — text extraction only
- Backlinks/bidirectional linking — defer until note volume demands it
- Mobile app — web-first
- OAuth / magic link login — no auth needed for single-user self-hosted

## Context

- Inspired by Karpathy's insight: at small scale, LLM + good indexes + full-text search replaces fancy RAG. Raw sources compiled into a markdown wiki by the LLM, every query compounds the knowledge base.
- Most medical sources (UpToDate, CPS, SOGC) require institutional authentication, so manual PDF upload is the realistic primary ingest path. Open-access sources can be auto-fetched.
- The web search agent scopes searches to trusted domains configured in the source registry, bridging the gap between manual upload and full automation.
- Clinical notes need provenance — every claim must trace back to a source with citation. Trust is non-negotiable.
- Three usage contexts: clinic prep (before patients), during encounters (quick reference), after-hours deep dives. The research workflow serves all three — no separate "quick mode."

## Constraints

- **Tech stack**: FastAPI (Python) backend, Next.js 14+ (App Router) + shadcn/ui frontend, Postgres via SQLModel — consistent with user's existing projects
- **LLM provider**: litellm for provider abstraction — Ollama (local default), Anthropic/OpenAI (cloud option). No custom provider layer.
- **Search**: Postgres full-text search (tsvector + GIN indexes) — no vector DB at this scale
- **Parsing**: PyMuPDF for PDFs, trafilatura for web pages
- **Dev environment**: Docker Compose (Postgres + backend + frontend)
- **Package managers**: uv (backend), pnpm (frontend)
- **Privacy**: Local-first — clinical data stays on the user's machine by default
- **Architecture**: Single Python process backend, no workers, no message broker
- **Testing**: Every phase includes tests for new functionality. Tests must pass before merging. TDD where practical — write tests alongside features, not as an afterthought.

## Testing Strategy

Every phase delivers tests alongside its features. This is a cross-cutting concern, not a separate phase.

- **Backend**: pytest with real Postgres (no SQLite substitution). Tests hit actual FTS, thesaurus, and migrations. Docker Compose test profile for isolated test runs.
- **Frontend**: Vitest + React Testing Library for component/unit tests. E2E tests (Playwright) added when there's real UI to test.
- **Coverage philosophy**: Test critical paths — API endpoints, business logic, data integrity. No arbitrary coverage % target. Tests should catch regressions, not pad metrics.
- **Test infrastructure**: Set up in Phase 1 alongside the dev stack. `docker compose --profile test run backend-test` for backend. `pnpm test` for frontend.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| FTS over vector DB | At ~100-400 articles, full-text search + LLM context window is sufficient. Simpler, no embedding pipeline. | — Pending |
| litellm over custom provider layer | Wraps Ollama/Anthropic/OpenAI with unified API. No maintenance burden. | — Pending |
| Markdown on disk + Postgres index | DB is the index, files are the content. Portable, inspectable, git-trackable. | — Pending |
| Web search scoped to trusted domains | Balances automation with source trust. Agent discovers content, user controls which sources are trusted. | — Pending |
| No quick mode / always full workflow | Simplifies UX — one mode, one flow. The research workflow is the product. | — Pending |
| Single user, no auth | Self-hosted personal tool. Open-source friendly but no multi-tenant complexity. | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-06 after initialization*
