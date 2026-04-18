import { API_BASE_URL } from "@/lib/api-base";
import { ORGANIZATION_HEADER } from "@/lib/auth-storage";

function authHeaders(token: string, organizationId: string): HeadersInit {
  return {
    Authorization: `Bearer ${token}`,
    [ORGANIZATION_HEADER]: organizationId,
  };
}

export type TelegramConnectResponse = {
  integration_account_id: string;
  display_name: string;
};

export async function connectTelegramBot(
  token: string,
  organizationId: string,
  workspaceId: number,
  body: { bot_token: string; display_name?: string | null },
): Promise<TelegramConnectResponse> {
  const response = await fetch(
    `${API_BASE_URL}/integrations/telegram/workspaces/${workspaceId}/telegram/connect`,
    {
      method: "POST",
      headers: {
        ...authHeaders(token, organizationId),
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        bot_token: body.bot_token,
        display_name: body.display_name ?? null,
      }),
    },
  );
  if (!response.ok) {
    const err = (await response.json().catch(() => null)) as { error?: string } | null;
    throw new Error(err?.error ?? `Failed to connect Telegram (${response.status})`);
  }
  return response.json() as Promise<TelegramConnectResponse>;
}

export type TelegramApproveResponse = {
  approved_telegram_user_id: string;
};

export async function approveTelegramSender(
  token: string,
  organizationId: string,
  workspaceId: number,
  body: { integration_account_id: string; code: string },
): Promise<TelegramApproveResponse> {
  const response = await fetch(
    `${API_BASE_URL}/integrations/telegram/workspaces/${workspaceId}/telegram/approve-sender`,
    {
      method: "POST",
      headers: {
        ...authHeaders(token, organizationId),
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        integration_account_id: body.integration_account_id,
        code: body.code,
      }),
    },
  );
  if (!response.ok) {
    const err = (await response.json().catch(() => null)) as { error?: string } | null;
    throw new Error(err?.error ?? `Failed to approve sender (${response.status})`);
  }
  return response.json() as Promise<TelegramApproveResponse>;
}

export async function disconnectTelegramIntegration(
  token: string,
  organizationId: string,
  workspaceId: number,
  integrationAccountId: string,
): Promise<void> {
  const response = await fetch(
    `${API_BASE_URL}/integrations/telegram/workspaces/${workspaceId}/telegram/${integrationAccountId}`,
    {
      method: "DELETE",
      headers: authHeaders(token, organizationId),
    },
  );
  if (!response.ok && response.status !== 204) {
    const err = (await response.json().catch(() => null)) as { error?: string } | null;
    throw new Error(err?.error ?? `Failed to disconnect Telegram (${response.status})`);
  }
}
