"use client"

import { Progress } from "@/components/ui/progress"
import { CheckCircle2 } from "lucide-react"
import type { IngestionProgress } from "@/lib/sse"

interface IngestionProgressProps {
  progress: IngestionProgress | null
  isComplete: boolean
}

/**
 * Maps ingestion status to a percentage for the progress bar.
 * When page/total are available during parsing, interpolates between 30-80%.
 */
function statusToPercent(progress: IngestionProgress | null, isComplete: boolean): number {
  if (isComplete) return 100
  if (!progress) return 0

  switch (progress.status) {
    case "uploading":
      return 10
    case "parsing": {
      if (progress.page && progress.total && progress.total > 0) {
        return 30 + Math.round((progress.page / progress.total) * 50)
      }
      return 50
    }
    case "fetching":
      return 20
    case "extracting":
      return 60
    case "indexing":
      return 90
    default:
      return 0
  }
}

function statusToText(progress: IngestionProgress | null, isComplete: boolean): string {
  if (isComplete) return "Source indexed"
  if (!progress) return ""

  switch (progress.status) {
    case "uploading":
      return "Uploading..."
    case "parsing":
      if (progress.page && progress.total) {
        return `Parsing page ${progress.page} of ${progress.total}...`
      }
      return "Parsing..."
    case "fetching":
      return "Fetching..."
    case "extracting":
      return "Extracting content..."
    case "indexing":
      return "Indexing..."
    default:
      // Handle JS fallback message from backend
      if (progress.message?.includes("Retrying with browser rendering")) {
        return "Retrying with browser rendering..."
      }
      return progress.message || ""
  }
}

export function IngestionProgressDisplay({ progress, isComplete }: IngestionProgressProps) {
  const percent = statusToPercent(progress, isComplete)
  const text = statusToText(progress, isComplete)

  return (
    <div className="space-y-2">
      <Progress
        value={percent}
        role="progressbar"
        aria-valuenow={percent}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label="Ingestion progress"
      />
      <div className="flex items-center gap-2">
        {isComplete && <CheckCircle2 className="h-4 w-4 text-green-500" />}
        <p className={`text-sm ${isComplete ? "text-green-500" : "text-muted-foreground"}`}>
          {text}
        </p>
      </div>
    </div>
  )
}
