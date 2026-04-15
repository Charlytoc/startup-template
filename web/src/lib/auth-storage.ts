import type { components } from "@/lib/api/schema";

export const TOKEN_KEY = "startup_template_token";
export const USER_KEY = "startup_template_user";
export const SELECTED_ORG_ID_KEY = "startup_template_selected_org_id";

export type AuthUser = components["schemas"]["UserResponse"];

export function readStoredAuth(): { token: string | null; user: AuthUser | null } {
  if (typeof window === "undefined") {
    return { token: null, user: null };
  }
  try {
    const rawT = localStorage.getItem(TOKEN_KEY);
    const rawU = localStorage.getItem(USER_KEY);
    const token = rawT ? (JSON.parse(rawT) as string | null) : null;
    const user = rawU ? (JSON.parse(rawU) as AuthUser | null) : null;
    return {
      token: typeof token === "string" && token.length > 0 ? token : null,
      user: user && typeof user === "object" && "id" in user ? user : null,
    };
  } catch {
    return { token: null, user: null };
  }
}

export function parseOrganization(org: AuthUser["organization"]): {
  id: number | null;
  name: string | null;
  domain: string | null;
  status: string | null;
} {
  if (!org || typeof org !== "object") {
    return { id: null, name: null, domain: null, status: null };
  }
  const o = org as Record<string, unknown>;
  const id = typeof o.id === "number" ? o.id : null;
  const name = typeof o.name === "string" ? o.name : null;
  const domain = typeof o.domain === "string" ? o.domain : null;
  const status = typeof o.status === "string" ? o.status : null;
  return { id, name, domain, status };
}
