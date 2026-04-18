import { API_BASE_URL } from "@/lib/api-base";
import { ORGANIZATION_HEADER } from "@/lib/auth-storage";

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

export type JobAssignment = {
  id: string;
  workspace_id: number;
  role_name: string;
  description: string;
  instructions: string;
  enabled: boolean;
  config: Record<string, unknown>;
  created: string;
};

export type JobAssignmentCreateInput = {
  role_name: string;
  description?: string;
  instructions?: string;
  enabled?: boolean;
  config?: Record<string, unknown>;
};

export type JobAssignmentUpdateInput = Partial<JobAssignmentCreateInput>;

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
