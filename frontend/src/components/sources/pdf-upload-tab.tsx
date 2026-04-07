"use client"

import { useRef, useState, useCallback } from "react"
import { Upload } from "lucide-react"
import { Button } from "@/components/ui/button"
import { postSSE } from "@/lib/sse"
import type { IngestionProgress, IngestionComplete } from "@/lib/sse"
import { IngestionProgressDisplay } from "./ingestion-progress"
import { QualityWarning } from "./quality-warning"

type UploadState = "idle" | "uploading" | "complete" | "error" | "warning" | "duplicate"

interface PdfUploadTabProps {
  onSourceAdded: () => void
}

export function PdfUploadTab({ onSourceAdded }: PdfUploadTabProps) {
  const [state, setState] = useState<UploadState>("idle")
  const [progress, setProgress] = useState<IngestionProgress | null>(null)
  const [errorMessage, setErrorMessage] = useState("")
  const [, setCompleteData] = useState<IngestionComplete | null>(null)
  const [isDragOver, setIsDragOver] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const abortControllerRef = useRef<AbortController | null>(null)

  const handleFile = useCallback(
    async (file: File) => {
      // Client-side size validation: 50 MB limit (D-03)
      if (file.size > 50 * 1024 * 1024) {
        setState("error")
        setErrorMessage("This file exceeds the 50 MB limit.")
        return
      }

      setState("uploading")
      setProgress(null)
      setErrorMessage("")
      setCompleteData(null)

      const controller = new AbortController()
      abortControllerRef.current = controller

      const fd = new FormData()
      fd.append("file", file)

      try {
        await postSSE(
          "/api/sources/upload",
          fd,
          {
            onProgress: (data) => setProgress(data),
            onComplete: (data) => {
              setCompleteData(data)
              onSourceAdded()
              if (data.quality_flags.includes("scanned_pdf")) {
                setState("warning")
              } else {
                setState("complete")
              }
            },
            onError: (error, existingSourceId) => {
              if (existingSourceId) {
                setState("duplicate")
                setErrorMessage("This document has already been ingested.")
              } else {
                setState("error")
                setErrorMessage(error || "Upload failed")
              }
            },
          },
          controller.signal
        )
      } catch (err) {
        if (err instanceof DOMException && err.name === "AbortError") {
          setState("idle")
        } else {
          setState("error")
          setErrorMessage("Upload failed. Please try again.")
        }
      }
    },
    [onSourceAdded]
  )

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      setIsDragOver(false)
      const file = e.dataTransfer.files[0]
      if (file && file.type === "application/pdf") {
        handleFile(file)
      }
    },
    [handleFile]
  )

  const handleFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0]
      if (file) handleFile(file)
      // Reset input so the same file can be re-selected
      e.target.value = ""
    },
    [handleFile]
  )

  const handleReset = () => {
    abortControllerRef.current?.abort()
    setState("idle")
    setProgress(null)
    setErrorMessage("")
    setCompleteData(null)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault()
      fileInputRef.current?.click()
    }
  }

  if (state === "idle") {
    return (
      <div className="mt-4">
        <div
          role="button"
          aria-label="Upload PDF file"
          tabIndex={0}
          onClick={() => fileInputRef.current?.click()}
          onKeyDown={handleKeyDown}
          onDragOver={(e) => {
            e.preventDefault()
            setIsDragOver(true)
          }}
          onDragLeave={() => setIsDragOver(false)}
          onDrop={handleDrop}
          className={`flex min-h-[160px] cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed transition-colors ${
            isDragOver
              ? "border-primary bg-primary/5"
              : "border-border hover:border-muted-foreground"
          }`}
        >
          <Upload className="h-8 w-8 text-muted-foreground mb-2" />
          <p className="text-sm font-medium">Drop a PDF here</p>
          <p className="text-xs text-muted-foreground">or click to browse. Max 50 MB.</p>
        </div>
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf"
          className="hidden"
          onChange={handleFileChange}
        />
      </div>
    )
  }

  return (
    <div className="mt-4 space-y-4">
      {(state === "uploading") && (
        <IngestionProgressDisplay progress={progress} isComplete={false} />
      )}

      {state === "complete" && (
        <>
          <IngestionProgressDisplay progress={progress} isComplete={true} />
          <Button variant="outline" size="sm" onClick={handleReset}>
            Upload another
          </Button>
        </>
      )}

      {state === "warning" && (
        <>
          <IngestionProgressDisplay progress={progress} isComplete={true} />
          <QualityWarning
            variant="warning"
            message="This PDF appears to contain scanned images. Text extraction may be incomplete."
          />
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              onSourceAdded()
              handleReset()
            }}
          >
            Upload another
          </Button>
        </>
      )}

      {state === "duplicate" && (
        <>
          <QualityWarning variant="error" message={errorMessage} />
          <Button variant="outline" size="sm" onClick={handleReset}>
            Try another file
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
