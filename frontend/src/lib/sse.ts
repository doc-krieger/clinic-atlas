import { API_URL } from "./api"

export interface SSECallbacks {
  onProgress?: (data: IngestionProgress) => void
  onComplete?: (data: IngestionComplete) => void
  onError?: (error: string, existingSourceId?: number) => void
}

export interface IngestionProgress {
  status: string
  page?: number
  total?: number
  message?: string
}

export interface IngestionComplete {
  id: number
  title: string | null
  author: string | null
  parse_status: string
  page_count: number | null
  content_preview: string
  source_type: string
  quality_flags: string[]
}

/**
 * POST-based SSE client using fetch + ReadableStream.
 * Native EventSource only supports GET, so we use fetch() for POST endpoints
 * (file upload, URL fetch) and manually parse the SSE text/event-stream format.
 */
export async function postSSE(
  path: string,
  body: FormData | string,
  callbacks: SSECallbacks,
  signal?: AbortSignal,
  options?: { headers?: Record<string, string> }
): Promise<void> {
  const headers: Record<string, string> = { ...options?.headers }
  if (typeof body === "string") {
    headers["Content-Type"] = "application/json"
  }

  const response = await fetch(`${API_URL}${path}`, {
    method: "POST",
    body,
    headers,
    signal,
  })

  if (!response.ok) {
    const text = await response.text()
    callbacks.onError?.(text)
    return
  }

  if (!response.body) {
    callbacks.onError?.("No response body")
    return
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ""

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })

      // SSE frames are separated by double newlines
      const frames = buffer.split("\n\n")
      buffer = frames.pop() || "" // Keep incomplete frame in buffer

      for (const frame of frames) {
        if (!frame.trim()) continue
        let eventType = ""
        const dataLines: string[] = []

        for (const line of frame.split("\n")) {
          if (line.startsWith("event:")) {
            eventType = line.slice(6).trim()
          } else if (line.startsWith("data:")) {
            dataLines.push(line.slice(5).trim())
          }
          // Ignore comment lines (starting with :) -- these are keep-alive pings
        }

        const data = dataLines.join("\n")
        if (!data) continue

        try {
          const parsed = JSON.parse(data)
          if (eventType === "progress") callbacks.onProgress?.(parsed)
          else if (eventType === "complete") callbacks.onComplete?.(parsed)
          else if (eventType === "error" || eventType === "duplicate")
            callbacks.onError?.(parsed.error, parsed.existing_source_id)
        } catch {
          // Skip malformed JSON frames
        }
      }
    }
  } finally {
    reader.releaseLock()
  }
}
