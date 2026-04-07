"use client"

import { useEffect, useState } from "react"
import { Separator } from "@/components/ui/separator"
import { useTheme } from "next-themes"
import { Moon, Sun } from "lucide-react"
import { Button } from "@/components/ui/button"
import { fetchHealth } from "@/lib/api"

export function Sidebar() {
  const { theme, setTheme } = useTheme()
  const [mounted, setMounted] = useState(false)
  const [healthStatus, setHealthStatus] = useState<
    "loading" | "ok" | "degraded" | "error" | "unavailable"
  >("loading")

  useEffect(() => {
    setMounted(true)
  }, [])

  // Health check polling — handles 404/network failure cleanly
  useEffect(() => {
    const checkHealth = async () => {
      const data = await fetchHealth()
      // fetchHealth never throws — returns { status: "unavailable" } on failure
      if (data.status === "ok") {
        setHealthStatus("ok")
      } else if (data.status === "degraded") {
        setHealthStatus("degraded")
      } else {
        setHealthStatus("unavailable")
      }
    }
    checkHealth()
    const interval = setInterval(checkHealth, 30000) // Poll every 30s
    return () => clearInterval(interval)
  }, [])

  return (
    <aside className="flex h-screen w-[256px] flex-col border-r border-border bg-card">
      {/* App title */}
      <div className="flex items-center gap-2 px-6 py-6">
        <h1 className="text-lg font-semibold text-foreground">Clinic Atlas</h1>
      </div>

      <Separator />

      {/* Nav placeholder */}
      <nav className="flex-1 px-4 py-4">
        <p className="px-2 text-xs text-muted-foreground">Navigation</p>
      </nav>

      <Separator />

      {/* Footer: health indicator + theme toggle */}
      <div className="flex items-center justify-between px-4 py-4">
        {/* Health indicator per UI-SPEC Interaction States */}
        <div className="flex items-center gap-2">
          <div
            className={`h-2 w-2 rounded-full ${
              healthStatus === "loading"
                ? "animate-pulse bg-muted-foreground"
                : healthStatus === "ok"
                  ? "bg-green-500"
                  : healthStatus === "degraded"
                    ? "bg-yellow-500"
                    : "bg-red-500"
            }`}
          />
          <span className="text-xs text-muted-foreground">
            {healthStatus === "loading"
              ? "Checking..."
              : healthStatus === "ok"
                ? "All systems operational"
                : healthStatus === "degraded"
                  ? "Some services unavailable"
                  : "Services unavailable"}
          </span>
        </div>

        {/* Theme toggle */}
        {mounted && (
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            aria-label="Toggle theme"
          >
            {theme === "dark" ? (
              <Sun className="h-4 w-4" />
            ) : (
              <Moon className="h-4 w-4" />
            )}
          </Button>
        )}
      </div>
    </aside>
  )
}
