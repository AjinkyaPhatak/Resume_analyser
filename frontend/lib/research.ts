// Typed access to public/research/data.json (written by `python -m research.analysis.export_web`).
import raw from "@/public/research/data.json";

export type CI = [number, number, number] | null; // mean, low, high (95% cluster bootstrap)

export interface ScorerInfo {
  id: string;
  label: string;
  family: "lexical" | "full-text" | "legacy" | "entity";
  description: string;
}

export interface ResearchData {
  generated_utc: string;
  main_run: { commit: string | null; timestamp_utc: string | null };
  scorers: ScorerInfo[];
  conditions: { id: string; label: string }[];
  main: {
    ranking: Record<string, Record<string, CI>>;
    dev_ranking: Record<string, Record<string, CI>>;
    abs_gap: Record<string, Record<string, CI>>;
    signed_gap: Record<string, Record<string, CI>>;
    rank_shift: Record<string, Record<string, CI>>;
    abs_gap_nonempty: Record<string, Record<string, CI>>;
    tpr_gap_mean: Record<string, CI>;
    tpr_gap_rms: Record<string, number | null>;
    exposure: Record<string, CI>;
    frac_nonempty: Record<string, CI>;
    tests: { condition: string; metric: string; baseline: string; mean_diff: number; p_holm: number; n: number }[];
  };
  fresh_pools: {
    n_fresh: number;
    n_test: number;
    scorers: Record<string, { "ndcg@10": number[]; gender_gap: number[] }>;
  };
  ablations: Record<
    string,
    {
      title: string;
      held_fixed: string;
      rows: { id: string; label: string; reference: boolean; "ndcg@10": CI; frac_nonempty: CI; gaps: Record<string, CI> }[];
    }
  >;
  selection: {
    rule: string;
    chosen: string;
    rows: { id: string; extractor: string; backbone: string; aggregation: string; "dev_ndcg@10": CI }[];
  };
  nearmiss: {
    bands: Record<"old" | "chosen", { band: [number, number]; dev: BandStats; test: BandStats }>;
    grid_dev: { lo: number; hi: number; n: number; lenient: number | null }[];
    min_suggestions_dev: number;
  };
  extraction: { rows: { extractor: string; split: string; mode: string; precision: number; recall: number; f1: number }[] };
  training: {
    seeds: Record<string, { epoch: number; train_loss: number; dev_exact_f1: number; dev_partial_f1: number; seconds: number }[]>;
    base_model: string;
    max_epochs: number;
    patience: number;
    lr: number;
    batch_size: number;
    select_on: string;
  };
  data: {
    bios: Record<string, number>;
    n_jds: number;
    jd_mean_words: number;
    pools: Record<string, number>;
    pool_size: number;
    relevant_per_pool: number;
    jds_per_occupation: Record<string, number>;
    n_occupations_total: number;
    n_occupations_with_pools: number;
    perturbation_coverage: Record<string, Record<string, number>>;
  };
  examples: { condition: string; context: string; changes: { from: string; to: string }[] }[];
  figures: string[];
}

interface BandStats {
  n: number;
  strict: number;
  lenient: number;
  per_pair: number;
}

export const data = raw as unknown as ResearchData;

export const FAMILY_COLOR: Record<ScorerInfo["family"], string> = {
  entity: "var(--series-1)",
  "full-text": "var(--series-2)",
  lexical: "var(--series-3)",
  legacy: "var(--series-legacy)",
};

export const FAMILY_LABEL: Record<ScorerInfo["family"], string> = {
  entity: "Entity-level (ours)",
  "full-text": "Full-text neural",
  lexical: "Lexical",
  legacy: "Old app matcher",
};

export const scorer = (id: string): ScorerInfo => data.scorers.find((s) => s.id === id) ?? { id, label: id, family: "legacy", description: "" };

export const condLabel = (id: string) => data.conditions.find((c) => c.id === id)?.label ?? id;

export const f3 = (x: number | null | undefined) => (x == null ? "–" : x.toFixed(3));

export const ciText = (c: CI) => (c ? `${c[0].toFixed(3)} [${c[1].toFixed(3)}, ${c[2].toFixed(3)}]` : "–");

export const pText = (p: number) => (p < 0.001 ? "< 0.001" : p.toFixed(3));
