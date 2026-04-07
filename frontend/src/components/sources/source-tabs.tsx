"use client"

import { useState } from "react"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Separator } from "@/components/ui/separator"
import { PdfUploadTab } from "./pdf-upload-tab"
import { UrlFetchTab } from "./url-fetch-tab"
import { SearchTab } from "./search-tab"
import { SourceList } from "./source-list"

export function SourceTabs() {
  // refreshKey incremented after successful ingestion to trigger SourceList refetch
  const [refreshKey, setRefreshKey] = useState(0)

  const handleSourceAdded = () => {
    setRefreshKey((prev) => prev + 1)
  }

  return (
    <div>
      <Tabs defaultValue="upload">
        <TabsList>
          <TabsTrigger value="upload">Upload PDF</TabsTrigger>
          <TabsTrigger value="fetch">Fetch URL</TabsTrigger>
          <TabsTrigger value="search">Search Sources</TabsTrigger>
        </TabsList>

        <TabsContent value="upload">
          <PdfUploadTab onSourceAdded={handleSourceAdded} />
        </TabsContent>

        <TabsContent value="fetch">
          <UrlFetchTab onSourceAdded={handleSourceAdded} />
        </TabsContent>

        <TabsContent value="search">
          <SearchTab onSourceAdded={handleSourceAdded} />
        </TabsContent>
      </Tabs>

      <Separator className="my-6" />
      <SourceList refreshKey={refreshKey} />
    </div>
  )
}
