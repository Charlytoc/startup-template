"use client";

import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import {
  Badge,
  Button,
  Container,
  Group,
  Paper,
  PasswordInput,
  ScrollArea,
  Stack,
  Text,
  TextInput,
  Title,
} from "@mantine/core";
import { useLocalStorage } from "@mantine/hooks";
import { io, Socket } from "socket.io-client";

type AuthUser = {
  id: number;
  email: string;
  first_name?: string | null;
  last_name?: string | null;
};

type AuthResponse = {
  api_token: string;
  user: AuthUser;
};

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
  const socketRef = useRef<Socket | null>(null);

  const canSend = useMemo(() => Boolean(user && token && input.trim().length > 0), [input, token, user]);

  useEffect(() => {
    if (!user) return;
    const socket = io(REALTIME_URL, {
      transports: ["websocket", "polling"],
      timeout: 10000,
    });
    socketRef.current = socket;
    socket.on("connect", () => {
      setStatus("Realtime connected");
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
    });

    socket.on("connect_error", () => {
      setStatus("Realtime connection error");
    });

    return () => {
      socket.disconnect();
      socketRef.current = null;
      setStatus("Realtime disconnected");
    };
  }, [user]);

  async function submitAuth(e: FormEvent) {
    e.preventDefault();
    const endpoint = mode === "login" ? "/auth/login" : "/auth/signup";
    const body =
      mode === "login"
        ? { email, password }
        : { email, password, first_name: firstName || undefined, last_name: lastName || undefined };

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!response.ok) {
      const err = await response.json();
      setStatus(`Auth error: ${err.error ?? response.statusText}`);
      return;
    }
    const data = (await response.json()) as AuthResponse;
    setToken(data.api_token);
    setUser(data.user);
    setStatus(`Authenticated as ${data.user.email}`);
  }

  async function sendMessage(e: FormEvent) {
    e.preventDefault();
    if (!canSend || !token) return;
    const content = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { id: `${Date.now()}-user`, role: "user", content }]);

    const response = await fetch(`${API_BASE_URL}/agentic-chat/messages`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ message: content }),
    });
    if (!response.ok) {
      const err = await response.json();
      setStatus(`Chat error: ${err.error ?? response.statusText}`);
    }
  }

  function logout() {
    removeToken();
    removeUser();
    setMessages([]);
    setStatus("Logged out");
  }

  return (
    <Container size="md" py="xl">
      <Stack gap="md">
        <Title order={1}>Startup Template Web</Title>
        <Group gap="sm">
          <Badge variant="light">API: {API_BASE_URL}</Badge>
          <Badge variant="light">Realtime: {REALTIME_URL}</Badge>
        </Group>
        <Text c="dimmed">{status}</Text>

        {!user ? (
          <Paper withBorder shadow="sm" p="md" radius="md">
            <form onSubmit={submitAuth}>
              <Stack gap="sm">
                <Title order={3}>{mode === "login" ? "Login" : "Sign up"}</Title>
                <TextInput placeholder="Email" value={email} onChange={(e) => setEmail(e.currentTarget.value)} required />
                <PasswordInput
                  placeholder="Password"
                  value={password}
                  onChange={(e) => setPassword(e.currentTarget.value)}
                  required
                />
                {mode === "signup" && (
                  <>
                    <TextInput placeholder="First name" value={firstName} onChange={(e) => setFirstName(e.currentTarget.value)} />
                    <TextInput placeholder="Last name" value={lastName} onChange={(e) => setLastName(e.currentTarget.value)} />
                  </>
                )}
                <Button type="submit">{mode === "login" ? "Login" : "Create account"}</Button>
                <Button variant="subtle" type="button" onClick={() => setMode(mode === "login" ? "signup" : "login")}>
                  {mode === "login" ? "Need an account? Sign up" : "Already have an account? Login"}
                </Button>
              </Stack>
            </form>
          </Paper>
        ) : (
          <Paper withBorder shadow="sm" p="md" radius="md">
            <Stack gap="sm">
              <Group justify="space-between">
                <Title order={3}>Agentic Chat</Title>
                <Button variant="subtle" onClick={logout}>
                  Logout
                </Button>
              </Group>

              <ScrollArea h={360} type="auto">
                <Stack gap="xs">
                  {messages.map((m) => (
                    <Paper
                      key={m.id}
                      p="xs"
                      radius="sm"
                      bg={m.role === "user" ? "blue.9" : "gray.1"}
                      c={m.role === "user" ? "white" : "black"}
                    >
                      <Text size="sm">
                        <strong>{m.role}:</strong> {m.content}
                      </Text>
                    </Paper>
                  ))}
                </Stack>
              </ScrollArea>

              <form onSubmit={sendMessage}>
                <Group grow align="flex-start">
                  <TextInput
                    placeholder="Write a message..."
                    value={input}
                    onChange={(e) => setInput(e.currentTarget.value)}
                  />
                  <Button type="submit" disabled={!canSend}>
                    Send
                  </Button>
                </Group>
              </form>
            </Stack>
          </Paper>
        )}
      </Stack>
    </Container>
  );
}
