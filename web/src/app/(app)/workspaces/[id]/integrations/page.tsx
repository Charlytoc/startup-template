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
  Paper,
  Stack,
  Table,
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
import { disconnectTelegramIntegration } from "@/lib/telegram-integration";
import { fetchWorkspaceIntegrations } from "@/lib/workspace-integrations";

export default function WorkspaceIntegrationsPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const params = useParams();
  const workspaceIdParam = params.id;
  const workspaceId =
    typeof workspaceIdParam === "string"
      ? Number.parseInt(workspaceIdParam, 10)
      : Array.isArray(workspaceIdParam)
        ? Number.parseInt(workspaceIdParam[0] ?? "", 10)
        : Number.NaN;

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

  const [disconnectError, setDisconnectError] = useState<string | null>(null);

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
    if (!workspaces?.length || Number.isNaN(workspaceId)) {
      return null;
    }
    return workspaces.find((w) => w.id === workspaceId) ?? null;
  }, [workspaces, workspaceId]);

  const {
    data: integrations,
    isPending: intPending,
    error: intError,
  } = useQuery({
    queryKey: ["workspace-integrations", token, orgId, workspaceId],
    queryFn: () => fetchWorkspaceIntegrations(token!, orgId!, workspaceId),
    enabled: Boolean(token) && sessionOk && orgId != null && !Number.isNaN(workspaceId) && Boolean(workspace),
    staleTime: 15_000,
  });

  const disconnectMutation = useMutation({
    mutationFn: (integrationAccountId: string) =>
      disconnectTelegramIntegration(token!, orgId!, workspaceId, integrationAccountId),
    onSuccess: async () => {
      setDisconnectError(null);
      await queryClient.invalidateQueries({
        queryKey: ["workspace-integrations", token, orgId, workspaceId],
      });
      await queryClient.invalidateQueries({
        queryKey: ["workspace-actionables", token, orgId, workspaceId],
      });
      await queryClient.invalidateQueries({
        queryKey: ["job-assignments", token, orgId, workspaceId],
      });
    },
    onError: (err: Error) => {
      setDisconnectError(err.message);
    },
  });

  const displayUser = user ?? readStoredAuth().user;
  const workspaceMismatch =
    selectedWorkspaceId != null && selectedWorkspaceId !== workspaceId && !Number.isNaN(workspaceId);

  if (!sessionOk || !displayUser) {
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
    <Container size="md" py="xl" style={{ flex: 1 }}>
      <Stack gap="lg">
        <div>
          <Button component={Link} href="/workspace" variant="subtle" size="xs" mb="xs">
            ← Workspace home
          </Button>
          <Group justify="space-between" align="flex-start" wrap="wrap" gap="sm">
            <div>
              <Title order={2}>Integrations</Title>
              <Text size="sm" c="dimmed" mt={4}>
                Workspace: <strong>{workspace.name}</strong>
              </Text>
            </div>
            <Button component={Link} href={`/workspaces/${workspaceId}/connect-integration`}>
              Add integration
            </Button>
          </Group>
        </div>

        {workspaceMismatch ? (
          <Alert color="yellow" title="Different workspace selected in sidebar">
            The URL points to workspace id {workspaceId}, but the sidebar has workspace {selectedWorkspaceId}{" "}
            selected.
          </Alert>
        ) : null}

        {intError ? (
          <Alert color="red" title="Could not load integrations">
            {(intError as Error).message}
          </Alert>
        ) : null}

        {disconnectError ? (
          <Alert color="red" title="Could not disconnect" onClose={() => setDisconnectError(null)} withCloseButton>
            {disconnectError}
          </Alert>
        ) : null}

        <Paper withBorder radius="md" p="lg">
          {intPending ? (
            <Center py="xl">
              <Loader size="sm" />
            </Center>
          ) : !integrations?.length ? (
            <Stack gap="sm">
              <Text c="dimmed" size="sm">
                No integrations yet. Connect Telegram (or other providers later) to receive webhooks and run tasks.
              </Text>
              <Button component={Link} href={`/workspaces/${workspaceId}/connect-integration`} variant="light" w="fit-content">
                Connect Telegram
              </Button>
            </Stack>
          ) : (
            <Table striped highlightOnHover verticalSpacing="sm">
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>Provider</Table.Th>
                  <Table.Th>Display name</Table.Th>
                  <Table.Th>Status</Table.Th>
                  <Table.Th>External id</Table.Th>
                  <Table.Th>Created</Table.Th>
                  <Table.Th style={{ width: 200 }}>Actions</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {integrations.map((row) => (
                  <Table.Tr key={row.id}>
                    <Table.Td>{row.provider}</Table.Td>
                    <Table.Td>{row.display_name || "—"}</Table.Td>
                    <Table.Td>{row.status}</Table.Td>
                    <Table.Td>
                      <Text size="xs" ff="monospace">
                        {row.external_account_id}
                      </Text>
                    </Table.Td>
                    <Table.Td>
                      <Text size="xs">{new Date(row.created).toLocaleString()}</Text>
                    </Table.Td>
                    <Table.Td>
                      <Group gap={4}>
                        <Button
                          size="xs"
                          variant="subtle"
                          component={Link}
                          href={`/workspaces/${workspaceId}/integrations/${row.id}`}
                        >
                          View
                        </Button>
                        {row.provider === "telegram" ? (
                          <Button
                            size="xs"
                            variant="subtle"
                            color="red"
                            loading={disconnectMutation.isPending}
                            disabled={!token || orgId == null}
                            onClick={() => {
                              if (
                                confirm(
                                  `Disconnect ${row.display_name || "this Telegram bot"}? Webhooks will be removed and the bot will stop receiving events here.`,
                                )
                              ) {
                                setDisconnectError(null);
                                disconnectMutation.mutate(row.id);
                              }
                            }}
                          >
                            Disconnect
                          </Button>
                        ) : null}
                      </Group>
                    </Table.Td>
                  </Table.Tr>
                ))}
              </Table.Tbody>
            </Table>
          )}
        </Paper>

        {/* Approve-sender flow now lives in the integration details page (/integrations/[accountId]). */}
      </Stack>
    </Container>
  );
}
