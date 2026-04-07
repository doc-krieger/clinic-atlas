# Pitfalls Research

**Domain:** Clinical knowledge assistant — chat-first, self-hosted, FTS + markdown + LLM pipeline
**Researched:** 2026-04-06
**Confidence:** HIGH (most pitfalls verified against official docs, GitHub issues, peer-reviewed sources)

---

## Critical Pitfalls

### Pitfall 1: LLM Fabricates Citations That Were Never in the Sources

**What goes wrong:**
The LLM generates a synthesis note with inline citations (e.g., `[UpToDate, 2024]`) that do not accurately reflect what the source said, or invents citations entirely. Studies show 50–90% of LLM-generated statements are not fully supported by the sources they cite, even when those sources are in context. With Ollama local models, the problem is worse because smaller models hallucinate at higher rates on synthesis tasks.

**Why it happens:**
LLMs are trained to produce fluent, authoritative text. When asked to synthesize and cite, they confabulate plausible-sounding attributions. The model "knows" the correct structure of a citation but fills it with whatever content sounds right — not necessarily what the actual document said. This is compounded by the "lost-in-the-middle" effect where key facts in the middle of a long context are attended to poorly.

**How to avoid:**
- Design the synthesis prompt to require verbatim quoted evidence before each claim, not post-hoc citation
- Never ask the model to both synthesize AND attribute in a single pass — do retrieval first, quote extraction second, synthesis third
- Show the user the source chunks that grounded each section of the note (provenance display, not just citation labels)
- Add a citation verification step: after generating a note, re-query each cited claim against the source document to check support
- For local Ollama models, use a larger model (≥7B, preferably ≥13B) for synthesis tasks — smaller models hallucinate more on attribution

**Warning signs:**
- Citations in generated notes reference section numbers or page numbers that don't exist in the source file
- The same "citation" appears in multiple notes with slightly different wording
- Notes include confident claims about drug dosages or diagnostic criteria that weren't in any ingested source for that session

**Phase to address:**
Research workflow phase (synthesis step) — the prompt architecture and verification step must be designed here, not retrofitted later.

---

### Pitfall 2: Scanned PDFs Silently Produce Garbage Text

**What goes wrong:**
PyMuPDF extracts text from scanned PDFs (image-based, not text-layer PDFs) and returns garbled output — misspellings, merged words, missing spaces, or near-empty strings. This gets indexed in Postgres, stored as a source note, and the system treats it as valid content. UpToDate PDFs exported via print-to-PDF and institutional guideline PDFs (especially older SOGC/ACOG documents) are often scanned.

**Why it happens:**
PyMuPDF has no built-in OCR. It extracts the text layer directly. Scanned PDFs have no text layer — only an image of the page. PyMuPDF returns whatever little machine-readable text exists (headers, footers from software, invisible metadata) which is near-zero or corrupted.

