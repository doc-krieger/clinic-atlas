"use client"

import { Checkbox } from "@/components/ui/checkbox"
import { Badge } from "@/components/ui/badge"
import { Loader2, CheckCircle2, AlertTriangle, XCircle } from "lucide-react"

export interface SearchResult {
  title: string
  url: string
  snippet: string
  domain: string
}

interface SearchResultItemProps {
  result: SearchResult
  selected: boolean
  onToggle: () => void
  ingestionStatus?: "pending" | "ingesting" | "done" | "warning" | "error"
  disabled?: boolean
}

export function SearchResultItem({
  result,
  selected,
  onToggle,
  ingestionStatus,
  disabled,
}: SearchResultItemProps) {
  const checkboxId = `search-result-${encodeURIComponent(result.url)}`

  return (
    <div className="flex items-start gap-3 py-3">
      <Checkbox
        id={checkboxId}
        checked={selected}
        onCheckedChange={onToggle}
        disabled={disabled}
        className="mt-0.5"
      />
      <label htmlFor={checkboxId} className="flex-1 min-w-0 cursor-pointer">
        <p className="text-sm text-primary truncate">{result.title}</p>
        <div className="flex items-center gap-2 mt-0.5">
          <Badge variant="outline" className="text-xs">
            {result.domain}
          </Badge>
        </div>
        <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
          {result.snippet}
        </p>
      </label>
      <div className="flex-shrink-0 mt-0.5">
        {ingestionStatus === "ingesting" && (
          <Loader2 className="animate-spin h-4 w-4 text-muted-foreground" />
        )}
        {ingestionStatus === "done" && (
          <CheckCircle2 className="h-4 w-4 text-green-500" />
        )}
        {ingestionStatus === "warning" && (
          <AlertTriangle className="h-4 w-4 text-yellow-500" />
        )}
        {ingestionStatus === "error" && (
          <XCircle className="h-4 w-4 text-destructive" />
        )}
      </div>
    </div>
  )
}
