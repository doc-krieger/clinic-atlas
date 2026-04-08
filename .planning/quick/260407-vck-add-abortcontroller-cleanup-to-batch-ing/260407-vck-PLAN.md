---
phase: quick
plan: 260407-vck
type: execute
wave: 1
depends_on: []
files_modified:
  - frontend/src/components/sources/search-tab.tsx
autonomous: true
must_haves:
  truths:
    - "Batch ingestion SSE calls are aborted when the SearchTab component unmounts"
    - "State setters do not fire after the component unmounts or after abort"
  artifacts:
    - path: "frontend/src/components/sources/search-tab.tsx"
      provides: "AbortController lifecycle for batch ingestion"
      contains: "useRef<AbortController"
  key_links:
    - from: "search-tab.tsx useEffect cleanup"
      to: "AbortController.abort()"
      via: "controllerRef.current?.abort()"
      pattern: "controllerRef\\.current\\?.abort"
---

<objective>
Add AbortController cleanup to batch ingestion in SearchTab to prevent state updates after unmount.

Purpose: Prevents React "Can't perform a React state update on an unmounted component" warnings and potential memory leaks when the user navigates away during batch ingestion.
Output: Updated search-tab.tsx with proper abort/cleanup lifecycle.
</objective>

<execution_context>
@/home/wihan/Projects/clinic-atlas/.claude/get-shit-done/workflows/execute-plan.md
@/home/wihan/Projects/clinic-atlas/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@frontend/src/components/sources/search-tab.tsx
@frontend/src/lib/sse.ts
</context>

<tasks>

<task type="auto">
  <name>Task 1: Add AbortController lifecycle to SearchTab batch ingestion</name>
  <files>frontend/src/components/sources/search-tab.tsx</files>
  <action>
1. Add `useRef` and `useEffect` to the import from "react" (line 3).

2. Add a ref after the existing useState declarations (after line 28):
   ```ts
   const controllerRef = useRef<AbortController | null>(null)
   ```

3. Add a useEffect for cleanup (after the ref declaration):
   ```ts
   useEffect(() => {
     return () => {
       controllerRef.current?.abort()
     }
   }, [])
   ```

4. In `handleIngestSelected`, at the start (line 79, after `const urls = ...`):
   - Abort any existing controller: `controllerRef.current?.abort()`
   - Create a new one: `controllerRef.current = new AbortController()`
   - Capture the signal: `const signal = controllerRef.current.signal`

5. Replace `undefined` (line 98) with `signal` in the `postSSE` call.

6. Guard the callbacks against aborted signal. Wrap the body of `onComplete` and `onError` callbacks:
   ```ts
   onComplete: (data) => {
     if (signal.aborted) return
     const status = data.quality_flags.length > 0 ? "warning" : "done"
     setIngestionState((prev) => new Map(prev).set(urls[i], status))
   },
   onError: () => {
     if (signal.aborted) return
     setIngestionState((prev) => new Map(prev).set(urls[i], "error"))
   },
   ```

7. Guard the post-loop state updates (lines 103-104). Wrap them:
   ```ts
   if (!signal.aborted) {
     setIngestionProgress(null)
     onSourceAdded()
   }
   ```

8. Handle the AbortError from `postSSE` — the `fetch()` inside `postSSE` will throw when aborted. Wrap the for-loop body in a try/catch that breaks on AbortError:
   ```ts
   try {
     await postSSE(...)
   } catch (err) {
     if (err instanceof DOMException && err.name === "AbortError") break
     throw err
   }
   ```

9. Clear the ref after the loop completes or breaks:
   ```ts
   controllerRef.current = null
   ```
  </action>
  <verify>
    <automated>cd /home/wihan/Projects/clinic-atlas && make test-frontend 2>&1 | tail -20</automated>
  </verify>
  <done>
    - `useRef<AbortController | null>` declared and used
    - `useEffect` cleanup calls `abort()` on unmount
    - `postSSE` receives `signal` instead of `undefined`
    - `onComplete`, `onError`, and post-loop state updates are guarded with `signal.aborted`
    - AbortError from fetch is caught and breaks the loop gracefully
  </done>
</task>

</tasks>

<verification>
- Frontend compiles without errors: `cd frontend && pnpm build`
- No lint errors: `cd frontend && pnpm lint`
- Existing tests pass: `make test-frontend`
</verification>

<success_criteria>
- SearchTab aborts in-flight SSE requests on unmount
- No state updates occur after abort/unmount
- AbortError is handled gracefully (no unhandled promise rejections)
- Existing functionality unchanged when component stays mounted
</success_criteria>

<output>
After completion, create `.planning/quick/260407-vck-add-abortcontroller-cleanup-to-batch-ing/260407-vck-SUMMARY.md`
</output>
