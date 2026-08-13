import type { Metadata } from "next";
import { AppShell } from "@/components/layout/AppShell";
import { ChatWorkspace } from "@/components/chat/ChatWorkspace";

export const metadata: Metadata = {
  title: "Conversations",
};

export default function ChatPage() {
  return (
    <AppShell fullBleed showTopBar>
      <ChatWorkspace />
    </AppShell>
  );
}
