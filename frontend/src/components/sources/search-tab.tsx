"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Loader2 } from "lucide-react"
import { API_URL } from "@/lib/api"
import { postSSE } from "@/lib/sse"
import { SearchResultItem, type SearchResult } from "./search-result-item"

interface SearchTabProps {
  onSourceAdded: () => void
}

export function SearchTab({ onSourceAdded }: SearchTabProps) {
  const [query, setQuery] = useState("")
  const [results, setResults] = useState<SearchResult[]>([])
  const [selectedUrls, setSelectedUrls] = useState<Set<string>>(new Set())
  const [searchLoading, setSearchLoading] = useState(false)
  const [searchDone, setSearchDone] = useState(false)
  const [ingestionState, setIngestionState] = useState<
    Map<string, "pending" | "ingesting" | "done" | "warning" | "error">
  >(new Map())
  const [ingestionProgress, setIngestionProgress] = useState<{
    current: number
    total: number
  } | null>(null)

  const isIngesting = ingestionProgress !== null

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim()) return

    setSearchLoading(true)
    setResults([])
    setSelectedUrls(new Set())
    setIngestionState(new Map())
    setIngestionProgress(null)
    setSearchDone(false)

    try {
      const res = await fetch(`${API_URL}/api/sources/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: query.trim(), limit: 10 }),
      })
      if (res.ok) {
        const data = await res.json()
        setResults(data.results || [])
      } else {
        setResults([])
      }
    } catch {
      setResults([])
    } finally {
      setSearchLoading(false)
      setSearchDone(true)
    }
  }

  const toggleUrl = (url: string) => {
    setSelectedUrls((prev) => {
      const next = new Set(prev)
      if (next.has(url)) {
        next.delete(url)
      } else {
        next.add(url)
      }
      return next
    })
  }

  const handleIngestSelected = async () => {
    const urls = Array.from(selectedUrls)
    setIngestionProgress({ current: 0, total: urls.length })

    for (let i = 0; i < urls.length; i++) {
      setIngestionProgress({ current: i + 1, total: urls.length })
      setIngestionState((prev) => new Map(prev).set(urls[i], "ingesting"))

      await postSSE(
        "/api/sources/fetch",
        JSON.stringify({ url: urls[i] }),
        {
          onComplete: (data) => {
            const status = data.quality_flags.length > 0 ? "warning" : "done"
            setIngestionState((prev) => new Map(prev).set(urls[i], status))
          },
          onError: () => {
            setIngestionState((prev) => new Map(prev).set(urls[i], "error"))
          },
        },
        undefined, // no abort signal for batch -- runs to completion
        { headers: { "Content-Type": "application/json" } }
      )
    }

    setIngestionProgress(null)
    onSourceAdded()
  }

  return (
    <div className="mt-4 space-y-4">
      <form onSubmit={handleSearch} className="space-y-3">
        <div>
          <Input
            type="text"
            placeholder="Search trusted sources..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <p className="text-xs text-muted-foreground mt-1">
            Results scoped to trusted source domains
          </p>
        </div>
        <Button type="submit" disabled={!query.trim() || searchLoading}>
          Search
        </Button>
      </form>

      {searchLoading && (
        <div className="flex items-center justify-center gap-2 py-8">
          <Loader2 className="animate-spin h-4 w-4 text-muted-foreground" />
          <p className="text-sm text-muted-foreground">Searching...</p>
        </div>
      )}

      {!searchLoading && searchDone && results.length === 0 && (
        <p className="text-sm text-muted-foreground py-4">
          No results found. Try different search terms.
        </p>
      )}

      {results.length > 0 && (
        <div>
          <div className="divide-y divide-border">
            {results.map((result) => (
              <SearchResultItem
                key={result.url}
                result={result}
                selected={selectedUrls.has(result.url)}
                onToggle={() => toggleUrl(result.url)}
                ingestionStatus={ingestionState.get(result.url)}
                disabled={isIngesting}
              />
            ))}
          </div>

          <div className="flex items-center gap-3 mt-4">
            <Button
              onClick={handleIngestSelected}
              disabled={selectedUrls.size === 0 || isIngesting}
            >
              {isIngesting
                ? `Ingesting ${ingestionProgress?.current} of ${ingestionProgress?.total}...`
                : `Ingest ${selectedUrls.size} selected`}
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
