import { apiClient } from "../api/client";

export type AuditAction = "view" | "create" | "update" | "issue" | "deactivate";
export type AuditEntityType = "assessment" | "user";

export interface AuditChange {
  field: string;
  before: unknown;
  after: unknown;
}

export interface AuditActor {
  id: string;
  display_name: string;
}

export interface AuditEvent {
  id: string;
  occurred_at: string;
  actor: AuditActor;
  action: AuditAction;
  entity_type: AuditEntityType;
  entity_id: string;
  changes: AuditChange[];
}

export interface AuditEventListResponse {
  items: AuditEvent[];
  page: number;
  page_size: number;
  total: number;
}

export interface ListAuditEventsParams {
  entity_type?: AuditEntityType;
  entity_id?: string;
  actor_id?: string;
  action?: AuditAction;
  from_time?: string;
  to_time?: string;
  page?: number;
  page_size?: number;
}

export async function listAuditEvents(
  params: ListAuditEventsParams,
): Promise<AuditEventListResponse> {
  const response = await apiClient.get<AuditEventListResponse>("/audit/events", { params });
  return response.data;
}
