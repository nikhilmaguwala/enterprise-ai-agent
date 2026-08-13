import { apiFetch, apiUpload } from "@/lib/api";
import { getStoredUser, setAccessToken, setStarterOrderNumber, setStoredUser } from "@/lib/auth";
import { env } from "@/lib/env";
import {
  AgentRunSchema,
  ConversationListSchema,
  ConversationSchema,
  DevLoginResponseSchema,
  MeResponseSchema,
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

async function exchangeAuth(path: string, body: Record<string, string>) {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify(body),
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
        : `Authentication failed (${response.status})`;
    throw new Error(detail);
  }

  const data = DevLoginResponseSchema.parse(parsed);
  setAccessToken(data.access_token);
  setStoredUser(data.user);
  if (data.starter_order_number) {
    setStarterOrderNumber(data.starter_order_number);
  }
  return data;
}

export async function registerAccount(input: {
  email: string;
  password: string;
  fullName: string;
  companyName: string;
}) {
  return exchangeAuth("/api/auth/register", {
    email: input.email,
    password: input.password,
    full_name: input.fullName,
    company_name: input.companyName,
  });
}

export async function loginAccount(input: { email: string; password: string }) {
  return exchangeAuth("/api/auth/login", {
    email: input.email,
    password: input.password,
  });
}

export async function fetchCurrentUser() {
  const response = await apiFetch("/api/auth/me", { schema: MeResponseSchema });
  if (response.starter_order_number) {
    setStarterOrderNumber(response.starter_order_number);
  }
  setStoredUser(response.user);
  return response;
}

export async function devLogin(email: string) {
  return exchangeAuth("/api/auth/dev-login", { email });
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

export function isRegistrationEnabled(): boolean {
  return env.registrationEnabled;
}

/** True for seeded demo accounts — real signup users never see demo chrome. */
export function isDemoMode(): boolean {
  if (!env.devAuthEnabled) return false;
  if (!env.registrationEnabled) return true;
  const user = getStoredUser();
  if (!user) return false;
  return (
    user.email.endsWith("@acme-demo.test") ||
    user.email.endsWith("@globex-demo.test")
  );
}
