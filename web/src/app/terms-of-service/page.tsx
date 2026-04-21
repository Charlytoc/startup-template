import type { Metadata } from "next";
import { LegalDocPage } from "@/components/LegalDocPage";
import { Stack, Text, Title } from "@mantine/core";

export const metadata: Metadata = {
  title: "Terms of Service | Coworkers AI",
  description: "Terms governing your use of Coworkers AI.",
};

export default function TermsOfServicePage() {
  return (
    <LegalDocPage title="Terms of Service" lastUpdated="April 20, 2026">
      <Stack gap="lg">
        <Stack gap="sm">
          <Title order={3}>Agreement</Title>
          <Text c="dimmed">
            By accessing or using Coworkers AI (the “Services”), you agree to these Terms. If you are using
            the Services on behalf of an organization, you represent that you have authority to bind that
            organization.
          </Text>
        </Stack>

        <Stack gap="sm">
          <Title order={3}>Accounts and access</Title>
          <Text c="dimmed">
            You are responsible for safeguarding credentials and for activity under your account. You must
            provide accurate information and comply with applicable laws.
          </Text>
        </Stack>

        <Stack gap="sm">
          <Title order={3}>Acceptable use</Title>
          <Text c="dimmed">You agree not to:</Text>
          <Stack component="ol" gap="xs" c="dimmed" pl="md" my={0}>
            <Text component="li" c="dimmed">
              Use the Services to violate law or third-party rights, or to send spam or malware.
            </Text>
            <Text component="li" c="dimmed">
              Attempt to probe, scan, or test the vulnerability of the Services without authorization.
            </Text>
            <Text component="li" c="dimmed">
              Reverse engineer or circumvent security or rate limits, except where prohibited law applies.
            </Text>
          </Stack>
        </Stack>

        <Stack gap="sm">
          <Title order={3}>Third-party services</Title>
          <Text c="dimmed">
            Integrations may be subject to separate provider terms. We are not responsible for third-party
            services you choose to connect.
          </Text>
        </Stack>

        <Stack gap="sm">
          <Title order={3}>Disclaimers</Title>
          <Text c="dimmed">
            The Services are provided “as is” to the fullest extent permitted by law. We disclaim warranties
            not expressly stated here.
          </Text>
        </Stack>

        <Stack gap="sm">
          <Title order={3}>Limitation of liability</Title>
          <Text c="dimmed">
            To the maximum extent permitted by law, we will not be liable for indirect, incidental, special,
            consequential, or punitive damages, or for loss of profits or data, arising from your use of the
            Services.
          </Text>
        </Stack>

        <Stack gap="sm">
          <Title order={3}>Termination</Title>
          <Text c="dimmed">
            We may suspend or terminate access for violations of these Terms or to protect the Services. You
            may stop using the Services at any time.
          </Text>
        </Stack>

        <Stack gap="sm">
          <Title order={3}>Changes</Title>
          <Text c="dimmed">
            We may modify these Terms by posting an updated version. Continued use after changes become
            effective constitutes acceptance of the revised Terms.
          </Text>
        </Stack>

        <Stack gap="sm">
          <Title order={3}>Contact</Title>
          <Text c="dimmed">
            For questions about these Terms, use the contact method provided by your organization or replace
            this with your company legal contact.
          </Text>
        </Stack>
      </Stack>
    </LegalDocPage>
  );
}
