"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

import FairnessCheck from "@/components/FairnessCheck";
import type { MatchResponse, Requirement, StoredAnalysis } from "@/lib/types";

function ScoreScale({ m }: { m: MatchResponse }) {
  // 0-1 axis with the user's score and the dev-split medians as reference ticks
  const c = m.calibration;
  const pos = (v: number) => `${Math.min(100, Math.max(0, v * 100))}%`;
  const marks = [
    { v: c.irrelevant_median, label: "typical unrelated pair", below: true },
    { v: c.relevant_median, label: "typical same-job pair", below: false },
  ];
  return (
    <div className="relative mt-10 mb-10 h-2 rounded-full bg-surface-2">
      <div className="absolute inset-y-0 left-0 rounded-full bg-accent" style={{ width: pos(m.score) }} />
      {marks.map((k) => (
        <div key={k.label} className="absolute top-1/2 -translate-x-1/2" style={{ left: pos(k.v) }}>
          <div className="mx-auto h-4 w-px -translate-y-1/2 bg-ink-2" />
          <span className={`absolute left-1/2 -translate-x-1/2 whitespace-nowrap text-[11px] text-muted ${k.below ? "top-3" : "-top-8"}`}>
            {k.label} {k.v.toFixed(2)}
          </span>
        </div>
      ))}
      <div className="absolute -top-1 h-4 w-4 -translate-x-1/2 rounded-full border-2 border-surface bg-accent" style={{ left: pos(m.score) }} />
    </div>
  );
}

type SortKey = "lost" | "weight" | "similarity";

