"use client";

import Link from "next/link";
import { Anchor, Container, Group, Stack, Text, Title } from "@mantine/core";

const PRODUCT = "Coworkers AI";

export type LegalDocPageProps = {
  title: string;
  lastUpdated: string;
  children: React.ReactNode;
};

export function LegalDocPage({ title, lastUpdated, children }: LegalDocPageProps) {
  return (
    <Container component="main" size={680} py="xl" pb={96}>
      <Stack gap="xl">
        <Group justify="space-between" wrap="wrap" gap="sm">
          <Anchor component={Link} href="/" size="sm" c="dimmed">
            ← {PRODUCT}
          </Anchor>
          <Group gap="md" wrap="wrap">
            <Anchor component={Link} href="/privacy-policy" size="sm" c="dimmed">
              Privacy
            </Anchor>
            <Anchor component={Link} href="/terms-of-service" size="sm" c="dimmed">
              Terms
            </Anchor>
          </Group>
        </Group>
        <Stack gap="xs">
          <Title order={1}>{title}</Title>
          <Text size="sm" c="dimmed">
            Last updated: {lastUpdated}
          </Text>
        </Stack>
        <Stack gap="lg" fz="sm" lh={1.7} c="var(--mantine-color-text)">
          {children}
        </Stack>
      </Stack>
    </Container>
  );
}
