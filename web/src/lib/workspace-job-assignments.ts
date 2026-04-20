import { API_BASE_URL } from "@/lib/api-base";
import { ORGANIZATION_HEADER } from "@/lib/auth-storage";
import type { CyberIdentity } from "@/lib/workspace-cyber-identities";

export type ActionableCatalogRow = {
  slug: string;
  name: string;
  description: string;
  provider: string;
  integration_account_id: string;
  integration: {
    integration_account_id: string;
    provider: string;
    display_name: string;
    status: string;
  };
};

export type JobAssignmentConfigAccount = {
  id: string;
  provider: string;
};

export type JobAssignmentConfigIdentity = {
  id: string;
  type: string;
  config: Record<string, unknown>;
};

/** Canonical ``JobAssignment.config`` from the API (after create/update). */
export type JobAssignmentConfig = {
  accounts: JobAssignmentConfigAccount[];
  identities: JobAssignmentConfigIdentity[];
  triggers: Record<string, unknown>[];
  actions: Record<string, unknown>[];
  approval_policy?: Record<string, unknown> | null;
  output_schema?: Record<string, unknown> | null;
};

export type JobAssignment = {
  id: string;
  workspace_id: number;
  role_name: string;
  description: string;
  instructions: string;
  enabled: boolean;
  config: JobAssignmentConfig;
  created: string;
};

export type JobAssignmentCreateInput = {
  role_name: string;
  description?: string;
  instructions?: string;
  enabled?: boolean;
  /** Partial config is merged with server defaults and coerced to ``JobAssignmentConfig``. */
  config?: Partial<JobAssignmentConfig> & Record<string, unknown>;
};

export type JobAssignmentUpdateInput = Partial<JobAssignmentCreateInput>;

/** Catalog row key: ``slug::<integration_account_id>`` (empty suffix when id is null). */
export function actionKey(row: ActionableCatalogRow): string {
  const id = row.integration_account_id;
  return `${row.slug}::${id ?? ""}`;
}

/** Reverse of :func:`actionKey` for PATCH payloads. */
export function keyToAction(key: string): { actionable_slug: string; integration_account_id: string | null } {
  const idx = key.indexOf("::");
  if (idx === -1) return { actionable_slug: key, integration_account_id: null };
  const slug = key.slice(0, idx);
  const rest = key.slice(idx + 2);
  return { actionable_slug: slug, integration_account_id: rest || null };
}

export function buildIdentitiesPayload(
  selectedIdentityIds: string[],
  identities: CyberIdentity[],
): JobAssignmentConfigIdentity[] {
  return selectedIdentityIds
    .map((id) => identities.find((i) => i.id === id))
    .filter((row): row is CyberIdentity => Boolean(row))
    .map((i) => ({ id: i.id, type: i.type, config: i.config ?? {} }));
}

export function buildActionsPayload(selectedActionKeys: string[]) {
  return selectedActionKeys.map((key) => keyToAction(key));
}

/** Build MultiSelect keys from persisted ``config.actions``. */
export function actionsToKeys(actions: Record<string, unknown>[]): string[] {
  return actions.map((a) => {
    const slug = String((a as { actionable_slug?: string }).actionable_slug ?? "");
    const raw = (a as { integration_account_id?: string | null }).integration_account_id;
    return `${slug}::${raw ?? ""}`;
  });
}

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

export async function fetchWorkspaceActionables(
  token: string,
  organizationId: string,
  workspaceId: number,
): Promise<ActionableCatalogRow[]> {
  const response = await fetch(`${API_BASE_URL}/workspaces/${workspaceId}/actionables/`, {
    headers: authHeaders(token, organizationId),
  });
  if (!response.ok) await parseError(response, "Failed to load actionables");
  return response.json() as Promise<ActionableCatalogRow[]>;
}

export async function fetchJobAssignments(
  token: string,
  organizationId: string,
  workspaceId: number,
): Promise<JobAssignment[]> {
  const response = await fetch(`${API_BASE_URL}/workspaces/${workspaceId}/job-assignments/`, {
    headers: authHeaders(token, organizationId),
  });
  if (!response.ok) await parseError(response, "Failed to load job assignments");
  return response.json() as Promise<JobAssignment[]>;
}

export async function fetchJobAssignment(
  token: string,
  organizationId: string,
  workspaceId: number,
  jobAssignmentId: string,
): Promise<JobAssignment> {
  const response = await fetch(
    `${API_BASE_URL}/workspaces/${workspaceId}/job-assignments/${jobAssignmentId}/`,
    { headers: authHeaders(token, organizationId) },
  );
  if (!response.ok) await parseError(response, "Failed to load job assignment");
  return response.json() as Promise<JobAssignment>;
}

export async function createJobAssignment(
  token: string,
  organizationId: string,
  workspaceId: number,
  input: JobAssignmentCreateInput,
): Promise<JobAssignment> {
  const response = await fetch(`${API_BASE_URL}/workspaces/${workspaceId}/job-assignments/`, {
    method: "POST",
    headers: authHeaders(token, organizationId, true),
    body: JSON.stringify(input),
  });
  if (!response.ok) await parseError(response, "Failed to create job assignment");
  return response.json() as Promise<JobAssignment>;
}

export async function updateJobAssignment(
  token: string,
  organizationId: string,
  workspaceId: number,
  jobAssignmentId: string,
  input: JobAssignmentUpdateInput,
): Promise<JobAssignment> {
  const response = await fetch(
    `${API_BASE_URL}/workspaces/${workspaceId}/job-assignments/${jobAssignmentId}/`,
    {
      method: "PATCH",
      headers: authHeaders(token, organizationId, true),
      body: JSON.stringify(input),
    },
  );
  if (!response.ok) await parseError(response, "Failed to update job assignment");
  return response.json() as Promise<JobAssignment>;
}

export async function deleteJobAssignment(
  token: string,
  organizationId: string,
  workspaceId: number,
  jobAssignmentId: string,
): Promise<void> {
  const response = await fetch(
    `${API_BASE_URL}/workspaces/${workspaceId}/job-assignments/${jobAssignmentId}/`,
    {
      method: "DELETE",
      headers: authHeaders(token, organizationId),
    },
  );
  if (!response.ok && response.status !== 204) {
    await parseError(response, "Failed to delete job assignment");
  }
}