function RequirementTable({ rows }: { rows: Requirement[] }) {
  const [sort, setSort] = useState<SortKey>("lost");
  const [all, setAll] = useState(false);
  const sorted = useMemo(() => [...rows].sort((a, b) => (sort === "similarity" ? a.similarity - b.similarity : b[sort] - a[sort])), [rows, sort]);
  const shown = all ? sorted : sorted.slice(0, 12);
  const wmax = Math.max(...rows.map((r) => r.weight));
  const btn = (k: SortKey, label: string) => (
    <button onClick={() => setSort(k)} className={`rounded-md px-2.5 py-1 text-xs ${sort === k ? "bg-accent-wash font-medium text-accent-ink" : "text-ink-2 hover:bg-surface-2"}`}>
      {label}
    </button>
  );
  return (
    <section className="rounded-2xl border border-line bg-surface p-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold">Job requirements and your closest skills</h2>
          <p className="mt-1 text-sm text-ink-2">
            Every skill found in the job description, its weight (rarer, more specific skills count more), and the
            resume skill closest to it. The score is the sum of the contributions.
          </p>
        </div>
        <div className="flex gap-1">
          {btn("lost", "Biggest gaps")}
          {btn("weight", "Most important")}
          {btn("similarity", "Weakest match")}
        </div>
      </div>
      <div className="mt-4 overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-line text-left text-xs text-muted">
              <th className="py-2 pr-3 font-normal">Requirement</th>
              <th className="py-2 pr-3 font-normal">Weight</th>
              <th className="py-2 pr-3 font-normal">Closest resume skill</th>
              <th className="py-2 pr-3 font-normal">Similarity</th>
              <th className="py-2 text-right font-normal">Points lost</th>
            </tr>
          </thead>
          <tbody>
            {shown.map((r) => (
              <tr key={r.skill} className="border-b border-line/60 align-top">
                <td className="py-2 pr-3">
                  <div className="font-medium">{r.skill}</div>
                  <div className="text-[11px] text-muted">{r.found_by.join(" · ")}</div>
                </td>
                <td className="py-2 pr-3">
                  <div className="h-1.5 w-20 rounded-full bg-surface-2">
                    <div className="h-1.5 rounded-full bg-ink-2" style={{ width: `${(r.weight / wmax) * 100}%` }} />
                  </div>
                  <div className="mt-1 text-[11px] text-muted tabular">{(r.weight * 100).toFixed(1)}%</div>
                </td>
                <td className="py-2 pr-3 text-ink-2">{r.best_match ?? "–"}</td>
                <td className="py-2 pr-3">
                  <div className="h-1.5 w-24 rounded-full bg-surface-2">
                    <div className="h-1.5 rounded-full bg-accent" style={{ width: `${Math.max(0, r.similarity) * 100}%` }} />
                  </div>
                  <div className="mt-1 text-[11px] text-muted tabular">{r.similarity.toFixed(2)}</div>
                </td>
                <td className="py-2 text-right tabular text-ink-2">{(r.lost * 100).toFixed(1)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {rows.length > 12 && (
        <button onClick={() => setAll(!all)} className="mt-3 text-sm text-accent-ink hover:underline">
          {all ? "Show fewer" : `Show all ${rows.length} requirements`}
        </button>
      )}
    </section>
  );
}

export default function ResultsPage() {
  const router = useRouter();
  const [a, setA] = useState<StoredAnalysis | null>(null);

  useEffect(() => {
    const stored = sessionStorage.getItem("analysis");
    if (!stored) {
      router.push("/analyse");
      return;
    }
    setA(JSON.parse(stored));
  }, [router]);

  if (!a) return null;
  const { match: m, bias } = a;
  const c = m.calibration;
  const bySource = new Map<string, string[]>();
  m.resume_skills.forEach((s) => s.found_by.forEach((src) => bySource.set(src, [...(bySource.get(src) ?? []), s.skill])));

  return (
    <main className="mx-auto max-w-5xl space-y-6 px-4 py-12">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Results</h1>
        <Link href="/analyse" className="text-sm text-accent-ink hover:underline">
          ← Analyse another
        </Link>
      </div>

      <section className="rounded-2xl border border-line bg-surface p-6">
        <div className="flex flex-wrap items-end justify-between gap-6">
          <div>
            <p className="text-sm text-ink-2">Skill match score</p>
            <p className="mt-1 text-6xl font-semibold tabular">{m.score.toFixed(2)}</p>
          </div>
          <div className="max-w-md text-sm text-ink-2">
            Higher than <span className="font-semibold text-ink tabular">{c.percentile_vs_relevant.toFixed(0)}%</span> of
            same-occupation bio–job pairs and{" "}
            <span className="font-semibold text-ink tabular">{c.percentile_vs_irrelevant.toFixed(0)}%</span> of
            unrelated pairs in the paper&apos;s dev split.
          </div>
        </div>
        <ScoreScale m={m} />
        <p className="text-xs text-muted">
          The score is the weighted average, over the job&apos;s skills, of how close your nearest skill is (cosine
          similarity of JobBERT-v2 embeddings, weight = IDF). It&apos;s not a percentage of skills matched. Reference
          points come from {c.n_relevant.toLocaleString("en-US")} same-job and {c.n_irrelevant.toLocaleString("en-US")} unrelated
          BiasBios pairs; bios are short (≈60 words), so full resumes tend to score higher than bios.
        </p>
        {m.empty_resume && (
          <p className="mt-3 text-sm text-critical">
            ✕ No skills were found in the resume, so the score is 0. Check that the text was extracted correctly.
          </p>
        )}
      </section>

      <RequirementTable rows={m.requirements} />

      <section className="rounded-2xl border border-line bg-surface p-6">
        <h2 className="text-lg font-semibold">Reframing suggestions</h2>
        <p className="mt-1 text-sm text-ink-2">
          Job skills where your resume has a related but different ESCO skill (similarity {m.suggestion_band[0].toFixed(2)}–
          {m.suggestion_band[1].toFixed(2)}). This band was chosen on the dev split because suggestions in it are usually
          the same or neighbouring ESCO concepts. The old band (0.35–0.55) was no better than chance.
        </p>
        {m.suggestions.length === 0 ? (
          <p className="mt-4 text-sm text-muted">No near-misses found.</p>
        ) : (
          <ul className="mt-4 space-y-2">
            {m.suggestions.map((s) => (
              <li key={s.jd_concept} className="rounded-lg bg-surface-2 px-4 py-2.5 text-sm">
                Your <span className="font-medium">“{s.resume_phrase}”</span> is close to the job&apos;s{" "}
                <span className="font-medium">“{s.jd_skill}”</span>. Consider naming it the way the posting does.{" "}
                <span className="text-xs text-muted tabular">({s.similarity.toFixed(2)})</span>
              </li>
            ))}
          </ul>
        )}
      </section>

      <FairnessCheck resume={a.resume_text} jd={a.jd_text} />

      <section className="rounded-2xl border border-line bg-surface p-6">
        <h2 className="text-lg font-semibold">What the matcher read from your resume</h2>
        <p className="mt-1 text-sm text-ink-2">
          Only these {m.resume_skills.length} entities are compared with the job. Everything else, including most of
          your name, pronouns and wording, never reaches the score. Noun phrases can still let a name through; the
          fairness check shows whether that moves anything.
        </p>
        <div className="mt-4 space-y-3">
          {[...bySource.entries()].map(([src, skills]) => (
            <div key={src}>
              <p className="mb-1.5 text-xs text-muted">{src}</p>
              <div className="flex flex-wrap gap-1.5">
                {skills.map((s) => (
                  <span key={s} className="rounded-full bg-surface-2 px-2.5 py-0.5 text-xs text-ink-2">
                    {s}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="rounded-2xl border border-line bg-surface p-6">
        <h2 className="text-lg font-semibold">Gender-coded wording in the job description</h2>
        <p className="mt-2 text-sm font-medium">{bias.verdict}</p>
        <p className="mt-1 text-xs text-muted tabular">
          {bias.masculine_count} masculine-coded and {bias.feminine_count} feminine-coded words in {bias.n_words}; score{" "}
          {bias.bias_score} per 100 words (positive = masculine-leaning). Word lists adapted from Gaucher et al. (2011),
          not yet checked word-by-word against the paper.
        </p>
        {bias.flagged_words.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-1.5">
            {bias.flagged_words.map((w, i) => (
              <span key={i} className="rounded-full border border-line px-2.5 py-0.5 text-xs text-ink-2">
                <span aria-hidden>{w.type === "masculine-coded" ? "♂ " : "♀ "}</span>
                {w.word}
                <span className="sr-only"> ({w.type})</span>
              </span>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}
