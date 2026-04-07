import { Sidebar } from "@/components/layout/sidebar"
import { MessageList } from "@/components/chat/message-list"
import { MessageInput } from "@/components/chat/message-input"

export default function ChatPage() {
  return (
    <div className="flex h-screen bg-background">
      <Sidebar />
      <main className="flex flex-1 flex-col">
        <div className="mx-auto flex w-full max-w-3xl flex-1 flex-col">
          <MessageList />
          <MessageInput />
        </div>
      </main>
    </div>
  )
}
