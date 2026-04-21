"use client";

import { useCallback, useMemo, useState } from "react";
import {
  Badge,
  Button,
  Group,
  Modal,
  MultiSelect,
  Paper,
  Select,
  Stack,
  Text,
} from "@mantine/core";
import { useDisclosure } from "@mantine/hooks";
import type { WorkspaceIntegrationItem } from "@/lib/workspace-integrations";
import {
  actionKey,
  groupSelectionByIntegration,
  integrationActionOptionsForAccount,
  keyToAction,
  mergeIntegrationGroup,
  PROVIDER_INBOUND_EVENTS,
  removeIntegrationGroup,
  systemActionOptions,
  type ActionableCatalogRow,
} from "@/lib/workspace-job-assignments";

type Props = {
  actionables: ActionableCatalogRow[];
  integrations: WorkspaceIntegrationItem[];
  actionKeys: string[];
  integrationEventSlugs: string[];
  onActionKeysChange: (keys: string[]) => void;
  onIntegrationEventSlugsChange: (slugs: string[]) => void;
};

type ModalDraft = {
  accountId: string;
  triggerSlugs: string[];
  actionKeysForAccount: string[];
};

const EMPTY_DRAFT: ModalDraft = {
  accountId: "",
  triggerSlugs: [],
  actionKeysForAccount: [],
};

