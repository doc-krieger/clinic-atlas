"use client"

import { Badge } from "@/components/ui/badge"

export interface SourceItem {
  id: number
  title: string | null
  author: string | null
  source_type: string
  parse_status: string
  quality_flags: string[]
  page_count: number | null
  url: string | null
  created_at: string
}

interface SourceListItemProps {
  source: SourceItem
}

function formatRelativeTime(dateStr: string): string {
  const now = Date.now()
  const date = new Date(dateStr).getTime()
  const diffMs = now - date
  const diffMin = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMin < 1) return "just now"
  if (diffMin < 60) return `${diffMin} min ago`
  if (diffHours < 24) return `${diffHours} hours ago`
  return `${diffDays} days ago`
}

function typeBadgeLabel(sourceType: string): string {
  switch (sourceType) {
    case "pdf":
      return "PDF"
    case "url":
      return "URL"
    case "search":
      return "Search"
    default:
      return sourceType
  }
}

function getStatusBadge(source: SourceItem) {
  if (source.quality_flags.includes("scanned_pdf")) {
    return (
      <Badge
        className="bg-yellow-500/10 text-yellow-500"
        aria-label="Status: warning - scanned PDF detected"
      >
        Warning
      </Badge>
    )
  }
  if (source.quality_flags.includes("thin_content")) {
    return (
      <Badge
        className="bg-yellow-500/10 text-yellow-500"
        aria-label="Status: warning - limited content"
      >
        Warning
      </Badge>
    )
  }
  if (source.parse_status === "failed") {
    return <Badge variant="destructive">Failed</Badge>
  }
  return <Badge variant="secondary">Indexed</Badge>
}

export function SourceListItem({ source }: SourceListItemProps) {
  return (
    <div className="flex items-center gap-3 py-2">
      <p className="flex-1 truncate text-sm">{source.title || "Untitled"}</p>
      <Badge variant="outline">{typeBadgeLabel(source.source_type)}</Badge>
      {getStatusBadge(source)}
      <span className="text-xs text-muted-foreground whitespace-nowrap">
        {formatRelativeTime(source.created_at)}
      </span>
    </div>
  )
}
