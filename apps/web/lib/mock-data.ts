import type {
  ApprovalRecord,
  AgentRun,
  AssessmentRun,
  AuditEvent,
  ChatMessage,
  CloudConnection,
  CostRoiSummary,
  DashboardSummary,
  DependencyEdge,
  DependencyGraph,
  DependencyNode,
  EvalRun,
  EvidenceReference,
  FactoryProposal,
  Finding,
  ProjectOverview,
  ProviderOption,
  Recommendation,
  RegistryEntry,
  Report,
  ReportArtifact,
  RiskComplianceSummary,
  ScenarioDiff,
  SourceConnection,
  Scenario
} from "@contracts/index";

export type { ChatMessage };

export interface ConnectorItem {
  id: string;
  name: string;
  kind: "source" | "cloud" | "observability" | "registry";
  status: "connected" | "needs_attention" | "needs_configuration" | "proposed" | "disabled";
  details: string;
  lastSyncAt?: string;
}

export interface EvalSummary {
  overallScore: number;
  checks: Array<{
    name: string;
    score: number;
    note: string;
  }>;
}

export interface ProjectDataset {
  projectId: string;
  projectName: string;
  clientName: string;
  dashboard: DashboardSummary;
  overview: {
    readinessScore: number;
    migrationDecision: string;
    confidence: number;
    phase: string;
    status: string;
    recommendedProvider: string;
    owner: string;
    lastScanAt: string;
    sourceSystem: string;
    targetSystem: string;
    businessSummary: string;
    narrative: string;
  };
  evidence: EvidenceReference[];
  findings: Finding[];
  recommendations: Recommendation[];
  providers: ProviderOption[];
  scenarios: Scenario[];
  dependencyNodes: DependencyNode[];
  dependencyEdges: DependencyEdge[];
  reports: Report[];
  artifacts: ReportArtifact[];
  approvals: ApprovalRecord[];
  auditEvents: AuditEvent[];
  chat: ChatMessage[];
  connectors: ConnectorItem[];
  sourceConnections: SourceConnection[];
  cloudConnections: CloudConnection[];
  assessmentRuns: AssessmentRun[];
  agentRuns: AgentRun[];
  evalRuns: EvalRun[];
  factoryProposals: FactoryProposal[];
  scenarioDiffs: ScenarioDiff[];
  evaluation: EvalSummary;
  reportHighlights: string[];
  exportFormats: string[];
  costModel: {
    currentMonthlyRunRate: number;
    targetMonthlyRunRate: number;
    migrationOneTimeCost: number;
    estimatedPaybackMonths: number;
    roiPercent: number;
    assumptions: string[];
    driverBreakdown: Array<{
      label: string;
      current: number;
      target: number;
    }>;
  };
  riskModel: {
    overallRisk: string;
    complianceNotes: string[];
    openIssues: string[];
    recommendedControls: string[];
    rpo: string;
    rto: string;
  };
  roadmap: {
    waves: Array<{
      name: string;
      description: string;
      duration: string;
      exitCriteria: string[];
    }>;
    cutover: string[];
    rollback: string[];
  };
}

const evidence: EvidenceReference[] = [
  {
    id: "ev-001",
    sourceType: "file",
    sourceUri: "demo-systems/legacycart/backend/src/main/resources/application-prod.yml",
    excerpt: "spring.datasource.password=supersecret123",
    locator: { lineStart: 8, lineEnd: 11 },
    confidence: 0.98
  },
  {
    id: "ev-002",
    sourceType: "log",
    sourceUri: "demo-systems/legacycart/data/sample-logs/app.log",
    excerpt: "user=jane.doe@example.com authHeader=Bearer eyJhbGciOi...",
    locator: { lineStart: 14, lineEnd: 16 },
    confidence: 0.95
  },
  {
    id: "ev-003",
    sourceType: "manifest",
    sourceUri: "demo-systems/legacycart/infra/jenkins/Jenkinsfile",
    excerpt: "withCredentials([string(credentialsId: 'legacy-aws-key' ...",
    locator: { lineStart: 19, lineEnd: 24 },
    confidence: 0.96
  },
  {
    id: "ev-004",
    sourceType: "file",
    sourceUri: "demo-systems/legacycart/jobs/invoice-export.py",
    excerpt: "upload_to_nfs('/mnt/shared/invoices')",
    locator: { lineStart: 42, lineEnd: 45 },
    confidence: 0.91
  }
];

const findings: Finding[] = [
  {
    id: "find-001",
    title: "Production database credentials are hardcoded",
    category: "secrets",
    severity: "critical",
    confidence: 0.98,
    summary: "The backend config contains a production password value that would be exposed during code transfer or build-time logging.",
    recommendation: "Move the database credential to a vault-backed secret store and rotate the exposed credential before any migration work.",
    evidence: [evidence[0]]
  },
  {
    id: "find-002",
    title: "Sensitive identity data is present in logs",
    category: "logging",
    severity: "high",
    confidence: 0.95,
    summary: "Sample logs show email addresses and authorization headers being written without redaction.",
    recommendation: "Redact auth headers and PII at the logging edge and add sink-side filters before enabling cloud observability.",
    evidence: [evidence[1]]
  },
  {
    id: "find-003",
    title: "Long-lived deployment credentials are embedded in CI",
    category: "ci_cd",
    severity: "high",
    confidence: 0.96,
    summary: "The Jenkins pipeline references a static cloud key rather than short-lived role assumption.",
    recommendation: "Replace the static credential with an assumed role or workload identity and gate writes behind approval.",
    evidence: [evidence[2]]
  },
  {
    id: "find-004",
    title: "Invoice exports depend on shared NFS storage",
    category: "storage",
    severity: "medium",
    confidence: 0.91,
    summary: "The batch export job writes customer invoices to a shared file mount that lacks object-level access control and lifecycle policy.",
    recommendation: "Move invoice artifacts to object storage with encryption, retention policies, and signed access.",
    evidence: [evidence[3]]
  }
];

