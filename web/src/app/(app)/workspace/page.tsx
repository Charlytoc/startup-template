"use client";

import { useEffect, useMemo } from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import {
  Button,
  Card,
  Center,
  Container,
  Loader,
  Paper,
  Stack,
  Text,
  Title,
} from "@mantine/core";
import { useLocalStorage } from "@mantine/hooks";
import { fetchMyOrganizations } from "@/lib/my-organizations";
import { fetchWorkspaces } from "@/lib/my-workspaces";
import {
  SELECTED_ORG_ID_KEY,
  SELECTED_WORKSPACE_ID_KEY,
  TOKEN_KEY,
  USER_KEY,
  readStoredAuth,
  type AuthUser,
} from "@/lib/auth-storage";

export default function WorkspacePage() {
  const router = useRouter();
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
    }
  }, [router]);

  const orgId = selectedOrgId != null ? String(selectedOrgId) : null;
  const displayUser = user ?? readStoredAuth().user;

  const { data: organizations, isPending: orgsPending } = useQuery({
    queryKey: ["my-organizations", token],
    queryFn: () => fetchMyOrganizations(token!),
    enabled: Boolean(token) && Boolean(displayUser),
    staleTime: 60_000,
  });

  const { data: workspaces, isPending: wsPending } = useQuery({
    queryKey: ["workspaces", token, orgId],
    queryFn: () => fetchWorkspaces(token!, orgId!),
    enabled: Boolean(token) && Boolean(displayUser) && orgId != null,
    staleTime: 30_000,
  });

  const activeOrg = useMemo(() => {
    if (!organizations?.length || orgId == null) {
      return null;
    }
    return organizations.find((o) => String(o.id) === orgId) ?? null;
  }, [organizations, orgId]);

  const activeWorkspace = useMemo(() => {
    if (selectedWorkspaceId == null || !workspaces?.length) {
      return null;
    }
    return workspaces.find((w) => w.id === selectedWorkspaceId) ?? null;
  }, [workspaces, selectedWorkspaceId]);

  if (!displayUser) {
    return (
      <Center style={{ flex: 1 }}>
        <Loader size="sm" />
      </Center>
    );
  }

  if (orgsPending || (orgId != null && wsPending)) {
    return (
      <Center style={{ flex: 1 }}>
        <Loader size="sm" />
      </Center>
    );
  }

  return (
    <Container size="sm" py="xl" style={{ flex: 1 }}>
      <Paper withBorder radius="md" p="lg">
        <Stack gap="md">
          <Title order={2}>Workspace</Title>
          {orgId == null ? (
            <Text c="dimmed" size="sm">
              Choose an organization in the header (or sidebar on mobile), then pick or create a workspace from the
              sidebar.
            </Text>
          ) : (
            <>
              <Text size="sm">
                <Text span fw={600}>
                  Organization:
                </Text>{" "}
                {activeOrg?.name ?? orgId}
              </Text>
              {activeWorkspace ? (
                <Text size="sm">
                  <Text span fw={600}>
                    Selected workspace:
                  </Text>{" "}
                  {activeWorkspace.name}
                </Text>
              ) : (
                <Text c="dimmed" size="sm">
                  No workspace selected yet. Use the sidebar to create one or pick an existing workspace.
                </Text>
              )}
              {activeWorkspace ? (
                <Stack gap="sm" mt="md">
                  <Card withBorder radius="md" p="md">
                    <Stack gap="xs">
                      <Title order={4}>Integrations</Title>
                      <Text size="sm" c="dimmed">
                        View connected accounts (Telegram, and more later) or add a new integration.
                      </Text>
                      <Button
                        component={Link}
                        href={`/workspaces/${activeWorkspace.id}/integrations`}
                        variant="light"
                        w="fit-content"
                      >
                        View integrations
                      </Button>
                    </Stack>
                  </Card>
                  <Card withBorder radius="md" p="md">
                    <Stack gap="xs">
                      <Title order={4}>Cyber identities</Title>
                      <Text size="sm" c="dimmed">
                        Personas your agents take on (influencer, community manager, analyst, personal assistant).
                      </Text>
                      <Button
                        component={Link}
                        href={`/workspaces/${activeWorkspace.id}/cyber-identities`}
                        variant="light"
                        w="fit-content"
                      >
                        Manage identities
                      </Button>
                    </Stack>
                  </Card>
                  <Card withBorder radius="md" p="md">
                    <Stack gap="xs">
                      <Title order={4}>Artifacts</Title>
                      <Text size="sm" c="dimmed">
                        Browse durable outputs created by workspace agents and filter them by identity, job, or integration.
                      </Text>
                      <Button
                        component={Link}
                        href={`/workspaces/${activeWorkspace.id}/artifacts`}
                        variant="light"
                        w="fit-content"
                      >
                        View artifacts
                      </Button>
                    </Stack>
                  </Card>
                  <Card withBorder radius="md" p="md">
                    <Stack gap="xs">
                      <Title order={4}>Job assignments</Title>
                      <Text size="sm" c="dimmed">
                        Define roles, triggers, and which actionables run against connected accounts.
                      </Text>
                      <Button
                        component={Link}
                        href={`/workspaces/${activeWorkspace.id}/job-assignments`}
                        variant="light"
                        w="fit-content"
                      >
                        Manage jobs
                      </Button>
                    </Stack>
                  </Card>
                </Stack>
              ) : null}
            </>
          )}
        </Stack>
      </Paper>
    </Container>
  );
}
