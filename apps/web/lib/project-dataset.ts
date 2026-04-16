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
      evidence: finalRecommendation.evidence,
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
        evidence: finding.evidence,
      };
    }),
  ];

  const latestEvalRun = evalRuns[0];
  const evaluationChecks =
    latestEvalRun?.metrics.map((metric) => ({
      name: metric.label,
      score: metric.score,
      note: metric.summary,
    })) ??
    assessment.agentOutputs
      .filter((agent) => ["citation_evidence_critic", "safety_critic"].includes(agent.agentKey))
      .map((agent) => ({
        name: agent.displayName,
        score: Math.round(agent.confidence * 100),
        note: agent.summary,
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
        note: "The final recommendation is assembled after specialist-agent synthesis and critic review.",
      },
    ],
  };

  const connectors = [
    ...sourceConnections.map((connection) => ({
      id: connection.id,
      name: connection.name,
      kind: "source" as const,
      status: connection.status === "disabled" ? ("disabled" as const) : connection.status,
      details: `${connection.target} · ${connection.notes.join(" ")}`,
      lastSyncAt: connection.lastSyncAt,
    })),
    ...cloudConnections.map((connection) => ({
      id: connection.id,
      name: connection.name,
      kind: "cloud" as const,
      status: connection.status === "disabled" ? ("disabled" as const) : connection.status,
      details: `${connection.accountLabel} · ${connection.notes.join(" ")}`,
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
        { label: "Operations overhead", current: 11600, target: 5700 },
      ],
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
      waves: [
        {
          name: "Wave 0 - Remediation",
          description: "Close exposed secrets, logging, and transport blockers before migration approvals move forward.",
          duration: "1-2 weeks",
          exitCriteria: finalRecommendation.blockers.slice(0, 3),
        },
        {
          name: "Wave 1 - Foundation",
          description: "Establish the landing zone, platform guardrails, and first cloud-ready application boundary.",
          duration: "2-4 weeks",
          exitCriteria: [
            "Source and cloud connectors validated",
            "Approval-gated CI/CD path ready",
            "Target architecture and network posture agreed",
          ],
        },
        {
          name: "Wave 2 - Migration",
          description: "Move the first migration wave with rollback, restore, and evidence-linked change control.",
          duration: "2-3 weeks",
          exitCriteria: [
            "Cutover runbook approved",
            "Rollback tested",
            "Operations and monitoring checklist accepted",
          ],
        },
      ],
      cutover: [
        "Freeze writes and capture a verified source snapshot.",
        "Run the approved migration wave and validate record counts.",
        "Switch the workload and monitor the first production window closely.",
      ],
      rollback: [
        "Retain the source system in a recoverable standby posture.",
        "Preserve reversible network and deployment changes.",
        "Use the approved rollback checklist if validation gates fail.",
      ],
    },
  };
}