const recommendations: Recommendation[] = [
  {
    id: "rec-001",
    title: "Re-architect first, then migrate",
    summary: "The system is viable to move, but only after secrets, logging, and job orchestration are remediated.",
    confidence: 0.9,
    rationale: "Critical security findings and brittle operational dependencies make a pure lift-and-shift risky. A small modernization wave reduces migration failure risk materially.",
    effort: "large",
    impact: "high"
  },
  {
    id: "rec-002",
    title: "Adopt AWS as the primary target",
    summary: "AWS offers the cleanest path for container migration, object storage, managed databases, and IAM controls for this workload.",
    confidence: 0.82,
    rationale: "The workload is operationally constrained but technically straightforward once the remediation blockers are removed.",
    effort: "medium",
    impact: "high"
  }
];

const providers: ProviderOption[] = [
  {
    id: "aws",
    name: "AWS",
    score: 91,
    bestFor: "IAM, managed databases, and a broad execution surface for cloud migration programs.",
    tradeoffs: ["Broad service surface needs tighter guardrails", "Requires upfront landing zone discipline"],
    confidence: 0.9,
    rationale: "AWS best matches the roadmap for IAM, managed database services, and future dry-run execution.",
    evidence
  },
  {
    id: "gcp",
    name: "Google Cloud",
    score: 79,
    bestFor: "Data-centric platforms with strong analytics and container primitives.",
    tradeoffs: ["Fewer migration-specific guardrails in this scenario", "Less aligned with the current operating model"],
    confidence: 0.82,
    rationale: "A credible modernization option, but less aligned with the AWS-first execution path.",
    evidence
  },
  {
    id: "azure",
    name: "Azure",
    score: 76,
    bestFor: "Microsoft-centric enterprises and identity-heavy rollouts.",
    tradeoffs: ["Current app stack and operations patterns do not benefit as much in this scenario", "Requires extra explanation to stakeholders"],
    confidence: 0.79,
    rationale: "Strong enterprise controls, but the workspace has AWS-first execution and limited Azure-specific connectors.",
    evidence
  }
];

const dependencyNodes: DependencyNode[] = [
  { id: "web", label: "Legacy web UI", kind: "service", environment: "legacy", status: "at_risk", x: 84, y: 110 },
  { id: "api", label: "Backend API", kind: "service", environment: "legacy", status: "at_risk", x: 250, y: 114 },
  { id: "db", label: "PostgreSQL 9.x", kind: "database", environment: "legacy", status: "at_risk", x: 424, y: 110 },
  { id: "files", label: "Shared NFS invoices", kind: "storage", environment: "legacy", status: "observed", x: 428, y: 232 },
  { id: "jobs", label: "Nightly jobs", kind: "job", environment: "legacy", status: "at_risk", x: 255, y: 240 },
  { id: "jenkins", label: "Jenkins pipeline", kind: "pipeline", environment: "legacy", status: "observed", x: 78, y: 244 },
  { id: "soap", label: "SOAP payment gateway", kind: "external_api", environment: "legacy", status: "observed", x: 596, y: 164 }
];

const dependencyEdges: DependencyEdge[] = [
  { id: "edge-1", source: "web", target: "api", relation: "depends_on" },
  { id: "edge-2", source: "api", target: "db", relation: "reads_from" },
  { id: "edge-3", source: "jobs", target: "db", relation: "writes_to" },
  { id: "edge-4", source: "jobs", target: "files", relation: "writes_to" },
  { id: "edge-5", source: "jenkins", target: "api", relation: "deployed_via" },
  { id: "edge-6", source: "api", target: "soap", relation: "calls" }
];

const scenarios: Scenario[] = [
  {
    id: "scenario-security-first",
    name: "Security first",
    description: "Remediate secrets, logging, and credential handling before migration.",
    assumptionSet: ["Rotate exposed secrets", "Externalize config", "Introduce vault-backed credentials"],
    outcome: {
      readiness: 69,
      riskDelta: "risk drops by 38% after blocker remediation",
      costDelta: "slight near-term cost increase, lower migration failure risk",
      summary: "Best for cautious stakeholder groups and regulated environments."
    }
  },
  {
    id: "scenario-lift-shift",
    name: "Lift and shift with guardrails",
    description: "Move the app quickly after the highest-severity blockers are closed.",
    assumptionSet: ["Containerize backend", "Move files to object storage", "Keep the current operating model"],
    outcome: {
      readiness: 58,
      riskDelta: "downtime risk remains moderate",
      costDelta: "migration effort falls, cloud run-rate stays higher",
      summary: "Fastest path to an early cloud landing but least future-proof."
    }
  },
  {
    id: "scenario-strangler",
    name: "Strangler modernization",
    description: "Carve out invoices, jobs, and the admin surface in phased waves.",
    assumptionSet: ["Split the jobs from the monolith", "Modernize the admin UI in slices", "Adopt managed services"],
    outcome: {
      readiness: 82,
      riskDelta: "operational risk decreases over time",
      costDelta: "best long-term ROI, highest coordination effort",
      summary: "Best match for a consultancy-led program with approvals."
    }
  }
];

