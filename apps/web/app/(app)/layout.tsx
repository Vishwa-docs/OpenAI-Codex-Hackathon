import { getServerSession } from "@/lib/auth";
import { CockpitShell } from "@/components/cockpit-shell";
import { redirect } from "next/navigation";
import type { ReactNode } from "react";

export const dynamic = "force-dynamic";

export default async function AppLayout({ children }: { children: ReactNode }) {
  const session = await getServerSession();

  if (!session) {
    redirect("/sign-in");
  }

  return <CockpitShell session={session}>{children}</CockpitShell>;
}
