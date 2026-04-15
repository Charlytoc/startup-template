import { API_BASE_URL } from "@/lib/api-base";
import type { components } from "@/lib/api/schema";

export type OrganizationResponse = components["schemas"]["OrganizationResponse"];

export async function fetchMyOrganizations(token: string): Promise<OrganizationResponse[]> {
  const response = await fetch(`${API_BASE_URL}/auth/my-organizations`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) {
    throw new Error(`Failed to load organizations (${response.status})`);
  }
  return response.json() as Promise<OrganizationResponse[]>;
}