const artifacts: ReportArtifact[] = [
  {
    id: "art-001",
    kind: "executive_summary",
    title: "Executive Summary PDF",
    format: "pdf",
    description: "A concise stakeholder-facing recommendation with confidence, risk, and cost framing.",
    updatedAt: "2026-04-16T06:12:00Z"
  },
  {
    id: "art-002",
    kind: "technical_dossier",
    title: "Technical migration dossier",
    format: "markdown",
    description: "Evidence-backed findings, dependency graph notes, and remediation guidance.",
    updatedAt: "2026-04-16T06:12:00Z"
  },
  {
    id: "art-003",
    kind: "cost_report",
    title: "Cost and ROI report",
    format: "json",
    description: "Current-state and target-state run-rate estimates with payback assumptions.",
    updatedAt: "2026-04-16T06:12:00Z"
  },
  {
    id: "art-004",
    kind: "diagram",
    title: "Target architecture diagram",
    format: "mermaid",
    description: "A cloud landing-zone concept with a phased migration path.",
    updatedAt: "2026-04-16T06:12:00Z"
  },
  {
    id: "art-005",
    kind: "terraform",
    title: "Terraform starter snippet",
    format: "hcl",
    description: "Seed scaffold for IAM, database, and storage modules.",
    updatedAt: "2026-04-16T06:12:00Z"
  }
];

const reports: Report[] = [
  {
    id: "report-executive",
    kind: "executive_summary",
    title: "Executive migration summary",
    summary: "Executive framing of readiness, ROI, risk posture, and next-step approvals.",
    confidence: 0.91,
    sections: [
      { title: "Decision", body: "Defer migration until the security and delivery blockers are closed.", citations: [evidence[0], evidence[2]] },
      { title: "Business framing", body: "A short remediation wave materially improves execution confidence and protects timeline credibility.", citations: [evidence[1]] }
    ],
    generatedAt: "2026-04-16T06:12:00Z",
    artifactIds: ["art-001"]
  },
  {
    id: "report-technical",
    kind: "technical_dossier",
    title: "Technical migration dossier",
    summary: "Dependency, runtime, storage, and security posture analysis for the operator audience.",
    confidence: 0.9,
    sections: [
      { title: "Current state", body: "Java monolith, AngularJS admin, PostgreSQL, shell jobs, shared storage, and external SOAP/SFTP integrations.", citations: evidence.slice(0, 4) },
      { title: "Primary blockers", body: "Hardcoded secrets, sensitive log leakage, and long-lived CI credentials block safe migration readiness.", citations: [evidence[0], evidence[1], evidence[2]] }
    ],
    generatedAt: "2026-04-16T06:12:00Z",
    artifactIds: ["art-002"]
  },
  {
    id: "report-cost",
    kind: "cost_report",
    title: "Cost and ROI pack",
    summary: "Target-state run rate, one-time migration investment, and payback framing for stakeholder review.",
    confidence: 0.87,
    sections: [{ title: "Cost delta", body: "Managed services reduce monthly run-rate once the remediation wave closes operational toil." }],
    generatedAt: "2026-04-16T06:12:00Z",
    artifactIds: ["art-003"]
  },
  {
    id: "report-risk",
    kind: "risk_report",
    title: "Security and compliance pack",
    summary: "Risk register, compliance posture, and recommended controls for migration approval review.",
    confidence: 0.89,
    sections: [{ title: "Risk register", body: "Security posture and logging controls need remediation before move-day." }],
    generatedAt: "2026-04-16T06:12:00Z",
    artifactIds: ["art-001"]
  },
  {
    id: "report-architecture",
    kind: "architecture_recommendation",
    title: "Architecture recommendation",
    summary: "Phased AWS landing-zone approach with managed data and object storage controls.",
    confidence: 0.88,
    sections: [{ title: "Target architecture", body: "Adopt AWS landing-zone controls, managed PostgreSQL, and object storage-backed document flows." }],
    generatedAt: "2026-04-16T06:12:00Z",
    artifactIds: ["art-004", "art-005"]
  },
  {
    id: "report-wave-plan",
    kind: "migration_wave_plan",
    title: "Migration wave plan",
    summary: "Program sequencing across remediation, foundation, and cutover phases.",
    confidence: 0.88,
    sections: [{ title: "Wave sequencing", body: "Three waves move from remediation to cutover with explicit exit criteria." }],
    generatedAt: "2026-04-16T06:12:00Z",
    artifactIds: ["art-004"]
  },
  {
    id: "report-cutover",
    kind: "cutover_rollback",
    title: "Cutover and rollback plan",
    summary: "Rollback-aware production transition with restore testing and approval gates.",
    confidence: 0.86,
    sections: [{ title: "Rollback", body: "Keep the legacy platform reversible during the validation window and rehearse restore flows first." }],
    generatedAt: "2026-04-16T06:12:00Z",
    artifactIds: ["art-004"]
  },
  {
    id: "report-ops",
    kind: "operations_checklist",
    title: "Operations and monitoring checklist",
    summary: "Observability, runbook, backup, and ownership readiness checklist for the target operating model.",
    confidence: 0.85,
    sections: [{ title: "Operations readiness", body: "Add SLO baselines, alert routing, and restore drills before execution enablement." }],
    generatedAt: "2026-04-16T06:12:00Z",
    artifactIds: ["art-002"]
  }
];

const approvals: ApprovalRecord[] = [
  {
    id: "app-001",
    phase: "Assessment",
    state: "approved",
    requestedBy: "Mia Chen",
    approver: "Jordan Patel",
    comment: "Assessment run approved for workspace scope.",
    decidedAt: "2026-04-16T06:14:00Z"
  },
  {
    id: "app-002",
    phase: "Planning",
    state: "pending",
    requestedBy: "Mia Chen",
    comment: "Waiting for remediation strategy sign-off.",
    decidedAt: undefined
  },
  {
    id: "app-003",
    phase: "Execution",
    state: "not_required",
    requestedBy: "System",
    comment: "Execution remains locked until planning approval.",
    decidedAt: undefined
  }
];

