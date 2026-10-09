import Link from "next/link";

import { data } from "@/lib/research";

const gap = (id: string) => data.main.abs_gap[id].gender_full![0];
const ndcg = (id: string) => data.main.ranking[id]["ndcg@10"]![0];

const STEPS = [
  {
    n: "1",
    title: "Extract skills",
    body: "A JobBERT tagger fine-tuned on SkillSpan, the ESCO skills taxonomy and filtered noun phrases pull skill and knowledge entities out of both texts. Names, pronouns and most demographic wording never become entities.",
  },
  {
    n: "2",
    title: "Match skill to skill",
    body: "Each job requirement is paired with its closest resume skill (JobBERT-v2 embeddings, MaxSim late interaction as in ColBERT and BERTScore), weighted by how specific the requirement is (IDF).",
  },
  {
    n: "3",
    title: "Check what moves the score",
    body: "Run the same counterfactual audit as the paper on your own resume: swap pronouns, names or wording and see how much each matcher's score shifts.",
  },
];

export default function Home() {
  return (
    <main className="mx-auto max-w-6xl px-4">
      <section className="py-16 md:py-24">
        <p className="mb-4 text-sm font-medium text-accent-ink">Entity-level resume matching · counterfactual fairness audit</p>
        <h1 className="max-w-3xl text-4xl font-bold tracking-tight md:text-5xl">
          Match a resume on its skills, not on who wrote it.
        </h1>
        <p className="mt-5 max-w-2xl text-lg text-ink-2">
          Most semantic matchers embed the whole resume, so a name or a pronoun can move the score. This analyser
          compares extracted skills only, and lets you test that claim on your own resume.
        </p>
        <div className="mt-8 flex flex-wrap gap-3">
          <Link href="/analyse" className="rounded-lg bg-accent px-5 py-3 font-medium text-white transition hover:opacity-90">
            Analyse a resume
          </Link>
          <Link href="/research" className="rounded-lg border border-line px-5 py-3 font-medium text-ink transition hover:bg-surface-2">
            Read the research
          </Link>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        <div className="rounded-xl border border-line bg-surface p-5">
          <p className="text-sm text-ink-2">Score shift under a full gender flip</p>
          <p className="mt-2 text-4xl font-semibold tabular">{gap("entity_li").toFixed(3)}</p>
          <p className="mt-2 text-sm text-ink-2">
            vs {gap("jobbert_v2").toFixed(3)}–{gap("sbert_minilm").toFixed(3)} for full-text neural matchers and{" "}
            {gap("backend_match").toFixed(3)} for this app&apos;s old matcher (in pool SDs; lower is better).
          </p>
        </div>
        <div className="rounded-xl border border-line bg-surface p-5">
          <p className="text-sm text-ink-2">Ranking accuracy (nDCG@10)</p>
          <p className="mt-2 text-4xl font-semibold tabular">{ndcg("entity_li").toFixed(3)}</p>
          <p className="mt-2 text-sm text-ink-2">
            Above MiniLM ({ndcg("sbert_minilm").toFixed(3)}) and BM25 ({ndcg("bm25").toFixed(3)}), below full-text
            JobBERT-v2 ({ndcg("jobbert_v2").toFixed(3)}).
          </p>
        </div>
        <div className="rounded-xl border border-line bg-surface p-5">
          <p className="text-sm text-ink-2">Evaluation</p>
          <p className="mt-2 text-4xl font-semibold tabular">{data.data.pools.test}</p>
          <p className="mt-2 text-sm text-ink-2">
            held-out job-description pools of {data.data.pool_size} BiasBios candidates each, with 7 counterfactual
            perturbations and paired significance tests.
          </p>
        </div>
      </section>
      <p className="mt-3 text-sm text-muted">
        The honest caveat: word-count matchers (BM25, TF-IDF) shift even less, because they ignore pronouns by
        construction, but they rank worse. Details on the{" "}
        <Link href="/research" className="underline hover:text-ink">
          research page
        </Link>
        .
      </p>

      <section className="mt-20">
        <h2 className="text-2xl font-semibold">How it works</h2>
        <div className="mt-6 grid gap-4 md:grid-cols-3">
          {STEPS.map((s) => (
            <div key={s.n} className="rounded-xl border border-line bg-surface p-5">
              <span className="inline-flex h-7 w-7 items-center justify-center rounded-full bg-accent-wash text-sm font-semibold text-accent-ink">
                {s.n}
              </span>
              <h3 className="mt-3 font-semibold">{s.title}</h3>
              <p className="mt-2 text-sm text-ink-2">{s.body}</p>
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}
