import { apiFetch, apiUpload } from "@/lib/api";
import { setAccessToken, setStoredUser } from "@/lib/auth";
import { env } from "@/lib/env";
import {
  AgentRunSchema,
  ConversationListSchema,
  ConversationSchema,
  DevLoginResponseSchema,
  EscalationListSchema,
  EvaluationsDashboardSchema,
  KnowledgeDocumentListSchema,
  DocumentPresignResponseSchema,
  KnowledgeDocumentSchema,
  MessageListSchema,
  MessageSchema,
  OperationsDashboardSchema,
  type AgentRun,
  type Approval,
  type Conversation,
  type ConversationList,
  type EscalationList,
  type EvaluationsDashboard,
  type KnowledgeDocumentList,
  type DocumentPresignResponse,
  type KnowledgeDocument,
  type Message,
  type MessageList,
  type OperationsDashboard,
} from "@/lib/schemas";

export async function devLogin(email: string) {
  // Prefer same-origin route so browser CORS is not required during local demo.
  const response = await fetch("/api/auth/dev-login", {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify({ email }),
  });

  const text = await response.text();
  let parsed: unknown = null;
  if (text) {
    try {
      parsed = JSON.parse(text) as unknown;
    } catch {
      parsed = { detail: text };
    }
  }

  if (!response.ok) {
    const detail =
      typeof parsed === "object" &&
      parsed &&
      "detail" in parsed &&
      typeof (parsed as { detail: unknown }).detail === "string"
        ? (parsed as { detail: string }).detail
        : `Dev login failed (${response.status})`;
    throw new Error(detail);
  }

  const data = DevLoginResponseSchema.parse(parsed);
  setAccessToken(data.access_token);
  setStoredUser(data.user);
  return data;
}

export async function listConversations(): Promise<ConversationList> {
  return apiFetch("/api/v1/conversations", { schema: ConversationListSchema });
}

export async function createConversation(title?: string): Promise<Conversation> {
  return apiFetch("/api/v1/conversations", {
    method: "POST",
    body: { title },
    schema: ConversationSchema,
  });
}

export async function listMessages(
  conversationId: string,
): Promise<MessageList> {
  return apiFetch(`/api/v1/conversations/${conversationId}/messages`, {
    schema: MessageListSchema,
  });
}

export async function sendMessage(
  conversationId: string,
  content: string,
): Promise<Message> {
  return apiFetch(`/api/v1/conversations/${conversationId}/messages`, {
    method: "POST",
    body: { content },
    schema: MessageSchema,
  });
}

export async function decideApproval(
  approvalId: string,
  decision: "approve" | "reject",
  note?: string,
): Promise<Approval> {
  return apiFetch(`/api/v1/approvals/${approvalId}/${decision}`, {
    method: "POST",
    body: { note },
  });
}

export async function listEscalations(): Promise<EscalationList> {
  return apiFetch("/api/v1/inbox/escalations", { schema: EscalationListSchema });
}

export async function listDocuments(): Promise<KnowledgeDocumentList> {
  return apiFetch("/api/v1/knowledge/documents", {
    schema: KnowledgeDocumentListSchema,
  });
}

export async function uploadKnowledgeDocument(file: File): Promise<KnowledgeDocument> {
  const presign = await apiFetch<DocumentPresignResponse>("/api/v1/documents/presign", {
    method: "POST",
    body: {
      title: file.name,
      mime_type: file.type || "application/octet-stream",
      byte_size: file.size,
    },
    schema: DocumentPresignResponseSchema,
  });

  await apiUpload(presign.upload_url, file);

  return apiFetch<KnowledgeDocument>(
    `/api/v1/documents/${presign.document_id}/complete`,
    {
      method: "POST",
      body: {},
      schema: KnowledgeDocumentSchema,
    },
  );
}

export async function getAgentRun(runId: string): Promise<AgentRun> {
  return apiFetch(`/api/v1/runs/${runId}`, { schema: AgentRunSchema });
}

export async function getEvaluations(): Promise<EvaluationsDashboard> {
  return apiFetch("/api/v1/evaluations/dashboard", {
    schema: EvaluationsDashboardSchema,
  });
}

export async function getOperations(): Promise<OperationsDashboard> {
  return apiFetch("/api/v1/operations/dashboard", {
    schema: OperationsDashboardSchema,
  });
}

export async function replayJob(jobId: string): Promise<{ id: string }> {
  return apiFetch(`/api/v1/operations/jobs/${jobId}/replay`, { method: "POST" });
}

export function conversationEventsPath(conversationId: string): string {
  return `/api/v1/conversations/${conversationId}/events`;
}

export function isDevAuthEnabled(): boolean {
  return env.devAuthEnabled;
}