const auditEvents: AuditEvent[] = [
  {
    id: "audit-001",
    actor: "System",
    action: "assessment.run.started",
    entityType: "migration_project",
    entityId: "legacycart",
    createdAt: "2026-04-16T06:11:00Z",
    metadata: { mode: "local", source: "local-worker" }
  },
  {
    id: "audit-002",
    actor: "Worker",
    action: "evidence.normalized",
    entityType: "evidence_bundle",
    entityId: "legacycart:evidence",
    createdAt: "2026-04-16T06:11:18Z",
    metadata: { evidenceCount: "4", graphEdges: "6" }
  },
  {
    id: "audit-003",
    actor: "Recommendation Engine",
    action: "assessment.recommendation.generated",
    entityType: "recommendation",
    entityId: "rec-001",
    createdAt: "2026-04-16T06:12:02Z",
    metadata: { confidence: "0.9", provider: "AWS" }
  },
  {
    id: "audit-004",
    actor: "User",
    action: "approval.requested",
    entityType: "approval",
    entityId: "app-002",
    createdAt: "2026-04-16T06:14:13Z",
    metadata: { phase: "Planning" }
  }
];

const chat: ChatMessage[] = [
  {
    id: "chat-001",
    author: "Mia Chen",
    role: "human",
    createdAt: "2026-04-16T06:13:00Z",
    content: "Can we move the database first if we only have two weeks for remediation?"
  },
  {
    id: "chat-002",
    author: "Cockpit Assistant",
    role: "ai",
    createdAt: "2026-04-16T06:13:10Z",
    content: "Yes, but only after the credential and logging issues are fixed. A database-first scenario improves control-plane safety, yet the current hardcoded password and direct job access still make the move too risky."
  },
  {
    id: "chat-003",
    author: "Mia Chen",
    role: "human",
    createdAt: "2026-04-16T06:13:42Z",
    content: "What is the safest provider choice for the first wave?"
  },
  {
    id: "chat-004",
    author: "Cockpit Assistant",
    role: "ai",
    createdAt: "2026-04-16T06:13:55Z",
    content: "AWS remains the best match here because the migration blockers are operational rather than platform-specific, and AWS gives us the strongest landing-zone and IAM primitives for the workspace."
  }
];

const connectors: ConnectorItem[] = [
  {
    id: "conn-001",
    name: "Assessment local directory",
    kind: "source",
    status: "connected",
    details: "Scans `demo-systems/legacycart` and normalizes files, logs, and manifests for the workspace.",
    lastSyncAt: "2026-04-16T06:10:00Z"
  },
  {
    id: "conn-002",
    name: "GitHub repository",
    kind: "source",
    status: "proposed",
    details: "Disabled until an explicit connector token or repo URL is provided.",
    lastSyncAt: undefined
  },
  {
    id: "conn-003",
    name: "Azure Repos",
    kind: "source",
    status: "proposed",
    details: "Supported by the shell but gated until credentials are wired.",
    lastSyncAt: undefined
  },
  {
    id: "conn-004",
    name: "AWS execution adapter",
    kind: "cloud",
    status: "disabled",
    details: "Execution remains read-only until planning approval lands.",
    lastSyncAt: undefined
  }
];

const sourceConnections: SourceConnection[] = [
  {
    id: "source-local-legacycart",
    kind: "local_directory",
    name: "Assessment local directory",
    status: "connected",
    mode: "read_only",
    target: "demo-systems/legacycart",
    lastSyncAt: "2026-04-16T06:10:00Z",
    credentialRef: { id: "cred-none-local", kind: "none", label: "No credential required", redactedValue: "n/a" },
    notes: ["Primary local source for the workspace."]
  },
  {
    id: "source-github-template",
    kind: "github",
    name: "GitHub repo handoff",
    status: "proposed",
    mode: "discovery",
    target: "github.com/northstar/legacycart",
    branch: "main",
    credentialRef: { id: "cred-gh-template", kind: "oauth", label: "GitHub app install", redactedValue: "gho_****" },
    notes: ["Ready for live ingestion once credentials are supplied."]
  },
  {
    id: "source-azure-template",
    kind: "azure_repos",
    name: "Azure Repos handoff",
    status: "proposed",
    mode: "discovery",
    target: "dev.azure.com/northstar/legacycart",
    branch: "main",
    credentialRef: { id: "cred-azdo-template", kind: "oauth", label: "Azure DevOps OAuth", redactedValue: "ado_****" },
    notes: ["Tool Factory proposal exists but remains disabled until approved."]
  }
];

const cloudConnections: CloudConnection[] = [
  {
    id: "cloud-aws-discovery",
    provider: "aws",
    name: "AWS discovery adapter",
    status: "connected",
    mode: "discovery",
    accountLabel: "Northstar sandbox",
    regionScope: ["us-east-1", "us-west-2"],
    credentialRef: { id: "cred-aws-role", kind: "assumed_role", label: "Assumed discovery role", redactedValue: "arn:aws:iam::****:role/discovery" },
    notes: ["Read-only inventory and dry-run planning enabled."]
  },
  {
    id: "cloud-gcp-advisory",
    provider: "gcp",
    name: "GCP advisory model",
    status: "disabled",
    mode: "discovery",
    accountLabel: "Not connected",
    regionScope: ["us-central1"],
    credentialRef: { id: "cred-gcp-none", kind: "none", label: "No active credential", redactedValue: "n/a" },
    notes: ["Recommendation logic is available even without live account discovery."]
  },
  {
    id: "cloud-azure-advisory",
    provider: "azure",
    name: "Azure advisory model",
    status: "disabled",
    mode: "discovery",
    accountLabel: "Not connected",
    regionScope: ["eastus"],
    credentialRef: { id: "cred-azure-none", kind: "none", label: "No active credential", redactedValue: "n/a" },
    notes: ["Execution adapters remain AWS-first for this release."]
  }
];

