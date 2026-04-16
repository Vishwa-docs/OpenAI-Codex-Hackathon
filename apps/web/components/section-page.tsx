import { Badge, Card, EmptyState, MetricCard, PillList, SectionHeader } from "@/components/ui";
import { formatConfidence, formatDate, formatDateTime, formatPercent } from "@/lib/format";
import type {
  ApprovalRecord,
  AuditEvent,
  DependencyEdge,
  DependencyNode,
  Finding,
  ProviderOption,
  Recommendation,
  ReportArtifact,
  Scenario
} from "@contracts/index";
import type { ReactNode } from "react";

export function BulletList({ items }: { items: string[] }) {
  return (
    <div className="space-y-2">
      {items.map((item) => (
        <div key={item} className="rounded-2xl bg-white/5 px-4 py-3 text-sm leading-6 text-slate-300">
          {item}
        </div>
      ))}
    </div>
  );
}

export function EvidenceList({
  evidence,
  title = "Evidence trail"
}: {
  evidence: Array<{
    id: string;
    sourceType: string;
    sourceUri: string;
    excerpt: string;
    locator?: { lineStart?: number; lineEnd?: number };
    confidence: number;
  }>;
  title?: string;
}) {
  return (
    <Card className="space-y-4">
      <div className="flex items-center justify-between gap-4">
        <h3 className="text-lg font-medium text-white">{title}</h3>
        <Badge tone="blue">{evidence.length} refs</Badge>
      </div>
      <div className="space-y-3">
        {evidence.map((item) => (
          <div key={item.id} className="rounded-2xl bg-white/5 p-4">
            <div className="flex flex-wrap items-center gap-2">
              <Badge tone="slate">{item.sourceType}</Badge>
              <span className="text-sm text-slate-300">{item.sourceUri}</span>
            </div>
            <p className="mt-3 text-sm leading-6 text-slate-100">{item.excerpt}</p>
            <p className="mt-2 text-xs uppercase tracking-[0.2em] text-slate-400">
              {item.locator ? `lines ${item.locator.lineStart ?? "?"}-${item.locator.lineEnd ?? "?"}` : "no locator"} · {formatConfidence(item.confidence)}
            </p>
          </div>
        ))}
      </div>
    </Card>
  );
}

export function FindingsList({ findings }: { findings: Finding[] }) {
  return (
    <div className="space-y-4">
      {findings.map((finding) => (
        <Card key={finding.id} className="space-y-3">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-xs uppercase tracking-[0.28em] text-slate-400">{finding.category}</p>
              <h3 className="mt-2 text-lg font-medium text-white">{finding.title}</h3>
            </div>
            <Badge
              tone={finding.severity === "critical" ? "rose" : finding.severity === "high" ? "amber" : "slate"}
            >
              {finding.severity}
            </Badge>
          </div>
          <p className="text-sm leading-6 text-slate-300">{finding.summary}</p>
          <p className="rounded-2xl bg-white/5 px-4 py-3 text-sm leading-6 text-sky-100">{finding.recommendation}</p>
          <EvidenceList evidence={finding.evidence} title="Evidence" />
        </Card>
      ))}
    </div>
  );
}

export function RecommendationList({ recommendations }: { recommendations: Recommendation[] }) {
  return (
    <div className="grid gap-4 xl:grid-cols-2">
      {recommendations.map((item) => (
        <Card key={item.id} className="space-y-4">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-xs uppercase tracking-[0.28em] text-slate-400">Recommendation</p>
              <h3 className="mt-2 text-lg font-medium text-white">{item.title}</h3>
            </div>
            <Badge tone={item.impact === "high" ? "green" : "amber"}>{formatConfidence(item.confidence)}</Badge>
          </div>
          <p className="text-sm leading-6 text-slate-300">{item.summary}</p>
          <p className="rounded-2xl bg-white/5 px-4 py-3 text-sm leading-6 text-slate-100">{item.rationale}</p>
          <div className="flex gap-3 text-sm text-slate-300">
            <span>Effort: {item.effort}</span>
            <span>Impact: {item.impact}</span>
          </div>
        </Card>
      ))}
    </div>
  );
}

export function ProviderCards({ providers }: { providers: ProviderOption[] }) {
  return (
    <div className="grid gap-4 xl:grid-cols-3">
      {providers.map((provider) => (
        <Card key={provider.id} className="space-y-4">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-xs uppercase tracking-[0.28em] text-slate-400">{provider.id}</p>
              <h3 className="mt-2 text-lg font-medium text-white">{provider.name}</h3>
            </div>
            <Badge tone={provider.score > 85 ? "green" : "amber"}>{provider.score}</Badge>
          </div>
          <div className="h-2 rounded-full bg-white/10">
            <div className="h-2 rounded-full bg-sky-400" style={{ width: `${provider.score}%` }} />
          </div>
          <p className="text-sm leading-6 text-slate-300">{provider.bestFor}</p>
          <BulletList items={provider.tradeoffs} />
        </Card>
      ))}
    </div>
  );
}

