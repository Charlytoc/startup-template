import { API_BASE_URL } from "@/lib/api-base";
import { ORGANIZATION_HEADER } from "@/lib/auth-storage";

function authHeaders(token: string, organizationId: string): HeadersInit {
  return {
    Authorization: `Bearer ${token}`,
    [ORGANIZATION_HEADER]: organizationId,
  };
}

export type InstagramOAuthUrlResponse = {
  oauth_url: string;
};

export type InstagramConnectedAccount = {
  integration_account_id: string;
  display_name: string;
  ig_username: string;
};

/**
 * Step 1 of the OAuth flow.
 * Returns the Meta authorization URL. Redirect the user (or open a popup) to this URL.
 */
export async function getInstagramOAuthUrl(
  token: string,
  organizationId: string,
  workspaceId: number,
): Promise<InstagramOAuthUrlResponse> {
  const response = await fetch(
    `${API_BASE_URL}/integrations/instagram/workspaces/${workspaceId}/instagram/oauth-url`,
    { headers: authHeaders(token, organizationId) },
  );
  if (!response.ok) {
    const err = (await response.json().catch(() => null)) as { error?: string } | null;
    throw new Error(err?.error ?? `Failed to get Instagram OAuth URL (${response.status})`);
  }
  return response.json() as Promise<InstagramOAuthUrlResponse>;
}

/**
 * Delete a connected Instagram integration account.
 */
export async function disconnectInstagramIntegration(
  token: string,
  organizationId: string,
  workspaceId: number,
  integrationAccountId: string,
): Promise<void> {
  const response = await fetch(
    `${API_BASE_URL}/integrations/instagram/workspaces/${workspaceId}/instagram/${integrationAccountId}`,
    {
      method: "DELETE",
      headers: authHeaders(token, organizationId),
    },
  );
  if (!response.ok && response.status !== 204) {
    const err = (await response.json().catch(() => null)) as { error?: string } | null;
    throw new Error(err?.error ?? `Failed to disconnect Instagram (${response.status})`);
  }
}
