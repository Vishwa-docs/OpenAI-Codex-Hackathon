import type { DependencyEdge, DependencyNode, ProviderOption, Scenario } from "@contracts/index";
import { Badge, Card } from "@/components/ui";
import { formatConfidence, formatPercent } from "@/lib/format";

export function ReadinessGauge({
  readiness,
  confidence,
  decision
}: {
  readiness: number;
  confidence: number;
  decision: string;
}) {
  const radius = 62;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (readiness / 100) * circumference;

  return (
    <Card className="flex items-center gap-5">
      <svg viewBox="0 0 160 160" className="h-36 w-36 shrink-0">
        <circle cx="80" cy="80" r={radius} stroke="rgba(255,255,255,0.08)" strokeWidth="14" fill="none" />
        <circle
          cx="80"
          cy="80"
          r={radius}
          stroke="url(#readinessGradient)"
          strokeWidth="14"
          strokeLinecap="round"
          fill="none"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          transform="rotate(-90 80 80)"
        />
        <defs>
          <linearGradient id="readinessGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#7dd3fc" />
            <stop offset="100%" stopColor="#38bdf8" />
          </linearGradient>
        </defs>
        <text x="80" y="76" textAnchor="middle" className="fill-white text-[30px] font-semibold">
          {formatPercent(readiness)}
        </text>
        <text x="80" y="98" textAnchor="middle" className="fill-slate-300 text-[12px] uppercase tracking-[0.3em]">
          readiness
        </text>
      </svg>
      <div>
        <Badge tone="amber">{decision}</Badge>
        <p className="mt-3 max-w-sm text-sm leading-6 text-slate-300">
          {formatConfidence(confidence)}. The cockpit keeps the recommendation grounded in evidence and flags unsafe shortcuts.
        </p>
      </div>
    </Card>
  );
}

export function ProviderComparison({
  providers
}: {
  providers: ProviderOption[];
}) {
  return (
    <div className="grid gap-4 xl:grid-cols-3">
      {providers.map((provider) => (
        <Card key={provider.id} className="space-y-4">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-xs uppercase tracking-[0.28em] text-slate-400">{provider.id}</p>
              <h3 className="mt-2 text-lg font-medium text-white">{provider.name}</h3>
            </div>
            <Badge tone={provider.score > 85 ? "green" : provider.score > 75 ? "amber" : "slate"}>{provider.score}</Badge>
          </div>
          <p className="text-sm leading-6 text-slate-300">{provider.bestFor}</p>
          <div className="space-y-2">
            {provider.tradeoffs.map((tradeoff) => (
              <div key={tradeoff} className="rounded-2xl bg-white/5 px-3 py-2 text-sm text-slate-300">
                {tradeoff}
              </div>
            ))}
          </div>
        </Card>
      ))}
    </div>
  );
}

export function ScenarioComparison({
  scenarios
}: {
  scenarios: Scenario[];
}) {
  return (
    <div className="grid gap-4 xl:grid-cols-3">
      {scenarios.map((scenario, index) => (
        <Card key={scenario.id} className={index === 2 ? "border-sky-400/30 bg-sky-400/8" : ""}>
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-xs uppercase tracking-[0.28em] text-slate-400">Scenario</p>
              <h3 className="mt-2 text-lg font-medium text-white">{scenario.name}</h3>
            </div>
            <Badge tone={index === 2 ? "green" : "slate"}>{formatPercent(scenario.outcome.readiness)}</Badge>
          </div>
          <p className="mt-3 text-sm leading-6 text-slate-300">{scenario.description}</p>
          <p className="mt-3 rounded-2xl bg-white/5 px-3 py-2 text-sm text-sky-100">{scenario.outcome.summary}</p>
          <div className="mt-4 space-y-2 text-sm text-slate-300">
            <div>Risk: {scenario.outcome.riskDelta}</div>
            <div>Cost: {scenario.outcome.costDelta}</div>
          </div>
        </Card>
      ))}
    </div>
  );
}

export function DependencyGraph({
  nodes,
  edges
}: {
  nodes: DependencyNode[];
  edges: DependencyEdge[];
}) {
  const nodeMap = new Map(nodes.map((node) => [node.id, node]));

  return (
    <Card className="overflow-hidden">
      <div className="mb-4 flex items-center justify-between gap-4">
        <div>
          <h3 className="text-lg font-medium text-white">Dependency graph</h3>
          <p className="mt-1 text-sm text-slate-300">Read-only topology extracted from the project evidence graph.</p>
        </div>
        <Badge tone="blue">{nodes.length} nodes</Badge>
      </div>
      <svg viewBox="0 0 720 360" className="h-[360px] w-full">
        <defs>
          <marker id="graphArrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto">
            <path d="M0,0 L0,6 L9,3 z" fill="rgba(96,165,250,0.85)" />
          </marker>
        </defs>
        {edges.map((edge) => {
          const source = nodeMap.get(edge.source);
          const target = nodeMap.get(edge.target);
          if (!source || !target) return null;
          return (
            <line
              key={edge.id}
              x1={source.x + 92}
              y1={source.y + 32}
              x2={target.x}
              y2={target.y + 32}
              stroke="rgba(125,211,252,0.8)"
              strokeWidth="2"
              markerEnd="url(#graphArrow)"
            />
          );
        })}
        {nodes.map((node) => (
          <g key={node.id} transform={`translate(${node.x}, ${node.y})`}>
            <rect
              rx="18"
              ry="18"
              width="184"
              height="64"
              fill={node.status === "at_risk" ? "rgba(239,68,68,0.2)" : "rgba(255,255,255,0.08)"}
              stroke={node.status === "at_risk" ? "rgba(248,113,113,0.6)" : "rgba(255,255,255,0.12)"}
            />
            <text x="18" y="28" fill="white" fontSize="14" fontWeight="600">
              {node.label}
            </text>
            <text x="18" y="46" fill="rgba(226,232,240,0.8)" fontSize="11" letterSpacing="1.8">
              {node.kind.toUpperCase()}
            </text>
          </g>
        ))}
      </svg>
    </Card>
  );
}

export function EvaluationPanel({
  checks,
  overallScore
}: {
  checks: Array<{ name: string; score: number; note: string }>;
  overallScore: number;
}) {
  return (
    <Card>
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.28em] text-slate-400">Evals</p>
          <h3 className="mt-2 text-lg font-medium text-white">Assessment quality</h3>
        </div>
        <Badge tone={overallScore > 85 ? "green" : "amber"}>{overallScore}</Badge>
      </div>
      <div className="mt-4 space-y-3">
        {checks.map((check) => (
          <div key={check.name} className="rounded-2xl bg-white/5 p-3">
            <div className="flex items-center justify-between gap-4">
              <span className="text-sm font-medium text-white">{check.name}</span>
              <span className="text-sm text-slate-300">{check.score}</span>
            </div>
            <p className="mt-1 text-sm leading-6 text-slate-300">{check.note}</p>
          </div>
        ))}
      </div>
    </Card>
  );
}