export function IntegrationActionsTriggersEditor({
  actionables,
  integrations,
  actionKeys,
  integrationEventSlugs,
  onActionKeysChange,
  onIntegrationEventSlugsChange,
}: Props) {
  const [opened, { open, close }] = useDisclosure(false);
  const [modalMode, setModalMode] = useState<"add" | "edit">("add");
  const [step, setStep] = useState(0);
  const [draft, setDraft] = useState<ModalDraft>(EMPTY_DRAFT);

  const { attached, systemActionKeys } = useMemo(
    () => groupSelectionByIntegration(actionKeys, integrationEventSlugs, integrations),
    [actionKeys, integrationEventSlugs, integrations],
  );

  const attachedIds = useMemo(() => new Set(attached.map((a) => a.integration_account_id)), [attached]);

  const availableToAttach = useMemo(
    () => integrations.filter((i) => !attachedIds.has(i.id)),
    [integrations, attachedIds],
  );

  const openAdd = useCallback(() => {
    setModalMode("add");
    setStep(0);
    setDraft(EMPTY_DRAFT);
    open();
  }, [open]);

  const openEdit = useCallback(
    (integrationAccountId: string) => {
      const g = attached.find((x) => x.integration_account_id === integrationAccountId);
      if (!g) return;
      setModalMode("edit");
      setStep(1);
      setDraft({
        accountId: integrationAccountId,
        triggerSlugs: [...g.eventSlugs],
        actionKeysForAccount: [...g.actionKeys],
      });
      open();
    },
    [attached, open],
  );

  const closeModal = useCallback(() => {
    close();
    setDraft(EMPTY_DRAFT);
    setStep(0);
  }, [close]);

  const selectedIntegration = useMemo(
    () => integrations.find((i) => i.id === draft.accountId) ?? null,
    [integrations, draft.accountId],
  );

  const provider = (selectedIntegration?.provider ?? "").toLowerCase();
  const triggerOptions =
    provider === "telegram" || provider === "instagram"
      ? [...PROVIDER_INBOUND_EVENTS[provider]]
      : [];

  const actionOptionsForDraft = useMemo(
    () => integrationActionOptionsForAccount(actionables, draft.accountId),
    [actionables, draft.accountId],
  );

  const attachSelectData = useMemo(
    () =>
      availableToAttach.map((i) => ({
        value: i.id,
        label: `${i.display_name} (${i.provider})`,
      })),
    [availableToAttach],
  );

  const confirmModal = useCallback(() => {
    if (!draft.accountId) return;
    const { actionKeys: nextKeys, eventSlugs: nextSlugs } = mergeIntegrationGroup(
      actionKeys,
      integrationEventSlugs,
      draft.accountId,
      draft.actionKeysForAccount,
      draft.triggerSlugs,
      integrations,
    );
    onActionKeysChange(nextKeys);
    onIntegrationEventSlugsChange(nextSlugs);
    closeModal();
  }, [
    actionKeys,
    integrationEventSlugs,
    draft,
    integrations,
    onActionKeysChange,
    onIntegrationEventSlugsChange,
    closeModal,
  ]);

  const removeCard = useCallback(
    (integrationAccountId: string) => {
      const { actionKeys: k, eventSlugs: s } = removeIntegrationGroup(
        actionKeys,
        integrationEventSlugs,
        integrationAccountId,
      );
      onActionKeysChange(k);
      onIntegrationEventSlugsChange(s);
    },
    [actionKeys, integrationEventSlugs, onActionKeysChange, onIntegrationEventSlugsChange],
  );

  const onSystemToolsChange = useCallback(
    (nextSystemKeys: string[]) => {
      const integrationKeys = actionKeys.filter((k) => keyToAction(k).integration_account_id != null);
      onActionKeysChange([...integrationKeys, ...nextSystemKeys]);
    },
    [actionKeys, onActionKeysChange],
  );

  const sysOptions = useMemo(() => systemActionOptions(actionables), [actionables]);

  const canGoNextFromStep0 = draft.accountId.length > 0;
  const canGoNextFromStep1 = draft.accountId.length > 0;
  const canConfirm = draft.actionKeysForAccount.length > 0;
  const minStep = modalMode === "add" ? 0 : 1;

  return (
    <Stack gap="md">
      <div>
        <Text size="sm" fw={600} mb={4}>
          Connected integrations
        </Text>
        <Text size="xs" c="dimmed" mb="sm">
          Configure triggers and actions per account. Use &quot;Attach integration&quot; to add another
          workspace account this job may use.
        </Text>
        <Stack gap="sm">
          {attached.map((g) => (
            <Paper key={g.integration_account_id} withBorder radius="md" p="md">
              <Group justify="space-between" align="flex-start" wrap="nowrap" mb="xs">
                <Group gap="xs">
                  <Badge variant="light">{g.provider}</Badge>
                  <Text fw={500}>{g.display_name}</Text>
                </Group>
                <Group gap="xs">
                  <Button size="xs" variant="light" onClick={() => openEdit(g.integration_account_id)}>
                    Edit
                  </Button>
                  <Button size="xs" variant="subtle" color="red" onClick={() => removeCard(g.integration_account_id)}>
                    Remove
                  </Button>
                </Group>
              </Group>
              <Text size="xs" c="dimmed" mb={4}>
                Triggers
              </Text>
              <Group gap={6} mb="sm">
                {g.eventSlugs.length ? (
                  g.eventSlugs.map((s) => (
                    <Badge key={s} size="sm" variant="outline">
                      {s}
                    </Badge>
                  ))
                ) : (
                  <Text size="xs" c="dimmed">
                    None (tools-only for this account)
                  </Text>
                )}
              </Group>
              <Text size="xs" c="dimmed" mb={4}>
                Actions
              </Text>
              <Group gap={6}>
                {g.actionKeys.map((k) => {
                  const row = actionables.find((a) => actionKey(a) === k);
                  return (
                    <Badge key={k} size="sm" variant="light">
                      {row?.name ?? k}
                    </Badge>
                  );
                })}
              </Group>
            </Paper>
          ))}
          <Button
            variant="default"
            style={{ borderStyle: "dashed" }}
            disabled={availableToAttach.length === 0}
            onClick={openAdd}
          >
            Attach integration
          </Button>
        </Stack>
      </div>

      <div>
        <Text size="sm" fw={600} mb={4}>
          System tools
        </Text>
        <Text size="xs" c="dimmed" mb="sm">
          Scheduling and web chat tools are not tied to a specific integration account.
        </Text>
        <MultiSelect
          placeholder="Optional system capabilities"
          data={sysOptions}
          value={systemActionKeys}
          onChange={onSystemToolsChange}
          searchable
        />
      </div>

      <Modal
        opened={opened}
        onClose={closeModal}
        title={modalMode === "add" ? "Attach integration" : "Edit integration"}
        centered
        size="md"
      >
        <Stack gap="md">
          {modalMode === "add" && step === 0 ? (
            <>
              <Text size="sm" c="dimmed">
                The AI will receive events from this account (when you add triggers) and may call actions
                you grant on this account.
              </Text>
              <Select
                label="Integration"
                placeholder="Choose a workspace account"
                data={attachSelectData}
                value={draft.accountId || null}
                onChange={(v) => setDraft((d) => ({ ...d, accountId: v ?? "" }))}
                searchable
              />
            </>
          ) : null}

          {step === 1 ? (
            <>
              <Text size="sm" c="dimmed">
                A trigger starts this job when the event fires; the agent then runs with the job&apos;s
                instructions and tools.
              </Text>
              <MultiSelect
                label="Inbound triggers for this account"
                description={`Provider: ${provider || "—"}`}
                data={triggerOptions}
                value={draft.triggerSlugs}
                onChange={(v) => setDraft((d) => ({ ...d, triggerSlugs: v }))}
                searchable
              />
            </>
          ) : null}

          {step === 2 ? (
            <>
              <Text size="sm" c="dimmed">
                Pick what this job may do on this account (e.g. send a DM). More capabilities appear here as
                the catalog grows.
              </Text>
              <MultiSelect
                label="Actions on this account"
                data={actionOptionsForDraft}
                value={draft.actionKeysForAccount}
                onChange={(v) => setDraft((d) => ({ ...d, actionKeysForAccount: v }))}
                searchable
              />
            </>
          ) : null}

          <Group justify="space-between">
            <Button variant="default" onClick={closeModal}>
              Cancel
            </Button>
            <Group gap="xs">
              {step > minStep ? (
                <Button variant="default" onClick={() => setStep((s) => s - 1)}>
                  Back
                </Button>
              ) : null}
              {modalMode === "add" && step === 0 ? (
                <Button disabled={!canGoNextFromStep0} onClick={() => setStep(1)}>
                  Next
                </Button>
              ) : null}
              {step === 1 ? (
                <Button onClick={() => setStep(2)} disabled={!canGoNextFromStep1}>
                  Next
                </Button>
              ) : null}
              {step === 2 ? (
                <Button onClick={confirmModal} disabled={!canConfirm}>
                  Save
                </Button>
              ) : null}
            </Group>
          </Group>
        </Stack>
      </Modal>
    </Stack>
  );
}
