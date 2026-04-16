"use client";

import { AppErrorState } from "@/components/app-error-state";

export default function ProjectError({
  error,
  reset
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return <AppErrorState error={error} reset={reset} title="This project cannot load right now." />;
}
