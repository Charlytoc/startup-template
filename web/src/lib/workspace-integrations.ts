import { API_BASE_URL } from "@/lib/api-base";
import { ORGANIZATION_HEADER } from "@/lib/auth-storage";

function authHeaders(token: string, organizationId: string): HeadersInit {
  return {
    Authorization: `Bearer ${token}`,
    [ORGANIZATION_HEADER]: organizationId,
  };
}

export type WorkspaceIntegrationItem = {
  id: string;
  provider: string;
  display_name: string;
  status: string;
  external_account_id: string;
  created: string;
};

export async function fetchWorkspaceIntegrations(
  token: string,
  organizationId: string,
  workspaceId: number,
): Promise<WorkspaceIntegrationItem[]> {
  const response = await fetch(`${API_BASE_URL}/workspaces/${workspaceId}/integrations/`, {
    headers: authHeaders(token, organizationId),
  });
  if (!response.ok) {
    throw new Error(`Failed to load integrations (${response.status})`);
  }
  return response.json() as Promise<WorkspaceIntegrationItem[]>;
}

export type IntegrationAccountSenderApprovalStatus =
  | "pending"
  | "not_required"
  | "approved";

export type IntegrationAccountSender = {
  external_thread_id: string;
  approval_status: IntegrationAccountSenderApprovalStatus;
  /** Display-oriented id (Telegram @username or numeric id, Instagram @username when known). */
  handle?: string | null;
  extractions: Record<string, unknown>;
  first_seen_at: string | null;
  last_seen_at: string | null;
};

export type WorkspaceIntegrationDetail = {
  id: string;
  workspace_id: number;
  provider: string;
  display_name: string;
  status: string;
  external_account_id: string;
  config: Record<string, unknown>;
  senders: IntegrationAccountSender[];
  last_synced_at: string | null;
  last_error: string;
  created: string;
  modified: string;
};

export async function fetchWorkspaceIntegrationDetail(
  token: string,
  organizationId: string,
  workspaceId: number,
  integrationAccountId: string,
): Promise<WorkspaceIntegrationDetail> {
  const response = await fetch(
    `${API_BASE_URL}/workspaces/${workspaceId}/integrations/${integrationAccountId}/`,
    { headers: authHeaders(token, organizationId) },
  );
  if (!response.ok) {
    throw new Error(`Failed to load integration (${response.status})`);
  }
  return response.json() as Promise<WorkspaceIntegrationDetail>;
}

export type IntegrationTaskExecutionItem = {
  id: string;
  status: string;
  requires_approval: boolean;
  job_assignment_id: string | null;
  job_role_name: string;
  scheduled_to: string | null;
  started_at: string | null;
  completed_at: string | null;
  created: string;
};

export type IntegrationConversationItem = {
  id: string;
  status: string;
  cyber_identity_id: string;
  cyber_identity_name: string;
  external_thread_id: string;
  external_user_id: string;
  message_count: number;
  last_interaction_at: string | null;
  created: string;
};

export async function fetchIntegrationConversations(
  token: string,
  organizationId: string,
  workspaceId: number,
  integrationAccountId: string,
  limit = 100,
): Promise<IntegrationConversationItem[]> {
  const response = await fetch(
    `${API_BASE_URL}/workspaces/${workspaceId}/integrations/${integrationAccountId}/conversations/?limit=${limit}`,
    { headers: authHeaders(token, organizationId) },
  );
  if (!response.ok) {
    throw new Error(`Failed to load conversations (${response.status})`);
  }
  return response.json() as Promise<IntegrationConversationItem[]>;
}

export async function fetchIntegrationTaskExecutions(
  token: string,
  organizationId: string,
  workspaceId: number,
  integrationAccountId: string,
  limit = 100,
): Promise<IntegrationTaskExecutionItem[]> {
  const response = await fetch(
    `${API_BASE_URL}/workspaces/${workspaceId}/integrations/${integrationAccountId}/task-executions/?limit=${limit}`,
    { headers: authHeaders(token, organizationId) },
  );
  if (!response.ok) {
    throw new Error(`Failed to load task executions (${response.status})`);
  }
  return response.json() as Promise<IntegrationTaskExecutionItem[]>;
}
