# Phase 1: Foundation - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-07
**Phase:** 01-foundation
**Areas discussed:** Database schema, Medical synonyms, Disk layout, Source registry, Docker Compose setup, FastAPI project structure, Frontend bootstrapping, SearXNG configuration

---

## Database Schema

| Option | Description | Selected |
|--------|-------------|----------|
| Unified notes table | Single table with type column, one FTS index | ✓ |
| Separate tables per note type | Distinct tables, FTS across all three | |
| Notes + raw sources split | Separate raw_sources table for input material | |

**User's choice:** Unified notes table
**Notes:** None

| Option | Description | Selected |
|--------|-------------|----------|
| Separate raw_sources table | Input material tracked separately, FK from notes | ✓ |
| Everything in notes table | Raw sources as another note type | |
| You decide | Claude picks | |

**User's choice:** Separate raw_sources table

| Option | Description | Selected |
|--------|-------------|----------|
| Junction table | note_sources with page/section/quote metadata | ✓ |
| JSONB array on notes | Source references as JSON array | |
| You decide | Claude picks | |

**User's choice:** Junction table

| Option | Description | Selected |
|--------|-------------|----------|
| Slug + status + tags | Full metadata columns | ✓ |
| Minimal — just slug + status | Lean approach | |
| You decide | Claude picks | |

**User's choice:** Slug + status + tags

| Option | Description | Selected |
|--------|-------------|----------|
| Postgres table | research_sessions with JSONB chat log | ✓ |
| Disk as markdown | Research logs as note files on disk | |
| You decide | Claude picks | |

**User's choice:** Postgres table

| Option | Description | Selected |
|--------|-------------|----------|
| Alembic from the start | Schema changes tracked from day one | ✓ |
| create_all now, Alembic later | Simple bootstrap, add migrations later | |
| You decide | Claude picks | |

**User's choice:** Alembic from the start

| Option | Description | Selected |
|--------|-------------|----------|
| GENERATED ALWAYS AS | Stored generated column, auto-updates | ✓ |
| Application-managed trigger | Trigger on INSERT/UPDATE, more flexible | |
| You decide | Claude picks | |

**User's choice:** GENERATED ALWAYS AS

| Option | Description | Selected |
|--------|-------------|----------|
| Yes — title weight A, content weight D | Weighted tsvector for ranking | ✓ |
| No — equal weight for now | Unweighted, simpler | |
| You decide | Claude picks | |

**User's choice:** Yes — title weight A, content weight D

| Option | Description | Selected |
|--------|-------------|----------|
| Store extracted text in DB | Content column + metadata, enables FTS on raw sources | ✓ |
| Metadata only, text on disk | DB stores paths, text on disk | |
| You decide | Claude picks | |

**User's choice:** Store extracted text in DB

| Option | Description | Selected |
|--------|-------------|----------|
| FTS on both | Index raw_sources and notes with tsvector + GIN | ✓ |
| Notes only | Only index compiled notes | |
| You decide | Claude picks | |

**User's choice:** FTS on both

| Option | Description | Selected |
|--------|-------------|----------|
| Page + section + quote excerpt | Granular citation metadata on junction table | ✓ |
| Just the link, no granular metadata | Foreign key only | |
| You decide | Claude picks | |

**User's choice:** Page + section + quote excerpt

| Option | Description | Selected |
|--------|-------------|----------|
| Add version column now | Integer version counter for future refresh/diff | ✓ |
| Defer — handle in Phase 7 | Keep schema minimal, add later | |
| You decide | Claude picks | |

**User's choice:** Add version column now

---

## Medical Synonyms

| Option | Description | Selected |
|--------|-------------|----------|
| Custom Postgres thesaurus dictionary | Thesaurus file mapping abbreviations to expanded terms | ✓ |
| Runtime query expansion in Python | Python dict/table, expand before tsquery | |
| Postgres synonym file (simple) | Built-in synonym dict, one-to-one mapping | |
| You decide | Claude picks | |

**User's choice:** Custom Postgres thesaurus dictionary