const assessmentRuns: AssessmentRun[] = [
  {
    id: "run-legacycart-sync",
    projectId: "legacycart",
    status: "succeeded",
    startedAt: "2026-04-16T06:11:00Z",
    completedAt: "2026-04-16T06:12:05Z",
    mode: "local_worker",
    pipelineSummaries: [
      { pipelineKey: "intake_connections", title: "Intake + connections", status: "succeeded", summary: "Business inputs and source connectors normalized.", startedAt: "2026-04-16T06:11:00Z", completedAt: "2026-04-16T06:11:06Z" },
      { pipelineKey: "evidence_ingestion", title: "Evidence ingestion", status: "succeeded", summary: "Files, logs, and manifests normalized into a typed dossier.", startedAt: "2026-04-16T06:11:06Z", completedAt: "2026-04-16T06:11:18Z" },
      { pipelineKey: "assessment_swarm", title: "Assessment swarm", status: "succeeded", summary: "Specialist agents produced findings, provider fit, cost, and risk outputs.", startedAt: "2026-04-16T06:11:18Z", completedAt: "2026-04-16T06:11:40Z" },
      { pipelineKey: "planning_artifacts", title: "Planning artifacts", status: "succeeded", summary: "Migration waves, diagram, and IaC starter artifacts generated.", startedAt: "2026-04-16T06:11:40Z", completedAt: "2026-04-16T06:11:48Z" },
      { pipelineKey: "report_composition", title: "Report composition", status: "succeeded", summary: "Executive, technical, risk, and roadmap reports assembled.", startedAt: "2026-04-16T06:11:48Z", completedAt: "2026-04-16T06:11:58Z" },
      { pipelineKey: "evals_governance", title: "Evals + governance", status: "succeeded", summary: "Critics scored evidence coverage, safety, and consistency before final output.", startedAt: "2026-04-16T06:11:58Z", completedAt: "2026-04-16T06:12:05Z" }
    ],
    agentOutputs: [],
    finalRecommendation: {
      decision: "defer",
      label: "Defer until blockers are remediated",
      confidence: 0.9,
      summary: "The product should stay in remediation mode until security, identity, and operational blockers are addressed.",
      recommendedProvider: "AWS",
      rationale: ["Security posture blocks immediate migration.", "AWS remains the best target once blockers are removed."],
      blockers: ["Hardcoded credentials", "Sensitive logs", "Static CI credentials"],
      nextSteps: ["Approve the remediation backlog.", "Run the planning phase after blocker closure."],
      evidence
    }
  }
];

const agentRuns: AgentRun[] = [
  { id: "agent-001", assessmentRunId: "run-legacycart-sync", agentKey: "intake_normalizer", displayName: "Intake Normalizer Agent", stage: "intake", status: "succeeded", critic: false, confidence: 0.95, summary: "Captured business context, geography, and migration constraints.", evidenceCount: 2, latencyMs: 320, warningCount: 0, retryCount: 0, startedAt: "2026-04-16T06:11:00Z", completedAt: "2026-04-16T06:11:02Z" },
  { id: "agent-002", assessmentRunId: "run-legacycart-sync", agentKey: "iam_secrets_posture", displayName: "IAM & Secrets Posture Agent", stage: "analysis", status: "succeeded", critic: false, confidence: 0.97, summary: "Detected hardcoded database credentials and long-lived deploy secrets.", evidenceCount: 3, latencyMs: 410, warningCount: 2, retryCount: 0, startedAt: "2026-04-16T06:11:18Z", completedAt: "2026-04-16T06:11:23Z" },
  { id: "agent-003", assessmentRunId: "run-legacycart-sync", agentKey: "landing_zone_strategy", displayName: "Landing Zone Strategy Agent", stage: "planning", status: "succeeded", critic: false, confidence: 0.9, summary: "Recommended an AWS landing zone with staged database and storage modernization.", evidenceCount: 2, latencyMs: 380, warningCount: 0, retryCount: 0, startedAt: "2026-04-16T06:11:40Z", completedAt: "2026-04-16T06:11:44Z" },
  { id: "agent-004", assessmentRunId: "run-legacycart-sync", agentKey: "citation_evidence_critic", displayName: "Citation / Evidence Critic Agent", stage: "critique", status: "succeeded", critic: true, confidence: 0.93, summary: "Verified that surfaced outputs remain evidence-backed.", evidenceCount: 4, latencyMs: 210, warningCount: 0, retryCount: 0, startedAt: "2026-04-16T06:11:58Z", completedAt: "2026-04-16T06:12:01Z" },
  { id: "agent-005", assessmentRunId: "run-legacycart-sync", agentKey: "safety_critic", displayName: "Safety Critic Agent", stage: "critique", status: "succeeded", critic: true, confidence: 0.92, summary: "Confirmed execution adapters remain disabled without approval.", evidenceCount: 1, latencyMs: 180, warningCount: 0, retryCount: 0, startedAt: "2026-04-16T06:12:01Z", completedAt: "2026-04-16T06:12:03Z" }
];

const evalRuns: EvalRun[] = [
  {
    id: "eval-001",
    assessmentRunId: "run-legacycart-sync",
    overallScore: 90,
    status: "succeeded",
    completedAt: "2026-04-16T06:12:05Z",
    metrics: [
      { metricKey: "citation_coverage", label: "Citation coverage", score: 96, summary: "Recommendations remain linked to evidence.", status: "pass" },
      { metricKey: "unsupported_claim_rate", label: "Unsupported claim rate", score: 92, summary: "Workspace outputs keep unsupported claims low.", status: "pass" },
      { metricKey: "recommendation_consistency", label: "Recommendation consistency", score: 89, summary: "Specialist-agent outputs converge on the same final recommendation.", status: "pass" },
      { metricKey: "cost_sanity", label: "Cost sanity", score: 84, summary: "Cost model assumptions are directionally sound but still scenario-based.", status: "warn" },
      { metricKey: "latency", label: "Agent latency", score: 87, summary: "Assessment finished comfortably within local runtime expectations.", status: "pass" },
      { metricKey: "policy_compliance", label: "Policy compliance", score: 90, summary: "Discovery remains read-only and execution stays approval-gated.", status: "pass" }
    ]
  }
];

