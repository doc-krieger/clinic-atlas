# Architecture Research

**Domain:** Chat-first clinical knowledge assistant with source ingestion and compounding knowledge base
**Researched:** 2026-04-06
**Confidence:** HIGH

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Browser (Next.js 14+)                     │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────┐  │
│  │  Chat UI     │  │ Topic Browser│  │  Source Ingestion UI  │  │
│  │ (SSE stream) │  │  (search)    │  │  (PDF upload / URL)   │  │
│  └──────┬───────┘  └──────┬───────┘  └───────────┬───────────┘  │
└─────────┼─────────────────┼──────────────────────┼──────────────┘
          │ SSE stream       │ REST                 │ multipart POST
          ▼                 ▼                      ▼
┌─────────────────────────────────────────────────────────────────┐
│              Next.js Route Handlers (API proxy layer)            │
│  /api/chat/stream   /api/topics/**   /api/sources/ingest         │
│  (proxy SSE, set no-buffer headers, forward auth context)        │
└─────────────────────────────┬───────────────────────────────────┘
                              │ HTTP / SSE
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Backend (port 8000)                    │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              Research Orchestrator                        │    │
│  │  search → evaluate → plan → fetch → parse → synthesize   │    │
│  │  → [approval gate SSE event] → save → log                │    │
│  └─────────────────┬───────────────────────────────────────┘    │
│                    │                                              │
│  ┌─────────────────┴─────────────────────────────────────────┐  │
│  │                   Service Layer                             │  │
│  │  ┌─────────────┐ ┌────────────┐ ┌──────────────────────┐  │  │
│  │  │ LLM Service │ │ FTS Service│ │  Ingestion Service   │  │  │
│  │  │ (litellm)   │ │ (Postgres  │ │  (PyMuPDF/trafilatura│  │  │
│  │  │             │ │  tsvector) │ │   + httpx)           │  │  │
│  │  └──────┬──────┘ └─────┬──────┘ └──────────┬───────────┘  │  │
│  │         │              │                    │               │  │
│  └─────────┴──────────────┴────────────────────┴───────────────┘  │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │              Storage Layer                                   │ │
│  │  ┌───────────────────┐      ┌──────────────────────────┐   │ │
│  │  │  knowledge/ (disk)│      │  PostgreSQL               │   │ │
│  │  │  sources/         │      │  - notes (metadata + FTS) │   │ │
│  │  │  topics/          │◄────►│  - sources (registry)     │   │ │
│  │  │  logs/            │      │  - sessions (history)     │   │ │
│  │  └───────────────────┘      └──────────────────────────┘   │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
          │                     │
          ▼                     ▼
   Ollama (local)         Anthropic / OpenAI
   (via litellm)          (via litellm, cloud fallback)
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| Chat UI | Stream display, approval gate rendering, session history | Next.js client component, EventSource API |
| Topic Browser | Search, browse, view/refresh topics | Next.js server + client components |
| Source Ingestion UI | PDF upload form, URL fetch trigger | React form, multipart POST |
| Next.js Route Handlers | SSE proxy, REST proxy, header management | App Router route.ts files |
| Research Orchestrator | 10-step workflow, step-by-step SSE emission, approval gate | Python async generator |
| LLM Service | Provider-abstracted LLM calls | litellm wrapper |
| FTS Service | tsvector search, note retrieval | SQLModel + raw SQL for GIN queries |
| Ingestion Service | PDF parse, HTML extract, metadata extraction | PyMuPDF + trafilatura |
| Storage Layer | Dual storage: disk for content, Postgres for index | SQLModel models + pathlib file I/O |

## Recommended Project Structure

```
clinic-atlas/
├── frontend/                    # Next.js 14+ App Router
│   ├── app/
│   │   ├── (chat)/
│   │   │   └── page.tsx         # Chat interface
│   │   ├── topics/
│   │   │   ├── page.tsx         # Topic browser
│   │   │   └── [slug]/page.tsx  # Topic detail
│   │   ├── sources/
│   │   │   └── page.tsx         # Source ingestion
│   │   └── api/
│   │       ├── chat/
│   │       │   └── stream/route.ts   # SSE proxy to FastAPI
│   │       ├── topics/
│   │       │   └── [...slug]/route.ts
│   │       └── sources/
│   │           └── ingest/route.ts
│   ├── components/
│   │   ├── chat/
│   │   │   ├── ChatWindow.tsx        # Main chat container
│   │   │   ├── MessageList.tsx       # Scrollable history
│   │   │   ├── ApprovalGate.tsx      # Save/Edit/Discard widget
│   │   │   └── StepProgress.tsx      # Workflow step indicator
│   │   ├── topics/
│   │   └── sources/
│   └── lib/
│       └── sse.ts                    # EventSource hook
│
├── backend/                     # FastAPI (Python)
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   │   ├── chat.py          # /chat/stream SSE endpoint
│   │   │   ├── topics.py        # CRUD + search
│   │   │   └── sources.py       # Upload + ingest
│   │   ├── services/
│   │   │   ├── orchestrator.py  # Research workflow (async gen)
│   │   │   ├── llm.py           # litellm wrapper
│   │   │   ├── search.py        # FTS against Postgres
│   │   │   ├── ingestion.py     # PDF + HTML parsing
│   │   │   └── web_fetch.py     # httpx + trafilatura
│   │   ├── models/
│   │   │   ├── note.py          # SQLModel: source/topic notes
│   │   │   ├── session.py       # SQLModel: research sessions
│   │   │   └── source.py        # SQLModel: source registry
│   │   ├── storage/
│   │   │   └── disk.py          # knowledge/ file I/O
│   │   └── config/
│   │       └── sources.yaml     # Trusted source registry
│   └── knowledge/               # Disk knowledge base
│       ├── sources/             # One .md per raw source
│       ├── topics/              # One .md per synthesized topic
│       └── logs/                # One .md per research session
│
└── docker-compose.yml
```

### Structure Rationale

- **api/ vs services/:** Route handlers own HTTP concerns (request parsing, SSE framing). Services own business logic. This boundary makes services testable without HTTP.
- **storage/disk.py:** Centralizing all file I/O into one module isolates path concerns and makes future refactoring (e.g., adding git commits) a single-file change.
- **knowledge/ sibling to backend/:** Knowledge base lives outside app code so it can be inspected, searched with grep, and optionally git-tracked independently of the application.

## Architectural Patterns

### Pattern 1: Async Generator as Research Workflow

**What:** The orchestrator is a single `async def` Python generator that `yield`s typed event objects at each workflow step. The FastAPI SSE endpoint iterates this generator and converts each event to an SSE message. This makes the entire 10-step workflow a flat, readable sequence rather than a callback chain.

**When to use:** Any multi-step process where progress must stream to the client in real time, without a task queue.

**Trade-offs:** Simple, debuggable, no infrastructure overhead. However, because it runs in the request's event loop, a very slow step (e.g., a 30s LLM call) blocks that coroutine — acceptable for single-user, unacceptable for concurrent users.

**Example:**
```python
# services/orchestrator.py
async def research_workflow(query: str) -> AsyncGenerator[WorkflowEvent, None]:
    yield WorkflowEvent(step="search", status="running")
    existing = await search_service.fts(query)
    yield WorkflowEvent(step="search", status="done", data=existing)

    yield WorkflowEvent(step="evaluate", status="running")
    evaluation = await llm_service.evaluate(query, existing)
    yield WorkflowEvent(step="evaluate", status="done", data=evaluation)

    # ... more steps ...

    yield WorkflowEvent(step="approval", status="pending", data=draft_notes)
    # Generator pauses — client shows approval gate.
    # Approval response arrives via separate POST endpoint.
    # Continuation via asyncio.Event or queue handoff.

# api/chat.py
@router.get("/stream", response_class=EventSourceResponse)
async def chat_stream(query: str) -> AsyncIterable[ServerSentEvent]:
    async for event in orchestrator.research_workflow(query):
        yield ServerSentEvent(data=event.model_dump_json(), event=event.step)
```

### Pattern 2: Approval Gate via SSE + Separate POST

**What:** The approval gate is not implemented as a generator pause (generators cannot resume from external input). Instead: (1) the orchestrator emits an `approval_pending` SSE event with draft notes, then exits; (2) the client renders the approval widget; (3) the user's approval/edit/discard arrives as a separate POST to `/chat/approve/{session_id}`; (4) the save step executes and a final SSE event confirms completion.

**When to use:** Any human-in-the-loop checkpoint in a streaming workflow.

**Trade-offs:** Requires session state in Postgres or in-memory dict to hold draft notes between the stream end and approval POST. Simple for single-user; for multi-user would need session isolation.

**Example:**
```python
# State held server-side between stream and approval
pending_approvals: dict[str, DraftNotes] = {}

@router.get("/stream")
async def chat_stream(query: str, session_id: str):
    async for event in orchestrator.run_until_approval(query, session_id):
        yield ServerSentEvent(...)
    # Stream ends. Draft is in pending_approvals[session_id].

@router.post("/approve/{session_id}")
async def approve(session_id: str, action: ApprovalAction):
    draft = pending_approvals.pop(session_id)
    if action == "save":
        await storage.save_notes(draft)
    return {"status": "done"}
```

### Pattern 3: Dual Storage (Disk + Postgres Index)

**What:** Markdown files on disk are the authoritative source of content. Postgres holds metadata, FTS vectors, and foreign keys — but not raw content. Every write operation is atomic: write file first, then upsert Postgres row. Every delete removes both.

**When to use:** When content must be human-readable, git-trackable, and portable, but also requires fast structured search.

**Trade-offs:** Two writes per save creates a small consistency window. At single-user scale this is inconsequential. Postgres is easily rebuilt from disk if it drifts. Do not store content in Postgres — it creates a sync problem.

**Example:**
```python
# storage/disk.py
async def save_topic_note(note: TopicNote) -> Path:
    path = TOPICS_DIR / f"{note.slug}.md"
    path.write_text(note.to_markdown())  # YAML frontmatter + body
    return path

# services/notes.py
async def save_and_index(note: TopicNote):
    path = await disk.save_topic_note(note)          # 1. Write file
    await db.upsert_note_index(note, str(path))      # 2. Upsert Postgres
```

### Pattern 4: SSE Proxy in Next.js Route Handler

**What:** The Next.js route handler acts as a thin proxy: it fetches from FastAPI using `fetch()` with `cache: 'no-store'`, then pipes the response body as a `ReadableStream` directly into the `Response`. Critical headers prevent buffering at every layer.

**When to use:** When backend and frontend are on different ports (Docker Compose) and you need CORS-free SSE delivery to the browser.

**Trade-offs:** Adds one network hop. For local self-hosted use this is negligible. The alternative — browser connecting directly to FastAPI — works but exposes the backend port and bypasses the Next.js API layer.

**Example:**
```typescript
// app/api/chat/stream/route.ts
export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const upstream = await fetch(
    `http://backend:8000/chat/stream?${searchParams}`,
    { cache: 'no-store' }
  );

  return new Response(upstream.body, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache, no-transform',
      'Connection': 'keep-alive',
      'X-Accel-Buffering': 'no',   // Disables nginx buffering
    },
  });
}
```

## Data Flow

### Research Workflow Flow (primary path)

```
User types query
    ↓
ChatWindow.tsx → POST /api/chat/stream (Next.js route)
    ↓
Next.js proxy → GET /chat/stream (FastAPI SSE)
    ↓
orchestrator.research_workflow(query) async generator:
    step 1: FTS search → Postgres tsvector query
    step 2: LLM evaluates existing coverage
    step 3: LLM plans what sources to fetch
    step 4: httpx fetches URLs (trusted domains only)
    step 5: trafilatura/PyMuPDF parses content
    step 6: LLM synthesizes draft notes
    step 7: approval_pending event → stream ends
    ↓
Client receives SSE events → renders StepProgress + ApprovalGate
    ↓
User clicks Save/Edit/Discard → POST /api/chat/approve/{session_id}
    ↓
step 8: save notes to disk + index in Postgres
step 9: save research log to disk + Postgres
step 10: return completion event (polling or new SSE stream)
```

### Source Ingestion Flow

```
User uploads PDF or enters URL
    ↓
POST /api/sources/ingest (Next.js) → POST /sources/ingest (FastAPI)
    ↓
ingestion_service:
    PDF: PyMuPDF → extract text + metadata
    URL: httpx fetch → trafilatura extract
    ↓
Write source markdown to knowledge/sources/{slug}.md
Upsert source_notes row in Postgres (with tsvector)
    ↓
Return ingestion summary to client
```

### FTS Query Flow

```
User searches topics
    ↓
GET /api/topics?q=... → GET /topics?q=... (FastAPI)
    ↓
search_service.fts(query):
    SELECT id, title, slug, excerpt,
           ts_rank(search_vector, plainto_tsquery('english', $1)) AS rank
    FROM notes
    WHERE search_vector @@ plainto_tsquery('english', $1)
    ORDER BY rank DESC LIMIT 20
    ↓
Return ranked results → Topic Browser renders list
```

### SSE Event Stream Structure

```
event: step_start
data: {"step": "search", "label": "Searching knowledge base..."}

event: step_done
data: {"step": "search", "result": {"found": 3, "top_match": "Neonatal jaundice"}}

event: step_start
data: {"step": "fetch", "label": "Fetching 2 sources..."}

... more steps ...

event: approval_pending
data: {"session_id": "abc123", "draft": {"source_notes": [...], "topic_note": {...}}}

[stream closes — client shows approval gate]
```

## Scaling Considerations

This is a single-user self-hosted tool. Scaling considerations are included for completeness but are not a current concern.

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 1 user (current target) | Single process FastAPI is sufficient. No workers needed. In-memory dicts for session state are safe. |
| 2-10 users | Replace in-memory pending_approvals dict with Postgres session table. Add connection pooling (asyncpg). |
| 10+ users | Introduce task queue (Celery + Redis) for research workflows. SSE streams from task status rather than inline. This is the "out of scope" Celery path deferred by PROJECT.md. |

### First bottleneck (if ever reached)

The in-memory `pending_approvals` dict is lost on restart. For single-user this is acceptable (rare) but for any persistence requirement, move session state to Postgres immediately.

The second bottleneck is concurrent LLM calls — litellm with Ollama is effectively serialized by the local GPU. This is a hardware constraint, not an architectural one.

## Anti-Patterns

### Anti-Pattern 1: Buffering the SSE stream in Next.js

**What people do:** Return `new Response(await upstream.json(), ...)` — `await`ing the upstream response before creating the Response.

**Why it's wrong:** Next.js buffers the entire response body before sending anything to the client. The user sees no progress until the entire research workflow completes — defeating the purpose of SSE.

**Do this instead:** Pipe `upstream.body` (a `ReadableStream`) directly into the Response constructor without awaiting. Set `Cache-Control: no-cache, no-transform` and `X-Accel-Buffering: no` headers.

### Anti-Pattern 2: Storing Note Content in Postgres

**What people do:** Put the full markdown content into a Postgres `TEXT` column alongside the metadata.

**Why it's wrong:** Creates a sync problem — disk and DB can drift. Postgres TEXT columns are not the canonical source for large documents. The whole value of the disk-first pattern is portability and inspectability.

**Do this instead:** Store only the file path (relative to knowledge/) and a content hash in Postgres. Read file content from disk when needed. Rebuild the Postgres index from disk on startup if needed.

### Anti-Pattern 3: Resuming a Generator for the Approval Gate

**What people do:** Try to `yield`-pause a Python async generator and resume it when the user approves, using `asend()` from another coroutine.

**Why it's wrong:** The generator lives in the context of an HTTP request. That request's connection closes when the approval SSE event is emitted. There is no mechanism to resume it from a separate POST request without shared mutable state and significant complexity.

**Do this instead:** Split the workflow at the approval boundary. The stream runs to `approval_pending` and exits cleanly. A separate POST endpoint handles continuation, reading draft state from Postgres or a short-lived in-memory dict keyed by session ID.

### Anti-Pattern 4: Running Blocking I/O in the FastAPI Event Loop

**What people do:** Call `PyMuPDF` or `trafilatura` parsing synchronously inside an `async def` endpoint.

**Why it's wrong:** PDF parsing and HTML extraction are CPU/IO-bound. Running them synchronously in an async endpoint blocks the event loop and stalls all other concurrent requests (even the single-user ping endpoint).

**Do this instead:** Wrap blocking calls with `asyncio.to_thread()` (Python 3.9+):
```python
text = await asyncio.to_thread(pymupdf_extract, file_bytes)
```

### Anti-Pattern 5: Trusted Domain Scoping via URL Filtering Alone

**What people do:** Accept any URL from the user but filter results by domain after fetching.

**Why it's wrong:** The fetch itself may be undesirable (hitting untrusted servers, logging your queries). Domain scoping must happen before the HTTP request, not after.

**Do this instead:** The trusted source registry (YAML) defines allowed domains. Web search queries are scoped to `site:domain1.com OR site:domain2.com`. Manual URL ingestion validates the hostname against the registry before fetching. Reject out-of-scope URLs at the service layer with a clear error.

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| Ollama (local) | litellm → `ollama/` prefix, base_url=localhost:11434 | Default. No API key. Requires Ollama running on host. |
| Anthropic | litellm → `anthropic/claude-*`, ANTHROPIC_API_KEY env var | Cloud fallback. Clinical data leaves local machine — user must opt in explicitly. |
| OpenAI | litellm → `openai/gpt-*`, OPENAI_API_KEY env var | Cloud fallback, same privacy caveat. |
| Trusted web sources | httpx async GET, domain validated against sources.yaml | trafilatura for HTML extraction. Respects robots.txt delays. |
| Web search (scoped) | httpx → search API or SerpAPI scoped to trusted domains | Domain scope: `site:uptodate.com OR site:cps.ca ...` |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| Next.js ↔ FastAPI | HTTP REST + SSE (no shared memory, no direct DB access from frontend) | Frontend never touches Postgres directly. All data flows through FastAPI. |
| Orchestrator ↔ LLM Service | Direct async function call | litellm is a library, not a service — no network hop. |
| Orchestrator ↔ FTS Service | Direct async function call | Same process, no IPC needed. |
| FastAPI ↔ Postgres | asyncpg via SQLModel | Connection pool managed by SQLModel/SQLAlchemy async engine. |
| FastAPI ↔ Disk | Direct pathlib file I/O in `storage/disk.py` | Synchronous — wrap with `asyncio.to_thread()` for large files. |

## Suggested Build Order

The architecture has clear dependency layers. Build bottom-up:

1. **Storage foundation** — Postgres schema (SQLModel models), disk layout, FTS indexes. Nothing else works without this.

2. **Ingestion service** — PDF + HTML parsing, source note writing. Lets you populate the knowledge base for testing before any chat UI exists.

3. **FTS service** — tsvector indexing and query. Validates that ingested content is searchable. Required by the orchestrator's search step.

4. **LLM service** — litellm wrapper with Ollama default. Validates provider config in isolation before plugging into orchestrator.

5. **Research orchestrator** — The core 10-step workflow as an async generator. Test with direct Python calls before wiring SSE.

6. **FastAPI SSE endpoint** — Wire orchestrator to HTTP. Validate SSE framing, event structure, and heartbeat.

7. **Next.js SSE proxy + Chat UI** — Build on a working backend SSE stream. Handle buffering, reconnect logic, and step progress display.

8. **Approval gate** — Implement `approval_pending` event, client-side widget, and POST `/approve` endpoint. Requires working SSE and orchestrator.

9. **Topic browser + session history** — Read-only views over the Postgres index. Straightforward once data exists.

10. **On-demand refresh** — Diff existing topic note against fresh research. Builds on all prior layers.

## Sources

- FastAPI SSE official docs: https://fastapi.tiangolo.com/tutorial/server-sent-events/
- Next.js SSE buffering discussion: https://github.com/vercel/next.js/discussions/48427
- Streaming APIs with FastAPI and Next.js: https://sahansera.dev/streaming-apis-python-nextjs-part1/
- Fixing slow SSE in Next.js: https://medium.com/@oyetoketoby80/fixing-slow-sse-server-sent-events-streaming-in-next-js-and-vercel-99f42fbdb996
- Karpathy LLM Wiki architecture: https://venturebare.com/data/karpathy-shares-llm-knowledge-base-architecture-that-bypasses-rag-with-an
- Knowledge Engine (dual-layer pattern): https://github.com/tashisleepy/knowledge-engine
- Pal compounding knowledge base: https://github.com/agno-agi/pal
- FastAPI async generator SSE workflows: https://dev.to/zachary62/build-an-llm-web-app-in-python-from-scratch-part-4-fastapi-background-tasks-sse-21g4
- Trafilatura documentation: https://trafilatura.readthedocs.io/

---
*Architecture research for: clinical knowledge assistant with source ingestion and compounding knowledge base*
*Researched: 2026-04-06*
