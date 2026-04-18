import { API_BASE_URL } from "@/lib/api-base";
import { ORGANIZATION_HEADER } from "@/lib/auth-storage";

export type CyberIdentityType =
  | "influencer"
  | "community_manager"
  | "analyst"
  | "personal_assistant";

export const CYBER_IDENTITY_TYPE_OPTIONS: { value: CyberIdentityType; label: string }[] = [
  { value: "influencer", label: "Influencer" },
  { value: "community_manager", label: "Community manager" },
  { value: "analyst", label: "Analyst" },
  { value: "personal_assistant", label: "Personal assistant" },
];

export type CyberIdentity = {
  id: string;
  workspace_id: number;
  type: CyberIdentityType;
  display_name: string;
  is_active: boolean;
  config: Record<string, unknown>;
  created: string;
};

export type CyberIdentityCreateInput = {
  type: CyberIdentityType;
  display_name: string;
  is_active?: boolean;
  config?: Record<string, unknown>;
};

export type CyberIdentityUpdateInput = Partial<CyberIdentityCreateInput>;

function authHeaders(token: string, organizationId: string, json = false): HeadersInit {
  const base: Record<string, string> = {
    Authorization: `Bearer ${token}`,
    [ORGANIZATION_HEADER]: organizationId,
  };
  if (json) base["Content-Type"] = "application/json";
  return base;
}

async function parseError(response: Response, fallback: string): Promise<never> {
  let message = fallback;
  try {
    const body = (await response.json()) as { error?: string };
    if (body?.error) message = body.error;
  } catch {
    // ignore
  }
  throw new Error(`${message} (${response.status})`);
}

export async function fetchCyberIdentities(
  token: string,
  organizationId: string,
  workspaceId: number,
): Promise<CyberIdentity[]> {
  const response = await fetch(
    `${API_BASE_URL}/workspaces/${workspaceId}/cyber-identities/`,
    { headers: authHeaders(token, organizationId) },
  );
  if (!response.ok) await parseError(response, "Failed to load cyber identities");
  return response.json() as Promise<CyberIdentity[]>;
}

export async function createCyberIdentity(
  token: string,
  organizationId: string,
  workspaceId: number,
  input: CyberIdentityCreateInput,
): Promise<CyberIdentity> {
  const response = await fetch(
    `${API_BASE_URL}/workspaces/${workspaceId}/cyber-identities/`,
    {
      method: "POST",
      headers: authHeaders(token, organizationId, true),
      body: JSON.stringify(input),
    },
  );
  if (!response.ok) await parseError(response, "Failed to create cyber identity");
  return response.json() as Promise<CyberIdentity>;
}

export async function updateCyberIdentity(
  token: string,
  organizationId: string,
  workspaceId: number,
  cyberIdentityId: string,
  input: CyberIdentityUpdateInput,
): Promise<CyberIdentity> {
  const response = await fetch(
    `${API_BASE_URL}/workspaces/${workspaceId}/cyber-identities/${cyberIdentityId}/`,
    {
      method: "PATCH",
      headers: authHeaders(token, organizationId, true),
      body: JSON.stringify(input),
    },
  );
  if (!response.ok) await parseError(response, "Failed to update cyber identity");
  return response.json() as Promise<CyberIdentity>;
}

export async function deleteCyberIdentity(
  token: string,
  organizationId: string,
  workspaceId: number,
  cyberIdentityId: string,
): Promise<void> {
  const response = await fetch(
    `${API_BASE_URL}/workspaces/${workspaceId}/cyber-identities/${cyberIdentityId}/`,
    {
      method: "DELETE",
      headers: authHeaders(token, organizationId),
    },
  );
  if (!response.ok && response.status !== 204) {
    await parseError(response, "Failed to delete cyber identity");
  }
}
