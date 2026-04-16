import { cache } from "react";
import { BackendUnavailableError } from "@/lib/app-errors";
import { buildProjectDatasetFromApi } from "@/lib/project-dataset";
import { getDefaultWorkspaceId } from "@/lib/runtime";
import type {
  ApprovalRecord,
  AgentRun,
  AnalysisQuestion,
  AssessmentRun,
  AuditEvent,
  ChatMessage,
  CloudConnection,
  CostRoiSummary,
  DashboardSummary,
  DeploymentPlan,
  DependencyGraph,
  EvalRun,
  Finding,
  FactoryProposal,
  IntakeProfile,
  ObservabilityTrace,
  ProjectOverview,
  ProviderOption,
  PreviewDeploymentStatus,
  ProjectCreate,
  RegistryEntry,
  Report,
  ReportArtifact,
  RiskComplianceSummary,
  ScenarioDiff,
  SourceConnection,
  Scenario
} from "@contracts/index";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";
export const DEFAULT_WORKSPACE_ID = getDefaultWorkspaceId();

export interface RuntimeHealth {
  status: string;
  service: string;
  version: string;
  appMode: string;
  defaultWorkspaceId: string;
  desktopDownloadUrl: string;
  desktopAvailable: boolean;
  checkedAt: string;
}

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

export const loadRuntimeHealth = cache(async () => fetchJson<RuntimeHealth>("/health"));

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
    chatMessages,
    intake,
    observability,
    deploymentPlan,
    analysisQuestions,
    previewStatus
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
    fetchJson<ChatMessage[]>(`/projects/${projectId}/chat/messages`),
    fetchJson<IntakeProfile>(`/projects/${projectId}/intake`),
    fetchJson<ObservabilityTrace[]>(`/projects/${projectId}/observability-traces`),
    fetchJson<DeploymentPlan>(`/projects/${projectId}/deployment-plan`),
    fetchJson<AnalysisQuestion[]>(`/projects/${projectId}/analysis-questions`),
    fetchJson<PreviewDeploymentStatus>(`/projects/${projectId}/preview-status`)
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
    chatMessages,
    intake,
    mtcPipeline: assessment.pipelineSummaries,
    observability,
    deploymentPlan,
    analysisQuestions,
    previewStatus
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

export async function answerAnalysisQuestion(
  projectId: string,
  questionId: string,
  answer: { actor: string; answer: string }
) {
  return fetchJson<AnalysisQuestion>(`/projects/${projectId}/analysis-questions/${questionId}/answer`, 5000, {
    method: "POST",
    headers: {
      "content-type": "application/json",
    },
    body: JSON.stringify(answer),
  });
}

export async function decideApproval(
  projectId: string,
  approvalId: string,
  decision: { decision: "approved" | "rejected"; actor: string; comment: string }
) {
  return fetchJson<ApprovalRecord>(`/projects/${projectId}/approvals/${approvalId}/decision`, 5000, {
    method: "POST",
    headers: {
      "content-type": "application/json",
    },
    body: JSON.stringify(decision),
  });
}

export async function launchLocalPreview(projectId: string, request: { triggeredBy: string }) {
  return fetchJson<PreviewDeploymentStatus>(`/projects/${projectId}/preview-status/launch`, 45000, {
    method: "POST",
    headers: {
      "content-type": "application/json",
    },
    body: JSON.stringify(request),
  });
}

export { BackendUnavailableError };