**How to avoid:**
- After PyMuPDF extraction, check the text-to-page-area ratio: if a multi-page PDF yields fewer than 100 words per page, flag it as likely scanned
- Implement a "low text confidence" warning shown to the user before the source is processed further
- Optionally integrate Tesseract OCR (via pytesseract or PyMuPDF's optional OCR path with Tesseract) as a fallback for flagged PDFs
- Log extraction metadata (page count, word count, character count) for every PDF ingested — this makes diagnosing silent failures possible

**Warning signs:**
- Source notes generated from PDFs contain mostly numbers, punctuation, or single characters
- FTS queries that should match a recently uploaded PDF return no results
- The synthesis step produces very short or vague outputs because source context was essentially empty

**Phase to address:**
Source ingestion phase — the extraction quality check must be implemented before the search index or LLM pipeline is built on top of it.

---

### Pitfall 3: SSE Streaming Errors Are Silently Swallowed by litellm + Ollama

**What goes wrong:**
There is a confirmed bug in litellm (GitHub issue #8868) where async streaming errors from Ollama are swallowed — the exception is not raised, the stream just stops. The user sees the response truncate mid-sentence with no error message. The sync litellm path raises correctly, but async (which is what FastAPI uses) does not.

**Why it happens:**
litellm's async generator wraps Ollama's streaming output and swallows exceptions in the iteration loop. This is a library bug, not a configuration issue. Combined with FastAPI's StreamingResponse, errors during generation disappear unless explicitly handled at the yield level.

**How to avoid:**
- Wrap the litellm async streaming iterator in a try/except and explicitly yield an error event (`event: error`) before closing the SSE stream
- Never rely on litellm to surface Ollama errors — implement your own heartbeat/timeout: if no token arrives within N seconds, yield a timeout error event and close
- Test streaming error paths explicitly: send a request while Ollama is stopped, while Ollama has the model unloaded, and mid-stream network interrupt
- Use sse-starlette for SSE implementation (active maintenance, correct header handling) rather than raw StreamingResponse

**Warning signs:**
- Chat responses truncate at inconsistent lengths with no error displayed
- Frontend EventSource connection closes without an error event, leaving the UI in a loading state
- Ollama logs show errors but the API returns HTTP 200

**Phase to address:**
Chat + streaming phase — the SSE error contract (what events the client can receive, how the client handles them) must be defined before building the frontend chat interface.

---

### Pitfall 4: Ollama Model Unload Causes Cold-Start Latency in Interactive Use

**What goes wrong:**
Ollama unloads models from VRAM after 5 minutes of inactivity by default. The next request triggers a full model reload, adding 20–60 seconds of latency before the first token. For a clinical tool used during patient encounters, this is unusable. The litellm layer adds an additional ~20 seconds of connection re-establishment latency on top of the model reload (confirmed bug: GitHub issue #17954).

**Why it happens:**
Ollama's default `keep_alive` is 5 minutes — a reasonable default for servers, wrong for interactive single-user tools. litellm has a connection pooling bug that manifests as high latency specifically after idle periods when routing through Ollama.

**How to avoid:**
- Set `OLLAMA_KEEP_ALIVE=-1` in the Docker Compose environment to keep the model loaded indefinitely (single-user, single model — no memory sharing concern)
- Alternatively, implement a model warm-up ping on application startup: make a short completion request before the user's first interaction
- Consider bypassing litellm for Ollama specifically and calling the Ollama API directly (it is OpenAI-compatible) — this eliminates the litellm connection bug while still using litellm for cloud providers
- Add a model-load status indicator in the UI: if the first token takes >5 seconds, show "Loading model..."

**Warning signs:**
- First request after opening the app takes 30–60 seconds; subsequent requests are fast
- Latency varies unpredictably based on how long since the last request
- Direct `curl` to Ollama is fast but requests through the app are slow

**Phase to address:**
Infrastructure/Docker Compose phase — set keep_alive before the first end-to-end test, or early latency will be misattributed to the app code.

---

### Pitfall 5: Postgres FTS Fails on Medical Abbreviations and Synonyms

**What goes wrong:**
A search for "HTN" finds nothing when all articles use "hypertension." A search for "T2DM" misses documents tagged "type 2 diabetes mellitus." Postgres FTS uses a stemming dictionary (English Snowball by default) that has no knowledge of medical abbreviations, brand names (Metformin vs glucophage), or clinical synonyms (MI, STEMI, myocardial infarction). At 100–400 articles, every false-negative is noticeable.

**Why it happens:**
Postgres FTS is a general-purpose text search system. Its stemmer normalizes "running" to "run" but has no concept that "HTN" == "hypertension" or "Tylenol" == "acetaminophen." The system will faithfully index what is in the documents, but query terms that differ from document terms will return zero results even when semantically identical.

**How to avoid:**
- Build a custom synonym dictionary for Postgres FTS (thesaurus dictionary format) covering at minimum: common abbreviations (HTN, T2DM, MI, PE, DVT, URTI, LRTI), drug brand/generic pairs relevant to the scope, and Canadian-specific variants (e.g., "paracetamol" not commonly used, but "acetaminophen" vs "APAP")
- Add the synonym expansion at index time (during tsvector generation), not just at query time, so both paths benefit
- Implement query expansion in the search layer: before running FTS, expand the user's query terms using the same synonym map
- This is where the "FTS is sufficient at small scale" assumption holds — but only if synonyms are handled. Without it, recall degrades badly for medical queries.

**Warning signs:**
- Searches by abbreviation return empty results even though matching articles exist
- Users learn to search by exact terms from documents rather than natural clinical language
- The LLM workflow's local search step consistently returns "no relevant articles found" for common topics

**Phase to address:**
Search infrastructure phase — synonym dictionary must be designed alongside the FTS schema, not added later when articles have already been indexed with wrong lexemes.

---

### Pitfall 6: Markdown File and Postgres Index Go Out of Sync

**What goes wrong:**
The file on disk and the Postgres row diverge: a file is edited directly (e.g., via git or a text editor), the DB row is not updated. Or a DB record is deleted but the file remains. Or the YAML frontmatter in the file is modified but the indexed columns are not re-extracted. The system silently serves stale or split-brain data.

**Why it happens:**
Dual-storage architectures have a fundamental consistency problem: there is no atomic write that updates both the file and the database simultaneously. Any crash, error, or manual intervention between the two writes creates an inconsistent state. With single-user self-hosted tools, users are expected to sometimes "just edit the files" — and they will.

**How to avoid:**
- Treat the file as the canonical source of truth; Postgres is a derived index only
- Implement a startup integrity check: scan all markdown files, compare YAML frontmatter hashes against DB records, log discrepancies, offer a re-index command
- Expose a `POST /api/reindex` endpoint that re-scans all files and rebuilds the Postgres index — this should be a first-class operation, not an emergency fix
- Write files atomically: write to a temp file first, then rename (atomic on Linux/ext4), then update DB. If the DB update fails, the file is still valid and the re-index can recover
- Never delete files from the app without also removing the DB record in the same transaction (soft-delete first, then file deletion)

**Warning signs:**
- Search returns results for articles that can't be opened (file missing)
- Search misses articles that are clearly present on disk
- Note content differs between what the browser shows and what the file contains

**Phase to address:**
Knowledge base persistence phase — the file-as-canonical-source contract and integrity check must be established before notes are written at scale.

---

### Pitfall 7: Single-Process Python Blocks During LLM Inference

**What goes wrong:**
A 10-step research workflow runs a sequence of LLM calls, web fetches, PDF parsing, and DB writes — all in a single async FastAPI request. If any step uses a synchronous library (e.g., PyMuPDF's `fitz.open()`, synchronous litellm calls, or a blocking file write), it blocks the event loop. While a second request comes in (e.g., the user opens the topic browser while research is running), it gets no response until the blocking call finishes.

**Why it happens:**
FastAPI is async but Python's GIL and many common libraries are not. Calling a sync library from an `async def` endpoint blocks the entire event loop — all other requests stall. This is the most common FastAPI performance mistake for AI workloads. It is invisible in development (single user, no concurrent requests) and only surfaces under real use.

**How to avoid:**
- Run all blocking calls (PyMuPDF parsing, file I/O, CPU-heavy operations) inside `asyncio.to_thread()` or `loop.run_in_executor()` — never call sync blocking code directly from an async handler
- Use only async HTTP clients (httpx with async) for web fetch steps, never requests
- Use litellm's async methods (`await litellm.acompletion()`) not sync ones
- For the research workflow, implement step-level streaming progress via SSE: each workflow step emits a status event so the frontend knows what is happening without requiring a blocking wait
- Accept that single-process is a conscious tradeoff: document it clearly, design the workflow steps to be interruptible/cancellable

**Warning signs:**
- Opening any page while a research workflow is running takes 30+ seconds to load
- Uvicorn logs show requests queuing up during inference
- The `/healthz` endpoint returns slowly when a research workflow is active

**Phase to address:**
Research workflow phase — async discipline must be enforced from the first workflow step, not refactored in after observing slowness.

---

### Pitfall 8: Web Search Agent Fetches Gated Content It Cannot Access

**What goes wrong:**
The trusted source registry includes domains like `uptodate.com`, `cps.ca`, `sogc.org`. The web search agent discovers URLs from these domains and attempts to fetch them. UpToDate is behind an institutional paywall; the fetch returns a login page or HTTP 403. trafilatura extracts the login page HTML (navigation menus, "please sign in" text) as if it were the article content. This gets passed to the LLM as source material.

**Why it happens:**
The search agent finds URLs from trusted domains correctly, but URL discoverability and content accessibility are different problems. Institutional medical sources assume authenticated access. trafilatura cannot distinguish between a login redirect and actual article content — both return HTTP 200 with HTML.

**How to avoid:**
- After fetching, run a content quality check before passing to LLM: minimum word count (>300 words), absence of gating signals ("sign in", "subscribe", "access denied", "institutional login")
- For gated sources, the web search step should surface the URL as a "manual upload required" suggestion rather than attempting auto-fetch
- Clearly distinguish two source paths in the UI: auto-fetched (open access) vs. manual upload (gated). Don't try to unify them
- Add per-domain fetch behavior in the source registry YAML: `fetch_mode: auto | manual_only | ask` so the user can configure expected behavior per source

**Warning signs:**
- Source notes contain text like "Please log in to view this content" or "Subscribe to UpToDate"
- Short source notes (<500 words) from domains that typically produce long articles
- LLM synthesis produces vague outputs because the "source context" was a login page

**Phase to address:**
Source ingestion phase — the gating detection logic and source registry `fetch_mode` field must be implemented before the web search agent is wired to auto-fetch.

---

### Pitfall 9: Context Window Overrun Degrades Synthesis Quality Without Obvious Failure

**What goes wrong:**
The research workflow fetches 5–8 source documents averaging 3,000 words each and passes them all into a single synthesis prompt. For Ollama local models with a 4K–8K context window (common for models that run on consumer hardware), the combined source content plus system prompt plus chat history exceeds the window. The model truncates silently, synthesizes from partial information, and may not mention topics covered only in the truncated portion.

**Why it happens:**
litellm does not automatically truncate or warn when input exceeds the model's context window for Ollama — it depends on the Ollama model's behavior, which varies. Cloud models (Claude, GPT-4) have 100K+ windows, so developers test with cloud and assume Ollama is equivalent. It is not.

**How to avoid:**
- Before building the synthesis prompt, count tokens for all source chunks using tiktoken (or the model's tokenizer) and enforce a hard budget (e.g., 60% of the model's context window for sources, 20% for system prompt, 20% for output headroom)
- If sources exceed the budget, prioritize by relevance score from the FTS query rather than dropping arbitrarily
- Surface the truncation decision to the user: "5 of 8 sources included; 3 omitted due to context limits"
- Test the full workflow with Ollama llama3:8b (4K context) as a baseline, not just with cloud models
- Document the minimum recommended context window size in the self-hosting instructions

**Warning signs:**
- Synthesis notes are missing information that is clearly present in the ingested source files
- Notes for complex topics are shorter than notes for simpler topics (opposite of expected)
- Switching from Ollama to Claude produces dramatically different output quality for the same sources

**Phase to address:**
Research workflow phase — token budget management must be built into the workflow orchestration, not added later when users report missing information.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Skip citation verification step | Faster synthesis, simpler prompt | Users stop trusting the tool when they catch one wrong citation | Never — this is the core trust mechanism |
| Store full parsed text in DB instead of filesystem | Simpler architecture, single source of truth | Loses portability, git-trackability, and inspectability of the knowledge base | Never for a "living wiki" tool |
| Use sync litellm calls in async FastAPI handlers | Faster initial development | Blocks event loop under any concurrent use | Only in fully synchronous scripts, never in FastAPI async handlers |
| Single synthesis prompt for all sources | Simpler code | Context window overrun, lost-in-the-middle degradation | MVP only with explicit token budget check |
| No scanned PDF detection | Ship PDF upload faster | Silent garbage in knowledge base poisons future searches and synthesis | Never — add the word-count check from day one |
| Hardcode Ollama as only provider | No abstraction needed yet | Makes cloud fallback (for complex synthesis) require a rewrite | Never — litellm is already in scope, use it from the start |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| litellm + Ollama async | Trust litellm to surface Ollama errors | Wrap async iterator in try/except, yield explicit error SSE events, implement timeout heartbeat |
| trafilatura + gated sites | Pass all fetched HTML to LLM without content check | Check word count and gating signals before including in source context |
| PyMuPDF + scanned PDFs | Assume successful open means successful extraction | Check word-count-per-page ratio; flag low-density PDFs before indexing |
| Postgres FTS + medical queries | Use default English stemmer | Build custom thesaurus dictionary; expand queries with synonym map before FTS |
| SSE + reverse proxy (nginx) | No special configuration | Set `X-Accel-Buffering: no` and `Cache-Control: no-cache` headers; use ASGI server (Uvicorn not gunicorn sync) |
| Ollama + Docker Compose | Default keep_alive (5 min) | Set `OLLAMA_KEEP_ALIVE=-1` in environment; implement warm-up ping on app start |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Sync blocking calls in async handlers | UI freezes during research workflow | `asyncio.to_thread()` for all sync libs; async httpx; `await litellm.acompletion()` | First concurrent request (even just opening a second browser tab) |
| Full source document in synthesis prompt | Slow generation, truncated output | Token budget enforcement; relevance-ranked truncation | Ollama models <8K context with >3 sources |
| No GIN index on tsvector column | FTS queries take seconds | `CREATE INDEX CONCURRENTLY` on tsvector column at schema creation time | >1,000 articles (well within project scope) |
| Postgres FTS re-ranking all matches | Slow ranked search | GIN index handles matching; ts_rank applied only to top-N matches | >10,000 articles (outside current scope, but plan for it) |
| File system walk on every search | Search latency grows with article count | Never walk files for search — all search goes through Postgres; files are read-only on query | >500 files |

---

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Storing LLM-generated content without sanitization | XSS in note rendering (markdown → HTML) | Sanitize HTML output at render time (DOMPurify client-side or bleach server-side); never trust LLM output as safe HTML |
| Exposing raw file paths in API responses | Path traversal if API is accidentally network-accessible | Use opaque IDs (UUIDs) in API; resolve to file paths only server-side |
| Passing user query directly to web search without rate limiting | Self-DoS on search API quota; scraping abuse | Rate limit search calls per session; cache search results for identical queries |
| API keys (Anthropic/OpenAI) in Docker Compose plain text | Credential exposure in git | Use `.env` file excluded from git; document this clearly in setup instructions |
| No timeout on LLM calls | Runaway request holds process indefinitely | Always set `request_timeout` in litellm calls; implement server-side SSE timeout |

---

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| No progress indication during 10-step workflow | User thinks app is broken during 30-60 second workflow | Stream step-by-step status via SSE: "Searching local knowledge..." → "Fetching sources..." → "Synthesizing..." |
| Approval gate shows full markdown without diff | User re-reads entire note even for minor refresh changes | On re-research (existing topic refresh), show a diff view highlighting what changed |
| "No results found" with no query suggestion | User doesn't know if they searched wrong or the topic is missing | Show "Did you mean: [expanded query]?" using the synonym map; show count of articles searched |
| Saving notes without user understanding provenance | User cites the note but can't trace back to the original source | Every note must display its source chain prominently (not buried in frontmatter) |
| Model cold-start during clinical encounter | 30-second wait when time is critical | Show model load status on startup; consider a "ready" indicator in the UI header |

---

## "Looks Done But Isn't" Checklist

- [ ] **PDF ingestion:** Extraction appears to work — verify word count per page is >100 for non-scanned PDFs; test with a known scanned PDF and confirm it is flagged
- [ ] **SSE streaming:** Chat appears to stream — verify what happens when Ollama is stopped mid-stream; confirm the frontend handles the error event and exits loading state
- [ ] **Citation display:** Notes show citation labels — verify each label resolves to a real source file with matching content; open the source and confirm the cited claim is present
- [ ] **FTS search:** Search returns results — test with medical abbreviations (HTN, T2DM, MI); confirm synonym expansion is working, not just exact string matching
- [ ] **File-DB sync:** App shows note in browser — edit the markdown file directly on disk, restart the app, confirm the change is reflected without manual intervention
- [ ] **Web fetch gating:** Source fetch succeeds — test with an UpToDate URL; confirm the system recognizes the gating and surfaces "manual upload required" rather than storing login page text
- [ ] **Context budget:** Synthesis runs — test with 8 long sources; confirm the token budget check fires and the user is notified of omitted sources
- [ ] **Ollama cold start:** First request works — measure time from app start to first token; confirm keep_alive is set correctly

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Citation fabrication discovered after many notes saved | HIGH | Add citation verification to new notes immediately; audit existing notes manually; mark unverified notes with a "needs review" flag in frontmatter |
| Scanned PDFs indexed as garbage | MEDIUM | Run re-index with word-count check; flag affected source notes; delete and re-upload with OCR |
| File-DB sync divergence | LOW | Run `POST /api/reindex` to rebuild Postgres from files; spot-check 5 random articles post-reindex |
| Context window overrun discovered (missing content in notes) | MEDIUM | Add token budget enforcement to synthesis prompt; re-research affected topics with the fix in place |
| Ollama async errors silently swallowed discovered in production | MEDIUM | Implement SSE error wrapping immediately; add integration test that asserts error events are emitted on Ollama failure |
| Gated content stored as source notes | MEDIUM | Add content quality check; delete affected source notes; re-run web search with gating detection in place |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Citation fabrication | Research workflow (synthesis design) | Test: ask for a claim not present in any source; verify it is not fabricated with a citation |
| Scanned PDF garbage extraction | Source ingestion (PDF parsing) | Test: upload a known scanned PDF; verify it is flagged and not silently indexed |
| SSE error swallowing (litellm/Ollama) | Chat + streaming infrastructure | Test: stop Ollama mid-stream; verify frontend receives error event and exits loading state |
| Ollama cold-start latency | Infrastructure / Docker Compose | Test: wait 6 minutes, send a request, measure time-to-first-token; should be <5 seconds with keep_alive=-1 |
| Postgres FTS medical synonym gap | Search infrastructure | Test: search "HTN"; verify it returns documents containing "hypertension" |
| Markdown-DB drift | Knowledge base persistence | Test: edit a file directly, restart app, verify Postgres reflects the change |
| Event loop blocking (sync in async) | Research workflow (async discipline) | Test: open topic browser while research workflow is running; verify response time <500ms |
| Web fetch gating blindness | Source ingestion (fetch + quality check) | Test: fetch an UpToDate URL; verify system detects gating and does not store login page as source |
| Context window overrun | Research workflow (token budget) | Test: synthesize with 8 long sources on Ollama 8B; verify token budget enforcement and user notification |

---

## Sources

- [litellm GitHub Issue #8868 — Ollama async streaming errors swallowed](https://github.com/BerriAI/litellm/issues/8868)
- [litellm GitHub Issue #17954 — High latency after idle with Ollama](https://github.com/BerriAI/litellm/issues/17954)
- [PyMuPDF Common Issues Documentation](https://pymupdf.readthedocs.io/en/latest/recipes-common-issues-and-their-solutions.html)
- [Nature Communications — Automated framework for assessing LLM citation accuracy in medicine](https://www.nature.com/articles/s41467-025-58551-6)
- [medRxiv — Medical Hallucination in Foundation Models](https://www.medrxiv.org/content/10.1101/2025.02.28.25323115v2.full)
- [arXiv — Investigating LLM Capabilities on Long Context for Medical QA](https://arxiv.org/html/2510.18691v1)
- [Redis — Context Window Management for LLM Apps](https://redis.io/blog/context-window-management-llm-apps-developer-guide/)
- [FastAPI GitHub Discussion #10138 — StreamingResponse exception handling](https://github.com/fastapi/fastapi/discussions/10138)
- [JAM with AI — Concurrency mistake in FastAPI AI services](https://jamwithai.substack.com/p/the-concurrency-mistake-hiding-in)
- [Frontiers in AI — Auditable source-verified clinical AI decision support](https://www.frontiersin.org/journals/artificial-intelligence/articles/10.3389/frai.2026.1737532/full)
- [Postgres FTS Documentation — Dictionaries and thesaurus](https://www.postgresql.org/docs/current/textsearch-dictionaries.html)
- [Fix RAG Hallucinations at the Source: PDF Parsers Ranked 2025](https://infinityai.medium.com/3-proven-techniques-to-accurately-parse-your-pdfs-2c01c5badb84)

---
*Pitfalls research for: clinical knowledge assistant (Clinic Atlas)*
*Researched: 2026-04-06*
