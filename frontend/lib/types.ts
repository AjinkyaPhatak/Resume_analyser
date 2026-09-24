export interface MatchedSkill {
  jd_skill: string;
  resume_match: string;
  score: number;
}

export interface MatchResponse {
  match_percent: number;
  matched_skills: MatchedSkill[];
  missing_skills: string[];
  total_jd_skills: number;
  total_matched: number;
}

export interface FlaggedWord {
  word: string;
  type: "masculine-coded" | "feminine-coded";
  source: string;
}

export interface BiasResponse {
  bias_score: number;
  flagged_words: FlaggedWord[];
  verdict: string;
}