const factoryProposals: FactoryProposal[] = [
  {
    id: "proposal-azure-repos",
    name: "Azure Repos live ingestion connector",
    kind: "connector",
    status: "proposed",
    rationale: "Requested source type is present in the product but still disabled until credentials and approval are available.",
    requiredPermissions: ["repo:read", "oauth:azure-devops"],
    promptVersion: "2026-04-16-connector-proposal-v1",
    scaffoldFiles: ["services/worker/app/connectors/azure_repos.py", "services/api/app/api/routes/azure_repos.py"],
    approvalRequired: true
  },
  {
    id: "proposal-cert-inventory",
    name: "Certificate inventory collector",
    kind: "tool",
    status: "proposed",
    rationale: "Network ingress and DNS evidence is still thin for certificate cutover readiness.",
    requiredPermissions: ["dns:read", "network:read"],
    promptVersion: "2026-04-16-tool-proposal-v1",
    scaffoldFiles: ["services/worker/app/tools/certificate_inventory.py"],
    approvalRequired: true
  }
];

const scenarioDiffs: ScenarioDiff[] = [
  {
    baselineScenarioId: "scenario-security-first",
    comparedScenarioId: "scenario-lift-and-shift",
    readinessDelta: -9,
    riskShift: "Risk increases because remediation debt remains in the cutover path.",
    costShift: "Near-term spend is lower, but long-term carry cost is worse.",
    summary: "Lift-and-shift buys speed at the expense of safety and cleanup effort."
  },
  {
    baselineScenarioId: "scenario-security-first",
    comparedScenarioId: "scenario-strangler",
    readinessDelta: 1,
    riskShift: "Risk stays controlled while long-term flexibility improves.",
    costShift: "Program cost rises slightly due to more coordination and phased delivery.",
    summary: "Strangler-style modernization is the most balanced MSP delivery track."
  }
];

const evaluation: EvalSummary = {
  overallScore: 88,
  checks: [
    { name: "Report completeness", score: 91, note: "All major business and technical sections are represented." },
    { name: "Citation coverage", score: 96, note: "Findings and recommendations are linked to evidence refs." },
    { name: "Unsupported claim rate", score: 92, note: "The workspace story keeps claims grounded in evidence." },
    { name: "Action safety compliance", score: 84, note: "Writes remain gated and the AWS adapter is disabled." }
  ]
};

export function createMockDashboardSummary(): DashboardSummary {
  return {
    activeProjects: 8,
    pendingApprovals: 2,
    openFindings: 14,
    reportExports: 23,
    topProjects: [
      {
        id: "legacycart",
        name: "Retail commerce modernization assessment",
        clientName: "Northwind Retail Group",
        readinessScore: 52,
        migrationDecision: "Defer until blockers are remediated",
        confidence: 0.9,
        phase: "Assessment",
        status: "Awaiting planning approval",
        recommendedProvider: "AWS"
      },
      {
        id: "atlas-inventory",
        name: "Atlas inventory platform",
        clientName: "Atlas Logistics",
        readinessScore: 63,
        migrationDecision: "Migrate partially",
        confidence: 0.84,
        phase: "Risk review",
        status: "Provider comparison ready",
        recommendedProvider: "Azure"
      },
      {
        id: "summit-booking",
        name: "Summit booking engine",
        clientName: "Summit Experiences",
        readinessScore: 72,
        migrationDecision: "Migrate now",
        confidence: 0.8,
        phase: "Plan",
        status: "Execution pending",
        recommendedProvider: "GCP"
      }
    ]
  };
}

