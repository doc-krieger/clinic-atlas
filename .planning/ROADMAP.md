# Roadmap: Clinic Atlas

## Overview

Clinic Atlas is built bottom-up: storage and search infrastructure first, then source ingestion to populate the knowledge base, then the LLM service and SSE plumbing that everything streams over, then the research orchestrator that ties it all together, then the approval gate that makes knowledge accumulation trustworthy, then the read-only navigation views, and finally on-demand topic refresh — the feature that most visibly demonstrates the "every query compounds the knowledge base" thesis.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Foundation** - Docker Compose stack, Postgres schema with FTS and medical synonym dictionary, disk layout, trusted source registry
- [ ] **Phase 2: Source Ingestion** - PDF upload and URL fetch with quality gates (scanned PDF detection, gated content detection)
- [ ] **Phase 3: LLM Service and Chat** - litellm wrapper, SSE streaming with heartbeat and error handling, basic chat UI
- [ ] **Phase 4: Research Orchestrator** - 10-step async workflow, verbatim-quote synthesis prompts, token budget, SearXNG web search, note generation
- [ ] **Phase 5: Approval Gate and KB Persistence** - Split-workflow approval gate, atomic disk writes, Postgres sync, note storage
- [ ] **Phase 6: Navigation** - Topic browser with FTS search, topic detail view, session history with chat replay
- [ ] **Phase 7: Topic Refresh** - On-demand re-research of existing topics with diff view and approval

## Phase Details

### Phase 1: Foundation
**Goal**: The full development stack runs locally and the knowledge base schema is ready to index content
**Depends on**: Nothing (first phase)
**Requirements**: KBSE-01, KBSE-02, SRCI-04
**Success Criteria** (what must be TRUE):
  1. `docker compose up` starts Postgres 17, FastAPI, Next.js, Ollama, and SearXNG with no errors
  2. Postgres schema exists with tsvector columns and GIN indexes for full-text search
  3. A search for "HTN" returns results containing "hypertension" (medical synonym dictionary active)
  4. The trusted source registry loads from YAML at startup with no errors
  5. Disk layout directories exist and the reindex endpoint responds 200
**Plans:** 3 plans

Plans:
- [ ] 01-01-PLAN.md — Docker Compose stack + Postgres schema with FTS and medical thesaurus + Alembic migrations
- [ ] 01-02-PLAN.md — Source registry, search/health/reindex endpoints, and backend test suite
- [ ] 01-03-PLAN.md — Next.js 15 frontend skeleton with shadcn/ui and chat layout

### Phase 2: Source Ingestion
**Goal**: The physician can add clinical source material to the knowledge base via PDF upload or URL, with quality guaranteed before indexing
**Depends on**: Phase 1
**Requirements**: SRCI-01, SRCI-02, SRCI-03, SRCI-05
**Success Criteria** (what must be TRUE):
  1. User can upload a PDF and see it appear as an indexed raw source
  2. User can submit a URL and see it fetched, extracted, and indexed as a raw source
  3. Uploading a scanned/image-only PDF surfaces a visible flag rather than silently indexing garbage text
  4. SearXNG can be queried for a trusted source domain and returns results
**Plans**: TBD

### Phase 3: LLM Service and Chat
**Goal**: The physician can send a message and receive a streamed LLM response in real time, with streaming errors surfaced rather than swallowed
**Depends on**: Phase 2
**Requirements**: CHAT-01, CHAT-02, CHAT-04
**Success Criteria** (what must be TRUE):
  1. User can type a message in the chat interface and receive a streaming response token by token
  2. Switching LLM provider in config (Ollama / Anthropic / OpenAI) takes effect on next request with no code changes
  3. When a streaming error occurs (e.g. Ollama disconnects mid-stream), the UI displays an error message rather than hanging or silently truncating
  4. Ollama model stays loaded between requests (no 20-60 second cold-start delays)
**Plans**: TBD
**UI hint**: yes

### Phase 4: Research Orchestrator
**Goal**: A user query triggers the full 10-step research workflow and the physician sees real-time progress as the system searches, fetches, and synthesizes cited notes
**Depends on**: Phase 3
**Requirements**: RSRW-01, RSRW-02, RSRW-03, SRCI-05, NOTE-01, NOTE-02, NOTE-03, CHAT-03
**Success Criteria** (what must be TRUE):
  1. Submitting a clinical question triggers visible step-by-step progress (local search → evaluate → plan → fetch → parse → synthesize) in the UI
  2. Every claim in the synthesized response includes an inline citation traceable to a source document
  3. When source context would exceed the model's context window, the user is notified which sources were omitted rather than receiving silently degraded output
  4. The system generates a source note, a topic note with inline citations, and a research log for the session
  5. Web search results are scoped to domains in the trusted source registry
**Plans**: TBD

### Phase 5: Approval Gate and KB Persistence
**Goal**: The physician controls what enters the knowledge base — synthesized notes are held for review and only saved after explicit approval
**Depends on**: Phase 4
**Requirements**: APPR-01, APPR-02, KBSE-03, KBSE-04
**Success Criteria** (what must be TRUE):
  1. After synthesis completes, the user sees an approval widget with save / edit / discard options before any note is written
  2. User can edit note content inline before saving
  3. Approved notes appear as markdown files on disk with correct YAML frontmatter
  4. Postgres metadata matches disk files after save; the reindex endpoint can restore sync after manual file changes
**Plans**: TBD

### Phase 6: Navigation
**Goal**: The physician can browse, search, and read the accumulated knowledge base and revisit past research sessions
**Depends on**: Phase 5
**Requirements**: NAVI-01, NAVI-02, NAVI-03
**Success Criteria** (what must be TRUE):
  1. User can browse all topic notes and filter by full-text search query
  2. User can open a topic note and read it rendered as formatted markdown with source citations visible
  3. User can view a list of past research sessions and replay the chat log for any session
**Plans**: TBD
**UI hint**: yes

### Phase 7: Topic Refresh
**Goal**: The physician can re-research any existing topic and see what changed before deciding whether to update the knowledge base
**Depends on**: Phase 6
**Requirements**: REFR-01, REFR-02, APPR-03
**Success Criteria** (what must be TRUE):
  1. User can trigger a re-research of an existing topic from the topic detail page
  2. After re-research completes, user sees a diff of the old note versus the proposed new content before the approval gate
  3. Approving a refresh updates the note on disk and in Postgres with an updated timestamp
**Plans**: TBD
**UI hint**: yes

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6 → 7

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation | 0/3 | Planning complete | - |
| 2. Source Ingestion | 0/? | Not started | - |
| 3. LLM Service and Chat | 0/? | Not started | - |
| 4. Research Orchestrator | 0/? | Not started | - |
| 5. Approval Gate and KB Persistence | 0/? | Not started | - |
| 6. Navigation | 0/? | Not started | - |
| 7. Topic Refresh | 0/? | Not started | - |
