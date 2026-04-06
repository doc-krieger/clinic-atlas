# Project: Clinic Atlas

## One-line summary
A self-hosted, chat-first clinical knowledge assistant that researches trusted sources, drafts source-grounded answers and notes, and maintains a living markdown knowledge base behind the scenes.

## Core idea
This project should not require Obsidian as the main interface.

Instead, it should have a primary **web app UI** where I can:
- ask clinical questions in a chat/query interface
- see answers synthesized from trusted sources
- inspect which sources were used
- review/update saved topic notes
- trigger refreshes
- browse prior topics and research sessions

Under the hood, the system should maintain a durable **markdown knowledge base** plus preserved raw sources.
Obsidian should be optional as a secondary interface for browsing/editing the compiled markdown wiki, not the required way to use the system.

## Product concept
This is a **self-hosted clinical research assistant** with a **bounded agent workflow**.

It should:
1. search a curated set of trusted medical sources
2. search its own existing local knowledge base first
3. retrieve and parse relevant documents/pages
4. synthesize a source-grounded answer
5. generate/update markdown notes and indexes
6. save those outputs into a durable local library
7. support future refresh/update runs on the same topic

The project is not just a scraper, not just a RAG bot, and not just an Obsidian vault.
It is a **chat-first research app backed by a persistent markdown knowledge system**.

## Main problem
As a physician, I repeatedly need to look up:
- guidelines
- pathways
- society statements
- local documents
- PDFs
- website pages
- policies/bulletins

The same topics recur over time, and sources change.
I want one system where:
- I can ask a question naturally
- it searches trusted sources
- it gives a useful answer
- it preserves the answer and supporting sources
- it builds a reusable knowledge base over time
- it can refresh/update prior topics later

## High-level design principles
### 1. Chat-first UI
The primary interaction should be a web UI similar in spirit to ChatGPT:
- ask a question
- see the answer
- inspect sources
- inspect notes created/updated
- take follow-up actions

### 2. Ground-truth preservation
Original source artifacts remain the ground truth:
- PDFs
- HTML snapshots
- uploaded docs
- saved images/figures

LLM outputs are derived artifacts, not the source of truth.

### 3. Query-driven retrieval
Do not broadly monitor everything continuously by default.
Use:
- internal library search first
- targeted trusted-source retrieval second
- freshness checks when needed
- optional light refresh for saved topics later

### 4. Incremental knowledge accumulation
Every query should improve the local knowledge base:
- update topic notes
- create source notes
- create concept notes when useful
- update indexes/backlinks
- generate research logs

### 5. Bounded agent behavior
The system can behave agentically, but within controlled boundaries.
It should not be fully autonomous in a wide-open way.

## Main user-facing experience

### Primary UI
A web app with:
- chat/query panel
- source/results panel
- note preview/update panel
- history/version panel
- topic browser
- refresh controls

### Optional Obsidian view
The underlying markdown wiki should be viewable in Obsidian if desired, but that is optional.

## Main use cases

### 1. Ask a clinical question
Examples:
- “abnormal uterine bleeding”
- “adult ADHD diagnosis Canada”
- “trigger finger management Alberta”
- “pediatric hypertension workup”

Expected behavior:
1. search existing local library/wiki first
2. decide whether it already has a recent useful answer
3. if needed, retrieve from trusted external sources
4. parse/summarize/synthesize
5. present answer in UI
6. update local knowledge base artifacts

### 2. Re-ask a topic later
If I ask the same topic 3 months later:
- check prior topic note
- inspect prior sources used
- run a targeted freshness check
- retrieve only what is needed
- update the answer and note if needed
- show what changed

### 3. Browse saved topics
I should be able to browse:
- saved topic notes
- source notes
- concept notes
- recent updates
- research sessions
- source collections

### 4. Manually add documents
I should be able to upload or drop in:
- PDFs
- DOCX later
- webpages or URLs
- local images/figures

These should enter the same pipeline and become searchable/usable in the system.

### 5. Generate derived outputs
Not just chat answers.
The system should eventually support generating:
- markdown topic notes
- quick-reference summaries
- comparison pages
- update/diff notes
- slide decks
- maybe teaching handouts later

## Bounded agent design
The system should support **semi-agentic workflows**.

### Actions it can do automatically
- search local library
- search trusted sources
- retrieve PDFs/pages
- parse documents
- draft source notes
- draft topic notes
- suggest concept notes
- suggest backlinks/index updates
- propose note refreshes
- produce temporary research artifacts

### Actions that should likely require approval
- publish/update a major topic note
- overwrite an existing curated note
- mark a source or note as superseded
- change source trust policies
- schedule recurring refresh behavior
- archive/delete content

This creates an **agentic assistant with approval gates**, not a fully autonomous system.

## Internal knowledge model
The system should still use a `raw/` and `compiled/` model.

### raw/
Ground-truth materials:
- source PDFs
- webpage snapshots
- uploaded docs
- images/figures
- extracted page images
- any preserved source artifacts

### compiled/
Derived markdown knowledge artifacts:
- source notes
- topic notes
- concept notes
- indexes
- research logs
- update/diff notes
- derived outputs

This keeps provenance clear.

## Main note/document types

### 1. Source notes
One per raw source.
Purpose:
- summarize a specific document/page
- preserve metadata and provenance
- make that source reusable

### 2. Topic notes
Synthesis across multiple sources for a clinical topic.
This is the main reusable note type for user questions.

