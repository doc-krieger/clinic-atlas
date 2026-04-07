"use client"

import { useEffect, useState } from "react"
import { Skeleton } from "@/components/ui/skeleton"
import { API_URL } from "@/lib/api"
import { SourceListItem, type SourceItem } from "./source-list-item"

interface SourceListProps {
  refreshKey: number
}

export function SourceList({ refreshKey }: SourceListProps) {
  const [sources, setSources] = useState<SourceItem[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false

    async function fetchSources() {
      setLoading(true)
      try {
        const res = await fetch(`${API_URL}/api/sources`)
        if (!res.ok) {
          setSources([])
          return
        }
        const data = await res.json()
        if (!cancelled) {
          setSources(data.sources || [])
        }
      } catch {
        if (!cancelled) setSources([])
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    fetchSources()
    return () => {
      cancelled = true
    }
  }, [refreshKey])

  if (loading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="flex items-center gap-3 py-2">
            <Skeleton className="h-4 w-48" />
            <Skeleton className="h-4 w-16" />
            <Skeleton className="h-4 w-24" />
          </div>
        ))}
      </div>
    )
  }

  if (sources.length === 0) {
    return (
      <div className="py-8 text-center">
        <p className="text-sm font-medium">No sources yet</p>
        <p className="text-xs text-muted-foreground mt-1">
          Upload a PDF, fetch a URL, or search trusted sources to start building your
          knowledge base.
        </p>
      </div>
    )
  }

  return (
    <div className="divide-y divide-border">
      {sources.map((source) => (
        <SourceListItem key={source.id} source={source} />
      ))}
    </div>
  )
}
