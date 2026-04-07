<!-- GSD:project-start source:PROJECT.md -->
## Project

**Clinic Atlas**

A self-hosted, chat-first clinical knowledge assistant that researches trusted sources, synthesizes source-grounded answers, and maintains a living markdown knowledge base. Every research session compounds into the wiki — the system gets smarter with use. Built for a physician (Canada/Alberta) as a personal clinical reference tool, with open-source intent.

**Core Value:** Every query compounds the knowledge base. Unlike ChatGPT where each session starts from zero, Clinic Atlas builds a growing, cited, searchable wiki that makes every future question faster and richer to answer.

### Constraints

- **Tech stack**: FastAPI (Python) backend, Next.js 14+ (App Router) + shadcn/ui frontend, Postgres via SQLModel — consistent with user's existing projects
- **LLM provider**: litellm for provider abstraction — Ollama (local default), Anthropic/OpenAI (cloud option). No custom provider layer.
- **Search**: Postgres full-text search (tsvector + GIN indexes) — no vector DB at this scale
- **Parsing**: PyMuPDF for PDFs, trafilatura for web pages
- **Dev environment**: Docker Compose (Postgres + backend + frontend)
- **Package managers**: uv (backend), pnpm (frontend)
- **Privacy**: Local-first — clinical data stays on the user's machine by default
- **Architecture**: Single Python process backend, no workers, no message broker
<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->
## Technology Stack