| Option | Description | Selected |
|--------|-------------|----------|
| Comprehensive (~500+) | Published-scale abbreviation coverage | ✓ |
| Common clinical (~50-100) | Most frequent abbreviations | |
| Minimal seed (~20) | Handful, grow organically | |
| You decide | Claude picks | |

**User's choice:** Comprehensive (~500+)

| Option | Description | Selected |
|--------|-------------|----------|
| Expand to all meanings | HTN → all meanings, recall over precision | ✓ |
| Pick most common meaning only | Single mapping per abbreviation | |
| You decide | Claude picks | |

**User's choice:** Expand to all meanings

| Option | Description | Selected |
|--------|-------------|----------|
| Static file in repo | config/medical_thesaurus.ths, version-controlled | ✓ |
| Editable via API endpoint | Runtime admin endpoint for synonym management | |
| You decide | Claude picks | |

**User's choice:** Static file in repo

| Option | Description | Selected |
|--------|-------------|----------|
| Yes — include spelling variants | Canadian/British spelling normalization | ✓ |
| No — abbreviations only | Focus on abbreviation expansion | |
| You decide | Claude picks | |

**User's choice:** Yes — include spelling variants

| Option | Description | Selected |
|--------|-------------|----------|
| Index time | Thesaurus applied when building tsvectors | ✓ |
| Query time only | Thesaurus applied to search queries | |
| Both index and query time | Applied at both stages | |
| You decide | Claude picks | |

**User's choice:** Index time

| Option | Description | Selected |
|--------|-------------|----------|
| LLM-generated seed list | Claude generates comprehensive abbreviation list | ✓ |
| Published medical abbreviation database | Pull from UMLS or published lists | |
| Manual curation by user | Physician curates from clinical experience | |
| You decide | Claude picks | |

**User's choice:** LLM-generated seed list

---

## Disk Layout

| Option | Description | Selected |
|--------|-------------|----------|
| Flat by type | notes/topics/, notes/sources/, notes/logs/ | ✓ |
| Nested by topic category | notes/cardiology/, notes/obstetrics/ | |
| Single flat directory | All notes in one notes/ directory | |
| You decide | Claude picks | |

**User's choice:** Flat by type

| Option | Description | Selected |
|--------|-------------|----------|
| Full metadata set | title, slug, type, status, tags, created, updated, version, sources | ✓ |
| Minimal — title, type, dates only | Lean frontmatter | |
| You decide | Claude picks | |

**User's choice:** Full metadata set

| Option | Description | Selected |
|--------|-------------|----------|
| data/sources/ directory | Separate from notes, content hash dedup | ✓ |
| Same notes directory tree | Source files alongside extracted markdown | |
| You decide | Claude picks | |

**User's choice:** data/sources/ directory

| Option | Description | Selected |
|--------|-------------|----------|
| Docker volume, outside repo | Mount as Docker volumes, survives rebuilds | ✓ |
| Inside repo, gitignored | In project dir but gitignored | |
| You decide | Claude picks | |

**User's choice:** Docker volume, outside repo

| Option | Description | Selected |
|--------|-------------|----------|
| Title-based slug | Slugify the title, collision suffix | ✓ |
| UUID-based | Opaque filenames | |
| Date + title hybrid | Chronologically sortable | |
| You decide | Claude picks | |

**User's choice:** Title-based slug

| Option | Description | Selected |
|--------|-------------|----------|
| Full reindex endpoint | POST /api/reindex rebuilds Postgres from disk | ✓ |
| Integrity check only | Report differences, don't fix | |
| You decide | Claude picks | |

**User's choice:** Full reindex endpoint

| Option | Description | Selected |
|--------|-------------|----------|
| Auto-create on startup | FastAPI startup checks/creates directories | ✓ |
| CLI setup command | Manual make init step | |
| You decide | Claude picks | |

**User's choice:** Auto-create on startup

| Option | Description | Selected |
|--------|-------------|----------|
| Env vars with sensible defaults | CLINIC_ATLAS_NOTES_DIR, overridable | ✓ |
| Hardcoded paths | Always /data/notes, /data/sources | |
| You decide | Claude picks | |

