import { API_BASE_URL } from "@/lib/api-base";
import { ORGANIZATION_HEADER } from "@/lib/auth-storage";

export type ArtifactKind =
  | "image"
  | "video"
  | "audio"
  | "document"
  | "text"
  | "external_resource";

export const ARTIFACT_KIND_OPTIONS: { value: ArtifactKind; label: string }[] = [
  { value: "text", label: "Text" },
  { value: "image", label: "Image" },
  { value: "video", label: "Video" },
  { value: "audio", label: "Audio" },
  { value: "document", label: "Document" },
  { value: "external_resource", label: "External resource" },
];

export type WorkspaceArtifact = {
  id: string;
  workspace_id: number;
  kind: ArtifactKind;
  label: string;
  metadata: Record<string, unknown>;
  identity: {
    id: string;
    type: string;
    display_name: string;
  } | null;
  task_execution: {
    id: string;
    name: string;
    status: string;
    job_assignment_id: string | null;
    job_role_name: string;
  } | null;
  media: {
    id: string;
    display_name: string;
    mime_type: string;
    byte_size: number | null;
    public_url: string | null;
  } | null;
  integration_account: {
    id: string;
    provider: string;
    display_name: string;
    external_account_id: string;
  } | null;
  created: string;
  modified: string;
};

export type WorkspaceArtifactFilters = {
  identityId?: string | null;
  jobAssignmentId?: string | null;
  integrationAccountId?: string | null;
  kind?: ArtifactKind | null;
  limit?: number;
};

function authHeaders(token: string, organizationId: string): HeadersInit {
  return {
    Authorization: `Bearer ${token}`,
    [ORGANIZATION_HEADER]: organizationId,
  };
}

async function parseError(response: Response, fallback: string): Promise<never> {
  let message = fallback;
  try {
    const body = (await response.json()) as { error?: string };
    if (body?.error) message = body.error;
  } catch {
    // Ignore malformed error bodies.
  }
  throw new Error(`${message} (${response.status})`);
}

export async function fetchWorkspaceArtifacts(
  token: string,
  organizationId: string,
  workspaceId: number,
  filters: WorkspaceArtifactFilters = {},
): Promise<WorkspaceArtifact[]> {
  const params = new URLSearchParams();
  if (filters.identityId) params.set("identity_id", filters.identityId);
  if (filters.jobAssignmentId) params.set("job_assignment_id", filters.jobAssignmentId);
  if (filters.integrationAccountId) {
    params.set("integration_account_id", filters.integrationAccountId);
  }
  if (filters.kind) params.set("kind", filters.kind);
  params.set("limit", String(filters.limit ?? 100));

  const response = await fetch(
    `${API_BASE_URL}/workspaces/${workspaceId}/artifacts/?${params.toString()}`,
    { headers: authHeaders(token, organizationId) },
  );
  if (!response.ok) await parseError(response, "Failed to load artifacts");
  return response.json() as Promise<WorkspaceArtifact[]>;
}
