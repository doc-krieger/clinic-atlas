# Feature Research

**Domain:** Clinical knowledge assistant (personal, self-hosted, chat-first, knowledge-compounding)
**Researched:** 2026-04-06
**Confidence:** MEDIUM-HIGH (commercial tool features verified via official sources and comparative research; PKM physician patterns from forum data, lower confidence)

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = product feels incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Cited answers | Every clinical AI tool (UpToDate ExpertAI, Dyna AI, ClinicalKey AI, OpenEvidence) shows citations. Without provenance, a clinical tool is untrustworthy. | MEDIUM | Must link every claim to its source. Inline citation markers + source list minimum. |
| Conversational chat interface | The standard UX paradigm for all 2025 clinical AI tools. Physicians now expect natural language queries, not keyword search. | MEDIUM | Streaming responses (SSE) are expected for perceived speed. |
| Full-text search over knowledge base | Core to any knowledge tool. Obsidian, Notion, and all clinical tools provide this. | LOW | Postgres tsvector + GIN is sufficient at this scale. |
| Source provenance traceability | ClinicalKey AI explicitly markets "traceability" — physicians want to verify where claims come from. | MEDIUM | Each claim must trace to a named source with enough context to find the original. |
| Topic browser / knowledge navigation | PKM tools (Obsidian, Notion) and clinical tools all provide browsable indexes. Without it, the KB is write-only. | LOW | Simple search + list view is sufficient for v1. |
| Session/query history | UpToDate and all modern clinical AI tools log queries. Physicians revisit questions they've asked before. | LOW | Flat log of past research sessions with chat replay. |
| PDF ingestion | The primary source format for clinical literature (guidelines, CPG PDFs). Most clinical content requires institutional auth — upload is the realistic path. | MEDIUM | PyMuPDF handles this well. Text extraction only (no images). |
| Markdown/text export | Obsidian-using physicians already work in Markdown. Portability and git-trackability are expected for a local-first tool. | LOW | Files on disk with YAML frontmatter satisfies this. |
| Trusted source scoping | Physicians do not want hallucinated or unreliable web results. ClinicalKey AI, Dyna AI, and iatroX are all scoped to vetted corpora. | MEDIUM | YAML source registry with domain-scoped web search. |

### Differentiators (Competitive Advantage)

