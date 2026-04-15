"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Alert,
  Center,
  Container,
  Loader,
  Paper,
  Select,
  SimpleGrid,
  Stack,
  Text,
  Title,
} from "@mantine/core";
import { useLocalStorage } from "@mantine/hooks";
import {
  SELECTED_ORG_ID_KEY,
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
  const [selectedOrgId, setSelectedOrgId] = useLocalStorage<number | null>({
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

  const displayUser = user ?? readStoredAuth().user;

  const org = displayUser ? parseOrganization(displayUser.organization) : null;

  useEffect(() => {
    if (org?.id != null && selectedOrgId == null) {
      setSelectedOrgId(org.id);
    }
  }, [org?.id, selectedOrgId, setSelectedOrgId]);

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

  const orgSelectData =
    org?.id != null && org.name
      ? [{ value: String(org.id), label: org.name }]
      : org?.id != null
        ? [{ value: String(org.id), label: `Organization #${org.id}` }]
        : [];

  const activeOrg =
    org?.id != null && selectedOrgId === org.id
      ? org
      : org?.id != null
        ? org
        : null;

  return (
    <Container size="md" py="lg" style={{ flex: 1 }}>
      <Stack gap="lg">
        <div>
          <Title order={2}>Dashboard</Title>
          <Text c="dimmed" mt={4}>
            Signed in as {displayName}
          </Text>
        </div>

        <Alert variant="light" color="gray" title="Multiple organizations">
          Membership in more than one organization will be listed here once the API exposes
          it. Until then, your session reflects the organization returned at login. The active
          organization choice below is stored in this browser so we can reuse it when multiple
          orgs are supported.
        </Alert>

        <Paper withBorder radius="md" p="md">
          <Stack gap="md">
            <Title order={4}>Organization</Title>
            {orgSelectData.length > 0 ? (
              <Select
                label="Active organization"
                description="Switching will apply when your account has more than one membership."
                data={orgSelectData}
                value={selectedOrgId != null ? String(selectedOrgId) : null}
                onChange={(v) => setSelectedOrgId(v != null ? Number(v) : null)}
              />
            ) : (
              <Text size="sm" c="dimmed">
                No organization is attached to your profile in the API response yet.
              </Text>
            )}

            {activeOrg && (
              <SimpleGrid cols={{ base: 1, sm: 2 }} spacing="sm">
                <div>
                  <Text size="xs" c="dimmed" tt="uppercase" fw={600}>
                    Name
                  </Text>
                  <Text>{activeOrg.name ?? "—"}</Text>
                </div>
                <div>
                  <Text size="xs" c="dimmed" tt="uppercase" fw={600}>
                    Domain
                  </Text>
                  <Text>{activeOrg.domain ?? "—"}</Text>
                </div>
                <div>
                  <Text size="xs" c="dimmed" tt="uppercase" fw={600}>
                    Status
                  </Text>
                  <Text>{activeOrg.status ?? "—"}</Text>
                </div>
              </SimpleGrid>
            )}
          </Stack>
        </Paper>
      </Stack>
    </Container>
  );
}
