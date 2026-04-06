# Clinic Atlas — MVP Implementation Plan

## Overview

A self-hosted, chat-first clinical knowledge assistant that researches trusted sources, drafts source-grounded answers, and maintains a living markdown knowledge base.

Inspired by [Karpathy's approach](karpathy-post.md): at small scale (~100–400 articles), LLM + good indexes + full-text search replaces fancy RAG. Raw sources are compiled into a markdown wiki by the LLM, and every query compounds the knowledge base.

---

## What's In V1

Ask a question in chat → system checks local notes → optionally fetches from trusted sources → synthesizes a cited answer → offers to save topic/source notes. Browse saved topics. Re-ask to refresh.

### In scope
- Chat/query UI with streaming responses
- Curated source registry (YAML config)
- Local knowledge base search (Postgres full-text search)
- Manual source ingestion (PDF upload, URL fetch)
- PDF and webpage parsing
- Source note generation (one per raw source)
- Topic note generation (synthesis across sources)
- Research log generation (one per session)
- Markdown knowledge storage on disk
- Provenance/source links in every note
- On-demand refresh of prior topics
- Topic browser with search
- Approval gate before saving notes (chat-inline)

### Cut from V1
- Concept notes, index notes, update/diff notes
- Mermaid/figure generation, slide/handout generation
- Health checks / knowledge base linting
- Scheduled/recurring refresh (on-demand only)
- Comparison pages
- DOCX support (PDF and HTML only)
- Image/figure extraction from PDFs
- Celery/worker queue (single user = inline + SSE)
- Backlinks/bidirectional linking system
- Three-panel layout (two panels: chat + detail sidebar)
- Source registry UI editor (YAML file only)
- Obsidian compatibility concerns

---

## Tech Stack

| Layer | Choice | Why |
|---|---|---|
| Backend | **FastAPI** (Python) | LLM libs, PDF parsing, markdown — all Python-native. Async, typed, auto-docs. |
| Frontend | **Next.js 14+ (App Router)** + **shadcn/ui** | Polished components, productive DX. Consistent with existing projects. |
| Database | **Postgres** via **SQLModel** | Full-text search via tsvector. Reliable, well-understood. Docker Compose for dev. |
| LLM | **litellm** | Wraps Ollama/Anthropic/OpenAI with unified API. No custom provider layer needed. |
| PDF parsing | **PyMuPDF (fitz)** | Fast, reliable text + metadata extraction. |
| HTML parsing | **trafilatura** | Best-in-class article/content extraction from web pages. |
| HTTP client | **httpx** | Async Python HTTP client. |
| Streaming | **Server-Sent Events** (SSE) | Native FastAPI support for streaming LLM responses. |
| Dev environment | **Docker Compose** | Postgres + backend + frontend in one `docker compose up`. |
| Package managers | **uv** (backend), **pnpm** (frontend) | Fast, modern. |

### What we're NOT using
- **No vector DB** — at small scale, full-text search + LLM context window is sufficient
- **No RAG pipeline** — relevant source text goes directly into the LLM prompt
- **No task queue** — single user, one query at a time, SSE streaming
- **No custom provider abstraction** — litellm handles this

---

## Architecture

```
Browser
  │
  ▼
Next.js frontend (port 3000)
  │  API calls
  ▼
FastAPI backend (port 8000)
  ├── Postgres (metadata, FTS via tsvector)
  ├── knowledge/ directory (raw + compiled files on disk)
  ├── litellm → Ollama (local) or Anthropic/OpenAI (cloud)
  ├── httpx → trusted sources (web fetch)
  └── PyMuPDF / trafilatura (parsing)
```

Single Python process backend. No workers, no message broker. Postgres runs in Docker.

---

## Repo Structure

```
clinic-atlas/
├── docs/                              # Project docs (this file, brainstorming)
├── docker-compose.yml                 # Postgres + dev services
├── backend/
│   ├── pyproject.toml                 # uv project
│   ├── sources.yaml                   # Trusted source registry
│   └── src/clinic_atlas/
│       ├── main.py                    # FastAPI app, lifespan, CORS
│       ├── config.py                  # Settings via pydantic-settings
│       ├── db.py                      # Postgres/SQLModel engine + session
│       ├── models/
│       │   ├── source.py              # RawSource table
│       │   ├── note.py                # CompiledNote table
│       │   └── session.py             # ResearchSession + ChatMessage tables
│       ├── api/
│       │   ├── chat.py                # POST /api/chat (SSE streaming)
│       │   ├── notes.py               # CRUD for compiled notes
│       │   ├── sources.py             # Upload/fetch raw sources
│       │   └── sessions.py            # Research session history
│       ├── services/
│       │   ├── llm.py                 # litellm wrapper + prompt dispatch
│       │   ├── research.py            # Core research workflow orchestrator
│       │   ├── retrieval.py           # Fetch from trusted sources
│       │   ├── parsing.py             # PDF + HTML text extraction
│       │   ├── knowledge.py           # Read/write compiled markdown files
│       │   └── search.py              # Postgres FTS queries
│       └── prompts/
│           ├── system.py              # Base system prompt
│           ├── synthesis.py           # Answer synthesis prompt
│           ├── source_note.py         # Source note generation prompt
│           └── topic_note.py          # Topic note generation prompt
├── frontend/
│   ├── package.json
│   ├── next.config.js
│   └── src/
│       ├── app/
│       │   ├── layout.tsx             # Root layout with sidebar
│       │   ├── page.tsx               # Chat page (default route)
│       │   ├── topics/
│       │   │   ├── page.tsx           # Topic browser
│       │   │   └── [id]/page.tsx      # Single topic view
│       │   └── sessions/
│       │       └── page.tsx           # Research session history
│       ├── components/
│       │   ├── chat/                  # Chat panel, messages, source cards, approval
│       │   ├── notes/                 # Note viewer, topic list
│       │   └── ui/                    # shadcn components
│       └── lib/
│           ├── api.ts                 # Backend fetch wrapper
│           └── types.ts               # Shared TypeScript types
└── knowledge/                         # The knowledge base (on disk)
    ├── raw/
    │   └── sources/                   # PDFs, HTML snapshots, extracted text
    └── compiled/
        ├── source-notes/              # One .md per raw source
        ├── topic-notes/               # One .md per clinical topic
        └── research-logs/             # One .md per research session
```

---

## Database Schema

Four tables. Postgres full-text search via `tsvector` columns.

### raw_sources

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| title | TEXT NOT NULL | |
| source_name | TEXT | e.g. "UpToDate", "SOGC", "Manual Upload" |
| source_type | TEXT | pdf, webpage, upload |
| original_url | TEXT | |
| local_path | TEXT NOT NULL | Relative path in knowledge/raw/ |
| file_hash | TEXT | SHA-256 of file content |
| retrieved_at | TIMESTAMP | |
| published_date | TEXT | Freeform, as found in document |
| jurisdiction | TEXT | e.g. "Canada", "Alberta" |
| parser_status | TEXT | pending, parsed, failed |
| metadata_json | JSONB | Flexible extra metadata |
| search_vector | TSVECTOR | FTS on title + extracted text |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | |

### compiled_notes

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| note_type | TEXT NOT NULL | topic_note, source_note, research_log |
| title | TEXT NOT NULL | |
| slug | TEXT UNIQUE | URL-friendly, also the filename stem |
| local_path | TEXT NOT NULL | Relative path in knowledge/compiled/ |
| source_ids | JSONB | Array of raw_source UUIDs used |
| specialty | TEXT | |
| jurisdiction | TEXT | |
| status | TEXT | draft, published |
| version | INTEGER DEFAULT 1 | |
| previous_version_id | UUID | Self-ref FK for version history |
| search_vector | TSVECTOR | FTS on title + markdown content |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | |

### research_sessions

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| query | TEXT NOT NULL | |
| summary | TEXT | One-line summary of findings |
| source_ids_used | JSONB | Array of raw_source UUIDs |
| note_ids_created | JSONB | Array of compiled_note UUIDs |
| note_ids_updated | JSONB | Array of compiled_note UUIDs |
| created_at | TIMESTAMP | |

### chat_messages

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| session_id | UUID FK | References research_sessions |
| role | TEXT NOT NULL | user, assistant, system |
| content | TEXT NOT NULL | |
| metadata_json | JSONB | Citations, tool calls, approval state |
| created_at | TIMESTAMP | |

### Full-text search setup

```sql
-- Trigger to auto-update search vectors
CREATE INDEX idx_raw_sources_fts ON raw_sources USING GIN(search_vector);
CREATE INDEX idx_compiled_notes_fts ON compiled_notes USING GIN(search_vector);
```

Search vectors are updated via triggers or application-level updates when content changes.

---

## Knowledge Model on Disk

### Raw sources

```
knowledge/raw/sources/
  {uuid}--{slugified-title}.pdf       # Original PDF
  {uuid}--{slugified-title}.html      # Saved webpage
  {uuid}--{slugified-title}.txt       # Extracted text cache
```

Ground truth. Never modified after creation.

### Compiled notes

```
knowledge/compiled/
  topic-notes/{slug}.md               # Synthesis across sources
  source-notes/{slug}.md              # Summary of one raw source
  research-logs/{date}--{slug}.md     # Session record
```

All compiled markdown files use YAML frontmatter that mirrors the DB row.

### Rules
- Every file in `raw/sources/` has a corresponding `raw_sources` row
- Every file in `compiled/` has a corresponding `compiled_notes` row
- The DB is the index; the files are the content
- On note update: old content preserved as a new DB row with `previous_version_id`, file on disk overwritten
- Version history lives in the DB chain, not git (though knowledge/ can optionally be git-tracked)

---

## Source Registry

A YAML config file at `backend/sources.yaml`. Loaded at startup.

```yaml
sources:
  - name: SOGC Guidelines
    base_url: https://www.jogc.com
    type: pdf
    jurisdiction: Canada
    trust_level: high
    tags: [obstetrics, gynecology]
    requires_auth: false

  - name: UpToDate
    base_url: https://www.uptodate.com
    type: webpage
    jurisdiction: international
    trust_level: high
    tags: [clinical, guidelines]
    requires_auth: true
    auth_note: "Requires institutional login; manual upload preferred"

  - name: CPS
    base_url: https://www.pharmacists.ca
    type: webpage
    jurisdiction: Canada
    trust_level: high
    tags: [pharmacy, drugs]
    requires_auth: true

  - name: Alberta Health Services
    base_url: https://www.albertahealthservices.ca
    type: webpage
    jurisdiction: Alberta
    trust_level: high
    tags: [pathways, protocols]
    requires_auth: false

  - name: Manual Upload
    type: upload
    trust_level: user
    tags: []
```

V1 reality: most medical sources require authentication, so the primary ingest path is **manual upload** (drag-and-drop PDF/paste URL). Open-access sources can auto-fetch via httpx + trafilatura.

UI editor is v2. For v1, edit the YAML file.

---

## LLM Provider Layer

Use **litellm** directly. No custom abstraction.

```python
# services/llm.py — simplified
import litellm

async def complete(messages, model=None):
    model = model or settings.default_model
    response = await litellm.acompletion(model=model, messages=messages)
    return response.choices[0].message.content

async def stream(messages, model=None):
    model = model or settings.default_model
    response = await litellm.acompletion(model=model, messages=messages, stream=True)
    async for chunk in response:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta
```

Configuration:

```python
# config.py
class Settings(BaseSettings):
    default_model: str = "ollama/llama3.1:8b"       # Local default
    synthesis_model: str = "ollama/llama3.1:8b"      # For topic synthesis
    # Cloud override example:
    # default_model: str = "anthropic/claude-sonnet-4-20250514"
    ollama_api_base: str = "http://localhost:11434"
```

Swap models by changing a config string. litellm handles the rest.

---

## Research Workflow

When a user asks "abnormal uterine bleeding" in the chat:

### Step 1: Create session
- Create a `research_sessions` row with the query
- Return session ID to frontend, open SSE stream

### Step 2: Local search
- Full-text search `compiled_notes` and `raw_sources` via Postgres tsvector
- Rank results by relevance

### Step 3: Evaluate existing knowledge
- If a recent topic note exists (e.g. updated < 90 days ago), present it:
  *"I found an existing topic note on this. Here it is. Want me to refresh it?"*
- If found but stale, or partial matches, collect as context

### Step 4: Plan retrieval
- Send a planning prompt to the LLM with existing context:
  *"Given this query and these existing notes, do we need to fetch new sources?"*
- Stream the reasoning to the user

### Step 5: Retrieve (if needed)
- For URLs: fetch with httpx, extract with trafilatura, save to `knowledge/raw/sources/`
- For auth-required sources: prompt user to upload
  *"I need the UpToDate article on AUB. Can you upload the PDF?"*
- Create `raw_sources` rows for each new source

### Step 6: Parse
- Extract text: PyMuPDF for PDFs, trafilatura for HTML
- Save extracted text as `.txt` alongside the raw file
- Update `parser_status` to `parsed`

### Step 7: Synthesize
- Build prompt with:
  - System prompt (clinical knowledge assistant, cite sources)
  - Relevant existing topic note content
  - Parsed text from raw sources (directly in context — the Karpathy insight)
  - The user's question
- Stream response via SSE with inline citations: `[Source: SOGC 2023, p.12]`

### Step 8: Approval gate
- After streaming, propose:
  *"I can save this as a topic note on 'Abnormal Uterine Bleeding' and create source notes for the 2 new sources. Approve?"*
- Three options: **Save** / **Edit first** / **Discard**

### Step 9: Save (on approval)
- Generate topic note markdown via structured prompt
- Generate source note markdown for each new raw source
- Write files to `knowledge/compiled/`
- Create `compiled_notes` rows
- Update `research_sessions` with note IDs

### Step 10: Log
- Generate research log markdown file
- Record: query, sources used, notes created/updated, open questions

---

## Note Schemas

### Topic note

```markdown
---
id: "uuid"
title: "Abnormal Uterine Bleeding"
note_type: topic_note
specialty: gynecology
jurisdiction: Canada
sources:
  - id: "uuid-1"
    title: "SOGC Clinical Practice Guideline No. 292"
  - id: "uuid-2"
    title: "UpToDate: AUB in nonpregnant reproductive-age females"
status: published
version: 1
created: 2026-04-06
updated: 2026-04-06
---

# Abnormal Uterine Bleeding

## Overview
Brief 2-3 sentence summary.

## Key Points
- Point 1 [SOGC 2023, p.3]
- Point 2 [UpToDate, "Evaluation" section]

## Classification
PALM-COEIN classification... [SOGC 2023, p.5]

## Workup
- History: ...
- Physical: ...
- Investigations: ... [SOGC 2023, p.8]

## Management
...

## Referral Thresholds
...

## Red Flags
...

## Sources
- SOGC Clinical Practice Guideline No. 292 (2023)
- UpToDate: AUB (retrieved 2026-04-06)

## Open Questions
- [ ] Check for 2025/2026 SOGC update
```

### Source note

```markdown
---
id: "uuid"
title: "SOGC Guideline No. 292 — Source Note"
note_type: source_note
raw_source_id: "uuid-1"
source_name: SOGC
source_type: pdf
jurisdiction: Canada
published_date: "2023"
retrieved: 2026-04-06
---

# SOGC Clinical Practice Guideline No. 292: AUB

## Summary
One-paragraph summary.

## Key Recommendations
- Recommendation 1 (Grade A)
- Recommendation 2 (Grade B)

## Important Thresholds/Numbers
- Endometrial biopsy if age ≥45 or risk factors

## Scope and Applicability
Who this applies to, limitations.

## Raw Source
knowledge/raw/sources/uuid-1--sogc-aub-guideline.pdf
```

### Research log

```markdown
---
session_id: "uuid"
query: "abnormal uterine bleeding"
date: 2026-04-06
---

# Research Log: Abnormal Uterine Bleeding

**Query:** abnormal uterine bleeding
**Date:** 2026-04-06

## Sources Used
- SOGC Guideline No. 292 (existing)
- UpToDate AUB article (newly fetched)

## Notes Created
- Topic note: Abnormal Uterine Bleeding
- Source note: SOGC Guideline 292
- Source note: UpToDate AUB

## Open Questions
- Check for 2025/2026 guideline updates
```

---

## Approval Gates

Chat-inline only. No separate queue or workflow system.

After synthesis, the assistant sends a structured message:

```json
{
  "role": "assistant",
  "type": "approval_request",
  "content": "I've drafted a topic note and 2 source notes. Save them?",
  "preview": {
    "topic_note": { "title": "...", "preview": "first 500 chars..." },
    "source_notes": [{ "title": "..." }]
  },
  "actions": ["approve", "edit_first", "discard"]
}
```

Frontend renders as a card with three buttons:
- **Save** — writes notes to disk and DB
- **Edit first** — opens markdown in editable text area, then save
- **Discard** — logs the session but saves no notes

For **updates to existing notes**: show a diff (old vs proposed), same three buttons. Old version preserved via `previous_version_id` chain.

---

## Build Order

### Phase 1: Foundation
Build the skeleton that runs end-to-end.

- [ ] Docker Compose: Postgres container + volume
- [ ] Backend skeleton: FastAPI app, config, SQLModel, models, table creation
- [ ] litellm integration: verify Ollama connectivity
- [ ] Knowledge directory structure on disk
- [ ] `POST /api/chat`: accepts query, calls LLM, returns SSE stream
- [ ] Frontend skeleton: Next.js + shadcn, chat page, renders streamed response

**Milestone:** Working chat app that talks to Ollama.

### Phase 2: Source Ingestion
Get documents into the system.

- [ ] `POST /api/sources/upload`: accepts PDF, saves to raw/, creates DB row
- [ ] `POST /api/sources/fetch`: accepts URL, fetches + extracts, saves
- [ ] Parsing service: PyMuPDF (PDF) + trafilatura (HTML) → extracted text
- [ ] `GET /api/sources`: list all raw sources
- [ ] Frontend: file upload dropzone + URL input

**Milestone:** Can upload PDFs and save web pages.

### Phase 3: Research Workflow
The core product value.

- [ ] Postgres FTS setup: tsvector columns, GIN indexes, update triggers
- [ ] Local search service: queries FTS, returns ranked results
- [ ] Research orchestrator: the 10-step workflow (build incrementally)
  - Local search + LLM synthesis
  - Source context injection
  - "Should I fetch more?" planning step
- [ ] Prompt templates: system, synthesis, topic note, source note
- [ ] Note writing service: generate markdown + frontmatter, write to disk, create DB rows
- [ ] Update chat endpoint to use the orchestrator

**Milestone:** Ask a question → searches local notes → injects sources → synthesizes answer → generates notes.

### Phase 4: Approval & Polish
Make it feel like a product.

- [ ] Approval flow: structured message, frontend card, save/edit/discard
- [ ] Topic browser: list all topic notes with search
- [ ] Note viewer: render markdown in browser (react-markdown)
- [ ] Session history: list past sessions, view chat log
- [ ] Refresh flow: detect existing topic, show diff, approval gate
- [ ] Research log generation
- [ ] Source registry loading from YAML

**Milestone:** Full MVP loop working end-to-end.

### Phase 5: Quality of Life
Iterate from actual usage.

- Better search tuning (tsvector weights, ranking)
- Note editing in the UI
- Source viewer (PDF in browser, HTML snapshot)
- Dark mode, mobile-responsive
- Export topic note as PDF
- Concept notes, index notes (when scale demands it)
- Health checks / linting

---

## Verification

How to test the MVP end-to-end:

1. `docker compose up` starts Postgres + backend + frontend
2. Navigate to `localhost:3000`, see the chat interface
3. Upload a PDF via the sources page → verify it appears in `knowledge/raw/sources/`
4. Ask a clinical question in chat → verify SSE streaming works
5. Verify the system searches local notes (Postgres FTS)
6. Verify source text is injected into the LLM context
7. Verify the approval prompt appears after synthesis
8. Approve → verify topic note + source notes written to `knowledge/compiled/`
9. Browse topics page → see the saved topic note
10. Re-ask the same topic → verify it finds the existing note and offers to refresh
11. Check research log was generated in `knowledge/compiled/research-logs/`
