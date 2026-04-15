"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import {
  Center,
  Container,
  Loader,
  Paper,
  SimpleGrid,
  Stack,
  Text,
  Title,
} from "@mantine/core";
import { useLocalStorage } from "@mantine/hooks";
import { fetchMyOrganizations } from "@/lib/my-organizations";
import {
  SELECTED_ORG_ID_KEY,
  TOKEN_KEY,
  USER_KEY,
  parseOrganization,
  readStoredAuth,
  type AuthUser,
} from "@/lib/auth-storage";

export default function DashboardPage() {
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

  useEffect(() => {
    const { user: stored } = readStoredAuth();
    if (!stored) {
      router.replace("/chat");
      return;
    }
    setSessionOk(true);
  }, [router]);

  const { data: organizations, isPending } = useQuery({
    queryKey: ["my-organizations", token],
    queryFn: () => fetchMyOrganizations(token!),
    enabled: Boolean(token) && sessionOk,
    staleTime: 60_000,
  });

  const displayUser = user ?? readStoredAuth().user;

  const activeOrg = useMemo(() => {
    if (!organizations?.length || selectedOrgId == null) {
      return null;
    }
    return (
      organizations.find((o) => String(o.id) === String(selectedOrgId)) ?? null
    );
  }, [organizations, selectedOrgId]);

  const profileOrg = displayUser ? parseOrganization(displayUser.organization) : null;

  if (!sessionOk || !displayUser) {
    return (
      <Center style={{ flex: 1 }}>
        <Loader size="sm" />
      </Center>
    );
  }

  const displayName =
    [displayUser.first_name, displayUser.last_name].filter(Boolean).join(" ").trim() ||
    displayUser.email;

  return (
    <Container size="md" py="lg" style={{ flex: 1 }}>
      <Stack gap="lg">
        <div>
          <Title order={2}>Dashboard</Title>
          <Text c="dimmed" mt={4}>
            Signed in as {displayName}
          </Text>
        </div>

        <Text size="sm" c="dimmed">
          Use the organization menu in the header to switch context. API requests send the
          selected organization id in the X-Org-Id header.
        </Text>

        <Paper withBorder radius="md" p="md">
          <Stack gap="md">
            <Title order={4}>Active organization</Title>
            {isPending && (
              <Center py="md">
                <Loader size="sm" />
              </Center>
            )}
            {!isPending && activeOrg && (
              <SimpleGrid cols={{ base: 1, sm: 2 }} spacing="sm">
                <div>
                  <Text size="xs" c="dimmed" tt="uppercase" fw={600}>
                    Name
                  </Text>
                  <Text>{activeOrg.name}</Text>
                </div>
                <div>
                  <Text size="xs" c="dimmed" tt="uppercase" fw={600}>
                    Domain
                  </Text>
                  <Text>{activeOrg.domain}</Text>
                </div>
                <div>
                  <Text size="xs" c="dimmed" tt="uppercase" fw={600}>
                    Status
                  </Text>
                  <Text>{activeOrg.status}</Text>
                </div>
              </SimpleGrid>
            )}
            {!isPending && !activeOrg && profileOrg?.id != null && (
              <Text size="sm" c="dimmed">
                Loading organization context… If this persists, open the header menu once your
                memberships have loaded.
              </Text>
            )}
          </Stack>
        </Paper>
      </Stack>
    </Container>
  );
}
