import type { AuthSession } from "@/lib/auth-shared";

export const APP_MODE = process.env.NEXT_PUBLIC_APP_MODE ?? process.env.APP_MODE ?? "demo";

export function isJudgeMode() {
  return APP_MODE === "judge";
}

export function getDefaultWorkspaceId() {
  return process.env.NEXT_PUBLIC_DEFAULT_WORKSPACE_ID ?? (isJudgeMode() ? "workspace-judge" : "workspace-demo");
}

export function getDesktopDownloadUrl() {
  return process.env.NEXT_PUBLIC_DESKTOP_DOWNLOAD_URL ?? "/downloads/cloud-migration-cockpit-judge-macos.zip";
}

export function getJudgeSession(): AuthSession {
  return {
    user: {
      id: "judge-local-session",
      email: "judge@localhost",
      name: "Judge Workspace",
    },
    createdAt: new Date().toISOString(),
    activeOrganizationId: isJudgeMode() ? "org-judge" : "org-demo",
  };
}
