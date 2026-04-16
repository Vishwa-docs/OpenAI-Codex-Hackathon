import { cache } from "react";
import { BackendUnavailableError } from "@/lib/app-errors";
import { buildProjectDatasetFromApi } from "@/lib/project-dataset";
import type {
  ApprovalRecord,
  AgentRun,
  AssessmentRun,
  AuditEvent,
  ChatMessage,
  CloudConnection,
  CostRoiSummary,
  DashboardSummary,
  DependencyGraph,
  EvalRun,
  Finding,
  FactoryProposal,
  ProjectOverview,
  ProviderOption,
  RegistryEntry,
  Report,
  ReportArtifact,
  RiskComplianceSummary,
  ScenarioDiff,
  SourceConnection,
  ProjectCreate,
  Scenario
} from "@contracts/index";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";
export const DEFAULT_WORKSPACE_ID =
  process.env.NEXT_PUBLIC_DEFAULT_WORKSPACE_ID ?? "workspace-demo";

async function fetchJson<T>(path: string, timeoutMs = 1800, init?: RequestInit): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(`${API_BASE}${path}`, {
      cache: "no-store",
      signal: controller.signal,
      ...init,
    });

    if (!response.ok) {
      throw new BackendUnavailableError(path, `Backend unavailable for ${path} (${response.status})`);
    }

    return (await response.json()) as T;
  } catch (error) {
    if (error instanceof BackendUnavailableError) {
      throw error;
    }

    throw new BackendUnavailableError(path, `Backend unavailable for ${path}`);
  } finally {
    clearTimeout(timer);
  }
}

export const loadDashboardSummary = cache(async (): Promise<DashboardSummary> => fetchJson<DashboardSummary>("/dashboard/summary"));
export const loadWorkspaceContext = cache(async (workspaceId: string) =>
  fetchJson<import("@contracts/index").WorkspaceContext>(`/workspaces/${workspaceId}/context`)
);

export const loadWorkspaceProjects = cache(async (workspaceId: string) =>
  fetchJson<import("@contracts/index").ProjectOverview[]>(`/workspaces/${workspaceId}/projects`)
);

export const loadProjectDataset = cache(async (projectId: string) => {
  const [
    dashboard,
    overview,
    assessment,
    assessmentRuns,
    agentRuns,
    evalRuns,
    graph,
    findings,
    providers,
    costRoi,
    riskCompliance,
    scenarios,
    scenarioDiffs,
    reports,
    artifacts,
    approvals,
    auditEvents,
    registryEntries,
    sourceConnections,
    cloudConnections,
    factoryProposals,
    chatMessages
  ] = await Promise.all([
    loadDashboardSummary(),
    fetchJson<ProjectOverview>(`/projects/${projectId}/overview`),
    fetchJson<AssessmentRun>(`/projects/${projectId}/assessment`),
    fetchJson<AssessmentRun[]>(`/projects/${projectId}/assessment-runs`),
    fetchJson<AgentRun[]>(`/projects/${projectId}/agent-runs`),
    fetchJson<EvalRun[]>(`/projects/${projectId}/eval-runs`),
    fetchJson<DependencyGraph>(`/projects/${projectId}/dependency-graph`),
    fetchJson<Finding[]>(`/projects/${projectId}/findings`),
    fetchJson<ProviderOption[]>(`/projects/${projectId}/provider-comparison`),
    fetchJson<CostRoiSummary>(`/projects/${projectId}/cost-roi`),
    fetchJson<RiskComplianceSummary>(`/projects/${projectId}/risk-compliance`),
    fetchJson<Scenario[]>(`/projects/${projectId}/scenarios`),
    fetchJson<ScenarioDiff[]>(`/projects/${projectId}/scenario-diffs`),
    fetchJson<Report[]>(`/projects/${projectId}/reports`),
    fetchJson<ReportArtifact[]>(`/projects/${projectId}/artifacts`),
    fetchJson<ApprovalRecord[]>(`/projects/${projectId}/approvals`),
    fetchJson<AuditEvent[]>(`/projects/${projectId}/audit-events`),
    fetchJson<RegistryEntry[]>(`/projects/${projectId}/registry-entries`),
    fetchJson<SourceConnection[]>(`/projects/${projectId}/source-connections`),
    fetchJson<CloudConnection[]>(`/projects/${projectId}/cloud-connections`),
    fetchJson<FactoryProposal[]>(`/projects/${projectId}/factory-proposals`),
    fetchJson<ChatMessage[]>(`/projects/${projectId}/chat/messages`)
  ]);

  return buildProjectDatasetFromApi({
    projectId,
    dashboard,
    overview,
    assessment,
    assessmentRuns,
    agentRuns,
    evalRuns,
    graph,
    findings,
    providers,
    costRoi,
    riskCompliance,
    scenarios,
    scenarioDiffs,
    reports,
    artifacts,
    approvals,
    auditEvents,
    registryEntries,
    sourceConnections,
    cloudConnections,
    factoryProposals,
    chatMessages
  });
});

export function getReportExportHref(projectId: string, reportId: string, format: "pdf" | "markdown" | "json") {
  return `${API_BASE}/projects/${projectId}/reports/${reportId}/export?format=${format}`;
}

export async function createWorkspaceProject(workspaceId: string, draft: ProjectCreate) {
  return fetchJson<import("@contracts/index").ProjectOverview>(`/workspaces/${workspaceId}/projects`, 5000, {
    method: "POST",
    headers: {
      "content-type": "application/json",
    },
    body: JSON.stringify(draft),
  });
}

export { BackendUnavailableError };
