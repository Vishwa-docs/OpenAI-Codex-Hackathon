import { CockpitShell } from "@/components/cockpit-shell";
import type { ReactNode } from "react";

export default function AppLayout({ children }: { children: ReactNode }) {
  return <CockpitShell>{children}</CockpitShell>;
}
