"use client";

import { useState } from "react";
import Link from "next/link";

import api, { errorMessage } from "@/lib/api";
import type { ConditionResult, CounterfactualResponse } from "@/lib/types";

const SCORERS: Record<string, { label: string; color: string }> = {
  entity_li: { label: "Entity LI (this app)", color: "var(--series-1)" },
  sbert_minilm: { label: "Full-text MiniLM", color: "var(--series-2)" },
  backend_match: { label: "Old app matcher", color: "var(--series-legacy)" },
};

function ShiftBars({ row, max }: { row: ConditionResult; max: number }) {
  // diverging bars around 0, in units of a typical pool's score SD (the paper's normalisation)
  const W = 420, rowH = 22, m = { l: 150, r: 64 };
  const H = row.scores.length * rowH + 4;
  const mid = m.l + (W - m.l - m.r) / 2;
  const half = (W - m.l - m.r) / 2;
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full max-w-xl">
      <line x1={mid} x2={mid} y1={0} y2={H} stroke="var(--axis)" />
      {row.scores.map((s, i) => {
        const y = 2 + i * rowH;
        const w = (Math.min(Math.abs(s.delta_norm), max) / max) * half;
        const x = s.delta_norm >= 0 ? mid : mid - w;
        const meta = SCORERS[s.scorer] ?? { label: s.scorer, color: "var(--muted)" };
        return (
          <g key={s.scorer}>
            <title>{`${meta.label}: ${s.original.toFixed(4)} → ${s.perturbed.toFixed(4)} (Δ ${s.delta.toFixed(4)}, ${s.delta_norm.toFixed(3)} pool SDs)`}</title>
            <text x={m.l - 10} y={y + 14} textAnchor="end" fontSize={11} className="fill-ink-2">
              {meta.label}
            </text>
            <rect x={x} y={y + 4} width={Math.max(w, 1)} height={12} rx={3} fill={meta.color} />
            <text x={W - m.r + 8} y={y + 14} fontSize={11} className="fill-ink tabular">
              {s.delta_norm >= 0 ? "+" : ""}
              {s.delta_norm.toFixed(3)}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

export default function FairnessCheck({ resume, jd }: { resume: string; jd: string }) {
  const [res, setRes] = useState<CounterfactualResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [open, setOpen] = useState<string | null>(null);

  const run = async () => {
    setLoading(true);
    setError("");
    try {
      const r = await api.post("/analysis/counterfactual", { resume_text: resume, jd_text: jd });
      setRes(r.data);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const changed = res?.conditions.filter((c) => c.changed) ?? [];
  const max = Math.max(0.05, ...changed.flatMap((c) => c.scores.map((s) => Math.abs(s.delta_norm))));

  return (
    <section className="rounded-2xl border border-line bg-surface p-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="max-w-2xl">
          <h2 className="text-lg font-semibold">Fairness check on your resume</h2>
          <p className="mt-1 text-sm text-ink-2">
            The paper&apos;s counterfactual audit, run on this resume: we rewrite it (swap pronouns, the first name, or
            agentic wording) and re-score every version with three matchers. A fair matcher shouldn&apos;t move.
          </p>
        </div>
        {!res && (
          <button onClick={run} disabled={loading} className="rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white hover:opacity-90 disabled:opacity-50">
            {loading ? "Running 3 matchers × 7 rewrites…" : "Run fairness check"}
          </button>
        )}
      </div>
      {error && <p className="mt-4 text-sm text-critical">✕ {error}</p>}
      {res && (
        <div className="mt-6 space-y-5">
          <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-ink-2">
            {Object.entries(SCORERS).map(([k, v]) => (
              <span key={k} className="inline-flex items-center gap-1.5">
                <span className="h-2.5 w-2.5 rounded-full" style={{ background: v.color }} />
                {v.label}
              </span>
            ))}
          </div>
          <p className="text-xs text-muted">
            Bars show the score change in units of a typical candidate pool&apos;s score spread (median pool SD on the dev
            split), as in the paper, so matchers with different score scales are comparable. 0.1 means the rewrite
            moved the score by a tenth of the gap between typical candidates.{" "}
            {res.detected_gender
              ? `Subject read as ${res.detected_gender === "F" ? "female" : "male"} from the first name or pronouns; name swaps go to the other gender.`
              : "No gendered first name or pronouns found, so name swaps were skipped."}
            {!res.names_available && " Name lists are not installed on this server, so name swaps are off."}
          </p>
          {res.conditions.map((c) => (
            <div key={c.condition} className="border-t border-line pt-4">
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <h3 className="text-sm font-medium">{c.label}</h3>
                {c.changed ? (
                  <button className="text-xs text-accent-ink hover:underline" onClick={() => setOpen(open === c.condition ? null : c.condition)}>
                    {open === c.condition ? "hide rewritten resume" : `${c.changes.length} change${c.changes.length === 1 ? "" : "s"} · show rewritten resume`}
                  </button>
                ) : (
                  <span className="text-xs text-muted">{c.skipped ?? "nothing to change in this resume"}</span>
                )}
              </div>
              {c.changed && (
                <>
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {c.changes.slice(0, 12).map((ch, i) => (
                      <span key={i} className="rounded-full bg-surface-2 px-2.5 py-0.5 text-xs text-ink-2">
                        {ch.original} → <span className="font-medium text-ink">{ch.replacement}</span>
                      </span>
                    ))}
                    {c.changes.length > 12 && <span className="text-xs text-muted">+{c.changes.length - 12} more</span>}
                  </div>
                  <div className="mt-3">
                    <ShiftBars row={c} max={max} />
                  </div>
                  {open === c.condition && (
                    <pre className="mt-3 max-h-64 overflow-auto whitespace-pre-wrap rounded-lg bg-surface-2 p-3 text-xs text-ink-2">{c.perturbed_text}</pre>
                  )}
                </>
              )}
            </div>
          ))}
          <p className="text-xs text-muted">
            One resume is an anecdote, not evidence: the paper measures these shifts over thousands of bios and 234 job
            pools.{" "}
            <Link href="/research#fairness" className="underline hover:text-ink">
              See the averaged results
            </Link>
            .
          </p>
        </div>
      )}
    </section>
  );
}
