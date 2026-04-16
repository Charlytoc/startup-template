"use client";

import { useEffect, useRef, useState } from "react";
import { Button, Group, Loader, Modal, Select, Stack, Text, TextInput } from "@mantine/core";
import { highlightedSelectOptionProps } from "@/components/highlighted-select-option";
import { useDisclosure, useLocalStorage } from "@mantine/hooks";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createWorkspace, fetchWorkspaces } from "@/lib/my-workspaces";
import {
  SELECTED_ORG_ID_KEY,
  SELECTED_WORKSPACE_ID_KEY,
  TOKEN_KEY,
} from "@/lib/auth-storage";

export function WorkspaceSwitcher() {
  const queryClient = useQueryClient();
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
  const [selectedWorkspaceId, setSelectedWorkspaceId] = useLocalStorage<number | null>({
    key: SELECTED_WORKSPACE_ID_KEY,
    defaultValue: null,
    getInitialValueInEffect: true,
  });

  const [createOpened, { open: openCreate, close: closeCreate }] = useDisclosure(false);
  const [newName, setNewName] = useState("");
  const prevOrgIdRef = useRef<string | null>(null);

  const orgId = selectedOrgId != null ? String(selectedOrgId) : null;
  const enabled = Boolean(token && orgId);

  const { data: workspaces, isPending, isError } = useQuery({
    queryKey: ["workspaces", token, orgId],
    queryFn: () => fetchWorkspaces(token!, orgId!),
    enabled,
    staleTime: 30_000,
  });

  useEffect(() => {
    const prev = prevOrgIdRef.current;
    prevOrgIdRef.current = orgId;
    if (prev != null && prev !== orgId) {
      setSelectedWorkspaceId(null);
    }
  }, [orgId, setSelectedWorkspaceId]);

  useEffect(() => {
    if (!workspaces?.length) return;
    const allowed = new Set(workspaces.map((w) => w.id));
    const current = selectedWorkspaceId;
    if (current == null || !allowed.has(current)) {
      setSelectedWorkspaceId(workspaces[0].id);
    }
  }, [workspaces, selectedWorkspaceId, setSelectedWorkspaceId]);

  const createMutation = useMutation({
    mutationFn: async (name: string) => {
      if (!token || !orgId) throw new Error("Not signed in or no organization selected.");
      return createWorkspace(token, orgId, name);
    },
    onSuccess: (created) => {
      void queryClient.invalidateQueries({ queryKey: ["workspaces", token, orgId] });
      setSelectedWorkspaceId(created.id);
      setNewName("");
      closeCreate();
    },
  });

  if (!token) {
    return null;
  }

  if (orgId == null) {
    return (
      <Text size="xs" c="dimmed" lineClamp={2}>
        Select an organization to use workspaces.
      </Text>
    );
  }

  if (isPending) {
    return (
      <Group gap="xs" wrap="nowrap">
        <Loader size="xs" />
      </Group>
    );
  }

  if (isError) {
    return (
      <Text size="xs" c="dimmed" lineClamp={2}>
        Workspaces unavailable
      </Text>
    );
  }

  const selectData =
    workspaces?.map((w) => ({
      value: String(w.id),
      label: w.name,
    })) ?? [];

  function submitCreate() {
    const name = newName.trim();
    if (!name) return;
    createMutation.mutate(name);
  }

  return (
    <>
      <Stack gap="xs">
        {selectData.length > 0 ? (
          <Group gap="xs" wrap="nowrap" align="flex-start">
            <Select
              size="xs"
              flex={1}
              miw={0}
              aria-label="Active workspace"
              placeholder="Workspace"
              data={selectData}
              value={selectedWorkspaceId != null ? String(selectedWorkspaceId) : null}
              onChange={(v) => {
                if (v == null) return;
                setSelectedWorkspaceId(Number(v));
              }}
              allowDeselect={false}
              clearable={false}
              comboboxProps={{ withinPortal: true, zIndex: 400 }}
              {...highlightedSelectOptionProps}
            />
            <Button size="xs" variant="default" onClick={openCreate}>
              New
            </Button>
          </Group>
        ) : (
          <Button size="xs" variant="light" fullWidth onClick={openCreate}>
            Create workspace
          </Button>
        )}
      </Stack>

      <Modal opened={createOpened} onClose={closeCreate} title="New workspace" centered>
        <Stack gap="sm">
          <TextInput
            label="Name"
            placeholder="e.g. Marketing"
            value={newName}
            onChange={(e) => setNewName(e.currentTarget.value)}
            data-autofocus
          />
          {createMutation.isError ? (
            <Text size="sm" c="red">
              {createMutation.error instanceof Error ? createMutation.error.message : "Something went wrong."}
            </Text>
          ) : null}
          <Group justify="flex-end" gap="xs">
            <Button variant="default" onClick={closeCreate}>
              Cancel
            </Button>
            <Button loading={createMutation.isPending} onClick={submitCreate}>
              Create
            </Button>
          </Group>
        </Stack>
      </Modal>
    </>
  );
}