export function ScenarioCards({ scenarios }: { scenarios: Scenario[] }) {
  return (
    <div className="grid gap-4 xl:grid-cols-3">
      {scenarios.map((scenario) => (
        <Card key={scenario.id} className="space-y-4">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-xs uppercase tracking-[0.28em] text-slate-400">Scenario</p>
              <h3 className="mt-2 text-lg font-medium text-white">{scenario.name}</h3>
            </div>
            <Badge tone="blue">{formatPercent(scenario.outcome.readiness)}</Badge>
          </div>
          <p className="text-sm leading-6 text-slate-300">{scenario.description}</p>
          <BulletList items={scenario.assumptionSet} />
          <div className="rounded-2xl bg-white/5 p-4 text-sm leading-6 text-slate-100">{scenario.outcome.summary}</div>
        </Card>
      ))}
    </div>
  );
}

export function ArtifactCards({ artifacts }: { artifacts: ReportArtifact[] }) {
  return (
    <div className="grid gap-4 lg:grid-cols-2">
      {artifacts.map((artifact) => (
        <Card key={artifact.id} className="space-y-4">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-xs uppercase tracking-[0.28em] text-slate-400">{artifact.kind}</p>
              <h3 className="mt-2 text-lg font-medium text-white">{artifact.title}</h3>
            </div>
            <Badge tone="slate">{artifact.format}</Badge>
          </div>
          <p className="text-sm leading-6 text-slate-300">{artifact.description}</p>
          <p className="text-xs uppercase tracking-[0.22em] text-slate-400">Updated {formatDate(artifact.updatedAt)}</p>
        </Card>
      ))}
    </div>
  );
}

export function ApprovalCards({ approvals }: { approvals: ApprovalRecord[] }) {
  return (
    <div className="space-y-4">
      {approvals.map((approval) => (
        <Card key={approval.id} className="space-y-3">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <p className="text-xs uppercase tracking-[0.28em] text-slate-400">{approval.phase}</p>
              <h3 className="mt-2 text-lg font-medium text-white">Approval {approval.id}</h3>
            </div>
            <Badge
              tone={approval.state === "approved" ? "green" : approval.state === "pending" ? "amber" : "slate"}
            >
              {approval.state}
            </Badge>
          </div>
          <p className="text-sm leading-6 text-slate-300">{approval.comment}</p>
          <div className="flex flex-wrap gap-4 text-sm text-slate-300">
            <span>Requested by {approval.requestedBy}</span>
            {approval.approver ? <span>Approved by {approval.approver}</span> : null}
            {approval.decidedAt ? <span>Decided {formatDateTime(approval.decidedAt)}</span> : null}
          </div>
        </Card>
      ))}
    </div>
  );
}

export function AuditTable({ events }: { events: AuditEvent[] }) {
  return (
    <Card className="overflow-hidden p-0">
      <table className="w-full text-left text-sm">
        <thead className="border-b border-white/10 text-xs uppercase tracking-[0.24em] text-slate-400">
          <tr>
            <th className="px-5 py-4">When</th>
            <th className="px-5 py-4">Actor</th>
            <th className="px-5 py-4">Action</th>
            <th className="px-5 py-4">Target</th>
          </tr>
        </thead>
        <tbody>
          {events.map((event) => (
            <tr key={event.id} className="border-b border-white/5 last:border-none">
              <td className="px-5 py-4 text-slate-300">{formatDateTime(event.createdAt)}</td>
              <td className="px-5 py-4 text-white">{event.actor}</td>
              <td className="px-5 py-4 text-slate-300">{event.action}</td>
              <td className="px-5 py-4 text-slate-300">
                {event.entityType}/{event.entityId}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </Card>
  );
}

export function SectionGrid({ children }: { children: ReactNode }) {
  return <div className="grid gap-4 xl:grid-cols-2">{children}</div>;
}

export function SectionHero({
  title,
  description,
  eyebrow,
  action
}: {
  title: string;
  description: string;
  eyebrow: string;
  action?: ReactNode;
}) {
  return <SectionHeader eyebrow={eyebrow} title={title} description={description} action={action} />;
}

export function EmptySection({
  title,
  description
}: {
  title: string;
  description: string;
}) {
  return <EmptyState title={title} description={description} />;
}
