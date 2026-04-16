import { MarketingShell } from "@/components/marketing-shell";
import type { ReactNode } from "react";

export default function MarketingLayout({ children }: { children: ReactNode }) {
  return <MarketingShell>{children}</MarketingShell>;
}
