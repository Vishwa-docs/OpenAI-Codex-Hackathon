"use client";

import { AppErrorState } from "@/components/app-error-state";

export default function AppGroupError({
  error,
  reset
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return <AppErrorState error={error} reset={reset} />;
}
