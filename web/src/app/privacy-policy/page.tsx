import type { Metadata } from "next";
import { LegalDocPage } from "@/components/LegalDocPage";
import { Stack, Text, Title } from "@mantine/core";

export const metadata: Metadata = {
  title: "Privacy Policy | Coworkers AI",
  description: "How Coworkers AI collects, uses, and protects your information.",
};

export default function PrivacyPolicyPage() {
  return (
    <LegalDocPage title="Privacy Policy" lastUpdated="April 20, 2026">
      <Stack gap="lg">
        <Stack gap="sm">
          <Title order={3}>Who we are</Title>
          <Text c="dimmed">
            This policy describes how Coworkers AI (“we”, “us”) handles personal information when you use
            our website, applications, and related services (the “Services”).
          </Text>
        </Stack>

        <Stack gap="sm">
          <Title order={3}>Information we collect</Title>
          <Text c="dimmed">We may collect:</Text>
          <Stack component="ol" gap="xs" c="dimmed" pl="md" my={0}>
            <Text component="li" c="dimmed">
              Account and profile data you provide (for example name, email, organization details).
            </Text>
            <Text component="li" c="dimmed">
              Content you submit through the Services (messages, files, integrations you configure).
            </Text>
            <Text component="li" c="dimmed">
              Technical data such as device type, browser, IP address, and logs used for security and
              reliability.
            </Text>
          </Stack>
        </Stack>

        <Stack gap="sm">
          <Title order={3}>How we use information</Title>
          <Text c="dimmed">We use information to provide and improve the Services, authenticate users, prevent abuse, comply with law, and communicate with you about the product.</Text>
        </Stack>

        <Stack gap="sm">
          <Title order={3}>Third parties and integrations</Title>
          <Text c="dimmed">
            If you connect third-party accounts (for example social or messaging platforms), we process data
            according to your configuration and those providers’ terms. We do not sell your personal
            information.
          </Text>
        </Stack>

        <Stack gap="sm">
          <Title order={3}>Retention and security</Title>
          <Text c="dimmed">
            We retain data as long as needed to operate the Services and meet legal obligations. We use
            industry-standard safeguards; no method of transmission over the internet is completely secure.
          </Text>
        </Stack>

        <Stack gap="sm">
          <Title order={3}>Your rights</Title>
          <Text c="dimmed">
            Depending on where you live, you may have rights to access, correct, delete, or export your
            data, or to object to certain processing. Contact us to exercise these rights where applicable.
          </Text>
        </Stack>

        <Stack gap="sm">
          <Title order={3}>Changes</Title>
          <Text c="dimmed">
            We may update this policy from time to time. We will post the revised version here and update
            the “Last updated” date.
          </Text>
        </Stack>

        <Stack gap="sm">
          <Title order={3}>Contact</Title>
          <Text c="dimmed">
            For privacy questions, contact your organization administrator or the email address provided in
            your Coworkers AI workspace settings (replace this sentence with your legal contact when ready).
          </Text>
        </Stack>
      </Stack>
    </LegalDocPage>
  );
}
