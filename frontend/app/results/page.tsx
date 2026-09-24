"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { MatchResponse, BiasResponse } from "@/lib/types";

interface Results {
  resume_id: string;
  match: MatchResponse;
  bias: BiasResponse;
}

export default function ResultsPage() {
  const router = useRouter();
  const [results, setResults] = useState<Results | null>(null);

  useEffect(() => {
    const stored = localStorage.getItem("results");
    if (!stored) {
      router.push("/analyse");
      return;
    }
    setResults(JSON.parse(stored));
  }, [router]);

  if (!results) return null;

  const { match, bias } = results;

  const scoreColor =
    match.match_percent >= 75
      ? "text-green-400"
      : match.match_percent >= 50
        ? "text-yellow-400"
        : "text-red-400";

  return (
    <main className="min-h-screen bg-gray-950 text-white px-4 py-12">
      <div className="max-w-3xl mx-auto space-y-8">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold">Your Results</h1>
          <Link
            href="/analyse"
            className="text-sm text-blue-400 hover:underline"
          >
            ← Analyse another
          </Link>
        </div>

        {/* Match Score */}
        <div className="bg-gray-900 rounded-2xl p-6 space-y-4">
          <h2 className="text-lg font-semibold text-gray-300">
            Semantic Match Score
          </h2>
          <p className={`text-6xl font-bold ${scoreColor}`}>
            {match.match_percent}%
          </p>
          <p className="text-gray-400 text-sm">
            {match.total_matched} of {match.total_jd_skills} job requirements
            matched semantically
          </p>
        </div>

        {/* Matched Skills */}
        <div className="bg-gray-900 rounded-2xl p-6 space-y-4">
          <h2 className="text-lg font-semibold text-gray-300">
            Matched Skills
          </h2>
          {match.matched_skills.length === 0 ? (
            <p className="text-gray-500 text-sm">No matches found</p>
          ) : (
            <div className="space-y-2">
              {match.matched_skills.map((s, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between bg-gray-800 rounded-lg px-4 py-2"
                >
                  <div className="text-sm">
                    <span className="text-white">{s.jd_skill}</span>
                    <span className="text-gray-500 mx-2">→</span>
                    <span className="text-green-400">{s.resume_match}</span>
                  </div>
                  <span className="text-xs text-gray-400">
                    {Math.round(s.score * 100)}% similar
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Missing Skills */}
        {match.missing_skills.length > 0 && (
          <div className="bg-gray-900 rounded-2xl p-6 space-y-4">
            <h2 className="text-lg font-semibold text-gray-300">
              Missing Skills
            </h2>
            <div className="flex flex-wrap gap-2">
              {match.missing_skills.map((skill, i) => (
                <span
                  key={i}
                  className="bg-red-900/40 text-red-300 text-xs px-3 py-1 rounded-full"
                >
                  {skill}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Bias Report */}
        <div className="bg-gray-900 rounded-2xl p-6 space-y-4">
          <h2 className="text-lg font-semibold text-gray-300">Bias Report</h2>
          <p
            className={`text-sm font-medium ${
              bias.flagged_words.length === 0
                ? "text-green-400"
                : "text-yellow-400"
            }`}
          >
            {bias.verdict}
          </p>
          <p className="text-gray-400 text-xs">
            Bias score: {bias.bias_score} (positive = masculine-leaning,
            negative = feminine-leaning)
          </p>

          {bias.flagged_words.length > 0 && (
            <div className="space-y-2 pt-2">
              <p className="text-xs text-gray-500 uppercase tracking-wide">
                Flagged Words
              </p>
              <div className="flex flex-wrap gap-2">
                {bias.flagged_words.map((w, i) => (
                  <span
                    key={i}
                    className={`text-xs px-3 py-1 rounded-full ${
                      w.type === "masculine-coded"
                        ? "bg-blue-900/40 text-blue-300"
                        : "bg-pink-900/40 text-pink-300"
                    }`}
                  >
                    {w.word}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
