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
