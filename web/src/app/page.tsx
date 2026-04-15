"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Button,
  Center,
  Container,
  Group,
  Loader,
  Stack,
  Text,
  Title,
} from "@mantine/core";
import type { components } from "@/lib/api/schema";

type AuthUser = components["schemas"]["UserResponse"];

const TOKEN_KEY = "startup_template_token";
const USER_KEY = "startup_template_user";

function readStoredAuth(): { token: string | null; user: AuthUser | null } {
  if (typeof window === "undefined") {
    return { token: null, user: null };
  }
  try {
    const rawT = localStorage.getItem(TOKEN_KEY);
    const rawU = localStorage.getItem(USER_KEY);
    const token = rawT ? (JSON.parse(rawT) as string | null) : null;
    const user = rawU ? (JSON.parse(rawU) as AuthUser | null) : null;
    return {
      token: typeof token === "string" && token.length > 0 ? token : null,
      user: user && typeof user === "object" && "id" in user ? user : null,
    };
  } catch {
    return { token: null, user: null };
  }
}

export default function Home() {
  const router = useRouter();
  const [phase, setPhase] = useState<"checking" | "landing">("checking");

  useEffect(() => {
    const { token, user } = readStoredAuth();
    if (token && user) {
      router.replace("/chat");
      return;
    }
    setPhase("landing");
  }, [router]);

  if (phase === "checking") {
    return (
      <Center h="100vh" bg="var(--mantine-color-body)">
        <Loader size="sm" />
      </Center>
    );
  }

  return (
    <Center h="100vh" bg="var(--mantine-color-body)">
      <Container size="sm" py="xl">
        <Stack gap="xl" align="center" ta="center">
          <Stack gap="xs" maw={480}>
            <Title order={1} fw={800}>
              Coworkers AI
            </Title>
            <Text c="dimmed" size="lg">
              Virtual workers for your organization — chat, tasks, and realtime collaboration.
            </Text>
          </Stack>
          <Group gap="sm">
            <Button component={Link} href="/chat" size="md">
              Open app
            </Button>
            <Button component={Link} href="/chat" variant="default" size="md">
              Sign in
            </Button>
          </Group>
        </Stack>
      </Container>
    </Center>
  );
}