export function createMockProjectDataset(projectId = "legacycart"): ProjectDataset {
  return {
    projectId,
    projectName: "Retail commerce modernization assessment",
    clientName: "Northwind Retail Group",
    dashboard: createMockDashboardSummary(),
    overview: {
      readinessScore: 52,
      migrationDecision: "Defer until blockers are remediated",
      confidence: 0.9,
      phase: "Assessment Cockpit",
      status: "Assessment ready",
      recommendedProvider: "AWS",
      owner: "Mia Chen",
      lastScanAt: "2026-04-16T06:11:20Z",
      sourceSystem: "demo-systems/legacycart",
      targetSystem: "AWS landing zone with containerized backend and managed PostgreSQL",
      businessSummary: "Retail order management with batch invoicing, nightly reconciliation, and external payment integrations.",
      narrative:
        "The application can move, but the current security posture and operational model mean a straight lift-and-shift would recreate the same risks in cloud. The strongest path is a short remediation wave followed by a phased modernization plan."
    },
    evidence,
    findings,
    recommendations,
    providers,
    scenarios,
    dependencyNodes,
    dependencyEdges,
    reports,
    artifacts,
    approvals,
    auditEvents,
    chat,
    connectors,
    sourceConnections,
    cloudConnections,
    assessmentRuns,
    agentRuns,
    evalRuns,
    factoryProposals,
    scenarioDiffs,
    evaluation,
    reportHighlights: [
      "Hardcoded credentials and leaked log data make immediate production movement unsafe.",
      "AWS is the recommended target because the workload benefits from strong IAM, managed database, and storage primitives.",
      "A security-first or strangler-style sequence has a materially better risk profile than a pure lift-and-shift."
    ],
    exportFormats: ["Executive PDF", "Technical dossier", "Roadmap outline", "Terraform snippet", "Mermaid diagram"],
    costModel: {
      currentMonthlyRunRate: 48600,
      targetMonthlyRunRate: 32100,
      migrationOneTimeCost: 142000,
      estimatedPaybackMonths: 11,
      roiPercent: 38,
      assumptions: [
        "AWS managed PostgreSQL replaces the self-managed database VM",
        "Invoice files move to object storage with lifecycle rules",
        "Legacy jobs are containerized before cutover"
      ],
      driverBreakdown: [
        { label: "Compute", current: 18600, target: 14200 },
        { label: "Database", current: 15400, target: 9800 },
        { label: "Storage", current: 7400, target: 5100 },
        { label: "Operations", current: 7200, target: 3000 }
      ]
    },
    riskModel: {
      overallRisk: "High until secret handling and logging are remediated",
      complianceNotes: [
        "PII appears in logs and requires redaction controls",
        "Invoice storage should meet retention and encryption policy",
        "Cross-border data residency needs confirmation before execution"
      ],
      openIssues: [
        "Hardcoded database password",
        "Static deployment credential",
        "Shared NFS-based invoice storage",
        "No tested rollback procedure for batch jobs"
      ],
      recommendedControls: [
        "Rotate credentials and store them in a vault",
        "Add log redaction and retain only security-approved fields",
        "Split jobs into retryable workers with explicit approvals",
        "Define a backup and restore drill before execution"
      ],
      rpo: "15 minutes for transactional data",
      rto: "2 hours for core order intake"
    },
    roadmap: {
      waves: [
        {
          name: "Wave 0 - Remediation",
          description: "Fix secrets, logging, and credential handling; confirm backup posture.",
          duration: "1-2 weeks",
          exitCriteria: ["Secrets rotated", "Logs redacted", "Approval gate in place"]
        },
        {
          name: "Wave 1 - Foundation",
          description: "Move the backend into containers and establish the AWS landing zone.",
          duration: "2-3 weeks",
          exitCriteria: ["Container image built", "Managed database selected", "Network controls defined"]
        },
        {
          name: "Wave 2 - Cutover",
          description: "Move the data path, batch jobs, and invoice storage with rollback rehearsed.",
          duration: "2 weeks",
          exitCriteria: ["Restore test passed", "Cutover plan approved", "Rollback rehearsal complete"]
        }
      ],
      cutover: [
        "Freeze writes and snapshot the source database",
        "Backfill the target database and validate record counts",
        "Switch the jobs to the new queue-backed worker",
        "Monitor error budgets during the first 24 hours"
      ],
      rollback: [
        "Retain the source environment in read-only mode for one week",
        "Keep DNS and user-facing traffic switchable",
        "Document a one-command restore path for the database and file store"
      ]
    }
  };
}

export const sectionLabels = {
  overview: "Project overview",
  programBoard: "Program board",
  commandCenter: "Command center",
  dependencies: "Dependency graph",
  findings: "Findings",
  providers: "Provider comparison",
  cost: "Cost and ROI",
  risk: "Risk and compliance",
  scenarios: "Scenario analysis",
  reports: "Report center",
  artifacts: "Artifacts",
  approvals: "Approval center",
  audit: "Audit log",
  chat: "Stakeholder chat",
  connectors: "Connectors and settings",
  settings: "Workspace settings"
} as const;

