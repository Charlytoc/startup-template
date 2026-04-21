import { API_BASE_URL } from "@/lib/api-base";
import { ORGANIZATION_HEADER } from "@/lib/auth-storage";
import type { CyberIdentity } from "@/lib/workspace-cyber-identities";
import type { WorkspaceIntegrationItem } from "@/lib/workspace-integrations";

export type ActionableCatalogRow = {
  slug: string;
  name: string;
  description: string;
  provider: string;
  integration_account_id: string | null;
  integration: {
    integration_account_id: string;
    provider: string;
    display_name: string;
    status: string;
  } | null;
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

/** Inbound events that map to at most one enabled listener per integration account. */
export const INTEGRATION_INBOUND_EVENT_SLUGS = [
  "telegram.private_message",
  "instagram.dm_message",
] as const;

const INBOUND_SLUG_SET = new Set<string>(INTEGRATION_INBOUND_EVENT_SLUGS);

export const INTEGRATION_INBOUND_EVENT_OPTIONS = [
  { value: "telegram.private_message", label: "Telegram — inbound private messages" },
  { value: "instagram.dm_message", label: "Instagram — inbound direct messages" },
] as const;

/** Inbound event options shown per provider when attaching/editing an integration. */
export const PROVIDER_INBOUND_EVENTS: Record<
  "telegram" | "instagram",
  readonly { value: string; label: string }[]
> = {
  telegram: INTEGRATION_INBOUND_EVENT_OPTIONS.filter((o) => o.value.startsWith("telegram.")),
  instagram: INTEGRATION_INBOUND_EVENT_OPTIONS.filter((o) => o.value.startsWith("instagram.")),
};

export type AttachedIntegrationGroup = {
  integration_account_id: string;
  provider: string;
  display_name: string;
  actionKeys: string[];
  /** Subset of ``integrationEventSlugs`` that apply to this provider (for display). */
  eventSlugs: string[];
};

export function groupSelectionByIntegration(
  actionKeys: string[],
  integrationEventSlugs: string[],
  integrations: WorkspaceIntegrationItem[],
): { attached: AttachedIntegrationGroup[]; systemActionKeys: string[] } {
  const systemActionKeys: string[] = [];
  const byAccount = new Map<string, string[]>();

  for (const key of actionKeys) {
    const { integration_account_id } = keyToAction(key);
    if (!integration_account_id) {
      systemActionKeys.push(key);
      continue;
    }
    if (!byAccount.has(integration_account_id)) {
      byAccount.set(integration_account_id, []);
    }
    byAccount.get(integration_account_id)!.push(key);
  }

  const integrationById = new Map(integrations.map((i) => [i.id, i] as const));

  const attached: AttachedIntegrationGroup[] = [];
  for (const [accountId, keys] of byAccount) {
    const row = integrationById.get(accountId);
    const provider = (row?.provider ?? "unknown").toLowerCase();
    const inboundOpts =
      provider === "telegram" || provider === "instagram"
        ? PROVIDER_INBOUND_EVENTS[provider]
        : [];
    const allowed = new Set(inboundOpts.map((o) => o.value));
    const eventSlugs = integrationEventSlugs.filter((s) => allowed.has(s));
    attached.push({
      integration_account_id: accountId,
      provider,
      display_name: row?.display_name ?? accountId,
      actionKeys: keys,
      eventSlugs,
    });
  }
  attached.sort((a, b) => a.display_name.localeCompare(b.display_name));
  return { attached, systemActionKeys };
}

/** Actionable rows not bound to an integration (system tools). */
export function systemActionableRows(actionables: ActionableCatalogRow[]): ActionableCatalogRow[] {
  return actionables.filter((a) => a.integration_account_id == null);
}

export function systemActionOptions(actionables: ActionableCatalogRow[]) {
  return systemActionableRows(actionables).map((a) => ({
    value: actionKey(a),
    label: a.name,
  }));
}

export function integrationActionOptionsForAccount(
  actionables: ActionableCatalogRow[],
  integrationAccountId: string,
) {
  return actionables
    .filter((a) => a.integration_account_id === integrationAccountId)
    .map((a) => ({
      value: actionKey(a),
      label: a.name,
    }));
}

/** Remove one integration’s actions and prune inbound slugs if no send actions remain for that provider. */
export function removeIntegrationGroup(
  actionKeys: string[],
  integrationEventSlugs: string[],
  integrationAccountId: string,
): { actionKeys: string[]; eventSlugs: string[] } {
  const newKeys = actionKeys.filter(
    (k) => keyToAction(k).integration_account_id !== integrationAccountId,
  );
  const hasTelegramSend = newKeys.some((k) => {
    const a = keyToAction(k);
    return a.actionable_slug === "telegram.send_message" && a.integration_account_id != null;
  });
  const hasInstagramSend = newKeys.some((k) => {
    const a = keyToAction(k);
    return a.actionable_slug === "instagram.send_message" && a.integration_account_id != null;
  });
  let eventSlugs = [...integrationEventSlugs];
  if (!hasTelegramSend) {
    eventSlugs = eventSlugs.filter((s) => s !== "telegram.private_message");
  }
  if (!hasInstagramSend) {
    eventSlugs = eventSlugs.filter((s) => s !== "instagram.dm_message");
  }
  return { actionKeys: newKeys, eventSlugs };
}

/** Replace or add actions for ``integrationAccountId`` and set inbound slugs for that account's provider. */
export function mergeIntegrationGroup(
  actionKeys: string[],
  integrationEventSlugs: string[],
  integrationAccountId: string,
  newActionKeysForAccount: string[],
  newEventSlugsForModal: string[],
  integrations: WorkspaceIntegrationItem[],
): { actionKeys: string[]; eventSlugs: string[] } {
  const without = actionKeys.filter(
    (k) => keyToAction(k).integration_account_id !== integrationAccountId,
  );
  const mergedKeys = [...without, ...newActionKeysForAccount];
  const row = integrations.find((i) => i.id === integrationAccountId);
  const provider = (row?.provider ?? "").toLowerCase();
  let nextSlugs: string[];
  if (provider === "telegram" || provider === "instagram") {
    const providerSlugSet = new Set(PROVIDER_INBOUND_EVENTS[provider].map((o) => o.value));
    const allowedModal = newEventSlugsForModal.filter((s) => providerSlugSet.has(s));
    const stripped = integrationEventSlugs.filter((s) => !providerSlugSet.has(s));
    nextSlugs = [...stripped, ...allowedModal];
  } else {
    const slugSet = new Set(integrationEventSlugs);
    for (const s of newEventSlugsForModal) {
      slugSet.add(s);
    }
    nextSlugs = [...slugSet];
  }
  return { actionKeys: mergedKeys, eventSlugs: [...new Set(nextSlugs)] };
}

export type TriggerRecord = Record<string, unknown>;

/** Split known inbound integration event triggers from cron / other triggers (preserved on save). */
export function splitJobTriggers(triggers: TriggerRecord[] | undefined): {
  integrationEventSlugs: string[];
  otherTriggers: TriggerRecord[];
} {
  const list = triggers ?? [];
  const seenInbound = new Set<string>();
  const otherTriggers: TriggerRecord[] = [];
  for (const t of list) {
    const ty = typeof t.type === "string" ? t.type : "";
    const on = typeof (t as { on?: string }).on === "string" ? (t as { on: string }).on : "";
    if (ty === "event" && INBOUND_SLUG_SET.has(on)) {
      seenInbound.add(on);
    } else {
      otherTriggers.push(t);
    }
  }
  const integrationEventSlugs = INTEGRATION_INBOUND_EVENT_SLUGS.filter((s) => seenInbound.has(s));
  return { integrationEventSlugs, otherTriggers };
}

export function buildTriggersPayload(
  integrationEventSlugs: string[],
  otherTriggers: TriggerRecord[],
): TriggerRecord[] {
  const events = integrationEventSlugs.map((on) => ({ type: "event", on, filter: {} }));
  return [...events, ...otherTriggers];
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
