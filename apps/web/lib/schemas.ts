import { z } from "zod";

export const RoleSchema = z.enum([
  "customer",
  "agent",
  "supervisor",
  "admin",
]);
export type Role = z.infer<typeof RoleSchema>;

export const UserSchema = z.object({
  id: z.string(),
  email: z.string().email(),
  name: z.string().optional(),
  role: RoleSchema,
  organization_id: z.string(),
  organization_name: z.string().optional(),
});
export type User = z.infer<typeof UserSchema>;

export const DevLoginResponseSchema = z.object({
  access_token: z.string(),
  token_type: z.string().default("bearer"),
  expires_in: z.number().optional(),
  user: UserSchema,
  starter_order_number: z.string().optional(),
});
export type DevLoginResponse = z.infer<typeof DevLoginResponseSchema>;

export const MeResponseSchema = z.object({
  user: UserSchema,
  starter_order_number: z.string().optional(),
});
export type MeResponse = z.infer<typeof MeResponseSchema>;

export const InviteRoleSchema = z.enum([
  "customer",
  "agent",
  "supervisor",
  "admin",
]);
export type InviteRole = z.infer<typeof InviteRoleSchema>;

export const InviteResponseSchema = z.object({
  ok: z.boolean(),
  email: z.string().email(),
  role: RoleSchema,
  temporary_password_sent: z.boolean(),
});
export type InviteResponse = z.infer<typeof InviteResponseSchema>;

export const CitationSchema = z.object({
  id: z.string(),
  title: z.string(),
  excerpt: z.string(),
  source_uri: z.string().nullish(),
  document_id: z.string().nullish(),
  score: z.number().nullish(),
});
export type Citation = z.infer<typeof CitationSchema>;

export const ToolProgressSchema = z.object({
  tool_name: z.string(),
  status: z.enum(["pending", "running", "succeeded", "failed", "skipped"]),
  detail: z.string().optional(),
  started_at: z.string().optional(),
  finished_at: z.string().optional(),
});
export type ToolProgress = z.infer<typeof ToolProgressSchema>;

export const ApprovalSchema = z.object({
  id: z.string(),
  conversation_id: z.string(),
  action_type: z.string(),
  summary: z.string(),
  payload: z.record(z.string(), z.unknown()).optional(),
  status: z.enum(["pending", "approved", "rejected", "expired"]),
  created_at: z.string(),
  risk_level: z.enum(["low", "medium", "high"]).optional(),
});
export type Approval = z.infer<typeof ApprovalSchema>;

export const MessageSchema = z.object({
  id: z.string(),
  conversation_id: z.string(),
  role: z.enum(["user", "assistant", "system", "tool"]),
  content: z.string(),
  created_at: z.string(),
  citations: z.array(CitationSchema).nullish(),
  tool_progress: z.array(ToolProgressSchema).nullish(),
  approval: ApprovalSchema.nullish(),
  run_id: z.string().nullish(),
});
export type Message = z.infer<typeof MessageSchema>;

export const ConversationSchema = z.object({
  id: z.string(),
  title: z.string().nullable().optional(),
  status: z.enum([
    "open",
    "waiting_approval",
    "escalated",
    "resolved",
    "closed",
  ]),
  created_at: z.string(),
  updated_at: z.string(),
  last_message_preview: z.string().optional(),
  customer_email: z.string().optional(),
});
export type Conversation = z.infer<typeof ConversationSchema>;

export const ConversationListSchema = z.object({
  items: z.array(ConversationSchema),
  total: z.number().optional(),
});
export type ConversationList = z.infer<typeof ConversationListSchema>;

export const MessageListSchema = z.object({
  items: z.array(MessageSchema),
});
export type MessageList = z.infer<typeof MessageListSchema>;

export const EscalationSchema = z.object({
  id: z.string(),
  conversation_id: z.string(),
  reason: z.string(),
  handoff_summary: z.string(),
  status: z.enum(["open", "claimed", "resolved"]),
  priority: z.enum(["low", "medium", "high", "urgent"]).optional(),
  created_at: z.string(),
  customer_email: z.string().optional(),
  assigned_to: z.string().nullable().optional(),
});
export type Escalation = z.infer<typeof EscalationSchema>;

export const EscalationListSchema = z.object({
  items: z.array(EscalationSchema),
});
export type EscalationList = z.infer<typeof EscalationListSchema>;

