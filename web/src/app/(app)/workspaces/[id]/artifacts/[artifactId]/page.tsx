"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Alert,
  Badge,
  Box,
  Button,
  Center,
  Collapse,
  Container,
  Group,
  Loader,
  Modal,
  Paper,
  Stack,
  Text,
  Title,
} from "@mantine/core";
import { useDisclosure, useLocalStorage } from "@mantine/hooks";
import {
  SELECTED_ORG_ID_KEY,
  SELECTED_WORKSPACE_ID_KEY,
  TOKEN_KEY,
  USER_KEY,
  readStoredAuth,
  type AuthUser,
} from "@/lib/auth-storage";
import { fetchWorkspaces } from "@/lib/my-workspaces";
import {
  artifactTextBody,
  artifactTitle,
  deleteWorkspaceArtifact,
  fetchWorkspaceArtifact,
  formatArtifactBytes,
  isHtmlTextArtifact,
  isImageArtifact,
  type WorkspaceArtifact,
} from "@/lib/workspace-artifacts";

function parseWorkspaceId(value: string | string[] | undefined): number {
  const raw = Array.isArray(value) ? value[0] : value;
  return Number.parseInt(raw ?? "", 10);
}

export default function WorkspaceArtifactDetailPage() {
  const queryClient = useQueryClient();
  const router = useRouter();
  const params = useParams();
  const workspaceId = parseWorkspaceId(params.id);
  const artifactIdParam = params.artifactId;
  const artifactId = typeof artifactIdParam === "string" ? artifactIdParam : "";

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

  const [artifactToDelete, setArtifactToDelete] = useState<WorkspaceArtifact | null>(null);
  const [copied, setCopied] = useState(false);
  const htmlPreviewIframeRef = useRef<HTMLIFrameElement | null>(null);
  const [metadataOpened, { toggle: toggleMetadata, close: closeMetadata }] = useDisclosure(false);

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
    Boolean(token) &&
    Boolean(displayUser) &&
    orgId != null &&
    !Number.isNaN(workspaceId) &&
    Boolean(workspace) &&
    Boolean(artifactId);

  const {
    data: artifact,
    isPending: artifactPending,
    error: artifactError,
  } = useQuery({
    queryKey: ["workspace-artifact", token, orgId, workspaceId, artifactId],
    queryFn: () => fetchWorkspaceArtifact(token!, orgId!, workspaceId, artifactId),
    enabled: baseEnabled,
    staleTime: 15_000,
  });

  const deleteMutation = useMutation({
    mutationFn: async () => {
      if (!token || orgId == null || !artifact) throw new Error("Not signed in.");
      await deleteWorkspaceArtifact(token, orgId, workspaceId, artifact.id);
    },
    onSuccess: () => {
      setArtifactToDelete(null);
      void queryClient.invalidateQueries({
        queryKey: ["workspace-artifacts", token, orgId, workspaceId],
      });
      router.push(`/workspaces/${workspaceId}/artifacts`);
    },
  });

  const workspaceMismatch =
    selectedWorkspaceId != null && selectedWorkspaceId !== workspaceId && !Number.isNaN(workspaceId);

  const body = artifact ? artifactTextBody(artifact) : null;
  const htmlArtifact = artifact ? isHtmlTextArtifact(artifact) : false;
  const imageArtifact = artifact ? isImageArtifact(artifact) : false;

  useEffect(() => {
    if (!htmlArtifact || !body) return;
    const el = htmlPreviewIframeRef.current;
    if (!el) return;
    const applyHeight = () => {
      try {
        const doc = el.contentDocument;
        const root = doc?.documentElement;
        const h = Math.max(
          root?.scrollHeight ?? 0,
          doc?.body?.scrollHeight ?? 0,
          root?.offsetHeight ?? 0,
          doc?.body?.offsetHeight ?? 0,
        );
        if (h > 0) el.style.height = `${h}px`;
      } catch {
        // Sandboxed or cross-origin; leave default min-height.
      }
    };
    el.addEventListener("load", applyHeight);
    applyHeight();
    return () => el.removeEventListener("load", applyHeight);
  }, [htmlArtifact, body, artifactId]);

  useEffect(() => {
    closeMetadata();
  }, [artifactId, closeMetadata]);

  async function copyBody() {
    if (!body) return;
    await navigator.clipboard.writeText(body);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1500);
  }

  if (!displayUser) {
    return (
      <Center style={{ flex: 1 }}>
        <Loader size="sm" />
      </Center>
    );
  }

  if (Number.isNaN(workspaceId) || !artifactId) {
    return (
      <Container size="sm" py="xl">
        <Alert color="red" title="Invalid URL">
          Missing or invalid workspace or artifact id.
        </Alert>
        <Button component={Link} href="/workspace" variant="light" mt="md">
          Workspace home
        </Button>
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
          This workspace is not in your list for the current organization.
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
          <Button
            component={Link}
            href={`/workspaces/${workspaceId}/artifacts`}
            variant="subtle"
            size="xs"
            mb="xs"
          >
            ← Artifacts
          </Button>
          {workspaceMismatch ? (
            <Alert color="yellow" title="Different workspace selected in sidebar" mb="sm">
              The URL points to workspace id {workspaceId}, but the sidebar has workspace{" "}
              {selectedWorkspaceId} selected.
            </Alert>
          ) : null}
        </div>

        {artifactError ? (
          <Alert color="red" title="Could not load artifact">
            {(artifactError as Error).message}
          </Alert>
        ) : null}

        {artifactPending ? (
          <Center py="xl">
            <Loader size="sm" />
          </Center>
        ) : artifact ? (
          <Stack gap="md">
            <Group justify="space-between" align="flex-start" wrap="wrap" gap="sm">
              <div style={{ minWidth: 0 }}>
                <Group gap="xs" mb={6}>
                  <Badge variant="light">{artifact.kind}</Badge>
                  {artifact.task_execution?.status ? (
                    <Badge variant="outline" color="gray">
                      {artifact.task_execution.status}
                    </Badge>
                  ) : null}
                </Group>
                <Title order={2}>{artifactTitle(artifact)}</Title>
                <Text size="sm" c="dimmed" mt={4}>
                  Created {new Date(artifact.created).toLocaleString()}
                  {artifact.modified !== artifact.created ? (
                    <> · Modified {new Date(artifact.modified).toLocaleString()}</>
                  ) : null}
                </Text>
              </div>
              <Group gap="xs">
                {body ? (
                  <Button variant="light" size="sm" onClick={() => void copyBody()}>
                    {copied ? "Copied" : "Copy content"}
                  </Button>
                ) : null}
                <Button color="red" variant="light" size="sm" onClick={() => setArtifactToDelete(artifact)}>
                  Delete
                </Button>
              </Group>
            </Group>

            <Paper withBorder radius="md" p="md">
              <Stack gap="xs">
                <Text size="sm" fw={600}>
                  Details
                </Text>
                <Text size="sm" c="dimmed">
                  Identity: {artifact.identity?.display_name ?? "None"}
                </Text>
                <Text size="sm" c="dimmed">
                  Job: {artifact.task_execution?.job_role_name || "None"}
                </Text>
                <Text size="sm" c="dimmed">
                  Integration:{" "}
                  {artifact.integration_account
                    ? `${artifact.integration_account.display_name || artifact.integration_account.external_account_id} (${artifact.integration_account.provider})`
                    : "None"}
                </Text>
                {artifact.media ? (
                  <Text size="sm" c="dimmed">
                    Media: {artifact.media.display_name} · {artifact.media.mime_type}{" "}
                    {formatArtifactBytes(artifact.media.byte_size)}
                  </Text>
                ) : null}
                <Group gap="xs" mt="xs">
                  {artifact.task_execution?.job_assignment_id ? (
                    <Button
                      component={Link}
                      href={`/workspaces/${workspaceId}/job-assignments/${artifact.task_execution.job_assignment_id}`}
                      variant="subtle"
                      size="xs"
                    >
                      Open job
                    </Button>
                  ) : null}
                  {artifact.integration_account ? (
                    <Button
                      component={Link}
                      href={`/workspaces/${workspaceId}/integrations/${artifact.integration_account.id}`}
                      variant="subtle"
                      size="xs"
                    >
                      Open integration
                    </Button>
                  ) : null}
                  {artifact.media?.public_url ? (
                    <Button
                      component="a"
                      href={artifact.media.public_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      variant="subtle"
                      size="xs"
                    >
                      Open media URL
                    </Button>
                  ) : null}
                </Group>
              </Stack>
            </Paper>

            {imageArtifact && artifact.media?.public_url ? (
              <Paper withBorder radius="md" p="md">
                <Box
                  component="img"
                  src={artifact.media.public_url}
                  alt={artifactTitle(artifact)}
                  style={{
                    display: "block",
                    maxWidth: "100%",
                    height: "auto",
                    borderRadius: 8,
                  }}
                />
              </Paper>
            ) : null}

            {body && htmlArtifact ? (
              <Paper withBorder radius="md" p="md">
                <Title order={5} mb="sm">
                  Preview
                </Title>
                <Box
                  ref={htmlPreviewIframeRef}
                  component="iframe"
                  srcDoc={body}
                  sandbox="allow-same-origin"
                  title={artifactTitle(artifact)}
                  style={{
                    display: "block",
                    width: "100%",
                    minHeight: 240,
                    border: "1px solid var(--mantine-color-default-border)",
                    borderRadius: 8,
                    background: "white",
                  }}
                />
              </Paper>
            ) : null}

            {body && !htmlArtifact ? (
              <Paper withBorder radius="md" p="md">
                <Title order={5} mb="sm">
                  Content
                </Title>
                <Text size="sm" style={{ whiteSpace: "pre-wrap" }}>
                  {body}
                </Text>
              </Paper>
            ) : null}

            {!body && !imageArtifact ? (
              <Paper withBorder radius="md" p="md">
                <Text size="sm" c="dimmed">
                  No text or image preview for this artifact.
                </Text>
              </Paper>
            ) : null}

            {Object.keys(artifact.metadata || {}).length > 0 ? (
              <Paper withBorder radius="md" p="md">
                <Button variant="subtle" size="xs" px={0} onClick={toggleMetadata}>
                  {metadataOpened ? "Hide metadata" : "Show metadata"}
                </Button>
                <Collapse in={metadataOpened}>
                  <Text
                    component="pre"
                    size="xs"
                    mt="sm"
                    style={{
                      whiteSpace: "pre-wrap",
                      wordBreak: "break-word",
                      margin: 0,
                      fontFamily: "var(--mantine-font-monospace)",
                    }}
                  >
                    {JSON.stringify(artifact.metadata, null, 2)}
                  </Text>
                </Collapse>
              </Paper>
            ) : null}
          </Stack>
        ) : null}

        <Modal
          opened={artifactToDelete != null}
          onClose={() => {
            if (!deleteMutation.isPending) setArtifactToDelete(null);
          }}
          title="Delete artifact"
          centered
        >
          <Stack gap="md">
            <Text size="sm">
              {artifactToDelete
                ? `Remove “${artifactTitle(artifactToDelete)}” and any linked media files from storage.`
                : null}
            </Text>
            {artifactToDelete?.task_execution ? (
              <Alert color="orange" title="Task run will be removed">
                This artifact is tied to a task execution. Deleting it removes that entire run and every
                other artifact produced in the same run.
              </Alert>
            ) : null}
            {deleteMutation.isError ? (
              <Alert color="red" title="Could not delete">
                {(deleteMutation.error as Error).message}
              </Alert>
            ) : null}
            <Group justify="flex-end" gap="sm">
              <Button variant="default" onClick={() => setArtifactToDelete(null)} disabled={deleteMutation.isPending}>
                Cancel
              </Button>
              <Button color="red" loading={deleteMutation.isPending} onClick={() => deleteMutation.mutate()}>
                Delete
              </Button>
            </Group>
          </Stack>
        </Modal>
      </Stack>
    </Container>
  );
}
