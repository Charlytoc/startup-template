"use client";

import { useEffect } from "react";
import { Group, Loader, Select, Text } from "@mantine/core";
import { useQuery } from "@tanstack/react-query";
import { useLocalStorage } from "@mantine/hooks";
import { fetchMyOrganizations } from "@/lib/my-organizations";
import {
  SELECTED_ORG_ID_KEY,
  TOKEN_KEY,
  USER_KEY,
  parseOrganization,
  type AuthUser,
} from "@/lib/auth-storage";

export function OrganizationSwitcher() {
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
  const [selectedOrgId, setSelectedOrgId] = useLocalStorage<string | null>({
    key: SELECTED_ORG_ID_KEY,
    defaultValue: null,
    getInitialValueInEffect: true,
  });

  const { data: organizations, isPending, isError } = useQuery({
    queryKey: ["my-organizations", token],
    queryFn: () => fetchMyOrganizations(token!),
    enabled: Boolean(token),
    staleTime: 60_000,
  });

  useEffect(() => {
    if (!organizations) return;
    if (organizations.length === 0) {
      const fallback = user ? parseOrganization(user.organization).id : null;
      if (fallback != null) {
        setSelectedOrgId(String(fallback));
      }
      return;
    }
    const allowed = new Set(organizations.map((o) => String(o.id)));
    const current = selectedOrgId != null ? String(selectedOrgId) : null;
    if (current == null || !allowed.has(current)) {
      setSelectedOrgId(String(organizations[0].id));
    }
  }, [organizations, selectedOrgId, setSelectedOrgId, user]);

  if (!token) {
    return null;
  }

  if (isPending) {
    return (
      <Group gap="xs" wrap="nowrap" visibleFrom="sm">
        <Loader size="xs" />
      </Group>
    );
  }

  if (isError || !organizations?.length) {
    return (
      <Text size="xs" c="dimmed" visibleFrom="sm" lineClamp={1} maw={160}>
        Org unavailable
      </Text>
    );
  }

  const selectData = organizations.map((o) => ({
    value: String(o.id),
    label: o.name,
  }));

  return (
    <Select
      size="xs"
      w={{ base: "100%", sm: 200 }}
      maw={240}
      aria-label="Active organization"
      placeholder="Organization"
      data={selectData}
      value={selectedOrgId != null ? String(selectedOrgId) : null}
      onChange={(v) => {
        if (v == null) return;
        setSelectedOrgId(v);
      }}
      allowDeselect={false}
      clearable={false}
      comboboxProps={{ withinPortal: true, zIndex: 400 }}
    />
  );
}
