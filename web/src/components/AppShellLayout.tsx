"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  AppShell,
  Box,
  Button,
  Center,
  Group,
  Loader,
  NavLink,
  Text,
  Title,
} from "@mantine/core";
import { useLocalStorage } from "@mantine/hooks";
import { OrganizationSwitcher } from "@/components/OrganizationSwitcher";
import {
  SELECTED_ORG_ID_KEY,
  TOKEN_KEY,
  USER_KEY,
  readStoredAuth,
  type AuthUser,
} from "@/lib/auth-storage";

export function AppShellLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [mounted, setMounted] = useState(false);
  const [user, , removeUser] = useLocalStorage<AuthUser | null>({
    key: USER_KEY,
    defaultValue: null,
    getInitialValueInEffect: true,
  });
  const [, , removeToken] = useLocalStorage<string | null>({
    key: TOKEN_KEY,
    defaultValue: null,
    getInitialValueInEffect: true,
  });
  const [, , removeSelectedOrg] = useLocalStorage<number | null>({
    key: SELECTED_ORG_ID_KEY,
    defaultValue: null,
    getInitialValueInEffect: true,
  });

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!mounted) return;
    const onDashboard = pathname === "/dashboard" || pathname?.startsWith("/dashboard/");
    if (!onDashboard) return;
    // useLocalStorage(..., getInitialValueInEffect: true) is still null on first paint; do not
    // treat that as "logged out" or we redirect before localStorage is applied to state.
    if (!readStoredAuth().user) {
      router.replace("/chat");
    }
  }, [mounted, pathname, router]);

  if (!mounted) {
    const onChat = pathname === "/chat" || pathname?.startsWith("/chat/");
    if (onChat) {
      return <>{children}</>;
    }
    return (
      <Center h="100vh" bg="var(--mantine-color-body)">
        <Loader size="sm" />
      </Center>
    );
  }

  const sessionUser = readStoredAuth().user;
  const effectiveUser = user ?? sessionUser;

  if (!effectiveUser) {
    return <>{children}</>;
  }

  function signOut() {
    removeToken();
    removeUser();
    removeSelectedOrg();
    router.push("/");
  }

  return (
    <AppShell
      header={{ height: 56 }}
      navbar={{
        width: 220,
        breakpoint: "sm",
        collapsed: { mobile: false },
      }}
      padding={0}
    >
      <AppShell.Header px="md" py={6} style={{ display: "flex", alignItems: "center" }}>
        <Group justify="space-between" w="100%" wrap="nowrap" gap="sm">
          <Title order={4} fw={700} lineClamp={1}>
            Coworkers AI
          </Title>
          <Group gap="sm" wrap="nowrap" justify="flex-end" style={{ flex: 1, minWidth: 0 }}>
            <OrganizationSwitcher />
            <Text size="sm" c="dimmed" visibleFrom="sm" lineClamp={1} maw={200}>
              {effectiveUser.email}
            </Text>
            <Button variant="default" size="xs" onClick={signOut}>
              Sign out
            </Button>
          </Group>
        </Group>
      </AppShell.Header>

      <AppShell.Navbar p="xs">
        <NavLink
          component={Link}
          href="/dashboard"
          label="Dashboard"
          active={pathname === "/dashboard"}
        />
        <NavLink
          component={Link}
          href="/chat"
          label="Chat"
          active={pathname === "/chat"}
        />
      </AppShell.Navbar>

      <AppShell.Main
        bg="var(--mantine-color-body)"
        style={{
          display: "flex",
          flexDirection: "column",
          minHeight: 0,
          height: "calc(100vh - var(--app-shell-header-height, 56px))",
        }}
      >
        <Box style={{ flex: 1, minHeight: 0, display: "flex", flexDirection: "column" }}>
          {children}
        </Box>
      </AppShell.Main>
    </AppShell>
  );
}
