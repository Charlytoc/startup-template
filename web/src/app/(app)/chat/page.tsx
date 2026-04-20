"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import {
  ActionIcon,
  Avatar,
  Badge,
  Box,
  Button,
  Center,
  Group,
  Loader,
  Paper,
  PasswordInput,
  ScrollArea,
  Stack,
  Text,
  Textarea,
  TextInput,
  Title,
} from "@mantine/core";
import { useLocalStorage } from "@mantine/hooks";
import { io, Socket } from "socket.io-client";
import { API_BASE_URL } from "@/lib/api-base";
import type { components } from "@/lib/api/schema";
import {
  ORGANIZATION_HEADER,
  SELECTED_ORG_ID_KEY,
  SELECTED_WORKSPACE_ID_KEY,
  TOKEN_KEY,
  USER_KEY,
  parseOrganization,
  type AuthUser,
} from "@/lib/auth-storage";
import { fetchWorkspaces } from "@/lib/my-workspaces";
import {
  fetchCyberIdentities,
  type CyberIdentity,
} from "@/lib/workspace-cyber-identities";

type ApiSchemas = components["schemas"];
type AuthResponse = ApiSchemas["AuthResponse"];
type SignupRequest = ApiSchemas["SignupRequest"];
type LoginRequest = ApiSchemas["LoginRequest"];
type ApiError = ApiSchemas["ErrorResponseSchema"];

type AgenticChatMessageRequest = {
  message: string;
  cyber_identity_id: string;
};

type AgenticChatMessageResponse = {
  status: string;
  conversation_id: string;
  message_id: string;
  job_assignment_id: string;
};

type AgenticChatErrorResponse = { error: string; error_code: string };

type RealtimeMessage = {
  message: {
    role: "assistant";
    content: string;
    created: string;
  };
  timestamp: string;
};

type ChatEntry = {
  id: string;
  role: "user" | "assistant";
  content: string;
};

const REALTIME_URL = process.env.NEXT_PUBLIC_REALTIME_URL ?? "http://localhost:3001";