## Recommended Stack
### Core Technologies
| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| FastAPI | 0.135.3 | Python API backend, SSE streaming | Native `EventSourceResponse` added in 0.135.0 — no third-party SSE library needed. Fastest Python web framework, first-class async, automatic OpenAPI docs. |
| SQLModel | 0.0.24 | ORM + schema layer over Postgres | Tiangolo's own library bridges Pydantic v2 and SQLAlchemy 2.0. Tight FastAPI integration. Appropriate for a project that already commits to this stack family. |
| PostgreSQL | 17 | Primary database (FTS + metadata index) | Built-in tsvector/tsquery FTS with GIN indexes replaces Elasticsearch for this scale. `GENERATED ALWAYS AS` columns keep search vectors in sync without triggers. |
| Next.js | 15.x (App Router) | Frontend framework | Latest stable, fully compatible with React 19 and shadcn/ui 0.9.x. App Router required for streaming Route Handlers. |
| shadcn/ui | 0.9.x | Component library | Tailwind v4-compatible, full React 19 support. Unstyled primitives (Radix UI base) — no fighting CSS framework conflicts in a chat UI. |
| litellm | 1.83.3 | LLM provider abstraction | Unified OpenAI-format API over Ollama, Anthropic, OpenAI. Do NOT use 1.82.7 or 1.82.8 (supply chain attack, March 24 2026). Pin to `>=1.83.0`. |
| Ollama | latest | Local LLM runtime | Default provider. litellm calls it via `ollama_chat/` prefix for better response quality. Zero cost, fully local, privacy-preserving. |
| uv | 0.6.x | Python package/project manager | 10-100x faster than pip. Replaces pip + virtualenv + pip-tools in one tool. Docker-native with cache mounts. First-class `pyproject.toml` support. |
| pnpm | 9.x | Node.js package manager | Faster installs than npm/yarn, strict dependency resolution, good monorepo support if frontend ever splits. |
| Docker Compose | v2 | Local dev orchestration | Three-service setup: postgres + backend + frontend. Single `docker compose up` for onboarding. |
### Supporting Libraries — Backend
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| PyMuPDF4LLM | latest | PDF → Markdown for LLM ingestion | Preferred over raw `fitz`. Outputs clean GitHub-compatible Markdown preserving headers, tables, structure. Built on PyMuPDF. Use `pymupdf4llm.to_markdown(path, page_chunks=True)` for page-level chunking. |
| PyMuPDF (fitz) | 1.25.x | Low-level PDF access | Pulled in automatically as PyMuPDF4LLM dependency. Use directly only if you need page bounding boxes or raw spans. |
| trafilatura | 2.x | HTML/web page text extraction | Industry standard for main-content extraction from arbitrary HTML. `fetch_url()` + `extract()` pipeline. Handles boilerplate removal, metadata, date extraction. |
| httpx | 0.28.x | Async HTTP client | Replaces requests for async FastAPI contexts. HTTP/2 support, streaming response support, connection pooling. Use for URL fetching in the research agent. |
| Pydantic | v2 | Data validation / settings | Bundled with FastAPI 0.135+. Use `pydantic-settings` for config/env management. |
| python-frontmatter | 1.1.x | YAML frontmatter read/write on markdown files | Clean interface for reading/writing the frontmatter in knowledge base files. Handles the disk-based note storage pattern. |
| PyYAML | 6.x | YAML config parsing | Source registry YAML config. Already a transitive dep of python-frontmatter. |
| alembic | 1.14.x | Database migrations | SQLModel/SQLAlchemy migration tool. Required when schema evolves. Run via `uv run alembic`. |
### Supporting Libraries — Frontend
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| react-markdown | 9.x | Render markdown in chat/notes UI | Standard choice. Supports `components` prop for custom renderers. Use with remark-gfm for tables and task lists. |
| remark-gfm | 4.x | GitHub Flavored Markdown plugin for react-markdown | Enables tables, strikethrough, task lists — all present in clinical notes. Required alongside react-markdown. |
| react-syntax-highlighter | 15.x | Code block syntax highlighting | Use with react-markdown `components` override for code fences in generated notes. |
| @tanstack/react-query | 5.x | Server state / data fetching | Handles loading/error states, cache invalidation for topic browser and session history. Pairs naturally with Next.js App Router. |
| Tailwind CSS | v4.x | Utility-first CSS | Bundled with shadcn/ui 0.9.x. No separate config file needed in v4. |
| zustand | 5.x | Lightweight client state | Chat message list, streaming buffer, UI state. Simpler than Redux for single-user app with no auth complexity. |
### Development Tools
| Tool | Purpose | Notes |
|------|---------|-------|
| uv | Backend dependency management, virtualenv, script running | `uv sync`, `uv run` for all Python commands in Docker |
| pnpm | Frontend dependency management | `pnpm install`, `pnpm dev`, `pnpm build` |
| Alembic | Database migrations | `alembic revision --autogenerate -m "..."` then `alembic upgrade head` |
| Docker Compose v2 | Multi-service dev environment | Postgres 17 + FastAPI + Next.js + optional SearXNG container |
| Ruff | Python linter + formatter | Replaces flake8 + black + isort in one tool. `uv add --dev ruff` |
| ESLint + Prettier | Frontend lint + format | Standard with Next.js 15 scaffolding |
## Installation
# Backend (uv)
# Frontend (pnpm)
# shadcn/ui (via CLI, not direct install)
## Alternatives Considered
| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| FastAPI native SSE (`fastapi.sse`) | `sse-starlette` (third-party) | Only if you're on FastAPI < 0.135.0. Native support since 0.135.0 makes the third-party library redundant. |
| litellm `>=1.83.0` | Custom provider abstraction | Only if litellm's supply chain incident is an unacceptable risk posture for your org — for a personal self-hosted tool it's fine. |
| PyMuPDF4LLM | Plain `fitz` (PyMuPDF) | Use raw fitz only if you need fine-grained control over PDF rendering beyond text extraction. PyMuPDF4LLM is strictly better for the Markdown→LLM pipeline. |
| PostgreSQL tsvector FTS | pgvector + embeddings | If note count grows past ~1000 articles and keyword search recall drops. At the stated scale (100-400 articles), tsvector + GIN is simpler and sufficient. |
| SearXNG (self-hosted) | Brave Search API, Google PSE | Brave API requires API key + billing (credit-based as of Feb 2026). Google Custom Search Site Restricted API deprecated Jan 2025. SearXNG is free, self-hosted, no API key, supports domain filtering via JSON API. |
| react-markdown + remark-gfm | `@mdxjs/mdx` or `next-mdx-remote` | MDX is appropriate when markdown needs embedded React components. For display-only rendering of LLM output, react-markdown is simpler and safer (no eval risk). |
| zustand | Jotai, Redux Toolkit | Zustand 5.x has smaller API surface, no boilerplate, good TypeScript inference. Jotai is fine too. Redux is overkill for single-user app. |
| @tanstack/react-query v5 | SWR | react-query v5 has better mutation support and more predictable invalidation. Both work; react-query is the more common choice in 2025-era Next.js apps. |
## What NOT to Use
| Avoid | Why | Use Instead |
|-------|-----|-------------|
| litellm 1.82.7 or 1.82.8 | Supply chain attack published March 24, 2026. Contained credential-stealing malware for ~40 minutes on PyPI. Codebase itself was not compromised but PyPI packages were poisoned. | `litellm>=1.83.0` (verified clean by new CI/CD pipeline) |
| `sse-starlette` (third-party) | Redundant since FastAPI 0.135.0 ships `fastapi.sse.EventSourceResponse` natively. Third-party library adds a dependency with no benefit. | `fastapi.sse.EventSourceResponse` |
| Next.js Route Handlers as SSE proxy | Next.js buffers SSE responses unless compression is disabled and `X-Accel-Buffering: no` is set. Architecturally fragile for streaming. | Connect the browser's `EventSource` directly to the FastAPI backend. CORS-allow the frontend origin on the FastAPI side. |
| Vector DB (Chroma, Qdrant, Weaviate) | Adds embedding pipeline complexity and infrastructure. At 100-400 article scale, tsvector + GIN achieves sufficient recall with zero additional services. | PostgreSQL tsvector + GIN index |
| Celery / task queues | Single-user, single-process backend. No background workers needed. Adds Redis dependency and operational complexity. | FastAPI async handlers + SSE for long-running operations |
| Google Programmable Search Engine (Site Restricted API) | Deprecated January 2025. Migration path is Vertex AI Search, which is expensive and cloud-dependent. | SearXNG self-hosted instance |
| `requests` library | Synchronous — blocks the event loop in FastAPI async handlers. | `httpx` with `async with httpx.AsyncClient()` |
| SQLAlchemy directly (without SQLModel) | Not wrong, but SQLModel provides Pydantic validation on top and reduces boilerplate when the project already uses FastAPI + Pydantic. | SQLModel (wraps SQLAlchemy 2.0, compatible with raw SQLAlchemy when needed) |
## Stack Patterns by Context
- Use `EventSourceResponse` from `fastapi.sse` as `response_class`
- Yield Pydantic models from an `async def` path operation
- FastAPI handles JSON serialization automatically
- Browser connects via native `EventSource` API directly to FastAPI (not proxied through Next.js)
- Use `GENERATED ALWAYS AS (to_tsvector('english', content)) STORED` column on the notes table
- Create a `GIN` index on the generated column
- SQLModel does not natively model tsvector columns — use raw `text()` queries via `session.exec()` for FTS queries
- For ranking, use `ts_rank()` in the ORDER BY clause
- Prefix model with `ollama_chat/` not `ollama/` for better response formatting: `model="ollama_chat/llama3.2"`
- Set `api_base="http://ollama:11434"` in Docker Compose service networking
- Use `stream=True` and iterate chunks for SSE forwarding
- Store files as `notes/<slug>.md` with YAML frontmatter (`title`, `created`, `updated`, `sources`, `type`)
- Use `python-frontmatter` to read/write: `frontmatter.load(path)` → `post.metadata`, `post.content`
- Postgres stores the FTS index + metadata; disk files are the source of truth
- Use `pymupdf4llm.to_markdown(path, page_chunks=True)` — returns list of dicts with `text` and page metadata
- Join chunks for LLM context; keep page metadata for citation provenance
## Version Compatibility
| Package | Compatible With | Notes |
|---------|-----------------|-------|
| FastAPI 0.135.x | Pydantic v2, Python 3.10+ | Requires Python 3.10+ per release notes |
| SQLModel 0.0.24 | SQLAlchemy 2.x, Pydantic v2 | Do not mix with SQLAlchemy 1.x |
| litellm >=1.83.0 | Python 3.8+, all major providers | Avoid 1.82.7 and 1.82.8 explicitly in requirements |
| PyMuPDF4LLM latest | PyMuPDF 1.25.x (auto-installed) | No GPU needed for layout analysis |
| react-markdown 9.x | React 18+, React 19 | v9 is ESM-only — ensure bundler supports ESM (Next.js 15 does) |
| shadcn/ui 0.9.x | Next.js 14-15, Tailwind v4, React 19 | Use `pnpm dlx shadcn@latest init`, not `shadcn-ui` (deprecated CLI name) |
| @tanstack/react-query v5 | React 18+, React 19 | v5 is a major API break from v4 — do not mix docs |
## Web Search Integration (Gap Identified)
- Google Custom Search Site Restricted API deprecated January 2025
- Brave Search API shifted to credit-based billing in February 2026
- SearXNG is free, self-hosted, privacy-preserving, no API key
- Supports JSON output format (requires enabling in `settings.yml`)
- Simple HTTP API: `GET /search?q=site:cps.ca+neonatal+jaundice&format=json`
- Docker image: `searxng/searxng:latest`
# In FastAPI research agent
## Sources
- Context7 `/fastapi/fastapi` — SSE `EventSourceResponse` pattern, version 0.135.x
- Context7 `/berriai/litellm` — streaming, Ollama integration, provider config
- Context7 `/websites/sqlmodel_tiangolo` — index patterns (FTS not natively supported, raw SQL required)
- Context7 `/remarkjs/react-markdown` — custom components, syntax highlighting integration
- Context7 `/pymupdf/pymupdf4llm` — `to_markdown()` API, page_chunks parameter
- Context7 `/adbar/trafilatura` — `fetch_url()`, `extract_metadata()` API
- Context7 `/websites/astral_sh_uv` — Docker integration patterns
- [FastAPI SSE official docs](https://fastapi.tiangolo.com/tutorial/server-sent-events/) — confirmed 0.135.0 requirement (HIGH confidence)
- [LiteLLM supply chain security update](https://docs.litellm.ai/blog/security-update-march-2026) — 1.82.7/1.82.8 compromised, 1.83.0+ clean (HIGH confidence)
- [LiteLLM PyPI](https://pypi.org/project/litellm/) — 1.83.3 current as of 2026-04-05 (HIGH confidence)
- [FastAPI GitHub releases](https://github.com/fastapi/fastapi/releases) — 0.135.3 current as of 2026-04-01 (HIGH confidence)
- [shadcn/ui React 19 docs](https://ui.shadcn.com/docs/react-19) — 0.9.x, Next.js 14-15, Tailwind v4 compatible (HIGH confidence)
- [SearXNG search API docs](https://docs.searxng.org/dev/search_api.html) — JSON output format, query parameters (HIGH confidence)
- [Google Custom Search Site Restricted deprecation](https://developers.google.com/custom-search/v1/site_restricted_api) — deprecated Jan 2025 (HIGH confidence)
- [PyMuPDF4LLM ReadTheDocs](https://pymupdf.readthedocs.io/en/latest/pymupdf4llm/) — LLM-optimized Markdown extraction (HIGH confidence)
- WebSearch: Next.js SSE buffering issues and workarounds — `compress: false`, `X-Accel-Buffering: no` (MEDIUM confidence, multiple consistent sources)
- WebSearch: SQLModel + tsvector hybrid approach requiring raw SQL — confirmed by multiple SQLAlchemy/SQLModel issues (MEDIUM confidence)
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

### Makefile

Use `make <target>` for common operations instead of running raw docker compose / pytest / ruff commands:

- `make up` / `make down` — start/stop all containers
- `make test` — run all tests (backend + frontend)
- `make test-backend` / `make test-frontend` — run tests for one stack
- `make lint` / `make fmt` — lint check / auto-format
- `make migrate` — run pending Alembic migrations
- `make migrate-new msg="..."` — generate a new migration
- `make shell-backend` / `make shell-db` — drop into container shells
- `make clean` — stop containers and delete volumes
- `make` (no args) — show all available targets
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->
## Project Skills

| Skill | Description | Path |
|-------|-------------|------|
| playwright-cli | Automate browser interactions, test web pages and work with Playwright tests. | `.claude/skills/playwright-cli/SKILL.md` |
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