Features that set the product apart. Not required, but valuable.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Compounding knowledge base | Every query enriches a personal wiki. No commercial tool does this — UpToDate, DynaMed, OpenEvidence all start from zero per session. This is the core value proposition. | HIGH | Research workflow: search local KB first, retrieve if needed, synthesize, save. |
| Approval gate before saving notes | Puts the physician in control of what enters their KB. Prevents garbage-in. No commercial tool exposes this — they save implicitly to their own corpus. | LOW-MEDIUM | Save / edit in place / discard. Diff on refresh. |
| Three note types (source, topic, research log) | Structured knowledge capture: raw source notes preserve provenance, topic notes synthesize across sources, research logs document the reasoning chain. Obsidian users try to build this manually — it's not automated anywhere. | MEDIUM | Markdown files on disk, separate templates per type. |
| On-demand topic refresh with diff | When guidelines update, physician can re-run research and see what changed before accepting. No commercial tool offers this for personal notes. | MEDIUM | Requires stable topic identity (filename/slug). Show old vs new diff in approval step. |
| Local-first privacy | All commercial tools (UpToDate, DynaMed, ClinicalKey) are cloud-only and require institutional subscriptions. A self-hosted local tool eliminates data residency concerns for Canadian/Alberta privacy requirements. | LOW | Docker Compose default. Ollama for fully offline operation. |
| LLM provider flexibility | Commercial tools are locked to their own models. Local Ollama for full privacy; cloud APIs for higher capability when needed. | LOW | litellm handles this with one config change. |
| Web search scoped to trusted domains | Glass Health and OpenEvidence search broadly; iatroX is scoped to NICE/SIGN. Domain-scoped search gives automation without sacrificing trust. | MEDIUM | Trusted source registry drives search scope. Auto-fetch open-access, manual upload for paywalled. |
| Knowledge compounds over time | The system gets smarter with use — richer answers as local KB grows. Karpathy's insight: at small scale, FTS + LLM context window replaces RAG pipelines. | HIGH (architecture) | Realized through local search first → retrieve only if needed logic. |
| Open-source / self-hostable | No equivalent in the commercial space. Enables customization (local guidelines, Alberta-specific CPGs), community contribution, and zero subscription cost. | LOW (intent) | Greenfield — needs Docker Compose and documented setup. |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem good but create problems.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Automatic note saving without review | Feels efficient — why review every note? | Clinical knowledge requires accuracy. Auto-saved LLM output could encode errors silently. The KB becomes unreliable over time. | Hard approval gate. Make review fast (one-click save) but mandatory. |
| Vector DB / semantic RAG pipeline | Modern AI apps use embeddings. Feels more "AI-native." | At 100-400 article scale, embedding pipeline adds significant complexity (chunking, embedding model, vector store) with marginal recall benefit over FTS. Karpathy's insight: at small scale, FTS + full context window is better. | Postgres tsvector + GIN. Revisit when KB exceeds ~1000 nodes. |
| Real-time source monitoring / alerts | "Notify me when guidelines update" sounds useful. | Requires continuous background jobs, source polling infrastructure, and managing notification fatigue. For a single-user personal tool, it's overengineered for v1. | On-demand refresh: physician triggers re-research when they suspect guidelines have changed. |
| Multi-user / team collaboration | "What if I want to share with colleagues?" | Auth, permissions, conflict resolution, and sync complexity explode the scope. The core value is personal compounding — multi-user dilutes that. | Open-source: colleagues clone and run their own instance. |
| Concept / index notes (Zettelkasten-style) | Obsidian power users build concept maps and backlinks. Feels like "proper PKM." | Backlinks and concept notes require significant note volume to become useful (~500+ notes). Pre-maturely building graph infrastructure creates maintenance overhead for zero benefit at launch scale. | Defer. Add backlinks when note volume demands it (explicitly out of scope in PROJECT.md). |
| Differential diagnosis / patient-case mode | Glass Health's feature — "enter a patient, get differentials." | Shifts the product from knowledge research to clinical decision support, which is a different regulatory and liability posture. Increases scope dramatically. | Stay in research/reference mode. The physician applies knowledge to their case. |
| CME / MOC credit logging | ClinicalKey AI and iatroX offer this as a differentiator for their platforms. | Requires integration with CME tracking systems (AMA, RCPSC for Canada). Heavyweight for a personal tool. | Out of scope for v1. Session logs already document research history if needed manually. |
| Image / figure extraction from PDFs | "I want the tables and figures from guidelines." | Complex to implement (PyMuPDF image extraction + rendering). Guidelines are primarily text-based — value is marginal for v1. | Text extraction only. Physician can open the source PDF for figures. |
| DOCX support | "Some guidelines come as Word docs." | PyMuPDF doesn't handle DOCX. Adds python-docx or pandoc dependency for edge-case format. | PDF conversion first (most clinical guidelines are PDF). Add DOCX in v1.x if needed. |
| Scheduled / recurring refresh | "Auto-update my KB when guidelines change." | Background job infrastructure (Celery, Redis) for a single-user tool. Notification UX. Not justified for v1. | On-demand refresh. Physician controls when topics are re-researched. |

## Feature Dependencies

```
Chat Interface (streaming)
    └──requires──> LLM Provider (litellm)
                       └──requires──> Ollama / Anthropic / OpenAI config

Source Ingestion (PDF + URL)
    └──requires──> Parsing (PyMuPDF + trafilatura)
    └──produces──> Source Notes

Source Notes
    └──enables──> Topic Notes (synthesis across multiple source notes)
    └──enables──> Research Log (session artifact referencing source notes)

Web Search (domain-scoped)
    └──requires──> Trusted Source Registry (YAML)
    └──produces──> Discovered URLs → Source Ingestion

Postgres FTS (tsvector + GIN)
    └──indexes──> Markdown KB on disk
    └──enables──> Local KB search (first step in research workflow)

Research Workflow
    └──requires──> Chat Interface
    └──requires──> Source Ingestion
    └──requires──> Postgres FTS
    └──requires──> LLM Provider
    └──produces──> Source Notes + Topic Notes + Research Log

Approval Gate
    └──requires──> Research Workflow (produces notes to approve)
    └──gates──> Markdown KB (notes only saved after approval)

Topic Refresh
    └──requires──> Existing Topic Notes in KB
    └──requires──> Research Workflow
    └──enhances──> Approval Gate (shows diff of old vs new)

Topic Browser
    └──requires──> Markdown KB (something to browse)
    └──requires──> Postgres FTS (search within browser)

Session History
    └──requires──> Research Log (each session produces a log)
    └──enables──> Chat replay (read past sessions)
```