export const KnowledgeDocumentSchema = z.object({
  id: z.string(),
  title: z.string(),
  filename: z.string().optional(),
  status: z.enum([
    "pending",
    "uploading",
    "processing",
    "active",
    "failed",
    "archived",
  ]),
  mime_type: z.string().optional(),
  byte_size: z.number().optional(),
  chunk_count: z.number().optional(),
  created_at: z.string(),
  updated_at: z.string().optional(),
  error_message: z.string().nullable().optional(),
});
export type KnowledgeDocument = z.infer<typeof KnowledgeDocumentSchema>;

export const KnowledgeDocumentListSchema = z.object({
  items: z.array(KnowledgeDocumentSchema),
});
export type KnowledgeDocumentList = z.infer<typeof KnowledgeDocumentListSchema>;

export const DocumentPresignResponseSchema = z.object({
  document_id: z.string(),
  upload_url: z.string(),
  storage_key: z.string(),
});
export type DocumentPresignResponse = z.infer<typeof DocumentPresignResponseSchema>;

export const DocumentUploadResponseSchema = z.object({
  document_id: z.string(),
  storage_key: z.string(),
  byte_size: z.number(),
  checksum_sha256: z.string(),
  mime_type: z.string(),
});
export type DocumentUploadResponse = z.infer<typeof DocumentUploadResponseSchema>;

export const AgentRunStepSchema = z.object({
  id: z.string(),
  name: z.string(),
  status: z.enum(["pending", "running", "succeeded", "failed", "skipped"]),
  started_at: z.string().optional(),
  finished_at: z.string().optional(),
  detail: z.string().optional(),
  input: z.unknown().optional(),
  output: z.unknown().optional(),
});
export type AgentRunStep = z.infer<typeof AgentRunStepSchema>;

export const AgentRunSchema = z.object({
  id: z.string(),
  conversation_id: z.string(),
  status: z.enum([
    "queued",
    "running",
    "paused",
    "succeeded",
    "failed",
    "cancelled",
  ]),
  graph_version: z.string().optional(),
  started_at: z.string().optional(),
  finished_at: z.string().optional(),
  steps: z.array(AgentRunStepSchema).default([]),
  error: z.string().nullable().optional(),
});
export type AgentRun = z.infer<typeof AgentRunSchema>;

export const EvaluationMetricSchema = z.object({
  name: z.string(),
  value: z.number(),
  unit: z.string().optional(),
  target: z.number().optional(),
  trend: z.enum(["up", "down", "flat"]).optional(),
});
export type EvaluationMetric = z.infer<typeof EvaluationMetricSchema>;

export const EvaluationSuiteSchema = z.object({
  id: z.string(),
  name: z.string(),
  last_run_at: z.string().nullable().optional(),
  pass_rate: z.number().nullable().optional(),
  case_count: z.number().optional(),
  status: z.enum(["idle", "running", "passed", "failed"]).optional(),
});
export type EvaluationSuite = z.infer<typeof EvaluationSuiteSchema>;

export const EvaluationsDashboardSchema = z.object({
  metrics: z.array(EvaluationMetricSchema).default([]),
  suites: z.array(EvaluationSuiteSchema).default([]),
});
export type EvaluationsDashboard = z.infer<typeof EvaluationsDashboardSchema>;

export const IntegrationHealthSchema = z.object({
  name: z.string(),
  status: z.enum(["healthy", "degraded", "down", "unknown"]),
  latency_ms: z.number().nullable().optional(),
  last_checked_at: z.string().optional(),
  detail: z.string().optional(),
});
export type IntegrationHealth = z.infer<typeof IntegrationHealthSchema>;

export const QueueStatsSchema = z.object({
  name: z.string(),
  depth: z.number(),
  oldest_age_seconds: z.number().nullable().optional(),
  processing: z.number().optional(),
  failed: z.number().optional(),
});
export type QueueStats = z.infer<typeof QueueStatsSchema>;

export const OperationsDashboardSchema = z.object({
  queues: z.array(QueueStatsSchema).default([]),
  integrations: z.array(IntegrationHealthSchema).default([]),
  recent_replays: z
    .array(
      z.object({
        id: z.string(),
        job_id: z.string(),
        status: z.enum(["queued", "succeeded", "failed"]),
        created_at: z.string(),
      }),
    )
    .default([]),
});
export type OperationsDashboard = z.infer<typeof OperationsDashboardSchema>;

export const SseEventSchema = z.object({
  id: z.string().optional(),
  type: z.string(),
  data: z.unknown(),
});
export type SseEvent = z.infer<typeof SseEventSchema>;

export const ApiErrorSchema = z.object({
  detail: z.union([z.string(), z.array(z.unknown())]).optional(),
  message: z.string().optional(),
  code: z.string().optional(),
});