**User's choice:** Env vars with sensible defaults

| Option | Description | Selected |
|--------|-------------|----------|
| Yes — atomic writes | Write to .tmp, fsync, rename | ✓ |
| Direct writes are fine | Just write to file directly | |
| You decide | Claude picks | |

**User's choice:** Yes — atomic writes

| Option | Description | Selected |
|--------|-------------|----------|
| Bind mounts for dev | Mount host dirs into containers | ✓ |
| Named volumes always | Named Docker volumes in dev and prod | |
| You decide | Claude picks | |

**User's choice:** Bind mounts for dev

| Option | Description | Selected |
|--------|-------------|----------|
| Yes — validate and report issues | Reindex validates frontmatter, flags issues non-blocking | ✓ |
| No — just sync what's there | Trust files, skip/default on malformed | |
| You decide | Claude picks | |

**User's choice:** Yes — validate and report issues

| Option | Description | Selected |
|--------|-------------|----------|
| Yes — comprehensive health endpoint | GET /api/health reports all service dependencies | ✓ |
| Basic liveness only | 200 if FastAPI is running | |
| You decide | Claude picks | |

**User's choice:** Yes — comprehensive health endpoint

---

## Source Registry

| Option | Description | Selected |
|--------|-------------|----------|
| Rich metadata | name, domain, category, base_url, search_url_pattern, requires_auth, notes | ✓ |
| Minimal — name + domain only | Just source name and domain | |
| You decide | Claude picks | |

**User's choice:** Rich metadata

| Option | Description | Selected |
|--------|-------------|----------|
| Grouped by category | Top-level keys are categories | ✓ |
| Flat list of sources | Single list with category field | |
| You decide | Claude picks | |

**User's choice:** Grouped by category

| Option | Description | Selected |
|--------|-------------|----------|
| Yes — pre-populated Canadian sources | CPS, SOGC, Choosing Wisely, UpToDate, etc. | ✓ |
| Empty template with examples | Example entry, user populates | |
| You decide | Claude picks | |

**User's choice:** Yes — pre-populated Canadian sources

| Option | Description | Selected |
|--------|-------------|----------|
| Validate and warn, don't crash | Log warnings, load valid entries | ✓ |
| Strict — fail on invalid config | Refuse to start on malformed YAML | |
| You decide | Claude picks | |

**User's choice:** Validate and warn, don't crash

| Option | Description | Selected |
|--------|-------------|----------|
| Fixed path with env override | config/sources.yml, CLINIC_ATLAS_SOURCES_FILE override | ✓ |
| Always config/sources.yml | Hardcoded | |
| You decide | Claude picks | |

**User's choice:** Fixed path with env override

| Option | Description | Selected |
|--------|-------------|----------|
| Yes — add a reliability tier | authoritative/reference/supplementary ranking | ✓ |
| No — all sources equal | Everything in registry is equally valid | |
| You decide | Claude picks | |

**User's choice:** Yes — add a reliability tier

---

## LLM Provider Configuration

**User's input:** Currently serves models with llama-serve (llama.cpp). Wanted to know if it could be added as a provider.

**Claude's analysis:** llama-server exposes an OpenAI-compatible API; litellm supports it via `openai/` prefix. Tool use support depends on model and llama.cpp version.

**User's choice:** Add as optional provider alongside Ollama (Ollama stays default, llama-server via LLAMA_SERVER_URL env var)

---

## Docker Compose Setup

| Option | Description | Selected |
|--------|-------------|----------|
| No profiles — all services always | Single docker compose up | ✓ |
| Profiles for optional services | Core stack default, --profile full for LLM/search | |
| You decide | Claude picks | |

**User's choice:** No profiles — all services always

| Option | Description | Selected |
|--------|-------------|----------|
| Bind mount source code + watchers | Hot-reload via bind mounts | ✓ |
| Rebuild containers on change | No bind mounts, rebuild on change | |
| You decide | Claude picks | |

**User's choice:** Bind mount source code + watchers

