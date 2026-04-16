export type Severity = "critical" | "high" | "medium" | "low";
export type ApprovalState = "not_required" | "pending" | "approved" | "rejected";
export type RunStatus = "queued" | "running" | "succeeded" | "failed";
export type ConnectionStatus = "connected" | "needs_attention" | "proposed" | "disabled";
export type PipelineStatus = "queued" | "running" | "blocked" | "succeeded" | "failed";
export type ReportKind =
  | "executive_summary"
  | "technical_dossier"
  | "cost_report"
  | "risk_report"
  | "architecture_recommendation"
  | "migration_wave_plan"
  | "cutover_rollback"
  | "operations_checklist"
  | "terraform"
  | "diagram";

export interface EvidenceReference {
  id: string;
  sourceType: "file" | "log" | "manifest" | "command_output";
  sourceUri: string;
  excerpt: string;
  locator?: {
    lineStart?: number;
    lineEnd?: number;
  };
  confidence: number;
}

export interface CredentialRef {
  id: string;
  kind: "token" | "oauth" | "assumed_role" | "access_key" | "none";
  label: string;
  redactedValue: string;
  expiresAt?: string;
}

export interface Finding {
  id: string;
  title: string;
  category: string;
  severity: Severity;
  confidence: number;
  summary: string;
  recommendation: string;
  evidence: EvidenceReference[];
}

export interface Recommendation {
  id: string;
  title: string;
  summary: string;
  confidence: number;
  rationale: string;
  effort: "small" | "medium" | "large";
  impact: "high" | "medium" | "low";
  evidence?: EvidenceReference[];
}

export interface DependencyNode {
  id: string;
  label: string;
  kind: "service" | "job" | "database" | "storage" | "external_api" | "pipeline";
  environment: "legacy" | "target";
  status: "observed" | "at_risk" | "planned";
  x: number;
  y: number;
}

export interface DependencyEdge {
  id: string;
  source: string;
  target: string;
  relation:
    | "depends_on"
    | "calls"
    | "writes_to"
    | "reads_from"
    | "deployed_via"
    | "schedules";
}

export interface DependencyGraph {
  nodes: DependencyNode[];
  edges: DependencyEdge[];
  generatedAt: string;
  summary: string;
}

export interface ScenarioOutcome {
  readiness: number;
  riskDelta: string;
  costDelta: string;
  summary: string;
}

export interface Scenario {
  id: string;
  name: string;
  description: string;
  assumptionSet: string[];
  outcome: ScenarioOutcome;
}

export interface ProviderOption {
  id: "aws" | "gcp" | "azure";
  name: string;
  score: number;
  bestFor: string;
  tradeoffs: string[];
  rationale?: string;
  confidence?: number;
  evidence?: EvidenceReference[];
}

export interface ReportArtifact {
  id: string;
  kind: ReportKind;
  title: string;
  format: "json" | "markdown" | "pdf" | "mermaid" | "hcl";
  description: string;
  updatedAt: string;
}

export interface ReportSection {
  title: string;
  body: string;
  citations?: EvidenceReference[];
}

export interface Report {
  id: string;
  kind: ReportKind;
  title: string;
  summary: string;
  confidence: number;
  sections: ReportSection[];
  generatedAt: string;
  artifactIds: string[];
}

export interface SourceConnection {
  id: string;
  kind: "local_directory" | "github" | "azure_repos";
  name: string;
  status: ConnectionStatus;
  mode: "read_only" | "discovery" | "approval_gated";
  target: string;
  branch?: string;
  lastSyncAt?: string;
  credentialRef: CredentialRef;
  notes: string[];
}

export interface CloudConnection {
  id: string;
  provider: "aws" | "gcp" | "azure";
  name: string;
  status: ConnectionStatus;
  mode: "discovery" | "dry_run" | "approval_gated";
  accountLabel: string;
  regionScope: string[];
  credentialRef: CredentialRef;
  notes: string[];
}

export interface PipelineSummary {
  pipelineKey:
    | "intake_clarification"
    | "codebase_discovery"
    | "architecture_analysis"
    | "security_readiness"
    | "hosting_fit_recommendation"
    | "migration_strategy"
    | "infra_plan_generation"
    | "evaluation_critique"
    | "deployment_readiness"
    | "aws_execution"
    | "post_deploy_validation";
  title: string;
  status: PipelineStatus;
  summary: string;
  plainLanguageSummary?: string;
  startedAt?: string;
  completedAt?: string;
}

export interface ApprovalRecord {
  id: string;
  phase: string;
  state: ApprovalState;
  requestedBy: string;
  approver?: string;
  comment?: string;
  decidedAt?: string;
}

export interface ApprovalDecision {
  decision: Extract<ApprovalState, "approved" | "rejected">;
  actor: string;
  comment: string;
}

export interface AuditEvent {
  id: string;
  actor: string;
  action: string;
  entityType: string;
  entityId: string;
  createdAt: string;
  metadata?: Record<string, string>;
}

export interface RegistryEntry {
  id: string;
  name: string;
  kind: "agent" | "tool" | "connector";
  status: "enabled" | "disabled" | "proposed";
  requiredPermissions: string[];
  rationale: string;
  version?: string;
  proposedBy?: string;
  enabled?: boolean;
}

export interface FactoryProposal {
  id: string;
  name: string;
  kind: "agent" | "tool" | "connector";
  status: "proposed";
  rationale: string;
  requiredPermissions: string[];
  promptVersion: string;
  scaffoldFiles: string[];
  approvalRequired: boolean;
}

