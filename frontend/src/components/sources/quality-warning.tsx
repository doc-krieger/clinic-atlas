"use client"

import { Alert, AlertDescription } from "@/components/ui/alert"
import { AlertTriangle, XCircle } from "lucide-react"

interface QualityWarningProps {
  variant: "warning" | "error"
  message: string
}

export function QualityWarning({ variant, message }: QualityWarningProps) {
  if (variant === "error") {
    return (
      <Alert variant="destructive">
        <XCircle className="h-4 w-4" />
        <AlertDescription>{message}</AlertDescription>
      </Alert>
    )
  }

  return (
    <Alert className="bg-yellow-500/10 border-yellow-500/20">
      <AlertTriangle className="h-4 w-4 text-yellow-500" />
      <AlertDescription>{message}</AlertDescription>
    </Alert>
  )
}
