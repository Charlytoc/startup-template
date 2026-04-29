import { API_BASE_URL } from "@/lib/api-base";
import type { components } from "@/lib/api/schema";
import { ORGANIZATION_HEADER } from "@/lib/auth-storage";

export const ARTIFACT_KIND_OPTIONS = [
  { value: "text", label: "Text" },
  { value: "image", label: "Image" },
  { value: "video", label: "Video" },
  { value: "audio", label: "Audio" },
  { value: "document", label: "Document" },
  { value: "external_resource", label: "External resource" },
] as const;

export type ArtifactKind = (typeof ARTIFACT_KIND_OPTIONS)[number]["value"];

export type WorkspaceArtifact = components["schemas"]["ArtifactOut"];

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

export async function deleteWorkspaceArtifact(
  token: string,
  organizationId: string,
  workspaceId: number,
  artifactId: string,
): Promise<void> {
  const response = await fetch(
    `${API_BASE_URL}/workspaces/${workspaceId}/artifacts/${artifactId}/`,
    {
      method: "DELETE",
      headers: authHeaders(token, organizationId),
    },
  );
  if (!response.ok) await parseError(response, "Failed to delete artifact");
}
