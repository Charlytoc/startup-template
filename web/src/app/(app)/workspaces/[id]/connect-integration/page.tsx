"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Alert,
  Anchor,
  Button,
  Container,
  Loader,
  Center,
  Paper,
  PasswordInput,
  Stack,
  Text,
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
import { connectTelegramBot } from "@/lib/telegram-integration";

export default function ConnectIntegrationPage() {
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

  const [botToken, setBotToken] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [formError, setFormError] = useState<string | null>(null);

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

  const connectMutation = useMutation({
    mutationFn: () =>
      connectTelegramBot(token!, orgId!, workspaceId, {
        bot_token: botToken.trim(),
        display_name: displayName.trim() || null,
      }),
    onSuccess: async () => {
      setFormError(null);
      await queryClient.invalidateQueries({
        queryKey: ["workspace-integrations", token, orgId, workspaceId],
      });
      router.push(`/workspaces/${workspaceId}/integrations`);
    },
    onError: (err: Error) => {
      setFormError(err.message);
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
    <Container size="sm" py="xl" style={{ flex: 1 }}>
      <Stack gap="lg">
        <div>
          <Button component={Link} href={`/workspaces/${workspaceId}/integrations`} variant="subtle" size="xs" mb="xs">
            ← Integrations
          </Button>
          <Title order={2}>Connect integration</Title>
          <Text size="sm" c="dimmed" mt={4}>
            Workspace: <strong>{workspace.name}</strong>
          </Text>
        </div>

        {workspaceMismatch ? (
          <Alert color="yellow" title="Different workspace selected in sidebar">
            The URL points to workspace id {workspaceId}, but the sidebar has workspace {selectedWorkspaceId} selected.
            You can still continue if you have access.
          </Alert>
        ) : null}

        <Paper withBorder radius="md" p="lg">
          <Stack gap="md">
            <Title order={3}>Telegram</Title>
            <Text size="sm" c="dimmed">
              Create a bot with{" "}
              <Anchor href="https://t.me/BotFather" target="_blank" rel="noreferrer" size="sm">
                @BotFather
              </Anchor>
              , then paste the bot token here. After connecting you will return to Integrations. New chatters get a
              12-digit code; approve them on the Integrations page.
            </Text>
            {formError ? (
              <Alert color="red" title="Could not connect">
                {formError}
              </Alert>
            ) : null}
            <PasswordInput
              label="Bot token"
              placeholder="123456789:ABC..."
              value={botToken}
              onChange={(e) => setBotToken(e.currentTarget.value)}
              disabled={connectMutation.isPending}
              required
            />
            <TextInput
              label="Display name (optional)"
              placeholder="@MyBot or label shown in the app"
              value={displayName}
              onChange={(e) => setDisplayName(e.currentTarget.value)}
              disabled={connectMutation.isPending}
            />
            <Button
              onClick={() => connectMutation.mutate()}
              loading={connectMutation.isPending}
              disabled={!botToken.trim()}
            >
              Connect Telegram bot
            </Button>
          </Stack>
        </Paper>
      </Stack>
    </Container>
  );
}
