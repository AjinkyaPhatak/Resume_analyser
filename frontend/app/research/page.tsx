import type { Metadata } from "next";
import type { ReactNode } from "react";

import ConditionExplorer from "@/components/ConditionExplorer";
import { BandHeatmap, ForestPlot, HBars, Legend, LineChart, ScatterCI, type ScatterPoint } from "@/components/charts";
import { FAMILY_COLOR, FAMILY_LABEL, ciText, condLabel, data, f3, pText, scorer } from "@/lib/research";

export const metadata: Metadata = {
  title: "Research · Resume Analyser",
  description: "Do entity-level resume matchers leak less demographic signal? A counterfactual fairness audit.",
};

const M = data.main;
const OURS = "entity_li";
const ndcg = (id: string) => M.ranking[id]["ndcg@10"]!;
const ggap = (id: string) => M.abs_gap[id].gender_full!;

const TOC = [
  ["question", "The question"],
  ["method", "Method"],
  ["data", "Data and counterfactuals"],
  ["extraction", "Skill extraction and training"],
  ["headline", "Headline result"],
  ["fairness", "Every perturbation"],
  ["significance", "Significance"],
  ["accuracy", "Ranking accuracy"],
  ["more-fairness", "Other fairness metrics"],
  ["heldout", "Held-out check"],
  ["ablations", "Ablations"],
  ["selection", "Choosing the final method"],
  ["nearmiss", "Suggestion band"],
  ["figures", "Paper figures"],
  ["limitations", "Limitations"],
  ["reproduce", "Reproduce"],
];

function Section({ id, title, kicker, children }: { id: string; title: string; kicker?: string; children: ReactNode }) {
  return (
    <section id={id} className="scroll-mt-20 border-t border-line pt-10">
      {kicker && <p className="text-xs font-medium uppercase tracking-wide text-accent-ink">{kicker}</p>}
      <h2 className="mt-1 text-2xl font-semibold tracking-tight">{title}</h2>
      <div className="mt-4 space-y-4 text-[15px] leading-relaxed text-ink-2">{children}</div>
    </section>
  );
}

function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <div className={`rounded-xl border border-line bg-surface p-5 ${className}`}>{children}</div>;
}

function Stat({ value, label }: { value: string; label: string }) {
  return (
    <div className="rounded-xl border border-line bg-surface p-4">
      <p className="text-2xl font-semibold text-ink tabular">{value}</p>
      <p className="mt-1 text-xs text-ink-2">{label}</p>
    </div>
  );
}

const th = "py-2 pr-4 text-left text-xs font-normal text-muted";
const td = "py-2 pr-4 tabular";

function FamilyLegend() {
  return <Legend items={(["entity", "full-text", "lexical", "legacy"] as const).map((f) => ({ label: FAMILY_LABEL[f], color: FAMILY_COLOR[f] }))} />;
}

function Pipeline() {
  const box = "rounded-lg border border-line bg-surface px-3 py-2 text-center text-xs text-ink";
  const arrow = <span className="text-muted">→</span>;
  return (
    <div className="flex flex-wrap items-center gap-2">
      <div className={box}>
        Resume
        <br />
        Job description
      </div>
      {arrow}
      <div className="rounded-lg border border-accent bg-accent-wash px-3 py-2 text-xs text-accent-ink">
        <p className="font-semibold">Extract entities (union)</p>
        <p>Fine-tuned JobBERT tagger</p>
        <p>ESCO EntityRuler</p>
        <p>Filtered noun chunks</p>
      </div>
      {arrow}
      <div className={box}>
        Keep skill +<br />
        knowledge spans
      </div>
      {arrow}
      <div className={box}>
        JobBERT-v2
        <br />
        entity embeddings
      </div>
      {arrow}
      <div className={box}>
        JD × resume
        <br />
        cosine matrix
      </div>
      {arrow}
      <div className={box}>
        IDF-weighted
        <br />
        MaxSim → score
      </div>
    </div>
  );
}

