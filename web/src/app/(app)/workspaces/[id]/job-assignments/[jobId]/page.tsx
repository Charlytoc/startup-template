"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Alert,
  Button,
  Center,
  Container,
  Group,
  Loader,
  MultiSelect,
  Paper,
  Select,
  Stack,
  Switch,
  Text,
  Textarea,
  TextInput,
  Title,
} from "@mantine/core";
import { useLocalStorage } from "@mantine/hooks";
import {
  SELECTED_ORG_ID_KEY,
  SELECTED_WORKSPACE_ID_KEY,
  TOKEN_KEY,
  USER_KEY,
  readStoredAuth,
  type AuthUser,
} from "@/lib/auth-storage";
import { fetchWorkspaces } from "@/lib/my-workspaces";
import { fetchWorkspaceIntegrations } from "@/lib/workspace-integrations";
import { fetchCyberIdentities } from "@/lib/workspace-cyber-identities";
import {
  actionKey,
  actionsToKeys,
  buildActionsPayload,
  buildIdentitiesPayload,
  fetchJobAssignment,
  fetchWorkspaceActionables,
  updateJobAssignment,
  type JobAssignment,
} from "@/lib/workspace-job-assignments";

export default function JobAssignmentDetailPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const params = useParams();
  const workspaceIdParam = params.id;
  const jobIdParam = params.jobId;

  const workspaceId =
    typeof workspaceIdParam === "string"
      ? Number.parseInt(workspaceIdParam, 10)
      : Array.isArray(workspaceIdParam)
        ? Number.parseInt(workspaceIdParam[0] ?? "", 10)
        : Number.NaN;

  const jobId =
    typeof jobIdParam === "string"
      ? jobIdParam
      : Array.isArray(jobIdParam)
        ? (jobIdParam[0] ?? "")
        : "";

  const [sessionOk, setSessionOk] = useState(false);
  const [user] = useLocalStorage<AuthUser | null>({
    key: USER_KEY,
    defaultValue: null,
    getInitialValueInEffect: true,
  });
  const [token] = useLocalStorage<string | null>({
    key: TOKEN_KEY,
    defaultValue: null,
    getInitialValueInEffect: true,
  });
  const [selectedOrgId] = useLocalStorage<string | null>({
    key: SELECTED_ORG_ID_KEY,
    defaultValue: null,
    getInitialValueInEffect: true,
  });
  const [selectedWorkspaceId] = useLocalStorage<number | null>({
    key: SELECTED_WORKSPACE_ID_KEY,
    defaultValue: null,
    getInitialValueInEffect: true,
  });

  useEffect(() => {
    const { user: stored } = readStoredAuth();
    if (!stored) {
      router.replace("/chat");
      return;
    }
    setSessionOk(true);
  }, [router]);

  const orgId = selectedOrgId != null ? String(selectedOrgId) : null;

  const { data: workspaces, isPending: wsPending } = useQuery({
    queryKey: ["workspaces", token, orgId],
    queryFn: () => fetchWorkspaces(token!, orgId!),
    enabled: Boolean(token) && sessionOk && orgId != null,
    staleTime: 30_000,
  });

  const workspace = useMemo(() => {
    if (!workspaces?.length || Number.isNaN(workspaceId)) return null;
    return workspaces.find((w) => w.id === workspaceId) ?? null;
  }, [workspaces, workspaceId]);

  const baseEnabled =
    Boolean(token) &&
    sessionOk &&
    orgId != null &&
    !Number.isNaN(workspaceId) &&
    Boolean(workspace) &&
    Boolean(jobId);

  const { data: identities } = useQuery({
    queryKey: ["cyber-identities", token, orgId, workspaceId],
    queryFn: () => fetchCyberIdentities(token!, orgId!, workspaceId),
    enabled: baseEnabled,
    staleTime: 15_000,
  });

  const { data: actionables } = useQuery({
    queryKey: ["workspace-actionables", token, orgId, workspaceId],
    queryFn: () => fetchWorkspaceActionables(token!, orgId!, workspaceId),
    enabled: baseEnabled,
    staleTime: 15_000,
  });

  const { data: integrations } = useQuery({
    queryKey: ["workspace-integrations", token, orgId, workspaceId],
    queryFn: () => fetchWorkspaceIntegrations(token!, orgId!, workspaceId),
    enabled: baseEnabled,
    staleTime: 15_000,
  });

  const {
    data: job,
    isPending: jobPending,
    error: jobError,
  } = useQuery({
    queryKey: ["job-assignment", token, orgId, workspaceId, jobId],
    queryFn: () => fetchJobAssignment(token!, orgId!, workspaceId, jobId),
    enabled: baseEnabled,
    staleTime: 15_000,
  });

  const [roleName, setRoleName] = useState("");
  const [description, setDescription] = useState("");
  const [instructions, setInstructions] = useState("");
  const [identityId, setIdentityId] = useState<string | null>(null);
  const [actionKeys, setActionKeys] = useState<string[]>([]);
  const [formError, setFormError] = useState<string | null>(null);

  useEffect(() => {
    if (!job) return;
    setRoleName(job.role_name);
    setDescription(job.description ?? "");
    setInstructions(job.instructions ?? "");
    const ids = (job.config.identities ?? []).map((i) => i.id);
    setIdentityId(ids[0] ?? null);
    setActionKeys(actionsToKeys(job.config.actions ?? []));
    setFormError(null);
  }, [job]);

  const invalidateList = () => {
    void queryClient.invalidateQueries({
      queryKey: ["job-assignments", token, orgId, workspaceId],
    });
  };

  const saveMutation = useMutation({
    mutationFn: () => {
      const identityPayload = buildIdentitiesPayload(
        identityId ? [identityId] : [],
        identities ?? [],
      );
      const actions = buildActionsPayload(actionKeys);
      return updateJobAssignment(token!, orgId!, workspaceId, jobId, {
        role_name: roleName.trim(),
        description: description.trim(),
        instructions: instructions.trim(),
        config: {
          identities: identityPayload,
          actions,
        },
      });
    },
    onSuccess: async (updated: JobAssignment) => {
      setFormError(null);
      invalidateList();
      await queryClient.invalidateQueries({
        queryKey: ["job-assignment", token, orgId, workspaceId, jobId],
      });
      setRoleName(updated.role_name);
      setDescription(updated.description ?? "");
      setInstructions(updated.instructions ?? "");
    },
    onError: (err: Error) => setFormError(err.message),
  });

  const toggleMutation = useMutation({
    mutationFn: (next: boolean) =>
      updateJobAssignment(token!, orgId!, workspaceId, jobId, { enabled: next }),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: ["job-assignment", token, orgId, workspaceId, jobId],
      });
      invalidateList();
    },
  });

  const identityOptions = useMemo(
    () =>
      (identities ?? []).map((i) => ({
        value: i.id,
        label: `${i.display_name} (${i.type})`,
      })),
    [identities],
  );

  const actionOptions = useMemo(
    () =>
      (actionables ?? []).map((a) => ({
        value: actionKey(a),
        label: `${a.name} — ${a.integration?.display_name ?? "system"}`,
      })),
    [actionables],
  );

  const displayUser = user ?? readStoredAuth().user;
  const workspaceMismatch =
    selectedWorkspaceId != null &&
    selectedWorkspaceId !== workspaceId &&
    !Number.isNaN(workspaceId);

  if (!sessionOk || !displayUser) {
    return (
      <Center style={{ flex: 1 }}>
        <Loader size="sm" />
      </Center>
    );
  }

  if (Number.isNaN(workspaceId) || !jobId) {
    return (
      <Container size="sm" py="xl">
        <Alert color="red" title="Invalid link">
          <Button component={Link} href="/workspace" variant="light" size="xs" mt="sm">
            Workspace home
          </Button>
        </Alert>
      </Container>
    );
  }

  if (orgId != null && wsPending) {
    return (
      <Center style={{ flex: 1 }}>
        <Loader size="sm" />
      </Center>
    );
  }

  if (orgId == null || !workspace) {
    return (
      <Container size="sm" py="xl">
        <Text c="dimmed" size="sm">
          Select an organization and open this link from a workspace you belong to.
        </Text>
        <Button component={Link} href="/workspace" variant="light" mt="md">
          Workspace home
        </Button>
      </Container>
    );
  }

  const hasIntegration = (integrations?.length ?? 0) > 0;

  return (
    <Container size="md" py="xl" style={{ flex: 1 }}>
      <Stack gap="lg">
        <div>
          <Button
            component={Link}
            href={`/workspaces/${workspaceId}/job-assignments`}
            variant="subtle"
            size="xs"
            mb="xs"
          >
            ← Job assignments
          </Button>
          <Group justify="space-between" align="flex-start" wrap="wrap">
            <div>
              <Title order={2}>Job assignment</Title>
              <Text size="sm" c="dimmed" mt={4}>
                Workspace: <strong>{workspace.name}</strong>
              </Text>
            </div>
            {job ? (
              <Group gap="sm">
                <Text size="sm" c="dimmed">
                  Enabled
                </Text>
                <Switch
                  checked={job.enabled}
                  onChange={(e) => toggleMutation.mutate(e.currentTarget.checked)}
                  disabled={toggleMutation.isPending}
                />
              </Group>
            ) : null}
          </Group>
        </div>

        {workspaceMismatch ? (
          <Alert color="yellow" title="Different workspace selected in sidebar">
            The URL points to workspace id {workspaceId}, but the sidebar has workspace{" "}
            {selectedWorkspaceId} selected.
          </Alert>
        ) : null}

        {!hasIntegration ? (
          <Alert color="blue" title="No integrations">
            Some actionables require a connected account.
          </Alert>
        ) : null}

        {jobError ? (
          <Alert color="red" title="Could not load job">
            {(jobError as Error).message}
          </Alert>
        ) : null}

        {jobPending ? (
          <Center py="xl">
            <Loader size="sm" />
          </Center>
        ) : job ? (
          <Paper withBorder radius="md" p="lg">
            <Stack gap="md">
              <Text size="xs" c="dimmed" ff="monospace">
                ID: {job.id}
              </Text>
              {formError ? (
                <Alert color="red" title="Could not save">
                  {formError}
                </Alert>
              ) : null}
              <TextInput
                label="Role name"
                value={roleName}
                onChange={(e) => setRoleName(e.currentTarget.value)}
              />
              <Textarea
                label="Description"
                value={description}
                onChange={(e) => setDescription(e.currentTarget.value)}
                autosize
                minRows={3}
                maxRows={16}
              />
              <Textarea
                label="Instructions"
                value={instructions}
                onChange={(e) => setInstructions(e.currentTarget.value)}
                autosize
                minRows={8}
                maxRows={24}
              />
              <Select
                label="Cyber identity"
                description="The workspace persona this job runs as."
                data={identityOptions}
                value={identityId}
                onChange={setIdentityId}
                searchable
                clearable={false}
                allowDeselect={false}
              />
              <MultiSelect
                label="Actions"
                data={actionOptions}
                value={actionKeys}
                onChange={setActionKeys}
                searchable
              />
              <Group justify="flex-end">
                <Button
                  loading={saveMutation.isPending}
                  onClick={() => saveMutation.mutate()}
                  disabled={
                    !roleName.trim() || actionKeys.length === 0 || identityId == null
                  }
                >
                  Save changes
                </Button>
              </Group>
              <div>
                <Text size="sm" fw={600} mb="xs">
                  Raw config (read-only)
                </Text>
                <Paper withBorder p="sm" radius="sm">
                  <pre style={{ margin: 0, fontSize: 11, overflow: "auto", maxHeight: 240 }}>
                    {JSON.stringify(job.config, null, 2)}
                  </pre>
                </Paper>
              </div>
            </Stack>
          </Paper>
        ) : (
          <Alert color="gray" title="Not found">
            This job assignment does not exist or was removed.
          </Alert>
        )}
      </Stack>
    </Container>
  );
}
