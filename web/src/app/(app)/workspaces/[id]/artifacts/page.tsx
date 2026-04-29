"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import {
  Alert,
  Badge,
  Button,
  Card,
  Center,
  Container,
  Group,
  Loader,
  Paper,
  Select,
  SimpleGrid,
  Stack,
  Text,
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
import { fetchCyberIdentities } from "@/lib/workspace-cyber-identities";
import { fetchWorkspaceIntegrations } from "@/lib/workspace-integrations";
import { fetchJobAssignments } from "@/lib/workspace-job-assignments";
import {
  ARTIFACT_KIND_OPTIONS,
  fetchWorkspaceArtifacts,
  type ArtifactKind,
  type WorkspaceArtifact,
} from "@/lib/workspace-artifacts";

function parseWorkspaceId(value: string | string[] | undefined): number {
  const raw = Array.isArray(value) ? value[0] : value;
  return Number.parseInt(raw ?? "", 10);
}

function artifactTitle(row: WorkspaceArtifact): string {
  if (row.label.trim()) return row.label;
  if (row.media?.display_name) return row.media.display_name;
  if (typeof row.metadata.title === "string" && row.metadata.title.trim()) {
    return row.metadata.title;
  }
  return `${row.kind} artifact`;
}

function textPreview(row: WorkspaceArtifact): string | null {
  const text = row.metadata.text;
  if (typeof text === "string" && text.trim()) return text.trim();
  const summary = row.metadata.summary;
  if (typeof summary === "string" && summary.trim()) return summary.trim();
  return null;
}