export interface ProjectOverview {
  id: string;
  name: string;
  clientName: string;
  readinessScore: number;
  migrationDecision: string;
  confidence: number;
  phase: string;
  status: string;
  recommendedProvider: string;
}

export interface DashboardSummary {
  activeProjects: number;
  pendingApprovals: number;
  openFindings: number;
  reportExports: number;
  topProjects: ProjectOverview[];
}

export interface RiskItem {
  id: string;
  severity: Severity;
  domain: string;
  title: string;
  impact: string;
  mitigation: string;
  confidence: number;
  evidence: EvidenceReference[];
}

export interface RiskComplianceSummary {
  overallRisk: "critical" | "high" | "moderate" | "low";
  complianceFrameworks: string[];
  dataResidency: string;
  operationalReadiness: string;
  risks: RiskItem[];
  summary: string;
  confidence: number;
}

export interface CostRoiSummary {
  annualBaselineCost: number;
  annualTargetCost: number;
  migrationInvestment: number;
  annualSavings: number;
  paybackMonths: number;
  roiPercent: number;
  summary: string;
  confidence: number;
  assumptions: string[];
  evidence: EvidenceReference[];
}

export interface AgentOutput {
  agentKey: string;
  displayName: string;
  status: RunStatus;
  confidence: number;
  summary: string;
  evidence: EvidenceReference[];
  structuredOutput: Record<string, unknown>;
  limitations?: string[];
}

export interface AgentRun {
  id: string;
  assessmentRunId: string;
  agentKey: string;
  displayName: string;
  stage:
    | "intake"
    | "discovery"
    | "analysis"
    | "planning"
    | "critique"
    | "reporting";
  status: RunStatus;
  critic: boolean;
  confidence: number;
  summary: string;
  evidenceCount: number;
  latencyMs: number;
  warningCount: number;
  retryCount: number;
  startedAt: string;
  completedAt?: string;
}

export interface EvalMetric {
  metricKey:
    | "citation_coverage"
    | "unsupported_claim_rate"
    | "recommendation_consistency"
    | "cost_sanity"
    | "latency"
    | "policy_compliance";
  label: string;
  score: number;
  summary: string;
  status: "pass" | "warn" | "fail";
}

export interface EvalRun {
  id: string;
  assessmentRunId: string;
  overallScore: number;
  status: RunStatus;
  completedAt: string;
  metrics: EvalMetric[];
}

export interface ChatMessage {
  id: string;
  role: "ai" | "human" | "system";
  author: string;
  createdAt: string;
  content: string;
}

export interface IntakeProfile {
  id: string;
  projectId: string;
  name: string;
  clientName: string;
  sourceKind: "local_directory" | "github" | "azure_repos";
  sourceTarget: string;
  expectedUsers: number;
  preferredCloud: "aws" | "gcp" | "azure";
  businessConstraints: string[];
  complianceNotes: string[];
  credentialLabel: string;
  credentialKind: "token" | "oauth" | "assumed_role" | "access_key" | "none";
  founderSummary: string;
}

export interface PlatformRecommendation {
  platformKey: "vercel" | "railway" | "aws-ec2" | "aws-ecs" | "aws-lambda" | "cloudflare-workers";
  label: string;
  fitScore: number;
  bestFor: string;
  rationale: string;
  plainLanguageRationale: string;
  tradeoffs: string[];
  monthlyCostEstimate: string;
  scalingThreshold: string;
  executionReady: boolean;
}

export interface DeploymentArtifact {
  id: string;
  kind: "terraform" | "ansible" | "checklist";
  title: string;
  summary: string;
  preview: string;
}

export interface DeploymentExecution {
  id: string;
  provider: "aws";
  mode: "dry_run" | "apply";
  status: RunStatus;
  triggeredBy: string;
  summary: string;
  createdAt: string;
  nextSteps: string[];
}

export interface DeploymentPlan {
  projectId: string;
  executionState: "blocked" | "ready" | "in_progress" | "succeeded";
  founderSummary: string;
  recommendedPlatform: PlatformRecommendation;
  platformOptions: PlatformRecommendation[];
  requiredActions: string[];
  artifacts: DeploymentArtifact[];
  lastExecution?: DeploymentExecution;
}

export interface ObservabilityTrace {
  id: string;
  stageKey: PipelineSummary["pipelineKey"];
  agentKey: string;
  title: string;
  status: RunStatus;
  summary: string;
  confidence: number;
  latencyMs: number;
  evidenceCount: number;
  warnings: string[];
  evaluationSummary: string;
  questionCheckpoint?: string;
}

export interface FinalRecommendation {
  decision: "migrate_now" | "migrate_partially" | "defer" | "rearchitect_first";
  label: string;
  confidence: number;
  summary: string;
  recommendedProvider: string;
  rationale: string[];
  blockers: string[];
  nextSteps: string[];
  evidence: EvidenceReference[];
}

export interface AssessmentRun {
  id: string;
  projectId: string;
  status: RunStatus;
  startedAt: string;
  completedAt: string;
  mode: "sync" | "local_worker";
  pipelineSummaries: PipelineSummary[];
  agentOutputs: AgentOutput[];
  finalRecommendation: FinalRecommendation;
}

export interface ScenarioDiff {
  baselineScenarioId: string;
  comparedScenarioId: string;
  readinessDelta: number;
  riskShift: string;
  costShift: string;
  summary: string;
}
