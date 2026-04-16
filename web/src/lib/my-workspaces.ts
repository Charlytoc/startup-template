import { API_BASE_URL } from "@/lib/api-base";
import type { components } from "@/lib/api/schema";
import { ORGANIZATION_HEADER } from "@/lib/auth-storage";

export type WorkspaceResponse = components["schemas"]["WorkspaceResponse"];

function authHeaders(token: string, organizationId: string): HeadersInit {
  return {
    Authorization: `Bearer ${token}`,
    [ORGANIZATION_HEADER]: organizationId,
  };
}

export async function fetchWorkspaces(token: string, organizationId: string): Promise<WorkspaceResponse[]> {
  const response = await fetch(`${API_BASE_URL}/workspaces/`, {
    headers: authHeaders(token, organizationId),
  });
  if (!response.ok) {
    throw new Error(`Failed to load workspaces (${response.status})`);
  }
  return response.json() as Promise<WorkspaceResponse[]>;
}

export async function createWorkspace(
  token: string,
  organizationId: string,
  name: string,
): Promise<WorkspaceResponse> {
  const response = await fetch(`${API_BASE_URL}/workspaces/`, {
    method: "POST",
    headers: {
      ...authHeaders(token, organizationId),
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ name }),
  });
  if (!response.ok) {
    const err = (await response.json().catch(() => null)) as { error?: string } | null;
    throw new Error(err?.error ?? `Failed to create workspace (${response.status})`);
  }
  return response.json() as Promise<WorkspaceResponse>;
}
