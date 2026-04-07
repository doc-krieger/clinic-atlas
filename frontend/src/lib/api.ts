const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export async function fetchHealth(): Promise<{
  status: string
  checks?: Record<string, unknown>
}> {
  try {
    const res = await fetch(`${API_URL}/api/health`, {
      signal: AbortSignal.timeout(5000), // 5s timeout for health checks
    })
    if (!res.ok) {
      return { status: "error" }
    }
    return res.json()
  } catch {
    // Handle network failure, 404, timeout gracefully
    // (addresses review concern: health polling tolerance for missing endpoints)
    return { status: "unavailable" }
  }
}

export { API_URL }
