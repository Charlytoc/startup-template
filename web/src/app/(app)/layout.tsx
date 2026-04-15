import { AppShellLayout } from "@/components/AppShellLayout";

export default function AppGroupLayout({ children }: { children: React.ReactNode }) {
  return <AppShellLayout>{children}</AppShellLayout>;
}