function formatBytes(value: number | null): string {
  if (value == null) return "";
  if (value < 1024) return `${value} B`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`;
  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}

export default function WorkspaceArtifactsPage() {
  const router = useRouter();
  const params = useParams();
  const workspaceId = parseWorkspaceId(params.id);

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

  const [identityId, setIdentityId] = useState<string | null>(null);
  const [jobAssignmentId, setJobAssignmentId] = useState<string | null>(null);
  const [integrationAccountId, setIntegrationAccountId] = useState<string | null>(null);
  const [kind, setKind] = useState<ArtifactKind | null>(null);

  useEffect(() => {
    const { user: stored } = readStoredAuth();
    if (!stored) {
      router.replace("/chat");
    }
  }, [router]);

  const orgId = selectedOrgId != null ? String(selectedOrgId) : null;
  const displayUser = user ?? readStoredAuth().user;

  const { data: workspaces, isPending: wsPending } = useQuery({
    queryKey: ["workspaces", token, orgId],
    queryFn: () => fetchWorkspaces(token!, orgId!),
    enabled: Boolean(token) && Boolean(displayUser) && orgId != null,
    staleTime: 30_000,
  });

  const workspace = useMemo(() => {
    if (!workspaces?.length || Number.isNaN(workspaceId)) return null;
    return workspaces.find((w) => w.id === workspaceId) ?? null;
  }, [workspaces, workspaceId]);

  const baseEnabled =
    Boolean(token) && Boolean(displayUser) && orgId != null && !Number.isNaN(workspaceId) && Boolean(workspace);

  const { data: identities } = useQuery({
    queryKey: ["cyber-identities", token, orgId, workspaceId],
    queryFn: () => fetchCyberIdentities(token!, orgId!, workspaceId),
    enabled: baseEnabled,
    staleTime: 15_000,
  });

  const { data: jobs } = useQuery({
    queryKey: ["job-assignments", token, orgId, workspaceId],
    queryFn: () => fetchJobAssignments(token!, orgId!, workspaceId),
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
    data: artifacts,
    isPending: artifactsPending,
    error: artifactsError,
  } = useQuery({
    queryKey: [
      "workspace-artifacts",
      token,
      orgId,
      workspaceId,
      identityId,
      jobAssignmentId,
      integrationAccountId,
      kind,
    ],
    queryFn: () =>
      fetchWorkspaceArtifacts(token!, orgId!, workspaceId, {
        identityId,
        jobAssignmentId,
        integrationAccountId,
        kind,
        limit: 200,
      }),
    enabled: baseEnabled,
    staleTime: 10_000,
  });

  const workspaceMismatch =
    selectedWorkspaceId != null && selectedWorkspaceId !== workspaceId && !Number.isNaN(workspaceId);

  const identityOptions = useMemo(
    () =>
      (identities ?? []).map((row) => ({
        value: row.id,
        label: `${row.display_name} (${row.type})`,
      })),
    [identities],
  );

  const jobOptions = useMemo(
    () =>
      (jobs ?? []).map((row) => ({
        value: row.id,
        label: row.role_name,
      })),
    [jobs],
  );

  const integrationOptions = useMemo(
    () =>
      (integrations ?? []).map((row) => ({
        value: row.id,
        label: `${row.display_name || row.external_account_id} (${row.provider})`,
      })),
    [integrations],
  );

  if (!displayUser) {
    return (
      <Center style={{ flex: 1 }}>
        <Loader size="sm" />
      </Center>
    );
  }

  if (Number.isNaN(workspaceId)) {
    return (
      <Container size="sm" py="xl">
        <Alert color="red" title="Invalid workspace">
          The workspace id in the URL is not valid.{" "}
          <Button component={Link} href="/workspace" variant="light" size="xs" mt="sm">
            Back to workspace
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

  if (orgId == null) {
    return (
      <Container size="sm" py="xl">
        <Text c="dimmed" size="sm">
          Select an organization in the header first.
        </Text>
        <Button component={Link} href="/workspace" variant="light" mt="md">
          Workspace home
        </Button>
      </Container>
    );
  }

  if (!workspace) {
    return (
      <Container size="sm" py="xl">
        <Alert color="yellow" title="Workspace not found">
          This workspace is not in your list for the current organization, or the id does not match.
        </Alert>
        <Button component={Link} href="/workspace" variant="light" mt="md">
          Workspace home
        </Button>
      </Container>
    );
  }

  return (
    <Container size="lg" py="xl" style={{ flex: 1 }}>
      <Stack gap="lg">
        <div>
          <Button component={Link} href="/workspace" variant="subtle" size="xs" mb="xs">
            ← Workspace home
          </Button>
          <Group justify="space-between" align="flex-start" wrap="wrap" gap="sm">
            <div>
              <Title order={2}>Artifacts</Title>
              <Text size="sm" c="dimmed" mt={4}>
                Workspace: <strong>{workspace.name}</strong>
              </Text>
            </div>
            <Button
              component={Link}
              href={`/workspaces/${workspaceId}/job-assignments`}
              variant="default"
            >
              Manage jobs
            </Button>
          </Group>
        </div>

        {workspaceMismatch ? (
          <Alert color="yellow" title="Different workspace selected in sidebar">
            The URL points to workspace id {workspaceId}, but the sidebar has workspace{" "}
            {selectedWorkspaceId} selected.
          </Alert>
        ) : null}

        <Paper withBorder radius="md" p="md">
          <SimpleGrid cols={{ base: 1, sm: 2, md: 4 }} spacing="sm">
            <Select
              label="Identity"
              placeholder="All identities"
              data={identityOptions}
              value={identityId}
              onChange={setIdentityId}
              searchable
              clearable
            />
            <Select
              label="Job assignment"
              placeholder="All jobs"
              data={jobOptions}
              value={jobAssignmentId}
              onChange={setJobAssignmentId}
              searchable
              clearable
            />
            <Select
              label="Integration"
              placeholder="All integrations"
              data={integrationOptions}
              value={integrationAccountId}
              onChange={setIntegrationAccountId}
              searchable
              clearable
            />
            <Select
              label="Kind"
              placeholder="All kinds"
              data={ARTIFACT_KIND_OPTIONS}
              value={kind}
              onChange={(value) => setKind(value as ArtifactKind | null)}
              clearable
            />
          </SimpleGrid>
          {identityId || jobAssignmentId || integrationAccountId || kind ? (
            <Button
              variant="subtle"
              size="xs"
              mt="sm"
              onClick={() => {
                setIdentityId(null);
                setJobAssignmentId(null);
                setIntegrationAccountId(null);
                setKind(null);
              }}
            >
              Clear filters
            </Button>
          ) : null}
        </Paper>

        {artifactsError ? (
          <Alert color="red" title="Could not load artifacts">
            {(artifactsError as Error).message}
          </Alert>
        ) : null}

        {artifactsPending ? (
          <Center py="xl">
            <Loader size="sm" />
          </Center>
        ) : !artifacts?.length ? (
          <Paper withBorder radius="md" p="lg">
            <Stack gap="sm">
              <Text c="dimmed" size="sm">
                No artifacts match these filters yet.
              </Text>
              <Button
                component={Link}
                href={`/workspaces/${workspaceId}/job-assignments`}
                variant="light"
                w="fit-content"
              >
                Review artifact-producing jobs
              </Button>
            </Stack>
          </Paper>
        ) : (
          <SimpleGrid cols={{ base: 1, md: 2 }} spacing="md">
            {artifacts.map((row) => {
              const preview = textPreview(row);
              const mediaMeta = row.media
                ? [row.media.mime_type, formatBytes(row.media.byte_size)].filter(Boolean).join(" · ")
                : "";
              return (
                <Card key={row.id} withBorder radius="md" p="lg">
                  <Stack gap="sm">
                    <Group justify="space-between" align="flex-start" gap="xs">
                      <div>
                        <Group gap="xs" mb={4}>
                          <Badge variant="light">{row.kind}</Badge>
                          {row.task_execution?.status ? (
                            <Badge variant="outline" color="gray">
                              {row.task_execution.status}
                            </Badge>
                          ) : null}
                        </Group>
                        <Title order={4}>{artifactTitle(row)}</Title>
                        <Text size="xs" c="dimmed">
                          {new Date(row.created).toLocaleString()}
                        </Text>
                      </div>
                    </Group>

                    {preview ? (
                      <Paper withBorder radius="sm" p="sm" bg="var(--mantine-color-gray-light)">
                        <Text size="sm" lineClamp={5} style={{ whiteSpace: "pre-wrap" }}>
                          {preview}
                        </Text>
                      </Paper>
                    ) : row.media ? (
                      <Paper withBorder radius="sm" p="sm">
                        <Text size="sm" fw={500}>
                          {row.media.display_name}
                        </Text>
                        {mediaMeta ? (
                          <Text size="xs" c="dimmed">
                            {mediaMeta}
                          </Text>
                        ) : null}
                        {row.media.public_url ? (
                          <Button
                            component="a"
                            href={row.media.public_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            variant="light"
                            size="xs"
                            mt="xs"
                          >
                            Open media
                          </Button>
                        ) : null}
                      </Paper>
                    ) : (
                      <Text size="sm" c="dimmed">
                        No inline preview for this artifact kind.
                      </Text>
                    )}

                    <Stack gap={4}>
                      <Text size="xs" c="dimmed">
                        Identity: {row.identity?.display_name ?? "None"}
                      </Text>
                      <Text size="xs" c="dimmed">
                        Job: {row.task_execution?.job_role_name || "None"}
                      </Text>
                      <Text size="xs" c="dimmed">
                        Integration:{" "}
                        {row.integration_account
                          ? `${row.integration_account.display_name || row.integration_account.external_account_id} (${row.integration_account.provider})`
                          : "None"}
                      </Text>
                    </Stack>

                    <Group gap="xs">
                      {row.task_execution?.job_assignment_id ? (
                        <Button
                          component={Link}
                          href={`/workspaces/${workspaceId}/job-assignments/${row.task_execution.job_assignment_id}`}
                          variant="subtle"
                          size="xs"
                        >
                          Open job
                        </Button>
                      ) : null}
                      {row.integration_account ? (
                        <Button
                          component={Link}
                          href={`/workspaces/${workspaceId}/integrations/${row.integration_account.id}`}
                          variant="subtle"
                          size="xs"
                        >
                          Open integration
                        </Button>
                      ) : null}
                    </Group>
                  </Stack>
                </Card>
              );
            })}
          </SimpleGrid>
        )}
      </Stack>
    </Container>
  );
}