export default function ResearchPage() {
  const scorers = data.scorers;
  const best = scorers.reduce((a, b) => (ndcg(a.id)[0] > ndcg(b.id)[0] ? a : b));
  const neural = scorers.filter((s) => s.family === "full-text");
  const lexical = scorers.filter((s) => s.family === "lexical");

  // --- headline scatter
  const labelPos: Record<string, ScatterPoint["labelPos"]> = { tfidf: "left", bm25: "above", entity_li: "right", sbert_minilm: "above" };
  const points: ScatterPoint[] = scorers.map((s) => ({
    id: s.id,
    label: s.label,
    color: FAMILY_COLOR[s.family],
    x: ndcg(s.id) as [number, number, number],
    y: ggap(s.id) as [number, number, number],
    emphasis: s.id === OURS,
    labelPos: labelPos[s.id],
    detail: <div className="mt-1 max-w-56 text-muted">{s.description}</div>,
  }));
  const xs = points.flatMap((p) => [p.x[1], p.x[2]]);
  const ys = points.flatMap((p) => [p.y[2]]);

  // --- extraction
  const ex = data.extraction.rows.filter((r) => r.split === "test");
  const exNames: [string, string][] = [
    ["noun_chunk", "Noun chunks (old app)"],
    ["filtered_nc", "Filtered noun chunks"],
    ["esco", "ESCO EntityRuler"],
    ["esco+nc", "ESCO + noun chunks"],
    ["jobbert_ft_s13", "JobBERT fine-tuned, seed 13"],
    ["jobbert_ft_s14", "JobBERT fine-tuned, seed 14"],
    ["jobbert_ft_s15", "JobBERT fine-tuned, seed 15"],
  ];
  const exRows = exNames.map(([id, label]) => ({
    id,
    label,
    emphasis: id === "jobbert_ft_s13",
    values: [
      { key: "exact-match F1", value: ex.find((r) => r.extractor === id && r.mode === "exact")!.f1, color: "var(--series-1)" },
      { key: "partial-match F1", value: ex.find((r) => r.extractor === id && r.mode === "partial")!.f1, color: "var(--series-2)" },
    ],
  }));
  const seeds = Object.keys(data.training.seeds);
  const seedColors = ["var(--series-1)", "var(--series-2)", "var(--series-3)"];
  const bestEpoch = Object.fromEntries(
    seeds.map((s) => [s, data.training.seeds[s].reduce((a, b) => (b.dev_exact_f1 > a.dev_exact_f1 ? b : a)).epoch]),
  );
  const ftTest = seeds.map((s) => ex.find((r) => r.extractor === `jobbert_ft_s${s}` && r.mode === "exact")!.f1);
  const ftMean = ftTest.reduce((a, b) => a + b, 0) / ftTest.length;

  // --- data
  const cov = data.data.perturbation_coverage.test;
  const occ = Object.entries(data.data.jds_per_occupation);

  // --- significance
  const sig = (metric: string, cond: string) => M.tests.filter((t) => t.metric === metric && t.condition === cond);

  const nm = data.nearmiss.bands;

  return (
    <main className="mx-auto max-w-6xl px-4 py-12">
      <div className="lg:grid lg:grid-cols-[200px_1fr] lg:gap-10">
        <aside className="hidden lg:block">
          <nav className="sticky top-20 space-y-1 text-sm">
            {TOC.map(([id, label]) => (
              <a key={id} href={`#${id}`} className="block rounded px-2 py-1 text-ink-2 hover:bg-surface-2 hover:text-ink">
                {label}
              </a>
            ))}
          </nav>
        </aside>

        <article className="min-w-0 space-y-12">
          <header>
            <p className="text-sm font-medium text-accent-ink">Research</p>
            <h1 className="mt-2 text-3xl font-bold tracking-tight md:text-4xl">
              Do entity-level resume matchers leak less demographic signal?
            </h1>
            <p className="mt-3 text-lg text-ink-2">A counterfactual fairness audit of semantic resume–job matching.</p>
            <Card className="mt-6 border-accent">
              <p className="text-sm font-semibold text-ink">Short answer</p>
              <p className="mt-2 text-[15px] text-ink-2">
                <span className="font-medium text-ink">Yes, compared with full-text neural matchers.</span> When a candidate&apos;s
                pronouns and first name are flipped to the other gender, the entity-level matcher&apos;s score moves by{" "}
                {ggap(OURS)[0].toFixed(3)} pool SDs, against {Math.min(...neural.map((s) => ggap(s.id)[0])).toFixed(3)}–
                {Math.max(...neural.map((s) => ggap(s.id)[0])).toFixed(3)} for the neural full-text matchers (Holm-corrected
                p &lt; 0.001 for every one). Its ranking accuracy (nDCG@10 {ndcg(OURS)[0].toFixed(3)}) is competitive but not
                the best: full-text {best.label} reaches {ndcg(best.id)[0].toFixed(3)}.{" "}
                <span className="font-medium text-ink">No, compared with word-count matchers:</span> BM25 and TF-IDF move
                even less ({lexical.map((s) => ggap(s.id)[0].toFixed(3)).join(" and ")}) because pronouns are stop-words for
                them, but they rank worse.
              </p>
            </Card>
            <div className="mt-4 grid grid-cols-2 gap-3 md:grid-cols-4">
              <Stat value={data.data.pools.test.toString()} label="test job pools (100 candidates each)" />
              <Stat value={`${scorers.length}`} label="matchers compared" />
              <Stat value={`${data.conditions.length}`} label="counterfactual rewrites" />
              <Stat value={(data.data.bios.train + data.data.bios.dev + data.data.bios.test).toLocaleString("en-US")} label="BiasBios bios after cleaning" />
            </div>
          </header>

          <Section id="question" title="The question" kicker="Motivation">
            <p>
              Semantic resume matchers usually embed the whole resume and the whole job description and compare the two
              vectors. Everything in the text goes into that vector: the skills, but also the candidate&apos;s name, their
              pronouns, the clubs they belonged to, and how assertively they describe their work. If any of that shifts the
              vector, it shifts the match score.
            </p>
            <p>
              The alternative tested here extracts the skills first and compares skill to skill. Our hypothesis:{" "}
              <span className="text-ink">
                restricting the comparison to extracted skill entities keeps demographic cues out of the score, at
                competitive ranking accuracy.
              </span>{" "}
              The matching step is late interaction (MaxSim), as in ColBERT (Khattab &amp; Zaharia, 2020) and BERTScore
              (Zhang et al., 2020). That mechanism isn&apos;t new and we don&apos;t claim it. The contribution is the
              fairness audit and the entity-restriction hypothesis.
            </p>
          </Section>

          <Section id="method" title="Method" kicker="What the app runs">
            <Pipeline />
            <p>
              For every skill in the job description, the matcher finds the most similar skill on the resume (cosine
              similarity of JobBERT-v2 embeddings). The score is the average of those best similarities, with rarer, more
              specific job skills weighted more (IDF over the {data.data.n_jds} job descriptions). The analyser on this
              site runs exactly this code, imported from the research package. A test checks that its score equals the
              research scorer&apos;s.
            </p>
            <p>The audit compares it with seven other matchers, run through the same harness:</p>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-line">
                    <th className={th}>Matcher</th>
                    <th className={th}>Family</th>
                    <th className={th}>What it compares</th>
                  </tr>
                </thead>
                <tbody>
                  {scorers.map((s) => (
                    <tr key={s.id} className="border-b border-line/60">
                      <td className="py-2 pr-4 font-medium text-ink">
                        <span className="mr-2 inline-block h-2.5 w-2.5 rounded-full" style={{ background: FAMILY_COLOR[s.family] }} />
                        {s.label}
                      </td>
                      <td className="py-2 pr-4">{FAMILY_LABEL[s.family]}</td>
                      <td className="py-2 pr-4">{s.description}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Section>

          <Section id="data" title="Data and counterfactuals" kicker="Setup">
            <p>
              <span className="text-ink">Candidates</span> are BiasBios biographies (De-Arteaga et al., 2019): short
              third-person professional bios labelled with one of 28 occupations and a binary gender. We kept the official
              splits and removed duplicates and dev/test bios that also appear in an earlier split.{" "}
              <span className="text-ink">Jobs</span> are LinkedIn postings (Kaggle, CC BY-SA 4.0), mapped to the BiasBios
              occupations by title. {data.data.n_occupations_with_pools} of the {data.data.n_occupations_total} occupations
              had enough postings to build pools.
            </p>
            <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
              <Stat value={data.data.bios.train.toLocaleString("en-US")} label="train bios (IDF and lexical statistics only)" />
              <Stat value={data.data.bios.dev.toLocaleString("en-US")} label="dev bios" />
              <Stat value={data.data.bios.test.toLocaleString("en-US")} label="test bios" />
              <Stat value={`${data.data.n_jds}`} label={`job descriptions (mean ${data.data.jd_mean_words} words)`} />
            </div>
            <p>
              Each job description gets a <span className="text-ink">pool</span> of {data.data.pool_size} candidates:{" "}
              {data.data.relevant_per_pool} from the same occupation (5 women, 5 men) and 90 from other occupations (45/45).
              Relevance is graded: 2 for the same occupation, 1 for the same SOC major group, 0 otherwise. Pools are split
              by job into {data.data.pools.dev} dev pools, used for every choice, and {data.data.pools.test} test pools, used
              only for reporting.
            </p>
            <Card>
              <p className="text-sm font-medium text-ink">Job descriptions per occupation</p>
              <div className="mt-3 flex flex-wrap gap-1.5">
                {occ.map(([o, n]) => (
                  <span key={o} className="rounded-full bg-surface-2 px-2.5 py-0.5 text-xs text-ink-2 tabular">
                    {o.replace(/_/g, " ")} · {n}
                  </span>
                ))}
              </div>
            </Card>
            <p>
              <span className="text-ink">Counterfactuals.</span> Each pooled bio is rewritten seven ways, and every
              substitution is logged. Names come from US Social Security counts and Wikidata given names of Indian citizens.
              A name is swapped only if it is strongly gendered (≥ 95%) and belongs to the bio&apos;s subject. Rewrites that
              don&apos;t apply leave the bio unchanged, so coverage differs a lot between them:
            </p>
            <HBars
              rows={data.conditions.map((c) => ({ id: c.id, label: c.label, values: [{ key: "% of test bios changed", value: cov[c.id], color: "var(--series-1)" }] }))}
              xLabel="% of pooled test bios the rewrite changes"
              max={100}
              digits={1}
            />
            <Card>
              <p className="text-sm font-medium text-ink">Examples from the dev split (rewritten text, substitutions highlighted)</p>
              <div className="mt-3 space-y-3">
                {data.examples.map((e, i) => (
                  <div key={i} className="text-sm">
                    <span className="mr-2 rounded bg-surface-2 px-1.5 py-0.5 text-[11px] text-muted">{condLabel(e.condition)}</span>
                    {e.changes.map((c, j) => (
                      <span key={j} className="mr-1.5 text-xs text-ink-2">
                        {c.from} → <span className="font-medium text-ink">{c.to}</span>
                      </span>
                    ))}
                    <p className="mt-1 text-xs leading-relaxed text-muted">{e.context}</p>
                  </div>
                ))}
              </div>
            </Card>
          </Section>

          <Section id="extraction" title="Skill extraction and training" kicker="Phase 1">
            <p>
              Extractors were evaluated on SkillSpan (Zhang et al., 2022), job postings annotated with skill and knowledge
              spans. Rule-based extractors stay below 0.2 exact-match F1. We fine-tuned JobBERT ({data.training.base_model})
              as a token classifier with one BIO head per SkillSpan layer, three seeds, keeping the epoch with the best{" "}
              {data.training.select_on}. Test exact F1 averages {ftMean.toFixed(3)} over the three seeds.
            </p>
            <Legend items={[{ label: "exact-match F1", color: "var(--series-1)" }, { label: "partial-match F1", color: "var(--series-2)" }]} />
            <HBars rows={exRows} xLabel="SkillSpan test F1" max={1} />
            <p>
              Training curves: dev exact F1 per epoch (learning rate {data.training.lr}, batch {data.training.batch_size}, up
              to {data.training.max_epochs} epochs, early stopping after {data.training.patience} without improvement; fp16 on
              an RTX 2060). Circles mark the kept epoch. The app uses seed 13.
            </p>
            <LineChart
              series={seeds.map((s, i) => ({
                id: s,
                label: `seed ${s}`,
                color: seedColors[i],
                points: data.training.seeds[s].map((h) => ({ x: h.epoch, y: h.dev_exact_f1 })),
              }))}
              markX={bestEpoch}
              xLabel="epoch"
              yLabel="dev exact span F1"
            />
            <LineChart
              series={seeds.map((s, i) => ({
                id: s,
                label: `seed ${s}`,
                color: seedColors[i],
                points: data.training.seeds[s].map((h) => ({ x: h.epoch, y: h.train_loss })),
              }))}
              xLabel="epoch"
              yLabel="training loss"
              yDomain={[0, Math.max(...seeds.flatMap((s) => data.training.seeds[s].map((h) => h.train_loss)))]}
            />
          </Section>

          <Section id="headline" title="Headline result" kicker="Accuracy vs leakage, 234 test pools">
            <p>
              Each matcher is placed by ranking accuracy (right is better) and by how much its scores move under the full
              gender flip, i.e. pronouns plus first name (down is better). Bars are 95% cluster-bootstrap confidence
              intervals over job pools. Hover a point for details.
            </p>
            <FamilyLegend />
            <ScatterCI
              points={points}
              xLabel="nDCG@10 (ranking accuracy)"
              yLabel="|score change|, gender flip (pool SDs)"
              xDomain={[Math.floor(Math.min(...xs) * 20) / 20, Math.ceil(Math.max(...xs) * 20) / 20]}
              yDomain={[-0.01, Math.ceil(Math.max(...ys) * 20) / 20]}
            />
            <p>
              Score changes are divided by the standard deviation of the pool&apos;s original scores, because matchers use
              different scales. A value of 0.1 means flipping gender moves a candidate by a tenth of the typical spread
              between candidates for that job. Only bios the rewrite actually changed are counted.
            </p>
          </Section>

          <Section id="fairness" title="Every perturbation" kicker="Counterfactual gaps">
            <p>
              Pick a rewrite. On every gender rewrite the entity matcher moves less than every full-text neural matcher. The
              agentic→communal rewrite (for example &ldquo;led&rdquo; → &ldquo;supported&rdquo;) moves all matchers by similar
              amounts, because those words are partly skills themselves; it touches only {cov.agentic_communal}% of bios.
            </p>
            <ConditionExplorer />
          </Section>

          <Section id="significance" title="Significance" kicker="Paired permutation tests over pools">
            <p>
              Our matcher against each baseline: mean per-pool difference (ours − baseline), with two-sided sign-flip
              permutation tests over the {data.data.pools.test} test pools, Holm-corrected within each metric family.
            </p>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-line">
                    <th className={th}>Baseline</th>
                    <th className={th}>Δ |gap|, full gender flip</th>
                    <th className={th}>Holm p</th>
                    <th className={th}>Δ nDCG@10</th>
                    <th className={th}>Holm p</th>
                  </tr>
                </thead>
                <tbody>
                  {sig("abs_gap_norm_changed", "gender_full").map((t) => {
                    const acc = sig("ndcg@10", "original").find((a) => a.baseline === t.baseline);
                    return (
                      <tr key={t.baseline} className="border-b border-line/60">
                        <td className="py-2 pr-4 font-medium text-ink">{scorer(t.baseline).label}</td>
                        <td className={`${td} ${t.mean_diff < 0 ? "text-good" : "text-critical"}`}>
                          {t.mean_diff < 0 ? "▼ " : "▲ "}
                          {t.mean_diff.toFixed(3)}
                        </td>
                        <td className={td}>{pText(t.p_holm)}</td>
                        <td className={`${td} ${acc && acc.mean_diff > 0 ? "text-good" : "text-critical"}`}>
                          {acc ? `${acc.mean_diff > 0 ? "▲ " : "▼ "}${acc.mean_diff.toFixed(3)}` : "–"}
                        </td>
                        <td className={td}>{acc ? pText(acc.p_holm) : "–"}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            <p className="text-xs text-muted">
              ▼ green = our matcher leaks less / ▲ green = ranks better. With 10,000 permutations the smallest attainable p
              is about 0.0001 before correction.
            </p>
          </Section>

          <Section id="accuracy" title="Ranking accuracy" kicker="Test pools, original bios">
            <p>
              Tie-aware expected metrics (McSherry &amp; Najork, 2008), since entity matchers can give exactly tied scores.
              Graded nDCG@10 uses gain 2<sup>g</sup>−1. Mean over pools [95% CI].
            </p>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-line">
                    <th className={th}>Matcher</th>
                    <th className={th}>nDCG@10</th>
                    <th className={th}>MRR</th>
                    <th className={th}>P@5</th>
                    <th className={th}>P@10</th>
                  </tr>
                </thead>
                <tbody>
                  {[...scorers]
                    .sort((a, b) => ndcg(b.id)[0] - ndcg(a.id)[0])
                    .map((s) => (
                      <tr key={s.id} className={`border-b border-line/60 ${s.id === OURS ? "bg-accent-wash/40" : ""}`}>
                        <td className="py-2 pr-4 font-medium text-ink">{s.label}</td>
                        {(["ndcg@10", "mrr", "p@5", "p@10"] as const).map((k) => (
                          <td key={k} className={td}>
                            {ciText(M.ranking[s.id][k])}
                          </td>
                        ))}
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          </Section>

          <Section id="more-fairness" title="Other fairness metrics" kicker="Outcome parity">
            <p>
              Counterfactual gaps ask whether the same candidate is scored differently. These ask whether women and men are
              treated differently as groups. <span className="text-ink">TPR gap</span>: share of relevant women minus relevant
              men above a threshold chosen on dev (best F1 on per-pool z-scores), per occupation, then averaged.{" "}
              <span className="text-ink">Top-10 share</span>: female share of the top 10 minus 0.5 (pools are 50/50). The RMS
              TPR gap has no CI, because the bootstrap interval was not valid for that statistic here.
            </p>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-line">
                    <th className={th}>Matcher</th>
                    <th className={th}>Signed gap, full flip (+ favours female version)</th>
                    <th className={th}>Mean TPR gap (F − M)</th>
                    <th className={th}>RMS TPR gap</th>
                    <th className={th}>Top-10 female share − 0.5</th>
                  </tr>
                </thead>
                <tbody>
                  {scorers.map((s) => (
                    <tr key={s.id} className={`border-b border-line/60 ${s.id === OURS ? "bg-accent-wash/40" : ""}`}>
                      <td className="py-2 pr-4 font-medium text-ink">{s.label}</td>
                      <td className={td}>{ciText(M.signed_gap[s.id].gender_full)}</td>
                      <td className={td}>{ciText(M.tpr_gap_mean[s.id])}</td>
                      <td className={td}>{f3(M.tpr_gap_rms[s.id])}</td>
                      <td className={td}>{ciText(M.exposure[s.id])}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Section>

          <Section id="heldout" title="Held-out check" kicker="Robustness">
            <p>
              The final method&apos;s design was informed by ablations run on 200 of the 234 test pools. The other{" "}
              {data.fresh_pools.n_fresh} test pools were never used before the final run, so they are a clean check of that
              design loop. The pattern holds there:
            </p>
            <ForestPlot
              rows={[...scorers]
                .sort((a, b) => data.fresh_pools.scorers[a.id].gender_gap[0] - data.fresh_pools.scorers[b.id].gender_gap[0])
                .map((s) => ({
                  id: s.id,
                  label: s.label,
                  color: FAMILY_COLOR[s.family],
                  ci: data.fresh_pools.scorers[s.id].gender_gap as [number, number, number],
                  emphasis: s.id === OURS,
                  note: `nDCG@10 on these pools: ${data.fresh_pools.scorers[s.id]["ndcg@10"][0].toFixed(3)}`,
                }))}
              xLabel={`|score change| under full gender flip, ${data.fresh_pools.n_fresh} untouched test pools`}
            />
          </Section>

          <Section id="ablations" title="Ablations" kicker="What drives the leakage?">
            <p>
              Each ablation changes one component of the earlier reference method (JobBERT + ESCO skills, MiniLM, MaxSim-mean)
              and is run on all test pools. The clearest finding: <span className="text-ink">the extractor decides what
              leaks.</span> The ESCO ruler barely reacts to pronouns or names but reacts strongly to agentic/communal wording,
              because words like &ldquo;lead&rdquo; are ESCO skills. The fine-tuned tagger reads context, so swapping a pronoun
              can change which nearby spans it tags. Adding filtered noun chunks improved both accuracy and coverage, which motivated the final method.
            </p>
            <div className="space-y-6">
              {Object.entries(data.ablations).map(([key, a]) => (
                <Card key={key}>
                  <p className="font-semibold text-ink">{a.title}</p>
                  <p className="text-xs text-muted">Held fixed: {a.held_fixed}</p>
                  <div className="mt-3 overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-line">
                          <th className={th}>Variant</th>
                          <th className={th}>nDCG@10</th>
                          <th className={th}>Pairs with entities</th>
                          {["pronoun_swap", "name_swap_us", "agentic_communal", "gender_full"].map((c) => (
                            <th key={c} className={th}>
                              |gap| {condLabel(c).toLowerCase()}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {a.rows.map((r) => (
                          <tr key={r.id} className="border-b border-line/60">
                            <td className="py-2 pr-4 text-ink">
                              {r.label}
                              {r.reference && <span className="ml-2 rounded bg-surface-2 px-1.5 text-[10px] text-muted">reference</span>}
                            </td>
                            <td className={td}>{f3(r["ndcg@10"]?.[0])}</td>
                            <td className={td}>{r.frac_nonempty ? `${(r.frac_nonempty[0] * 100).toFixed(0)}%` : "–"}</td>
                            {["pronoun_swap", "name_swap_us", "agentic_communal", "gender_full"].map((c) => (
                              <td key={c} className={td}>
                                {f3(r.gaps[c]?.[0])}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </Card>
              ))}
            </div>
            <p className="text-xs text-muted">
              Pairs without entities on both sides score 0 before and after a rewrite, which looks like perfect fairness for
              trivial reasons. The &ldquo;pairs with entities&rdquo; column shows how often that happens. The final method
              finds entities in every test pair.
            </p>
          </Section>

          <Section id="selection" title="Choosing the final method" kicker="Dev split only">
            <p>
              Eight candidates (two extractor unions × two entity encoders × two aggregations) were scored on the{" "}
              {data.data.pools.dev} dev pools. The rule, written down before running: {data.selection.rule}. Fairness metrics
              were not looked at, because they are the outcome under test. The winner is the method this app runs.
            </p>
            <HBars
              rows={[...data.selection.rows]
                .sort((a, b) => b["dev_ndcg@10"]![0] - a["dev_ndcg@10"]![0])
                .map((r) => ({
                  id: r.id,
                  label: `${r.extractor.startsWith("jobbert") ? "JobBERT+ESCO+NC" : "ESCO+NC"} · ${r.backbone === "jobbert_v2" ? "JobBERT-v2" : "MiniLM"} · ${r.aggregation === "idf_weighted" ? "IDF" : "mean"}`,
                  emphasis: r.id === data.selection.chosen,
                  values: [{ key: "dev nDCG@10", value: r["dev_ndcg@10"]![0], color: r.id === data.selection.chosen ? "var(--series-1)" : "var(--series-legacy)" }],
                }))}
              ci={Object.fromEntries(data.selection.rows.map((r) => [r.id, [r["dev_ndcg@10"]![1], r["dev_ndcg@10"]![2]] as [number, number]]))}
              xLabel="dev nDCG@10 (line = 95% CI)"
              max={0.7}
              labelWidth={250}
            />
          </Section>

          <Section id="nearmiss" title="Where to draw the suggestion band" kicker="Phase 6">
            <p>
              The old app suggested &ldquo;reframe X to highlight Y&rdquo; when a job skill&apos;s best resume match had
              similarity 0.35–0.55. With no gold labels, we scored suggestions against the ESCO hierarchy: a suggestion
              counts as right if the two skills are the same concept or neighbours (lenient: siblings too). The band was
              picked on dev (highest lenient precision with ≥ {data.nearmiss.min_suggestions_dev} suggestions) and checked on
              test.
            </p>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-line">
                    <th className={th}>Band</th>
                    <th className={th}>Split</th>
                    <th className={th}>Suggestions</th>
                    <th className={th}>Per pair</th>
                    <th className={th}>Strict precision</th>
                    <th className={th}>Lenient precision</th>
                  </tr>
                </thead>
                <tbody>
                  {(["old", "chosen"] as const).flatMap((k) =>
                    (["dev", "test"] as const).map((sp) => (
                      <tr key={k + sp} className="border-b border-line/60">
                        <td className="py-2 pr-4 text-ink">
                          {k === "old" ? "Old app" : "Chosen"} {nm[k].band[0].toFixed(2)}–{nm[k].band[1].toFixed(2)}
                        </td>
                        <td className={td}>{sp}</td>
                        <td className={td}>{nm[k][sp].n.toLocaleString("en-US")}</td>
                        <td className={td}>{nm[k][sp].per_pair.toFixed(2)}</td>
                        <td className={td}>{nm[k][sp].strict.toFixed(3)}</td>
                        <td className={td}>{nm[k][sp].lenient.toFixed(3)}</td>
                      </tr>
                    )),
                  )}
                </tbody>
              </table>
            </div>
            <p>
              The old band is at the base rate, so its suggestions are about as good as random pairings. The app now uses
              the chosen band. It makes far fewer suggestions, but most point to a genuinely related skill. Dev precision of
              every band:
            </p>
            <BandHeatmap
              cells={data.nearmiss.grid_dev}
              marks={[
                { label: "old", lo: nm.old.band[0], hi: nm.old.band[1] },
                { label: "chosen", lo: nm.chosen.band[0], hi: nm.chosen.band[1] },
              ]}
              minN={data.nearmiss.min_suggestions_dev}
            />
          </Section>

          <Section id="figures" title="Paper figures" kicker="Static versions">
            <div className="grid gap-4 md:grid-cols-2">
              {data.figures.map((f) => (
                <Card key={f} className="p-3">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={`/research/figures/${f}.png`} alt={f.replace(/_/g, " ")} className="w-full rounded bg-white" />
                  <div className="mt-2 flex justify-between text-xs">
                    <span className="text-ink-2">{f.replace(/_/g, " ")}</span>
                    <a href={`/research/figures/${f}.pdf`} className="text-accent-ink hover:underline">
                      PDF
                    </a>
                  </div>
                </Card>
              ))}
            </div>
          </Section>

          <Section id="limitations" title="Limitations" kicker="Read before citing">
            <ul className="list-disc space-y-2 pl-5">
              <li>
                <span className="text-ink">Bios are not resumes.</span> BiasBios bios are ~60-word third-person summaries.
                Real resumes are longer, first-person and list more skills. The app&apos;s score references come from bios.
              </li>
              <li>
                <span className="text-ink">Binary gender.</span> The source labels are M/F, so the audit can&apos;t speak to
                non-binary candidates.
              </li>
              <li>
                <span className="text-ink">Design informed by test data.</span> The candidate family for the final method was
                motivated by ablations on 200 test pools. The final choice used dev only, and the {data.fresh_pools.n_fresh}{" "}
                untouched test pools confirm the pattern, but it isn&apos;t a fully pre-registered design.
              </li>
              <li>
                <span className="text-ink">Coverage.</span> {data.data.n_occupations_total - data.data.n_occupations_with_pools}{" "}
                occupations had too few postings for pools. The affiliation and agentic rewrites change under 3% of bios, so
                those comparisons are underpowered.
              </li>
              <li>
                <span className="text-ink">Less leakage isn&apos;t no leakage.</span> Lexical matchers leak less still. Noun
                chunks can carry names into the entity set, and ESCO counts agentic words like &ldquo;lead&rdquo; as skills.
              </li>
              <li>
                <span className="text-ink">Unverified resources.</span> The gender-coded word lists aren&apos;t yet checked
                against Gaucher et al. (2011). Wikidata name labels contain some errors. Human relevance ratings are still
                being collected. The LLM-judge baseline was not run.
              </li>
              <li>
                <span className="text-ink">JobBERT-v2</span> was trained on job titles and skill lists, not documents. Using
                it as a full-text matcher (64-token windows) is outside its design.
              </li>
            </ul>
          </Section>

          <Section id="reproduce" title="Reproduce" kicker="From the repository root">
            <p>
              Every number on this page comes from <code className="text-ink">public/research/data.json</code>, exported from
              the final runs (main run commit <code className="text-ink">{data.main_run.commit?.slice(0, 7)}</code>). Full
              instructions are in <code className="text-ink">research/README.md</code>.
            </p>
            <pre className="overflow-x-auto rounded-lg bg-surface-2 p-4 text-xs text-ink">
              {[
                "python -m research.experiments.train_extractor --set seed=13",
                "python -m research.experiments.prepare_data",
                "python -m research.experiments.make_perturbations",
                "python -m research.experiments.run --config configs/selection.yaml",
                "python -m research.experiments.run --config configs/main.yaml",
                "python -m research.analysis.make_all",
                "python -m research.analysis.export_app   # backend/artifacts/entity_li.json",
                "python -m research.analysis.export_web   # this page's data",
              ].join("\n")}
            </pre>
          </Section>
        </article>
      </div>
    </main>
  );
}
