import { AnalysisQuestionQueue } from "@/components/analysis-question-queue";
import { Badge, Card, MetricCard, SectionHeader } from "@/components/ui";
import { DEFAULT_WORKSPACE_ID, loadDashboardSummary, loadProjectDataset, loadWorkspaceProjects } from "@/lib/app-api";
import Link from "next/link";

function formatTimestamp(value: string | undefined) {
  if (!value) {
    return "Waiting for next run";
  }

  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function formatCurrency(value: number) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
}

export default async function DashboardPage() {
  const [dashboard, projects] = await Promise.all([loadDashboardSummary(), loadWorkspaceProjects(DEFAULT_WORKSPACE_ID)]);

  if (projects.length === 0) {
    return (
      <div className="space-y-6">
        <SectionHeader
          eyebrow="MTC workbench"
          title="The judge workspace is ready for the first real project."
          description="Download the macOS desktop app from the local SaaS site or start directly here by pasting a real project path into the intake workspace."
          action={
            <Link href="/projects/new" className="rounded-full bg-sky-400 px-5 py-3 text-sm font-medium text-slate-950">
              Open intake workspace
            </Link>
          }
        />
        <Card className="space-y-4">
          <h2 className="text-lg font-medium text-white">No analysis is running yet</h2>
          <p className="text-sm leading-6 text-slate-300">
            Nothing has been preloaded into this UI. Start with a real local path so the swarm can scan code, raise questions, generate reports, and prepare the approval-safe execution plan.
          </p>
        </Card>
      </div>
    );
  }

  const activeProject = projects[0];
  const project = await loadProjectDataset(activeProject.id);
  const pendingApproval = project.approvals.find((approval) => approval.state === "pending");
  const nextWave = project.roadmap.waves[0];
  const openQuestionCount = project.analysisQuestions.filter((question) => question.state !== "answered").length;

  const inferenceBoard = [
    {
      label: "Migration decision",
      title: project.overview.migrationDecision,
      detail: project.overview.narrative,
      confidence: `${Math.round(project.overview.confidence * 100)}% confidence`,
    },
    {
      label: "Provider position",
      title: project.overview.recommendedProvider,
      detail: project.providers[0]?.rationale ?? "The AI already ranked provider fit from the current evidence trail.",
      confidence: `${project.providers[0]?.score ?? 0} score`,
    },
    {
      label: "Preview posture",
      title: project.previewStatus.supported ? "Local preview supported" : "Preview support limited",
      detail: project.previewStatus.summary,
      confidence: project.previewStatus.status,
    },
  ];

  const reportDeck = project.reports.slice(0, 4).map((report) => ({
    title: report.title,
    detail: report.summary,
    confidence: `${Math.round(report.confidence * 100)}% confidence`,
    generatedAt: formatTimestamp(report.generatedAt),
  }));

  const pipelineLinks = [
    { href: `/projects/${project.projectId}`, label: "Open project overview", detail: "Readiness, evidence posture, and executive framing." },
    { href: `/projects/${project.projectId}/findings`, label: "Review findings", detail: "Inspect blockers, recommendations, and evidence citations." },
    { href: `/projects/${project.projectId}/scenarios`, label: "Compare scenarios", detail: "See how the recommendation changes when answers change." },
    { href: `/projects/${project.projectId}/reports`, label: "Open reports", detail: "Move through executive, technical, and planning packs." },
    { href: `/projects/${project.projectId}/approvals`, label: "Manage approvals", detail: "Keep planning and execution behind explicit signoff." },
    { href: `/projects/${project.projectId}/connectors`, label: "Check connectors", detail: "Inspect source state, sync posture, and adapter readiness." },
  ];

  const recentConversation = [...project.chat].slice(-3).reverse();
  const latestEvents = [...project.auditEvents].slice(-3).reverse();
  const otherProjects = dashboard.topProjects.filter((item) => item.id !== project.projectId).slice(0, 2);

  return (
    <div className="space-y-6">
      <SectionHeader
        eyebrow="MTC workbench"
        title="Every MTC interaction now lives inside the dashboard."
        description="The public site sells the product. The local runtime performs the AI work. This surface is where operators answer open questions, inspect inferences, review reports, and move the pipeline forward safely."
        action={
          <Link href={`/projects/${project.projectId}`} className="rounded-full bg-sky-400 px-5 py-3 text-sm font-medium text-slate-950">
            Open active workspace
          </Link>
        }
      />

      <Card className="space-y-5 border-sky-400/20 bg-[linear-gradient(135deg,rgba(56,189,248,0.14),rgba(15,23,42,0.94))]">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div className="max-w-3xl">
            <p className="text-xs uppercase tracking-[0.3em] text-sky-100/75">Active workspace</p>
            <h2 className="mt-2 text-3xl font-semibold text-white">{project.projectName}</h2>
            <p className="mt-2 text-sm leading-6 text-slate-200">{project.overview.businessSummary}</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Badge tone="blue">Local AI runtime</Badge>
            <Badge tone="amber">{`${openQuestionCount} open questions`}</Badge>
            <Badge tone="green">{project.overview.status}</Badge>
          </div>
        </div>

        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          <MetricCard label="Readiness" value={`${project.overview.readinessScore}`} detail="Current project posture for the active workspace." />
          <MetricCard label="Confidence" value={`${Math.round(project.overview.confidence * 100)}%`} detail="How strongly the AI backs the current recommendation." />
          <MetricCard label="Open findings" value={`${dashboard.openFindings}`} detail="Evidence-backed blockers still influencing the plan." />
          <MetricCard
            label="Projected monthly delta"
            value={formatCurrency(project.costModel.currentMonthlyRunRate - project.costModel.targetMonthlyRunRate)}
            detail="Estimated savings opportunity after remediation and migration waves land."
            trend={`${project.costModel.estimatedPaybackMonths} month payback`}
          />
        </div>

        <div className="grid gap-3 lg:grid-cols-2">
          <div className="rounded-3xl border border-white/10 bg-white/[0.05] p-4">
            <p className="text-xs uppercase tracking-[0.24em] text-slate-300">Next wave</p>
            <h3 className="mt-2 text-lg font-medium text-white">{nextWave?.name ?? "Wave planning pending"}</h3>
            <p className="mt-2 text-sm leading-6 text-slate-300">{nextWave?.description ?? "The dashboard is waiting for the next approved planning step."}</p>
          </div>
          <div className="rounded-3xl border border-white/10 bg-white/[0.05] p-4">
            <p className="text-xs uppercase tracking-[0.24em] text-slate-300">Preview status</p>
            <h3 className="mt-2 text-lg font-medium text-white">{project.previewStatus.status}</h3>
            <p className="mt-2 text-sm leading-6 text-slate-300">{project.previewStatus.summary}</p>
          </div>
        </div>
      </Card>

      <div className="grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
        <Card className="space-y-4">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-xs uppercase tracking-[0.28em] text-slate-400">Question queue</p>
              <h2 className="mt-2 text-xl font-medium text-white">Answers the AI is still waiting for</h2>
              <p className="mt-2 text-sm leading-6 text-slate-300">
                Use this lane when the system needs business, compliance, or delivery context before the next report or plan update.
              </p>
            </div>
            <Badge tone="amber">{openQuestionCount}</Badge>
          </div>
          <AnalysisQuestionQueue projectId={project.projectId} questions={project.analysisQuestions} />
        </Card>

        <Card className="space-y-4">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-xs uppercase tracking-[0.28em] text-slate-400">Inference board</p>
              <h2 className="mt-2 text-xl font-medium text-white">What the system believes right now</h2>
            </div>
            <Badge tone="blue">live narrative</Badge>
          </div>
          <div className="grid gap-3">
            {inferenceBoard.map((item) => (
              <div key={item.label} className="rounded-3xl border border-white/10 bg-white/[0.04] p-4">
                <div className="flex items-start justify-between gap-3">
                  <p className="text-xs uppercase tracking-[0.22em] text-slate-400">{item.label}</p>
                  <Badge tone="slate">{item.confidence}</Badge>
                </div>
                <h3 className="mt-2 text-lg font-medium text-white">{item.title}</h3>
                <p className="mt-3 text-sm leading-6 text-slate-300">{item.detail}</p>
              </div>
            ))}
          </div>
        </Card>
      </div>

      <div className="grid gap-4 xl:grid-cols-[1.05fr_0.95fr]">
        <Card className="space-y-4">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-xs uppercase tracking-[0.28em] text-slate-400">Reports ready</p>
              <h2 className="mt-2 text-xl font-medium text-white">Reports are presented like answers, not buried downloads.</h2>
            </div>
            <Badge tone="green">{project.exportFormats.length} export types</Badge>
          </div>
          <div className="grid gap-3 md:grid-cols-2">
            {reportDeck.map((report) => (
              <div key={report.title} className="rounded-3xl border border-white/10 bg-white/[0.04] p-4">
                <div className="flex items-start justify-between gap-3">
                  <h3 className="text-base font-medium text-white">{report.title}</h3>
                  <Badge tone="blue">{report.confidence}</Badge>
                </div>
                <p className="mt-3 text-sm leading-6 text-slate-300">{report.detail}</p>
                <p className="mt-3 text-xs uppercase tracking-[0.22em] text-slate-400">{report.generatedAt}</p>
              </div>
            ))}
          </div>
        </Card>

        <Card className="space-y-4">
          <div>
            <p className="text-xs uppercase tracking-[0.28em] text-slate-400">Pipeline navigation</p>
            <h2 className="mt-2 text-xl font-medium text-white">Move through the MTC pipeline from one surface.</h2>
          </div>
          <div className="grid gap-3">
            {pipelineLinks.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="rounded-3xl border border-white/10 bg-white/[0.04] p-4 transition hover:bg-white/[0.08]"
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h3 className="text-base font-medium text-white">{item.label}</h3>
                    <p className="mt-2 text-sm leading-6 text-slate-300">{item.detail}</p>
                  </div>
                  <Badge tone="slate">open</Badge>
                </div>
              </Link>
            ))}
          </div>
        </Card>
      </div>

      <div className="grid gap-4 xl:grid-cols-[0.92fr_1.08fr]">
        <Card className="space-y-4">
          <div>
            <p className="text-xs uppercase tracking-[0.28em] text-slate-400">Conversation and approvals</p>
            <h2 className="mt-2 text-xl font-medium text-white">People and AI stay in the same loop.</h2>
          </div>
          <div className="space-y-3">
            {recentConversation.map((message) => (
              <div key={message.id} className="rounded-3xl border border-white/10 bg-white/[0.04] p-4">
                <div className="flex items-center justify-between gap-3">
                  <p className="text-sm font-medium text-white">{message.author}</p>
                  <Badge tone={message.role === "ai" ? "blue" : "slate"}>{message.role === "ai" ? "AI response" : "Human input"}</Badge>
                </div>
                <p className="mt-3 text-sm leading-6 text-slate-300">{message.content}</p>
              </div>
            ))}
          </div>
          <div className="rounded-3xl border border-white/10 bg-white/[0.04] p-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-xs uppercase tracking-[0.22em] text-slate-400">Approval center</p>
                <h3 className="mt-2 text-base font-medium text-white">{pendingApproval ? `${pendingApproval.phase} approval pending` : "No pending approval"}</h3>
              </div>
              <Badge tone={pendingApproval ? "amber" : "green"}>{pendingApproval ? "needs signoff" : "clear"}</Badge>
            </div>
            <p className="mt-3 text-sm leading-6 text-slate-300">
              {pendingApproval?.comment ?? "The next pipeline action can continue without an additional approval gate."}
            </p>
          </div>
        </Card>

        <div className="grid gap-4">
          <Card className="space-y-4">
            <div>
              <p className="text-xs uppercase tracking-[0.28em] text-slate-400">Latest system events</p>
              <h2 className="mt-2 text-xl font-medium text-white">Recent pipeline activity</h2>
            </div>
            <div className="space-y-3">
              {latestEvents.map((event) => (
                <div key={event.id} className="rounded-3xl border border-white/10 bg-white/[0.04] p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <h3 className="text-base font-medium text-white">{event.action}</h3>
                      <p className="mt-1 text-xs uppercase tracking-[0.22em] text-slate-400">{event.actor}</p>
                    </div>
                    <Badge tone="slate">{formatTimestamp(event.createdAt)}</Badge>
                  </div>
                </div>
              ))}
            </div>
          </Card>

          <Card className="space-y-4">
            <div>
              <p className="text-xs uppercase tracking-[0.28em] text-slate-400">Other workspaces</p>
              <h2 className="mt-2 text-xl font-medium text-white">Keep the wider portfolio nearby.</h2>
            </div>
            <div className="grid gap-3 md:grid-cols-2">
              {otherProjects.map((item) => (
                <Link
                  key={item.id}
                  href={`/projects/${item.id}`}
                  className="rounded-3xl border border-white/10 bg-white/[0.04] p-4 transition hover:bg-white/[0.08]"
                >
                  <p className="text-xs uppercase tracking-[0.22em] text-slate-400">{item.clientName}</p>
                  <h3 className="mt-2 text-base font-medium text-white">{item.name}</h3>
                  <p className="mt-2 text-sm leading-6 text-slate-300">{item.migrationDecision}</p>
                </Link>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
