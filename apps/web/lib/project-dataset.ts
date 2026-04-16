import type {
  AnalysisQuestion,
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
  DeploymentPlan,
  EvalRun,
  EvidenceReference,
  FactoryProposal,
  Finding,
  IntakeProfile,
  ObservabilityTrace,
  PipelineSummary,
  PreviewDeploymentStatus,
  ProjectOverview,
  ProviderOption,
  Recommendation,
  RegistryEntry,
  Report,
  ReportArtifact,
  RiskComplianceSummary,
  ScenarioDiff,
  SourceConnection,
  Scenario,
} from "@contracts/index";

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
  intake: IntakeProfile;
  mtcPipeline: PipelineSummary[];
  observability: ObservabilityTrace[];
  deploymentPlan: DeploymentPlan;
  factoryProposals: FactoryProposal[];
  scenarioDiffs: ScenarioDiff[];
  analysisQuestions: AnalysisQuestion[];
  previewStatus: PreviewDeploymentStatus;
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
  chatMessages,
  intake,
  mtcPipeline,
  observability,
  deploymentPlan,
  analysisQuestions,
  previewStatus,
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
  intake: IntakeProfile;
  mtcPipeline: PipelineSummary[];
  observability: ObservabilityTrace[];
  deploymentPlan: DeploymentPlan;
  analysisQuestions: AnalysisQuestion[];
  previewStatus: PreviewDeploymentStatus;
}): ProjectDataset {
  const evidence = Array.from(
    new Map(findings.flatMap((finding) => finding.evidence).map((item) => [item.id, item])).values(),
  );
  const finalRecommendation = assessment.finalRecommendation;
  const primarySource = sourceConnections[0];
  const primaryAuditActor = auditEvents[0]?.actor ?? "Judge Workspace";
  const primaryProvider = providers[0]?.name ?? overview.recommendedProvider ?? "Pending";

  const recommendations: Recommendation[] = [
    {
      id: `rec-${finalRecommendation.decision}`,
      title: finalRecommendation.label,
      summary: finalRecommendation.summary,
      confidence: finalRecommendation.confidence,
      rationale: finalRecommendation.rationale.join(" "),
      effort: "medium",
      impact: "high",
      evidence: finalRecommendation.evidence,
    },
    ...findings.slice(0, 2).map((finding, index) => ({
      id: `derived-${index + 1}`,
      title: finding.recommendation,
      summary: finding.summary,
      confidence: finding.confidence,
      rationale: `Derived from ${finding.title.toLowerCase()} and kept linked to the same evidence trail.`,
      effort: (index === 0 ? "small" : "medium") as Recommendation["effort"],
      impact: (finding.severity === "critical" ? "high" : "medium") as Recommendation["impact"],
      evidence: finding.evidence,
    })),
  ];

  const latestEvalRun = evalRuns[0];
  const evaluationChecks =
    latestEvalRun?.metrics.map((metric) => ({
      name: metric.label,
      score: metric.score,
      note: metric.summary,
    })) ??
    assessment.agentOutputs.map((agent) => ({
      name: agent.displayName,
      score: Math.round(agent.confidence * 100),
      note: agent.summary,
    }));

  const evaluation = {
    overallScore:
      latestEvalRun?.overallScore ??
      (evaluationChecks.length > 0
        ? Math.round(evaluationChecks.reduce((sum, item) => sum + item.score, 0) / evaluationChecks.length)
        : Math.round(finalRecommendation.confidence * 100)),
    checks: evaluationChecks,
  };

  const connectors = [
    ...sourceConnections.map((connection) => ({
      id: connection.id,
      name: connection.name,
      kind: "source" as const,
      status: connection.status === "disabled" ? ("disabled" as const) : connection.status,
      details: `${connection.target}${connection.notes.length > 0 ? ` · ${connection.notes.join(" ")}` : ""}`,
      lastSyncAt: connection.lastSyncAt,
    })),
    ...cloudConnections.map((connection) => ({
      id: connection.id,
      name: connection.name,
      kind: "cloud" as const,
      status: connection.status === "disabled" ? ("disabled" as const) : connection.status,
      details: `${connection.accountLabel}${connection.notes.length > 0 ? ` · ${connection.notes.join(" ")}` : ""}`,
      lastSyncAt: undefined,
    })),
    ...factoryProposals.map((proposal) => ({
      id: proposal.id,
      name: proposal.name,
      kind: proposal.kind === "connector" ? ("source" as const) : ("registry" as const),
      status: "proposed" as const,
      details: proposal.rationale,
      lastSyncAt: undefined,
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
      lastSyncAt: undefined,
    })),
  ];

  const currentMonthlyRunRate = Math.round(costRoi.annualBaselineCost / 12);
  const targetMonthlyRunRate = Math.round(costRoi.annualTargetCost / 12);
  const driverBreakdown = [
    { label: "Application hosting", current: Math.round(currentMonthlyRunRate * 0.36), target: Math.round(targetMonthlyRunRate * 0.34) },
    { label: "Data platform", current: Math.round(currentMonthlyRunRate * 0.28), target: Math.round(targetMonthlyRunRate * 0.3) },
    { label: "Storage and transfer", current: Math.round(currentMonthlyRunRate * 0.16), target: Math.round(targetMonthlyRunRate * 0.14) },
    { label: "Operations overhead", current: Math.round(currentMonthlyRunRate * 0.2), target: Math.round(targetMonthlyRunRate * 0.22) },
  ];

  const roadmapWaves =
    scenarios.length > 0
      ? scenarios.slice(0, 3).map((scenario, index) => ({
          name: `Wave ${index} - ${scenario.name}`,
          description: scenario.description,
          duration: index === 0 ? "1-2 weeks" : index === 1 ? "2-4 weeks" : "2-3 weeks",
          exitCriteria: scenario.assumptionSet,
        }))
      : [
          {
            name: "Wave 0 - Intake",
            description: "Complete discovery, answer open questions, and validate the first migration plan.",
            duration: "1 week",
            exitCriteria: finalRecommendation.nextSteps.slice(0, 3),
          },
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
      owner: primaryAuditActor,
      lastScanAt: primarySource?.lastSyncAt ?? assessment.completedAt,
      sourceSystem: primarySource?.target ?? "Source not connected yet",
      targetSystem: `${primaryProvider} target landing zone`,
      businessSummary:
        findings[0]?.summary ??
        analysisQuestions[0]?.rationale ??
        "The project is ready for evidence-backed analysis from the supplied source.",
      narrative: finalRecommendation.summary,
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
    intake,
    mtcPipeline,
    observability,
    deploymentPlan,
    factoryProposals,
    analysisQuestions,
    previewStatus,
    evaluation,
    reportHighlights: (reports.length > 0 ? reports : recommendations).slice(0, 3).map((item) => item.summary),
    exportFormats: Array.from(new Set(artifacts.map((artifact) => artifact.format.toUpperCase()))),
    costModel: {
      currentMonthlyRunRate,
      targetMonthlyRunRate,
      migrationOneTimeCost: costRoi.migrationInvestment,
      estimatedPaybackMonths: costRoi.paybackMonths,
      roiPercent: costRoi.roiPercent,
      assumptions: costRoi.assumptions,
      driverBreakdown,
    },
    riskModel: {
      overallRisk: `${riskCompliance.overallRisk[0].toUpperCase()}${riskCompliance.overallRisk.slice(1)} until blockers are remediated`,
      complianceNotes: [
        ...riskCompliance.complianceFrameworks.map((framework) => `${framework} coverage requires evidence-backed controls.`),
        riskCompliance.dataResidency,
      ],
      openIssues: riskCompliance.risks.map((risk) => risk.title),
      recommendedControls: riskCompliance.risks.map((risk) => risk.mitigation),
      rpo: "15 minutes for transactional data",
      rto: "2 hours for order intake",
    },
    roadmap: {
      waves: roadmapWaves,
      cutover: finalRecommendation.nextSteps.slice(0, 3),
      rollback:
        finalRecommendation.blockers.length > 0
          ? finalRecommendation.blockers.slice(0, 3)
          : ["Preserve the current source in a recoverable state until the preview passes health checks."],
    },
  };
}
