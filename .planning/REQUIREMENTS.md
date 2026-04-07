# Requirements: Clinic Atlas

**Defined:** 2026-04-06
**Core Value:** Every query compounds the knowledge base — the system gets smarter with use.

## v1 Requirements

### Chat & LLM

- [ ] **CHAT-01**: User can ask clinical questions in a conversational chat interface
- [ ] **CHAT-02**: LLM responses stream to the UI via SSE in real-time
- [ ] **CHAT-03**: Every claim in a response includes an inline citation linking to its source
- [ ] **CHAT-04**: User can switch LLM provider (Ollama local / Anthropic / OpenAI) via config

### Source Ingestion

- [ ] **SRCI-01**: User can upload PDF files which are parsed and stored as raw sources
- [ ] **SRCI-02**: User can submit a URL which is fetched, extracted, and stored as a raw source
- [ ] **SRCI-03**: Scanned/image-only PDFs are detected and flagged (not silently indexed)
- [ ] **SRCI-04**: Trusted source registry is loaded from a YAML config file at startup
- [ ] **SRCI-05**: System can search trusted source domains via SearXNG and ingest results

### Knowledge Base & Search

- [ ] **KBSE-01**: Raw sources and compiled notes are indexed with Postgres full-text search (tsvector + GIN)
- [ ] **KBSE-02**: Medical abbreviation synonym dictionary improves FTS recall (e.g. HTN → hypertension)
- [ ] **KBSE-03**: All compiled notes are stored as markdown files on disk with YAML frontmatter
- [ ] **KBSE-04**: Postgres metadata stays in sync with disk files via integrity check / reindex endpoint

### Research Workflow

- [ ] **RSRW-01**: User query triggers the research workflow: local search → evaluate → plan retrieval → fetch → parse → synthesize
- [ ] **RSRW-02**: Synthesis prompt uses defensive citation: verbatim quote extraction before generating the answer
- [ ] **RSRW-03**: Token budget management ensures source context fits within the LLM context window

### Note Generation

- [ ] **NOTE-01**: System generates source notes (one per raw source, preserving provenance and key findings)
- [ ] **NOTE-02**: System generates topic notes (synthesis across multiple sources, with inline citations)
- [ ] **NOTE-03**: System generates research logs (one per session, documenting query, sources, notes created)

### Approval & Quality

- [ ] **APPR-01**: After synthesis, user sees an approval gate with save / edit / discard options
- [ ] **APPR-02**: User can edit note content before saving
- [ ] **APPR-03**: On topic refresh, user sees a diff of old vs proposed new content before approving

### Navigation

- [ ] **NAVI-01**: User can browse all topic notes with search
- [ ] **NAVI-02**: User can view a single topic note rendered as formatted markdown
- [ ] **NAVI-03**: User can view past research sessions and replay chat logs

### Topic Refresh

- [ ] **REFR-01**: User can trigger a re-research of an existing topic
- [ ] **REFR-02**: Refresh re-runs the research workflow and presents updated findings for approval

## v2 Requirements

### Document Formats

- **DOCX-01**: User can upload DOCX files for parsing and ingestion

### Knowledge Graph

- **GRPH-01**: Notes display backlinks to other notes that reference them
- **GRPH-02**: User can view a graph visualization of note connections

### Monitoring & Automation

- **MNTR-01**: System monitors trusted sources on a schedule for new content
- **MNTR-02**: User receives notification when relevant source updates are detected

### Professional Development

- **CMED-01**: Research sessions are logged in a format compatible with CME/CPD reporting

### Multi-User

- **MUSR-01**: Multiple users can authenticate and maintain separate knowledge bases

## Out of Scope

| Feature | Reason |
|---------|--------|
| Vector DB / RAG pipeline | At ~100-400 articles, FTS + LLM context window is sufficient. Revisit at ~1000 notes. |
| Task queue / Celery / background workers | Single user, single process. Inline processing + SSE is sufficient. |
| Auto-save without review | Clinical knowledge requires physician approval. Garbage-in degrades the entire KB. |
| Differential diagnosis / patient-case mode | Different product, different liability posture. Stay in research/reference mode. |
| Real-time collaboration | Single user tool. Open-source: colleagues run their own instance. |
| Mobile app | Web-first. Responsive design is sufficient. |
| Image/figure extraction from PDFs | Text extraction only. Physician opens source PDF for figures. |
| OAuth / magic link login | No auth needed for single-user self-hosted. |
| Source registry UI editor | YAML file is sufficient for v1. |
| Mermaid/figure generation | Not core to knowledge compounding. |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| KBSE-01 | Phase 1 | Pending |
| KBSE-02 | Phase 1 | Pending |
| SRCI-04 | Phase 1 | Pending |
| SRCI-01 | Phase 2 | Pending |
| SRCI-02 | Phase 2 | Pending |
| SRCI-03 | Phase 2 | Pending |
| SRCI-05 | Phase 2 | Pending |
| CHAT-01 | Phase 3 | Pending |
| CHAT-02 | Phase 3 | Pending |
| CHAT-04 | Phase 3 | Pending |
| RSRW-01 | Phase 4 | Pending |
| RSRW-02 | Phase 4 | Pending |
| RSRW-03 | Phase 4 | Pending |
| NOTE-01 | Phase 4 | Pending |
| NOTE-02 | Phase 4 | Pending |
| NOTE-03 | Phase 4 | Pending |
| CHAT-03 | Phase 4 | Pending |
| APPR-01 | Phase 5 | Pending |
| APPR-02 | Phase 5 | Pending |
| KBSE-03 | Phase 5 | Pending |
| KBSE-04 | Phase 5 | Pending |
| NAVI-01 | Phase 6 | Pending |
| NAVI-02 | Phase 6 | Pending |
| NAVI-03 | Phase 6 | Pending |
| REFR-01 | Phase 7 | Pending |
| REFR-02 | Phase 7 | Pending |
| APPR-03 | Phase 7 | Pending |

**Coverage:**
- v1 requirements: 27 total
- Mapped to phases: 27
- Unmapped: 0 ✓

---
*Requirements defined: 2026-04-06*
*Last updated: 2026-04-06 after roadmap creation*
