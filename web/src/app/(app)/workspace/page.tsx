"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import {
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

  const { data: organizations, isPending: orgsPending } = useQuery({
    queryKey: ["my-organizations", token],
    queryFn: () => fetchMyOrganizations(token!),
    enabled: Boolean(token) && sessionOk,
    staleTime: 60_000,
  });

  const { data: workspaces, isPending: wsPending } = useQuery({
    queryKey: ["workspaces", token, orgId],
    queryFn: () => fetchWorkspaces(token!, orgId!),
    enabled: Boolean(token) && sessionOk && orgId != null,
    staleTime: 30_000,
  });

  const displayUser = user ?? readStoredAuth().user;

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

  if (!sessionOk || !displayUser) {
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
            </>
          )}
        </Stack>
      </Paper>
    </Container>
  );
}
