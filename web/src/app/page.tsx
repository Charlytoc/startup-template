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
import { readStoredAuth } from "@/lib/auth-storage";

export default function Home() {
  const router = useRouter();
  const [phase, setPhase] = useState<"checking" | "landing">("checking");

  useEffect(() => {
    const { token, user } = readStoredAuth();
    if (token && user) {
      router.replace("/dashboard");
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
            <Button component={Link} href="/dashboard" size="md">
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