### 3. Concept notes
Reusable subtopic pages to reduce duplication and improve linking.
Examples:
- PALM-COEIN
- endometrial biopsy indications
- steroid injection precautions
- red flags

### 4. Index notes
System-maintained navigation pages:
- gynecology index
- MSK index
- recent updates
- red flags index
- source registry summary

### 5. Research logs
A note or record for each research session:
- question asked
- what sources were used
- what notes changed
- whether freshness check ran
- unresolved uncertainty

### 6. Update/diff notes
Optional notes capturing what changed between refreshes.

## Suggested UI layout

### Left sidebar
- saved topics
- recent sessions
- favorite topics
- source collections
- updates queue

### Main center panel
- chat/query interface
- answer display
- follow-up actions
- regenerate/refine options

### Right panel
- sources used
- provenance
- freshness status
- notes created/updated
- actions:
  - refresh topic
  - compare versions
  - open source doc
  - publish note
  - regenerate note
  - create quick reference
  - create concept page

## Suggested architecture

### Core app
- Backend API: FastAPI
- Frontend UI: Next.js or React
- Database: Postgres
- File storage: local disk first
- Worker system: Celery / Dramatiq / similar
- Scheduler: APScheduler or equivalent

### Parsing / ingestion
- PDF and webpage parsing
- document normalization
- metadata extraction
- source snapshot storage

### Model/provider layer
Provider-agnostic abstraction over:
- local: Ollama first
- optional local: llama.cpp later
- cloud: Anthropic/OpenAI

Important:
Do not scatter provider-specific calls around the codebase.
Build a provider/harness layer.

### Internal operations examples
- search_library()
- search_sources()
- fetch_source()
- parse_document()
- classify_document()
- summarize_source()
- synthesize_topic()
- refresh_topic()
- compare_versions()
- generate_note()
- update_indexes()
- summarize_figure()

## Source strategy
Use a curated source registry, editable in the UI.

Each source may include:
- source name
- base URL
- source type
- topic tags
- jurisdiction
- trust level
- retrieval/search method
- refresh policy
- provider policy

Trusted sources should be primary.
Broader web search can be optional/secondary.

## Provenance and citations
Every important fact in a generated note should ideally map back to source evidence:
- source title
- URL or local file reference
- retrieved date
- reviewed/updated date if available
- page number for PDF
- section heading when possible

The UI should make source inspection easy.

## Diagram / figure strategy
Do not require automatic recreation of every figure/flowchart.

Instead:
- preserve original figures/pages/images in raw/
- allow the model to reference them
- optionally generate:
  - figure summary
  - pathway logic summary
  - Mermaid draft marked as derived/non-authoritative

## Health checks / maintenance
Later, the system should be able to run knowledge-base health checks:
- stale notes
- missing citations
- orphaned notes
- contradictory thresholds
- raw docs lacking source notes
- repeated concepts with no concept page
- notes missing jurisdiction/review metadata

## Metadata model
The system should track both raw artifacts and compiled note artifacts.

### Raw/source metadata
- id
- title
- source_name
- source_type
- original_url
- local_file_path
- retrieved_date
- reviewed_date
- published_date
- jurisdiction
- trust_level
- version_hash
- parser_status
- parser_confidence
- related compiled notes

### Compiled note metadata
- id
- note_type
- title
- topics
- specialty
- jurisdiction
- sources_used
- last_refreshed
- review_status
- confidence
- related_notes
- backlinks
- previous_version / superseded_by
- output_path

## Standard note structure
Topic notes should generally include:
- Overview
- Key points
- Applicability
- Workup / diagnosis
- Management
- Referral thresholds
- Red flags
- Important numbers/thresholds
- What changed
- Source references
- Related notes
- Open questions

## MVP scope
Keep v1 realistic but useful.

### MVP
- chat/query UI
- curated source registry
- local library/wiki search
- targeted trusted-source retrieval
- PDF/webpage parsing
- source note generation
- topic note generation
- markdown knowledge storage
- provenance/source links
- on-demand refresh of prior topics
- research log creation
- simple topic browser
- basic approval gate before publishing/updating major notes

### Not MVP
- fully autonomous open-ended agents
- broad continuous crawling
- polished SaaS-grade UX
- perfect diagram recreation
- fine-tuning
- complicated vector infrastructure as a requirement
- full automation with no review

## V2 / later ideas
- periodic light refresh of saved/starred topics
- change/diff notes
- richer concept-note generation
- health checks / linting
- figure understanding
- Mermaid draft generation
- comparison pages between multiple sources
- quick-reference sheet generation
- slide generation
- more powerful search over the knowledge base
- limited deeper agent workflows

## Guardrails
Because this is medical content:
- preserve originals
- preserve prior note versions
- show freshness timestamps
- show machine-generated/reviewed status
- retain source traceability
- use approval gates for important updates
- distinguish raw evidence from derived interpretation

## What I want from Claude Code
Please help refine this into a practical implementation plan.

Specifically:
1. sharpen the MVP
2. refine the architecture
3. propose repo/folder structure
4. propose database schema
5. define the raw/compiled model clearly
6. design the source registry
7. design the provider abstraction
8. design the chat/research workflow
9. design the approval-gate workflow
10. design the note schemas/templates
11. design the refresh/update logic
12. design the research-log model
13. design the index/backlink update logic
14. design the UI structure and screens
15. recommend the best self-hosted local-first stack
16. cut anything unnecessary for v1

Please optimize for a builder’s plan, not a vague product vision.