### Dependency Notes

- **Source Notes require parsing:** You cannot generate source notes without first ingesting and parsing source documents. PDF and URL ingestion must be built before note generation.
- **Topic Notes require Source Notes:** A topic note synthesizes across multiple source notes. Source note generation must precede topic note generation.
- **Research Workflow requires all primitives:** The full workflow (local search → plan → fetch → parse → synthesize → approve → save) is the integration point for all lower-level features. Build primitives first, assemble workflow last.
- **Approval Gate requires notes to exist:** The gate has nothing to review until the research workflow produces candidate notes. Gate logic is simple but sequentially dependent.
- **Topic Refresh enhances Approval Gate:** Refresh is a second pass through the same workflow, with the added step of diffing against the existing note before the approval decision.
- **Topic Browser has no blocking dependencies except KB content:** Can be built as soon as any notes exist in the KB.

## MVP Definition

### Launch With (v1)

Minimum viable product — what's needed to validate "knowledge compounds."

- [ ] Chat interface with streaming LLM responses — entry point for all research
- [ ] PDF ingestion + URL fetch with text parsing — primary source input paths
- [ ] Trusted source registry (YAML) + domain-scoped web search — controlled source discovery
- [ ] Postgres FTS over KB — local knowledge search (first step in research workflow)
- [ ] Full research workflow (local search → retrieve → parse → synthesize) — core loop
- [ ] Source note generation (one per ingested source, with provenance)
- [ ] Topic note generation (synthesis across sources, inline citations)
- [ ] Research log per session
- [ ] Approval gate (save / edit / discard) — quality control for KB entries
- [ ] Markdown KB on disk with YAML frontmatter — the compounding artifact
- [ ] Topic browser with search — navigate what's been built
- [ ] Session history — replay past research

### Add After Validation (v1.x)

Features to add once core loop is working and KB is accumulating.

- [ ] On-demand topic refresh with diff — once there are topics worth refreshing
- [ ] DOCX support — if source ingestion proves PDF-insufficient
- [ ] Backlinks / graph view — once KB exceeds ~200-300 notes

### Future Consideration (v2+)

Features to defer until product-market fit is established.

- [ ] CME/CPD logging — requires external system integration
- [ ] Multi-user support — requires auth, permissions, significant rearchitecture
- [ ] Scheduled source monitoring — requires background job infrastructure
- [ ] Image/figure extraction — marginal value vs complexity
- [ ] Differential diagnosis / patient-case mode — different product, different liability posture

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Chat interface (streaming) | HIGH | MEDIUM | P1 |
| Cited answers with provenance | HIGH | MEDIUM | P1 |
| PDF ingestion + parsing | HIGH | LOW | P1 |
| Research workflow (full loop) | HIGH | HIGH | P1 |
| Approval gate | HIGH | LOW | P1 |
| Markdown KB on disk | HIGH | LOW | P1 |
| Postgres FTS | MEDIUM | LOW | P1 |
| Source notes | HIGH | MEDIUM | P1 |
| Topic notes (synthesis) | HIGH | MEDIUM | P1 |
| Research log | MEDIUM | LOW | P1 |
| Trusted source registry + web search | HIGH | MEDIUM | P1 |
| Topic browser + search | MEDIUM | LOW | P1 |
| Session history | MEDIUM | LOW | P1 |
| On-demand topic refresh + diff | HIGH | MEDIUM | P2 |
| URL ingestion (direct fetch) | MEDIUM | LOW | P2 |
| LLM provider flexibility (litellm) | MEDIUM | LOW | P1 (architectural) |
| Local-first / Ollama support | HIGH | LOW | P1 (architectural) |
| Backlinks / graph view | LOW | HIGH | P3 |
| CME/CPD logging | LOW | HIGH | P3 |
| Multi-user support | LOW | HIGH | P3 |

## Competitor Feature Analysis

