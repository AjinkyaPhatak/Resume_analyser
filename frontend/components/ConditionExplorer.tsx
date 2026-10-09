"use client";

import { useState } from "react";

import { ForestPlot, Legend } from "@/components/charts";
import { FAMILY_COLOR, FAMILY_LABEL, data, type CI } from "@/lib/research";

const METRICS = {
  abs_gap: { label: "|score change|", axis: "mean |score change| in pool SDs (changed bios; lower = less leakage)", zero: false },
  signed_gap: { label: "Direction", axis: "mean signed change in pool SDs (+ favours the female / communal version)", zero: true },
  rank_shift: { label: "Rank shift", axis: "mean |change in rank| within the 100-candidate pool", zero: false },
} as const;
type MetricKey = keyof typeof METRICS;

export default function ConditionExplorer() {
  const [cond, setCond] = useState("gender_full");
  const [metric, setMetric] = useState<MetricKey>("abs_gap");
  const table = data.main[metric];
  const rows = data.scorers
    .map((s) => ({ s, ci: table[s.id]?.[cond] as CI }))
    .filter((r) => r.ci)
    .sort((a, b) => (metric === "signed_gap" ? b.ci![0] - a.ci![0] : a.ci![0] - b.ci![0]))
    .map(({ s, ci }) => ({
      id: s.id,
      label: s.label,
      color: FAMILY_COLOR[s.family],
      ci: ci as [number, number, number],
      emphasis: s.id === "entity_li",
      note: s.description,
    }));
  const cov = data.data.perturbation_coverage.test[cond];
  return (
    <div>
      <div className="flex flex-wrap gap-1.5">
        {data.conditions.map((c) => (
          <button
            key={c.id}
            onClick={() => setCond(c.id)}
            className={`rounded-full border px-3 py-1 text-xs transition ${cond === c.id ? "border-accent bg-accent-wash font-medium text-accent-ink" : "border-line text-ink-2 hover:bg-surface-2"}`}
          >
            {c.label}
          </button>
        ))}
      </div>
      <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
        <div className="flex gap-1 rounded-lg bg-surface-2 p-1">
          {(Object.keys(METRICS) as MetricKey[]).map((k) => (
            <button
              key={k}
              onClick={() => setMetric(k)}
              className={`rounded-md px-3 py-1 text-xs ${metric === k ? "bg-surface font-medium text-ink shadow-sm" : "text-ink-2"}`}
            >
              {METRICS[k].label}
            </button>
          ))}
        </div>
        <span className="text-xs text-muted">This rewrite changes {cov}% of test bios; unchanged bios are excluded.</span>
      </div>
      <div className="mt-4">
        <ForestPlot rows={rows} xLabel={METRICS[metric].axis} zeroLine={METRICS[metric].zero} digits={metric === "rank_shift" ? 2 : 3} />
      </div>
      <Legend items={(["entity", "full-text", "lexical", "legacy"] as const).map((f) => ({ label: FAMILY_LABEL[f], color: FAMILY_COLOR[f] }))} />
    </div>
  );
}
