"use client"

interface SearchTabProps {
  onSourceAdded: () => void
}

/**
 * Placeholder -- fully implemented in Task 3.
 */
export function SearchTab({ onSourceAdded: _onSourceAdded }: SearchTabProps) {
  return (
    <div className="mt-4">
      <p className="text-sm text-muted-foreground">Search tab loading...</p>
    </div>
  )
}