| Feature | UpToDate ExpertAI | DynaMed / Dyna AI | OpenEvidence | Glass Health | Obsidian (PKM) | Clinic Atlas |
|---------|-------------------|-------------------|--------------|--------------|----------------|--------------|
| Cited answers | Yes — links to UpToDate topics | Yes — links to DynaMed articles with evidence grading | Yes — paper-level citations from 35M+ PubMed papers | Yes — evidence summaries | No (manual) | Yes — inline citations to source notes |
| Conversational chat | Yes | Yes | Yes | Yes (case-centric) | No | Yes (streaming) |
| Personal knowledge compounding | No — read-only access to shared corpus | No | No | No | Yes (manual, no AI) | Yes — automated, AI-generated, approved by user |
| Note generation | No | No | No | Care plan drafts only | Manual only | Yes — source notes, topic notes, research logs |
| Approval before saving | No | No | No | No | N/A (manual) | Yes — explicit gate |
| Source ingestion (PDF/URL) | No (closed corpus) | No (closed corpus) | No (closed corpus) | No (closed corpus) | Manual paste | Yes — PDF upload + URL fetch |
| Local-first / self-hosted | No | No | No | No | Yes | Yes |
| Open-source | No | No | No | No | Yes (core) | Yes (intent) |
| Trusted source scoping | Yes (own corpus only) | Yes (own corpus only) | Broad (35M papers) | Broad | No | Yes (configurable YAML registry) |
| Topic refresh / update detection | No | No | No | No | Manual | Yes (on-demand, diff view) |
| Evidence grading | No | Yes (3-tier) | Paper quality signals | Yes | No | Deferred (source metadata) |
| Drug information | Via Lexicomp integration | Via Micromedex integration | Partial | No | No | Out of scope v1 |
| CME/CPD integration | No | No | Yes (AMA credits) | No | No | Out of scope |
| Offline / air-gap capable | No | No | No | No | Yes | Yes (with Ollama) |
| Pricing | ~$600 USD/yr institutional | Institutional subscription | Free (US verified physicians) | Free tier + paid | Free/paid | Free (self-hosted) |

## Sources

- [iatroX: Best AI Clinical Decision Support Tools 2026](https://www.iatrox.com/blog/best-ai-clinical-decision-support-tools-2026-uptodate-ai-dynamed-iatrox)
- [iatroX: 2025 New Guard of Clinical AI](https://www.iatrox.com/blog/ai-cdss-best-knowledge-retrieval-2025-uptodate-expertai-dyna-ai-clinicalkey-ai-openevidence-glass-health-iatrox)
- [EBSCO: DynaMed vs UpToDate AI Comparison](https://about.ebsco.com/blogs/health-notes/dynamed-vs-uptodate-ai-clinical-decision-support-tools-comparison)
- [PMC: Comparing DynaMed and UpToDate — Randomized Crossover Trial](https://pmc.ncbi.nlm.nih.gov/articles/PMC8810269/)
- [PMC: UpToDate vs DynaMed Speed and Accuracy](https://pmc.ncbi.nlm.nih.gov/articles/PMC8485969/)
- [Glass Health vs OpenEvidence 2026 Comparison](https://glass.health/compare/openevidence)
- [Medium: OpenEvidence AI Clinical Decision-Making](https://medium.com/@davidsehyeonbaek/how-openevidence-is-transforming-clinical-decision-making-with-ai-powered-medical-intelligence-b1b88ad52c54)
- [Obsidian Forum: How to manage knowledge as a medical doctor](https://forum.obsidian.md/t/how-to-manage-knowledge-as-a-medical-doctor/85846)
- [Stanford Lane Library Blog: DynaMed and the Elephant in the Room](https://laneblog.stanford.edu/2024/03/01/dynamed-and-the-elephant-in-the-room/)
- [PMC: Features of Effective Medical Knowledge Resources (Focus Group Study)](https://pmc.ncbi.nlm.nih.gov/articles/PMC3840020/)
- [Cleveland Clinic Journal of Medicine: Staying afloat in a sea of information](https://www.ccjm.org/content/84/3/225)
- [The Excellent Physician: Obsidian](https://www.excellentphysician.com/obsidian)

---
*Feature research for: Clinical knowledge assistant (personal, self-hosted, chat-first)*
*Researched: 2026-04-06*
