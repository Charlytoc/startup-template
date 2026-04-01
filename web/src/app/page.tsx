"use client";

import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import {
  ActionIcon,
  Avatar,
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
import type { components } from "@/lib/api/schema";

type ApiSchemas = components["schemas"];
type AuthUser = ApiSchemas["UserResponse"];
type AuthResponse = ApiSchemas["AuthResponse"];
type SignupRequest = ApiSchemas["SignupRequest"];
type LoginRequest = ApiSchemas["LoginRequest"];
type ApiError = ApiSchemas["ErrorResponseSchema"];
type AgenticChatMessageRequest = ApiSchemas["AgenticChatMessageRequest"];
type AgenticChatMessageResponse = ApiSchemas["AgenticChatMessageResponse"];

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

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api";
const REALTIME_URL = process.env.NEXT_PUBLIC_REALTIME_URL ?? "http://localhost:3001";
const TOKEN_KEY = "startup_template_token";
const USER_KEY = "startup_template_user";

export default function Home() {
  const [mode, setMode] = useState<"login" | "signup">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [status, setStatus] = useState("Not connected");
  const [user, setUser, removeUser] = useLocalStorage<AuthUser | null>({
    key: USER_KEY,
    defaultValue: null,
    getInitialValueInEffect: true,
  });
  const [token, setToken, removeToken] = useLocalStorage<string | null>({
    key: TOKEN_KEY,
    defaultValue: null,
    getInitialValueInEffect: true,
  });
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<ChatEntry[]>([]);
  const [waiting, setWaiting] = useState(false);
  const socketRef = useRef<Socket | null>(null);
  const bottomRef = useRef<HTMLDivElement | null>(null);
  const viewportRef = useRef<HTMLDivElement | null>(null);

  const canSend = useMemo(
    () => Boolean(user && token && input.trim().length > 0 && !waiting),
    [input, token, user, waiting]
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

  async function submitAuth(e: FormEvent) {
    e.preventDefault();
    const endpoint = mode === "login" ? "/auth/login" : "/auth/signup";
    const body: LoginRequest | SignupRequest =
      mode === "login"
        ? { email, password }
        : { email, password, first_name: firstName || undefined, last_name: lastName || undefined };

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!response.ok) {
      const err = (await response.json()) as Partial<ApiError>;
      setStatus(`Auth error: ${err.error ?? response.statusText}`);
      return;
    }
    const data = (await response.json()) as AuthResponse;
    setToken(data.api_token);
    setUser(data.user);
  }

  async function sendMessage(e?: FormEvent) {
    e?.preventDefault();
    if (!canSend || !token) return;
    const content = input.trim();
    setInput("");
    setWaiting(true);
    setMessages((prev) => [...prev, { id: `${Date.now()}-user`, role: "user", content }]);

    const payload: AgenticChatMessageRequest = { message: content };
    const response = await fetch(`${API_BASE_URL}/agentic-chat/messages`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      const err = (await response.json()) as Partial<ApiError>;
      setStatus(`Chat error: ${err.error ?? response.statusText}`);
      setWaiting(false);
    } else {
      await response.json() as AgenticChatMessageResponse;
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }

  function logout() {
    removeToken();
    removeUser();
    setMessages([]);
    setStatus("Not connected");
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
                <Button type="submit" fullWidth mt="xs">
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

  return (
    <Box h="100vh" style={{ display: "flex", flexDirection: "column", background: "var(--mantine-color-body)" }}>
      {/* Header */}
      <Box
        px="lg"
        py="sm"
        style={{
          borderBottom: "1px solid var(--mantine-color-default-border)",
          background: "var(--mantine-color-default)",
          flexShrink: 0,
        }}
      >
        <Group justify="space-between">
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
          <Button variant="subtle" color="gray" size="xs" onClick={logout}>
            Sign out
          </Button>
        </Group>
      </Box>

      {/* Messages */}
      <ScrollArea style={{ flex: 1 }} viewportRef={viewportRef} px="md" py="sm">
        <Stack gap="md" py="sm" maw={720} mx="auto">
          {messages.length === 0 && (
            <Center h={200}>
              <Stack align="center" gap="xs">
                <Text size="xl">👋</Text>
                <Text fw={500}>How can I help you today?</Text>
                <Text size="sm" c="dimmed">Ask me anything — I have access to your profile info.</Text>
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
                <Avatar color="violet" radius="xl" size="sm">AI</Avatar>
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
              <Avatar color="violet" radius="xl" size="sm">AI</Avatar>
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

      {/* Input */}
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
