import { cache } from "react";
import {
  buildProjectDatasetFromApi,
  createMockDashboardSummary,
  createMockProjectDataset,
  type ProjectDataset
} from "@/lib/mock-data";
import type {
  ApprovalRecord,
  AgentRun,
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
  RegistryEntry,
  Report,
  ReportArtifact,
  RiskComplianceSummary,
  ScenarioDiff,
  SourceConnection,
  Scenario
} from "@contracts/index";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

async function fetchJson<T>(path: string, timeoutMs = 1800): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(`${API_BASE}${path}`, {
      cache: "no-store",
      signal: controller.signal
    });

    if (!response.ok) {
      throw new Error(`Request failed with ${response.status}`);
    }

    return (await response.json()) as T;
  } finally {
    clearTimeout(timer);
  }
}

export const loadDashboardSummary = cache(async (): Promise<DashboardSummary> => {
  try {
    return await fetchJson<DashboardSummary>("/dashboard/summary");
  } catch {
    return createMockDashboardSummary();
  }
});

export const loadProjectDataset = cache(async (projectId: string): Promise<ProjectDataset> => {
  try {
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
      deploymentPlan
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
      fetchJson<DeploymentPlan>(`/projects/${projectId}/deployment-plan`)
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
      deploymentPlan
    });
  } catch {
    return createMockProjectDataset(projectId);
  }
});

export function getReportExportHref(
  projectId: string,
  reportId: string,
  format: "pdf" | "markdown" | "json"
) {
  return `${API_BASE}/projects/${projectId}/reports/${reportId}/export?format=${format}`;
}