export default function ChatPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const identityId = searchParams.get("identity");
  const [mode, setMode] = useState<"login" | "signup">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [status, setStatus] = useState("Not connected");
  const [user, setUser] = useLocalStorage<AuthUser | null>({
    key: USER_KEY,
    defaultValue: null,
    getInitialValueInEffect: true,
  });
  const [token, setToken] = useLocalStorage<string | null>({
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
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<ChatEntry[]>([]);
  const [waiting, setWaiting] = useState(false);
  const socketRef = useRef<Socket | null>(null);
  const bottomRef = useRef<HTMLDivElement | null>(null);
  const viewportRef = useRef<HTMLDivElement | null>(null);

  const authMutation = useMutation({
    mutationFn: async (payload: {
      mode: "login" | "signup";
      body: LoginRequest | SignupRequest;
    }) => {
      const endpoint = payload.mode === "login" ? "/auth/login" : "/auth/signup";
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload.body),
      });
      const data = (await response.json()) as AuthResponse | ApiError;
      if (!response.ok) {
        throw new Error((data as ApiError).error ?? response.statusText);
      }
      return data as AuthResponse;
    },
    onSuccess: (data) => {
      setToken(data.api_token);
      setUser(data.user);
      setStatus("Not connected");
      router.replace("/dashboard");
    },
    onError: (err: Error) => {
      setStatus(`Auth error: ${err.message}`);
    },
  });

  const sendMessageMutation = useMutation({
    mutationFn: async (payload: {
      token: string;
      message: string;
      organizationId: string;
      cyberIdentityId: string;
    }) => {
      const response = await fetch(`${API_BASE_URL}/agentic-chat/messages`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${payload.token}`,
          [ORGANIZATION_HEADER]: String(payload.organizationId),
        },
        body: JSON.stringify({
          message: payload.message,
          cyber_identity_id: payload.cyberIdentityId,
        } satisfies AgenticChatMessageRequest),
      });
      const data = (await response.json()) as
        | AgenticChatMessageResponse
        | AgenticChatErrorResponse
        | ApiError;
      if (!response.ok) {
        const err = data as AgenticChatErrorResponse | ApiError;
        const msg = err.error ?? response.statusText;
        const code = (err as AgenticChatErrorResponse).error_code;
        if (code === "WEB_CHAT_NOT_ENABLED") {
          throw new Error(
            "This identity does not have web chat enabled yet. Go to Cyber identities and click 'Enable in chat'.",
          );
        }
        throw new Error(msg);
      }
      return data as AgenticChatMessageResponse;
    },
    onMutate: ({ message }) => {
      setMessages((prev) => [...prev, { id: `${Date.now()}-user`, role: "user", content: message }]);
      setWaiting(true);
    },
    onError: (err: Error) => {
      setStatus(`Chat error: ${err.message}`);
      setWaiting(false);
    },
  });

  const activeOrganizationId = useMemo(() => {
    if (!user) return null;
    const fromUser = parseOrganization(user.organization).id;
    const picked = selectedOrgId != null ? String(selectedOrgId) : null;
    return picked ?? fromUser ?? null;
  }, [user, selectedOrgId]);

  const needsIdentityPicker = Boolean(user && token && activeOrganizationId && !identityId);

  const { data: workspacesData } = useQuery({
    queryKey: ["workspaces", token, activeOrganizationId],
    queryFn: () => fetchWorkspaces(token!, activeOrganizationId!),
    enabled: needsIdentityPicker,
    staleTime: 30_000,
  });

  const { data: chatEnabledIdentities, isPending: identitiesPending } = useQuery<
    (CyberIdentity & { workspace_name: string })[]
  >({
    queryKey: [
      "chat-enabled-identities",
      token,
      activeOrganizationId,
      (workspacesData ?? []).map((w) => w.id).join(","),
    ],
    queryFn: async () => {
      const workspaces = workspacesData ?? [];
      const lists = await Promise.all(
        workspaces.map((ws) =>
          fetchCyberIdentities(token!, activeOrganizationId!, ws.id)
            .then((rows) =>
              rows
                .filter((r) => r.is_active && r.web_chat_enabled)
                .map((r) => ({ ...r, workspace_name: ws.name })),
            )
            .catch(() => []),
        ),
      );
      return lists.flat();
    },
    enabled: needsIdentityPicker && Array.isArray(workspacesData),
    staleTime: 15_000,
  });

  const canSend = useMemo(
    () =>
      Boolean(
        user &&
          token &&
          activeOrganizationId != null &&
          identityId &&
          input.trim().length > 0 &&
          !waiting &&
          !sendMessageMutation.isPending
      ),
    [input, token, user, activeOrganizationId, identityId, waiting, sendMessageMutation.isPending]
  );

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, waiting]);

  useEffect(() => {
    if (!user) return;
    const socket = io(REALTIME_URL, {
      transports: ["websocket", "polling"],
      timeout: 10000,
    });
    socketRef.current = socket;
    socket.on("connect", () => {
      setStatus("connected");
      socket.emit("join-user", { userId: user.id });
    });
    socket.on("room-joined", (data) => {
      setStatus(`Joined ${data.room}`);
    });
    socket.on("agentic-chat-message", (payload: RealtimeMessage) => {
      setMessages((prev) => [
        ...prev,
        {
          id: `${Date.now()}-assistant`,
          role: "assistant",
          content: payload.message.content,
        },
      ]);
      setWaiting(false);
    });
    socket.on("connect_error", () => {
      setStatus("connection error");
    });
    return () => {
      socket.disconnect();
      socketRef.current = null;
    };
  }, [user]);

  function submitAuth(e: FormEvent) {
    e.preventDefault();
    const body: LoginRequest | SignupRequest =
      mode === "login"
        ? { email, password }
        : { email, password, first_name: firstName || undefined, last_name: lastName || undefined };
    authMutation.mutate({ mode, body });
  }

  function sendMessage(e?: FormEvent) {
    e?.preventDefault();
    if (
      !user ||
      !token ||
      activeOrganizationId == null ||
      !identityId ||
      !input.trim() ||
      waiting ||
      sendMessageMutation.isPending
    ) {
      return;
    }
    const content = input.trim();
    setInput("");
    sendMessageMutation.mutate({
      token,
      message: content,
      organizationId: activeOrganizationId,
      cyberIdentityId: identityId,
    });
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }

  const userInitial = user?.email?.[0]?.toUpperCase() ?? "U";

  if (!user) {
    return (
      <Center h="100vh" bg="var(--mantine-color-body)">
        <Paper w={380} p="xl" radius="lg" shadow="md" withBorder>
          <Stack gap="lg">
            <Stack gap={4}>
              <Title order={2} fw={700}>
                {mode === "login" ? "Welcome back" : "Create account"}
              </Title>
              <Text c="dimmed" size="sm">
                {mode === "login"
                  ? "Sign in to your account to continue"
                  : "Fill in your details to get started"}
              </Text>
            </Stack>

            <form onSubmit={submitAuth}>
              <Stack gap="sm">
                {mode === "signup" && (
                  <Group grow>
                    <TextInput
                      label="First name"
                      placeholder="Jane"
                      value={firstName}
                      onChange={(e) => setFirstName(e.currentTarget.value)}
                    />
                    <TextInput
                      label="Last name"
                      placeholder="Doe"
                      value={lastName}
                      onChange={(e) => setLastName(e.currentTarget.value)}
                    />
                  </Group>
                )}
                <TextInput
                  label="Email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.currentTarget.value)}
                  required
                />
                <PasswordInput
                  label="Password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.currentTarget.value)}
                  required
                />
                <Button type="submit" fullWidth mt="xs" loading={authMutation.isPending}>
                  {mode === "login" ? "Sign in" : "Create account"}
                </Button>
              </Stack>
            </form>

            <Text size="sm" ta="center" c="dimmed">
              {mode === "login" ? "Don't have an account? " : "Already have an account? "}
              <Text
                span
                c="blue"
                style={{ cursor: "pointer" }}
                onClick={() => setMode(mode === "login" ? "signup" : "login")}
              >
                {mode === "login" ? "Sign up" : "Sign in"}
              </Text>
            </Text>
          </Stack>
        </Paper>
      </Center>
    );
  }

  if (!identityId) {
    const manageHref =
      selectedWorkspaceId != null
        ? `/workspaces/${selectedWorkspaceId}/cyber-identities`
        : "/workspace";
    const rows = chatEnabledIdentities ?? [];
    return (
      <Center style={{ flex: 1 }} p="xl">
        <Paper withBorder radius="md" p="xl" maw={560} w="100%">
          <Stack gap="md">
            <div>
              <Title order={3}>Pick a cyber identity</Title>
              <Text c="dimmed" size="sm" mt={4}>
                The chat now runs against a specific identity. Pick one of the
                chat-enabled identities below, or manage them from the cyber
                identities page.
              </Text>
            </div>

            {identitiesPending ? (
              <Center py="md">
                <Loader size="sm" />
              </Center>
            ) : rows.length === 0 ? (
              <Text c="dimmed" size="sm">
                You don&apos;t have any chat-enabled identities yet. Open the cyber
                identities page and click <strong>Enable in chat</strong> on one
                of them.
              </Text>
            ) : (
              <Stack gap="xs">
                {rows.map((row) => (
                  <Button
                    key={row.id}
                    variant="light"
                    justify="space-between"
                    rightSection={<Badge variant="outline">{row.workspace_name}</Badge>}
                    onClick={() => router.push(`/chat?identity=${row.id}`)}
                  >
                    {row.display_name}
                  </Button>
                ))}
              </Stack>
            )}

            <Button component={Link} href={manageHref} variant="default">
              Manage cyber identities
            </Button>
          </Stack>
        </Paper>
      </Center>
    );
  }

  return (
    <Box
      flex={1}
      mih={0}
      style={{ display: "flex", flexDirection: "column", background: "var(--mantine-color-body)" }}
    >
      <Box
        px="lg"
        py="sm"
        style={{
          borderBottom: "1px solid var(--mantine-color-default-border)",
          background: "var(--mantine-color-default)",
          flexShrink: 0,
        }}
      >
        <Group gap="sm" justify="space-between">
          <Group gap="sm">
            <Avatar color="blue" radius="xl" size="sm">
              {userInitial}
            </Avatar>
            <Box>
              <Text size="sm" fw={600} lh={1.2}>
                AI Assistant
              </Text>
              <Text size="xs" c={status === "connected" || status.startsWith("Joined") ? "teal" : "dimmed"}>
                {status.startsWith("Joined") ? "● Online" : status === "connected" ? "● Online" : "○ " + status}
              </Text>
            </Box>
          </Group>
          <Group gap="xs">
            <Badge variant="light" color="violet" title={identityId}>
              Identity: {identityId.slice(0, 8)}…
            </Badge>
            <ActionIcon
              size="sm"
              variant="subtle"
              onClick={() => router.replace("/chat")}
              aria-label="Clear identity"
              title="Clear identity context"
            >
              ✕
            </ActionIcon>
          </Group>
        </Group>
      </Box>

      <ScrollArea style={{ flex: 1 }} viewportRef={viewportRef} px="md" py="sm">
        <Stack gap="md" py="sm" maw={720} mx="auto">
          {messages.length === 0 && (
            <Center h={200}>
              <Stack align="center" gap="xs">
                <Text size="xl">👋</Text>
                <Text fw={500}>How can I help you today?</Text>
                <Text size="sm" c="dimmed">
                  Ask me anything — I have access to your profile info.
                </Text>
              </Stack>
            </Center>
          )}

          {messages.map((m) =>
            m.role === "user" ? (
              <Group key={m.id} justify="flex-end" align="flex-end" gap="xs">
                <Box maw="75%">
                  <Paper
                    px="md"
                    py="sm"
                    radius="xl"
                    style={{
                      background: "var(--mantine-color-blue-6)",
                      borderBottomRightRadius: 4,
                    }}
                  >
                    <Text size="sm" c="white" style={{ whiteSpace: "pre-wrap" }}>
                      {m.content}
                    </Text>
                  </Paper>
                </Box>
                <Avatar color="blue" radius="xl" size="sm">
                  {userInitial}
                </Avatar>
              </Group>
            ) : (
              <Group key={m.id} align="flex-end" gap="xs">
                <Avatar color="violet" radius="xl" size="sm">
                  AI
                </Avatar>
                <Box maw="75%">
                  <Paper
                    px="md"
                    py="sm"
                    radius="xl"
                    style={{
                      background: "var(--mantine-color-default)",
                      border: "1px solid var(--mantine-color-default-border)",
                      borderBottomLeftRadius: 4,
                    }}
                  >
                    <Text size="sm" style={{ whiteSpace: "pre-wrap" }}>
                      {m.content}
                    </Text>
                  </Paper>
                </Box>
              </Group>
            )
          )}

          {waiting && (
            <Group align="flex-end" gap="xs">
              <Avatar color="violet" radius="xl" size="sm">
                AI
              </Avatar>
              <Paper
                px="md"
                py="sm"
                radius="xl"
                style={{
                  background: "var(--mantine-color-default)",
                  border: "1px solid var(--mantine-color-default-border)",
                  borderBottomLeftRadius: 4,
                }}
              >
                <Loader size="xs" type="dots" />
              </Paper>
            </Group>
          )}

          <div ref={bottomRef} />
        </Stack>
      </ScrollArea>

      <Box
        px="md"
        py="sm"
        style={{
          borderTop: "1px solid var(--mantine-color-default-border)",
          background: "var(--mantine-color-default)",
          flexShrink: 0,
        }}
      >
        <Box maw={720} mx="auto">
          <form onSubmit={sendMessage}>
            <Paper
              radius="xl"
              withBorder
              style={{
                display: "flex",
                alignItems: "flex-end",
                gap: 8,
                padding: "8px 8px 8px 16px",
                borderColor: "var(--mantine-color-default-border)",
              }}
            >
              <Textarea
                style={{ flex: 1 }}
                placeholder="Message AI Assistant… (Enter to send, Shift+Enter for new line)"
                value={input}
                onChange={(e) => setInput(e.currentTarget.value)}
                onKeyDown={handleKeyDown}
                autosize
                minRows={1}
                maxRows={6}
                variant="unstyled"
              />
              <ActionIcon
                type="submit"
                size="lg"
                radius="xl"
                disabled={!canSend}
                color="blue"
                variant={canSend ? "filled" : "subtle"}
              >
                ↑
              </ActionIcon>
            </Paper>
          </form>
        </Box>
      </Box>
    </Box>
  );
}
