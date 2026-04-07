import { Card, CardContent } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"

export function MessageList() {
  return (
    <ScrollArea className="flex-1">
      <div className="flex h-full items-center justify-center p-8">
        <Card className="max-w-md">
          <CardContent className="flex flex-col items-center gap-4 p-8 text-center">
            <h2 className="text-lg font-semibold text-foreground">
              No conversations yet
            </h2>
            <p className="text-sm text-muted-foreground">
              Ask a clinical question to start building your knowledge base.
            </p>
          </CardContent>
        </Card>
      </div>
    </ScrollArea>
  )
}