| Option | Description | Selected |
|--------|-------------|----------|
| Yes — healthchecks + depends_on | All services with healthchecks, proper ordering | ✓ |
| Basic depends_on only | No healthchecks, just ordering | |
| You decide | Claude picks | |

**User's choice:** Yes — healthchecks + depends_on

| Option | Description | Selected |
|--------|-------------|----------|
| Standard ports | 3000, 8000, 5432, 11434, 8888 | ✓ |
| Offset ports | 3100, 8100, 5433 to avoid conflicts | |
| You decide | Claude picks | |

**User's choice:** Standard ports

---

## FastAPI Project Structure

| Option | Description | Selected |
|--------|-------------|----------|
| Feature-based modules | app/notes/, app/sources/, app/search/, app/health/ | ✓ |
| Flat module layout | All files at top level | |
| You decide | Claude picks | |

**User's choice:** Feature-based modules

| Option | Description | Selected |
|--------|-------------|----------|
| Pydantic BaseSettings with .env | Single Settings class, env vars + .env fallback | ✓ |
| YAML config file | Structured YAML for all settings | |
| You decide | Claude picks | |

**User's choice:** Pydantic BaseSettings with .env

| Option | Description | Selected |
|--------|-------------|----------|
| /api/ without versioning | No /v1/ prefix | ✓ |
| /api/v1/ with versioning | Version prefix for future-proofing | |
| You decide | Claude picks | |

**User's choice:** /api/ without versioning

---

## Frontend Bootstrapping

| Option | Description | Selected |
|--------|-------------|----------|
| Chat layout skeleton | Sidebar + main area, /chat route, placeholder components | ✓ |
| Minimal shell — just landing page | App name + health status only | |
| You decide | Claude picks | |

**User's choice:** Chat layout skeleton

| Option | Description | Selected |
|--------|-------------|----------|
| Dark mode default, clinical-clean | Dark BG, muted accents, high contrast, Linear/Raycast feel | ✓ |
| Light mode default, professional | Light BG, clean typography, UpToDate feel | |
| System preference with both modes | Follow OS preference | |
| You decide | Claude picks | |

**User's choice:** Dark mode default, clinical-clean

| Option | Description | Selected |
|--------|-------------|----------|
| Direct to FastAPI with CORS | Browser calls FastAPI directly, CORS allows frontend origin | ✓ |
| Next.js API route proxy | Proxy through Next.js | |
| You decide | Claude picks | |

**User's choice:** Direct to FastAPI with CORS

| Option | Description | Selected |
|--------|-------------|----------|
| Init + a few base components | Button, Card, Input, ScrollArea, Separator | ✓ |
| Just init, no components yet | Setup only, add components later | |
| You decide | Claude picks | |

**User's choice:** Init + a few base components

---

## SearXNG Configuration

| Option | Description | Selected |
|--------|-------------|----------|
| Google + Bing + DuckDuckGo | Multiple engines for redundancy | ✓ |
| Google only | Best coverage but single point of failure | |
| DuckDuckGo only | Privacy-first | |
| You decide | Claude picks | |

**User's choice:** Google + Bing + DuckDuckGo

| Option | Description | Selected |
|--------|-------------|----------|
| JSON API + web UI both | Web UI for debugging, JSON for programmatic access | ✓ |
| JSON API only | Disable web UI | |
| You decide | Claude picks | |

**User's choice:** JSON API + web UI both

| Option | Description | Selected |
|--------|-------------|----------|
| Checked into repo, mounted into container | Version-controlled settings.yml | ✓ |
| Generated at first startup | Random secret key at startup | |
| You decide | Claude picks | |

**User's choice:** Checked into repo, mounted into container

---

## Claude's Discretion

- Loading skeleton design and exact spacing/typography
- Exact Tailwind color palette within the dark-mode clinical-clean direction
- Alembic configuration details (env.py, migration naming)
- Docker Compose network naming and internal service hostnames
- Exact tsvector concatenation formula
- Pydantic settings field naming and grouping

## Deferred Ideas

None — discussion stayed within phase scope