export function buildProjectDatasetFromApi({
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
}: {
  projectId: string;
  dashboard: DashboardSummary;
  overview: ProjectOverview;
  assessment: AssessmentRun;
  assessmentRuns: AssessmentRun[];
  agentRuns: AgentRun[];
  evalRuns: EvalRun[];
  graph: DependencyGraph;
  findings: Finding[];
  providers: ProviderOption[];
  costRoi: CostRoiSummary;
  riskCompliance: RiskComplianceSummary;
  scenarios: Scenario[];
  scenarioDiffs: ScenarioDiff[];
  reports: Report[];
  artifacts: ReportArtifact[];
  approvals: ApprovalRecord[];
  auditEvents: AuditEvent[];
  registryEntries: RegistryEntry[];
  sourceConnections: SourceConnection[];
  cloudConnections: CloudConnection[];
  factoryProposals: FactoryProposal[];
  chatMessages: ChatMessage[];
}): ProjectDataset {
  const evidence = Array.from(
    new Map(findings.flatMap((finding) => finding.evidence).map((item) => [item.id, item])).values()
  );
  const finalRecommendation = assessment.finalRecommendation;
  const recommendations: Recommendation[] = [
    {
      id: `rec-${finalRecommendation.decision}`,
      title: finalRecommendation.label,
      summary: finalRecommendation.summary,
      confidence: finalRecommendation.confidence,
      rationale: finalRecommendation.rationale.join(" "),
      effort: "medium",
      impact: "high",
      evidence: finalRecommendation.evidence
    },
    ...findings.slice(0, 2).map((finding, index) => {
      const effort: Recommendation["effort"] = index === 0 ? "small" : "medium";
      const impact: Recommendation["impact"] = finding.severity === "critical" ? "high" : "medium";

      return {
        id: `derived-${index + 1}`,
        title: finding.recommendation,
        summary: finding.summary,
        confidence: finding.confidence,
        rationale: `Derived from ${finding.title.toLowerCase()} and kept linked to the same evidence trail.`,
        effort,
        impact,
        evidence: finding.evidence
      };
    })
  ];

  const latestEvalRun = evalRuns[0];
  const evaluationChecks =
    latestEvalRun?.metrics.map((metric) => ({
      name: metric.label,
      score: metric.score,
      note: metric.summary
    })) ??
    assessment.agentOutputs
      .filter((agent) => ["citation_evidence_critic", "safety_critic"].includes(agent.agentKey))
      .map((agent) => ({
        name: agent.displayName,
        score: Math.round(agent.confidence * 100),
        note: agent.summary
      }));

  const evaluation = {
    overallScore:
      latestEvalRun?.overallScore ??
      (evaluationChecks.length > 0
        ? Math.round(evaluationChecks.reduce((sum, item) => sum + item.score, 0) / evaluationChecks.length)
        : Math.round(assessment.finalRecommendation.confidence * 100)),
    checks: [
      ...evaluationChecks,
      {
        name: "Recommendation consistency",
        score: Math.round(assessment.finalRecommendation.confidence * 100),
        note: "The final recommendation is assembled after specialist-agent synthesis and critic review."
      }
    ]
  };

  const connectors = [
    ...sourceConnections.map((connection) => ({
      id: connection.id,
      name: connection.name,
      kind: "source" as const,
      status: connection.status === "disabled" ? ("disabled" as const) : connection.status,
      details: `${connection.target} · ${connection.notes.join(" ")}`,
      lastSyncAt: connection.lastSyncAt
    })),
    ...cloudConnections.map((connection) => ({
      id: connection.id,
      name: connection.name,
      kind: "cloud" as const,
      status: connection.status === "disabled" ? ("disabled" as const) : connection.status,
      details: `${connection.accountLabel} · ${connection.notes.join(" ")}`,
      lastSyncAt: undefined
    })),
    ...factoryProposals.map((proposal) => ({
      id: proposal.id,
      name: proposal.name,
      kind: proposal.kind === "connector" ? ("source" as const) : ("registry" as const),
      status: "proposed" as const,
      details: proposal.rationale,
      lastSyncAt: undefined
    })),
    ...registryEntries.map((entry) => ({
      id: entry.id,
      name: entry.name,
      kind:
        entry.kind === "connector"
          ? ("source" as const)
          : entry.kind === "tool"
            ? ("registry" as const)
            : ("cloud" as const),
      status:
        entry.status === "enabled"
          ? ("connected" as const)
          : entry.status === "proposed"
            ? ("proposed" as const)
            : ("disabled" as const),
      details: entry.rationale,
      lastSyncAt: undefined
    }))
  ];

  return {
    projectId,
    projectName: overview.name,
    clientName: overview.clientName,
    dashboard,
    overview: {
      readinessScore: overview.readinessScore,
      migrationDecision: overview.migrationDecision,
      confidence: overview.confidence,
      phase: overview.phase,
      status: overview.status,
      recommendedProvider: overview.recommendedProvider,
      owner: "Mia Chen",
      lastScanAt: assessment.completedAt,
      sourceSystem: "demo-systems/legacycart",
      targetSystem: `${providers[0]?.name ?? "AWS"} landing zone with phased modernization`,
      businessSummary:
        "Legacy retail order and invoicing platform with cron-style jobs, shared file storage, and brittle external integrations.",
      narrative: finalRecommendation.summary
    },
    evidence,
    findings,
    recommendations,
    providers,
    scenarios,
    scenarioDiffs,
    dependencyNodes: graph.nodes,
    dependencyEdges: graph.edges,
    reports,
    artifacts,
    approvals,
    auditEvents,
    chat: chatMessages,
    connectors,
    sourceConnections,
    cloudConnections,
    assessmentRuns,
    agentRuns,
    evalRuns,
    factoryProposals,
    evaluation,
    reportHighlights: reports.slice(0, 3).map((report) => report.summary),
    exportFormats: Array.from(new Set(artifacts.map((artifact) => artifact.format.toUpperCase()))),
    costModel: {
      currentMonthlyRunRate: Math.round(costRoi.annualBaselineCost / 12),
      targetMonthlyRunRate: Math.round(costRoi.annualTargetCost / 12),
      migrationOneTimeCost: costRoi.migrationInvestment,
      estimatedPaybackMonths: costRoi.paybackMonths,
      roiPercent: costRoi.roiPercent,
      assumptions: costRoi.assumptions,
      driverBreakdown: [
        { label: "Compute & app hosting", current: 18000, target: 13200 },
        { label: "Database & backups", current: 14500, target: 9800 },
        { label: "Storage & transfer", current: 7800, target: 4300 },
        { label: "Operations overhead", current: 11600, target: 5700 }
      ]
    },
    riskModel: {
      overallRisk: `${riskCompliance.overallRisk[0].toUpperCase()}${riskCompliance.overallRisk.slice(1)} until blockers are remediated`,
      complianceNotes: [
        ...riskCompliance.complianceFrameworks.map((framework) => `${framework} coverage requires evidence-backed controls.`),
        riskCompliance.dataResidency
      ],
      openIssues: riskCompliance.risks.map((risk) => risk.title),
      recommendedControls: riskCompliance.risks.map((risk) => risk.mitigation),
      rpo: "15 minutes for transactional data",
      rto: "2 hours for order intake"
    },
    roadmap: {
      waves: [
        {
          name: "Wave 0 - Remediation",
          description: "Close exposed secrets, logging, and transport blockers before migration approvals move forward.",
          duration: "1-2 weeks",
          exitCriteria: finalRecommendation.blockers.slice(0, 3)
        },
        {
          name: "Wave 1 - Platform foundation",
          description: `Establish the ${providers[0]?.name ?? "AWS"} landing zone, object storage, and managed database target.`,
          duration: "2-3 weeks",
          exitCriteria: ["Landing zone approved", "Database target ready", "Observability baseline enabled"]
        },
        {
          name: "Wave 2 - Controlled cutover",
          description: "Move data paths and jobs after restore testing and rollback rehearsal.",
          duration: "1-2 weeks",
          exitCriteria: ["Restore test passed", "Cutover plan approved", "Rollback runbook signed off"]
        }
      ],
      cutover: [
        "Snapshot and validate the source database before traffic movement.",
        "Switch jobs and invoice storage after evidence-backed validation checks pass.",
        "Monitor error budgets and rollback thresholds during the first 24 hours."
      ],
      rollback: [
        "Retain the source environment in read-only mode during the validation window.",
        "Keep traffic and job schedules reversible until business sign-off is complete.",
        "Use the approval center to gate any execution adapter enablement."
      ]
    }
  };
}
