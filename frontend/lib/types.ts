// Mirrors backend/app/schemas/analysis.py

export interface Requirement {
  skill: string;
  found_by: string[];
  weight: number;
  best_match: string | null;
  similarity: number;
  contribution: number;
  lost: number;
}

export interface Suggestion {
  jd_skill: string;
  resume_phrase: string;
  similarity: number;
  jd_concept: string;
  resume_concept: string;
}

export interface Calibration {
  percentile_vs_relevant: number;
  percentile_vs_irrelevant: number;
  relevant_median: number;
  irrelevant_median: number;
  n_relevant: number;
  n_irrelevant: number;
}

export interface MatchResponse {
  score: number;
  calibration: Calibration;
  requirements: Requirement[];
  resume_skills: { skill: string; found_by: string[] }[];
  suggestions: Suggestion[];
  suggestion_band: [number, number];
  empty_resume: boolean;
}

export interface ScoreShift {
  scorer: string;
  original: number;
  perturbed: number;
  delta: number;
  delta_norm: number;
}

export interface ConditionResult {
  condition: string;
  label: string;
  changed: boolean;
  skipped: string | null;
  perturbed_text: string;
  changes: { kind: string; original: string; replacement: string }[];
  scores: ScoreShift[];
}

export interface CounterfactualResponse {
  detected_gender: "F" | "M" | null;
  names_available: boolean;
  conditions: ConditionResult[];
  scorers: Record<string, string>;
  pool_sd: Record<string, number>;
}

export interface FlaggedWord {
  word: string;
  type: "masculine-coded" | "feminine-coded";
  matched: string;
  source: string;
}

export interface BiasResponse {
  bias_score: number;
  flagged_words: FlaggedWord[];
  verdict: string;
  masculine_count: number;
  feminine_count: number;
  n_words: number;
}

export interface StoredAnalysis {
  filename: string | null;
  resume_text: string;
  jd_text: string;
  match: MatchResponse;
  bias: BiasResponse;
}
