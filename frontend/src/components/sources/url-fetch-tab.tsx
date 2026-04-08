"use client"

import { useState, useRef } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { postSSE } from "@/lib/sse"
import type { IngestionProgress } from "@/lib/sse"
import { IngestionProgressDisplay } from "./ingestion-progress"
import { QualityWarning } from "./quality-warning"

type FetchState = "idle" | "fetching" | "complete" | "error" | "warning"

interface UrlFetchTabProps {
  onSourceAdded: () => void
}

function isValidUrl(value: string): boolean {
  try {
    new URL(value)
    return true
  } catch {
    return false
  }
}

export function UrlFetchTab({ onSourceAdded }: UrlFetchTabProps) {
  const [url, setUrl] = useState("")
  const [urlError, setUrlError] = useState("")
  const [state, setState] = useState<FetchState>("idle")
  const [progress, setProgress] = useState<IngestionProgress | null>(null)
  const [errorMessage, setErrorMessage] = useState("")
  const [warningMessage, setWarningMessage] = useState("")
  const abortControllerRef = useRef<AbortController | null>(null)

  const handleBlur = () => {
    if (url && !isValidUrl(url)) {
      setUrlError("Enter a valid URL.")
    } else {
      setUrlError("")
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!isValidUrl(url)) {
      setUrlError("Enter a valid URL.")
      return
    }

    setState("fetching")
    setProgress(null)
    setErrorMessage("")
    setWarningMessage("")

    const controller = new AbortController()
    abortControllerRef.current = controller

    try {
      await postSSE(
        "/api/sources/fetch",
        JSON.stringify({ url }),
        {
          onProgress: (data) => setProgress(data),
          onComplete: (data) => {
            // Always refresh source list -- source was stored regardless of warnings
            onSourceAdded()
            if (data.quality_flags.includes("thin_content")) {
              setState("warning")
              setWarningMessage(
                "Content appears limited -- the page may require authentication."
              )
            } else if (data.quality_flags.includes("js_fallback_used")) {
              // JS fallback was used but content is OK
              setState("complete")
            } else {
              setState("complete")
            }
          },
          onError: (error) => {
            setState("error")
            setErrorMessage(
              error || "Could not fetch this URL. Check the address and try again."
            )
          },
        },
        controller.signal,
        { headers: { "Content-Type": "application/json" } }
      )
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") {
        setState("idle")
      } else {
        setState("error")
        setErrorMessage("Could not fetch this URL. Check the address and try again.")
      }
    }
  }

  const handleReset = () => {
    abortControllerRef.current?.abort()
    setState("idle")
    setUrl("")
    setProgress(null)
    setErrorMessage("")
    setWarningMessage("")
  }

  return (
    <div className="mt-4 space-y-4">
      {state === "idle" && (
        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <Input
              type="text"
              placeholder="https://cps.ca/..."
              value={url}
              onChange={(e) => {
                setUrl(e.target.value)
                if (urlError) setUrlError("")
              }}
              onBlur={handleBlur}
              className={urlError ? "border-destructive" : ""}
            />
            {urlError && (
              <p className="text-xs text-destructive mt-1">{urlError}</p>
            )}
          </div>
          <Button type="submit" disabled={!url || !!urlError}>
            Fetch
          </Button>
        </form>
      )}

      {state === "fetching" && (
        <IngestionProgressDisplay progress={progress} isComplete={false} />
      )}

      {state === "complete" && (
        <>
          <IngestionProgressDisplay progress={progress} isComplete={true} />
          <Button variant="outline" size="sm" onClick={handleReset}>
            Fetch another
          </Button>
        </>
      )}

      {state === "warning" && (
        <>
          <IngestionProgressDisplay progress={progress} isComplete={true} />
          <QualityWarning variant="warning" message={warningMessage} />
          <Button
            variant="outline"
            size="sm"
            onClick={handleReset}
          >
            Fetch another
          </Button>
        </>
      )}

      {state === "error" && (
        <>
          <QualityWarning variant="error" message={errorMessage} />
          <Button variant="outline" size="sm" onClick={handleReset}>
            Try again
          </Button>
        </>
      )}
    </div>
  )
}
