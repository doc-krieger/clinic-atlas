---
description: Archive accumulated phase directories from completed milestones
tools:
  read: true
  write: true
  bash: true
  question: true
---
<objective>
Archive phase directories from completed milestones into `.planning/milestones/v{X.Y}-phases/`.

Use when `.planning/phases/` has accumulated directories from past milestones.
</objective>

<execution_context>
@/home/wihan/Projects/clinic-atlas/.opencode/get-shit-done/workflows/cleanup.md
</execution_context>

<process>
Follow the cleanup workflow at @/home/wihan/Projects/clinic-atlas/.opencode/get-shit-done/workflows/cleanup.md.
Identify completed milestones, show a dry-run summary, and archive on confirmation.
</process>
