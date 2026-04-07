---
phase: 01-foundation
plan: 03
subsystem: ui
tags: [next.js, shadcn-ui, tailwind-v4, next-themes, dark-mode, react-19, vitest]

# Dependency graph
requires: []
provides:
  - Next.js 15 frontend scaffold with App Router and TypeScript
  - shadcn/ui component library (Button, Card, Input, ScrollArea, Separator)
  - Dark mode default via next-themes with UI-SPEC color contract
  - Chat layout skeleton (sidebar + message area)
  - Health polling with graceful backend-unavailable handling
  - Vitest test infrastructure
  - API client pointing to localhost:8000
affects: [chat-streaming, knowledge-base-ui, research-agent-ui]

# Tech tracking
tech-stack:
  added: [next.js 15, react 19, shadcn/ui, next-themes, @tanstack/react-query, zustand, vitest, tailwind v4, lucide-react]
  patterns: [theme-provider-wrapper, health-polling-with-graceful-failure, sidebar-layout-256px, semantic-html-landmarks]

key-files:
  created:
    - frontend/src/app/layout.tsx
    - frontend/src/app/chat/page.tsx
    - frontend/src/components/theme-provider.tsx
    - frontend/src/components/layout/sidebar.tsx
    - frontend/src/components/chat/message-list.tsx
    - frontend/src/components/chat/message-input.tsx
    - frontend/src/lib/api.ts
    - frontend/vitest.config.ts
  modified:
    - frontend/src/app/globals.css
    - frontend/src/app/page.tsx

key-decisions:
  - "Used HSL color values for dark mode overrides (UI-SPEC) while keeping oklch for light mode (shadcn default)"
  - "Inter font with swap display for offline Docker build resilience"
  - "Health polling at 30s intervals with 5s AbortSignal timeout"

patterns-established:
  - "ThemeProvider wrapper: next-themes with attribute=class, defaultTheme=dark"
  - "API client pattern: fetch with AbortSignal.timeout, catch returns safe default"
  - "Sidebar layout: 256px fixed aside with semantic nav, main content max-w-3xl centered"
  - "Component organization: layout/, chat/, ui/ directories under components/"

requirements-completed: [KBSE-01]

# Metrics
duration: 4min
completed: 2026-04-07
---

# Phase 1 Plan 3: Frontend Scaffold Summary

**Next.js 15 chat skeleton with shadcn/ui dark mode, Inter font, sidebar layout, and graceful health polling**

## Performance

- **Duration:** 4 min
- **Started:** 2026-04-07T07:40:49Z
- **Completed:** 2026-04-07T07:45:10Z
- **Tasks:** 2
- **Files modified:** 27 (Task 1) + 5 (Task 2) = 32

## Accomplishments
- Next.js 15 app with React 19, TypeScript, Tailwind v4, and shadcn/ui fully scaffolded
- Dark mode default with UI-SPEC color contract (HSL overrides for dark theme)
- Chat layout skeleton: 256px sidebar with health indicator + theme toggle, centered message area with empty state
- API client with graceful failure handling (returns safe defaults on network error, 404, timeout)

## Task Commits

Each task was committed atomically:

1. **Task 1: Next.js 15 scaffolding with shadcn/ui and dark mode** - `5bb6c12` (feat)
2. **Task 2: Chat layout skeleton with sidebar, message list, and input** - `1639cc6` (feat)

## Files Created/Modified
- `frontend/src/app/layout.tsx` - Root layout with Inter font, ThemeProvider, dark mode default
- `frontend/src/app/globals.css` - UI-SPEC dark mode color overrides
- `frontend/src/app/page.tsx` - Redirect to /chat
- `frontend/src/app/chat/page.tsx` - Chat skeleton composing sidebar + message area
- `frontend/src/components/theme-provider.tsx` - next-themes wrapper component
- `frontend/src/components/layout/sidebar.tsx` - App title, health indicator, theme toggle
- `frontend/src/components/chat/message-list.tsx` - Empty state card with UI-SPEC copy
- `frontend/src/components/chat/message-input.tsx` - Disabled input with placeholder
- `frontend/src/lib/api.ts` - fetchHealth with timeout and graceful failure
- `frontend/vitest.config.ts` - Vitest with jsdom, React plugin, path aliases
- `frontend/src/components/ui/*.tsx` - shadcn Button, Card, Input, ScrollArea, Separator

## Decisions Made
- Used HSL color values for dark mode CSS variable overrides to match UI-SPEC exactly, while keeping shadcn's oklch defaults for light mode
- Inter font loaded with `display: "swap"` for offline Docker build resilience (system font fallback)
- Health polling every 30s with 5s AbortSignal.timeout -- fetchHealth never throws, returns `{ status: "unavailable" }` on any failure

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- `create-next-app` created an embedded `.git` directory inside `frontend/` which had to be removed before committing to the parent repo

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Frontend shell is ready for chat streaming integration (Phase 3)
- shadcn/ui components available for knowledge base browser UI
- Vitest infrastructure ready for component tests
- Health polling will automatically show green when backend starts responding

## Self-Check: PASSED

All 10 key files verified present. Both task commits (5bb6c12, 1639cc6) verified in git log. `pnpm build` exits 0.

---
*Phase: 01-foundation*
*Completed: 2026-04-07*
