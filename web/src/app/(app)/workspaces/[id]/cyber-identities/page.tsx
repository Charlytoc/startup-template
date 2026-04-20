"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ActionIcon,
  Alert,
  Badge,
  Button,
  Center,
  Container,
  Group,
  Loader,
  Modal,
  Paper,
  Select,
  Stack,
  Switch,
  Table,
  Text,
  TextInput,
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
  CYBER_IDENTITY_TYPE_OPTIONS,
  createCyberIdentity,
  deleteCyberIdentity,
  fetchCyberIdentities,
  updateCyberIdentity,
  type CyberIdentity,
  type CyberIdentityType,
} from "@/lib/workspace-cyber-identities";

function typeLabel(type: string): string {
  return CYBER_IDENTITY_TYPE_OPTIONS.find((t) => t.value === type)?.label ?? type;
}

export default function WorkspaceCyberIdentitiesPage() {
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

  const {
    data: identities,
    isPending: identitiesPending,
    error: identitiesError,
  } = useQuery({
    queryKey: ["cyber-identities", token, orgId, workspaceId],
    queryFn: () => fetchCyberIdentities(token!, orgId!, workspaceId),
    enabled:
      Boolean(token) && sessionOk && orgId != null && !Number.isNaN(workspaceId) && Boolean(workspace),
    staleTime: 15_000,
  });

  const [createOpened, { open: openCreate, close: closeCreate }] = useDisclosure(false);
  const [form, setForm] = useState<{ type: CyberIdentityType; display_name: string }>({
    type: "influencer",
    display_name: "",
  });
  const [formError, setFormError] = useState<string | null>(null);

  const invalidate = () =>
    queryClient.invalidateQueries({
      queryKey: ["cyber-identities", token, orgId, workspaceId],
    });

  const createMutation = useMutation({
    mutationFn: () =>
      createCyberIdentity(token!, orgId!, workspaceId, {
        type: form.type,
        display_name: form.display_name.trim(),
      }),
    onSuccess: async () => {
      setFormError(null);
      setForm({ type: "influencer", display_name: "" });
      closeCreate();
      await invalidate();
    },
    onError: (err: Error) => setFormError(err.message),
  });

  const toggleActiveMutation = useMutation({
    mutationFn: ({ row, next }: { row: CyberIdentity; next: boolean }) =>
      updateCyberIdentity(token!, orgId!, workspaceId, row.id, { is_active: next }),
    onSuccess: () => invalidate(),
  });

  const deleteMutation = useMutation({
    mutationFn: (row: CyberIdentity) =>
      deleteCyberIdentity(token!, orgId!, workspaceId, row.id),
    onSuccess: () => invalidate(),
  });

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
              <Title order={2}>Cyber identities</Title>
              <Text size="sm" c="dimmed" mt={4}>
                Workspace: <strong>{workspace.name}</strong>
              </Text>
            </div>
            <Button onClick={openCreate}>New identity</Button>
          </Group>
        </div>

        {workspaceMismatch ? (
          <Alert color="yellow" title="Different workspace selected in sidebar">
            The URL points to workspace id {workspaceId}, but the sidebar has workspace{" "}
            {selectedWorkspaceId} selected.
          </Alert>
        ) : null}

        {identitiesError ? (
          <Alert color="red" title="Could not load cyber identities">
            {(identitiesError as Error).message}
          </Alert>
        ) : null}

        <Paper withBorder radius="md" p="lg">
          {identitiesPending ? (
            <Center py="xl">
              <Loader size="sm" />
            </Center>
          ) : !identities?.length ? (
            <Stack gap="sm">
              <Text c="dimmed" size="sm">
                No cyber identities yet. Create one to assign it to jobs later.
              </Text>
              <Button variant="light" w="fit-content" onClick={openCreate}>
                Create first identity
              </Button>
            </Stack>
          ) : (
            <Table striped highlightOnHover verticalSpacing="sm">
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>Display name</Table.Th>
                  <Table.Th>Type</Table.Th>
                  <Table.Th>Active</Table.Th>
                  <Table.Th>Created</Table.Th>
                  <Table.Th />
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {identities.map((row) => (
                  <Table.Tr key={row.id}>
                    <Table.Td>{row.display_name}</Table.Td>
                    <Table.Td>
                      <Badge variant="light">{typeLabel(row.type)}</Badge>
                    </Table.Td>
                    <Table.Td>
                      <Switch
                        checked={row.is_active}
                        onChange={(e) =>
                          toggleActiveMutation.mutate({
                            row,
                            next: e.currentTarget.checked,
                          })
                        }
                        disabled={toggleActiveMutation.isPending}
                      />
                    </Table.Td>
                    <Table.Td>
                      <Text size="xs">{new Date(row.created).toLocaleString()}</Text>
                    </Table.Td>
                    <Table.Td>
                      <Group gap={4} justify="flex-end">
                        <Button
                          size="xs"
                          variant="subtle"
                          component={Link}
                          href={`/chat?identity=${row.id}`}
                          disabled={!row.is_active}
                          title={row.is_active ? "Chat as this identity" : "Activate first"}
                        >
                          Chat
                        </Button>
                        <ActionIcon
                          variant="subtle"
                          color="red"
                          onClick={() => {
                            if (confirm(`Delete "${row.display_name}"?`)) {
                              deleteMutation.mutate(row);
                            }
                          }}
                          disabled={deleteMutation.isPending}
                          aria-label="Delete"
                          title="Delete"
                        >
                          ✕
                        </ActionIcon>
                      </Group>
                    </Table.Td>
                  </Table.Tr>
                ))}
              </Table.Tbody>
            </Table>
          )}
        </Paper>
      </Stack>

      <Modal opened={createOpened} onClose={closeCreate} title="New cyber identity" centered>
        <Stack gap="sm">
          {formError ? (
            <Alert color="red" title="Could not create">
              {formError}
            </Alert>
          ) : null}
          <TextInput
            label="Display name"
            placeholder="e.g. Campaign persona Alex"
            value={form.display_name}
            onChange={(e) => {
              const value = e.currentTarget.value;
              setForm((f) => ({ ...f, display_name: value }));
            }}
            data-autofocus
          />
          <Select
            label="Type"
            data={CYBER_IDENTITY_TYPE_OPTIONS}
            value={form.type}
            onChange={(v) => {
              if (v != null) setForm((f) => ({ ...f, type: v as CyberIdentityType }));
            }}
            allowDeselect={false}
          />
          <Group justify="flex-end" gap="xs">
            <Button variant="default" onClick={closeCreate}>
              Cancel
            </Button>
            <Button
              loading={createMutation.isPending}
              onClick={() => createMutation.mutate()}
              disabled={!form.display_name.trim()}
            >
              Create
            </Button>
          </Group>
        </Stack>
      </Modal>
    </Container>
  );
}
