import { ChatPanel } from "@/components/chat-panel";
import { loadProjectDataset } from "@/lib/app-api";

export default async function ChatPage({
  params
}: {
  params: Promise<{ projectId: string }>;
}) {
  const { projectId } = await params;
  const project = await loadProjectDataset(projectId);

  return <ChatPanel messages={project.chat} projectName={project.projectName} projectId={projectId} />;
}
