import { Input } from "@/components/ui/input"

export function MessageInput() {
  return (
    <footer className="border-t border-border p-4">
      <Input
        placeholder="Ask a clinical question..."
        disabled
        className="min-h-[52px] cursor-not-allowed bg-muted/50"
        aria-label="Message input"
      />
    </footer>
  )
}
