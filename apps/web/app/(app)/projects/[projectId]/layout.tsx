import { ProjectShell } from "@/components/project-shell";
import { loadProjectDataset } from "@/lib/app-api";
import type { ReactNode } from "react";

export default async function ProjectLayout({
  children,
  params
}: {
  children: ReactNode;
  params: Promise<{ projectId: string }>;
}) {
  const { projectId } = await params;
  const project = await loadProjectDataset(projectId);

  return (
    <>
      <ProjectShell
        projectId={project.projectId}
        projectName={project.projectName}
        clientName={project.clientName}
      />
      {children}
    </>
  );
}
