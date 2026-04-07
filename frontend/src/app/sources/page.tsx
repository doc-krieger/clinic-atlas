import { Sidebar } from "@/components/layout/sidebar"
import { SourceTabs } from "@/components/sources/source-tabs"

export default function SourcesPage() {
  return (
    <div className="flex h-screen">
      <Sidebar />
      <main className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-3xl px-6 py-8">
          <h1 className="text-2xl font-semibold mb-8">Sources</h1>
          <SourceTabs />
        </div>
      </main>
    </div>
  )
}
